"""Shared synthesis helpers for the intro's sound: filters, noise, and the paper foley
(rips, slaps, clock ticks, whooshes, the burst impact, a short room).

Everything here draws from one seeded generator (`rng`), so a cue that calls these
in the same order always renders the same sound.
"""
import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

SR = 48000
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

