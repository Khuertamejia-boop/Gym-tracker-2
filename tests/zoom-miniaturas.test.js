// Prueba de navegador (Playwright). Se ejecuta con tests/run.sh.
// Miniaturas con zoom al músculo principal de cada ejercicio (hombre y mujer, claro y oscuro).
const { chromium, devices } = require('playwright'); const OUT = process.env.OUT;
const IDS = ['press-banca', 'remo-barra', 'press-hombro-mancuernas', 'jalon-pecho', 'curl-barra-z', 'extension-polea',
  'sentadilla-bulgara', 'extension-cuadriceps', 'curl-femoral-sentado', 'elevacion-talones-pie', 'elevaciones-laterales', 'face-pull'];
(async () => { const b = await chromium.launch(); const errs = [];
  for (const [gender, scheme] of [['male', 'light'], ['female', 'dark']]) {
    const ctx = await b.newContext({ ...devices['iPhone 13'], colorScheme: scheme });
    const p = await ctx.newPage(); p.on('pageerror', e => errs.push(e.message));
    await p.goto('http://localhost:8766/js/vendor/muscle-map/README.md');
    const boxes = await p.evaluate(async ({ IDS, gender, scheme }) => {
      localStorage.setItem('gymtrack.v1', JSON.stringify({ profile: { gender } }));
      document.body.innerHTML = `<style>body{margin:0;padding:12px;background:${scheme === 'dark' ? '#101112' : '#f4f4f2'};display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
        .t{width:80px;height:80px;border-radius:14px;overflow:hidden;background:${scheme === 'dark' ? '#1a1a19' : '#fff'}}.t>div{width:100%;height:100%}
        .r{width:60px;height:90px}</style>` + IDS.map(id => `<div class="t"><div data-muscle-map="${id}" data-thumb></div></div>`).join('')
        + IDS.slice(0, 4).map(id => `<div class="t r"><div data-muscle-map="${id}" data-thumb="tall"></div></div>`).join('');
      const { mountMuscleMaps } = await import('/js/body.js'); mountMuscleMaps();
      return [...document.querySelectorAll('[data-thumb] svg')].map(s => s.getAttribute('viewBox'));
    }, { IDS, gender, scheme });
    await p.waitForTimeout(800);
    console.log(gender, 'distinct boxes:', new Set(boxes).size, 'of', boxes.length);
    await p.screenshot({ path: OUT + `/zoom-${gender}-${scheme}.png` });
    await ctx.close();
  }
  console.log('errors', JSON.stringify(errs)); await b.close(); })();
