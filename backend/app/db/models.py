"""
SQLAlchemy ORM Models for Quantum Forge Database

This module defines all database models using SQLAlchemy with comprehensive
docstrings for future AI/ML analysis and researcher understanding.

Models support:
- User-based data isolation via user_id foreign key
- JSON metadata for extensibility
- Automatic timestamps
- Comprehensive relationships for ML feature engineering
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey,
    JSON, Index, UniqueConstraint, CheckConstraint, Sequence, BigInteger,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

Base = declarative_base()


class Molecule(Base):
    """
    Represents a unique molecular structure in the database.
    
    This table stores molecular structures to enable:
    - De-duplication: Same molecule across multiple batches uses one record
    - Structure searching: Query by SMILES notation
    - ML feature extraction: Chemistry researchers can analyze structure patterns
    
    Attributes:
        id: Unique identifier (primary key)
        user_id: For future multi-user isolation (GDPR compliance)
        name: Human-readable name (e.g., "water", "aspirin")
        smiles: SMILES notation (unique chemical identifier)
        formula: Chemical formula (e.g., "H2O", "C8H10N4O2")
        created_at: When molecule was added to database
        updated_at: Last modification timestamp
        mol_metadata: JSON field for extensibility (molecular_weight, logP, etc.)
        
        Relationships:
        - calculations: One molecule → many calculations
        - batch_items: One molecule → many batch associations
    """
    __tablename__ = "molecules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # For future auth
    
    name = Column(String(255), nullable=False)
    smiles = Column(Text, unique=True, nullable=False, index=True)
    formula = Column(String(255), nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    mol_metadata = Column(JSONB, default={})
    
    # Relationships
    calculations = relationship("Calculation", back_populates="molecule", cascade="all, delete-orphan")
    batch_items = relationship("BatchItem", back_populates="molecule", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("LENGTH(TRIM(smiles)) > 0", name="smiles_not_empty"),
        CheckConstraint("LENGTH(TRIM(name)) > 0", name="name_not_empty"),
        Index("idx_molecules_user_id", "user_id"),
        Index("idx_molecules_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<Molecule(id={self.id}, name={self.name}, smiles={self.smiles[:30]})>"


class Calculation(Base):
    """
    Represents a single xTB quantum chemistry calculation result.
    
    This is the PRIMARY table for ML training data. Each calculation:
    - References one molecule (foreign key)
    - Contains full xTB output (energy, HOMO, LUMO, dipole, etc.)
    - Includes execution metadata and convergence info
    - Can have associated atomic-level properties
    
    Used for:
    - ML training: Primary dataset for property prediction models
    - Data analysis: Researchers query energy ranges, gaps, etc.
    - Debugging: Find failed calculations or outliers
    
    Attributes:
        energy: Total electronic energy (Hartree)
        homo/lumo: Orbital energies (for gap calculation)
        gap: HOMO-LUMO gap (eV) - key metric for electronics/photonics
        dipole: Dipole moment (Debye) - affects molecular properties
        execution_time_seconds: Computational cost tracking
        convergence_status: Did the calculation converge?
        
    Relationships:
        - molecule: One calculation belongs to one molecule
        - atomic_properties: One calculation has many atoms' properties
    """
    __tablename__ = "calculations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    molecule_id = Column(Integer, ForeignKey("molecules.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Core quantum chemistry outputs
    energy = Column(Float, nullable=False)  # Total energy (Hartree)
    homo = Column(Float, nullable=True)  # Highest occupied MO (eV)
    lumo = Column(Float, nullable=True)  # Lowest unoccupied MO (eV)
    gap = Column(Float, nullable=True)  # HOMO-LUMO gap (eV)
    dipole = Column(Float, nullable=True)  # Dipole moment (Debye)
    total_charge = Column(Float, default=0.0)  # Molecular charge (e)
    
    # Execution metadata
    execution_time_seconds = Column(Float, nullable=False)
    xtb_version = Column(String(50), nullable=True)  # e.g., "6.7.1"
    solvation = Column(String(50), nullable=True)  # e.g., "GBSA", "ALPB"
    method = Column(String(50), default="GFN2-xTB")  # Calculation method
    convergence_status = Column(String(50), default="converged")  # converged, not_converged, error
    
    # File references for reproducibility
    xyz_file_hash = Column(String(64), nullable=True)  # SHA256 of input XYZ
    output_json_path = Column(Text, nullable=True)  # Path to xtbout.json
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Extensible metadata
    calc_metadata = Column(JSONB, default={})  # Custom fields, notes, parameters
    
    # Relationships
    molecule = relationship("Molecule", back_populates="calculations")
    atomic_properties = relationship("AtomicProperty", back_populates="calculation", cascade="all, delete-orphan")
    
    # Indexes for ML queries
    __table_args__ = (
        Index("idx_calculations_user_id", "user_id"),
        Index("idx_calculations_molecule_id", "molecule_id"),
        Index("idx_calculations_created_at", "created_at"),
        Index("idx_calculations_energy", "energy"),  # Range queries on energy
        Index("idx_calculations_gap", "gap"),  # Filter by bandgap
        Index("idx_calculations_molecule_created", "molecule_id", "created_at"),  # Composite
    )

    def __repr__(self):
        return f"<Calculation(id={self.id}, mol_id={self.molecule_id}, energy={self.energy:.4f})>"


class AtomicProperty(Base):
    """
    Per-atom properties from xTB calculations.
    
    This table enables atom-level ML models:
    - Atomic charge prediction
    - Orbital energy models
    - Force field parameterization
    
    For each atom in each calculation, stores:
    - Position (x, y, z in Angstroms)
    - Partial charge (Mulliken, etc.)
    - Forces (Hartree/Bohr)
    - Orbital energy if available
    
    Attributes:
        calculation_id: Reference to parent calculation
        atom_index: 0-based position in molecule (matches XYZ order)
        element: Element symbol (H, C, N, O, etc.)
        partial_charge: Mulliken charge or similar
        position_x/y/z: Atomic coordinates (Angstroms)
        force_x/y/z: Force vectors (atomic units)
    """
    __tablename__ = "atomic_properties"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    calculation_id = Column(Integer, ForeignKey("calculations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Atom identification
    atom_index = Column(Integer, nullable=False)  # 0-based index
    element = Column(String(3), nullable=False, index=True)  # H, C, N, O, S, etc.
    atomic_number = Column(Integer, nullable=False)  # Atomic number
    
    # Computed properties
    partial_charge = Column(Float, nullable=True)  # Charge (e)
    position_x = Column(Float, nullable=False)  # Position in Angstroms
    position_y = Column(Float, nullable=False)
    position_z = Column(Float, nullable=False)
    
    # Forces
    force_x = Column(Float, nullable=True)  # Force (Hartree/Bohr)
    force_y = Column(Float, nullable=True)
    force_z = Column(Float, nullable=True)
    
    # Orbital energy
    orbital_energy = Column(Float, nullable=True)  # If available
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    atom_metadata = Column(JSONB, default={})
    
    # Relationships
    calculation = relationship("Calculation", back_populates="atomic_properties")
    
    __table_args__ = (
        Index("idx_atomic_properties_calculation_id", "calculation_id"),
        Index("idx_atomic_properties_element", "element"),
    )

    def __repr__(self):
        return f"<AtomicProperty(calc_id={self.calculation_id}, atom={self.element}{self.atom_index})>"


class BatchJob(Base):
    """
    Groups multiple molecules for bulk processing.
    
    Used for:
    - Drug discovery screens (test 1000 compounds)
    - Materials discovery (systematic parameter variation)
    - Data collection campaigns
    - ML dataset curation
    
    Tracks:
    - Progress: which molecules succeeded/failed
    - Status: pending → in_progress → completed
    - Parameters: what xTB settings were used
    - Metadata: reason for batch, researcher notes, etc.
    
    Attributes:
        batch_name: User-friendly identifier
        status: pending, in_progress, completed, failed
        total_molecules: Expected count
        successful_count: Completed calculations
        failed_count: Failed calculations
        parameters: Shared xTB parameters for all molecules
    """
    __tablename__ = "batch_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    batch_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="pending", index=True)  # pending, in_progress, completed, failed
    
    # Progress tracking
    total_molecules = Column(Integer, default=0)
    successful_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    
    # Shared parameters
    parameters = Column(JSONB, default={})  # xTB method, solvent, etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    batch_metadata = Column(JSONB, default={})
    
    # Relationships
    batch_items = relationship("BatchItem", back_populates="batch", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_batch_jobs_status", "status"),
    )

    def __repr__(self):
        return f"<BatchJob(id={self.id}, name={self.batch_name}, status={self.status})>"


class BatchItem(Base):
    """
    Links molecules to batches and tracks individual item status.
    
    Many-to-many relationship:
    - One batch can contain many molecules
    - One molecule can be in multiple batches
    
    Tracks per-item status within batch:
    - pending: Queued for processing
    - processing: Currently running
    - completed: Finished, result in calculations table
    - failed: Error occurred (check error_message)
    - skipped: Intentionally not run
    
    Attributes:
        batch_id: Which batch this molecule is in
        molecule_id: Which molecule
        calculation_id: Reference to result (if completed)
        error_message: Error details if failed
        retry_count: How many times we tried
    """
    __tablename__ = "batch_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    batch_id = Column(Integer, ForeignKey("batch_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    molecule_id = Column(Integer, ForeignKey("molecules.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Item status
    status = Column(String(50), default="pending", index=True)  # pending, processing, completed, failed, skipped
    calculation_id = Column(Integer, ForeignKey("calculations.id", ondelete="SET NULL"), nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    item_metadata = Column(JSONB, default={})
    
    # Relationships
    batch = relationship("BatchJob", back_populates="batch_items")
    molecule = relationship("Molecule", back_populates="batch_items")
    
    __table_args__ = (
        UniqueConstraint("batch_id", "molecule_id", name="unique_batch_molecule"),
        Index("idx_batch_items_batch_id", "batch_id"),
        Index("idx_batch_items_molecule_id", "molecule_id"),
        Index("idx_batch_items_status", "status"),
    )

    def __repr__(self):
        return f"<BatchItem(batch_id={self.batch_id}, mol_id={self.molecule_id}, status={self.status})>"


class EventLog(Base):
    """
    Comprehensive audit trail of all database operations.
    
    Every important action is logged:
    - Calculation started/completed/failed
    - Batch processed
    - Errors encountered
    - Data modifications
    
    Used for:
    - Debugging: Trace exactly what happened
    - Monitoring: Alert on failures
    - Compliance: GDPR audit trail
    - Analytics: Understand system usage patterns
    
    Attributes:
        event_type: What happened (calculation_started, etc.)
        entity_type: What was affected (calculations, batches, etc.)
        entity_id: Which specific record
        status: success, warning, error
        error_message: Details if something went wrong
        context: JSON with full event details for ML training
    """
    __tablename__ = "event_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Event classification
    event_type = Column(String(50), nullable=False, index=True)  # calculation_started, batch_completed, etc.
    entity_type = Column(String(50), nullable=False, index=True)  # molecules, calculations, batches
    entity_id = Column(Integer, nullable=True)  # ID of affected entity
    
    # Status and errors
    status = Column(String(50), default="success", index=True)  # success, warning, error
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)
    
    # Full context for reconstruction and ML
    context = Column(JSONB, default={})  # xTB version, method, timing, etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    
    # Service tracking
    service = Column(String(50), default="api")  # Which service logged this
    
    __table_args__ = (
        Index("idx_event_logs_created_at", "created_at"),
        Index("idx_event_logs_entity_type", "entity_type"),
        Index("idx_event_logs_event_type", "event_type"),
        Index("idx_event_logs_status", "status"),
        Index("idx_event_logs_composite", "user_id", "created_at", "event_type"),
    )

    def __repr__(self):
        return f"<EventLog(id={self.id}, event={self.event_type}, status={self.status})>"
