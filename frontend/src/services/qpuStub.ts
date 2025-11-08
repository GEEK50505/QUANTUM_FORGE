/**
 * frontend/src/services/qpuStub.ts
 *
 * Purpose:
 *  - Provide development-time stub implementations for QPU operations (VQE, job
 *    status). These simulate latency and return deterministic mock data so the
 *    frontend can be developed and tested without real quantum hardware.
 *
 * Exports:
 *  - runVQEStub(params: VqeParams): Promise<QpuJob>
 *  - getJobStatusStub(jobId: string): Promise<QpuJob>
 *
 * Behavior:
 *  - Generates fake job IDs, simulates delays, and returns mock energies.
 *  - Keep this module lightweight and deterministic; replace in production
 *    with a real QPU adapter that implements the same export signatures.
 *
 * Example:
 *  const job = await runVQEStub({ molecule: 'H2', basis: 'sto-3g', qubits: 2, shots: 100, optimizer: 'SPSA' })
 */

// Type definitions for QPU operations
export interface QpuJob {
  jobId: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  energy?: number; // in Hartree
  qubits: number;
  runtime?: number; // in seconds
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
}

export interface VqeParams {
  molecule: string;
  basis: string;
  qubits: number;
  shots: number;
  optimizer: string;
}

/**
 * Run VQE Stub
 * 
 * Simulates running a Variational Quantum Eigensolver (VQE) calculation.
 * VQE is a quantum algorithm used to find the ground state energy of molecules.
 * 
 * For non-coders: This function pretends to run a quantum chemistry calculation
 * that finds the lowest energy state of a molecule. In reality, it just waits
 * a bit and returns fake results to simulate what a real quantum computer would do.
 * 
 * @param params - Parameters for the VQE calculation
 * @returns Promise with job information and results
 */
export async function runVQEStub(params: VqeParams): Promise<QpuJob> {
  // Generate a fake job ID
  const jobId = `qpu-job-${Date.now()}`;
  
  // Create initial job object
  const job: QpuJob = {
    jobId,
    status: 'queued',
    qubits: params.qubits,
    createdAt: new Date().toISOString()
  };
  
  // Simulate queuing time (1-3 seconds)
  await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));
  
  // Update status to running
  job.status = 'running';
  job.startedAt = new Date().toISOString();
  
  // Simulate computation time (3-7 seconds)
  await new Promise(resolve => setTimeout(resolve, 3000 + Math.random() * 4000));
  
  // Generate mock results based on input parameters
  const mockEnergies: Record<string, number> = {
    'H2': -1.137,
    'LiH': -8.012,
    'H2O': -76.421,
    'default': -5.123
  };
  
  // Update job with results
  job.status = 'completed';
  job.completedAt = new Date().toISOString();
  job.runtime = (new Date(job.completedAt).getTime() - new Date(job.startedAt!).getTime()) / 1000;
  job.energy = mockEnergies[params.molecule] || mockEnergies.default;
  
  return job;
}

/**
 * Get Job Status Stub
 * 
 * Simulates checking the status of a quantum computing job.
 * 
 * For non-coders: This function pretends to check on a running quantum calculation
 * to see if it's finished yet. In a real system, this would query actual quantum
 * hardware or cloud services.
 * 
 * @param jobId - The ID of the job to check
 * @returns Promise with current job status
 */
export async function getJobStatusStub(jobId: string): Promise<QpuJob> {
  // In a real implementation, this would query the actual QPU
  // For now, we'll just return a mock completed job
  
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 500));
  
  // Return a mock job (in reality this would fetch real job data)
  return {
    jobId,
    status: 'completed',
    energy: -1.137,
    qubits: 4,
    runtime: 5.2,
    createdAt: new Date(Date.now() - 10000).toISOString(),
    startedAt: new Date(Date.now() - 5000).toISOString(),
    completedAt: new Date().toISOString()
  };
}
