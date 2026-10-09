-- =====================================================================
-- HISTORIAS DE 24 H · PARTE 2 de 2  (ejecútala DESPUÉS de la parte 1)
-- Tablas, funciones, reportes, moderación y limpieza automática.
-- Es seguro ejecutarla más de una vez.
-- =====================================================================

-- ---------- 1. Tablas ----------
-- Nadie las toca directo desde la app: todo pasa por las funciones de abajo.
create table if not exists public.stories (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references public.profiles(id) on delete cascade,
  key        text not null unique,                       -- ruta de la foto en Cloudflare R2
  status     text not null default 'pending'
             check (status in ('pending','active','hidden','deleted','removed')),
  created_at timestamptz not null default now(),
  expires_at timestamptz not null default now() + interval '24 hours'
);
create index if not exists stories_user_created_idx on public.stories (user_id, created_at desc);
create index if not exists stories_expires_idx on public.stories (expires_at);
alter table public.stories enable row level security;

create table if not exists public.story_views (
  story_id  uuid not null references public.stories(id) on delete cascade,
  viewer    uuid not null references public.profiles(id) on delete cascade,
  viewed_at timestamptz not null default now(),
  primary key (story_id, viewer)
);
alter table public.story_views enable row level security;

create table if not exists public.story_moderation (
  user_id uuid primary key references public.profiles(id) on delete cascade,
  strikes smallint not null default 0,
  banned  boolean  not null default false                 -- con 2 strikes ya no puede publicar
);
alter table public.story_moderation enable row level security;

revoke all on public.stories, public.story_views, public.story_moderation from anon, authenticated;

-- ---------- 2. Quién puede ver una historia ----------
-- Tú y tus amigos, sin bloqueos en ningún sentido.
-- (Para que la vea cualquier usuario, cambia el cuerpo por:  select auth.uid() is not null;)
create or replace function public.story_visible_to_me(p_owner uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select auth.uid() is not null and (
    p_owner = auth.uid()
    or (are_friends(auth.uid(), p_owner)
        and not is_blocked(auth.uid(), p_owner)
        and not is_blocked(p_owner, auth.uid()))
  );
$$;

-- ---------- 3. Publicar (1 cada 24 h) ----------
-- La llama el Worker de Cloudflare con la sesión del usuario. Reserva el cupo antes de subir la foto.
create or replace function public.create_story(p_key text) returns uuid
language plpgsql security definer set search_path = public as $$
declare
  me     uuid := auth.uid();
  new_id uuid;
begin
  if me is null then raise exception 'No autenticado'; end if;
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

-- Foto ya subida: la historia pasa a verse.
create or replace function public.confirm_story(p_story uuid) returns timestamptz
language plpgsql security definer set search_path = public as $$
declare exp timestamptz;
begin
  if auth.uid() is null then raise exception 'No autenticado'; end if;
  update stories set status = 'active'
   where id = p_story and user_id = auth.uid() and status = 'pending'
  returning expires_at into exp;
  if exp is null then raise exception 'Historia no encontrada'; end if;
  return exp;
end $$;

-- La subida falló: se libera el cupo del día.
create or replace function public.cancel_story(p_story uuid) returns void
language plpgsql security definer set search_path = public as $$
begin
  if auth.uid() is null then raise exception 'No autenticado'; end if;
  delete from stories where id = p_story and user_id = auth.uid() and status = 'pending';
end $$;

-- ---------- 4. Ver ----------
create or replace function public.get_stories()
returns table (story_id uuid, user_id uuid, username text, avatar_path text, key text,
               created_at timestamptz, expires_at timestamptz, seen boolean, is_mine boolean)
language sql stable security definer set search_path = public as $$
  select s.id, s.user_id, p.username, p.avatar_path, s.key, s.created_at, s.expires_at,
         exists (select 1 from story_views v where v.story_id = s.id and v.viewer = auth.uid()) as seen,
         (s.user_id = auth.uid()) as is_mine
    from stories s
    join profiles p on p.id = s.user_id
   where s.status = 'active'
     and s.expires_at > now()
     and public.story_visible_to_me(s.user_id)
   order by is_mine desc, seen asc, s.created_at desc;
$$;

create or replace function public.mark_story_seen(p_story uuid) returns void
language plpgsql security definer set search_path = public as $$
begin
  if auth.uid() is null then raise exception 'No autenticado'; end if;
  insert into story_views (story_id, viewer)
  select s.id, auth.uid() from stories s
   where s.id = p_story and s.status = 'active' and s.expires_at > now()
     and public.story_visible_to_me(s.user_id)
  on conflict do nothing;
end $$;

-- ---------- 5. Borrar mi historia ----------
-- Devuelve la ruta de la foto; la app avisa después al Worker para borrar el archivo.
create or replace function public.delete_my_story(p_story uuid) returns text
language plpgsql security definer set search_path = public as $$
declare k text;
begin
  if auth.uid() is null then raise exception 'No autenticado'; end if;
  update stories set status = 'deleted'
   where id = p_story and user_id = auth.uid() and status in ('active','hidden')
  returning key into k;
  if k is null then raise exception 'Historia no encontrada'; end if;
  return k;
end $$;

-- El Worker pregunta esto antes de borrar un archivo de R2:
-- solo si la historia ya no está activa y quien pide es su dueño o administrador.
create or replace function public.story_object_deletable(p_key text) returns boolean
language sql stable security definer set search_path = public as $$
  select auth.uid() is not null and exists (
    select 1 from stories
     where key = p_key and status in ('deleted','removed')
       and (user_id = auth.uid() or public.is_admin())
  );
$$;

-- ---------- 6. Reportes de historias ----------
-- Se conserva TODO lo que ya hacían para las fotos de perfil y se añade «story».
create or replace function public.before_report() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if new.target_type::text = 'avatar' then
    select avatar_path into new.snapshot from profiles where id = new.target_id;
    if new.snapshot is null then raise exception 'Ese usuario no tiene foto'; end if;
  elsif new.target_type::text = 'story' then
    select s.key into new.snapshot from stories s
     where s.id = new.target_id and s.status in ('active','hidden') and s.expires_at > now()
       and public.story_visible_to_me(s.user_id);
    if new.snapshot is null then raise exception 'Esa historia ya no está disponible'; end if;
  end if;
  return new;
end;
$$;

create or replace function public.after_report() returns trigger
language plpgsql security definer set search_path = public as $$
declare
  n int;
begin
  if new.target_type::text = 'story' then
    select count(distinct reporter) into n
      from reports
     where target_type = new.target_type and target_id = new.target_id and status = 'open';
    if n >= 2 then                                   -- con 2 personas distintas se oculta sola
      update stories set status = 'hidden' where id = new.target_id and status = 'active';
    end if;
    return new;
  end if;

  if new.target_type::text <> 'avatar' then return new; end if;

  select count(distinct reporter) into n
    from reports
   where target_type = new.target_type and target_id = new.target_id
     and snapshot = new.snapshot and status = 'open';

  if n >= 2 then                                   -- ← cambia el 2 si quieres
    insert into avatar_moderation (user_id, review_path)
    values (new.target_id, new.snapshot)
    on conflict (user_id) do update set review_path = excluded.review_path;
    update profiles set avatar_path = null
     where id = new.target_id and avatar_path = new.snapshot;
  end if;
  return new;
end;
$$;

-- «Otros reportes» ya no mezcla las historias (tienen su propia lista).
create or replace function public.admin_other_reports()
returns table(id bigint, target_type text, target_id uuid, target_username text,
              reporter_username text, reason text, created_at timestamptz)
language plpgsql stable security definer set search_path = public as $$
begin
  if not is_admin() then raise exception 'Solo administradores'; end if;
  return query
    select r.id, r.target_type::text, r.target_id,
           coalesce(pu.username, pw.username), rp.username, r.reason, r.created_at
      from reports r
      left join profiles rp on rp.id = r.reporter
      left join profiles pu on r.target_type::text = 'user' and pu.id = r.target_id
      left join workouts w  on r.target_type::text = 'workout' and w.id = r.target_id
      left join profiles pw on pw.id = w.user_id
     where r.target_type::text not in ('avatar','story') and r.status = 'open'
     order by r.created_at;
end;
$$;

-- ---------- 7. Moderación (para la página moderar.html) ----------
create or replace function public.admin_pending_stories()
returns table (story_id uuid, user_id uuid, username text, key text, hidden boolean,
               reports bigint, reasons text[], first_report timestamptz, expires_at timestamptz)
language plpgsql stable security definer set search_path = public as $$
begin
  if not is_admin() then raise exception 'Solo administradores'; end if;
  return query
    select s.id, s.user_id, p.username, s.key, (s.status = 'hidden'),
           count(distinct r.reporter), array_agg(r.reason order by r.created_at),
           min(r.created_at), s.expires_at
      from reports r
      join stories s on s.id = r.target_id
      join profiles p on p.id = s.user_id
     where r.target_type::text = 'story' and r.status = 'open'
       and s.status in ('active','hidden') and s.expires_at > now()
     group by s.id, s.user_id, p.username, s.key, s.status, s.expires_at
     order by 6 desc, 8;
end;
$$;

-- remove = quitar la historia (+1 strike; con 2 no puede publicar más) · keep = está bien.
-- Con 'remove' devuelve la ruta: la página avisa al Worker para borrar el archivo de R2.
create or replace function public.admin_resolve_story(p_story uuid, p_action text) returns text
language plpgsql security definer set search_path = public as $$
declare
  v_owner uuid;
  v_key   text;
begin
  if not is_admin() then raise exception 'Solo administradores'; end if;
  if p_action not in ('remove','keep') then raise exception 'Acción no válida'; end if;
  select user_id, key into v_owner, v_key from stories where id = p_story;
  if v_owner is null then raise exception 'Historia no encontrada'; end if;

  if p_action = 'remove' then
    update stories set status = 'removed' where id = p_story;
    insert into story_moderation (user_id, strikes, banned) values (v_owner, 1, false)
    on conflict (user_id) do update
       set strikes = story_moderation.strikes + 1,
           banned  = (story_moderation.strikes + 1) >= 2;
    update reports set status = 'reviewed'
     where target_type::text = 'story' and target_id = p_story and status = 'open';
    return v_key;
  end if;

  update stories set status = 'active' where id = p_story and status = 'hidden';
  update reports set status = 'dismissed'
   where target_type::text = 'story' and target_id = p_story and status = 'open';
  return null;
end $$;

-- ---------- 8. Limpieza automática (cada día) ----------
create or replace function public.purge_old_stories() returns void
language plpgsql security definer set search_path = public as $$
begin
  -- reportes de historias que ya caducaron o se borraron: se cierran solos
  update reports set status = 'dismissed'
   where target_type::text = 'story' and status = 'open'
     and not exists (select 1 from stories s
                      where s.id = reports.target_id and s.status in ('active','hidden') and s.expires_at > now());
  delete from stories where created_at < now() - interval '3 days';
end $$;

do $$
begin
  if exists (select 1 from pg_extension where extname = 'pg_cron') then
    perform cron.schedule('limpiar-historias', '50 8 * * *', 'select public.purge_old_stories()');
    raise notice 'Limpieza de historias programada.';
  else
    raise notice 'pg_cron no está activo: actívalo en Integrations → Cron y vuelve a ejecutar este bloque.';
  end if;
end $$;

-- ---------- 9. Permisos ----------
revoke execute on function
  public.story_visible_to_me(uuid), public.create_story(text), public.confirm_story(uuid),
  public.cancel_story(uuid), public.get_stories(), public.mark_story_seen(uuid),
  public.delete_my_story(uuid), public.story_object_deletable(text),
  public.admin_pending_stories(), public.admin_resolve_story(uuid, text)
  from public, anon;
grant execute on function
  public.story_visible_to_me(uuid), public.create_story(text), public.confirm_story(uuid),
  public.cancel_story(uuid), public.get_stories(), public.mark_story_seen(uuid),
  public.delete_my_story(uuid), public.story_object_deletable(text),
  public.admin_pending_stories(), public.admin_resolve_story(uuid, text)
  to authenticated;
revoke execute on function public.purge_old_stories() from public, anon, authenticated;

notify pgrst, 'reload schema';
