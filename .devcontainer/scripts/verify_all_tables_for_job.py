"""Verify logging coverage across many Supabase tables for a given job_key.

Usage: python scripts/verify_all_tables_for_job.py <job_key>

This script is best-effort: it will try to query each table using job_key,
fall back to calculation_id when available, and print a concise report.
"""
import os
import sys
import re
from pprint import pprint
from backend.app.db.supabase_client import get_supabase_client

def load_service_key_from_envfile(path='.env.backend'):
    p = path
    if not os.path.exists(p):
        return
    with open(p, 'r') as f:
        txt = f.read()
    m = re.search(r'^SUPABASE_SERVICE_ROLE_KEY=(.+)$', txt, flags=re.M)
    if m:
        os.environ['SUPABASE_SERVICE_ROLE_KEY'] = m.group(1).strip()

TABLES = [
    'api_usage_logs', 'atomic_properties', 'batch_items', 'batch_job_performance', 'batch_jobs',
    'calculation_errors', 'calculation_execution_metrics', 'calculations', 'data_anomalies',
    'data_lineage', 'data_quality_metrics', 'event_logs', 'feature_extraction_log',
    'ml_dataset_assignments', 'ml_dataset_splits', 'model_training_log', 'molecule_properties_computed',
    'molecules', 'performance_metrics', 'runs', 'user_audit_log', 'user_preferences', 'user_sessions'
]

def main(job_key: str):
    load_service_key_from_envfile()
    sb = get_supabase_client()

    report = {}

    # Try to find calculation numeric id first
    calc_rows = []
    try:
        calc_rows = sb.get('calculations', filters={'job_key': job_key}, limit=5)
    except Exception:
        calc_rows = []

    calc_id = None
    if calc_rows and isinstance(calc_rows, list) and len(calc_rows) > 0:
        # pick first
        r = calc_rows[0]
        calc_id = r.get('id') or r.get('calculation_id')

    for table in TABLES:
        tbl_info = {'rows': None, 'count': 0, 'columns': []}
        try:
            # fetch writable/acceptable columns via OPTIONS when available
            try:
                cols = sb._get_table_writable_columns(table, method='insert')
                tbl_info['columns'] = cols
            except Exception:
                tbl_info['columns'] = []

            try:
                rows = sb.get(table, filters={'job_key': job_key}, limit=5)
                tbl_info['rows'] = rows
                tbl_info['count'] = len(rows) if isinstance(rows, list) else (1 if rows else 0)
            except Exception:
                # Try using calculation_id if available
                if calc_id is not None:
                    try:
                        rows = sb.get(table, filters={'calculation_id': calc_id}, limit=5)
                        tbl_info['rows'] = rows
                        tbl_info['count'] = len(rows) if isinstance(rows, list) else (1 if rows else 0)
                    except Exception:
                        tbl_info['rows'] = None
                else:
                    tbl_info['rows'] = None

        except Exception as e:
            tbl_info['error'] = str(e)

        report[table] = tbl_info

    # Print concise report
    print(f"Verification report for job_key={job_key}")
    for t, info in report.items():
        print('\n---', t, '---')
        if info.get('error'):
            print('ERROR:', info['error'])
            continue
        print('Writable columns (sample):', info.get('columns')[:10])
        print('Rows found:', info.get('count'))
        if info.get('rows'):
            sample = info['rows'][:2] if isinstance(info['rows'], list) else [info['rows']]
            print('Sample rows:')
            pprint(sample)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python scripts/verify_all_tables_for_job.py <job_key>')
        sys.exit(1)
    main(sys.argv[1])
