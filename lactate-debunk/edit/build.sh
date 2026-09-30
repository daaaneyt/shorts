#!/usr/bin/env bash
# Rebuild the reel from the source clip.
# Needs ffmpeg and: pip install numpy scipy soundfile pillow opencv-contrib-python-headless sherpa-onnx
# Put the original clip here as src.mp4. words.json (the Parakeet transcript) is committed, so
# transcribe.py only needs re-running for a new clip (it expects the sherpa-onnx Parakeet model dir).
set -euo pipefail
cd "$(dirname "$0")"

ffmpeg -v error -y -i src.mp4 -vn -ac 2 -ar 48000 -c:a pcm_f32le audio48.wav
python3 env.py          # audio envelope -> env_db.npy
python3 edl.py          # retakes + pause trims -> edl.json
python3 cut_audio.py    # voice_cut.wav
python3 render.py       # video_only.mp4 (captions, cards, titles)

ffmpeg -v error -y -i voice_cut.wav -af "pan=mono|c0=0.5*c0+0.5*c1,highpass=f=75:poles=2,afftdn=nr=10:nf=-56:tn=1,equalizer=f=280:t=q:w=1.1:g=-2.5,equalizer=f=3600:t=q:w=1.3:g=3,treble=g=2.5:f=8000,deesser=i=0.3,acompressor=threshold=-24dB:ratio=3:attack=6:release=140:knee=4:makeup=3dB" -ar 48000 -c:a pcm_f32le voice_proc.wav
python3 mix.py          # mix_music.wav / mix_voice.wav

for n in music voice; do
  m=$(ffmpeg -hide_banner -i mix_$n.wav -af loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p' |
      python3 -c "import json,sys; d=json.load(sys.stdin); print(f\"measured_I={d['input_i']}:measured_TP={d['input_tp']}:measured_LRA={d['input_lra']}:measured_thresh={d['input_thresh']}:offset={d['target_offset']}\")")
  ffmpeg -v error -y -i mix_$n.wav -af "loudnorm=I=-14:TP=-1.5:LRA=9:$m:linear=true,alimiter=limit=0.84:attack=3:release=60:level=disabled" -ar 48000 -c:a pcm_f32le final_$n.wav
done

ffmpeg -v error -y -i video_only.mp4 -i final_music.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -map_metadata -1 -movflags +faststart -shortest ../sub3piece_lactate-debunk.mp4
ffmpeg -v error -y -i video_only.mp4 -i final_voice.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -map_metadata -1 -movflags +faststart -shortest ../sub3piece_lactate-debunk_no-music.mp4
ffmpeg -v error -y -i video_only.mp4 -frames:v 1 -q:v 2 ../cover.jpg
