// NOTE (permanent): This file contains educational notes for non-coders.
// Do not remove comments unless explicitly requested in a written instruction.
// These notes explain purpose, props, and data contract shapes.
//
// Module Purpose: Simulation jobs list page
// What this file renders: Table of all simulation jobs with filtering options
// How it fits into the Quantum Forge app: Main interface for viewing and managing
// simulation jobs
// Author: Qwen 3 Coder — Scaffold Stage

import React, { useState, useEffect } from 'react';
import { get } from '../../services/api';
import { Simulation } from '../../hooks/useMockApi';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Table from '../../components/ui/table';
import { SIMULATION_STATUS } from '../../utils/constants';

/**
 * Simulations List Page
 * 
 * Displays a table of all simulation jobs with filtering and sorting capabilities.
 * Users can view job details, status, and create new simulations from here.
 * 
 * For non-coders: This page shows all your simulation jobs in a table format.
 * You can see which jobs are running, completed, or failed, and when they were created.
 * The "Create New Job" button lets you start a new simulation.
 */
const SimulationsListPage: React.FC = () => {
  const [simulations, setSimulations] = useState<Simulation[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  // Fetch simulations when component mounts
  useEffect(() => {
    fetchSimulations();
  }, []);

  const fetchSimulations = async () => {
    try {
      setLoading(true);
      const response = await get<Simulation[]>('/simulations');
      setSimulations(response.data);
    } catch (error) {
      console.error('Failed to fetch simulations:', error);
      // In a real app, we'd show an error message to the user
    } finally {
      setLoading(false);
    }
  };

  // Filter simulations based on selected filter
  const filteredSimulations = filter === 'all' 
    ? simulations 
    : simulations.filter(sim => sim.status === filter);

  // Format date for display
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  // Get status badge class based on status
  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case SIMULATION_STATUS.QUEUED:
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100';
      case SIMULATION_STATUS.RUNNING:
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100';
      case SIMULATION_STATUS.COMPLETED:
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100';
      case SIMULATION_STATUS.FAILED:
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100';
      case SIMULATION_STATUS.CANCELLED:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-100';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-100';
    }
  };

  return (
    <div className="p-4 md:p-6">
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Simulation Jobs
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            View and manage all simulation jobs
          </p>
        </div>
        <div className="mt-4 sm:mt-0">
          <Button 
            variant="primary"
            onClick={() => window.location.hash = '/sims/new'}
            aria-label="Create new simulation job"
          >
            Create New Job
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <div className="flex flex-wrap items-center gap-4">
          <div>
            <label htmlFor="status-filter" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Filter by Status
            </label>
            <select
              id="status-filter"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
            >
              <option value="all">All Statuses</option>
              <option value={SIMULATION_STATUS.QUEUED}>Queued</option>
              <option value={SIMULATION_STATUS.RUNNING}>Running</option>
              <option value={SIMULATION_STATUS.COMPLETED}>Completed</option>
              <option value={SIMULATION_STATUS.FAILED}>Failed</option>
              <option value={SIMULATION_STATUS.CANCELLED}>Cancelled</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Simulations Table */}
      <Card>
        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <div className="text-center">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
              <p className="mt-2 text-gray-600 dark:text-gray-400">Loading simulations...</p>
            </div>
          </div>
        ) : (
          <Table>
            <Table.Head>
              <Table.Row>
                <Table.HeaderCell>ID</Table.HeaderCell>
                <Table.HeaderCell>Name</Table.HeaderCell>
                <Table.HeaderCell>Type</Table.HeaderCell>
                <Table.HeaderCell>Status</Table.HeaderCell>
                <Table.HeaderCell>Created</Table.HeaderCell>
                <Table.HeaderCell>Duration</Table.HeaderCell>
                <Table.HeaderCell>Energy</Table.HeaderCell>
              </Table.Row>
            </Table.Head>
            <Table.Body>
              {filteredSimulations.length === 0 ? (
                <Table.Row>
                  <Table.Cell colSpan={7} className="text-center py-8">
                    <p className="text-gray-500 dark:text-gray-400">
                      No simulations found matching your criteria
                    </p>
                  </Table.Cell>
                </Table.Row>
              ) : (
                filteredSimulations.map((simulation) => (
                  <Table.Row 
                    key={simulation.id} 
                    className="hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer"
                    onClick={() => window.location.hash = `/sims/job/${simulation.id}`}
                  >
                    <Table.Cell className="font-mono text-sm">{simulation.id}</Table.Cell>
                    <Table.Cell className="font-medium">{simulation.name}</Table.Cell>
                    <Table.Cell>
                      <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-800 dark:bg-gray-700 dark:text-gray-200">
                        {simulation.type}
                      </span>
                    </Table.Cell>
                    <Table.Cell>
                      <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${getStatusBadgeClass(simulation.status)}`}>
                        {simulation.status}
                      </span>
                    </Table.Cell>
                    <Table.Cell>{formatDate(simulation.createdAt)}</Table.Cell>
                    <Table.Cell>
                      {simulation.duration ? `${simulation.duration}s` : '-'}
                    </Table.Cell>
                    <Table.Cell>
                      {simulation.energy !== undefined ? `${simulation.energy.toFixed(3)} Ha` : '-'}
                    </Table.Cell>
                  </Table.Row>
                ))
              )}
            </Table.Body>
          </Table>
        )}
      </Card>
    </div>
  );
};

export default SimulationsListPage;
