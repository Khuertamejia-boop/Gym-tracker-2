// Código de rutina «GT1» — formato para compartir una rutina de entrenador sin servidor.
// La especificación completa (para la app de Xcode) está en docs/app-ios/MODO-ENTRENADOR.md.
//
//   GT1-<datos>.<control>
//   datos   = base64url sin relleno de DEFLATE «crudo» (RFC 1951) del JSON en UTF-8
//   control = 6 cifras hex (minúsculas) = FNV-1a de 32 bits sobre el texto <datos>, quedándose con los 24 bits bajos
//
// Este archivo funciona igual en el navegador (Safari 16.4+) y en Node 18+.

export const PREFIX = 'GT1-';
export const LIMITS = {
  codeChars: 12000, // longitud máxima del código completo
  jsonBytes: 65536, // tamaño máximo del JSON ya descomprimido
  days: 7,
  exercisesPerDay: 30,
  exercisesTotal: 150,
  sets: 20,
  rest: 600,
  routineName: 60,
  dayName: 40,
  person: 40,
  note: 500,
  exerciseNote: 200,
  customExercises: 50,
  customName: 60,
  equipment: 30,
};
export const MUSCLE_GROUPS = [
  'Pecho', 'Espalda', 'Hombros', 'Bíceps', 'Tríceps', 'Antebrazo',
  'Cuádriceps', 'Isquios', 'Glúteos', 'Pantorrillas', 'Abdomen',
];

const MESSAGES = {
  NO_CODE: 'No encontramos un código de rutina. Revisa que lo hayas copiado completo (empieza por «GT1-»).',
  VERSION: 'Este código es de una versión más nueva de la app. Actualiza GymTracker y vuelve a intentarlo.',
  TOO_BIG: 'El código es demasiado largo.',
  CHECKSUM: 'El código está incompleto o tiene un error. Pide a tu entrenador que te lo vuelva a enviar.',
  CORRUPT: 'El código está dañado. Pide a tu entrenador que te lo vuelva a enviar.',
  INVALID: 'El código no contiene una rutina válida.',
};

export class RoutineCodeError extends Error {
  constructor(code, detail = '') {
    super(MESSAGES[code] || code);
    this.code = code;
    this.detail = detail;
  }
}

// ---------- utilidades ----------

export function fnv24(text) {
  let h = 0x811c9dc5;
  for (let i = 0; i < text.length; i++) {
    h ^= text.charCodeAt(i) & 0xff;
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return (h & 0xffffff).toString(16).padStart(6, '0');
}

function toBase64Url(bytes) {
  let bin = '';
  for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function fromBase64Url(text) {
  const b64 = text.replace(/-/g, '+').replace(/_/g, '/');
  const bin = atob(b64 + '='.repeat((4 - (b64.length % 4)) % 4));
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

async function pipe(bytes, stream, maxOut = Infinity) {
  const writer = stream.writable.getWriter();
  writer.write(bytes).catch(() => {});
  writer.close().catch(() => {});
  const reader = stream.readable.getReader();
  const chunks = []; let total = 0;
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    total += value.length;
    if (total > maxOut) { reader.cancel().catch(() => {}); throw new RoutineCodeError('TOO_BIG'); }
    chunks.push(value);
  }
  const out = new Uint8Array(total); let o = 0;
  for (const c of chunks) { out.set(c, o); o += c.length; }
  return out;
}

// ---------- buscar el código dentro de un texto pegado ----------

// Acepta el código solo, el enlace (…/r/#GT1-…) o el mensaje de WhatsApp completo.
export function extractCode(input) {
  const text = String(input ?? '');
  const find = (t) => t.match(/GT([0-9])-([A-Za-z0-9_-]+)\.([0-9a-fA-F]{6})(?![0-9a-zA-Z])/);
  const m = find(text) || find(text.replace(/\s+/g, ''));
  if (!m) {
    if (/GT[2-9]-/.test(text)) throw new RoutineCodeError('VERSION');
    throw new RoutineCodeError('NO_CODE');
  }
  if (m[1] !== '1') throw new RoutineCodeError('VERSION');
  if (m[0].length > LIMITS.codeChars) throw new RoutineCodeError('TOO_BIG');
  return { full: m[0], payload: m[2], check: m[3].toLowerCase() };
}

// ---------- validación y limpieza ----------

const str = (v, max, { required = false, field = '' } = {}) => {
  if (v === undefined || v === null || v === '') {
    if (required) throw new RoutineCodeError('INVALID', `${field} vacío`);
    return undefined;
  }
  if (typeof v !== 'string') throw new RoutineCodeError('INVALID', `${field} no es texto`);
  // Sin caracteres de control (salvo salto de línea en notas).
  const clean = v.replace(/[\u0000-\u0009\u000b-\u001f\u007f]/g, '').trim();
  if (!clean && required) throw new RoutineCodeError('INVALID', `${field} vacío`);
  if ([...clean].length > max) throw new RoutineCodeError('INVALID', `${field} demasiado largo`);
  return clean || undefined;
};
const int = (v, min, max, field) => {
  if (!Number.isInteger(v) || v < min || v > max) throw new RoutineCodeError('INVALID', `${field} fuera de rango`);
  return v;
};
const EX_ID = /^[a-z0-9][a-z0-9-]{0,59}$/;
const REPS = /^(\d{1,3})(?:-(\d{1,3}))?$/;

// Comprueba el objeto y devuelve una copia limpia (solo los campos conocidos, en orden fijo).
export function validateRoutine(r) {
  if (!r || typeof r !== 'object' || Array.isArray(r)) throw new RoutineCodeError('INVALID', 'no es un objeto');
  if (r.v !== 1) throw new RoutineCodeError(Number.isInteger(r.v) && r.v > 1 ? 'VERSION' : 'INVALID', 'versión');
  const out = { v: 1, n: str(r.n, LIMITS.routineName, { required: true, field: 'nombre' }) };
  const c = str(r.c, LIMITS.person, { field: 'entrenador' }); if (c) out.c = c;
  const a = str(r.a, LIMITS.person, { field: 'alumno' }); if (a) out.a = a;
  const m = str(r.m, LIMITS.note, { field: 'nota' }); if (m) out.m = m;

  if (!Array.isArray(r.d) || r.d.length < 1 || r.d.length > LIMITS.days) throw new RoutineCodeError('INVALID', 'días');
  const custom = {};
  if (r.x !== undefined) {
    if (!r.x || typeof r.x !== 'object' || Array.isArray(r.x)) throw new RoutineCodeError('INVALID', 'ejercicios propios');
    const keys = Object.keys(r.x);
    if (keys.length > LIMITS.customExercises) throw new RoutineCodeError('INVALID', 'demasiados ejercicios propios');
    for (const id of keys) {
      if (!id.startsWith('c-') || !EX_ID.test(id)) throw new RoutineCodeError('INVALID', `id propio ${id}`);
      const e = r.x[id];
      if (!e || typeof e !== 'object') throw new RoutineCodeError('INVALID', `ejercicio propio ${id}`);
      const g = e.g;
      if (!MUSCLE_GROUPS.includes(g)) throw new RoutineCodeError('INVALID', `músculo de ${id}`);
      const ce = { n: str(e.n, LIMITS.customName, { required: true, field: 'nombre del ejercicio' }), g };
      const q = str(e.q, LIMITS.equipment, { field: 'equipo' }); if (q) ce.q = q;
      custom[id] = ce;
    }
  }

  let total = 0;
  out.d = r.d.map((d, di) => {
    if (!d || typeof d !== 'object') throw new RoutineCodeError('INVALID', `día ${di + 1}`);
    const name = str(d.n, LIMITS.dayName, { required: true, field: `nombre del día ${di + 1}` });
    if (!Array.isArray(d.e) || d.e.length < 1 || d.e.length > LIMITS.exercisesPerDay) throw new RoutineCodeError('INVALID', `ejercicios del día ${di + 1}`);
    total += d.e.length;
    const e = d.e.map((x, xi) => {
      const where = `día ${di + 1}, ejercicio ${xi + 1}`;
      if (!x || typeof x !== 'object') throw new RoutineCodeError('INVALID', where);
      if (typeof x.i !== 'string' || !EX_ID.test(x.i)) throw new RoutineCodeError('INVALID', `${where}: id`);
      if (x.i.startsWith('c-') && !custom[x.i]) throw new RoutineCodeError('INVALID', `${where}: ejercicio propio sin definir`);
      const reps = typeof x.r === 'string' ? x.r.replace(/\s+/g, '').replace(/[–—]/g, '-') : '';
      const rm = reps.match(REPS);
      if (reps && (!rm || +rm[1] < 1 || (rm[2] && +rm[2] < +rm[1]))) throw new RoutineCodeError('INVALID', `${where}: repeticiones`);
      const ex = { i: x.i, s: int(x.s, 1, LIMITS.sets, `${where}: series`) };
      if (reps) ex.r = reps; // sin «r» = sin objetivo de repeticiones
      if (x.t !== undefined && x.t !== 0) ex.t = int(x.t, 0, LIMITS.rest, `${where}: descanso`);
      const o = str(x.o, LIMITS.exerciseNote, { field: `${where}: nota` }); if (o) ex.o = o;
      return ex;
    });
    return { n: name, e };
  });
  if (total > LIMITS.exercisesTotal) throw new RoutineCodeError('INVALID', 'demasiados ejercicios');

  if (r.w !== undefined) {
    if (!Array.isArray(r.w) || r.w.length !== 7) throw new RoutineCodeError('INVALID', 'semana');
    out.w = r.w.map((v) => (v === null ? null : int(v, 0, out.d.length - 1, 'semana')));
  }
  // Solo se guardan los ejercicios propios que se usan.
  const used = Object.keys(custom).filter((id) => out.d.some((d) => d.e.some((x) => x.i === id)));
  if (used.length) out.x = Object.fromEntries(used.map((id) => [id, custom[id]]));
  return out;
}

// ---------- codificar / decodificar ----------

export async function encodeRoutine(routine) {
  const clean = validateRoutine(routine);
  const json = new TextEncoder().encode(JSON.stringify(clean));
  const packed = await pipe(json, new CompressionStream('deflate-raw'));
  const payload = toBase64Url(packed);
  const code = `${PREFIX}${payload}.${fnv24(payload)}`;
  if (code.length > LIMITS.codeChars) throw new RoutineCodeError('TOO_BIG');
  return code;
}

export async function decodeRoutine(input) {
  const { payload, check } = extractCode(input);
  if (fnv24(payload) !== check) throw new RoutineCodeError('CHECKSUM');
  let json;
  try {
    const bytes = await pipe(fromBase64Url(payload), new DecompressionStream('deflate-raw'), LIMITS.jsonBytes);
    json = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes));
  } catch (e) {
    if (e instanceof RoutineCodeError) throw e;
    throw new RoutineCodeError('CORRUPT', e.message);
  }
  return validateRoutine(json);
}

// Resumen para la vista previa: «4 días · 22 ejercicios · 68 series por semana».
export function summarize(r) {
  const exercises = r.d.reduce((n, d) => n + d.e.length, 0);
  const setsPerDay = r.d.map((d) => d.e.reduce((n, x) => n + x.s, 0));
  const weekly = r.w ? r.w.reduce((n, di) => n + (di === null ? 0 : setsPerDay[di]), 0) : setsPerDay.reduce((a, b) => a + b, 0);
  return { days: r.d.length, exercises, weeklySets: weekly };
}
