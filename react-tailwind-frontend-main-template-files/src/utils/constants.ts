// NOTE (permanent): This file contains educational notes for non-coders.
// Do not remove comments unless explicitly requested in a written instruction.
// These notes explain purpose, props, and data contract shapes.
//
// Module Purpose: Application constants for Quantum Forge
// What this file renders: N/A (constants only)
// How it fits into the Quantum Forge app: Provides shared configuration values
// and constant definitions used throughout the application
// Author: Qwen 3 Coder — Scaffold Stage

/**
 * Application Constants
 * 
 * This file contains shared constants used throughout the Quantum Forge application.
 * 
 * For non-coders: These are values that don't change during the application's
 * operation but are used in multiple places. Having them in one place makes
 * it easier to update them later if needed.
 */

// Development mode flag
// When true, the app uses mock data instead of real API calls
export const DEV_MODE = true;

// Default API endpoint
// This is where the backend server is expected to be running
export const API_BASE_URL = 'http://localhost:8000/api';

// Simulation status constants
// These represent the possible states of a simulation job
export const SIMULATION_STATUS = {
  QUEUED: 'queued',
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled'
} as const;

// Simulation backend types
// These represent the different computational backends available
export const SIMULATION_BACKENDS = {
  CLASSICAL: 'classical',
  QUANTUM: 'quantum',
  HYBRID: 'hybrid'
} as const;

// Default pagination values
export const DEFAULT_PAGE_SIZE = 10;
export const DEFAULT_PAGE_NUMBER = 1;

// Time formatting constants
export const TIME_FORMAT = 'YYYY-MM-DD HH:mm:ss';
export const DATE_FORMAT = 'YYYY-MM-DD';

// Energy unit (Hartree)
export const ENERGY_UNIT = 'Ha';
