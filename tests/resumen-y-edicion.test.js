// Prueba de navegador (Playwright). Se ejecuta con tests/run.sh.
const { chromium } = require('playwright');
const OUT = process.env.OUT; const FIX = process.env.FIX;
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, colorScheme: 'dark' });
  await ctx.route('**/chart.umd.min.js', r => r.fulfill({ path: FIX + '/chart.umd.min.js', contentType: 'application/javascript' }));
  await ctx.route('**/js/config.js', r => r.fulfill({ contentType: 'application/javascript', body: "export const SUPABASE_URL=''; export const SUPABASE_ANON_KEY='';" }));
  const p = await ctx.newPage(); const errs = [];
  p.on('pageerror', e => errs.push(e.message)); p.on('console', m => m.type() === 'error' && errs.push(m.text()));
  p.on('dialog', d => d.accept());
  const click = (sel) => p.click(sel).then(() => p.waitForTimeout(150));
  await p.goto('http://localhost:8766/?importar=excel'); await p.waitForTimeout(600);
  await p.evaluate(() => JSON.parse(localStorage.getItem('gymtrack.v1')).profile && 0);
  await click('[data-action="set-gender"][data-v="male"]').catch(() => {});
  await p.evaluate(() => { [...document.querySelectorAll('[data-action="plan-day"]')].find(x => x.textContent.includes('Torso A')).click(); });
  await p.waitForTimeout(200);
  await click('.cta-bar [data-action="start"]');
  console.log('discard visible in page:', await p.locator('#view [data-action="discard"]').count());
  // ⋯ menú
  await click('[data-action="session-menu"]');
  console.log('menu has discard:', await p.locator('#sheet [data-action="discard"]').count());
  await p.screenshot({ path: OUT + '/v7-menu.png' });
  await click('#sheet [data-action="close-sheet"]');
  // Marcar todas las series con el botón inferior y pasar de ejercicio
  for (let k = 0; k < 20; k++) {
    const btn = p.locator('.session-btn');
    const action = await btn.getAttribute('data-action');
    if (action === 'finish') break;
    await btn.click(); await p.waitForTimeout(120);
  }
  console.log('toast after all sets:', await p.textContent('#toast'));
  await p.screenshot({ path: OUT + '/v7-bottom.png' });
  await click('.finish-btn'); await p.waitForTimeout(2200);
  console.log('summary open:', await p.locator('.celebrate').count(), '| stats:', (await p.locator('.win-stat').allTextContents()).map(t => t.replace(/\s+/g, ' ').trim()).join(' | '));
  console.log('worked:', await p.locator('.win-ex').count(), '| week:', (await p.locator('.win-week').textContent().catch(() => '')).replace(/\s+/g, ' ').trim());
  console.log('body maps in summary:', await p.locator('.celebrate svg image').count());
  await p.screenshot({ path: OUT + '/v7-summary.png' });
  await p.screenshot({ path: OUT + '/v7-summary-full.png', fullPage: false });
  await p.locator('.win-done').scrollIntoViewIfNeeded();
  await p.screenshot({ path: OUT + '/v7-summary-bottom.png' });
  await click('.win-done');
  console.log('closed:', await p.locator('.celebrate').count() === 0, '| title:', await p.textContent('#view-title'));
  // Edición: botón Guardar cambios
  await click('.tabbar [data-tab="progress"]');
  await click('[data-action="session-detail"]'); await click('#sheet [data-action="edit-session"]');
  console.log('edit button:', await p.textContent('.session-bar [data-action="finish"]'));
  await click('[data-action="session-menu"]'); console.log('edit menu:', (await p.textContent('#sheet .danger-row')).trim());
  await click('#sheet [data-action="discard"]');
  console.log('errors:', JSON.stringify(errs));
  await b.close();
})();
