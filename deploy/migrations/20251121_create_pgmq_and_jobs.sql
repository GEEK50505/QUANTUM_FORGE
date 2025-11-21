-- Migration: enable pgmq extension, create queue and jobs table
-- Date: 2025-11-21

-- Enable pgmq extension (idempotent)
CREATE EXTENSION IF NOT EXISTS pgmq;

-- Create a PGMQ queue for xTB calculations. This uses the pgmq extension.
-- If your pgmq installation uses a different function, adapt accordingly.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pgmq.queue WHERE queue_name = 'xtb_calculation_queue') THEN
    PERFORM pgmq.create('xtb_calculation_queue');
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
CREATE INDEX IF NOT EXISTS idx_jobs_batch ON public.jobs (batch_id);

-- Example RLS policy placeholders (enable and tailor for your setup)
-- ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY jobs_select_owner ON public.jobs FOR SELECT USING (auth.uid() = user_id::text);
