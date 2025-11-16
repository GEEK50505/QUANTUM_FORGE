#!/usr/bin/env python3
"""
Database Validation and Test Script

Performs:
- Connection testing
- Schema verification
- CRUD operations testing
- Performance benchmarking
- Data integrity checks

Usage:
    python backend/scripts/test_database.py

Requires:
    - DATABASE_URL or DB_* environment variables set
    - Database initialized with schema.sql
"""

import sys
import time
import logging
from pathlib import Path
from typing import List

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.db.database import setup_database, get_db_context, check_db_health
from backend.app.db import crud
from backend.app.db.schemas import (
    MoleculeCreate, CalculationCreate, BatchJobCreate, BatchItemCreate
)
from backend.app.config import validate_database_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestResults:
    """Track test results"""
    def __init__(self):
        self.passed = []
        self.failed = []
    
    def add_pass(self, test_name: str, details: str = ""):
        self.passed.append((test_name, details))
        logger.info(f"✓ PASS: {test_name}" + (f" - {details}" if details else ""))
    
    def add_fail(self, test_name: str, error: str):
        self.failed.append((test_name, error))
        logger.error(f"✗ FAIL: {test_name} - {error}")
    
    def summary(self):
        total = len(self.passed) + len(self.failed)
        passed_count = len(self.passed)
        return f"{passed_count}/{total} tests passed"


def test_connection():
    """Test database connection"""
    results = TestResults()
    
    try:
        # Validate config
        is_valid, message = validate_database_config()
        if not is_valid:
            results.add_fail("Config validation", message)
            return results
        results.add_pass("Config validation")
        
        # Setup database
        engine, SessionLocal = setup_database()
        results.add_pass("Engine creation")
        
        # Health check
        health = check_db_health(engine)
        if health['status'] == 'healthy':
            results.add_pass("Health check", health['message'])
        else:
            results.add_fail("Health check", health['message'])
        
        return results
        
    except Exception as e:
        results.add_fail("Connection", str(e))
        return results


def test_crud_operations():
    """Test CRUD operations"""
    results = TestResults()
    
    try:
        setup_database()
        
        with get_db_context() as db:
            # Create molecule
            mol_create = MoleculeCreate(
                name="Test Water",
                smiles="O",
                formula="H2O",
                metadata={"source": "test"}
            )
            molecule = crud.create_molecule(db, mol_create)
            results.add_pass("Create molecule", f"ID={molecule.id}")
            
            # Read molecule
            mol_read = crud.get_molecule(db, molecule.id)
            if mol_read and mol_read.smiles == "O":
                results.add_pass("Read molecule")
            else:
                results.add_fail("Read molecule", "SMILES mismatch")
            
            # List molecules
            mols, total = crud.list_molecules(db, limit=10)
            results.add_pass("List molecules", f"Found {total} total")
            
            # Create calculation
            calc_create = CalculationCreate(
                molecule_id=molecule.id,
                energy=-5.105,
                homo=-0.42,
                lumo=0.18,
                gap=0.60,
                dipole=1.85,
                execution_time_seconds=2.5,
                xtb_version="6.7.1",
                convergence_status="converged"
            )
            calculation = crud.create_calculation(db, calc_create)
            results.add_pass("Create calculation", f"ID={calculation.id}, E={calculation.energy}")
            
            # Read calculation
            calc_read = crud.get_calculation(db, calculation.id)
            if calc_read and abs(calc_read.energy - (-5.105)) < 0.001:
                results.add_pass("Read calculation")
            else:
                results.add_fail("Read calculation", "Energy mismatch")
            
            # List calculations
            calcs, total = crud.list_calculations(db, limit=10)
            results.add_pass("List calculations", f"Found {total} total")
            
            # Query by energy range
            calcs_range = crud.get_calculations_by_energy_range(db, -10.0, 0.0)
            if len(calcs_range) > 0:
                results.add_pass("Energy range query", f"Found {len(calcs_range)}")
            else:
                results.add_fail("Energy range query", "No results")
            
            # Query by gap range
            calcs_gap = crud.get_calculations_by_gap_range(db, 0.0, 1.0)
            if len(calcs_gap) > 0:
                results.add_pass("Gap range query", f"Found {len(calcs_gap)}")
            else:
                results.add_fail("Gap range query", "No results")
            
            # Create atomic properties
            props = crud.create_atomic_properties(
                db,
                calculation.id,
                [
                    {
                        'atom_index': 0,
                        'element': 'O',
                        'atomic_number': 8,
                        'partial_charge': -0.5,
                        'position_x': 0.0,
                        'position_y': 0.0,
                        'position_z': 0.0
                    },
                    {
                        'atom_index': 1,
                        'element': 'H',
                        'atomic_number': 1,
                        'partial_charge': 0.25,
                        'position_x': 0.957,
                        'position_y': 0.0,
                        'position_z': 0.0
                    }
                ]
            )
            results.add_pass("Create atomic properties", f"Created {len(props)} atoms")
            
            # Read atomic properties
            props_read = crud.get_atomic_properties_for_calculation(db, calculation.id)
            if len(props_read) == 2:
                results.add_pass("Read atomic properties")
            else:
                results.add_fail("Read atomic properties", f"Expected 2, got {len(props_read)}")
            
            # Create batch job
            batch_create = BatchJobCreate(
                batch_name="Test Batch",
                description="For testing",
                total_molecules=1
            )
            batch = crud.create_batch_job(db, batch_create)
            results.add_pass("Create batch", f"ID={batch.id}")
            
            # Create batch item
            item_create = BatchItemCreate(
                batch_id=batch.id,
                molecule_id=molecule.id,
                status="completed"
            )
            item = crud.create_batch_item(db, item_create)
            results.add_pass("Create batch item", f"ID={item.id}")
            
            # Update batch item
            item_updated = crud.update_batch_item_status(
                db,
                item.id,
                "completed",
                calculation_id=calculation.id
            )
            if item_updated and item_updated.calculation_id == calculation.id:
                results.add_pass("Update batch item")
            else:
                results.add_fail("Update batch item", "Update failed")
            
            # Get batch items
            items = crud.get_batch_items(db, batch.id)
            if len(items) == 1:
                results.add_pass("List batch items")
            else:
                results.add_fail("List batch items", f"Expected 1, got {len(items)}")
        
        return results
        
    except Exception as e:
        results.add_fail("CRUD operations", str(e))
        return results


def test_performance():
    """Test query performance"""
    results = TestResults()
    
    try:
        setup_database()
        
        with get_db_context() as db:
            # Bulk create for performance testing
            start = time.time()
            for i in range(10):
                mol_create = MoleculeCreate(
                    name=f"Perf Test {i}",
                    smiles=f"C{i}",  # Each gets unique SMILES
                    formula="CxHy"
                )
                mol = crud.create_molecule(db, mol_create)
                
                calc_create = CalculationCreate(
                    molecule_id=mol.id,
                    energy=-5.0 - i * 0.1,
                    gap=0.5 + i * 0.05,
                    execution_time_seconds=1.0 + i * 0.1
                )
                crud.create_calculation(db, calc_create)
            
            creation_time = time.time() - start
            results.add_pass("Bulk creation", f"10 molecules + calcs in {creation_time:.2f}s")
            
            # List performance
            start = time.time()
            mols, total = crud.list_molecules(db, limit=1000)
            list_time = time.time() - start
            results.add_pass("List 1000", f"{total} molecules fetched in {list_time:.3f}s")
            
            # Range query performance
            start = time.time()
            calcs = crud.get_calculations_by_energy_range(db, -10.0, 0.0, limit=1000)
            query_time = time.time() - start
            results.add_pass("Range query", f"Found {len(calcs)} in {query_time:.3f}s")
        
        return results
        
    except Exception as e:
        results.add_fail("Performance", str(e))
        return results


def test_event_logging():
    """Test event logging"""
    results = TestResults()
    
    try:
        setup_database()
        
        with get_db_context() as db:
            # Create an event
            event = crud.log_event(
                db=db,
                event_type="test_event",
                entity_type="molecules",
                entity_id=1,
                status="success",
                context={"test": True}
            )
            
            if event and event.event_type == "test_event":
                results.add_pass("Log event", f"ID={event.id}")
            else:
                results.add_fail("Log event", "Event creation failed")
            
            # Retrieve events
            events, total = crud.get_event_logs(
                db=db,
                entity_type="molecules",
                limit=100
            )
            
            results.add_pass("Retrieve events", f"Found {total} events")
        
        return results
        
    except Exception as e:
        results.add_fail("Event logging", str(e))
        return results


def test_statistics():
    """Test statistics queries"""
    results = TestResults()
    
    try:
        setup_database()
        
        with get_db_context() as db:
            stats = crud.get_database_stats(db)
            
            required_keys = [
                'total_molecules',
                'total_calculations',
                'total_batches',
                'success_rate'
            ]
            
            missing_keys = [k for k in required_keys if k not in stats]
            if missing_keys:
                results.add_fail("Statistics", f"Missing keys: {missing_keys}")
            else:
                details = (
                    f"Molecules={stats['total_molecules']}, "
                    f"Calcs={stats['total_calculations']}, "
                    f"Success={stats['success_rate']:.1f}%"
                )
                results.add_pass("Statistics query", details)
        
        return results
        
    except Exception as e:
        results.add_fail("Statistics", str(e))
        return results


def main():
    """Run all tests"""
    logger.info("=" * 80)
    logger.info("QUANTUM FORGE DATABASE TEST SUITE")
    logger.info("=" * 80)
    
    all_results = {
        "Connection": test_connection(),
        "CRUD Operations": test_crud_operations(),
        "Performance": test_performance(),
        "Event Logging": test_event_logging(),
        "Statistics": test_statistics(),
    }
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    
    total_passed = 0
    total_failed = 0
    
    for test_group, results in all_results.items():
        logger.info(f"\n{test_group}: {results.summary()}")
        total_passed += len(results.passed)
        total_failed += len(results.failed)
    
    logger.info(f"\nOverall: {total_passed}/{total_passed + total_failed} tests passed")
    
    return 0 if total_failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
