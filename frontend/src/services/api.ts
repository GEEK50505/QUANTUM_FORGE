/**
 * frontend/src/services/api.ts
 *
 * Purpose:
 *  - Small wrapper around fetch-based HTTP calls used across the frontend.
 *  - Provides `client`, `get`, `post`, `put`, `del` helpers and automatically
 *    uses mock implementations when `DEV_MODE` is enabled.
 *
 * Exports:
 *  - client<T>(endpoint: string, config?: HttpClientConfig): Promise<ApiResponse<T>>
 *  - get<T>(endpoint: string): Promise<ApiResponse<T>>
 *  - post<T>(endpoint: string, body: any): Promise<ApiResponse<T>>
 *  - put<T>(endpoint: string, body: any): Promise<ApiResponse<T>>
 *  - del<T>(endpoint: string): Promise<ApiResponse<T>>
 *
 * Behavior:
 *  - In DEV_MODE the module delegates calls to the `useMockApi` helper so UI
 *    developers can work offline without a running backend.
 *  - In production it builds the full URL using `API_BASE_URL` and the native
 *    fetch API. Responses are returned as `{ data, status, message? }`.
 *
 * Example usage:
 *  const { data } = await post<JobResponse>('/jobs/submit', { name, xyz })
 */

import { DEV_MODE, API_BASE_URL } from '../utils/constants';
import { useMockApi } from '../hooks/useMockApi';

// Type definitions for API responses
export interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}

// HTTP client configuration
interface HttpClientConfig {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  headers?: Record<string, string>;
  body?: any;
}

/**
 * HTTP Client
 * 
 * A wrapper around the fetch API that handles requests to the backend.
 * In development mode, it uses mock data instead of real network calls.
 * 
 * @param endpoint - The API endpoint to call (e.g., '/simulations')
 * @param config - Configuration options for the request
 * @returns Promise with the API response
 */
export async function client<T>(
  endpoint: string,
  config: HttpClientConfig = {}
): Promise<ApiResponse<T>> {
  // If in development mode, use mock API
  if (DEV_MODE) {
    return useMockApi<T>(endpoint, config);
  }

  // In production mode, make real API calls
  const { method = 'GET', headers = {}, body } = config;
  
  const url = `${API_BASE_URL}${endpoint}`;
  
  const defaultHeaders = {
    'Content-Type': 'application/json',
    ...headers
  };
  
  const options: RequestInit = {
    method,
    headers: defaultHeaders,
    body: body ? JSON.stringify(body) : undefined
  };
  
  try {
    const response = await fetch(url, options);
    const data = await response.json();
    
    return {
      data,
      status: response.status,
      message: response.statusText
    };
  } catch (error) {
    throw new Error(`API request failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * GET Request Helper
 * 
 * Convenience function for making GET requests.
 */
export function get<T>(endpoint: string): Promise<ApiResponse<T>> {
  return client<T>(endpoint, { method: 'GET' });
}

/**
 * POST Request Helper
 * 
 * Convenience function for making POST requests.
 */
export function post<T>(endpoint: string, body: any): Promise<ApiResponse<T>> {
  return client<T>(endpoint, { method: 'POST', body });
}

/**
 * PUT Request Helper
 * 
 * Convenience function for making PUT requests.
 */
export function put<T>(endpoint: string, body: any): Promise<ApiResponse<T>> {
  return client<T>(endpoint, { method: 'PUT', body });
}

/**
 * DELETE Request Helper
 * 
 * Convenience function for making DELETE requests.
 */
export function del<T>(endpoint: string): Promise<ApiResponse<T>> {
  return client<T>(endpoint, { method: 'DELETE' });
}
