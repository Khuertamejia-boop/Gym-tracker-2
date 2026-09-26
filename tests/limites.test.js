// Prueba de navegador (Playwright). Se ejecuta con tests/run.sh.
// Peso y repeticiones: sin ceros delante (025 → 25), mayores que 0 y con máximo por ejercicio.
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
  await p.evaluate(() => { [...document.querySelectorAll('[data-action="plan-day"]')].find(x => x.textContent.includes('Torso A')).click(); });
  await p.waitForTimeout(200);
  await click('.cta-bar [data-action="start"]'); await p.waitForTimeout(1000);
  const stored = (f) => p.evaluate((f) => { const d = JSON.parse(localStorage.getItem('gymtrack.v1')).draft; return d.exercises[d.current || 0].sets[0][f]; }, f);
  const type = async (sel, v) => { await p.fill(sel, ''); await p.type(sel, v); await p.locator(sel).blur(); await p.waitForTimeout(200); };
  const kg = '[data-set="kg"][data-j="0"]', reps = '[data-set="reps"][data-j="0"]';
  const exId = await p.evaluate(() => { const d = JSON.parse(localStorage.getItem('gymtrack.v1')).draft; return d.exercises[d.current || 0].exId; });
  const max = await p.evaluate(async (id) => (await import('/js/store.js')).maxKg(id), exId);
  await type(kg, '025'); console.log(exId, '| 025 →', await p.inputValue(kg), '| guardado', await stored('kg'));
  await type(kg, '9999'); console.log('9999 →', await p.inputValue(kg), '(máx', max + ') | aviso:', await p.textContent('#toast'));
  await p.screenshot({ path: OUT + '/limites-max.png' });
  await type(kg, '0'); console.log('0 kg →', JSON.stringify(await p.inputValue(kg)), '| aviso:', await p.textContent('#toast'));
  await type(reps, '0'); console.log('0 reps →', JSON.stringify(await p.inputValue(reps)));
  await type(reps, '08'); console.log('08 reps →', await p.inputValue(reps));
  await type(reps, '500'); console.log('500 reps →', await p.inputValue(reps));
  const t = await p.evaluate(async () => { const S = await import('/js/store.js');
    return ['peso-muerto', 'press-banca', 'curl-mancuernas', 'prensa', 'dominadas'].map(id => `${id}:${S.maxKg(id)}`).join(' '); });
  console.log('límites', t);
  console.log('errors', JSON.stringify(errs)); await b.close();
})();
