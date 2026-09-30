import json, re, subprocess, sys
import numpy as np, soundfile as sf, sherpa_onnx

M = "sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8"
rec = sherpa_onnx.OfflineRecognizer.from_transducer(
    encoder=f"{M}/encoder.int8.onnx", decoder=f"{M}/decoder.int8.onnx",
    joiner=f"{M}/joiner.int8.onnx", tokens=f"{M}/tokens.txt",
    model_type="nemo_transducer", num_threads=4)

audio, sr = sf.read("audio16k.wav", dtype="float32")
dur = len(audio) / sr
out = subprocess.run(["ffmpeg", "-hide_banner", "-i", "audio16k.wav", "-af",
                      "silencedetect=noise=-38dB:d=0.25", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]
ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
mids = [(s + e) / 2 for s, e in zip(starts, ends)]

# Greedy chunking at silence midpoints, max ~22s per chunk.
cuts, last = [0.0], 0.0
for m in mids:
    if m - last > 12:
        cuts.append(m); last = m
cuts.append(dur)

words = []
for a, b in zip(cuts[:-1], cuts[1:]):
    seg = audio[int(a * sr):int(b * sr)]
    s = rec.create_stream(); s.accept_waveform(sr, seg); rec.decode_stream(s)
    r = s.result
    toks, ts = r.tokens, r.timestamps
    # Merge sentencepiece tokens into words (tokens starting with space begin a word).
    cur = None
    for i, (t, st) in enumerate(zip(toks, ts)):
        if t.startswith(" ") or cur is None:
            if cur: words.append(cur)
            cur = {"w": t.strip(), "s": a + st}
        else:
            cur["w"] += t
        cur["e"] = a + (ts[i + 1] if i + 1 < len(ts) else st + 0.3)
    if cur: words.append(cur)
    print(f"[{a:6.2f}-{b:6.2f}] {r.text}")

json.dump(words, open("words.json", "w"), indent=1)
