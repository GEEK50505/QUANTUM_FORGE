// NOTE (permanent): This file contains educational notes for non-coders.
// Do not remove comments unless explicitly requested in a written instruction.
// These notes explain purpose, props, and data contract shapes.
//
// Module Purpose: Central API client for Quantum Forge
// What this file renders: N/A (service functions only)
// How it fits into the Quantum Forge app: Provides a single point of contact
// for all backend API calls, switching between real and mock implementations
// Author: Qwen 3 Coder — Scaffold Stage

/**
 * API Service
 * 
 * This module provides a centralized client for making API calls to the
 * Quantum Forge backend. It automatically switches between real API calls
 * and mock implementations based on the DEV_MODE setting.
 * 
 * For non-coders: This is the "messenger" that sends requests to the backend
 * server and brings back the responses. When in development mode (DEV_MODE=true),
 * it uses fake data so you can test the UI without needing a real server.
 * When you connect to a real backend, it will automatically switch to making
 * actual network requests.
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
