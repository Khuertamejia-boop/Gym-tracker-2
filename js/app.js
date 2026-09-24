import * as S from './store.js';
import { MUSCLES } from './data/exercises.js';
import { TEMPLATES } from './data/templates.js';
import { barChart, lineChart, destroyCharts } from './charts.js';
import * as Cloud from './cloud.js';

const $view = document.getElementById('view');
const $title = document.getElementById('view-title');
const $sheet = document.getElementById('sheet');
const $toast = document.getElementById('toast');

const ui = {
  tab: 'train',
  editRoutineId: null,
  exQuery: '',
  exMuscle: '',
  period: 'week', // 'week' | 'month'
  muscleMetric: 'sets', // 'sets' | 'volume'
  bodyField: 'weight',
  openNotes: new Set(),
  exTab: 'about',
  exMetric: 'e1rm',
};

const TITLES = { train: 'Entrenar', routines: 'Rutinas', exercises: 'Ejercicios', progress: 'Progreso' };

// ---------- Utilidades ----------

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const kg = (v) => `${Math.round(v).toLocaleString('es')} kg`;
const num = (v) => (v === '' || v === null || v === undefined ? '' : Number(v));
const fmtN = (v, d = 1) => Number(v).toLocaleString('es', { maximumFractionDigits: d });

const ICON_CHECK = '<svg viewBox="0 0 24 24"><path d="M9 16.2 4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2Z"/></svg>';
const ICON_X = '<svg viewBox="0 0 24 24"><path d="M19 6.4 17.6 5 12 10.6 6.4 5 5 6.4 10.6 12 5 17.6 6.4 19 12 13.4 17.6 19 19 17.6 13.4 12 19 6.4Z"/></svg>';
const ICON_UP = '<svg viewBox="0 0 24 24"><path d="m7 14 5-5 5 5H7Z"/></svg>';
const ICON_DOWN = '<svg viewBox="0 0 24 24"><path d="m7 10 5 5 5-5H7Z"/></svg>';

function toast(msg) {
  $toast.textContent = msg;
  $toast.classList.add('show');
  clearTimeout(toast.t);
  toast.t = setTimeout(() => $toast.classList.remove('show'), 2200);
}

function openSheet(title, body, onMount) {
  $sheet.innerHTML = `
    <div class="sheet-inner">
      <div class="sheet-head"><h2>${esc(title)}</h2>
        <button class="icon-btn" data-action="close-sheet" aria-label="Cerrar">${ICON_X}</button>
      </div>
      <div class="sheet-body">${body}</div>
    </div>`;
  $sheet.onclick = null;
  if (!$sheet.open) $sheet.showModal();
  onMount?.($sheet);
}
const closeSheet = () => $sheet.open && $sheet.close();
$sheet.addEventListener('click', (e) => { if (e.target === $sheet) closeSheet(); });

// ---------- Navegación ----------

function setTab(tab) {
  ui.tab = tab;
  if (tab !== 'routines') ui.editRoutineId = null;
  document.querySelectorAll('.tabbar button').forEach((b) => b.classList.toggle('active', b.dataset.tab === tab));
  render();
  window.scrollTo(0, 0);
}

function render() {
  destroyCharts();
  clearInterval(render.timer);
  $title.textContent = TITLES[ui.tab];
  const views = { train: renderTrain, routines: renderRoutines, exercises: renderExercises, progress: renderProgress };
  views[ui.tab]();
}

// =====================================================================
// ENTRENAR
// =====================================================================

function renderTrain() {
  const st = S.getState();
  if (st.draft) return renderSession();

  const routine = S.activeRoutine();
  const wd = S.weekdayIndex();
  const todayDay = routine ? routine.days.find((d) => d.id === routine.week[wd]) : null;
  const doneToday = st.sessions.some((s) => s.date === S.todayISO());

  let html = '';
  if (Cloud.isConfigured() && !Cloud.getUser()) {
    html += `<button class="card banner" data-action="open-settings">☁️ <span class="grow"><b>Inicia sesión</b> para guardar tus datos en la nube y no perderlos.</span> ›</button>`;
  }
  if (!routine) {
    html += `<div class="card empty"><p>Aún no tienes una rutina activa.</p>
      <button class="btn primary" data-action="goto" data-tab="routines">Elegir rutina</button></div>`;
  } else {
    html += `<div class="card">
      <div class="muted small">${S.DAY_NAMES[wd]} · ${esc(routine.name)}</div>
      ${todayDay
        ? `<h2 style="font-size:1.35rem;margin:2px 0 6px">${esc(todayDay.name)}</h2>
           <p class="muted small" style="margin:0 0 12px">${todayDay.exercises.length} ejercicios · ${todayDay.exercises.map((e) => esc(S.exById(e.exId).name)).slice(0, 3).join(', ')}${todayDay.exercises.length > 3 ? '…' : ''}</p>
           <button class="btn primary block" data-action="start" data-day="${todayDay.id}">${doneToday ? 'Entrenar otra vez' : 'Empezar entrenamiento'}</button>`
        : `<h2 style="font-size:1.35rem;margin:2px 0 6px">Hoy toca descanso</h2>
           <p class="muted small" style="margin:0">Recupérate. Si quieres entrenar igual, elige un día abajo.</p>`}
    </div>`;
    html += `<div class="section-title">Esta semana</div><div class="card">${weekStrip(routine, true)}</div>`;
    html += `<div class="section-title">Otro día de la rutina</div><div class="card"><div class="list">
      ${routine.days.map((d) => `<button class="list-item" data-action="start" data-day="${d.id}">
        <div class="grow"><div><b>${esc(d.name)}</b></div><div class="muted small">${d.exercises.length} ejercicios</div></div>
        <span class="btn sm">Empezar</span></button>`).join('')}
    </div></div>`;
  }
  html += `<button class="btn block" data-action="start-free">+ Entrenamiento libre</button>`;

  const recent = st.sessions.slice(-15).reverse();
  html += `<div class="section-title">Historial</div>`;
  html += recent.length
    ? `<div class="card"><div class="list">${recent.map((s) => `
        <button class="list-item" data-action="session-detail" data-id="${s.id}">
          <div class="grow"><div><b>${esc(s.dayName)}</b></div>
          <div class="muted small">${S.formatDate(s.date)} · ${S.doneSets(s)} series · ${kg(S.sessionVolume(s))}</div></div>
          <span class="muted">›</span>
        </button>`).join('')}</div></div>`
    : `<div class="card empty small">Tus entrenamientos terminados aparecerán aquí.</div>`;
  $view.innerHTML = html;
}

function weekStrip(routine, withDone) {
  const st = S.getState();
  const monday = S.startOfWeek(new Date());
  const today = S.weekdayIndex();
  return `<div class="week">${S.DAY_SHORT.map((short, i) => {
    const date = new Date(monday); date.setDate(monday.getDate() + i);
    const iso = S.todayISO(date);
    const day = routine.days.find((d) => d.id === routine.week[i]);
    const done = withDone && st.sessions.some((s) => s.date === iso);
    return `<div class="week-day ${i === today && withDone ? 'today' : ''} ${done ? 'done' : ''} ${day ? '' : 'rest'}">
      <b>${short}</b><span class="dot"></span><span>${day ? esc(day.name) : 'Descanso'}</span></div>`;
  }).join('')}</div>`;
}

function renderSession() {
  const d = S.getState().draft;
  const effort = S.getState().settings.effort;
  $view.innerHTML = `
    <div class="card session-head">
      <div class="row between">
        <div class="grow"><h2 style="margin:0">${esc(d.dayName)}</h2>
          <div class="muted small">${d.editing ? 'Editando entrenamiento' : '<span id="elapsed"></span>'} · <span id="live-stats"></span></div></div>
        <button class="btn primary" data-action="finish">${d.editing ? 'Guardar' : 'Terminar'}</button>
      </div>
      ${d.editing ? `<label class="field" style="margin-top:10px"><span>Fecha</span>
        <input type="date" value="${d.date}" max="${S.todayISO()}" data-draft="date"></label>` : ''}
    </div>
    ${d.exercises.map((e, i) => exerciseCard(e, i, effort, d)).join('')}
    <button class="btn block" data-action="session-add-ex">+ Añadir ejercicio</button>
    <button class="btn block ghost danger" style="margin-top:8px" data-action="discard">${d.editing ? 'Cancelar edición' : 'Descartar entrenamiento'}</button>`;
  const tick = () => {
    const el = document.getElementById('elapsed');
    if (!el || d.editing) return;
    const m = Math.floor((Date.now() - d.startedAt) / 60000);
    el.textContent = m >= 60 ? `${Math.floor(m / 60)} h ${m % 60} min` : `${m} min`;
  };
  tick();
  updateLiveStats();
  render.timer = setInterval(tick, 15000);
}

function updateLiveStats() {
  const el = document.getElementById('live-stats');
  const d = S.getState().draft;
  if (el && d) el.textContent = `${S.doneSets(d)} series · ${kg(S.sessionVolume(d))}`;
}

function exerciseCard(e, i, effort, d) {
  const ex = S.exById(e.exId);
  const excludeId = d.editing ? d.id : null;
  const last = S.lastPerformance(e.exId, excludeId);
  const hint = d.editing ? null : S.progressionHint(e.exId, e.target, excludeId);
  const noteOpen = e.note || ui.openNotes.has(i);
  return `<div class="card ex-card">
    <div class="ex-head">
      <div class="grow">
        <button class="link-btn" data-action="ex-detail" data-id="${e.exId}"><h3>${esc(ex.name)}</h3></button>
        <div class="row wrap small" style="gap:6px;margin-top:4px">
          <span class="tag">${esc(ex.muscle)}</span>
          ${e.target ? `<span class="tag accent">Objetivo: ${esc(e.target)} reps</span>` : ''}
        </div>
      </div>
      <button class="icon-btn" data-action="ex-up" data-i="${i}" aria-label="Subir">${ICON_UP}</button>
      <button class="icon-btn" data-action="ex-remove" data-i="${i}" aria-label="Quitar ejercicio">${ICON_X}</button>
    </div>
    ${hint ? `<div class="hint hint-${hint.type}">${hint.type === 'up' ? '📈' : '💡'} ${esc(hint.text)}</div>` : ''}
    ${last?.note ? `<div class="hint">📝 Nota anterior: ${esc(last.note)}</div>` : ''}
    <table class="sets">
      <thead><tr><th>#</th><th>Anterior</th><th>kg</th><th>Reps</th><th>${effort}</th><th></th></tr></thead>
      <tbody>${e.sets.map((s, j) => {
        const p = last?.sets[j];
        const repsPh = p?.reps || (e.target ? String(e.target).split('-')[0] : '');
        return `<tr class="${s.done ? 'done' : ''}">
          <td class="n">${s.pr ? '<span title="Récord personal">🏆</span>' : j + 1}</td>
          <td class="prev">${p ? `${fmtN(p.kg)}×${p.reps}` : '—'}</td>
          <td><input type="number" inputmode="decimal" step="0.5" min="0" value="${esc(s.kg)}" placeholder="${p ? esc(p.kg) : '0'}" data-set="kg" data-i="${i}" data-j="${j}" aria-label="Kilos serie ${j + 1}"></td>
          <td><input type="number" inputmode="numeric" min="0" value="${esc(s.reps)}" placeholder="${esc(repsPh)}" data-set="reps" data-i="${i}" data-j="${j}" aria-label="Repeticiones serie ${j + 1}"></td>
          <td><input type="number" inputmode="decimal" step="0.5" min="0" max="10" value="${esc(s.effort)}" placeholder="–" data-set="effort" data-i="${i}" data-j="${j}" aria-label="${effort} serie ${j + 1}"></td>
          <td><button class="check" data-action="toggle-set" data-i="${i}" data-j="${j}" aria-label="Marcar serie ${j + 1} como hecha">${ICON_CHECK}</button></td>
        </tr>`;
      }).join('')}</tbody>
    </table>
    <div class="row" style="margin-top:4px">
      <button class="btn sm" data-action="add-set" data-i="${i}">+ Serie</button>
      ${e.sets.length > 1 ? `<button class="btn sm ghost" data-action="remove-set" data-i="${i}">− Quitar serie</button>` : ''}
      ${noteOpen ? '' : `<button class="btn sm ghost" data-action="note-open" data-i="${i}" style="margin-left:auto">+ Nota</button>`}
    </div>
    ${noteOpen ? `<textarea class="note" rows="2" maxlength="300" placeholder="Nota: agarre, sensaciones, molestias…" data-note="${i}" aria-label="Nota del ejercicio">${esc(e.note || '')}</textarea>` : ''}
  </div>`;
}

// =====================================================================
// RUTINAS
// =====================================================================

function renderRoutines() {
  if (ui.editRoutineId && S.routineById(ui.editRoutineId)) return renderRoutineEditor(S.routineById(ui.editRoutineId));
  const st = S.getState();
  const active = S.activeRoutine();
  let html = '';
  if (active) {
    html += `<div class="section-title">Rutina activa</div>
      <div class="card">
        <div class="row between" style="margin-bottom:10px"><h2 style="margin:0">${esc(active.name)}</h2>
        <button class="btn sm" data-action="edit-routine" data-id="${active.id}">Editar</button></div>
        ${weekStrip(active, false)}
      </div>`;
  }
  const others = st.routines.filter((r) => r.id !== st.activeRoutineId);
  if (others.length) {
    html += `<div class="section-title">Mis rutinas</div><div class="card"><div class="list">
      ${others.map((r) => `<div class="list-item">
        <div class="grow"><b>${esc(r.name)}</b><div class="muted small">${r.days.length} días · ${r.week.filter(Boolean).length} entrenamientos/semana</div></div>
        <button class="btn sm" data-action="activate-routine" data-id="${r.id}">Activar</button>
        <button class="btn sm ghost" data-action="edit-routine" data-id="${r.id}">Editar</button>
      </div>`).join('')}</div></div>`;
  }
  html += `<button class="btn primary block" data-action="new-routine" style="margin-top:12px">+ Crear rutina personalizada</button>`;
  const tplCard = (t) => `<div class="card">
      <h3>${esc(t.name)} ${t.mine ? '<span class="tag accent">Tu Excel</span>' : ''}</h3>
      <p class="muted small" style="margin:2px 0 10px">${esc(t.description)}</p>
      <div class="row wrap" style="gap:6px;margin-bottom:12px">${t.days.map((d) => `<span class="tag">${esc(d.name)}</span>`).join('')}</div>
      <div class="row">
        <button class="btn sm" data-action="preview-template" data-key="${t.key}">Ver ejercicios</button>
        <button class="btn sm primary" data-action="use-template" data-key="${t.key}">Usar esta rutina</button>
      </div>
    </div>`;
  const mine = TEMPLATES.filter((t) => t.mine && !st.routines.some((r) => r.fromTemplate === t.key));
  if (mine.length) html += `<div class="section-title">Tu rutina</div>${mine.map(tplCard).join('')}`;
  html += `<div class="section-title">Rutinas clásicas</div>${TEMPLATES.filter((t) => !t.mine).map(tplCard).join('')}`;
  $view.innerHTML = html;
}

function renderRoutineEditor(r) {
  const isActive = S.getState().activeRoutineId === r.id;
  $view.innerHTML = `
    <button class="btn ghost" data-action="close-editor" style="padding-left:0">‹ Rutinas</button>
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

    <div class="stack" style="margin-top:20px">
      ${isActive ? '' : `<button class="btn primary block" data-action="activate-routine" data-id="${r.id}">Usar como rutina activa</button>`}
      <button class="btn block" data-action="close-editor">Listo</button>
      <button class="btn block ghost danger" data-action="delete-routine" data-id="${r.id}">Eliminar rutina</button>
    </div>`;
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

function exerciseListHTML(list, action) {
  if (!list.length) return '<div class="empty small">No hay ejercicios que coincidan.</div>';
  return `<div class="list">${list.map((e) => `
    <button class="list-item" data-action="${action}" data-id="${e.id}">
      <div class="grow"><div>${esc(e.name)}</div><div class="muted small">${esc(e.muscle)} · ${esc(e.equipment)}${e.custom ? ' · propio' : ''}</div></div>
      <span class="muted">›</span>
    </button>`).join('')}</div>`;
}

function renderExercises() {
  $view.innerHTML = `
    <input type="search" id="ex-search" placeholder="Buscar ejercicio (p. ej. press, remo, cuádriceps)" value="${esc(ui.exQuery)}" aria-label="Buscar ejercicio" style="margin-bottom:8px">
    ${muscleChips(ui.exMuscle, 'ex-filter')}
    <div class="card" id="ex-results" style="padding:4px 12px"></div>
    <button class="btn block" data-action="new-exercise">+ Crear ejercicio propio</button>`;
  updateExerciseResults();
}

function updateExerciseResults() {
  const box = document.getElementById('ex-results');
  if (box) box.innerHTML = exerciseListHTML(S.searchExercises(ui.exQuery, ui.exMuscle), 'ex-detail');
}

function showExerciseDetail(id, tab = ui.exTab) {
  ui.exTab = tab;
  const ex = S.exById(id);
  const hist = S.exerciseHistory(id);
  const rec = S.exerciseRecords(id);
  const routine = S.activeRoutine();
  const tabs = [['about', 'Acerca de'], ['history', 'Historial'], ['charts', 'Gráficos'], ['records', 'Récords']];
  let body = '';

  if (tab === 'about') {
    const video = `https://www.youtube.com/results?search_query=${encodeURIComponent(ex.name + ' técnica correcta')}`;
    body = `
      <div class="row wrap" style="gap:6px;margin-bottom:12px"><span class="tag">${esc(ex.muscle)}</span><span class="tag">${esc(ex.equipment)}</span></div>
      ${rec.sets ? `<p class="small" style="margin:0 0 12px">Lo has hecho en <b>${rec.sessions}</b> ${rec.sessions === 1 ? 'sesión' : 'sesiones'} (${rec.sets} series). Mejor serie: <b>${fmtN(rec.maxKg.kg)} kg × ${rec.maxKg.reps}</b>.</p>`
        : '<p class="muted small" style="margin:0 0 12px">Todavía no has registrado este ejercicio.</p>'}
      <a class="btn block" href="${video}" target="_blank" rel="noopener">▶ Ver técnica en YouTube</a>
      ${routine ? `<div class="section-title">Añadir a “${esc(routine.name)}”</div>
        <div class="row wrap">${routine.days.map((d) => `<button class="btn sm" data-action="add-ex-to-day" data-ex="${id}" data-day="${d.id}">${esc(d.name)}</button>`).join('')}</div>` : ''}`;
  } else if (tab === 'history') {
    body = hist.length
      ? `<div class="list small">${hist.slice(0, 30).map((h) => `<div class="list-item" style="align-items:flex-start">
          <div style="width:90px;flex:none" class="muted">${S.formatDate(h.date)}</div>
          <div class="grow">${h.sets.map((x) => `${fmtN(x.kg)}×${x.reps}${x.effort !== '' && x.effort !== undefined ? `<span class="muted">@${x.effort}</span>` : ''}`).join(' · ')}
            ${h.note ? `<div class="muted">📝 ${esc(h.note)}</div>` : ''}</div></div>`).join('')}</div>`
      : '<div class="empty small">Sin historial todavía.</div>';
  } else if (tab === 'charts') {
    const metrics = [['e1rm', '1RM est.'], ['max', 'Peso máx.'], ['volume', 'Volumen']];
    body = `<div class="segmented" style="margin-bottom:8px">${metrics.map(([k, l]) => `<button class="${ui.exMetric === k ? 'active' : ''}" data-action="ex-metric" data-m="${k}" data-id="${id}">${l}</button>`).join('')}</div>
      <div class="muted small">${ui.exMetric === 'e1rm' ? 'Máximo estimado para 1 repetición (fórmula de Epley), mejor serie de cada sesión' : ui.exMetric === 'max' ? 'Peso más alto usado en cada sesión' : 'kg × reps totales de cada sesión'}</div>
      ${hist.length >= 2 ? '<div class="chart-box"><canvas id="c-exercise" role="img" aria-label="Evolución del ejercicio"></canvas></div>'
        : '<div class="empty small">Necesitas al menos 2 sesiones para ver la evolución.</div>'}`;
  } else {
    const tile = (label, value, sub) => `<div class="stat"><div class="label">${label}</div><div class="value">${value}</div><div class="delta">${sub}</div></div>`;
    body = rec.sets ? `<div class="grid-2">
        ${tile('Peso máximo', `${fmtN(rec.maxKg.kg)} kg`, `× ${rec.maxKg.reps} · ${S.formatDate(rec.maxKg.date)}`)}
        ${tile('1RM estimado', `${fmtN(rec.bestE1rm.value)} kg`, `${fmtN(rec.bestE1rm.kg)}×${rec.bestE1rm.reps} · ${S.formatDate(rec.bestE1rm.date)}`)}
        ${tile('Más repeticiones', rec.maxReps.reps, `con ${fmtN(rec.maxReps.kg)} kg · ${S.formatDate(rec.maxReps.date)}`)}
        ${tile('Mejor sesión', kg(rec.bestVolume.value), `volumen · ${S.formatDate(rec.bestVolume.date)}`)}
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
      data: rows.map((h) => Math.round(val(h) * 10) / 10),
      unit: 'kg',
    });
  }
}

// Selector reutilizable: busca un ejercicio y ejecuta onPick(id).
function openPicker(onPick) {
  let query = '', muscle = '';
  openSheet('Añadir ejercicio', `
    <input type="search" id="pick-search" placeholder="Buscar ejercicio" aria-label="Buscar ejercicio" style="margin-bottom:8px">
    <div id="pick-chips"></div>
    <div id="pick-results" style="max-height:50vh;overflow:auto"></div>`, (root) => {
    const input = root.querySelector('#pick-search');
    const draw = () => {
      root.querySelector('#pick-chips').innerHTML = muscleChips(muscle, 'pick-filter');
      root.querySelector('#pick-results').innerHTML = exerciseListHTML(S.searchExercises(query, muscle), 'pick');
    };
    input.addEventListener('input', () => { query = input.value; draw(); });
    root.onclick = (e) => {
      const b = e.target.closest('[data-action]');
      if (!b) return;
      if (b.dataset.action === 'pick-filter') { muscle = b.dataset.muscle; draw(); }
      if (b.dataset.action === 'pick') { root.onclick = null; closeSheet(); onPick(b.dataset.id); }
    };
    draw();
    setTimeout(() => input.focus(), 50);
  });
}

function newExerciseForm(prefill = '') {
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
      toast(`“${ex.name}” añadido`);
      render();
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

function periodBuckets(period, count) {
  const out = [];
  const now = new Date();
  for (let i = count - 1; i >= 0; i--) {
    if (period === 'month') {
      const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
      out.push({ key: periodKey(S.todayISO(d), 'month'), label: S.MONTHS_SHORT[d.getMonth()], title: `${S.MONTHS_SHORT[d.getMonth()]} ${d.getFullYear()}` });
    } else {
      const d = S.startOfWeek(now); d.setDate(d.getDate() - i * 7);
      out.push({ key: S.todayISO(d), label: `${d.getDate()} ${S.MONTHS_SHORT[d.getMonth()]}`, title: `Semana del ${d.getDate()} ${S.MONTHS_SHORT[d.getMonth()]}` });
    }
  }
  return out;
}

function aggregate(period, count) {
  const buckets = periodBuckets(period, count);
  const idx = new Map(buckets.map((b, i) => [b.key, i]));
  const volume = buckets.map(() => 0);
  const sessions = buckets.map(() => 0);
  const sets = buckets.map(() => 0);
  for (const s of S.getState().sessions) {
    const i = idx.get(periodKey(s.date, period));
    if (i === undefined) continue;
    volume[i] += S.sessionVolume(s);
    sessions[i] += 1;
    sets[i] += S.doneSets(s);
  }
  return { buckets, volume, sessions, sets };
}

function weekStreak() {
  const weeks = new Set(S.getState().sessions.map((s) => periodKey(s.date, 'week')));
  const d = S.startOfWeek(new Date());
  if (!weeks.has(S.todayISO(d))) d.setDate(d.getDate() - 7); // la semana actual aún puede completarse
  let n = 0;
  while (weeks.has(S.todayISO(d))) { n++; d.setDate(d.getDate() - 7); }
  return n;
}

// El periodo actual todavía no ha terminado, así que se muestra la cifra
// anterior como referencia en lugar de un porcentaje engañoso.
function deltaText(prev, unitLabel) {
  return prev ? `${fmtN(prev / 1000)} t ${unitLabel}` : 'sin datos previos';
}

function tableView(headers, rows) {
  return `<details class="table-view"><summary>Ver como tabla</summary><table>
    <thead><tr>${headers.map((h) => `<th>${h}</th>`).join('')}</tr></thead>
    <tbody>${rows.map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join('')}</tr>`).join('')}</tbody></table></details>`;
}

function renderProgress() {
  const st = S.getState();
  const p = ui.period;
  const count = 12;
  const agg = aggregate(p, count);
  const last = count - 1;
  const prevLabel = p === 'week' ? 'semana pasada' : 'mes pasado';
  const nowLabel = p === 'week' ? 'Esta semana' : 'Este mes';

  let html = `<div class="row between" style="margin-bottom:12px">
      <div class="segmented" role="tablist">
        <button class="${p === 'week' ? 'active' : ''}" data-action="period" data-p="week">Semanal</button>
        <button class="${p === 'month' ? 'active' : ''}" data-action="period" data-p="month">Mensual</button>
      </div>
    </div>`;

  if (!st.sessions.length && !st.body.length) {
    html += `<div class="card empty"><p><b>Todavía no hay datos.</b></p><p class="small">Termina tu primer entrenamiento para ver aquí tu volumen, tu constancia y tu evolución.</p></div>`;
  }

  html += `<div class="stats">
    <div class="stat"><div class="label">Entrenos · ${nowLabel.toLowerCase()}</div><div class="value">${agg.sessions[last]}</div><div class="delta">${agg.sets[last]} series</div></div>
    <div class="stat"><div class="label">Volumen · ${nowLabel.toLowerCase()}</div><div class="value">${fmtN(agg.volume[last] / 1000)} t</div><div class="delta">${deltaText(agg.volume[last - 1], prevLabel)}</div></div>
    <div class="stat"><div class="label">Racha</div><div class="value">${weekStreak()}</div><div class="delta">semanas seguidas</div></div>
  </div>`;

  // Volumen total
  html += `<div class="card">
    <h3>Volumen total ${p === 'week' ? 'por semana' : 'por mes'}</h3>
    <div class="muted small">kg levantados (kg × reps de las series hechas)</div>
    <div class="chart-box"><canvas id="c-volume" role="img" aria-label="Gráfico de volumen"></canvas></div>
    ${tableView(['Periodo', 'Volumen', 'Series'], agg.buckets.map((b, i) => [b.title, kg(agg.volume[i]), agg.sets[i]]).reverse())}
  </div>`;

  // Por grupo muscular
  const muscleRange = p === 'week' ? 4 : 3;
  html += `<div class="card">
    <div class="row between wrap"><h3>Por grupo muscular</h3>
      <div class="segmented">
        <button class="${ui.muscleMetric === 'sets' ? 'active' : ''}" data-action="muscle-metric" data-m="sets">Series</button>
        <button class="${ui.muscleMetric === 'volume' ? 'active' : ''}" data-action="muscle-metric" data-m="volume">Volumen</button>
      </div></div>
    <div class="muted small">${ui.muscleMetric === 'sets' ? 'Series efectivas' : 'kg levantados'} por semana, promedio de ${p === 'week' ? 'las últimas 4 semanas' : 'los últimos 3 meses'}</div>
    <div class="chart-box tall"><canvas id="c-muscle" role="img" aria-label="Gráfico por grupo muscular"></canvas></div>
    <div id="t-muscle"></div>
  </div>`;

  // Constancia
  html += `<div class="card">
    <h3>Constancia</h3>
    <div class="muted small">Días entrenados en las últimas 20 semanas (más oscuro = más volumen)</div>
    ${heatmapHTML(20)}
    <div class="chart-box" style="height:170px"><canvas id="c-sessions" role="img" aria-label="Entrenamientos por periodo"></canvas></div>
    <div class="muted small" style="text-align:center">Entrenamientos ${p === 'week' ? 'por semana' : 'por mes'}</div>
  </div>`;

  // Cuerpo
  const field = S.BODY_FIELDS.find((f) => f.key === ui.bodyField);
  const bodyData = st.body.filter((b) => b[field.key] !== undefined && b[field.key] !== '' && b[field.key] !== null);
  const lastBody = bodyData[bodyData.length - 1];
  const firstBody = bodyData[0];
  html += `<div class="card">
    <div class="row between"><h3>Peso corporal y medidas</h3>
      <button class="btn sm primary" data-action="body-add" style="white-space:nowrap">+ Registrar</button></div>
    <div class="chips" style="margin-top:8px">${S.BODY_FIELDS.map((f) => `<button class="chip ${f.key === ui.bodyField ? 'active' : ''}" data-action="body-field" data-f="${f.key}">${f.label}</button>`).join('')}</div>
    ${lastBody ? `<p class="small" style="margin:0">Actual: <b>${fmtN(lastBody[field.key])} ${field.unit}</b>
      ${bodyData.length > 1 ? `<span class="muted"> · ${Number(lastBody[field.key]) - Number(firstBody[field.key]) >= 0 ? '+' : ''}${fmtN(lastBody[field.key] - firstBody[field.key])} ${field.unit} desde ${S.formatDate(firstBody.date)}</span>` : ''}</p>` : ''}
    ${bodyData.length
      ? `<div class="chart-box"><canvas id="c-body" role="img" aria-label="Evolución de ${field.label}"></canvas></div>`
      : `<div class="empty small">Registra tu ${field.label.toLowerCase()} para ver su evolución.</div>`}
    ${st.body.length ? `<details class="table-view"><summary>Ver registros</summary><table>
      <thead><tr><th>Fecha</th>${S.BODY_FIELDS.map((f) => `<th>${f.label}</th>`).join('')}<th></th></tr></thead>
      <tbody>${[...st.body].reverse().map((b) => `<tr><td>${S.formatDate(b.date)}</td>${S.BODY_FIELDS.map((f) => `<td>${b[f.key] !== undefined && b[f.key] !== '' ? fmtN(b[f.key]) : '–'}</td>`).join('')}
        <td><button class="btn sm ghost" data-action="body-edit" data-date="${b.date}">Editar</button></td></tr>`).join('')}</tbody></table></details>` : ''}
  </div>`;

  $view.innerHTML = html;

  const titleOf = (i) => agg.buckets[i].title;
  barChart(document.getElementById('c-volume'), {
    labels: agg.buckets.map((b) => b.label), data: agg.volume, unit: 'kg', highlightLast: true, tooltipTitle: titleOf,
  });
  barChart(document.getElementById('c-sessions'), {
    labels: agg.buckets.map((b) => b.label), data: agg.sessions, unit: '', tooltipTitle: titleOf,
  });
  drawMuscleChart(muscleRange);
  if (bodyData.length) {
    lineChart(document.getElementById('c-body'), {
      labels: bodyData.map((b) => S.formatDate(b.date)),
      data: bodyData.map((b) => Number(b[field.key])),
      unit: field.unit,
    });
  }
}

function drawMuscleChart(range) {
  const p = ui.period;
  const keys = new Set(periodBuckets(p, range).map((b) => b.key));
  const weeksInRange = p === 'week' ? range : Math.max(1, (range * 30.4) / 7);
  const totals = new Map(MUSCLES.map((m) => [m, 0]));
  for (const s of S.getState().sessions) {
    if (!keys.has(periodKey(s.date, p))) continue;
    for (const e of s.exercises) {
      const m = S.exById(e.exId).muscle;
      for (const set of e.sets) {
        if (!set.done) continue;
        totals.set(m, (totals.get(m) || 0) + (ui.muscleMetric === 'sets' ? 1 : S.setVolume(set)));
      }
    }
  }
  const rows = [...totals.entries()].map(([m, v]) => [m, v / weeksInRange]).sort((a, b) => b[1] - a[1]);
  barChart(document.getElementById('c-muscle'), {
    labels: rows.map((r) => r[0]),
    data: rows.map((r) => Math.round(r[1] * 10) / 10),
    unit: ui.muscleMetric === 'sets' ? 'series/sem' : 'kg/sem',
    horizontal: true,
  });
  document.getElementById('t-muscle').innerHTML = tableView(
    ['Grupo', ui.muscleMetric === 'sets' ? 'Series/sem' : 'kg/sem'],
    rows.map((r) => [r[0], ui.muscleMetric === 'sets' ? fmtN(r[1]) : kg(r[1])]),
  );
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
      <div class="grid-2">${S.BODY_FIELDS.map((f) => `<label class="field"><span>${f.label} (${f.unit})</span>
        <input type="number" inputmode="decimal" step="0.1" min="0" name="${f.key}" value="${esc(existing[f.key] ?? '')}"></label>`).join('')}</div>
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
        if (v !== '') entry[bf.key] = Number(v);
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
// RESUMEN AL TERMINAR
// =====================================================================

function showSummary(session) {
  const mins = Math.max(1, Math.round((session.finishedAt - session.startedAt) / 60000));
  const vol = S.sessionVolume(session);
  const prev = S.previousSameDay(session);
  const prs = [];
  for (const e of session.exercises) for (const x of e.sets) if (x.pr) prs.push({ e, x });
  let compare = '';
  if (prev) {
    const pv = S.sessionVolume(prev);
    const pct = pv ? Math.round(((vol - pv) / pv) * 100) : 0;
    compare = pv ? `${pct >= 0 ? '▲' : '▼'} ${Math.abs(pct)}% de volumen vs. el ${S.formatDate(prev.date)}` : '';
  }
  const tile = (label, value) => `<div class="stat"><div class="label">${label}</div><div class="value">${value}</div></div>`;
  openSheet('¡Entrenamiento terminado! 💪', `
    <p class="muted" style="margin:0 0 12px">${esc(session.dayName)} · ${S.formatDate(session.date)}</p>
    <div class="grid-3" style="margin-bottom:10px">
      ${tile('Duración', mins >= 60 ? `${Math.floor(mins / 60)}h ${mins % 60}m` : `${mins} min`)}
      ${tile('Series', S.doneSets(session))}
      ${tile('Volumen', `${fmtN(vol / 1000)} t`)}
    </div>
    ${compare ? `<p class="small" style="margin:0 0 12px">${compare}</p>` : ''}
    ${prs.length ? `<div class="hint hint-up" style="margin-bottom:12px"><b>🏆 ${prs.length === 1 ? 'Nuevo récord' : `${prs.length} récords nuevos`}</b><br>
      ${prs.map(({ e, x }) => `${esc(S.exById(e.exId).name)}: ${fmtN(x.kg)} kg × ${x.reps}`).join('<br>')}</div>` : ''}
    <div class="section-title" style="margin-top:4px">Mejor serie por ejercicio</div>
    <div class="list small">${session.exercises.map((e) => {
      const best = e.sets.reduce((a, x) => (S.e1rm(x) > S.e1rm(a) ? x : a), e.sets[0]);
      return `<div class="list-item" style="padding:8px 0"><span class="grow">${esc(S.exById(e.exId).name)}</span><b>${fmtN(best.kg)}×${best.reps}</b></div>`;
    }).join('')}</div>
    <button class="btn primary block" data-action="close-sheet" style="margin-top:12px">Listo</button>`);
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

function accountHTML() {
  if (!Cloud.isConfigured()) {
    return `<div class="card" style="margin:0"><b>Cuenta en la nube</b>
      <p class="muted small" style="margin:4px 0 0">La sincronización aún no está configurada (falta conectar Supabase en js/config.js). Mientras tanto, los datos se guardan en este dispositivo.</p></div>`;
  }
  const user = Cloud.getUser();
  if (user) {
    return `<div class="card" style="margin:0">
      <div class="row between"><div class="grow"><b>Cuenta</b><div class="muted small" style="overflow-wrap:anywhere">${esc(user.email)}</div></div>
        <button class="btn sm" data-action="cloud-sync">Sincronizar</button></div>
      <p class="small muted" id="sync-status" style="margin:8px 0">${syncLabel()}</p>
      <button class="btn sm ghost danger" data-action="cloud-logout" style="padding-left:0">Cerrar sesión</button>
    </div>`;
  }
  return `<form class="card stack" id="login-form" style="margin:0">
      <div><b>Inicia sesión</b><div class="muted small">Guarda tus datos en la nube y úsalos en cualquier dispositivo.</div></div>
      <input type="email" name="email" placeholder="Correo" autocomplete="email" required>
      <input type="password" name="password" placeholder="Contraseña (mín. 6 caracteres)" autocomplete="current-password" minlength="6" required>
      <div class="grid-2">
        <button class="btn primary" name="mode" value="login">Entrar</button>
        <button class="btn" name="mode" value="signup">Crear cuenta</button>
      </div>
      <button type="button" class="btn sm ghost" data-action="cloud-reset">¿Olvidaste tu contraseña?</button>
      <p class="small" id="login-msg" style="margin:0" role="status"></p>
    </form>`;
}

function bindAccountForm(root) {
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
          msg.textContent = '📧 Te enviamos un correo. Abre el enlace para confirmar tu cuenta y luego entra aquí.';
          return;
        }
      } else {
        await Cloud.signIn(f.get('email'), f.get('password'));
      }
      closeSheet();
      toast('Sesión iniciada · sincronizando tus datos');
    } catch (err) {
      msg.textContent = err.message;
    } finally {
      buttons.forEach((b) => { b.disabled = false; });
    }
  });
}

function openSettings() {
  const st = S.getState();
  let theme = 'auto';
  try { theme = localStorage.getItem('gymtrack.theme') || 'auto'; } catch {}
  openSheet('Ajustes', `
    <div class="stack">
      ${accountHTML()}
      <div class="row between"><div><b>Esfuerzo por serie</b><div class="muted small">RIR = reps en reserva · RPE = esfuerzo 1-10</div></div>
        <div class="segmented">
          <button class="${st.settings.effort === 'RIR' ? 'active' : ''}" data-action="set-effort" data-v="RIR">RIR</button>
          <button class="${st.settings.effort === 'RPE' ? 'active' : ''}" data-action="set-effort" data-v="RPE">RPE</button>
        </div></div>
      <div class="row between"><b>Tema</b>
        <div class="segmented">
          ${[['auto', 'Auto'], ['light', 'Claro'], ['dark', 'Oscuro']].map(([v, l]) => `<button class="${theme === v ? 'active' : ''}" data-action="set-theme" data-v="${v}">${l}</button>`).join('')}
        </div></div>
      <div class="section-title">Respaldo</div>
      <p class="muted small" style="margin:0">${Cloud.getUser() ? 'Tus datos se guardan en la nube. Aun así puedes descargar una copia.' : 'Sin sesión iniciada, los datos se guardan solo en este navegador. Descarga un respaldo de vez en cuando.'}</p>
      <button class="btn block" data-action="export">Descargar respaldo (.json)</button>
      <label class="btn block">Restaurar respaldo<input type="file" accept="application/json,.json" id="import-file" hidden></label>
      <button class="btn block ghost danger" data-action="reset">Borrar todos los datos</button>
      <p class="muted small" style="text-align:center">${st.sessions.length} entrenamientos · ${st.routines.length} rutinas · ${st.body.length} registros corporales</p>
    </div>`, (root) => {
    bindAccountForm(root);
    root.querySelector('#import-file').addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      try {
        const data = JSON.parse(await file.text());
        if (!Array.isArray(data.sessions) || !Array.isArray(data.routines)) throw new Error('formato');
        if (!confirm('Esto reemplazará los datos actuales por los del respaldo. ¿Continuar?')) return;
        S.replaceState(data);
        closeSheet();
        toast('Respaldo restaurado');
        render();
      } catch {
        toast('El archivo no es un respaldo válido');
      }
    });
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
  goto: (b) => setTab(b.dataset.tab),
  'open-settings': openSettings,
  'close-sheet': closeSheet,

  // Entrenar
  start: (b) => {
    const r = S.activeRoutine();
    S.startDraft(r, r.days.find((d) => d.id === b.dataset.day));
    render(); window.scrollTo(0, 0);
  },
  'start-free': () => { S.startDraft(null, null); render(); window.scrollTo(0, 0); },
  'toggle-set': (b) => {
    const d = S.getState().draft;
    const e = d.exercises[b.dataset.i];
    const s = e.sets[b.dataset.j];
    const row = b.closest('tr');
    if (!s.done) {
      // Rellena con los valores sugeridos si el campo quedó vacío.
      const kgIn = row.querySelector('[data-set="kg"]');
      const repsIn = row.querySelector('[data-set="reps"]');
      if (s.kg === '' && kgIn.placeholder) s.kg = num(kgIn.placeholder);
      if (s.reps === '' && repsIn.placeholder) s.reps = num(repsIn.placeholder);
      if (s.reps === '' || s.reps === 0) { repsIn.focus(); return toast('Anota las repeticiones'); }
      kgIn.value = s.kg; repsIn.value = s.reps;
    }
    s.done = !s.done;
    row.classList.toggle('done', s.done);
    delete s.pr;
    if (s.done) {
      const others = e.sets.filter((x) => x !== s && x.done);
      const pr = S.prType(e.exId, s, d.editing ? d.id : null, others);
      if (pr) {
        s.pr = pr;
        toast(pr === 'peso' ? `🏆 ¡Récord de peso! ${fmtN(s.kg)} kg` : `🏆 ¡Récord personal! 1RM estimado ${fmtN(S.e1rm(s))} kg`);
        if (navigator.vibrate) navigator.vibrate([60, 40, 60]);
      }
    }
    row.querySelector('.n').innerHTML = s.pr ? '<span title="Récord personal">🏆</span>' : Number(b.dataset.j) + 1;
    if (s.done) {
      // Las series siguientes sin peso heredan el de esta.
      e.sets.forEach((x, k) => {
        if (k <= b.dataset.j || x.done || x.kg !== '') return;
        x.kg = s.kg;
        const input = document.querySelector(`[data-set="kg"][data-i="${b.dataset.i}"][data-j="${k}"]`);
        if (input) input.value = s.kg;
      });
    }
    S.save();
    updateLiveStats();
  },
  'add-set': (b) => {
    const e = S.getState().draft.exercises[b.dataset.i];
    const prev = e.sets[e.sets.length - 1];
    e.sets.push({ kg: prev ? prev.kg : '', reps: '', effort: '', done: false });
    S.save(); render();
  },
  'remove-set': (b) => {
    const e = S.getState().draft.exercises[b.dataset.i];
    e.sets.pop(); S.save(); render();
  },
  'ex-remove': (b) => {
    const d = S.getState().draft;
    const e = d.exercises[b.dataset.i];
    if (e.sets.some((s) => s.done) && !confirm('¿Quitar este ejercicio y sus series hechas?')) return;
    d.exercises.splice(b.dataset.i, 1); ui.openNotes.clear(); S.save(); render();
  },
  'ex-up': (b) => {
    const d = S.getState().draft; const i = Number(b.dataset.i);
    if (i > 0) { [d.exercises[i - 1], d.exercises[i]] = [d.exercises[i], d.exercises[i - 1]]; S.save(); render(); }
  },
  'session-add-ex': () => openPicker((id) => {
    S.getState().draft.exercises.push(S.draftExercise(id, 3, ''));
    S.save(); render();
    window.scrollTo(0, document.body.scrollHeight);
  }),
  finish: () => {
    const d = S.getState().draft;
    const n = S.doneSets(d);
    if (!n) {
      if (confirm('No has marcado ninguna serie como hecha. ¿Descartar el entrenamiento?')) { S.getState().draft = null; S.save(); render(); }
      return;
    }
    const pending = d.exercises.reduce((a, e) => a + e.sets.filter((s) => !s.done).length, 0);
    if (pending && !confirm(`Tienes ${pending} series sin marcar; no se guardarán. ¿${d.editing ? 'Guardar' : 'Terminar'} igual?`)) return;
    const editing = d.editing;
    const saved = S.finishDraft();
    ui.openNotes.clear();
    render(); window.scrollTo(0, 0);
    if (editing) toast('Cambios guardados');
    else showSummary(saved);
  },
  discard: () => {
    const d = S.getState().draft;
    if (!d.editing && !confirm('¿Descartar este entrenamiento? Se perderá lo anotado.')) return;
    S.getState().draft = null; S.save(); ui.openNotes.clear(); render();
  },
  'edit-session': (b) => {
    if (S.getState().draft) return toast('Termina o descarta el entrenamiento en curso primero');
    S.editSession(b.dataset.id);
    closeSheet(); setTab('train');
  },
  'note-open': (b) => {
    ui.openNotes.add(Number(b.dataset.i)); render();
    document.querySelector(`[data-note="${b.dataset.i}"]`)?.focus();
  },
  'ex-tab': (b) => showExerciseDetail(b.dataset.id, b.dataset.tab),
  'ex-metric': (b) => { ui.exMetric = b.dataset.m; showExerciseDetail(b.dataset.id, 'charts'); },
  'session-detail': (b) => {
    const s = S.getState().sessions.find((x) => x.id === b.dataset.id);
    if (!s) return;
    const mins = s.finishedAt ? Math.round((s.finishedAt - s.startedAt) / 60000) : null;
    openSheet(s.dayName, `
      <p class="muted small" style="margin-top:0">${S.formatDate(s.date)}${mins ? ` · ${mins} min` : ''} · ${S.doneSets(s)} series · ${kg(S.sessionVolume(s))}</p>
      ${s.exercises.map((e) => `<div style="margin-bottom:10px"><b class="small">${esc(S.exById(e.exId).name)}</b>
        <div class="muted small">${e.sets.map((x) => `${x.pr ? '🏆' : ''}${fmtN(x.kg)}×${x.reps}${x.effort !== '' && x.effort !== undefined ? ` @${x.effort}` : ''}`).join(' · ')}</div>
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

  // Rutinas
  'use-template': (b) => {
    const tpl = TEMPLATES.find((t) => t.key === b.dataset.key);
    const r = S.addRoutine(S.routineFromTemplate(tpl));
    const hasHistory = tpl.days.some((d) => d.exercises.some((e) => e.last));
    let msg = `“${r.name}” es ahora tu rutina activa`;
    if (hasHistory && confirm('¿Importar también tus últimos pesos y repeticiones al historial? Así la app sabrá desde dónde empiezas.')) {
      const n = S.importTemplateHistory(tpl, r);
      msg += ` · ${n} entrenamientos importados`;
    }
    closeSheet();
    toast(msg);
    render(); window.scrollTo(0, 0);
  },
  'preview-template': (b) => {
    const tpl = TEMPLATES.find((t) => t.key === b.dataset.key);
    openSheet(tpl.name, `${tpl.days.map((d) => `<div style="margin-bottom:14px"><b>${esc(d.name)}</b>
      <div class="list small">${d.exercises.map((e) => `<div class="list-item" style="padding:6px 0"><span class="grow">${esc(S.exById(e.exId).name)}</span><span class="muted">${e.sets} × ${esc(e.reps)}</span></div>`).join('')}</div></div>`).join('')}
      <p class="muted small">Semana: ${tpl.week.map((i, wd) => `${S.DAY_SHORT[wd]} ${i === null ? '—' : esc(tpl.days[i].name)}`).join(' · ')}</p>
      <button class="btn primary block" data-action="use-template" data-key="${tpl.key}">Usar esta rutina</button>`);
  },
  'new-routine': () => {
    const r = S.addRoutine(S.newEmptyRoutine(), false);
    ui.editRoutineId = r.id; render(); window.scrollTo(0, 0);
  },
  'edit-routine': (b) => { ui.editRoutineId = b.dataset.id; render(); window.scrollTo(0, 0); },
  'close-editor': () => { ui.editRoutineId = null; render(); window.scrollTo(0, 0); },
  'activate-routine': (b) => {
    S.getState().activeRoutineId = b.dataset.id; S.save();
    toast('Rutina activada'); render();
  },
  'delete-routine': (b) => {
    const r = S.routineById(b.dataset.id);
    if (!confirm(`¿Eliminar la rutina “${r.name}”? Tu historial de entrenamientos no se borra.`)) return;
    S.deleteRoutine(r.id); ui.editRoutineId = null; render();
  },
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
  'ex-filter': (b) => {
    ui.exMuscle = b.dataset.muscle;
    document.querySelectorAll('#view .chip').forEach((c) => c.classList.toggle('active', c.dataset.muscle === ui.exMuscle));
    updateExerciseResults();
  },
  'ex-detail': (b) => showExerciseDetail(b.dataset.id, 'about'),
  'new-exercise': () => newExerciseForm(ui.exQuery),
  'add-ex-to-day': (b) => {
    const r = S.activeRoutine();
    const d = r.days.find((x) => x.id === b.dataset.day);
    d.exercises.push({ exId: b.dataset.ex, sets: 3, reps: '8-12' });
    S.save(); closeSheet();
    toast(`Añadido a ${d.name}`);
  },

  // Progreso
  period: (b) => { ui.period = b.dataset.p; render(); },
  'muscle-metric': (b) => { ui.muscleMetric = b.dataset.m; render(); },
  'body-field': (b) => { ui.bodyField = b.dataset.f; render(); },
  'body-add': () => bodyForm(),
  'body-edit': (b) => bodyForm(b.dataset.date),
  'body-delete': (b) => {
    if (!confirm('¿Eliminar este registro?')) return;
    S.deleteBody(b.dataset.date); closeSheet(); render();
  },

  // Ajustes
  'cloud-sync': () => Cloud.sync(),
  'cloud-logout': async () => {
    if (!confirm('¿Cerrar sesión? Tus datos seguirán en la nube y en este dispositivo.')) return;
    await Cloud.signOut(); closeSheet(); toast('Sesión cerrada'); render();
  },
  'cloud-reset': async () => {
    const email = document.querySelector('#login-form [name="email"]').value;
    if (!email) return toast('Escribe primero tu correo');
    try { await Cloud.resetPassword(email); toast('Te enviamos un correo para cambiar la contraseña'); }
    catch (err) { toast(err.message); }
  },
  'set-effort': (b) => { S.getState().settings.effort = b.dataset.v; S.save(); closeSheet(); render(); },
  'set-theme': (b) => {
    try { localStorage.setItem('gymtrack.theme', b.dataset.v); } catch {}
    applyTheme(); closeSheet(); render();
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
    S.resetState(); closeSheet(); render();
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
  if (t.id === 'ex-search') { ui.exQuery = t.value; updateExerciseResults(); return; }
  if (t.dataset.note !== undefined) {
    S.getState().draft.exercises[t.dataset.note].note = t.value;
    S.save();
    return;
  }
  if (t.dataset.draft === 'date') {
    if (t.value) { S.getState().draft.date = t.value; S.save(); }
    return;
  }
  if (t.dataset.set) {
    const s = S.getState().draft.exercises[t.dataset.i].sets[t.dataset.j];
    s[t.dataset.set] = num(t.value);
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
    S.save();
  }
});

// Vuelve a dibujar los gráficos si cambia el tema del sistema.
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => ui.tab === 'progress' && render());

// ---------- Inicio ----------

applyTheme();
S.seedIfEmpty();
render();

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
Cloud.onChange(() => {
  const el = document.getElementById('sync-status');
  if (el) el.innerHTML = syncLabel();
  const id = Cloud.getUser()?.id;
  if (id !== lastUserId) { lastUserId = id; safeRender(); }
});
Cloud.initCloud({ onData: safeRender });

if ('serviceWorker' in navigator && location.protocol === 'https:') {
  navigator.serviceWorker.register('sw.js').catch(() => {});
}
