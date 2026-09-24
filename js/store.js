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
    draft: null,
  };
}

let state = load();

function load() {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) return { ...emptyState(), ...JSON.parse(raw) };
  } catch (e) {
    console.warn('No se pudieron leer los datos guardados', e);
  }
  return emptyState();
}

export function save() {
  try {
    localStorage.setItem(KEY, JSON.stringify(state));
  } catch (e) {
    alert('No se pudieron guardar los datos en este navegador.');
  }
}

export const getState = () => state;

export function replaceState(next) {
  state = { ...emptyState(), ...next };
  save();
}

export function resetState() {
  state = emptyState();
  save();
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
      const hay = normalize(`${e.name} ${e.muscle} ${e.equipment}`);
      return words.every((w) => hay.includes(w));
    })
    .sort((a, b) => a.name.localeCompare(b.name, 'es'));
}

// ---------- Rutinas ----------

export function routineFromTemplate(tpl) {
  const days = tpl.days.map((d) => ({
    id: uid(),
    name: d.name,
    exercises: d.exercises.map((e) => ({ ...e })),
  }));
  return {
    id: uid(),
    name: tpl.name,
    fromTemplate: tpl.key,
    days,
    week: tpl.week.map((i) => (i === null ? null : days[i].id)),
  };
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
  if (state.activeRoutineId === id) state.activeRoutineId = state.routines[0]?.id || null;
  save();
}

export function seedIfEmpty() {
  if (state.routines.length === 0 && !localStorage.getItem(KEY)) {
    addRoutine(routineFromTemplate(TEMPLATES[0]));
  }
}

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

// Última vez que se hizo un ejercicio (sesión más reciente distinta de la actual).
export function lastPerformance(exId) {
  for (let i = state.sessions.length - 1; i >= 0; i--) {
    const e = state.sessions[i].exercises.find((x) => x.exId === exId);
    if (e && e.sets.some((s) => s.done)) return { date: state.sessions[i].date, sets: e.sets.filter((s) => s.done) };
  }
  return null;
}

export function exerciseHistory(exId) {
  const out = [];
  for (const s of state.sessions) {
    const e = s.exercises.find((x) => x.exId === exId);
    if (!e) continue;
    const sets = e.sets.filter((x) => x.done);
    if (sets.length) out.push({ date: s.date, sets });
  }
  return out.reverse();
}

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
  const rows = [];
  for (let i = 0; i < sets; i++) {
    const prev = last?.sets[i] || last?.sets[last.sets.length - 1];
    rows.push({ kg: prev ? prev.kg : '', reps: '', effort: '', done: false });
  }
  return { exId, target: reps, sets: rows };
}

export function finishDraft() {
  const d = state.draft;
  if (!d) return null;
  d.exercises = d.exercises
    .map((e) => ({ ...e, sets: e.sets.filter((s) => s.done) }))
    .filter((e) => e.sets.length);
  d.finishedAt = Date.now();
  state.draft = null;
  if (d.exercises.length) {
    state.sessions.push(d);
    state.sessions.sort((a, b) => (a.date === b.date ? a.startedAt - b.startedAt : a.date < b.date ? -1 : 1));
  }
  save();
  return d;
}

export function deleteSession(id) {
  state.sessions = state.sessions.filter((s) => s.id !== id);
  save();
}

// ---------- Cuerpo ----------

export const BODY_FIELDS = [
  { key: 'weight', label: 'Peso', unit: 'kg' },
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
  state.body.sort((a, b) => (a.date < b.date ? -1 : 1));
  save();
}

export function deleteBody(date) {
  state.body = state.body.filter((b) => b.date !== date);
  save();
}
