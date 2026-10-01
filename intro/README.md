# sub3piece series intro

A reusable intro for the weekly vlogs. It's a torn-paper collage animated on posterised time: everything moves on threes (10 updates a second) and the paper re-jitters each step, so it feels like stop-motion.

**v2 (current)** holds the end card for one extra bar, 1.6 s, so it runs 9.6 s. It also comes with audio stems. v1 (8.0 s) is kept in `v1/`.

| File | What it is |
| --- | --- |
| `sub3piece_intro_v2.mp4` | H.264 with sound. The final tear reveals brand ink (`#0C0D10`). |
| `sub3piece_intro_v2_alpha.mov` | ProRes 4444 with alpha and sound. Use this one in the edit: the final tear reveals whatever is on the track below. |
| `sub3piece_intro_v2_audio.wav` | The full mix, 24-bit, -14 LUFS. |
| `stems/` | The mix as 10 stems (see below). |
| `end_card.jpg` | A still of the end card. |
| `v1/` | The original 8.0 s cut: MP4, alpha MOV, mix and a foley-only track. |

**Specs:** 1920×1080, 30 fps, 9.6 s (288 frames), BT.709. Audio is 48 kHz.

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
| 5.6 | End card: the **sub3piece** wordmark, then LONDON MARATHON 2027 (6.0) and RUNNING FOR SPINAL RESEARCH (6.2). Adam keeps running on the spot. |
| 9.2 | Rip 3: the end card tears away into the episode (this was 7.6 in v1) |

**In the edit:** put `sub3piece_intro_v2_alpha.mov` on the top track with the episode's first shot already running underneath from about 9.2 s. The tear then opens straight into the episode. For a hard cut instead, cut at 9.2 s.

## Stems
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
`edit/build.sh "WEEK 07"` renders the same intro with a WEEK 07 scrap slapped onto the end card at 6.4 s. The output is `sub3piece_intro_v2_week-07.mp4` and `.mov`. Any short text works.

## Rebuild
`edit/build.sh` regenerates the v2 video, mix and stems in about 4 minutes. It needs ffmpeg and `pip install numpy scipy soundfile pillow opencv-python-headless`.
- **End-card hold:** `HOLD=0.8 NAME=sub3piece_intro_v3 edit/build.sh` changes how long the end card lingers past v1. The default is 1.6. Keep it a multiple of 0.4 to stay on the beat. `HOLD=0` gives the v1 timing.
- **4K:** `SCALE=2 edit/build.sh` renders at 3840×2160. Those files exceed GitHub's size limit, so don't commit them.
- `edit/render.py`: all visuals. Timings are the `T_*` constants at the top, copy is in the scene functions, and the run cycle is `run_pose`.
- `edit/audio.py`: the synthesised groove and foley, cued to the same times. Each `add("stem-name", …)` call says which stem a sound lands on. The alternative bass lines are `alt_rolling`, `alt_808` and `alt_reese` at the end of the file, and the chord plan they share is in `plan()`.
- `edit/cutout.py`: how the `adam{1,2,3}.png` cutouts were made (rembg isnet + SAM, plus hand-drawn masks to remove the runners around him). The cutouts are committed, so you only need it for new photos.

## Heads-up
- Adam's bib in all three photos shows the **AJ Bell** sponsor logo from the Great North Run. In black and white it's subtle, but it's readable on the run shot.
- The intro says "Guinness World Record" as a plain description, with no GWR logo. Check that 2:38:21 is still the current mark for the category before it goes out.
- v2's mix runs through a bus compressor instead of v1's master soft-clip, because that soft-clip couldn't be split into stems. On level meters its tonal balance is within 1 dB of v1 in every band, but give it a listen against v1.
