// Enlaces cortos para las rutinas de entrenador (Cloudflare Worker + KV).
//
// Guarda el código de rutina «GT1-…» (el mismo de r/codigo.js) con una clave corta de 7 letras:
//   https://<este worker>/r/k7Qx2pA  →  abre la página de la rutina con el código completo
//
// API para la app de iPhone (detalles en docs/app-ios/MODO-ENTRENADOR.md, sección 7):
//   POST /api/r            cuerpo {"code":"GT1-…"}            → 201 {"id","url","editKey"}
//   PUT  /api/r/<id>       cuerpo {"code":"GT1-…"} + cabecera Authorization: Bearer <editKey> → 200 {"id","url"}
//   GET  /api/r/<id>                                          → 200 {"code"}
//   GET  /r/<id>           redirige a la página de la rutina   (404 con aviso si no existe)
//
// En Cloudflare necesita un «KV namespace» enlazado con el nombre de variable RUTINAS.

const PAGE = 'https://khuertamejia-boop.github.io/Gym-tracker-2/r/';
const MAX_CODE = 12000;
const ID_LEN = 7;
const ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789'; // sin 0/O, 1/l/I

const CODE_RE = /^GT1-[A-Za-z0-9_-]+\.[0-9a-f]{6}$/;
const ID_RE = new RegExp(`^[${ALPHABET}]{${ID_LEN}}$`);

function fnv24(text) {
  let h = 0x811c9dc5;
  for (let i = 0; i < text.length; i++) {
    h ^= text.charCodeAt(i) & 0xff;
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return (h & 0xffffff).toString(16).padStart(6, '0');
}

// Comprueba la forma y el control del código (no lo descomprime: eso lo hacen la app y la página).
function validCode(code) {
  if (typeof code !== 'string' || code.length > MAX_CODE || !CODE_RE.test(code)) return false;
  const dot = code.lastIndexOf('.');
  return fnv24(code.slice(4, dot)) === code.slice(dot + 1);
}

function randomString(len) {
  const bytes = crypto.getRandomValues(new Uint8Array(len));
  let out = '';
  for (const b of bytes) out += ALPHABET[b % ALPHABET.length];
  return out;
}

async function sha256(text) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
};

const json = (body, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', ...CORS },
});

const notFoundPage = () => new Response(`<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Rutina no encontrada</title>
<style>body{margin:0;min-height:100vh;display:grid;place-items:center;font:16px/1.45 -apple-system,system-ui,sans-serif;
background:#f4f4f2;color:#0b0b0b;text-align:center;padding:24px}p{color:#52514e;max-width:320px}
@media (prefers-color-scheme:dark){body{background:#101112;color:#fff}p{color:#c3c2b7}}</style></head>
<body><div><h1>No encontramos esta rutina</h1><p>Revisa que el enlace esté completo o pide a tu entrenador que te lo vuelva a enviar.</p></div></body></html>`,
{ status: 404, headers: { 'Content-Type': 'text/html; charset=utf-8' } });

async function readCode(request) {
  if (Number(request.headers.get('Content-Length') || 0) > MAX_CODE + 200) return null;
  try {
    const text = await request.text();
    if (text.length > MAX_CODE + 200) return null;
    const { code } = JSON.parse(text);
    return validCode(code) ? code : null;
  } catch {
    return null;
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origin = url.origin;
    const parts = url.pathname.split('/').filter(Boolean);

    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS });

    // Página: /r/<id> → redirige a la página de la rutina con el código
    if (parts[0] === 'r' && parts.length === 2 && request.method === 'GET') {
      if (!ID_RE.test(parts[1])) return notFoundPage();
      const rec = await env.RUTINAS.get(parts[1], 'json');
      if (!rec) return notFoundPage();
      return new Response(null, { status: 302, headers: { Location: `${PAGE}#${rec.code}`, 'Cache-Control': 'no-store' } });
    }

    if (parts[0] === 'api' && parts[1] === 'r') {
      // Crear
      if (parts.length === 2 && request.method === 'POST') {
        const code = await readCode(request);
        if (!code) return json({ error: 'codigo-invalido' }, 400);
        let id;
        for (let i = 0; i < 5; i++) {
          const candidate = randomString(ID_LEN);
          if (!(await env.RUTINAS.get(candidate))) { id = candidate; break; }
        }
        if (!id) return json({ error: 'intenta-de-nuevo' }, 503);
        const editKey = randomString(24);
        const now = new Date().toISOString();
        await env.RUTINAS.put(id, JSON.stringify({ code, editHash: await sha256(editKey), createdAt: now, updatedAt: now }));
        return json({ id, url: `${origin}/r/${id}`, editKey }, 201);
      }

      if (parts.length === 3 && ID_RE.test(parts[2])) {
        const id = parts[2];
        // Leer (la app del alumno, cuando pega un enlace corto)
        if (request.method === 'GET') {
          const rec = await env.RUTINAS.get(id, 'json');
          return rec ? json({ code: rec.code }) : json({ error: 'no-existe' }, 404);
        }
        // Actualizar (el entrenador corrige la rutina: el mismo enlace muestra la versión nueva)
        if (request.method === 'PUT') {
          const rec = await env.RUTINAS.get(id, 'json');
          if (!rec) return json({ error: 'no-existe' }, 404);
          const key = (request.headers.get('Authorization') || '').replace(/^Bearer\s+/i, '');
          if (!key || (await sha256(key)) !== rec.editHash) return json({ error: 'sin-permiso' }, 403);
          const code = await readCode(request);
          if (!code) return json({ error: 'codigo-invalido' }, 400);
          await env.RUTINAS.put(id, JSON.stringify({ ...rec, code, updatedAt: new Date().toISOString() }));
          return json({ id, url: `${origin}/r/${id}` });
        }
      }
      return json({ error: 'no-encontrado' }, 404);
    }

    if (url.pathname === '/' || url.pathname === '') return Response.redirect(PAGE, 302);
    return json({ error: 'no-encontrado' }, 404);
  },
};
