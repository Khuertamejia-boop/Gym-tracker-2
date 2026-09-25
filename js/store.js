// Persistencia en localStorage y utilidades de datos.
import { BASE_EXERCISES } from './data/exercises.js';
import { TEMPLATES } from './data/templates.js';

const KEY = 'gymtrack.v1';

export const uid = () => Math.random().toString(36).slice(2, 10) + Date.now().toString(36).slice(-4);

function emptyState() {
  return {
    version: 1,
    settings: { effort: 'RIR' },
    routines: [],
    activeRoutineId: null,
    sessions: [],
    body: [],
    customExercises: [],
    profile: null, // { level: 'beginner' | 'intermediate' | 'advanced', days: [0..6], simple: bool }
    deletedIds: [], // marcas de borrado para que la sincronización no "resucite" datos
    updatedAt: 0,
    draft: null,
  };
}

let state = load();
const saveListeners = [];

function load() {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) return { ...emptyState(), ...JSON.parse(raw) };
  } catch (e) {
    console.warn('No se pudieron leer los datos guardados', e);
  }
  return emptyState();
}

// silent: guarda sin marcar un cambio del usuario (p. ej. al aplicar datos de la nube).
export function save({ silent = false } = {}) {
  if (!silent) state.updatedAt = Date.now();
  try {
    localStorage.setItem(KEY, JSON.stringify(state));
  } catch (e) {
    alert('No se pudieron guardar los datos en este navegador.');
  }
  if (!silent) saveListeners.forEach((fn) => fn());
}

export const onSave = (fn) => saveListeners.push(fn);

export const getState = () => state;

export function replaceState(next, opts) {
  state = { ...emptyState(), ...next, draft: next.draft ?? state.draft };
  exIndex = null;
  save(opts);
}

// Borra todo, dejando marcas de borrado para que la nube también lo elimine.
export function resetState() {
  const deletedIds = [
    ...state.deletedIds,
    ...state.sessions.map((x) => x.id),
    ...state.routines.map((x) => x.id),
    ...state.body.map((x) => 'body:' + x.date),
  ];
  state = { ...emptyState(), deletedIds };
  save();
}

const tombstone = (id) => { if (!state.deletedIds.includes(id)) state.deletedIds.push(id); };

// ---------- Sincronización: fusión de dos copias ----------

function unionBy(a, b, key, preferB) {
  const map = new Map(a.map((x) => [key(x), x]));
  for (const x of b) {
    const k = key(x);
    if (!map.has(k) || preferB(map.get(k), x)) map.set(k, x);
  }
  return [...map.values()];
}

// Une los datos locales con los de la nube sin perder entrenamientos de
// ningún dispositivo. En conflictos gana la copia modificada más recientemente.
export function mergeStates(local, remote) {
  const remoteNewer = (remote.updatedAt || 0) > (local.updatedAt || 0);
  const deleted = new Set([...(local.deletedIds || []), ...(remote.deletedIds || [])]);
  const stamp = (s) => s.editedAt || s.finishedAt || s.startedAt || 0;
  const alive = (id) => !deleted.has(id);

  const sessions = unionBy(local.sessions || [], remote.sessions || [], (s) => s.id, (a, b) => stamp(b) > stamp(a))
    .filter((s) => alive(s.id))
    .sort((a, b) => (a.date === b.date ? a.startedAt - b.startedAt : a.date < b.date ? -1 : 1));
  const routines = unionBy(local.routines || [], remote.routines || [], (r) => r.id, () => remoteNewer)
    .filter((r) => alive(r.id));
  const customExercises = unionBy(local.customExercises || [], remote.customExercises || [], (e) => e.id, () => remoteNewer);
  const body = unionBy(local.body || [], remote.body || [], (b) => b.date, () => remoteNewer)
    .filter((b) => alive('body:' + b.date))
    .sort((a, b) => (a.date < b.date ? -1 : 1));
  const newer = remoteNewer ? remote : local;
  let activeRoutineId = newer.activeRoutineId;
  if (!routines.some((r) => r.id === activeRoutineId)) activeRoutineId = routines[0]?.id || null;

  return {
    ...emptyState(),
    profile: (remoteNewer ? remote.profile || local.profile : local.profile || remote.profile) || null,
    settings: { ...local.settings, ...(remoteNewer ? remote.settings : {}) },
    routines,
    activeRoutineId,
    sessions,
    body,
    customExercises,
    deletedIds: [...deleted],
    importedHistory: [...new Set([...(local.importedHistory || []), ...(remote.importedHistory || [])])],
    updatedAt: Math.max(local.updatedAt || 0, remote.updatedAt || 0),
    draft: local.draft || null,
  };
}

// ---------- Ejercicios ----------

export function allExercises() {
  return [...BASE_EXERCISES, ...state.customExercises];
}

let exIndex = null;
export function exById(id) {
  if (!exIndex || exIndex.size !== BASE_EXERCISES.length + state.customExercises.length) {
    exIndex = new Map(allExercises().map((e) => [e.id, e]));
  }
  return exIndex.get(id) || { id, name: 'Ejercicio eliminado', muscle: 'Otro', equipment: '' };
}

export function addCustomExercise(name, muscle, equipment) {
  const e = { id: 'c-' + uid(), name: name.trim(), muscle, equipment, custom: true };
  state.customExercises.push(e);
  exIndex = null;
  save();
  return e;
}

export const normalize = (s) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

export function searchExercises(query, muscle) {
  const q = normalize(query.trim());
  const words = q.split(/\s+/).filter(Boolean);
  return allExercises()
    .filter((e) => !muscle || e.muscle === muscle)
    .filter((e) => {
      const hay = normalize(`${e.name} ${e.muscle} ${e.equipment} ${e.aliases || ''}`);
      return words.every((w) => hay.includes(w));
    })
    .sort((a, b) => a.name.localeCompare(b.name, 'es'));
}

// ---------- Rutinas ----------

// weekdays (opcional): días de la semana elegidos (0 = lunes). Los días de la
// rutina se reparten en orden sobre ellos, repitiendo el ciclo si hace falta.
export function routineFromTemplate(tpl, weekdays) {
  const days = tpl.days.map((d) => ({
    id: uid(),
    name: d.name,
    exercises: d.exercises.map(({ exId, sets, reps }) => ({ exId, sets, reps })),
  }));
  const week = weekdays?.length
    ? assignWeek(days, weekdays)
    : tpl.week.map((i) => (i === null ? null : days[i].id));
  return { id: uid(), name: tpl.name, fromTemplate: tpl.key, days, week };
}

function assignWeek(days, weekdays) {
  const week = [null, null, null, null, null, null, null];
  [...weekdays].sort((a, b) => a - b).forEach((wd, i) => { week[wd] = days[i % days.length].id; });
  return week;
}

// Rutina vacía con un día de entrenamiento por cada día elegido.
export function routineForDays(weekdays, name = 'Mi rutina') {
  const sorted = [...weekdays].sort((a, b) => a - b);
  const days = sorted.map((wd, i) => ({ id: uid(), name: `Día ${i + 1}`, exercises: [] }));
  return { id: uid(), name, days, week: assignWeek(days, sorted) };
}

// Convierte los últimos pesos/reps que trae una plantilla (p. ej. la del Excel)
// en entrenamientos del historial, fechados la semana pasada.
export function importTemplateHistory(tpl, routine) {
  // Versiones anteriores importaban sin dejar marca: se detecta por las sesiones importadas.
  if (state.importedHistory?.includes(tpl.key) || state.sessions.some((x) => x.imported)) {
    if (!state.importedHistory?.includes(tpl.key)) { state.importedHistory = [...(state.importedHistory || []), tpl.key]; save(); }
    return 0;
  }
  state.importedHistory = [...(state.importedHistory || []), tpl.key];
  const monday = startOfWeek(new Date());
  monday.setDate(monday.getDate() - 7);
  let added = 0;
  tpl.days.forEach((d, di) => {
    const exercises = d.exercises
      .filter((e) => e.last && e.last.reps.length)
      .map((e) => ({
        exId: e.exId,
        target: e.reps,
        note: e.last.note || '',
        sets: e.last.reps.map((reps) => ({ kg: e.last.kg, reps, effort: '', done: true })),
      }));
    if (!exercises.length) return;
    const wd = tpl.week.indexOf(di);
    const date = new Date(monday);
    date.setDate(monday.getDate() + (wd >= 0 ? wd : di));
    const t = date.getTime() + 18 * 3600000;
    state.sessions.push({
      id: uid(), date: todayISO(date), startedAt: t, finishedAt: t + 3600000,
      routineId: routine.id, dayName: d.name, imported: true, exercises,
    });
    added++;
  });
  sortSessions();
  save();
  return added;
}

export function addRoutine(routine, makeActive = true) {
  state.routines.push(routine);
  if (makeActive || !state.activeRoutineId) state.activeRoutineId = routine.id;
  save();
  return routine;
}

export function newEmptyRoutine(name = 'Mi rutina') {
  const day = { id: uid(), name: 'Día 1', exercises: [] };
  return { id: uid(), name, days: [day], week: [day.id, null, null, null, null, null, null] };
}

export const routineById = (id) => state.routines.find((r) => r.id === id);
export const activeRoutine = () => routineById(state.activeRoutineId);

export function deleteRoutine(id) {
  state.routines = state.routines.filter((r) => r.id !== id);
  tombstone(id);
  if (state.activeRoutineId === id) state.activeRoutineId = state.routines[0]?.id || null;
  save();
}

// ---------- Unidades (kg / lb) ----------
// Los pesos se guardan siempre en kg; solo se convierten para mostrarlos y al escribirlos.
// settings.unit es la unidad por defecto y settings.units guarda la de cada ejercicio
// (útil cuando algunas máquinas del gimnasio están en libras).

export const LB = 0.45359237;
export const defaultUnit = () => state.settings.unit || 'kg';
export const unitFor = (exId) => state.settings.units?.[exId] || defaultUnit();
const round1 = (n) => Math.round(n * 10) / 10;
const roundHalf = (n) => Math.round(n * 2) / 2; // las máquinas en libras van de 2,5 en 2,5 o de 5 en 5
export const toUnit = (kg, unit) => (kg === '' || kg === null || kg === undefined ? ''
  : unit === 'lb' ? roundHalf(Number(kg) / LB) : round1(Number(kg)));
export const fromUnit = (v, unit) => (v === '' || v === null || v === undefined ? '' : unit === 'lb' ? Number(v) * LB : Number(v));

export function setDefaultUnit(unit) {
  state.settings.unit = unit;
  save();
}

export function setExerciseUnit(exId, unit) {
  const units = { ...(state.settings.units || {}) };
  if (unit === defaultUnit()) delete units[exId];
  else units[exId] = unit;
  state.settings.units = units;
  save();
}

// ---------- Perfil y configuración inicial ----------

// Un usuario nuevo (sin entrenamientos ni rutinas propias) pasa por la configuración inicial.
export function needsOnboarding() {
  return !state.profile && !state.sessions.length && state.routines.every((r) => r.seeded);
}

// Quien ya usaba la app antes de existir el perfil no repite la configuración.
export function ensureProfile() {
  if (state.profile || needsOnboarding()) return;
  state.profile = { level: 'advanced', days: [], simple: false, auto: true };
  save({ silent: true });
}

export function setProfile(profile) {
  state.profile = { ...state.profile, ...profile };
  save();
}

export const isSimple = () => Boolean(state.profile?.simple);

// Recomendación según experiencia y días disponibles.
export function recommendTemplate(level, dayCount) {
  if (dayCount <= 3) return 'full-body';
  if (level === 'beginner' || dayCount === 4) return 'torso-pierna';
  return 'ppl';
}

export const templateByKey = (key) => TEMPLATES.find((t) => t.key === key);

// ---------- Fechas ----------

export function todayISO(d = new Date()) {
  const off = d.getTimezoneOffset();
  return new Date(d.getTime() - off * 60000).toISOString().slice(0, 10);
}

export function parseISO(s) {
  const [y, m, d] = s.split('-').map(Number);
  return new Date(y, m - 1, d);
}

// Lunes = 0 ... domingo = 6
export const weekdayIndex = (d = new Date()) => (d.getDay() + 6) % 7;

export function startOfWeek(d) {
  const x = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  x.setDate(x.getDate() - weekdayIndex(x));
  return x;
}

export const DAY_NAMES = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
export const DAY_SHORT = ['L', 'M', 'X', 'J', 'V', 'S', 'D'];
export const MONTHS_SHORT = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];

export function formatDate(iso) {
  const d = parseISO(iso);
  return `${DAY_NAMES[weekdayIndex(d)].slice(0, 3)} ${d.getDate()} ${MONTHS_SHORT[d.getMonth()]}`;
}

// ---------- Sesiones ----------

export function setVolume(s) {
  const kg = Number(s.kg) || 0;
  const reps = Number(s.reps) || 0;
  return kg * reps;
}

// 1RM estimado (fórmula de Epley).
export function e1rm(s) {
  const kg = Number(s.kg) || 0;
  const reps = Number(s.reps) || 0;
  if (!kg || !reps) return 0;
  return reps === 1 ? kg : kg * (1 + reps / 30);
}

export function sessionVolume(session) {
  let v = 0;
  for (const e of session.exercises) for (const s of e.sets) if (s.done) v += setVolume(s);
  return v;
}

export function doneSets(session) {
  let n = 0;
  for (const e of session.exercises) for (const s of e.sets) if (s.done) n++;
  return n;
}

function sortSessions() {
  state.sessions.sort((a, b) => (a.date === b.date ? a.startedAt - b.startedAt : a.date < b.date ? -1 : 1));
}

// Última vez que se hizo un ejercicio, ignorando la sesión indicada (la que se edita).
export function lastPerformance(exId, excludeId) {
  for (let i = state.sessions.length - 1; i >= 0; i--) {
    const s = state.sessions[i];
    if (s.id === excludeId) continue;
    const e = s.exercises.find((x) => x.exId === exId);
    if (e && e.sets.some((x) => x.done)) {
      return { date: s.date, target: e.target, note: e.note || '', sets: e.sets.filter((x) => x.done) };
    }
  }
  return null;
}

export function exerciseHistory(exId) {
  const out = [];
  for (const s of state.sessions) {
    const e = s.exercises.find((x) => x.exId === exId);
    if (!e) continue;
    const sets = e.sets.filter((x) => x.done);
    if (sets.length) out.push({ date: s.date, sessionId: s.id, note: e.note || '', sets });
  }
  return out.reverse();
}

// Récords de un ejercicio, opcionalmente sin contar una sesión.
export function exerciseRecords(exId, excludeId) {
  const r = { maxKg: null, bestE1rm: null, bestVolume: null, maxReps: null, sessions: 0, sets: 0 };
  for (const s of state.sessions) {
    if (s.id === excludeId) continue;
    const e = s.exercises.find((x) => x.exId === exId);
    if (!e) continue;
    const sets = e.sets.filter((x) => x.done);
    if (!sets.length) continue;
    r.sessions++;
    let vol = 0;
    for (const x of sets) {
      r.sets++;
      vol += setVolume(x);
      const kg = Number(x.kg) || 0, reps = Number(x.reps) || 0;
      if (!r.maxKg || kg > r.maxKg.kg || (kg === r.maxKg.kg && reps > r.maxKg.reps)) r.maxKg = { kg, reps, date: s.date };
      const est = e1rm(x);
      if (!r.bestE1rm || est > r.bestE1rm.value) r.bestE1rm = { value: est, kg, reps, date: s.date };
      if (!r.maxReps || reps > r.maxReps.reps) r.maxReps = { kg, reps, date: s.date };
    }
    if (!r.bestVolume || vol > r.bestVolume.value) r.bestVolume = { value: vol, date: s.date };
  }
  return r;
}

// ¿Esta serie supera el récord previo? Devuelve el tipo de récord o null.
// otherSets: series ya hechas en la sesión actual, que también cuentan.
export function prType(exId, set, excludeId, otherSets = []) {
  const rec = exerciseRecords(exId, excludeId);
  if (!rec.sets) return null; // primera vez: no cuenta como récord
  let maxKg = rec.maxKg.kg;
  let best = rec.bestE1rm.value;
  for (const x of otherSets) {
    maxKg = Math.max(maxKg, Number(x.kg) || 0);
    best = Math.max(best, e1rm(x));
  }
  const kg = Number(set.kg) || 0;
  if (kg > 0 && kg > maxKg) return 'peso';
  if (e1rm(set) > best + 0.01) return '1RM';
  return null;
}

export function parseRange(target) {
  const nums = String(target || '').match(/\d+/g);
  if (!nums) return null;
  const lo = Number(nums[0]);
  const hi = Number(nums[1] ?? nums[0]);
  return { lo: Math.min(lo, hi), hi: Math.max(lo, hi) };
}

// Sugerencia de doble progresión: si la última vez se llegó al tope del rango
// en todas las series, subir peso; si no, buscar más repeticiones con el mismo peso.
export function progressionHint(exId, target, excludeId) {
  const last = lastPerformance(exId, excludeId);
  if (!last) return null;
  const range = parseRange(target || last.target);
  const top = last.sets.reduce((a, s) => (Number(s.kg) > Number(a.kg) ? s : a), last.sets[0]);
  const kg = Number(top.kg) || 0;
  const working = last.sets.filter((s) => Number(s.kg) === kg);
  const simple = isSimple();
  const u = unitFor(exId);
  const w = (valueKg) => `${fmt(toUnit(valueKg, u))} ${u}`;
  if (!range || !kg) return { type: 'reps', kg, text: 'Intenta hacer 1 repetición más que la vez pasada' };
  const minReps = Math.min(...working.map((s) => Number(s.reps) || 0));
  if (minReps >= range.hi) {
    // Saltos habituales: 2,5 kg (1 kg en mancuernas ligeras) o 5 lb (2,5 lb en pesos ligeros).
    const current = toUnit(kg, u);
    const step = u === 'lb' ? (current < 45 ? 2.5 : 5) : (kg < 20 ? 1 : 2.5);
    const next = fromUnit(current + step, u);
    return { type: 'up', kg: next, text: simple
      ? `¡Lo dominas! Hoy sube a ${w(next)} (ya te lo puse)`
      : `Llegaste a ${range.hi} reps en todas las series: sube a ${w(next)}` };
  }
  if (minReps < range.lo) {
    return { type: 'hold', kg, text: simple
      ? `Repite ${w(kg)} e intenta llegar a ${range.lo} repeticiones en cada serie`
      : `Mantén ${w(kg)} hasta llegar a ${range.lo} reps en todas las series` };
  }
  return { type: 'reps', kg, text: simple
    ? `Usa ${w(kg)} e intenta hacer 1 repetición más que la vez pasada`
    : `Mantén ${w(kg)} y suma reps hasta llegar a ${range.hi}` };
}

const fmt = (n) => Number(n).toLocaleString('es', { maximumFractionDigits: 1 });

export function startDraft(routine, day) {
  state.draft = {
    id: uid(),
    date: todayISO(),
    startedAt: Date.now(),
    routineId: routine?.id || null,
    dayName: day?.name || 'Entrenamiento libre',
    exercises: (day?.exercises || []).map((e) => draftExercise(e.exId, e.sets, e.reps)),
  };
  save();
  return state.draft;
}

export function draftExercise(exId, sets = 3, reps = '') {
  const last = lastPerformance(exId);
  const hint = progressionHint(exId, reps);
  const rows = [];
  for (let i = 0; i < sets; i++) {
    const prev = last?.sets[i] || last?.sets[last.sets.length - 1];
    const kg = hint && hint.type === 'up' ? hint.kg : prev ? prev.kg : '';
    rows.push({ kg, reps: '', effort: '', done: false });
  }
  return { exId, target: reps, note: '', sets: rows };
}

// Abre un entrenamiento terminado para corregirlo.
export function editSession(id) {
  const s = state.sessions.find((x) => x.id === id);
  if (!s) return null;
  state.draft = { ...JSON.parse(JSON.stringify(s)), editing: true };
  save();
  return state.draft;
}

export function finishDraft() {
  const d = state.draft;
  if (!d) return null;
  const editing = d.editing;
  delete d.editing;
  d.exercises = d.exercises
    .map((e) => ({ ...e, sets: e.sets.filter((s) => s.done).map(({ kgTouched, ...rest }) => rest) }))
    .filter((e) => e.sets.length);
  if (editing) d.editedAt = Date.now();
  else d.finishedAt = Date.now();
  state.draft = null;
  state.sessions = state.sessions.filter((s) => s.id !== d.id);
  if (d.exercises.length) state.sessions.push(d);
  else if (editing) tombstone(d.id);
  sortSessions();
  save();
  return d;
}

export function deleteSession(id) {
  state.sessions = state.sessions.filter((s) => s.id !== id);
  tombstone(id);
  save();
}

// Sesión anterior con el mismo nombre de día (para comparar en el resumen).
export function previousSameDay(session) {
  const list = state.sessions.filter((s) => s.dayName === session.dayName && s.id !== session.id && s.date <= session.date);
  return list[list.length - 1] || null;
}

// ---------- Cuerpo ----------

export const BODY_FIELDS = [
  { key: 'weight', label: 'Peso', unit: 'kg', convert: true },
  { key: 'bodyfat', label: '% grasa', unit: '%' },
  { key: 'waist', label: 'Cintura', unit: 'cm' },
  { key: 'chest', label: 'Pecho', unit: 'cm' },
  { key: 'arm', label: 'Brazo', unit: 'cm' },
  { key: 'thigh', label: 'Muslo', unit: 'cm' },
  { key: 'hip', label: 'Cadera', unit: 'cm' },
];

export function upsertBody(entry) {
  const i = state.body.findIndex((b) => b.date === entry.date);
  if (i >= 0) state.body[i] = { ...state.body[i], ...entry };
  else state.body.push(entry);
  state.deletedIds = state.deletedIds.filter((id) => id !== 'body:' + entry.date);
  state.body.sort((a, b) => (a.date < b.date ? -1 : 1));
  save();
}

export function deleteBody(date) {
  state.body = state.body.filter((b) => b.date !== date);
  tombstone('body:' + date);
  save();
}
