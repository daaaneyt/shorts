"""Sound design for the sub3piece intro, synthesised from scratch.

Every event time comes from events.json, which render.cjs exports from the
same race clock the picture uses, so each tick, km click, lock and note lands on
the frame it belongs to.

Layers
  open    hairline draw (air), playhead tink, label type clicks, reel ratchet
  run     stopwatch start, second ticks (only while they're slower than ~25/s),
          km ratchet (one click per km marker crossing the playhead), the
          spinning-drum whir whose pitch follows the clock speed, a sub pulse
          on the 150 BPM beat and a low fifth that opens with the speed
  stop    stopwatch stop, low impact, photo-finish shimmer; everything else
          cuts dead so the frozen 2:59:59 sits in its own reverb tail
  pieces  three whooshes (right to left, with the bands) and three latches,
          each playing one note of the sonic logo: E5, B5, F#6 (stacked
          fifths) which resolve onto D at the logo as a D6/9 chord
Output: 48 kHz 24-bit stereo WAV, about -16 LUFS integrated, -1 dBTP ceiling.

Usage: python3 sound.py [events.json] [out.wav]
"""
import json, sys
import numpy as np
from scipy import signal

SR = 48000
ev = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "events.json"))
OUT = sys.argv[2] if len(sys.argv) > 2 else "intro_audio.wav"
T = ev["T"]
DUR = T["end"]
N = int(round(DUR * SR))
rng = np.random.default_rng(3)
t_axis = np.arange(N) / SR

dry = np.zeros((N, 2))
send = np.zeros((N, 2))      # to the reverb


def db(x):
    return 10 ** (x / 20)


def pan_gains(p):            # equal-power, p in [-1, 1]
    a = (p + 1) * np.pi / 4
    return np.cos(a), np.sin(a)


def place(buf, x, t0, gain=1.0, pan=0.0, rev=0.0):
    """Add mono (or stereo) x into the mix at time t0 (seconds)."""
    i0 = int(round(t0 * SR))
    if i0 >= N:
        return
    if x.ndim == 1:
        l, r = pan_gains(pan)
        x = np.stack([x * l, x * r], 1)
    if i0 < 0:
        x, i0 = x[-i0:], 0
    n = min(len(x), N - i0)
    buf[i0:i0 + n] += x[:n] * gain
    if rev:
        send[i0:i0 + n] += x[:n] * gain * rev


def bp(x, f, q):
    b, a = signal.iirpeak(min(f, SR * 0.45) / (SR / 2), q)
    return signal.lfilter(b, a, x)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f / (SR / 2), "high", output="sos"), x)


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, min(f, SR * 0.45) / (SR / 2), "low", output="sos"), x)


def tv_bandpass(x, fc, q, block=128):
    """Band-pass whose centre follows fc (array, Hz); coefficients per block."""
    y = np.zeros_like(x)
    zi = np.zeros(2)
    for i in range(0, len(x), block):
        f = float(np.clip(fc[min(i + block // 2, len(fc) - 1)], 30, SR * 0.45))
        w = 2 * np.pi * f / SR
        al = np.sin(w) / (2 * q)
        b = np.array([al, 0, -al]) / (1 + al)
        a = np.array([1, -2 * np.cos(w) / (1 + al), (1 - al) / (1 + al)])
        y[i:i + block], zi = signal.lfilter(b, a, x[i:i + block], zi=zi)
    return y


def env_exp(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


# ---------------------------------------------------------------- sources
def click(f1=3200, f2=6900, tau=0.0025, ring=0.0, ring_f=1900, ring_tau=0.03, dur=0.05, seed=None):
    """Mechanical click: a noise impulse through two resonances, optional ring."""
    r = np.random.default_rng(seed)
    n = int(dur * SR)
    x = r.standard_normal(n) * env_exp(n, tau)
    y = bp(x, f1, 9) + 0.7 * bp(x, f2, 7) + 0.25 * hp(x, 7000)
    if ring:
        y += ring * np.sin(2 * np.pi * ring_f * np.arange(n) / SR) * env_exp(n, ring_tau)
    y[:16] *= np.linspace(0, 1, 16)
    return y / (np.abs(y).max() + 1e-9)


def thump(f0=58, f1=40, tau=0.16, dur=0.6, drive=1.3):
    """Soft sub hit: a sine falling in pitch."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-tt / 0.05)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.tanh(drive * np.sin(ph)) / np.tanh(drive) * env_exp(n, tau)
    y[:48] *= np.linspace(0, 1, 48)
    return y


def mallet(freq, dur=1.6, tau=0.55, bright=1.0):
    """Soft vibraphone-like bar: fundamental + inharmonic bar partials."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    y = np.sin(2 * np.pi * freq * tt) * np.exp(-tt / tau)
    y += 0.22 * bright * np.sin(2 * np.pi * freq * 3.99 * tt) * np.exp(-tt / (tau * 0.18))
    y += 0.06 * bright * np.sin(2 * np.pi * freq * 9.6 * tt) * np.exp(-tt / (tau * 0.06))
    y += 0.10 * np.sin(2 * np.pi * freq * 2.0 * tt) * np.exp(-tt / (tau * 0.35))
    a = int(0.002 * SR)
    y[:a] *= np.linspace(0, 1, a)
    return y


def pad(freqs, dur, attack, release_tau, cutoff=1800, detune=0.0035, seed=0):
    """Warm detuned saw pad (band-limited by a low-pass)."""
    r = np.random.default_rng(seed)
    n = int(dur * SR)
    tt = np.arange(n) / SR
    y = np.zeros(n)
    for f in freqs:
        for d in (-detune, 0, detune):
            ph = r.uniform(0, 1)
            saw = 2 * ((f * (1 + d) * tt + ph) % 1) - 1
            y += saw
    y = lp(y, cutoff, 4)
    e = np.minimum(1, tt / attack) * np.exp(-np.maximum(0, tt - attack) / release_tau)
    return y * e / (len(freqs) * 3)


def noise(n, seed=None):
    return np.random.default_rng(seed).standard_normal(n)


def whoosh(t0, t1, pan0=0.8, pan1=-0.8, f0=900, f1=4200, seed=0):
    """Air swipe whose loudness follows the band's speed profile."""
    n = int((t1 - t0 + 0.25) * SR)
    tt = np.arange(n) / SR
    u = np.clip(tt / (t1 - t0), 0, 1)
    sp = np.sin(np.pi * u) ** 2 * (tt <= (t1 - t0))
    sp += (tt > (t1 - t0)) * 0  # tail via reverb only
    x = noise(n, seed)
    # time-varying band-pass by summing three fixed bands weighted by speed
    lo, mid, hi_ = bp(x, f0, 1.4), bp(x, (f0 * f1) ** 0.5, 1.6), bp(x, f1, 1.8)
    y = lo * (1 - sp) * 0.6 + mid * sp + hi_ * sp ** 2 * 0.8
    y *= sp
    p = pan0 + (pan1 - pan0) * u
    l, r = pan_gains(p)
    return np.stack([y * l, y * r], 1) / (np.abs(y).max() + 1e-9)


# ---------------------------------------------------------------- the open
# hairline draws outward: a widening air sweep
n = int(0.5 * SR)
tt = np.arange(n) / SR
air_l, air_r = noise(n, 11), noise(n, 12)
sweep_e = np.sin(np.pi * np.clip(tt / 0.46, 0, 1)) ** 1.5
air = []
for ch, src in enumerate((air_l, air_r)):
    y = 0.6 * bp(src, 2600, 1.2) + 0.4 * bp(src, 5200, 1.5)
    air.append(y)
mid = (air[0] + air[1]) / 2
side = (air[0] - air[1]) / 2
width = np.clip(tt / 0.46, 0, 1)
L = (mid + side * width) * sweep_e
R = (mid - side * width) * sweep_e
air_st = np.stack([L, R], 1) / np.abs(np.stack([L, R], 1)).max()
place(dry, air_st, T["lineIn"][0], db(-35), rev=0.4)

# playhead appears: a small high tink
tink = mallet(3520, dur=0.4, tau=0.08, bright=0.3)
place(dry, tink, T["playIn"][0], db(-34), rev=0.6)

# corner labels type on: whisper clicks, panned to their corners
labels = [("LONDON MARATHON 2027", T["labelsIn"], -0.7),
          ("TARGET  SUB 3:00:00", T["labelsIn"] + 0.05, 0.7),
          ("Z2  TRAIN", T["labelsIn"] + 0.1, -0.7),
          ("DIST  00.000 KM", T["labelsIn"] + 0.15, 0.7)]
for k, (s, t0, p) in enumerate(labels):
    for i, ch in enumerate(s):
        if ch == " ":
            continue
        c = click(5200, 9800, tau=0.0008, dur=0.012, seed=100 * k + i)
        place(dry, c, t0 + i * 0.016 + 0.01, db(-44) * (0.8 + 0.4 * ((i * 7) % 5) / 5), pan=p)

# readout reels land one after another
cells_x = [-0.33, -0.12, 0.0, 0.2, 0.33]
for k, p in enumerate(cells_x):
    c = click(2400, 5600, tau=0.002, ring=0.2, ring_f=1500, dur=0.04, seed=200 + k)
    place(dry, c, T["readoutIn"] + k * 0.035 + 0.07, db(-31), pan=p, rev=0.2)

# ---------------------------------------------------------------- the run
start, stop = T["start"], T["stop"]
press = click(3000, 7200, tau=0.003, ring=0.35, ring_f=1750, ring_tau=0.04, dur=0.08, seed=1)
release = click(3600, 8200, tau=0.0015, dur=0.03, seed=2)
place(dry, press, start, db(-14), rev=0.25)
place(dry, release, start + 0.045, db(-26), rev=0.2)
place(dry, thump(64, 44, tau=0.09, dur=0.4), start, db(-18))

# second ticks: audible as individual ticks only while slower than ~25/s
secs = np.array(ev["secTicks"])
gaps = np.minimum(np.diff(np.r_[secs[0] - 1, secs]), np.diff(np.r_[secs, secs[-1] + 1]))
for i, (t0, g) in enumerate(zip(secs, gaps)):
    w = np.clip((g - 0.035) / 0.06, 0, 1)
    if w <= 0:
        continue
    final = t0 > T["fastEnd"] - 0.01
    tock = i % 2 == 1
    c = click(4300 if tock else 3700, 8000, tau=0.0018, ring=0.25, ring_f=2300 if tock else 2050,
              ring_tau=0.025, dur=0.06, seed=300 + i % 50)
    g_db = (-19 + 2.0 * (t0 - T["fastEnd"]) / 0.2) if final else -26   # crescendo into the stop
    if t0 >= stop - 1e-3:
        continue          # the stop click covers 2:59:59
    place(dry, c, t0, db(g_db) * w, pan=0.12, rev=0.35 if final else 0.15)

# km ratchet: one click per km marker crossing the playhead
for i, t0 in enumerate(ev["kmTicks"]):
    c = click(1500, 3900, tau=0.0022, ring=0.3, ring_f=900, ring_tau=0.015, dur=0.04, seed=400 + i)
    place(dry, c, t0, db(-25), pan=-0.05, rev=0.1)

# whir: a spinning drum whose pitch and brightness follow the clock speed
sp = np.interp(t_axis, np.arange(len(ev["speed"])) / 1000, ev["speed"])
s = np.clip(np.log(np.maximum(sp, 1) / 5) / np.log(max(ev["speed"]) / 5), 0, 1)
s_smooth = signal.filtfilt(*signal.butter(2, 30 / (SR / 2)), s)
s_smooth = np.clip(s_smooth, 0, 1)
f0 = 52 * 2 ** (3.0 * s_smooth)
ph = 2 * np.pi * np.cumsum(f0) / SR
tone = sum((0.8 ** h) * np.sin(h * ph * (1 + 0.004 * h) + 0.3 * h) for h in range(1, 7))
flutter = 1 + 0.3 * np.sin(2 * np.pi * np.cumsum(5 + 34 * s_smooth) / SR)
fc = 320 * 2 ** (4.3 * s_smooth)
air_band = tv_bandpass(noise(N, 7), fc, 1.1) + 0.35 * tv_bandpass(noise(N, 17), fc * 2.03, 6.0)
air_band /= np.abs(air_band).max()
tone /= np.abs(tone).max()
whir = (tone * 0.22 + air_band * 1.0) * flutter
gate = (t_axis >= start) * (t_axis < stop)
whir *= s_smooth ** 1.3 * gate
whir_l = whir
whir_r = np.r_[np.zeros(36), whir[:-36]]          # 0.75 ms Haas for width
place(dry, np.stack([whir_l, whir_r], 1), 0, db(-22))

# sub pulse on the 150 BPM beat while running
for b in np.arange(start + 0.4, stop - 0.01, 0.4):
    place(dry, thump(58, 46, tau=0.07, dur=0.3, drive=1.0), b, db(-25))

# a low fifth that opens with the speed and cuts on the stop
n_run = int((stop - start) * SR)
tt = np.arange(n_run) / SR
drone = hp(pad([110.0, 146.83], stop - start, 0.5, 9.0, cutoff=700, seed=5), 90)
seg_s = s_smooth[int(start * SR):int(start * SR) + n_run]
bright = lp(pad([146.83, 220.0, 293.66], stop - start, 0.4, 9.0, cutoff=3200, seed=6), 4000) * seg_s
build = np.linspace(0.3, 1.0, n_run) ** 1.5
drone_mix = (drone * 0.8 + bright * 0.5) * build
drone_mix[-int(0.006 * SR):] *= np.linspace(1, 0, int(0.006 * SR))
drone_st = np.stack([drone_mix, np.r_[np.zeros(60), drone_mix[:-60]]], 1)
place(dry, drone_st, start, db(-29))

# held breath: a thin band of air swelling under the last ticks, cut by the stop
n = int((stop - T["fastEnd"]) * SR)
tt = np.arange(n) / SR
br = tv_bandpass(noise(n, 31), 2400 * 2 ** (1.2 * tt / tt[-1]), 2.2)
br = br / np.abs(br).max() * (tt / tt[-1]) ** 2.2
br[-int(0.004 * SR):] *= np.linspace(1, 0, int(0.004 * SR))
place(dry, np.stack([br, np.r_[np.zeros(40), br[:-40]]], 1), T["fastEnd"], db(-26))

# ---------------------------------------------------------------- the stop
stop_press = click(3300, 7600, tau=0.003, ring=0.45, ring_f=1650, ring_tau=0.05, dur=0.1, seed=9)
place(dry, stop_press, stop, db(-12), rev=0.55)
place(dry, click(3900, 8800, tau=0.0012, dur=0.03, seed=10), stop + 0.012, db(-20), rev=0.3)
place(dry, thump(74, 40, tau=0.18, dur=0.9, drive=1.5), stop, db(-13))
body = lp(noise(int(0.25 * SR), 13) * env_exp(int(0.25 * SR), 0.03), 300, 2)
place(dry, body / np.abs(body).max(), stop, db(-20), rev=0.3)
# photo-finish line: a short bright shimmer
n = int(0.5 * SR)
tt = np.arange(n) / SR
sh = sum(np.sin(2 * np.pi * f * tt) for f in (5274, 6272, 7040)) * np.exp(-tt / 0.07)
sh[:96] *= np.linspace(0, 1, 96)
place(dry, sh / np.abs(sh).max(), stop + 0.004, db(-36), pan=0.0, rev=0.7)

# ---------------------------------------------------------------- the three pieces
notes = {2: 659.26, 1: 987.77, 0: 1479.98}           # bottom band locks first: E5, B5, F#6
for i, (b0, b1) in enumerate(T["bands"]):
    place(dry, whoosh(b0, b1, 0.85, -0.85, seed=20 + i), b0, db(-27), rev=0.2)
    latch = click(2900, 6400, tau=0.0022, ring=0.3, ring_f=1300, ring_tau=0.02, dur=0.06, seed=30 + i)
    place(dry, latch, b1, db(-16), pan=0.0, rev=0.3)
    place(dry, thump(90, 60, tau=0.05, dur=0.2, drive=1.0), b1, db(-24))
    place(dry, mallet(notes[i], dur=2.4, tau=0.5), b1, db(-25), pan=[-0.25, 0.0, 0.25][2 - i], rev=0.45)

# ---------------------------------------------------------------- the logo
logo = T["logo"]
sub = thump(73.42 * 1.03, 73.42, tau=0.45, dur=1.6, drive=1.05)
place(dry, sub, logo, db(-24))
for f, g, p, dt in ((146.83, -29, -0.2, 0.000), (220.00, -30, 0.2, 0.006), (329.63, -30, -0.3, 0.012),
                    (369.99, -30, 0.3, 0.016), (587.33, -32, 0.0, 0.022)):
    place(dry, mallet(f, dur=DUR - logo + 0.1, tau=0.9, bright=0.5), logo + dt, db(g), pan=p, rev=0.45)
bed = hp(pad([146.83, 220.0, 329.63, 369.99], DUR - logo + 0.2, 0.25, 1.2, cutoff=1100, seed=8), 120)
place(dry, np.stack([bed, np.r_[np.zeros(90), bed[:-90]]], 1), logo, db(-34), rev=0.3)
# the tick forms and the tagline types: two tiny details
place(dry, mallet(2349.3, dur=0.6, tau=0.12, bright=0.2), T["tickGrow"][1] - 0.02, db(-36), rev=0.6)
for i in range(0, 42, 3):
    place(dry, click(5600, 10500, tau=0.0007, dur=0.01, seed=500 + i), T["tagline"] + i * 0.009 + 0.02,
          db(-48), pan=-0.4 + 0.8 * i / 42)

# ---------------------------------------------------------------- reverb + master
def make_ir(rt60=0.9, dur=1.6, seed=42):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    decay = np.exp(-6.91 * tt / rt60)
    ir = []
    for c in range(2):
        x = np.random.default_rng(seed + c).standard_normal(n) * decay
        x = lp(hp(x, 250), 7000)
        x[: int(0.012 * SR)] = 0            # pre-delay
        ir.append(x / np.sqrt(np.sum(x ** 2)))
    return np.stack(ir, 1)


ir = make_ir()
wet = np.stack([signal.fftconvolve(send[:, c], ir[:, c])[:N] for c in range(2)], 1)
mix = dry + wet * db(-6)

# master: gentle high-pass, exit fade, loudness, true-peak ceiling
mix = np.stack([hp(mix[:, c], 28, 2) for c in range(2)], 1)
e0, e1 = T["exit"]
fade = np.clip((e1 - t_axis) / (e1 - e0), 0, 1)
fade = 0.5 - 0.5 * np.cos(np.pi * fade)
mix *= fade[:, None]
mix[-64:] *= np.linspace(1, 0, 64)[:, None]


def k_weight(x):
    b1, a1 = [1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    return signal.lfilter(b2, a2, signal.lfilter(b1, a1, x))


def lufs(x):
    y = np.stack([k_weight(x[:, c]) for c in range(2)], 1)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    ms = np.array([np.mean(y[i:i + blk] ** 2, 0).sum() for i in range(0, len(y) - blk, hop)])
    l = -0.691 + 10 * np.log10(ms + 1e-12)
    g = l > -70
    rel = -0.691 + 10 * np.log10(ms[g].mean()) - 10
    g2 = l > max(-70, rel)
    return -0.691 + 10 * np.log10(ms[g2].mean())


def true_peak(x):
    up = signal.resample_poly(x, 4, 1, axis=0)
    return 20 * np.log10(np.abs(up).max())


TARGET = -16.0
mix *= db(TARGET - lufs(mix))
# soft limiter towards a -1 dBTP ceiling (look-ahead gain computer on the 4x signal)
ceil = db(-1.2)
up = signal.resample_poly(mix, 4, 1, axis=0)
pk = np.abs(up).max(1).reshape(-1, 4).max(1)[: len(mix)]
need = np.minimum(1, ceil / np.maximum(pk, 1e-9))
win = int(0.004 * SR)
from scipy.ndimage import minimum_filter1d, uniform_filter1d
g = minimum_filter1d(need, size=2 * win + 1, origin=0)
g = uniform_filter1d(g, size=win)
mix *= g[:, None]
print(f"integrated {lufs(mix):.2f} LUFS, true peak {true_peak(mix):.2f} dBTP, "
      f"max gain reduction {20 * np.log10(g.min()):.2f} dB")

pcm = np.clip(mix, -1, 1)
i24 = (pcm * (2 ** 23 - 1)).astype(np.int32)
import wave
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(3)
    w.setframerate(SR)
    w.writeframes(i24.astype("<i4").view(np.uint8).reshape(-1, 4)[:, :3].tobytes())
print("wrote", OUT)
