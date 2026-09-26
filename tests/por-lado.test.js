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
  const day = async (name) => { await p.evaluate((n) => { [...document.querySelectorAll('[data-action="plan-day"]')].find(x => x.textContent.includes(n)).click(); }, name); await p.waitForTimeout(200); };
  await p.goto('http://localhost:8766/?importar=excel'); await p.waitForTimeout(600);
  await click('[data-action="set-gender"][data-v="male"]');
  await day('Pierna B');
  console.log('plan meta búlgara:', (await p.locator('.plan-item .meta').first().textContent()).trim());
  await click('.cta-bar [data-action="start"]'); await p.waitForTimeout(500);
  console.log('búlgara rows:', await p.locator('.stage .set-row:not(.warm)').count(), '| labels:', (await p.locator('.stage .set-row:not(.warm) .set-n').allTextContents()).join(','), '| sub:', await p.textContent('.stage-sub'));
  await p.fill('[data-set="reps"][data-i="0"][data-j="0"]', '10'); await p.fill('[data-set="kg"][data-i="0"][data-j="0"]', '16');
  await click('[data-action="toggle-set"][data-i="0"][data-j="0"]');
  console.log('after L1 sub:', await p.textContent('.stage-sub'), '| R1 kg carried:', await p.inputValue('[data-set="kg"][data-i="0"][data-j="1"]'));
  await p.screenshot({ path: OUT + '/v10-bulgara.png' });
  await p.fill('[data-set="reps"][data-i="0"][data-j="1"]', '9'); await click('[data-action="toggle-set"][data-i="0"][data-j="1"]');
  await click('[data-action="add-set"]'); console.log('after add pair rows:', await p.locator('.stage .set-row:not(.warm)').count());
  await click('[data-action="remove-set"]'); console.log('after remove pair rows:', await p.locator('.stage .set-row:not(.warm)').count());
  // desactivar y volver a activar
  await click('[data-action="uni-toggle"]'); console.log('off rows:', await p.locator('.stage .set-row:not(.warm)').count(), '| first done:', await p.locator('.stage .set-row.done').count());
  await click('[data-action="uni-toggle"]'); console.log('on rows:', await p.locator('.stage .set-row:not(.warm)').count());
  // rellenar reps faltantes y marcar todo
  for (const j of [2, 3, 4, 5]) await p.fill(`[data-set="reps"][data-i="0"][data-j="${j}"]`, '10');
  await click('[data-action="log-all"]');
  console.log('done sub:', await p.textContent('.stage-sub'));
  // añadir step-up desde el buscador
  await click('[data-action="session-add-ex"]'); await p.fill('#pick-search', 'step'); await p.waitForTimeout(200);
  console.log('search step:', (await p.locator('#pick-results .list-item .grow > div:first-child').allTextContents()).join(' | '));
  await click('#pick-results [data-action="pick"]');
  console.log('step-up rows:', await p.locator('.stage .set-row:not(.warm)').count(), '| toggle on:', await p.locator('[data-action="uni-toggle"].on').count());
  await click('[data-action="ex-menu"]'); await click('#sheet [data-action="ex-remove"]');
  await click('.session-bar [data-action="finish"]'); await p.waitForTimeout(400);
  const sess = (await st()).sessions.slice(-1)[0];
  console.log('saved búlgara sets:', sess.exercises[0].sets.map(x => (x.side || '-') + x.kg + 'x' + x.reps).join(' '));
  await click('.win-done');
  // Historial
  await click('.tabbar [data-tab="progress"]'); await click('[data-action="session-detail"]');
  console.log('detail:', (await p.locator('#sheet .muted.small').nth(1).textContent()).trim());
  await click('#sheet [data-action="close-sheet"]'); await click('.tabbar [data-tab="train"]');
  // Siguiente vez búlgara: última vez con lados
  await day('Pierna B'); await click('.cta-bar [data-action="start"]'); await p.waitForTimeout(300);
  console.log('last line:', (await p.textContent('.last-line')).trim(), '| R1 placeholder reps:', await p.getAttribute('[data-set="reps"][data-i="0"][data-j="1"]', 'placeholder'));
  await click('[data-action="session-menu"]'); await click('#sheet [data-action="discard"]');
  // Jalón: activar por lado y recordar
  await day('Torso A'); await click('.cta-bar [data-action="start"]'); await p.waitForTimeout(300);
  await click('[data-action="go-ex"][data-i="1"]');
  console.log('jalón toggle present:', await p.locator('[data-action="uni-toggle"]').count(), '| on:', await p.locator('[data-action="uni-toggle"].on').count());
  await click('[data-action="uni-toggle"]');
  console.log('jalón rows now:', await p.locator('.stage .set-row:not(.warm)').count());
  await p.screenshot({ path: OUT + '/v10-jalon.png' });
  await click('[data-action="session-menu"]'); await click('#sheet [data-action="discard"]');
  await day('Torso A');
  console.log('plan meta jalón:', (await p.locator('.plan-item .meta').nth(1).textContent()).trim());
  console.log('errors:', JSON.stringify(errs));
  await b.close();
})();
