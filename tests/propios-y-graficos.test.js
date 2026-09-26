// Prueba de navegador (Playwright). Se ejecuta con tests/run.sh.
// Ejercicios propios: editar y borrar. Progreso: tocar un punto del gráfico abre ese entreno.
const { chromium } = require('playwright'); const OUT = process.env.OUT; const FIX = process.env.FIX;
(async () => { const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, colorScheme: 'light', hasTouch: false });
  await ctx.route('**/chart.umd.min.js', r => r.fulfill({ path: FIX + '/chart.umd.min.js', contentType: 'application/javascript' }));
  await ctx.route('**/js/config.js', r => r.fulfill({ contentType: 'application/javascript', body: "export const SUPABASE_URL=''; export const SUPABASE_ANON_KEY='';" }));
  const p = await ctx.newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => m.type() === 'error' && errs.push(m.text()));
  p.on('dialog', d => d.accept());
  const click = (sel) => p.click(sel).then(() => p.waitForTimeout(300));
  await p.goto('http://localhost:8766/?importar=excel'); await p.waitForTimeout(500);
  await p.evaluate(() => {
    const st = JSON.parse(localStorage.getItem('gymtrack.v1'));
    st.profile.gender = 'male';
    st.customExercises.push({ id: 'c-x1', name: 'Pres de banco raro', muscle: 'Pecho', equipment: 'Barra', custom: true });
    const r = st.routines[0]; const now = Date.now();
    for (let w = 8; w >= 1; w--) r.days.forEach((d, k) => {
      const t = now - (w * 7 - k * 2) * 86400000; const date = new Date(t).toISOString().slice(0, 10);
      st.sessions.push({ id: 'x' + w + k, date, startedAt: t, finishedAt: t + 50 * 60000, dayName: d.name,
        exercises: d.exercises.map((e, j) => ({ exId: e.exId, sets: [{ kg: w === 4 ? 900 : 40 + j * 5, reps: 10, done: true }] })) });
    });
    st.sessions.sort((a, b) => a.date < b.date ? -1 : 1);
    localStorage.setItem('gymtrack.v1', JSON.stringify(st));
  });
  await p.reload(); await p.waitForTimeout(600);
  // Editar y borrar el ejercicio propio desde su ficha
  await p.evaluate(() => { const x = document.createElement('button'); x.id = 'open-c'; x.dataset.action = 'ex-detail'; x.dataset.id = 'c-x1'; document.body.append(x); });
  await click('#open-c');
  console.log('botones:', await p.locator('#sheet [data-action="custom-edit"]').count(), await p.locator('#sheet [data-action="custom-delete"]').count());
  await click('#sheet [data-action="custom-edit"]');
  await p.fill('#new-ex [name=name]', 'Press de banca raro'); await click('#new-ex button');
  console.log('renombrado:', await p.textContent('#sheet h2'), '| aviso:', await p.textContent('#toast'));
  await click('#sheet [data-action="custom-delete"]');
  const search = await p.evaluate(async () => (await import('/js/store.js')).searchExercises('raro').length);
  console.log('borrado → en buscador:', search, '| nombre conservado:', await p.evaluate(async () => (await import('/js/store.js')).exById('c-x1').name));
  // Progreso: tocar un punto del gráfico abre ese entreno
  await click('.tabbar [data-tab="progress"]'); await p.waitForTimeout(700);
  const box = await p.locator('#c-ex-0').boundingBox();
  await p.mouse.click(box.x + box.width * 0.5, box.y + box.height * 0.5); await p.waitForTimeout(500);
  console.log('toque en gráfico → hoja:', await p.evaluate(() => document.getElementById('sheet').open), '| editar:', await p.locator('#sheet [data-action="edit-session"]').count());
  await p.screenshot({ path: OUT + '/grafico-toque.png' });
  console.log('errors', JSON.stringify(errs)); await b.close(); })();
