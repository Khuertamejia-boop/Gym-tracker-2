// Prueba de navegador (Playwright). Se ejecuta con tests/run.sh.
// Recuperar contraseña: al volver del correo se abre una hoja de la app (sin ventanas del navegador).
const { chromium, devices } = require('playwright'); const OUT = process.env.OUT; const FIX = process.env.FIX;
(async () => { const b = await chromium.launch();
  const ctx = await b.newContext({ ...devices['iPhone 13'], colorScheme: 'light' });
  await ctx.route('**/chart.umd.min.js', r => r.fulfill({ path: FIX + '/chart.umd.min.js', contentType: 'application/javascript' }));
  await ctx.route('**/js/config.js', r => r.fulfill({ contentType: 'application/javascript', body: "export const SUPABASE_URL='https://x.supabase.co'; export const SUPABASE_ANON_KEY='k';" }));
  await ctx.route('**/supabase-js@*/**', r => r.fulfill({ path: FIX + '/mock-supabase.js', contentType: 'application/javascript' }));
  await ctx.route('**/__cloud_get', r => r.fulfill({ body: 'null' }));
  await ctx.route('**/__cloud_put', r => r.fulfill({ body: 'ok' }));
  const p = await ctx.newPage(); const errs = []; let dialogs = 0;
  p.on('pageerror', e => errs.push(e.message)); p.on('dialog', d => { dialogs++; d.dismiss(); });
  await p.goto('http://localhost:8766/'); await p.waitForTimeout(900);
  await p.evaluate(() => globalThis.__authEmit('PASSWORD_RECOVERY')); await p.waitForTimeout(400);
  console.log('hoja:', await p.textContent('#sheet h2'), '| campos contraseña:', await p.locator('#pw-form input[type=password]').count());
  await p.fill('[name=pw]', 'nueva123'); await p.fill('[name=pw2]', 'otra1234'); await p.click('#pw-form button'); await p.waitForTimeout(200);
  console.log('no coinciden:', await p.textContent('#pw-msg'));
  await p.screenshot({ path: OUT + '/contrasena.png' });
  await p.fill('[name=pw2]', 'nueva123'); await p.click('#pw-form button'); await p.waitForTimeout(400);
  console.log('aviso:', await p.textContent('#toast'), '| hoja abierta:', await p.evaluate(() => document.getElementById('sheet').open), '| ventanas del navegador:', dialogs);
  console.log('errors', JSON.stringify(errs)); await b.close(); })();
