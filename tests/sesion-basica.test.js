// Prueba de navegador (Playwright). Se ejecuta con tests/run.sh.
const { chromium } = require('playwright');
const OUT = process.env.OUT; const FIX = process.env.FIX;
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, colorScheme: 'dark', hasTouch: true });
  await ctx.route('**/chart.umd.min.js', r => r.fulfill({ path: FIX + '/chart.umd.min.js', contentType: 'application/javascript' }));
  await ctx.route('**/js/config.js', r => r.fulfill({ contentType: 'application/javascript', body: "export const SUPABASE_URL=''; export const SUPABASE_ANON_KEY='';" }));
  const p = await ctx.newPage(); const errs = [];
  p.on('pageerror', e => errs.push(e.message)); p.on('console', m => m.type() === 'error' && errs.push(m.text()));
  p.on('dialog', d => d.accept());
  const click = (sel) => p.click(sel).then(() => p.waitForTimeout(150));
  const cur = () => p.evaluate(() => JSON.parse(localStorage.getItem('gymtrack.v1')).draft?.current);
  await p.goto('http://localhost:8766/?importar=excel'); await p.waitForTimeout(600);
  await click('[data-action="set-gender"][data-v="male"]');
  await p.evaluate(() => { [...document.querySelectorAll('[data-action="plan-day"]')].find(x => x.textContent.includes('Torso A')).click(); });
  await p.waitForTimeout(200);
  await click('.cta-bar [data-action="start"]');
  await p.waitForTimeout(1200);
  console.log('focus mode: tabbar hidden', await p.evaluate(() => getComputedStyle(document.querySelector('.tabbar')).display === 'none'), '| rail items', await p.locator('.rail-item').count(), '| timer', await p.textContent('#elapsed'));
  console.log('title:', await p.textContent('.stage-head h2'), '| sub:', await p.textContent('.stage-sub'), '| cta:', await p.textContent('.session-btn'));
  await p.screenshot({ path: OUT + '/v8-start.png' });
  // Marcar la primera serie con el ✓
  await click('[data-action="toggle-set"][data-i="0"][data-j="0"]');
  console.log('after 1 set sub:', await p.textContent('.stage-sub'), '| cta:', await p.textContent('.session-btn'));
  await p.screenshot({ path: OUT + '/v8-one-set.png' });
  await click('[data-action="log-all"]'); await p.waitForTimeout(200);
  console.log('after log-all sub:', await p.textContent('.stage-sub'), '| cta:', await p.textContent('.session-btn'), '| rail done:', await p.locator('.rail-item.done').count());
  await p.screenshot({ path: OUT + '/v8-ex-done.png' });
  await click('.session-btn[data-action="go-ex"]');
  console.log('now current:', await cur(), '| title:', await p.textContent('.stage-head h2'));
  // Deslizar a la izquierda (siguiente) y a la derecha (anterior)
  const swipe = async (dx) => p.evaluate((dx) => {
    const el = document.getElementById('stage');
    const t = (x) => new Touch({ identifier: 1, target: el, clientX: x, clientY: 300 });
    el.dispatchEvent(new TouchEvent('touchstart', { touches: [t(200)], changedTouches: [t(200)], bubbles: true }));
    el.dispatchEvent(new TouchEvent('touchend', { touches: [], changedTouches: [t(200 + dx)], bubbles: true }));
  }, dx);
  await swipe(-120); await p.waitForTimeout(200); console.log('after swipe left:', await cur());
  await swipe(120); await p.waitForTimeout(200); console.log('after swipe right:', await cur());
  // lb en el ejercicio actual
  const exId = await p.evaluate(() => JSON.parse(localStorage.getItem('gymtrack.v1')).draft.exercises[1].exId);
  await click(`.stage [data-action="ex-unit"][data-u="lb"]`);
  console.log('unit label now lb:', await p.locator('.stage .unit-switch button.active').textContent());
  await click(`.stage [data-action="ex-unit"][data-u="kg"]`);
  // menú del ejercicio: mover después
  await click('[data-action="ex-menu"]');
  await p.screenshot({ path: OUT + '/v8-ex-menu.png' });
  await click('#sheet [data-action="ex-move"][data-dir="1"]');
  console.log('moved, current:', await cur(), '| rail order ok:', await p.evaluate((id) => JSON.parse(localStorage.getItem('gymtrack.v1')).draft.exercises[2].exId === id, exId));
  // Terminar todos con log-all + siguiente
  for (let k = 0; k < 12; k++) {
    const btn = p.locator('.session-btn');
    const action = await btn.getAttribute('data-action');
    if (action === 'finish') break;
    if (action === 'log-all') {
      // si falta reps sin sugerencia, rellenar
      await btn.click(); await p.waitForTimeout(150);
      const empties = await p.locator('.stage .set-row:not(.done) [data-set="reps"]').count();
      if (empties) { for (let q = 0; q < empties; q++) { await p.locator('.stage .set-row:not(.done) [data-set="reps"]').nth(0).fill('10'); await p.locator('.stage .set-row:not(.done) [data-set="kg"]').nth(0).fill('20'); await p.locator('.stage .set-row:not(.done) .set-check').nth(0).click(); await p.waitForTimeout(100); } }
    } else await btn.click();
    await p.waitForTimeout(150);
  }
  console.log('final cta:', await p.textContent('.session-btn'), '| all done:', await p.locator('.rail-item.done').count(), '/', await p.locator('.rail-item:not(.rail-add)').count());
  await p.screenshot({ path: OUT + '/v8-final.png' });
  await click('.session-btn'); await p.waitForTimeout(500);
  console.log('summary:', await p.locator('.celebrate').count(), '| tabbar back after close:');
  await click('.win-done');
  console.log('tabbar visible:', await p.evaluate(() => getComputedStyle(document.querySelector('.tabbar')).display !== 'none'));
  // Light mode screenshot of a session
  await p.emulateMedia({ colorScheme: 'light' });
  await p.evaluate(() => { [...document.querySelectorAll('[data-action="plan-day"]')].find(x => x.textContent.includes('Pierna A')).click(); });
  await p.waitForTimeout(200); await click('.cta-bar [data-action="start"]'); await p.waitForTimeout(800);
  await p.screenshot({ path: OUT + '/v8-light.png' });
  console.log('errors:', JSON.stringify(errs));
  await b.close();
})();
