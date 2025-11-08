/*
Purpose: 
Description: 
Exports: 
Notes: Add a short usage example and expected props/return types.
*/

import { AxiosError } from 'axios'

/**
 * Extract user-friendly error message from axios/API errors
 * @param error - The error object
 * @returns A user-friendly error message
 */
export const getErrorMessage = (error: unknown): string => {
  if (error instanceof Error) {
    // Handle axios errors
    if (isApiError(error)) {
      const axiosError = error as AxiosError
      if (axiosError.response?.data) {
        // Try to extract error message from response data
        const data = axiosError.response.data as any
        if (data.error_message) {
          return data.error_message
        }
        if (data.message) {
          return data.message
        }
        if (data.detail) {
          return data.detail
        }
      }
      
      // Return status text or generic message
      if (axiosError.response?.statusText) {
        return `${axiosError.response.status}: ${axiosError.response.statusText}`
      }
      
      return `API Error: ${axiosError.message}`
    }
    
    // Handle network errors
    if (isNetworkError(error)) {
      return 'Network error: Please check your connection and try again'
    }
    
    // Handle other Error instances
    return error.message
  }
  
  // Handle non-Error objects
  if (typeof error === 'string') {
    return error
  }
  
  // Handle other types
  return 'An unexpected error occurred'
}

/**
 * Check if an error is a network error
 * @param error - The error object
 * @returns True if the error is a network error
 */
export const isNetworkError = (error: unknown): boolean => {
  if (error instanceof Error) {
    return !!(error as any).isAxiosError && !(error as AxiosError).response
  }
  return false
}

/**
 * Check if an error is an API error (axios error with response)
 * @param error - The error object
 * @returns True if the error is an API error
 */
export const isApiError = (error: unknown): boolean => {
  return error instanceof Error && !!(error as any).isAxiosError
}

/**
 * Check if an error is a timeout error
 * @param error - The error object
 * @returns True if the error is a timeout error
 */
export const isTimeoutError = (error: unknown): boolean => {
  if (isApiError(error)) {
    const axiosError = error as AxiosError
    return axiosError.code === 'ECONNABORTED'
  }
  return false
}