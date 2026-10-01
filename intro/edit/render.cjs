// Drive intro.html in headless Chromium.
//   node render.cjs events <out.json>
//   node render.cjs stills <scale> <outdir> <t1,t2,...> [fps]   (motion blur at fps)
//   node render.cjs frames <fps> <scale> <outdir> [workers]
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const PAGE = 'file://' + path.resolve(__dirname, 'intro.html');

async function openPage(browser, scale) {
  const W = Math.round(1920 * scale), H = Math.round(1080 * scale);
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  await page.goto(`${PAGE}?scale=${scale}`);
  await page.evaluate(() => window.ready);
  return { page, W, H };
}
async function shot(p, file) {
  await p.page.screenshot({ path: file, type: 'png', clip: { x: 0, y: 0, width: p.W, height: p.H } });
}

(async () => {
  const [mode, ...a] = process.argv.slice(2);
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files', '--disable-gpu'] });
  try {
    if (mode === 'events') {
      const p = await openPage(browser, 0.25);
      fs.writeFileSync(a[0], JSON.stringify(await p.page.evaluate(() => exportEvents())));
    } else if (mode === 'stills') {
      const [scale, out, times, fps] = [+a[0], a[1], a[2].split(',').map(Number), +(a[3] || 0)];
      fs.mkdirSync(out, { recursive: true });
      const p = await openPage(browser, scale);
      for (const t of times) {
        const n = fps ? await p.page.evaluate(([t, f]) => renderFrame(t, f), [t, fps])
                      : await p.page.evaluate(t => (drawScene(t), 1), t);
        await shot(p, path.join(out, `t${t.toFixed(3)}.png`));
        console.log(t, n);
      }
    } else if (mode === 'frames') {
      const [fps, scale, out, workers] = [+a[0], +a[1], a[2], +(a[3] || 4)];
      fs.mkdirSync(out, { recursive: true });
      const probe = await openPage(browser, 0.25);
      const dur = await probe.page.evaluate(() => T.end);
      await probe.page.close();
      const N = Math.round(dur * fps);
      let next = 0, done = 0; const t0 = Date.now();
      await Promise.all(Array.from({ length: workers }, async () => {
        const p = await openPage(browser, scale);
        for (;;) {
          const i = next++; if (i >= N) break;
          const file = path.join(out, `f${String(i).padStart(4, '0')}.png`);
          if (fs.existsSync(file)) { done++; continue; }
          const n = await p.page.evaluate(([t, f]) => renderFrame(t, f), [i / fps, fps]);
          await shot(p, file + '.tmp.png'); fs.renameSync(file + '.tmp.png', file);
          done++;
          if (done % 10 === 0 || n > 1) process.stdout.write(`frame ${i} (${n} samples) ${done}/${N} ${((Date.now() - t0) / 1000).toFixed(0)}s\n`);
        }
      }));
    }
  } finally { await browser.close(); }
})();
