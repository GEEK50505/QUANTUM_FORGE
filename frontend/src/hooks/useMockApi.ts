// NOTE (permanent): This file contains educational notes for non-coders.
// Do not remove comments unless explicitly requested in a written instruction.
// These notes explain purpose, props, and data contract shapes.
//
// Module Purpose: Mock API implementation for development
// What this file renders: N/A (mock data functions only)
// How it fits into the Quantum Forge app: Provides fake data during development
// so the UI can be tested without a real backend
// Author: Qwen 3 Coder — Scaffold Stage

/**
 * Mock API Hook
 * 
 * This module provides mock implementations of API calls for development purposes.
 * It simulates backend responses with realistic data structures and delays.
 * 
 * For non-coders: This is a "fake server" that pretends to have data so you can
 * test how the application looks and works without connecting to a real backend.
 * All the data here is made up but follows the same format as real data would.
 */

import { ApiResponse } from '../services/api';
import { SIMULATION_STATUS, SIMULATION_BACKENDS } from '../utils/constants';

// Mock data types
export interface Simulation {
  id: string;
  name: string;
  // Use the runtime values (the constant values are lowercase strings)
  type: typeof SIMULATION_BACKENDS[keyof typeof SIMULATION_BACKENDS];
  status: typeof SIMULATION_STATUS[keyof typeof SIMULATION_STATUS];
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  duration?: number; // in seconds
  energy?: number; // in Hartree
  qubits?: number;
  shots?: number;
  optimizer?: string;
}

export interface Dataset {
  id: string;
  name: string;
  size: number; // in MB
  createdAt: string;
  version: string;
  description: string;
}

export interface Model {
  id: string;
  name: string;
  type: 'classical' | 'quantum';
  version: string;
  createdAt: string;
  description: string;
  deployed: boolean;
}

// Mock data collections
const mockSimulations: Simulation[] = [
  {
    id: 'sim-001',
    name: 'H2 Ground State Calculation',
    type: SIMULATION_BACKENDS.QUANTUM,
    status: SIMULATION_STATUS.COMPLETED,
    createdAt: '2025-10-25T10:30:00Z',
    startedAt: '2025-10-25T10:31:00Z',
    completedAt: '2025-10-25T10:35:00Z',
    duration: 240,
    energy: -1.137,
    qubits: 4,
    shots: 1024,
    optimizer: 'VQE'
  },
  {
    id: 'sim-002',
    name: 'LiH Dissociation Curve',
    type: SIMULATION_BACKENDS.HYBRID,
    status: SIMULATION_STATUS.RUNNING,
    createdAt: '2025-10-26T14:15:00Z',
    startedAt: '2025-10-26T14:16:00Z',
    duration: 180,
    energy: -8.012,
    qubits: 12,
    shots: 2048,
    optimizer: 'ADAPT-VQE'
  },
  {
    id: 'sim-003',
    name: 'Water Cluster Optimization',
    type: SIMULATION_BACKENDS.CLASSICAL,
    status: SIMULATION_STATUS.QUEUED,
    createdAt: '2025-10-26T16:45:00Z',
    qubits: 0,
    shots: 0,
    optimizer: 'L-BFGS'
  },
  {
    id: 'sim-004',
    name: 'FeMoco Active Site',
    type: SIMULATION_BACKENDS.QUANTUM,
    status: SIMULATION_STATUS.FAILED,
    createdAt: '2025-10-27T08:20:00Z',
    startedAt: '2025-10-27T08:21:00Z',
    completedAt: '2025-10-27T08:25:00Z',
    duration: 240,
    qubits: 54,
    shots: 4096,
    optimizer: 'QAOA'
  }
];

const mockDatasets: Dataset[] = [
  {
    id: 'ds-001',
    name: 'H2 Binding Energies',
    size: 2.4,
    createdAt: '2025-10-20T09:00:00Z',
    version: '1.0.0',
    description: 'Experimental and calculated binding energies for hydrogen molecule'
  },
  {
    id: 'ds-002',
    name: 'LiH Geometry Scan',
    size: 5.7,
    createdAt: '2025-10-22T14:30:00Z',
    version: '1.1.0',
    description: 'Complete geometry scan of lithium hydride molecule'
  }
];

const mockModels: Model[] = [
  {
    id: 'mdl-001',
    name: 'UCCSD Ansatz',
    type: 'quantum',
    version: '2.1.0',
    createdAt: '2025-10-15T11:20:00Z',
    description: 'Unitary Coupled Cluster Singles and Doubles variational form',
    deployed: true
  },
  {
    id: 'mdl-002',
    name: 'DFT Functional B3LYP',
    type: 'classical',
    version: '1.0.0',
    createdAt: '2025-10-18T16:45:00Z',
    description: 'Becke three-parameter Lee-Yang-Parr density functional',
    deployed: true
  }
];

/**
 * Mock API Implementation
 * 
 * Simulates API calls with realistic delays and data structures.
 * 
 * @param endpoint - The API endpoint being called
 * @param config - Configuration for the request
 * @returns Promise with mock API response
 */
export async function useMockApi<T>(
  endpoint: string,
  config: any
): Promise<ApiResponse<T>> {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 300 + Math.random() * 700));
  
  // Handle different endpoints
  if (endpoint === '/simulations') {
    if (config.method === 'GET') {
      return {
        data: mockSimulations as unknown as T,
        status: 200
      };
    } else if (config.method === 'POST') {
      const newSimulation: Simulation = {
        id: `sim-${String(mockSimulations.length + 1).padStart(3, '0')}`,
        name: config.body?.name || 'New Simulation',
        type: config.body?.type || SIMULATION_BACKENDS.CLASSICAL,
        status: SIMULATION_STATUS.QUEUED,
        createdAt: new Date().toISOString(),
        qubits: config.body?.qubits || 0,
        shots: config.body?.shots || 0,
        optimizer: config.body?.optimizer || 'Unknown'
      };
      
      mockSimulations.push(newSimulation);
      
      return {
        data: newSimulation as unknown as T,
        status: 201
      };
    }
  }
  
  if (endpoint.startsWith('/simulations/')) {
    const id = endpoint.split('/')[2];
    const simulation = mockSimulations.find(sim => sim.id === id);
    
    if (simulation) {
      return {
        data: simulation as unknown as T,
        status: 200
      };
    } else {
      return {
        data: null as unknown as T,
        status: 404,
        message: 'Simulation not found'
      };
    }
  }
  
  if (endpoint === '/datasets') {
    return {
      data: mockDatasets as unknown as T,
      status: 200
    };
  }
  
  if (endpoint === '/models') {
    return {
      data: mockModels as unknown as T,
      status: 200
    };
  }
  
  // Default response for unknown endpoints
  return {
    data: null as unknown as T,
    status: 404,
    message: 'Endpoint not found'
  };
}
