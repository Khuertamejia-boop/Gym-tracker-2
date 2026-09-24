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

export function barChart(canvas, { labels, data, unit, horizontal, highlightLast, tooltipTitle }) {
  const color = css('--series-1');
  const muted = css('--heat-1');
  const colors = data.map((_, i) => (highlightLast && i !== data.length - 1 ? muted : color));
  mount(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: highlightLast ? colors : color,
        hoverBackgroundColor: color,
        borderRadius: 4,
        borderSkipped: 'start',
        maxBarThickness: horizontal ? 18 : 28,
        categoryPercentage: 0.8,
        barPercentage: 0.9,
      }],
    },
    options: base({ unit, horizontal, tooltipTitle }),
  });
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
