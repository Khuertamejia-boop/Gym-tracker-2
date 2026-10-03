// Prueba sin navegador: formato del código de rutina «GT1» (r/codigo.js).
// Comprueba ida y vuelta, el ejemplo de docs/app-ios/datos/codigo-rutina/ y los errores.
const fs = require('fs'); const path = require('path');
(async () => {
  const C = await import(path.resolve(__dirname, '../r/codigo.js'));
  const errors = []; const ok = (cond, msg) => { if (!cond) errors.push(msg); };
  const expectErr = async (input, code, msg) => {
    try { await C.decodeRoutine(input); errors.push(`${msg}: no dio error`); }
    catch (e) { ok(e.code === code, `${msg}: esperaba ${code}, dio ${e.code} (${e.detail || e.message})`); }
  };
  const dir = path.resolve(__dirname, '../docs/app-ios/datos/codigo-rutina');
  const sample = JSON.parse(fs.readFileSync(dir + '/ejemplo.json', 'utf8'));

  // 1) Ida y vuelta
  const code = await C.encodeRoutine(sample);
  console.log('largo del código:', code.length);
  const back = await C.decodeRoutine(code);
  ok(JSON.stringify(back) === JSON.stringify(C.validateRoutine(sample)), 'ida y vuelta distinta');

  // 2) El código guardado en docs (vector para Swift) se sigue leyendo igual
  const vectorFile = dir + '/ejemplo.codigo.txt';
  if (!fs.existsSync(vectorFile) || process.env.REGENERAR) fs.writeFileSync(vectorFile, code + '\n');
  const vector = fs.readFileSync(vectorFile, 'utf8').trim();
  ok(JSON.stringify(await C.decodeRoutine(vector)) === JSON.stringify(back), 'el vector de docs no coincide');
  const vectorJson = dir + '/ejemplo.decodificado.json';
  fs.writeFileSync(vectorJson, JSON.stringify(back, null, 1) + '\n');

  // 3) Dentro de un enlace o de un mensaje de WhatsApp
  const msg = `Hola Luis 💪 Descarga la app: https://khuertamejia-boop.github.io/Gym-tracker-2/r/#${code}\nCódigo: ${code}`;
  ok((await C.decodeRoutine(msg)).n === sample.n, 'no lo encuentra dentro del mensaje');
  ok((await C.decodeRoutine(code.slice(0, 40) + '\n ' + code.slice(40))).n === sample.n, 'no tolera espacios/saltos');

  // 4) Errores
  await expectErr('hola', 'NO_CODE', 'texto sin código');
  await expectErr(code.slice(0, -20) + code.slice(-7), 'CHECKSUM', 'código cortado');
  await expectErr(code.slice(0, -1) + (code.endsWith('0') ? '1' : '0'), 'CHECKSUM', 'control alterado');
  await expectErr(code.replace('GT1-', 'GT2-'), 'VERSION', 'versión nueva');
  const evil = async (obj) => { const raw = new TextEncoder().encode(JSON.stringify(obj));
    const s = new CompressionStream('deflate-raw'); const w = s.writable.getWriter(); w.write(raw); w.close();
    const buf = new Uint8Array(await new Response(s.readable).arrayBuffer());
    const p = Buffer.from(buf).toString('base64url'); return `GT1-${p}.${C.fnv24(p)}`; };
  await expectErr(await evil({ ...sample, d: [] }), 'INVALID', 'sin días');
  await expectErr(await evil({ ...sample, n: 'x'.repeat(61) }), 'INVALID', 'nombre largo');
  await expectErr(await evil({ ...sample, d: [{ n: 'A', e: [{ i: '<img src=x onerror=alert(1)>', s: 3, r: '8' }] }] }), 'INVALID', 'id con HTML');
  await expectErr(await evil({ ...sample, d: [{ n: 'A', e: [{ i: 'press-banca', s: 99, r: '8' }] }] }), 'INVALID', 'series fuera de rango');
  await expectErr(await evil({ ...sample, d: [{ n: 'A', e: [{ i: 'press-banca', s: 3, r: '12-8' }] }] }), 'INVALID', 'reps al revés');
  await expectErr(await evil({ ...sample, d: [{ n: 'A', e: [{ i: 'c-nada', s: 3, r: '8' }] }] }), 'INVALID', 'propio sin definir');
  await expectErr(await evil({ ...sample, w: [0, 9, null, null, null, null, null] }), 'INVALID', 'semana con día inexistente');
  const big = { v: 1, n: 'Grande', d: Array.from({ length: 7 }, (_, i) => ({ n: 'D' + i, e: Array.from({ length: 30 }, () => ({ i: 'press-banca', s: 3, r: '8-10' })) })) };
  await expectErr(await evil(big), 'INVALID', 'demasiados ejercicios');
  await expectErr(await evil({ v: 1, n: 'Bomba', m: 'a'.repeat(200000), d: sample.d }), 'TOO_BIG', 'bomba de compresión');
  await expectErr('GT1-' + 'A'.repeat(40) + '.' + C.fnv24('A'.repeat(40)), 'CORRUPT', 'datos basura');
  // Campos desconocidos se ignoran (compatibilidad dentro de v1)
  ok((await C.decodeRoutine(await evil({ ...sample, z: 1 }))).z === undefined, 'no ignora campos nuevos');

  // 5) Rutina típica de 6 días: largo del código
  const tpls = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../docs/app-ios/datos/plantillas.json'), 'utf8'));
  for (const t of tpls) {
    const r = { v: 1, n: t.name, c: 'Carlos Ríos', w: t.week, d: t.days.map((d) => ({ n: d.name, e: d.exercises.map((e) => ({ i: e.exId, s: e.sets, r: e.reps })) })) };
    console.log(`  ${t.name}: ${(await C.encodeRoutine(r)).length} caracteres`);
  }
  console.log('resumen', JSON.stringify(C.summarize(back)));
  console.log('errors:', JSON.stringify(errors));
  if (errors.length) process.exit(1);
})().catch((e) => { console.log('errors: ["' + e.message + '"]'); process.exit(1); });
