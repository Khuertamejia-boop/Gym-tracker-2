// Prueba de navegador (Playwright). Se ejecuta con tests/run.sh.
const { chromium } = require('playwright'); const OUT = process.env.OUT; const FIX = process.env.FIX;
(async () => { const b = await chromium.launch();
for (const scheme of ['dark', 'light']) {
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, colorScheme: scheme });
  await ctx.route('**/chart.umd.min.js', r => r.fulfill({ path: FIX + '/chart.umd.min.js', contentType: 'application/javascript' }));
  await ctx.route('**/js/config.js', r => r.fulfill({ contentType: 'application/javascript', body: "export const SUPABASE_URL=''; export const SUPABASE_ANON_KEY='';" }));
  const p = await ctx.newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => m.type() === 'error' && errs.push(m.text()));
  const click = (sel) => p.click(sel).then(() => p.waitForTimeout(300));
  // Historial sintético de 5 meses
  await p.goto('http://localhost:8766/?importar=excel'); await p.waitForTimeout(500);
  await p.evaluate(() => {
    const st = JSON.parse(localStorage.getItem('gymtrack.v1'));
    st.profile.gender = 'male';
    const r = st.routines[0]; const now = Date.now();
    for (let w = 22; w >= 1; w--) r.days.forEach((d, k) => {
      const t = now - (w * 7 - k * 2) * 86400000; const date = new Date(t).toISOString().slice(0, 10);
      st.sessions.push({ id: 'x' + w + k, date, startedAt: t, finishedAt: t + (50 + k * 5) * 60000, dayName: d.name,
        exercises: d.exercises.map((e, j) => ({ exId: e.exId, sets: Array.from({ length: Number(e.sets) }, () => ({ kg: 20 + j * 10 + (22 - w) * 1.5 + (w % 3), reps: 10, done: true })) })) });
    });
    st.sessions.sort((a, b) => a.date < b.date ? -1 : 1);
    localStorage.setItem('gymtrack.v1', JSON.stringify(st));
  });
  await p.reload(); await p.waitForTimeout(600);
  await click('.tabbar [data-tab="progress"]'); await p.waitForTimeout(600);
  console.log(scheme, 'tiles:', (await p.locator('.an-tile').allTextContents()).map(t => t.replace(/\s+/g, ' ').trim()).join(' | '));
  console.log('bars:', (await p.locator('.mb-row').allTextContents()).map(t => t.replace(/\s+/g, ' ').trim()).join(' | '), '| sparks', await p.locator('.ex-spark canvas').count());
  await p.screenshot({ path: `${OUT}/an-${scheme}-1.png` });
  await p.evaluate(() => window.scrollTo(0, document.querySelector('.an-section:nth-of-type(2)') ? 560 : 560)); await p.waitForTimeout(300);
  await p.screenshot({ path: `${OUT}/an-${scheme}-2.png` });
  if (scheme === 'dark') {
    await click('[data-action="ex-metric-p"][data-m="vol"]'); await p.waitForTimeout(400);
    console.log('vol head:', (await p.locator('.ex-spark-head').first().textContent()).replace(/\s+/g, ' ').trim());
    await click('[data-action="range"][data-r="1m"]'); console.log('1m tiles:', (await p.locator('.an-tile').allTextContents()).map(t => t.replace(/\s+/g, ' ').trim()).join(' | '));
    await click('[data-action="range"][data-r="all"]'); await click('[data-action="muscle-info"]'); console.log('info:', await p.textContent('#sheet h2'));
    await p.evaluate(() => document.getElementById('sheet').close());
    await click('[data-action="ex-metric-p"][data-m="max"]');
  }
  console.log('errors', JSON.stringify(errs)); await ctx.close(); }
await b.close(); })();
