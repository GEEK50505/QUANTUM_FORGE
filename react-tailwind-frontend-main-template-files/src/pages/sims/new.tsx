// NOTE (permanent): This file contains educational notes for non-coders.
// Do not remove comments unless explicitly requested in a written instruction.
// These notes explain purpose, props, and data contract shapes.
//
// Module Purpose: New simulation wizard page
// What this file renders: Step-by-step wizard for creating new simulation jobs
// How it fits into the Quantum Forge app: Interface for configuring and starting
// new simulation jobs
// Author: Qwen 3 Coder — Scaffold Stage

import React, { useState } from 'react';
import { post } from '../../services/api';
import { Simulation } from '../../hooks/useMockApi';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';

/**
 * New Simulation Wizard Page
 * 
 * A step-by-step wizard for creating and configuring new simulation jobs.
 * Users select a system, configure backend parameters, and start the simulation.
 * 
 * For non-coders: This wizard guides you through creating a new simulation job.
 * Step 1: Choose what system to simulate (like a molecule)
 * Step 2: Choose the computational method and settings
 * Step 3: Review your choices and start the simulation
 */
const NewSimulationPage: React.FC = () => {
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [loading, setLoading] = useState(false);
  
  // Form state
  const [system, setSystem] = useState<string>('');
  const [backend, setBackend] = useState<'classical' | 'quantum' | 'hybrid'>('classical');
  const [qubits, setQubits] = useState<number>(4);
  const [shots, setShots] = useState<number>(1024);
  const [optimizer, setOptimizer] = useState<string>('L-BFGS');
  
  // Mock systems data
  const systems = [
    { id: 'H2', name: 'Hydrogen Molecule (H₂)', description: 'Simple diatomic molecule, good for testing' },
    { id: 'LiH', name: 'Lithium Hydride (LiH)', description: 'Small molecule with ionic character' },
    { id: 'H2O', name: 'Water Molecule (H₂O)', description: 'Common molecule with bent geometry' },
    { id: 'SiCluster', name: 'Silicon Cluster', description: 'Small silicon nanocluster system' }
  ];
  
  // Backend descriptions
  const backendDescriptions = {
    classical: 'Fast CPU-based simulation using classical algorithms. Good for initial approximations and large systems.',
    quantum: 'Quantum simulation using variational algorithms. More accurate for quantum systems but slower.',
    hybrid: 'Combines classical and quantum methods for optimal balance of speed and accuracy.'
  };
  
  // Handle form submission
  const handleSubmit = async () => {
    setLoading(true);
    
    try {
      // In a real app, this would create the actual simulation job
      const response = await post<Simulation>('/simulations', {
        name: `${system} Simulation`,
        type: backend,
        qubits: backend === 'classical' ? 0 : qubits,
        shots: backend === 'classical' ? 0 : shots,
        optimizer: optimizer
      });
      
      // In a real app, we'd redirect to the job details page
      alert(`Simulation job created successfully with ID: ${response.data.id}`);
      window.location.hash = `/sims/job/${response.data.id}`;
    } catch (error) {
      console.error('Failed to create simulation:', error);
      alert('Failed to create simulation. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="p-4 md:p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          New Simulation
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Create and configure a new quantum-classical simulation job
        </p>
      </div>
      
      {/* Progress Steps */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {[1, 2, 3].map((stepNum) => (
            <div key={stepNum} className="flex items-center">
              <div className={`flex h-8 w-8 items-center justify-center rounded-full ${
                step >= stepNum 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-200 text-gray-600 dark:bg-gray-700 dark:text-gray-300'
              }`}>
                {stepNum}
              </div>
              <div className="ml-2 hidden sm:block">
                <span className={`text-sm font-medium ${
                  step === stepNum 
                    ? 'text-blue-600 dark:text-blue-400' 
                    : 'text-gray-600 dark:text-gray-400'
                }`}>
                  {stepNum === 1 && 'Select System'}
                  {stepNum === 2 && 'Configure'}
                  {stepNum === 3 && 'Review & Start'}
                </span>
              </div>
              {stepNum < 3 && (
                <div className={`ml-4 mr-4 h-1 w-16 sm:w-24 ${
                  step > stepNum 
                    ? 'bg-blue-600' 
                    : 'bg-gray-200 dark:bg-gray-700'
                }`} />
              )}
            </div>
          ))}
        </div>
      </div>
      
      <Card>
        {/* Step 1: Select System */}
        {step === 1 && (
          <div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
              Step 1: Select System
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Choose the molecular system or dataset you want to simulate
            </p>
            
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {systems.map((sys) => (
                <div
                  key={sys.id}
                  className={`rounded-lg border p-4 cursor-pointer transition-colors ${
                    system === sys.id
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 hover:border-gray-300 dark:border-gray-700 dark:hover:border-gray-600'
                  }`}
                  onClick={() => setSystem(sys.id)}
                >
                  <h3 className="font-medium text-gray-900 dark:text-white">
                    {sys.name}
                  </h3>
                  <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                    {sys.description}
                  </p>
                </div>
              ))}
            </div>
            
            <div className="mt-8 flex justify-between">
              <div></div> {/* Empty div for spacing */}
              <Button
                variant="primary"
                onClick={() => setStep(2)}
                disabled={!system}
                aria-label="Continue to configuration step"
              >
                Continue
              </Button>
            </div>
          </div>
        )}
        
        {/* Step 2: Configure */}
        {step === 2 && (
          <div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
              Step 2: Configure Simulation
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Select computational backend and parameters
            </p>
            
            <div className="space-y-6">
              {/* Backend Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Computational Backend
                </label>
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                  {(['classical', 'quantum', 'hybrid'] as const).map((type) => (
                    <div
                      key={type}
                      className={`rounded-lg border p-4 cursor-pointer transition-colors ${
                        backend === type
                          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                          : 'border-gray-200 hover:border-gray-300 dark:border-gray-700 dark:hover:border-gray-600'
                      }`}
                      onClick={() => setBackend(type)}
                    >
                      <h3 className="font-medium text-gray-900 dark:text-white capitalize">
                        {type}
                      </h3>
                      <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                        {backendDescriptions[type]}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Quantum-specific parameters */}
              {backend !== 'classical' && (
                <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                  <div>
                    <label htmlFor="qubits" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Number of Qubits
                    </label>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                      More qubits allow larger systems but require more resources
                    </p>
                    <input
                      type="range"
                      id="qubits"
                      min="1"
                      max="64"
                      value={qubits}
                      onChange={(e) => setQubits(parseInt(e.target.value))}
                      className="w-full"
                    />
                    <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
                      <span>1</span>
                      <span className="font-medium text-gray-900 dark:text-white">{qubits} qubits</span>
                      <span>64</span>
                    </div>
                  </div>
                  
                  <div>
                    <label htmlFor="shots" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Number of Shots
                    </label>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                      More shots improve accuracy but increase computation time
                    </p>
                    <input
                      type="range"
                      id="shots"
                      min="128"
                      max="8192"
                      step="128"
                      value={shots}
                      onChange={(e) => setShots(parseInt(e.target.value))}
                      className="w-full"
                    />
                    <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
                      <span>128</span>
                      <span className="font-medium text-gray-900 dark:text-white">{shots.toLocaleString()} shots</span>
                      <span>8K</span>
                    </div>
                  </div>
                </div>
              )}
              
              {/* Optimizer Selection */}
              <div>
                <label htmlFor="optimizer" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Optimization Algorithm
                </label>
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                  Algorithm used to minimize the energy function
                </p>
                <select
                  id="optimizer"
                  value={optimizer}
                  onChange={(e) => setOptimizer(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
                >
                  <option value="L-BFGS">L-BFGS (Classical)</option>
                  <option value="VQE">VQE (Variational Quantum Eigensolver)</option>
                  <option value="QAOA">QAOA (Quantum Approximate Optimization Algorithm)</option>
                  <option value="ADAPT-VQE">ADAPT-VQE (Adaptive VQE)</option>
                </select>
              </div>
            </div>
            
            <div className="mt-8 flex justify-between">
              <Button
                variant="secondary"
                onClick={() => setStep(1)}
                aria-label="Go back to system selection step"
              >
                Back
              </Button>
              <Button
                variant="primary"
                onClick={() => setStep(3)}
                aria-label="Continue to review step"
              >
                Continue
              </Button>
            </div>
          </div>
        )}
        
        {/* Step 3: Review & Start */}
        {step === 3 && (
          <div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
              Step 3: Review & Start Simulation
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Review your simulation configuration and start the job
            </p>
            
            <div className="space-y-6">
              <Card>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                  Simulation Summary
                </h3>
                
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div>
                    <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                      System
                    </h4>
                    <p className="mt-1 text-sm text-gray-900 dark:text-white">
                      {systems.find(s => s.id === system)?.name}
                    </p>
                  </div>
                  
                  <div>
                    <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                      Backend
                    </h4>
                    <p className="mt-1 text-sm text-gray-900 dark:text-white capitalize">
                      {backend}
                    </p>
                  </div>
                  
                  {backend !== 'classical' && (
                    <>
                      <div>
                        <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                          Qubits
                        </h4>
                        <p className="mt-1 text-sm text-gray-900 dark:text-white">
                          {qubits}
                        </p>
                      </div>
                      
                      <div>
                        <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                          Shots
                        </h4>
                        <p className="mt-1 text-sm text-gray-900 dark:text-white">
                          {shots.toLocaleString()}
                        </p>
                      </div>
                    </>
                  )}
                  
                  <div>
                    <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                      Optimizer
                    </h4>
                    <p className="mt-1 text-sm text-gray-900 dark:text-white">
                      {optimizer}
                    </p>
                  </div>
                </div>
              </Card>
              
              <div className="rounded-lg bg-blue-50 p-4 dark:bg-blue-900/20">
                <h3 className="font-medium text-blue-800 dark:text-blue-200">
                  What happens next?
                </h3>
                <p className="mt-1 text-sm text-blue-700 dark:text-blue-300">
                  When you start the simulation, it will be added to the job queue. 
                  You can monitor its progress from the simulations list page. 
                  {backend !== 'classical' && ' Quantum simulations may take several minutes to complete.'}
                </p>
              </div>
            </div>
            
            <div className="mt-8 flex justify-between">
              <Button
                variant="secondary"
                onClick={() => setStep(2)}
                aria-label="Go back to configuration step"
              >
                Back
              </Button>
              <Button
                variant="primary"
                onClick={handleSubmit}
                disabled={loading}
                aria-label="Start simulation"
              >
                {loading ? (
                  <span className="flex items-center">
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Starting...
                  </span>
                ) : (
                  'Start Simulation'
                )}
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};

export default NewSimulationPage;
