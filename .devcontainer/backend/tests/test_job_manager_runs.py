import tempfile
import os
import json
import time
from unittest.mock import Mock, patch
from pathlib import Path

from backend.api.job_manager import JobManager
from backend.config import XTBConfig


class MockXTBRunner:
    def __init__(self, *args, **kwargs):
        self.supabase_client = Mock()
        self.enable_quality_logging = True
        self.log_error = Mock()
        self.log_run = Mock()
        self.log_molecule = Mock(return_value=(True, 123))
        self.log_calculation = Mock(return_value=True)
        # Record instances so test can inspect calls
        if not hasattr(MockXTBRunner, '_instances'):
            MockXTBRunner._instances = []
        MockXTBRunner._instances.append(self)

    def execute(self, xyz_file_path, job_id, optimization_level="normal"):
        # Simulate validation failure for overlapping coords
        return {"success": False, "error": "Invalid XYZ file: overlapping"}


def test_execute_logs_run_and_error_on_invalid_xyz(tmp_path, monkeypatch):
    cfg = XTBConfig(XTB_EXECUTABLE="/usr/bin/xtb", JOBS_DIR=str(tmp_path), WORKDIR=str(tmp_path))
    jm = JobManager(cfg)

    # Patch XTBRunner with our mock
    monkeypatch.setattr('backend.api.job_manager.XTBRunner', MockXTBRunner)

    # Submit a job with overlapping coordinates
    xyz = "3\nbad water\nO 0 0 0\nH 0 0 0\nH 0 0 0\n"
    job_id = jm.submit_job({'molecule_name': 'bad_water', 'xyz_content': xyz})
    # Execute synchronously
    jm.execute_job(job_id)

    # Read metadata and ensure status failed
    meta = jm.get_job_status(job_id)
    assert meta is not None and meta['status'] == 'FAILED'
    # Ensure metadata contains an error message
    assert 'error_message' in meta and 'Invalid XYZ' in meta['error_message']
    # Check that the mocked runner's log_error and log_run were called
    assert hasattr(MockXTBRunner, '_instances') and len(MockXTBRunner._instances) > 0
    inst = MockXTBRunner._instances[0]
    inst.log_error.assert_called()
    # The mock's log_run should be called for failed runs
    inst.log_run.assert_called()


def test_execute_logs_run_and_error_on_runtime_exception(tmp_path, monkeypatch):
    cfg = XTBConfig(XTB_EXECUTABLE="/usr/bin/xtb", JOBS_DIR=str(tmp_path), WORKDIR=str(tmp_path))
    jm = JobManager(cfg)

    class MockXTBRunnerRaise(MockXTBRunner):
        def execute(self, xyz_file_path, job_id, optimization_level="normal"):
            raise RuntimeError("Unexpected error in runner")

    # Patch XTBRunner with our exception-raising mock
    monkeypatch.setattr('backend.api.job_manager.XTBRunner', MockXTBRunnerRaise)

    xyz = "2\nH2\nH 0 0 0\nH 0.74 0 0\n"
    job_id = jm.submit_job({'molecule_name': 'h2', 'xyz_content': xyz})
    jm.execute_job(job_id)

    meta = jm.get_job_status(job_id)
    assert meta is not None and meta['status'] == 'FAILED'
    assert 'Unexpected error' in meta['error_message']
    # Check that log_run and log_error were called on the instance
    assert len(MockXTBRunnerRaise._instances) > 0
    inst = MockXTBRunnerRaise._instances[0]
    # We expect the runner to have recorded the run; log_error may or may
    # not be called depending on execution path, but run should be logged.
    inst.log_run.assert_called()
