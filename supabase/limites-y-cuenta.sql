-- =====================================================================
-- LÍMITES (termómetro + freno automático) y BORRAR CUENTA
-- Pégalo entero en el SQL Editor de Supabase y pulsa Run.
-- Es seguro ejecutarlo más de una vez.
-- Al final debe salir:  funciones 7 · freno apagado
-- =====================================================================

-- ---------- 1. Estado de los límites (una sola fila) ----------
create table if not exists public.app_limits (
  id           int primary key default 1 check (id = 1),
  brake_auto   boolean not null default false,   -- lo enciende solo al pasar del 85 %
  brake_manual boolean not null default false,   -- lo enciendes tú desde moderar.html
  db_mb        numeric not null default 0,
  storage_mb   numeric not null default 0,
  r2_mb        numeric not null default 0,       -- estimado: historias vivas × 0,6 MB
  users_30d    int     not null default 0,       -- personas activas en 30 días
  users_total  int     not null default 0,
  stories_live int     not null default 0,
  workouts     int     not null default 0,
  updated_at   timestamptz not null default now()
);
insert into public.app_limits (id) values (1) on conflict do nothing;
alter table public.app_limits enable row level security;
revoke all on public.app_limits from anon, authenticated;

-- ¿Está puesto el freno? (lo usan las funciones de abajo; la app no lo llama)
create or replace function public.app_braked() returns boolean
language sql stable security definer set search_path = public as $$
  select coalesce((select brake_auto or brake_manual from app_limits where id = 1), false);
$$;

-- ---------- 2. Medir y decidir (corre sola cada hora) ----------
-- Plan gratis de Supabase: base de datos 500 MB · archivos 1 GB · 50.000 personas activas al mes.
-- Cloudflare R2 gratis: 10 GB. (La transferencia y las peticiones del Worker no se pueden medir desde aquí.)
-- Freno: se enciende al llegar al 85 % de cualquiera y se apaga al bajar del 75 %.
create or replace function public.refresh_app_limits() returns void
language plpgsql security definer set search_path = public as $$
declare
  v_db   numeric := pg_database_size(current_database()) / 1048576.0;
  v_sto  numeric := 0;
  v_live int     := 0;
  v_mau  int     := 0;
  v_tot  int     := 0;
  v_wk   int     := 0;
  worst  numeric;
  was    boolean;
begin
  begin
    select coalesce(sum(coalesce((metadata->>'size')::bigint, 0)), 0) / 1048576.0 into v_sto
      from storage.objects where bucket_id = 'avatars';
  exception when others then v_sto := 0; end;
  select count(*) into v_live from stories where status in ('pending','active','hidden');
  select count(*) filter (where last_sign_in_at > now() - interval '30 days'), count(*)
    into v_mau, v_tot from auth.users;
  select count(*) into v_wk from workouts;

  worst := greatest(v_db / 500.0, v_sto / 1024.0, v_mau / 50000.0, (v_live * 0.6) / 10240.0);
  select brake_auto into was from app_limits where id = 1;

  update app_limits set
    db_mb = round(v_db, 1), storage_mb = round(v_sto, 1), r2_mb = round(v_live * 0.6, 1),
    users_30d = v_mau, users_total = v_tot, stories_live = v_live, workouts = v_wk,
    brake_auto = case when worst >= 0.85 then true when worst < 0.75 then false else was end,
    updated_at = now()
  where id = 1;
end $$;

-- ---------- 3. Termómetro y botón de freno (solo administradores) ----------
create or replace function public.admin_usage()
returns table (db_mb numeric, db_limit numeric, storage_mb numeric, storage_limit numeric,
               r2_mb numeric, r2_limit numeric, users_30d int, users_limit int,
               users_total int, stories_live int, workouts int,
               brake_auto boolean, brake_manual boolean, updated_at timestamptz)
language plpgsql security definer set search_path = public as $$
begin
  if not is_admin() then raise exception 'Solo administradores'; end if;
  perform refresh_app_limits();
  return query
    select l.db_mb, 500::numeric, l.storage_mb, 1024::numeric, l.r2_mb, 10240::numeric,
           l.users_30d, 50000, l.users_total, l.stories_live, l.workouts,
           l.brake_auto, l.brake_manual, l.updated_at
      from app_limits l where l.id = 1;
end $$;

create or replace function public.admin_set_brake(p_on boolean) returns void
language plpgsql security definer set search_path = public as $$
begin
  if not is_admin() then raise exception 'Solo administradores'; end if;
  update app_limits set brake_manual = p_on where id = 1;
end $$;

-- ---------- 4. Qué frena el freno ----------
-- 4a. Cuentas nuevas. Si algo falla al medir, NUNCA se bloquea el registro por error.
create or replace function public.block_signups_when_braked() returns trigger
language plpgsql security definer set search_path = public as $$
declare b boolean := false;
begin
  begin b := public.app_braked(); exception when others then b := false; end;
  if b then
    raise exception 'Estamos recibiendo muchas cuentas nuevas. Intenta de nuevo en unos días.';
  end if;
  return new;
end $$;

drop trigger if exists block_signups on auth.users;
create trigger block_signups before insert on auth.users
  for each row execute function public.block_signups_when_braked();

-- 4b. Historias nuevas (igual que antes + el freno). Lo demás sigue funcionando.
create or replace function public.create_story(p_key text) returns uuid
language plpgsql security definer set search_path = public as $$
declare
  me     uuid := auth.uid();
  new_id uuid;
begin
  if me is null then raise exception 'No autenticado'; end if;
  if public.app_braked() then
    raise exception 'Las historias están en pausa por unos días';
  end if;
  perform pg_advisory_xact_lock(hashtextextended(me::text, 0));
  if not exists (select 1 from profiles where id = me) then
    raise exception 'Primero crea tu perfil';
  end if;
  if coalesce((select banned from story_moderation where user_id = me), false) then
    raise exception 'No puedes publicar historias';
  end if;
  if p_key is null or p_key !~ ('^' || me::text || '/[0-9a-f-]{36}\.jpg$') then
    raise exception 'Ruta no válida';
  end if;
  if exists (select 1 from stories where user_id = me and created_at > now() - interval '24 hours') then
    raise exception 'Ya publicaste tu historia de hoy';
  end if;
  insert into stories (user_id, key) values (me, p_key) returning id into new_id;
  return new_id;
end $$;

-- 4c. Revisión cada hora
do $$
begin
  if exists (select 1 from pg_extension where extname = 'pg_cron') then
    perform cron.schedule('revisar-limites', '0 * * * *', 'select public.refresh_app_limits()');
    raise notice 'Revisión de límites programada (cada hora).';
  else
    raise notice 'pg_cron no está activo: actívalo en Integrations → Cron y vuelve a ejecutar este bloque.';
  end if;
end $$;

-- ---------- 5. Borrar mi cuenta ----------
-- Paso 1 (la app lo llama primero): marca mis historias como borradas y devuelve las rutas
-- de mis archivos, para que la app los borre del Worker (historias) y de Storage (foto de perfil).
create or replace function public.prepare_account_deletion()
returns table (kind text, path text)
language plpgsql security definer set search_path = public as $$
declare me uuid := auth.uid();
begin
  if me is null then raise exception 'No autenticado'; end if;
  if is_admin() then
    raise exception 'Las cuentas de administrador no se borran desde la app';
  end if;
  update stories set status = 'deleted'
   where user_id = me and status in ('pending','active','hidden');
  return query select 'story'::text, s.key from stories s where s.user_id = me;
  return query select 'avatar'::text, p.avatar_path from profiles p
    where p.id = me and p.avatar_path is not null;
  return query select 'avatar'::text, m.review_path from avatar_moderation m
    where m.user_id = me and m.review_path is not null;
end $$;

-- Paso 2: borra todo (entrenos, amigos, reacciones, reportes enviados, historias, crews, datos de la nube...).
-- Los crews que creé y tienen más gente pasan al miembro más antiguo; los que quedan vacíos se borran.
create or replace function public.delete_my_account() returns void
language plpgsql security definer set search_path = public as $$
declare
  me   uuid := auth.uid();
  c    record;
  heir uuid;
begin
  if me is null then raise exception 'No autenticado'; end if;
  if is_admin() then
    raise exception 'Las cuentas de administrador no se borran desde la app';
  end if;

  for c in select id from crews where owner = me loop
    select m.user_id into heir from crew_members m
     where m.crew_id = c.id and m.user_id <> me order by m.joined_at limit 1;
    if heir is null then
      delete from crews where id = c.id;
    else
      update crews set owner = heir where id = c.id;
    end if;
  end loop;

  delete from reports where target_id = me and target_type::text in ('user','avatar');
  delete from auth.users where id = me;   -- el resto se borra en cascada
end $$;

-- ---------- 6. Permisos ----------
revoke execute on function
  public.app_braked(), public.refresh_app_limits(), public.admin_usage(), public.admin_set_brake(boolean),
  public.prepare_account_deletion(), public.delete_my_account()
  from public, anon;
revoke execute on function public.app_braked(), public.refresh_app_limits() from authenticated;
grant execute on function
  public.admin_usage(), public.admin_set_brake(boolean),
  public.prepare_account_deletion(), public.delete_my_account()
  to authenticated;

notify pgrst, 'reload schema';

-- ---------- 7. Comprobación ----------
select refresh_app_limits();
select
  (select count(*) from pg_proc p join pg_namespace n on n.oid = p.pronamespace
    where n.nspname = 'public' and p.proname in ('app_braked','refresh_app_limits','admin_usage',
      'admin_set_brake','prepare_account_deletion','delete_my_account','block_signups_when_braked')) as funciones,
  case when public.app_braked() then 'freno ENCENDIDO' else 'freno apagado' end as estado;
