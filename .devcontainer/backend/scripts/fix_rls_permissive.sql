-- Aggressive RLS policy fix - disable RLS entirely as a test
-- This is for testing only; in production you'd want proper policies

-- Drop ALL existing policies on these tables
DROP POLICY IF EXISTS "Service role can insert quality metrics" ON data_quality_metrics;
DROP POLICY IF EXISTS "Service role can update quality metrics" ON data_quality_metrics;
DROP POLICY IF EXISTS "Service role can insert lineage" ON data_lineage;
DROP POLICY IF EXISTS "Service role can update lineage" ON data_lineage;
DROP POLICY IF EXISTS "Public can insert quality metrics" ON data_quality_metrics;
DROP POLICY IF EXISTS "Public can update quality metrics" ON data_quality_metrics;
DROP POLICY IF EXISTS "Public can insert lineage" ON data_lineage;
DROP POLICY IF EXISTS "Public can update lineage" ON data_lineage;
DROP POLICY IF EXISTS "Users can view quality metrics for their data" ON data_quality_metrics;
DROP POLICY IF EXISTS "Users can view data lineage for their data" ON data_lineage;

-- Disable RLS temporarily to test
ALTER TABLE data_quality_metrics DISABLE ROW LEVEL SECURITY;
ALTER TABLE data_lineage DISABLE ROW LEVEL SECURITY;

-- Re-enable RLS with permissive policies
ALTER TABLE data_quality_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_lineage ENABLE ROW LEVEL SECURITY;

-- Create ultra-permissive policies (for testing)
CREATE POLICY "Allow all on data_quality_metrics" ON data_quality_metrics
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Allow all on data_lineage" ON data_lineage
    FOR ALL USING (true) WITH CHECK (true);

-- Verify
SELECT tablename, policyname, permissive, roles 
FROM pg_policies 
WHERE tablename IN ('data_quality_metrics', 'data_lineage')
ORDER BY tablename, policyname;
