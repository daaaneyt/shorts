"""Render the sub3piece series intro: a torn-paper collage on posterised time.

8 s at 30 fps. Everything that moves updates on threes (10 steps a second), like
stop-motion, and every step re-jitters the paper a touch ("boil"). The cut is
timed to a 150 bpm grid, so one beat is 0.4 s = 4 steps.

  0.0  "26.2 miles."  0.4 "In a suit."            black sheet
  0.8  rip 1: the sheet tears across and flies apart
  1.0  Adam runs (stop-motion photo swaps) between two ticker strips, a race clock spinning up
  3.2  rip 2: diagonal tear
  3.6  GUINNESS WORLD RECORD / 2:38:21 slapped on digit by digit / THE TIME TO BEAT
  5.1  the time cracks, 5.2 Adam bursts through it
  5.6  end card: sub3piece, London Marathon 2027, Spinal Research
  9.2  rip 3: the end card tears away to transparent (the episode shows through)

--hold sets how long the end card lingers past v1's: 1.6 s (one bar) by default
for v2, 0 for the v1 cut. Keep it a multiple of 0.4 to stay on the beat.

Usage:
  python3 render.py                       # RGBA PNG sequence -> frames/
  python3 render.py --preview 0.5 2 4.7   # preview PNGs (over ink) at those times
  python3 render.py --label "WEEK 07"     # adds an episode tag to the end card
  python3 render.py --scale 2             # 3840x2160
  python3 render.py --hold 0              # v1 timing (8.0 s)
"""
import argparse, functools, math, os, zlib
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter1d

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--scale", type=float, default=1.0, help="1 = 1920x1080, 2 = 3840x2160")
ap.add_argument("--label", default="", help='optional episode tag on the end card, e.g. "WEEK 07"')
ap.add_argument("--preview", nargs="*", type=float, help="write preview PNGs at these times (s)")
ap.add_argument("--frames", default="frames", help="output folder for the RGBA PNG sequence")
ap.add_argument("--hold", type=float, default=1.6, help="extra end-card seconds over v1 (multiple of 0.1)")
args = ap.parse_args()

HERE = os.path.dirname(os.path.abspath(__file__))
S = args.scale
W, H = round(1920 * S), round(1080 * S)
HOLD = round(args.hold * 10) / 10
FPS, POST, DUR = 30, 10, 8.0 + HOLD   # 30 fps out, motion posterised to 10 fps
NF = round(DUR * FPS)
MD = 100                              # sheets overhang the frame by this much (design px)
M = round(MD * S)
SW, SH = W + 2 * M, H + 2 * M

T_LINE2, T_RIP1 = 0.4, 0.8
T_RIP2 = 3.2
T_EYEBROW, T_DIGITS, T_TOBEAT = 3.6, 4.0, 4.8
T_CRACK, T_BURST = 5.1, 5.2
T_WORD, T_STRIP1, T_STRIP2, T_LABEL = 5.6, 6.0, 6.2, 6.4
T_OUT = 7.6 + HOLD


def hexc(h):
    return np.float32([int(h[i:i + 2], 16) for i in (0, 2, 4)]) / 255


INK, PAPER, WHITE, ORANGE = hexc("0C0D10"), hexc("F3F1EA"), hexc("FBFAF6"), hexc("FF5A2C")
BASE = {"ink": hexc("141519"), "paper": PAPER, "white": WHITE, "orange": ORANGE}
CORE = {"ink": hexc("D2CFC5"), "paper": hexc("FFFFFD"), "white": hexc("FFFFFF"), "orange": hexc("FFE4D3")}
TEXAMT = {"ink": (0.6, 0.30), "paper": (0.5, 0.0), "white": (0.45, 0.0), "orange": (0.8, 0.0)}


# ----------------------------------------------------------------------------
# time
def step_of(t):
    return math.floor(t * POST + 1e-6)


def q(t):
    return step_of(t) / POST


def seed_of(*key):
    return zlib.crc32(repr(key).encode())


def boil(key, k, amt=1.0):
    """Per-step stop-motion jitter: (dx, dy, drot)."""
    r = np.random.default_rng(seed_of("boil", key, k))
    return r.normal(0, 1.4 * amt), r.normal(0, 1.4 * amt), r.normal(0, 0.35 * amt)


# ----------------------------------------------------------------------------
# paper
def bnoise(h, w, sigma, rng):
    f = max(1, int(sigma / 3))
    n = rng.standard_normal((h // f + 2, w // f + 2)).astype(np.float32)
    if sigma / f > 0.3:
        n = cv2.GaussianBlur(n, (0, 0), sigma / f)
    if f > 1:
        n = cv2.resize(n, (w, h), interpolation=cv2.INTER_CUBIC)
    n = n[:h, :w]
    return n / (n.std() + 1e-6)


def fibres(h, w, rng):
    f = np.zeros((h, w), np.float32)
    n = int(h * w / (S * S) / 650)
    cx, cy = rng.uniform(0, w, n), rng.uniform(0, h, n)
    ang, ln = rng.uniform(0, np.pi, n), rng.uniform(3, 18, n) * S
    val = rng.choice([-1.0, 1.0], n) * rng.uniform(0.4, 1.0, n)
    dx, dy = np.cos(ang) * ln / 2, np.sin(ang) * ln / 2
    th = max(1, round(S))
    for i in range(n):
        cv2.line(f, (int(cx[i] - dx[i]), int(cy[i] - dy[i])), (int(cx[i] + dx[i]), int(cy[i] + dy[i])),
                 float(val[i]), th, cv2.LINE_AA)
    return cv2.GaussianBlur(f, (0, 0), 0.6 * S)


def paper_tex(h, w, kind, seed):
    rng = np.random.default_rng(seed)
    lum = (0.032 * bnoise(h, w, 80 * S, rng) + 0.02 * bnoise(h, w, 16 * S, rng)
           + 0.016 * bnoise(h, w, 0.8 * S, rng) + 0.05 * fibres(h, w, rng))
    km, ka = TEXAMT[kind]
    tex = BASE[kind] * (1 + km * lum[..., None]) + ka * lum[..., None]
    return np.clip(tex, 0, 1).astype(np.float32)


@functools.lru_cache(None)
def sheet_tex(kind):
    return paper_tex(SH, SW, kind, seed_of("sheet", kind))


def fill(dst, kind, off, key, k):
    """Lay a full sheet of paper into dst (a frame, or a sheet canvas when off == (M, M))."""
    tex = sheet_tex(kind)
    if dst.shape[:2] == (SH, SW):
        dst[..., :3], dst[..., 3] = tex, 1
        return
    dx, dy, _ = boil(key, k, 0.8)
    x0, y0 = M + int(round(dx * S)), M + int(round(dy * S))
    dst[..., :3], dst[..., 3] = tex[y0:y0 + H, x0:x0 + W], 1


# ----------------------------------------------------------------------------
# torn edges
def jag(n, rng, octaves):
    d = np.zeros(n, np.float32)
    for sig, amp in octaves:
        pad = int(4 * sig) + 2
        r = rng.standard_normal(n + 2 * pad).astype(np.float32)
        if sig > 0.3:
            r = gaussian_filter1d(r, sig)
        d += r[pad:pad + n] / (r.std() + 1e-6) * amp
    return d


def torn_path(p0, p1, rng, amp=1.0):
    """Jagged polyline from p0 to p1 (px), pinned at both ends."""
    p0, p1 = np.float32(p0), np.float32(p1)
    v = p1 - p0
    L = float(np.hypot(*v))
    st = 2.5 * S
    n = max(8, int(L / st))
    t = np.linspace(0, 1, n, dtype=np.float32)
    nrm = np.float32([-v[1], v[0]]) / L
    d = jag(n, rng, [(90 * S / st, 14 * S * amp), (18 * S / st, 5 * S * amp), (3 * S / st, 1.8 * S * amp),
                     (0, 0.8 * S)])
    d *= np.clip(np.minimum(t, 1 - t) * L / (30 * S), 0, 1)
    return p0 + v * t[:, None] + nrm * d[:, None]


def poly_mask(h, w, polys, ox=0, oy=0):
    m = np.zeros((h, w), np.uint8)
    cv2.fillPoly(m, [np.int32(np.round((np.asarray(p, np.float64) - (ox, oy)) * 16)) for p in polys],
                 255, cv2.LINE_AA, shift=4)
    return m.astype(np.float32) / 255


def rim_mask(mc, rng, width=1.0):
    """The fibrous white paper core that shows past the printed face along a tear."""
    h, w = mc.shape
    dist = cv2.distanceTransform((mc < 0.5).astype(np.uint8), cv2.DIST_L2, 3)
    field = (1.0 + 4.2 * np.abs(bnoise(h, w, 7 * S, rng)) + 1.1 * bnoise(h, w, 1.0 * S, rng)) * S * width
    return np.maximum(np.clip(field - dist + 0.5, 0, 1), mc)


# ----------------------------------------------------------------------------
# sprites and compositing (premultiplied float RGBA throughout)
class Sprite:
    def __init__(self, img, pivot):
        self.img = np.ascontiguousarray(img, np.float32)
        self.pivot = np.float32(pivot)


def put(dst, spr, pos, rot=0.0, scale=1.0, alpha=1.0, shadow=0.0, sh_off=(5, 9), sh_blur=9, off=(0, 0)):
    """Composite spr with its pivot at pos (design px), rotated (deg) and scaled about the pivot."""
    th = math.radians(rot)
    c, s = math.cos(th) * scale, math.sin(th) * scale
    px, py = spr.pivot
    tx = pos[0] * S + off[0] - (c * px - s * py)
    ty = pos[1] * S + off[1] - (s * px + c * py)
    A = np.float32([[c, -s, tx], [s, c, ty]])
    h, w = spr.img.shape[:2]
    cr = A @ np.float32([[0, w, 0, w], [0, 0, h, h], [1, 1, 1, 1]])
    pad = int((sh_blur * 3 + max(abs(sh_off[0]), abs(sh_off[1]))) * S) + 2 if shadow else 2
    x0, x1 = max(0, int(cr[0].min()) - pad), min(dst.shape[1], int(cr[0].max()) + pad + 1)
    y0, y1 = max(0, int(cr[1].min()) - pad), min(dst.shape[0], int(cr[1].max()) + pad + 1)
    if x1 <= x0 or y1 <= y0:
        return
    A[0, 2] -= x0
    A[1, 2] -= y0
    bw, bh = x1 - x0, y1 - y0
    reg = dst[y0:y1, x0:x1]
    if shadow:
        f = 4
        Aq = A / f
        Aq[0, 2] += sh_off[0] * S / f
        Aq[1, 2] += sh_off[1] * S / f
        sa = cv2.warpAffine(np.ascontiguousarray(spr.img[..., 3]), Aq, (bw // f + 2, bh // f + 2),
                            flags=cv2.INTER_LINEAR)
        sa = cv2.GaussianBlur(sa, (0, 0), max(0.5, sh_blur * S / f))
        sa = cv2.resize(sa, (bw + 2 * f, bh + 2 * f), interpolation=cv2.INTER_LINEAR)[:bh, :bw]
        sa *= shadow * alpha
        reg *= (1 - sa)[..., None]
        reg[..., 3] += sa
    wimg = cv2.warpAffine(spr.img, A, (bw, bh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT,
                          borderValue=(0, 0, 0, 0))
    if alpha != 1:
        wimg *= alpha
    reg *= 1 - wimg[..., 3:4]
    reg += wimg


# ----------------------------------------------------------------------------
# type
@functools.lru_cache(None)
def font(kind, px):
    if kind == "grotesk":
        f = ImageFont.truetype(f"{HERE}/fonts/SpaceGrotesk-Variable.ttf", px)
        f.set_variation_by_axes([700])
    else:
        f = ImageFont.truetype(f"{HERE}/fonts/SpaceMono-Bold.ttf", px)
    return f


def text_img(text, kind, size, colors, tracking=0.0):
    """Straight RGB + alpha of a line of text, cropped to its ink."""
    px = max(1, round(size * S))
    f = font(kind, px)
    if not isinstance(colors, list):
        colors = [colors] * len(text)
    adv = [f.getlength(ch) for ch in text]
    tr = tracking * px
    asc, desc = f.getmetrics()
    pad = px // 2
    wt = int(sum(adv) + tr * (len(text) - 1) + 2 * pad)
    im = Image.new("RGBA", (wt, asc + desc + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if tracking == 0 and all((c == colors[0]).all() for c in colors):
        d.text((pad, pad), text, font=f, fill=tuple(int(v * 255) for v in colors[0]) + (255,))
    else:
        x = pad
        for ch, a, col in zip(text, adv, colors):
            d.text((x, pad), ch, font=f, fill=tuple(int(v * 255) for v in col) + (255,))
            x += a + tr
    arr = np.asarray(im, np.float32) / 255
    ys, xs = np.where(arr[..., 3] > 0.01)
    arr = arr[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return arr[..., :3], arr[..., 3]


def inked(a, key):
    """Uneven print: knock a little density out of the ink."""
    rng = np.random.default_rng(seed_of("ink", key))
    n = bnoise(a.shape[0], a.shape[1], 1.2 * S, rng) * 0.6 + bnoise(a.shape[0], a.shape[1], 12 * S, rng) * 0.4
    return a * np.clip(0.93 + 0.05 * n, 0, 1)


@functools.lru_cache(None)
def text_sprite(text, kind, size, color, tracking=0.0, key=""):
    cols = [hexc(c) for c in color.split(",")] if "," in color else hexc(color)
    if isinstance(cols, list):
        cols = [cols[1] if ch == "3" else cols[0] for ch in text]   # wordmark: the 3 in the second colour
    rgb, a = text_img(text, kind, size, cols, tracking)
    a = inked(a, (text, key))
    return Sprite(np.dstack([rgb * a[..., None], a]), (a.shape[1] / 2, a.shape[0] / 2))


def print_on(tex, text, kind, size, color, tracking, cx, cy, key):
    rgb, a = text_img(text, kind, size, color, tracking)
    a = inked(a, key)
    h, w = a.shape
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    sx0, sy0 = max(0, -x0), max(0, -y0)
    sx1, sy1 = min(w, tex.shape[1] - x0), min(h, tex.shape[0] - y0)
    a, rgb = a[sy0:sy1, sx0:sx1], rgb[sy0:sy1, sx0:sx1]
    sl = tex[y0 + sy0:y0 + sy1, x0 + sx0:x0 + sx1]
    sl[:] = sl * (1 - a[..., None]) + rgb * a[..., None]


# ----------------------------------------------------------------------------
# scraps: torn rectangles of paper with something printed on them
@functools.lru_cache(None)
def scrap(w, h, kind, key, text="", tkind="mono", tsize=40, tcolor="0C0D10", tracking=0.14, amp=0.5,
          repeat=0, accent=""):
    rng = np.random.default_rng(seed_of("scrap", key))
    pad = int(26 * S)
    pw, ph = int(w * S), int(h * S)
    cw, ch = pw + 2 * pad, ph + 2 * pad
    c = [(pad, pad), (pad + pw, pad), (pad + pw, pad + ph), (pad, pad + ph)]
    sides = []
    for i in range(4):
        a, b = c[i], c[(i + 1) % 4]
        ln = math.hypot(b[0] - a[0], b[1] - a[1])
        sides.append(torn_path(a, b, rng, amp * min(1.0, ln / (260 * S)))[:-1])
    mc = poly_mask(ch, cw, [np.concatenate(sides)])
    mk = rim_mask(mc, rng, 0.9)
    tex = paper_tex(ch, cw, kind, seed_of("scraptex", key))
    if text:
        col = hexc(tcolor)
        if repeat:                       # ticker: repeat the phrase along the strip, separators in accent
            unit = text
            line = unit * repeat
            cols = [hexc(accent) if ch_ == "•" else col for ch_ in line]
            print_on(tex, line, tkind, tsize, cols, tracking, cw / 2, ch / 2, key)
        else:
            print_on(tex, text, tkind, tsize, col, tracking, cw / 2, ch / 2, key)
    img = np.dstack([tex * mc[..., None] + CORE[kind] * (mk - mc)[..., None], mk])
    return Sprite(img, (cw / 2, ch / 2))


def label_scrap(text, kind, tcolor, key, size=40, tkind="mono", tracking=0.14, padx=46, pady=30):
    px = round(size * S)
    f = font(tkind, px)
    tw = (sum(f.getlength(ch) for ch in text) + tracking * px * (len(text) - 1)) / S
    return scrap(int(tw + 2 * padx), int(size * 0.75 + 2 * pady), kind, key, text, tkind, size, tcolor, tracking)


@functools.lru_cache(None)
def blob(radius, kind, key):
    """A torn disc of paper."""
    rng = np.random.default_rng(seed_of("blob", key))
    pad = int(30 * S)
    r = radius * S
    n = int(2 * math.pi * r / (2.5 * S))
    ang = np.linspace(0, 2 * math.pi, n, endpoint=False)
    d = jag(n + 200, rng, [(36, 16 * S), (7, 5 * S), (1.2, 1.8 * S), (0, 0.8 * S)])
    d = d[100:100 + n]
    d -= np.linspace(0, d[-1] - d[0], n)            # close the loop
    rr = r + d
    cx = cy = r + pad + 20 * S
    pts = np.stack([cx + rr * np.cos(ang), cy + rr * np.sin(ang)], 1)
    size = int(2 * cx)
    mc = poly_mask(size, size, [pts])
    mk = rim_mask(mc, rng, 1.0)
    tex = paper_tex(size, size, kind, seed_of("blobtex", key))
    return Sprite(np.dstack([tex * mc[..., None] + CORE[kind] * (mk - mc)[..., None], mk]), (cx, cy))


# ----------------------------------------------------------------------------
# Adam: photocopied, scissor-cut stickers
HEAD = {1: (190.0, (770, 375)), 2: (195.6, (665, 270)), 3: (85.7, (405, 445))}   # head size, eye centre (src px)


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


@functools.lru_cache(None)
def adam(pose, head):
    src = np.asarray(Image.open(f"{HERE}/assets/adam{pose}.png").convert("RGBA"), np.float32) / 255
    ys, xs = np.where(src[..., 3] > 0.03)
    y0, x0 = ys.min(), xs.min()
    src = src[y0:ys.max() + 1, x0:xs.max() + 1]
    ex, ey = HEAD[pose][1][0] - x0, HEAD[pose][1][1] - y0
    sc = head * S / HEAD[pose][0]
    pre = np.dstack([src[..., :3] * src[..., 3:4], src[..., 3]])
    pre = cv2.resize(pre, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA if sc < 1 else cv2.INTER_CUBIC)
    a = np.clip(pre[..., 3], 0, 1)
    rgb = np.clip(pre[..., :3] / np.maximum(a, 1e-4)[..., None], 0, 1)
    a = smoothstep(0.2, 0.6, a)

    rng = np.random.default_rng(seed_of("adam", pose))
    g = rgb @ np.float32([0.3, 0.59, 0.11])
    g = np.clip((g - 0.07) / 0.79, 0, 1) ** 0.9
    g = cv2.GaussianBlur(g.astype(np.float32), (0, 0), 0.5 * S)
    g = np.clip(g + 0.055 * bnoise(*g.shape, 0.7 * S, rng) + 0.03 * bnoise(*g.shape, 20 * S, rng), 0, 1)
    col = INK + (WHITE - INK) * g[..., None]

    pad = int(44 * S)
    a = np.pad(a, pad)
    col = np.pad(col, ((pad, pad), (pad, pad), (0, 0)))
    inside = (a > 0.4).astype(np.uint8) * 255
    k = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * int(r * S) + 1,) * 2)
    inside = cv2.morphologyEx(inside, cv2.MORPH_CLOSE, k(10))
    inside = cv2.dilate(inside, k(14))
    cnts, _ = cv2.findContours(inside, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cut = [cv2.approxPolyDP(cn, 4.5 * S, True)[:, 0, :].astype(np.float64) for cn in cnts
           if cv2.contourArea(cn) > (60 * S) ** 2]
    border = np.maximum(poly_mask(*a.shape, cut), a)
    tex = paper_tex(*a.shape, "white", seed_of("sticker", pose))
    img = np.dstack([col * a[..., None] + tex * (border - a)[..., None], border])
    return Sprite(img, (ex * sc + pad, ey * sc + pad))


# ----------------------------------------------------------------------------
# tearing a flattened sheet into pieces
class Piece:
    def __init__(self, sheet, poly, key, core, rim=1.0):
        rng = np.random.default_rng(seed_of("piece", key))
        poly = np.asarray(poly, np.float64)
        pad = int(24 * S)
        x0 = max(0, int(poly[:, 0].min()) - pad)
        x1 = min(SW, int(poly[:, 0].max()) + pad)
        y0 = max(0, int(poly[:, 1].min()) - pad)
        y1 = min(SH, int(poly[:, 1].max()) + pad)
        h, w = y1 - y0, x1 - x0
        mc = poly_mask(h, w, [poly], x0, y0)
        mk = rim_mask(mc, rng, rim)
        reg = sheet[y0:y1, x0:x1]
        rimw = mk - mc * reg[..., 3]
        self.img = reg * mc[..., None] + np.dstack([core * rimw[..., None], rimw])
        self.rim = np.dstack([core * (mk - mc)[..., None], mk - mc])
        ys, xs = np.nonzero(mc > 0.5)
        px, py = xs.mean(), ys.mean()
        self.x0, self.y0 = x0, y0
        self.spr = Sprite(self.img, (px, py))
        self.home = ((x0 + px - M) / S, (y0 + py - M) / S)

    def put(self, dst, dx=0.0, dy=0.0, rot=0.0, shadow=0.45, lift=1.0):
        put(dst, self.spr, (self.home[0] + dx, self.home[1] + dy), rot,
            shadow=shadow, sh_off=(6 * lift, 11 * lift), sh_blur=10 * lift)

    def crack(self, dst, keep):
        """Draw only this piece's torn rim, where keep(x, y) (sheet px) says the tear has reached."""
        h, w = self.rim.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        m = keep(xx + self.x0, yy + self.y0)
        put(dst, Sprite(self.rim * m[..., None], self.spr.pivot), self.home, shadow=0.55, sh_off=(1.5, 3),
            sh_blur=2.5)


def dpx(p):
    """design px -> sheet px"""
    return (p[0] * S + M, p[1] * S + M)


def split(sheet, p0, p1, key, core, amp=1.2):
    """Tear a sheet along p0 -> p1 (design px). Returns (piece on the normal side, the other piece, path)."""
    rng = np.random.default_rng(seed_of("split", key))
    a, b = np.float64(dpx(p0)), np.float64(dpx(p1))
    path = torn_path(a, b, rng, amp).astype(np.float64)
    v = b - a
    nrm = np.float64([-v[1], v[0]]) / np.hypot(*v)
    far = 5000 * S
    pa = np.concatenate([path, [b + nrm * far, a + nrm * far]])
    pb = np.concatenate([path, [b - nrm * far, a - nrm * far]])
    return Piece(sheet, pa, (key, "a"), core), Piece(sheet, pb, (key, "b"), core), (a, b)


def progress_keep(a, b, frac):
    v = b - a
    L = float(np.hypot(*v))
    return lambda x, y: np.clip((frac * L - ((x - a[0]) * v[0] + (y - a[1]) * v[1]) / L) / (25 * S), 0, 1)


# ----------------------------------------------------------------------------
# scenes. Each draws into dst (a frame, or a sheet canvas with off=(M, M)) at time t.
def slap(t, ta):
    """Stop-motion slap-on: None before ta, then (scale, rot, lift) for the landing step and after."""
    if q(t) < ta - 1e-6:
        return None
    k = step_of(t) - step_of(ta)
    return (1.13, 2.5, 2.2) if k == 0 else (1.0, 0.0, 1.0)


def put_slapped(dst, spr, key, t, ta, pos, rot, off, shadow=0.5, amt=1.0):
    s = slap(t, ta)
    if s is None:
        return
    sc, dr, lift = s
    bx, by, br = boil(key, step_of(t), amt)
    put(dst, spr, (pos[0] + bx, pos[1] + by), rot + br + dr * (1 if seed_of(key) % 2 else -1), sc,
        shadow=shadow, sh_off=(6 * lift, 10 * lift), sh_blur=9 * lift, off=off)


def scene1(dst, t, off):
    k = step_of(t)
    fill(dst, "ink", off, "s1", k)
    for text, col, y, ta in (("26.2 miles.", "F3F1EA", 372, 0.0), ("In a suit.", "FF5A2C", 738, T_LINE2)):
        if q(t) >= ta:
            bx, by, br = boil(("s1", text), k, 0.8)
            put(dst, text_sprite(text, "grotesk", 215, col, -0.02, "s1"), (960 + bx, y + by), br * 0.5, off=off)


TICK_A = "FASTEST MARATHON IN A SUIT • "
TICK_B = "WORLD RECORD ATTEMPT • "


def run_pose(t):
    return (1, 2)[(step_of(t) // 2) % 2]


def scene2(dst, t, off):
    k = step_of(t)
    tt = q(t) - 1.0
    fill(dst, "orange", off, "s2", k)
    ta = scrap(3700, 196, "paper", "tickA", TICK_A, "grotesk", 132, "0C0D10", 0.0, 0.6, 3, "FF5A2C")
    tb = scrap(3700, 132, "ink", "tickB", TICK_B, "mono", 78, "F3F1EA", 0.06, 0.6, 4, "FF5A2C")
    bx, by, br = boil("tickA", k, 0.7)
    put(dst, ta, (1460 - 470 * tt + bx, 292 + by), -5 + br * 0.4, shadow=0.45, off=off)
    bx, by, br = boil("tickB", k, 0.7)
    put(dst, tb, (460 + 470 * tt + bx, 838 + by), 4 + br * 0.4, shadow=0.45, off=off)
    # race clock: a marathon's worth of time in 2.2 s, stopping short of the record
    kc = min(max(k, 10), 31) - 10
    secs = int((kc / 21) ** 0.9 * (2 * 3600 + 29 * 60)) + int(np.random.default_rng(kc).integers(0, 59)) * (kc > 0)
    clock = scrap(330, 96, "ink", "clock", f"{secs // 3600}:{secs // 60 % 60:02d}:{secs % 60:02d}", "mono", 62,
                  "FF5A2C", 0.04, 0.4)
    bx, by, br = boil("clock", k, 0.8)
    put(dst, clock, (262 + bx, 122 + by), -3 + br * 0.4, shadow=0.45, off=off)
    pose = run_pose(t)
    bx, by, br = boil("adam", k, 1.2)
    lift = -16 if pose == 2 else 0
    sc = 1 + 0.035 * tt
    put(dst, adam(pose, 124), (960 + bx, 248 + lift + by), br + (-1.2 if pose == 2 else 1.0), sc,
        shadow=0.5, sh_off=(10, 16), sh_blur=14, off=off)


DIGITS = [("2", "paper", "grotesk"), (":", None, None), ("3", "orange", "mono"), ("8", "white", "grotesk"),
          (":", None, None), ("2", "orange", "grotesk"), ("1", "paper", "mono")]


def digit_layout():
    out, x = [], 960 - 640
    rng = np.random.default_rng(7)
    for i, (g, kind, fk) in enumerate(DIGITS):
        w = 196 if kind else 76
        out.append((g, kind, fk, x + w / 2, 560 + rng.uniform(-18, 18), rng.uniform(-7, 7)))
        x += w + 15
    return out


DLAY = digit_layout()


def scene3(dst, t, off):
    k = step_of(t)
    fill(dst, "ink", off, "s3", k)
    put_slapped(dst, label_scrap("GUINNESS WORLD RECORD", "paper", "0C0D10", "eyebrow"), "eyebrow", t,
                T_EYEBROW, (960, 262), -2.2, off)
    for i, (g, kind, fk, x, y, r) in enumerate(DLAY):
        ta = T_DIGITS + 0.1 * i
        if kind:
            spr = scrap(196, 272, kind, ("digit", i), g, fk, 236 if fk == "grotesk" else 214, "0C0D10", 0.0, 0.35)
        else:
            spr = text_sprite(":", "grotesk", 210, "FF5A2C", 0.0, "colon")
        put_slapped(dst, spr, ("digit", i), t, ta, (x, y), r, off, shadow=0.55 if kind else 0.0)
    put_slapped(dst, label_scrap("THE TIME TO BEAT", "orange", "0C0D10", "tobeat"), "tobeat", t, T_TOBEAT,
                (960, 868), 1.8, off)


ADAM_END = (1452, 214)          # eye position on the end card
ADAM_END_HEAD = 70


def scene4(dst, t, off, with_adam=True):
    k = step_of(t)
    fill(dst, "paper", off, "s4", k)
    bx, by, br = boil("blob", k, 0.6)
    put(dst, blob(372, "orange", "sun"), (1440 + bx, 590 + by), br, shadow=0.35, off=off)
    if with_adam:
        bx, by, br = boil("adam_end", k, 1.0)
        stride = (k // 2) % 2                       # keeps running on the spot, on twos of steps
        put(dst, adam(3, ADAM_END_HEAD), (ADAM_END[0] + bx, ADAM_END[1] + by - 7 * stride), br - 1.5 + stride, 1.0,
            shadow=0.5, sh_off=(10, 14), sh_blur=12, off=off)
    word = text_sprite("sub3piece", "grotesk", 212, "0C0D10,FF5A2C", -0.04, "wordmark")
    put_slapped(dst, word, "wordmark", t, T_WORD, (650, 480), 0.0, off, shadow=0.0, amt=0.5)
    s1 = label_scrap("LONDON MARATHON 2027", "ink", "F3F1EA", "strip1", 40)
    s2 = label_scrap("RUNNING FOR SPINAL RESEARCH", "orange", "0C0D10", "strip2", 40)
    put_slapped(dst, s1, "strip1", t, T_STRIP1, (128 + s1.img.shape[1] / 2 / S, 662), -1.6, off)
    put_slapped(dst, s2, "strip2", t, T_STRIP2, (168 + s2.img.shape[1] / 2 / S, 752), 1.2, off)
    if args.label:
        lab = label_scrap(args.label.upper(), "white", "0C0D10", "label", 34)
        put_slapped(dst, lab, "label", t, T_LABEL, (150 + lab.img.shape[1] / 2 / S, 252), -3.5, off)


def flatten(fn, t, **kw):
    cv = np.zeros((SH, SW, 4), np.float32)
    fn(cv, t, (M, M), **kw)
    return cv


# ----------------------------------------------------------------------------
# the tears
@functools.lru_cache(None)
def tear1():
    return split(flatten(scene1, T_RIP1 - 0.01), (-MD - 40, 568), (1920 + MD + 40, 536), "rip1", CORE["ink"])


@functools.lru_cache(None)
def tear2():
    return split(flatten(scene2, T_RIP2 - 0.01), (1190, -MD - 40), (740, 1080 + MD + 40), "rip2", CORE["orange"])


@functools.lru_cache(None)
def tear4():
    return split(flatten(scene4, T_OUT - 0.01), (1010, -MD - 40), (925, 1080 + MD + 40), "rip4", CORE["paper"])


BURST_C = (960, 566)


@functools.lru_cache(None)
def burst():
    sheet = flatten(scene3, T_BURST - 0.01)
    rng = np.random.default_rng(11)
    c = np.float64(dpx(BURST_C))
    n = 7
    ang = np.sort((np.arange(n) * 2 * math.pi / n + rng.uniform(-0.25, 0.25, n) + 0.3) % (2 * math.pi))
    R = 2600 * S
    paths = [torn_path(c, c + R * np.float64([math.cos(a), math.sin(a)]), rng, 1.3).astype(np.float64)
             for a in ang]
    shards = []
    for i in range(n):
        a0, a1 = ang[i], ang[(i + 1) % n] + (2 * math.pi if i == n - 1 else 0)
        arc = [c + R * np.float64([math.cos(a), math.sin(a)]) for a in np.linspace(a0, a1, 8)]
        poly = np.concatenate([paths[i], arc, paths[(i + 1) % n][::-1]])
        mid = (a0 + a1) / 2
        shards.append((Piece(sheet, poly, ("shard", i), CORE["ink"]), mid, 1 if i % 2 else -1))
    return shards, c


# ----------------------------------------------------------------------------
def render(t):
    k = step_of(t)
    fr = np.zeros((H, W, 4), np.float32)
    o = (0, 0)

    if t < T_RIP1:
        scene1(fr, t, o)
    elif t < T_RIP1 + 0.2:                          # crack runs across the sheet
        a, b, (p0, p1) = tear1()                     # a = lower half, b = upper half
        scene1(fr, t, o)
        frac = (0.45, 1.0)[k - step_of(T_RIP1)]
        b.crack(fr, progress_keep(p0, p1, frac))
    elif t < T_RIP2:
        scene2(fr, t, o)
        if t < T_RIP1 + 0.6:
            a, b, _ = tear1()
            i = k - step_of(T_RIP1) - 2
            lo = [(0, 7, 0.4), (14, 96, 2.2), (46, 440, 5.5), (80, 1150, 9)][i]
            up = [(0, -7, -0.4), (-10, -96, -2.6), (-36, -430, -6.5), (-70, -1150, -11)][i]
            a.put(fr, lo[0], lo[1], lo[2], lift=1 + i)
            b.put(fr, up[0], up[1], up[2], lift=1 + i)
    elif t < T_RIP2 + 0.4:
        a, b, (p0, p1) = tear2()                     # a = left, b = right
        i = k - step_of(T_RIP2)
        if i == 0:
            scene2(fr, T_RIP2 - 0.01, o)
            b.crack(fr, progress_keep(p0, p1, 0.55))
        else:
            scene3(fr, t, o)
            le = [(-10, -4, -0.6), (-150, -50, -4), (-620, -170, -9)][i - 1]
            ri = [(10, 4, 0.6), (150, 50, 4), (620, 180, 9)][i - 1]
            a.put(fr, *le, lift=i)
            b.put(fr, *ri, lift=i)
    elif t < T_CRACK:
        scene3(fr, t, o)
    elif t < T_BURST:                                # the time cracks from the middle
        scene3(fr, t, o)
        shards, c = burst()
        keep = lambda x, y: np.clip((150 * S - np.hypot(x - c[0], y - c[1])) / (30 * S), 0, 1)
        for p, _, _ in shards:
            p.crack(fr, keep)
    elif t < T_BURST + 0.3:                          # Adam bursts through
        scene4(fr, t, o, with_adam=False)
        shards, c = burst()
        i = k - step_of(T_BURST)
        poses = [((960, 452), 0.34, -6), ((1150, 300), 0.74, -4), ((1400, 178), 1.16, -2)]
        (ax, ay), asc, arot = poses[i]
        if i == 0:
            put(fr, adam(3, ADAM_END_HEAD), (ax, ay), arot, asc, shadow=0.4)
        dist = [26, 300, 1050][i]
        spin = [2.0, 11, 26][i]
        for p, mid, sgn in shards:
            p.put(fr, math.cos(mid) * dist, math.sin(mid) * dist, sgn * spin, lift=1 + i)
        if i > 0:
            put(fr, adam(3, ADAM_END_HEAD), (ax, ay), arot, asc, shadow=0.55, sh_off=(16, 24), sh_blur=18)
    elif t < T_OUT:
        scene4(fr, t, o)
    else:                                            # tear away to transparent
        a, b, (p0, p1) = tear4()                     # a = left, b = right
        i = k - step_of(T_OUT)
        if i == 0:
            scene4(fr, T_OUT - 0.01, o)
            b.crack(fr, progress_keep(p0, p1, 0.6))
        else:
            le = [(-12, 2, -0.8), (-640, 40, -8), (-1500, 90, -14)][i - 1]
            ri = [(12, -2, 0.8), (640, -40, 8), (1500, -90, 14)][i - 1]
            a.put(fr, *le, lift=i)
            b.put(fr, *ri, lift=i)

    # grain + a soft vignette, on the steps like everything else
    g = grain_frames()[k % 4]
    fr[..., :3] = np.clip(fr[..., :3] * VIG[..., None] + g[..., None] * fr[..., 3:4], 0, 1)
    fr[..., :3] = np.minimum(fr[..., :3], fr[..., 3:4])
    return fr


@functools.lru_cache(None)
def grain_frames():
    out = []
    for i in range(4):
        rng = np.random.default_rng(1000 + i)
        out.append((0.018 * bnoise(H, W, 0.7 * S, rng)).astype(np.float32))
    return out


yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = 1 - 0.13 * np.clip(np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2)) - 0.45, 0, None) ** 1.7
del yy, xx


def to_straight(fr):
    a = fr[..., 3:4]
    rgb = np.where(a > 1e-4, fr[..., :3] / np.maximum(a, 1e-4), 0)
    return np.uint8(np.round(np.clip(np.dstack([rgb, a]), 0, 1) * 255))


if __name__ == "__main__":
    if args.preview is not None:
        os.makedirs("prev", exist_ok=True)
        for t in args.preview:
            fr = render(t)
            out = fr[..., :3] + INK * (1 - fr[..., 3:4])
            Image.fromarray(np.uint8(np.clip(out, 0, 1) * 255)).save(f"prev/prev_{t:05.2f}.png")
            print("prev", t)
    else:
        os.makedirs(args.frames, exist_ok=True)
        for i in range(NF):
            fr = render(i / FPS)
            Image.fromarray(to_straight(fr), "RGBA").save(f"{args.frames}/{i:04d}.png", compress_level=1)
            if i % 30 == 0:
                print("frame", i, flush=True)
