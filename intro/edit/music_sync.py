"""Find the musical grid of a supplied track and write music_sync.json.

The intro's animation moves in "steps", and in music mode each step is one 16th
note of the track. This script finds that grid:

  1. Decode the track and compute per-band onset strength (kick, body, backbeat,
     hats) on a 5 ms hop.
  2. Brute-force the 16th-note length and phase that best line up with those
     onsets, with step 0 forced to be the first hit of the opening roll.
  3. Refine the phase against the real transient attacks (a spectrogram-based
     detector reads a few ms early), using the strong hits on the grid.

Usage:  python3 music_sync.py assets/music_source.mp4 [music_sync.json]
Needs:  ffmpeg, numpy, scipy, soundfile.
"""
import json, os, subprocess, sys, tempfile
import numpy as np, soundfile as sf
from scipy.signal import butter, find_peaks, medfilt, sosfilt, stft

src = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else "music_sync.json"

with tempfile.TemporaryDirectory() as td:
    wav = os.path.join(td, "a.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-ar", "48000", "-c:a", "pcm_f32le", wav], check=True)
    x, sr = sf.read(wav)
m = x.mean(1) if x.ndim > 1 else x

hop = 240                                           # 5 ms
f, t, Z = stft(m, sr, nperseg=2048, noverlap=2048 - hop)
A = np.abs(Z)


def flux(lo, hi):
    L = np.log1p(A[(f >= lo) & (f < hi)] * 60)
    fl = np.concatenate([[0], np.maximum(0, np.diff(L, axis=1)).sum(0)])
    fl /= np.percentile(fl, 99) + 1e-9
    return np.maximum(fl - 0.9 * medfilt(fl, 41), 0)


comb = flux(40, 160) + 0.6 * flux(160, 900) + flux(900, 4000) + 0.5 * flux(6000, 16000)
dt = t[1] - t[0]


def score(S, g0, n=73):
    idx = np.clip(np.round((g0 + S * np.arange(n)) / dt).astype(int), 1, len(t) - 2)
    return sum(comb[i - 1:i + 2].max() for i in idx)


best = max(((score(S, g), S, g) for S in np.arange(0.100, 0.125, 0.0001) for g in np.arange(0.03, 0.09, 0.004)))
_, S, g0 = best
best = max(((score(s, g), s, g) for s in np.arange(S - 0.0003, S + 0.0003, 0.00001)
            for g in np.arange(g0 - 0.004, g0 + 0.004, 0.0005)))
_, S, g0 = best

# refine against the real attack of each strong hit: the steepest rise of a 1-6 kHz envelope (0.5 ms hop)
sos = butter(4, [1000, 6000], "bandpass", fs=sr, output="sos")
band = np.abs(sosfilt(sos, m))
h2 = int(0.0005 * sr)
env = np.convolve(band, np.ones(h2 * 4) / (h2 * 4), "same")[::h2]
tt = np.arange(len(env)) * h2 / sr
d = np.gradient(np.log(env + 1e-5))
offs, hits = [], []
pk, _ = find_peaks(comb, height=1.3, distance=int(0.05 / dt))
for i in pk:
    n = round((t[i] - g0) / S)
    if 0 <= n <= 72 and abs((t[i] - g0) / S - n) < 0.25:
        c = g0 + n * S
        w = (tt > c - 0.03) & (tt < c + 0.04)
        att = tt[w][np.argmax(d[w])]
        offs.append(att - c)
        hits.append((int(n), round(float(t[i]), 3), round(float(comb[i]), 1)))
delta = float(np.median(offs))
g0 += delta
print(f"16th = {S:.5f} s ({60 / (4 * S):.2f} bpm), bar = {16 * S:.4f} s")
print(f"phase refined by {delta * 1000:+.1f} ms against {len(offs)} attacks -> g0 = {g0:.4f} s "
      f"(spread {np.std(offs) * 1000:.1f} ms)")
for n in (0, 4, 8, 24, 40, 56, 72, 88):
    print(f"  step {n:3d} = {g0 + S * n:7.3f} s")

json.dump({"source": os.path.basename(src), "step": round(float(S), 6), "g0": round(float(g0), 4),
           "bpm": round(60 / (4 * S), 2), "drop_step": 8, "phrase_end_step": 72,
           "note": "step n happens at g0 + n*step; step 0 is the first hit of the opening roll, step 8 the drop"},
          open(out, "w"), indent=1)
print("wrote", out)
