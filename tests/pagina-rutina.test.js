// Prueba de navegador (Playwright). Se ejecuta con tests/run.sh.
// Página del enlace de rutina (r/): vista previa, copiar código, enlace inválido y sin código.
const { chromium, devices } = require('playwright');
const fs = require('fs'); const path = require('path');
const OUT = process.env.OUT;
(async () => {
  const code = fs.readFileSync(path.resolve(__dirname, '../docs/app-ios/datos/codigo-rutina/ejemplo.codigo.txt'), 'utf8').trim();
  const b = await chromium.launch(); const errs = [];
  for (const scheme of ['light', 'dark']) {
    const ctx = await b.newContext({ ...devices['iPhone 13'], colorScheme: scheme });
    await ctx.grantPermissions(['clipboard-read', 'clipboard-write']).catch(() => {});
    const p = await ctx.newPage();
    p.on('pageerror', (e) => errs.push(e.message)); p.on('console', (m) => m.type() === 'error' && errs.push(m.text()));
    await p.goto('http://localhost:8766/r/#' + code); await p.waitForTimeout(700);
    const title = await p.textContent('.hero h1');
    console.log(scheme, 'título:', title, '| stats:', (await p.textContent('.stats')).replace(/\s+/g, ' '));
    if (!title.includes('Hipertrofia')) errs.push('no muestra la rutina');
    if ((await p.locator('details').count()) !== 4) errs.push('no hay 4 días');
    if (!(await p.textContent('.days')).includes('Hip thrust con banda')) errs.push('falta el ejercicio propio');
    const open = await p.getAttribute('#open', 'href');
    if (!open.startsWith('gymtracker://rutina?c=GT1-')) errs.push('enlace a la app mal: ' + open);
    await p.screenshot({ path: `${OUT}/rutina-${scheme}-1.png`, fullPage: true });
    await p.click('#copy'); await p.waitForTimeout(300);
    const clip = await p.evaluate(() => navigator.clipboard.readText().catch(() => ''));
    if (scheme === 'light' && clip !== code) errs.push('el portapapeles no tiene el código');
    console.log(scheme, 'botón:', await p.textContent('#copy'), '| store:', await p.textContent('#store'));
    await p.screenshot({ path: `${OUT}/rutina-${scheme}-2-copiado.png` });
    // enlace cortado
    await p.goto('about:blank'); await p.goto('http://localhost:8766/r/#' + code.slice(0, 300) + code.slice(-7)); await p.waitForTimeout(500);
    console.log(scheme, 'cortado:', await p.textContent('.empty h1'), '|', await p.isHidden('#bar'));
    await p.screenshot({ path: `${OUT}/rutina-${scheme}-3-error.png` });
    await p.goto('about:blank'); await p.goto('http://localhost:8766/r/'); await p.waitForTimeout(500);
    console.log(scheme, 'sin código:', await p.textContent('.empty h1'));
    // XSS: un nombre con HTML se ve como texto
    await ctx.close();
  }
  const C = await import(path.resolve(__dirname, '../r/codigo.js'));
  const evil = await C.encodeRoutine({ v: 1, n: '<img src=x onerror="window.pwned=1">', c: '<b>X</b>', d: [{ n: '<script>alert(1)</script>', e: [{ i: 'press-banca', s: 3, r: '8' }] }] });
  const ctx = await b.newContext({ ...devices['iPhone 13'] }); const p = await ctx.newPage();
  p.on('pageerror', (e) => errs.push(e.message));
  await p.goto('http://localhost:8766/r/#' + evil); await p.waitForTimeout(600);
  if (await p.evaluate(() => window.pwned || document.querySelector('.hero img, .days script'))) errs.push('XSS: se interpretó HTML');
  console.log('xss título como texto:', await p.textContent('.hero h1'));
  await b.close();
  console.log('errors:', JSON.stringify(errs));
})();
