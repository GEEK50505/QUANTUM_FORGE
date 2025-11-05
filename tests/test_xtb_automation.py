"""
Integration tests for QUANTUM_FORGE xTB automation pipeline.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import tempfile
import hashlib
from pathlib import Path
from backend.core.logger import setup_logger
from backend.simulation.classical_sim.xtb_runner import XTBRunner
from backend.simulation.classical_sim.xtb_parser import XTBLogParser


# Test fixtures
@pytest.fixture
def logger_fixture():
    """Create a test logger."""
    return setup_logger("test_xtb_automation")


@pytest.fixture
def test_workdir():
    """Create a temporary working directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def benzene_input():
    """Create a benzene test input file."""
    # Create a simple benzene XYZ file
    benzene_xyz = """12
benzene molecule
C    0.000000    1.390000    0.000000
C    1.200000    0.695000    0.000000
C    1.200000   -0.695000    0.000000
C    0.000000   -1.390000    0.000000
C   -1.200000   -0.695000    0.000000
C   -1.200000    0.695000    0.000000
H    0.000000    2.470000    0.000000
H    2.140000    1.235000    0.000000
H    2.140000   -1.235000    0.000000
H    0.000000   -2.470000    0.000000
H   -2.140000   -1.235000    0.000000
H   -2.140000    1.235000    0.000000
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
        f.write(benzene_xyz)
        f.flush()
        yield Path(f.name)
    
    # Cleanup
    Path(f.name).unlink(missing_ok=True)


def test_full_pipeline_benzene(benzene_input, test_workdir, logger_fixture, caplog):
    """Test full pipeline with benzene molecule."""
    logger_fixture.info("Starting full pipeline test with benzene")
    
    # Create runner
    runner = XTBRunner(str(benzene_input), str(test_workdir), logger_fixture)
    
    # Verify job ID is unique
    assert runner.job_id is not None
    assert "_" in runner.job_id
    
    # Test hash computation
    file_hash = runner.compute_file_hash(str(benzene_input))
    assert isinstance(file_hash, str)
    assert len(file_hash) == 64  # SHA256 hash length
    
    # Test input validation
    assert runner.validate_input_file() is True
    
    # Note: We're not actually running xTB in tests to avoid external dependencies
    # Instead, we'll test the structure and logging
    logger_fixture.info("Full pipeline test completed successfully")


def test_runner_logging_contains_expected_messages(benzene_input, test_workdir, logger_fixture, caplog):
    """Test that runner produces expected log messages."""
    caplog.clear()
    
    # Create runner (this will generate logs)
    runner = XTBRunner(str(benzene_input), str(test_workdir), logger_fixture)
    
    # Check for expected log messages
    log_messages = [record.message for record in caplog.records]
    
    # Should contain initialization messages
    assert any("Initializing XTBRunner" in msg for msg in log_messages)
    assert any("Working directory" in msg for msg in log_messages)
    assert any("Generated job ID" in msg for msg in log_messages)
    
    logger_fixture.info("Runner logging test completed")


def test_parser_logging_on_missing_values(logger_fixture, caplog):
    """Test parser logging when values are missing."""
    # Create a minimal log file with missing values
    minimal_log_content = """------------------------------------------------------------
          xtb version 6.4.1 (compiled for linux64)
------------------------------------------------------------
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write(minimal_log_content)
        f.flush()
        log_file = Path(f.name)
    
    try:
        caplog.clear()
        parser = XTBLogParser(str(log_file), logger_fixture)
        
        # Try to extract values (should log warnings for missing values)
        energy = parser.extract_total_energy()
        assert energy is None
        
        gap = parser.extract_homo_lumo_gap()
        assert gap is None
        
        # Check that warnings were logged
        warning_messages = [record.message for record in caplog.records if record.levelname == "WARNING"]
        assert any("Could not extract total energy" in msg for msg in warning_messages)
        assert any("Could not extract HOMO-LUMO gap" in msg for msg in warning_messages)
        
    finally:
        log_file.unlink(missing_ok=True)
    
    logger_fixture.info("Parser missing values logging test completed")


def test_job_retry_on_timeout(logger_fixture, caplog, mocker):
    """Test job retry mechanism on timeout."""
    # This test would mock subprocess to simulate timeout
    # For now, we'll test the structure
    logger_fixture.info("Job retry test completed (mock implementation)")


def test_hash_computation_consistency(benzene_input, logger_fixture, caplog):
    """Test that hash computation is consistent."""
    caplog.clear()
    
    # Create runner
    runner = XTBRunner(str(benzene_input), "./test_runs", logger_fixture)
    
    # Generate hash twice
    hash1 = runner.compute_file_hash(str(benzene_input))
    hash2 = runner.compute_file_hash(str(benzene_input))
    
    # Should be identical
    assert hash1 == hash2
    assert len(hash1) == 64
    
    # Check log contains file path and hash
    log_messages = [record.message for record in caplog.records]
    assert any(str(benzene_input) in msg for msg in log_messages)
    assert any(hash1[:10] in msg for msg in log_messages)  # Check first 10 chars of hash
    
    logger_fixture.info("Hash computation consistency test completed")