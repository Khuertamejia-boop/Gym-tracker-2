// Prueba de navegador (Playwright). Se ejecuta con tests/run.sh.
// moderar.html: entrar como administrador, revisar fotos e historias reportadas (borrosas hasta tocarlas),
// eliminar / aprobar (las historias también borran el archivo en el Worker), cerrar otros reportes
// y rechazar cuentas que no son administrador.
const { chromium, devices } = require('playwright'); const OUT = process.env.OUT; const FIX = process.env.FIX;
(async () => { const b = await chromium.launch(); const errors = []; const ok = (c, m) => { if (!c) errors.push(m); };
  const ctx = await b.newContext({ ...devices['iPhone 13'], colorScheme: 'dark' });
  await ctx.route('**/supabase-js@*/**', r => r.fulfill({ path: FIX + '/mock-supabase-admin.js', contentType: 'application/javascript' }));
  // Worker de historias simulado: GET → un GIF; DELETE → se anota (con la sesión) y responde `deleteStatus`.
  const GIF = Buffer.from('R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=', 'base64'); const worker = []; let deleteStatus = 204;
  const CORS = { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'Authorization, Content-Type', 'Access-Control-Allow-Methods': 'DELETE, OPTIONS' };
  await ctx.route('https://historias.khuertamejia.workers.dev/**', r => { const q = r.request(), m = q.method();
    if (m === 'OPTIONS') return r.fulfill({ status: 204, headers: CORS });
    worker.push({ m, url: q.url(), auth: q.headers()['authorization'] || '' });
    if (m === 'DELETE') return r.fulfill({ status: deleteStatus, headers: CORS });
    if (q.url().includes('33333333')) return r.fulfill({ status: 410, body: 'Caducada' });  // foto ya caducada
    return r.fulfill({ status: 200, contentType: 'image/gif', body: GIF }); });
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
  console.log('contadores: fotos', await p.textContent('#nf'), '| historias', await p.textContent('#nh'), '| otros', await p.textContent('#no'), '| título', await p.title());
  ok(await p.textContent('#nf') === '2' && await p.textContent('#nh') === '2' && await p.textContent('#no') === '1', 'contadores');
  ok(await p.title() === '(5) Moderar', 'título con pendientes');
  ok(await p.evaluate(() => [...document.querySelectorAll('.tabs button')].every(b => b.offsetHeight < 50)), 'las 3 pestañas caben en una línea');
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

  // Historias: foto vertical borrosa, quitar borra el archivo en el Worker con la sesión del administrador
  await p.click('.tabs [data-t=historias]'); await p.waitForTimeout(400);
  const h1 = await p.textContent('.card');
  ok(h1.includes('@eva') && h1.includes('OCULTA AUTO') && h1.includes('Spam') && h1.includes('Acoso') && h1.includes('2 personas') && h1.includes('Se borra sola en 5 h'), 'tarjeta de historia con datos');
  ok((await p.getAttribute('.card .photo', 'src')).endsWith('/s/e0000000-0000-0000-0000-00000000000e/11111111-1111-1111-1111-111111111111.jpg'), 'la foto sale del Worker');
  ok((await blur()).includes('blur'), 'la historia empieza borrosa');
  await p.screenshot({ path: OUT + '/moderar-historias.png', fullPage: true });
  const bajo = await p.evaluate(() => document.querySelector('.card [data-a=remove]').getBoundingClientRect().bottom);
  ok(bajo < 844 + 40, 'los botones de la historia quedan casi a la vista en un iPhone (' + Math.round(bajo) + ' px)');
  await p.click('.ph'); await p.waitForTimeout(400); ok((await blur()) === 'none', 'la historia se ve nítida al tocar');
  await p.screenshot({ path: OUT + '/moderar-historia-vista.png' });
  await p.click('.card [data-a=remove]'); await p.waitForTimeout(800);
  const s3 = await state();
  ok(confirmMsg.includes('@eva') && confirmMsg.includes('historia'), 'pide confirmar la historia con el nombre');
  ok(s3.calls.some(([n, a]) => n === 'admin_resolve_story' && a.p_story === 's-eva' && a.p_action === 'remove'), 'resolver historia (remove)');
  const del = worker.filter(w => w.m === 'DELETE');
  ok(del.length === 1 && del[0].url.endsWith('/s/e0000000-0000-0000-0000-00000000000e/11111111-1111-1111-1111-111111111111.jpg') && del[0].auth === 'Bearer token-admin', 'borra el archivo en el Worker con la sesión del admin');
  ok(await p.textContent('#nh') === '1', 'queda 1 historia');
  await p.click('.card [data-a=keep]'); await p.waitForTimeout(700);
  ok((await state()).calls.some(([n, a]) => n === 'admin_resolve_story' && a.p_story === 's-tom' && a.p_action === 'keep'), 'resolver historia (keep)');
  ok(worker.filter(w => w.m === 'DELETE').length === 1, 'aprobar no borra archivos');
  ok((await p.textContent('#lista')).includes('Nada pendiente'), 'lista vacía de historias');

  // Foto ya caducada (410) y el Worker no puede borrar el archivo: se resuelve igual y avisa
  await p.evaluate(() => { __mod.stories.push({ story_id: 's-ivo', user_id: 'u-ivo', username: 'ivo', key: 'c0000000-0000-0000-0000-00000000000c/33333333-3333-3333-3333-333333333333.jpg', hidden: false, reports: 1, reasons: ['otro'], first_report: new Date().toISOString(), expires_at: new Date(Date.now() + 3600e3).toISOString() }); });
  await p.click('#recargar'); await p.waitForTimeout(600);
  ok(await p.locator('.card .gone').count() === 1 && (await p.textContent('.card .gone')).includes('ya no está disponible'), 'foto caducada: aviso en lugar de imagen rota');
  deleteStatus = 403; await p.click('.card [data-a=remove]'); await p.waitForTimeout(500);
  ok((await p.textContent('#toast')).includes('se borra solo'), 'si no se pudo borrar el archivo, lo dice'); deleteStatus = 204;
  ok(await p.textContent('#nh') === '0', 'la historia caducada también se pudo quitar');

  // Otros reportes
  await p.click('.tabs [data-t=otros]'); await p.waitForTimeout(300);
  ok((await p.textContent('.card')).includes('@marta') && (await p.textContent('.card')).includes('Entreno'), 'tarjeta de entreno reportado');
  await p.screenshot({ path: OUT + '/moderar-otros.png' });
  await p.click('.card [data-s=reviewed]'); await p.waitForTimeout(700);
  ok((await state()).calls.some(([n, a]) => n === 'admin_close_report' && a.p_id === 7 && a.p_status === 'reviewed'), 'cerrar reporte');
  ok(await p.title() === 'Moderar', 'título sin pendientes');

  // Si las historias fallan en Supabase, el resto de la página sigue funcionando
  await p.evaluate(() => { __mod.storiesFail = true; __mod.avatars.push({ user_id: 'u-zoe', username: 'zoe', photo_path: 'u-zoe/5.jpg', hidden: false, reports: 1, reasons: ['spam'], first_report: new Date().toISOString() }); });
  await p.click('#recargar'); await p.waitForTimeout(500);
  await p.click('.tabs [data-t=fotos]'); await p.waitForTimeout(300);
  ok((await p.textContent('.card')).includes('@zoe') && await p.textContent('#nh') === '0', 'las fotos siguen cargando si fallan las historias');
  await p.click('.tabs [data-t=historias]'); await p.waitForTimeout(300);
  ok((await p.textContent('#lista')).includes('No se pudieron cargar las historias'), 'avisa cuando fallan las historias');
  await p.screenshot({ path: OUT + '/moderar-historias-error.png' });

  // Cuenta que no es administrador: se rechaza y se cierra la sesión
  await p.evaluate(() => { __mod.admin = false; __mod.session = null; });
  await p.click('#salir'); await p.waitForTimeout(200);
  await p.fill('#email', 'x@y.z'); await p.fill('#pass', 'secreto1'); await p.click('#f button'); await p.waitForTimeout(500);
  ok((await p.textContent('.error')).includes('permisos'), 'rechaza a quien no es admin');
  ok(await p.evaluate(() => __mod.session === null), 'cierra la sesión del no admin');
  await p.screenshot({ path: OUT + '/moderar-sin-permiso.png' });

  console.log('errors:', JSON.stringify(errors)); await b.close(); if (errors.length) process.exit(1); })().catch((e) => { console.log('errors: ["' + e.message + '"]'); process.exit(1); });
