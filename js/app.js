import * as S from './store.js';
import { MUSCLES, FAMILIES } from './data/exercises.js';
import { MUSCLE_NAMES as MUSCLE_NAME } from './data/muscles.js';
import { TEMPLATES } from './data/templates.js';
import { lineChart, sparkArea, destroyCharts } from './charts.js';
import * as Cloud from './cloud.js';
import { mountMuscleMaps, musclesFor, muscleNames } from './body.js';
import { renderShare, renderSticker, composeShare, defaultTransform, autoInk, groupNum, W as ShareW, H as ShareH } from './share.js';

const $view = document.getElementById('view');
const $title = document.getElementById('view-title');
const $sheet = document.getElementById('sheet');
const $toast = document.getElementById('toast');

const ui = {
  tab: 'train', // 'plan' | 'train' | 'progress'
  ob: null, // configuración inicial en curso: { step, level, days, fromSettings }
  editRoutineId: null,
  range: '3m', // periodo de Progreso: '1m' | '3m' | '1a' | 'all'
  exMetricP: 'max', // evolución de ejercicios: 'max' | 'vol'
  exShowAll: false,
  bodyField: 'weight',
  openNotes: new Set(),
  historyLimit: 10,
  exTab: 'about',
  exMetric: 'e1rm',
};

const TITLES = { plan: 'Mi plan', train: 'Entrenar', progress: 'Progreso' };

// ---------- Utilidades ----------

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
// Volumen total en la unidad por defecto, siempre en kg o lb (nunca en toneladas).
const vol = (kgValue) => { const u = S.defaultUnit(); return `${Math.round(S.toUnit(kgValue, u) || 0).toLocaleString('es')} ${u}`; };
// Peso de una serie en la unidad del ejercicio: número solo (wn) o con unidad (wt).
const wn = (kgValue, u) => fmtN(S.toUnit(kgValue, u) || 0);
const wt = (kgValue, u) => `${wn(kgValue, u)} ${u}`;
const unitSwitch = (exId, u) => `<span class="segmented unit-switch" role="group" aria-label="Unidad de peso">
    ${['kg', 'lb'].map((x) => `<button class="${x === u ? 'active' : ''}" data-action="ex-unit" data-id="${exId}" data-u="${x}">${x}</button>`).join('')}</span>`;
const num = (v) => (v === '' || v === null || v === undefined ? '' : Number(v));
const series = (n) => `${n} ${n === 1 ? 'serie' : 'series'}`;
const fmtN = (v, d = 1) => Number(v).toLocaleString('es', { maximumFractionDigits: d });

const ICON_CLOUD = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 18h10.5a4 4 0 0 0 .6-7.96A6 6 0 0 0 6.4 9.1 4.5 4.5 0 0 0 7 18Z"/><path d="m9.5 13.5 2 2 3.5-4"/></svg>';
const ICON_CHECK = '<svg viewBox="0 0 24 24"><path d="M9 16.2 4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2Z"/></svg>';
const ICON_X = '<svg viewBox="0 0 24 24"><path d="M19 6.4 17.6 5 12 10.6 6.4 5 5 6.4 10.6 12 5 17.6 6.4 19 12 13.4 17.6 19 19 17.6 13.4 12 19 6.4Z"/></svg>';
const ICON_UP = '<svg viewBox="0 0 24 24"><path d="m7 14 5-5 5 5H7Z"/></svg>';
const ICON_DOWN = '<svg viewBox="0 0 24 24"><path d="m7 10 5 5 5-5H7Z"/></svg>';
const ICON_MORE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 10a2 2 0 1 0 0 4 2 2 0 0 0 0-4Zm6 0a2 2 0 1 0 0 4 2 2 0 0 0 0-4Zm6 0a2 2 0 1 0 0 4 2 2 0 0 0 0-4Z"/></svg>';
const ICON_CLOCK = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm1 10.4 3.3 3.3-1.4 1.4-3.9-3.9V6h2v6.4Z"/></svg>';
const ICON_BACK = '<svg viewBox="0 0 24 24"><path d="M15.4 7.4 14 6l-6 6 6 6 1.4-1.4L10.8 12l4.6-4.6Z"/></svg>';
const ICON_BARS = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 13h4v7H4v-7Zm6-5h4v12h-4V8Zm6-4h4v16h-4V4Z"/></svg>';
const ICON_SHARE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3 7.5 7.5l1.4 1.4L11 6.8V15h2V6.8l2.1 2.1 1.4-1.4L12 3ZM5 11v9h14v-9h-3v2h1v5H7v-5h1v-2H5Z"/></svg>';
const ICON_SAVE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M11 3h2v9.2l3.1-3.1 1.4 1.4L12 16l-5.5-5.5 1.4-1.4 3.1 3.1V3ZM5 18h14v2H5v-2Z"/></svg>';
const ICON_PHOTO = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h16a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1Zm1 2v8.6l4-4 3.5 3.5 2-2L19 17.6V7H5Zm11 1.5a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3Z"/></svg>';
const ICON_PERSON = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 12a4.5 4.5 0 1 0 0-9 4.5 4.5 0 0 0 0 9Zm0 2c-4.4 0-8 2.2-8 5v2h16v-2c0-2.8-3.6-5-8-5Z"/></svg>';

function toast(msg) {
  $toast.textContent = msg;
  $toast.classList.add('show');
  clearTimeout(toast.t);
  toast.t = setTimeout(() => $toast.classList.remove('show'), 2200);
}

// back: acción del botón "atrás" (para las pantallas del menú de cuenta).
function openSheet(title, body, onMount, back) {
  $sheet.innerHTML = `
    <div class="sheet-inner">
      <div class="sheet-head">${back ? `<button class="icon-btn back-btn" data-action="${back}" aria-label="Atrás">${ICON_BACK}</button>` : ''}<h2 class="grow">${esc(title)}</h2>
        <button class="icon-btn" data-action="close-sheet" aria-label="Cerrar">${ICON_X}</button>
      </div>
      <div class="sheet-body">${body}</div>
    </div>`;
  $sheet.onclick = null;
  $sheet.classList.remove('sheet-top');
  $sheet.style.transform = '';
  if (!$sheet.open) $sheet.showModal();
  onMount?.($sheet);
  mountMuscleMaps($sheet);
}
const closeSheet = () => $sheet.open && $sheet.close();
$sheet.addEventListener('click', (e) => { if (e.target === $sheet) closeSheet(); });

// ---------- Navegación ----------

function setTab(tab) {
  ui.tab = tab;
  ui.editRoutineId = null;
  document.querySelectorAll('.tabbar button').forEach((b) => b.classList.toggle('active', b.dataset.tab === tab));
  render();
  window.scrollTo(0, 0);
}

function render() {
  destroyCharts();
  clearInterval(render.timer);
  if (!ui.ob && S.needsOnboarding()) ui.ob = { step: 'welcome', days: [] };
  document.body.classList.toggle('onboarding', Boolean(ui.ob));
  document.body.classList.toggle('in-session', !ui.ob && ui.tab === 'train' && Boolean(S.getState().draft));
  if (ui.ob) { renderOnboarding(); mountMuscleMaps($view); return; }
  $title.textContent = ui.editRoutineId ? 'Mi rutina' : TITLES[ui.tab];
  ({ plan: renderPlan, train: renderTrain, progress: renderProgress })[ui.tab]();
  mountMuscleMaps($view);
  syncWakeLock();
}

// =====================================================================
// MI PLAN
// =====================================================================

// Músculos en los que se mide el volumen semanal (los pequeños se omiten para no saturar).
const VOLUME_GROUPS = ['chest', 'lats', 'upper_back', 'shoulders', 'biceps', 'triceps', 'quads', 'hamstrings', 'glutes', 'calves', 'abs'];
const VOLUME_MIN = 10;
const VOLUME_MAX = 20;

// Series por músculo: las del plan de la semana y las ya hechas. Un músculo
// secundario cuenta como media serie; en ejercicios por lado, cada par es una serie.
function weeklyVolume(routine, week) {
  const planned = {}, done = {};
  const add = (bag, exId, n) => {
    const [p, sec] = musclesFor(exId);
    p.forEach((g) => { bag[g] = (bag[g] || 0) + n; });
    sec.filter((g) => !p.includes(g)).forEach((g) => { bag[g] = (bag[g] || 0) + n / 2; });
  };
  week.forEach((id) => {
    const day = routine.days.find((d) => d.id === id);
    day?.exercises.forEach((e) => add(planned, e.exId, Number(e.sets) || 0));
  });
  weekSessions().forEach((s) => s.exercises.forEach((e) => add(done, e.exId, e.sets.filter((x) => x.side !== 'R').length)));
  return { planned, done };
}

const dayMinutes = (day) => Math.max(10, Math.round((day.exercises.reduce((a, e) => a + Number(e.sets || 0), 0) * 2.5) / 5) * 5);

function renderPlan() {
  const editing = ui.editRoutineId && S.routineById(ui.editRoutineId);
  if (editing) {
    $view.innerHTML = `<button class="btn ghost" data-action="close-editor" style="padding-left:0">‹ Volver</button>
      ${routineEditorHTML(editing)}`;
    return;
  }
  const routine = S.activeRoutine();
  if (!routine) {
    $view.innerHTML = `<div class="card empty"><p>Aún no tienes un plan de entrenamiento.</p>
      <button class="btn primary" data-action="change-routine">Elegir rutina</button></div>`;
    return;
  }

  const week = S.weekPlan(routine);
  const changed = S.weekChanged(routine);
  const today = S.weekdayIndex();
  const monday = S.startOfWeek(new Date());
  const sessions = weekSessions();
  const days = S.DAY_NAMES.map((name, i) => {
    const date = new Date(monday); date.setDate(monday.getDate() + i);
    const iso = S.todayISO(date);
    const plan = routine.days.find((d) => d.id === week[i]) || null;
    const done = sessions.filter((x) => x.date === iso);
    return {
      i, name, date, plan, done: done[0] || null,
      past: i < today,
      editable: i >= today && !done.length,
      moved: changed && week[i] !== routine.week[i],
    };
  });
  const planned = week.filter(Boolean).length;
  const trained = new Set(sessions.map((x) => x.date)).size;
  const goal = Math.max(planned, trained);
  const pct = goal ? Math.min(100, (trained / goal) * 100) : 0;

  // Tira L–D: toda la semana en una fila (tocar un día libre permite moverlo o entrenar).
  const strip = days.map((d) => {
    const cls = d.done ? 'done' : d.plan ? (d.past ? 'missed' : 'planned') : 'rest';
    const inner = d.done ? ICON_CHECK : d.date.getDate();
    const tag = d.editable ? `button data-action="plan-row" data-wd="${d.i}"` : 'div';
    return `<${tag} class="wk ${cls} ${d.i === today ? 'today' : ''}" aria-label="${d.name}${d.plan ? `: ${esc(shortName(d.plan.name))}` : ': descanso'}${d.done ? ' (hecho)' : ''}">
      <small>${S.DAY_SHORT[d.i]}</small><span>${inner}</span></${d.editable ? 'button' : 'div'}>`;
  }).join('');

  // Próximo entrenamiento: hoy si toca y no está hecho; si no, el siguiente de la semana.
  const next = days.find((d) => d.i >= today && d.plan && !d.done);
  const nextLabel = next ? (next.i === today ? 'hoy' : `${next.name.toLowerCase()} ${next.date.getDate()}`) : '';

  // Días de entreno (los del plan y los entrenados), en cuadrícula.
  const tiles = days.filter((d) => d.plan || d.done).map((d) => {
    const title = d.done ? shortName(d.done.dayName) : shortName(d.plan.name);
    const state = d.done ? `<span class="pt-state ok">${ICON_CHECK} Hecho</span>`
      : d.i === today ? '<span class="pt-state today">Hoy</span>'
      : d.past ? '<span class="pt-state">No hecho</span>'
      : `<span class="pt-state">${d.plan.exercises.length} ejercicios · ~${dayMinutes(d.plan)} min</span>`;
    const tag = d.editable ? `button data-action="plan-row" data-wd="${d.i}"` : 'div';
    return `<${tag} class="pt ${d.done ? 'done' : ''} ${d.past && !d.done ? 'missed' : ''} ${d.i === today ? 'is-today' : ''}">
      <small>${d.name.slice(0, 3)} ${d.date.getDate()}${d.moved ? ' · <em>cambiado</em>' : ''}</small>
      <b>${esc(title)}</b>${state}</${d.editable ? 'button' : 'div'}>`;
  }).join('');

  const { planned: pv, done: dv } = weeklyVolume(routine, week);
  const groups = VOLUME_GROUPS.filter((g) => pv[g] || dv[g]).sort((a, b) => (pv[b] || 0) - (pv[a] || 0));
  const scale = Math.max(24, ...groups.map((g) => Math.max(pv[g] || 0, dv[g] || 0)));
  const pctOf = (v) => `${Math.min(100, (v / scale) * 100).toFixed(1)}%`;
  const volumeRows = groups.map((g) => {
    const p = pv[g] || 0, d = dv[g] || 0;
    const zone = p < VOLUME_MIN ? '<span class="vz low">bajo</span>' : p > VOLUME_MAX ? '<span class="vz high">alto</span>' : '';
    return `<div class="vol-row">
      <span class="vol-name">${g === 'upper_back' ? 'Espalda alta' : MUSCLE_NAME[g]}${zone}</span>
      <span class="vol-bar" aria-hidden="true">
        <span class="vol-band" style="left:${pctOf(VOLUME_MIN)};width:calc(${pctOf(VOLUME_MAX)} - ${pctOf(VOLUME_MIN)})"></span>
        <span class="vol-plan" style="width:${pctOf(p)}"></span>
        <span class="vol-done" style="width:${pctOf(d)}"></span>
      </span>
      <span class="vol-num"><b>${Math.round(d)}</b>/${Math.round(p)}</span>
    </div>`;
  }).join('');

  $view.innerHTML = `
    <div class="card plan-hero">
      <div class="ring" style="--p:${pct}%" role="img" aria-label="${trained} de ${goal} entrenamientos esta semana">
        <div><b>${trained}/${goal}</b><small>esta semana</small></div>
      </div>
      <div class="plan-routine">${esc(routine.name)} · <button class="link" data-action="edit-routine" data-id="${routine.id}">Editar</button></div>
      <div class="week-strip">${strip}</div>
    </div>

    ${next
      ? `<button class="next-card" data-action="plan-go" data-id="${next.plan.id}">
          <span class="grow"><small>Próximo entrenamiento</small><b>${esc(shortName(next.plan.name))} · ${nextLabel}</b></span>
          <span class="next-chev" aria-hidden="true">›</span></button>`
      : `<div class="next-card done"><span class="grow"><small>Esta semana</small><b>${trained >= planned && planned ? '¡Semana completada! 💪' : 'No quedan entrenamientos'}</b></span></div>`}

    <div class="plan-head"><b>Esta semana</b>${changed
      ? '<button class="link small" data-action="plan-reset">Volver al plan original</button>'
      : '<span class="muted small">Toca un día para moverlo</span>'}</div>
    <div class="plan-tiles">${tiles}</div>

    ${groups.length ? `<details class="vol-acc" ${ui.volOpen ? 'open' : ''}>
      <summary><span class="grow">Volumen semanal</span><span class="muted small">series hechas / plan</span><span class="acc-chev" aria-hidden="true">⌄</span></summary>
      <div class="vol-body">
        ${volumeRows}
        <div class="vol-legend muted small"><span class="lg-band"></span> Zona para hipertrofia: ${VOLUME_MIN}–${VOLUME_MAX} series por músculo. Los músculos secundarios cuentan como media serie.</div>
      </div>
    </details>` : ''}
    <button class="btn block ghost" data-action="change-routine">Cambiar de rutina</button>`;
  $view.querySelector('.vol-acc')?.addEventListener('toggle', (e) => { ui.volOpen = e.target.open; });
}

// Hoja para mover un día de esta semana (o entrenar en un día de descanso).
function openPlanDay(wd) {
  const routine = S.activeRoutine();
  const week = [...S.weekPlan(routine)];
  const today = S.weekdayIndex();
  const monday = S.startOfWeek(new Date());
  const doneDates = new Set(weekSessions().map((x) => x.date));
  const free = (j) => {
    const date = new Date(monday); date.setDate(monday.getDate() + j);
    return j >= today && !doneDates.has(S.todayISO(date));
  };
  const dayOf = (id) => routine.days.find((d) => d.id === id);
  const day = dayOf(week[wd]);
  const name = S.DAY_NAMES[wd];

  if (day) {
    const targets = S.DAY_NAMES.map((n, j) => [n, j]).filter(([, j]) => j !== wd && free(j));
    openSheet(`Mover ${shortName(day.name)}`, `
      <p class="muted small" style="margin:0 0 8px">Toca el día en que lo harás esta semana.</p>
      <div class="menu-list">${targets.map(([n, j]) => {
        const other = dayOf(week[j]);
        return `<button class="menu-row" data-action="plan-move" data-from="${wd}" data-to="${j}"><span class="grow">${n}${j === today ? ' (hoy)' : ''}</span>
          <span class="muted small">${other ? `intercambiar con ${esc(shortName(other.name))}` : 'descanso'}</span></button>`;
      }).join('') || '<div class="menu-row muted">No quedan días libres esta semana.</div>'}</div>
      <button class="btn block ghost danger" data-action="plan-skip" data-wd="${wd}">Saltar esta semana</button>`);
    return;
  }
  openSheet(name, `
    <p class="muted small" style="margin:0 0 8px">Hoy toca descanso. ¿Quieres entrenar este día?</p>
    <div class="menu-list">${orderedDays(routine).map((d) => {
      const from = week.findIndex((id, j) => id === d.id && j !== wd && free(j));
      return `<button class="menu-row" data-action="plan-set" data-wd="${wd}" data-id="${d.id}" data-from="${from}"><span class="grow">${esc(shortName(d.name))}</span>
        <span class="muted small">${from >= 0 ? `se mueve desde el ${S.DAY_NAMES[from].toLowerCase()}` : 'extra'}</span></button>`;
    }).join('')}</div>`);
}

// =====================================================================
// ENTRENAR
// =====================================================================

function renderTrain() {
  const st = S.getState();
  if (st.draft) return renderSession();

  const routine = S.activeRoutine();
  const wd = S.weekdayIndex();
  const week = routine ? S.weekPlan(routine) : [];
  const todayDay = routine ? routine.days.find((d) => d.id === week[wd]) : null;

  let html = installCardHTML();
  if (st.profile && !st.profile.gender) {
    html += `<div class="card"><b>¿Eres hombre o mujer?</b>
      <p class="muted small" style="margin:2px 0 10px">Lo usamos para mostrarte el cuerpo correcto en la guía de músculos.</p>
      <div class="grid-2"><button class="btn" data-action="set-gender" data-v="male">Hombre</button><button class="btn" data-action="set-gender" data-v="female">Mujer</button></div></div>`;
  }
  if (!routine) {
    html += `<div class="card empty"><p>Aún no tienes una rutina.</p>
      <button class="btn primary" data-action="change-routine">Elegir rutina</button></div>`;
    html += `<button class="btn block" data-action="start-free">+ Entrenamiento libre</button>`;
    $view.innerHTML = html;
    return;
  }

  // Días en el orden de la semana; el seleccionado por defecto es el de hoy o el próximo.
  const ordered = orderedDays(routine);
  let selected = ordered.find((d) => d.id === ui.planDay);
  if (!selected) {
    for (let k = 0; k < 7 && !selected; k++) selected = routine.days.find((d) => d.id === week[(wd + k) % 7]);
    selected = selected || ordered[0];
  }
  const doneThisWeek = new Set(weekSessions().map((x) => x.dayName));
  const sets = selected.exercises.reduce((a, e) => a + Number(e.sets || 0), 0);
  const minutes = Math.max(10, Math.round((sets * 2.5) / 5) * 5);

  html += `<p class="muted small" style="margin:0 4px 8px">${S.DAY_NAMES[wd]} · ${todayDay ? `hoy toca <b>${esc(shortName(todayDay.name))}</b>` : 'hoy toca descanso'}</p>
    <div class="chips plan-chips" role="tablist">${ordered.map((d) => `<button class="chip ${d.id === selected.id ? 'active' : ''}" role="tab" aria-selected="${d.id === selected.id}" data-action="plan-day" data-id="${d.id}">
      ${esc(shortName(d.name))}${doneThisWeek.has(d.name) ? ' <span class="ok">✓</span>' : ''}</button>`).join('')}</div>
    <div class="plan-head"><b>Ejercicios · ${selected.exercises.length}</b>${selected.exercises.length ? `<span class="muted small">~ ${minutes} min</span>` : ''}</div>`;
  html += selected.exercises.length
    ? `<div class="plan-list">${selected.exercises.map((e) => {
        const ex = S.exById(e.exId);
        const last = S.lastPerformance(e.exId);
        const top = last ? last.sets.reduce((a, x) => (Number(x.kg) > Number(a.kg) ? x : a), last.sets[0]) : null;
        return `<button class="plan-item" data-action="ex-detail" data-id="${e.exId}">
          <span class="thumb" data-muscle-map="${e.exId}" data-thumb></span>
          <span class="grow"><span class="name">${esc(ex.name)}</span>
          <span class="meta">${series(Number(e.sets))}${S.unilateralFor(e.exId) ? ' por lado' : ''}${e.reps ? ` · ${esc(e.reps)} reps` : ''}${top && Number(top.kg) ? ` · ${wt(top.kg, S.unitFor(e.exId))}` : ''}</span></span></button>`;
      }).join('')}</div>`
    : `<div class="card empty small">Este día no tiene ejercicios todavía. Tócalo en la pestaña <b>Mi plan → Editar</b> para añadirlos.</div>`;
  if (selected.exercises.length) {
    html += `<div class="cta-bar"><button class="btn primary block cta" data-action="start" data-day="${selected.id}">Empezar ${esc(shortName(selected.name))}</button></div>`;
  }
  html += `<button class="btn block" data-action="start-free" style="margin-top:16px">+ Entrenamiento libre</button>`;
  $view.innerHTML = html;
}

// Días de la rutina en el orden en que aparecen en la semana (los no asignados, al final).
function orderedDays(routine) {
  const seen = new Set();
  const out = [];
  S.weekPlan(routine).forEach((id) => { if (id && !seen.has(id)) { seen.add(id); out.push(routine.days.find((d) => d.id === id)); } });
  routine.days.forEach((d) => { if (!seen.has(d.id)) out.push(d); });
  return out.filter(Boolean);
}

function weekSessions() {
  const monday = S.todayISO(S.startOfWeek(new Date()));
  return S.getState().sessions.filter((x) => x.date >= monday);
}

// Nombre corto para la tira de la semana: "Torso A (Pecho / Espalda)" → "Torso A".
const shortName = (name) => name.replace(/\s*\(.*\)\s*/g, ' ').trim();

// Sesión en modo enfoque: un ejercicio por pantalla, carrusel arriba y botón inferior
// que guía el siguiente paso (marcar series → siguiente ejercicio → terminar).
const exDone = (x) => x.sets.length > 0 && x.sets.every((y) => y.done);

function renderSession() {
  const d = S.getState().draft;
  const effort = S.isSimple() ? null : S.getState().settings.effort;
  const n = d.exercises.length;
  d.current = Math.max(0, Math.min(Number(d.current) || 0, n - 1));
  const i = d.current;
  const e = d.exercises[i];

  let cta = '';
  if (e && e.sets.some((x) => !x.done)) {
    const left = e.sets.filter((x) => !x.done).length;
    cta = `<button class="btn primary block session-btn" data-action="log-all">${left === e.sets.length ? 'Marcar todas las series' : `Marcar ${left === 1 ? 'la serie que falta' : `las ${left} series que faltan`}`}</button>`;
  } else {
    const next = [...d.exercises.keys()].map((k) => (i + 1 + k) % n).find((k) => k !== i && !exDone(d.exercises[k]));
    cta = next !== undefined
      ? `<button class="btn primary block session-btn" data-action="go-ex" data-i="${next}">Siguiente: ${esc(S.exById(d.exercises[next].exId).name)} →</button>`
      : `<button class="btn primary block session-btn finish-btn" data-action="finish">${d.editing ? 'Guardar cambios' : 'Terminar entrenamiento'}</button>`;
  }

  $view.innerHTML = `
    <div class="session-bar">
      ${d.editing
        ? `<input type="date" class="pill pill-input" value="${d.date}" max="${S.todayISO()}" data-draft="date" aria-label="Fecha del entrenamiento">`
        : `<span class="pill timer-pill">${ICON_CLOCK}<span id="elapsed">0:00</span></span>`}
      <span class="grow"></span>
      <button class="icon-btn" data-action="session-menu" aria-label="Más opciones">${ICON_MORE}</button>
      <button class="btn sm primary pill-btn" data-action="finish">${d.editing ? 'Guardar' : 'Terminar'}</button>
    </div>
    <div class="rail" id="rail" role="tablist" aria-label="Ejercicios">
      ${d.exercises.map((x, k) => `<button class="rail-item ${k === i ? 'active' : ''} ${exDone(x) ? 'done' : ''}" role="tab" aria-selected="${k === i}" data-action="go-ex" data-i="${k}" aria-label="${esc(S.exById(x.exId).name)}${exDone(x) ? ' (hecho)' : ''}">
        <span data-muscle-map="${x.exId}" data-thumb="tall"></span>${exDone(x) ? '<span class="rail-check" aria-hidden="true">✓</span>' : ''}</button>`).join('')}
      <button class="rail-item rail-add" data-action="session-add-ex" aria-label="Añadir ejercicio">+</button>
    </div>
    ${e ? exerciseStage(e, i, effort, d) : `<div class="empty">Este entrenamiento no tiene ejercicios.<br><br><button class="btn primary" data-action="session-add-ex">+ Añadir ejercicio</button></div>`}
    ${e ? `<div class="session-cta">${restBarHTML(d)}${cta}</div>` : ''}`;

  const rail = document.getElementById('rail');
  const active = rail.querySelector('.active');
  if (active) rail.scrollLeft = active.offsetLeft - (rail.clientWidth - active.clientWidth) / 2;

  // Deslizar a los lados para cambiar de ejercicio.
  const stage = document.getElementById('stage');
  if (stage) {
    let x0 = 0, y0 = 0;
    stage.addEventListener('touchstart', (ev) => { x0 = ev.touches[0].clientX; y0 = ev.touches[0].clientY; }, { passive: true });
    stage.addEventListener('touchend', (ev) => {
      const dx = ev.changedTouches[0].clientX - x0;
      const dy = ev.changedTouches[0].clientY - y0;
      if (Math.abs(dx) < 60 || Math.abs(dx) < Math.abs(dy) * 1.5) return;
      const k = i + (dx < 0 ? 1 : -1);
      if (k >= 0 && k < n) goToExercise(k);
    });
  }

  const tick = () => {
    const el = document.getElementById('elapsed');
    if (!el) return;
    const sec = Math.max(0, Math.floor((Date.now() - d.startedAt) / 1000));
    const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60), ss = String(sec % 60).padStart(2, '0');
    el.textContent = h ? `${h}:${String(m).padStart(2, '0')}:${ss}` : `${m}:${ss}`;
    restTick(d);
  };
  tick();
  if (!d.editing) render.timer = setInterval(tick, 1000);
}

// ---------- Descanso entre series ----------

const mmss = (sec) => `${Math.floor(sec / 60)}:${String(sec % 60).padStart(2, '0')}`;

function restBarHTML(d) {
  if (!d.rest || d.editing) return '';
  const left = Math.max(0, Math.ceil((d.rest.end - Date.now()) / 1000));
  const pct = Math.min(100, (left / d.rest.total) * 100);
  return `<div class="rest-bar" id="rest-bar" role="timer" aria-label="Descanso">
    <span class="rest-fill" id="rest-fill" style="width:${pct}%"></span>
    <button class="rest-adj" data-action="rest-adj" data-s="-15" aria-label="Quitar 15 segundos">−15</button>
    <span class="rest-time"><small>Descanso</small><b id="rest-left">${mmss(left)}</b></span>
    <button class="rest-adj" data-action="rest-adj" data-s="15" aria-label="Añadir 15 segundos">+15</button>
    <button class="rest-skip" data-action="rest-skip">Saltar</button>
  </div>`;
}

function restTick(d) {
  if (!d.rest) return;
  const left = Math.max(0, Math.ceil((d.rest.end - Date.now()) / 1000));
  const el = document.getElementById('rest-left');
  if (el) el.textContent = mmss(left);
  const fill = document.getElementById('rest-fill');
  if (fill) fill.style.width = `${Math.min(100, (left / d.rest.total) * 100)}%`;
  if (left > 0) return;
  const late = Date.now() - d.rest.end > 5000; // la app estaba cerrada: sin alarma tardía
  d.rest = null;
  S.save();
  document.getElementById('rest-bar')?.remove();
  if (late) return;
  beep();
  if (navigator.vibrate) navigator.vibrate([200, 100, 200]);
  toast('⏱ ¡Descanso terminado! A por la siguiente serie');
}

function startRest(e) {
  const d = S.getState().draft;
  if (!S.restEnabled() || d.editing || d.exercises.every(exDone)) return;
  const total = S.restFor(e.exId, e.target);
  d.rest = { end: Date.now() + total * 1000, total, exId: e.exId };
  unlockAudio();
}

// Sonido corto al terminar el descanso (el audio se habilita al tocar una serie).
let audioCtx = null;
function unlockAudio() {
  try {
    audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
    if (audioCtx.state === 'suspended') audioCtx.resume();
  } catch { audioCtx = null; }
}
function beep() {
  if (!audioCtx) return;
  try {
    [0, 0.22, 0.44].forEach((t, k) => {
      const o = audioCtx.createOscillator(), g = audioCtx.createGain();
      o.frequency.value = k === 2 ? 1320 : 880;
      g.gain.setValueAtTime(0.0001, audioCtx.currentTime + t);
      g.gain.exponentialRampToValueAtTime(0.35, audioCtx.currentTime + t + 0.02);
      g.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + t + 0.18);
      o.connect(g).connect(audioCtx.destination);
      o.start(audioCtx.currentTime + t); o.stop(audioCtx.currentTime + t + 0.2);
    });
  } catch {}
}

// Pantalla encendida mientras entrenas (se suelta al terminar o salir).
let wakeLock = null;
async function syncWakeLock() {
  const want = document.body.classList.contains('in-session') && document.visibilityState === 'visible';
  try {
    if (want && !wakeLock && 'wakeLock' in navigator) {
      wakeLock = await navigator.wakeLock.request('screen');
      wakeLock.addEventListener('release', () => { wakeLock = null; });
    } else if (!want && wakeLock) {
      await wakeLock.release();
      wakeLock = null;
    }
  } catch { wakeLock = null; }
}
document.addEventListener('visibilitychange', () => {
  syncWakeLock();
  if (document.visibilityState === 'visible' && S.getState().draft?.rest) restTick(S.getState().draft);
});

function goToExercise(k) {
  S.getState().draft.current = k;
  S.save();
  render();
  window.scrollTo(0, 0);
}

function updateLiveStats() {}

// Valores sugeridos de una serie: los de la última vez o el mínimo del objetivo.
// "Última vez" compacto: agrupa series seguidas con el mismo peso → "80 kg × 6 · 6 · 5".
function lastSummary(sets, u) {
  const groups = [];
  for (const x of sets) {
    const kgText = wn(x.kg, u);
    const g = groups[groups.length - 1];
    if (g && g.kg === kgText) g.reps.push(`${sideTag(x)}${x.reps}`);
    else groups.push({ kg: kgText, reps: [`${sideTag(x)}${x.reps}`] });
  }
  return groups.map((g) => `<b>${g.kg} ${u}</b> × ${g.reps.join(' · ')}`).join('<span class="muted"> | </span>');
}

// Texto corto de una serie: "I 20×10" en ejercicios por lado.
const sideTag = (x) => (x.side ? `${x.side === 'L' ? 'I' : 'D'} ` : '');

function setSuggestion(e, j, last) {
  const side = e.sets[j]?.side || null;
  let p = last?.sets[j];
  if (last && (p?.side || null) !== side) {
    // La última vez se registró de otra forma: busca la serie equivalente del mismo lado.
    const k = e.sets.slice(0, j).filter((x) => (x.side || null) === side).length;
    const same = last.sets.filter((x) => (x.side || null) === side);
    p = same[k] || last.sets[side ? Math.floor(j / 2) : j] || last.sets[last.sets.length - 1];
  }
  return { kg: p ? p.kg : '', reps: p?.reps || (e.target ? Number(String(e.target).split('-')[0]) || '' : '') };
}

function exerciseStage(e, i, effort, d) {
  const ex = S.exById(e.exId);
  const excludeId = d.editing ? d.id : null;
  const last = S.lastPerformance(e.exId, excludeId);
  const noteOpen = e.note || ui.openNotes.has(i);
  const u = S.unitFor(e.exId);
  const nextSet = e.sets.findIndex((x) => !x.done);
  const perSide = e.sets.some((x) => x.side);
  const total = perSide ? Math.ceil(e.sets.length / 2) : e.sets.length;
  const pos = nextSet === -1 ? '' : perSide
    ? `Serie ${Math.floor(nextSet / 2) + 1} de ${total} · lado ${e.sets[nextSet].side === 'L' ? 'izquierdo' : 'derecho'}`
    : `Serie ${nextSet + 1} de ${total}`;
  return `<div class="stage" id="stage">
    <div class="muted small">${esc(shortName(d.dayName))} · Ejercicio ${i + 1} de ${d.exercises.length}</div>
    <div class="stage-head">
      <button class="link-btn grow" data-action="ex-detail" data-id="${e.exId}"><h2>${esc(ex.name)}</h2></button>
      <button class="icon-btn" data-action="ex-menu" data-i="${i}" aria-label="Opciones del ejercicio">${ICON_MORE}</button>
    </div>
    <div class="stage-sub">${nextSet === -1 ? '✓ Ejercicio completado' : pos}${e.target ? ` · objetivo ${esc(e.target)} reps` : ''}</div>
    ${last ? `<div class="last-line"><span class="last-label">Última vez</span> ${lastSummary(last.sets, u)}</div>` : ''}
    ${e.upFrom && e.sets.some((x) => !x.done) && Number(e.sets[0].kg) > e.upFrom ? `<div class="up-line">↑ +${wn(Number(e.sets[0].kg) - e.upFrom, u)} ${u} <span>· la última vez completaste todas las reps</span></div>` : ''}
    ${last?.note ? `<div class="last-line">📝 ${esc(last.note)}</div>` : ''}
    ${!last && !d.editing && S.isSimple() ? `<div class="hint">👋 Primera vez: elige un peso con el que puedas hacer ${esc(S.parseRange(e.target)?.hi || 10)} repeticiones con buena técnica, sin llegar al límite.</div>` : ''}
    <div class="toggles">
      <button class="toggle-chip ${e.warmupOn ? 'on' : ''}" data-action="warm-toggle" data-i="${i}" role="switch" aria-checked="${Boolean(e.warmupOn)}" title="Series de calentamiento con menos peso; no cuentan en tus estadísticas">
        <span class="chip-mark" aria-hidden="true">${e.warmupOn ? '✓' : '+'}</span>Aproximación</button>
      ${S.canUnilateral(e.exId) ? `<button class="toggle-chip ${perSide ? 'on' : ''}" data-action="uni-toggle" data-i="${i}" role="switch" aria-checked="${perSide}" title="Registra cada serie para la izquierda (I) y la derecha (D)">
        <span class="chip-mark" aria-hidden="true">${perSide ? '✓' : '+'}</span>Por lado</button>` : ''}
      <button class="toggle-chip ${e.note ? 'on' : ''}" data-action="note-open" data-i="${i}" aria-expanded="${Boolean(noteOpen)}" aria-label="${e.note ? 'Nota del ejercicio' : 'Añadir nota'}">
        <span class="chip-mark" aria-hidden="true">${e.note ? '✓' : '+'}</span>Nota</button>
    </div>
    ${noteOpen ? `<textarea class="note" rows="2" maxlength="300" placeholder="Nota: agarre, sensaciones, molestias…" data-note="${i}" aria-label="Nota del ejercicio">${esc(e.note || '')}</textarea>` : ''}
    <div class="set-grid ${effort ? 'with-effort' : ''}">
      <div class="set-labels"><span>Serie</span><span>Reps</span><span class="unit-label">Peso ${unitSwitch(e.exId, u)}</span>${effort ? `<span>${effort}</span>` : ''}<span></span></div>
      ${e.warmupOn ? (e.warmup || []).map((w, j) => `<div class="set-row warm ${w.done ? 'done' : ''}">
          ${S.isSimple() ? '<span class="set-n" title="Serie de aproximación">A</span>'
            : `<button class="set-n" data-action="set-menu" data-kind="warm" data-i="${i}" data-j="${j}" aria-label="Opciones de la aproximación ${j + 1}">A</button>`}
          <input class="pill-input" type="number" inputmode="numeric" min="0" value="${esc(w.reps)}" placeholder="–" data-warm="reps" data-i="${i}" data-j="${j}" aria-label="Repeticiones aproximación ${j + 1}">
          <input class="pill-input" type="number" inputmode="decimal" step="0.5" min="0" value="${esc(S.toUnit(w.kg, u))}" placeholder="–" data-warm="kg" data-i="${i}" data-j="${j}" aria-label="Peso en ${u} aproximación ${j + 1}">
          ${effort ? '<span></span>' : ''}
          <button class="set-check" data-action="toggle-warm" data-i="${i}" data-j="${j}" aria-pressed="${w.done}" aria-label="Marcar aproximación ${j + 1} como hecha">${ICON_CHECK}</button>
        </div>`).join('') + `<div class="warm-actions"><button class="link" data-action="warm-add" data-i="${i}">+ Aproximación</button>${(e.warmup || []).length ? `<button class="link" data-action="warm-remove" data-i="${i}">Quitar</button>` : ''}</div>` : ''}
      ${e.sets.map((x, j) => {
        const sug = setSuggestion(e, j, last);
        const label = x.side ? `${Math.floor(j / 2) + 1}<small>${x.side === 'L' ? 'I' : 'D'}</small>` : j + 1;
        return `<div class="set-row ${x.done ? 'done' : ''} ${j === nextSet ? 'next' : ''} ${x.side === 'R' ? 'side-end' : ''}">
          ${S.isSimple()
            ? `<span class="set-n">${x.pr ? '<span title="Récord personal">🏆</span>' : label}</span>`
            : `<button class="set-n" data-action="set-menu" data-kind="set" data-i="${i}" data-j="${j}" aria-label="Opciones de la serie ${x.side ? `${Math.floor(j / 2) + 1} ${x.side === 'L' ? 'izquierda' : 'derecha'}` : j + 1}">${x.pr ? '🏆' : label}</button>`}
          <input class="pill-input" type="number" inputmode="numeric" min="0" value="${esc(x.reps)}" placeholder="${esc(sug.reps)}" data-set="reps" data-i="${i}" data-j="${j}" aria-label="Repeticiones serie ${x.side ? `${Math.floor(j / 2) + 1} ${x.side === 'L' ? 'izquierda' : 'derecha'}` : j + 1}">
          <input class="pill-input" type="number" inputmode="decimal" step="0.5" min="0" value="${esc(S.toUnit(x.kg, u))}" placeholder="${sug.kg !== '' ? esc(S.toUnit(sug.kg, u)) : '–'}" data-set="kg" data-i="${i}" data-j="${j}" aria-label="Peso en ${u} serie ${j + 1}">
          ${effort ? `<input class="pill-input small-input" type="number" inputmode="decimal" step="0.5" min="0" max="10" value="${esc(x.effort)}" placeholder="–" data-set="effort" data-i="${i}" data-j="${j}" aria-label="${effort} serie ${j + 1}">` : ''}
          <button class="set-check" data-action="toggle-set" data-i="${i}" data-j="${j}" aria-pressed="${x.done}" aria-label="Marcar serie ${j + 1} como hecha">${ICON_CHECK}</button>
        </div>`;
      }).join('')}
    </div>
    <div class="set-actions">
      <span class="stepper-label"><span class="step-count" aria-live="polite">${total}</span> ${total === 1 ? 'serie' : 'series'}</span>
      <div class="stepper" role="group" aria-label="Número de series">
        <button class="step-btn" data-action="remove-set" data-i="${i}" aria-label="Quitar una serie" ${e.sets.length > (perSide ? 2 : 1) ? '' : 'disabled'}>−</button>
        <button class="step-btn" data-action="add-set" data-i="${i}" aria-label="Añadir una serie">+</button>
      </div>
    </div>
  </div>`;
}

// Marca una serie como hecha (rellenando lo que falte con lo sugerido). Devuelve false si faltan reps.
function markSet(i, j) {
  const d = S.getState().draft;
  const e = d.exercises[i];
  const s = e.sets[j];
  const u = S.unitFor(e.exId);
  const sug = setSuggestion(e, j, S.lastPerformance(e.exId, d.editing ? d.id : null));
  if (s.kg === '' && sug.kg !== '') s.kg = sug.kg;
  if (s.kg === '') s.kg = 0;
  if (s.reps === '' && sug.reps !== '') s.reps = sug.reps;
  if (s.reps === '' || s.reps === 0) return false;
  s.done = true;
  delete s.pr;
  const pr = S.prType(e.exId, s, d.editing ? d.id : null, e.sets.filter((x) => x !== s && x.done));
  if (pr) {
    s.pr = pr;
    toast(pr === 'peso' ? `🏆 ¡Récord de peso! ${wt(s.kg, u)}`
      : S.isSimple() ? '🏆 ¡Tu mejor serie hasta ahora en este ejercicio!' : `🏆 ¡Récord personal! 1RM estimado ${wt(S.e1rm(s), u)}`);
    if (navigator.vibrate) navigator.vibrate([60, 40, 60]);
  }
  // Las series siguientes heredan este peso, salvo las que el usuario cambió a mano.
  e.sets.forEach((x, k) => { if (k > j && !x.done && !x.kgTouched) x.kg = s.kg; });
  return true;
}

function afterMarking(anyPr) {
  const d = S.getState().draft;
  if (d.rest && d.exercises.every(exDone)) d.rest = null; // última serie: sin descanso
  S.save();
  const y = window.scrollY;
  render();
  window.scrollTo(0, y);
  if (!d.editing && d.exercises.every(exDone)) {
    setTimeout(() => toast('¡Completaste todas las series! 💪'), anyPr ? 2300 : 0);
  }
}

// ---------- Compartir el entrenamiento (plantillas tipo historia) ----------

const isIOS = () => /iphone|ipad|ipod/i.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);

const ICON_AL = {
  left: '<svg viewBox="0 0 24 24"><path d="M4 5h16v2H4V5Zm0 4h10v2H4V9Zm0 4h16v2H4v-2Zm0 4h10v2H4v-2Z"/></svg>',
  center: '<svg viewBox="0 0 24 24"><path d="M4 5h16v2H4V5Zm3 4h10v2H7V9Zm-3 4h16v2H4v-2Zm3 4h10v2H7v-2Z"/></svg>',
  right: '<svg viewBox="0 0 24 24"><path d="M4 5h16v2H4V5Zm6 4h10v2H10V9Zm-6 4h16v2H4v-2Zm6 4h10v2H10v-2Z"/></svg>',
};
const NEXT_ALIGN = { left: 'center', center: 'right', right: 'left' };

// Compartir: el bloque de datos es un "sticker" sobre la vista previa. Se arrastra con
// un dedo, con dos se pellizca (tamaño) y se gira, y un toque cambia la alineación.
// El botón «Color» alterna texto blanco/negro; con tu foto se elige solo hasta que lo toques.
function openShare(session) {
  const st = S.getState().settings;
  const saved = st.shareLayout || {};
  const state = { align: saved.align || 'left', color: saved.color || 'white', t: saved.t || null, photo: null, sticker: null, autoColor: false };

  openSheet('Compartir', `
    <div class="share-stage">
      <div class="share-frame checker${state.color === 'black' ? ' light' : ''}">
        <img class="sf-photo" alt="" hidden>
        <img class="sf-sticker" alt="Datos del entrenamiento" draggable="false">
        <span class="sf-guide" aria-hidden="true"></span>
        <span class="sf-align" aria-hidden="true">${ICON_AL[state.align]}</span>
        <span class="share-spin" aria-hidden="true"></span>
      </div>
    </div>
    <p class="share-hint muted small">Toca para alinear · arrastra, pellizca o gira</p>
    <div class="share-acts">
      <button type="button" data-act="share"><span class="ic p">${ICON_SHARE}</span>Compartir</button>
      <button type="button" data-act="save"><span class="ic">${ICON_SAVE}</span>Guardar</button>
      <label><span class="ic">${ICON_PHOTO}</span>Usar mi foto<input type="file" accept="image/*" hidden></label>
      <button type="button" data-act="color" aria-label="Color del texto"><span class="ic"><i class="ink-dot ${state.color}"></i></span>Color</button>
    </div>`, (root) => {
    const frame = root.querySelector('.share-frame');
    const stickerImg = root.querySelector('.sf-sticker');
    const photoImg = root.querySelector('.sf-photo');
    const guide = root.querySelector('.sf-guide');
    const alignBtn = root.querySelector('.sf-align');
    const ratio = () => frame.clientWidth / ShareW;

    const place = () => {
      if (!state.sticker) return;
      const r = ratio(), t = state.t;
      const w = state.sticker.width * t.s * r, h = state.sticker.height * t.s * r;
      stickerImg.style.width = `${w}px`;
      stickerImg.style.left = `${t.cx * r - w / 2}px`;
      stickerImg.style.top = `${t.cy * r - h / 2}px`;
      stickerImg.style.transform = t.r ? `rotate(${t.r}rad)` : '';
    };
    const save = () => { st.shareLayout = { align: state.align, color: state.color, t: { ...state.t } }; S.save(); };
    const colorDot = root.querySelector('.ink-dot');

    const load = async (keepHeight) => {
      frame.classList.add('loading');
      try {
        state.sticker = await renderSticker(session, state.align, state.color);
        if (!state.t) state.t = defaultTransform(state.sticker, state.align);
        else if (keepHeight) {
          // Nueva alineación: misma altura y tamaño; el lado se ajusta a la alineación.
          const w = state.sticker.width * state.t.s;
          state.t = { ...state.t, cx: state.align === 'center' ? ShareW / 2 : state.align === 'right' ? ShareW - 60 - w / 2 : 60 + w / 2 };
        }
        stickerImg.src = state.sticker.toDataURL('image/png');
        place();
      } catch {
        toast('No se pudo crear la imagen');
      } finally {
        frame.classList.remove('loading');
      }
    };

    const setColor = async (color) => {
      if (color === state.color) return;
      state.color = color;
      colorDot.className = `ink-dot ${color}`;
      frame.classList.toggle('light', color === 'black');
      await load(false);
      save();
    };
    // Con foto: color automático según lo clara u oscura que sea la zona detrás del bloque.
    const autoColor = () => { if (state.photo && state.autoColor && state.sticker) setColor(autoInk(state.photo, state.sticker, state.t)); };
    root.querySelector('[data-act="color"]').addEventListener('click', () => {
      state.autoColor = false;
      setColor(state.color === 'white' ? 'black' : 'white');
    });

    // Un toque cambia la alineación (izquierda → centro → derecha) y la muestra un momento.
    const cycleAlign = async () => {
      state.align = NEXT_ALIGN[state.align];
      alignBtn.innerHTML = ICON_AL[state.align];
      alignBtn.classList.remove('on'); void alignBtn.offsetWidth; alignBtn.classList.add('on');
      await load(true);
      save();
    };

    // Gestos: un dedo mueve; dos dedos pellizcan (tamaño) y giran. Un toque corto: alineación.
    const pts = new Map();
    let start = null;
    let tap = null;
    const snapshot = () => {
      const [a, b] = [...pts.values()];
      start = {
        t: { ...state.t }, a: { ...a },
        dist: b ? Math.hypot(b.x - a.x, b.y - a.y) : 0,
        ang: b ? Math.atan2(b.y - a.y, b.x - a.x) : 0,
        mid: b ? { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 } : { ...a },
      };
    };
    frame.addEventListener('pointerdown', (e) => {
      if (!state.sticker) return;
      try { frame.setPointerCapture(e.pointerId); } catch { /* puntero ya liberado */ }
      pts.set(e.pointerId, { x: e.clientX, y: e.clientY });
      tap = pts.size === 1 ? { x: e.clientX, y: e.clientY, time: Date.now() } : null;
      snapshot();
    });
    frame.addEventListener('pointermove', (e) => {
      if (!pts.has(e.pointerId) || !start) return;
      pts.set(e.pointerId, { x: e.clientX, y: e.clientY });
      const r = ratio();
      const [a, b] = [...pts.values()];
      const t = { ...start.t };
      if (b && start.dist) {
        const dist = Math.hypot(b.x - a.x, b.y - a.y);
        t.s = Math.min(1.5, Math.max(0.35, start.t.s * (dist / start.dist)));
        // Giro con imán a la posición recta (±6°).
        let rot = (start.t.r || 0) + Math.atan2(b.y - a.y, b.x - a.x) - start.ang;
        rot = Math.atan2(Math.sin(rot), Math.cos(rot));
        t.r = Math.abs(rot) < 0.105 ? 0 : rot;
        const mid = { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
        t.cx += (mid.x - start.mid.x) / r; t.cy += (mid.y - start.mid.y) / r;
      } else {
        t.cx += (a.x - start.a.x) / r; t.cy += (a.y - start.a.y) / r;
      }
      // Imán al centro con guía, como en Instagram.
      const snap = Math.abs(t.cx - ShareW / 2) < 24;
      if (snap) t.cx = ShareW / 2;
      guide.classList.toggle('on', snap);
      const hw = (state.sticker.width * t.s) / 2, hh = (state.sticker.height * t.s) / 2;
      t.cx = Math.min(ShareW - hw * 0.3, Math.max(hw * 0.3, t.cx));
      t.cy = Math.min(ShareH - hh * 0.3, Math.max(hh * 0.3, t.cy));
      state.t = t;
      place();
    });
    const end = (e) => {
      if (!pts.has(e.pointerId)) return;
      pts.delete(e.pointerId);
      guide.classList.remove('on');
      if (pts.size) { tap = null; snapshot(); return; }
      start = null;
      const moved = tap && Math.hypot(e.clientX - tap.x, e.clientY - tap.y);
      if (e.type === 'pointerup' && tap && moved < 8 && Date.now() - tap.time < 350) {
        tap = null;
        cycleAlign();
        return;
      }
      tap = null;
      save();
      autoColor();
    };
    frame.addEventListener('pointerup', end);
    frame.addEventListener('pointercancel', end);
    frame.addEventListener('wheel', (e) => {
      if (!state.sticker) return;
      e.preventDefault();
      state.t = { ...state.t, s: Math.min(1.5, Math.max(0.35, state.t.s * (e.deltaY < 0 ? 1.05 : 0.95))) };
      place(); save();
    }, { passive: false });
    window.addEventListener('resize', place);

    root.querySelector('input[type=file]').addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      try {
        state.photo = await createImageBitmap(file);
      } catch {
        state.photo = await new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = rej; im.src = URL.createObjectURL(file); });
      }
      photoImg.src = URL.createObjectURL(file);
      photoImg.hidden = false;
      frame.classList.remove('checker');
      state.autoColor = true;
      autoColor();
    });

    const toFile = async () => {
      const c = composeShare({ sticker: state.sticker, photo: state.photo, t: state.t });
      const blob = await new Promise((r) => c.toBlob(r, 'image/png'));
      return new File([blob], `entrenamiento-${session.date}.png`, { type: 'image/png' });
    };
    const download = (file) => {
      const a = document.createElement('a');
      a.href = URL.createObjectURL(file);
      a.download = file.name;
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 1000);
      toast('Imagen guardada');
    };
    const share = async (file) => {
      try {
        if (navigator.canShare?.({ files: [file] })) { await navigator.share({ files: [file] }); return true; }
      } catch (err) {
        if (err?.name === 'AbortError') return true;
      }
      return false;
    };
    root.querySelector('[data-act="share"]').addEventListener('click', async () => {
      if (!state.sticker) return;
      const file = await toFile();
      if (!(await share(file))) download(file);
    });
    // En el iPhone, "Guardar imagen" está en el menú de compartir (guarda en Fotos, con transparencia).
    root.querySelector('[data-act="save"]').addEventListener('click', async () => {
      if (!state.sticker) return;
      const file = await toFile();
      if (isIOS() && (await share(file))) return;
      download(file);
    });
    load(false);
  });
}

// =====================================================================
// RUTINAS
// =====================================================================

// embedded: dentro de la configuración inicial (sin botones de gestión).
function routineEditorHTML(r, { embedded = false } = {}) {
  return `
    <div class="card">
      <label class="field"><span>Nombre de la rutina</span>
        <input type="text" value="${esc(r.name)}" data-rfield="name" maxlength="60"></label>
    </div>

    <div class="section-title">Semana</div>
    <div class="card stack">
      ${S.DAY_NAMES.map((name, i) => `<div class="row">
        <div style="width:92px" class="small"><b>${name}</b></div>
        <select class="grow" data-rweek="${i}" aria-label="Entrenamiento del ${name}">
          <option value="">Descanso</option>
          ${r.days.map((d) => `<option value="${d.id}" ${r.week[i] === d.id ? 'selected' : ''}>${esc(d.name)}</option>`).join('')}
        </select></div>`).join('')}
    </div>

    <div class="section-title">Días de entrenamiento</div>
    ${r.days.map((d, di) => `<div class="card">
      <div class="row" style="margin-bottom:8px">
        <input type="text" class="grow" value="${esc(d.name)}" data-dfield="name" data-di="${di}" aria-label="Nombre del día" maxlength="40">
        <button class="icon-btn" data-action="day-remove" data-di="${di}" aria-label="Eliminar día">${ICON_X}</button>
      </div>
      ${d.exercises.length ? `<div class="list">${d.exercises.map((e, ei) => `
        <div class="list-item" style="flex-wrap:wrap">
          <div class="grow" style="min-width:140px"><b class="small">${esc(S.exById(e.exId).name)}</b>
            <div class="muted small">${esc(S.exById(e.exId).muscle)}</div></div>
          <div class="row" style="gap:4px">
            <input type="number" inputmode="numeric" min="1" max="20" value="${e.sets}" data-efield="sets" data-di="${di}" data-ei="${ei}" style="width:52px;text-align:center" aria-label="Series">
            <span class="muted small">×</span>
            <input type="text" value="${esc(e.reps)}" data-efield="reps" data-di="${di}" data-ei="${ei}" style="width:70px;text-align:center" aria-label="Repeticiones" placeholder="8-12">
            <button class="icon-btn" data-action="rex-up" data-di="${di}" data-ei="${ei}" aria-label="Subir">${ICON_UP}</button>
            <button class="icon-btn" data-action="rex-down" data-di="${di}" data-ei="${ei}" aria-label="Bajar">${ICON_DOWN}</button>
            <button class="icon-btn" data-action="rex-remove" data-di="${di}" data-ei="${ei}" aria-label="Quitar">${ICON_X}</button>
          </div>
        </div>`).join('')}</div>` : '<p class="muted small">Sin ejercicios todavía.</p>'}
      <button class="btn sm" data-action="day-add-ex" data-di="${di}" style="margin-top:8px">+ Añadir ejercicio</button>
    </div>`).join('')}
    <button class="btn block" data-action="day-add">+ Añadir día</button>
    ${embedded ? '' : `<div class="stack" style="margin-top:20px">
      <button class="btn primary block" data-action="close-editor">Listo</button>
      <button class="btn block ghost" data-action="change-routine">Cambiar a otra rutina</button>
    </div>`}`;
}

// =====================================================================
// EJERCICIOS
// =====================================================================

function muscleChips(active, action) {
  return `<div class="chips">
    <button class="chip ${!active ? 'active' : ''}" data-action="${action}" data-muscle="">Todos</button>
    ${MUSCLES.map((m) => `<button class="chip ${active === m ? 'active' : ''}" data-action="${action}" data-muscle="${m}">${m}</button>`).join('')}
  </div>`;
}

function showExerciseDetail(id, tab = ui.exTab) {
  ui.exTab = tab;
  const ex = S.exById(id);
  const hist = S.exerciseHistory(id);
  const rec = S.exerciseRecords(id);
  const routine = S.activeRoutine();
  const u = S.unitFor(id);
  const tabs = [['about', 'Acerca de'], ['history', 'Historial'], ['charts', 'Gráficos'], ['records', 'Récords']];
  let body = '';

  if (tab === 'about') {
    const video = `https://www.youtube.com/results?search_query=${encodeURIComponent(ex.name + ' técnica correcta')}`;
    const [primary, secondary] = musclesFor(id);
    body = `
      <div class="muscle-guide">
        <div class="bodies">
          <div><div class="body-map" data-muscle-map="${id}" data-view="front"></div><div class="cap">Frente</div></div>
          <div><div class="body-map" data-muscle-map="${id}" data-view="back"></div><div class="cap">Espalda</div></div>
        </div>
        <div class="legend"><span><span class="sw sw-primary"></span>Principal</span>${secondary.length ? '<span><span class="sw sw-secondary"></span>Secundario</span>' : ''}</div>
        <div class="row wrap" style="gap:6px;justify-content:center">
          ${muscleNames(primary).map((n) => `<span class="tag tag-primary">${n}</span>`).join('')}
          ${muscleNames(secondary).map((n) => `<span class="tag">${n}</span>`).join('')}
        </div>
      </div>
      <div class="row wrap" style="gap:6px;margin:12px 0"><span class="tag">${esc(ex.equipment)}</span></div>
      ${rec.sets ? `<p class="small" style="margin:0 0 12px">Lo has hecho en <b>${rec.sessions}</b> ${rec.sessions === 1 ? 'sesión' : 'sesiones'} (${series(rec.sets)}). Mejor serie: <b>${wt(rec.maxKg.kg, u)} × ${rec.maxKg.reps}</b>.</p>`
        : '<p class="muted small" style="margin:0 0 12px">Todavía no has registrado este ejercicio.</p>'}
      <div class="row between" style="margin-bottom:12px"><div class="grow"><b>Unidad de peso</b><div class="muted small">Si esta máquina está en libras, elige lb</div></div>${unitSwitch(id, u)}</div>
      <a class="btn block" href="${video}" target="_blank" rel="noopener">▶ Ver técnica en YouTube</a>
      ${routine ? `<div class="section-title">Añadir a “${esc(routine.name)}”</div>
        <div class="row wrap">${routine.days.map((d) => `<button class="btn sm" data-action="add-ex-to-day" data-ex="${id}" data-day="${d.id}">${esc(d.name)}</button>`).join('')}</div>` : ''}`;
  } else if (tab === 'history') {
    body = hist.length
      ? `<div class="list small">${hist.slice(0, 30).map((h) => `<div class="list-item" style="align-items:flex-start">
          <div style="width:90px;flex:none" class="muted">${S.formatDate(h.date)}</div>
          <div class="grow">${h.sets.map((x) => `${sideTag(x)}${wn(x.kg, u)}×${x.reps}${x.effort !== '' && x.effort !== undefined ? `<span class="muted">@${x.effort}</span>` : ''}`).join(' · ')}
            ${h.note ? `<div class="muted">📝 ${esc(h.note)}</div>` : ''}</div></div>`).join('')}</div>`
      : '<div class="empty small">Sin historial todavía.</div>';
  } else if (tab === 'charts') {
    const metrics = S.isSimple() ? [['max', 'Peso máx.'], ['volume', 'Volumen']] : [['e1rm', '1RM est.'], ['max', 'Peso máx.'], ['volume', 'Volumen']];
    if (!metrics.some(([k]) => k === ui.exMetric)) ui.exMetric = metrics[0][0];
    body = `<div class="segmented" style="margin-bottom:8px">${metrics.map(([k, l]) => `<button class="${ui.exMetric === k ? 'active' : ''}" data-action="ex-metric" data-m="${k}" data-id="${id}">${l}</button>`).join('')}</div>
      <div class="muted small">${ui.exMetric === 'e1rm' ? 'Máximo estimado para 1 repetición (fórmula de Epley), mejor serie de cada sesión' : ui.exMetric === 'max' ? 'Peso más alto usado en cada sesión' : `Peso × repeticiones sumados en cada sesión (${u})`}</div>
      ${hist.length >= 2 ? '<div class="chart-box"><canvas id="c-exercise" role="img" aria-label="Evolución del ejercicio"></canvas></div>'
        : '<div class="empty small">Necesitas al menos 2 sesiones para ver la evolución.</div>'}`;
  } else {
    const tile = (label, value, sub) => `<div class="stat"><div class="label">${label}</div><div class="value">${value}</div><div class="delta">${sub}</div></div>`;
    body = rec.sets ? `<div class="grid-2">
        ${tile('Peso máximo', wt(rec.maxKg.kg, u), `× ${rec.maxKg.reps} · ${S.formatDate(rec.maxKg.date)}`)}
        ${S.isSimple() ? '' : tile('1RM estimado', wt(rec.bestE1rm.value, u), `${wn(rec.bestE1rm.kg, u)}×${rec.bestE1rm.reps} · ${S.formatDate(rec.bestE1rm.date)}`)}
        ${tile('Más repeticiones', rec.maxReps.reps, `con ${wt(rec.maxReps.kg, u)} · ${S.formatDate(rec.maxReps.date)}`)}
        ${tile('Mejor sesión', wt(rec.bestVolume.value, u), `volumen · ${S.formatDate(rec.bestVolume.date)}`)}
      </div>` : '<div class="empty small">Aún no hay récords. ¡Registra tu primera sesión!</div>';
  }

  openSheet(ex.name, `
    <div class="segmented tabs" style="margin-bottom:14px">${tabs.map(([k, l]) => `<button class="${k === tab ? 'active' : ''}" data-action="ex-tab" data-tab="${k}" data-id="${id}">${l}</button>`).join('')}</div>
    ${body}`);

  if (tab === 'charts' && hist.length >= 2) {
    const rows = [...hist].reverse();
    const val = (h) => ui.exMetric === 'e1rm' ? Math.max(...h.sets.map(S.e1rm))
      : ui.exMetric === 'max' ? Math.max(...h.sets.map((x) => Number(x.kg) || 0))
      : h.sets.reduce((a, x) => a + S.setVolume(x), 0);
    lineChart(document.getElementById('c-exercise'), {
      labels: rows.map((h) => S.formatDate(h.date)),
      data: rows.map((h) => S.toUnit(val(h), u)),
      unit: u,
    });
  }
}

// Selector reutilizable: busca un ejercicio y ejecuta onPick(id).
// Selector reutilizable: busca un ejercicio y ejecuta onPick(id).
// Se abre desde arriba para que el teclado del teléfono no tape los resultados, y
// los ejercicios con variantes (p. ej. prensa) aparecen una sola vez: al tocarlos se elige el enfoque.
function openPicker(onPick, initialQuery = '') {
  let query = initialQuery, muscle = '';
  openSheet('Añadir ejercicio', `
    <input type="search" id="pick-search" placeholder="Buscar ejercicio" aria-label="Buscar ejercicio" value="${esc(query)}" style="margin-bottom:8px" autocomplete="off">
    <div id="pick-chips"></div>
    <div id="pick-results" class="pick-results"></div>
    <button class="btn block" data-action="pick-new" style="margin-top:10px">+ Crear ejercicio propio</button>`, (root) => {
    $sheet.classList.add('sheet-top');
    const input = root.querySelector('#pick-search');
    const results = root.querySelector('#pick-results');
    // Con el teclado abierto, iOS reduce y desplaza la zona visible: el buscador la sigue.
    const fit = () => {
      const vv = window.visualViewport;
      const visible = vv ? vv.height : window.innerHeight;
      document.documentElement.style.setProperty('--vvh', `${visible}px`);
      $sheet.style.transform = vv && vv.offsetTop ? `translateY(${vv.offsetTop}px)` : '';
      const top = results.getBoundingClientRect().top - (vv ? vv.offsetTop : 0);
      results.style.maxHeight = `${Math.max(120, visible - top - 16)}px`;
    };
    const draw = () => {
      root.querySelector('#pick-chips').innerHTML = muscleChips(muscle, 'pick-filter');
      const seen = new Set();
      const items = [];
      for (const e of S.searchExercises(query, muscle)) {
        if (!e.family) { items.push(e); continue; }
        if (seen.has(e.family)) continue;
        seen.add(e.family);
        items.push({ family: e.family, name: FAMILIES[e.family].name, variants: FAMILIES[e.family].variants.map(([, l]) => l) });
      }
      results.innerHTML = items.length ? `<div class="list">${items.map((e) => e.family
        ? `<button class="list-item" data-action="pick-family" data-family="${e.family}">
            <div class="grow"><div>${esc(e.name)}</div><div class="muted small">Elige el enfoque: ${e.variants.join(' o ').toLowerCase()}</div></div><span class="muted">›</span></button>`
        : `<button class="list-item" data-action="pick" data-id="${e.id}">
            <div class="grow"><div>${esc(e.name)}</div><div class="muted small">${esc(e.muscle)} · ${esc(e.equipment)}${e.custom ? ' · propio' : ''}</div></div><span class="muted">›</span></button>`).join('')}</div>`
        : '<div class="empty small">No hay ejercicios que coincidan.</div>';
      fit();
    };
    input.addEventListener('input', () => { query = input.value; draw(); });
    window.visualViewport?.addEventListener('resize', fit);
    window.visualViewport?.addEventListener('scroll', fit);
    $sheet.addEventListener('close', () => {
      window.visualViewport?.removeEventListener('resize', fit);
      window.visualViewport?.removeEventListener('scroll', fit);
      $sheet.style.transform = '';
    }, { once: true });
    root.onclick = (e) => {
      const b = e.target.closest('[data-action]');
      if (!b) return;
      if (b.dataset.action === 'pick-filter') { muscle = b.dataset.muscle; draw(); }
      if (b.dataset.action === 'pick') { root.onclick = null; closeSheet(); onPick(b.dataset.id); }
      if (b.dataset.action === 'pick-family') { root.onclick = null; openVariantPicker(b.dataset.family, onPick, query); }
      if (b.dataset.action === 'pick-new') { root.onclick = null; newExerciseForm(query, onPick); }
    };
    draw();
    setTimeout(() => { input.focus(); fit(); }, 50);
  });
}

function openVariantPicker(key, onPick, query) {
  const fam = FAMILIES[key];
  openSheet(fam.name, `
    <p class="muted" style="margin:0 0 10px">¿Con qué enfoque lo vas a hacer?</p>
    <div class="variant-list">${fam.variants.map(([id, label]) => `
      <button class="variant" data-action="pick" data-id="${id}">
        <span class="thumb" data-muscle-map="${id}" data-thumb></span>
        <span class="grow"><b>Enfoque en ${label.toLowerCase()}</b><span class="muted small">${muscleNames(musclesFor(id)[0]).join(' · ')}</span></span>
        <span class="chev" aria-hidden="true">›</span>
      </button>`).join('')}</div>`, (root) => {
    $sheet.classList.add('sheet-top');
    root.onclick = (e) => {
      const b = e.target.closest('[data-action]');
      if (!b) return;
      if (b.dataset.action === 'pick') { root.onclick = null; closeSheet(); onPick(b.dataset.id); }
      if (b.dataset.action === 'variant-back') { root.onclick = null; openPicker(onPick, query); }
    };
  }, 'variant-back');
}

function newExerciseForm(prefill = '', onCreated) {
  openSheet('Nuevo ejercicio', `
    <form id="new-ex" class="stack">
      <label class="field"><span>Nombre</span><input type="text" name="name" required maxlength="60" value="${esc(prefill)}"></label>
      <div class="grid-2">
        <label class="field"><span>Grupo muscular</span><select name="muscle">${MUSCLES.map((m) => `<option>${m}</option>`).join('')}</select></label>
        <label class="field"><span>Equipo</span><select name="equipment">${['Barra', 'Mancuernas', 'Máquina', 'Polea', 'Smith', 'Peso corporal', 'Otro'].map((m) => `<option>${m}</option>`).join('')}</select></label>
      </div>
      <button class="btn primary block">Guardar ejercicio</button>
    </form>`, (root) => {
    root.querySelector('#new-ex').addEventListener('submit', (e) => {
      e.preventDefault();
      const f = new FormData(e.target);
      const ex = S.addCustomExercise(f.get('name'), f.get('muscle'), f.get('equipment'));
      closeSheet();
      toast(`“${ex.name}” creado`);
      if (onCreated) onCreated(ex.id);
      else render();
    });
  });
}

// =====================================================================
// PROGRESO
// =====================================================================

function periodKey(iso, period) {
  const d = S.parseISO(iso);
  if (period === 'month') return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
  return S.todayISO(S.startOfWeek(d));
}

function weekStreak() {
  const weeks = new Set(S.getState().sessions.map((s) => periodKey(s.date, 'week')));
  const d = S.startOfWeek(new Date());
  if (!weeks.has(S.todayISO(d))) d.setDate(d.getDate() - 7); // la semana actual aún puede completarse
  let n = 0;
  while (weeks.has(S.todayISO(d))) { n++; d.setDate(d.getDate() - 7); }
  return n;
}

const RANGES = [['1m', '1M', 30], ['3m', '3M', 91], ['1a', '1A', 365], ['all', 'Todo', Infinity]];

function rangeSessions() {
  const days = RANGES.find(([k]) => k === ui.range)[2];
  if (days === Infinity) return S.getState().sessions;
  const from = new Date(); from.setDate(from.getDate() - days);
  const iso = S.todayISO(from);
  return S.getState().sessions.filter((x) => x.date > iso);
}

// Números cortos para las fichas: 9,9 K · 1,08 M.
function short(v) {
  if (v >= 1e6) return `${(v / 1e6).toLocaleString('es', { maximumFractionDigits: 2 })} M`;
  if (v >= 1e4) return `${(v / 1e3).toLocaleString('es', { maximumFractionDigits: 1 })} K`;
  return Math.round(v).toLocaleString('es');
}

// Grupos del gráfico de músculos; cada uno suma los músculos del mapa que lo forman.
const MUSCLE_BARS = [
  ['Brazos', ['biceps', 'triceps', 'forearms']],
  ['Pecho', ['chest']],
  ['Espalda', ['lats', 'upper_back', 'lower_back']],
  ['Hombros', ['shoulders']],
  ['Piernas', ['quads', 'hamstrings', 'glutes', 'calves']],
  ['Core', ['abs', 'obliques']],
];

function rangeStats(sessions) {
  const exIds = new Set();
  let sets = 0, reps = 0, minutes = 0;
  const direct = MUSCLE_BARS.map(() => 0), indirect = MUSCLE_BARS.map(() => 0);
  const barOf = (g) => MUSCLE_BARS.findIndex(([, gs]) => gs.includes(g));
  for (const s of sessions) {
    const m = (s.finishedAt - s.startedAt) / 60000;
    if (m > 0 && m < 300) minutes += m;
    for (const e of s.exercises) {
      exIds.add(e.exId);
      const done = e.sets.filter((x) => x.done !== false && x.side !== 'R');
      sets += done.length;
      done.forEach((x) => { reps += Number(x.reps) || 0; });
      // Cada serie cuenta una vez por grupo: directa si algún músculo principal es del grupo.
      const [p, sec] = musclesFor(e.exId);
      const pb = new Set(p.map(barOf).filter((i) => i >= 0));
      const sb = new Set(sec.map(barOf).filter((i) => i >= 0 && !pb.has(i)));
      pb.forEach((i) => { direct[i] += done.length; });
      sb.forEach((i) => { indirect[i] += done.length / 2; });
    }
  }
  const volume = sessions.reduce((a, x) => a + S.sessionVolume(x), 0);
  return { workouts: sessions.length, minutes, exercises: exIds.size, sets, reps, volume, direct, indirect };
}

// Evolución de cada ejercicio: un punto por entrenamiento (peso máximo o volumen).
function exerciseSeries(sessions) {
  const map = new Map();
  for (const s of sessions) {
    for (const e of s.exercises) {
      const done = e.sets.filter((x) => x.done !== false);
      if (!done.length) continue;
      const y = ui.exMetricP === 'vol'
        ? done.reduce((a, x) => a + S.setVolume(x), 0)
        : Math.max(...done.map((x) => Number(x.kg) || 0));
      if (!map.has(e.exId)) map.set(e.exId, []);
      map.get(e.exId).push({ x: S.parseISO(s.date).getTime(), y });
    }
  }
  return [...map.entries()]
    .filter(([, pts]) => pts.length >= 2 && pts.some((p) => p.y > 0))
    .sort((a, b) => b[1].length - a[1].length || b[1][b[1].length - 1].x - a[1][a[1].length - 1].x);
}

function renderProgress() {
  const st = S.getState();
  const sessions = rangeSessions();
  const t = rangeStats(sessions);
  const du = S.defaultUnit();
  const tile = (value, label) => `<div class="an-tile"><b>${value}</b><span>${label}</span></div>`;
  const hours = t.minutes >= 60 ? `${Math.round(t.minutes / 60)} h` : `${Math.round(t.minutes)} min`;
  const streak = weekStreak();

  let html = `<div class="segmented range-tabs" role="tablist">${RANGES.map(([k, l]) =>
    `<button class="${ui.range === k ? 'active' : ''}" data-action="range" data-r="${k}" role="tab" aria-selected="${ui.range === k}">${l}</button>`).join('')}</div>`;

  if (!st.sessions.length) {
    $view.innerHTML = `<div class="card empty-progress">
        <div class="ep-icon" aria-hidden="true">📈</div>
        <b>Aquí verás cómo mejoras</b>
        <p class="muted small">Cuando termines tu primer entrenamiento aparecerán tus entrenos, los músculos que trabajas y la evolución de cada ejercicio.</p>
        <button class="btn primary" data-action="go-train">Ir a entrenar</button>
      </div>${bodyCardHTML()}`;
    drawBodyChart();
    return;
  }
  if (!sessions.length) {
    html += `<div class="card empty small">No hay entrenamientos en este periodo. Prueba con un periodo más largo.</div>`;
  }

  html += `<div class="an-grid">
    ${tile(t.workouts, t.workouts === 1 ? 'Entreno' : 'Entrenos')}
    ${tile(hours, 'Duración')}
    ${tile(t.exercises, 'Ejercicios')}
    ${tile(short(t.sets), 'Series')}
    ${tile(short(t.reps), 'Reps')}
    ${tile(short(S.toUnit(t.volume, du)), `Volumen ${du}`)}
  </div>`;

  const maxBar = Math.max(1, ...t.direct.map((d, i) => d + t.indirect[i]));
  const pct = (v) => `${((v / maxBar) * 100).toFixed(1)}%`;
  html += `<section class="an-section">
    <div class="an-head"><h3>Músculos</h3><button class="info-btn" data-action="muscle-info" aria-label="Qué significan las barras">i</button></div>
    ${MUSCLE_BARS.map(([name], i) => `<div class="mb-row">
      <span class="mb-name">${name}</span>
      <span class="mb-track"><span class="mb-direct" style="width:${pct(t.direct[i])}"></span><span class="mb-indirect" style="width:${pct(t.indirect[i])}"></span></span>
      <span class="mb-num">${Math.round(t.direct[i] + t.indirect[i])}</span>
    </div>`).join('')}
  </section>`;

  const list = exerciseSeries(sessions);
  const shown = list.slice(0, ui.exShowAll ? 30 : 5);
  const isVol = ui.exMetricP === 'vol';
  html += `<section class="an-section">
    <div class="an-head"><h3>Ejercicios</h3>
      <div class="segmented sm">
        <button class="${isVol ? 'active' : ''}" data-action="ex-metric-p" data-m="vol">Vol</button>
        <button class="${isVol ? '' : 'active'}" data-action="ex-metric-p" data-m="max">Máx</button>
      </div></div>
    ${shown.length ? shown.map(([id, pts], i) => {
      const u = isVol ? du : S.unitFor(id);
      const lastY = S.toUnit(pts[pts.length - 1].y, u);
      return `<div class="ex-spark">
        <button class="ex-spark-head" data-action="ex-detail" data-id="${id}"><span class="ellipsis">${esc(S.exById(id).name)}</span>
          <b>${isVol ? short(lastY) : fmtN(lastY)} <small>${u}</small></b></button>
        <div class="spark-box"><canvas id="c-ex-${i}" role="img" aria-label="Evolución de ${esc(S.exById(id).name)}"></canvas></div>
      </div>`;
    }).join('') : '<p class="muted small" style="margin:4px 0 0">Cuando repitas un ejercicio al menos dos veces en este periodo verás aquí cómo evoluciona.</p>'}
    ${list.length > 5 ? `<button class="btn sm ghost block" data-action="ex-show-all">${ui.exShowAll ? 'Ver menos' : `Ver los ${list.length} ejercicios`}</button>` : ''}
  </section>`;

  html += `<section class="an-section">
    <div class="an-head"><h3>Constancia</h3><span class="muted small">Racha: <b>${streak}</b> ${streak === 1 ? 'semana' : 'semanas'}</span></div>
    ${heatmapHTML(20)}
  </section>`;

  html += bodyCardHTML();
  html += historyHTML();
  $view.innerHTML = html;

  shown.forEach(([id, pts], i) => {
    const u = isVol ? du : S.unitFor(id);
    sparkArea(document.getElementById(`c-ex-${i}`), { points: pts.map((p) => ({ x: p.x, y: S.toUnit(p.y, u) })), unit: u });
  });
  drawBodyChart();
}

function drawBodyChart() {
  const field = S.BODY_FIELDS.find((f) => f.key === ui.bodyField);
  const bodyData = bodySeries(field);
  if (bodyData.length) {
    lineChart(document.getElementById('c-body'), {
      labels: bodyData.map((b) => S.formatDate(b.date)),
      data: bodyData.map((b) => bodyVal(b[field.key], field)),
      unit: bodyUnit(field),
    });
  }
}

// El peso corporal se guarda en kg y se muestra en la unidad por defecto.
const bodyUnit = (field) => (field.convert ? S.defaultUnit() : field.unit);
const bodyVal = (v, field) => (field.convert ? S.toUnit(v, S.defaultUnit()) : Number(v));

function bodySeries(field) {
  return S.getState().body.filter((b) => b[field.key] !== undefined && b[field.key] !== '' && b[field.key] !== null);
}

function bodyCardHTML() {
  const st = S.getState();
  const field = S.BODY_FIELDS.find((f) => f.key === ui.bodyField);
  const bodyData = bodySeries(field);
  const lastBody = bodyData[bodyData.length - 1];
  const firstBody = bodyData[0];
  return `<div class="card">
    <div class="row between"><h3>Peso corporal y medidas</h3>
      <button class="btn sm primary" data-action="body-add" style="white-space:nowrap">+ Registrar</button></div>
    <div class="chips" style="margin-top:8px">${S.BODY_FIELDS.map((f) => `<button class="chip ${f.key === ui.bodyField ? 'active' : ''}" data-action="body-field" data-f="${f.key}">${f.label}</button>`).join('')}</div>
    ${lastBody ? (() => {
      const cur = bodyVal(lastBody[field.key], field);
      const diff = cur - bodyVal(firstBody[field.key], field);
      return `<p class="small" style="margin:0">Actual: <b>${fmtN(cur)} ${bodyUnit(field)}</b>
        ${bodyData.length > 1 ? `<span class="muted"> · ${diff >= 0 ? '+' : ''}${fmtN(diff)} ${bodyUnit(field)} desde ${S.formatDate(firstBody.date)}</span>` : ''}</p>`;
    })() : ''}
    ${bodyData.length
      ? `<div class="chart-box"><canvas id="c-body" role="img" aria-label="Evolución de ${field.label}"></canvas></div>`
      : `<div class="empty small">Registra tu ${field.label.toLowerCase()} para ver su evolución.</div>`}
    ${st.body.length ? `<details class="table-view"><summary>Ver registros</summary><table>
      <thead><tr><th>Fecha</th>${S.BODY_FIELDS.map((f) => `<th>${f.label}</th>`).join('')}<th></th></tr></thead>
      <tbody>${[...st.body].reverse().map((b) => `<tr><td>${S.formatDate(b.date)}</td>${S.BODY_FIELDS.map((f) => `<td>${b[f.key] !== undefined && b[f.key] !== '' ? fmtN(bodyVal(b[f.key], f)) : '–'}</td>`).join('')}
        <td><button class="btn sm ghost" data-action="body-edit" data-date="${b.date}">Editar</button></td></tr>`).join('')}</tbody></table></details>` : ''}
  </div>`;
}

function historyHTML() {
  const all = [...S.getState().sessions].reverse();
  const shown = all.slice(0, ui.historyLimit);
  return `<div class="card">
    <h3>Historial</h3>
    ${shown.length ? `<div class="list">${shown.map((s) => `
      <button class="list-item" data-action="session-detail" data-id="${s.id}">
        <div class="grow"><div><b>${esc(s.dayName)}</b></div>
        <div class="muted small">${S.formatDate(s.date)} · ${series(S.doneSets(s))}${S.isSimple() ? '' : ` · ${vol(S.sessionVolume(s))}`}</div></div>
        <span class="muted">›</span>
      </button>`).join('')}</div>
      ${all.length > shown.length ? `<button class="btn sm ghost" data-action="history-more">Ver más</button>` : ''}`
    : '<div class="empty small">Tus entrenamientos terminados aparecerán aquí.</div>'}
  </div>`;
}

function heatmapHTML(weeks) {
  const perDay = new Map();
  for (const s of S.getState().sessions) perDay.set(s.date, (perDay.get(s.date) || 0) + S.sessionVolume(s) + 1);
  const values = [...perDay.values()].sort((a, b) => a - b);
  const q = (f) => values[Math.floor(f * (values.length - 1))] || 0;
  const [q1, q2, q3] = [q(0.25), q(0.5), q(0.75)];
  const level = (v) => (!v ? 0 : v <= q1 ? 1 : v <= q2 ? 2 : v <= q3 ? 3 : 4);

  const start = S.startOfWeek(new Date());
  start.setDate(start.getDate() - (weeks - 1) * 7);
  const today = S.todayISO();
  let cells = '';
  for (let i = 0; i < weeks * 7; i++) {
    const d = new Date(start); d.setDate(start.getDate() + i);
    const iso = S.todayISO(d);
    const v = perDay.get(iso);
    const future = iso > today;
    const title = future ? '' : `${S.formatDate(iso)}: ${v ? 'entrenado' : 'descanso'}`;
    cells += `<div class="heat ${future ? 'future' : ''}" data-l="${future ? 0 : level(v)}" title="${title}"></div>`;
  }
  return `<div class="heatmap" style="grid-template-columns:repeat(${weeks},1fr)">${cells}</div>
    <div class="heat-legend">Menos <span class="heat"></span><span class="heat" data-l="1"></span><span class="heat" data-l="2"></span><span class="heat" data-l="3"></span><span class="heat" data-l="4"></span> Más</div>`;
}

function bodyForm(date = S.todayISO()) {
  const existing = S.getState().body.find((b) => b.date === date) || {};
  openSheet('Registrar medidas', `
    <form id="body-form" class="stack">
      <label class="field"><span>Fecha</span><input type="date" name="date" value="${date}" max="${S.todayISO()}" required></label>
      <div class="grid-2">${S.BODY_FIELDS.map((f) => `<label class="field"><span>${f.label} (${bodyUnit(f)})</span>
        <input type="number" inputmode="decimal" step="0.1" min="0" name="${f.key}" value="${esc(existing[f.key] !== undefined && existing[f.key] !== '' ? bodyVal(existing[f.key], f) : '')}"></label>`).join('')}</div>
      <p class="muted small" style="margin:0">Deja en blanco lo que no midas hoy.</p>
      <button class="btn primary block">Guardar</button>
      ${existing.date ? `<button type="button" class="btn ghost danger block" data-action="body-delete" data-date="${date}">Eliminar este registro</button>` : ''}
    </form>`, (root) => {
    root.querySelector('#body-form').addEventListener('submit', (e) => {
      e.preventDefault();
      const f = new FormData(e.target);
      const entry = { date: f.get('date') };
      for (const bf of S.BODY_FIELDS) {
        const v = f.get(bf.key);
        if (v !== '') entry[bf.key] = bf.convert ? S.fromUnit(Number(v), S.defaultUnit()) : Number(v);
      }
      if (Object.keys(entry).length === 1) return toast('Introduce al menos una medida');
      S.upsertBody(entry);
      closeSheet();
      toast('Medidas guardadas');
      render();
    });
  });
}

// =====================================================================
// CONFIGURACIÓN INICIAL
// =====================================================================

const LEVELS = [
  ['beginner', 'Menos de 6 meses', 'Estoy empezando o volviendo después de mucho tiempo'],
  ['intermediate', 'De 6 meses a 2 años', 'Conozco los ejercicios básicos'],
  ['advanced', 'Más de 2 años', 'Tengo experiencia y sé qué rutina quiero'],
];

const WHY = {
  'full-body': 'Trabajas todo el cuerpo en cada sesión: aprendes los ejercicios básicos más rápido y progresas aunque vayas pocos días.',
  'torso-pierna': 'Alternas torso y pierna, así cada músculo descansa entre sesiones.',
  ppl: 'Separa empuje, tracción y pierna para entrenar con más volumen.',
  'torso-pierna-ppl': 'Cada músculo se entrena dos veces por semana, repartido en 5 días.',
  arnold: 'Más volumen por músculo, pensado para quien ya tiene experiencia.',
};
// Resumen de una línea para la lista de rutinas (avanzados).
const TPL_SUB = {
  'full-body': 'todo el cuerpo',
  'torso-pierna': 'variantes A y B',
  'torso-pierna-ppl': 'cada músculo 2 veces',
  ppl: 'empuje, tracción, pierna',
  arnold: 'exigente',
  'excel-4-dias': 'énfasis en glúteo',
};

// Cifras de una plantilla repartida sobre los días elegidos: días, ejercicios por
// día, series por semana y minutos por sesión (≈ 3 min por serie con descanso).
function tplStats(t, weekdays) {
  const n = weekdays.length || t.daysPerWeek;
  const perDay = t.days.map((d) => d.exercises.reduce((a, e) => a + e.sets, 0));
  const avg = (xs) => xs.reduce((a, x) => a + x, 0) / xs.length;
  return {
    days: n,
    exercises: Math.round(avg(t.days.map((d) => d.exercises.length))),
    weekSets: Array.from({ length: n }, (_, i) => perDay[i % perDay.length]).reduce((a, x) => a + x, 0),
    minutes: Math.round((avg(perDay) * 3) / 5) * 5,
  };
}

// Nombre corto de un día de la plantilla para la tira semanal («Torso», «Pierna», «A»…).
function weekLabel(t, d) {
  const words = t.days.map((x) => shortName(x.name).split(' '));
  const shared = words.every((w) => w[0] === words[0][0]);
  const w = shortName(d.name).split(' ');
  return shared ? w[w.length - 1] : w[0];
}

function renderOnboarding() {
  const ob = ui.ob;
  const back = (step) => `<button class="btn ghost" data-action="ob-go" data-step="${step}" style="padding-left:0">‹ Atrás</button>`;
  const cancel = ob.fromSettings ? `<button class="btn ghost" data-action="ob-cancel" style="padding-left:0">Cancelar</button>` : '';
  const progress = (n) => `<div class="ob-progress" aria-label="Paso ${n} de 3">${[1, 2, 3].map((i) => `<span class="${i <= n ? 'on' : ''}"></span>`).join('')}</div>`;
  let html = '';
  $title.textContent = ob.fromSettings ? 'Cambiar rutina' : 'Bienvenido';

  if (ob.step === 'welcome') {
    $title.textContent = '';
    html = `<div class="ob-hero">
        <img src="icons/icon.svg" alt="" width="72" height="72">
        <h1>Tu rutina y tu progreso, en un solo lugar</h1>
        <p class="muted">Responde 3 preguntas y te armamos una rutina en un minuto. Luego solo anota tus series y mira cómo mejoras.</p>
      </div>
      <div class="stack">
        <button class="btn primary block" data-action="ob-go" data-step="experience">Empezar</button>
        ${Cloud.isConfigured() ? '<button class="btn block" data-action="ob-go" data-step="login">Ya tengo cuenta</button>' : ''}
      </div>`;
  } else if (ob.step === 'login') {
    html = `${back('welcome')}
      <h2 class="ob-q">Entra a tu cuenta</h2>
      <p class="muted">Recuperaremos tu rutina y tu historial.</p>
      <form class="card stack" id="login-form">
        <input type="email" name="email" placeholder="Correo" autocomplete="email" required>
        <input type="password" name="password" placeholder="Contraseña" autocomplete="current-password" minlength="6" required>
        <button class="btn primary block" name="mode" value="login">Entrar</button>
        <button type="button" class="btn sm ghost" data-action="cloud-reset">¿Olvidaste tu contraseña?</button>
        <p class="small" id="login-msg" style="margin:0" role="status"></p>
      </form>`;
  } else if (ob.step === 'experience') {
    // Al configurar por primera vez, el cuerpo de la guía se elige en esta misma pantalla.
    const askGender = !ob.fromSettings && !S.getState().profile?.gender;
    html = `${ob.fromSettings ? cancel : back('welcome')}${progress(1)}
      ${askGender ? `<h2 class="ob-q">Tu cuerpo en la guía de músculos</h2>
      <div class="segmented ob-gender" role="group" aria-label="Cuerpo en la guía">${[['male', 'Hombre'], ['female', 'Mujer']].map(([k, t]) =>
        `<button class="${ob.gender === k ? 'active' : ''}" data-action="ob-gender" data-v="${k}" aria-pressed="${ob.gender === k}">${t}</button>`).join('')}</div>` : ''}
      <h2 class="ob-q">¿Cuánto tiempo llevas entrenando?</h2>
      <div class="stack">${LEVELS.map(([k, t, d]) => `<button class="option ${ob.level === k ? 'selected' : ''}" data-action="ob-level" data-v="${k}">
        <b>${t}</b><span class="muted small">${d}</span></button>`).join('')}</div>`;
  } else if (ob.step === 'days') {
    const n = ob.days.length;
    const rec = n ? S.templateByKey(S.recommendTemplate(ob.level, n)) : null;
    html = `${back('experience')}${progress(2)}
      <h2 class="ob-q">¿Qué días puedes entrenar?</h2>
      <p class="muted" style="margin-top:0">Toca los días. Puedes cambiarlos cuando quieras.</p>
      <div class="day-picker">${S.DAY_NAMES.map((name, i) => `<button class="day-toggle ${ob.days.includes(i) ? 'on' : ''}" data-action="ob-day" data-d="${i}" aria-pressed="${ob.days.includes(i)}">
        <b>${S.DAY_SHORT[i]}</b><span>${name.slice(0, 3)}</span></button>`).join('')}</div>
      <p class="small" style="min-height:2.6em">${n ? `<b>${n} ${n === 1 ? 'día' : 'días'} por semana.</b> ${n === 1 ? 'Con 2 o 3 días progresarás más rápido.' : ''}
        ${n === 7 ? 'Deja al menos un día de descanso: el músculo crece mientras descansas.' : ob.level === 'beginner' && n > 4 ? 'Para empezar, 3-4 días bastan: el descanso también hace crecer el músculo.' : ''}` : 'Elige al menos un día.'}</p>
      <button class="btn primary block" data-action="ob-go" data-step="choose" ${n ? '' : 'disabled'}>Continuar</button>`;
    void rec;
  } else if (ob.step === 'choose') {
    const recKey = S.recommendTemplate(ob.level, ob.days.length);
    const rec = S.templateByKey(recKey);
    const saved = S.getState().routines.filter((r) => !r.seeded && r.id !== S.getState().activeRoutineId);
    const savedHTML = saved.length ? `<div class="section-title">Tus rutinas guardadas</div><div class="group-list">${saved.map((r) => `<div class="ob-row">
        <div class="grow"><div class="ob-row-t">${esc(r.name)}</div><div class="ob-row-s">${r.days.length} días</div></div>
        <button class="btn sm" data-action="ob-activate" data-id="${r.id}">Usar</button></div>`).join('')}</div>` : '';
    if (ob.level === 'beginner' && !ob.showAll) {
      // A · Principiante: solo la rutina recomendada, su semana y un botón.
      const st = tplStats(rec, ob.days);
      const sorted = [...ob.days].sort((x, y) => x - y);
      const label = (wd) => { const i = sorted.indexOf(wd); return i < 0 ? '' : esc(weekLabel(rec, rec.days[i % rec.days.length])); };
      html = `${back('days')}${progress(3)}
      <div class="ob-rec">
        <div class="eyebrow accent">Recomendada para ti</div>
        <h1 class="ob-title">${esc(rec.name)}</h1>
        <p class="ob-lead">${WHY[rec.key] || esc(rec.description)}</p>
        <div class="ob-stats">
          <div><b>${st.days}</b><span>${st.days === 1 ? 'Día' : 'Días'}</span></div>
          <div><b>${st.exercises}</b><span>Ejercicios</span></div>
          <div><b>~${st.minutes}</b><span>Minutos</span></div>
        </div>
        <div class="eyebrow">Tu semana</div>
        <div class="ob-week">${S.DAY_SHORT.map((l, wd) => `<div class="${sorted.includes(wd) ? 'on' : ''}"><b>${l}</b><i>${label(wd)}</i></div>`).join('')}</div>
        ${savedHTML}
        <div class="ob-foot">
          <button class="btn primary block lg" data-action="ob-pick" data-key="${rec.key}">Empezar con esta rutina</button>
          <button class="btn block ghost" data-action="preview-template" data-key="${rec.key}">Ver ejercicios</button>
          <button class="btn block ghost quiet" data-action="ob-show-all">Ver otras opciones</button>
        </div>
      </div>`;
    } else {
      // B · Avanzado: lista de rutinas; la elegida se abre con sus cifras.
      const sel = ob.sel || recKey;
      const others = TEMPLATES.filter((t) => t.key !== recKey);
      const radio = (on) => `<span class="ob-radio ${on ? 'on' : ''}" aria-hidden="true"></span>`;
      const row = (t, recommended) => {
        const on = sel === t.key;
        const st = tplStats(t, ob.days);
        return `<div class="ob-item ${on ? 'open' : ''}">
          <button class="ob-row" data-action="ob-sel" data-key="${t.key}" aria-pressed="${on}">${radio(on)}
            <div class="grow">${recommended ? '<div class="eyebrow accent">Recomendada</div>' : ''}
              <div class="ob-row-t">${esc(t.name)}</div>
              <div class="ob-row-s">${t.daysPerWeek} días${TPL_SUB[t.key] ? ` · ${TPL_SUB[t.key]}` : ''}</div></div></button>
          ${on ? `<div class="ob-detail">
            <div class="ob-mini">
              <div><b>${st.days}</b><span>Días</span></div>
              <div><b>${st.exercises}</b><span>Ejerc./día</span></div>
              <div><b>${st.weekSets}</b><span>Series/sem</span></div>
              <div><b>~${st.minutes}</b><span>Min</span></div>
            </div>
            <div class="ob-days">${t.days.map((d) => esc(shortName(d.name))).join(' · ')}</div>
            <button class="link" data-action="preview-template" data-key="${t.key}">Ver ejercicios ›</button>
          </div>` : ''}
        </div>`;
      };
      html = `${back('days')}${progress(3)}
      <h1 class="ob-title" style="margin-bottom:20px">Elige tu rutina</h1>
      <div class="group-list">${row(rec, true)}</div>
      <div class="section-title">Otras rutinas</div>
      <div class="group-list">${others.map((t) => row(t, false)).join('')}
        <div class="ob-item ${sel === 'custom' ? 'open' : ''}"><button class="ob-row" data-action="ob-sel" data-key="custom" aria-pressed="${sel === 'custom'}">${radio(sel === 'custom')}
          <div class="grow"><div class="ob-row-t">Crear la mía</div><div class="ob-row-s">Eliges tú los ejercicios de cada día</div></div></button></div>
      </div>
      ${savedHTML}
      <div class="ob-foot sticky">
        <button class="btn primary block lg" data-action="ob-pick" data-key="${sel}">Continuar</button>
      </div>`;
    }
  } else if (ob.step === 'review') {
    const r = S.routineById(ob.routineId);
    ui.editRoutineId = r.id;
    const empty = r.days.every((d) => !d.exercises.length);
    html = `${back('choose')}${progress(3)}
      <h2 class="ob-q">${empty ? 'Arma tu rutina' : 'Revisa tu rutina'}</h2>
      <p class="muted" style="margin-top:0">${empty
        ? 'Añade los ejercicios de cada día. Abajo puedes cambiar qué día entrenas cada uno.'
        : 'Estos son los ejercicios recomendados. Puedes cambiar ejercicios, series y días ahora o cuando quieras desde la pestaña <b>Mi plan</b>.'}</p>
      ${routineEditorHTML(r, { embedded: true })}
      <button class="btn primary block" data-action="ob-review-done" style="margin-top:16px">Continuar</button>`;
  }
  $view.innerHTML = `<div class="ob">${html}</div>`;
  if (ob.step === 'login') bindAccountForm($view, obLoggedIn);
}

// Tras entrar desde la bienvenida: recupera la rutina o sigue con la configuración.
async function obLoggedIn() {
  closeSheet();
  await Cloud.sync();
  if (!ui.ob) { toast('Sesión iniciada · sincronizando tus datos'); render(); return; }
  if (S.needsOnboarding()) {
    ui.ob = { step: 'experience', days: [] };
    toast('Tu cuenta aún no tiene rutina: vamos a crearla');
  } else {
    S.ensureProfile();
    ui.ob = null;
    toast('¡Bienvenido de vuelta!');
  }
  render();
}

// Entrar con un código de 6 dígitos enviado al correo (sin contraseña).
function openCodeLogin(onDone) {
  const back = ui.ob ? null : 'open-menu';
  openSheet('Entrar con código', `
    <form id="code-form" class="stack">
      <p class="muted small" style="margin:0">Te enviamos un código de 6 dígitos a tu correo. Si no tienes cuenta, se crea sola.</p>
      <input type="email" name="email" placeholder="Correo" autocomplete="email" required>
      <div id="code-step" hidden>
        <input type="text" name="code" inputmode="numeric" autocomplete="one-time-code" pattern="[0-9]{6,8}" maxlength="8" placeholder="Código de 6 dígitos" class="code-input">
      </div>
      <button class="btn primary block" id="code-btn">Enviarme el código</button>
      <p class="small" id="code-msg" style="margin:0" role="status"></p>
    </form>`, (root) => {
    const form = root.querySelector('#code-form');
    const btn = form.querySelector('#code-btn');
    const msg = form.querySelector('#code-msg');
    let sent = false;
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = form.email.value.trim();
      btn.disabled = true;
      try {
        if (!sent) {
          msg.textContent = 'Enviando…';
          await Cloud.sendCode(email);
          sent = true;
          form.querySelector('#code-step').hidden = false;
          form.email.readOnly = true;
          btn.textContent = 'Entrar';
          msg.textContent = `📧 Revisa ${email} (también la carpeta de spam) y escribe el código.`;
          form.code.focus();
        } else {
          msg.textContent = 'Comprobando…';
          await Cloud.verifyCode(email, form.code.value.trim());
          if (onDone) return onDone();
          closeSheet(); document.getElementById('win-save')?.remove();
          toast('Sesión iniciada · sincronizando tus datos'); render();
        }
      } catch (err) {
        msg.textContent = err.message;
      } finally {
        btn.disabled = false;
      }
    });
  }, back);
}

// Aviso único para instalar la app en la pantalla de inicio (iPhone: Safari no lo ofrece solo).
let installEvent = null;
window.addEventListener('beforeinstallprompt', (e) => { e.preventDefault(); installEvent = e; if (ui.tab === 'train') safeRender(); });
function installCardHTML() {
  const standalone = navigator.standalone || matchMedia('(display-mode: standalone)').matches;
  let dismissed = false;
  try { dismissed = Boolean(localStorage.getItem('gymtrack.installDismissed')); } catch {}
  if (standalone || dismissed) return '';
  const ios = /iphone|ipad|ipod/i.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  if (!ios && !installEvent) return '';
  const SHARE = '<svg class="inline-ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3 7.5 7.5l1.4 1.4L11 6.8V15h2V6.8l2.1 2.1 1.4-1.4L12 3ZM5 11v9h14v-9h-3v2h1v5H7v-5h1v-2H5Z"/></svg>';
  return `<div class="card install-card">
    <button class="icon-btn install-x" data-action="install-dismiss" aria-label="Cerrar">${ICON_X}</button>
    <b>Instala la app en tu teléfono</b>
    <p class="muted small">Se abre a pantalla completa, más rápido y funciona sin señal en el gym.</p>
    ${ios ? `<ol class="install-steps small">
      <li>Toca <b>Compartir</b> ${SHARE} en la barra de Safari.</li>
      <li>Elige <b>Añadir a pantalla de inicio</b>.</li>
      <li>Abre la app desde el nuevo ícono.</li></ol>`
      : '<button class="btn primary block" data-action="install-app">Instalar</button>'}
  </div>`;
}

function finishOnboarding() {
  const ob = ui.ob;
  S.setProfile({
    ...(ob.gender ? { gender: ob.gender } : {}),
    level: ob.level,
    days: ob.days,
    simple: ob.fromSettings ? S.isSimple() : ob.level === 'beginner',
    auto: false,
  });
  ui.ob = null;
  ui.editRoutineId = null;
  ui.tab = 'train';
  document.querySelectorAll('.tabbar button').forEach((b) => b.classList.toggle('active', b.dataset.tab === 'train'));
  render();
  window.scrollTo(0, 0);
}

// =====================================================================
// RESUMEN AL TERMINAR
// =====================================================================

// Cuenta: se ofrece tras el 1.er entrenamiento (cuando ya vio que la app le sirve)
// y se recuerda solo un par de veces más, nunca en la configuración inicial.
const askSignup = (session) => Cloud.isConfigured() && !Cloud.getUser() && !session.editedAt
  && [1, 5, 15].includes(S.getState().sessions.length);

// Resumen a pantalla completa al terminar: tiempo, series, volumen, músculos trabajados,
// récords y progreso de la semana.
function showSummary(session) {
  const mins = Math.max(1, Math.round((session.finishedAt - session.startedAt) / 60000));
  const volume = S.sessionVolume(session);
  const prs = [];
  for (const e of session.exercises) for (const x of e.sets) if (x.pr) prs.push({ e, x });

  // Solo se compara si es para bien.
  const prev = S.previousSameDay(session);
  const pv = prev ? S.sessionVolume(prev) : 0;
  const pct = pv ? Math.round(((volume - pv) / pv) * 100) : 0;

  // Semana: días distintos entrenados frente a los días previstos en la rutina.
  const routine = S.activeRoutine();
  const planned = routine ? S.weekPlan(routine).filter(Boolean).length : 0;
  const trained = new Set(weekSessions().map((x) => x.date)).size;
  const goal = Math.max(planned, trained);

  const stat = (icon, value, label) => `<div class="win-stat">${icon}<b>${value}</b><span>${label}</span></div>`;
  const u = S.defaultUnit();
  const exRows = session.exercises.map((e) => {
    const sets = e.sets.filter((x) => x.side !== 'R').length;
    const top = Math.max(...e.sets.map((x) => Number(x.kg) || 0));
    return `<div class="win-ex"><span class="grow">${esc(S.exById(e.exId).name)}${e.sets.some((x) => x.pr) ? ' <span class="win-pr" title="Récord">🏆</span>' : ''}</span>
      <span class="win-ex-val">${sets}${top ? ` × ${wt(top, S.unitFor(e.exId))}` : ` ${sets === 1 ? 'serie' : 'series'}`}</span></div>`;
  }).join('');
  const overlay = document.createElement('div');
  overlay.className = 'celebrate';
  overlay.setAttribute('role', 'dialog');
  overlay.setAttribute('aria-modal', 'true');
  overlay.setAttribute('aria-label', 'Resumen del entrenamiento');
  overlay.innerHTML = `
    <div class="win-glow" aria-hidden="true"></div>
    <div class="win">
      <div class="win-check" aria-hidden="true"><span>${ICON_CHECK}</span></div>
      <h2 class="win-title">Entrenamiento completado</h2>
      <div class="win-sub">${esc(shortName(session.dayName))} · ${S.formatDate(session.date)}</div>
      <div class="win-stats">
        ${stat(ICON_CLOCK, mins >= 60 ? `${Math.floor(mins / 60)} h ${mins % 60} min` : `${mins} min`, 'Tiempo')}
        ${stat(ICON_CHECK, S.doneSets(session), 'Series')}
        ${stat(ICON_BARS, `${groupNum(S.toUnit(volume, u))} ${u}`, 'Volumen')}
      </div>
      ${(pct > 0 && pct <= 200) || prs.length ? `<div class="win-chips">
        ${pct > 0 && pct <= 200 ? `<span class="win-chip up">↑ ${pct}% <small>volumen</small></span>` : ''}
        ${prs.length ? `<span class="win-chip gold">🏆 ${prs.length} <small>${prs.length === 1 ? 'récord' : 'récords'}</small></span>` : ''}
      </div>` : ''}
      <button class="share-cta" data-share aria-label="Compartir entrenamiento">
        <span class="sc-thumb" aria-hidden="true"><img alt=""></span>
        <span class="sc-text"><b>Comparte tu entrenamiento</b><small>Crea una imagen para tus historias</small></span>
        <span class="sc-go" aria-hidden="true">${ICON_SHARE}</span>
      </button>
      ${askSignup(session) ? `<div class="win-save" id="win-save">
        <div class="ws-top"><span class="ws-ico">${ICON_CLOUD}</span>
          <div><b>Guarda tu progreso</b><p>Crea una cuenta gratis y no lo pierdas nunca.</p></div></div>
        <div class="row"><button class="btn primary grow" data-action="win-signup">Crear cuenta</button><button class="btn ghost quiet" data-action="win-signup-later">Ahora no</button></div>
      </div>` : ''}
      <details class="win-exs">
        <summary><span class="grow">Ejercicios</span><span class="muted">${session.exercises.length}</span><span class="acc-chev" aria-hidden="true">⌄</span></summary>
        <div class="win-list">${exRows}</div>
      </details>
      ${goal ? `<div class="win-week"><span class="muted">Esta semana</span>
        <span class="dots">${Array.from({ length: goal }, (_, i) => `<i class="${i < trained ? 'on' : ''}"></i>`).join('')}</span>
        <b>${trained} de ${goal}</b></div>` : ''}
    </div>
    <div class="win-foot"><button class="btn block win-done">Listo</button></div>`;
  document.body.appendChild(overlay);
  document.body.classList.add('no-scroll');
  mountMuscleMaps(overlay);
  const close = () => {
    overlay.remove();
    document.body.classList.remove('no-scroll');
    document.removeEventListener('keydown', onKey);
  };
  const onKey = (e) => { if (e.key === 'Escape') close(); };
  document.addEventListener('keydown', onKey);
  overlay.querySelector('.win-done').addEventListener('click', close);
  overlay.querySelector('[data-share]').addEventListener('click', () => openShare(session));
  // Miniatura real de la historia dentro del botón: invita a compartir.
  renderShare(session, { background: '#15171a', layout: S.getState().settings.shareLayout }).then((c) => {
    const t = document.createElement('canvas');
    t.width = 180; t.height = 320;
    t.getContext('2d').drawImage(c, 0, 0, 180, 320);
    const img = overlay.querySelector('.sc-thumb img');
    if (img) { img.src = t.toDataURL('image/jpeg', 0.85); img.parentElement.classList.add('ready'); }
  }).catch(() => {});
  overlay.querySelector('.win-done').focus({ preventScroll: true });
  overlay.scrollTop = 0;
  if (navigator.vibrate) navigator.vibrate(80);
}

// =====================================================================
// AJUSTES
// =====================================================================

function syncLabel() {
  const { status, error, lastSync } = Cloud.getInfo();
  if (status === 'syncing') return 'Sincronizando…';
  if (status === 'error' || status === 'offline') return `⚠️ ${esc(error)}`;
  if (lastSync) return `✓ Sincronizado a las ${new Date(lastSync).toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' })}`;
  return '';
}

// ---------- Menú de cuenta (botón de perfil) ----------

const menuRow = (action, label, value = '', extra = '') =>
  `<button class="menu-row" data-action="${action}" ${extra}><span class="grow">${label}</span>${value ? `<span class="muted">${value}</span>` : ''}<span class="chev" aria-hidden="true">›</span></button>`;

function updateAvatar() {
  const btn = document.getElementById('profile-btn');
  if (!btn) return;
  const user = Cloud.getUser();
  btn.innerHTML = user
    ? `<span class="avatar">${esc((user.email || '?')[0].toUpperCase())}</span>`
    : `${ICON_PERSON}${Cloud.isConfigured() ? '<span class="dot" aria-hidden="true"></span>' : ''}`;
  btn.setAttribute('aria-label', user ? `Tu cuenta (${user.email})` : 'Tu cuenta y ajustes');
}

function openMenu() {
  const user = Cloud.getUser();
  let top = '';
  if (user) {
    const { status } = Cloud.getInfo();
    top = `<div class="account-head">
        <span class="avatar lg">${esc((user.email || '?')[0].toUpperCase())}</span>
        <div class="grow" style="min-width:0"><b class="ellipsis">${esc(user.email)}</b>
          <div class="muted small" id="sync-status">${syncLabel() || 'Conectado'}</div></div>
        ${status === 'error' || status === 'offline' ? '<button class="btn sm" data-action="cloud-sync">Reintentar</button>' : ''}
      </div>`;
  } else if (Cloud.isConfigured()) {
    top = `<div class="cloud-card">
        <b>Guarda tu progreso en la nube</b>
        <p class="muted small">Para no perder tus entrenamientos y verlos en cualquier dispositivo.</p>
        <button class="btn primary block" data-action="open-login">Iniciar sesión</button>
      </div>`;
  }
  openSheet(user ? 'Tu cuenta' : 'Menú', `${top}
    <div class="menu-list">
      ${menuRow('open-settings', 'Ajustes')}
      ${user ? '' : menuRow('open-backup', 'Respaldo de datos')}
    </div>
    ${user ? '<button class="btn block ghost danger" data-action="cloud-logout">Cerrar sesión</button>' : ''}`);
}

function openLogin(mode = 'login', { back = 'open-menu', onDone } = {}) {
  const login = mode === 'login';
  openSheet(login ? 'Iniciar sesión' : 'Crear cuenta', `
    <form id="login-form" class="stack">
      <input type="email" name="email" placeholder="Correo" autocomplete="email" required>
      <input type="password" name="password" placeholder="Contraseña${login ? '' : ' (mín. 6 caracteres)'}" autocomplete="${login ? 'current-password' : 'new-password'}" minlength="6" required>
      <button class="btn primary block" name="mode" value="${mode}">${login ? 'Entrar' : 'Crear cuenta'}</button>
      <p class="small" id="login-msg" style="margin:0" role="status"></p>
    </form>
    <div class="login-links">
      ${login
        ? `<button class="link" data-action="cloud-reset">¿Olvidaste tu contraseña?</button>
           <p>¿No tienes cuenta? <button class="link" data-action="open-signup">Créala aquí</button></p>`
        : `<p>¿Ya tienes cuenta? <button class="link" data-action="open-login">Inicia sesión</button></p>`}
    </div>`, (root) => bindAccountForm(root, onDone || (() => {
    closeSheet();
    toast('Sesión iniciada · sincronizando tus datos');
    render();
  })), back);
}

const themePref = () => { try { return localStorage.getItem('gymtrack.theme') || 'auto'; } catch { return 'auto'; } };

// Opciones de Ajustes: cada una se elige en su propia pantalla.
const CHOICES = {
  gender: {
    title: 'Cuerpo en la guía', help: 'Se usa en el mapa de músculos de cada ejercicio.',
    options: [['male', 'Hombre'], ['female', 'Mujer']],
    get: () => S.getState().profile?.gender || 'male',
    set: (v) => S.setProfile({ gender: v }),
  },
  unit: {
    title: 'Unidad de peso', help: 'Es la unidad por defecto. Cada ejercicio puede tener la suya (por ejemplo, máquinas en libras) desde su ficha.',
    options: [['kg', 'Kilos (kg)'], ['lb', 'Libras (lb)']],
    get: () => S.defaultUnit(),
    set: (v) => S.setDefaultUnit(v),
  },
  effort: {
    title: 'Esfuerzo por serie', help: 'Cómo anotas lo cerca que quedaste del fallo en cada serie.',
    options: [['RIR', 'RIR · repeticiones en reserva'], ['RPE', 'RPE · esfuerzo del 1 al 10']],
    get: () => S.getState().settings.effort,
    set: (v) => { S.getState().settings.effort = v; S.save(); },
  },
  theme: {
    title: 'Tema',
    options: [['auto', 'Automático (como el teléfono)'], ['light', 'Claro'], ['dark', 'Oscuro']],
    get: themePref,
    set: (v) => { try { localStorage.setItem('gymtrack.theme', v); } catch {} applyTheme(); },
  },
};
const choiceLabel = (key) => {
  const c = CHOICES[key];
  const label = (c.options.find(([v]) => v === c.get()) || c.options[0])[1];
  return key === 'unit' ? c.get() : key === 'effort' ? c.get() : label.replace(/ \(.*\)$/, '');
};

function openSettings() {
  const simple = S.isSimple();
  openSheet('Ajustes', `
    <div class="menu-list">
      ${menuRow('open-choice', 'Cuerpo en la guía', choiceLabel('gender'), 'data-key="gender"')}
      ${menuRow('open-choice', 'Unidad de peso', choiceLabel('unit'), 'data-key="unit"')}
      <button class="menu-row" data-action="toggle-simple" role="switch" aria-checked="${simple}">
        <span class="grow">Modo simple<span class="muted small row-help">Oculta RIR/RPE y las estadísticas avanzadas</span></span>
        <span class="switch ${simple ? 'on' : ''}" aria-hidden="true"></span>
      </button>
      <button class="menu-row" data-action="toggle-rest" role="switch" aria-checked="${S.restEnabled()}">
        <span class="grow">Temporizador de descanso<span class="muted small row-help">Arranca solo al marcar una serie</span></span>
        <span class="switch ${S.restEnabled() ? 'on' : ''}" aria-hidden="true"></span>
      </button>
      ${simple ? '' : menuRow('open-choice', 'Esfuerzo por serie', choiceLabel('effort'), 'data-key="effort"')}
      ${menuRow('open-choice', 'Tema', choiceLabel('theme'), 'data-key="theme"')}
    </div>
    ${Cloud.getUser() ? `<div class="data-links">
      <button class="link" data-action="export">Descargar mis datos</button>
      <button class="link danger" data-action="reset">Borrar todos los datos</button>
    </div>` : ''}`, null, 'open-menu');
}

function openChoice(key) {
  const c = CHOICES[key];
  const current = c.get();
  openSheet(c.title, `
    ${c.help ? `<p class="muted small" style="margin:0 0 8px">${c.help}</p>` : ''}
    <div class="menu-list">${c.options.map(([v, l]) => `<button class="menu-row" data-action="choose" data-key="${key}" data-v="${v}" aria-pressed="${v === current}">
      <span class="grow">${l}</span>${v === current ? '<span class="check-mark" aria-hidden="true">✓</span>' : ''}</button>`).join('')}</div>`, null, 'open-settings');
}

function openBackup() {
  const st = S.getState();
  openSheet('Respaldo de datos', `
    <p class="muted small" style="margin:0 0 10px">${Cloud.getUser()
      ? 'Tus datos ya se guardan en la nube. Aun así puedes descargar una copia.'
      : 'Sin sesión iniciada, tus datos se guardan solo en este teléfono. Descarga una copia de vez en cuando.'}</p>
    <div class="menu-list">
      ${menuRow('export', 'Descargar copia (.json)')}
      <label class="menu-row"><span class="grow">Restaurar desde una copia</span><span class="chev" aria-hidden="true">›</span>
        <input type="file" accept="application/json,.json" id="import-file" hidden></label>
    </div>
    <p class="muted small" style="text-align:center">${st.sessions.length} entrenamientos · ${st.routines.length} rutinas · ${st.body.length} registros corporales</p>
    <button class="btn block ghost danger" data-action="reset">Borrar todos los datos</button>`, (root) => {
    root.querySelector('#import-file').addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      try {
        const data = JSON.parse(await file.text());
        if (!Array.isArray(data.sessions) || !Array.isArray(data.routines)) throw new Error('formato');
        if (!confirm('Esto reemplazará los datos actuales por los de la copia. ¿Continuar?')) return;
        S.replaceState(data);
        S.ensureProfile();
        ui.ob = null;
        closeSheet();
        toast('Copia restaurada');
        render();
      } catch {
        toast('El archivo no es una copia válida');
      }
    });
  }, 'open-menu');
}

function bindAccountForm(root, onDone) {
  const form = root.querySelector('#login-form');
  if (!form) return;
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const f = new FormData(form);
    const mode = e.submitter?.value || 'login';
    const msg = form.querySelector('#login-msg');
    const buttons = form.querySelectorAll('button');
    buttons.forEach((b) => { b.disabled = true; });
    msg.textContent = mode === 'login' ? 'Entrando…' : 'Creando cuenta…';
    try {
      if (mode === 'signup') {
        const needsConfirm = await Cloud.signUp(f.get('email'), f.get('password'));
        if (needsConfirm) {
          msg.textContent = '📧 Te enviamos un correo. Abre el enlace para confirmar tu cuenta y luego inicia sesión desde tu perfil (arriba a la derecha).';
          const next = document.querySelector('[data-action="ob-finish"]');
          if (next) { next.textContent = 'Continuar'; next.classList.add('primary'); next.classList.remove('ghost'); }
          return;
        }
      } else {
        await Cloud.signIn(f.get('email'), f.get('password'));
      }
      if (onDone) return onDone();
      closeSheet();
      toast('Sesión iniciada · sincronizando tus datos');
    } catch (err) {
      msg.textContent = err.message;
    } finally {
      buttons.forEach((b) => { b.disabled = false; });
    }
  });
}

function applyTheme() {
  let t = 'auto';
  try { t = localStorage.getItem('gymtrack.theme') || 'auto'; } catch {}
  if (t === 'auto') delete document.documentElement.dataset.theme;
  else document.documentElement.dataset.theme = t;
}

// =====================================================================
// EVENTOS
// =====================================================================

const actions = {
  'open-menu': openMenu,
  'open-settings': openSettings,
  'open-login': () => openLogin('login'),
  'open-signup': () => openLogin('signup'),
  'open-backup': openBackup,
  'open-choice': (b) => openChoice(b.dataset.key),
  choose: (b) => {
    CHOICES[b.dataset.key].set(b.dataset.v);
    render();
    openSettings();
  },
  'toggle-rest': () => {
    S.getState().settings.restTimer = !S.restEnabled();
    S.save();
    openSettings();
  },
  'toggle-simple': () => {
    S.setProfile({ simple: !S.isSimple() });
    render();
    openSettings();
  },
  'close-sheet': closeSheet,

  // Mi plan
  'plan-row': (b) => openPlanDay(Number(b.dataset.wd)),
  'plan-move': (b) => {
    const r = S.activeRoutine();
    const week = [...S.weekPlan(r)];
    const from = Number(b.dataset.from), to = Number(b.dataset.to);
    [week[from], week[to]] = [week[to], week[from]];
    S.setWeekThisWeek(r, week);
    closeSheet(); toast(`Movido al ${S.DAY_NAMES[to].toLowerCase()}`); render();
  },
  'plan-skip': (b) => {
    const r = S.activeRoutine();
    const week = [...S.weekPlan(r)];
    week[Number(b.dataset.wd)] = null;
    S.setWeekThisWeek(r, week);
    closeSheet(); toast('Día saltado esta semana'); render();
  },
  'plan-set': (b) => {
    const r = S.activeRoutine();
    const week = [...S.weekPlan(r)];
    const wd = Number(b.dataset.wd), from = Number(b.dataset.from);
    if (from >= 0) week[from] = null;
    week[wd] = b.dataset.id;
    S.setWeekThisWeek(r, week);
    closeSheet(); render();
  },
  'plan-go': (b) => { ui.planDay = b.dataset.id; setTab('train'); },
  'plan-reset': () => { S.resetWeek(S.activeRoutine()); toast('Plan original restaurado'); render(); },

  // Entrenar
  start: (b) => {
    const r = S.activeRoutine();
    S.startDraft(r, r.days.find((d) => d.id === b.dataset.day));
    render(); window.scrollTo(0, 0);
  },
  'start-free': () => { S.startDraft(null, null); render(); window.scrollTo(0, 0); },
  'toggle-set': (b) => {
    const d = S.getState().draft;
    const i = Number(b.dataset.i), j = Number(b.dataset.j);
    const s = d.exercises[i].sets[j];
    if (s.done) {
      s.done = false;
      delete s.pr;
    } else if (!markSet(i, j)) {
      document.querySelector(`[data-set="reps"][data-i="${i}"][data-j="${j}"]`)?.focus();
      return toast('Anota las repeticiones');
    } else if (!(s.side === 'L' && d.exercises[i].sets[j + 1]?.side === 'R')) {
      // En ejercicios por lado, el descanso empieza tras el lado derecho.
      startRest(d.exercises[i]);
    }
    afterMarking(Boolean(s.pr));
  },
  'log-all': () => {
    const d = S.getState().draft;
    const i = d.current;
    let anyPr = false;
    for (const [j, s] of d.exercises[i].sets.entries()) {
      if (s.done) continue;
      if (!markSet(i, j)) {
        afterMarking(anyPr);
        document.querySelector(`[data-set="reps"][data-i="${i}"][data-j="${j}"]`)?.focus();
        return toast(`Anota las repeticiones de la serie ${j + 1}`);
      }
      anyPr = anyPr || Boolean(s.pr);
    }
    afterMarking(anyPr);
  },
  'go-ex': (b) => goToExercise(Number(b.dataset.i)),
  'rest-adj': (b) => {
    const d = S.getState().draft;
    if (!d?.rest) return;
    const delta = Number(b.dataset.s);
    const left = Math.max(0, Math.ceil((d.rest.end - Date.now()) / 1000));
    if (left + delta <= 0) return actions['rest-skip']();
    d.rest.end += delta * 1000;
    d.rest.total = Math.max(15, d.rest.total + delta);
    S.setRestFor(d.rest.exId, d.rest.total); // se recuerda para la próxima vez
    restTick(d);
  },
  'rest-skip': () => {
    const d = S.getState().draft;
    if (!d) return;
    d.rest = null;
    S.save();
    document.getElementById('rest-bar')?.remove();
  },
  // Menú de una serie (modo avanzado): convertir entre efectiva y aproximación, o eliminar.
  'set-menu': (b) => {
    const { kind, i, j } = b.dataset;
    const e = S.getState().draft.exercises[i];
    const perSide = e.sets.some((x) => x.side);
    const n = kind === 'warm' ? `Aproximación ${Number(j) + 1}` : `Serie ${perSide ? Math.floor(j / 2) + 1 : Number(j) + 1}`;
    const canDelete = kind === 'warm' || e.sets.length > (perSide ? 2 : 1);
    openSheet(n, `
      <div class="menu-list">
        ${kind === 'set'
          ? `<button class="menu-row" data-action="set-to-warm" data-i="${i}" data-j="${j}"><span class="grow">Convertir en serie de aproximación<span class="muted small row-help">No contará en volumen, récords ni progresión</span></span></button>`
          : `<button class="menu-row" data-action="warm-to-set" data-i="${i}" data-j="${j}"><span class="grow">Convertir en serie efectiva<span class="muted small row-help">Contará en tus estadísticas</span></span></button>`}
        ${canDelete ? `<button class="menu-row danger-row" data-action="set-delete" data-kind="${kind}" data-i="${i}" data-j="${j}"><span class="grow">Eliminar ${perSide && kind === 'set' ? 'serie (ambos lados)' : 'serie'}</span></button>` : ''}
      </div>`);
  },
  'set-to-warm': (b) => {
    const e = S.getState().draft.exercises[b.dataset.i];
    let j = Number(b.dataset.j);
    const perSide = e.sets.some((x) => x.side);
    if (perSide) j -= j % 2; // en ejercicios por lado se mueve la pareja
    const d = S.getState().draft;
    const sug = setSuggestion(e, j, S.lastPerformance(e.exId, d.editing ? d.id : null));
    const [first] = e.sets.splice(j, perSide ? 2 : 1);
    if (first.reps === '') first.reps = sug.reps;
    if (first.kg === '') first.kg = sug.kg;
    if (!e.sets.length) return toast('Debe quedar al menos una serie efectiva');
    const { side, pr, kgTouched, effort, ...w } = first;
    e.warmupOn = true;
    e.warmup = [...(e.warmup || []), { kg: w.kg, reps: w.reps, done: Boolean(w.done) }];
    closeSheet(); S.save(); const y = window.scrollY; render(); window.scrollTo(0, y);
    toast('Serie marcada como aproximación');
  },
  'warm-to-set': (b) => {
    const e = S.getState().draft.exercises[b.dataset.i];
    const [w] = e.warmup.splice(Number(b.dataset.j), 1);
    if (!e.warmup.length) e.warmupOn = false;
    const base = { kg: w.kg, reps: w.reps, effort: '', done: Boolean(w.done) };
    const rows = e.sets.some((x) => x.side) ? [{ ...base, side: 'L' }, { ...base, side: 'R' }] : [base];
    e.sets.unshift(...rows);
    closeSheet(); S.save(); const y = window.scrollY; render(); window.scrollTo(0, y);
    toast('Ahora es una serie efectiva');
  },
  'set-delete': (b) => {
    const e = S.getState().draft.exercises[b.dataset.i];
    let j = Number(b.dataset.j);
    if (b.dataset.kind === 'warm') {
      e.warmup.splice(j, 1);
      if (!e.warmup.length) e.warmupOn = false;
    } else {
      const perSide = e.sets.some((x) => x.side);
      if (perSide) j -= j % 2;
      e.sets.splice(j, perSide ? 2 : 1);
    }
    closeSheet(); S.save(); const y = window.scrollY; render(); window.scrollTo(0, y);
  },
  'warm-toggle': (b) => {
    const d = S.getState().draft;
    const e = d.exercises[b.dataset.i];
    e.warmupOn = !e.warmupOn;
    if (e.warmupOn && !(e.warmup || []).length) {
      const last = S.lastPerformance(e.exId, d.editing ? d.id : null);
      const work = e.sets.find((x) => x.kg !== '')?.kg || setSuggestion(e, 0, last).kg;
      e.warmup = S.suggestWarmup(e.exId, work);
    }
    S.save(); const y = window.scrollY; render(); window.scrollTo(0, y);
  },
  'toggle-warm': (b) => {
    const e = S.getState().draft.exercises[b.dataset.i];
    const w = e.warmup[b.dataset.j];
    if (!w.done && (w.reps === '' || w.reps === 0)) {
      document.querySelector(`[data-warm="reps"][data-i="${b.dataset.i}"][data-j="${b.dataset.j}"]`)?.focus();
      return toast('Anota las repeticiones');
    }
    if (w.kg === '') w.kg = 0;
    w.done = !w.done;
    S.save(); const y = window.scrollY; render(); window.scrollTo(0, y);
  },
  'warm-add': (b) => {
    const e = S.getState().draft.exercises[b.dataset.i];
    const prev = e.warmup[e.warmup.length - 1];
    e.warmup.push({ kg: prev ? prev.kg : '', reps: prev ? prev.reps : 5, done: false });
    S.save(); const y = window.scrollY; render(); window.scrollTo(0, y);
  },
  'warm-remove': (b) => {
    const e = S.getState().draft.exercises[b.dataset.i];
    e.warmup.pop();
    if (!e.warmup.length) e.warmupOn = false;
    S.save(); const y = window.scrollY; render(); window.scrollTo(0, y);
  },
  'ex-menu': (b) => {
    const i = Number(b.dataset.i);
    const d = S.getState().draft;
    const ex = S.exById(d.exercises[i].exId);
    openSheet(ex.name, `
      <div class="menu-list">
        <button class="menu-row" data-action="ex-detail" data-id="${ex.id}"><span class="grow">Ver músculos y técnica</span><span class="chev" aria-hidden="true">›</span></button>
        ${i > 0 ? `<button class="menu-row" data-action="ex-move" data-i="${i}" data-dir="-1"><span class="grow">Mover antes</span></button>` : ''}
        ${i < d.exercises.length - 1 ? `<button class="menu-row" data-action="ex-move" data-i="${i}" data-dir="1"><span class="grow">Mover después</span></button>` : ''}
        <button class="menu-row danger-row" data-action="ex-remove" data-i="${i}"><span class="grow">Quitar del entrenamiento</span></button>
      </div>`);
  },
  'ex-move': (b) => {
    const d = S.getState().draft;
    const i = Number(b.dataset.i), k = i + Number(b.dataset.dir);
    [d.exercises[i], d.exercises[k]] = [d.exercises[k], d.exercises[i]];
    d.current = k;
    ui.openNotes.clear();
    closeSheet(); S.save(); render();
  },
  'add-set': (b) => {
    const e = S.getState().draft.exercises[b.dataset.i];
    const sides = e.sets.some((x) => x.side) ? ['L', 'R'] : [null];
    for (const side of sides) {
      const prev = [...e.sets].reverse().find((x) => (x.side || null) === side);
      e.sets.push({ kg: prev ? prev.kg : '', reps: '', effort: '', done: false, ...(side ? { side } : {}) });
    }
    S.save(); const y = window.scrollY; render(); window.scrollTo(0, y);
  },
  'remove-set': (b) => {
    const e = S.getState().draft.exercises[b.dataset.i];
    e.sets.splice(e.sets.some((x) => x.side) ? -2 : -1);
    S.save(); const y = window.scrollY; render(); window.scrollTo(0, y);
  },
  'uni-toggle': (b) => {
    const e = S.getState().draft.exercises[b.dataset.i];
    const on = !e.sets.some((x) => x.side);
    S.convertSides(e, on);
    S.setUnilateral(e.exId, on);
    toast(on ? 'Registrarás cada lado por separado' : 'Series normales (ambos lados juntos)');
    const y = window.scrollY; render(); window.scrollTo(0, y);
  },
  'ex-remove': (b) => {
    const d = S.getState().draft;
    const e = d.exercises[b.dataset.i];
    if (e.sets.some((s) => s.done) && !confirm('¿Quitar este ejercicio y sus series hechas?')) return;
    d.exercises.splice(b.dataset.i, 1);
    d.current = Math.min(Number(b.dataset.i), d.exercises.length - 1);
    ui.openNotes.clear(); closeSheet(); S.save(); render();
  },
  'session-add-ex': () => openPicker((id) => {
    const d = S.getState().draft;
    d.exercises.push(S.draftExercise(id, 3, ''));
    d.current = d.exercises.length - 1;
    S.save(); render(); window.scrollTo(0, 0);
  }),
  finish: () => {
    const d = S.getState().draft;
    const n = S.doneSets(d);
    if (!n) {
      if (confirm('No has marcado ninguna serie como hecha. ¿Descartar el entrenamiento?')) { S.getState().draft = null; S.save(); render(); }
      return;
    }
    const pending = d.exercises.reduce((a, e) => a + e.sets.filter((s) => !s.done).length, 0);
    if (pending && !confirm(`Tienes ${series(pending)} sin marcar; no se guardarán. ¿${d.editing ? 'Guardar' : 'Terminar'} igual?`)) return;
    const editing = d.editing;
    const saved = S.finishDraft();
    ui.openNotes.clear();
    render(); window.scrollTo(0, 0);
    if (editing) toast('Cambios guardados');
    else showSummary(saved);
  },
  'session-menu': () => {
    const d = S.getState().draft;
    openSheet(d.editing ? 'Editando entrenamiento' : 'Entrenamiento en curso', `
      <div class="menu-list">
        <button class="menu-row" data-action="session-add-ex-menu"><span class="grow">Añadir ejercicio</span><span class="chev" aria-hidden="true">›</span></button>
        <button class="menu-row danger-row" data-action="discard"><span class="grow">${d.editing ? 'Cancelar edición' : 'Descartar entrenamiento'}</span></button>
      </div>
      ${d.editing ? '' : '<p class="muted small" style="margin:0">Al descartar se pierde lo anotado en esta sesión.</p>'}`);
  },
  'session-add-ex-menu': () => { closeSheet(); actions['session-add-ex'](); },
  discard: () => {
    const d = S.getState().draft;
    if (!d.editing && !confirm('¿Descartar este entrenamiento? Se perderá lo anotado.')) return;
    S.getState().draft = null; S.save(); ui.openNotes.clear(); closeSheet(); render(); window.scrollTo(0, 0);
  },
  'edit-session': (b) => {
    if (S.getState().draft) return toast('Termina o descarta el entrenamiento en curso primero');
    S.editSession(b.dataset.id);
    closeSheet(); setTab('train');
  },
  'note-open': (b) => {
    const i = Number(b.dataset.i);
    const e = S.getState().draft.exercises[i];
    const y = window.scrollY;
    if (ui.openNotes.has(i) && !e.note) { ui.openNotes.delete(i); render(); window.scrollTo(0, y); return; }
    ui.openNotes.add(i); render(); window.scrollTo(0, y);
    document.querySelector(`[data-note="${i}"]`)?.focus({ preventScroll: true });
  },
  'plan-day': (b) => { ui.planDay = b.dataset.id; render(); },
  'set-gender': (b) => {
    S.setProfile({ gender: b.dataset.v });
    closeSheet(); render();
    toast(`Guía muscular con cuerpo de ${b.dataset.v === 'female' ? 'mujer' : 'hombre'}`);
  },
  'ex-unit': (b) => {
    S.setExerciseUnit(b.dataset.id, b.dataset.u);
    if ($sheet.open && document.querySelector('#sheet [data-action="ex-tab"]')) showExerciseDetail(b.dataset.id);
    const scroll = window.scrollY;
    render(); window.scrollTo(0, scroll);
  },
  'ex-tab': (b) => showExerciseDetail(b.dataset.id, b.dataset.tab),
  'ex-metric': (b) => { ui.exMetric = b.dataset.m; showExerciseDetail(b.dataset.id, 'charts'); },
  'session-detail': (b) => {
    const s = S.getState().sessions.find((x) => x.id === b.dataset.id);
    if (!s) return;
    const mins = s.finishedAt ? Math.round((s.finishedAt - s.startedAt) / 60000) : null;
    openSheet(s.dayName, `
      <p class="muted small" style="margin-top:0">${S.formatDate(s.date)}${mins ? ` · ${mins} min` : ''} · ${series(S.doneSets(s))} · ${vol(S.sessionVolume(s))}</p>
      ${s.exercises.map((e) => `<div style="margin-bottom:10px"><b class="small">${esc(S.exById(e.exId).name)}</b> <span class="muted small">(${S.unitFor(e.exId)})</span>
        <div class="muted small">${e.sets.map((x) => `${x.pr ? '🏆' : ''}${sideTag(x)}${wn(x.kg, S.unitFor(e.exId))}×${x.reps}${x.effort !== '' && x.effort !== undefined ? ` @${x.effort}` : ''}`).join(' · ')}</div>
        ${e.warmup?.length ? `<div class="muted small">Aproximación: ${e.warmup.map((w) => `${wn(w.kg, S.unitFor(e.exId))}×${w.reps}`).join(' · ')}</div>` : ''}
        ${e.note ? `<div class="muted small">📝 ${esc(e.note)}</div>` : ''}</div>`).join('')}
      <div class="stack">
        <button class="btn block" data-action="edit-session" data-id="${s.id}">Editar entrenamiento</button>
        <button class="btn block ghost danger" data-action="delete-session" data-id="${s.id}">Eliminar entrenamiento</button>
      </div>`);
  },
  'delete-session': (b) => {
    if (!confirm('¿Eliminar este entrenamiento del historial?')) return;
    S.deleteSession(b.dataset.id); closeSheet(); render();
  },

  // Configuración inicial
  'ob-go': (b) => {
    const step = b.dataset.step;
    // Al volver desde la revisión se descarta la rutina recién creada.
    if (ui.ob.step === 'review' && step === 'choose' && ui.ob.routineId) {
      S.deleteRoutine(ui.ob.routineId);
      if (ui.ob.prevActive) { S.getState().activeRoutineId = ui.ob.prevActive; S.save(); }
      ui.ob.routineId = null;
      ui.editRoutineId = null;
    }
    ui.ob.step = step;
    render(); window.scrollTo(0, 0);
  },
  'ob-cancel': () => { ui.ob = null; ui.editRoutineId = null; render(); window.scrollTo(0, 0); },
  'ob-gender': (b) => { ui.ob.gender = b.dataset.v; render(); },
  'ob-level': (b) => {
    if (!ui.ob.fromSettings && !S.getState().profile?.gender && !ui.ob.gender) return toast('Elige primero hombre o mujer');
    ui.ob.level = b.dataset.v;
    ui.ob.step = 'days';
    render(); window.scrollTo(0, 0);
  },
  'ob-day': (b) => {
    const d = Number(b.dataset.d);
    const days = ui.ob.days;
    ui.ob.days = days.includes(d) ? days.filter((x) => x !== d) : [...days, d].sort((a, c) => a - c);
    render();
  },
  'ob-show-all': () => { ui.ob.showAll = true; render(); window.scrollTo(0, 0); },
  'ob-sel': (b) => { ui.ob.sel = b.dataset.key; render(); },
  'ob-pick': (b) => {
    closeSheet();
    const key = b.dataset.key;
    const st = S.getState();
    ui.ob.prevActive = st.activeRoutineId;
    // La rutina de ejemplo de versiones anteriores ya no hace falta.
    st.routines.filter((r) => r.seeded).forEach((r) => S.deleteRoutine(r.id));
    const r = key === 'custom'
      ? S.routineForDays(ui.ob.days)
      : S.routineFromTemplate(S.templateByKey(key), ui.ob.days);
    S.addRoutine(r, true);
    ui.ob.routineId = r.id;
    if (key !== 'custom') return actions['ob-review-done']();
    ui.ob.step = 'review';
    render(); window.scrollTo(0, 0);
  },
  'ob-activate': (b) => {
    S.getState().activeRoutineId = b.dataset.id;
    S.save();
    toast('Rutina activada');
    finishOnboarding();
  },
  'ob-review-done': () => {
    const r = S.routineById(ui.ob.routineId);
    if (r.days.every((d) => !d.exercises.length)) return toast('Añade al menos un ejercicio a tu rutina');
    if (!r.week.some(Boolean)) return toast('Asigna al menos un día de la semana a tu rutina');
    toast(ui.ob.fromSettings ? 'Rutina actualizada' : '¡Listo! Tu rutina te espera en Entrenar');
    finishOnboarding();
  },
  'install-dismiss': () => { try { localStorage.setItem('gymtrack.installDismissed', '1'); } catch {} render(); },
  'install-app': async () => {
    if (!installEvent) return;
    installEvent.prompt();
    await installEvent.userChoice.catch(() => {});
    installEvent = null;
    render();
  },
  'go-train': () => setTab('train'),
  'win-signup': () => openLogin('signup', { back: null, onDone: () => {
    closeSheet();
    document.getElementById('win-save')?.remove();
    toast('✅ Cuenta creada · tus entrenamientos ya están en la nube');
    render();
  } }),
  'win-signup-later': () => document.getElementById('win-save')?.remove(),
  'code-login': () => openCodeLogin(ui.ob ? obLoggedIn : null),
  'ob-finish': () => {
    toast('¡Listo! Tu rutina te espera en Entrenar');
    finishOnboarding();
  },
  'change-routine': () => {
    closeSheet();
    const pr = S.getState().profile || {};
    ui.editRoutineId = null;
    ui.ob = { step: 'experience', level: pr.level, days: pr.days?.length ? [...pr.days] : [], fromSettings: true };
    render(); window.scrollTo(0, 0);
  },

  // Rutinas
  'preview-template': (b) => {
    const tpl = TEMPLATES.find((t) => t.key === b.dataset.key);
    openSheet(tpl.name, `${tpl.days.map((d) => `<div style="margin-bottom:14px"><b>${esc(d.name)}</b>
      <div class="list small">${d.exercises.map((e) => `<div class="list-item" style="padding:6px 0"><span class="grow">${esc(S.exById(e.exId).name)}</span><span class="muted">${e.sets} × ${esc(e.reps)}</span></div>`).join('')}</div></div>`).join('')}
      <p class="muted small">Los días se repartirán entre los días que elegiste; podrás cambiarlos en el siguiente paso.</p>
      <button class="btn primary block" data-action="ob-pick" data-key="${tpl.key}">Elegir esta rutina</button>`);
  },
  'edit-routine': (b) => { ui.editRoutineId = b.dataset.id; render(); window.scrollTo(0, 0); },
  'close-editor': () => { ui.editRoutineId = null; toast('Rutina guardada'); render(); window.scrollTo(0, 0); },
  'day-add': () => {
    const r = S.routineById(ui.editRoutineId);
    r.days.push({ id: S.uid(), name: `Día ${r.days.length + 1}`, exercises: [] });
    S.save(); render();
  },
  'day-remove': (b) => {
    const r = S.routineById(ui.editRoutineId);
    const d = r.days[b.dataset.di];
    if (d.exercises.length && !confirm(`¿Eliminar “${d.name}”?`)) return;
    r.days.splice(b.dataset.di, 1);
    r.week = r.week.map((id) => (id === d.id ? null : id));
    S.save(); render();
  },
  'day-add-ex': (b) => {
    const r = S.routineById(ui.editRoutineId);
    const d = r.days[b.dataset.di];
    openPicker((id) => { d.exercises.push({ exId: id, sets: 3, reps: '8-12' }); S.save(); render(); });
  },
  'rex-up': (b) => moveRoutineEx(b, -1),
  'rex-down': (b) => moveRoutineEx(b, 1),
  'rex-remove': (b) => {
    const r = S.routineById(ui.editRoutineId);
    r.days[b.dataset.di].exercises.splice(b.dataset.ei, 1); S.save(); render();
  },

  // Ejercicios
  'ex-detail': (b) => showExerciseDetail(b.dataset.id, 'about'),
  'add-ex-to-day': (b) => {
    const r = S.activeRoutine();
    const d = r.days.find((x) => x.id === b.dataset.day);
    d.exercises.push({ exId: b.dataset.ex, sets: 3, reps: '8-12' });
    S.save(); closeSheet();
    toast(`Añadido a ${d.name}`);
  },

  // Progreso
  range: (b) => { ui.range = b.dataset.r; render(); },
  'ex-metric-p': (b) => { ui.exMetricP = b.dataset.m; render(); },
  'ex-show-all': () => { ui.exShowAll = !ui.exShowAll; render(); },
  'muscle-info': () => openSheet('Músculos', `<p style="margin-top:0">Cada barra suma las <b>series</b> que hiciste en el periodo para ese grupo.</p>
    <p><span class="mb-key"></span> <b>Sólido:</b> el grupo es el músculo principal del ejercicio.</p>
    <p><span class="mb-key indirect"></span> <b>Rayado:</b> trabaja como secundario (cuenta como media serie).</p>`),
  'history-more': () => { ui.historyLimit += 20; render(); },
  'body-field': (b) => { ui.bodyField = b.dataset.f; render(); },
  'body-add': () => bodyForm(),
  'body-edit': (b) => bodyForm(b.dataset.date),
  'body-delete': (b) => {
    if (!confirm('¿Eliminar este registro?')) return;
    S.deleteBody(b.dataset.date); closeSheet(); render();
  },

  // Ajustes
  'cloud-sync': () => Cloud.sync(),
  // Al cerrar sesión se vacía el dispositivo para que otra cuenta no mezcle datos; todo sigue en la nube.
  'cloud-logout': async () => {
    const inSession = Boolean(S.getState().draft);
    if (!confirm(`¿Cerrar sesión? Tus datos seguirán guardados en la nube y volverán al entrar.${inSession ? ' El entrenamiento en curso se descartará.' : ''}`)) return;
    await Cloud.sync();
    if (Cloud.getInfo().status !== 'ok'
      && !confirm('No se pudo guardar en la nube. Si cierras sesión ahora perderás los cambios que no se hayan subido. ¿Cerrar sesión igualmente?')) return;
    await Cloud.signOut();
    S.clearLocal();
    ui.ob = null; ui.editRoutineId = null; ui.tab = 'train';
    closeSheet(); updateAvatar(); render(); window.scrollTo(0, 0);
    toast('Sesión cerrada');
  },
  'cloud-reset': async () => {
    const email = document.querySelector('#login-form [name="email"]').value;
    if (!email) return toast('Escribe primero tu correo');
    try { await Cloud.resetPassword(email); toast('Te enviamos un correo para cambiar la contraseña'); }
    catch (err) { toast(err.message); }
  },
  export: () => {
    const blob = new Blob([JSON.stringify(S.getState(), null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `gym-tracker-respaldo-${S.todayISO()}.json`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  },
  reset: () => {
    if (!confirm('¿Borrar TODOS tus datos? Esta acción no se puede deshacer.')) return;
    S.resetState(); ui.ob = null; ui.editRoutineId = null; closeSheet(); render();
  },
};

function moveRoutineEx(b, dir) {
  const r = S.routineById(ui.editRoutineId);
  const list = r.days[b.dataset.di].exercises;
  const i = Number(b.dataset.ei), j = i + dir;
  if (j < 0 || j >= list.length) return;
  [list[i], list[j]] = [list[j], list[i]];
  S.save(); render();
}

document.addEventListener('click', (e) => {
  const tab = e.target.closest('.tabbar [data-tab]');
  if (tab) return setTab(tab.dataset.tab);
  const b = e.target.closest('[data-action]');
  if (!b) return;
  actions[b.dataset.action]?.(b);
});

document.addEventListener('input', (e) => {
  const t = e.target;
  if (t.dataset.note !== undefined) {
    S.getState().draft.exercises[t.dataset.note].note = t.value;
    S.save();
    return;
  }
  if (t.dataset.draft === 'date') {
    if (t.value) { S.getState().draft.date = t.value; S.save(); }
    return;
  }
  if (t.dataset.warm) {
    const ex = S.getState().draft.exercises[t.dataset.i];
    const w = ex.warmup[t.dataset.j];
    w[t.dataset.warm] = t.dataset.warm === 'kg' ? S.fromUnit(num(t.value), S.unitFor(ex.exId)) : num(t.value);
    S.save();
    return;
  }
  if (t.dataset.set) {
    const ex = S.getState().draft.exercises[t.dataset.i];
    const s = ex.sets[t.dataset.j];
    s[t.dataset.set] = t.dataset.set === 'kg' ? S.fromUnit(num(t.value), S.unitFor(ex.exId)) : num(t.value);
    if (t.dataset.set === 'kg') s.kgTouched = true;
    S.save();
    if (s.done) updateLiveStats();
    return;
  }
  const r = S.routineById(ui.editRoutineId);
  if (!r) return;
  if (t.dataset.rfield) r.name = t.value;
  if (t.dataset.dfield) {
    // Actualiza los selectores de la semana sin redibujar, para no cerrar el teclado.
    const day = r.days[t.dataset.di];
    day.name = t.value;
    document.querySelectorAll(`[data-rweek] option[value="${day.id}"]`).forEach((o) => { o.textContent = t.value; });
  }
  if (t.dataset.efield) {
    const ex = r.days[t.dataset.di].exercises[t.dataset.ei];
    ex[t.dataset.efield] = t.dataset.efield === 'sets' ? Math.max(1, Math.min(20, Number(t.value) || 1)) : t.value;
  }
  S.save();
});

document.addEventListener('change', (e) => {
  const t = e.target;
  if (t.dataset.rweek !== undefined) {
    const r = S.routineById(ui.editRoutineId);
    r.week[t.dataset.rweek] = t.value || null;
    delete r.weekOverride;
    S.save();
  }
});

// Vuelve a dibujar los gráficos si cambia el tema del sistema.
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => safeRender());

// ---------- Inicio ----------

applyTheme();
S.ensureProfile();
importFromLink();
render();

// Enlace personal ?importar=excel: añade la rutina del Excel con sus últimos pesos al historial.
function importFromLink() {
  const params = new URLSearchParams(location.search);
  if (params.get('importar') !== 'excel') return;
  history.replaceState(null, '', location.pathname);
  const tpl = S.templateByKey('excel-4-dias');
  const st = S.getState();
  if (st.importedHistory?.includes(tpl.key) || st.sessions.some((x) => x.imported)) {
    return setTimeout(() => toast('Tus datos del Excel ya estaban importados'), 300);
  }
  let r = st.routines.find((x) => x.fromTemplate === tpl.key);
  if (!r) {
    st.routines.filter((x) => x.seeded).forEach((x) => S.deleteRoutine(x.id));
    r = S.addRoutine(S.routineFromTemplate(tpl), true);
  }
  const n = S.importTemplateHistory(tpl, r);
  if (!st.profile) S.setProfile({ level: 'advanced', days: tpl.week.flatMap((v, i) => (v === null ? [] : [i])), simple: false });
  setTimeout(() => toast(`Excel importado: ${n} entrenamientos y la rutina “${r.name}”`), 300);
}

// Cuando llegan datos de otro dispositivo, redibuja salvo que el usuario esté escribiendo.
let pendingRender = false;
function safeRender() {
  const typing = document.activeElement?.matches?.('input, textarea, select');
  if ($sheet.open || typing || (ui.tab === 'train' && S.getState().draft)) { pendingRender = true; return; }
  pendingRender = false;
  render();
}
$sheet.addEventListener('close', () => { if (pendingRender) safeRender(); });
let lastUserId;
updateAvatar();
Cloud.onChange(() => {
  updateAvatar();
  const el = document.getElementById('sync-status');
  if (el) el.innerHTML = syncLabel();
  const id = Cloud.getUser()?.id;
  if (id !== lastUserId) { lastUserId = id; safeRender(); }
});
Cloud.initCloud({ onData: safeRender });

// Actualizaciones: al publicar una versión nueva, el service worker nuevo toma el control
// y la app se recarga sola (el entrenamiento en curso está guardado y no se pierde).
if ('serviceWorker' in navigator && location.protocol === 'https:') {
  const hadController = Boolean(navigator.serviceWorker.controller);
  let reloading = false;
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (!hadController || reloading) return;
    reloading = true;
    try { sessionStorage.setItem('gymtrack.updated', '1'); } catch {}
    location.reload();
  });
  navigator.serviceWorker.register('sw.js', { updateViaCache: 'none' }).then((reg) => {
    document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') reg.update().catch(() => {}); });
  }).catch(() => {});
  try {
    if (sessionStorage.getItem('gymtrack.updated')) {
      sessionStorage.removeItem('gymtrack.updated');
      setTimeout(() => toast('✨ App actualizada a la última versión'), 400);
    }
  } catch {}
}
