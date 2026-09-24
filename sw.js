// Service worker: permite usar la app sin conexión en el gym.
// Sirve la versión en caché al instante y la actualiza en segundo plano.
const CACHE = 'gymtrack-v1';
const SHELL = [
  './', 'index.html', 'css/styles.css', 'manifest.webmanifest', 'icons/icon.svg',
  'js/app.js', 'js/store.js', 'js/charts.js', 'js/data/exercises.js', 'js/data/templates.js',
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

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    caches.open(CACHE).then(async (cache) => {
      const cached = await cache.match(e.request, { ignoreSearch: true });
      const network = fetch(e.request)
        .then((res) => { if (res.ok) cache.put(e.request, res.clone()); return res; })
        .catch(() => cached);
      return cached || network;
    }),
  );
});
