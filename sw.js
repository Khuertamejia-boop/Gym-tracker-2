// Service worker: permite usar la app sin conexión en el gym.
// Archivos propios: primero la red (para recibir actualizaciones al momento)
// y, si no hay conexión o tarda demasiado, la copia guardada.
// Librerías del CDN: primero la copia guardada (nunca cambian de versión).
// Las peticiones a Supabase (datos y sesión) nunca se guardan en caché.
const CACHE = 'gymtrack-v9';
const SHELL = [
  './', 'index.html', 'css/styles.css', 'manifest.webmanifest', 'icons/icon.svg',
  'js/app.js', 'js/store.js', 'js/charts.js', 'js/cloud.js', 'js/config.js',
  'js/data/exercises.js', 'js/data/templates.js', 'js/data/muscles.js', 'js/body.js',
  'js/vendor/muscle-map/index.js', 'js/vendor/muscle-map/chunk-CGKLCEZK.js',
  ...['male', 'female'].flatMap((g) => ['front', 'back'].flatMap((v) => ['light', 'dark'].map((t) => `js/vendor/muscle-map/bodies/${g}-${v}-${t}.webp`))),
  'https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js',
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

const timeout = (ms) => new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), ms));

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET') return;
  const sameOrigin = url.origin === self.location.origin;
  const cdn = url.hostname === 'cdn.jsdelivr.net';
  if (!sameOrigin && !cdn) return; // Supabase y demás: directo a la red

  if (cdn) {
    e.respondWith(caches.open(CACHE).then(async (cache) => {
      const hit = await cache.match(e.request);
      if (hit) return hit;
      const res = await fetch(e.request);
      if (res.ok) cache.put(e.request, res.clone());
      return res;
    }));
    return;
  }

  e.respondWith(caches.open(CACHE).then(async (cache) => {
    try {
      const res = await Promise.race([fetch(e.request), timeout(4000)]);
      if (res.ok) cache.put(e.request, res.clone());
      return res;
    } catch {
      const hit = await cache.match(e.request, { ignoreSearch: true });
      return hit || Response.error();
    }
  }));
});
