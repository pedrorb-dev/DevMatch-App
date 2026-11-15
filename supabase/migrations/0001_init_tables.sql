-- SPEC 02 — Persistencia real en Supabase
-- Tablas base: vacantes, user_profiles y saved_jobs.
-- Postura temporal de un solo usuario: RLS habilitada con políticas permisivas.
-- Cuando llegue el multiusuario se reemplazan por políticas basadas en auth.uid().

create table public.vacantes (
  id              uuid primary key default gen_random_uuid(),
  titulo          text not null,
  empresa         text not null,
  modalidad       text not null check (modalidad in ('Remoto', 'Híbrido', 'Presencial')),
  descripcion     text not null default '',
  requirements    text[] not null default '{}',
  benefits        text[] not null default '{}',
  stack_detectado text[] not null default '{}',
  nivel_ingles    text not null default 'No especificado',
  es_practicante  boolean not null default false,
  ubicacion_texto text not null default '',
  url_oferta      text not null unique,
  created_at      timestamptz not null default now()
);

create table public.user_profiles (
  id               uuid primary key,
  stack            text[] not null default '{}',
  experiencia_anos integer not null default 0,
  nivel_ingles     text not null default 'B1',
  ubicacion_texto  text not null default ''
);

create table public.saved_jobs (
  id       uuid primary key default gen_random_uuid(),
  user_id  uuid not null references public.user_profiles (id) on delete cascade,
  job_id   uuid not null references public.vacantes (id) on delete cascade,
  saved_at timestamptz not null default now(),
  unique (user_id, job_id)
);

-- RLS permisiva (temporal, un solo usuario sin autenticación)
alter table public.vacantes enable row level security;
alter table public.user_profiles enable row level security;
alter table public.saved_jobs enable row level security;

create policy "vacantes_select_all"
  on public.vacantes for select
  to anon, authenticated
  using (true);

create policy "vacantes_insert_all"
  on public.vacantes for insert
  to anon, authenticated
  with check (true);

create policy "vacantes_update_all"
  on public.vacantes for update
  to anon, authenticated
  using (true)
  with check (true);

create policy "vacantes_delete_all"
  on public.vacantes for delete
  to anon, authenticated
  using (true);

create policy "user_profiles_select_all"
  on public.user_profiles for select
  to anon, authenticated
  using (true);

create policy "user_profiles_insert_all"
  on public.user_profiles for insert
  to anon, authenticated
  with check (true);

create policy "user_profiles_update_all"
  on public.user_profiles for update
  to anon, authenticated
  using (true)
  with check (true);

create policy "user_profiles_delete_all"
  on public.user_profiles for delete
  to anon, authenticated
  using (true);

create policy "saved_jobs_select_all"
  on public.saved_jobs for select
  to anon, authenticated
  using (true);

create policy "saved_jobs_insert_all"
  on public.saved_jobs for insert
  to anon, authenticated
  with check (true);

create policy "saved_jobs_update_all"
  on public.saved_jobs for update
  to anon, authenticated
  using (true)
  with check (true);

create policy "saved_jobs_delete_all"
  on public.saved_jobs for delete
  to anon, authenticated
  using (true);

-- Grants explícitos: en proyectos endurecidos una política RLS sin grant
-- devuelve "permission denied". No cambian nada donde ya existían.
grant select, insert, update, delete on public.vacantes to anon, authenticated;
grant select, insert, update, delete on public.user_profiles to anon, authenticated;
grant select, insert, update, delete on public.saved_jobs to anon, authenticated;
