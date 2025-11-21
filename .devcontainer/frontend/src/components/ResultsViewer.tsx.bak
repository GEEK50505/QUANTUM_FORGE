import React, { useState, useEffect } from 'react'
import { FiDownload, FiLoader } from 'react-icons/fi'
import { ResultsResponse } from '../types'
import { getJobResults } from '../api/client'
import { formatEnergy, formatGap } from '../utils/formatters'

interface ResultsViewerProps {
  jobId: string
}

const ResultsViewer: React.FC<ResultsViewerProps> = ({ jobId }) => {
  const [results, setResults] = useState<ResultsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchResults = async () => {
    try {
      setLoading(true)
      const data = await getJobResults(jobId)
      setResults(data)
      setError('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch results')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchResults()
  }, [jobId])

  const downloadJson = () => {
    if (!results) return
    
    const dataStr = JSON.stringify(results, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `results_${jobId}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  const downloadXYZ = () => {
    // This would require the optimized geometry to be available in results
    // For now, we'll just show an alert
    alert('Download XYZ functionality would be implemented here')
  }

  const downloadLog = () => {
    // This would require log data to be available
    // For now, we'll just show an alert
    alert('Download log functionality would be implemented here')
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-center">
          <FiLoader className="animate-spin h-8 w-8 text-blue-500 mx-auto" />
          <p className="mt-2 text-gray-600 dark:text-gray-400">Loading results...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
              Error loading results
            </h3>
            <div className="mt-2 text-sm text-red-700 dark:text-red-300">
              <p>{error}</p>
            </div>
            <div className="mt-4">
              <button
                onClick={fetchResults}
                className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!results) {
    return (
      <div className="text-center py-12">
        <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No results available</h3>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Results for this job are not yet available.
        </p>
      </div>
    )
  }

  // Convert Hartree to eV for HOMO-LUMO gap
  const gapInEv = results.homo_lumo_gap * 27.2114

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">Calculation Results</h2>
        <div className="flex space-x-2">
          <button
            onClick={downloadJson}
            className="inline-flex items-center px-3 py-1.5 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <FiDownload className="w-4 h-4 mr-1" />
            JSON
          </button>
          <button
            onClick={downloadXYZ}
            className="inline-flex items-center px-3 py-1.5 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <FiDownload className="w-4 h-4 mr-1" />
            XYZ
          </button>
          <button
            onClick={downloadLog}
            className="inline-flex items-center px-3 py-1.5 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <FiDownload className="w-4 h-4 mr-1" />
            Log
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-5">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Energy</h3>
          <p className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">
            {formatEnergy(results.energy)}
          </p>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-5">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">HOMO-LUMO Gap</h3>
          <p className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">
            {formatGap(gapInEv)}
          </p>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-5">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Gradient Norm</h3>
          <p className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">
            {results.gradient_norm.toFixed(6)}
          </p>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-5">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Convergence</h3>
          <p className={`mt-1 text-2xl font-semibold ${
            results.convergence_status === 'CONVERGED' 
              ? 'text-green-600 dark:text-green-400' 
              : 'text-red-600 dark:text-red-400'
          }`}>
            {results.convergence_status}
          </p>
        </div>
      </div>

      {/* Charts Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Atomic Charges</h3>
        <div className="h-64 flex items-end space-x-2 justify-center">
          {results.charges.map((charge, index) => (
            <div key={index} className="flex flex-col items-center">
              <div 
                className={`w-8 rounded-t ${
                  charge >= 0 
                    ? 'bg-red-500' 
                    : 'bg-blue-500'
                }`}
                style={{ height: `${Math.abs(charge) * 100}px` }}
                title={`Atom ${index + 1}: ${charge.toFixed(3)}`}
              ></div>
              <span className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {index + 1}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Molecular Properties */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Molecular Properties</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(results.properties).map(([key, value]) => (
            <div key={key} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 capitalize">
                {key.replace(/_/g, ' ')}
              </h4>
              <p className="mt-1 text-gray-900 dark:text-white">
                {typeof value === 'object' ? JSON.stringify(value) : String(value)}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default ResultsViewer