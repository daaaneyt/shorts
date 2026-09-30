"""Synthesize a soft music bed + whooshes and mix them under the processed voice.

Writes mix_music.wav (voice + bed + whooshes) and mix_voice.wav (voice + whooshes).
Both are un-normalized; loudness is set afterwards with a two-pass loudnorm.
"""
import json
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000
rng = np.random.default_rng(7)
voice, sr = sf.read("voice_proc.wav", dtype="float64")
assert sr == SR
N = len(voice)
DUR = N / SR


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def env_adsr(n, a, r, sus=1.0):
    e = np.full(n, sus)
    na, nr = int(a * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na) ** 2 * sus if na else e[:na]
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr) ** 1.5
    return e


def pad_voice(freq, n, detune_cents, phase):
    """Warm band-limited saw via additive synthesis with a steep spectral tilt."""
    t = np.arange(n) / SR
    f = freq * 2 ** (detune_cents / 1200)
    out = np.zeros(n)
    k = 1
    while k * f < 5000 and k <= 24:
        amp = (1 / k) * np.exp(-k * f / 900.0)
        out += amp * np.sin(2 * np.pi * k * f * t + phase * k)
        k += 1
    return out


# ---- progression: Fmaj7 - G6 - Em7 - Am7 (IV-V-iii-vi in C), 2 bars each at 88 bpm
BPM = 88
BEAT = 60 / BPM
CHORD_LEN = 8 * BEAT
CHORDS = [
    (41, [53, 57, 60, 64]),   # Fmaj7
    (43, [55, 59, 62, 64]),   # G6
    (40, [52, 55, 59, 62]),   # Em7
    (45, [57, 60, 64, 67]),   # Am7
]
ARP = [0, 1, 2, 3, 2, 1, 2, 3]  # indices into the chord (up an octave), 8th notes

n_chords = int(np.ceil(DUR / CHORD_LEN)) + 1
L = np.zeros(int((n_chords + 1) * CHORD_LEN * SR) + SR * 4)
R = np.zeros_like(L)
for ci in range(n_chords):
    root, notes = CHORDS[ci % 4]
    t0 = ci * CHORD_LEN
    i0 = int(t0 * SR)
    n = int((CHORD_LEN + 1.6) * SR)          # overlap into next chord for smooth changes
    e = env_adsr(n, 1.1, 1.8)
    for m in notes:
        for d, side in [(-7, "L"), (0, "C"), (6, "R")]:
            v = pad_voice(midi_hz(m), n, d, rng.uniform(0, 2 * np.pi)) * e * 0.05
            if side in "LC":
                L[i0:i0 + n] += v * (1.0 if side == "L" else 0.7)
            if side in "RC":
                R[i0:i0 + n] += v * (1.0 if side == "R" else 0.7)
    # soft bass
    tb = np.arange(n) / SR
    bass = (np.sin(2 * np.pi * midi_hz(root) * tb) + 0.25 * np.sin(4 * np.pi * midi_hz(root) * tb)) * e * 0.09
    L[i0:i0 + n] += bass
    R[i0:i0 + n] += bass
    # gentle plucked arpeggio (felt-piano-ish), panned slightly
    for k in range(16):
        tt = t0 + k * BEAT / 2
        j0 = int(tt * SR)
        nn = int(1.4 * SR)
        m = notes[ARP[k % 8]] + 12
        tp = np.arange(nn) / SR
        f = midi_hz(m)
        pl = (np.sin(2 * np.pi * f * tp) + 0.18 * np.sin(4 * np.pi * f * tp) + 0.05 * np.sin(6 * np.pi * f * tp))
        pl *= np.exp(-tp / 0.32) * np.minimum(1, tp / 0.004)
        vel = 0.030 * (1.0 if k % 4 == 0 else 0.75) * rng.uniform(0.85, 1.05)
        pan = 0.5 + 0.25 * np.sin(k * 0.9)
        L[j0:j0 + nn] += pl * vel * (1 - pan) * 1.4
        R[j0:j0 + nn] += pl * vel * pan * 1.4

bed = np.stack([L, R], 1)[:N + SR * 3]

# ---- reverb: decaying decorrelated noise IR
ir_len = int(2.6 * SR)
ti = np.arange(ir_len) / SR
ir = rng.standard_normal((ir_len, 2)) * np.exp(-ti / 0.55)[:, None]
ir = sosfilt(butter(2, 5000, "low", fs=SR, output="sos"), ir, axis=0)
ir /= np.sqrt((ir ** 2).sum(0))
wet = np.stack([fftconvolve(bed[:, c], ir[:, c])[:len(bed)] for c in range(2)], 1)
bed = 0.65 * bed + 0.55 * wet

# ---- tone the bed so it sits under speech: HPF, gentle LPF, dip the speech band
bed = sosfilt(butter(2, 70, "high", fs=SR, output="sos"), bed, axis=0)
bed = sosfilt(butter(2, 6500, "low", fs=SR, output="sos"), bed, axis=0)
band = sosfilt(butter(2, [900, 4000], "band", fs=SR, output="sos"), bed, axis=0)
bed = bed - 0.45 * band
bed = bed[:N]

# ---- ducking from the voice envelope
v = np.abs(voice)
win = int(0.03 * SR)
venv = np.sqrt(np.convolve(v ** 2, np.ones(win) / win, mode="same"))
active = (20 * np.log10(venv + 1e-9) > -45).astype(float)
# smooth: fast attack (~80 ms), slow release (~450 ms)
g = np.zeros(N)
a_att, a_rel = np.exp(-1 / (0.08 * SR)), np.exp(-1 / (0.45 * SR))
st = 0.0
step = 48
for i in range(0, N, step):
    tgt = active[i]
    coef = a_att if tgt > st else a_rel
    st = tgt + (st - tgt) * coef ** step
    g[i:i + step] = st
duck = 10 ** ((-5.0 * g) / 20)          # up to 5 dB extra dip while speaking

# fade in/out
fade = np.ones(N)
fi, fo = int(0.8 * SR), int(0.9 * SR)
fade[:fi] = np.linspace(0, 1, fi) ** 2
fade[-fo:] = np.linspace(1, 0, fo) ** 2
bed *= (duck * fade)[:, None]

# ---- set bed level: ~21 dB under the voice (RMS over speech)
vr = np.sqrt((voice[active > 0] ** 2).mean())
br = np.sqrt((bed[active > 0] ** 2).mean())
bed *= (vr / br) * 10 ** (-21 / 20)

# ---- whooshes on B-roll card entrances
import render_times
wh = np.zeros((N, 2))
for t_in, strength in render_times.WHOOSH:
    n = int(0.55 * SR)
    noise = rng.standard_normal((n, 2))
    tt = np.arange(n) / n
    out = np.zeros((n, 2))
    # sweep a band-pass up through the noise, block-wise
    blocks = 22
    for b in range(blocks):
        s0, s1 = b * n // blocks, (b + 1) * n // blocks
        fc = 350 * (9 ** (b / blocks))
        sos = butter(2, [fc * 0.6, min(fc * 1.7, 20000)], "band", fs=SR, output="sos")
        seg = sosfilt(sos, noise[max(0, s0 - 2000):s1], axis=0)[-(s1 - s0):]
        out[s0:s1] = seg
    envw = np.sin(np.pi * np.clip(tt / 0.75, 0, 1)) ** 2 * np.exp(-3 * np.clip(tt - 0.4, 0, None))
    pan = np.stack([1 - 0.35 * tt, 0.65 + 0.35 * tt], 1)
    out *= envw[:, None] * pan
    out = out / (np.abs(out).max() + 1e-9)
    i0 = int((t_in - 0.22) * SR)
    i1 = min(N, i0 + n)
    wh[i0:i1] += out[:i1 - i0] * strength
wh *= vr * 10 ** (-17 / 20) / 0.35

vst = np.stack([voice, voice], 1)
sf.write("mix_music.wav", vst + bed + wh, SR, subtype="FLOAT")
sf.write("mix_voice.wav", vst + wh, SR, subtype="FLOAT")
print("bed rms vs voice (dB):", 20 * np.log10(np.sqrt((bed ** 2).mean()) / np.sqrt((voice ** 2).mean())))
