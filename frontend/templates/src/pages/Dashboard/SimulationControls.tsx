// NOTE (permanent): This file contains educational notes for non-coders.
// Do not remove comments unless explicitly requested in a written instruction.
// These notes explain purpose, props, and data contract shapes.
//
// Module Purpose: Simulation controls for the Quantum Forge dashboard
// What this file renders: Controls to start demo simulations with different backends
// How it fits into the Quantum Forge app: Provides quick access to run simulations
// from the main dashboard
// Author: Qwen 3 Coder — Scaffold Stage

import React, { useState } from 'react';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';

/**
 * Simulation Controls Component
 * 
 * Provides controls to start demo simulations with different backend options.
 * Users can select between classical, quantum-stub, or hybrid simulation modes.
 * 
 * For non-coders: This is the main control panel for running simulations.
 * - Classical: Traditional computer simulation (fast but less accurate for quantum systems)
 * - Quantum-stub: Placeholder for real quantum computer (simulated for now)
 * - Hybrid: Combination of classical and quantum methods (best of both worlds)
 * 
 * The big "Run Demo" button starts a simulation with your selected method.
 */
const SimulationControls: React.FC = () => {
  const [selectedBackend, setSelectedBackend] = useState<'classical' | 'quantum-stub' | 'hybrid'>('classical');
  const [isRunning, setIsRunning] = useState(false);

  const handleRunSimulation = () => {
    setIsRunning(true);
    
    // In a real app, this would call the API to start a simulation
    // For now, we'll just simulate with a timeout
    setTimeout(() => {
      setIsRunning(false);
      alert(`Demo simulation started with ${selectedBackend} backend!`);
    }, 1000);
  };

  return (
    <Card>
      <div className="mb-4">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">Simulation Controls</h2>
        <p className="text-gray-600 dark:text-gray-400">
          Start a demo simulation with different computational backends
        </p>
      </div>
      
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        {/* Backend Selection */}
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Simulation Backend
          </label>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <button
              type="button"
              className={`px-4 py-3 rounded-lg border text-left transition-colors ${
                selectedBackend === 'classical'
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                  : 'border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'
              }`}
              onClick={() => setSelectedBackend('classical')}
              aria-label="Select classical simulation backend"
            >
              <div className="font-medium">Classical</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Fast CPU-based simulation
              </div>
            </button>
            
            <button
              type="button"
              className={`px-4 py-3 rounded-lg border text-left transition-colors ${
                selectedBackend === 'quantum-stub'
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                  : 'border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'
              }`}
              onClick={() => setSelectedBackend('quantum-stub')}
              aria-label="Select quantum stub simulation backend"
            >
              <div className="font-medium">Quantum (Stub)</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Simulated quantum processing
              </div>
            </button>
            
            <button
              type="button"
              className={`px-4 py-3 rounded-lg border text-left transition-colors ${
                selectedBackend === 'hybrid'
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                  : 'border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'
              }`}
              onClick={() => setSelectedBackend('hybrid')}
              aria-label="Select hybrid simulation backend"
            >
              <div className="font-medium">Hybrid</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Classical + Quantum combined
              </div>
            </button>
          </div>
        </div>
        
        {/* Run Button */}
        <div className="flex items-end">
          <Button
            variant="primary"
            onClick={handleRunSimulation}
            disabled={isRunning}
            className="w-full py-3 text-base font-semibold"
            aria-label="Run demo simulation"
          >
            {isRunning ? (
              <span className="flex items-center">
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Running...
              </span>
            ) : (
              `Run Demo (${selectedBackend})`
            )}
          </Button>
        </div>
      </div>
      
      {/* Backend Explanations */}
      <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
        <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-2">Backend Information</h3>
        <div className="text-sm text-gray-600 dark:text-gray-400">
          {selectedBackend === 'classical' && (
            <p>
              Classical simulations use traditional computing methods. They're fast and reliable 
              but may not capture all quantum effects accurately for complex systems.
            </p>
          )}
          {selectedBackend === 'quantum-stub' && (
            <p>
              Quantum simulations use quantum mechanical principles for more accurate modeling 
              of molecular systems. This is currently a stub implementation - in production 
              it would connect to real quantum processors.
            </p>
          )}
          {selectedBackend === 'hybrid' && (
            <p>
              Hybrid simulations combine classical and quantum methods to balance accuracy 
              and computational efficiency. Classical methods handle parts of the calculation 
              while quantum methods focus on the most sensitive components.
            </p>
          )}
        </div>
      </div>
    </Card>
  );
};

export default SimulationControls;
