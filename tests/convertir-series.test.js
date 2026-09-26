// Prueba de navegador (Playwright). Se ejecuta con tests/run.sh.
const { chromium } = require('playwright');
const OUT = process.env.OUT; const FIX = process.env.FIX;
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, colorScheme: 'light', hasTouch: true });
  await ctx.route('**/chart.umd.min.js', r => r.fulfill({ path: FIX + '/chart.umd.min.js', contentType: 'application/javascript' }));
  await ctx.route('**/js/config.js', r => r.fulfill({ contentType: 'application/javascript', body: "export const SUPABASE_URL=''; export const SUPABASE_ANON_KEY='';" }));
  const p = await ctx.newPage(); const errs = [];
  p.on('pageerror', e => errs.push(e.message)); p.on('console', m => m.type() === 'error' && errs.push(m.text()));
  p.on('dialog', d => d.accept());
  const click = (sel) => p.click(sel).then(() => p.waitForTimeout(150));
  const draft = () => p.evaluate(() => JSON.parse(localStorage.getItem('gymtrack.v1')).draft.exercises[0]);
  await p.goto('http://localhost:8766/?importar=excel'); await p.waitForTimeout(600);
  await click('[data-action="set-gender"][data-v="male"]');
  await p.evaluate(() => { [...document.querySelectorAll('[data-action="plan-day"]')].find(x => x.textContent.includes('Torso A')).click(); });
  await p.waitForTimeout(200); await click('.cta-bar [data-action="start"]'); await p.waitForTimeout(400);
  console.log('toggles visible:', (await p.locator('.toggle-chip').allTextContents()).map(t => t.trim()).join(' | '));
  await click('[data-action="set-menu"][data-kind="set"][data-j="0"]');
  console.log('menu:', (await p.locator('#sheet .menu-row').allTextContents()).map(t => t.replace(/\s+/g, ' ').trim()).join(' / '));
  await p.screenshot({ path: OUT + '/v11-setmenu.png' });
  await click('#sheet [data-action="set-to-warm"]');
  let d = await draft();
  console.log('after to-warm: sets', d.sets.length, 'warm', d.warmup.length, 'warmOn', d.warmupOn, '| warm rows UI', await p.locator('.set-row.warm').count());
  await p.screenshot({ path: OUT + '/v11-converted.png' });
  await click('[data-action="set-menu"][data-kind="warm"][data-j="0"]');
  await click('#sheet [data-action="warm-to-set"]');
  d = await draft(); console.log('after to-set: sets', d.sets.length, 'warm', (d.warmup || []).length, 'warmOn', d.warmupOn);
  await click('[data-action="set-menu"][data-kind="set"][data-j="2"]'); await click('#sheet [data-action="set-delete"]');
  d = await draft(); console.log('after delete: sets', d.sets.length);
  // buscador arriba
  await click('[data-action="session-add-ex"]');
  console.log('picker top class:', await p.evaluate(() => document.getElementById('sheet').classList.contains('sheet-top')), '| top px', await p.evaluate(() => Math.round(document.getElementById('sheet').getBoundingClientRect().top)));
  await p.fill('#pick-search', 'sentadill búl'); await p.waitForTimeout(200);
  console.log('results:', (await p.locator('#pick-results .list-item .grow > div:first-child').allTextContents()).join(' | '));
  await click('#sheet [data-action="close-sheet"]');
  // modo simple: número no es botón
  await click('[data-action="session-menu"]'); await click('#sheet [data-action="discard"]');
  await click('#profile-btn'); await click('#sheet [data-action="open-settings"]'); await click('#sheet [data-action="toggle-simple"]'); await click('#sheet [data-action="close-sheet"]');
  await click('.cta-bar [data-action="start"]'); await p.waitForTimeout(300);
  console.log('simple mode set buttons:', await p.locator('button.set-n').count(), '| toggles:', await p.locator('.toggle-chip').count());
  console.log('errors:', JSON.stringify(errs));
  await b.close();
})();
