/**
 * frontend/src/api/client.ts
 *
 * Purpose:
 *  - Typed axios-based API client used by frontend components to interact with
 *    the backend REST API (job submission, status, results, listing, delete).
 *
 * Exports:
 *  - submitJob(request: JobSubmitRequest): Promise<JobResponse>
 *  - getJobStatus(jobId: string): Promise<JobResponse>
 *  - getJobResults(jobId: string): Promise<ResultsResponse>
 *  - listJobs(status?: string): Promise<JobResponse[]>
 *  - deleteJob(jobId: string): Promise<void>
 *
 * Notes:
 *  - Uses an axios instance with interceptors for lightweight logging and
 *    centralized error handling. Error messages are normalized via
 *    `handleApiError` to surface friendly messages to UI components.
 *  - Base URL configured for local dev; adjust via environment variables in
 *    CI/CD or production builds as needed.
 *
 * Example:
 *  const job = await submitJob({ name: 'water', xyz: '...' })
 */

import axios, { AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios'
import { JobSubmitRequest, JobResponse, ResultsResponse } from '../types'

// Create axios instance with baseURL
const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 30000, // 30 seconds timeout
})

// Add request interceptor for logging
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    console.debug('API Request:', config.method?.toUpperCase(), config.url)
    return config
  },
  (error: any) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    console.debug('API Response:', response.status, response.config.url)
    return response
  },
  (error: any) => {
    console.error('API Response Error:', error.response?.status, error.response?.data)
    return Promise.reject(error)
  }
)

// Helper function to handle API errors
const handleApiError = (error: any): string => {
  if (axios.isAxiosError(error)) {
    if (error.response) {
      // Server responded with error status
      return error.response.data?.error_message || error.response.data?.detail || `Error ${error.response.status}: ${error.response.statusText}`
    } else if (error.request) {
      // Network error
      return 'Network error: Please check your connection'
    } else {
      // Other error
      return error.message || 'An unknown error occurred'
    }
  } else {
    // Non-Axios error
    return 'An unexpected error occurred'
  }
}

// API Functions

export const submitJob = async (request: JobSubmitRequest): Promise<JobResponse> => {
  try {
    const response = await apiClient.post<JobResponse>('/jobs/submit', request)
    return response.data
  } catch (error: any) {
    throw new Error(handleApiError(error))
  }
}

export const getJobStatus = async (jobId: string): Promise<JobResponse> => {
  try {
    const response = await apiClient.get<JobResponse>(`/jobs/${jobId}`)
    return response.data
  } catch (error: any) {
    throw new Error(handleApiError(error))
  }
}

export const getJobResults = async (jobId: string): Promise<ResultsResponse> => {
  try {
    const response = await apiClient.get<ResultsResponse>(`/jobs/${jobId}/results`)
    return response.data
  } catch (error: any) {
    throw new Error(handleApiError(error))
  }
}

export const listJobs = async (status?: string): Promise<JobResponse[]> => {
  try {
    const params = status ? { status } : {}
    const response = await apiClient.get<JobResponse[]>('/jobs/list', { params })
    return response.data
  } catch (error: any) {
    throw new Error(handleApiError(error))
  }
}

export const deleteJob = async (jobId: string): Promise<void> => {
  try {
    await apiClient.delete(`/jobs/${jobId}`)
  } catch (error: any) {
    throw new Error(handleApiError(error))
  }
}