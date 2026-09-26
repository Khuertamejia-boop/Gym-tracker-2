// Imagen para compartir un entrenamiento (formato historia 1080 × 1920): un "sticker"
// con los datos que se coloca sobre una foto o se guarda como PNG transparente.
// El cuerpo con los músculos se dibuja en el canvas con los mismos contornos del
// mapa muscular, para que salga nítido en la imagen.
import * as S from './store.js';
import { getMuscles, defaultBody, PX2MM, VIEWBOX_WIDTH, VIEWBOX_HEIGHT } from './vendor/muscle-map/index.js';
import { bodyGender, sessionMuscles, musclesFor } from './body.js';

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

// Colores del texto: blanco (con sombra suave) o negro (sin sombra).
export const INKS = {
  white: { fg: '#fff', soft: 'rgba(255,255,255,0.85)', brand: 'rgba(255,255,255,0.8)', shadow: 'rgba(0,0,0,0.45)', brandShadow: 'rgba(0,0,0,0.35)', glass: 'rgba(255,255,255,0.16)', ring: 'rgba(255,255,255,0.85)' },
  black: { fg: '#111', soft: 'rgba(17,17,17,0.8)', brand: 'rgba(17,17,17,0.75)', shadow: 'transparent', brandShadow: 'transparent', glass: 'rgba(255,255,255,0.35)', ring: 'rgba(17,17,17,0.85)' },
};

function brand(g, y, align, k, ink = INKS.white) {
  g.font = font(600, Math.round(26 * k));
  const label = 'MI GYM TRACKER';
  const sp = 6 * k;
  const dot = 16 * k;
  const w = dot + 14 * k + spacedWidth(g, label, sp);
  const x = blockX(align, w);
  g.fillStyle = ACCENT;
  g.beginPath(); g.arc(x + dot / 2, y - 9 * k, dot / 2, 0, Math.PI * 2); g.fill();
  g.fillStyle = ink.brand;
  spaced(g, label, x + dot + 14 * k, y, sp);
}

// Los 3 músculos con más series hechas (en empate, el orden del entrenamiento), sin repetir nombre.
function topMuscles(session, primary) {
  const sets = new Map(primary.map((gr) => [gr, 0]));
  for (const e of session.exercises) {
    const done = e.sets.filter((x) => x.done).length || e.sets.length;
    for (const gr of musclesFor(e.exId)[0]) if (sets.has(gr)) sets.set(gr, sets.get(gr) + done);
  }
  const names = [...sets.entries()].sort((a, b) => b[1] - a[1]).map(([gr]) => SHORT_MUSCLE[gr] || gr);
  return [...new Set(names)].slice(0, 3);
}

// Bloque de datos (el "sticker") dibujado a tamaño natural (k = 1).
async function drawBlock(g, session, align, y, ink) {
  const k = 1;
  const st = sessionStats(session);
  const [primary, secondary] = sessionMuscles(session);
  const eyebrow = `${shortDay(session.dayName).toUpperCase()} · ${upperDate(session.date).replace(/^\S+\s/, '')}`;
  const vol = `${st.volume} ${st.unit}`;
  const volSize = 120;
  const mini = await bodyCanvas('front', primary, secondary, align === 'center' ? 130 : 150);
  const prs = session.exercises.reduce((a, e) => a + e.sets.filter((x) => x.pr).length, 0);
  const stats = [[st.time, 'Tiempo'], [String(st.sets), 'Series']];
  const worked = topMuscles(session, primary).join(' · ');
  const musclesH = worked ? 50 : 0;
  const heroH = align === 'center'
    ? mini.height + 24 + volSize * 0.8 + 50 + musclesH
    : Math.max(mini.height, volSize * 0.8 + 50 + musclesH);

  g.shadowColor = ink.shadow; g.shadowBlur = 28; g.shadowOffsetY = 2;
  g.textAlign = 'left';

  // ¡NUEVO PR! en una cápsula de cristal, con el mismo color que el resto.
  if (prs) {
    const txt = prs === 1 ? '¡NUEVO PR!' : `¡${prs} NUEVOS PR!`;
    g.font = font(800, 28);
    const tw = spacedWidth(g, txt, 4);
    const bw = tw + 52, bh = 58;
    const bx = blockX(align, bw);
    g.save();
    g.shadowColor = 'transparent';
    g.fillStyle = ink.glass;
    g.strokeStyle = ink.ring; g.lineWidth = 2.5;
    g.beginPath(); g.roundRect(bx, y, bw, bh, bh / 2); g.fill(); g.stroke();
    g.restore();
    g.fillStyle = ink.fg; g.font = font(800, 28);
    spaced(g, txt, bx + 26, y + bh / 2 + 10, 4);
    y += bh + 30;
  }

  // Fecha y día.
  g.fillStyle = ink.fg; g.font = font(700, 30);
  spaced(g, eyebrow, blockX(align, spacedWidth(g, eyebrow, 5)), y + 30, 5);
  y += 68;

  // Cuerpo + volumen + músculos.
  g.font = font(800, volSize);
  const labelTxt = 'VOLUMEN LEVANTADO';
  if (align === 'center') {
    g.drawImage(mini, (W - mini.width) / 2, y);
    y += mini.height + 24;
    g.fillStyle = ink.fg; g.textAlign = 'center';
    g.fillText(vol, W / 2, y + volSize * 0.8, W - 2 * MARGIN);
    g.font = font(600, 26); g.fillStyle = ink.soft;
    spaced(g, labelTxt, W / 2, y + volSize * 0.8 + 46, 6, 'center');
    if (worked) {
      g.font = font(600, 34); g.fillStyle = ink.fg;
      g.fillText(worked, W / 2, y + volSize * 0.8 + 46 + musclesH, W - 2 * MARGIN);
    }
    y += volSize * 0.8 + 50 + musclesH;
  } else {
    const bodyX = align === 'left' ? MARGIN - 16 : W - MARGIN - mini.width + 16;
    g.drawImage(mini, bodyX, y + heroH - mini.height);
    const base = y + heroH - 50 - musclesH;
    const ta = align === 'left' ? 'left' : 'right';
    const tx = align === 'left' ? bodyX + mini.width + 20 : bodyX - 20;
    const maxW = align === 'left' ? W - MARGIN - tx : tx - MARGIN;
    g.fillStyle = ink.fg; g.textAlign = ta;
    g.fillText(vol, tx, base, maxW);
    g.font = font(600, 26); g.fillStyle = ink.soft;
    spaced(g, labelTxt, tx, base + 46, 6, ta);
    if (worked) {
      g.font = font(600, 34); g.fillStyle = ink.fg; g.textAlign = ta;
      g.fillText(worked, tx, base + 46 + musclesH, maxW);
    }
    y += heroH;
  }
  y += 56;

  // Tiempo y series.
  const colGap = 64;
  const cols = stats.map(([v, l]) => {
    g.font = font(700, 60); const vw = g.measureText(v).width;
    g.font = font(600, 22); const lw = spacedWidth(g, l.toUpperCase(), 5);
    return { v, l: l.toUpperCase(), w: Math.max(vw, lw) };
  });
  const rowW = cols.reduce((a, c) => a + c.w, 0) + colGap * (cols.length - 1);
  let x = blockX(align, rowW);
  const ta = align === 'center' ? 'center' : align === 'right' ? 'right' : 'left';
  for (const c of cols) {
    const cx = align === 'center' ? x + c.w / 2 : align === 'right' ? x + c.w : x;
    g.textAlign = ta; g.fillStyle = ink.fg; g.font = font(700, 60);
    g.fillText(c.v, cx, y + 60);
    g.fillStyle = ink.soft; g.font = font(600, 22);
    spaced(g, c.l, cx, y + 102, 5, ta);
    x += c.w + colGap;
  }
  y += 176;
  g.textAlign = 'left';
  g.shadowColor = ink.brandShadow;
  brand(g, y, align, k, ink);
  g.shadowColor = 'transparent';
  return y + 30;
}

// Sticker recortado a su contenido (transparente). Se cachea por entrenamiento, alineación y color.
const stickers = new Map();
export function renderSticker(session, align = 'left', color = 'white') {
  const key = `${session.id}|${session.editedAt || session.finishedAt}|${align}|${color}|${bodyGender()}`;
  if (!stickers.has(key)) {
    stickers.set(key, (async () => {
      const c = document.createElement('canvas');
      c.width = W; c.height = 1400;
      const g = c.getContext('2d');
      g.textBaseline = 'alphabetic';
      const bottom = await drawBlock(g, session, align, 60, INKS[color] || INKS.white);
      // Recorte por los píxeles visibles (incluida la sombra).
      const { data } = g.getImageData(0, 0, W, Math.min(c.height, bottom + 60));
      let x0 = W, x1 = 0, y0 = c.height, y1 = 0;
      const rows = Math.min(c.height, bottom + 60);
      for (let yy = 0; yy < rows; yy++) {
        for (let xx = 0; xx < W; xx++) {
          if (data[(yy * W + xx) * 4 + 3] > 8) {
            if (xx < x0) x0 = xx; if (xx > x1) x1 = xx;
            if (yy < y0) y0 = yy; if (yy > y1) y1 = yy;
          }
        }
      }
      const out = document.createElement('canvas');
      out.width = Math.max(1, x1 - x0 + 1); out.height = Math.max(1, y1 - y0 + 1);
      out.getContext('2d').drawImage(c, x0, y0, out.width, out.height, 0, 0, out.width, out.height);
      return out;
    })());
  }
  return stickers.get(key);
}

// Color automático sobre una foto: negro si la zona detrás del bloque es clara, blanco si es oscura.
export function autoInk(photo, sticker, t) {
  const sw = 108, sh = 192;
  const c = document.createElement('canvas'); c.width = sw; c.height = sh;
  const g = c.getContext('2d', { willReadFrequently: true });
  const r = Math.max(sw / photo.width, sh / photo.height);
  g.drawImage(photo, (sw - photo.width * r) / 2, (sh - photo.height * r) / 2, photo.width * r, photo.height * r);
  const k = sw / W;
  const hw = (sticker.width * t.s) / 2, hh = (sticker.height * t.s) / 2;
  const x0 = Math.max(0, Math.floor((t.cx - hw) * k)), x1 = Math.min(sw, Math.ceil((t.cx + hw) * k));
  const y0 = Math.max(0, Math.floor((t.cy - hh) * k)), y1 = Math.min(sh, Math.ceil((t.cy + hh) * k));
  if (x1 <= x0 || y1 <= y0) return 'white';
  const { data } = g.getImageData(x0, y0, x1 - x0, y1 - y0);
  let sum = 0;
  for (let i = 0; i < data.length; i += 4) sum += 0.2126 * data[i] + 0.7152 * data[i + 1] + 0.0722 * data[i + 2];
  return sum / (data.length / 4) > 150 ? 'black' : 'white';
}

// Posición inicial: abajo, con el margen de siempre y el 80 % del tamaño natural.
export function defaultTransform(sticker, align = 'left') {
  const s = 0.8;
  const w = sticker.width * s, h = sticker.height * s;
  const cx = align === 'center' ? W / 2 : align === 'right' ? W - 60 - w / 2 : 60 + w / 2;
  return { cx, cy: H - 130 - h / 2, s };
}

// Imagen final: foto (o transparente / fondo) + sticker en la posición y tamaño elegidos.
export function composeShare({ sticker, photo, t, background, backgroundTop = '#3a3f46' }) {
  const c = document.createElement('canvas');
  c.width = W; c.height = H;
  const g = c.getContext('2d');
  if (photo) {
    const r = Math.max(W / photo.width, H / photo.height);
    const pw = photo.width * r, ph = photo.height * r;
    g.drawImage(photo, (W - pw) / 2, (H - ph) / 2, pw, ph);
  } else if (background) {
    const bg = g.createLinearGradient(0, 0, 0, H);
    bg.addColorStop(0, backgroundTop); bg.addColorStop(1, background);
    g.fillStyle = bg; g.fillRect(0, 0, W, H);
  }
  const w = sticker.width * t.s, h = sticker.height * t.s;
  g.save();
  g.translate(t.cx, t.cy);
  if (t.r) g.rotate(t.r);
  g.drawImage(sticker, -w / 2, -h / 2, w, h);
  g.restore();
  return c;
}

// Atajo para la miniatura del resumen.
export async function renderShare(session, { photo, layout = {}, background } = {}) {
  const align = layout.align || 'left';
  const color = layout.color || 'white';
  const sticker = await renderSticker(session, align, color);
  const t = layout.t || defaultTransform(sticker, align);
  // Con texto negro, la miniatura va sobre un fondo claro para que se lea.
  return color === 'black'
    ? composeShare({ sticker, photo, t, background: background && '#d9d9de', backgroundTop: '#f5f5f7' })
    : composeShare({ sticker, photo, t, background });
}
