from backend.api.job_manager import JobManager
from backend.config import XTBConfig
from backend.app.db.supabase_client import get_supabase_client
from pathlib import Path
import time

cfg = XTBConfig()
jm = JobManager(cfg)
xyz = "2\nH2 molecule\nH 0.0 0.0 0.0\nH 0.74 0.0 0.0\n"
job_id = jm.submit_job({'molecule_name':'H2_container_test','xyz_content': xyz})
print('submitted', job_id)
client = get_supabase_client()
print('before counts:')
print('quality', len(client.get('data_quality_metrics')))
print('lineage', len(client.get('data_lineage')))
print('molecules', len(client.get('molecules')))
print('calculations', len(client.get('calculations')))

jm.execute_job(job_id)
print('execution finished; waiting briefly for network writes...')

time.sleep(2)

print('after counts:')
print('quality', len(client.get('data_quality_metrics')))
print('lineage', len(client.get('data_lineage')))
print('molecules', len(client.get('molecules')))
print('calculations', len(client.get('calculations')))