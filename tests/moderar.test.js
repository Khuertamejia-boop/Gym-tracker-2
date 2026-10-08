// Prueba de navegador (Playwright). Se ejecuta con tests/run.sh.
// moderar.html: entrar como administrador, revisar fotos reportadas (borrosas hasta tocarlas),
// eliminar / aprobar, cerrar otros reportes y rechazar cuentas que no son administrador.
const { chromium, devices } = require('playwright'); const OUT = process.env.OUT; const FIX = process.env.FIX;
(async () => { const b = await chromium.launch(); const errors = []; const ok = (c, m) => { if (!c) errors.push(m); };
  const ctx = await b.newContext({ ...devices['iPhone 13'], colorScheme: 'dark' });
  await ctx.route('**/supabase-js@*/**', r => r.fulfill({ path: FIX + '/mock-supabase-admin.js', contentType: 'application/javascript' }));
  const p = await ctx.newPage(); let confirmMsg = '';
  p.on('pageerror', e => errors.push(e.message)); p.on('dialog', d => { confirmMsg = d.message(); d.accept(); });
  // La página usa <script> clásico: se sirve el mock como global `supabase`.
  await p.route('**/moderar.html', async r => { const res = await r.fetch(); let html = await res.text();
    const mock = require('fs').readFileSync(FIX + '/mock-supabase-admin.js', 'utf8').replace(/export function/g, 'function');
    html = html.replace(/<script src="[^"]*supabase-js[^"]*"><\/script>/, `<script>${mock}\nwindow.supabase = { createClient };</script>`);
    await r.fulfill({ response: res, body: html, contentType: 'text/html' }); });
  const state = () => p.evaluate(() => JSON.parse(JSON.stringify({ calls: __mod.calls, removed: __mod.removed })));

  await p.goto('http://localhost:8766/moderar.html'); await p.waitForTimeout(300);
  ok(await p.locator('#f').count() === 1, 'debe mostrar el acceso');
  await p.fill('#email', 'a@b.c'); await p.fill('#pass', 'mala'); await p.click('#f button'); await p.waitForTimeout(300);
  ok((await p.textContent('.error')).includes('incorrectos'), 'contraseña mala');
  await p.fill('#email', 'a@b.c'); await p.fill('#pass', 'secreto1'); await p.click('#f button'); await p.waitForTimeout(500);
  console.log('contadores: fotos', await p.textContent('#nf'), '| otros', await p.textContent('#no'), '| título', await p.title());
  ok(await p.textContent('#nf') === '2' && await p.textContent('#no') === '1', 'contadores');
  ok(await p.title() === '(3) Moderar', 'título con pendientes');
  ok(await p.locator('.badge').count() === 1, 'solo la foto oculta lleva «OCULTA AUTO»');
  ok((await p.textContent('.card .chips')).trim() === 'Desnudo / sexual', 'motivos sin repetir y traducidos');
  const blur = () => p.evaluate(() => getComputedStyle(document.querySelector('.photo')).filter);
  ok((await blur()).includes('blur'), 'la foto empieza borrosa');
  await p.screenshot({ path: OUT + '/moderar-fotos.png' });
  await p.click('.ph'); await p.waitForTimeout(400); ok((await blur()) === 'none', 'al tocar se ve nítida');
  await p.screenshot({ path: OUT + '/moderar-foto-vista.png' });

  // Eliminar la primera foto: confirma, llama a la función, borra el archivo y la quita de la lista
  await p.click('.card [data-a=remove]'); await p.waitForTimeout(700);
  const s1 = await state();
  console.log('confirmación:', JSON.stringify(confirmMsg.split('\n')[0]), '| borrados del bucket:', s1.removed);
  ok(confirmMsg.includes('@ana'), 'pide confirmar con el nombre');
  ok(s1.calls.some(([n, a]) => n === 'admin_resolve_avatar' && a.p_user === 'u-ana' && a.p_action === 'remove' && a.p_path === 'u-ana/1.jpg'), 'resolver avatar (remove)');
  ok(s1.removed.length === 1 && s1.removed[0] === 'u-ana/1.jpg', 'archivo borrado del bucket');
  ok(await p.textContent('#nf') === '1', 'quedan 1 foto');

  // Aprobar la otra: no borra archivos
  await p.click('.card [data-a=keep]'); await p.waitForTimeout(700);
  const s2 = await state();
  ok(s2.calls.some(([n, a]) => n === 'admin_resolve_avatar' && a.p_user === 'u-leo' && a.p_action === 'keep'), 'resolver avatar (keep)');
  ok(s2.removed.length === 1, 'aprobar no borra archivos');
  ok((await p.textContent('#lista')).includes('Nada pendiente'), 'lista vacía de fotos');

  // Otros reportes
  await p.click('.tabs [data-t=otros]'); await p.waitForTimeout(300);
  ok((await p.textContent('.card')).includes('@marta') && (await p.textContent('.card')).includes('Entreno'), 'tarjeta de entreno reportado');
  await p.screenshot({ path: OUT + '/moderar-otros.png' });
  await p.click('.card [data-s=reviewed]'); await p.waitForTimeout(700);
  ok((await state()).calls.some(([n, a]) => n === 'admin_close_report' && a.p_id === 7 && a.p_status === 'reviewed'), 'cerrar reporte');
  ok(await p.title() === 'Moderar', 'título sin pendientes');

  // Cuenta que no es administrador: se rechaza y se cierra la sesión
  await p.evaluate(() => { __mod.admin = false; __mod.session = null; });
  await p.click('#salir'); await p.waitForTimeout(200);
  await p.fill('#email', 'x@y.z'); await p.fill('#pass', 'secreto1'); await p.click('#f button'); await p.waitForTimeout(500);
  ok((await p.textContent('.error')).includes('permisos'), 'rechaza a quien no es admin');
  ok(await p.evaluate(() => __mod.session === null), 'cierra la sesión del no admin');
  await p.screenshot({ path: OUT + '/moderar-sin-permiso.png' });

  console.log('errors:', JSON.stringify(errors)); await b.close(); if (errors.length) process.exit(1); })().catch((e) => { console.log('errors: ["' + e.message + '"]'); process.exit(1); });
