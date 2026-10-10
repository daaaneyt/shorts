# sub3piece paper text

Torn-paper text elements in the same style as the intro, for Premiere Pro and DaVinci Resolve. You type the words, pick a look, and export a transparent clip with the slap-on, the stop-motion wobble and the tear-away already animated.

## Quick start
1. Open **`paper-text-generator.html`** in Chrome, Edge, Safari or Firefox. It's a single file with no install, and it works offline. The same tool is also published as a private claude.ai page, which works the same way.
2. Pick an element, type your text, adjust the look. The preview loops live.
3. Press **Export clip (.zip)**. Unzip it, and import the PNG sequence into your editor (below).

The clip is a full 1920×1080 frame with the element already placed, so you drop it on the top track and it's in position. Pick a spot with the position grid, or drag the element in the preview.

## The elements
| Element | What it is | Text |
| --- | --- | --- |
| **Strip** | Mono caps on a torn strip, the way "LONDON MARATHON 2027" sits in the intro | One strip per line, alternating the two papers |
| **Lower third** | A name plate with a subtitle strip pasted under it | Line 1 is the name; other lines become the subtitle |
| **Title** | A big headline on one torn scrap | One or more lines |
| **Stat tiles** | Each character on its own ransom-note tile, stamped on one by one, like 2:38:21 | One line. Letters, numbers, `:` and `.` |
| **Chapter card** | A full-frame sheet with big text that tears open onto your footage | One line per row |

**Extras:** tape on the corners, little scraps that pop out when it lands, and a hand-drawn orange underline. **Motion:** hold time, wobble amount, arrive (slap or cut), leave (tear, cut, or stay). **New tear pattern** re-rolls every random edge.

Long text shrinks to fit the frame, so a long line never runs off the edge.

## Batch: a whole video's worth in one go
Open **Batch: one clip per line**, put one clip per line, and press **Export all**. Add `| 4` to set a clip's hold in seconds, and `//` for a line break inside a clip:

```
WEEK 07
LONG RUN // BY THE SEA | 4
5K PB | 3
```

Everything arrives in a single zip, one folder per clip, numbered in order. It uses the look currently set in the tool.

## Getting it into your editor
The export is a PNG sequence with transparency. The steps below are from how the apps normally behave, so menu names can differ a little between versions.

**Premiere Pro:** File > Import, open the unzipped folder, pick the first frame, tick **Image Sequence**, then Import. Right-click the clip > Modify > Interpret Footage > *Assume this frame rate* and enter the frame rate you exported (30 by default). Put it on a track above your footage.

**DaVinci Resolve:** On the Media page, drag the unzipped folder into the media pool. The numbered frames show up as one clip. If it picked a different frame rate, set it in Clip Attributes. Drag it onto a track above your footage.

If you'd rather have a single file, the **ready-made clips** in `samples/` are ProRes 4444 with alpha and drop in like any other clip. They're the quickest way to check the transparency works in your setup.

## Settings worth knowing
- **Frame rate:** match your timeline (24, 25, 30, 50 or 60). The stop-motion steps run 10 a second, so 30 fps (three frames per step) is the cleanest.
- **Frame size:** 1920×1080, or 3840×2160 for a 4K timeline.
- **Hold:** how long the element sits before it tears away. To change it, just export again with a different hold, which takes a few seconds. You can also cut the clip in the middle of the hold and repeat a stretch of it; the wobble is random every step, so the join doesn't show.
- **Arrive and Leave:** Slap lands with a small kick, and Tear rips the element in two and throws the halves out of frame. Choose Stay if you want to end the clip with the element still on screen.
- **Keep text inside the title-safe area.** Lower-left and bottom-centre are already placed with margins.
- **Export still (.png)** gives one transparent frame for thumbnails and static use.

## What's in this folder
| Path | What it is |
| --- | --- |
| `paper-text-generator.html` | The tool: one file, fonts inside, no install |
| `samples/` | Six ready-made ProRes 4444 alpha clips, one per element, to test your editor |
| `fonts/` | Space Grotesk and Space Mono Bold, to match the text if you add your own in the editor |
| `src/` | The source for the tool, in readable pieces |
| `build.py` | Rebuilds the single file from `src/` |
| `render_samples.js` | Re-renders `samples/` from the tool's own engine |

## Why a generator and not an editable template
A native, editable Premiere template (`.mogrt`) can only be made in After Effects, and a Resolve title would need a Fusion macro built and tested in Resolve. This session can't run either app, and an untested template that fails to load is worse than none. The generator gives the same result with the paper texture, ink and shadows rendered into the clip, so the text wobbles and tears with the paper, which a text layer sitting on top of a paper clip wouldn't.

If you do want true editable templates later, the right route is to rebuild a couple of these in After Effects and export them as `.mogrt`; the clips here are a good reference for the look.

## Fonts
Space Grotesk and Space Mono are open fonts (SIL Open Font License). They're embedded in the tool and also provided in `fonts/`.

## Rebuilding
`python3 build.py` rebuilds `paper-text-generator.html` from `src/`. `node render_samples.js` re-renders the sample clips; it needs Node, Playwright with a Chromium, and ffmpeg.
