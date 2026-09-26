// Prueba de navegador (Playwright). Se ejecuta con tests/run.sh.
// Compartir: sticker arrastrable, pellizco/rueda para el tamaño, alineación y exportar PNG.
const { chromium, devices } = require('playwright');
const OUT = process.env.OUT; const FIX = process.env.FIX;
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ ...devices['iPhone 13'], hasTouch: false, isMobile: false, colorScheme: 'light' });
  await ctx.route('**/chart.umd.min.js', r => r.fulfill({ path: FIX + '/chart.umd.min.js', contentType: 'application/javascript' }));
  await ctx.route('**/js/config.js', r => r.fulfill({ contentType: 'application/javascript', body: "export const SUPABASE_URL=''; export const SUPABASE_ANON_KEY='';" }));
  const p = await ctx.newPage(); const errs = [];
  p.on('pageerror', e => errs.push(e.message)); p.on('console', m => m.type() === 'error' && errs.push(m.text()));
  p.on('dialog', d => d.accept());
  const click = (sel) => p.click(sel).then(() => p.waitForTimeout(250));
  await p.goto('http://localhost:8766/?importar=excel'); await p.waitForTimeout(600);
  await p.evaluate(() => { const s = JSON.parse(localStorage.getItem('gymtrack.v1')); s.profile.gender = 'male'; localStorage.setItem('gymtrack.v1', JSON.stringify(s)); localStorage.setItem('gymtrack.installDismissed', '1'); });
  await p.reload(); await p.waitForTimeout(500);
  await p.evaluate(() => { [...document.querySelectorAll('[data-action="plan-day"]')].find(x => x.textContent.includes('Pierna B')).click(); });
  await p.waitForTimeout(200); await click('.cta-bar [data-action="start"]');
  await p.evaluate(() => { const i = document.querySelector('[data-set="kg"][data-j="0"]'); i.value = '150'; i.dispatchEvent(new Event('input', { bubbles: true })); });
  const n = await p.evaluate(() => JSON.parse(localStorage.getItem('gymtrack.v1')).draft.exercises.length);
  for (let i = 0; i < n; i++) { await click(`[data-action="go-ex"][data-i="${i}"]`); await click('[data-action="log-all"]'); }
  await click('.session-bar [data-action="finish"]'); await p.waitForTimeout(1500);
  await click('[data-share]'); await p.waitForTimeout(1500);
  const box = () => p.locator('.sf-sticker').boundingBox();
  const b0 = await box();
  console.log('sticker', Math.round(b0.width), 'x', Math.round(b0.height));
  await p.screenshot({ path: OUT + '/share-1-inicial.png' });
  // Arrastrar hacia arriba
  await p.mouse.move(b0.x + b0.width / 2, b0.y + b0.height / 2); await p.mouse.down();
  await p.mouse.move(b0.x + b0.width / 2 + 20, b0.y + b0.height / 2 - 200, { steps: 8 }); await p.mouse.up();
  const b1 = await box(); console.log('moved dy', Math.round(b1.y - b0.y));
  // Rueda = pellizco en escritorio
  for (let i = 0; i < 6; i++) await p.mouse.wheel(0, -100);
  await p.waitForTimeout(150); const b2 = await box(); console.log('scaled', (b2.width / b1.width).toFixed(2));
  await p.screenshot({ path: OUT + '/share-2-movido.png' });
  // Sin botón de alineación: cada toque cambia izquierda → centro → derecha → izquierda
  console.log('align button:', await p.locator('button.sf-align').count());
  const align = () => p.evaluate(() => JSON.parse(localStorage.getItem('gymtrack.v1')).settings.shareLayout.align);
  const fb = await p.locator('.share-frame').boundingBox();
  const seq = [];
  for (let i = 0; i < 3; i++) { await p.mouse.click(fb.x + 30, fb.y + 40); await p.waitForTimeout(700); seq.push(await align()); }
  console.log('taps:', seq.join(' → '));
  await p.mouse.click(fb.x + 30, fb.y + 40); await p.waitForTimeout(200);
  await p.screenshot({ path: OUT + '/share-2b-toque.png' });
  await p.waitForTimeout(900);
  // Girar con dos dedos (eventos de puntero simulados)
  await p.evaluate(() => {
    const f = document.querySelector('.share-frame'); const r = f.getBoundingClientRect();
    const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
    const ev = (type, id, x, y) => f.dispatchEvent(new PointerEvent(type, { pointerId: id, clientX: x, clientY: y, bubbles: true, pointerType: 'touch' }));
    ev('pointerdown', 11, cx - 60, cy); ev('pointerdown', 12, cx + 60, cy);
    for (let k = 1; k <= 10; k++) { const a = (k / 10) * (Math.PI / 6); ev('pointermove', 12, cx + 60 * Math.cos(a), cy + 60 * Math.sin(a)); ev('pointermove', 11, cx - 60 * Math.cos(a), cy - 60 * Math.sin(a)); }
    ev('pointerup', 12, 0, 0); ev('pointerup', 11, 0, 0);
  });
  await p.waitForTimeout(200);
  console.log('rotation deg:', await p.evaluate(() => Math.round(JSON.parse(localStorage.getItem('gymtrack.v1')).settings.shareLayout.t.r * 180 / Math.PI)));
  await p.screenshot({ path: OUT + '/share-2c-girado.png' });
  // Color del texto: botón blanco/negro y automático al poner una foto
  const color = () => p.evaluate(() => JSON.parse(localStorage.getItem('gymtrack.v1')).settings.shareLayout.color);
  await click('[data-act="color"]'); await p.waitForTimeout(700);
  console.log('color after tap:', await color(), '| light preview:', await p.locator('.share-frame.light').count());
  await p.screenshot({ path: OUT + '/share-2d-negro.png' });
  await click('[data-act="color"]'); await p.waitForTimeout(700); console.log('color after 2nd tap:', await color());
  const white = Buffer.from((await p.evaluate(() => { const c = document.createElement('canvas'); c.width = 400; c.height = 700; const g = c.getContext('2d'); g.fillStyle = '#f4f1ec'; g.fillRect(0, 0, 400, 700); return c.toDataURL('image/png'); })).split(',')[1], 'base64');
  await p.setInputFiles('.share-acts input[type=file]', { name: 'blanca.png', mimeType: 'image/png', buffer: white }); await p.waitForTimeout(900);
  console.log('auto on white photo:', await color());
  await p.screenshot({ path: OUT + '/share-2e-foto-blanca.png' });
  await p.setInputFiles('.share-acts input[type=file]', FIX + '/gymphoto.jpg'); await p.waitForTimeout(900);
  console.log('auto on dark photo:', await color());
  await p.screenshot({ path: OUT + '/share-3-foto.png' });
  const dl = p.waitForEvent('download', { timeout: 5000 }).catch(() => null);
  await click('[data-act="save"]'); const f = await dl;
  if (f) { await f.saveAs(OUT + '/share-final.png'); console.log('exportado'); } else { console.log('no download'); errs.push('sin descarga'); }
  console.log('errors:', JSON.stringify(errs));
  await b.close();
})();
