# sub3piece series intro

A reusable intro for the weekly vlogs. It's a torn-paper collage animated on posterised time: everything moves in steps and the paper re-jitters each step, so it feels like stop-motion.

**v3 (current)** is locked to your own track (`edit/assets/music_source.mp4`, 134 bpm): every slap, tear and stamp lands on a hit, and it runs 10.3 s. v2 (my synthesised 150 bpm track, 9.6 s, with stems) and v1 (8.0 s) are kept.

| File | What it is |
| --- | --- |
| `sub3piece_intro_v3.mp4` | H.264 with sound (your track plus a light layer of paper sounds). The final tear reveals brand ink (`#0C0D10`). |
| `sub3piece_intro_v3_alpha.mov` | ProRes 4444 with alpha and sound. Use this one in the edit: the final tear reveals whatever is on the track below. |
| `sub3piece_intro_v3_audio.wav` | The full mix, 24-bit, about -14 LUFS. |
| `stems_v3/` | Six stems that sum to the mix: your track on its own, plus five paper-sound stems (see below). |
| `end_card.jpg` | A still of the v3 end card. |
| `sub3piece_intro_v2*.mp4/.mov/.wav`, `stems/` | v2 and its 10 stems (synthesised track). |
| `v1/` | The original 8.0 s cut. |

**Specs (v3):** 1920×1080, 30 fps, 10.333 s (310 frames), BT.709. Audio is 48 kHz.

## v3: how it's locked to your track
The track is 134.4 bpm. Its first hit (the start of the opening roll) is at 0.062 s, the drop at 0.955 s, and bars then run every 1.786 s until the music stops dead at 8.10 s and rings out as echoes. In v3, each animation step is one 16th note of the track (0.1116 s), so nothing drifts. `edit/music_sync.py` finds that grid from the audio; every frame then shows the step whose 16th note it's closest to.

| Time | What happens | What the track is doing |
| --- | --- | --- |
| 0.06 | "26.2 miles." slaps on black paper | First hit of the opening roll |
| 0.40 | "In a suit." slaps on | The roll's strongest hit |
| 0.62–0.73 | A crack runs across the sheet | Roll accents |
| 0.96 | The sheet tears open and Adam is revealed | **The drop** |
| 0.96–3.4 | Adam runs, with the tickers and the race clock spinning up to 2:29 | Bars 1–2 of the groove |
| 3.41 | Rip 2 cracks open diagonally | A strong kick |
| 4.08 | GUINNESS WORLD RECORD | A backbeat hit |
| 4.53–5.20 | **2:38:21** is stamped on, one scrap per 16th note | Bar 3 downbeat and the kick fill |
| 5.42 | THE TIME TO BEAT | |
| 5.77 / 5.87 | The time cracks, then Adam bursts through it | The strongest hit of the second half |
| 6.31 | The **sub3piece** wordmark | Bar 4 downbeat |
| 6.76 / 6.98 | LONDON MARATHON 2027, then RUNNING FOR SPINAL RESEARCH | A backbeat, then the hit after it |
| 7.65, 7.87, 8.10 | The end card jolts | The last fill, and the stop |
| 9.89 | Rip 3 tears the end card away into the episode (from frame 297) | An echo of the final hit |

Measured against the track, every one of these lands within one frame (worst 16 ms against 33 ms per frame, average +1 ms). The end card is fully built from 6.98 s, so it's up for about 2.9 s before the tear, in line with v2's 3.0 s.

**What I did to your audio:** I trimmed it to the picture's length (10.33 s), faded the long reverb tail out from 9.0 s, and applied one gain of about -5.0 dB (your file is -8.7 LUFS with peaks above 0 dBFS; this brings it to -14 LUFS like v2). No EQ or compression. I found no vocal: a speech model hears only "[Music]", so there were no lyrics to sync.

**The paper sounds** are synthesised, so there's nothing to license. They sit under the track: rips are the most audible (a few dB above the track in the mid band), slaps and whooshes sit inside it, and the clock ticks and impact are subtle. If you'd rather hear only your track, use `01_music.wav`. If you want them louder or quieter, re-balance the stems or rebuild with `FOLEY_DB` (default -9).

### Stems (`stems_v3/`)
All six are 24-bit, 48 kHz, stereo, 10.333 s and start at 0. At 0 dB they sum to the mix, apart from its peak limiter (which doesn't act on this mix: it peaks at -2 dBFS).

| Stem | What's on it |
| --- | --- |
| `01_music` | Your track, trimmed, faded and gained. A stereo mix; it can't be split further |
| `02_paper-rips` | The three tears, the burst rip and the small crack before it |
| `03_paper-slaps` | Every slap-on: the two lines, record labels, the 7 digits, wordmark and end-card strips (plus the week tag, when there is one) |
| `04_clock-ticks` | The race clock ticks under the run |
| `05_whooshes-riser` | The whooshes after each rip, and the riser into the burst |
| `06_impact` | The low boom when Adam bursts through |

For a DAW: 134.36 bpm, 4/4. The first roll hit is at 0.062 s and bar 1 (the drop) starts at 0.955 s.

**In the edit:** put `sub3piece_intro_v3_alpha.mov` on the top track with the episode's first shot already running underneath from about 9.9 s. The tear then opens straight into the episode. For a hard cut, cut at 9.9 s.

## v2: the cut (synthesised 150 bpm track, one beat = 0.4 s)
| Time | What happens |
| --- | --- |
| 0.0 | "26.2 miles." then "In a suit." on black paper |
| 0.8 | Rip 1: the sheet tears across and both halves fly off |
| 1.0 | Adam runs, swapping between two photocopied photo stickers, with two ticker strips (FASTEST MARATHON IN A SUIT / WORLD RECORD ATTEMPT) and a race clock spinning up to 2:29 |
| 3.2 | Rip 2: a diagonal tear |
| 3.6 | GUINNESS WORLD RECORD, then **2:38:21** slapped on ransom-note style, one digit per 16th note, then THE TIME TO BEAT |
| 5.1 | The time cracks from the middle |
| 5.2 | Adam bursts through it and the digits tear apart |
| 5.6 | End card: the **sub3piece** wordmark, then LONDON MARATHON 2027 (6.0) and RUNNING FOR SPINAL RESEARCH (6.2). Adam keeps running on the spot. |
| 9.2 | Rip 3: the end card tears away into the episode (this was 7.6 in v1) |

**In the edit:** put `sub3piece_intro_v2_alpha.mov` on the top track with the episode's first shot already running underneath from about 9.2 s. The tear then opens straight into the episode. For a hard cut instead, cut at 9.2 s.

## v2 stems
All 10 stems are 24-bit, 48 kHz, stereo and 9.6 s long, and they all start at 0. Line them up with the start of the intro.

At 0 dB, the stems sum to the mix exactly, apart from the mix's final peak limiter. Summed raw, they peak around +1.4 dBFS. Put a limiter on your master (ceiling about -1.5 dB), or pull everything down 3 dB.

For a music app or DAW: 150 bpm, 4/4, bar 1 starts at 0.0 s, and the key is E minor.

| Stem | What's on it |
| --- | --- |
| `01_kick` | The groove kick, the hits under the two opening lines, the digit stamps, the burst and the final hit |
| `02_clap` | Backbeat claps and the final hit |
| `03_hats` | Closed and open hats, plus the 16th run under the digits |
| `04_bass` | Sub-bass, one note per kick (E, E, G, A; E, E, G, D on the end card) |
| `05_synth-stabs` | Chord stabs at rip 2, the burst, the wordmark and the final hit |
| `06_paper-rips` | All three tears, the burst rip and the small crack at 5.1 |
| `07_paper-slaps` | Every slap-on: the opening lines, the two record labels, the 7 digits, the wordmark and end-card strips (plus the week tag, when there is one) |
| `08_clock-ticks` | The race clock ticks under the run |
| `09_whooshes-riser` | Flyaway whooshes after each rip, plus the riser into the burst (4.8 to 5.2) |
| `10_impact` | The sub boom when Adam bursts through |

### Alternative bass lines (`stems/bass-alternates/`)
Three drop-in replacements for `04_bass`. Mute `04_bass` and drop one in at 0. They follow the same arrangement: in under the run from 0.8 s, out for the digits, back for the end card, and a note on the final hit. Unlike the original, which holds an E for almost the whole intro, they play a progression: E for the run, C then D into rip 2, then E E C G D on the end card, resolving to E on the final hit.

Each one goes through exactly the same processing as `04_bass`, with the compressor and loudness gains taken from the current mix. So the other nine stems, the mix and the video are unchanged. Each is level-matched to the original bass, and the mix measures -13.8 to -13.9 LUFS with any of them.

| File | Feel |
| --- | --- |
| `04_bass_alt-a_rolling-octaves` | Bouncing 8th notes, low on the beat and an octave up off it. A plucky tone with a sub under the low notes. Driving, like a running cadence. |
| `04_bass_alt-b_808-glide` | One long, slightly distorted 808 note per chord. It slides between notes (E up to C, down to G, up to D, home to E), has a punch on each new note, and dips under every kick so the kick still cuts through. The deepest and most modern option. |
| `04_bass_alt-c_reese` | Darker and syncopated: three detuned saws with a slow filter drift and a sine sub, hitting off the beat. Drum-and-bass flavoured. |

Each stem already has its share of the mix processing baked in: a short room, its own soft-clip, and the bus compressor's gain (keyed from the whole mix, so it rides every stem by the same amount). Mute or re-level them freely and the rest still sits the same.

## Design notes
These depart from the guidelines on purpose. They're things to keep or drop if you rework the brand.
- **Paper, not screen.** There are three paper stocks: ink, warm paper and signal orange. Torn edges show a white fibre core and every piece casts a soft shadow. Orange covers whole surfaces here, rather than being used for one accent per frame.
- **Adam as photocopy stickers.** He's black and white, high contrast and grainy, with a scissor-cut white border. It ties three very different photos together and keeps the look in ink, paper and orange.
- **Ransom-note numbers.** Each digit sits on its own scrap, alternating Space Grotesk and Space Mono. It's a good motif to reuse on thumbnails, splits and countdowns.
- **Uppercase grotesk on the tickers.** The guidelines keep uppercase for small mono labels, but at ticker size it reads like race signage.
- The wordmark is unchanged: lowercase, -0.04em, orange 3, never rotated.

## Episode tag
`edit/build.sh "WEEK 07"` renders v2 with a WEEK 07 scrap slapped onto the end card at 6.4 s (`sub3piece_intro_v2_week-07.mp4` and `.mov`). For v3, `MUSIC=assets/music_source.mp4 edit/build.sh "WEEK 07"` puts it on the end card at 7.2 s, on a hit (`sub3piece_intro_v3_week-07.*`). Any short text works.

## Rebuild
`MUSIC=assets/music_source.mp4 edit/build.sh` regenerates v3 (video, mix and stems) in about 3 minutes; plain `edit/build.sh` regenerates v2. It needs ffmpeg and `pip install numpy scipy soundfile pillow opencv-python-headless`. To use a different track, point `MUSIC` at it: `music_sync.py` finds its grid, but the picture assumes the same structure (a two-beat roll into the drop, then a four-bar phrase), so check the result.
- **End-card hold:** in v2, `HOLD=0.8 NAME=sub3piece_intro_v2b edit/build.sh` changes how long the end card lingers past v1 (default 1.6; `HOLD=0` gives v1). In v3 the hold is in animation time and defaults to 1.2, which puts the tear on the step-88 echo at 9.9 s. `HOLD=0.8` pulls the tear one beat (0.45 s) earlier, to 9.4 s, for a 9.9 s intro.
- **4K:** `SCALE=2 edit/build.sh` renders at 3840×2160. Those files exceed GitHub's size limit, so don't commit them.
- `edit/render.py`: all visuals. Copy is in the scene functions and the run cycle is `run_pose`. `--sync music_sync.json` selects music mode.
- `edit/timing.py`: the event times for v2 and v3 (the `T_*` constants), shared by the renderer and the audio.
- `edit/music_sync.py`: finds the supplied track's 16th-note grid and writes `music_sync.json`.
- `edit/foley.py`: v3 audio. It trims and levels the track and places the paper sounds on the same steps.
- `edit/synth.py`: the filters and paper-sound synthesis shared by `audio.py` and `foley.py`.
- `edit/audio.py`: v2's synthesised groove and foley, cued to the same times. Each `add("stem-name", …)` call says which stem a sound lands on. The alternative bass lines are `alt_rolling`, `alt_808` and `alt_reese` at the end of the file, and the chord plan they share is in `plan()`.
- `edit/cutout.py`: how the `adam{1,2,3}.png` cutouts were made (rembg isnet + SAM, plus hand-drawn masks to remove the runners around him). The cutouts are committed, so you only need it for new photos.

## Heads-up
- Adam's bib in all three photos shows the **AJ Bell** sponsor logo from the Great North Run. In black and white it's subtle, but it's readable on the run shot.
- The intro says "Guinness World Record" as a plain description, with no GWR logo. Check that 2:38:21 is still the current mark for the category before it goes out.
- v2's mix runs through a bus compressor instead of v1's master soft-clip, because that soft-clip couldn't be split into stems. On level meters its tonal balance is within 1 dB of v1 in every band, but give it a listen against v1.
