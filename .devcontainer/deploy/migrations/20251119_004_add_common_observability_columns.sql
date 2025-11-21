-- Add common observability columns (job_key, calculation_id_uuid, calculation_id, created_at, details)
-- Date: 2025-11-19

DO $$
DECLARE
    tbl TEXT;
    tables TEXT[] := ARRAY[
        'api_usage_logs', 'atomic_properties', 'batch_items', 'batch_job_performance', 'batch_jobs',
        'calculation_errors', 'calculation_execution_metrics', 'calculations', 'data_anomalies', 'data_lineage',
        'data_quality_metrics', 'event_logs', 'feature_extraction_log', 'ml_dataset_assignments', 'ml_dataset_splits',
        'model_training_log', 'molecule_properties_computed', 'molecules', 'performance_metrics', 'runs',
        'user_audit_log', 'user_preferences', 'user_sessions'
    ];
BEGIN
    FOREACH tbl IN ARRAY tables LOOP
        -- job_key (nullable)
        EXECUTE format('ALTER TABLE IF EXISTS %I ADD COLUMN IF NOT EXISTS job_key text;', tbl);
        -- uuid FK for calculation id
        EXECUTE format('ALTER TABLE IF EXISTS %I ADD COLUMN IF NOT EXISTS calculation_id_uuid uuid;', tbl);
        -- legacy numeric FK (nullable)
        EXECUTE format('ALTER TABLE IF EXISTS %I ADD COLUMN IF NOT EXISTS calculation_id bigint;', tbl);
        -- created_at timestamp
        EXECUTE format('ALTER TABLE IF EXISTS %I ADD COLUMN IF NOT EXISTS created_at timestamptz DEFAULT now();', tbl);
        -- details jsonb for free-form payloads
        EXECUTE format('ALTER TABLE IF EXISTS %I ADD COLUMN IF NOT EXISTS details jsonb;', tbl);
    END LOOP;
END$$;
