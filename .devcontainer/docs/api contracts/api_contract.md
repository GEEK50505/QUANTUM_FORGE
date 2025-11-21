# Quantum Forge API Contracts

## Overview

This document defines the API contracts and interfaces for the Quantum Forge platform, covering both backend services and frontend interactions.

**⚠️ NOTE: This document is currently under active development. API contracts are subject to change.**

## Table of Contents

1. [Backend API Contracts](#backend-api-contracts)
2. [Frontend API Contracts](#frontend-api-contracts)
3. [QPU Integration Contracts](#qpu-integration-contracts)
4. [Data Models](#data-models)
5. [Authentication](#authentication)
6. [Error Handling](#error-handling)

## Backend API Contracts

### Classical Simulation Service

#### POST /api/v1/simulation/classical
Start a classical molecular dynamics simulation

**Request:**
```json
{
  "num_particles": 100,
  "box_size": 10.0,
  "temperature": 300.0,
  "simulation_time": 1000,
  "time_step": 0.001
}
```

**Response:**
```json
{
  "simulation_id": "uuid-string",
  "status": "running",
  "start_time": "ISO8601-timestamp"
}
```

#### GET /api/v1/simulation/classical/{simulation_id}
Get classical simulation status and results

**Response:**
```json
{
  "simulation_id": "uuid-string",
  "status": "completed",
  "progress": 100,
  "results": {
    "positions": [[x1, y1, z1], [x2, y2, z2]],
    "energies": [1.23, 1.25, 1.24],
    "temperature": 300.0
  }
}
```

### Quantum Solver Service

#### POST /api/v1/simulation/quantum
Start a quantum mechanical calculation

**Request:**
```json
{
  "molecule": "H2",
  "positions": [[0.0, 0.0, 0.0], [0.74, 0.0, 0.0]],
  "method": "hartree-fock",
  "basis_set": "sto-3g"
}
```

**Response:**
```json
{
  "calculation_id": "uuid-string",
  "status": "running",
  "start_time": "ISO8601-timestamp"
}
```

### Hybrid Pipeline Service

#### POST /api/v1/simulation/hybrid
Start a hybrid quantum-classical simulation

**Request:**
```json
{
  "system": {
    "classical_particles": 1000,
    "quantum_regions": [
      {
        "region_id": "active_site",
        "particles": [1, 2, 3, 4],
        "method": "full-ci"
      }
    ]
  },
  "parameters": {
    "classical_steps": 1000,
    "quantum_frequency": 10,
    "time_step": 0.001
  }
}
```

## Frontend API Contracts

### Simulation Management

#### GET /api/v1/frontend/simulations
Get list of simulations for dashboard display

**Response:**
```json
{
  "simulations": [
    {
      "id": "uuid-string",
      "name": "H2 Hybrid Simulation",
      "type": "hybrid",
      "status": "running",
      "progress": 75,
      "start_time": "ISO8601-timestamp",
      "estimated_completion": "ISO8601-timestamp"
    }
  ]
}
```

#### GET /api/v1/frontend/simulations/{id}/results
Get simulation results for visualization

**Response:**
```json
{
  "id": "uuid-string",
  "results": {
    "classical": {
      "trajectory": [...],
      "energies": [...],
      "temperature_profile": [...]
    },
    "quantum": {
      "orbitals": [...],
      "energies": [...],
      "densities": [...]
    },
    "hybrid": {
      "combined_results": [...]
    }
  }
}
```

## QPU Integration Contracts

### Quantum Processing Unit Interface

#### POST /api/v1/qpu/submit
Submit quantum circuit for execution

**Request:**
```json
{
  "circuit": "openqasm-string",
  "shots": 1000,
  "backend": "simulator|ibm-quantum|ionq"
}
```

**Response:**
```json
{
  "job_id": "qpu-job-uuid",
  "status": "submitted",
  "submission_time": "ISO8601-timestamp"
}
```

#### GET /api/v1/qpu/results/{job_id}
Get quantum computation results

**Response:**
```json
{
  "job_id": "qpu-job-uuid",
  "status": "completed",
  "results": {
    "counts": {"00": 500, "01": 250, "10": 200, "11": 50},
    "probabilities": {"00": 0.5, "01": 0.25, "10": 0.2, "11": 0.05},
    "execution_time": 12.5
  }
}
```

## Data Models

### Simulation Model

```typescript
interface Simulation {
  id: string;
  name: string;
  type: 'classical' | 'quantum' | 'hybrid';
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number; // 0-100
  parameters: SimulationParameters;
  results?: SimulationResults;
  created_at: string; // ISO8601
  updated_at: string; // ISO8601
  completed_at?: string; // ISO8601
}

interface SimulationParameters {
  [key: string]: any; // Type-specific parameters
}

interface SimulationResults {
  classical?: ClassicalResults;
  quantum?: QuantumResults;
  hybrid?: HybridResults;
}
```

### Classical Results

```typescript
interface ClassicalResults {
  positions: number[][][]; // [timestep][particle][x,y,z]
  velocities: number[][][]; // [timestep][particle][vx,vy,vz]
  energies: {
    kinetic: number[];
    potential: number[];
    total: number[];
  };
  temperature: number[];
}
```

### Quantum Results

```typescript
interface QuantumResults {
  eigenvalues: number[];
  eigenvectors: number[][];
  orbitals: {
    energies: number[];
    coefficients: number[][];
  };
  density_matrices: number[][][];
}
```

## Authentication

### JWT Token Authentication

All API endpoints require a valid JWT token in the Authorization header:

```
Authorization: Bearer <jwt-token>
```

#### POST /api/v1/auth/login
User login

**Request:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "token": "jwt-token-string",
  "expires_in": 3600,
  "user": {
    "id": "user-uuid",
    "username": "string",
    "email": "string",
    "role": "user|admin"
  }
}
```

## Error Handling

### Standard Error Response Format

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "specific field if applicable",
      "value": "invalid value if applicable"
    }
  }
}
```

### Common Error Codes

- `VALIDATION_ERROR`: Request validation failed
- `AUTHENTICATION_ERROR`: Invalid or missing authentication
- `AUTHORIZATION_ERROR`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `INTERNAL_ERROR`: Server-side error
- `SERVICE_UNAVAILABLE`: External service unavailable

## Development Status

This API contract is under active development. The following areas are currently being refined:

- **Classical Simulation API**: Under development
- **Quantum Solver API**: Under development
- **Hybrid Pipeline API**: Under development
- **Frontend Integration**: Under development
- **QPU Integration**: Under development

## Version History

- **v0.1.0**: Initial draft (current)
- **v1.0.0**: Planned stable release

## Contributing

API contract changes should be carefully considered and documented. All breaking changes require version increment and migration documentation.
