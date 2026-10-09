"""Music mode audio: a supplied track plus paper foley, locked to the picture.

  1. Decode the supplied track, trim it to the picture's length and fade the long
     reverb tail out under the final tear. Nothing else is done to it: no EQ, no
     compression, one gain.
  2. Synthesise the paper foley (rips, slaps, stamps, clock ticks, whooshes, the
     burst impact) at the same step times the renderer uses (timing.py).
  3. Set one gain on the track so music + foley lands at -14 LUFS. The foley sits
     at fixed levels under it.

Writes stems_v3/ (the track and the five foley stems, 24-bit, all the same length
and starting at 0, so they sum to the mix) and mix_full.wav (float, pre-limiter).

  python3 foley.py --music assets/music_source.mp4 --sync music_sync.json [--hold 1.2] [--tag]
"""
import argparse, json, os, shutil, subprocess, tempfile
import numpy as np, soundfile as sf
from synth import *
import timing

ap = argparse.ArgumentParser()
ap.add_argument("--music", required=True)
ap.add_argument("--sync", required=True)
ap.add_argument("--hold", type=float, default=None)
ap.add_argument("--tag", action="store_true", help="the end card has an episode tag (adds its slap)")
ap.add_argument("--foley-db", type=float, default=-9.0,
                help="foley level against the synthesised v2 cue (-9 keeps its peaks about 6 dB under the track's)")
ap.add_argument("--fade-from", type=float, default=9.0, help="start of the music's fade-out (s)")
ap.add_argument("--out", default="stems_v3")
args = ap.parse_args()

grid = timing.Grid(args.sync)
C = timing.constants(True, None if args.hold is None else round(args.hold * 10) / 10)
R = grid.real                                       # internal seconds -> real seconds
NF = round(R(C["DUR"]) * 30)                        # the picture's frame count
DUR = NF / 30
N = int(round(DUR * SR))
RUN0 = round(C["T_RIP1"] + 0.2, 1)

# ---------------------------------------------------------------------------- the track
with tempfile.TemporaryDirectory() as td:
    wav = os.path.join(td, "m.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", args.music, "-ar", str(SR), "-c:a", "pcm_f32le", wav],
                   check=True)
    music, sr = sf.read(wav)
if music.ndim == 1:
    music = np.stack([music, music], 1)
music = music[:N]
if len(music) < N:
    music = np.vstack([music, np.zeros((N - len(music), 2))])
f0 = int(args.fade_from * SR)
music[f0:] *= (0.5 + 0.5 * np.cos(np.pi * np.linspace(0, 1, N - f0)))[:, None]   # cosine fade to silence at the end
music[-int(0.01 * SR):] *= np.linspace(1, 0, int(0.01 * SR))[:, None]

# ---------------------------------------------------------------------------- the foley
STEMS = ["paper-rips", "paper-slaps", "clock-ticks", "whooshes-riser", "impact"]
bus = {name: np.zeros((N + SR, 2)) for name in STEMS}


def add(stem, sig, t_internal, gain=1.0, pan=0.0, early=0.0):
    """Place a sound at an internal event time (mapped to the track's grid), `early` seconds ahead of it."""
    x = bus[stem]
    i = max(0, int(round((R(t_internal) - early) * SR)))
    if sig.ndim == 1:
        sig = np.stack([sig * np.sqrt(0.5 * (1 - pan)), sig * np.sqrt(0.5 * (1 + pan))], 1) * np.sqrt(2)
    n = min(len(sig), len(x) - i)
    x[i:i + n] += sig[:n] * gain


T = C
# the two lines land on the roll's accents
add("paper-slaps", slap(1.2), 0.0, 0.9)
add("paper-slaps", slap(1.0), T["T_LINE2"], 0.8, 0.1)
# rip 1: the crack runs across on the roll, the sheet tears open on the drop
add("paper-rips", rip(0.36), T["T_RIP1"], 1.0, -0.2, early=0.02)
add("paper-rips", rip(0.28, 1.3), T["T_RIP1"] + 0.3, 0.7, 0.2)
add("whooshes-riser", whoosh(0.35, 250, 1800), T["T_RIP1"] + 0.3, 0.7)
# the race clock ticks every other step under the run
for i in range(int(round((T["T_RIP2"] - RUN0) / 0.2))):
    add("clock-ticks", tick(), RUN0 + 0.2 * i, 0.35, 0.5)
# rip 2, then the record
add("paper-rips", rip(0.3, 1.2), T["T_RIP2"], 1.0, 0.25, early=0.02)
add("whooshes-riser", whoosh(0.3, 300, 2200), T["T_RIP2"] + 0.1, 0.6, -0.2)
add("paper-slaps", slap(0.8), T["T_EYEBROW"], 0.8)
for i in range(7):                                  # 2 : 3 8 : 2 1, one slap a step
    add("paper-slaps", slap(0.9 if i % 3 != 1 else 0.6), T["T_DIGITS"] + 0.1 * i, 0.75, (i - 3) * 0.08)
add("paper-slaps", slap(1.0), T["T_TOBEAT"], 0.8)
add("whooshes-riser", riser(R(T["T_BURST"]) - R(T["T_TOBEAT"])), T["T_TOBEAT"], 0.9)   # builds into the burst
add("paper-rips", rip(0.08, 1.4), T["T_CRACK"], 0.8)
# the burst
add("impact", impact(), T["T_BURST"], 0.6)
add("paper-rips", rip(0.42, 0.9), T["T_BURST"], 1.0)
add("whooshes-riser", whoosh(0.3, 200, 1500), T["T_BURST"] + 0.1, 0.6)
# the end card
add("paper-slaps", slap(1.2), T["T_WORD"], 0.9)
add("paper-slaps", slap(0.9), T["T_STRIP1"], 0.8, -0.15)
add("paper-slaps", slap(0.9), T["T_STRIP2"], 0.8, -0.1)
if args.tag:
    add("paper-slaps", slap(0.7), T["T_LABEL"], 0.6, -0.3)
# the last tear
add("paper-rips", rip(0.36, 1.1), T["T_OUT"], 1.0, early=0.02)
add("whooshes-riser", whoosh(0.3, 300, 2000), T["T_OUT"] + 0.1, 0.7)

ir_f = room(0.6)
end_fade = np.ones(N)
end_fade[-int(0.02 * SR):] = np.linspace(1, 0, int(0.02 * SR))
fgain = 10 ** (args.foley_db / 20)
foley = {}
for name in STEMS:
    x = verb(bus[name], ir_f, 0.10)[:N]
    foley[name] = hp(np.tanh(x * 0.9), 28, 2) * end_fade[:, None] * fgain
fsum = sum(foley.values())


# ---------------------------------------------------------------------------- level: one gain on the track
def lufs_of(y):
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "p.wav")
        sf.write(p, y.astype(np.float32), SR, subtype="FLOAT")
        m = subprocess.run(["ffmpeg", "-hide_banner", "-i", p, "-af", "loudnorm=I=-14:TP=-1.5:print_format=json",
                            "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(json.loads(m[m.index("{"):m.rindex("}") + 1])["input_i"])


gm = 1.0
for _ in range(4):
    L = lufs_of(music * gm + fsum)
    gm *= 10 ** ((-14 - L) / 20)
mix = music * gm + fsum
print(f"music gain {20 * np.log10(gm):+.1f} dB -> mix {lufs_of(mix):.1f} LUFS, "
      f"mix peak {20 * np.log10(np.abs(mix).max()):.1f} dBFS (the limiter in build.sh only shaves peaks)")
print(f"music alone: {lufs_of(music * gm):.1f} LUFS, peak {20 * np.log10(np.abs(music * gm).max()):.1f} dBFS")

# how the foley sits against the track in the 1-6 kHz band where paper lives: RMS over 100 ms around each peak
from scipy.signal import butter, sosfilt
sos = butter(4, [1000, 6000], "bandpass", fs=SR, output="sos")
mb = sosfilt(sos, (music * gm).mean(1))
w = int(0.05 * SR)
print("foley vs track (1-6 kHz band, RMS over 100 ms at each stem's loudest moment):")
for name in STEMS:
    fb = sosfilt(sos, foley[name].mean(1))
    i = int(np.argmax(np.abs(fb)))
    r = lambda a: np.sqrt((a[max(0, i - w): i + w] ** 2).mean()) + 1e-9
    print(f"  {name:15s} at {i / SR:5.2f} s: {20 * np.log10(r(fb) / r(mb)):+5.1f} dB   "
          f"(peak {20 * np.log10(np.abs(foley[name]).max()):.1f} dBFS)")

shutil.rmtree(args.out, ignore_errors=True)
os.makedirs(args.out)
sf.write(f"{args.out}/01_music.wav", (music * gm).astype(np.float32), SR, subtype="PCM_24")
for i, name in enumerate(STEMS, 2):
    sf.write(f"{args.out}/{i:02d}_{name}.wav", foley[name].astype(np.float32), SR, subtype="PCM_24")
sf.write("mix_full.wav", mix.astype(np.float32), SR, subtype="FLOAT")
print(f"wrote {args.out}/ (6 stems, {DUR:.3f} s) and mix_full.wav")
