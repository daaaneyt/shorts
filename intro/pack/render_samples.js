/* Render the sample clips in samples/ with the same engine the generator uses.
 *
 *   node render_samples.js [samples-dir] [only]      (only: render just the samples whose name contains this text)
 *
 * Needs: node, `npm i playwright-core` (or playwright) with a Chromium, and ffmpeg.
 * Set CHROME=/path/to/chrome if Playwright can't find its own Chromium.
 * Each clip becomes a ProRes 4444 .mov with alpha at 30 fps (1920x1080, or 1080x1920 for Shorts cards), encoded the way build.sh encodes the intro.
 */
const fs = require('fs'), path = require('path'), os = require('os'), { execFileSync } = require('child_process');
let pw; try { pw = require('playwright'); } catch (e) { try { pw = require('playwright-core'); } catch (e2) { pw = require('/opt/node22/lib/node_modules/playwright'); } }

const SAMPLES = [
  { name: 'strip_week-07', cfg: { type: 'strip', text: 'WEEK 07', kind: 'ink', hold: 2.5 } },
  { name: 'strips_london-marathon', cfg: { type: 'strip', text: 'LONDON MARATHON 2027\nRUNNING FOR SPINAL RESEARCH', kind: 'ink', kind2: 'orange', hold: 3, pop: true } },
  { name: 'lower-third_adam', cfg: { type: 'lower', text: 'Adam\nSub-3 attempt · Week 7', kind: 'paper', kind2: 'orange', hold: 3, tape: true } },
  { name: 'title_the-long-run', cfg: { type: 'title', text: 'THE LONG RUN', kind: 'paper', hold: 3, tape: true, underline: true } },
  { name: 'tiles_2-38-21', cfg: { type: 'tiles', text: '2:38:21', hold: 3 } },
  { name: 'chapter_week-07', cfg: { type: 'chapter', text: 'WEEK 07\nThe long run', kind: 'ink', hold: 2, underline: true } },
  // Shorts cards are 1080x1920. `endcard` makes a ready-to-append MP4 (silent audio track) on the given background; `still` saves a transparent PNG.
  { name: 'shorts-card_new-video', cfg: { type: 'cta', frame: 'v', text: 'NEW YOUTUBE VIDEO\nNOW LIVE\nLINK IN BIO', hold: 3, pop: true }, endcard: '0C0D10', still: true },
  { name: 'shorts-card_with-title', cfg: { type: 'cta', frame: 'v', text: 'NEW ON YOUTUBE\nOUT NOW\nLINK IN BIO\nWeek 7: the long run', headline: 'scrap', arrow: 'right', hold: 3 }, endcard: '0C0D10' },
];

(async () => {
  const outDir = path.resolve(process.argv[2] || path.join(__dirname, 'samples')), only = process.argv[3] || ''; fs.mkdirSync(outDir, { recursive: true });
  const launch = { args: ['--no-sandbox'] }; if (process.env.CHROME) launch.executablePath = process.env.CHROME;
  const browser = await pw.chromium.launch(launch), page = await browser.newPage({ viewport: { width: 400, height: 300 } });
  page.on('pageerror', (e) => console.log('PAGE ERROR', e.message));
  await page.goto('file://' + path.join(__dirname, 'paper-text-generator.html'));
  await page.evaluate(() => PaperText.fontsReady());
  for (const s of SAMPLES.filter((x) => x.name.includes(only))) {
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'pt-')), n = await page.evaluate((cfg) => {
      window.__clip = PaperText.buildClip(Object.assign({ fps: 30, scale: 1 }, cfg)); const c = document.createElement('canvas'); c.width = window.__clip.W; c.height = window.__clip.H; window.__cv = c; return window.__clip.nFrames;
    }, s.cfg);
    for (let i = 0; i < n; i++) {
      const d = await page.evaluate((i) => { window.__clip.draw(window.__cv.getContext('2d'), i); return window.__cv.toDataURL('image/png'); }, i);
      fs.writeFileSync(path.join(tmp, String(i + 1).padStart(4, '0') + '.png'), Buffer.from(d.split(',')[1], 'base64'));
    }
    if (s.still) fs.copyFileSync(path.join(tmp, String(Math.min(n, 36)).padStart(4, '0') + '.png'), path.join(outDir, 'sample_' + s.name + '_still.png'));
    if (s.endcard) {
      const size = await page.evaluate(() => window.__clip.W + 'x' + window.__clip.H), mp4 = path.join(outDir, 'sample_' + s.name + '_endcard.mp4');
      execFileSync('ffmpeg', ['-v', 'error', '-y', '-f', 'lavfi', '-i', 'color=c=0x' + s.endcard + ':s=' + size + ':r=30', '-framerate', '30', '-i', path.join(tmp, '%04d.png'), '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo',
        '-filter_complex', '[0:v][1:v]overlay=shortest=1,format=yuv420p[v]', '-map', '[v]', '-map', '2:a', '-shortest', '-c:v', 'libx264', '-crf', '17', '-preset', 'slow', '-c:a', 'aac', '-b:a', '128k',
        '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-movflags', '+faststart', mp4]);
      console.log(path.basename(mp4), (fs.statSync(mp4).size / 1048576).toFixed(1), 'MB');
    }
    const out = path.join(outDir, 'sample_' + s.name + '.mov');
    execFileSync('ffmpeg', ['-v', 'error', '-y', '-framerate', '30', '-i', path.join(tmp, '%04d.png'), '-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuva444p10le',
      '-c:v', 'prores_ks', '-profile:v', '4444', '-alpha_bits', '8', '-qscale:v', '28', '-vendor', 'apl0', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', out]);
    fs.rmSync(tmp, { recursive: true, force: true });
    console.log(path.basename(out), n, 'frames,', (fs.statSync(out).size / 1048576).toFixed(1), 'MB');
  }
  await browser.close();
})();
