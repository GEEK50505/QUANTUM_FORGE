from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum


class OptimizationLevel(str, Enum):
    TIGHT = "tight"
    NORMAL = "normal"


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class JobSubmitRequest(BaseModel):
    molecule_name: str = Field(..., example="benzene", description="Name of the molecule")
    xyz_content: str = Field(..., description="Raw XYZ file content")
    optimization_level: OptimizationLevel = Field(default=OptimizationLevel.NORMAL, description="Optimization level for xTB calculation")
    email: str = Field(..., example="user@university.edu", description="Email for notifications")
    tags: List[str] = Field(default=[], description="Tags for organizing results")

    @validator('molecule_name')
    def molecule_name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Molecule name cannot be empty')
        return v.strip()

    @validator('xyz_content')
    def xyz_content_must_be_valid(cls, v):
        if not v or not v.strip():
            raise ValueError('XYZ content cannot be empty')
        lines = v.strip().split('\n')
        if len(lines) < 2:
            raise ValueError('XYZ content must have at least 2 lines')
        try:
            int(lines[0].strip())
        except ValueError:
            raise ValueError('First line of XYZ content must be the number of atoms')
        return v.strip()


class JobResponse(BaseModel):
    job_id: str = Field(..., example="benzene_20251103_141530_a7f9e2d1", description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    created_at: datetime = Field(..., description="Job creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    results: Optional[Dict] = Field(None, description="Calculation results (only if completed)")
    error_message: Optional[str] = Field(None, description="Error message if job failed")


class ResultsResponse(BaseModel):
    energy: float = Field(..., example=-14.42, description="Total energy in Hartree")
    homo_lumo_gap: float = Field(..., example=0.117, description="HOMO-LUMO gap in Hartree")
    gradient_norm: float = Field(..., example=0.0027, description="Gradient norm")
    charges: List[float] = Field(..., description="Atomic charges")
    convergence_status: str = Field(..., example="CONVERGED", description="Convergence status")
    properties: Dict = Field(..., description="All extracted xTB properties")