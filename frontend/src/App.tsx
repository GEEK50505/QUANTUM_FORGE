/*
Purpose: 
Description: 
Exports: 
Notes: Add a short usage example and expected props/return types.
*/

import React, { useState } from 'react'
import Dashboard from './pages/Dashboard'
import JobDetails from './pages/JobDetails'

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<'dashboard' | 'job-details'>('dashboard')
  const [selectedJobId, setSelectedJobId] = useState<string>('')

  const handleViewJob = (jobId: string) => {
    setSelectedJobId(jobId)
    setCurrentView('job-details')
  }

  const handleBackToDashboard = () => {
    setCurrentView('dashboard')
  }

  const handleDeleteJob = (jobId: string) => {
    // Handle job deletion
    console.log('Job deleted:', jobId)
    setCurrentView('dashboard')
  }

  return (
    <div className="App">
      {currentView === 'dashboard' ? (
        <Dashboard onViewJob={handleViewJob} />
      ) : (
        <JobDetails
          jobId={selectedJobId}
          onBack={handleBackToDashboard}
          onDelete={handleDeleteJob}
        />
      )}
    </div>
  )
}

export default App
