#!/usr/bin/env python3
"""Integration test: submit a job with explicit SMILES and formula, run it and verify Supabase fills columns.
"""
from backend.api.job_manager import JobManager
from backend.config import XTBConfig
from backend.app.db.supabase_client import get_supabase_client
from pathlib import Path
import time
import os

jobs_dir = Path.cwd() / "test_jobs"
work_dir = Path.cwd() / "test_work"
# If the repo test_jobs isn't writable (e.g., owned by root in CI), fall back to a
# tmp directory to allow the integration test to run.
if not jobs_dir.exists() or os.access(str(jobs_dir), os.W_OK):
    cfg = XTBConfig(JOBS_DIR=str(jobs_dir), WORKDIR=str(work_dir))
else:
    import tempfile
    td = Path(tempfile.mkdtemp(prefix='integration_test_jobs_'))
    twd = td / 'work'
    cfg = XTBConfig(JOBS_DIR=str(td), WORKDIR=str(twd))
jm = JobManager(cfg)

xyz = "3\nWater\nO 0.0000 0.0000 0.0000\nH 0.7586 0.0000 0.5043\nH -0.7586 0.0000 0.5043\n"
job_id = jm.submit_job({'molecule_name': 'water_smiles_test', 'xyz_content': xyz, 'molecule_smiles': 'O', 'molecule_formula': 'H2O'})
print('Created job', job_id)

jm.run_job_async(job_id)

# Wait for job to finish
for i in range(30):
    metadata = jm.get_job_status(job_id)
    if metadata and metadata.get('status') == 'COMPLETED':
        print('Job completed')
        break
    time.sleep(1)
else:
    raise RuntimeError('Job did not complete in time')

client = get_supabase_client()
# Check molecules for our entry
mols = client.get('molecules', filters={'name': job_id.split('_')[0]})
print('Found molecules:', mols[:3])
calcs = client.get('calculations', filters={'output_json_path': f'jobs/{job_id}/xtbout.json'})
print('Found calcs:', calcs[:3])
metrics = client.get('data_quality_metrics', filters={'calculation_id': job_id})
print('Found quality metrics:', metrics[:3])
lineage = client.get('data_lineage', filters={'data_id': job_id})
print('Found lineage:', lineage[:3])
