"""
Pydantic Schemas for API Request/Response Validation

Defines data models for all database entities with:
- Type hints and validation
- Field descriptions for API documentation
- Relationships between entities
- Both request (POST/PUT) and response (GET) schemas
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


# ============================================================================
# MOLECULE SCHEMAS
# ============================================================================

class MoleculeBase(BaseModel):
    """Base molecule data (for create/update)"""
    name: str = Field(..., description="Human-readable molecule name (e.g., 'water')", min_length=1)
    smiles: str = Field(..., description="SMILES notation for structure", min_length=1)
    formula: str = Field(..., description="Chemical formula (e.g., 'H2O')", min_length=1)
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional data (JSON)")


class MoleculeCreate(MoleculeBase):
    """Schema for creating molecules"""
    pass


class MoleculeUpdate(BaseModel):
    """Schema for updating molecules"""
    name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class MoleculeResponse(MoleculeBase):
    """Schema for molecule API responses"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MoleculeDetail(MoleculeResponse):
    """Molecule with related calculations"""
    calculations: List['CalculationResponse'] = []


# ============================================================================
# CALCULATION SCHEMAS
# ============================================================================

class CalculationBase(BaseModel):
    """Base calculation data"""
    molecule_id: int
    energy: float = Field(..., description="Total energy in Hartree")
    homo: Optional[float] = Field(None, description="HOMO energy (eV)")
    lumo: Optional[float] = Field(None, description="LUMO energy (eV)")
    gap: Optional[float] = Field(None, description="HOMO-LUMO gap (eV)")
    dipole: Optional[float] = Field(None, description="Dipole moment (Debye)")
    total_charge: Optional[float] = Field(default=0.0, description="Total charge (e)")
    execution_time_seconds: float = Field(..., description="Runtime in seconds")
    xtb_version: Optional[str] = None
    solvation: Optional[str] = None
    method: Optional[str] = Field(default="GFN2-xTB")
    convergence_status: Optional[str] = Field(default="converged")
    metadata: Optional[Dict[str, Any]] = Field(default={})


class CalculationCreate(CalculationBase):
    """Schema for creating calculations"""
    pass


class CalculationUpdate(BaseModel):
    """Schema for updating calculations"""
    convergence_status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CalculationResponse(CalculationBase):
    """Schema for calculation API responses"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CalculationDetail(CalculationResponse):
    """Calculation with related atomic properties"""
    atomic_properties: List['AtomicPropertyResponse'] = []
    molecule: Optional[MoleculeResponse] = None


# ============================================================================
# ATOMIC PROPERTY SCHEMAS
# ============================================================================

class AtomicPropertyBase(BaseModel):
    """Base atomic property data"""
    calculation_id: int
    atom_index: int = Field(..., description="0-based atom index in molecule")
    element: str = Field(..., description="Element symbol (H, C, N, O, etc.)")
    atomic_number: int = Field(..., description="Atomic number")
    partial_charge: Optional[float] = Field(None, description="Mulliken charge (e)")
    position_x: float = Field(..., description="X coordinate (Angstroms)")
    position_y: float = Field(..., description="Y coordinate (Angstroms)")
    position_z: float = Field(..., description="Z coordinate (Angstroms)")
    force_x: Optional[float] = Field(None, description="X force (Hartree/Bohr)")
    force_y: Optional[float] = Field(None, description="Y force (Hartree/Bohr)")
    force_z: Optional[float] = Field(None, description="Z force (Hartree/Bohr)")
    orbital_energy: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = Field(default={})


class AtomicPropertyCreate(AtomicPropertyBase):
    """Schema for creating atomic properties"""
    pass


class AtomicPropertyResponse(AtomicPropertyBase):
    """Schema for atomic property API responses"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# BATCH JOB SCHEMAS
# ============================================================================

class BatchJobBase(BaseModel):
    """Base batch job data"""
    batch_name: str = Field(..., description="Batch identifier/name")
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = Field(default={}, description="Shared xTB parameters")


class BatchJobCreate(BatchJobBase):
    """Schema for creating batch jobs"""
    total_molecules: Optional[int] = None


class BatchJobUpdate(BaseModel):
    """Schema for updating batch jobs"""
    status: Optional[str] = None
    successful_count: Optional[int] = None
    failed_count: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class BatchJobResponse(BatchJobBase):
    """Schema for batch job API responses"""
    id: int
    status: str
    total_molecules: int
    successful_count: int
    failed_count: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BatchJobDetail(BatchJobResponse):
    """Batch with all items"""
    batch_items: List['BatchItemResponse'] = []


# ============================================================================
# BATCH ITEM SCHEMAS
# ============================================================================

class BatchItemBase(BaseModel):
    """Base batch item data"""
    batch_id: int
    molecule_id: int
    status: Optional[str] = Field(default="pending")


class BatchItemCreate(BatchItemBase):
    """Schema for creating batch items"""
    pass


class BatchItemUpdate(BaseModel):
    """Schema for updating batch items"""
    status: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: Optional[int] = None


class BatchItemResponse(BatchItemBase):
    """Schema for batch item API responses"""
    id: int
    calculation_id: Optional[int] = None
    error_message: Optional[str] = None
    retry_count: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# EVENT LOG SCHEMAS
# ============================================================================

class EventLogBase(BaseModel):
    """Base event log data"""
    event_type: str = Field(..., description="Event type (calculation_started, etc.)")
    entity_type: str = Field(..., description="Entity type (calculations, batches, etc.)")
    entity_id: Optional[int] = None
    status: str = Field(default="success", description="success, warning, error")
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    context: Optional[Dict[str, Any]] = Field(default={})


class EventLogCreate(EventLogBase):
    """Schema for creating event logs"""
    pass


class EventLogResponse(EventLogBase):
    """Schema for event log API responses"""
    id: int
    created_at: datetime
    service: str
    
    class Config:
        from_attributes = True


# ============================================================================
# SUMMARY SCHEMAS
# ============================================================================

class DatabaseStatsResponse(BaseModel):
    """Overall database statistics"""
    total_molecules: int
    total_calculations: int
    total_batches: int
    average_energy: Optional[float] = None
    median_gap: Optional[float] = None
    success_rate: float
    latest_calculation_at: Optional[datetime] = None


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="healthy, unhealthy")
    database: str = Field(..., description="Database type")
    message: str = Field(..., description="Details")
    tables_exist: bool
    pool_size: Optional[str] = None


# ============================================================================
# UPDATE FORWARD REFERENCES
# ============================================================================

MoleculeDetail.update_forward_refs()
CalculationDetail.update_forward_refs()
BatchJobDetail.update_forward_refs()
