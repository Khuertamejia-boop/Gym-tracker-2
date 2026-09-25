// Envoltorio fino sobre Chart.js que toma los colores de los tokens CSS
// para que los gráficos respeten el modo claro/oscuro.
const instances = new Map();

const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

export function destroyCharts() {
  for (const c of instances.values()) c.destroy();
  instances.clear();
}

function base({ unit = '', horizontal = false, tooltipTitle } = {}) {
  const text2 = css('--text-2');
  const grid = css('--grid');
  const fmt = (v) => `${Math.round(v).toLocaleString('es')}${unit ? ' ' + unit : ''}`;
  const valueAxis = {
    beginAtZero: true,
    grid: { color: grid, drawTicks: false },
    border: { display: false },
    ticks: { color: text2, padding: 6, maxTicksLimit: 5, callback: (v) => compact(v) },
  };
  const catAxis = {
    grid: { display: false },
    border: { color: grid },
    ticks: { color: text2, autoSkip: true, maxRotation: 0, padding: 4 },
  };
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 250 },
    indexAxis: horizontal ? 'y' : 'x',
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: css('--text'),
        titleColor: css('--bg'),
        bodyColor: css('--bg'),
        padding: 10,
        cornerRadius: 8,
        displayColors: false,
        callbacks: {
          title: tooltipTitle ? (items) => tooltipTitle(items[0].dataIndex) : undefined,
          label: (ctx) => fmt(horizontal ? ctx.parsed.x : ctx.parsed.y),
        },
      },
    },
    scales: horizontal ? { x: valueAxis, y: catAxis } : { x: catAxis, y: valueAxis },
  };
}

function compact(v) {
  if (Math.abs(v) >= 1000) return (v / 1000).toLocaleString('es', { maximumFractionDigits: 1 }) + 'k';
  return v.toLocaleString('es');
}

function mount(canvas, config) {
  if (!window.Chart || !canvas) return;
  const prev = instances.get(canvas.id);
  if (prev) prev.destroy();
  instances.set(canvas.id, new window.Chart(canvas, config));
}

export function lineChart(canvas, { labels, data, unit, tooltipTitle }) {
  const color = css('--series-1');
  const opts = base({ unit, tooltipTitle });
  opts.scales.y.beginAtZero = false;
  opts.scales.y.ticks.callback = (v) => v.toLocaleString('es', { maximumFractionDigits: 1 });
  opts.plugins.tooltip.callbacks.label = (ctx) =>
    `${ctx.parsed.y.toLocaleString('es', { maximumFractionDigits: 1 })} ${unit}`;
  mount(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        data,
        borderColor: color,
        backgroundColor: color,
        borderWidth: 2,
        pointRadius: data.length > 30 ? 0 : 4,
        pointHoverRadius: 6,
        pointBorderColor: css('--surface'),
        pointBorderWidth: 2,
        tension: 0.25,
        spanGaps: true,
      }],
    },
    options: opts,
  });
}

// '#8f8e86' → 'rgba(143,142,134,a)' (Safari no admite color-mix en los degradados del canvas).
function rgba(hex, a) {
  const h = hex.replace('#', '');
  const n = parseInt(h.length === 3 ? h.split('').map((c) => c + c).join('') : h, 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
}

const MONTHS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];

// Mini gráfico de evolución: línea gris con área suave, puntos en el color
// principal, eje de valores a la derecha y fechas reales en el eje X.
export function sparkArea(canvas, { points, unit }) {
  if (!window.Chart || !canvas) return;
  const accent = css('--accent');
  const line = css('--text-3');
  const grid = css('--grid');
  const text3 = css('--text-3');
  const span = points[points.length - 1].x - points[0].x;
  const long = span > 150 * 86400000;
  const fmtDate = (t) => {
    const d = new Date(t);
    return long ? `${MONTHS[d.getMonth()]} ${String(d.getFullYear()).slice(2)}` : `${d.getDate()} ${MONTHS[d.getMonth()]}`;
  };
  const fmtVal = (v) => (v >= 10000 ? compact(v) : v.toLocaleString('es', { maximumFractionDigits: 1 }));
  const ys = points.map((p) => p.y);
  const lo = Math.min(...ys), hi = Math.max(...ys);
  const pad = Math.max((hi - lo) * 0.18, hi * 0.04, 1);
  const ctx = canvas.getContext('2d');
  const fill = ctx.createLinearGradient(0, 0, 0, canvas.clientHeight || 120);
  fill.addColorStop(0, rgba(line, 0.32));
  fill.addColorStop(1, rgba(line, 0));
  mount(canvas, {
    type: 'line',
    data: {
      datasets: [{
        data: points,
        borderColor: line,
        borderWidth: 1.5,
        backgroundColor: fill,
        fill: 'start',
        tension: 0,
        pointRadius: points.length > 40 ? 2 : 3,
        pointHoverRadius: 5,
        pointBackgroundColor: accent,
        pointBorderWidth: 0,
        clip: 8,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 250 },
      layout: { padding: { top: 6, left: 6 } },
      interaction: { mode: 'nearest', intersect: false, axis: 'x' },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: css('--text'), titleColor: css('--bg'), bodyColor: css('--bg'),
          padding: 8, cornerRadius: 8, displayColors: false,
          callbacks: {
            title: (items) => { const d = new Date(items[0].parsed.x); return `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`; },
            label: (c) => `${fmtVal(c.parsed.y)} ${unit}`,
          },
        },
      },
      scales: {
        x: {
          type: 'linear',
          min: points[0].x, max: points[points.length - 1].x,
          grid: { display: false }, border: { display: false },
          ticks: { color: text3, maxTicksLimit: 3, maxRotation: 0, font: { size: 11 }, callback: (v) => fmtDate(v) },
          afterBuildTicks: (axis) => {
            const { min, max } = axis;
            axis.ticks = [min, (min + max) / 2, max].map((value) => ({ value }));
          },
        },
        y: {
          position: 'right',
          min: Math.max(0, Math.floor(lo - pad)), max: Math.ceil(hi + pad),
          grid: { color: grid, drawTicks: false }, border: { display: false },
          ticks: { color: text3, maxTicksLimit: 4, padding: 6, font: { size: 11 }, callback: (v, i, ticks) => ((i === 0 || i === ticks.length - 1) && v % 5 ? '' : fmtVal(Math.round(v))) },
        },
      },
    },
  });
}
