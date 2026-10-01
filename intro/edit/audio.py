"""Synthesise the intro's sound: a 150 bpm drum + bass groove and paper foley
(rips, slaps, digit stamps, the burst-through impact), locked to render.py's
timeline. Everything is generated here, so there is nothing to license.

Every element is built on its own stem. Each stem gets its group's room and its
own soft-clip, then one bus compressor keyed from the whole mix rides all stems
by the same gain, and one loudness gain takes the mix to -14 LUFS. So the stems
at 0 dB sum exactly to the mix before its final peak limiter.

Writes stems/NN_name.wav (24-bit) and mix_full.wav (float, pre-limiter).
  python3 audio.py              # v2: end card held one extra bar (1.6 s)
  python3 audio.py --hold 0     # v1 timing
"""
import argparse, json, os, subprocess
import numpy as np, soundfile as sf
from scipy.signal import butter, fftconvolve, sosfilt

ap = argparse.ArgumentParser()
ap.add_argument("--hold", type=float, default=1.6, help="extra end-card seconds (match render.py)")
ap.add_argument("--tag", action="store_true", help="the end card has an episode tag (adds its slap at 6.4 s)")
args = ap.parse_args()

SR = 48000
HOLD = args.hold
DUR = 8.0 + HOLD
N = int(SR * DUR)
BEAT = 60 / 150
rng = np.random.default_rng(3)


def t_(d):
    return np.arange(int(SR * d)) / SR


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "bandpass", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, "highpass", fs=SR, output="sos"), x, axis=0)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, "lowpass", fs=SR, output="sos"), x)


def noise(d):
    return rng.standard_normal(int(SR * d))


STEMS = ["kick", "clap", "hats", "bass", "synth-stabs",
         "paper-rips", "paper-slaps", "clock-ticks", "whooshes-riser", "impact"]
MUSIC = STEMS[:5]
bus = {name: np.zeros((N + SR, 2)) for name in STEMS}


def add(stem, sig, at, gain=1.0, pan=0.0):
    x = bus[stem]
    i = int(at * SR)
    if sig.ndim == 1:
        sig = np.stack([sig * np.sqrt(0.5 * (1 - pan)), sig * np.sqrt(0.5 * (1 + pan))], 1) * np.sqrt(2)
    n = min(len(sig), len(x) - i)
    x[i:i + n] += sig[:n] * gain


# ---------------------------------------------------------------------------- drums + bass
def kick(big=False):
    t = t_(0.6 if big else 0.4)
    f = 44 + 130 * np.exp(-t / 0.028)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (0.32 if big else 0.2))
    click = hp(noise(0.004), 2500) * np.exp(-t_(0.004) / 0.001) * 0.5
    body[:len(click)] += click
    return np.tanh(body * 1.6) * 0.9


def clap():
    t = t_(0.28)
    env = np.zeros_like(t)
    for d in (0.0, 0.011, 0.022):
        i = int(d * SR)
        env[i:] += np.exp(-(t[:len(t) - i]) / 0.008)
    env += 0.5 * np.exp(-t / 0.09)
    return bp(noise(0.28), 900, 3200) * env * 0.55


def hat(open_=False):
    d = 0.18 if open_ else 0.045
    t = t_(d)
    return hp(noise(d), 7000, 4) * np.exp(-t / (0.06 if open_ else 0.012)) * 0.35


def saw(freq, d):
    t = t_(d)
    ph = (freq * t) % 1.0
    return 2 * ph - 1


def bass(freq, d):
    t = t_(d)
    s = saw(freq, d) + 0.7 * saw(freq * 1.006, d) + 0.6 * np.sin(2 * np.pi * freq * t)
    env = np.minimum(1, t / 0.004) * np.exp(-t / 0.22)
    return lp(s, 380, 2) * env * 0.42


def stab(freqs, d=0.5):
    t = t_(d)
    s = sum(saw(f, d) + saw(f * 1.004, d) for f in freqs)
    return lp(s, 2200, 2) * np.minimum(1, t / 0.003) * np.exp(-t / 0.12) * 0.12


E1, G1, A1, B1, D2 = 41.2, 49.0, 55.0, 61.7, 73.4


def groove(start, end, bass_notes=(E1, E1, G1, A1)):
    """One bar = 16 sixteenths. Kick on 1 and the 'and' of 2 and 3, clap on 2 and 4, hats on the 8ths."""
    sx = BEAT / 4
    kicks = {0, 6, 8}
    i = 0
    while start + i * sx < end - 1e-6:
        tt = start + i * sx
        pos = i % 16
        if pos in kicks:
            add("kick", kick(), tt, 0.9)
            add("bass", bass(bass_notes[(i // 16) % len(bass_notes)] * 2, sx * 3.5), tt, 0.9)
        if pos in (4, 12):
            add("clap", clap(), tt, 0.8, 0.05)
        if pos % 2 == 0:
            add("hats", hat(pos == 14), tt, 0.7 if pos % 4 else 0.45, 0.3)
        elif pos in (3, 11, 15):
            add("hats", hat(), tt, 0.25, 0.3)
        i += 1


# ---------------------------------------------------------------------------- paper foley
def rip(d=0.32, bright=1.0):
    """Paper tear: band-limited noise, chopped by a fast random envelope, with fibre crackle on top."""
    t = t_(d)
    n = len(t)
    body = bp(noise(d), 600, 5200 * bright)
    rough = np.abs(lp(rng.standard_normal(n), 180, 2))
    rough /= rough.max()
    crack = np.zeros(n)
    idx = rng.integers(0, n, int(d * 900))
    crack[idx] = rng.uniform(-1, 1, len(idx))
    crack = bp(crack, 1800, 9000) * 6
    env = np.minimum(1, t / 0.015) * np.clip(1.15 - t / d, 0, 1) ** 0.6
    return (body * (0.35 + 1.2 * rough ** 1.5) + crack) * env * 0.5


def slap(weight=1.0):
    t = t_(0.18)
    thump = np.sin(2 * np.pi * (85 + 60 * np.exp(-t / 0.01)) * t) * np.exp(-t / 0.05) * 0.7 * weight
    flap = bp(noise(0.18), 300, 3500) * np.exp(-t / 0.025) * 0.8
    click = hp(noise(0.18), 3000) * np.exp(-t / 0.003) * 0.4
    return thump + flap + click


def tick():
    t = t_(0.03)
    return bp(noise(0.03), 2500, 7500) * np.exp(-t / 0.0025) * 0.5 + np.sin(2 * np.pi * 3100 * t) * np.exp(-t / 0.004) * 0.15


def whoosh(d=0.35, f0=300, f1=2500):
    t = t_(d)
    x = noise(d)
    out = np.zeros_like(x)
    k = 8                                     # band sweep as crossfaded fixed bands (no filter clicks)
    for j in range(k):
        fc = f0 * (f1 / f0) ** (j / (k - 1))
        w = np.exp(-0.5 * ((t / d - j / (k - 1)) / 0.16) ** 2)
        out += bp(x, fc * 0.7, min(fc * 1.4, SR / 2 - 100)) * w
    env = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2
    return out * env * 0.45


def riser(d=0.4):
    t = t_(d)
    w = whoosh(d, 400, 7000) * (t / d) ** 1.5 * 1.6
    tone = np.sin(2 * np.pi * np.cumsum(220 * 2 ** (2 * t / d)) / SR) * (t / d) ** 2 * 0.12
    return w + tone


def impact():
    t = t_(1.2)
    boom = np.sin(2 * np.pi * np.cumsum(30 + 45 * np.exp(-t / 0.06)) / SR) * np.exp(-t / 0.45)
    burst = lp(noise(1.2), 2500) * np.exp(-t / 0.08) * 0.6
    return np.tanh((boom + burst) * 1.5) * 0.9


def room(d):
    t = t_(d)
    ir = lp(rng.standard_normal(len(t)) * np.exp(-t / (d / 5)), 5000)
    return ir / np.sqrt((ir ** 2).sum())


def verb(x, ir, mix):
    wet = np.stack([fftconvolve(x[:, c], ir)[:len(x)] for c in (0, 1)], 1)
    return x + wet * mix


# ---------------------------------------------------------------------------- the cue
H = HOLD          # everything from the tear-out onwards moves later by the extra hold

# bar 1: the two lines, then the first rip into the groove
add("paper-slaps", slap(1.2), 0.0, 0.9)
add("kick", kick(True), 0.0, 0.8)
add("paper-slaps", slap(1.0), 0.4, 0.8, 0.1)
add("kick", kick(), 0.4, 0.6)
add("paper-rips", rip(0.36), 0.78, 1.0, -0.2)
add("whooshes-riser", whoosh(0.35, 250, 1800), 1.0, 0.7)
groove(0.8, 3.2)
for i in range(11):                        # the race clock
    add("clock-ticks", tick(), 1.0 + 0.2 * i, 0.35, 0.5)

# bar 3: second rip, record, digits stamped on sixteenths
add("paper-rips", rip(0.3, 1.2), 3.18, 1.0, 0.25)
add("whooshes-riser", whoosh(0.3, 300, 2200), 3.3, 0.6, -0.2)
add("synth-stabs", stab([E1 * 4, G1 * 4, B1 * 4]), 3.2, 0.9)
groove(3.2, 4.0)
add("paper-slaps", slap(0.8), 3.6, 0.8)
for i in range(7):
    add("paper-slaps", slap(0.9 if i % 3 != 1 else 0.6), 4.0 + 0.1 * i, 0.75, (i - 3) * 0.08)
    if i % 2 == 0:
        add("kick", kick(), 4.0 + 0.1 * i, 0.55)
for i in range(8):
    add("hats", hat(), 4.0 + 0.1 * i, 0.4, 0.3)
add("paper-slaps", slap(1.0), 4.8, 0.8)
add("kick", kick(), 4.8, 0.8)
add("whooshes-riser", riser(0.4), 4.8, 0.9)
add("paper-rips", rip(0.08, 1.4), 5.1, 0.8)

# the burst: impact, big rip, then the end card groove
add("impact", impact(), 5.2, 1.0)
add("paper-rips", rip(0.42, 0.9), 5.2, 1.0)
add("kick", kick(True), 5.2, 1.0)
add("synth-stabs", stab([E1 * 4, G1 * 4, B1 * 4, E1 * 8]), 5.2, 1.0)
add("whooshes-riser", whoosh(0.3, 200, 1500), 5.3, 0.6)
groove(5.6, 7.6 + H, (E1, E1, G1, D2 / 2))
add("paper-slaps", slap(1.2), 5.6, 0.9)
add("synth-stabs", stab([E1 * 4, B1 * 4]), 5.6, 0.7)
add("paper-slaps", slap(0.9), 6.0, 0.8, -0.15)
add("paper-slaps", slap(0.9), 6.2, 0.8, -0.1)
if args.tag:
    add("paper-slaps", slap(0.7), 6.4, 0.6, -0.3)

# out: final rip, last hit, let it ring
add("paper-rips", rip(0.36, 1.1), 7.58 + H, 1.0)
add("whooshes-riser", whoosh(0.3, 300, 2000), 7.7 + H, 0.7)
add("kick", kick(True), 7.6 + H, 1.0)
add("clap", clap(), 7.6 + H, 0.8)
add("synth-stabs", stab([E1 * 4, G1 * 4, B1 * 4, E1 * 8], 0.8), 7.6 + H, 1.0)

# ---------------------------------------------------------------------------- mix
# per stem: its group's room, music sits 2 dB under the foley, a soft-clip, DC/sub high-pass, the tail fade
fade = np.ones(N)
fade[int((7.75 + H) * SR):] = np.linspace(1, 0, N - int((7.75 + H) * SR))
ir_m, ir_f = room(0.8), room(0.6)
st = {}
for name in STEMS:
    music = name in MUSIC
    x = verb(bus[name], ir_m if music else ir_f, 0.12 if music else 0.10)[:N]
    st[name] = hp(np.tanh(x * (0.8 if music else 1.0) * 0.9), 28, 2) * fade[:, None]

# bus compressor keyed from the whole mix; the same gain rides every stem, so they still sum to the mix
mix = sum(st.values())
env = np.abs(mix).max(axis=1)
att, rel = np.exp(-1 / (0.002 * SR)), np.exp(-1 / (0.09 * SR))
fol = np.empty(N)
e = 0.0
for i, v in enumerate(env):
    e = att * e + (1 - att) * v if v > e else rel * e + (1 - rel) * v
    fol[i] = e
thr, ratio = 0.75, 3.0
gain = np.where(fol > thr, (thr / np.maximum(fol, 1e-9)) ** (1 - 1 / ratio), 1.0)
print(f"bus comp: max gain reduction {-20 * np.log10(gain.min()):.1f} dB, "
      f"{(gain < 0.89).mean() * 100:.0f}% of the time over 1 dB")
for name in STEMS:
    st[name] *= gain[:, None]
mix = sum(st.values())

# one loudness gain for everything: the mix lands at -14 LUFS (the limiter in build.sh only shaves peaks)
sf.write("mix_probe.wav", mix.astype(np.float32), SR, subtype="FLOAT")
meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", "mix_probe.wav", "-af",
                       "loudnorm=I=-14:TP=-1.5:print_format=json", "-f", "null", "-"],
                      capture_output=True, text=True).stderr
lufs = float(json.loads(meas[meas.index("{"):meas.rindex("}") + 1])["input_i"])
g = 10 ** ((-14 - lufs) / 20)
os.remove("mix_probe.wav")

os.makedirs("stems", exist_ok=True)
for f in os.listdir("stems"):
    os.remove(os.path.join("stems", f))
peaks = {}
for i, name in enumerate(STEMS, 1):
    y = st[name] * g
    peaks[name] = 20 * np.log10(np.abs(y).max() + 1e-12)
    sf.write(f"stems/{i:02d}_{name}.wav", y.astype(np.float32), SR, subtype="PCM_24")
sf.write("mix_full.wav", (mix * g).astype(np.float32), SR, subtype="FLOAT")
print(f"mix measured {lufs:.1f} LUFS -> gain {20 * np.log10(g):+.1f} dB; "
      f"mix peak {20 * np.log10(np.abs(mix * g).max()):.1f} dBFS before the limiter")
print("stem peaks (dBFS): " + ", ".join(f"{k} {v:.1f}" for k, v in peaks.items()))
