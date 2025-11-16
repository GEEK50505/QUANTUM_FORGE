-- Drop the old policies and recreate for public role
-- Run this in Supabase SQL Editor

DROP POLICY IF EXISTS "Service role can insert quality metrics" ON data_quality_metrics;
DROP POLICY IF EXISTS "Service role can update quality metrics" ON data_quality_metrics;
DROP POLICY IF EXISTS "Service role can insert lineage" ON data_lineage;
DROP POLICY IF EXISTS "Service role can update lineage" ON data_lineage;

-- Create new policies for public role (anon key)
CREATE POLICY "Public can insert quality metrics" ON data_quality_metrics
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Public can update quality metrics" ON data_quality_metrics
    FOR UPDATE USING (true);

CREATE POLICY "Public can insert lineage" ON data_lineage
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Public can update lineage" ON data_lineage
    FOR UPDATE USING (true);

-- Verify policies
SELECT tablename, policyname, permissive, roles, qual, with_check 
FROM pg_policies 
WHERE tablename IN ('data_quality_metrics', 'data_lineage')
ORDER BY tablename, policyname;
