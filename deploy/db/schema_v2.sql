-- =============================================================================
-- Quantum Forge DB Schema Migration v2 (Hybrid Quantum-Classical Swarm)
-- Clean, standalone migration implementing the polymorphic job model,
-- guarded pgmq usage, worker presence, DLQ, indexes, and RLS policies.
-- Run this file in the Supabase SQL editor or via psql as a privileged user.
-- =============================================================================

-- =============================================================================
-- 1. EXTENSIONS & CONFIGURATION
-- =============================================================================
create extension if not exists "uuid-ossp";

DO $$
BEGIN
  BEGIN
    EXECUTE 'CREATE EXTENSION IF NOT EXISTS pgmq';
  EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'pgmq extension not available or cannot be created: %', SQLERRM;
  END;
END$$;

-- =============================================================================
-- 2. ENUMS & TYPES
-- =============================================================================
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'job_status_v2') THEN
    CREATE TYPE public.job_status_v2 AS ENUM (
      'pending', 'queued', 'processing', 'submitted', 'polling', 'completed', 'failed', 'cancelled'
    );
  END IF;
END$$;

-- =============================================================================
-- 3. TABLES
-- =============================================================================

-- Profiles
CREATE TABLE IF NOT EXISTS public.profiles_v2 (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name text,
  organization text,
  preferences jsonb DEFAULT jsonb_build_object('default_backend','xtb','notify_email', true),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Molecules
CREATE TABLE IF NOT EXISTS public.molecules_v2 (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  name text NOT NULL,
  description text,
  canonical_smiles text,
  inchi_key text,
  geometry_format text CHECK (geometry_format IN ('xyz','sdf','mol','pdb','cif')),
  geometry_content text NOT NULL,
  properties jsonb DEFAULT jsonb_build_object('charge',0,'multiplicity',1),
  tags text,
  source_metadata jsonb,
  created_at timestamptz DEFAULT now()
);

-- Jobs (polymorphic)
CREATE TABLE IF NOT EXISTS public.jobs_v2 (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  molecule_id uuid REFERENCES public.molecules_v2(id) ON DELETE RESTRICT,

  status public.job_status_v2 DEFAULT 'pending',
  queue_name text DEFAULT 'xtb_job_queue',
  priority integer DEFAULT 100,
  visible_at timestamptz,
  retry_count integer DEFAULT 0,
  max_retries integer DEFAULT 5,

  provider_id text,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  result jsonb,

  log_url text,
  output_url text,

  error_message text,
  wall_time_seconds double precision,
  created_at timestamptz DEFAULT now(),
  started_at timestamptz,
  finished_at timestamptz
);

-- Dead-letter table
CREATE TABLE IF NOT EXISTS public.dead_jobs_v2 (
  id uuid PRIMARY KEY,
  original_job jsonb,
  moved_at timestamptz DEFAULT now(),
  reason text
);

-- Workers / presence
CREATE TABLE IF NOT EXISTS public.workers_v2 (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  name text,
  capabilities jsonb,
  last_heartbeat timestamptz,
  current_job uuid,
  meta jsonb
);

-- =============================================================================
-- 4. INDEXES
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_molecules_v2_user ON public.molecules_v2(user_id);
CREATE INDEX IF NOT EXISTS idx_molecules_v2_inchi ON public.molecules_v2(inchi_key);

CREATE INDEX IF NOT EXISTS idx_jobs_v2_user ON public.jobs_v2(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_v2_status ON public.jobs_v2(status);
CREATE INDEX IF NOT EXISTS idx_jobs_v2_queue_prio ON public.jobs_v2(queue_name, priority);
CREATE INDEX IF NOT EXISTS idx_jobs_v2_visible_at ON public.jobs_v2(visible_at) WHERE visible_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_jobs_v2_payload_backend ON public.jobs_v2 ((payload->> 'backend'));
CREATE INDEX IF NOT EXISTS idx_jobs_v2_payload_gin ON public.jobs_v2 USING gin (payload);
CREATE INDEX IF NOT EXISTS idx_jobs_v2_result_gin ON public.jobs_v2 USING gin (result);

-- =============================================================================
-- 5. STORAGE BUCKET (guarded)
-- =============================================================================
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'storage' AND table_name = 'buckets') THEN
    BEGIN
      INSERT INTO storage.buckets (id, name, public)
      VALUES ('job_artifacts', 'job_artifacts', true)
      ON CONFLICT (id) DO NOTHING;
    EXCEPTION WHEN OTHERS THEN
      RAISE NOTICE 'Could not create storage bucket record: %', SQLERRM;
    END;
  ELSE
    RAISE NOTICE 'Storage schema not present; create bucket via Supabase Console.';
  END IF;
END$$;

-- =============================================================================
-- 6. PGMQ QUEUE CREATION (guarded)
-- =============================================================================
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pgmq') THEN
    BEGIN
      PERFORM pgmq.create('xtb_job_queue');
    EXCEPTION WHEN SQLSTATE '42710' THEN
      RAISE NOTICE 'pgmq queue xtb_job_queue already exists';
    WHEN OTHERS THEN
      RAISE NOTICE 'pgmq.create failed: %', SQLERRM;
    END;
  ELSE
    RAISE NOTICE 'pgmq extension not installed; workers should fallback to SKIP LOCKED polling';
  END IF;
END$$;

-- =============================================================================
-- 7. DISPATCH TRIGGER (enqueue on status='queued')
-- =============================================================================
CREATE OR REPLACE FUNCTION public.dispatch_job_v2()
RETURNS trigger AS $$
DECLARE
  msg jsonb;
  q text;
BEGIN
  IF NEW.status = 'queued' THEN
    q := COALESCE(NEW.queue_name, 'xtb_job_queue');
    msg := jsonb_build_object('job_id', NEW.id, 'molecule_id', NEW.molecule_id, 'user_id', NEW.user_id, 'payload', NEW.payload, 'queue_name', q);

    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pgmq') THEN
      PERFORM pgmq.send(queue_name := q, msg := msg, delay := 0);
    ELSE
      RAISE NOTICE 'pgmq not available; job % left in table for pollers', NEW.id;
    END IF;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_dispatch_job_v2 ON public.jobs_v2;
CREATE TRIGGER tr_dispatch_job_v2
AFTER INSERT OR UPDATE OF status ON public.jobs_v2
FOR EACH ROW
WHEN (NEW.status = 'queued')
EXECUTE FUNCTION public.dispatch_job_v2();

-- =============================================================================
-- 8. DEAD LETTER HELPER
-- =============================================================================
CREATE OR REPLACE FUNCTION public.move_job_to_dead_v2(p_job uuid, p_reason text)
RETURNS void AS $$
DECLARE
  j jsonb;
BEGIN
  SELECT to_jsonb(t) INTO j FROM public.jobs_v2 t WHERE t.id = p_job;
  INSERT INTO public.dead_jobs_v2(id, original_job, reason) VALUES (p_job, j, p_reason);
  DELETE FROM public.jobs_v2 WHERE id = p_job;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 9. WORKER HEARTBEAT
-- =============================================================================
CREATE OR REPLACE FUNCTION public.heartbeat_v2(p_id uuid, p_meta jsonb)
RETURNS void AS $$
BEGIN
  INSERT INTO public.workers_v2(id, last_heartbeat, meta)
  VALUES (p_id, now(), p_meta)
  ON CONFLICT (id) DO UPDATE SET last_heartbeat = now(), meta = EXCLUDED.meta;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 10. RLS POLICIES (guarded)
-- =============================================================================
ALTER TABLE public.profiles_v2 ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.molecules_v2 ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jobs_v2 ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'profiles_select_public') THEN
    CREATE POLICY profiles_select_public ON public.profiles_v2 FOR SELECT USING (true);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'profiles_insert_own') THEN
    CREATE POLICY profiles_insert_own ON public.profiles_v2 FOR INSERT WITH CHECK (auth.uid() = id);
  END IF;
END$$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'molecules_select_own') THEN
    CREATE POLICY molecules_select_own ON public.molecules_v2 FOR SELECT USING (auth.uid() = user_id);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'molecules_insert_own') THEN
    CREATE POLICY molecules_insert_own ON public.molecules_v2 FOR INSERT WITH CHECK (auth.uid() = user_id);
  END IF;
END$$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'jobs_select_own') THEN
    CREATE POLICY jobs_select_own ON public.jobs_v2 FOR SELECT USING (auth.uid() = user_id);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'jobs_insert_own') THEN
    CREATE POLICY jobs_insert_own ON public.jobs_v2 FOR INSERT WITH CHECK (auth.uid() = user_id);
  END IF;
END$$;

-- Note: Workers should use the SERVICE_ROLE key or a dedicated worker role to update jobs_v2 rows.

-- =============================================================================
-- 11. VIEW & USER HOOK
-- =============================================================================
CREATE OR REPLACE VIEW public.jobs_v2_overview AS
SELECT id, user_id, molecule_id, status, queue_name, priority, provider_id, error_message, created_at, started_at, finished_at
FROM public.jobs_v2;

CREATE OR REPLACE FUNCTION public.handle_new_user_v2()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.profiles_v2(id, full_name, preferences)
  VALUES (NEW.id, COALESCE(NEW.raw_user_meta_data->>'full_name',''), jsonb_build_object('default_backend','xtb'))
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
  BEGIN
    CREATE TRIGGER on_auth_user_created_v2
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE PROCEDURE public.handle_new_user_v2();
  EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Could not create auth.users trigger (likely lacks permission): %', SQLERRM;
  END;
END$$;

-- =============================================================================
-- Migration complete. Use jobs_v2 for new workflows; the legacy `jobs`/`molecules` tables can
-- be migrated or kept read-only during rollout. Workers should support both pgmq and
-- SKIP LOCKED polling depending on platform capabilities.
-- =============================================================================
