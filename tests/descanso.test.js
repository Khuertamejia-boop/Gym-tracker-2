// Prueba de navegador (Playwright). Se ejecuta con tests/run.sh.
const { chromium } = require('playwright'); const OUT = process.env.OUT; const FIX = process.env.FIX;
(async () => { const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, colorScheme: 'dark', hasTouch: true });
  await ctx.route('**/chart.umd.min.js', r => r.fulfill({ path: FIX + '/chart.umd.min.js', contentType: 'application/javascript' }));
  await ctx.route('**/js/config.js', r => r.fulfill({ contentType: 'application/javascript', body: "export const SUPABASE_URL=''; export const SUPABASE_ANON_KEY='';" }));
  const p = await ctx.newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => m.type() === 'error' && errs.push(m.text()));
  p.on('dialog', d => d.accept());
  await p.clock.install();
  const click = (sel) => p.click(sel).then(() => p.waitForTimeout(200));
  const st = () => p.evaluate(() => JSON.parse(localStorage.getItem('gymtrack.v1')));
  await p.goto('http://localhost:8766/?importar=excel'); await p.waitForTimeout(600);
  await click('[data-action="set-gender"][data-v="male"]');
  await click('.cta-bar [data-action="start"]'); await p.waitForTimeout(300);
  const d0 = (await st()).draft;
  console.log('exercises:', d0.exercises.map(e => `${e.exId}${e.upFrom ? '↑' + e.upFrom : ''}`).join(', '));
  // ejercicio 1 (no por lado)
  const idx = d0.exercises.findIndex(e => !e.sets[0].side);
  await click(`[data-action="go-ex"][data-i="${idx}"]`);
  await click('[data-action="go-ex"][data-i="2"]'); console.log('up-line:', await p.locator('.up-line').count() ? (await p.textContent('.up-line')).replace(/\s+/g,' ').trim() : 'none');
  await p.screenshot({ path: OUT + '/v18-up.png' });
  await click(`[data-action="go-ex"][data-i="${idx}"]`);
  await click('[data-action="toggle-set"][data-j="0"]');
  console.log('rest bar:', await p.locator('#rest-bar').count(), '| left:', await p.textContent('#rest-left'), '| target', d0.exercises[idx].target);
  await p.screenshot({ path: OUT + '/v18-rest.png' });
  await click('[data-action="rest-adj"][data-s="15"]'); console.log('after +15:', await p.textContent('#rest-left'), '| saved', JSON.stringify((await st()).settings.rest));
  await p.clock.fastForward(30000); await p.waitForTimeout(300); console.log('after 30s:', await p.textContent('#rest-left'));
  await p.clock.runFor(110000); await p.waitForTimeout(400);
  console.log('ended bar:', await p.locator('#rest-bar').count(), '| toast:', await p.textContent('#toast'));
  await click('[data-action="toggle-set"][data-j="1"]'); console.log('2nd rest:', await p.textContent('#rest-left'));
  await click('[data-action="rest-skip"]'); console.log('skipped bar:', await p.locator('#rest-bar').count());
  // por lado: L no arranca, R sí
  const si = d0.exercises.findIndex(e => e.sets[0].side);
  if (si >= 0) { await click(`[data-action="go-ex"][data-i="${si}"]`);
    await click('[data-action="toggle-set"][data-j="0"]'); console.log('after L:', await p.locator('#rest-bar').count());
    await click('[data-action="toggle-set"][data-j="1"]'); console.log('after R:', await p.locator('#rest-bar').count()); }
  // ajuste off
  await click('[data-action="session-menu"]').catch(()=>{}); await p.evaluate(() => document.getElementById('sheet').open && document.getElementById('sheet').close());
  // terminar: rest no se guarda en sesión
  await click('.session-bar [data-action="finish"]'); await p.waitForTimeout(600);
  const last = (await st()).sessions.slice(-1)[0];
  console.log('session has rest:', 'rest' in last, '| upFrom leak:', last.exercises.some(e => 'upFrom' in e));
  await click('.win-done');
  await click('#profile-btn'); await click('#sheet [data-action="open-settings"]');
  await click('#sheet [data-action="toggle-rest"]'); console.log('rest setting:', (await st()).settings.restTimer);
  console.log('errors', JSON.stringify(errs)); await b.close(); })();
