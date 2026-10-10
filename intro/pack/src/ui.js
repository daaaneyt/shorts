/* Paper text: the interface. State in, a PaperText clip out, and zip export. */
(function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const PT = window.PaperText;

  const SAMPLE = { strip: 'WEEK 07', lower: 'Adam\nTraining week 7 · The long run', title: 'The long run', tiles: '16.2 MI', chapter: 'WEEK 07\nThe long run' };
  const HELP = {
    strip: 'One line per strip. Capitalised for you.',
    lower: 'The first line is the name. Any other lines become the subtitle strip.',
    title: 'One or more lines.',
    tiles: 'One line. Letters, numbers, a colon or a dot work best.',
    chapter: 'One line per row. The first row is paper-coloured, the next orange.',
  };
  const KIND_LABEL = { paper: 'Paper', ink: 'Ink', orange: 'Orange', white: 'White', mixed: 'Mixed' };
  const KIND_SWATCH = { paper: '#F3F1EA', ink: '#141519', orange: '#FF5A2C', white: '#FBFAF6', mixed: 'linear-gradient(135deg,#F3F1EA 0 33%,#FF5A2C 33% 66%,#FBFAF6 66%)' };
  const POS = ['tl', 'tc', 'tr', 'cl', 'c', 'cr', 'bl', 'bc', 'br'];

  const state = Object.assign({
    type: 'strip', text: SAMPLE.strip, kind: 'ink', kind2: 'orange', textColor: 'auto', size: 1, tilt: 'auto', pos: 'bl', x: null, y: null,
    hold: 2.5, inStyle: 'slap', outStyle: 'tear', boil: 1, seed: 7, tape: false, pop: false, underline: false, fps: 30, scale: 1, bg: 'checker',
  }, load());

  function load() { try { return JSON.parse(localStorage.getItem('sub3piece-paper-text') || '{}'); } catch (e) { return {}; } }
  function save() { try { localStorage.setItem('sub3piece-paper-text', JSON.stringify(state)); } catch (e) { /* storage is optional */ } }

  const cfgOf = (over) => Object.assign({
    type: state.type, text: state.text, kind: state.kind, kind2: state.kind2, textColor: state.textColor, size: state.size,
    tilt: state.tilt === 'flat' ? 0 : null, pos: state.pos, x: state.x, y: state.y, hold: state.hold, inStyle: state.inStyle,
    outStyle: state.outStyle, boil: state.boil, seed: state.seed, tape: state.tape, pop: state.pop, underline: state.underline,
    fps: state.fps, scale: 1, caps: true,
  }, over || {});

  // ------------------------------------------------------------------ controls
  function pressed(group, value) { group.querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.v === value || b.dataset.type === value || b.dataset.bg === value))); }
  function chips(el, kinds, key) {
    el.innerHTML = '';
    kinds.forEach((k) => {
      const b = document.createElement('button'); b.type = 'button'; b.className = 'chip'; b.dataset.v = k; b.setAttribute('aria-pressed', String(state[key] === k));
      const sw = document.createElement('i'); sw.style.background = KIND_SWATCH[k]; b.append(sw, KIND_LABEL[k]);
      b.addEventListener('click', () => { state[key] = k; syncControls(); changed(); });
      el.append(b);
    });
  }
  function syncControls() {
    const t = state.type, tiles = t === 'tiles', chapter = t === 'chapter', two = t === 'strip' || t === 'lower';
    document.querySelectorAll('#types .type').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.type === t)));
    $('text').value = state.text; $('textHelp').textContent = HELP[t];
    chips($('kind'), tiles ? ['mixed', 'paper', 'orange', 'white', 'ink'] : ['paper', 'ink', 'orange', 'white'], 'kind');
    chips($('kind2'), ['paper', 'ink', 'orange', 'white'], 'kind2');
    $('kindLbl').textContent = t === 'lower' ? 'Name paper' : t === 'strip' ? 'First strip' : chapter ? 'Sheet' : 'Paper';
    $('kind2Lbl').textContent = t === 'lower' ? 'Subtitle paper' : 'Second strip';
    $('kind2Wrap').hidden = !two;
    pressed($('textColor'), state.textColor); pressed($('tilt'), state.tilt); pressed($('inStyle'), state.inStyle); pressed($('outStyle'), state.outStyle); pressed($('bgs'), state.bg);
    $('size').value = state.size; $('sizeO').textContent = Math.round(state.size * 100) + '%';
    $('hold').value = state.hold; $('boil').value = state.boil; $('boilO').textContent = Number(state.boil).toFixed(1);
    $('tape').checked = state.tape; $('pop').checked = state.pop; $('underline').checked = state.underline;
    $('tape').disabled = chapter; $('pop').disabled = chapter; $('underline').disabled = tiles;
    $('fps').value = String(state.fps); $('res').value = String(state.scale);
    document.querySelectorAll('#pos button').forEach((b) => { b.setAttribute('aria-pressed', String(state.x == null && b.dataset.p === state.pos)); b.disabled = chapter; });
    $('screen').dataset.bg = state.bg;
  }
  function buildPos() {
    const el = $('pos');
    POS.forEach((p) => { const b = document.createElement('button'); b.type = 'button'; b.dataset.p = p; b.setAttribute('aria-label', 'Position ' + p); b.addEventListener('click', () => { state.pos = p; state.x = state.y = null; syncControls(); changed(); }); el.append(b); });
  }
  function seg(id, key) { $(id).addEventListener('click', (e) => { const b = e.target.closest('button'); if (!b || b.disabled) return; state[key] = b.dataset.v; syncControls(); changed(); }); }

  // ------------------------------------------------------------------ preview
  const cv = $('cv'), ctx = cv.getContext('2d'), screen = $('screen');
  let clip = null, playing = !matchMedia('(prefers-reduced-motion: reduce)').matches, startT = 0, scrubFrame = 0, timer = 0, dragOff = [0, 0], gen = 0;
  const END_PAUSE = 0.6;

  function rebuild() {
    const my = ++gen; $('busy').hidden = false;
    requestAnimationFrame(() => setTimeout(() => {
      if (my !== gen) return;
      try { clip = PT.buildClip(cfgOf()); } catch (e) { console.error(e); $('busy').textContent = 'Could not build'; return; }
      $('busy').hidden = true; $('busy').textContent = 'Building';
      dragOff = [0, 0]; $('scrub').max = String(clip.nFrames - 1); startT = performance.now();
      screen.classList.toggle('movable', clip.movable); $('hint').hidden = !clip.movable;
      draw();
    }, 0));
  }
  function changed() { save(); clearTimeout(timer); timer = setTimeout(rebuild, 160); }
  function frameNow() {
    if (!playing) return scrubFrame;
    const total = clip.nFrames + Math.round(END_PAUSE * clip.fps), f = Math.floor((performance.now() - startT) / 1000 * clip.fps) % total;
    return Math.min(f, clip.nFrames - 1);
  }
  function draw() {
    if (!clip) return;
    const f = frameNow(); clip.draw(ctx, f, dragOff[0], dragOff[1]);
    $('scrub').value = String(f); $('tc').textContent = (f / clip.fps).toFixed(2) + ' / ' + (clip.nFrames / clip.fps).toFixed(2) + ' s';
  }
  (function loop() { if (playing || dragging) draw(); requestAnimationFrame(loop); })();
  $('play').addEventListener('click', () => {
    playing = !playing; if (playing) startT = performance.now() - scrubFrame / clip.fps * 1000;
    $('play').setAttribute('aria-label', playing ? 'Pause' : 'Play'); $('playIcon').setAttribute('d', playing ? 'M3 2h3v10H3zM8 2h3v10H8z' : 'M4 2l8 5-8 5z'); draw();
  });
  $('scrub').addEventListener('input', (e) => { playing = false; scrubFrame = +e.target.value; $('play').setAttribute('aria-label', 'Play'); $('playIcon').setAttribute('d', 'M4 2l8 5-8 5z'); draw(); });
  $('bgs').addEventListener('click', (e) => { const b = e.target.closest('button'); if (b) { state.bg = b.dataset.bg; syncControls(); save(); } });

  // drag to place
  let dragging = false, dragStart = null;
  function design(e) { const r = screen.getBoundingClientRect(); return [(e.clientX - r.left) / r.width * 1920, (e.clientY - r.top) / r.height * 1080]; }
  screen.addEventListener('pointerdown', (e) => { if (!clip || !clip.movable) return; dragging = true; dragStart = design(e); screen.setPointerCapture(e.pointerId); screen.classList.add('dragging'); });
  screen.addEventListener('pointermove', (e) => {
    if (!dragging) return; const p = design(e), g = clip.group;
    dragOff = [Math.max(-g.cx, Math.min(1920 - g.cx, p[0] - dragStart[0])), Math.max(-g.cy, Math.min(1080 - g.cy, p[1] - dragStart[1]))];
  });
  function endDrag() {
    if (!dragging) return; dragging = false; screen.classList.remove('dragging');
    if (Math.abs(dragOff[0]) + Math.abs(dragOff[1]) > 2) { state.x = Math.round(clip.group.cx + dragOff[0]); state.y = Math.round(clip.group.cy + dragOff[1]); syncControls(); changed(); }
  }
  screen.addEventListener('pointerup', endDrag); screen.addEventListener('pointercancel', endDrag);

  // ------------------------------------------------------------------ export
  let downloads = null, canSave = true;
  const hasHost = typeof window.claude !== 'undefined' && window.claude && typeof window.claude.use === 'function';
  if (hasHost) {
    canSave = false; setExportEnabled(false);
    window.claude.use('downloads').then((d) => { downloads = d; canSave = !!d; setExportEnabled(canSave); if (!d) setStatus('Saving files is not available in this view. Download the standalone paper-text-generator.html from the repository and open it in your browser.', 'err'); }, () => { setExportEnabled(false); });
  }
  function setExportEnabled(on) { ['exClip', 'exStill', 'exBatch'].forEach((id) => { $(id).disabled = !on; }); }
  function setStatus(msg, cls) { const s = $('status'); s.textContent = msg; s.className = 'status' + (cls ? ' ' + cls : ''); }
  async function saveFile(filename, blob) {
    if (downloads) { await downloads.save({ filename, data: blob }); return; }
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = filename; document.body.appendChild(a); a.click();
    setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 5000);
  }

  const CRC = (() => { const t = new Uint32Array(256); for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
  function crc32(u8) { let c = 0xFFFFFFFF; for (let i = 0; i < u8.length; i++) c = CRC[(c ^ u8[i]) & 255] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; }
  /** A "stored" (uncompressed) zip: PNGs are already compressed, so this is quick and opens everywhere. */
  function makeZip(files) {
    const enc = new TextEncoder(), parts = [], central = []; let offset = 0;
    const d = new Date(), dosTime = (d.getHours() << 11) | (d.getMinutes() << 5) | (d.getSeconds() >> 1), dosDate = ((d.getFullYear() - 1980) << 9) | ((d.getMonth() + 1) << 5) | d.getDate();
    files.forEach((f) => {
      const name = enc.encode(f.name), crc = crc32(f.data), sz = f.data.length, h = new DataView(new ArrayBuffer(30));
      h.setUint32(0, 0x04034b50, true); h.setUint16(4, 20, true); h.setUint16(6, 0x0800, true); h.setUint16(8, 0, true); h.setUint16(10, dosTime, true); h.setUint16(12, dosDate, true);
      h.setUint32(14, crc, true); h.setUint32(18, sz, true); h.setUint32(22, sz, true); h.setUint16(26, name.length, true); h.setUint16(28, 0, true);
      parts.push(new Uint8Array(h.buffer), name, f.data);
      const c = new DataView(new ArrayBuffer(46));
      c.setUint32(0, 0x02014b50, true); c.setUint16(4, 20, true); c.setUint16(6, 20, true); c.setUint16(8, 0x0800, true); c.setUint16(10, 0, true); c.setUint16(12, dosTime, true); c.setUint16(14, dosDate, true);
      c.setUint32(16, crc, true); c.setUint32(20, sz, true); c.setUint32(24, sz, true); c.setUint16(28, name.length, true); c.setUint32(42, offset, true);
      central.push(new Uint8Array(c.buffer), name); offset += 30 + name.length + sz;
    });
    const csize = central.reduce((a, b) => a + b.length, 0), e = new DataView(new ArrayBuffer(22));
    e.setUint32(0, 0x06054b50, true); e.setUint16(8, files.length, true); e.setUint16(10, files.length, true); e.setUint32(12, csize, true); e.setUint32(16, offset, true);
    return new Blob([...parts, ...central, new Uint8Array(e.buffer)], { type: 'application/zip' });
  }
  const slug = (s) => (s.split(/\n|\/\//)[0] || 'clip').toLowerCase().normalize('NFKD').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 40) || 'clip';
  const png = (canvas) => new Promise((res) => canvas.toBlob(res, 'image/png'));

  async function renderFrames(cfg, label, prefix, onTick) {
    const c = PT.buildClip(cfg), cvs = document.createElement('canvas'); cvs.width = c.W; cvs.height = c.H; const x = cvs.getContext('2d'), files = [];
    for (let i = 0; i < c.nFrames; i++) {
      c.draw(x, i); const blob = await png(cvs);
      files.push({ name: prefix + '_' + String(i + 1).padStart(4, '0') + '.png', data: new Uint8Array(await blob.arrayBuffer()) });
      onTick && onTick(i + 1, c.nFrames); if (i % 4 === 3) await new Promise((r) => setTimeout(r, 0));
    }
    return { files, clip: c };
  }
  const guide = (c) => 'sub3piece Paper text\n\nPNG sequence with transparency, ' + c.W + 'x' + c.H + ', ' + c.fps + ' fps.\n\nPremiere Pro: File > Import, pick the first frame, tick "Image Sequence", Import. Then right-click the clip > Modify > Interpret Footage > Assume this frame rate: ' + c.fps + '.\nDaVinci Resolve: Media page, drag the folder into the media pool. It appears as one clip. Set Clip Attributes > Frame rate to ' + c.fps + ' if it picked another.\n';

  let busy = false;
  async function guard(fn) {
    if (busy) return; busy = true; setExportEnabled(false); $('prog').hidden = false; $('prog').value = 0;
    try { await fn(); } catch (e) {
      if (e && e.code === 'declined') setStatus('Save cancelled.');
      else if (e && e.code === 'rate_limited') setStatus('Another save prompt is still open. Answer it, then try again.', 'err');
      else { console.error(e); setStatus('Export failed: ' + ((e && e.message) || 'unknown error'), 'err'); }
    } finally { busy = false; $('prog').hidden = true; setExportEnabled(canSave); }
  }
  $('exClip').addEventListener('click', () => guard(async () => {
    const cfg = cfgOf({ scale: state.scale, fps: state.fps }), name = cfg.type + '-' + slug(cfg.text);
    const { files, clip: c } = await renderFrames(cfg, name, name, (i, n) => { $('prog').value = i / n; setStatus('Rendering frame ' + i + ' of ' + n + '…'); });
    files.push({ name: 'READ-ME.txt', data: new TextEncoder().encode(guide(c)) });
    const blob = makeZip(files.map((f) => Object.assign({}, f, { name: name + '/' + f.name })));
    await saveFile(name + '.zip', blob); setStatus('Saved ' + name + '.zip: ' + c.nFrames + ' frames, ' + (blob.size / 1048576).toFixed(1) + ' MB.', 'ok');
  }));
  $('exStill').addEventListener('click', () => guard(async () => {
    const cfg = cfgOf({ scale: state.scale }), c = PT.buildClip(cfg), cvs = document.createElement('canvas'); cvs.width = c.W; cvs.height = c.H; c.still(cvs.getContext('2d'));
    const name = cfg.type + '-' + slug(cfg.text) + '.png'; await saveFile(name, await png(cvs)); setStatus('Saved ' + name + '.', 'ok');
  }));
  $('exBatch').addEventListener('click', () => guard(async () => {
    const jobs = $('batchText').value.split('\n').map((l) => l.trim()).filter(Boolean).map((l) => { const [t, h] = l.split('|'); return { text: t.split('//').map((s) => s.trim()).join('\n'), hold: h && +h > 0 ? +h : state.hold }; });
    if (!jobs.length) { setStatus('Add at least one line to the batch box first.', 'err'); return; }
    const all = []; let total = 0;
    for (let j = 0; j < jobs.length; j++) {
      const cfg = cfgOf({ text: jobs[j].text, hold: jobs[j].hold, scale: state.scale, fps: state.fps, seed: state.seed + j }), base = String(j + 1).padStart(2, '0') + '_' + slug(jobs[j].text);
      const { files, clip: c } = await renderFrames(cfg, base, base, (i, n) => { setStatus('Clip ' + (j + 1) + ' of ' + jobs.length + ': ' + jobs[j].text.split('\n')[0]); $('prog').value = (j + i / n) / jobs.length; });
      files.forEach((f) => all.push(Object.assign({}, f, { name: base + '/' + f.name }))); total += c.nFrames;
      if (j === 0) all.push({ name: 'READ-ME.txt', data: new TextEncoder().encode(guide(c)) });
    }
    const blob = makeZip(all); await saveFile('paper-text-batch.zip', blob); setStatus('Saved paper-text-batch.zip: ' + jobs.length + ' clips, ' + total + ' frames, ' + (blob.size / 1048576).toFixed(1) + ' MB.', 'ok');
  }));

  // ------------------------------------------------------------------ wiring
  $('types').addEventListener('click', (e) => {
    const b = e.target.closest('.type'); if (!b) return; const prev = state.type, next = b.dataset.type; if (prev === next) return;
    if (state.text === SAMPLE[prev]) state.text = SAMPLE[next];
    const d = PT.DEFAULTS[next]; state.kind = d.kind; state.kind2 = d.kind2 || state.kind2; state.pos = d.pos; state.x = state.y = null; state.type = next;
    syncControls(); changed();
  });
  $('text').addEventListener('input', (e) => { state.text = e.target.value; changed(); });
  seg('textColor', 'textColor'); seg('tilt', 'tilt'); seg('inStyle', 'inStyle'); seg('outStyle', 'outStyle');
  $('size').addEventListener('input', (e) => { state.size = +e.target.value; $('sizeO').textContent = Math.round(state.size * 100) + '%'; changed(); });
  $('hold').addEventListener('input', (e) => { const v = +e.target.value; if (v > 0) { state.hold = v; changed(); } });
  $('boil').addEventListener('input', (e) => { state.boil = +e.target.value; $('boilO').textContent = state.boil.toFixed(1); changed(); });
  ['tape', 'pop', 'underline'].forEach((k) => $(k).addEventListener('change', (e) => { state[k] = e.target.checked; changed(); }));
  $('reroll').addEventListener('click', () => { state.seed = Math.floor(Math.random() * 9000) + 1; changed(); });
  $('fps').addEventListener('change', (e) => { state.fps = +e.target.value; changed(); });
  $('res').addEventListener('change', (e) => { state.scale = +e.target.value; save(); });

  buildPos(); syncControls();
  PT.fontsReady().then(() => document.fonts.ready).then(rebuild);
  window.__paperTextState = state;
})();
