# Lactate debunk reel (sub3piece)

| File | What it is |
| --- | --- |
| `sub3piece_lactate-debunk.mp4` | Post-ready reel with a soft music bed |
| `sub3piece_lactate-debunk_no-music.mp4` | Same cut without the bed, for adding a trending sound in-app |
| `cover.jpg` | First frame (hook title on screen), for use as the Reels/TikTok cover |

**Specs:** 1080×1920, 30 fps, H.264 High, BT.709 SDR, AAC 192 kbps, -14 LUFS integrated, -1.5 dBTP peak. Runs 1:48 (the source clip was 2:14).

## Edit
- Four retakes removed: the first "Michael Crawley, who is a Northeast based…", the repeated "so for example", the first "they're not measuring their lactate threshold every…", and "fastest marathon *in the world*…" (the "in a suit" take is kept). Pauses tightened to ~0.3 s.
- Face-anchored punch-ins (1.00 / 1.07 / 1.14) on the bigger jump cuts and emphasis lines. Light grade and sharpening.
- Captions phrase by phrase with a word-by-word highlight. Names are corrected (Ingebrigtsen, Sawe, Kipchoge, VO2 max).
- B-roll cards: the map on "Ethiopia, Kenya, Uganda", Ingebrigtsen, Sawe on "Sawe's dad was a maize farmer", the *Out of Thin Air* cover on "Michael Crawley", and the training photo on "lived there for over a year…"
- Hook title "DEBUNK · Does lactate testing make elite runners?" is on screen for the first sentence. A "Follow the journey @sub3piece" card appears on the call to action.
- Voice: high-pass, light denoise, de-box and presence EQ, de-ess and compression. The music bed and whooshes are synthesized, so there are no licensing issues. The bed ducks under speech.

## Heads-up
The line says Crawley "went to **Kenya**" (two separate speech models both hear "Kenya"), but *Out of Thin Air* is about his time training in **Ethiopia**. The book cover on screen says Ethiopia. Consider pinning a comment correction.

## Rebuild
`edit/build.sh` regenerates everything from the original clip (drop it in `edit/` as `src.mp4`). Caption wording is in `CAPTION_SCRIPT`, B-roll timings in `CARDS`, and zoom levels in `ZOOM_PLAN`. All three are in `edit/render.py`. Retake cuts are in `REMOVE` in `edit/edl.py`.
