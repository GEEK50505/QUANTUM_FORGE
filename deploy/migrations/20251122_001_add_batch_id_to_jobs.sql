-- Migration: add batch_id to jobs and create index if missing
-- Date: 2025-11-22

-- Add batch_id column if it doesn't exist
ALTER TABLE public.jobs
  ADD COLUMN IF NOT EXISTS batch_id uuid NULL;

-- Create index on batch_id if the column exists
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
