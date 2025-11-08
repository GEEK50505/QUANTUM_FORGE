# API Reference — Quantum_Forge

This document aims to list and describe all public REST endpoints provided
by the backend (FastAPI). It will be kept in sync with `backend/api/routes.py`.

## Base path

All endpoints are mounted under `/api/v1` by default in development.

## Jobs

- POST /jobs/submit
  - Description: Submit a new xTB job.
  - Request: Job submission payload (molecule name, XYZ content, optimization level, email optional)
  - Response: { job_id: string, status: 'queued' }

- GET /jobs/{job_id}
  - Description: Get job status and metadata

- GET /jobs/{job_id}/results
  - Description: Retrieve computation results when available

- GET /jobs/list?status={status}
  - Description: List jobs, optional filter by status

- DELETE /jobs/{job_id}
  - Description: Delete a job and its artifacts


(Will expand with full request/response schemas from `backend/api/schemas.py`)
