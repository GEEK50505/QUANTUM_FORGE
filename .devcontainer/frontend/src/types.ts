/*
Purpose: 
Description: 
Exports: 
Notes: Add a short usage example and expected props/return types.
*/

export interface JobSubmitRequest {
  molecule_name: string
  xyz_content: string
  optimization_level: 'tight' | 'normal'
  email: string
  tags: string[]
}

export interface JobResponse {
  job_id: string
  // Status uses runtime values that come from SIMULATION_STATUS (lowercase strings)
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled'
  created_at: string // ISO datetime
  updated_at: string
  molecule_name?: string
  xyz_content?: string
  tags?: string[]
  results?: ResultsResponse
  error_message?: string
}

export interface ResultsResponse {
  energy: number
  homo_lumo_gap: number
  gradient_norm: number
  charges: number[]
  convergence_status: string
  properties: Record<string, any>
}

export interface ApiError {
  error_code: string
  error_message: string
  status_code: number
}