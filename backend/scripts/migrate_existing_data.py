#!/usr/bin/env python3
"""
Migrate Existing Data to Supabase Database

Ingests existing xTB calculation results from the filesystem into the Supabase
database. Supports:
- Reading job results from /workspace/jobs directory structure
- Parsing metadata and calculation results
- Verifying data integrity
- Logging all operations
- Rollback capability (transaction-based)

Usage:
    python backend/scripts/migrate_existing_data.py

Environment:
    - DATABASE_URL or DB_* env vars must be set
    - Existing job files must be in /workspace/jobs/*/
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import hashlib
import argparse

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.db.database import setup_database, get_db_context, check_db_health
from backend.app.db import crud
from backend.app.db.schemas import (
    MoleculeCreate, CalculationCreate
)
from backend.app.utils import logger as db_logger
from backend.app.config import validate_database_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/workspace/logs/migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MigrationStats:
    """Track migration statistics"""
    def __init__(self):
        self.molecules_created = 0
        self.molecules_skipped = 0
        self.calculations_created = 0
        self.calculations_skipped = 0
        self.atomic_properties_created = 0
        self.errors: List[Dict[str, Any]] = []
        self.start_time = datetime.utcnow()
    
    def duration_seconds(self) -> float:
        """Calculate migration duration"""
        return (datetime.utcnow() - self.start_time).total_seconds()
    
    def __repr__(self) -> str:
        return (
            f"Migration Stats:\n"
            f"  Molecules created: {self.molecules_created}\n"
            f"  Molecules skipped: {self.molecules_skipped}\n"
            f"  Calculations created: {self.calculations_created}\n"
            f"  Calculations skipped: {self.calculations_skipped}\n"
            f"  Atomic properties: {self.atomic_properties_created}\n"
            f"  Errors: {len(self.errors)}\n"
            f"  Duration: {self.duration_seconds():.1f}s"
        )


def find_job_directories(jobs_root: Path = Path("/workspace/jobs")) -> List[Path]:
    """
    Discover all job directories.
    
    Job directories should match pattern: jobs_root/water_*/
    
    Args:
        jobs_root: Root directory containing jobs
    
    Returns:
        List of job directory paths
    """
    if not jobs_root.exists():
        logger.warning(f"Jobs root directory not found: {jobs_root}")
        return []
    
    job_dirs = [d for d in jobs_root.iterdir() if d.is_dir()]
    logger.info(f"Found {len(job_dirs)} job directories in {jobs_root}")
    
    return sorted(job_dirs)


def load_job_metadata(job_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Load metadata from a job directory.
    
    Looks for:
    - metadata.json: Job metadata
    - results.json: Calculation results
    
    Args:
        job_dir: Job directory path
    
    Returns:
        Combined metadata dict or None if missing
    """
    metadata_file = job_dir / "metadata.json"
    results_file = job_dir / "results.json"
    
    try:
        metadata = {}
        
        # Load metadata
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        
        # Load results
        if results_file.exists():
            with open(results_file, 'r') as f:
                results = json.load(f)
                metadata['calculation'] = results
        
        if not metadata:
            logger.warning(f"No metadata found in {job_dir}")
            return None
        
        return metadata
        
    except Exception as e:
        logger.error(f"Failed to load metadata from {job_dir}: {e}")
        return None


def calculate_xyz_hash(xyz_file: Path) -> Optional[str]:
    """Calculate SHA256 hash of XYZ file"""
    try:
        if not xyz_file.exists():
            return None
        
        with open(xyz_file, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception as e:
        logger.error(f"Failed to hash XYZ file {xyz_file}: {e}")
        return None


def extract_molecule_info(job_dir: Path, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract molecule information from job metadata.
    
    Args:
        job_dir: Job directory
        metadata: Job metadata
    
    Returns:
        Dict with name, smiles, formula or None if can't extract
    """
    try:
        # Try to get molecule info from metadata
        mol_name = metadata.get('molecule_name') or job_dir.name
        mol_smiles = metadata.get('smiles')
        mol_formula = metadata.get('formula')
        
        # Fallback: parse from job directory name
        if not mol_smiles and 'water' in mol_name.lower():
            mol_smiles = 'O'
            mol_formula = 'H2O'
        elif not mol_smiles and 'methane' in mol_name.lower():
            mol_smiles = 'C'
            mol_formula = 'CH4'
        
        if not mol_smiles:
            logger.warning(f"Could not determine SMILES for {job_dir.name}")
            return None
        
        return {
            'name': mol_name,
            'smiles': mol_smiles,
            'formula': mol_formula or 'Unknown'
        }
        
    except Exception as e:
        logger.error(f"Failed to extract molecule info from {job_dir}: {e}")
        return None


def extract_calculation_info(metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract calculation results from metadata.
    
    Args:
        metadata: Job metadata
    
    Returns:
        Dict with energy, gap, dipole, etc. or None
    """
    try:
        calc_data = metadata.get('calculation', {})
        
        # Require at least energy
        if 'energy' not in calc_data:
            logger.warning(f"No energy found in calculation data")
            return None
        
        return {
            'energy': float(calc_data['energy']),
            'homo': float(calc_data.get('homo')) if calc_data.get('homo') else None,
            'lumo': float(calc_data.get('lumo')) if calc_data.get('lumo') else None,
            'gap': float(calc_data.get('gap')) if calc_data.get('gap') else None,
            'dipole': float(calc_data.get('dipole')) if calc_data.get('dipole') else None,
            'total_charge': float(calc_data.get('total_charge', 0.0)),
            'execution_time_seconds': float(calc_data.get('execution_time_seconds', 0.0)),
            'xtb_version': calc_data.get('xtb_version', '6.7.1'),
            'convergence_status': calc_data.get('convergence_status', 'converged'),
        }
        
    except Exception as e:
        logger.error(f"Failed to extract calculation info: {e}")
        return None


def migrate_job(
    db,
    job_dir: Path,
    stats: MigrationStats,
    user_id: Optional[str] = None
) -> Optional[Tuple[int, int]]:
    """
    Migrate a single job to database.
    
    Args:
        db: Database session
        job_dir: Job directory path
        stats: Migration statistics tracker
        user_id: User ID for data isolation
    
    Returns:
        Tuple of (molecule_id, calculation_id) or None if failed
    """
    try:
        # Load metadata
        metadata = load_job_metadata(job_dir)
        if not metadata:
            stats.errors.append({'job_dir': job_dir.name, 'error': 'No metadata'})
            return None
        
        # Extract molecule info
        mol_info = extract_molecule_info(job_dir, metadata)
        if not mol_info:
            stats.molecules_skipped += 1
            return None
        
        # Check if molecule already exists
        existing_mol = crud.get_molecule_by_smiles(db, mol_info['smiles'], user_id)
        if existing_mol:
            logger.info(f"Molecule {mol_info['name']} already exists (ID: {existing_mol.id})")
            molecule_id = existing_mol.id
            stats.molecules_skipped += 1
        else:
            # Create molecule
            mol_create = MoleculeCreate(**mol_info, metadata={'migrated_from': job_dir.name})
            molecule = crud.create_molecule(db, mol_create, user_id)
            molecule_id = molecule.id
            stats.molecules_created += 1
            
            logger.info(f"Created molecule {molecule_id}: {mol_info['name']}")
        
        # Extract calculation info
        calc_info = extract_calculation_info(metadata)
        if not calc_info:
            stats.calculations_skipped += 1
            return (molecule_id, None)
        
        # Add XYZ file hash if available
        xyz_file = job_dir / "structure.xyz"
        if xyz_file.exists():
            calc_info['xyz_file_hash'] = calculate_xyz_hash(xyz_file)
        
        # Add file paths
        output_json = job_dir / "xtbout.json"
        if output_json.exists():
            calc_info['output_json_path'] = str(output_json)
        
        calc_info['molecule_id'] = molecule_id
        
        # Create calculation
        calc_create = CalculationCreate(**calc_info)
        calculation = crud.create_calculation(db, calc_create, user_id)
        stats.calculations_created += 1
        
        logger.info(f"Created calculation {calculation.id}: energy={calc_info['energy']:.4f}")
        
        # Extract atomic properties if available
        atomic_data = metadata.get('atomic_properties', [])
        if atomic_data:
            crud.create_atomic_properties(db, calculation.id, atomic_data, user_id)
            stats.atomic_properties_created += len(atomic_data)
        
        return (molecule_id, calculation.id)
        
    except Exception as e:
        logger.error(f"Failed to migrate job {job_dir.name}: {e}")
        stats.errors.append({'job_dir': job_dir.name, 'error': str(e)})
        return None


def run_migration(
    jobs_root: Path = Path("/workspace/jobs"),
    user_id: Optional[str] = None,
    dry_run: bool = False,
    limit: Optional[int] = None
) -> MigrationStats:
    """
    Run full migration from filesystem to database.
    
    Args:
        jobs_root: Root directory with job folders
        user_id: User ID for data isolation
        dry_run: If True, don't commit changes
        limit: Maximum jobs to process (for testing)
    
    Returns:
        MigrationStats object with results
    """
    stats = MigrationStats()
    
    # Validate database config
    is_valid, message = validate_database_config()
    if not is_valid:
        logger.error(f"Database configuration invalid: {message}")
        stats.errors.append({'error': message})
        return stats
    
    try:
        # Setup database
        logger.info("Setting up database connection...")
        engine, SessionLocal = setup_database()
        
        # Check database health
        health = check_db_health(engine)
        logger.info(f"Database health: {health['status']}")
        if health['status'] != 'healthy':
            logger.error(f"Database is unhealthy: {health['message']}")
            stats.errors.append(health)
            return stats
        
        # Find job directories
        job_dirs = find_job_directories(jobs_root)
        if not job_dirs:
            logger.warning("No job directories found!")
            return stats
        
        if limit:
            job_dirs = job_dirs[:limit]
            logger.info(f"Limiting to first {limit} jobs")
        
        # Migrate each job
        logger.info(f"Starting migration of {len(job_dirs)} jobs...")
        
        with get_db_context() as db:
            for i, job_dir in enumerate(job_dirs, 1):
                logger.info(f"[{i}/{len(job_dirs)}] Migrating {job_dir.name}...")
                
                result = migrate_job(db, job_dir, stats, user_id)
                
                # Log event
                if result and result[1]:  # If calculation created
                    mol_id, calc_id = result
                    db_logger.log_calculation_completed(
                        db=db,
                        calculation_id=calc_id,
                        molecule_id=mol_id,
                        energy=0.0,  # We'd need to fetch from DB
                        user_id=user_id,
                        context={'migration': True, 'job_dir': job_dir.name}
                    )
            
            # Commit or rollback
            if dry_run:
                logger.info("DRY RUN: Rolling back all changes")
                db.rollback()
            else:
                logger.info("Committing migration...")
                db.commit()
        
        logger.info(f"Migration completed: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        stats.errors.append({'error': str(e)})
        return stats


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Migrate existing xTB job results to Supabase database'
    )
    parser.add_argument(
        '--jobs-root',
        type=Path,
        default=Path('/workspace/jobs'),
        help='Root directory containing job folders'
    )
    parser.add_argument(
        '--user-id',
        type=str,
        default=None,
        help='User ID for data isolation (UUID format)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be migrated without committing'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of jobs to process'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info("Quantum Forge Database Migration")
    logger.info("=" * 80)
    
    stats = run_migration(
        jobs_root=args.jobs_root,
        user_id=args.user_id,
        dry_run=args.dry_run,
        limit=args.limit
    )
    
    logger.info("=" * 80)
    logger.info(stats)
    logger.info("=" * 80)
    
    # Exit with error if there were critical failures
    if stats.errors:
        logger.warning(f"Migration completed with {len(stats.errors)} errors")
        for error in stats.errors:
            logger.warning(f"  - {error}")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
