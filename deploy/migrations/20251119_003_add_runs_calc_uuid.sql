-- Add UUID calculation_id column to runs for hybrid compatibility
-- Non-destructive: adds a new column calculation_id_uuid and keeps existing calculation_id
-- Date: 2025-11-19

ALTER TABLE IF EXISTS runs
  ADD COLUMN IF NOT EXISTS calculation_id_uuid UUID;

-- Optional index to speed up lookups by calculation_id_uuid
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'runs') THEN
    EXECUTE 'CREATE INDEX IF NOT EXISTS idx_runs_calc_uuid ON runs(calculation_id_uuid)';
  END IF;
END
$$;

-- Also add calculation_id_uuid to other tables that commonly reference calculation_id
-- This is conservative; add only if the table exists
ALTER TABLE IF EXISTS molecule_properties_computed
  ADD COLUMN IF NOT EXISTS calculation_id_uuid UUID;

ALTER TABLE IF EXISTS performance_metrics
  ADD COLUMN IF NOT EXISTS calculation_id_uuid UUID;

ALTER TABLE IF EXISTS calculation_execution_metrics
  ADD COLUMN IF NOT EXISTS calculation_id_uuid UUID;
