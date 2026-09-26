// Supabase simulado: guarda la "nube" en window.__cloud (compartido vía sessionStorage del test).
const db = globalThis.__cloudDB || (globalThis.__cloudDB = JSON.parse(localStorage.getItem('__mockcloud') || '{}'));
const persist = () => localStorage.setItem('__mockcloud', JSON.stringify(db));
export function createClient() {
  let session = JSON.parse(localStorage.getItem('__mocksession') || 'null');
  const subs = [];
  return {
    auth: {
      getSession: async () => ({ data: { session } }),
      onAuthStateChange: (fn) => { subs.push(fn); fn('INITIAL_SESSION', session); },
      signInWithPassword: async ({ email, password }) => {
        if (password !== 'secreto1') return { error: { message: 'Invalid login credentials' } };
        session = { user: { id: 'u1', email } }; localStorage.setItem('__mocksession', JSON.stringify(session));
        subs.forEach((f) => f('SIGNED_IN', session)); return { error: null };
      },
      signInWithOtp: async () => ({ error: null }),
      verifyOtp: async ({ email, token }) => {
        if (token !== '123456') return { error: { message: 'Token has expired or is invalid' } };
        session = { user: { id: 'u1', email } }; localStorage.setItem('__mocksession', JSON.stringify(session));
        subs.forEach((f) => f('SIGNED_IN', session)); return { error: null };
      },
      signUp: async () => ({ data: { session: null }, error: null }),
      signOut: async () => { session = null; localStorage.removeItem('__mocksession'); subs.forEach((f) => f('SIGNED_OUT', null)); },
      resetPasswordForEmail: async () => ({ error: null }),
    },
    from: () => ({
      select: () => ({ eq: (_c, id) => ({ maybeSingle: async () => {
        const cloud = JSON.parse(await (await fetch('/__cloud_get')).text() || 'null');
        return { data: cloud ? { data: cloud } : null, error: null };
      } }) }),
      upsert: async (row) => { await fetch('/__cloud_put', { method: 'POST', body: JSON.stringify(row.data) }); return { error: null }; },
    }),
  };
}
