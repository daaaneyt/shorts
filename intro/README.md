# sub3piece channel intro

A 6.8-second ident for the top of every weekly vlog. A stopwatch runs a whole marathon and stops on **2:38:20**, one second inside the 2:38:21 record for the fastest marathon in a three-piece suit. The record is struck through in the corner. The readout is then swapped for the wordmark in three horizontal pieces (trousers, waistcoat, jacket), the start/finish line closes into the brand's orange tick, and the logo holds for just over two seconds.

| File | What it is |
| --- | --- |
| `sub3piece_intro_4k_25fps.mp4` | 3840×2160, 25 fps master for a 25p (UK/PAL) timeline |
| `sub3piece_intro_4k_30fps.mp4` | 3840×2160, 30 fps master for a 30p timeline |
| `sub3piece_intro_1080p_30fps.mp4` | 1920×1080, 30 fps, downscaled from the 4K frames, for 1080p timelines and quick previews |
| `sub3piece_intro_audio.wav` | The sound design on its own, 48 kHz 24-bit stereo, for the editor's own mix |
| `sub3piece_intro_endframe.png` | The 4K logo hold, for a thumbnail or an end card |

**Specs:** H.264 High, 4:2:0, BT.709 SDR, AAC 320 kbps. Audio is -16 LUFS integrated with true peaks at -1.1 dBTP (after AAC), so it sits level with dialogue before YouTube's -14 normalisation. The intro opens on ink and fades back to ink over its last 0.5 s, so a straight cut into footage works. If you prefer a hard cut, cut anywhere in the logo hold (4.5–6.3 s). There is no episode-specific text, so the same file works every week.

## Storyboard (150 BPM grid: beat 0.4 s)

| Time | Picture | Sound |
| --- | --- | --- |
| 0.00–0.80 | The hairline draws out from the centre and the 60 px grid fades up. Corner labels type on. The readout drums roll up to `0:00:00`. | Air widening with the line, a tink for the playhead, whisper clicks panned to each corner, and a ratchet as the drums land |
| 0.80 | **Start.** | Stopwatch press and release, with a soft sub |
| 0.80–2.00 | The clock runs 0:00:00 → 2:38:16 on a log-speed curve. The drums spin into streaks and the km ruler smears past the orange playhead. The line behind the playhead takes the zone colour of the effort (Z2 → Z3 → Z4 → Z5). Live zone and distance run in the corners. | A spinning-drum whir whose pitch rises and falls with the clock speed. One ratchet click for each of the 42 km markers. A sub pulse on the beat and a low fifth that opens up |
| 2.00–2.80 | The last seconds tick on eighth notes: `:17`, `:18`, `:19`. | Tick-tock crescendo over a thin swell of held breath |
| 2.80 | **Stop on 2:38:20.** The playhead flashes full height, like a photo-finish line. | Stop click, low impact and a bright shimmer. Everything else cuts dead, and the frozen time sits in its own reverb tail |
| 2.92–3.16 | A hairline strikes through `2:38:21` in the top-right `RECORD TO BEAT` label, and the old time dims. | A short dry pen scratch, top right |
| 3.16–3.80 | **The three pieces.** The bottom, middle and top bands each whip left and lock. The orange 3 builds from three slices. | Three right-to-left whooshes, each ending on a latch and one note of the sonic logo: E5, B5, F#6 |
| 3.44–3.96 | The start/finish line contracts and turns into the orange tick. | |
| 4.00 | **Logo.** The tagline types on. The footer rolls to `@sub3piece` and `TRAIN · RACE · RECOVER · REPEAT`. | The stacked fifths resolve onto D (a D6/9 chord), struck mallets over a low D |
| 3.80–6.80 | The hold: the lockup pushes in by 2.5% while the frame chrome stays still, so the hold keeps moving without adding anything new. | The chord rings out |
| 6.30–6.80 | Fade to ink | A soft stopwatch reset click (start, stop, reset), and the tail fades |

## Design system

Built from the sub3piece design system (tokens, `assets/logo.md`, the channel banner and the video `TitleCard`).

- **Colour:** ink `#0C0D10`, paper `#F1F0EC`, graphite `#8A8B90`/`#6E7077`/`#4A4C53` and line `#26282E`. Signal orange `#FF5A2C` is the only accent, and it moves through the piece: playhead, photo-finish line, then the tick and the 3. The zone palette appears only on data: the effort trace and the zone swatch.
- **Type:** the wordmark is set in Space Grotesk 700 at -0.04em, lowercase, with the 3 in signal, as `logo.md` specifies. All data and labels are in Space Mono, uppercase and widely tracked. The tagline is lowercase mono, as on the banner.
- **Graphic language:** the banner's ink panel with a 60 px hairline grid, grain and vignette. Hairline rules frame the stage, and the footer follows the `TitleCard` layout. Margins are 120 px on the 1920 stage, inside title-safe.
- **Motion:** `--ease-out` cubic-bezier(0.2, 0, 0, 1) and `--ease-in-out` cubic-bezier(0.65, 0, 0.35, 1). Digit snaps take 90 ms and band whips 240 ms. Nothing bounces or overshoots. The only slow move is the push-in during the hold. Motion blur is real temporal supersampling with a 180° shutter, up to 64 samples per frame.

The effort trace and the zones in it are illustrative, not data from a real run. The record is the `RECORD` constant in `intro.html`, and the clock stops one second inside it (`RACE_END`). If the record changes, update both and rebuild; the sound retimes itself.

## Rebuild

```
cd edit
./build.sh            # both 4K masters, the 1080p copy, the WAV and the end frame
./build.sh 24 2       # any other frame rate, e.g. 24p
./build.sh 30 1       # quick 1080p check
```

The build needs Node with Playwright (Chromium), Python 3 with numpy and scipy, and ffmpeg.

- `edit/intro.html` is the renderer. Everything is a function of time. The timeline is the `T` object, and the corner copy is in `drawFrameChrome`. Open it in a browser with `?t=3.5` to see any moment.
- `edit/render.cjs` drives it headless. It exports `events.json` (every tick and km crossing) and renders the frames.
- `edit/sound.py` synthesises the audio from `events.json`, so retiming the picture retimes the sound.
- `edit/build.sh` handles grain, encoding and muxing.
