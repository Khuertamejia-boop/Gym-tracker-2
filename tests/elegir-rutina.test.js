// Prueba de navegador (Playwright). Se ejecuta con tests/run.sh.
// Elegir rutina: A (principiante, una sola rutina) y B (avanzado, lista con detalle).
const { chromium, devices } = require('playwright'); const OUT = process.env.OUT; const FIX = process.env.FIX;
(async () => { const b = await chromium.launch(); const errs = [];
  for (const scheme of ['dark', 'light']) {
    const ctx = await b.newContext({ ...devices['iPhone 13'], colorScheme: scheme });
    await ctx.route('**/chart.umd.min.js', r => r.fulfill({ path: FIX + '/chart.umd.min.js', contentType: 'application/javascript' }));
    await ctx.route('**/js/config.js', r => r.fulfill({ contentType: 'application/javascript', body: "export const SUPABASE_URL='https://x.supabase.co'; export const SUPABASE_ANON_KEY='k';" }));
    await ctx.route('**/supabase-js@*/**', r => r.fulfill({ path: FIX + '/mock-supabase.js', contentType: 'application/javascript' }));
    await ctx.route('**/__cloud_get', r => r.fulfill({ body: 'null' }));
    await ctx.route('**/__cloud_put', r => r.fulfill({ body: 'ok' }));
    const p = await ctx.newPage(); p.on('pageerror', e => errs.push(e.message)); p.on('console', m => m.type() === 'error' && errs.push(m.text()));
    const click = (sel) => p.click(sel).then(() => p.waitForTimeout(250));
    const setup = async (level, days) => {
      await p.goto('http://localhost:8766/'); await p.evaluate(() => localStorage.clear()); await p.reload(); await p.waitForTimeout(600);
      await click('[data-action="ob-go"][data-step="experience"]'); await click('[data-action="ob-gender"][data-v="male"]');
      await click(`[data-action="ob-level"][data-v="${level}"]`);
      for (const d of days) await click(`[data-action="ob-day"][data-d="${d}"]`);
      await click('[data-action="ob-go"][data-step="choose"]');
    };
    // A · principiante con 4 días
    await setup('beginner', [0, 1, 3, 4]);
    console.log(scheme, 'A title:', await p.textContent('.ob-title'), '| star:', (await p.textContent('#view')).includes('⭐'),
      '| week:', (await p.$$eval('.ob-week .on i', els => els.map(e => e.textContent))).join(','),
      '| stats:', (await p.$$eval('.ob-stats b', els => els.map(e => e.textContent))).join(','));
    await p.screenshot({ path: OUT + `/rutina-A-${scheme}.png` });
    // Ver otras opciones → lista B
    await click('[data-action="ob-show-all"]');
    console.log(scheme, 'B from beginner rows:', await p.locator('.ob-row[data-action="ob-sel"]').count());
    // B · avanzado con 5 días
    await setup('advanced', [0, 1, 2, 3, 4]);
    console.log(scheme, 'B open:', await p.textContent('.ob-item.open .ob-row-t'), '| mini:', (await p.$$eval('.ob-item.open .ob-mini b', els => els.map(e => e.textContent))).join(','));
    await p.screenshot({ path: OUT + `/rutina-B-${scheme}.png` });
    await click('[data-action="ob-sel"][data-key="full-body"]');
    console.log(scheme, 'B selected:', await p.textContent('.ob-item.open .ob-row-t'), '| continuar key:', await p.getAttribute('.ob-foot [data-action="ob-pick"]', 'data-key'));
    await p.screenshot({ path: OUT + `/rutina-B2-${scheme}.png`, fullPage: true });
    await click('.ob-foot [data-action="ob-pick"]');
    console.log(scheme, 'routine:', await p.evaluate(() => { const s = JSON.parse(localStorage.getItem('gymtrack.v1')); return s.routines.find(r => r.id === s.activeRoutineId).name; }));
    await ctx.close();
  }
  console.log('errors', JSON.stringify(errs)); await b.close(); })();
