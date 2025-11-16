"""
Structured Database Logging Framework

Provides high-level logging functions that write to the event_logs table.
All major operations (calculations, batches, errors) are logged with:
- Structured data (JSON metadata)
- Full context for debugging and ML analysis
- Automatic timestamps
- No SQL injection vulnerabilities (using SQLAlchemy ORM)

Usage:
    from backend.app.utils.logger import log_calculation_started
    
    log_calculation_started(
        calculation_id=123,
        molecule_id=45,
        xtb_version="6.7.1",
        method="GFN2-xTB",
        db=session
    )
"""

import logging
import time
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from backend.app.db import crud

logger = logging.getLogger(__name__)


# ============================================================================
# CALCULATION EVENT LOGGING
# ============================================================================

def log_calculation_started(
    db: Session,
    calculation_id: int,
    molecule_id: int,
    xtb_version: Optional[str] = None,
    method: str = "GFN2-xTB",
    solvation: Optional[str] = None,
    user_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log when a calculation starts executing.
    
    Args:
        db: Database session
        calculation_id: ID of calculation
        molecule_id: ID of molecule
        xtb_version: xTB version (e.g., "6.7.1")
        method: Calculation method (e.g., "GFN2-xTB")
        solvation: Solvent model if used
        user_id: User ID for audit trail
        context: Additional context (input parameters, etc.)
    """
    ctx = context or {}
    ctx.update({
        "xtb_version": xtb_version,
        "method": method,
        "solvation": solvation,
        "timestamp": time.time()
    })
    
    crud.log_event(
        db=db,
        event_type="calculation_started",
        entity_type="calculations",
        entity_id=calculation_id,
        status="success",
        context=ctx,
        user_id=user_id,
        service="xTB_runner"
    )
    
    logger.info(f"Calculation {calculation_id} started (molecule {molecule_id})")


def log_calculation_completed(
    db: Session,
    calculation_id: int,
    molecule_id: int,
    energy: float,
    gap: Optional[float] = None,
    dipole: Optional[float] = None,
    execution_time_seconds: float = 0,
    xtb_version: Optional[str] = None,
    user_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log when a calculation completes successfully.
    
    Args:
        db: Database session
        calculation_id: ID of calculation
        molecule_id: ID of molecule
        energy: Total energy in Hartree
        gap: HOMO-LUMO gap in eV
        dipole: Dipole moment in Debye
        execution_time_seconds: How long it took
        xtb_version: xTB version used
        user_id: User ID
        context: Additional context
    """
    ctx = context or {}
    ctx.update({
        "energy": float(energy),
        "gap": float(gap) if gap else None,
        "dipole": float(dipole) if dipole else None,
        "execution_time_seconds": float(execution_time_seconds),
        "xtb_version": xtb_version,
        "timestamp": time.time()
    })
    
    crud.log_event(
        db=db,
        event_type="calculation_completed",
        entity_type="calculations",
        entity_id=calculation_id,
        status="success",
        context=ctx,
        user_id=user_id,
        service="xTB_runner"
    )
    
    logger.info(f"Calculation {calculation_id} completed: energy={energy:.4f}, gap={gap}")


def log_calculation_failed(
    db: Session,
    calculation_id: int,
    molecule_id: int,
    error_message: str,
    error_code: Optional[str] = None,
    xtb_stderr: Optional[str] = None,
    user_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log when a calculation fails.
    
    Args:
        db: Database session
        calculation_id: ID of calculation
        molecule_id: ID of molecule
        error_message: Human-readable error description
        error_code: Machine-readable error code (e.g., "XTB_CRASH")
        xtb_stderr: Full stderr output from xTB
        user_id: User ID
        context: Additional context
    """
    ctx = context or {}
    ctx.update({
        "error_message": error_message,
        "error_code": error_code,
        "xtb_stderr": xtb_stderr[:500] if xtb_stderr else None,  # Truncate for storage
        "timestamp": time.time()
    })
    
    crud.log_event(
        db=db,
        event_type="calculation_failed",
        entity_type="calculations",
        entity_id=calculation_id,
        status="error",
        error_message=error_message,
        error_code=error_code,
        context=ctx,
        user_id=user_id,
        service="xTB_runner"
    )
    
    logger.error(f"Calculation {calculation_id} failed: {error_code} - {error_message}")


# ============================================================================
# BATCH EVENT LOGGING
# ============================================================================

def log_batch_started(
    db: Session,
    batch_id: int,
    batch_name: str,
    molecule_count: int,
    user_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log when batch processing begins.
    
    Args:
        db: Database session
        batch_id: ID of batch job
        batch_name: Human-readable name
        molecule_count: Total molecules in batch
        user_id: User ID
        context: Additional context (parameters, etc.)
    """
    ctx = context or {}
    ctx.update({
        "batch_name": batch_name,
        "molecule_count": molecule_count,
        "timestamp": time.time()
    })
    
    crud.log_event(
        db=db,
        event_type="batch_started",
        entity_type="batch_jobs",
        entity_id=batch_id,
        status="success",
        context=ctx,
        user_id=user_id,
        service="api"
    )
    
    logger.info(f"Batch {batch_id} ({batch_name}) started with {molecule_count} molecules")


def log_batch_completed(
    db: Session,
    batch_id: int,
    batch_name: str,
    total_molecules: int,
    successful_count: int,
    failed_count: int,
    execution_time_seconds: float = 0,
    user_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log when batch processing completes.
    
    Args:
        db: Database session
        batch_id: ID of batch job
        batch_name: Human-readable name
        total_molecules: Total molecules processed
        successful_count: How many succeeded
        failed_count: How many failed
        execution_time_seconds: Total runtime
        user_id: User ID
        context: Additional context
    """
    success_rate = (successful_count / total_molecules * 100) if total_molecules > 0 else 0
    
    ctx = context or {}
    ctx.update({
        "batch_name": batch_name,
        "total_molecules": total_molecules,
        "successful_count": successful_count,
        "failed_count": failed_count,
        "success_rate": float(success_rate),
        "execution_time_seconds": float(execution_time_seconds),
        "timestamp": time.time()
    })
    
    crud.log_event(
        db=db,
        event_type="batch_completed",
        entity_type="batch_jobs",
        entity_id=batch_id,
        status="success",
        context=ctx,
        user_id=user_id,
        service="api"
    )
    
    logger.info(
        f"Batch {batch_id} ({batch_name}) completed: "
        f"{successful_count}/{total_molecules} successful ({success_rate:.1f}%), "
        f"{failed_count} failed, {execution_time_seconds:.1f}s"
    )


def log_batch_failed(
    db: Session,
    batch_id: int,
    batch_name: str,
    error_message: str,
    processed_count: int,
    total_molecules: int,
    user_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log when batch processing fails.
    
    Args:
        db: Database session
        batch_id: ID of batch job
        batch_name: Human-readable name
        error_message: What went wrong
        processed_count: How many completed before failure
        total_molecules: Total molecules in batch
        user_id: User ID
        context: Additional context
    """
    ctx = context or {}
    ctx.update({
        "batch_name": batch_name,
        "processed_count": processed_count,
        "total_molecules": total_molecules,
        "error_message": error_message,
        "timestamp": time.time()
    })
    
    crud.log_event(
        db=db,
        event_type="batch_failed",
        entity_type="batch_jobs",
        entity_id=batch_id,
        status="error",
        error_message=error_message,
        context=ctx,
        user_id=user_id,
        service="api"
    )
    
    logger.error(f"Batch {batch_id} ({batch_name}) failed: {error_message} ({processed_count}/{total_molecules})")


# ============================================================================
# MOLECULE EVENT LOGGING
# ============================================================================

def log_molecule_created(
    db: Session,
    molecule_id: int,
    name: str,
    smiles: str,
    user_id: Optional[str] = None
) -> None:
    """Log when molecule is created"""
    ctx = {
        "name": name,
        "smiles": smiles,
        "timestamp": time.time()
    }
    
    crud.log_event(
        db=db,
        event_type="molecule_created",
        entity_type="molecules",
        entity_id=molecule_id,
        status="success",
        context=ctx,
        user_id=user_id,
        service="api"
    )
    
    logger.info(f"Molecule {molecule_id} created: {name} ({smiles})")


def log_molecule_deleted(
    db: Session,
    molecule_id: int,
    name: str,
    user_id: Optional[str] = None
) -> None:
    """Log when molecule is deleted"""
    ctx = {
        "name": name,
        "timestamp": time.time()
    }
    
    crud.log_event(
        db=db,
        event_type="molecule_deleted",
        entity_type="molecules",
        entity_id=molecule_id,
        status="success",
        context=ctx,
        user_id=user_id,
        service="api"
    )
    
    logger.info(f"Molecule {molecule_id} deleted: {name}")


# ============================================================================
# ERROR LOGGING
# ============================================================================

def log_error(
    db: Session,
    error_message: str,
    error_code: str,
    entity_type: str,
    entity_id: Optional[int] = None,
    error_details: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    service: str = "api"
) -> None:
    """
    Log a general error to the audit trail.
    
    Args:
        db: Database session
        error_message: Human-readable error
        error_code: Machine code (e.g., "DB_CONSTRAINT")
        entity_type: What entity caused error
        entity_id: Which specific entity
        error_details: Detailed error info
        user_id: User ID
        service: Service that generated error
    """
    ctx = error_details or {}
    ctx.update({
        "error_message": error_message,
        "error_code": error_code,
        "timestamp": time.time()
    })
    
    crud.log_event(
        db=db,
        event_type="error",
        entity_type=entity_type,
        entity_id=entity_id,
        status="error",
        error_message=error_message,
        error_code=error_code,
        context=ctx,
        user_id=user_id,
        service=service
    )
    
    logger.error(f"Error {error_code}: {error_message} ({entity_type}:{entity_id})")


# ============================================================================
# PERFORMANCE MONITORING
# ============================================================================

def log_performance_metric(
    db: Session,
    metric_name: str,
    value: float,
    unit: str,
    context: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None
) -> None:
    """
    Log performance metrics for monitoring and analysis.
    
    Args:
        db: Database session
        metric_name: Name of metric (e.g., "query_time")
        value: Numeric value
        unit: Unit of measurement (e.g., "seconds")
        context: Additional context
        user_id: User ID
    """
    ctx = context or {}
    ctx.update({
        "metric_name": metric_name,
        "value": float(value),
        "unit": unit,
        "timestamp": time.time()
    })
    
    crud.log_event(
        db=db,
        event_type="performance_metric",
        entity_type="system",
        status="success",
        context=ctx,
        user_id=user_id,
        service="api"
    )
    
    logger.debug(f"Performance: {metric_name} = {value} {unit}")
