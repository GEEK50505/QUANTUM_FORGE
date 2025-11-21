-- Fix RLS Policies for Data Quality & Lineage Logging
-- Run this in Supabase SQL Editor to enable service role writes to logging tables
-- Date: 2025-11-15

-- ============================================================================
-- 1. Allow public role (anon key) to INSERT quality metrics
-- ============================================================================

CREATE POLICY "Public can insert quality metrics" ON data_quality_metrics
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Public can update quality metrics" ON data_quality_metrics
    FOR UPDATE USING (true);

-- ============================================================================
-- 2. Allow public role (anon key) to INSERT lineage data
-- ============================================================================

CREATE POLICY "Public can insert lineage" ON data_lineage
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Public can update lineage" ON data_lineage
    FOR UPDATE USING (true);

-- ============================================================================
-- Alternative: If service_role key is being used (backend operations)
-- ============================================================================
-- Uncomment below if you're using SUPABASE_KEY (service role key) instead of anon key

/*
CREATE POLICY "Service role can insert quality metrics (service_role)" ON data_quality_metrics
    FOR INSERT WITH CHECK (true)
    TO service_role;

CREATE POLICY "Service role can update quality metrics (service_role)" ON data_quality_metrics
    FOR UPDATE USING (true)
    TO service_role;

CREATE POLICY "Service role can insert lineage (service_role)" ON data_lineage
    FOR INSERT WITH CHECK (true)
    TO service_role;

CREATE POLICY "Service role can update lineage (service_role)" ON data_lineage
    FOR UPDATE USING (true)
    TO service_role;
*/

-- ============================================================================
-- Verification
-- ============================================================================

-- List all policies on data_quality_metrics
SELECT tablename, policyname, permissive, roles, qual, with_check 
FROM pg_policies 
WHERE tablename IN ('data_quality_metrics', 'data_lineage')
ORDER BY tablename, policyname;
