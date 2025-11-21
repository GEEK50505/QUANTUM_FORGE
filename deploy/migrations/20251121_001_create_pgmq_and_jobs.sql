-- Migration: enable pgmq and create jobs table + queue
-- Date: 2025-11-21

-- Enable extension
CREATE EXTENSION IF NOT EXISTS pgmq;

-- Create a dedicated queue for xTB calculations (idempotent)
SELECT pgmq.create('xtb_calculation_queue');

-- Jobs table to store canonical job metadata and payload (transactional with pgmq)
CREATE TABLE IF NOT EXISTS public.jobs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job_key text NOT NULL UNIQUE,
    user_id uuid NULL,
    status text NOT NULL DEFAULT 'queued', -- queued, running, completed, failed
    payload jsonb NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- Trigger to keep updated_at current
CREATE OR REPLACE FUNCTION public.jobs_updated_at_trigger()
RETURNS TRIGGER AS $${
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_jobs_updated_at ON public.jobs;
CREATE TRIGGER trg_jobs_updated_at
BEFORE UPDATE ON public.jobs
FOR EACH ROW EXECUTE FUNCTION public.jobs_updated_at_trigger();

-- Example RLS policy: allows users to see their own rows (adjust as needed)
ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;

-- Note: replace or extend these policies based on your auth setup
-- Example policy (requires supabase auth functions):
-- CREATE POLICY "Users can see own jobs" ON public.jobs
--   FOR ALL USING (auth.uid() IS NULL OR auth.uid()::uuid = user_id);

-- Index on status for efficient queries
CREATE INDEX IF NOT EXISTS idx_jobs_status ON public.jobs(status);

-- Archive table for pgmq history (optional)
CREATE TABLE IF NOT EXISTS public.jobs_archive (
    archived_at timestamptz NOT NULL DEFAULT now(),
    job_id uuid NULL,
    job_key text NULL,
    payload jsonb NULL,
    notes text NULL
);

-- End migration
