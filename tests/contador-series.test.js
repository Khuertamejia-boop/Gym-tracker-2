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
  const click = (sel) => p.click(sel).then(() => p.waitForTimeout(150));
  await p.goto('http://localhost:8766/?importar=excel'); await p.waitForTimeout(600);
  await click('[data-action="set-gender"][data-v="male"]');
  await p.evaluate(() => { [...document.querySelectorAll('[data-action="plan-day"]')].find(x => x.textContent.includes('Pierna B')).click(); });
  await p.waitForTimeout(200); await click('.cta-bar [data-action="start"]'); await p.waitForTimeout(400);
  await click('[data-action="go-ex"][data-i="1"]');
  const count = () => p.textContent('.step-count');
  console.log('count', await count(), 'rows', await p.locator('.stage .set-row').count());
  await click('.step-btn[data-action="add-set"]'); console.log('after +', await count(), await p.locator('.stage .set-row').count());
  await click('.step-btn[data-action="remove-set"]'); await click('.step-btn[data-action="remove-set"]'); await click('.step-btn[data-action="remove-set"]');
  console.log('after 3x −', await count(), '| minus disabled', await p.locator('.step-btn[data-action="remove-set"]').isDisabled());
  await click('.step-btn[data-action="add-set"]'); await click('.step-btn[data-action="add-set"]');
  await click('.note-btn'); console.log('note open', await p.locator('textarea.note').count());
  await click('.note-btn'); console.log('note closed (empty)', await p.locator('textarea.note').count());
  await p.screenshot({ path: OUT + '/v15-stepper.png' });
  // búlgara por lado: pares
  await click('[data-action="go-ex"][data-i="0"]');
  console.log('bulgara count', await count(), 'rows', await p.locator('.stage .set-row').count());
  await click('.step-btn[data-action="add-set"]'); console.log('bulgara after +', await count(), await p.locator('.stage .set-row').count());
  console.log('errors:', JSON.stringify(errs));
  await b.close();
})();
