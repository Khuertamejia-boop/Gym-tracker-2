// Supabase simulado para probar moderar.html (funciones admin_*, is_admin y borrado en Storage).
// El estado vive en globalThis.__mod para que la prueba lo consulte.
const state = (globalThis.__mod = {
  admin: true, session: null, calls: [], removed: [],
  avatars: [
    { user_id: 'u-ana', username: 'ana', photo_path: 'u-ana/1.jpg', hidden: true, reports: 2, reasons: ['desnudo', 'desnudo'], first_report: new Date(Date.now() - 3600e3).toISOString() },
    { user_id: 'u-leo', username: 'leo', photo_path: 'u-leo/9.jpg', hidden: false, reports: 1, reasons: ['spam'], first_report: new Date(Date.now() - 86400e3 * 2).toISOString() },
  ],
  others: [
    { id: 7, target_type: 'workout', target_id: 'w1', target_username: 'marta', reporter_username: 'ana', reason: 'otro', created_at: new Date(Date.now() - 600e3).toISOString() },
  ],
});
export function createClient() {
  return {
    auth: {
      getSession: async () => ({ data: { session: state.session } }),
      signInWithPassword: async ({ password }) => {
        if (password !== 'secreto1') return { error: { message: 'Invalid login credentials' } };
        state.session = { user: { id: 'admin' } }; return { error: null };
      },
      signOut: async () => { state.session = null; },
    },
    rpc: async (name, args) => {
      state.calls.push([name, args]);
      if (name === 'is_admin') return { data: state.admin, error: null };
      if (!state.admin) return { data: null, error: { message: 'Solo administradores' } };
      if (name === 'admin_pending_avatars') return { data: state.avatars, error: null };
      if (name === 'admin_other_reports') return { data: state.others, error: null };
      if (name === 'admin_resolve_avatar') { state.avatars = state.avatars.filter((a) => a.user_id !== args.p_user); return { data: null, error: null }; }
      if (name === 'admin_close_report') { state.others = state.others.filter((o) => o.id !== args.p_id); return { data: null, error: null }; }
      return { data: null, error: { message: 'función desconocida ' + name } };
    },
    storage: {
      from: () => ({
        getPublicUrl: (path) => ({ data: { publicUrl: 'data:image/gif;base64,R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=#' + path } }),
        remove: async (paths) => { state.removed.push(...paths); return { data: paths.map((name) => ({ name })), error: null }; },
      }),
    },
  };
}
