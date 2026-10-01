"""Synthesise the intro's sound: a 150 bpm drum + bass groove and paper foley
(rips, slaps, digit stamps, the burst-through impact), locked to render.py's
timeline. Everything is generated here, so there is nothing to license.

Writes mix_full.wav (music + foley) and mix_sfx.wav (foley only, for laying
under your own music). build.sh loudness-normalises both.
"""
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt

SR = 48000
DUR = 8.0
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


class Bus:
    def __init__(self):
        self.x = np.zeros((N + SR, 2))

    def add(self, sig, at, gain=1.0, pan=0.0):
        i = int(at * SR)
        if sig.ndim == 1:
            sig = np.stack([sig * np.sqrt(0.5 * (1 - pan)), sig * np.sqrt(0.5 * (1 + pan))], 1) * np.sqrt(2)
        n = min(len(sig), len(self.x) - i)
        self.x[i:i + n] += sig[:n] * gain


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


def groove(bus, start, end, bass_notes=(E1, E1, G1, A1)):
    """One bar = 16 sixteenths. Kick on 1 and the 'and' of 2 and 3, clap on 2 and 4, hats on the 8ths."""
    sx = BEAT / 4
    kicks = {0, 6, 8}
    i = 0
    while start + i * sx < end - 1e-6:
        tt = start + i * sx
        pos = i % 16
        if pos in kicks:
            bus.add(kick(), tt, 0.9)
            bus.add(bass(bass_notes[(i // 16) % len(bass_notes)] * 2, sx * 3.5), tt, 0.9)
        if pos in (4, 12):
            bus.add(clap(), tt, 0.8, 0.05)
        if pos % 2 == 0:
            bus.add(hat(pos == 14), tt, 0.7 if pos % 4 else 0.45, 0.3)
        elif pos in (3, 11, 15):
            bus.add(hat(), tt, 0.25, 0.3)
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


def verb(x, d=0.9, mix=0.18):
    t = t_(d)
    ir = rng.standard_normal(len(t)) * np.exp(-t / (d / 5))
    ir = lp(ir, 5000)
    ir /= np.sqrt((ir ** 2).sum())
    wet = np.stack([np.convolve(x[:, c], ir)[:len(x)] for c in (0, 1)], 1)
    return x + wet * mix


# ---------------------------------------------------------------------------- the cue
music, sfx = Bus(), Bus()

# bar 1: the two lines, then the first rip into the groove
sfx.add(slap(1.2), 0.0, 0.9)
music.add(kick(True), 0.0, 0.8)
sfx.add(slap(1.0), 0.4, 0.8, 0.1)
music.add(kick(), 0.4, 0.6)
sfx.add(rip(0.36), 0.78, 1.0, -0.2)
sfx.add(whoosh(0.35, 250, 1800), 1.0, 0.7)
groove(music, 0.8, 3.2)
for i in range(11):                        # the race clock
    sfx.add(tick(), 1.0 + 0.2 * i, 0.35, 0.5)

# bar 3: second rip, record, digits stamped on sixteenths
sfx.add(rip(0.3, 1.2), 3.18, 1.0, 0.25)
sfx.add(whoosh(0.3, 300, 2200), 3.3, 0.6, -0.2)
music.add(stab([E1 * 4, G1 * 4, B1 * 4]), 3.2, 0.9)
groove(music, 3.2, 4.0)
sfx.add(slap(0.8), 3.6, 0.8)
for i in range(7):
    sfx.add(slap(0.9 if i % 3 != 1 else 0.6), 4.0 + 0.1 * i, 0.75, (i - 3) * 0.08)
    if i % 2 == 0:
        music.add(kick(), 4.0 + 0.1 * i, 0.55)
for i in range(8):
    music.add(hat(), 4.0 + 0.1 * i, 0.4, 0.3)
sfx.add(slap(1.0), 4.8, 0.8)
music.add(kick(), 4.8, 0.8)
sfx.add(riser(0.4), 4.8, 0.9)
sfx.add(rip(0.08, 1.4), 5.1, 0.8)

# the burst: impact, big rip, then the end card groove
sfx.add(impact(), 5.2, 1.0)
sfx.add(rip(0.42, 0.9), 5.2, 1.0)
music.add(kick(True), 5.2, 1.0)
music.add(stab([E1 * 4, G1 * 4, B1 * 4, E1 * 8]), 5.2, 1.0)
sfx.add(whoosh(0.3, 200, 1500), 5.3, 0.6)
groove(music, 5.6, 7.6, (E1, E1, G1, D2 / 2))
sfx.add(slap(1.2), 5.6, 0.9)
music.add(stab([E1 * 4, B1 * 4]), 5.6, 0.7)
sfx.add(slap(0.9), 6.0, 0.8, -0.15)
sfx.add(slap(0.9), 6.2, 0.8, -0.1)
sfx.add(slap(0.7), 6.4, 0.6, -0.3)

# out: final rip, last hit, let it ring
sfx.add(rip(0.36, 1.1), 7.58, 1.0)
sfx.add(whoosh(0.3, 300, 2000), 7.7, 0.7)
music.add(kick(True), 7.6, 1.0)
music.add(clap(), 7.6, 0.8)
music.add(stab([E1 * 4, G1 * 4, B1 * 4, E1 * 8], 0.8), 7.6, 1.0)

# a short room on both, soft-clip, and fade the tail
m = verb(music.x, 0.8, 0.12)
f = verb(sfx.x, 0.6, 0.10)
fade = np.ones(len(m))
fade[int(7.75 * SR):int(8.0 * SR)] = np.linspace(1, 0, int(0.25 * SR))
fade[int(8.0 * SR):] = 0
full = hp(np.tanh((m * 0.8 + f) * 0.9)[:N], 28, 2) * fade[:N, None]
only = hp(np.tanh(f * 0.9)[:N], 28, 2) * fade[:N, None]
sf.write("mix_full.wav", (full / np.abs(full).max() * 0.8).astype(np.float32), SR, subtype="FLOAT")
sf.write("mix_sfx.wav", (only / np.abs(only).max() * 0.8).astype(np.float32), SR, subtype="FLOAT")
print("wrote mix_full.wav, mix_sfx.wav")
