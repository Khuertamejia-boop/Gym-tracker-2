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
  const st = () => p.evaluate(() => JSON.parse(localStorage.getItem('gymtrack.v1')));
  await p.goto('http://localhost:8766/?importar=excel'); await p.waitForTimeout(600);
  await click('[data-action="set-gender"][data-v="male"]');
  await p.evaluate(() => { [...document.querySelectorAll('[data-action="plan-day"]')].find(x => x.textContent.includes('Pierna A')).click(); });
  await p.waitForTimeout(200);
  await click('.cta-bar [data-action="start"]'); await p.waitForTimeout(600);
  // Buscador
  await click('[data-action="session-add-ex"]');
  const box = await p.evaluate(() => document.getElementById('sheet').getBoundingClientRect().top);
  await p.fill('#pick-search', 'prensa'); await p.waitForTimeout(200);
  const items = (await p.locator('#pick-results .list-item').allTextContents()).map(t => t.replace(/\s+/g, ' ').trim());
  console.log('sheet top:', Math.round(box), '| results for prensa:', items.join(' / '));
  // simular teclado: visualViewport más pequeño no se puede; comprobamos max-height aplicado
  console.log('results maxHeight:', await p.evaluate(() => document.getElementById('pick-results').style.maxHeight));
  await p.screenshot({ path: OUT + '/v9-picker.png' });
  await click('#pick-results [data-action="pick-family"]');
  console.log('variant sheet:', await p.textContent('#sheet h2'), '|', (await p.locator('#sheet .variant').allTextContents()).map(t => t.replace(/\s+/g, ' ').trim()).join(' / '));
  await p.waitForTimeout(300);
  await p.screenshot({ path: OUT + '/v9-variant.png' });
  await click('#sheet [data-action="pick"][data-id="prensa-gluteos"]');
  console.log('added current:', await p.textContent('.stage-head h2'));
  // Búsqueda "bulgara" y "smith"
  await click('[data-action="session-add-ex"]');
  await p.fill('#pick-search', 'sentadilla'); await p.waitForTimeout(200);
  console.log('sentadilla results:', (await p.locator('#pick-results .list-item .grow > div:first-child').allTextContents()).join(' | '));
  await click('#sheet [data-action="close-sheet"]');
  // Aproximación en el primer ejercicio
  await click('[data-action="go-ex"][data-i="0"]');
  await click('[data-action="warm-toggle"]');
  const warmVals = await p.evaluate(() => [...document.querySelectorAll('[data-warm]')].map(i => i.value));
  console.log('warm rows:', await p.locator('.set-row.warm').count(), '| values:', warmVals.join(','));
  await p.screenshot({ path: OUT + '/v9-warm.png' });
  await click('[data-action="toggle-warm"][data-j="0"]');
  await click('[data-action="log-all"]');
  const d = (await st()).draft.exercises[0];
  console.log('warm done:', d.warmup.map(w => w.done).join(','), '| sub:', await p.textContent('.stage-sub'), '| cta:', await p.textContent('.session-btn'));
  await click('.session-bar [data-action="finish"]'); await p.waitForTimeout(400);
  const sess = (await st()).sessions.slice(-1)[0];
  const e0 = sess.exercises[0];
  const vol = sess.exercises.reduce((a, e) => a + e.sets.reduce((b, s) => b + s.kg * s.reps, 0), 0);
  console.log('saved warmup:', JSON.stringify(e0.warmup), '| work sets:', e0.sets.length, '| summary vol:', await p.textContent('.win-stat:nth-child(3) b'), 'calc', Math.round(vol), '| series tile:', await p.textContent('.win-stat:nth-child(2) b'));
  await click('.win-done');
  // Siguiente vez: aproximación recordada
  await p.evaluate(() => { [...document.querySelectorAll('[data-action="plan-day"]')].find(x => x.textContent.includes('Pierna A')).click(); });
  await p.waitForTimeout(200); await click('.cta-bar [data-action="start"]'); await p.waitForTimeout(400);
  console.log('remembered warm on:', await p.locator('.warm-toggle .switch.on').count(), '| rows', await p.locator('.set-row.warm').count());
  await click('[data-action="session-menu"]'); await click('#sheet [data-action="discard"]');
  // Historial muestra aproximación
  await click('.tabbar [data-tab="progress"]'); await click('[data-action="session-detail"]');
  console.log('detail shows:', (await p.locator('#sheet .muted.small', { hasText: 'Aproximación' }).first().textContent()).trim());
  console.log('errors:', JSON.stringify(errs));
  await b.close();
})();
