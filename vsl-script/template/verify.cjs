// Browser QA for the built deck. Usage: npm install, then node verify.cjs
// Walks every slide in 3 viewports and 2 modes, tests every control, then captures one slide per visual.
// Set CHROME_PATH if Chrome is not found.
const fs = require('fs'), path = require('path'), { pathToFileURL } = require('url'), { execSync } = require('child_process');
const puppeteer = require('puppeteer-core');
const dist = path.join(__dirname, 'dist'), out = path.join(dist, 'verification');
const deck = JSON.parse(fs.readFileSync(path.join(dist, 'deck.json'), 'utf8'));
const url = pathToFileURL(path.join(dist, deck.id + '.html')).href;
const sleep = ms => new Promise(r => setTimeout(r, ms));
function chrome() {
  if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
  const mac = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  if (fs.existsSync(mac)) return mac;
  for (const bin of ['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser']) {
    try { return execSync(`command -v ${bin}`, { encoding: 'utf8' }).trim(); } catch (e) {}
  }
  throw new Error('Chrome not found. Set CHROME_PATH.');
}
(async () => {
  const browser = await puppeteer.launch({ executablePath: chrome(), headless: true, args: ['--allow-file-access-from-files'].concat(process.env.CI ? ['--no-sandbox'] : []) });
  const page = await browser.newPage(), errors = [], issues = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });

  // Every slide, every viewport, both modes: nothing may overflow, clip or mismatch the script.
  for (const vp of [{ width: 1440, height: 900 }, { width: 1280, height: 720 }, { width: 390, height: 844 }]) {
    await page.setViewport(vp);
    await page.goto(url, { waitUntil: 'load' });
    await page.evaluate(() => document.fonts.ready);
    for (const mode of ['reading', 'screen']) {
      if (mode === 'screen') await page.evaluate(() => document.getElementById('mode').click());
      const scan = await page.evaluate(() => {
        const fails = [], norm = s => s.replace(/\s+/g, ' ').trim();
        for (let n = 0; n < deckData.slides.length; n++) {
          goSlide(n);
          const st = document.querySelector('#stage'), sl = document.querySelector('#slide');
          const r = st.getBoundingClientRect(), c = sl.getBoundingClientRect();
          const over = st.scrollHeight > st.clientHeight + 1;
          const out = document.documentElement.scrollWidth > innerWidth;
          let svgOut = false; const svg = sl.querySelector('.visual svg');
          if (svg) {
            const vb = svg.viewBox.baseVal;
            svg.querySelectorAll('text').forEach(t => { const b = t.getBBox(); if (b.x < -1 || b.y < -1 || b.x + b.width > vb.width + 1 || b.y + b.height > vb.height + 3) svgOut = t.textContent; });
            svg.querySelectorAll('g').forEach(g => {
              const ring = g.querySelector(':scope > circle'), big = g.querySelector(':scope > text.big');
              if (ring && big && big.getBBox().width > 2 * ring.r.baseVal.value - 2) svgOut = big.textContent;
              const box = g.querySelector(':scope > rect.nd'); if (!box) return;
              const R = box.getBBox();
              g.querySelectorAll(':scope > text').forEach(t => { const b = t.getBBox(); if (b.x < R.x - 1 || b.x + b.width > R.x + R.width + 1) svgOut = t.textContent; });
            });
          }
          if (over || out || c.left < r.left - 2 || c.right > r.right + 2 || svgOut) fails.push({ n: n + 1, over, out, svgOut, sh: st.scrollHeight, ch: st.clientHeight });
          if (deckData.slides[n].v && !(sl.querySelector('.visual svg') && sl.querySelector('.visual svg').childElementCount)) fails.push({ n: n + 1, emptyVisual: deckData.slides[n].v.type });
          if ([...sl.querySelectorAll('.w')].some(w => /^[,.:;?!»]/.test(w.textContent))) fails.push({ n: n + 1, orphanPunctuation: true });
          if (norm(sl.querySelector('.spoken').textContent) !== norm(deckData.slides[n].plain)) fails.push({ n: n + 1, scriptMismatch: true });
          if (/TODO|TBD|lorem|__[A-Z_]+__/i.test(sl.innerText)) fails.push({ n: n + 1, internalText: true });
        }
        return fails;
      });
      if (scan.length) issues.push({ viewport: vp, mode, count: scan.length, scan: scan.slice(0, 40) });
    }
    console.log('checked', vp.width, vp.height);
  }

  // Controls: keyboard, part menu, modes, notes, idle toolbar, synced presenter window.
  await page.setViewport({ width: 1440, height: 900 });
  await page.goto(url, { waitUntil: 'load' });
  await page.evaluate(() => goSlide(0));
  await page.keyboard.press('ArrowRight');
  if (await page.evaluate(() => __deckState.index) !== 1) issues.push('keyboard');
  await page.select('#jump', deck.parts[2]);
  if (await page.evaluate(() => deckData.slides[__deckState.index].section) !== deck.parts[2]) issues.push('part menu');
  await page.keyboard.press('l');
  if (!(await page.evaluate(() => __deckState.screen))) issues.push('mode key L');
  await page.keyboard.press('l');
  await page.keyboard.press('n');
  if (!(await page.evaluate(() => __deckState.notes))) issues.push('notes key N');
  if (!(await page.evaluate(() => document.getElementById('noteText').textContent.includes(deckData.ui.frameTag)))) issues.push('framework marker missing from notes');
  await page.keyboard.press('n');
  await page.keyboard.press('a');
  if (await page.evaluate(() => __deckState.motion)) issues.push('animation key A');
  await page.keyboard.press('a');
  await page.mouse.move(300, 300);
  await sleep(2900);
  if (!(await page.evaluate(() => document.body.classList.contains('idle')))) issues.push('toolbar did not hide');
  await page.mouse.move(320, 320);
  if (await page.evaluate(() => document.body.classList.contains('idle'))) issues.push('toolbar did not wake');
  const popup = new Promise(r => page.once('popup', r));
  await page.click('#presenter');
  const pop = await popup;
  await pop.waitForFunction(() => window.__deckState);
  await page.evaluate(() => goSlide(4));
  await pop.waitForFunction(() => __deckState.index === 4, { timeout: 3000 });
  await pop.evaluate(() => goSlide(7));
  await page.waitForFunction(() => __deckState.index === 7, { timeout: 3000 });
  await sleep(800);
  await pop.screenshot({ path: path.join(out, 'presenter.png') });
  await pop.close();

  // One capture per visual type, in both modes. Look at them before delivering.
  const data = await page.evaluate(() => deckData.slides.map((s, n) => ({ n, v: s.v && s.v.type, st: s.stats.length, who: s.who, sec: s.section })));
  const seen = new Set(), picks = [];
  for (const d of data) if (d.v && !seen.has(d.v)) { seen.add(d.v); picks.push(d.n); }
  for (const n of [0, 1, data.findIndex(d => d.st), data.findIndex(d => d.who), data.length - 1]) if (n >= 0 && !picks.includes(n)) picks.push(n);
  picks.sort((a, b) => a - b);
  const caps = path.join(out, 'captures');
  fs.mkdirSync(caps, { recursive: true });
  for (const f of fs.readdirSync(caps)) fs.unlinkSync(path.join(caps, f));
  for (const mode of ['reading', 'screen']) {
    if (mode === 'screen') await page.evaluate(() => document.getElementById('mode').click());
    for (const n of picks) {
      await page.evaluate(k => goSlide(k), n);
      await sleep(1450);
      await page.screenshot({ path: path.join(caps, `${mode}-${String(n + 1).padStart(3, '0')}.png`) });
    }
  }
  await page.setViewport({ width: 390, height: 844 });
  await page.evaluate(k => goSlide(k), picks[Math.min(3, picks.length - 1)]);
  await sleep(1500);
  await page.screenshot({ path: path.join(caps, 'mobile.png') });
  await browser.close();

  const result = { errors, issues, captures: picks.length };
  fs.writeFileSync(path.join(out, 'browser-report.json'), JSON.stringify(result, null, 1));
  console.log(JSON.stringify(result, null, 1).slice(0, 3500));
  process.exit(errors.length || issues.length ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
