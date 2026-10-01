# sub3piece series intro

A reusable 8-second intro for the weekly vlogs. It's a torn-paper collage animated on posterised time: everything moves on threes (10 updates a second) and the paper re-jitters each step, so it feels like stop-motion.

| File | What it is |
| --- | --- |
| `sub3piece_intro.mp4` | H.264 with sound. The final tear reveals brand ink (`#0C0D10`). |
| `sub3piece_intro_alpha.mov` | ProRes 4444 with alpha and sound. Use this one in the edit: the final tear reveals whatever is on the track below. |
| `sub3piece_intro_audio.wav` | The full sound (music + paper foley), 24-bit. |
| `sub3piece_intro_sfx-only.wav` | Foley only (rips, slaps, stamps, ticks, impact), so you can lay your own music underneath. |
| `end_card.jpg` | A still of the end card. |

**Specs:** 1920×1080, 30 fps, 8.0 s (240 frames), BT.709. Audio is 48 kHz at -14 LUFS integrated.

## The cut (150 bpm, one beat = 0.4 s)
| Time | What happens |
| --- | --- |
| 0.0 | "26.2 miles." then "In a suit." on black paper |
| 0.8 | Rip 1: the sheet tears across and both halves fly off |
| 1.0 | Adam runs, swapping between two photocopied photo stickers, with two ticker strips (FASTEST MARATHON IN A SUIT / WORLD RECORD ATTEMPT) and a race clock spinning up to 2:29 |
| 3.2 | Rip 2: a diagonal tear |
| 3.6 | GUINNESS WORLD RECORD, then **2:38:21** slapped on ransom-note style, one digit per 16th note, then THE TIME TO BEAT |
| 5.1 | The time cracks from the middle |
| 5.2 | Adam bursts through it and the digits tear apart |
| 5.6 | End card: the **sub3piece** wordmark, LONDON MARATHON 2027, RUNNING FOR SPINAL RESEARCH. Adam keeps running on the spot. |
| 7.6 | Rip 3: the end card tears away into the episode |

**In the edit:** put `sub3piece_intro_alpha.mov` on the top track with the episode's first shot already running underneath from about 7.6 s. The tear then opens straight into the episode. For a hard cut instead, cut at 7.6 s.

## Design notes
These depart from the guidelines on purpose. They're things to keep or drop if you rework the brand.
- **Paper, not screen.** There are three paper stocks: ink, warm paper and signal orange. Torn edges show a white fibre core and every piece casts a soft shadow. Orange covers whole surfaces here, rather than being used for one accent per frame.
- **Adam as photocopy stickers.** He's black and white, high contrast and grainy, with a scissor-cut white border. It ties three very different photos together and keeps the look in ink, paper and orange.
- **Ransom-note numbers.** Each digit sits on its own scrap, alternating Space Grotesk and Space Mono. It's a good motif to reuse on thumbnails, splits and countdowns.
- **Uppercase grotesk on the tickers.** The guidelines keep uppercase for small mono labels, but at ticker size it reads like race signage.
- The wordmark is unchanged: lowercase, -0.04em, orange 3, never rotated.

## Episode tag
`edit/build.sh "WEEK 07"` renders the same intro with a WEEK 07 scrap slapped onto the end card at 6.4 s. The output is `sub3piece_intro_week-07.mp4` and `.mov`. Any short text works.

## Rebuild
`edit/build.sh` regenerates everything in about 3 minutes. It needs ffmpeg and `pip install numpy scipy soundfile pillow opencv-python-headless`. `SCALE=2 edit/build.sh` renders at 3840×2160; those files exceed GitHub's size limit, so don't commit them.
- `edit/render.py`: all visuals. Timings are the `T_*` constants at the top, copy is in the scene functions, and the run cycle is `run_pose`.
- `edit/audio.py`: the synthesised groove and foley, cued to the same times.
- `edit/cutout.py`: how the `adam{1,2,3}.png` cutouts were made (rembg isnet + SAM, plus hand-drawn masks to remove the runners around him). The cutouts are committed, so you only need it for new photos.

## Heads-up
- Adam's bib in all three photos shows the **AJ Bell** sponsor logo from the Great North Run. In black and white it's subtle, but it's readable on the run shot.
- The intro says "Guinness World Record" as a plain description, with no GWR logo. Check that 2:38:21 is still the current mark for the category before it goes out.
- Nobody has listened to the sound yet: it was checked for timing, loudness and peaks only. Give it a listen. `sub3piece_intro_sfx-only.wav` is there if the music isn't right.
