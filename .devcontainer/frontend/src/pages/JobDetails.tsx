/*
Purpose: 
Description: 
Exports: 
Notes: Add a short usage example and expected props/return types.
*/

import React, { useState, useEffect } from 'react'
import { FiArrowLeft, FiRefreshCw, FiTrash } from 'react-icons/fi'
import MoleculeViewer from '../components/MoleculeViewer'
import ResultsViewer from '../components/ResultsViewer'
import { JobResponse } from '../types'
import { getJobStatus, deleteJob } from '../api/client'

interface JobDetailsProps {
  jobId: string
  onBack: () => void
  onDelete: (jobId: string) => void
}

const JobDetails: React.FC<JobDetailsProps> = ({ jobId, onBack, onDelete }) => {
  const [job, setJob] = useState<JobResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchJob = async () => {
    try {
      setLoading(true)
      const data = await getJobStatus(jobId)
      setJob(data)
      setError('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch job details')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (jobId) {
      fetchJob()

      // Auto-refresh if job is still running
      const interval = setInterval(() => {
        if (job?.status === 'running' || job?.status === 'queued') {
          fetchJob()
        }
      }, 2000)

      return () => clearInterval(interval)
    }
  }, [jobId, job?.status])

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this job?')) {
      try {
        await deleteJob(jobId)
        onDelete(jobId)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to delete job')
      }
    }
  }

  const handleResubmit = () => {
    // Resubmit functionality would be implemented here
    alert('Resubmit functionality would be implemented here')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex justify-center items-center h-64">
            <div className="text-center">
              <FiRefreshCw className="animate-spin h-8 w-8 text-blue-500 mx-auto" />
              <p className="mt-2 text-gray-600 dark:text-gray-400">Loading job details...</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
                  Error loading job
                </h3>
                <div className="mt-2 text-sm text-red-700 dark:text-red-300">
                  <p>{error}</p>
                </div>
                <div className="mt-4">
                  <button
                    onClick={fetchJob}
                    className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                  >
                    Retry
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!job) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center py-12">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">Job not found</h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              The requested job could not be found.
            </p>
            <div className="mt-6">
              <button
                onClick={onBack}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <FiArrowLeft className="w-4 h-4 mr-2" />
                Back to Dashboard
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <button
              onClick={onBack}
              className="inline-flex items-center text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300"
            >
              <FiArrowLeft className="w-4 h-4 mr-1" />
              Back to Dashboard
            </button>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
              Job Details: {job.molecule_name || job.job_id}
            </h1>
          </div>

          <div className="flex space-x-2">
            <button
              onClick={handleResubmit}
              className="inline-flex items-center px-3 py-1.5 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Resubmit
            </button>
            <button
              onClick={handleDelete}
              className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-red-700 dark:text-red-300 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-800/30 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
            >
              <FiTrash className="w-4 h-4 mr-1" />
              Delete
            </button>
          </div>
        </div>

        {/* Job Status */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-8">
          <div className="flex flex-wrap items-center justify-between">
            <div>
              <h2 className="text-lg font-medium text-gray-900 dark:text-white">
                {job.molecule_name || 'Unnamed Molecule'}
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Job ID: {job.job_id}
              </p>
            </div>

            <div className="mt-4 sm:mt-0">
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${job.status === 'queued'
                  ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300'
                  : job.status === 'running'
                    ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300'
                    : job.status === 'completed'
                      ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                      : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                }`}>
                {job.status}
              </span>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-gray-500 dark:text-gray-400">Created</p>
              <p className="text-gray-900 dark:text-white">
                {new Date(job.created_at).toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-gray-500 dark:text-gray-400">Last Updated</p>
              <p className="text-gray-900 dark:text-white">
                {new Date(job.updated_at).toLocaleString()}
              </p>
            </div>
            {job.tags && job.tags.length > 0 && (
              <div>
                <p className="text-gray-500 dark:text-gray-400">Tags</p>
                <div className="flex flex-wrap gap-1 mt-1">
                  {job.tags.map((tag, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Molecule Viewer */}
        {job.xyz_content && (
          <div className="mb-8">
            <MoleculeViewer
              xyz_content={job.xyz_content}
              optimized_geometry={job.results?.properties?.optimized_geometry}
            />
          </div>
        )}

        {/* Results */}
        {job.status === 'completed' && job.results && (
          <div className="mb-8">
            <ResultsViewer jobId={job.job_id} />
          </div>
        )}

        {/* Error Message */}
        {job.status === 'failed' && job.error_message && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 mb-8">
            <h3 className="text-lg font-medium text-red-800 dark:text-red-200 mb-2">
              Calculation Failed
            </h3>
            <p className="text-red-700 dark:text-red-300">
              {job.error_message}
            </p>
          </div>
        )}

        {/* Logs */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Logs</h3>
          <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 font-mono text-sm">
            <p className="text-gray-600 dark:text-gray-400">
              Log output would be displayed here...
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default JobDetails