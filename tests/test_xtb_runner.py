"""Unit tests for xTB runner and parser modules."""

import pytest
import json
from pathlib import Path
from datetime import datetime

from backend.simulation.classical_sim.xtb_parser import XTBLogParser
from backend.simulation.classical_sim.xtb_runner import XTBRunner


@pytest.fixture
def benzene_input():
    """Fixture providing path to benzene XYZ file."""
    return Path("data/molecules/benzene/benzene.xyz")


@pytest.fixture
def log_file():
    """Fixture providing path to sample xTB log file."""
    return Path("data/molecules/benzene/xtbopt.log")


class TestXTBRunner:
    """Test cases for XTBRunner class."""

    def test_runner_initialization(self, benzene_input):
        """Test XTBRunner initialization."""
        runner = XTBRunner(benzene_input, workdir="./test_runs")
        assert runner.input_xyz == benzene_input
        assert runner.workdir.name == "test_runs"
        assert benzene_input.exists()

    def test_runner_execution(self, benzene_input):
        """Test XTBRunner execution (mocked)."""
        # This test would normally run xTB, but we'll skip actual execution
        # and focus on testing the structure
        runner = XTBRunner(benzene_input, workdir="./test_runs")
        job_id = runner.generate_job_id()
        assert job_id.startswith("xtb_job_")
        assert len(job_id) > 8


class TestXTBParser:
    """Test cases for XTBLogParser class."""

    def test_parser_initialization(self, log_file):
        """Test XTBLogParser initialization."""
        if log_file.exists():
            parser = XTBLogParser(log_file)
            assert parser.log_file == log_file
        else:
            # Skip if log file doesn't exist
            pytest.skip("Log file not found for testing")

    def test_extract_energy(self, log_file):
        """Test energy extraction from log file."""
        if not log_file.exists():
            pytest.skip("Log file not found for testing")
            
        parser = XTBLogParser(log_file)
        energy = parser.extract_total_energy()
        
        # Energy should be negative for stable molecules
        if energy is not None:
            assert energy < 0
            # Benzene energy should be reasonable
            assert -20 < energy < 0

    def test_extract_convergence(self, log_file):
        """Test convergence status extraction."""
        if not log_file.exists():
            pytest.skip("Log file not found for testing")
            
        parser = XTBLogParser(log_file)
        convergence = parser.extract_convergence_status()
        
        # Should be boolean or None
        assert convergence is None or isinstance(convergence, bool)

    def test_parse_all(self, log_file):
        """Test parsing all properties."""
        if not log_file.exists():
            pytest.skip("Log file not found for testing")
            
        parser = XTBLogParser(log_file)
        results = parser.parse_all()
        
        # Should return a dictionary
        assert isinstance(results, dict)
        
        # Check that all expected keys are present
        expected_keys = [
            "total_energy", "gradient_norm", "homo_lumo_gap", 
            "convergence_status", "timing", "homo_energy_ev",
            "lumo_energy_ev", "fermi_level_ev", "dipole_moment_debye"
        ]
        
        for key in expected_keys:
            assert key in results
            
        # Timing should be a dictionary
        assert isinstance(results["timing"], dict)
        
        # If energy is present, it should be reasonable
        if results["total_energy"] is not None:
            assert results["total_energy"] < 0
            assert -100 < results["total_energy"] < 0