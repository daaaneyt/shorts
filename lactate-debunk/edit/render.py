"""Render the sub3piece lactate-debunk reel (video only).

Reads the source clip at 30 fps, applies the EDL (retakes removed, pauses
tightened), reframes to 1080x1920 with face-anchored punch-ins, grades, and
composites captions, B-roll cards, the hook title and the follow card.

Usage:
  python3 render.py                 # full render -> video_only.mp4
  python3 render.py --preview 1.0 20.5 ...   # write preview PNGs at output times
"""
import json, math, subprocess, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
SW, SH = 406, 720
SRC = "src.mp4"
IMG = "assets/"
FONT = "fonts/Montserrat-{}.ttf"
YELLOW = (255, 214, 64)
WHITE = (255, 255, 255)
INK = (16, 16, 18)

edl = json.load(open("edl.json"))
SEGS = edl["segments"]
TOTAL_FRAMES = sum(s["dur_frames"] for s in SEGS)
for s in SEGS:
    s["end_out"] = s["out"] + s["dur_frames"] / FPS
    s["src_end"] = s["src"] + s["dur_frames"] / FPS


def src_to_out(t):
    """Map a source time to output time (times inside a cut snap forward)."""
    for s in SEGS:
        if t < s["src"]:
            return s["out"]
        if t < s["src_end"]:
            return s["out"] + (t - s["src"])
    return SEGS[-1]["end_out"]


# ----------------------------------------------------------------------------
# Framing: zoom level per segment (W wide, M medium, T tight punch-in)
Z = {"W": 1.0, "M": 1.07, "T": 1.14}
ZOOM_PLAN = "W T W W W M W M M T T W M M W W T T W W W T T T W M M T T T W W".split()
assert len(ZOOM_PLAN) == len(SEGS), (len(ZOOM_PLAN), len(SEGS))
ANCHOR = (0.62 * W, 0.52 * H)          # roughly the face centre
S0 = H / SH
OX = (W - SW * S0) / 2

# shots = runs of consecutive segments sharing a zoom level (for slow drift)
shot_start = []
for i, s in enumerate(SEGS):
    if i and ZOOM_PLAN[i] == ZOOM_PLAN[i - 1]:
        shot_start.append(shot_start[-1])
    else:
        shot_start.append(s["out"])


def zoom_at(i, t):
    drift = min(0.03, 0.0035 * (t - shot_start[i]))
    return Z[ZOOM_PLAN[i]] * (1 + drift)


def frame_matrix(z):
    ax, ay = ANCHOR
    return np.float32([[z * S0, 0, z * OX + (1 - z) * ax],
                       [0, z * S0, (1 - z) * ay]])


# ----------------------------------------------------------------------------
# Grade: gentle contrast, a touch of saturation and warmth, soft vignette
x = np.arange(256) / 255.0
curve = 0.5 + (x - 0.5) * 1.07
curve = np.where(curve > 0.92, 0.92 + (curve - 0.92) * 0.6, curve)   # protect the white wall
curve = np.clip(curve, 0, 1)
LUT_B = np.uint8(np.clip(curve * 0.985, 0, 1) * 255)
LUT_G = np.uint8(curve * 255)
LUT_R = np.uint8(np.clip(curve * 1.012, 0, 1) * 255)
yy, xx = np.mgrid[0:H, 0:W]
r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H * 0.47) / (H / 2)) ** 2)
VIGNETTE = np.uint8(np.clip(1 - 0.16 * np.clip(r - 0.55, 0, None) ** 1.6, 0, 1) * 255)
VIGNETTE = cv2.merge([VIGNETTE] * 3)


def grade(src_bgr):
    b, g, r_ = cv2.split(src_bgr)
    img = cv2.merge([cv2.LUT(b, LUT_B), cv2.LUT(g, LUT_G), cv2.LUT(r_, LUT_R)])
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    return cv2.addWeighted(img, 1.10, gray, -0.10, 0)


def sharpen(img, amount=0.45, sigma=1.3):
    bl = cv2.GaussianBlur(img, (0, 0), sigma)
    return cv2.addWeighted(img, 1 + amount, bl, -amount, 0)


# ----------------------------------------------------------------------------
# Easing / compositing helpers
def ease_out(p):
    p = min(max(p, 0.0), 1.0)
    return 1 - (1 - p) ** 3


def clamp01(v):
    return min(max(v, 0.0), 1.0)


def pil_to_bgra(im):
    a = np.asarray(im.convert("RGBA"))
    return a[..., [2, 1, 0, 3]].copy()


def composite(frame, patch, cx, cy, alpha=1.0, scale=1.0):
    """Alpha-blend a BGRA patch centred at (cx, cy)."""
    if alpha <= 0.003:
        return
    if abs(scale - 1.0) > 1e-3:
        ph, pw = patch.shape[:2]
        nw, nh = max(1, int(round(pw * scale))), max(1, int(round(ph * scale)))
        patch = cv2.resize(patch, (nw, nh), interpolation=cv2.INTER_LINEAR if scale > 1 else cv2.INTER_AREA)
    ph, pw = patch.shape[:2]
    x0, y0 = int(round(cx - pw / 2)), int(round(cy - ph / 2))
    fx0, fy0, fx1, fy1 = max(0, x0), max(0, y0), min(W, x0 + pw), min(H, y0 + ph)
    if fx1 <= fx0 or fy1 <= fy0:
        return
    p = patch[fy0 - y0:fy1 - y0, fx0 - x0:fx1 - x0].astype(np.float32)
    a = p[..., 3:4] * (alpha / 255.0)
    roi = frame[fy0:fy1, fx0:fx1].astype(np.float32)
    frame[fy0:fy1, fx0:fx1] = (roi * (1 - a) + p[..., :3] * a).astype(np.uint8)


def rounded_rect(size, radius, fill):
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius, fill=fill)
    return im


def with_shadow(im, blur=22, offset=10, opacity=0.55, pad=48):
    w, h = im.size
    canvas = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    mask = im.split()[3].point(lambda v: int(v * opacity))
    sh.paste((0, 0, 0, 255), (pad, pad + offset), mask)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    canvas = Image.alpha_composite(canvas, sh)
    canvas.alpha_composite(im, (pad, pad))
    return canvas


# ----------------------------------------------------------------------------
# Captions
CORRECT = {88: "Ingebrigtsen", 113: "Sawe's", 119: "Kipchoge", 302: "Sawe",
           355: "science", 364: "lactate", 173: "North\u00a0East,"}
MERGE = {  # first index -> (text, indices merged)
    265: ("VO2", [265, 266]), 267: ("max,", [267]), 268: ("their", [268]),
    269: ("resting", [269, 270]), 304: ("Kipchoge,", [304, 305]),
    220: ("smartwatch", [220, 221]), 257: ("smartwatches.", [257, 258]),
}


# word indices spoken in the retakes that the EDL removes
DROPPED = set(range(152, 161)) | set(range(203, 206)) | set(range(312, 319)) | set(range(375, 397))
WEAK_END = {"the", "a", "an", "their", "his", "of", "to", "in", "at", "and", "with", "for", "from",
            "on", "is", "are", "was", "were", "that", "this", "some", "who", "which", "you", "would",
            "been", "not", "did", "had", "they", "we", "he", "i", "it's", "i'm", "so", "but", "or"}
BREAK_BEFORE = {"and", "but", "when", "which", "who", "so", "or", "that", "then", "because"}


def load_words():
    raw = json.load(open("words.json"))
    words, skip = [], set()
    for i, w in enumerate(raw):
        if i in skip or i in DROPPED:
            continue
        text = CORRECT.get(i, w["w"])
        if i in MERGE:
            text, idxs = MERGE[i]
            skip.update(idxs)
        words.append({"w": text, "t": src_to_out(max(w["s"], 0.0))})
    return words


CAPTION_SCRIPT = """
Someone the other day
told me that they think
that the thing
that separates
the best athletes
in the world
is their ability
to accurately measure
and react to their
lactate threshold.
And I personally think
this is just like
a mad take.
When you look at
the actual best athletes
in the world,
or most of the best
athletes in the world,
when you look at
the best runners
in the world
historically,
they've come from
Ethiopia, Kenya, Uganda.
Obviously we've got
some amazing talent
in Europe,
Ingebrigtsen
comes to mind.
And many others.
But when you look at
those runners
from Africa,
they are coming from
some very, very
humble backgrounds.
Sawe's dad
was a maize farmer.
Kipchoge didn't even
know his dad
and he grew up
in a random village
and these people
did not have access
to the resources
that would enable them
to measure
the lactate threshold.
In fact, Michael Crawley,
who is an author
based here
in the North East,
went to Kenya
and lived there
for over a year,
training with some
of the best runners
in the country.
And some of the stuff
he experienced
was mad.
So for example
when he was training
with one group
they had literally one
smartwatch between
the entire group,
which the person
running at the front
of the pack
would use to measure
pace and stuff.
They did not use
smartwatches
on the daily.
They weren't tracking
the mileage
through smartwatches.
They weren't measuring
the, you know,
VO2 max,
their resting heart rate,
all of that
kind of stuff,
they were reliant
on much more
basic things.
And yet
these runners
were and are
the best in the world.
The likes of Sawe
and Kipchoge,
the people who are
setting records,
they're not measuring
their lactate threshold
after every rep
on the track.
And I appreciate
there's the
altitude component,
there's the
genetic component,
but my point is
just that like
we cannot reduce
running and
running science
down to just like,
"Oh, who measures
their lactate threshold
the best?"
It's about so much
more than that.
I'm trying to run
the fastest marathon
in a suit
at the London Marathon
next year.
So if you want
to follow along
with that mad journey,
then please
follow the page.
"""


def norm(tok):
    return "".join(c for c in tok.lower() if c.isalnum())


def build_groups(words, font=None):
    """Align the hand-phrased caption script to the timed word list."""
    groups, wi = [], 0
    for line in [l for l in CAPTION_SCRIPT.strip().splitlines() if l.strip()]:
        g = []
        for tok in line.split(" "):
            if norm(tok) != norm(words[wi]["w"]):
                raise ValueError(f"caption mismatch at {line!r}: {tok!r} vs {words[wi]['w']!r}")
            g.append({"w": tok, "t": words[wi]["t"]})
            wi += 1
        groups.append(g)
    assert wi == len(words), (wi, len(words))
    return groups


def clean(w):
    w = w.strip()
    while w and w[-1] in ".,":
        w = w[:-1]
    return w


CAP_FONT = ImageFont.truetype(FONT.format("ExtraBold"), 62)
CAP_Y = 1420


def render_caption(group, active):
    font = CAP_FONT
    toks = [w["w"] for w in group]
    toks[-1] = clean(toks[-1])
    space = font.getlength(" ")
    widths = [font.getlength(t) for t in toks]
    total = sum(widths) + space * (len(toks) - 1)
    pad = 40
    asc, desc = font.getmetrics()
    Wc, Hc = int(total + 2 * pad), asc + desc + 2 * pad
    txt = Image.new("RGBA", (Wc, Hc), (0, 0, 0, 0))
    d = ImageDraw.Draw(txt)
    xpos = pad
    for k, (t, wd) in enumerate(zip(toks, widths)):
        col = YELLOW if k == active else WHITE
        d.text((xpos, pad), t, font=font, fill=col + (255,), stroke_width=4, stroke_fill=(0, 0, 0, 200))
        xpos += wd + space
    sh = Image.new("RGBA", (Wc, Hc), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((pad, pad + 5), " ".join(toks), font=font, fill=(0, 0, 0, 150),
                            stroke_width=6, stroke_fill=(0, 0, 0, 150))
    sh = sh.filter(ImageFilter.GaussianBlur(9))
    out = Image.alpha_composite(sh, txt)
    return pil_to_bgra(out)


class Captions:
    def __init__(self):
        words = load_words()
        self.groups = build_groups(words, font=CAP_FONT)
        self.spans = []
        for gi, g in enumerate(self.groups):
            start = g[0]["t"] - 0.04
            nxt = self.groups[gi + 1][0]["t"] - 0.04 if gi + 1 < len(self.groups) else TOTAL_FRAMES / FPS
            end = min(nxt, g[-1]["t"] + 0.9)
            self.spans.append((start, end))
        self.cache = {}

    def draw(self, frame, t):
        for gi, (a, b) in enumerate(self.spans):
            if a <= t < b:
                g = self.groups[gi]
                active = 0
                for k, w in enumerate(g):
                    if t >= w["t"] - 0.02:
                        active = k
                key = (gi, active)
                if key not in self.cache:
                    self.cache[key] = render_caption(g, active)
                p = ease_out((t - a) / 0.12)
                alpha = clamp01((t - a) / 0.06)
                if b < self.next_start(gi) - 1e-3:          # a pause follows: fade out
                    alpha *= clamp01((b - t) / 0.08)
                composite(frame, self.cache[key], W / 2, CAP_Y, alpha=alpha, scale=0.9 + 0.1 * p)
                return

    def next_start(self, gi):
        return self.spans[gi + 1][0] if gi + 1 < len(self.spans) else 1e9


# ----------------------------------------------------------------------------
# Title blocks (hook + follow card)
def pill(text, size=32):
    f = ImageFont.truetype(FONT.format("Black"), size)
    tracking = 3
    wid = sum(f.getlength(c) for c in text) + tracking * (len(text) - 1)
    asc, desc = f.getmetrics()
    padx, pady = 22, 12
    im = rounded_rect((int(wid + 2 * padx), asc + desc // 2 + 2 * pady), 14, YELLOW + (255,))
    d = ImageDraw.Draw(im)
    x = padx
    for c in text:
        d.text((x, pady), c, font=f, fill=INK + (255,))
        x += f.getlength(c) + tracking
    return im


def title_block(tag, lines, size=62, highlight=()):
    """lines: list of strings; highlight: words drawn in yellow."""
    f = ImageFont.truetype(FONT.format("ExtraBold"), size)
    asc, desc = f.getmetrics()
    lh = int(size * 1.18)
    widths = [f.getlength(l) for l in lines]
    padx, pady = 40, 30
    bw, bh = int(max(widths) + 2 * padx), int(lh * len(lines) + 2 * pady - (lh - asc - desc // 2))
    box = rounded_rect((bw, bh), 30, (14, 14, 16, 215))
    d = ImageDraw.Draw(box)
    for i, l in enumerate(lines):
        x = (bw - widths[i]) / 2
        for k, word in enumerate(l.split(" ")):
            col = YELLOW if word.strip("?") in highlight else WHITE
            d.text((x, pady + i * lh), word, font=f, fill=col + (255,))
            x += f.getlength(word + " ")
    tg = pill(tag)
    gap = 18
    W2 = max(bw, tg.width)
    im = Image.new("RGBA", (W2, tg.height + gap + bh), (0, 0, 0, 0))
    im.alpha_composite(tg, ((W2 - tg.width) // 2, 0))
    im.alpha_composite(box, ((W2 - bw) // 2, tg.height + gap))
    return pil_to_bgra(with_shadow(im, blur=18, offset=8, opacity=0.35))


HOOK = title_block("DEBUNK", ["Does lactate testing", "make elite runners?"], highlight=("lactate", "testing"))
FOLLOW = title_block("FOLLOW THE JOURNEY", ["@sub3piece"], size=70)
HOOK_Y = 300 + HOOK.shape[0] / 2 - 48
FOLLOW_Y = 300 + FOLLOW.shape[0] / 2 - 48
HOOK_END = SEGS[0]["end_out"] - 0.05
FOLLOW_START = src_to_out(128.22)   # "So if you want to follow along..."


def draw_titles(frame, t):
    if t < HOOK_END + 0.3:
        a = clamp01((HOOK_END + 0.3 - t) / 0.3)
        p = ease_out(clamp01((HOOK_END + 0.3 - t) / 0.3))
        composite(frame, HOOK, W / 2, HOOK_Y - 20 * (1 - p), alpha=a)
    if t >= FOLLOW_START:
        p = ease_out((t - FOLLOW_START) / 0.35)
        composite(frame, FOLLOW, W / 2, FOLLOW_Y + 40 * (1 - p), alpha=clamp01((t - FOLLOW_START) / 0.25),
                  scale=0.94 + 0.06 * p)


# ----------------------------------------------------------------------------
# B-roll cards
def make_card(path, crop=None, max_w=880, max_h=990, max_up=1.6):
    im = Image.open(path).convert("RGB")
    if crop:
        im = im.crop(crop)
    s = min(max_w / im.width, max_h / im.height, max_up)
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    # light sharpen for upscaled stills
    if s > 1.05:
        im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
    mask = rounded_rect(im.size, 30, (255, 255, 255, 255)).split()[3]
    card = Image.new("RGBA", im.size, (0, 0, 0, 0))
    card.paste(im, (0, 0), mask)
    # hairline border for definition against the blurred background
    ImageDraw.Draw(card).rounded_rectangle([1, 1, im.width - 2, im.height - 2], 30,
                                           outline=(255, 255, 255, 70), width=3)
    return pil_to_bgra(with_shadow(card, blur=26, offset=14, opacity=0.6, pad=60))


CARD_Y = 820
CARDS = [  # (image, crop, src_in, src_out)
    ("2.webp", (0, 20, 1037, 945), 21.25, 23.64),     # map: "Ethiopia, Kenya, Uganda"
    ("5.jpg", None, 25.55, 28.10),                    # Ingebrigtsen
    ("4.jpg", None, 35.25, 38.05),                    # Sawe's dad was a maize farmer
    ("1.jpg", None, 52.75, 55.72),                    # Michael Crawley, author
    ("3.jpg", None, 55.72, 60.28),                    # training with the best runners
]
CARD_IMGS = [make_card(IMG + f, c) for f, c, _, _ in CARDS]
CARD_T = [(src_to_out(a), src_to_out(b)) for _, _, a, b in CARDS]
IN_D, OUT_D = 0.28, 0.2


def card_state(k, t):
    """-> (alpha, scale, y offset) for card k at output time t."""
    a, b = CARD_T[k]
    if t < a or t > b + OUT_D:
        return 0.0, 1.0, 0.0
    if t < a + IN_D:
        p = ease_out((t - a) / IN_D)
        return p, 0.9 + 0.1 * p, 36 * (1 - p)
    if t <= b:
        return 1.0, 1.0 + 0.035 * (t - a - IN_D) / max(0.1, b - a - IN_D), 0.0
    p = (t - b) / OUT_D
    return 1 - p, 1.035 + 0.02 * p, 0.0


def bg_amount(t):
    """How much the talking head is blurred/darkened behind cards."""
    v = 0.0
    for k in range(len(CARDS)):
        a, b = CARD_T[k]
        if a <= t <= b + OUT_D:
            if t < a + IN_D:
                v = max(v, ease_out((t - a) / IN_D))
            elif t <= b:
                v = 1.0
            else:
                nxt_close = any(abs(CARD_T[j][0] - b) < 0.05 for j in range(len(CARDS)))
                v = max(v, 1.0 if nxt_close else 1 - (t - b) / OUT_D)
    return v


# ----------------------------------------------------------------------------
def out_frame_to_src(n):
    t = n / FPS
    for i, s in enumerate(SEGS):
        if t < s["end_out"] - 1e-6:
            return i, t, s["src"] + (t - s["out"])
    s = SEGS[-1]
    return len(SEGS) - 1, t, s["src_end"] - 1 / FPS


class SourceReader:
    def __init__(self):
        self.p = subprocess.Popen(
            ["ffmpeg", "-v", "error", "-i", SRC, "-vf",
             "fps=30,scale=in_color_matrix=bt2020:in_range=tv,format=bgr24",
             "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
        self.idx = -1
        self.frame = None

    def get(self, k):
        while self.idx < k:
            b = self.p.stdout.read(SW * SH * 3)
            if len(b) < SW * SH * 3:
                return self.frame
            self.frame = np.frombuffer(b, np.uint8).reshape(SH, SW, 3)
            self.idx += 1
        return self.frame


CAPS = Captions()


def render_frame(src, seg_i, t):
    g = grade(src)
    z = zoom_at(seg_i, t)
    frame = cv2.warpAffine(g, frame_matrix(z), (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    frame = sharpen(frame)
    frame = cv2.multiply(frame, VIGNETTE, scale=1 / 255)
    bga = bg_amount(t)
    if bga > 0.003:
        small = cv2.GaussianBlur(g, (0, 0), 7)
        blur = cv2.warpAffine(small, frame_matrix(1.08), (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        blur = cv2.convertScaleAbs(blur, alpha=0.5, beta=0)
        frame = cv2.addWeighted(frame, 1 - bga, blur, bga, 0)
    for k in range(len(CARDS)):
        a, s, dy = card_state(k, t)
        if a > 0:
            composite(frame, CARD_IMGS[k], W / 2, CARD_Y + dy, alpha=a, scale=s)
    draw_titles(frame, t)
    CAPS.draw(frame, t)
    return frame


def main():
    if "--preview" in sys.argv:
        times = [float(v) for v in sys.argv[sys.argv.index("--preview") + 1:]]
        reader = SourceReader()
        todo = sorted((int(round(tt * FPS)), tt) for tt in times)
        for n, tt in todo:
            seg_i, t, ts = out_frame_to_src(n)
            src = reader.get(int(round(ts * FPS)))
            cv2.imwrite(f"prev_{tt:07.2f}.png", render_frame(src, seg_i, t))
        return
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-",
         "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
         "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-profile:v", "high", "-level", "4.2",
         "-x264-params", "keyint=60:min-keyint=30",
         "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
         "-movflags", "+faststart", "video_only.mp4"], stdin=subprocess.PIPE)
    reader = SourceReader()
    for n in range(TOTAL_FRAMES):
        seg_i, t, ts = out_frame_to_src(n)
        src = reader.get(int(round(ts * FPS)))
        enc.stdin.write(render_frame(src, seg_i, t).tobytes())
        if n % 300 == 0:
            print(f"frame {n}/{TOTAL_FRAMES}", flush=True)
    enc.stdin.close()
    enc.wait()
    print("done")


if __name__ == "__main__":
    main()
