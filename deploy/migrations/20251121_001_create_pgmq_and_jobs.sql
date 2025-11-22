-- Consolidated migration: enable pgmq and create canonical jobs table + queue
-- Date: 2025-11-21 (consolidated 2025-11-22)

-- Install real extension if available; otherwise keep dev shim.
DO $$
BEGIN
  IF (SELECT count(*) FROM pg_available_extensions WHERE name = 'pgmq') > 0 THEN
    -- If a dev shim provided functions earlier, drop them so CREATE EXTENSION succeeds
    IF EXISTS (
      SELECT 1 FROM pg_proc p
      JOIN pg_namespace n ON p.pronamespace = n.oid
      WHERE p.proname = 'send' AND n.nspname = 'pgmq'
    ) THEN
      RAISE NOTICE 'Dropping dev pgmq shim functions to allow extension install';
      EXECUTE 'DROP FUNCTION IF EXISTS pgmq.send(text, jsonb)';
      EXECUTE 'DROP FUNCTION IF EXISTS pgmq.create(text)';
      EXECUTE 'DROP FUNCTION IF EXISTS pgmq.read(text, integer, integer)';
      EXECUTE 'DROP FUNCTION IF EXISTS pgmq.archive(integer)';
    END IF;

    CREATE EXTENSION IF NOT EXISTS pgmq;
  ELSE
    RAISE NOTICE 'pgmq extension not available on this host; keeping dev shim functions';
  END IF;
END$$;

-- Ensure the pgmq queue exists (safe when extension installed)
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pgmq') THEN
    PERFORM pgmq.create('xtb_calculation_queue');
  ELSE
    RAISE NOTICE 'pgmq extension not installed; skipping queue creation';
  END IF;
END$$;

-- Canonical jobs table (merged schema)
CREATE TABLE IF NOT EXISTS public.jobs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job_key text NOT NULL UNIQUE,
    user_id uuid NULL,
    batch_id uuid NULL,
    status text NOT NULL DEFAULT 'queued', -- queued, running, completed, failed
    payload jsonb NULL,
    results jsonb NULL,
    error_message text NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- Trigger to keep updated_at current
CREATE OR REPLACE FUNCTION public.jobs_updated_at_trigger()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_jobs_updated_at ON public.jobs;
CREATE TRIGGER trg_jobs_updated_at
BEFORE UPDATE ON public.jobs
FOR EACH ROW EXECUTE FUNCTION public.jobs_updated_at_trigger();

-- Enable RLS as a default stance (policies should be added by app owners)
ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;

-- Index on status for efficient queries
CREATE INDEX IF NOT EXISTS idx_jobs_status ON public.jobs(status);

-- Create batch index only when column exists (safe for older DBs)
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'jobs' AND column_name = 'batch_id'
  ) THEN
    EXECUTE 'CREATE INDEX IF NOT EXISTS idx_jobs_batch ON public.jobs (batch_id)';
  ELSE
    RAISE NOTICE 'Skipping idx_jobs_batch creation: column batch_id missing';
  END IF;
END$$;

-- Archive table for pgmq history (optional)
CREATE TABLE IF NOT EXISTS public.jobs_archive (
    archived_at timestamptz NOT NULL DEFAULT now(),
    job_id uuid NULL,
    job_key text NULL,
    payload jsonb NULL,
    notes text NULL
);

-- End consolidated migration
