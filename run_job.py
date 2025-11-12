from backend.config import XTBConfig
from backend.api.job_manager import JobManager
cfg=XTBConfig()
jm=JobManager(cfg)
job_id='water_test_20251112_135754_4c32bab1'
print('executing', job_id)
jm.execute_job(job_id)
