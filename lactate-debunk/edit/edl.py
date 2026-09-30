"""Build the edit decision list: remove retakes, tighten pauses, snap to frames."""
import json, numpy as np
FPS = 30
db = np.load("env_db.npy")          # 10 ms RMS envelope (dBFS)
HOP = 0.01
SIL_DB = -45.0                      # below this = silence
MIN_SIL = 0.30                      # only touch pauses longer than this
PRE, POST = 0.10, 0.17              # keep this much air before/after speech

# Retakes / flubs to drop (source seconds, chosen inside silent gaps)
REMOVE = [
    (48.45, 52.35),   # "In fact, Michael Crawley, who is a Northeast based" (restarted)
    (63.20, 66.00),   # first "So for example" + long pause
    (96.35, 101.05),  # "They're not measuring their lactate threshold every" (restarted)
    (119.10, 124.70), # "...fastest marathon in the world ... if you want to help" (restarted)
]
START, END = 0.56, 132.52

silent = db < SIL_DB
# speech mask with small hangover so consonant tails aren't clipped
speech = ~silent
t = np.arange(len(db)) * HOP

def interval_minus(keep, cuts):
    out = []
    for a, b in keep:
        pieces = [(a, b)]
        for c0, c1 in cuts:
            nxt = []
            for p0, p1 in pieces:
                if c1 <= p0 or c0 >= p1: nxt.append((p0, p1)); continue
                if c0 > p0: nxt.append((p0, c0))
                if c1 < p1: nxt.append((c1, p1))
            pieces = nxt
        out += pieces
    return out

keep = interval_minus([(START, END)], REMOVE)

# Build a "virtual" timeline mask: which source 10ms frames are kept
kept = np.zeros(len(db), bool)
for a, b in keep: kept[int(round(a/HOP)):int(round(b/HOP))] = True
idx = np.where(kept)[0]
# walk kept frames in order and find silent runs (across removal joins)
cuts = []
run = []
for i in idx:
    if silent[i]:
        run.append(i)
    else:
        if run:
            cuts.append(run); run = []
if run: cuts.append(run)
extra = []
for r in cuts:
    dur = len(r) * HOP
    if dur <= MIN_SIL: continue
    first, last = r[0], r[-1]
    leading = first == idx[0]
    # keep POST after the preceding speech and PRE before next speech
    # (measured in kept-frames, so a join counts as one gap)
    keep_after = r[:int(round(POST/HOP))] if not leading else []
    keep_before = r[-int(round(PRE/HOP)):]
    drop = [i for i in r if i not in set(keep_after) | set(keep_before)]
    if drop:
        # convert kept-frame runs to source ranges
        s = drop[0]; p = drop[0]
        for i in drop[1:] + [None]:
            if i is None or i != p + 1:
                extra.append((s*HOP, (p+1)*HOP)); 
                if i is not None: s = i
            if i is not None: p = i
keep = interval_minus(keep, extra)
keep = [(a, b) for a, b in keep if b - a > 0.02]

# Merge tiny pieces (<0.12s) into neighbours isn't needed; snap durations to frames
segs, T = [], 0.0
for a, b in keep:
    n = max(1, int(round((b - a) * FPS)))
    segs.append({"src": round(a, 4), "dur_frames": n, "out": round(T, 4)})
    T += n / FPS
json.dump({"fps": FPS, "segments": segs, "total": T}, open("edl.json", "w"), indent=1)
print(f"{len(segs)} segments, output {T:.2f}s (source {END-START:.2f}s)")
for s in segs: print(f"  out {s['out']:7.2f}  src {s['src']:7.2f}  len {s['dur_frames']/FPS:5.2f}")
