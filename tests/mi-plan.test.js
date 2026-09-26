// Prueba de navegador (Playwright). Se ejecuta con tests/run.sh.
const { chromium, devices } = require('playwright'); const OUT = process.env.OUT; const FIX = process.env.FIX;
(async () => { const b = await chromium.launch();
for (const scheme of ['light', 'dark']) {
  const ctx = await b.newContext({ ...devices['iPhone 13'], colorScheme: scheme });
  await ctx.route('**/chart.umd.min.js', r => r.fulfill({ path: FIX + '/chart.umd.min.js', contentType: 'application/javascript' }));
  await ctx.route('**/js/config.js', r => r.fulfill({ contentType: 'application/javascript', body: "export const SUPABASE_URL=''; export const SUPABASE_ANON_KEY='';" }));
  const p = await ctx.newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => m.type() === 'error' && errs.push(m.text()));
  const click = (sel) => p.click(sel).then(() => p.waitForTimeout(250));
  await p.goto('http://localhost:8766/?importar=excel'); await p.waitForTimeout(600);
  await p.evaluate(() => { const st = JSON.parse(localStorage.getItem('gymtrack.v1')); st.profile.gender = 'male';
    try { localStorage.setItem('gymtrack.installDismissed', '1'); } catch {}
    // un entreno hecho ayer
    const d = new Date(Date.now() - 86400000); const iso = d.toISOString().slice(0, 10);
    const r = st.routines[0]; st.sessions.push({ id: 'y1', date: iso, startedAt: d.getTime(), finishedAt: d.getTime() + 3e6, dayName: r.days[0].name, exercises: r.days[0].exercises.map(e => ({ exId: e.exId, sets: [{ kg: 40, reps: 10, done: true }, { kg: 40, reps: 10, done: true }] })) });
    localStorage.setItem('gymtrack.v1', JSON.stringify(st)); });
  await p.reload(); await p.waitForTimeout(600);
  await click('.tabbar [data-tab="plan"]');
  console.log(scheme, 'ring:', (await p.textContent('.ring')).replace(/\s+/g, ' ').trim(), '| strip btns:', await p.locator('button.wk').count(), '| tiles:', await p.locator('.pt').count(), '| next:', (await p.textContent('.next-card')).replace(/\s+/g, ' ').trim());
  await p.screenshot({ path: `${OUT}/v21-plan-${scheme}.png` });
  if (scheme === 'light') {
    await click('.vol-acc summary'); console.log('vol open rows:', await p.locator('.vol-row').count());
    await p.screenshot({ path: `${OUT}/v21-plan-vol.png`, fullPage: true });
    await click('button.wk'); console.log('sheet:', await p.textContent('#sheet h2')); await click('#sheet [data-action="plan-set"]');
    console.log('next now:', (await p.textContent('.next-card')).replace(/\s+/g, ' ').trim(), '| moved tag:', await p.locator('.pt em').count());
    await p.screenshot({ path: `${OUT}/v21-plan-moved.png` });
    await click('.next-card'); console.log('went to:', await p.textContent('#view-title'), '| selected chip:', await p.textContent('.plan-chips .chip.active'));
    await p.screenshot({ path: `${OUT}/v21-train.png` });
    await click('.tabbar [data-tab="progress"]'); await p.screenshot({ path: `${OUT}/v21-progress.png` });
  }
  console.log('errors', JSON.stringify(errs)); await ctx.close(); }
await b.close(); })();
