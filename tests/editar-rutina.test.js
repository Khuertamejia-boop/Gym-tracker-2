// Prueba de navegador (Playwright). Se ejecuta con tests/run.sh.
// Editor de rutina: al elegirla (paso «Tu rutina»), desde Entrenar («Editar») y la hoja de cada ejercicio.
const { chromium, devices } = require('playwright'); const OUT = process.env.OUT; const FIX = process.env.FIX;
(async () => { const b = await chromium.launch(); const errs = [];
  for (const scheme of ['light', 'dark']) {
    const ctx = await b.newContext({ ...devices['iPhone 13'], colorScheme: scheme });
    await ctx.route('**/chart.umd.min.js', r => r.fulfill({ path: FIX + '/chart.umd.min.js', contentType: 'application/javascript' }));
    await ctx.route('**/js/config.js', r => r.fulfill({ contentType: 'application/javascript', body: "export const SUPABASE_URL=''; export const SUPABASE_ANON_KEY='';" }));
    const p = await ctx.newPage(); p.on('pageerror', e => errs.push(e.message)); p.on('console', m => m.type() === 'error' && errs.push(m.text()));
    p.on('dialog', d => d.accept());
    const click = (sel) => p.click(sel).then(() => p.waitForTimeout(250));
    const day = () => p.evaluate(() => { const s = JSON.parse(localStorage.getItem('gymtrack.v1')); const r = s.routines.find(x => x.id === s.activeRoutineId); return r.days.map(d => d.exercises.map(e => `${e.exId}:${e.sets}x${e.reps}`)); });
    await p.goto('http://localhost:8766/'); await p.waitForTimeout(600);
    await click('[data-action="ob-go"][data-step="experience"]'); await click('[data-action="ob-gender"][data-v="male"]');
    await click('[data-action="ob-level"][data-v="beginner"]');
    for (const d of [0, 1, 3, 4]) await click(`[data-action="ob-day"][data-d="${d}"]`);
    await click('[data-action="ob-go"][data-step="choose"]'); await click('.ob-foot [data-action="ob-pick"]');
    await p.waitForTimeout(500);
    console.log(scheme, 'paso:', await p.textContent('.ob-title'), '| días:', await p.locator('[data-action="red-day"]').count(), '| ejercicios:', await p.locator('.red-item').count());
    await p.screenshot({ path: OUT + `/editar-1-${scheme}.png` });
    if (scheme === 'light') {
      const before = (await day())[0];
      // Arrastrar el primero debajo del segundo
      const h = await p.locator('.red-handle').nth(0).boundingBox(); const h2 = await p.locator('.red-item').nth(1).boundingBox();
      await p.mouse.move(h.x + h.width / 2, h.y + h.height / 2); await p.mouse.down();
      await p.mouse.move(h.x + h.width / 2, h2.y + h2.height * 0.9, { steps: 10 }); await p.mouse.up(); await p.waitForTimeout(300);
      const after = (await day())[0];
      console.log('arrastrar: primero ahora segundo:', after[1] === before[0] && after[0] === before[1]);
      // Hoja del ejercicio: series +1, reps
      await click('.red-item:nth-child(1) [data-action="rex-open"]');
      await p.screenshot({ path: OUT + '/editar-2-hoja.png' });
      await click('#sheet [data-action="rex-sets"][data-d="1"]');
      await p.fill('#sheet .rex-reps', '10-12'); await click('#sheet [data-action="close-sheet"]');
      console.log('series/reps:', (await day())[0][0], '| fila:', (await p.textContent('.red-item:nth-child(1) .meta')).trim());
      // Cambiar por otro ejercicio (mismo músculo primero)
      await click('.red-item:nth-child(1) [data-action="rex-open"]'); await click('#sheet [data-action="rex-swap"]');
      console.log('buscador:', await p.textContent('#sheet h2'), '| filtro:', await p.textContent('#pick-chips .chip.active'));
      await p.locator('#pick-results [data-action="pick"]').nth(1).click(); await p.waitForTimeout(300);
      console.log('cambiado:', (await day())[0][0]);
      // Pasar a otro día y quitar
      await click('.red-item:nth-child(1) [data-action="rex-open"]'); await click('#sheet [data-action="rex-day-menu"]');
      await p.locator('#sheet [data-action="rex-to-day"]').nth(0).click(); await p.waitForTimeout(300);
      const d2 = await day(); console.log('pasado: día1', d2[0].length, 'día2', d2[1].length);
      await click('.red-item:nth-child(1) [data-action="rex-open"]'); await click('#sheet [data-action="rex-remove"]');
      console.log('quitado: día1', (await day())[0].length);
    }
    await click('[data-action="ob-review-done"]');
    console.log('tras empezar:', await p.textContent('#view-title'), '| botón Editar:', await p.locator('[data-action="edit-day"]').count());
    await p.screenshot({ path: OUT + `/editar-3-entrenar-${scheme}.png` });
    await click('[data-action="edit-day"]');
    console.log('editor desde Entrenar:', await p.locator('.red-item').count(), 'ejercicios | pestaña:', await p.textContent('#view-title'));
    await p.screenshot({ path: OUT + `/editar-4-plan-${scheme}.png` });
    await click('[data-action="close-editor"]');
    console.log('vuelve a:', await p.textContent('#view-title'));
    await ctx.close();
  }
  console.log('errors', JSON.stringify(errs)); await b.close(); })();
