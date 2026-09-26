// Imágenes para compartir un entrenamiento (formato historia 1080 × 1920).
// Plantillas: 'card' (tarjeta), 'photo' (sobre foto o PNG transparente) y 'record'.
// El cuerpo con los músculos se dibuja en el canvas con los mismos contornos del
// mapa muscular, para que salga nítido en la imagen.
import * as S from './store.js';
import { getMuscles, defaultBody, PX2MM, VIEWBOX_WIDTH, VIEWBOX_HEIGHT } from './vendor/muscle-map/index.js';
import { bodyGender, sessionMuscles } from './body.js';

export const W = 1080;
export const H = 1920;
const RED = '#e0302a';
const ACCENT = '#d9233a';
const FONT = '-apple-system, "SF Pro Display", "Helvetica Neue", Arial, sans-serif';
const font = (weight, size) => `${weight} ${size}px ${FONT}`;

const images = new Map();
function loadImage(src) {
  if (!images.has(src)) {
    images.set(src, new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = reject;
      img.src = src;
    }));
  }
  return images.get(src);
}

// Cuerpo (frente o espalda) con los músculos trabajados, en un canvas propio.
async function bodyCanvas(view, primary, secondary, width) {
  const gender = bodyGender();
  const img = await loadImage(defaultBody(gender, view, 'dark'));
  const scale = width / VIEWBOX_WIDTH;
  const c = document.createElement('canvas');
  c.width = Math.round(width);
  c.height = Math.round(VIEWBOX_HEIGHT * scale);
  const g = c.getContext('2d');
  g.drawImage(img, 0, 0, c.width, c.height);
  g.globalCompositeOperation = 'multiply';
  g.fillStyle = RED;
  for (const m of getMuscles(gender, view)) {
    const alpha = primary.includes(m.group) ? 0.9 : secondary.includes(m.group) ? 0.35 : 0;
    if (!alpha) continue;
    g.save();
    g.scale(scale, scale);
    if (m.offset) g.translate((m.offset.x || 0) * PX2MM, (m.offset.y || 0) * PX2MM);
    g.globalAlpha = alpha;
    g.fill(new Path2D(m.d));
    g.restore();
  }
  // El "multiply" también oscurece el fondo transparente: se recorta con la silueta.
  g.globalCompositeOperation = 'destination-in';
  g.globalAlpha = 1;
  g.drawImage(img, 0, 0, c.width, c.height);
  return c;
}

// Texto con espaciado entre letras (las etiquetas en mayúsculas).
function spaced(g, text, x, y, spacing, align = 'left') {
  const chars = [...text];
  const total = chars.reduce((a, ch) => a + g.measureText(ch).width, 0) + spacing * (chars.length - 1);
  let cx = align === 'center' ? x - total / 2 : align === 'right' ? x - total : x;
  const prev = g.textAlign;
  g.textAlign = 'left';
  for (const ch of chars) { g.fillText(ch, cx, y); cx += g.measureText(ch).width + spacing; }
  g.textAlign = prev;
}

// 7518 → "7.518" (el formato español no agrupa números de 4 cifras).
export const groupNum = (n) => String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, '.');

const upperDate = (iso) => S.formatDate(iso).toUpperCase();
const shortDay = (name) => name.replace(/\s*\(.*\)\s*/g, ' ').trim();

export function sessionStats(session) {
  const mins = Math.max(1, Math.round((session.finishedAt - session.startedAt) / 60000));
  const u = S.defaultUnit();
  return {
    mins,
    time: mins >= 60 ? `${Math.floor(mins / 60)} h ${mins % 60}` : `${mins} min`,
    timeShort: mins >= 60 ? `${Math.floor(mins / 60)}h ${mins % 60}′` : `${mins}′`,
    sets: S.doneSets(session),
    volume: groupNum(S.toUnit(S.sessionVolume(session), u)),
    unit: u,
  };
}

// Medidas de un texto con espaciado entre letras.
function spacedWidth(g, text, spacing) {
  return [...text].reduce((a, ch) => a + g.measureText(ch).width, 0) + spacing * ([...text].length - 1);
}

// Posición horizontal de un bloque de ancho w según la alineación.
const MARGIN = 80;

// Nombres cortos de los músculos para la línea "Cuádriceps · Glúteos".
const SHORT_MUSCLE = {
  chest: 'Pecho', shoulders: 'Hombros', biceps: 'Bíceps', triceps: 'Tríceps', forearms: 'Antebrazos',
  abs: 'Abdomen', obliques: 'Oblicuos', upper_back: 'Espalda alta', lats: 'Dorsales', lower_back: 'Lumbares',
  glutes: 'Glúteos', quads: 'Cuádriceps', hamstrings: 'Femorales', calves: 'Pantorrillas',
};
const blockX = (align, w) => (align === 'center' ? (W - w) / 2 : align === 'right' ? W - MARGIN - w : MARGIN);

function brand(g, y, align, k) {
  g.font = font(600, Math.round(26 * k));
  const label = 'MI GYM TRACKER';
  const sp = 6 * k;
  const dot = 16 * k;
  const w = dot + 14 * k + spacedWidth(g, label, sp);
  const x = blockX(align, w);
  g.fillStyle = ACCENT;
  g.beginPath(); g.arc(x + dot / 2, y - 9 * k, dot / 2, 0, Math.PI * 2); g.fill();
  g.fillStyle = 'rgba(255,255,255,0.8)';
  spaced(g, label, x + dot + 14 * k, y, sp);
}

// Plantilla "Sobre foto": PNG transparente o sobre una foto de la galería.
// layout: { align: 'left'|'center'|'right', size: 's'|'m'|'l', pos: 'bottom'|'top' }
async function drawPhoto(g, session, photo, layout = {}) {
  const align = layout.align || 'left';
  // Tamaños: la grande es la antigua mediana; la mediana, la antigua pequeña.
  const k = { s: 0.65, m: 0.8, l: 1 }[layout.size || 'm'];
  const top = layout.pos === 'top';
  const st = sessionStats(session);
  const [primary, secondary] = sessionMuscles(session);

  if (photo) {
    const r = Math.max(W / photo.width, H / photo.height);
    const pw = photo.width * r, ph = photo.height * r;
    g.drawImage(photo, (W - pw) / 2, (H - ph) / 2, pw, ph);
    const shade = top ? g.createLinearGradient(0, H * 0.55, 0, 0) : g.createLinearGradient(0, H * 0.45, 0, H);
    shade.addColorStop(0, 'rgba(0,0,0,0)'); shade.addColorStop(1, 'rgba(0,0,0,0.6)');
    g.fillStyle = shade; g.fillRect(0, 0, W, H);
  }

  // Medidas del bloque.
  const eyebrow = `${shortDay(session.dayName).toUpperCase()} · ${upperDate(session.date).replace(/^\S+\s/, '')}`;
  const vol = `${st.volume} ${st.unit}`;
  const volSize = Math.round(120 * k);
  const bodyW = Math.round((align === 'center' ? 130 : 150) * k);
  const mini = await bodyCanvas('front', primary, secondary, bodyW);
  const prs = session.exercises.reduce((a, e) => a + e.sets.filter((x) => x.pr).length, 0);
  const stats = [[st.time, 'Tiempo'], [String(st.sets), 'Series']];
  const worked = primary.slice(0, 4).map((gr) => SHORT_MUSCLE[gr] || gr).join(' · ');
  const musclesH = worked ? 50 * k : 0;
  const badgeH = prs ? 58 * k + 30 * k : 0;

  g.font = font(800, volSize);
  const volW = Math.min(g.measureText(vol).width, W - 2 * MARGIN - (align === 'center' ? 0 : bodyW + 30 * k));
  const heroH = align === 'center'
    ? mini.height + 24 * k + volSize * 0.8 + 50 * k + musclesH
    : Math.max(mini.height, volSize * 0.8 + 50 * k + musclesH);
  const eyebrowH = 32 * k + 36 * k;
  const statsH = 64 * k + 48 * k;
  const blockH = badgeH + eyebrowH + heroH + 56 * k + statsH + 64 * k + 26 * k;
  let y = top ? 250 : H - 110 - blockH;

  g.shadowColor = 'rgba(0,0,0,0.45)'; g.shadowBlur = 28; g.shadowOffsetY = 2;
  g.textAlign = 'left';

  // ¡NUEVO PR! en una cápsula dorada.
  if (prs) {
    const txt = prs === 1 ? '🏆 ¡NUEVO PR!' : `🏆 ¡${prs} NUEVOS PR!`;
    g.font = font(800, Math.round(28 * k));
    const tw = spacedWidth(g, txt, 3 * k);
    const bw = tw + 52 * k, bh = 58 * k;
    const bx = blockX(align, bw);
    const gold = g.createLinearGradient(bx, y, bx + bw, y + bh);
    gold.addColorStop(0, '#f6dc97'); gold.addColorStop(1, '#c8962e');
    g.fillStyle = gold;
    g.beginPath(); g.roundRect(bx, y, bw, bh, bh / 2); g.fill();
    g.save(); g.shadowColor = 'transparent';
    g.fillStyle = '#1a1206';
    spaced(g, txt, bx + 26 * k, y + bh / 2 + 10 * k, 3 * k);
    g.restore();
    y += badgeH;
  }

  // Fecha y día.
  g.fillStyle = '#fff'; g.font = font(700, Math.round(30 * k));
  const eyW = spacedWidth(g, eyebrow, 5 * k);
  spaced(g, eyebrow, blockX(align, eyW), y + 30 * k, 5 * k);
  y += eyebrowH;

  // Cuerpo + volumen.
  g.font = font(800, volSize);
  const labelTxt = 'VOLUMEN LEVANTADO';
  if (align === 'center') {
    g.drawImage(mini, (W - mini.width) / 2, y);
    y += mini.height + 24 * k;
    g.fillStyle = '#fff'; g.textAlign = 'center';
    g.fillText(vol, W / 2, y + volSize * 0.8, W - 2 * MARGIN);
    g.font = font(600, Math.round(26 * k)); g.fillStyle = 'rgba(255,255,255,0.85)';
    spaced(g, labelTxt, W / 2, y + volSize * 0.8 + 46 * k, 6 * k, 'center');
    if (worked) {
      g.font = font(600, Math.round(34 * k)); g.fillStyle = '#fff';
      g.fillText(worked, W / 2, y + volSize * 0.8 + 46 * k + musclesH, W - 2 * MARGIN);
    }
    y += volSize * 0.8 + 50 * k + musclesH;
  } else {
    const rowH = heroH;
    const bodyX = align === 'left' ? MARGIN - 16 * k : W - MARGIN - mini.width + 16 * k;
    g.drawImage(mini, bodyX, y + rowH - mini.height);
    const base = y + rowH - 50 * k - musclesH;
    g.fillStyle = '#fff';
    const ta = align === 'left' ? 'left' : 'right';
    g.textAlign = ta;
    const tx = align === 'left' ? bodyX + mini.width + 20 * k : bodyX - 20 * k;
    g.fillText(vol, tx, base, volW);
    g.font = font(600, Math.round(26 * k)); g.fillStyle = 'rgba(255,255,255,0.85)';
    spaced(g, labelTxt, tx, base + 46 * k, 6 * k, ta);
    if (worked) {
      g.font = font(600, Math.round(34 * k)); g.fillStyle = '#fff'; g.textAlign = ta;
      g.fillText(worked, tx, base + 46 * k + musclesH, W - MARGIN - (align === 'left' ? tx : W - tx));
    }
    y += rowH;
  }
  y += 56 * k;

  // Tiempo, series y récords.
  g.textAlign = 'left';
  const colGap = 64 * k;
  const cols = stats.map(([v, l]) => {
    g.font = font(700, Math.round(60 * k)); const vw = g.measureText(v).width;
    g.font = font(600, Math.round(22 * k)); const lw = spacedWidth(g, l.toUpperCase(), 5 * k);
    return { v, l: l.toUpperCase(), w: Math.max(vw, lw) };
  });
  const rowW = cols.reduce((a, c) => a + c.w, 0) + colGap * (cols.length - 1);
  let x = blockX(align, rowW);
  for (const c of cols) {
    const cx = align === 'center' ? x + c.w / 2 : align === 'right' ? x + c.w : x;
    const ta = align === 'center' ? 'center' : align === 'right' ? 'right' : 'left';
    g.textAlign = ta; g.fillStyle = '#fff'; g.font = font(700, Math.round(60 * k));
    g.fillText(c.v, cx, y + 60 * k);
    g.fillStyle = 'rgba(255,255,255,0.85)'; g.font = font(600, Math.round(22 * k));
    spaced(g, c.l, cx, y + 60 * k + 42 * k, 5 * k, ta);
    x += c.w + colGap;
  }
  y += statsH + 64 * k;
  g.textAlign = 'left';
  g.shadowColor = 'rgba(0,0,0,0.35)';
  brand(g, y, align, k);
  g.shadowColor = 'transparent';
}

// Devuelve el canvas de la imagen. photo: imagen de la galería (opcional).
// background: color de fondo (para miniaturas); sin él, PNG transparente.
export async function renderShare(session, { photo, layout, background } = {}) {
  const c = document.createElement('canvas');
  c.width = W; c.height = H;
  const g = c.getContext('2d');
  g.textBaseline = 'alphabetic';
  if (background && !photo) {
    const bg = g.createLinearGradient(0, 0, 0, H);
    bg.addColorStop(0, '#3a3f46'); bg.addColorStop(1, background);
    g.fillStyle = bg; g.fillRect(0, 0, W, H);
  }
  await drawPhoto(g, session, photo, layout);
  return c;
}
