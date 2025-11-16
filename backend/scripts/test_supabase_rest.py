#!/usr/bin/env python3
"""
Test Supabase REST API Connection

Validates:
- HTTP connectivity to Supabase
- REST API endpoint access
- Basic CRUD operations
- Schema verification

Usage:
    python backend/scripts/test_supabase_rest.py

Requires:
    - SUPABASE_URL environment variable
    - SUPABASE_KEY environment variable
    - Schema initialized (backend/scripts/schema.sql)
"""

import sys
import time
import logging
from pathlib import Path
from typing import List

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.db.supabase_client import get_supabase_client
from backend.app.config import get_settings
import json

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
        logger.info(f"✓ PASS: {test_name}")
        if details:
            logger.info(f"  {details}")
    
    def add_fail(self, test_name: str, error: str):
        self.failed.append((test_name, error))
        logger.error(f"✗ FAIL: {test_name} - {error}")
    
    def summary(self):
        total = len(self.passed) + len(self.failed)
        logger.info("\n" + "=" * 80)
        logger.info("TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"\nPassed: {len(self.passed)}/{total}")
        logger.info(f"Failed: {len(self.failed)}/{total}\n")
        
        if self.failed:
            logger.info("Failed Tests:")
            for test_name, error in self.failed:
                logger.info(f"  - {test_name}: {error}")
        
        return len(self.failed) == 0


def test_config():
    """Test configuration validation"""
    results = TestResults()
    
    try:
        settings = get_settings()
        if not settings.SUPABASE_URL:
            results.add_fail("Config validation", "SUPABASE_URL not set")
            return results
        if not settings.SUPABASE_KEY:
            results.add_fail("Config validation", "SUPABASE_KEY not set")
            return results
        
        results.add_pass("Config validation", f"Supabase: {settings.SUPABASE_URL}")
    except Exception as e:
        results.add_fail("Config validation", str(e))
    
    return results


def test_connection():
    """Test HTTP connection to Supabase"""
    results = TestResults()
    
    try:
        client = get_supabase_client()
        logger.info(f"Connecting to {client.url}...")
        
        # Test health check
        start = time.time()
        is_healthy = client.health_check()
        elapsed = time.time() - start
        
        if is_healthy:
            results.add_pass(
                "HTTP Connection",
                f"Connected in {elapsed:.2f}s via HTTP/HTTPS"
            )
        else:
            results.add_fail("HTTP Connection", "Health check returned False")
    
    except Exception as e:
        results.add_fail("HTTP Connection", str(e))
    
    return results


def test_read_operations():
    """Test GET operations on all tables"""
    results = TestResults()
    
    try:
        client = get_supabase_client()
        tables = [
            "molecules",
            "calculations",
            "atomic_properties",
            "batch_jobs",
            "batch_items",
            "event_logs",
        ]
        
        for table in tables:
            try:
                # Try to fetch one row
                rows = client.get(table, limit=1)
                count = len(rows)
                results.add_pass(
                    f"Read {table}",
                    f"Table exists, fetched {count} rows"
                )
            except Exception as e:
                results.add_fail(f"Read {table}", str(e))
    
    except Exception as e:
        results.add_fail("Read operations setup", str(e))
    
    return results


def test_write_operations():
    """Test INSERT operations"""
    results = TestResults()
    
    try:
        client = get_supabase_client()
        
        # Create test molecule
        molecule_data = {
            "name": "test_molecule_rest_api",
            "smiles": "CCO",
            "formula": "C2H6O",
        }
        
        try:
            mol = client.insert("molecules", molecule_data)
            if mol and "id" in mol:
                results.add_pass(
                    "Insert molecule",
                    f"Created molecule ID {mol['id']}"
                )
                mol_id = mol["id"]
                
                # Try to insert calculation for this molecule
                calc_data = {
                    "molecule_id": mol_id,
                    "energy": -10.5,
                    "homo": -0.3,
                    "lumo": 0.2,
                    "gap": 0.5,
                    "dipole": 1.85,
                    "execution_time_seconds": 12.5,
                    "method": "GFN2-xTB",
                    "convergence_status": "converged",
                }
                
                calc = client.insert("calculations", calc_data)
                if calc and "id" in calc:
                    results.add_pass(
                        "Insert calculation",
                        f"Created calculation ID {calc['id']}"
                    )
                else:
                    results.add_fail("Insert calculation", "No ID returned")
            else:
                results.add_fail("Insert molecule", "No ID returned")
        
        except Exception as e:
            results.add_fail("Write operations", str(e))
    
    except Exception as e:
        results.add_fail("Write setup", str(e))
    
    return results


def test_update_operations():
    """Test PATCH operations"""
    results = TestResults()
    
    try:
        client = get_supabase_client()
        
        # Get a molecule to update
        molecules = client.get("molecules", limit=1, select="id,name")
        if not molecules:
            results.add_fail("Update operations", "No molecules to update")
            return results
        
        mol_id = molecules[0]["id"]
        updated = client.update(
            "molecules",
            data={"name": f"updated_{int(time.time())}"},
            filters={"id": mol_id}
        )
        
        if updated:
            results.add_pass(
                "Update molecule",
                f"Updated {len(updated)} rows"
            )
        else:
            results.add_fail("Update molecule", "No rows updated")
    
    except Exception as e:
        results.add_fail("Update operations", str(e))
    
    return results


def test_query_operations():
    """Test advanced query operations (filters, ordering)"""
    results = TestResults()
    
    try:
        client = get_supabase_client()
        
        # Query with filters
        try:
            rows = client.get(
                "calculations",
                select="id,energy,gap",
                limit=5,
                order_by="created_at.desc"
            )
            results.add_pass(
                "Query with ordering",
                f"Fetched {len(rows)} calculations"
            )
        except Exception as e:
            results.add_fail("Query with ordering", str(e))
        
        # Query event logs
        try:
            logs = client.get(
                "event_logs",
                select="id,event_type,status",
                limit=10,
                order_by="created_at.desc"
            )
            results.add_pass(
                "Query event logs",
                f"Fetched {len(logs)} events"
            )
        except Exception as e:
            results.add_fail("Query event logs", str(e))
    
    except Exception as e:
        results.add_fail("Query setup", str(e))
    
    return results


def main():
    """Run all tests"""
    logger.info("=" * 80)
    logger.info("QUANTUM FORGE SUPABASE REST API TEST SUITE")
    logger.info("=" * 80)
    logger.info("")
    
    all_results = []
    
    # Run test suites
    all_results.append(("Configuration", test_config()))
    all_results.append(("Connection", test_connection()))
    all_results.append(("Read Operations", test_read_operations()))
    all_results.append(("Write Operations", test_write_operations()))
    all_results.append(("Update Operations", test_update_operations()))
    all_results.append(("Query Operations", test_query_operations()))
    
    # Print overall summary
    logger.info("\n" + "=" * 80)
    logger.info("OVERALL TEST SUMMARY")
    logger.info("=" * 80)
    
    total_passed = 0
    total_failed = 0
    
    for suite_name, results in all_results:
        passed = len(results.passed)
        failed = len(results.failed)
        total_passed += passed
        total_failed += failed
        
        status = "✓" if failed == 0 else "✗"
        logger.info(f"{status} {suite_name}: {passed} passed, {failed} failed")
    
    logger.info("")
    logger.info(f"Total: {total_passed} passed, {total_failed} failed")
    logger.info("=" * 80)
    
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
