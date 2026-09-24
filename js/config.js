// Conexión con Supabase para el inicio de sesión y la sincronización en la nube.
// Pega aquí los datos de tu proyecto (Supabase → Project Settings → API).
// La clave "anon"/"publishable" es pública por diseño: la seguridad la dan
// las políticas RLS de supabase/setup.sql, que solo dejan a cada usuario ver sus datos.
// Si se dejan vacíos, la app funciona igual pero solo guarda en este dispositivo.
export const SUPABASE_URL = '';
export const SUPABASE_ANON_KEY = '';
