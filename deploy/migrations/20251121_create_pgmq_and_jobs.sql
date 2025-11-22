-- Migration: enable pgmq extension, create queue and jobs table
-- Date: 2025-11-21

-- Enable pgmq extension (idempotent)
CREATE EXTENSION IF NOT EXISTS pgmq;

-- Create a PGMQ queue for xTB calculations. This uses the pgmq extension.
-- If your pgmq installation uses a different function, adapt accordingly.
DO $$
BEGIN
  -- Only attempt to inspect or call pgmq when the extension is installed.
  IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pgmq') THEN
    -- If the pgmq.queue relation exists, query it safely; otherwise call
    -- `pgmq.create` directly so the extension can initialize its objects.
    IF EXISTS (
      SELECT 1 FROM pg_catalog.pg_class c
      JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
      WHERE n.nspname = 'pgmq' AND c.relname = 'queue'
    ) THEN
      IF NOT EXISTS (SELECT 1 FROM pgmq.queue WHERE queue_name = 'xtb_calculation_queue') THEN
        PERFORM pgmq.create('xtb_calculation_queue');
      END IF;
    ELSE
      PERFORM pgmq.create('xtb_calculation_queue');
    END IF;
  ELSE
    RAISE NOTICE 'pgmq extension not installed; skipping queue creation';
  END IF;
END$$;

-- Create a jobs table that stores job metadata and payload. This is optional
-- and provides a canonical place to query job state for the UI.
CREATE TABLE IF NOT EXISTS public.jobs (
  job_id text PRIMARY KEY,
  user_id uuid NULL,
  batch_id uuid NULL,
  status text NOT NULL DEFAULT 'QUEUED',
  payload jsonb NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  results jsonb NULL,
  error_message text NULL
);

-- Indexes to speed common queries
CREATE INDEX IF NOT EXISTS idx_jobs_status ON public.jobs (status);
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

-- Example RLS policy placeholders (enable and tailor for your setup)
-- ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY jobs_select_owner ON public.jobs FOR SELECT USING (auth.uid() = user_id::text);
