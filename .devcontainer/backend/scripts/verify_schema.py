"""
Schema Verification Script for Quantum Forge ML Quality Tables

Verifies that all 16 new tables have been successfully deployed to Supabase.
Run this after deploying backend/scripts/schema_extensions_phase1.sql
"""

import os
import sys
sys.path.insert(0, '/workspace')
from backend.app.db.supabase_client import get_supabase_client

# Expected tables from Phase 1 deployment
EXPECTED_TABLES = {
    # 9 User-facing tables
    "user_sessions": "Frontend state persistence",
    "calculation_execution_metrics": "Detailed timing and performance data",
    "calculation_errors": "Error tracking and retry management",
    "performance_metrics": "System-wide analytics and monitoring",
    "user_preferences": "User configuration and settings",
    "api_usage_logs": "API request tracking for monitoring",
    "molecule_properties_computed": "Pre-computed ML features",
    "batch_job_performance": "Aggregate batch statistics",
    "user_audit_log": "Security and compliance audit trail",
    
    # 7 ML Quality tables
    "data_quality_metrics": "Quality scores & validation flags",
    "data_lineage": "Full provenance tracking for reproducibility",
    "ml_dataset_splits": "Train/test/validation set management",
    "ml_dataset_assignments": "Link data to splits with quality checks",
    "feature_extraction_log": "Feature engineering versioning & tracking",
    "model_training_log": "ML model training with full metrics",
    "data_anomalies": "Outlier/anomaly detection & management",
}


def verify_schema_deployment():
    """Verify all 16 tables exist in Supabase"""
    
    print("=" * 70)
    print("QUANTUM FORGE ML DATA QUALITY SCHEMA VERIFICATION")
    print("=" * 70)
    print()
    
    try:
        # Connect to Supabase
        client = get_supabase_client()
        print("✓ Connected to Supabase")
        print()
        
        # Get list of all tables
        print("Fetching table list from Supabase...")
        try:
            # Query information_schema to list all tables
            result = client.get(
                "information_schema.tables",
                filters={"table_schema": "public"},
                select="table_name",
                limit=100
            )
            
            existing_tables = {row['table_name'] for row in result} if result else set()
            
        except Exception as e:
            print(f"⚠ Could not query information_schema: {e}")
            print("Attempting alternative verification method...")
            existing_tables = set()
        
        # Check each expected table
        print()
        print("VERIFICATION RESULTS:")
        print("-" * 70)
        
        missing_tables = []
        found_tables = []
        
        for table_name, description in EXPECTED_TABLES.items():
            if table_name in existing_tables:
                print(f"✓ {table_name:<40} {description}")
                found_tables.append(table_name)
            else:
                # Try to verify by attempting a SELECT query
                try:
                    data = client.get(table_name, limit=1)
                    print(f"✓ {table_name:<40} {description}")
                    found_tables.append(table_name)
                except Exception:
                    print(f"✗ {table_name:<40} {description}")
                    missing_tables.append(table_name)
        
        print()
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Found: {len(found_tables)}/{len(EXPECTED_TABLES)} tables")
        print()
        
        if missing_tables:
            print(f"❌ DEPLOYMENT INCOMPLETE - {len(missing_tables)} tables missing:")
            for table in missing_tables:
                print(f"   - {table}")
            print()
            print("ACTION: Re-run the SQL script in Supabase SQL Editor")
            return False
        else:
            print("✅ SUCCESS! All 16 tables deployed successfully!")
            print()
            print("USER-FACING TABLES (9):")
            print("  ✓ user_sessions")
            print("  ✓ calculation_execution_metrics")
            print("  ✓ calculation_errors")
            print("  ✓ performance_metrics")
            print("  ✓ user_preferences")
            print("  ✓ api_usage_logs")
            print("  ✓ molecule_properties_computed")
            print("  ✓ batch_job_performance")
            print("  ✓ user_audit_log")
            print()
            print("ML QUALITY TABLES (7):")
            print("  ✓ data_quality_metrics")
            print("  ✓ data_lineage")
            print("  ✓ ml_dataset_splits")
            print("  ✓ ml_dataset_assignments")
            print("  ✓ feature_extraction_log")
            print("  ✓ model_training_log")
            print("  ✓ data_anomalies")
            print()
            print("NEXT STEPS:")
            print("  1. xTB runner code ready → quality metrics auto-logged")
            print("  2. QualityAssessor module ready → 5-D quality scoring")
            print("  3. Run test calculations to populate quality data")
            print()
            return True
    
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print()
        print("TROUBLESHOOTING:")
        print("  1. Check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env")
        print("  2. Verify Supabase project is accessible")
        print("  3. Check that the schema_extensions_phase1.sql completed without errors")
        return False


if __name__ == "__main__":
    success = verify_schema_deployment()
    sys.exit(0 if success else 1)
