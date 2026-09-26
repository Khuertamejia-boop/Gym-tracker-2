// Mapa muscular: cuerpo realista (hombre o mujer, según el perfil) con los
// músculos trabajados en rojo. Usa la librería local js/vendor/muscle-map.
import { MuscleMap } from './vendor/muscle-map/index.js';
import { EXERCISE_MUSCLES, BY_CATEGORY, BACK_GROUPS, MUSCLE_NAMES } from './data/muscles.js';
import { getState, exById } from './store.js';

const RED = '#e0302a';
const PRIMARY = 85;
const SECONDARY = 35;
// Caja de cada grupo muscular en la ilustración [x0, y0, x1, y1] (medida con la librería).
const BOXES = {
  'male-front': { chest: [124, 106, 237, 155], shoulders: [101, 105, 260, 150], biceps: [92, 138, 268, 200], forearms: [73, 188, 288, 265], abs: [155, 153, 206, 263], obliques: [133, 157, 227, 249], upper_back: [137, 85, 225, 103], quads: [121, 235, 239, 364], calves: [143, 390, 216, 441] },
  'male-back': { shoulders: [98, 103, 264, 144], triceps: [91, 134, 271, 195], forearms: [74, 186, 289, 264], upper_back: [132, 60, 231, 171], lats: [121, 111, 240, 216], lower_back: [137, 180, 225, 247], glutes: [132, 227, 229, 289], hamstrings: [128, 280, 234, 372], calves: [118, 374, 243, 442] },
  'female-front': { chest: [140, 121, 224, 169], shoulders: [122, 119, 241, 158], biceps: [116, 148, 247, 207], forearms: [91, 194, 272, 265], abs: [163, 165, 200, 264], obliques: [146, 167, 216, 256], upper_back: [147, 103, 217, 118], quads: [129, 242, 234, 368], calves: [152, 393, 211, 441] },
  'female-back': { shoulders: [117, 116, 245, 154], triceps: [112, 143, 251, 199], forearms: [90, 193, 272, 266], upper_back: [144, 75, 220, 172], lats: [136, 123, 227, 219], lower_back: [146, 187, 215, 243], glutes: [141, 230, 220, 289], hamstrings: [133, 282, 229, 371], calves: [124, 374, 236, 442] },
};
// Músculos de brazos y piernas: se enfoca un solo lado para acercar más.
const ONE_SIDE = ['shoulders', 'biceps', 'triceps', 'forearms', 'quads', 'hamstrings', 'calves'];
const W = 361;
const H = 542;

// Encuadre de la miniatura: zoom a los músculos principales del ejercicio.
// ratio = alto / ancho (1 para cuadradas, 1.5 para las del carrusel).
function zoomBox(view, primary, ratio) {
  const boxes = BOXES[`${bodyGender()}-${view}`];
  let x0 = Infinity; let y0 = Infinity; let x1 = -Infinity; let y1 = -Infinity;
  for (const g of primary) {
    const b = boxes[g];
    if (!b) continue;
    const right = ONE_SIDE.includes(g) ? Math.min(b[2], W / 2) : b[2];
    x0 = Math.min(x0, b[0]); y0 = Math.min(y0, b[1]); x1 = Math.max(x1, right); y1 = Math.max(y1, b[3]);
  }
  if (x1 < x0) return `0 0 ${W} ${H}`;
  const w = Math.max((x1 - x0) * 1.3, ((y1 - y0) * 1.3) / ratio, 78);
  const h = w * ratio;
  const cx = Math.min(Math.max((x0 + x1) / 2, w / 2), W - w / 2);
  const cy = Math.min(Math.max((y0 + y1) / 2, h / 2), H - h / 2);
  return [cx - w / 2, cy - h / 2, w, h].map((n) => Math.round(n)).join(' ');
}

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

function render(el, { view, primary, secondary, width, zoom, tall }) {
  const highlights = [
    ...secondary.map((group) => ({ group, intensity: SECONDARY, color: RED })),
    ...primary.map((group) => ({ group, intensity: PRIMARY, color: RED })),
  ];
  new MuscleMap(el, { gender: bodyGender(), view, theme: theme(), width, highlights, hoverHighlight: false });
  const svg = el.querySelector('svg');
  if (svg) {
    if (zoom) svg.setAttribute('viewBox', zoomBox(view, primary, tall ? 1.5 : 1));
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
      render(el, { view, primary, secondary, width: el.clientWidth || 64, zoom: true, tall: el.dataset.thumb === 'tall' });
    } else {
      render(el, { view: el.dataset.view || 'front', primary, secondary, width: '100%' });
    }
  });
}
