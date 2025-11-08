"""Simple filesystem-based JobStore used by JobManager.

This module provides a small, test-friendly abstraction over filesystem
operations so the rest of the code doesn't directly perform path and
JSON reads/writes. Keeping this layer makes it easier to migrate to a
database-backed store later.
"""
from pathlib import Path
from typing import Optional, Dict, List
import json


class JobStore:
	def __init__(self, jobs_dir: str):
		self.jobs_dir = Path(jobs_dir)
		self.jobs_dir.mkdir(parents=True, exist_ok=True)

	def create_job_dir(self, job_id: str) -> Path:
		p = self.jobs_dir / job_id
		p.mkdir(parents=True, exist_ok=True)
		return p

	def save_xyz(self, job_id: str, molecule_name: str, content: str) -> Path:
		job_dir = self.create_job_dir(job_id)
		xyz_path = job_dir / f"{molecule_name}.xyz"
		with open(xyz_path, 'w', encoding='utf-8') as f:
			f.write(content)
		return xyz_path

	def metadata_path(self, job_id: str) -> Path:
		return self.jobs_dir / job_id / "metadata.json"

	def save_metadata(self, job_id: str, metadata: Dict) -> Path:
		p = self.metadata_path(job_id)
		p.parent.mkdir(parents=True, exist_ok=True)
		with open(p, 'w', encoding='utf-8') as f:
			json.dump(metadata, f, indent=2)
		return p

	def load_metadata(self, job_id: str) -> Optional[Dict]:
		p = self.metadata_path(job_id)
		if not p.exists():
			return None
		with open(p, 'r', encoding='utf-8') as f:
			return json.load(f)

	def save_results(self, job_id: str, results: Dict) -> Path:
		job_dir = self.jobs_dir / job_id
		job_dir.mkdir(parents=True, exist_ok=True)
		out_path = job_dir / "results.json"
		with open(out_path, 'w', encoding='utf-8') as f:
			json.dump(results, f, indent=2)
		return out_path

	def list_jobs(self, status: Optional[str] = None, limit: int = 50) -> List[Dict]:
		jobs = []
		dirs = [d for d in self.jobs_dir.iterdir() if d.is_dir()]
		dirs.sort(key=lambda x: x.stat().st_ctime, reverse=True)
		for d in dirs[:limit]:
			meta = d / "metadata.json"
			if not meta.exists():
				continue
			try:
				with open(meta, 'r', encoding='utf-8') as f:
					data = json.load(f)
				if status is None or data.get('status') == status:
					jobs.append(data)
			except Exception:
				continue
		return jobs

