// NOTE (permanent): This file contains educational notes for non-coders.
// Do not remove comments unless explicitly requested in a written instruction.
// These notes explain purpose, props, and data contract shapes.
//
// Module Purpose: Experiments dashboard page
// What this file renders: Interface for comparing simulation results and experiments
// How it fits into the Quantum Forge app: Provides experiment comparison and analysis
// Author: Qwen 3 Coder — Scaffold Stage

import React, { useState } from 'react';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Table from '../../components/ui/table';

/**
 * Experiments Page
 * 
 * Dashboard for comparing multiple simulation jobs and analyzing results.
 * Provides side-by-side comparison and visualization capabilities.
 * 
 * For non-coders: This page helps you compare different simulation runs to see
 * which methods work best. You can select multiple jobs and compare their results
 * side-by-side, which is useful for validating your computational methods.
 */
const ExperimentsPage: React.FC = () => {
  const [selectedJobs, setSelectedJobs] = useState<string[]>([]);
  
  // Mock experiment data
  const experiments = [
    {
      id: 'exp-001',
      name: 'H2 Ground State Comparison',
      jobs: ['sim-001', 'sim-002'],
      createdAt: '2025-10-25',
      description: 'Compare VQE and classical methods for H2 ground state'
    },
    {
      id: 'exp-002',
      name: 'LiH Dissociation Curve',
      jobs: ['sim-003', 'sim-004'],
      createdAt: '2025-10-26',
      description: 'Dissociation energy curve for LiH molecule'
    }
  ];
  
  // Mock job data for comparison
  const jobs = [
    {
      id: 'sim-001',
      name: 'H2 Ground State VQE',
      type: 'quantum',
      status: 'completed',
      energy: -1.137,
      runtime: 240,
      qubits: 4
    },
    {
      id: 'sim-002',
      name: 'H2 Ground State Classical',
      type: 'classical',
      status: 'completed',
      energy: -1.125,
      runtime: 15,
      qubits: 0
    },
    {
      id: 'sim-003',
      name: 'LiH Dissociation Point 1',
      type: 'hybrid',
      status: 'completed',
      energy: -8.012,
      runtime: 180,
      qubits: 12
    },
    {
      id: 'sim-004',
      name: 'LiH Dissociation Point 2',
      type: 'hybrid',
      status: 'completed',
      energy: -7.985,
      runtime: 210,
      qubits: 12
    }
  ];

  // Toggle job selection
  const toggleJobSelection = (jobId: string) => {
    if (selectedJobs.includes(jobId)) {
      setSelectedJobs(selectedJobs.filter(id => id !== jobId));
    } else {
      setSelectedJobs([...selectedJobs, jobId]);
    }
  };

  // Select all jobs
  const selectAllJobs = () => {
    setSelectedJobs(jobs.map(job => job.id));
  };

  // Clear all selections
  const clearSelections = () => {
    setSelectedJobs([]);
  };

  // Get selected jobs data
  const selectedJobData = jobs.filter(job => selectedJobs.includes(job.id));

  return (
    <div className="p-4 md:p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Experiments
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Compare simulation results and analyze performance
        </p>
      </div>

      {/* Experiment Tabs */}
      <div className="mb-6">
        <div className="border-b border-gray-200 dark:border-gray-700">
          <nav className="-mb-px flex space-x-8">
            <button className="whitespace-nowrap border-b-2 border-blue-500 py-4 px-1 text-sm font-medium text-blue-600 dark:text-blue-400">
              Active Experiments
            </button>
            <button className="whitespace-nowrap border-b-2 border-transparent py-4 px-1 text-sm font-medium text-gray-500 hover:border-gray-300 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300">
              Saved Comparisons
            </button>
          </nav>
        </div>
      </div>

      {/* Job Selection Controls */}
      <Card className="mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-lg font-medium text-gray-900 dark:text-white">
              Select Jobs for Comparison
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {selectedJobs.length} job(s) selected
            </p>
          </div>
          <div className="mt-4 flex space-x-3 sm:mt-0">
            <Button
              variant="secondary"
              onClick={selectAllJobs}
              disabled={selectedJobs.length === jobs.length}
            >
              Select All
            </Button>
            <Button
              variant="secondary"
              onClick={clearSelections}
              disabled={selectedJobs.length === 0}
            >
              Clear
            </Button>
          </div>
        </div>
      </Card>

      {/* Jobs Table */}
      <Card className="mb-6">
        <Table>
          <Table.Head>
            <Table.Row>
              <Table.HeaderCell>Select</Table.HeaderCell>
              <Table.HeaderCell>Job ID</Table.HeaderCell>
              <Table.HeaderCell>Name</Table.HeaderCell>
              <Table.HeaderCell>Type</Table.HeaderCell>
              <Table.HeaderCell>Status</Table.HeaderCell>
              <Table.HeaderCell>Energy (Ha)</Table.HeaderCell>
              <Table.HeaderCell>Runtime (s)</Table.HeaderCell>
              <Table.HeaderCell>Qubits</Table.HeaderCell>
            </Table.Row>
          </Table.Head>
          <Table.Body>
            {jobs.map((job) => (
              <Table.Row 
                key={job.id} 
                className={selectedJobs.includes(job.id) ? 'bg-blue-50 dark:bg-blue-900/20' : ''}
              >
                <Table.Cell>
                  <input
                    type="checkbox"
                    checked={selectedJobs.includes(job.id)}
                    onChange={() => toggleJobSelection(job.id)}
                    className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:focus:ring-blue-600"
                  />
                </Table.Cell>
                <Table.Cell className="font-mono text-sm">{job.id}</Table.Cell>
                <Table.Cell className="font-medium">{job.name}</Table.Cell>
                <Table.Cell>
                  <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    job.type === 'quantum' 
                      ? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-100'
                      : job.type === 'hybrid'
                      ? 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-100'
                      : 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100'
                  }`}>
                    {job.type}
                  </span>
                </Table.Cell>
                <Table.Cell>
                  <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800 dark:bg-green-900 dark:text-green-100">
                    {job.status}
                  </span>
                </Table.Cell>
                <Table.Cell>
                  {job.energy !== undefined ? job.energy.toFixed(6) : '-'}
                </Table.Cell>
                <Table.Cell>
                  {job.runtime !== undefined ? job.runtime : '-'}
                </Table.Cell>
                <Table.Cell>
                  {job.qubits !== undefined ? job.qubits : '-'}
                </Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table>
      </Card>

      {/* Comparison Results */}
      {selectedJobData.length > 0 && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Energy Comparison */}
          <Card>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Energy Comparison
            </h3>
            <div className="space-y-4">
              {selectedJobData.map((job) => (
                <div key={job.id} className="flex items-center justify-between">
                  <div>
                    <div className="font-medium text-gray-900 dark:text-white">
                      {job.name}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      {job.id}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium text-gray-900 dark:text-white">
                      {job.energy !== undefined ? job.energy.toFixed(6) : '-'} Ha
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      {job.type}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            {selectedJobData.length >= 2 && (
              <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <div className="flex justify-between">
                  <span className="font-medium text-gray-900 dark:text-white">
                    Energy Difference
                  </span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {Math.abs(selectedJobData[0].energy! - selectedJobData[1].energy!).toFixed(6)} Ha
                  </span>
                </div>
                <div className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                  Between {selectedJobData[0].name} and {selectedJobData[1].name}
                </div>
              </div>
            )}
          </Card>

          {/* Performance Comparison */}
          <Card>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Performance Comparison
            </h3>
            <div className="space-y-4">
              {selectedJobData.map((job) => (
                <div key={job.id} className="flex items-center justify-between">
                  <div>
                    <div className="font-medium text-gray-900 dark:text-white">
                      {job.name}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium text-gray-900 dark:text-white">
                      {job.runtime !== undefined ? job.runtime : '-'}s
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      {job.qubits !== undefined ? `${job.qubits} qubits` : 'Classical'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            {selectedJobData.length >= 2 && (
              <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <div className="flex justify-between">
                  <span className="font-medium text-gray-900 dark:text-white">
                    Speedup Factor
                  </span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {Math.max(selectedJobData[0].runtime!, selectedJobData[1].runtime!) / 
                     Math.min(selectedJobData[0].runtime!, selectedJobData[1].runtime!)}x
                  </span>
                </div>
                <div className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                  {selectedJobData[0].runtime! > selectedJobData[1].runtime! 
                    ? `${selectedJobData[1].name} is faster`
                    : `${selectedJobData[0].name} is faster`}
                </div>
              </div>
            )}
          </Card>
        </div>
      )}

      {/* Visualization Placeholder */}
      <Card className="mt-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          Energy Convergence Visualization
        </h3>
        <div className="h-64 flex items-center justify-center bg-gray-50 dark:bg-gray-800 rounded-lg">
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
      </Card>
    </div>
  );
};

export default ExperimentsPage;
