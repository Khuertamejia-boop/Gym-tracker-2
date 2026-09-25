// Mapa muscular: cuerpo realista (hombre o mujer, según el perfil) con los
// músculos trabajados en rojo. Usa la librería local js/vendor/muscle-map.
import { MuscleMap } from './vendor/muscle-map/index.js';
import { EXERCISE_MUSCLES, BY_CATEGORY, BACK_GROUPS, LOWER_GROUPS, MUSCLE_NAMES } from './data/muscles.js';
import { getState, exById } from './store.js';

const RED = '#e0302a';
const PRIMARY = 85;
const SECONDARY = 35;
// Zonas de la ilustración (viewBox 361 × 542) para las miniaturas.
const CROPS = { upper: '55 55 250 250', lower: '75 245 210 210', calves: '85 370 190 190' };

export const bodyGender = () => (getState().profile?.gender === 'female' ? 'female' : 'male');

function theme() {
  const forced = document.documentElement.dataset.theme;
  if (forced) return forced;
  return matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export function musclesFor(exId) {
  if (EXERCISE_MUSCLES[exId]) return EXERCISE_MUSCLES[exId];
  return BY_CATEGORY[exById(exId).muscle] || [[], []];
}

export const muscleNames = (groups) => groups.map((g) => MUSCLE_NAMES[g]);

function render(el, { view, primary, secondary, width, crop }) {
  const highlights = [
    ...secondary.map((group) => ({ group, intensity: SECONDARY, color: RED })),
    ...primary.map((group) => ({ group, intensity: PRIMARY, color: RED })),
  ];
  new MuscleMap(el, { gender: bodyGender(), view, theme: theme(), width, highlights, hoverHighlight: false });
  const svg = el.querySelector('svg');
  if (svg) {
    if (crop) svg.setAttribute('viewBox', CROPS[crop]);
    svg.setAttribute('aria-hidden', 'true');
  }
}

// Músculos de un entrenamiento completo: principales de cualquier ejercicio y el resto como secundarios.
export function sessionMuscles(session) {
  const primary = new Set();
  const secondary = new Set();
  for (const e of session.exercises) {
    const [p, sec] = musclesFor(e.exId);
    p.forEach((g) => primary.add(g));
    sec.forEach((g) => secondary.add(g));
  }
  primary.forEach((g) => secondary.delete(g));
  return [[...primary], [...secondary]];
}

// Monta el mapa en todos los elementos con data-muscle-map="<exId>" dentro de root.
// data-view="front|back" (opcional) y data-thumb (miniatura con zoom a la zona trabajada).
export function mountMuscleMaps(root = document) {
  root.querySelectorAll('[data-muscle-map]:not([data-mounted])').forEach((el) => {
    el.dataset.mounted = '1';
    // data-groups="principal,principal|secundario,secundario" pinta grupos concretos (p. ej. un entrenamiento entero).
    const [primary, secondary] = el.dataset.groups !== undefined
      ? el.dataset.groups.split('|').map((part) => (part || '').split(',').filter(Boolean)).concat([[]]).slice(0, 2)
      : musclesFor(el.dataset.muscleMap);
    if (el.hasAttribute('data-thumb')) {
      const main = primary[0];
      const view = BACK_GROUPS.includes(main) && !primary.includes('chest') ? 'back' : 'front';
      const crop = main === 'calves' ? 'calves' : primary.some((g) => LOWER_GROUPS.includes(g)) ? 'lower' : 'upper';
      render(el, { view, primary, secondary, width: el.clientWidth || 64, crop });
    } else {
      render(el, { view: el.dataset.view || 'front', primary, secondary, width: '100%' });
    }
  });
}
