import json, numpy as np, soundfile as sf
edl = json.load(open("edl.json")); FPS = edl["fps"]
a, sr = sf.read("audio48.wav", dtype="float32")
FADE = int(0.008 * sr)
out = []
for s in edl["segments"]:
    i0 = int(round(s["src"] * sr)); n = int(round(s["dur_frames"] / FPS * sr))
    seg = a[i0:i0+n].copy()
    if len(seg) < n: seg = np.pad(seg, ((0, n-len(seg)), (0, 0)))
    ramp = np.linspace(0, 1, FADE)[:, None]
    seg[:FADE] *= ramp; seg[-FADE:] *= ramp[::-1]
    out.append(seg)
out = np.concatenate(out)
sf.write("voice_cut.wav", out, sr, subtype="FLOAT")
print(len(out)/sr, edl["total"])
