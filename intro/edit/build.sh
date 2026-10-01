#!/usr/bin/env bash
# Render the sub3piece intro.
#   ./build.sh            4K masters at 25 and 30 fps, 1080p30 copy, audio, end frame
#   ./build.sh 24 2       one or more frame rates at 4K (scale 2)
#   ./build.sh 30 1       quick 1920x1080 check
set -euo pipefail
cd "$(dirname "$0")"
export NODE_PATH="${NODE_PATH:-$(npm root -g)}"
OUT=..
RATES="${1:-25 30}"
SCALE="${2:-2}"
W=$((1920 * SCALE)); H=$((1080 * SCALE))
TAG=$([ "$SCALE" = 2 ] && echo 4k || echo "${H}p")
AUDIO="$OUT/sub3piece_intro_audio.wav"

node render.cjs events events.json
python3 sound.py events.json "$AUDIO"
DUR=$(python3 -c "import json;print(json.load(open('events.json'))['T']['end'])")

# encode <frames dir> <fps> <width> <height> <out.mp4>
# Film grain: half-res luma noise, softened and scaled up, overlaid on Y only.
encode() {
  local fr=$1 fps=$2 w=$3 h=$4 out=$5
  ffmpeg -hide_banner -loglevel error -y \
    -framerate "$fps" -i "$fr/f%04d.png" -i "$AUDIO" \
    -filter_complex "\
[0:v]scale=${w}:${h}:flags=lanczos:out_color_matrix=bt709:out_range=tv,format=yuv444p[v];\
color=c=0x808080:s=$((w/2))x$((h/2)):r=${fps}:d=${DUR},format=yuv444p,noise=c0s=30:c0f=t+u,gblur=sigma=0.6,scale=${w}x${h}:flags=bicubic[g];\
[v][g]blend=c0_mode=overlay:c0_opacity=0.32:c1_mode=normal:c1_opacity=1:c2_mode=normal:c2_opacity=1,format=yuv420p[out]" \
    -map "[out]" -map 1:a \
    -c:v libx264 -preset slow -crf 15 -profile:v high -tune grain -g "$fps" \
    -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv \
    -c:a aac -b:a 320k -ar 48000 -movflags +faststart -shortest "$out"
  echo "wrote $out"
}

for FPS in $RATES; do
  FR="frames_${TAG}_${FPS}"
  node render.cjs frames "$FPS" "$SCALE" "$FR" 4
  encode "$FR" "$FPS" "$W" "$H" "$OUT/sub3piece_intro_${TAG}_${FPS}fps.mp4"
done

if [ "$SCALE" = 2 ] && [ -d frames_4k_30 ]; then
  encode frames_4k_30 30 1920 1080 "$OUT/sub3piece_intro_1080p_30fps.mp4"
  cp frames_4k_30/f0138.png "$OUT/sub3piece_intro_endframe.png"   # t = 4.6 s, the logo hold
fi
