#!/usr/bin/env python3
import sys
from pathlib import Path
import json
from backend.config import XTBConfig, get_logger
from backend.core.xtb_runner import XTBRunner

logger = get_logger(__name__)

def main():
    if len(sys.argv) < 2:
        print("Usage: test_simulate_log.py <job_id>")
        sys.exit(2)

    job_id = sys.argv[1]
    cfg = XTBConfig()
    job_dir = Path(cfg.JOBS_DIR) / job_id
    results_path = job_dir / "results.json"
    if not results_path.exists():
        print(f"results.json not found for job {job_id} at {results_path}")
        sys.exit(1)

    with open(results_path, 'r') as fh:
        data = json.load(fh)
    results_obj = data.get('results') if isinstance(data, dict) and 'results' in data else data

    xtb_runner = XTBRunner(cfg, logger, enable_quality_logging=True)

    xtb_runner._assess_and_log_results(job_id, results_obj, 'normal', str(job_dir / (job_id.split('_')[0]+'.xyz')))
    print('Simulated logging complete.')


if __name__ == '__main__':
    main()
