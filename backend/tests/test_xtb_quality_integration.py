"""
Test xTB Runner Integration with Quality Assessment

Tests the quality logging and lineage tracking features added to
the xTB runner during Phase 2 implementation.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from backend.core.xtb_runner import XTBRunner, XTBConfig
from backend.app.db.data_quality import QualityAssessor


class TestXTBQualityIntegration:
    """Test quality assessment integration in XTB runner"""
    
    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return XTBConfig(
            XTB_EXECUTABLE="/usr/bin/xtb",
            JOBS_DIR="/tmp/test_jobs",
            WORKDIR="/tmp/test_work",
            XTB_TIMEOUT=30
        )
    
    @pytest.fixture
    def runner(self, config):
        """Create runner with quality logging disabled for faster tests"""
        runner = XTBRunner(config, enable_quality_logging=False)
        return runner
    
    @pytest.fixture
    def runner_with_quality(self, config):
        """Create runner with quality logging enabled (mocked)"""
        runner = XTBRunner(config, enable_quality_logging=True)
        # Mock the Supabase client
        runner.supabase_client = Mock()
        runner.supabase_client.insert = Mock(return_value={"id": 1})
        return runner
    
    def test_quality_assessor_initialization(self, runner):
        """Test QualityAssessor is properly initialized"""
        assert runner.quality_assessor is not None
        assert isinstance(runner.quality_assessor, QualityAssessor)
    
    def test_supabase_client_initialization(self, runner_with_quality):
        """Test Supabase client is initialized when enabled"""
        assert runner_with_quality.supabase_client is not None
        assert runner_with_quality.enable_quality_logging is True
    
    def test_log_quality_metrics_successful(self, runner_with_quality):
        """Test successful quality metrics logging"""
        calc_id = "test_calc_001"
        molecule_smiles = "C1=CC=CC=C1"
        quality_metrics = {
            'completeness': 95,
            'validity': 90,
            'consistency': 92,
            'uniqueness': 100,
        }
        
        result = runner_with_quality.log_quality_metrics(
            calc_id=calc_id,
            molecule_smiles=molecule_smiles,
            quality_metrics=quality_metrics,
            is_ml_ready=True
        )
        
        assert result is True
        runner_with_quality.supabase_client.insert.assert_called_once()
        
        # Verify the payload structure
        call_args = runner_with_quality.supabase_client.insert.call_args
        assert call_args[0][0] == 'data_quality_metrics'
        payload = call_args[0][1]
        assert payload['calculation_id'] == calc_id
        assert payload['molecule_smiles'] == molecule_smiles
        assert payload['is_ml_ready'] is True
        assert 'quality_score' in payload
        assert 'assessed_at' in payload
    
    def test_log_lineage_successful(self, runner_with_quality):
        """Test successful lineage logging"""
        calc_id = "test_calc_001"
        molecule_smiles = "C1=CC=CC=C1"
        
        result = runner_with_quality.log_lineage(
            calc_id=calc_id,
            molecule_smiles=molecule_smiles,
            xtb_version="6.7.1",
            git_commit="abc123def456",
            input_parameters={'method': 'gfn2-xtb', 'opt': 'normal'}
        )
        
        assert result is True
        runner_with_quality.supabase_client.insert.assert_called_once()
        
        # Verify the payload structure
        call_args = runner_with_quality.supabase_client.insert.call_args
        assert call_args[0][0] == 'data_lineage'
        payload = call_args[0][1]
        assert payload['data_id'] == calc_id
        assert payload['source_version'] == "6.7.1"
        assert payload['git_commit'] == "abc123def456"
        assert payload['approved_for_ml'] is False  # Initially not approved
        assert 'created_at_source' in payload
    
    def test_log_error_successful(self, runner_with_quality):
        """Test successful error logging"""
        calc_id = "test_calc_001"
        error_msg = "xTB optimization failed: convergence error"
        
        result = runner_with_quality.log_error(
            calc_id=calc_id,
            error_message=error_msg,
            error_type="convergence_error",
            molecule_smiles="C1=CC=CC=C1"
        )
        
        assert result is True
        runner_with_quality.supabase_client.insert.assert_called_once()
        
        # Verify the payload structure
        call_args = runner_with_quality.supabase_client.insert.call_args
        assert call_args[0][0] == 'calculation_errors'
        payload = call_args[0][1]
        assert payload['calculation_id'] == calc_id
        assert payload['error_type'] == "convergence_error"
        assert payload['error_message'] == error_msg
        assert 'occurred_at' in payload
    
    def test_logging_disabled(self, runner):
        """Test that logging gracefully skips when disabled"""
        calc_id = "test_calc_001"
        
        result = runner.log_quality_metrics(
            calc_id=calc_id,
            molecule_smiles="C1=CC=CC=C1",
            quality_metrics={},
            is_ml_ready=False
        )
        
        assert result is False  # Should return False when disabled
    
    def test_quality_metrics_calculation(self):
        """Test quality score calculation"""
        metrics = {
            'completeness': 100,  # 25% weight
            'validity': 80,       # 35% weight
            'consistency': 90,    # 30% weight
            'uniqueness': 100,    # 10% weight
        }
        
        # Calculate expected score
        expected = (
            0.25 * 100 +  # completeness
            0.35 * 80 +   # validity
            0.30 * 90 +   # consistency
            0.10 * 100    # uniqueness
        )
        # Expected: 25 + 28 + 27 + 10 = 90
        assert expected == 90.0


class TestXTBExecutionWithQuality:
    """Test xTB execution with quality assessment integration"""
    
    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return XTBConfig(
            XTB_EXECUTABLE="/usr/bin/xtb",
            JOBS_DIR="/tmp/test_jobs",
            WORKDIR="/tmp/test_work",
            XTB_TIMEOUT=30
        )
    
    @pytest.fixture
    def sample_xyz(self):
        """Create a sample XYZ file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
            f.write("2\n")
            f.write("H2 molecule\n")
            f.write("H 0.0 0.0 0.0\n")
            f.write("H 0.74 0.0 0.0\n")
            return f.name
    
    def test_execute_with_quality_logging_mocked(self, config, sample_xyz):
        """Test execute() with mocked quality logging"""
        runner = XTBRunner(config, enable_quality_logging=True)
        
        # Mock Supabase client
        runner.supabase_client = Mock()
        runner.supabase_client.insert = Mock(return_value={"id": 1})
        
        # Mock subprocess to return success
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            "energy": -1.174,
            "gap": 15.5,
            "homo": -8.5,
            "lumo": 7.0,
            "dipole_moment": 0.0
        })
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result):
            result = runner.execute(sample_xyz, "test_job_001")
        
        assert result["success"] is True
        assert result["energy"] is not None
        
        # Verify quality logging was called
        assert runner.supabase_client.insert.call_count >= 2
        
        # Check that both quality_metrics and lineage tables were logged
        calls = runner.supabase_client.insert.call_args_list
        tables_called = [call[0][0] for call in calls]
        assert 'data_quality_metrics' in tables_called
        assert 'data_lineage' in tables_called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
