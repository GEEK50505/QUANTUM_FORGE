// NOTE (permanent): This file contains educational notes for non-coders.
// Do not remove comments unless explicitly requested in a written instruction.
// These notes explain purpose, props, and data contract shapes.
//
// Module Purpose: KPI overview cards for the Quantum Forge dashboard
// What this file renders: Key performance indicators showing job statistics
// How it fits into the Quantum Forge app: Provides at-a-glance system status
// Author: Qwen 3 Coder — Scaffold Stage

import React from 'react';
import Card from '../../components/ui/Card';

/**
 * Overview Cards Component
 * 
 * Displays key performance indicators for the quantum simulation system.
 * Shows total jobs, running jobs, failed jobs, and last run energy delta.
 * 
 * For non-coders: These cards show you the current status of your simulation system.
 * - Total Jobs: How many simulations you've run
 * - Running: How many simulations are currently processing
 * - Failed: How many simulations had errors
 * - Last Run Energy Delta: The energy difference from your last simulation
 *   (lower energy usually means a better result in quantum chemistry)
 */
const OverviewCards: React.FC = () => {
  // Mock data - in a real app this would come from an API
  const kpiData = {
    totalJobs: 24,
    runningJobs: 3,
    failedJobs: 2,
    lastEnergyDelta: -12.45
  };

  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
      {/* Total Jobs Card */}
      <Card>
        <div className="flex items-center">
          <div className="p-3 rounded-full bg-blue-100 text-blue-600">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <div className="ml-4">
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Jobs</h3>
            <p className="text-2xl font-semibold text-gray-900 dark:text-white">{kpiData.totalJobs}</p>
          </div>
        </div>
      </Card>

      {/* Running Jobs Card */}
      <Card>
        <div className="flex items-center">
          <div className="p-3 rounded-full bg-yellow-100 text-yellow-600">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </div>
          <div className="ml-4">
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Running</h3>
            <p className="text-2xl font-semibold text-gray-900 dark:text-white">{kpiData.runningJobs}</p>
          </div>
        </div>
      </Card>

      {/* Failed Jobs Card */}
      <Card>
        <div className="flex items-center">
          <div className="p-3 rounded-full bg-red-100 text-red-600">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div className="ml-4">
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Failed</h3>
            <p className="text-2xl font-semibold text-gray-900 dark:text-white">{kpiData.failedJobs}</p>
          </div>
        </div>
      </Card>

      {/* Last Energy Delta Card */}
      <Card>
        <div className="flex items-center">
          <div className="p-3 rounded-full bg-green-100 text-green-600">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </div>
          <div className="ml-4">
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Last Run Energy Δ</h3>
            <p className="text-2xl font-semibold text-gray-900 dark:text-white">
              {kpiData.lastEnergyDelta > 0 ? '+' : ''}{kpiData.lastEnergyDelta} Ha
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default OverviewCards;
