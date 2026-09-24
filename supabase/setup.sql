-- Ejecuta esto una sola vez en Supabase → SQL Editor → New query → Run.
-- Crea la tabla donde se guarda una copia de los datos de cada usuario.

create table if not exists public.gym_data (
  user_id uuid primary key references auth.users (id) on delete cascade,
  data jsonb not null,
  updated_at timestamptz not null default now()
);

alter table public.gym_data enable row level security;

-- Cada usuario solo puede leer y escribir su propia fila.
drop policy if exists "leer mis datos" on public.gym_data;
create policy "leer mis datos" on public.gym_data
  for select using (auth.uid() = user_id);

drop policy if exists "crear mis datos" on public.gym_data;
create policy "crear mis datos" on public.gym_data
  for insert with check (auth.uid() = user_id);

drop policy if exists "actualizar mis datos" on public.gym_data;
create policy "actualizar mis datos" on public.gym_data
  for update using (auth.uid() = user_id) with check (auth.uid() = user_id);
