/*
Purpose: 
Description: 
Exports: 
Notes: Add a short usage example and expected props/return types.
*/

import React, { useState } from 'react'
import JobForm from '../components/JobForm'
import JobList from '../components/JobList'

type DashboardProps = {
  onViewJob?: (jobId: string) => void
}

const Dashboard: React.FC<DashboardProps> = ({ onViewJob }) => {
  const [jobs, setJobs] = useState<any[]>([])

  const localHandleViewJob = (jobId: string) => {
    // Fallback navigation behavior if parent doesn't provide a handler
    console.log('View job (local):', jobId)
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                  QUANTUM_FORGE
                </h1>
              </div>
            </div>
            <nav className="flex space-x-8">
              <a href="#" className="text-blue-600 dark:text-blue-400 font-medium">
                Dashboard
              </a>
              <a href="#" className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300">
                Documentation
              </a>
              <a href="#" className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300">
                About
              </a>
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - Job Form */}
          <div>
            <JobForm />
          </div>

          {/* Right Column - Job List */}
          <div>
            <JobList onViewJob={onViewJob || localHandleViewJob} />
          </div>
        </div>
      </main>
    </div>
  )
}

export default Dashboard