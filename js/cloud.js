// Inicio de sesión y sincronización con Supabase.
// Cada usuario tiene una fila en la tabla gym_data con una copia de sus datos.
// Al sincronizar se descarga la copia de la nube, se fusiona con la local
// (sin perder entrenamientos de ningún dispositivo) y se sube el resultado.
import { SUPABASE_URL, SUPABASE_ANON_KEY } from './config.js';
import * as S from './store.js';

const SUPABASE_JS = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.117.1/+esm';

let client = null;
let user = null;
let status = 'idle'; // idle | syncing | ok | error | offline
let error = '';
let lastSync = null;
let timer = null;
let running = null;
let again = false;
const listeners = [];
let onRemoteChange = () => {};

export const isConfigured = () => Boolean(SUPABASE_URL && SUPABASE_ANON_KEY);
export const getUser = () => user;
export const getInfo = () => ({ status, error, lastSync });
export const onChange = (fn) => listeners.push(fn);
const emit = () => listeners.forEach((fn) => fn());

export async function initCloud({ onData }) {
  onRemoteChange = onData;
  if (!isConfigured()) return;
  try {
    const { createClient } = await import(SUPABASE_JS);
    client = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
      auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
    });
    const { data } = await client.auth.getSession();
    user = data.session?.user || null;
    client.auth.onAuthStateChange((event, session) => {
      const prev = user?.id;
      user = session?.user || null;
      if (event === 'PASSWORD_RECOVERY') askNewPassword();
      if (user && user.id !== prev) sync();
      emit();
    });
    S.onSave(scheduleSync);
    document.addEventListener('visibilitychange', () => document.visibilityState === 'visible' && sync());
    window.addEventListener('online', () => sync());
    emit();
    if (user) sync();
  } catch (e) {
    status = 'error';
    error = 'No se pudo cargar el servicio de sincronización (¿sin conexión?).';
    emit();
  }
}

function scheduleSync() {
  if (!user) return;
  clearTimeout(timer);
  timer = setTimeout(sync, 1500);
}

const stripDraft = (st) => {
  const { draft, ...rest } = st;
  return rest;
};

export async function sync() {
  if (!client || !user) return;
  if (running) { again = true; return running; }
  running = (async () => {
    status = 'syncing';
    emit();
    try {
      const { data, error: err } = await client.from('gym_data').select('data').eq('user_id', user.id).maybeSingle();
      if (err) throw err;
      const local = S.getState();
      let next = local;
      if (data?.data) {
        // Un dispositivo nuevo que solo tiene la rutina de ejemplo adopta la copia de la nube tal cual.
        const pristine = !local.sessions.length && !local.body.length && !local.deletedIds.length
          && local.routines.every((r) => r.seeded);
        next = pristine ? { ...data.data, draft: local.draft } : S.mergeStates(local, data.data);
      }
      const before = JSON.stringify(stripDraft(local));
      const after = JSON.stringify(stripDraft(next));
      if (before !== after) {
        S.replaceState(next, { silent: true });
        onRemoteChange();
      }
      if (!data?.data || JSON.stringify(data.data) !== after) {
        const { error: upErr } = await client.from('gym_data').upsert({
          user_id: user.id,
          data: stripDraft(next),
          updated_at: new Date().toISOString(),
        });
        if (upErr) throw upErr;
      }
      status = 'ok';
      error = '';
      lastSync = Date.now();
    } catch (e) {
      status = navigator.onLine === false ? 'offline' : 'error';
      error = status === 'offline' ? 'Sin conexión: se sincronizará al volver.' : (e.message || String(e));
    } finally {
      running = null;
      emit();
      if (again) { again = false; sync(); }
    }
  })();
  return running;
}

const MSG = {
  'Invalid login credentials': 'Correo o contraseña incorrectos.',
  'Email not confirmed': 'Confirma tu correo antes de entrar (revisa tu bandeja de entrada).',
  'User already registered': 'Ya existe una cuenta con ese correo. Inicia sesión.',
  'Token has expired or is invalid': 'El código no es válido o ya caducó. Pide uno nuevo.',
};
const translate = (e) => {
  if (MSG[e?.message]) return MSG[e.message];
  if (/rate limit|security purposes/i.test(e?.message || '')) return 'Espera un minuto antes de pedir otro código.';
  return e?.message || 'Algo salió mal.';
};

function ensureClient() {
  if (!client) throw new Error('No se pudo conectar con el servidor. Revisa tu conexión y vuelve a abrir la app.');
}

export async function signIn(email, password) {
  ensureClient();
  const { error: e } = await client.auth.signInWithPassword({ email, password });
  if (e) throw new Error(translate(e));
}

// Devuelve true si hay que confirmar el correo antes de entrar.
export async function signUp(email, password) {
  ensureClient();
  const { data, error: e } = await client.auth.signUp({
    email, password, options: { emailRedirectTo: location.origin + location.pathname },
  });
  if (e) throw new Error(translate(e));
  return !data.session;
}

// Entrar sin contraseña: se envía un código de 6 dígitos al correo (crea la cuenta si no existe).
export async function sendCode(email) {
  ensureClient();
  const { error: e } = await client.auth.signInWithOtp({
    email, options: { shouldCreateUser: true, emailRedirectTo: location.origin + location.pathname },
  });
  if (e) throw new Error(translate(e));
}

export async function verifyCode(email, token) {
  ensureClient();
  const { error: e } = await client.auth.verifyOtp({ email, token, type: 'email' });
  if (e) throw new Error(translate(e));
}

export async function resetPassword(email) {
  ensureClient();
  const { error: e } = await client.auth.resetPasswordForEmail(email, { redirectTo: location.origin + location.pathname });
  if (e) throw new Error(translate(e));
}

async function askNewPassword() {
  const pw = prompt('Escribe tu nueva contraseña (mínimo 6 caracteres):');
  if (!pw) return;
  const { error: e } = await client.auth.updateUser({ password: pw });
  alert(e ? translate(e) : 'Contraseña actualizada.');
}

export async function signOut() {
  await client.auth.signOut();
  user = null;
  status = 'idle';
  emit();
}
