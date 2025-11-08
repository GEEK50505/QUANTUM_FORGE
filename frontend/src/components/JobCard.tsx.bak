import React from 'react'
import { FiCopy, FiEye, FiTrash, FiLoader, FiCheckCircle, FiXCircle, FiClock } from 'react-icons/fi'
import { JobResponse } from '../types'

interface JobCardProps {
  job: JobResponse
  onViewDetails: (jobId: string) => void
  onDelete: (jobId: string) => void
}

const JobCard: React.FC<JobCardProps> = ({ job, onViewDetails, onDelete }) => {
  const getStatusColor = () => {
    switch (job.status) {
      case 'QUEUED':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300'
      case 'RUNNING':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300'
      case 'COMPLETED':
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
      case 'FAILED':
        return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
    }
  }

  const getStatusIcon = () => {
    switch (job.status) {
      case 'QUEUED':
        return <FiClock className="w-4 h-4" />
      case 'RUNNING':
        return <FiLoader className="w-4 h-4 animate-spin" />
      case 'COMPLETED':
        return <FiCheckCircle className="w-4 h-4" />
      case 'FAILED':
        return <FiXCircle className="w-4 h-4" />
      default:
        return <FiClock className="w-4 h-4" />
    }
  }

  const copyJobId = () => {
    navigator.clipboard.writeText(job.job_id)
  }

  const formatRelativeTime = (iso: string): string => {
    try {
      const date = new Date(iso)
      const now = new Date()
      const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)
      
      if (diffInSeconds < 60) return 'just now'
      if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`
      if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`
      return `${Math.floor(diffInSeconds / 86400)} days ago`
    } catch (error) {
      return 'Unknown time'
    }
  }

  const truncateJobId = (jobId: string): string => {
    if (jobId.length <= 8) return jobId
    return jobId.substring(0, 8) + '...'
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-200">
      <div className="p-5">
        <div className="flex justify-between items-start">
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {job.molecule_name || 'Unnamed Molecule'}
              </h3>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor()}`}>
                {getStatusIcon()}
                <span className="ml-1">{job.status}</span>
              </span>
            </div>
            
            <div className="mt-2 flex items-center">
              <span 
                className="text-sm font-mono text-gray-600 dark:text-gray-400 cursor-pointer hover:text-gray-900 dark:hover:text-white"
                onClick={copyJobId}
                title="Click to copy"
              >
                {truncateJobId(job.job_id)}
              </span>
              <button
                onClick={copyJobId}
                className="ml-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
                aria-label="Copy job ID"
              >
                <FiCopy className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        <div className="mt-4 flex items-center text-sm text-gray-500 dark:text-gray-400">
          <span title={new Date(job.created_at).toLocaleString()}>
            Submitted {formatRelativeTime(job.created_at)}
          </span>
        </div>

        {job.status === 'RUNNING' && (
          <div className="mt-4">
            <div className="flex items-center">
              <FiLoader className="animate-spin h-4 w-4 text-yellow-500 mr-2" />
              <span className="text-sm text-yellow-700 dark:text-yellow-300">
                Calculation in progress...
              </span>
            </div>
            <div className="mt-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div 
                className="bg-yellow-500 h-2 rounded-full animate-pulse" 
                style={{ width: '60%' }}
              ></div>
            </div>
          </div>
        )}

        {job.status === 'FAILED' && job.error_message && (
          <div className="mt-3 p-2 bg-red-50 dark:bg-red-900/20 rounded text-sm text-red-700 dark:text-red-300">
            <p className="font-medium">Error:</p>
            <p className="truncate">{job.error_message}</p>
          </div>
        )}

        <div className="mt-4 flex space-x-2">
          <button
            onClick={() => onViewDetails(job.job_id)}
            className="inline-flex items-center px-3 py-1.5 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <FiEye className="w-4 h-4 mr-1" />
            {job.status === 'COMPLETED' ? 'View Results' : 'Details'}
          </button>
          
          <button
            onClick={() => onDelete(job.job_id)}
            className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-red-700 dark:text-red-300 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-800/30 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
          >
            <FiTrash className="w-4 h-4 mr-1" />
            Delete
          </button>
        </div>
      </div>
    </div>
  )
}

export default JobCard