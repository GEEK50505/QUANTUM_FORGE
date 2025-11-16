"""
CRUD Operations for Database Entities

Provides high-level functions for Create, Read, Update, Delete operations
on all database entities. All operations:
- Use SQLAlchemy ORM (no raw SQL)
- Include error handling with meaningful messages
- Log important events to event_logs table
- Support pagination for large datasets
- Are optimized for performance (proper indexes)
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from backend.app.db.models import (
    Molecule, Calculation, AtomicProperty, BatchJob, BatchItem, EventLog
)
from backend.app.db.schemas import (
    MoleculeCreate, MoleculeUpdate, CalculationCreate, AtomicPropertyCreate,
    BatchJobCreate, BatchItemCreate, EventLogCreate
)

logger = logging.getLogger(__name__)


# ============================================================================
# MOLECULE CRUD
# ============================================================================

def create_molecule(db: Session, molecule: MoleculeCreate, user_id: Optional[str] = None) -> Molecule:
    """
    Create a new molecule.
    
    Args:
        db: Database session
        molecule: Molecule data
        user_id: User ID for multi-tenant isolation
    
    Returns:
        Created Molecule object
    
    Raises:
        ValueError: If SMILES already exists
    """
    try:
        # Check for duplicate SMILES
        existing = db.query(Molecule).filter(Molecule.smiles == molecule.smiles).first()
        if existing:
            logger.warning(f"Attempt to create duplicate molecule: {molecule.smiles}")
            raise ValueError(f"Molecule with SMILES '{molecule.smiles}' already exists")
        
        db_molecule = Molecule(
            user_id=user_id,
            name=molecule.name,
            smiles=molecule.smiles,
            formula=molecule.formula,
            metadata=molecule.metadata or {}
        )
        
        db.add(db_molecule)
        db.commit()
        db.refresh(db_molecule)
        
        logger.info(f"Created molecule: {db_molecule.id} - {molecule.name}")
        return db_molecule
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create molecule: {e}")
        raise


def get_molecule(db: Session, molecule_id: int, user_id: Optional[str] = None) -> Optional[Molecule]:
    """Get molecule by ID with optional user filter"""
    query = db.query(Molecule).filter(Molecule.id == molecule_id)
    if user_id:
        query = query.filter(Molecule.user_id == user_id)
    return query.first()


def get_molecule_by_smiles(db: Session, smiles: str, user_id: Optional[str] = None) -> Optional[Molecule]:
    """Get molecule by SMILES notation"""
    query = db.query(Molecule).filter(Molecule.smiles == smiles)
    if user_id:
        query = query.filter(Molecule.user_id == user_id)
    return query.first()


def list_molecules(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[str] = None
) -> tuple[List[Molecule], int]:
    """
    List molecules with pagination.
    
    Returns:
        Tuple of (molecules, total_count)
    """
    query = db.query(Molecule)
    if user_id:
        query = query.filter(Molecule.user_id == user_id)
    
    total = query.count()
    molecules = query.order_by(desc(Molecule.created_at)).offset(skip).limit(limit).all()
    
    return molecules, total


def update_molecule(
    db: Session,
    molecule_id: int,
    update_data: MoleculeUpdate,
    user_id: Optional[str] = None
) -> Optional[Molecule]:
    """Update molecule fields"""
    molecule = get_molecule(db, molecule_id, user_id)
    if not molecule:
        return None
    
    try:
        update_dict = update_data.dict(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(molecule, key, value)
        
        molecule.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(molecule)
        
        logger.info(f"Updated molecule: {molecule_id}")
        return molecule
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update molecule: {e}")
        raise


def delete_molecule(db: Session, molecule_id: int, user_id: Optional[str] = None) -> bool:
    """Delete molecule and cascade delete calculations/properties"""
    molecule = get_molecule(db, molecule_id, user_id)
    if not molecule:
        return False
    
    try:
        db.delete(molecule)
        db.commit()
        logger.info(f"Deleted molecule: {molecule_id}")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete molecule: {e}")
        raise


# ============================================================================
# CALCULATION CRUD
# ============================================================================

def create_calculation(
    db: Session,
    calc: CalculationCreate,
    user_id: Optional[str] = None
) -> Calculation:
    """Create a new calculation result"""
    try:
        db_calc = Calculation(
            user_id=user_id,
            molecule_id=calc.molecule_id,
            energy=calc.energy,
            homo=calc.homo,
            lumo=calc.lumo,
            gap=calc.gap,
            dipole=calc.dipole,
            total_charge=calc.total_charge,
            execution_time_seconds=calc.execution_time_seconds,
            xtb_version=calc.xtb_version,
            solvation=calc.solvation,
            method=calc.method,
            convergence_status=calc.convergence_status,
            metadata=calc.metadata or {}
        )
        
        db.add(db_calc)
        db.commit()
        db.refresh(db_calc)
        
        logger.info(f"Created calculation: {db_calc.id} for molecule {calc.molecule_id}")
        return db_calc
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create calculation: {e}")
        raise


def get_calculation(db: Session, calc_id: int, user_id: Optional[str] = None) -> Optional[Calculation]:
    """Get calculation by ID"""
    query = db.query(Calculation).filter(Calculation.id == calc_id)
    if user_id:
        query = query.filter(Calculation.user_id == user_id)
    return query.first()


def list_calculations(
    db: Session,
    molecule_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[str] = None
) -> tuple[List[Calculation], int]:
    """List calculations with optional filtering"""
    query = db.query(Calculation)
    
    if user_id:
        query = query.filter(Calculation.user_id == user_id)
    if molecule_id:
        query = query.filter(Calculation.molecule_id == molecule_id)
    
    total = query.count()
    calcs = query.order_by(desc(Calculation.created_at)).offset(skip).limit(limit).all()
    
    return calcs, total


def get_calculations_by_energy_range(
    db: Session,
    min_energy: float,
    max_energy: float,
    user_id: Optional[str] = None,
    limit: int = 1000
) -> List[Calculation]:
    """Query calculations within energy range (ML feature queries)"""
    query = db.query(Calculation).filter(
        and_(
            Calculation.energy >= min_energy,
            Calculation.energy <= max_energy
        )
    )
    if user_id:
        query = query.filter(Calculation.user_id == user_id)
    
    return query.limit(limit).all()


def get_calculations_by_gap_range(
    db: Session,
    min_gap: float,
    max_gap: float,
    user_id: Optional[str] = None,
    limit: int = 1000
) -> List[Calculation]:
    """Query calculations by HOMO-LUMO gap range"""
    query = db.query(Calculation).filter(
        and_(
            Calculation.gap >= min_gap,
            Calculation.gap <= max_gap
        )
    )
    if user_id:
        query = query.filter(Calculation.user_id == user_id)
    
    return query.limit(limit).all()


# ============================================================================
# ATOMIC PROPERTY CRUD
# ============================================================================

def create_atomic_properties(
    db: Session,
    calc_id: int,
    properties_list: List[Dict[str, Any]],
    user_id: Optional[str] = None
) -> List[AtomicProperty]:
    """
    Create multiple atomic properties for a calculation.
    
    Args:
        db: Database session
        calc_id: Calculation ID
        properties_list: List of atom property dicts
        user_id: User ID
    
    Returns:
        List of created AtomicProperty objects
    """
    try:
        props = []
        for prop_data in properties_list:
            prop = AtomicProperty(
                user_id=user_id,
                calculation_id=calc_id,
                atom_index=prop_data["atom_index"],
                element=prop_data["element"],
                atomic_number=prop_data["atomic_number"],
                partial_charge=prop_data.get("partial_charge"),
                position_x=prop_data["position_x"],
                position_y=prop_data["position_y"],
                position_z=prop_data["position_z"],
                force_x=prop_data.get("force_x"),
                force_y=prop_data.get("force_y"),
                force_z=prop_data.get("force_z"),
                orbital_energy=prop_data.get("orbital_energy"),
                metadata=prop_data.get("metadata", {})
            )
            props.append(prop)
        
        db.add_all(props)
        db.commit()
        
        logger.info(f"Created {len(props)} atomic properties for calculation {calc_id}")
        return props
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create atomic properties: {e}")
        raise


def get_atomic_properties_for_calculation(
    db: Session,
    calc_id: int,
    user_id: Optional[str] = None
) -> List[AtomicProperty]:
    """Get all atomic properties for a calculation"""
    query = db.query(AtomicProperty).filter(AtomicProperty.calculation_id == calc_id)
    if user_id:
        query = query.filter(AtomicProperty.user_id == user_id)
    
    return query.order_by(AtomicProperty.atom_index).all()


# ============================================================================
# BATCH JOB CRUD
# ============================================================================

def create_batch_job(
    db: Session,
    batch: BatchJobCreate,
    user_id: Optional[str] = None
) -> BatchJob:
    """Create a new batch job"""
    try:
        db_batch = BatchJob(
            user_id=user_id,
            batch_name=batch.batch_name,
            description=batch.description,
            total_molecules=batch.total_molecules or 0,
            parameters=batch.parameters or {},
            status="pending"
        )
        
        db.add(db_batch)
        db.commit()
        db.refresh(db_batch)
        
        logger.info(f"Created batch job: {db_batch.id} - {batch.batch_name}")
        return db_batch
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create batch job: {e}")
        raise


def get_batch_job(db: Session, batch_id: int, user_id: Optional[str] = None) -> Optional[BatchJob]:
    """Get batch job by ID"""
    query = db.query(BatchJob).filter(BatchJob.id == batch_id)
    if user_id:
        query = query.filter(BatchJob.user_id == user_id)
    return query.first()


def list_batch_jobs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    user_id: Optional[str] = None
) -> tuple[List[BatchJob], int]:
    """List batch jobs with pagination and optional status filter"""
    query = db.query(BatchJob)
    
    if user_id:
        query = query.filter(BatchJob.user_id == user_id)
    if status:
        query = query.filter(BatchJob.status == status)
    
    total = query.count()
    batches = query.order_by(desc(BatchJob.created_at)).offset(skip).limit(limit).all()
    
    return batches, total


def update_batch_job_status(
    db: Session,
    batch_id: int,
    status: str,
    user_id: Optional[str] = None
) -> Optional[BatchJob]:
    """Update batch job status"""
    batch = get_batch_job(db, batch_id, user_id)
    if not batch:
        return None
    
    try:
        batch.status = status
        if status == "in_progress" and not batch.started_at:
            batch.started_at = datetime.utcnow()
        elif status == "completed":
            batch.completed_at = datetime.utcnow()
        
        batch.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(batch)
        
        return batch
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update batch status: {e}")
        raise


# ============================================================================
# BATCH ITEM CRUD
# ============================================================================

def create_batch_item(
    db: Session,
    item: BatchItemCreate,
    user_id: Optional[str] = None
) -> BatchItem:
    """Create a batch item (link molecule to batch)"""
    try:
        db_item = BatchItem(
            user_id=user_id,
            batch_id=item.batch_id,
            molecule_id=item.molecule_id,
            status=item.status or "pending"
        )
        
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        
        # Update batch molecule count
        batch = get_batch_job(db, item.batch_id, user_id)
        if batch:
            batch.total_molecules = db.query(BatchItem).filter(
                BatchItem.batch_id == item.batch_id
            ).count()
            db.commit()
        
        return db_item
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create batch item: {e}")
        raise


def get_batch_items(
    db: Session,
    batch_id: int,
    status: Optional[str] = None,
    user_id: Optional[str] = None
) -> List[BatchItem]:
    """Get all items in a batch"""
    query = db.query(BatchItem).filter(BatchItem.batch_id == batch_id)
    
    if user_id:
        query = query.filter(BatchItem.user_id == user_id)
    if status:
        query = query.filter(BatchItem.status == status)
    
    return query.all()


def update_batch_item_status(
    db: Session,
    item_id: int,
    status: str,
    calculation_id: Optional[int] = None,
    error_message: Optional[str] = None,
    user_id: Optional[str] = None
) -> Optional[BatchItem]:
    """Update batch item status and optionally link calculation"""
    query = db.query(BatchItem).filter(BatchItem.id == item_id)
    if user_id:
        query = query.filter(BatchItem.user_id == user_id)
    
    item = query.first()
    if not item:
        return None
    
    try:
        item.status = status
        if calculation_id:
            item.calculation_id = calculation_id
        if error_message:
            item.error_message = error_message
        if status == "processing" and not item.started_at:
            item.started_at = datetime.utcnow()
        elif status in ["completed", "failed"] and not item.completed_at:
            item.completed_at = datetime.utcnow()
        
        item.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(item)
        
        return item
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update batch item: {e}")
        raise


# ============================================================================
# EVENT LOG CRUD
# ============================================================================

def log_event(
    db: Session,
    event_type: str,
    entity_type: str,
    entity_id: Optional[int] = None,
    status: str = "success",
    error_message: Optional[str] = None,
    error_code: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    service: str = "api"
) -> EventLog:
    """
    Log an event to the event_logs table.
    
    All database operations should log important events for:
    - Debugging and troubleshooting
    - Compliance and audit trails
    - Monitoring and alerting
    - Performance analysis
    
    Args:
        db: Database session
        event_type: What happened (calculation_started, batch_completed, etc.)
        entity_type: What entity (calculations, batches, molecules)
        entity_id: Which specific record
        status: success, warning, error
        error_message: Details if error
        error_code: Error code for programmatic handling
        context: Full context as JSON (xTB version, timing, etc.)
        user_id: User ID
        service: Which service generated log
    
    Returns:
        Created EventLog
    """
    try:
        log_entry = EventLog(
            user_id=user_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            status=status,
            error_message=error_message,
            error_code=error_code,
            context=context or {},
            service=service
        )
        
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        
        if status == "error":
            logger.error(f"Event log: {event_type} - {error_message}")
        else:
            logger.debug(f"Event log: {event_type} for {entity_type}:{entity_id}")
        
        return log_entry
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create event log: {e}")
        # Don't raise - logging shouldn't break main operations
        return None


def get_event_logs(
    db: Session,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[str] = None
) -> tuple[List[EventLog], int]:
    """Get event logs with filtering"""
    query = db.query(EventLog)
    
    if user_id:
        query = query.filter(EventLog.user_id == user_id)
    if entity_type:
        query = query.filter(EventLog.entity_type == entity_type)
    if entity_id:
        query = query.filter(EventLog.entity_id == entity_id)
    if status:
        query = query.filter(EventLog.status == status)
    
    total = query.count()
    logs = query.order_by(desc(EventLog.created_at)).offset(skip).limit(limit).all()
    
    return logs, total


# ============================================================================
# STATISTICS & ANALYSIS
# ============================================================================

def get_database_stats(db: Session, user_id: Optional[str] = None) -> Dict[str, Any]:
    """Get overall database statistics for dashboard"""
    
    # Build base queries
    molecules_query = db.query(Molecule)
    calcs_query = db.query(Calculation)
    batches_query = db.query(BatchJob)
    
    if user_id:
        molecules_query = molecules_query.filter(Molecule.user_id == user_id)
        calcs_query = calcs_query.filter(Calculation.user_id == user_id)
        batches_query = batches_query.filter(BatchJob.user_id == user_id)
    
    total_molecules = molecules_query.count()
    total_calcs = calcs_query.count()
    total_batches = batches_query.count()
    
    # Energy statistics
    avg_energy = db.query(func.avg(Calculation.energy)).filter(Calculation.user_id == user_id if user_id else True).scalar()
    
    # Gap statistics
    median_gap = db.query(Calculation.gap).filter(
        Calculation.gap.isnot(None),
        Calculation.user_id == user_id if user_id else True
    ).all()
    median_gap = sorted([g[0] for g in median_gap])[len(median_gap)//2] if median_gap else None
    
    # Success rate
    successful = db.query(func.count(Calculation.id)).filter(
        Calculation.convergence_status == "converged",
        Calculation.user_id == user_id if user_id else True
    ).scalar() or 0
    success_rate = (successful / total_calcs * 100) if total_calcs > 0 else 0
    
    # Latest calculation
    latest_calc = calcs_query.order_by(desc(Calculation.created_at)).first()
    latest_at = latest_calc.created_at if latest_calc else None
    
    return {
        "total_molecules": total_molecules,
        "total_calculations": total_calcs,
        "total_batches": total_batches,
        "average_energy": float(avg_energy) if avg_energy else None,
        "median_gap": float(median_gap) if median_gap else None,
        "success_rate": float(success_rate),
        "latest_calculation_at": latest_at
    }
