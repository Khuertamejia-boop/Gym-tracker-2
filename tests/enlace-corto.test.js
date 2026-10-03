// Prueba sin navegador: worker/rutinas.js (enlaces cortos) con un KV simulado.
const fs = require('fs'); const path = require('path');
(async () => {
  const W = (await import(path.resolve(__dirname, '../worker/rutinas.js'))).default;
  const store = new Map();
  const env = { RUTINAS: { get: async (k, t) => (store.has(k) ? (t === 'json' ? JSON.parse(store.get(k)) : store.get(k)) : null), put: async (k, v) => { store.set(k, v); } } };
  const call = (method, p, body, headers = {}) => W.fetch(new Request('https://gymtracker.test' + p, { method, body: body && JSON.stringify(body), headers: { 'Content-Type': 'application/json', ...headers } }), env);
  const errors = []; const ok = (c, m) => { if (!c) errors.push(m); };
  const code = fs.readFileSync(path.resolve(__dirname, '../docs/app-ios/datos/codigo-rutina/ejemplo.codigo.txt'), 'utf8').trim();

  let r = await call('POST', '/api/r', { code });
  const created = await r.json();
  console.log('crear', r.status, created.url, '| largo del enlace:', created.url.replace('https://gymtracker.test', 'gymtracker.app').length);
  ok(r.status === 201 && /^[A-Za-z2-9]{7}$/.test(created.id) && created.editKey.length === 24, 'crear');

  r = await call('GET', '/r/' + created.id);
  ok(r.status === 302 && r.headers.get('Location').endsWith('#' + code), 'redirección');
  r = await call('GET', '/api/r/' + created.id);
  ok((await r.json()).code === code, 'leer código');

  // Actualizar con y sin permiso
  const C = await import(path.resolve(__dirname, '../r/codigo.js'));
  const sample = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../docs/app-ios/datos/codigo-rutina/ejemplo.json'), 'utf8'));
  const code2 = await C.encodeRoutine({ ...sample, n: 'Rutina corregida' });
  r = await call('PUT', '/api/r/' + created.id, { code: code2 }, { Authorization: 'Bearer malo' });
  ok(r.status === 403, 'actualizar sin permiso debería fallar');
  r = await call('PUT', '/api/r/' + created.id, { code: code2 }, { Authorization: 'Bearer ' + created.editKey });
  ok(r.status === 200, 'actualizar con permiso');
  ok((await (await call('GET', '/api/r/' + created.id)).json()).code === code2, 'el enlace muestra la versión nueva');

  // Errores
  ok((await call('POST', '/api/r', { code: code.slice(0, -1) + 'x' })).status === 400, 'código con control malo');
  ok((await call('POST', '/api/r', { code: 'hola' })).status === 400, 'texto cualquiera');
  ok((await call('POST', '/api/r', { code: 'GT1-' + 'A'.repeat(13000) + '.000000' })).status === 400, 'código enorme');
  ok((await call('GET', '/r/noexiste')).status === 404, 'id inexistente');
  ok((await call('GET', '/r/<script>')).status === 404, 'id raro');
  ok((await call('GET', '/api/r/ABCDEFG')).status === 404, 'api id inexistente');
  console.log('errors:', JSON.stringify(errors));
  if (errors.length) process.exit(1);
})().catch((e) => { console.log('errors: ["' + e.message + '"]'); process.exit(1); });
