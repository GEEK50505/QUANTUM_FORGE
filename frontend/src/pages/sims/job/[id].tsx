// NOTE (permanent): This file contains educational notes for non-coders.
// Do not remove comments unless explicitly requested in a written instruction.
// These notes explain purpose, props, and data contract shapes.
//
// Module Purpose: Simulation job detail page
// What this file renders: Detailed view of a single simulation job with logs,
// results, and visualizations
// How it fits into the Quantum Forge app: Detailed inspection interface for
// individual simulation jobs
// Author: Qwen 3 Coder — Scaffold Stage

import React, { useState, useEffect } from 'react';
import { get } from '../../../services/api';
import { Simulation } from '../../../hooks/useMockApi';
import Card from '../../../components/ui/Card';
import Button from '../../../components/ui/Button';
import { Modal } from '../../../components/ui/Modal';

/**
 * Job Detail Page
 * 
 * Displays detailed information about a specific simulation job including
 * metadata, logs, results, and visualizations.
 * 
 * For non-coders: This page shows all the details about a specific simulation
 * job. You can see when it started and finished, what parameters were used,
 * the results, and download artifacts. The tabs let you switch between
 * different types of information.
 */
const JobDetailPage: React.FC = () => {
  // In a real app, we'd get the job ID from the URL params
  // For now, we'll use a placeholder
  const jobId = 'sim-001';
  
  const [job, setJob] = useState<Simulation | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'logs' | 'results' | 'visualizations'>('logs');
  const [showDownloadModal, setShowDownloadModal] = useState(false);

  // Fetch job details when component mounts
  useEffect(() => {
    fetchJobDetails();
  }, []);

  const fetchJobDetails = async () => {
    try {
      setLoading(true);
      const response = await get<Simulation>(`/simulations/${jobId}`);
      setJob(response.data);
    } catch (error) {
      console.error('Failed to fetch job details:', error);
      // In a real app, we'd show an error message to the user
    } finally {
      setLoading(false);
    }
  };

  // Format date for display
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  // Mock log data
  const mockLogs = [
    '[2025-10-25 10:30:00] Job sim-001 created',
    '[2025-10-25 10:31:00] Job started on quantum backend',
    '[2025-10-25 10:31:05] Initializing qubits...',
    '[2025-10-25 10:31:15] Running VQE optimization cycle 1',
    '[2025-10-25 10:32:30] Running VQE optimization cycle 2',
    '[2025-10-25 10:33:45] Running VQE optimization cycle 3',
    '[2025-10-25 10:35:00] Optimization complete',
    '[2025-10-25 10:35:05] Job completed successfully'
  ];

  // Mock results data
  const mockResults = {
    "molecule": "H2",
    "basis": "sto-3g",
    "qubits": 4,
    "shots": 1024,
    "optimizer": "VQE",
    "ground_state_energy": -1.137,
    "excited_state_energies": [-0.821, -0.543],
    "runtime_seconds": 240,
    "convergence": true
  };

  // Handle download artifact
  const handleDownloadArtifact = () => {
    // In a real app, this would download the actual artifact
    // For now, we'll just show a modal
    setShowDownloadModal(true);
  };

  if (loading) {
    return (
      <div className="p-4 md:p-6">
        <div className="flex h-64 items-center justify-center">
          <div className="text-center">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
            <p className="mt-2 text-gray-600 dark:text-gray-400">Loading job details...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="p-4 md:p-6">
        <Card>
          <div className="text-center py-12">
            <h2 className="text-xl font-medium text-gray-900 dark:text-white mb-2">Job Not Found</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              The requested simulation job could not be found.
            </p>
            <Button 
              variant="primary"
              onClick={() => window.location.hash = '/sims'}
            >
              Back to Simulations
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6">
      <div className="mb-6">
        <Button 
          variant="secondary"
          onClick={() => window.location.hash = '/sims'}
          className="mb-4"
        >
          ← Back to Simulations
        </Button>
        
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Job Details: {job.name}
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              ID: {job.id}
            </p>
          </div>
          <div className="mt-4 sm:mt-0">
            <Button 
              variant="primary"
              onClick={handleDownloadArtifact}
              aria-label="Download job artifact"
            >
              Download Artifact
            </Button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Job Metadata */}
        <div className="lg:col-span-1">
          <Card>
            <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Job Metadata</h2>
            
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Status</h3>
           <p className="mt-1 text-sm font-medium capitalize" 
             style={{ color: job.status === 'COMPLETED' ? '#10B981' : 
                   job.status === 'RUNNING' ? '#3B82F6' : 
                   job.status === 'FAILED' ? '#EF4444' : '#F59E0B' }}>
                  {job.status}
                </p>
              </div>
              
              <div>
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Backend Type</h3>
                <p className="mt-1 text-sm font-medium text-gray-900 dark:text-white capitalize">
                  {job.type}
                </p>
              </div>
              
              <div>
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Created</h3>
                <p className="mt-1 text-sm text-gray-900 dark:text-white">
                  {formatDate(job.createdAt)}
                </p>
              </div>
              
              {job.startedAt && (
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Started</h3>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white">
                    {formatDate(job.startedAt)}
                  </p>
                </div>
              )}
              
              {job.completedAt && (
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Completed</h3>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white">
                    {formatDate(job.completedAt)}
                  </p>
                </div>
              )}
              
              {job.duration && (
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Duration</h3>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white">
                    {job.duration} seconds
                  </p>
                </div>
              )}
              
              {job.qubits !== undefined && job.qubits > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Qubits</h3>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white">
                    {job.qubits}
                  </p>
                </div>
              )}
              
              {job.shots !== undefined && job.shots > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Shots</h3>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white">
                    {job.shots.toLocaleString()}
                  </p>
                </div>
              )}
              
              {job.energy !== undefined && (
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Energy Result</h3>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white">
                    {job.energy.toFixed(6)} Ha
                  </p>
                </div>
              )}
            </div>
          </Card>
        </div>
        
        {/* Tabbed Content Area */}
        <div className="lg:col-span-2">
          <Card>
            {/* Tabs */}
            <div className="border-b border-gray-200 dark:border-gray-700">
              <nav className="-mb-px flex space-x-8">
                <button
                  onClick={() => setActiveTab('logs')}
                  className={`whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium ${
                    activeTab === 'logs'
                      ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                  }`}
                >
                  Logs
                </button>
                <button
                  onClick={() => setActiveTab('results')}
                  className={`whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium ${
                    activeTab === 'results'
                      ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                  }`}
                >
                  Results
                </button>
                <button
                  onClick={() => setActiveTab('visualizations')}
                  className={`whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium ${
                    activeTab === 'visualizations'
                      ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                  }`}
                >
                  Visualizations
                </button>
              </nav>
            </div>
            
            {/* Tab Content */}
            <div className="mt-6">
              {activeTab === 'logs' && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Execution Logs</h3>
                  <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 font-mono text-sm">
                    <div className="space-y-1">
                      {mockLogs.map((log, index) => (
                        <div key={index} className="text-gray-800 dark:text-gray-200">
                          {log}
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
                    <p>
                      These logs show the execution progress of your simulation job. 
                      In a production environment, these would be real-time logs from the backend.
                    </p>
                  </div>
                </div>
              )}
              
              {activeTab === 'results' && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Job Results</h3>
                  <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                    <pre className="text-sm text-gray-800 dark:text-gray-200 overflow-x-auto">
                      {JSON.stringify(mockResults, null, 2)}
                    </pre>
                  </div>
                  <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
                    <p>
                      This JSON contains the detailed results of your simulation. 
                      In a production environment, this would be the actual computed data 
                      that can be used for further analysis.
                    </p>
                  </div>
                </div>
              )}
              
              {activeTab === 'visualizations' && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Energy Convergence</h3>
                  <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 h-64 flex items-center justify-center">
                    <div className="text-center">
                      <div className="bg-gray-200 border-2 border-dashed rounded-xl w-16 h-16 mx-auto mb-4 dark:bg-gray-700" />
                      <p className="text-gray-600 dark:text-gray-400">
                        Energy convergence plot would appear here
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                        (Placeholder for matplotlib-like visualization)
                      </p>
                    </div>
                  </div>
                  <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
                    <p>
                      This visualization would show the energy convergence during the 
                      optimization process. In a production environment, this would be 
                      a real plot generated from the simulation data.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
      
      {/* Download Modal */}
      <Modal
        isOpen={showDownloadModal}
        onClose={() => setShowDownloadModal(false)}
        title="Download Artifact"
      >
        <div className="space-y-4">
          <p className="text-gray-700 dark:text-gray-300">
            In a production environment, this would download the actual simulation artifact.
          </p>
          <div className="bg-blue-50 dark:bg-blue-900/30 rounded-lg p-4">
            <h4 className="font-medium text-blue-800 dark:text-blue-200 mb-2">Artifact Information</h4>
            <ul className="text-sm text-blue-700 dark:text-blue-300 space-y-1">
              <li>• File: {job.id}-results.json</li>
              <li>• Size: 2.4 KB</li>
              <li>• Format: JSON</li>
              <li>• Contains: Simulation results and metadata</li>
            </ul>
          </div>
          <div className="flex justify-end space-x-3">
            <Button
              variant="secondary"
              onClick={() => setShowDownloadModal(false)}
            >
              Close
            </Button>
            <Button
              variant="primary"
              onClick={() => {
                // In a real app, this would trigger the actual download
                alert('In a real application, this would download the artifact file.');
                setShowDownloadModal(false);
              }}
            >
              Download
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default JobDetailPage;
