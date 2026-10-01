#!/usr/bin/env bash
# Rebuild the intro. Needs ffmpeg and: pip install numpy scipy soundfile pillow opencv-python-headless
#   ./build.sh                 # 1920x1080
#   ./build.sh "WEEK 07"       # same, with an episode tag on the end card (written as *_week-07.*)
#   SCALE=2 ./build.sh         # 3840x2160
set -euo pipefail
cd "$(dirname "$0")"
LABEL="${1:-}"
SCALE="${SCALE:-1}"
SUFFIX=""
[ -n "$LABEL" ] && SUFFIX="_$(echo "$LABEL" | tr '[:upper:] ' '[:lower:]-')"
[ "$SCALE" != "1" ] && SUFFIX="${SUFFIX}_4k"
OUT="../sub3piece_intro${SUFFIX}"
SIZE=$(python3 -c "print(f'{round(1920*$SCALE)}x{round(1080*$SCALE)}')")
TAGS="-color_primaries bt709 -color_trc bt709 -colorspace bt709"

rm -rf frames
python3 render.py --scale "$SCALE" --label "$LABEL" --frames frames
python3 audio.py

for n in full sfx; do
  m=$(ffmpeg -hide_banner -i mix_$n.wav -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p' |
      python3 -c "import json,sys; d=json.load(sys.stdin); print(f\"measured_I={d['input_i']}:measured_TP={d['input_tp']}:measured_LRA={d['input_lra']}:measured_thresh={d['input_thresh']}:offset={d['target_offset']}\")")
  ffmpeg -v error -y -i mix_$n.wav -af "loudnorm=I=-14:TP=-1.5:LRA=11:$m:linear=true,alimiter=limit=0.84:attack=2:release=50:level=disabled" -ar 48000 -c:a pcm_s24le final_$n.wav
done

# H.264 for posting / quick use: the transparent tail sits on brand ink
ffmpeg -v error -y -framerate 30 -i frames/%04d.png -i final_full.wav \
  -filter_complex "color=c=0x0C0D10:s=$SIZE:r=30[bg];[bg][0:v]overlay=shortest=1,scale=out_color_matrix=bt709:out_range=tv,format=yuv420p[v]" \
  -map "[v]" -map 1:a -c:v libx264 -preset slow -crf 14 -profile:v high -c:a aac -b:a 256k \
  $TAGS -movflags +faststart -shortest "$OUT.mp4"

# ProRes 4444 with alpha, for the edit: the last tear reveals whatever is underneath
ffmpeg -v error -y -framerate 30 -i frames/%04d.png -i final_full.wav \
  -map 0:v -map 1:a -vf "scale=out_color_matrix=bt709:out_range=tv,format=yuva444p10le" \
  -c:v prores_ks -profile:v 4444 -alpha_bits 8 -qscale:v 28 -vendor apl0 \
  $TAGS -c:a pcm_s24le -shortest "${OUT}_alpha.mov"

if [ -z "$LABEL" ] && [ "$SCALE" = "1" ]; then
  cp final_full.wav ../sub3piece_intro_audio.wav
  cp final_sfx.wav ../sub3piece_intro_sfx-only.wav
  ffmpeg -v error -y -i "$OUT.mp4" -ss 6.9 -frames:v 1 -q:v 2 ../end_card.jpg
fi
