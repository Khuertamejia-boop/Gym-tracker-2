// Prueba de navegador (Playwright). Se ejecuta con tests/run.sh.
const { chromium, devices } = require('playwright'); const OUT = process.env.OUT; const FIX = process.env.FIX; const fs = require('fs');
(async () => { const b = await chromium.launch();
  const ctx = await b.newContext({ ...devices['iPhone 13'], colorScheme: 'light' });
  await ctx.route('**/chart.umd.min.js', r => r.fulfill({ path: FIX + '/chart.umd.min.js', contentType: 'application/javascript' }));
  await ctx.route('**/js/config.js', r => r.fulfill({ contentType: 'application/javascript', body: "export const SUPABASE_URL=''; export const SUPABASE_ANON_KEY='';" }));
  const p = await ctx.newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => m.type() === 'error' && errs.push(m.text()));
  p.on('dialog', d => d.accept());
  const click = (sel) => p.click(sel).then(() => p.waitForTimeout(250));
  await p.goto('http://localhost:8766/?importar=excel'); await p.waitForTimeout(600);
  await p.evaluate(() => { const s = JSON.parse(localStorage.getItem('gymtrack.v1')); s.profile.gender = 'male'; localStorage.setItem('gymtrack.v1', JSON.stringify(s)); localStorage.setItem('gymtrack.installDismissed', '1'); });
  await p.reload(); await p.waitForTimeout(500);
  await p.evaluate(() => { [...document.querySelectorAll('[data-action="plan-day"]')].find(x => x.textContent.includes('Pierna B')).click(); });
  await p.waitForTimeout(200); await click('.cta-bar [data-action="start"]');
  const n = await p.evaluate(() => JSON.parse(localStorage.getItem('gymtrack.v1')).draft.exercises.length);
  for (let i = 0; i < n; i++) { await click(`[data-action="go-ex"][data-i="${i}"]`); await click('[data-action="log-all"]'); }
  await click('.session-bar [data-action="finish"]'); await p.waitForTimeout(1500);
  await p.screenshot({ path: `${OUT}/v25-summary.png` });
  await click('[data-share]'); await p.waitForTimeout(1500);
  await p.screenshot({ path: `${OUT}/v25-sheet.png` });
  const grab = async (name) => { await p.waitForTimeout(1200); const d = await p.getAttribute('.share-frame img', 'src'); fs.writeFileSync(`${OUT}/v25-${name}.png`, Buffer.from(d.split(',')[1], 'base64')); };
  await p.setInputFiles('.share-acts input[type=file]', FIX + '/gymphoto.jpg');
  for (const [al, sz, pos] of [['left','m','bottom'],['center','m','bottom'],['right','m','bottom'],['center','s','top'],['left','l','bottom']]) {
    await click(`[data-l="align"][data-v="${al}"]`); await click(`[data-l="size"][data-v="${sz}"]`); await click(`[data-l="pos"][data-v="${pos}"]`);
    await grab(`${al}-${sz}-${pos}`);
  }
  console.log('saved layout:', JSON.stringify(await p.evaluate(() => JSON.parse(localStorage.getItem('gymtrack.v1')).settings.shareLayout)));
  await p.screenshot({ path: `${OUT}/v25-sheet-photo.png` });
  console.log('errors', JSON.stringify(errs)); await b.close(); })();
