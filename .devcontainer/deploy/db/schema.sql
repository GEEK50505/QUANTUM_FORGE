-- =============================================================================
-- 1. CLEANUP (Reset database to clean state)
-- =============================================================================
DROP VIEW IF EXISTS public.jobs_overview CASCADE;
DROP TRIGGER IF EXISTS tr_dispatch_job ON public.jobs CASCADE;
DROP FUNCTION IF EXISTS public.dispatch_job_to_queue() CASCADE;
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users CASCADE;
DROP FUNCTION IF EXISTS public.handle_new_user() CASCADE;
DROP TABLE IF EXISTS public.jobs CASCADE;
DROP TABLE IF EXISTS public.molecules CASCADE;
DROP TABLE IF EXISTS public.profiles CASCADE;
DROP TYPE IF EXISTS public.job_status CASCADE;

-- =============================================================================
-- 2. EXTENSIONS
-- =============================================================================
create extension if not exists "uuid-ossp";
create extension if not exists pgmq;

-- Try to enable vector, but don't fail the script if it's missing
do $$
begin
  create extension if not exists vector;
exception when others then
  raise notice 'Vector extension not available, skipping.';
end $$;

-- =============================================================================
-- 3. ENUMS
-- =============================================================================
create type public.job_status as enum (
  'pending', 'queued', 'processing', 'completed', 'failed', 'cancelled'
);

-- =============================================================================
-- 4. TABLES
-- =============================================================================

-- Profiles
create table public.profiles (
  id uuid references auth.users(id) on delete cascade not null primary key,
  full_name text,
  organization text,
  preferences jsonb default '{"default_backend": "xtb"}'::jsonb,
  created_at timestamptz default now()
);

-- Molecules
create table public.molecules (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references auth.users(id) on delete cascade not null,
  name text not null,
  canonical_smiles text,
  geometry_content text not null,
  geometry_format text default 'xyz',
  
  -- Fallback: Use jsonb if vector is not strictly required for now
  embedding jsonb, 
  properties jsonb default '{}'::jsonb,
  tags text,
  created_at timestamptz default now()
);

-- Jobs
create table public.jobs (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references auth.users(id) on delete cascade not null,
  molecule_id uuid references public.molecules(id) on delete restrict not null,
  
  status public.job_status default 'pending',
  queue_name text default 'xtb_job_queue',
  
  -- Inputs
  payload jsonb not null default '{}'::jsonb,
  
  -- Outputs
  energy_scf double precision,
  homo_lumo_gap double precision,
  result jsonb,
  
  -- Logs
  log_url text,
  error_message text,
  
  started_at timestamptz,
  finished_at timestamptz,
  created_at timestamptz default now()
);

-- =============================================================================
-- 5. QUEUES & TRIGGERS
-- =============================================================================
-- Initialize Queue
select pgmq.create('xtb_job_queue');

-- Dispatch Function
create or replace function public.dispatch_job_to_queue()
returns trigger as $$
begin
  if new.status = 'queued' then
    perform pgmq.send(
      queue_name := new.queue_name,
      msg := jsonb_build_object(
        'job_id', new.id,
        'molecule_id', new.molecule_id,
        'user_id', new.user_id,
        'payload', new.payload
      )
    );
  end if;
  return new;
end;
$$ language plpgsql;

create trigger tr_dispatch_job
after insert on public.jobs
for each row
when (new.status = 'queued')
execute function public.dispatch_job_to_queue();

-- =============================================================================
-- 6. SECURITY & STORAGE
-- =============================================================================
alter table public.jobs enable row level security;
alter table public.molecules enable row level security;
alter table public.profiles enable row level security;

create policy "User view own jobs" on public.jobs for select using (auth.uid() = user_id);
create policy "User insert own jobs" on public.jobs for insert with check (auth.uid() = user_id);
create policy "User view own molecules" on public.molecules for select using (auth.uid() = user_id);
create policy "User insert own molecules" on public.molecules for insert with check (auth.uid() = user_id);

-- Storage Bucket
insert into storage.buckets (id, name, public) values ('job_artifacts', 'job_artifacts', true)
on conflict (id) do nothing;

create policy "User own artifacts" on storage.objects for select
using (bucket_id = 'job_artifacts' and auth.uid()::text = (storage.foldername(name))[1]);

create policy "User upload artifacts" on storage.objects for insert
with check (bucket_id = 'job_artifacts' and auth.uid()::text = (storage.foldername(name))[1]);

-- =============================================================================
-- 7. VIEW
-- =============================================================================
create or replace view public.jobs_overview as
select id, user_id, status, energy_scf, created_at from public.jobs;