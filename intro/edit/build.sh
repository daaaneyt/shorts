#!/usr/bin/env bash
# Rebuild the intro. Needs ffmpeg and: pip install numpy scipy soundfile pillow opencv-python-headless
#
#   ./build.sh                    # v2: synthesised 150 bpm track -> ../sub3piece_intro_v2*, ../stems/
#   ./build.sh "WEEK 07"          # same, with an episode tag on the end card (written as *_week-07.*)
#   SCALE=2 ./build.sh            # 3840x2160
#   HOLD=0 NAME=v1/sub3piece_intro ./build.sh   # the v1 timing (8.0 s)
#
#   MUSIC=assets/music_source.mp4 ./build.sh      # v3: picture and paper foley locked to a supplied track
#                                                 #     -> ../sub3piece_intro_v3*, ../stems_v3/
#   MUSIC=... FOLEY_DB=-12 ./build.sh             # a quieter foley layer (default -9)
#
# In music mode music_sync.py finds the track's 16th-note grid, render.py draws one animation step per
# 16th, and foley.py trims/levels the track and adds the paper sounds on the same steps.
set -euo pipefail
cd "$(dirname "$0")"
LABEL="${1:-}"
SCALE="${SCALE:-1}"
MUSIC="${MUSIC:-}"
if [ -n "$MUSIC" ]; then HOLD="${HOLD:-1.2}"; NAME="${NAME:-sub3piece_intro_v3}"
else HOLD="${HOLD:-1.6}"; NAME="${NAME:-sub3piece_intro_v2}"; fi
SUFFIX=""
[ -n "$LABEL" ] && SUFFIX="_$(echo "$LABEL" | tr '[:upper:] ' '[:lower:]-')"
[ "$SCALE" != "1" ] && SUFFIX="${SUFFIX}_4k"
OUT="../${NAME}${SUFFIX}"
SIZE=$(python3 -c "print(f'{round(1920*$SCALE)}x{round(1080*$SCALE)}')")
TAGS="-color_primaries bt709 -color_trc bt709 -colorspace bt709"

rm -rf frames
if [ -n "$MUSIC" ]; then
  python3 music_sync.py "$MUSIC" music_sync.json
  python3 render.py --scale "$SCALE" --label "$LABEL" --hold "$HOLD" --sync music_sync.json --frames frames
  python3 foley.py --music "$MUSIC" --sync music_sync.json --hold "$HOLD" --foley-db "${FOLEY_DB:--9}" ${LABEL:+--tag}
  STEMDIR=stems_v3
else
  python3 render.py --scale "$SCALE" --label "$LABEL" --hold "$HOLD" --frames frames
  python3 audio.py --hold "$HOLD" ${LABEL:+--tag}   # stems/ + mix_full.wav, already at -14 LUFS
  STEMDIR=stems
fi

# the mix only gets a peak limiter (delay-compensated, so it stays sample-aligned with the stems)
ffmpeg -v error -y -i mix_full.wav -af "alimiter=limit=0.84:attack=2:release=50:level=disabled:latency=1" \
  -ar 48000 -c:a pcm_s24le final_full.wav

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
  cp final_full.wav "${OUT}_audio.wav"
  if [ -n "$MUSIC" ] || [ "$HOLD" = "1.6" ]; then
    rm -rf "../$STEMDIR" && cp -r "$STEMDIR" "../$STEMDIR"
    ffmpeg -v error -y -i "$OUT.mp4" -ss "$([ -n "$MUSIC" ] && echo 7.5 || echo 6.9)" -frames:v 1 -q:v 2 ../end_card.jpg
  fi
fi
