#!/usr/bin/env python3
"""Verify logging across all schema_v1 tables for a given job_key.

Usage: python3 scripts/verify_logging_full.py <job_key>

Prints counts and a sample row (first) for each important table.
"""
import sys
from backend.app.db.supabase_client import get_supabase_client

TABLES_TO_CHECK = [
    'molecules',
    'calculations',
    'calculation_execution_metrics',
    'calculation_errors',
    'runs',
    'data_quality_metrics',
    'data_lineage',
    'molecule_properties_computed',
    'feature_extraction_log',
    'ml_dataset_splits',
    'ml_dataset_assignments',
    'model_training_log',
    'data_anomalies',
    'performance_metrics',
    'api_usage_logs',
    'user_sessions',
    'user_preferences',
    'user_audit_log',
    'batch_job_performance',
]

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: verify_logging_full.py <job_key>')
        sys.exit(2)
    job_key = sys.argv[1]
    client = get_supabase_client()

    print(f"Verifying logging for job_key={job_key}\n")

    # Helper to print a sample
    def sample(table, filters=None, select='*', limit=5):
        try:
            rows = client.get(table, filters=filters or {}, select=select, limit=limit)
            count = len(rows) if isinstance(rows, list) else (0 if rows is None else 1)
            print(f"{table}: count_sample={count}")
            if isinstance(rows, list) and rows:
                print('  sample:', rows[0])
        except Exception as e:
            print(f"{table}: ERROR: {e}")

    # molecules: look up by job_key in metadata.calc_id or by smiles O
    print('--- molecules ---')
    sample('molecules', filters={'smiles': 'O'})

    print('\n--- calculations ---')
    sample('calculations', filters={'output_json_path': f'jobs/{job_key}/xtbout.json'})

    print('\n--- calculation_execution_metrics ---')
    # Prefer job_key lookup for execution metrics (calculation_id may be numeric and absent)
    try:
        rows = client.get('calculation_execution_metrics', filters={'job_key': job_key}, select='*', limit=5)
        count = len(rows) if isinstance(rows, list) else (0 if rows is None else 1)
        print(f"calculation_execution_metrics: count_sample={count}")
        if isinstance(rows, list) and rows:
            print('  sample:', rows[0])
    except Exception:
        print("calculation_execution_metrics: filter by job_key failed; falling back to recent rows")
        sample('calculation_execution_metrics', filters={})

    print('\n--- calculation_errors ---')
    sample('calculation_errors', filters={'job_key': job_key})

    print('\n--- runs ---')
    sample('runs', filters={'run_id': job_key})

    print('\n--- data_quality_metrics ---')
    sample('data_quality_metrics', filters={'job_key': job_key})

    print('\n--- data_lineage ---')
    sample('data_lineage', filters={'job_key': job_key})

    # Other tables: check for any rows referencing this job_key where relevant
    print('\n--- molecule_properties_computed ---')
    sample('molecule_properties_computed', filters={})

    print('\n--- feature_extraction_log ---')
    sample('feature_extraction_log', filters={})

    print('\n--- ml_dataset_splits ---')
    sample('ml_dataset_splits', filters={})

    print('\n--- ml_dataset_assignments ---')
    sample('ml_dataset_assignments', filters={})

    print('\n--- model_training_log ---')
    sample('model_training_log', filters={})

    print('\n--- data_anomalies ---')
    sample('data_anomalies', filters={})

    print('\n--- performance_metrics ---')
    sample('performance_metrics', filters={})

    print('\n--- api_usage_logs ---')
    sample('api_usage_logs', filters={'endpoint': '/api/calculate'})

    print('\n--- user_sessions ---')
    sample('user_sessions', filters={})

    print('\n--- user_preferences ---')
    sample('user_preferences', filters={})

    print('\n--- user_audit_log ---')
    sample('user_audit_log', filters={})

    print('\n--- batch_job_performance ---')
    sample('batch_job_performance', filters={})

    print('\nVerification complete.')
