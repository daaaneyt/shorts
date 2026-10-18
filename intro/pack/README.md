# sub3piece paper text

Torn-paper text elements in the same style as the intro, for Premiere Pro and DaVinci Resolve. You type the words, pick a look, and export a transparent clip with the slap-on, the stop-motion wobble and the tear-away already animated.

## Quick start
1. Open **`paper-text-generator.html`** in Chrome, Edge, Safari or Firefox. It's a single file with no install, and it works offline. The same tool is also published as a private claude.ai page, which works the same way.
2. Pick an element, type your text, adjust the look. The preview loops live.
3. Press **Export clip (.zip)**. Unzip it, and import the PNG sequence into your editor (below).

The clip is a full frame (1920×1080, or 1080×1920 for Shorts) with the element already placed, so you drop it on the top track and it's in position. Pick a spot with the position grid, or drag the element in the preview.

## The elements
| Element | What it is | Text |
| --- | --- | --- |
| **Shorts card** | A vertical "new video now live, link in bio" announcement: a small label, big ransom-note words, a call-to-action strip with a bouncing arrow, and an optional video title and thumbnail | Four boxes (see below) |
| **Strip** | Mono caps on a torn strip, the way "LONDON MARATHON 2027" sits in the intro | One strip per line, alternating the two papers |
| **Lower third** | A name plate with a subtitle strip pasted under it | Line 1 is the name; other lines become the subtitle |
| **Title** | A big headline on one torn scrap | One or more lines |
| **Stat tiles** | Each character on its own ransom-note tile, stamped on one by one, like 2:38:21 | One line. Letters, numbers, `:` and `.` |
| **Chapter card** | A full-frame sheet with big text that tears open onto your footage | One line per row |

**Extras:** tape on the corners, little scraps that pop out when it lands, and a hand-drawn orange underline. **Motion:** hold time, wobble amount, arrive (slap or cut), leave (tear, cut, or stay). **New tear pattern** re-rolls every random edge.

Long text shrinks to fit the frame, so a long line never runs off the edge.

## The Shorts card: "New YouTube video now live (link in bio)"
Pick **Shorts card** and the frame switches to vertical 1080×1920. It has four boxes, and each one is a piece of the card:

| Box | Default | What it does |
| --- | --- | --- |
| Small label | `NEW YOUTUBE VIDEO` | A mono-caps strip across the top of the big words |
| Big words | `NOW LIVE` | Each word gets its own row of ransom-note tiles that stamp on one by one (or choose **One scrap** for each word stacked on a single torn scrap) |
| Call to action | `LINK IN BIO` | An orange strip, with a torn arrow that hops towards the bio (up, right, down, left or none) |
| Video title | empty | Optional. A white strip with the name of the video |

Leave a box empty and that piece drops out, so `NEW ON YOUTUBE` / `OUT NOW` / `LINK IN BIO` or just `NOW LIVE` on its own both work. It also takes **Tape**, **Pop-out scraps**, and its own paper colour for the label, the big words and the call to action.

**Video thumbnail:** choose an image and it's cropped to 16:9 and taped on above the words, with a **Photocopy look** option that matches Adam in the intro. The image never leaves your browser.

**Safe area:** tick **Safe area** under the preview to see the shaded zones where Shorts, Reels and TikTok draw their caption block, buttons and top bar over your picture. The card is placed inside the clear area by default, using conservative margins of about 11% at the top, 22% at the bottom and 7% at the sides. Those margins are my estimate rather than any platform's published figures, so check one export on your phone before you rely on them.

**Ways to use it:**
- **As an end card:** `samples/sample_shorts-card_*_endcard.mp4` are finished 3.5 s clips on an ink background, with a silent audio track, that you can append to the end of a Short as they are. For your own words, export the transparent clip from the tool and put it over a plain background in your editor.
- **Over your footage:** drop the transparent clip on the track above your Short.
- **As a still:** **Export still (.png)** gives one transparent frame, for a cover image or a story. `samples/sample_shorts-card_new-video_still.png` is an example.

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
- **Frame rate:** match your timeline (24, 25, 30, 50 or 60). The stop-motion steps run 10 a second, so 30 fps (three identical frames per step) is the cleanest.
- **10 fps (smallest, same look):** because the animation only changes 10 times a second, a 10 fps export looks identical but is about three times smaller. A Shorts card with a thumbnail is about 90 MB at 30 fps and about 33 MB at 10. Import it and set the clip to 10 fps (Interpret Footage in Premiere, Clip Attributes in Resolve); on a 30 fps timeline it holds each frame for three.
- **Frame size:** 1920×1080 (or 1080×1920 for Shorts), or double that for a 4K timeline.
- **Hold:** how long the element sits before it tears away. To change it, just export again with a different hold, which takes a few seconds. You can also cut the clip in the middle of the hold and repeat a stretch of it; the wobble is random every step, so the join doesn't show.
- **Arrive and Leave:** Slap lands with a small kick, and Tear rips the element in two and throws the halves out of frame. Choose Stay if you want to end the clip with the element still on screen.
- **Keep text inside the title-safe area.** Lower-left and bottom-centre are already placed with margins.
- **Export still (.png)** gives one transparent frame for thumbnails and static use.

## What's in this folder
| Path | What it is |
| --- | --- |
| `paper-text-generator.html` | The tool: one file, fonts inside, no install |
| `samples/` | Ready-made ProRes 4444 alpha clips, one per element, to test your editor, plus two finished Shorts end-card MP4s and a transparent Shorts card still |
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
