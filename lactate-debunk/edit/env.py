import numpy as np, soundfile as sf
a, sr = sf.read("audio48.wav"); m = a.mean(1)
hop = int(sr*0.01); n = len(m)//hop
rms = np.sqrt((m[:n*hop].reshape(n,hop)**2).mean(1)+1e-12); db = 20*np.log10(rms)
np.save("env_db.npy", db)
print("percentiles", {p: round(float(np.percentile(db,p)),1) for p in [5,10,20,30,50,70,90,99]})
# print envelope around the retake regions
for (s,e) in [(48.3,49.8),(51.5,52.8),(62.6,63.6),(63.9,66.3),(95.8,97.9),(99.5,101.4),(118.6,120.3),(123.9,125.1),(132.0,134.2)]:
    seg = db[int(s*100):int(e*100)]
    print(f"{s}-{e}: " + " ".join(f"{v:.0f}" for v in seg[::5]))
