// Cloudflare Worker «historias»: sube, muestra y borra las fotos de las historias de 24 h (guardadas en R2).
//
// Ajustes en el panel de Cloudflare (Worker → Settings):
//   · Bindings → R2 bucket: nombre de variable  HISTORIAS  → bucket «historias»
//   · Variables (texto):    SUPABASE_URL  y  SUPABASE_ANON_KEY   (la clave pública, la misma de la app)
//
// Cómo se protege: el Worker nunca decide por su cuenta. Cada permiso se lo pregunta a Supabase usando la
// sesión del usuario (create_story, confirm_story, story_object_deletable). Las fotos tienen nombre
// imposible de adivinar y dejan de verse a las 24 h aunque Cloudflare tarde en borrarlas.
//
// Rutas:
//   POST   /s            sube la foto (JPEG, máx. 600 KB) → 201 {id, key, url, expires_at}
//   GET    /s/<ruta>     muestra la foto (410 si ya pasaron 24 h)
//   DELETE /s/<ruta>     borra el archivo (solo la dueña o un administrador, y solo si la historia ya no está activa)

const MAX_BYTES = 600 * 1024;
const TTL_MS = 24 * 60 * 60 * 1000;
const UUID = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}';
const UUID_RE = new RegExp(`^${UUID}$`);
const KEY_RE = new RegExp(`^${UUID}/${UUID}\\.jpg$`);
const ORIGINS = ['https://khuertamejia-boop.github.io']; // páginas que pueden pedir borrados (moderar.html)

const corsHeaders = (req) => {
  const o = req.headers.get('Origin');
  return ORIGINS.includes(o)
    ? { 'Access-Control-Allow-Origin': o, 'Access-Control-Allow-Methods': 'DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Authorization, Content-Type', 'Access-Control-Max-Age': '86400', Vary: 'Origin' }
    : {};
};

const json = (req, data, status = 200) => new Response(JSON.stringify(data), {
  status,
  headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', ...corsHeaders(req) },
});

// Lee el usuario del token. No se verifica aquí la firma: Supabase la verifica en cada pregunta
// y las funciones comprueban que la ruta pertenezca a auth.uid().
function userFromToken(req) {
  const h = req.headers.get('Authorization') || '';
  const token = h.startsWith('Bearer ') ? h.slice(7).trim() : '';
  const parts = token.split('.');
  if (parts.length !== 3) return null;
  try {
    const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')));
    if (!UUID_RE.test(payload.sub || '')) return null;
    if (payload.exp && payload.exp * 1000 < Date.now()) return null;
    return { id: payload.sub, token };
  } catch { return null; }
}

async function rpc(env, token, fn, args) {
  const r = await fetch(`${env.SUPABASE_URL}/rest/v1/rpc/${fn}`, {
    method: 'POST',
    headers: { apikey: env.SUPABASE_ANON_KEY, Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(args || {}),
  });
  let body = null;
  try { body = await r.json(); } catch { /* sin cuerpo */ }
  return { ok: r.ok, status: r.status, body };
}

function failure(req, res) {
  const msg = String((res.body && (res.body.message || res.body.error)) || 'Error');
  if (res.status === 401 || /JWT|No autenticado/i.test(msg)) return json(req, { error: 'Sesión caducada: vuelve a iniciar sesión' }, 401);
  if (/Ya publicaste/.test(msg)) return json(req, { error: msg }, 409);
  if (/No puedes publicar/.test(msg)) return json(req, { error: msg }, 403);
  if (res.status >= 500) return json(req, { error: 'Servidor no disponible, inténtalo en un momento' }, 502);
  return json(req, { error: msg }, 400);
}

async function upload(req, env) {
  const user = userFromToken(req);
  if (!user) return json(req, { error: 'Inicia sesión' }, 401);

  if (Number(req.headers.get('Content-Length') || 0) > MAX_BYTES) return json(req, { error: 'La foto pesa demasiado' }, 413);
  const bytes = new Uint8Array(await req.arrayBuffer());
  if (bytes.length > MAX_BYTES) return json(req, { error: 'La foto pesa demasiado' }, 413);
  const isJpeg = bytes.length > 1000 && bytes[0] === 0xff && bytes[1] === 0xd8 && bytes[2] === 0xff;
  if (!isJpeg) return json(req, { error: 'La foto debe ser un JPEG' }, 400);

  // 1) Reservar el cupo del día (si ya publicó hoy, aquí se corta y no se sube nada)
  const key = `${user.id}/${crypto.randomUUID()}.jpg`;
  const made = await rpc(env, user.token, 'create_story', { p_key: key });
  if (!made.ok) return failure(req, made);
  const id = made.body;

  // 2) Guardar la foto en R2
  try {
    await env.HISTORIAS.put(key, bytes, { httpMetadata: { contentType: 'image/jpeg' } });
  } catch {
    await rpc(env, user.token, 'cancel_story', { p_story: id });
    return json(req, { error: 'No se pudo guardar la foto, inténtalo otra vez' }, 502);
  }

  // 3) Activar la historia
  const done = await rpc(env, user.token, 'confirm_story', { p_story: id });
  if (!done.ok) {
    await env.HISTORIAS.delete(key);
    await rpc(env, user.token, 'cancel_story', { p_story: id });
    return failure(req, done);
  }
  return json(req, { id, key, url: `${new URL(req.url).origin}/s/${key}`, expires_at: done.body }, 201);
}

async function show(req, env, key) {
  const obj = await env.HISTORIAS.get(key);
  if (!obj) return new Response('No encontrada', { status: 404 });
  const left = obj.uploaded.getTime() + TTL_MS - Date.now();
  if (left <= 0) return new Response('Caducada', { status: 410 });
  return new Response(obj.body, {
    headers: {
      'Content-Type': 'image/jpeg',
      'Cache-Control': `public, max-age=${Math.min(3600, Math.floor(left / 1000))}`,
      'X-Content-Type-Options': 'nosniff',
    },
  });
}

async function remove(req, env, key) {
  const user = userFromToken(req);
  if (!user) return json(req, { error: 'Inicia sesión' }, 401);
  const ok = await rpc(env, user.token, 'story_object_deletable', { p_key: key });
  if (!ok.ok) return failure(req, ok);
  if (ok.body !== true) return json(req, { error: 'No permitido' }, 403);
  await env.HISTORIAS.delete(key);
  return new Response(null, { status: 204, headers: corsHeaders(req) });
}

export default {
  async fetch(req, env) {
    const { pathname } = new URL(req.url);
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: corsHeaders(req) });
    if (pathname === '/' && req.method === 'GET') return new Response('historias ok');

    if (pathname === '/s' && req.method === 'POST') return upload(req, env);

    if (pathname.startsWith('/s/')) {
      const key = pathname.slice(3);
      if (!KEY_RE.test(key)) return new Response('No encontrada', { status: 404 });
      if (req.method === 'GET' || req.method === 'HEAD') return show(req, env, key);
      if (req.method === 'DELETE') return remove(req, env, key);
      return new Response('Método no permitido', { status: 405 });
    }
    return new Response('No encontrada', { status: 404 });
  },
};
