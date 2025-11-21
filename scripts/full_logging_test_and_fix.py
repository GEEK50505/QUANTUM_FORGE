"""Run a full logging test and attempt to fix missing-table inserts by probing writable columns.

Usage: run in the repo with the virtualenv activated. The script will:
 - load SUPABASE_SERVICE_ROLE_KEY from .env.backend if present
 - submit a temporary no-SMILES job and run it to completion
"""Run a full logging test and attempt to fix missing-table inserts by probing writable columns.

Usage: run in the repo with the virtualenv activated. The script will:
 - load SUPABASE_SERVICE_ROLE_KEY from .env.backend if present
 - submit a temporary no-SMILES job and run it to completion
 - query calculations to find numeric calculation_id and molecule_id
 - for each table from the attachment, query writable columns via OPTIONS
 - attempt a best-effort insert mapping available columns to values we have
 - re-query and print a summary of which inserts succeeded

This is best-effort and intentionally conservative: it only inserts fields
that are safe (job_key, calculation_id, molecule_id, timestamps, numeric values).
"""
import os
import sys
"""Run a full logging test and attempt to fix missing-table inserts by probing writable columns.
    'calculation_errors','calculation_execution_metrics','calculations','data_anomalies',
    'data_lineage','data_quality_metrics','event_logs','feature_extraction_log',
    'ml_dataset_assignments','ml_dataset_splits','model_training_log','molecule_properties_computed',
    'molecules','performance_metrics','runs','user_audit_log','user_preferences','user_sessions'
]


def load_service_key(path='.env.backend'):
    p = Path(path)
    if not p.exists():
        return
    txt = p.read_text()
    m = re.search(r'^SUPABASE_SERVICE_ROLE_KEY=(.+)$', txt, flags=re.M)
    if m:
        os.environ['SUPABASE_SERVICE_ROLE_KEY'] = m.group(1).strip()


def submit_and_run_job():
    td = Path(tempfile.mkdtemp(prefix='full_test_jobs_'))
    workdir = td / 'work'
    workdir.mkdir(parents=True, exist_ok=True)
    cfg = XTBConfig(JOBS_DIR=str(td), WORKDIR=str(workdir))
    jm = JobManager(cfg)
    xyz = "3\nNoSMILES\nO 0.0000 0.0000 0.0000\nH 0.7586 0.0000 0.5043\nH -0.7586 0.0000 0.5043\n"
    job_id = jm.submit_job({'molecule_name':'no_smiles_fulltest','xyz_content':xyz})
    jm.run_job_async(job_id)

    # wait for completion with timeout
    for _ in range(60):
        s = jm.get_job_status(job_id)
        if s and s.get('status') == 'COMPLETED':
            break
        time.sleep(1)
    else:
        raise RuntimeError('job did not complete in time')

    return job_id, td


def probe_and_fix(job_key: str):
    sb = get_supabase_client()

    # find calculation and molecule info
    calcs = []
    try:
        calcs = sb.get('calculations', filters={'job_key': job_key}, limit=5)
    except Exception as e:
        print('GET calculations failed:', e)
        return

    if not calcs:
        print('No calculation row found for job_key; aborting fix step')
        return

    calc = calcs[0]
    calc_id = calc.get('id')
    mol_id = calc.get('molecule_id')
    energy = calc.get('energy')
    gap = calc.get('gap')

    print('Found calc_id:', calc_id, 'molecule_id:', mol_id)

    results = {}
    now = time.strftime('%Y-%m-%dT%H:%M:%S%z')

    for table in TABLES:
        print('\nProbing table:', table)
        allowed = sb._get_table_writable_columns(table, method='insert')
        print('Writable columns:', allowed[:20])
        if not allowed:
            results[table] = 'no-writable-columns'
            continue

        payload = {}
        # conservative mappings
        if 'job_key' in allowed:
            payload['job_key'] = job_key
        if 'calculation_id' in allowed and calc_id is not None:
            payload['calculation_id'] = int(calc_id)
        if 'molecule_id' in allowed and mol_id is not None:
            payload['molecule_id'] = int(mol_id)
        if 'timestamp' in allowed and 'created_at' not in allowed:
            payload['timestamp'] = now
        if 'created_at' in allowed:
            payload['created_at'] = now
        if 'event_type' in allowed:
            payload['event_type'] = 'JOB_COMPLETED'
        if 'details' in allowed:
            payload['details'] = f'Auto-fill from full_logging_test for job {job_key}'
        if 'homo' in allowed:
            payload['homo'] = calc.get('homo')
        if 'lumo' in allowed:
            payload['lumo'] = calc.get('lumo')
        if 'gap' in allowed:
            payload['gap'] = calc.get('gap')
        if 'wall_time_seconds' in allowed:
            # Try to compute wall_time from execution metrics if present
            try:
                em = sb.get('calculation_execution_metrics', filters={'job_key': job_key}, limit=1)
                wt = em[0].get('wall_time_seconds') if em and isinstance(em, list) and em else None
            except Exception:
                wt = None
            payload['wall_time_seconds'] = wt
        if 'user_email' in allowed:
            payload['user_email'] = None

        # Skip empty payloads
        if not payload:
            results[table] = 'no-safe-fields'
            continue

        # Attempt the insert
        try:
            r = sb.insert(table, payload)
            if r:
                results[table] = 'inserted'
                print('Inserted into', table, 'result sample:', (r if isinstance(r, dict) else (r[0] if isinstance(r, list) and r else r)))
            else:
                results[table] = 'insert-failed'
                print('Insert returned falsy for', table)
        except Exception as e:
            results[table] = f'error:{e}'
            print('Insert error for', table, e)

    print('\nSummary of fix attempts:')
    pprint(results)
    return results


def reverify(job_key: str):
    print('\nRe-running verification report:')
    # reuse the verify script if present
    from subprocess import run
    env = os.environ.copy()
    env['PYTHONPATH'] = str(ROOT)
    proc = run([sys.executable, 'scripts/verify_all_tables_for_job.py', job_key], capture_output=True, text=True, env=env)
    print(proc.stdout)
    if proc.stderr:
        print('VERIFY STDERR:', proc.stderr)


if __name__ == '__main__':
    load_service_key()
    job_key, td = submit_and_run_job()
    try:
        probe_and_fix(job_key)
        reverify(job_key)
    finally:
        # cleanup
        shutil.rmtree(td)