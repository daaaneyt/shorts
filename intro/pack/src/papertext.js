/* sub3piece paper-text engine
 *
 * Draws the intro's torn-paper elements (plates with printed text, ransom-note tiles, full-frame
 * chapter sheets) and animates them the same way: stop-motion steps (10 a second), a slap-on landing,
 * a small "boil" jitter every step, and a tear-away to transparent at the end.
 *
 * Everything is in design pixels on a 1920x1080 frame; `scale` (1 or 2) multiplies that for export.
 * No dependencies. Needs the fonts "Space Grotesk" (700) and "Space Mono" (700) to be loaded.
 *
 *   const clip = PaperText.buildClip({ type: 'strip', text: 'WEEK 07', hold: 2.5 });
 *   clip.nFrames; clip.draw(ctx, frameIndex);   // ctx is a (1920*scale) x (1080*scale) 2D context
 */
(function (root) {
  'use strict';

  const W0 = 1920, H0 = 1080, MD = 100;          // frame size; full-frame sheets overhang by MD
  const STEP_RATE = 10;                           // animation steps a second
  const KINDS = ['paper', 'ink', 'orange', 'white'];
  const BASE = { ink: [20, 21, 25], paper: [243, 241, 234], white: [251, 250, 246], orange: [255, 90, 44], tape: [236, 226, 190] };
  const CORE = { ink: '#D2CFC5', paper: '#FFFFFD', white: '#FFFFFF', orange: '#FFE4D3', tape: '#FAF6E4' };
  const TEXT = { ink: '#0C0D10', paper: '#F3F1EA', orange: '#FF5A2C', white: '#FBFAF6' };
  const LIGHT_ON = { ink: 'paper', paper: 'ink', white: 'ink', orange: 'ink' };   // default text colour per plate

  // ------------------------------------------------------------------ small utilities
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  function strSeed(s) { let h = 2166136261 >>> 0; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
  function mulberry32(a) {
    return function () { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  }
  class RNG {
    constructor(seed) { this.f = mulberry32(typeof seed === 'string' ? strSeed(seed) : seed >>> 0); this.spare = null; }
    next() { return this.f(); }
    uni(a, b) { return a + (b - a) * this.f(); }
    int(n) { return Math.floor(this.f() * n); }
    pick(a) { return a[this.int(a.length)]; }
    sign() { return this.f() < 0.5 ? -1 : 1; }
    normal() {
      if (this.spare !== null) { const s = this.spare; this.spare = null; return s; }
      let u = 0; while (u === 0) u = this.f(); const v = this.f(), m = Math.sqrt(-2 * Math.log(u));
      this.spare = m * Math.sin(2 * Math.PI * v); return m * Math.cos(2 * Math.PI * v);
    }
  }
  const rngOf = (...k) => new RNG(k.join('|'));

  function mk(w, h) { const c = document.createElement('canvas'); c.width = Math.max(1, Math.ceil(w)); c.height = Math.max(1, Math.ceil(h)); return c; }
  const mctx = mk(4, 4).getContext('2d');

  const cache = new Map();
  function memo(key, fn) {
    if (!cache.has(key)) { if (cache.size > 140) cache.clear(); cache.set(key, fn()); }
    return cache.get(key);
  }

  // ------------------------------------------------------------------ noise, paper, torn edges
  /** Gaussian-ish noise as a black/white canvas whose alpha carries the noise, at 1/f resolution upscaled. */
  function noiseCanvas(w, h, f, rng, amp) {
    f = Math.max(1, Math.round(f));
    const lw = Math.ceil(w / f) + 2, lh = Math.ceil(h / f) + 2;
    const c = mk(lw, lh), x = c.getContext('2d'), id = x.createImageData(lw, lh), d = id.data;
    for (let i = 0; i < lw * lh; i++) {
      const n = rng.normal(), v = n > 0 ? 255 : 0;
      d[i * 4] = d[i * 4 + 1] = d[i * 4 + 2] = v; d[i * 4 + 3] = Math.min(255, Math.abs(n) * amp * 255);
    }
    x.putImageData(id, 0, 0);
    if (f === 1) return c;
    const o = mk(w, h), ox = o.getContext('2d');
    ox.imageSmoothingEnabled = true; ox.imageSmoothingQuality = 'high';
    ox.drawImage(c, 0, 0, lw * f, lh * f);
    return o;
  }

  function paperTexture(w, h, kind, rng, S) {
    const c = mk(w, h), x = c.getContext('2d'), b = BASE[kind];
    x.fillStyle = `rgb(${b[0]},${b[1]},${b[2]})`; x.fillRect(0, 0, w, h);
    const dark = kind === 'ink', m = kind === 'orange' ? 0.7 : 1.0;      // white flecks show hard on near-black, so ink is flatter
    x.drawImage(noiseCanvas(w, h, 44 * S, rng, (dark ? 0.012 : 0.055) * m), 0, 0);
    x.drawImage(noiseCanvas(w, h, 9 * S, rng, (dark ? 0.012 : 0.04) * m), 0, 0);
    x.drawImage(noiseCanvas(w, h, S, rng, (dark ? 0.035 : 0.07) * m), 0, 0);
    // fibres: short faint hairs, light on dark paper, mixed on light paper
    const n = Math.floor(w * h / (S * S) / 650);
    x.lineCap = 'round'; x.lineWidth = Math.max(1, 0.8 * S);
    for (let i = 0; i < n; i++) {
      const cx = rng.uni(0, w), cy = rng.uni(0, h), a = rng.uni(0, Math.PI), ln = rng.uni(3, 18) * S / 2;
      const light = kind === 'ink' ? true : rng.next() < 0.45;
      x.strokeStyle = light ? `rgba(255,255,255,${kind === 'ink' ? rng.uni(0.03, 0.11) : rng.uni(0.1, 0.32)})` : `rgba(0,0,0,${rng.uni(0.04, 0.12)})`;
      x.beginPath(); x.moveTo(cx - Math.cos(a) * ln, cy - Math.sin(a) * ln); x.lineTo(cx + Math.cos(a) * ln, cy + Math.sin(a) * ln); x.stroke();
    }
    return c;
  }

  function blur1d(a, sigma) {                       // three box passes ~ a gaussian
    const n = a.length; let w = Math.max(1, Math.round(Math.sqrt(4 * sigma * sigma + 1))); if (w % 2 === 0) w++;
    const r = (w - 1) >> 1; let src = a, dst = new Float32Array(n);
    for (let p = 0; p < 3; p++) {
      let acc = 0; for (let i = -r; i <= r; i++) acc += src[clamp(i, 0, n - 1)];
      for (let i = 0; i < n; i++) { dst[i] = acc / w; acc += src[clamp(i + r + 1, 0, n - 1)] - src[clamp(i - r, 0, n - 1)]; }
      const t = src; src = dst; dst = t;
    }
    return src;
  }
  function jag(n, rng, octaves) {                   // multi-octave smooth noise, each octave unit-variance * amp
    const d = new Float32Array(n);
    for (const [sig, amp] of octaves) {
      const pad = Math.ceil(4 * sig) + 2, m = n + 2 * pad; let r = new Float32Array(m);
      for (let i = 0; i < m; i++) r[i] = rng.normal();
      if (sig > 0.3) r = blur1d(r, sig);
      let s = 0, s2 = 0; for (let i = 0; i < m; i++) { s += r[i]; s2 += r[i] * r[i]; }
      const std = Math.sqrt(Math.max(0, s2 / m - (s / m) * (s / m))) + 1e-6;
      for (let i = 0; i < n; i++) d[i] += r[pad + i] / std * amp;
    }
    return d;
  }
  /** A jagged line from p0 to p1, pinned at both ends. */
  function tornPath(p0, p1, rng, amp, S) {
    const dx = p1[0] - p0[0], dy = p1[1] - p0[1], L = Math.hypot(dx, dy), st = 2.5 * S;
    const n = Math.max(8, Math.floor(L / st)), nx = -dy / L, ny = dx / L;
    const d = jag(n, rng, [[90 * S / st, 14 * S * amp], [18 * S / st, 5 * S * amp], [3 * S / st, 1.8 * S * amp], [0, 0.8 * S]]);
    const pts = [];
    for (let i = 0; i < n; i++) {
      const t = i / (n - 1), win = clamp(Math.min(t, 1 - t) * L / (30 * S), 0, 1);
      pts.push([p0[0] + dx * t + nx * d[i] * win, p0[1] + dy * t + ny * d[i] * win]);
    }
    return pts;
  }
  /** Torn edges along every side of a polygon given by its corners. */
  function tornPoly(c, rng, amp, S) {
    const poly = [];
    for (let i = 0; i < c.length; i++) {
      const a = c[i], b = c[(i + 1) % c.length], ln = Math.hypot(b[0] - a[0], b[1] - a[1]);
      const p = tornPath(a, b, rng, amp * Math.min(1, ln / (260 * S)), S);
      for (let j = 0; j < p.length - 1; j++) poly.push(p[j]);
    }
    return poly;
  }
  function tornRect(x, y, w, h, rng, amp, S) { return tornPoly([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], rng, amp, S); }
  /** The white paper core that shows past the printed face along a tear: the polygon pushed outward by a noisy width. */
  function offsetPoly(poly, rng, S, k) {
    const n = poly.length; let A = 0;
    for (let i = 0; i < n; i++) { const p = poly[i], q = poly[(i + 1) % n]; A += p[0] * q[1] - q[0] * p[1]; }
    const sgn = A > 0 ? 1 : -1, a = jag(n, rng, [[2.8, 1]]), b = jag(n, rng, [[0.5, 1]]), out = [];
    for (let i = 0; i < n; i++) {
      const p0 = poly[(i - 1 + n) % n], p1 = poly[(i + 1) % n], tx = p1[0] - p0[0], ty = p1[1] - p0[1], L = Math.hypot(tx, ty) || 1;
      const w = Math.max(0.3, 1 + 4.2 * Math.abs(a[i]) + 1.1 * b[i]) * S * k;
      out.push([poly[i][0] + sgn * ty / L * w, poly[i][1] - sgn * tx / L * w]);
    }
    return out;
  }
  function pathOf(x, pts) { x.beginPath(); x.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) x.lineTo(pts[i][0], pts[i][1]); x.closePath(); }

  // ------------------------------------------------------------------ type
  const fontStr = (face, px) => face === 'mono' ? `700 ${px}px "Space Mono", monospace` : `700 ${px}px "Space Grotesk", sans-serif`;
  function textWidth(text, face, px, tracking) {
    mctx.font = fontStr(face, px);
    if (!tracking) return mctx.measureText(text).width;
    let w = 0; for (const ch of text) w += mctx.measureText(ch).width + tracking * px;
    return w - tracking * px;
  }
  /** Print text centred at (cx, cy) on ctx with a little uneven ink. Sizes are already multiplied by S. */
  function printText(x, text, face, px, color, tracking, cx, cy, S, rng) {
    const tw = textWidth(text, face, px, tracking), pad = Math.ceil(px * 0.6), w = Math.ceil(tw + 2 * pad), h = Math.ceil(px * 2);
    const t = mk(w, h), tx = t.getContext('2d');
    tx.font = fontStr(face, px); tx.fillStyle = color; tx.textBaseline = 'alphabetic';
    const m = tx.measureText(text), by = h / 2 + (m.actualBoundingBoxAscent - m.actualBoundingBoxDescent) / 2;
    if (!tracking) tx.fillText(text, pad, by);
    else { let p = pad; for (const ch of text) { tx.fillText(ch, p, by); p += tx.measureText(ch).width + tracking * px; } }
    tx.globalCompositeOperation = 'destination-out';
    tx.drawImage(noiseCanvas(w, h, S, rng, 0.14), 0, 0);
    tx.drawImage(noiseCanvas(w, h, 10 * S, rng, 0.07), 0, 0);
    x.drawImage(t, cx - w / 2 + pad - pad, cy - h / 2);   // pad cancels: the text's centre is the canvas centre
  }
  /** Loose printed text with no paper behind it (chapter-card lines, colons between tiles). */
  function textSprite(text, face, px, color, tracking, S, seed) {
    const rng = rngOf('text', seed, text), pxS = px * S, tw = textWidth(text, face, pxS, tracking);
    const w = Math.ceil(tw + pxS), h = Math.ceil(pxS * 1.7), c = mk(w, h), x = c.getContext('2d');
    printText(x, text, face, pxS, color, tracking, w / 2, h / 2, S, rng);
    return { cv: c, pw: w / 2, ph: h / 2, w: w / S, h: h / S };
  }

  // ------------------------------------------------------------------ scraps (torn plates)
  /** A torn plate. `content(ctx, ox, oy, W, H, S, rng)` prints on it (sizes in device px). */
  function makeScrap(o) {
    const S = o.S, pad = Math.round(24 * S), W = Math.round(o.w * S), H = Math.round(o.h * S);
    const cw = W + 2 * pad + Math.round(16 * S), ch = H + 2 * pad + Math.round(16 * S), ox = (cw - W) / 2, oy = (ch - H) / 2;
    const rng = rngOf('scrap', o.seed), kind = o.kind;
    const amp = o.amp == null ? 0.5 : o.amp;
    const poly = o.corners ? tornPoly(o.corners.map(([px, py]) => [ox + px * S, oy + py * S]), rng, amp, S) : tornRect(ox, oy, W, H, rng, amp, S);
    const outer = offsetPoly(poly, rng, S, 1);
    const c = mk(cw, ch), x = c.getContext('2d');
    pathOf(x, outer); x.fillStyle = CORE[kind]; x.fill();
    x.save(); pathOf(x, poly); x.clip();
    x.drawImage(paperTexture(cw, ch, kind, rng, S), 0, 0);
    if (o.content) o.content(x, ox, oy, W, H, S, rng);
    x.restore();
    return { cv: c, pw: cw / 2, ph: ch / 2, w: o.w, h: o.h };
  }
  /** A torn disc (the orange sun behind the end card). */
  function makeBlob(radius, kind, seed, S) {
    const rng = rngOf('blob', seed), r = radius * S, pad = Math.round(50 * S), size = Math.ceil(2 * (r + pad)), cx = size / 2;
    const n = Math.floor(2 * Math.PI * r / (2.5 * S)), d = jag(n + 200, rng, [[36, 16 * S], [7, 5 * S], [1.2, 1.8 * S], [0, 0.8 * S]]);
    const pts = [];
    for (let i = 0; i < n; i++) { const a = i / n * 2 * Math.PI, dd = d[100 + i] - (d[100 + n - 1] - d[100]) * i / n; pts.push([cx + (r + dd) * Math.cos(a), cx + (r + dd) * Math.sin(a)]); }
    const outer = offsetPoly(pts, rng, S, 1), c = mk(size, size), x = c.getContext('2d');
    pathOf(x, outer); x.fillStyle = CORE[kind]; x.fill();
    x.save(); pathOf(x, pts); x.clip(); x.drawImage(paperTexture(size, size, kind, rng, S), 0, 0); x.restore();
    return { cv: c, pw: size / 2, ph: size / 2, w: radius * 2, h: radius * 2 };
  }

  // ------------------------------------------------------------------ stop-motion
  function boil(seed, key, step, amt) {
    const r = rngOf('boil', seed, key, step);
    return { dx: r.normal() * 1.4 * amt, dy: r.normal() * 1.4 * amt, dr: r.normal() * 0.35 * amt };
  }

  /** Draw a sprite centred (at its pivot) on design-pixel (x, y). */
  function drawSprite(ctx, spr, S, x, y, rot, sc, shadow, alpha) {
    ctx.save();
    ctx.translate(x * S, y * S); ctx.rotate(rot * Math.PI / 180); ctx.scale(sc, sc);
    if (alpha != null) ctx.globalAlpha = alpha;
    if (shadow && shadow.a > 0) {
      ctx.shadowColor = `rgba(0,0,0,${shadow.a})`; ctx.shadowBlur = 2 * 9 * shadow.lift * S;
      ctx.shadowOffsetX = 6 * shadow.lift * S; ctx.shadowOffsetY = 10 * shadow.lift * S;
    }
    ctx.drawImage(spr.cv, -spr.pw, -spr.ph);
    ctx.restore();
  }

  // ------------------------------------------------------------------ layouts: each returns { parts, tear }
  // part: { spr, x, y (relative to the group's centre), rot, slap (step it lands, or null if always there),
  //         boil, shadow (0..1), key, sgn, w, h, alpha }
  function colorOf(cfg, kind, override) { return TEXT[override && override !== 'auto' ? override : LIGHT_ON[kind]]; }

  function layoutStrips(cfg, S, rng) {
    const lines = cfg.text.split('\n').map(s => s.trim()).filter(Boolean); if (!lines.length) lines.push(' ');
    const sz = cfg.size, px = 40 * sz, parts = []; let y = 0;
    lines.forEach((line, i) => {
      const txt = cfg.caps === false ? line : line.toUpperCase(), kind = (i % 2 === 0 ? cfg.kind : cfg.kind2) || 'ink';
      const tw = textWidth(txt, 'mono', px, 0.14), w = Math.max(cfg.minW || 0, tw + 2 * 46 * sz), h = px * 0.75 + 2 * 30 * sz;
      const spr = makeScrap({ w, h, kind, seed: [cfg.seed, 's', i].join(), S, amp: 0.5,
        content: (x, ox, oy, W, H, S2, r) => printText(x, txt, 'mono', px * S2, colorOf(cfg, kind, i === 0 ? cfg.textColor : 'auto'), 0.14, ox + W / 2, oy + H / 2, S2, r) });
      const sg = i % 2 ? 1 : -1, tilt = cfg.tilt == null ? sg * rng.uni(0.8, 2.0) : cfg.tilt * sg;
      parts.push({ spr, x: i % 2 ? 26 * sz : 0, y: 0, rot: tilt, slap: i * 2, boil: 0.7, shadow: 0.45, key: 'strip' + i, sgn: rng.sign(), w, h, row: i });
    });
    // stack the strips, each overlapping the one above by a few px (they read as pasted on top of each other)
    let top = 0; const hs = parts.map(p => p.h);
    parts.forEach((p, i) => { p.y = top + hs[i] / 2; top += hs[i] - 10 * cfg.size; });
    return { parts, tear: 'v' };
  }

  function layoutLower(cfg, S, rng) {
    const lines = cfg.text.split('\n').map(s => s.trim()).filter(Boolean), sz = cfg.size, parts = [];
    const l1 = lines[0] || ' ', l2 = lines.slice(1).join('  ·  ');
    const px1 = 74 * sz, tw1 = textWidth(l1, 'grotesk', px1, -0.02), w1 = Math.max(cfg.minW || 0, tw1 + 2 * 56 * sz), h1 = px1 * 0.74 + 2 * 36 * sz;
    const k1 = cfg.kind || 'paper';
    const A = makeScrap({ w: w1, h: h1, kind: k1, seed: cfg.seed + 'A', S, amp: 0.5,
      content: (x, ox, oy, W, H, S2, r) => printText(x, l1, 'grotesk', px1 * S2, colorOf(cfg, k1, cfg.textColor), -0.02, ox + W / 2, oy + H / 2, S2, r) });
    parts.push({ spr: A, x: 0, y: 0, rot: cfg.tilt == null ? -rng.uni(0.8, 1.8) : -cfg.tilt, slap: 0, boil: 0.8, shadow: 0.5, key: 'A', sgn: rng.sign(), w: w1, h: h1 });
    if (l2) {
      const px2 = 32 * sz, tw2 = textWidth(l2.toUpperCase(), 'mono', px2, 0.14), w2 = tw2 + 2 * 40 * sz, h2 = px2 * 0.75 + 2 * 26 * sz, k2 = cfg.kind2 || 'orange';
      const B = makeScrap({ w: w2, h: h2, kind: k2, seed: cfg.seed + 'B', S, amp: 0.5,
        content: (x, ox, oy, W, H, S2, r) => printText(x, l2.toUpperCase(), 'mono', px2 * S2, colorOf(cfg, k2, 'auto'), 0.14, ox + W / 2, oy + H / 2, S2, r) });
      parts.push({ spr: B, x: -w1 / 2 + w2 / 2 + 44 * sz, y: h1 / 2 + h2 / 2 - 14 * sz, rot: cfg.tilt == null ? rng.uni(0.8, 1.6) : cfg.tilt, slap: 2, boil: 0.7, shadow: 0.45, key: 'B', sgn: rng.sign(), w: w2, h: h2 });
    }
    return { parts, tear: 'v', anchorX: 'left' };
  }

  function layoutTitle(cfg, S, rng) {
    const lines = cfg.text.split('\n').map(s => s.trim()).filter(Boolean); if (!lines.length) lines.push(' ');
    const sz = cfg.size, px = 118 * sz, lh = px * 1.02, kind = cfg.kind || 'paper';
    const tw = Math.max(...lines.map(l => textWidth(l, 'grotesk', px, -0.03)));
    const w = Math.max(cfg.minW || 0, tw + 2 * 84 * sz), h = lines.length * lh + 2 * 52 * sz - (lh - px * 0.74);
    const spr = makeScrap({ w, h, kind, seed: cfg.seed + 'T', S, amp: 0.6,
      content: (x, ox, oy, W, H, S2, r) => lines.forEach((l, i) => {
        const cy = oy + H / 2 + (i - (lines.length - 1) / 2) * lh * S2;
        printText(x, l, 'grotesk', px * S2, colorOf(cfg, kind, cfg.textColor), -0.03, ox + W / 2, cy, S2, r);
      }) });
    return { parts: [{ spr, x: 0, y: 0, rot: cfg.tilt == null ? rng.uni(-1.8, 1.8) : cfg.tilt, slap: 0, boil: 1, shadow: 0.5, key: 'T', sgn: rng.sign(), w, h }], tear: 'v' };
  }

  const CYCLE_K = ['paper', 'orange', 'white', 'orange', 'paper'], CYCLE_F = ['grotesk', 'mono', 'grotesk', 'grotesk', 'mono'];
  const tileDims = (chars) => chars.map(c => c === ':' || c === '.' ? 76 : c === ' ' ? 70 : 196);
  const rowWidth = (chars) => tileDims(chars).reduce((a, b) => a + b + 15, -15);
  /** One row of ransom-note tiles centred on x = 0 at height yc. k scales it; slap0 is the step its first character lands. */
  function tileRow(cfg, S, rng, chars, k, yc, slap0, tag) {
    const dims = tileDims(chars), total = rowWidth(chars), parts = []; let x = -total * k / 2, ti = 0;
    chars.forEach((ch, i) => {
      const w = dims[i] * k;
      if (ch === ' ') { x += w + 15 * k; return; }
      if (ch === ':' || ch === '.') {
        const spr = textSprite(ch, 'grotesk', 210 * k, TEXT.orange, 0, S, cfg.seed + tag + 'c' + i);
        parts.push({ spr, x: x + w / 2, y: yc, rot: rng.uni(-5, 5), slap: slap0 + i, boil: 1, shadow: 0, key: tag + 'c' + i, sgn: rng.sign(), w: spr.w, h: spr.h });
      } else {
        const kind = cfg.kind === 'mixed' || !cfg.kind ? CYCLE_K[ti % 5] : cfg.kind, face = CYCLE_F[ti % 5], px = (face === 'grotesk' ? 236 : 214) * k, h = 272 * k, txt = ch;
        const spr = makeScrap({ w, h, kind, seed: cfg.seed + tag + 't' + i, S, amp: 0.35,
          content: (xx, ox, oy, W, H, S2, r) => printText(xx, txt, face, px * S2, colorOf(cfg, kind, cfg.textColor), 0, ox + W / 2, oy + H / 2, S2, r) });
        parts.push({ spr, x: x + w / 2, y: yc + rng.uni(-18, 18) * k, rot: rng.uni(-7, 7), slap: slap0 + i, boil: 1, shadow: 0.55, key: tag + 't' + i, sgn: rng.sign(), w, h });
        ti++;
      }
      x += w + 15 * k;
    });
    return { parts, w: total * k, h: 272 * k, last: slap0 + chars.length - 1 };
  }

  function layoutTiles(cfg, S, rng) {
    const chars = [...(cfg.text.split('\n')[0] || ' ')], sz = cfg.size;
    const k = sz * Math.min(1, (cfg.fw - 160) / (rowWidth(chars) * sz));
    return { parts: tileRow(cfg, S, rng, chars, k, 0, 0, '').parts, tear: 'v' };
  }

  function layoutChapter(cfg, S, rng) {
    const lines = cfg.text.split('\n').map(s => s.trim()).filter(Boolean); if (!lines.length) lines.push(' ');
    const sz = cfg.size, kind = cfg.kind || 'ink', parts = [];
    let px = 215 * sz * (lines.length > 2 ? 0.8 : 1);
    const widest = Math.max(...lines.map(l => textWidth(l, 'grotesk', px, -0.02)));
    if (widest > cfg.fw - 140) px *= (cfg.fw - 140) / widest;                    // long lines shrink to the frame
    const sw = cfg.fw + 2 * MD, sh = cfg.fh + 2 * MD;
    const sheet = memo(['sheet', kind, cfg.seed, S].join(), () => {
      const c = mk(sw * S, sh * S), x = c.getContext('2d'); x.drawImage(paperTexture(sw * S, sh * S, kind, rngOf('sheet', cfg.seed, kind), S), 0, 0);
      return { cv: c, pw: sw * S / 2, ph: sh * S / 2, w: sw, h: sh };
    });
    parts.push({ spr: sheet, x: 0, y: 0, rot: 0, slap: null, boil: 0.8, shadow: 0, key: 'sheet', sgn: 1, w: sw, h: sh, sheet: true });
    const colors = kind === 'ink' ? ['paper', 'orange'] : ['ink', 'orange'], gap = px * 1.7;
    lines.forEach((l, i) => {
      const colorKey = cfg.textColor && cfg.textColor !== 'auto' && i === 0 ? cfg.textColor : colors[i % 2];
      const spr = textSprite(l, 'grotesk', px, TEXT[colorKey], -0.02, S, cfg.seed + 'L' + i);
      parts.push({ spr, x: 0, y: (i - (lines.length - 1) / 2) * gap, rot: 0, slap: i * 3, boil: 0.8, shadow: 0, key: 'L' + i, sgn: rng.sign(), w: spr.w, h: spr.h });
    });
    return { parts, tear: 'h', full: true };
  }

  // ------------------------------------------------------------------ the Shorts card: "new video now live, link in bio"
  function drawPhoto(x, img, ox, oy, W, H, S, rng, bw) {            // a thumbnail printed inside a white paper border
    const m = 16 * S, iw = Math.round(W - 2 * m), ih = Math.round(H - 2 * m), nw = img.naturalWidth || img.width, nh = img.naturalHeight || img.height;
    const r = Math.max(iw / nw, ih / nh), sw = iw / r, sh = ih / r, c = mk(iw, ih), cx = c.getContext('2d');
    cx.drawImage(img, (nw - sw) / 2, (nh - sh) / 2, sw, sh, 0, 0, iw, ih);
    if (bw) {                                                        // photocopy look: grey, a bit more contrast
      const d = cx.getImageData(0, 0, iw, ih), q = d.data;
      for (let i = 0; i < q.length; i += 4) { const v = clamp((0.3 * q[i] + 0.59 * q[i + 1] + 0.11 * q[i + 2] - 128) * 1.35 + 134, 0, 255); q[i] = q[i + 1] = q[i + 2] = v; }
      cx.putImageData(d, 0, 0);
    }
    x.drawImage(c, ox + m, oy + m);
    x.drawImage(noiseCanvas(W, H, S, rng, 0.05), ox, oy);
  }
  const ARROW = { up: [0, -1, 0], right: [1, 0, 90], down: [0, 1, 180], left: [-1, 0, 270] };

  function layoutCta(cfg, S, rng) {
    const L = cfg.text.split('\n').map(t => t.trim()), eyebrow = L[0] || '', head = L[1] || '', call = L[2] || '', title = L[3] || '';
    const sz = cfg.size, blocks = []; let slap = 0;
    const plate = (txt, o) => {                                       // one torn plate with printed text
      const tw = textWidth(txt, o.face, o.px, o.tracking), w = Math.max(60, tw + 2 * o.padx), h = o.px * (o.face === 'mono' ? 0.75 : 0.74) + 2 * o.pady;
      const spr = makeScrap({ w, h, kind: o.kind, seed: cfg.seed + o.key, S, amp: 0.5,
        content: (x, ox, oy, W, H, S2, r) => printText(x, txt, o.face, o.px * S2, colorOf(cfg, o.kind, o.color || 'auto'), o.tracking, ox + W / 2, oy + H / 2, S2, r) });
      return { spr, x: 0, y: 0, rot: cfg.tilt == null ? o.tilt : o.tilt < 0 ? -cfg.tilt : cfg.tilt, slap: o.slap, boil: 0.8, shadow: 0.5, key: o.key, sgn: rng.sign(), w, h };
    };
    if (cfg.image) {                                                  // the video thumbnail, taped on
      const w = Math.min(880, cfg.fw - 200) * sz, h = w * 9 / 16;
      const spr = makeScrap({ w, h, kind: 'white', seed: cfg.seed + 'photo', S, amp: 0.4, content: (x, ox, oy, W, H, S2, r) => drawPhoto(x, cfg.image, ox, oy, W, H, S2, r, cfg.photoBW) });
      blocks.push({ parts: [{ spr, x: 0, y: 0, rot: cfg.tilt == null ? -rng.uni(1.6, 3) : -cfg.tilt, slap, boil: 0.8, shadow: 0.55, key: 'photo', sgn: rng.sign(), w, h, tapeHere: true }], h, gap: -14 * sz });
      slap += 2;
    }
    if (eyebrow) {
      const p = plate(eyebrow.toUpperCase(), { face: 'mono', px: 38 * sz, tracking: 0.14, padx: 40 * sz, pady: 24 * sz, kind: cfg.kind || 'ink', key: 'eyebrow', tilt: 1.6, slap, color: cfg.textColor });
      blocks.push({ parts: [p], h: p.h, gap: 30 * sz }); slap += 2;
    }
    const words = head.split(/\s+/).filter(Boolean).slice(0, 3);
    if (words.length && cfg.headline === 'scrap') {                   // the big words on one torn scrap
      const px = 170 * sz, lh = px * 1.0, lines = words.map(w => w.toUpperCase()), tw = Math.max(...lines.map(l => textWidth(l, 'grotesk', px, -0.03)));
      const w = tw + 2 * 76 * sz, h = lines.length * lh + 2 * 46 * sz - (lh - px * 0.74), kind = cfg.kind3 && cfg.kind3 !== 'mixed' ? cfg.kind3 : 'paper';
      const spr = makeScrap({ w, h, kind, seed: cfg.seed + 'head', S, amp: 0.6, content: (x, ox, oy, W, H, S2, r) => lines.forEach((l, i) =>
        printText(x, l, 'grotesk', px * S2, colorOf(cfg, kind, cfg.textColor), -0.03, ox + W / 2, oy + H / 2 + (i - (lines.length - 1) / 2) * lh * S2, S2, r)) });
      blocks.push({ parts: [{ spr, x: 0, y: 0, rot: cfg.tilt == null ? -rng.uni(1, 2.2) : cfg.tilt, slap, boil: 1, shadow: 0.55, key: 'head', sgn: rng.sign(), w, h }], h, gap: -12 * sz }); slap += 2;
    } else if (words.length) {                                        // the big words as ransom-note tiles, one word a row
      const rows = words.map(w => [...w.toUpperCase()]), k = sz * Math.min(1, (cfg.fw - 200) / (Math.max(...rows.map(rowWidth)) * sz));
      const rowH = 272 * k, gapR = 16 * k, bh = rows.length * rowH + (rows.length - 1) * gapR, parts = []; let at = slap;
      rows.forEach((chars, r) => {
        const row = tileRow(Object.assign({}, cfg, { kind: cfg.kind3 || 'mixed' }), S, rng, chars, k, -bh / 2 + rowH / 2 + r * (rowH + gapR), at, 'r' + r + '-');
        parts.push(...row.parts); at = row.last + 1;
      });
      blocks.push({ parts, h: bh, gap: -8 * sz }); slap = at + 1;
    }
    if (call) {
      const p = plate(call.toUpperCase(), { face: 'mono', px: 46 * sz, tracking: 0.14, padx: 52 * sz, pady: 30 * sz, kind: cfg.kind2 || 'orange', key: 'call', tilt: -1.4, slap });
      const parts = [p];
      if (cfg.arrow && cfg.arrow !== 'none' && ARROW[cfg.arrow]) {    // a torn arrow that bounces towards the bio
        const [dx, dy, rot] = ARROW[cfg.arrow], aw = 80 * sz, ah = 100 * sz, vert = rot % 180 === 0;
        const spr = makeScrap({ w: aw, h: ah, kind: 'paper', seed: cfg.seed + 'arrow', S, amp: 0.45,
          corners: [[aw / 2, 0], [aw, ah * 0.46], [aw * 0.68, ah * 0.46], [aw * 0.68, ah], [aw * 0.32, ah], [aw * 0.32, ah * 0.46], [0, ah * 0.46]] });
        parts.push({ spr, x: p.w / 2 + 22 * sz + (vert ? aw : ah) / 2, y: 0, rot, slap: slap + 1, boil: 0.8, shadow: 0.5, key: 'arrow', sgn: 1, w: vert ? aw : ah, h: vert ? ah : aw, bounce: [dx, dy, 14 * sz] });
      }
      blocks.push({ parts, h: p.h, gap: 14 * sz }); slap += 2;
    }
    if (title) {
      const p = plate(title, { face: 'grotesk', px: 52 * sz, tracking: -0.02, padx: 44 * sz, pady: 28 * sz, kind: 'white', key: 'title', tilt: 1.1, slap });
      blocks.push({ parts: [p], h: p.h, gap: 0 }); slap += 2;
    }
    if (!blocks.length) { const p = plate(' ', { face: 'mono', px: 38, tracking: 0, padx: 40, pady: 24, kind: 'ink', key: 'eyebrow', tilt: 0, slap: 0 }); blocks.push({ parts: [p], h: p.h, gap: 0 }); }
    const parts = []; let top = 0;
    blocks.forEach((b) => { const yc = top + b.h / 2; b.parts.forEach(p => { p.y += yc; parts.push(p); }); top += b.h + b.gap; });
    return { parts, tear: 'v' };
  }

  const LAYOUTS = { cta: layoutCta, strip: layoutStrips, lower: layoutLower, title: layoutTitle, tiles: layoutTiles, chapter: layoutChapter };
  const DEFAULTS = {
    strip: { kind: 'ink', kind2: 'orange', pos: 'bl', size: 1 }, lower: { kind: 'paper', kind2: 'orange', pos: 'bl', size: 1 },
    title: { kind: 'paper', pos: 'c', size: 1 }, tiles: { kind: 'mixed', pos: 'c', size: 1 }, chapter: { kind: 'ink', pos: 'c', size: 1 },
    cta: { kind: 'ink', kind2: 'orange', pos: 'c', size: 1, frame: 'v', arrow: 'up', headline: 'tiles' },
  };

  // ------------------------------------------------------------------ accents: tape, little pop-out scraps, scribble underline
  function addTape(parts, group, S, cfg, rng) {
    const main = parts.find(p => p.tapeHere) || parts.filter(p => p.slap !== null && !p.sheet)[0]; if (!main) return;
    const spr = makeScrap({ w: 74, h: 30, kind: 'tape', seed: cfg.seed + 'tape', S, amp: 0.45 });
    [[-1, -rng.uni(24, 38)], [1, rng.uni(22, 34)]].forEach(([side, rot], i) => {
      parts.push({ spr, x: main.x + side * (main.w / 2 - 14), y: main.y - main.h / 2 + 6, rot, slap: main.slap + 1 + i, boil: 0.6, shadow: 0.25, key: 'tape' + i, sgn: 1, w: 74, h: 30, alpha: 0.82 });
    });
  }
  function addUnderline(parts, S, cfg, rng, group) {
    const w = group.w * 0.84, h = 44, c = mk(w * S, h * S), x = c.getContext('2d');
    const n = 7, pts = []; for (let i = 0; i < n; i++) pts.push([w * S * (0.02 + 0.96 * i / (n - 1)), h * S * (0.5 + rng.uni(-0.22, 0.22))]);
    x.strokeStyle = 'rgba(255,90,44,0.95)'; x.lineWidth = 13 * S; x.lineCap = 'round'; x.lineJoin = 'round';
    x.beginPath(); x.moveTo(pts[0][0], pts[0][1]);
    for (let i = 1; i < n; i++) x.quadraticCurveTo(pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * 0.5, pts[i - 1][1] + rng.uni(-8, 8) * S, pts[i][0], pts[i][1]);
    x.stroke();
    const cut = (g) => g;   // reveal handled at draw time
    parts.push({ spr: { cv: c, pw: c.width / 2, ph: c.height / 2, w, h }, x: group.cx, y: group.y1 + 24, rot: -0.8, slap: 3, boil: 0.8, shadow: 0, key: 'ul', sgn: 1, w, h, reveal: [3, 7] });
  }
  function popBits(cfg, group, S, rng, startStep) {
    const bits = [], N = 9;
    for (let i = 0; i < N; i++) {
      const kind = rng.pick(['paper', 'orange', 'ink', 'white', 'orange']), w = rng.uni(14, 34), h = rng.uni(10, 24);
      const top = rng.next() < 0.6, ex = rng.uni(-0.5, 0.5) * group.w;
      bits.push({ spr: makeScrap({ w, h, kind, seed: cfg.seed + 'bit' + i, S, amp: 0.8 }), x0: group.cx + ex, y0: top ? group.y0 : group.y1, vx: rng.normal() * 38 + ex / group.w * 90,
        vy: (top ? -1 : 0.4) * rng.uni(28, 72) - 18, rot0: rng.uni(0, 360), vr: rng.normal() * 40, start: startStep + (i % 3 === 0 ? 1 : 0) });
    }
    return bits;
  }

  // ------------------------------------------------------------------ clips
  function resolve(cfgIn) {
    const type = cfgIn.type && LAYOUTS[cfgIn.type] ? cfgIn.type : 'strip';
    const cfg = Object.assign({ type, text: 'WEEK 07', textColor: 'auto', tilt: null, x: null, y: null, hold: 2.5, inStyle: 'slap', outStyle: 'tear',
      boil: 1, seed: 7, tape: false, pop: false, underline: false, fps: 30, scale: 1, caps: true, frame: 'h', arrow: 'up', headline: 'tiles' }, DEFAULTS[type], cfgIn, { type });
    cfg.fw = cfg.frame === 'v' ? 1080 : 1920; cfg.fh = cfg.frame === 'v' ? 1920 : 1080;
    return cfg;
  }
  /** Safe margins: landscape uses title-safe edges. Vertical keeps clear of the top bar, the caption block and the side buttons
   *  that Shorts, Reels and TikTok draw over the picture (approximate: about 11% top, 22% bottom, 7% sides). */
  function margins(cfg) { return cfg.fw > cfg.fh ? { l: 96, r: 96, t: 90, b: 90 } : { l: 70, r: 70, t: 210, b: 430 }; }
  function anchor(cfg, gw, gh) {
    if (cfg.x != null && cfg.y != null) return [cfg.x, cfg.y];
    const m = margins(cfg), p = cfg.pos || 'c';
    const cx = { l: m.l + gw / 2, c: (m.l + cfg.fw - m.r) / 2, r: cfg.fw - m.r - gw / 2 }, cy = { t: m.t + gh / 2, c: (m.t + cfg.fh - m.b) / 2, b: cfg.fh - m.b - gh / 2 };
    const k = { bl: ['l', 'b'], bc: ['c', 'b'], br: ['r', 'b'], tl: ['l', 't'], tc: ['c', 't'], tr: ['r', 't'], c: ['c', 'c'], cl: ['l', 'c'], cr: ['r', 'c'] }[p] || ['c', 'c'];
    return [cx[k[0]], cy[k[1]]];
  }

  function buildClip(cfgIn) {
    const cfg = resolve(cfgIn), S = cfg.scale, fps = cfg.fps, FW = cfg.fw, FH = cfg.fh, rng = rngOf('layout', cfg.seed, cfg.type);
    const lay = LAYOUTS[cfg.type](cfg, S, rng), parts = lay.parts;
    // group bounds (relative to the group's own centre), then place the group
    let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
    parts.forEach(p => { if (p.sheet) return; x0 = Math.min(x0, p.x - p.w / 2); x1 = Math.max(x1, p.x + p.w / 2); y0 = Math.min(y0, p.y - p.h / 2); y1 = Math.max(y1, p.y + p.h / 2); });
    const gw = x1 - x0, gh = y1 - y0, gcx = (x0 + x1) / 2, gcy = (y0 + y1) / 2;
    if (!lay.full && !cfgIn._fitted) {                                // long text shrinks to fit the safe area
      const m = margins(cfg), limW = FW - m.l - m.r, limH = FH - m.t - m.b;
      if (gw > limW || gh > limH) return buildClip(Object.assign({}, cfgIn, { size: (cfgIn.size || 1) * Math.min(limW / gw, limH / gh) * 0.98, _fitted: true }));
    }
    parts.forEach(p => { if (!p.sheet) { p.x -= gcx; p.y -= gcy; } });
    const [ax, ay] = lay.full ? [FW / 2, FH / 2] : anchor(cfg, gw, gh);
    parts.forEach(p => { p.x += ax; p.y += ay; });
    const group = { w: gw, h: gh, cx: ax, cy: ay, x0: ax - gw / 2, x1: ax + gw / 2, y0: ay - gh / 2, y1: ay + gh / 2 };
    if (cfg.tape && !lay.full) addTape(parts, group, S, cfg, rng);
    if (cfg.underline && cfg.type !== 'tiles' && cfg.type !== 'cta') {
      const base = lay.full ? parts.filter(p => !p.sheet).slice(-1)[0] : null;
      if (lay.full && base) { group.cx = base.x; group.y1 = base.y + base.h / 2 - 20; group.w = base.w; }
      addUnderline(parts, S, cfg, rng, group);
    }
    const lastSlap = Math.max(...parts.filter(p => p.slap !== null).map(p => p.slap), 0);
    const holdSteps = Math.max(Math.round(cfg.hold * STEP_RATE), lastSlap + 3);
    const outSteps = lay.tear === 'h' ? 6 : 4;
    const total = cfg.outStyle === 'tear' ? holdSteps + outSteps + 1 : cfg.outStyle === 'cut' ? holdSteps + 1 : holdSteps + 1;
    const nFrames = Math.ceil(total / STEP_RATE * fps);
    const bits = cfg.pop && !lay.full ? popBits(cfg, group, S, rng, 0) : [];
    const tearRng = rngOf('tear', cfg.seed, cfg.type);
    let cutPath = null;
    if (cfg.outStyle === 'tear') {
      if (lay.tear === 'h') cutPath = tornPath([-MD - 40, FH / 2 + tearRng.uni(-40, 40)], [FW + MD + 40, FH / 2 + tearRng.uni(-40, 40)], tearRng, 1.2, 1);
      else { const cx = group.cx + tearRng.uni(-0.14, 0.14) * group.w, sk = tearRng.uni(-0.1, 0.1) * group.h; cutPath = tornPath([cx + sk, group.y0 - 80], [cx - sk, group.y1 + 80], tearRng, 1.2, 1); }
    }

    function poseOf(p, step) {
      if (p.slap !== null && step < p.slap) return null;
      const k = p.slap === null ? 99 : step - p.slap, kick = cfg.inStyle === 'slap' && k === 0;
      const b = boil(cfg.seed, p.key, step, p.boil * cfg.boil);
      let ox = 0, oy = 0;
      if (p.bounce) { const ph = [0, 0.55, 1, 0.55][k % 4] * p.bounce[2]; ox = p.bounce[0] * ph; oy = p.bounce[1] * ph; }   // a four-step hop towards the bio
      return { x: p.x + b.dx + ox, y: p.y + b.dy + oy, rot: p.rot + b.dr + (kick ? 2.5 * p.sgn : 0), sc: kick ? 1.13 : 1, lift: kick ? 2.2 : 1 };
    }
    function drawParts(ctx, step, withShadow, S_) {
      parts.slice().forEach(p => {
        const q = poseOf(p, step); if (!q) return;
        let spr = p.spr;
        if (p.reveal) {                                   // scribble: wipe in left to right over a few steps
          const prog = clamp((step - p.reveal[0] + 1) / (p.reveal[1] - p.reveal[0]), 0, 1); if (prog <= 0) return;
          const c = mk(spr.cv.width, spr.cv.height), cx = c.getContext('2d'); cx.drawImage(spr.cv, 0, 0, spr.cv.width * prog, spr.cv.height, 0, 0, spr.cv.width * prog, spr.cv.height);
          spr = { cv: c, pw: spr.pw, ph: spr.ph };
        }
        drawSprite(ctx, spr, S_, q.x, q.y, q.rot, q.sc, withShadow && p.shadow ? { a: p.shadow, lift: q.lift } : null, p.alpha);
      });
    }
    function drawBits(ctx, step) {
      bits.forEach(b => {
        const k = step - b.start; if (k < 0 || k > 7) return;
        const alpha = k < 5 ? 1 : 1 - (k - 4) / 3, x = b.x0 + b.vx * k, y = b.y0 + b.vy * k + 11 * k * k;
        drawSprite(ctx, b.spr, S, x, y, b.rot0 + b.vr * k, 1 - 0.06 * k, { a: 0.35, lift: 0.6 }, alpha);
      });
    }

    // the tear: render the group to a flat layer, then draw it as two torn halves
    function halves(ctx, step, oi) {
      const g = mk(FW * S, FH * S), gx = g.getContext('2d');
      drawParts(gx, step, false, S);
      const horiz = lay.tear === 'h', coreKey = cfg.kind && CORE[cfg.kind] ? cfg.kind : 'paper';
      const states = horiz
        ? [[[0, 7, 0.4], [0, -7, -0.4]], [[14, 96, 2.2], [-10, -96, -2.6]], [[46, 440, 5.5], [-36, -430, -6.5]], [[80, 1150, 9], [-70, -1150, -11]]]
        : [[[-10, -4, -0.6], [10, 4, 0.6]], [[-150, -50, -4], [150, 50, 4]], [[-620, -170, -9], [620, 180, 9]]];
      const st = states[oi - (horiz ? 2 : 1)]; if (!st) return;
      const path = cutPath, L = path.length, far = 3000;
      const p0 = path[0], p1 = path[L - 1], nrm = (() => { const dx = p1[0] - p0[0], dy = p1[1] - p0[1], l = Math.hypot(dx, dy); return [-dy / l, dx / l]; })();
      const sides = [[1, st[0]], [-1, st[1]]];
      sides.forEach(([sg, [dx, dy, rot]], idx) => {
        const poly = path.concat([[p1[0] + nrm[0] * far * sg, p1[1] + nrm[1] * far * sg], [p0[0] + nrm[0] * far * sg, p0[1] + nrm[1] * far * sg]]);
        const h = mk(FW * S, FH * S), hx = h.getContext('2d'); hx.scale(S, S);
        hx.save(); pathOf(hx, poly); hx.clip(); hx.setTransform(1, 0, 0, 1, 0, 0); hx.drawImage(g, 0, 0); hx.scale(S, S);
        const rr = rngOf('rim', cfg.seed, idx), a = jag(L, rr, [[2.8, 1]]), b = jag(L, rr, [[0.5, 1]]), off = path.map((pt, i) => {
          const w = Math.max(0.5, 2 + 3.4 * Math.abs(a[i]) + 1 * b[i]); return [pt[0] + nrm[0] * w * sg, pt[1] + nrm[1] * w * sg]; });
        hx.beginPath(); hx.moveTo(path[0][0], path[0][1]); path.forEach(pt => hx.lineTo(pt[0], pt[1])); for (let i = L - 1; i >= 0; i--) hx.lineTo(off[i][0], off[i][1]); hx.closePath();
        hx.fillStyle = CORE[coreKey]; hx.fill(); hx.restore();
        const cxh = horiz ? FW / 2 : (sg > 0 ? (group.x0 + path[(L / 2) | 0][0]) / 2 : (group.x1 + path[(L / 2) | 0][0]) / 2), cyh = horiz ? (sg > 0 ? FH * 0.73 : FH * 0.27) : group.cy;
        ctx.save(); ctx.translate((cxh + dx) * S, (cyh + dy) * S); ctx.rotate(rot * Math.PI / 180); ctx.translate(-cxh * S, -cyh * S);
        const lift = 1 + oi * 0.5; ctx.shadowColor = 'rgba(0,0,0,0.45)'; ctx.shadowBlur = 20 * lift * S; ctx.shadowOffsetX = 6 * lift * S; ctx.shadowOffsetY = 11 * lift * S;
        ctx.drawImage(h, 0, 0); ctx.restore();
      });
    }
    function crack(ctx, frac) {
      const n = Math.max(2, Math.floor(cutPath.length * frac));
      ctx.save(); ctx.scale(S, S); ctx.lineJoin = 'round'; ctx.lineCap = 'round';
      ctx.shadowColor = 'rgba(0,0,0,0.6)'; ctx.shadowBlur = 3 * S; ctx.shadowOffsetY = 1.5 * S;
      ctx.strokeStyle = CORE[cfg.kind && CORE[cfg.kind] ? cfg.kind : 'paper']; ctx.lineWidth = 2.4;
      ctx.beginPath(); ctx.moveTo(cutPath[0][0], cutPath[0][1]); for (let i = 1; i < n; i++) ctx.lineTo(cutPath[i][0], cutPath[i][1]); ctx.stroke(); ctx.restore();
    }

    function draw(ctx, i, dx, dy) {
      ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, FW * S, FH * S); ctx.translate((dx || 0) * S, (dy || 0) * S);
      const step = Math.floor(i / fps * STEP_RATE + 1e-6);
      if (cfg.outStyle === 'tear' && step >= holdSteps) {
        const oi = step - holdSteps, horiz = lay.tear === 'h';
        if (horiz) {
          if (oi <= 1) { drawParts(ctx, holdSteps - 1, true, S); crack(ctx, oi === 0 ? 0.45 : 1); }
          else if (oi === 2) { halves(ctx, holdSteps - 1, 2); }
          else if (oi <= 5) halves(ctx, holdSteps - 1, oi);
        } else {
          if (oi === 0) { drawParts(ctx, holdSteps - 1, true, S); crack(ctx, 0.55); }
          else if (oi <= 3) halves(ctx, holdSteps - 1, oi);
        }
        return;
      }
      if (cfg.outStyle === 'cut' && step >= holdSteps) return;
      drawParts(ctx, Math.min(step, holdSteps - 1), true, S);
      if (bits.length) drawBits(ctx, step);
    }
    function still(ctx, dx, dy) { ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, FW * S, FH * S); ctx.translate((dx || 0) * S, (dy || 0) * S); drawParts(ctx, lastSlap + 3, true, S); }
    return { cfg, nFrames, fps, S, W: FW * S, H: FH * S, FW, FH, draw, still, group, steps: total, holdSteps, movable: !lay.full };
  }

  root.PaperText = { buildClip, resolve, KINDS, DEFAULTS, W0, H0, fontsReady: () => Promise.all([
    document.fonts.load('700 40px "Space Grotesk"'), document.fonts.load('700 40px "Space Mono"')]) };
})(typeof window !== 'undefined' ? window : globalThis);
