-- =====================================================================
-- CREWS (grupos de gente del gym, sin chat) · un solo archivo
-- Pégalo entero en Supabase → SQL Editor → Run. Es seguro ejecutarlo más de una vez.
-- No cambia nada de lo que ya existe (perfiles, amigos, entrenos, feed).
--
-- Reglas:
--   · Cualquier usuario crea un crew (nombre 3–30 letras, descripción opcional ≤ 140). Sin foto.
--   · Se entra con un código de 8 letras/números (sin 0/O ni 1/I para no confundirse).
--   · Máximo 50 personas por crew; cada usuario puede estar en 5 crews y ser dueño de 3.
--   · El dueño cambia nombre/descripción, cambia el código y saca gente (quien sale sacado no puede volver).
--   · Si el dueño se va, el crew pasa al miembro más antiguo; si no queda nadie, se borra.
--   · Dentro del crew se ven los entrenos NO privados de los miembros desde que entraron,
--     y un ranking semanal (entrenos y series). Con bloqueo (en cualquier sentido) no os veis.
--   · Datos irreales no cuentan en el ranking: más de 80 series o más de 6 h en un entreno.
-- =====================================================================

-- ---------- 1. Tablas ----------
create table if not exists public.crews (
  id          uuid primary key default gen_random_uuid(),
  name        text not null check (char_length(btrim(name)) between 3 and 30),
  description text check (description is null or char_length(description) <= 140),
  owner       uuid not null references public.profiles(id) on delete cascade,
  invite_code text not null unique,
  created_at  timestamptz not null default now()
);

create table if not exists public.crew_members (
  crew_id   uuid not null references public.crews(id) on delete cascade,
  user_id   uuid not null references public.profiles(id) on delete cascade,
  joined_at timestamptz not null default now(),
  primary key (crew_id, user_id)
);
create index if not exists crew_members_user_idx on public.crew_members (user_id);

create table if not exists public.crew_kicked (
  crew_id uuid not null references public.crews(id) on delete cascade,
  user_id uuid not null references public.profiles(id) on delete cascade,
  primary key (crew_id, user_id)
);

alter table public.crews        enable row level security;
alter table public.crew_members enable row level security;
alter table public.crew_kicked  enable row level security;
revoke all on public.crews, public.crew_members, public.crew_kicked from anon, authenticated;
-- Nadie toca las tablas directo: todo pasa por las funciones de abajo.

-- ---------- 2. Ayudas internas ----------
create or replace function public.crew_new_code() returns text
language plpgsql volatile set search_path = public as $$
declare
  abc  constant text := 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  b    bytea;
  code text;
begin
  loop
    b := uuid_send(gen_random_uuid());
    code := '';
    for i in 0..7 loop
      code := code || substr(abc, (get_byte(b, i) % 32) + 1, 1);
    end loop;
    exit when not exists (select 1 from crews where invite_code = code);
  end loop;
  return code;
end $$;

create or replace function public.crew_clean_code(p_code text) returns text
language sql immutable as $$
  select upper(regexp_replace(coalesce(p_code, ''), '[^A-Za-z0-9]', '', 'g'));
$$;

create or replace function public.is_crew_member(p_crew uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from crew_members where crew_id = p_crew and user_id = auth.uid());
$$;

create or replace function public.crew_assert_owner(p_crew uuid) returns void
language plpgsql stable security definer set search_path = public as $$
begin
  if auth.uid() is null then raise exception 'No autenticado'; end if;
  if not exists (select 1 from crews where id = p_crew and owner = auth.uid()) then
    raise exception 'Solo el creador del crew puede hacer esto';
  end if;
end $$;

-- ---------- 3. Crear, ver antes de entrar, entrar ----------
create or replace function public.create_crew(p_name text, p_description text default null) returns uuid
language plpgsql security definer set search_path = public as $$
declare
  me uuid := auth.uid();
  new_id uuid;
begin
  if me is null then raise exception 'No autenticado'; end if;
  perform pg_advisory_xact_lock(hashtextextended('crews:' || me::text, 0));
  if not exists (select 1 from profiles where id = me) then raise exception 'Primero crea tu perfil'; end if;
  if char_length(btrim(coalesce(p_name, ''))) not between 3 and 30 then
    raise exception 'El nombre debe tener entre 3 y 30 caracteres';
  end if;
  if (select count(*) from crews where owner = me) >= 3 then
    raise exception 'Ya creaste 3 crews, el máximo';
  end if;
  if (select count(*) from crew_members where user_id = me) >= 5 then
    raise exception 'Ya estás en 5 crews, el máximo';
  end if;
  insert into crews (name, description, owner, invite_code)
  values (btrim(p_name), nullif(btrim(coalesce(p_description, '')), ''), me, crew_new_code())
  returning id into new_id;
  insert into crew_members (crew_id, user_id) values (new_id, me);
  return new_id;
end $$;

-- Lo que se muestra antes de unirse (nombre, descripción, cuántos son y quién lo creó).
create or replace function public.crew_preview(p_code text)
returns table (crew_id uuid, name text, description text, members bigint, owner_username text, already_member boolean)
language sql stable security definer set search_path = public as $$
  select c.id, c.name, c.description,
         (select count(*) from crew_members m where m.crew_id = c.id),
         p.username,
         exists (select 1 from crew_members m where m.crew_id = c.id and m.user_id = auth.uid())
    from crews c join profiles p on p.id = c.owner
   where auth.uid() is not null and c.invite_code = crew_clean_code(p_code);
$$;

create or replace function public.join_crew(p_code text) returns uuid
language plpgsql security definer set search_path = public as $$
declare
  me uuid := auth.uid();
  c  crews%rowtype;
begin
  if me is null then raise exception 'No autenticado'; end if;
  select * into c from crews where invite_code = crew_clean_code(p_code);
  if c.id is null then raise exception 'Código no válido'; end if;
  if exists (select 1 from crew_members where crew_id = c.id and user_id = me) then return c.id; end if;
  perform pg_advisory_xact_lock(hashtextextended('crew:' || c.id::text, 0));
  perform pg_advisory_xact_lock(hashtextextended('crews:' || me::text, 0));
  if exists (select 1 from crew_kicked where crew_id = c.id and user_id = me) then
    raise exception 'No puedes unirte a este crew';
  end if;
  if not exists (select 1 from profiles where id = me) then raise exception 'Primero crea tu perfil'; end if;
  if (select count(*) from crew_members where crew_id = c.id) >= 50 then
    raise exception 'Este crew está lleno (50 personas)';
  end if;
  if (select count(*) from crew_members where user_id = me) >= 5 then
    raise exception 'Ya estás en 5 crews, el máximo';
  end if;
  insert into crew_members (crew_id, user_id) values (c.id, me);
  return c.id;
end $$;

-- ---------- 4. Mis crews ----------
create or replace function public.my_crews()
returns table (crew_id uuid, name text, description text, is_owner boolean, members bigint,
               invite_code text, joined_at timestamptz)
language sql stable security definer set search_path = public as $$
  select c.id, c.name, c.description, (c.owner = auth.uid()),
         (select count(*) from crew_members x where x.crew_id = c.id),
         c.invite_code, m.joined_at
    from crew_members m join crews c on c.id = m.crew_id
   where m.user_id = auth.uid()
   order by m.joined_at;
$$;

-- ---------- 5. Ranking de la semana (lunes a domingo, en la zona horaria del teléfono) ----------
create or replace function public.crew_ranking(p_crew uuid, p_tz text default 'America/Lima')
returns table (user_id uuid, username text, display_name text, avatar_path text, power_level smallint,
               is_owner boolean, is_me boolean, week_workouts bigint, week_sets bigint)
language plpgsql stable security definer set search_path = public as $$
declare
  tz text := case when exists (select 1 from pg_timezone_names where name = p_tz) then p_tz else 'America/Lima' end;
  desde timestamptz := (date_trunc('week', now() at time zone tz)) at time zone tz;
begin
  if not is_crew_member(p_crew) then raise exception 'No eres miembro de este crew'; end if;
  return query
    select m.user_id, p.username, p.display_name, p.avatar_path, p.power_level,
           (c.owner = m.user_id), (m.user_id = auth.uid()),
           count(w.id),
           coalesce(sum(case when w.id is not null then least(w.total_sets, 60) end), 0)::bigint  -- tope 60 series por entreno
      from crew_members m
      join crews c on c.id = m.crew_id
      join profiles p on p.id = m.user_id
      left join workouts w
        on w.user_id = m.user_id
       and w.started_at >= desde
       and w.visibility <> 'private'
       and w.total_sets between 1 and 80
       and coalesce(w.duration_sec, 0) <= 6 * 3600
     where m.crew_id = p_crew
       and (m.user_id = auth.uid() or not is_blocked(auth.uid(), m.user_id))
     group by m.user_id, p.username, p.display_name, p.avatar_path, p.power_level, c.owner, m.joined_at
     order by 8 desc, 9 desc, m.joined_at;
end $$;

-- ---------- 6. Entrenos del crew (mismo formato que get_feed) ----------
create or replace function public.get_crew_feed(p_crew uuid, p_limit integer default 20, p_before timestamptz default now())
returns table (workout_id uuid, user_id uuid, username text, display_name text, avatar_path text,
               started_at timestamptz, duration_sec integer, total_volume_kg numeric, total_sets integer,
               kcal integer, muscle_groups text[], pr_count integer, exercises jsonb,
               reaction_count bigint, my_reaction text)
language plpgsql stable security definer set search_path = public as $$
begin
  if not is_crew_member(p_crew) then raise exception 'No eres miembro de este crew'; end if;
  return query
    select w.id, w.user_id, p.username, p.display_name, p.avatar_path,
           w.started_at, w.duration_sec, w.total_volume_kg, w.total_sets,
           w.kcal, w.muscle_groups::text[], w.pr_count,
           coalesce((select jsonb_agg(jsonb_build_object('name', e.exercise_name, 'sets', e.sets, 'is_pr', e.is_pr)
                                      order by e.position)
                       from workout_exercises e where e.workout_id = w.id), '[]'::jsonb),
           (select count(*) from reactions r where r.workout_id = w.id),
           (select r.kind from reactions r where r.workout_id = w.id and r.user_id = auth.uid())
      from crew_members m
      join workouts w on w.user_id = m.user_id
      join profiles p on p.id = w.user_id
     where m.crew_id = p_crew
       and w.started_at >= m.joined_at
       and w.started_at < p_before
       and w.visibility <> 'private'
       and (m.user_id = auth.uid() or not is_blocked(auth.uid(), m.user_id))
     order by w.started_at desc
     limit least(greatest(p_limit, 1), 50);
end $$;

-- ---------- 7. Salir, sacar, cambiar código, editar, borrar ----------
create or replace function public.leave_crew(p_crew uuid) returns void
language plpgsql security definer set search_path = public as $$
declare
  me uuid := auth.uid();
  heir uuid;
begin
  if me is null then raise exception 'No autenticado'; end if;
  perform pg_advisory_xact_lock(hashtextextended('crew:' || p_crew::text, 0));
  delete from crew_members where crew_id = p_crew and user_id = me;
  if not found then return; end if;
  if exists (select 1 from crews where id = p_crew and owner = me) then
    select m.user_id into heir from crew_members m where m.crew_id = p_crew order by m.joined_at limit 1;
    if heir is null then
      delete from crews where id = p_crew;
    else
      update crews set owner = heir where id = p_crew;
    end if;
  end if;
end $$;

create or replace function public.remove_crew_member(p_crew uuid, p_user uuid) returns void
language plpgsql security definer set search_path = public as $$
begin
  perform crew_assert_owner(p_crew);
  if p_user = auth.uid() then raise exception 'Para irte usa «Salir del crew»'; end if;
  delete from crew_members where crew_id = p_crew and user_id = p_user;
  insert into crew_kicked (crew_id, user_id) values (p_crew, p_user) on conflict do nothing;
end $$;

create or replace function public.regenerate_crew_code(p_crew uuid) returns text
language plpgsql security definer set search_path = public as $$
declare code text;
begin
  perform crew_assert_owner(p_crew);
  code := crew_new_code();
  update crews set invite_code = code where id = p_crew;
  return code;
end $$;

create or replace function public.update_crew(p_crew uuid, p_name text, p_description text default null) returns void
language plpgsql security definer set search_path = public as $$
begin
  perform crew_assert_owner(p_crew);
  if char_length(btrim(coalesce(p_name, ''))) not between 3 and 30 then
    raise exception 'El nombre debe tener entre 3 y 30 caracteres';
  end if;
  update crews set name = btrim(p_name), description = nullif(btrim(coalesce(p_description, '')), '')
   where id = p_crew;
end $$;

create or replace function public.delete_crew(p_crew uuid) returns void
language plpgsql security definer set search_path = public as $$
begin
  perform crew_assert_owner(p_crew);
  delete from crews where id = p_crew;
end $$;

-- ---------- 8. Permisos: solo usuarios con sesión ----------
revoke execute on function
  public.crew_new_code(), public.is_crew_member(uuid), public.crew_assert_owner(uuid),
  public.create_crew(text, text), public.crew_preview(text), public.join_crew(text), public.my_crews(),
  public.crew_ranking(uuid, text), public.get_crew_feed(uuid, integer, timestamptz),
  public.leave_crew(uuid), public.remove_crew_member(uuid, uuid), public.regenerate_crew_code(uuid),
  public.update_crew(uuid, text, text), public.delete_crew(uuid)
  from public, anon;
revoke execute on function public.crew_new_code(), public.crew_assert_owner(uuid), public.is_crew_member(uuid)
  from authenticated;
grant execute on function
  public.create_crew(text, text), public.crew_preview(text), public.join_crew(text), public.my_crews(),
  public.crew_ranking(uuid, text), public.get_crew_feed(uuid, integer, timestamptz),
  public.leave_crew(uuid), public.remove_crew_member(uuid, uuid), public.regenerate_crew_code(uuid),
  public.update_crew(uuid, text, text), public.delete_crew(uuid)
  to authenticated;

notify pgrst, 'reload schema';

-- ---------- 9. Comprobación (debe salir: funciones 11 · tablas 3) ----------
select
  (select count(*) from pg_proc p join pg_namespace n on n.oid = p.pronamespace
    where n.nspname = 'public' and p.proname in ('create_crew','crew_preview','join_crew','my_crews',
      'crew_ranking','get_crew_feed','leave_crew','remove_crew_member','regenerate_crew_code',
      'update_crew','delete_crew')) as funciones,
  (select count(*) from information_schema.tables
    where table_schema = 'public' and table_name in ('crews','crew_members','crew_kicked')) as tablas;
