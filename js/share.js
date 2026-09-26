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
const GRAY = '#8e8e93';
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

function fitText(g, text, maxWidth, weight, size) {
  let s = size;
  g.font = font(weight, s);
  while (g.measureText(text).width > maxWidth && s > 20) { s -= 2; g.font = font(weight, s); }
  return s;
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

// Mejor récord del entrenamiento y la marca anterior de ese ejercicio.
export function bestRecord(session) {
  let best = null;
  for (const e of session.exercises) {
    for (const x of e.sets) {
      if (!x.pr) continue;
      if (!best || (x.pr === 'peso') > (best.set.pr === 'peso') || Number(x.kg) > Number(best.set.kg)) best = { e, set: x };
    }
  }
  if (!best) return null;
  let prev = 0;
  for (const s of S.getState().sessions) {
    if (s.id === session.id || s.date > session.date) continue;
    for (const e of s.exercises) if (e.exId === best.e.exId) for (const x of e.sets) prev = Math.max(prev, Number(x.kg) || 0);
  }
  return { ...best, prev };
}

function brand(g, y, align = 'center', x = W / 2) {
  g.font = font(600, 28);
  g.fillStyle = GRAY;
  const label = 'MI GYM TRACKER';
  const w = [...label].reduce((a, ch) => a + g.measureText(ch).width, 0) + 7 * (label.length - 1);
  const start = align === 'center' ? x - (w + 30) / 2 : x;
  g.fillStyle = ACCENT;
  g.beginPath(); g.arc(start + 8, y - 10, 8, 0, Math.PI * 2); g.fill();
  g.fillStyle = align === 'center' ? GRAY : 'rgba(255,255,255,0.75)';
  spaced(g, label, start + 30, y, 7);
}

function statsRow(g, stats, y, { x0 = 80, x1 = W - 80, big = 76, label = 26, color = '#fff' } = {}) {
  const colW = (x1 - x0) / stats.length;
  stats.forEach(([v, l], k) => {
    const x = x0 + colW * k;
    g.fillStyle = color; g.font = font(700, big); g.textAlign = 'left';
    g.fillText(v, x, y);
    g.fillStyle = color === '#fff' ? GRAY : 'rgba(255,255,255,0.8)'; g.font = font(600, label);
    spaced(g, l.toUpperCase(), x, y + 48, 5);
  });
}

async function drawCard(g, session) {
  const st = sessionStats(session);
  const [primary, secondary] = sessionMuscles(session);
  g.fillStyle = '#0b0b0c'; g.fillRect(0, 0, W, H);
  const glow = g.createRadialGradient(W / 2, 820, 60, W / 2, 820, 820);
  glow.addColorStop(0, 'rgba(217,35,58,0.30)'); glow.addColorStop(1, 'rgba(217,35,58,0)');
  g.fillStyle = glow; g.fillRect(0, 0, W, H);

  g.fillStyle = GRAY; g.font = font(600, 30);
  spaced(g, `${upperDate(session.date)} · ${shortDay(session.dayName).toUpperCase()}`, 80, 170, 6);
  g.fillStyle = '#fff'; g.font = font(800, 96);
  g.fillText('Entrenamiento', 80, 290); g.fillText('completado', 80, 395);

  const bw = 600;
  const [front, back] = await Promise.all([bodyCanvas('front', primary, secondary, bw), bodyCanvas('back', primary, secondary, bw)]);
  g.drawImage(front, W / 2 - bw + 50, 470);
  g.drawImage(back, W / 2 - 50, 470);

  g.fillStyle = 'rgba(255,255,255,0.12)'; g.fillRect(80, 1480, W - 160, 2);
  statsRow(g, [[st.timeShort, 'Tiempo'], [String(st.sets), 'Series'], [st.volume, st.unit]], 1620);
  brand(g, 1830);
}

async function drawPhoto(g, session, photo) {
  const st = sessionStats(session);
  const [primary, secondary] = sessionMuscles(session);
  if (photo) {
    const r = Math.max(W / photo.width, H / photo.height);
    const pw = photo.width * r, ph = photo.height * r;
    g.drawImage(photo, (W - pw) / 2, (H - ph) / 2, pw, ph);
    const shade = g.createLinearGradient(0, H * 0.45, 0, H);
    shade.addColorStop(0, 'rgba(0,0,0,0)'); shade.addColorStop(1, 'rgba(0,0,0,0.62)');
    g.fillStyle = shade; g.fillRect(0, 0, W, H);
  }
  g.shadowColor = 'rgba(0,0,0,0.45)'; g.shadowBlur = 28; g.shadowOffsetY = 2;
  g.fillStyle = '#fff'; g.font = font(700, 32);
  spaced(g, `${shortDay(session.dayName).toUpperCase()} · ${upperDate(session.date).replace(/^\S+\s/, '')}`, 80, 1250, 5);

  const mini = await bodyCanvas('front', primary, secondary, 230);
  g.drawImage(mini, 64, 1290);
  const vol = `${st.volume} ${st.unit}`;
  const size = fitText(g, vol, W - 360 - 80, 800, 132);
  g.fillStyle = '#fff'; g.font = font(800, size);
  g.fillText(vol, 330, 1560);
  g.font = font(600, 28); g.fillStyle = 'rgba(255,255,255,0.85)';
  spaced(g, 'VOLUMEN LEVANTADO', 334, 1612, 6);

  const prs = session.exercises.reduce((a, e) => a + e.sets.filter((x) => x.pr).length, 0);
  const row = [[st.time, 'Tiempo'], [String(st.sets), 'Series']];
  if (prs) row.push([`🏆 ${prs}`, prs === 1 ? 'Récord' : 'Récords']);
  statsRow(g, row, 1745, { x1: 80 + 260 * row.length, big: 64, label: 24, color: '#fff' });
  g.shadowColor = 'transparent';
  brand(g, 1860, 'left', 80);
}

async function drawRecord(g, session) {
  const st = sessionStats(session);
  const rec = bestRecord(session);
  const bg = g.createLinearGradient(0, 0, 0, H);
  bg.addColorStop(0, '#141416'); bg.addColorStop(1, '#0b0b0c');
  g.fillStyle = bg; g.fillRect(0, 0, W, H);
  g.textAlign = 'center';
  g.fillStyle = GRAY; g.font = font(600, 32);
  spaced(g, 'NUEVO RÉCORD PERSONAL', W / 2, 250, 8, 'center');

  const cx = W / 2, cy = 590, r = 190;
  const halo = g.createRadialGradient(cx, cy, r * 0.6, cx, cy, r * 2);
  halo.addColorStop(0, 'rgba(224,176,74,0.35)'); halo.addColorStop(1, 'rgba(224,176,74,0)');
  g.fillStyle = halo; g.fillRect(0, cy - r * 2, W, r * 4);
  const medal = g.createRadialGradient(cx - 60, cy - 70, 20, cx, cy, r);
  medal.addColorStop(0, '#f6dc97'); medal.addColorStop(0.6, '#c8962e'); medal.addColorStop(1, '#8a6418');
  g.fillStyle = medal; g.beginPath(); g.arc(cx, cy, r, 0, Math.PI * 2); g.fill();
  g.font = font(400, 170); g.textBaseline = 'middle'; g.fillText('🏆', cx, cy + 8); g.textBaseline = 'alphabetic';

  const u = S.unitFor(rec.e.exId);
  const fmt = (kg) => S.toUnit(kg, u).toLocaleString('es', { maximumFractionDigits: 1 });
  const value = `${fmt(rec.set.kg)} ${u}`;
  g.fillStyle = '#fff'; g.font = font(800, fitText(g, value, W - 160, 800, 190));
  g.fillText(value, cx, 1010);
  const name = S.exById(rec.e.exId).name;
  g.font = font(600, fitText(g, name, W - 160, 600, 60));
  g.fillText(name, cx, 1105);
  const diff = Number(rec.set.kg) - rec.prev;
  const sub = rec.set.pr === 'peso' && rec.prev && diff > 0
    ? `Antes: ${fmt(rec.prev)} ${u} · +${fmt(diff)} ${u}`
    : `${rec.set.reps} repeticiones · tu mejor serie`;
  g.fillStyle = GRAY; g.font = font(500, 40); g.fillText(sub, cx, 1175);

  g.fillStyle = 'rgba(255,255,255,0.12)'; g.fillRect(80, 1300, W - 160, 2);
  g.textAlign = 'left';
  const cols = [[st.timeShort, 'Tiempo'], [String(st.sets), 'Series'], [st.volume, st.unit]];
  const colW = (W - 160) / 3;
  cols.forEach(([v, l], k) => {
    const x = 80 + colW * k + colW / 2;
    g.textAlign = 'center'; g.fillStyle = '#fff'; g.font = font(700, 76); g.fillText(v, x, 1440);
    g.fillStyle = GRAY; g.font = font(600, 26); spaced(g, l.toUpperCase(), x, 1488, 5, 'center');
  });
  brand(g, 1830);
}

// Devuelve el canvas de la plantilla pedida. photo: imagen de la galería (plantilla 'photo').
export async function renderShare(kind, session, { photo } = {}) {
  const c = document.createElement('canvas');
  c.width = W; c.height = H;
  const g = c.getContext('2d');
  g.textBaseline = 'alphabetic';
  if (kind === 'record') await drawRecord(g, session);
  else if (kind === 'photo') await drawPhoto(g, session, photo);
  else await drawCard(g, session);
  return c;
}
