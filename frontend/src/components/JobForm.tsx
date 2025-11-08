/**
 * frontend/src/components/JobForm.tsx
 *
 * Purpose:
 *  - Form component for submitting new xTB calculation jobs. Handles file
 *    upload via `FileUpload`, collects metadata (molecule name, email, tags)
 *    and posts a `JobSubmitRequest` to the backend API.
 *
 * Exports:
 *  - default: JobForm component
 *
 * Usage:
 *  <JobForm />
 */

import React, { useState } from 'react'
import { FiSend, FiLoader } from 'react-icons/fi'
import FileUpload from './FileUpload'
import { JobSubmitRequest } from '../types'
import { submitJob } from '../api/client'

const JobForm: React.FC = () => {
  const [moleculeName, setMoleculeName] = useState('')
  const [optimizationLevel, setOptimizationLevel] = useState<'tight' | 'normal'>('normal')
  const [email, setEmail] = useState('')
  const [tags, setTags] = useState('')
  const [fileContent, setFileContent] = useState('')
  const [fileName, setFileName] = useState('')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [jobId, setJobId] = useState('')
  const [error, setError] = useState('')

  const handleFileSelect = (content: string, name: string) => {
    setFileContent(content)
    setFileName(name)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!moleculeName.trim()) {
      setError('Molecule name is required')
      return
    }
    
    if (!fileContent) {
      setError('Please upload an XYZ file')
      return
    }

    setLoading(true)
    setError('')
    setSuccess(false)

    try {
      const request: JobSubmitRequest = {
        molecule_name: moleculeName.trim(),
        xyz_content: fileContent,
        optimization_level: optimizationLevel,
        email: email.trim(),
        tags: tags.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0)
      }

      const response = await submitJob(request)
      setJobId(response.job_id)
      setSuccess(true)
      
      // Reset form
      setMoleculeName('')
      setOptimizationLevel('normal')
      setEmail('')
      setTags('')
      setFileContent('')
      setFileName('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit job')
    } finally {
      setLoading(false)
    }
  }

  const resetForm = () => {
    setMoleculeName('')
    setOptimizationLevel('normal')
    setEmail('')
    setTags('')
    setFileContent('')
    setFileName('')
    setError('')
    setSuccess(false)
    setJobId('')
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">Submit New Calculation</h2>
      
      {success ? (
        <div className="mb-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-green-800 dark:text-green-200">
                Job submitted successfully!
              </h3>
              <div className="mt-2 text-sm text-green-700 dark:text-green-300">
                <p>Job ID: <span className="font-mono font-bold">{jobId}</span></p>
              </div>
              <div className="mt-4">
                <button
                  onClick={resetForm}
                  className="text-sm font-medium text-green-800 dark:text-green-200 hover:text-green-600 dark:hover:text-green-300"
                >
                  Submit another job
                </button>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="moleculeName" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Molecule Name *
            </label>
            <input
              type="text"
              id="moleculeName"
              value={moleculeName}
              onChange={(e) => setMoleculeName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder="e.g., benzene, water"
              disabled={loading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              XYZ File *
            </label>
            <FileUpload onFileSelect={handleFileSelect} />
          </div>

          <div>
            <label htmlFor="optimizationLevel" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Optimization Level
            </label>
            <select
              id="optimizationLevel"
              value={optimizationLevel}
              onChange={(e) => setOptimizationLevel(e.target.value as 'tight' | 'normal')}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              disabled={loading}
            >
              <option value="normal">Normal</option>
              <option value="tight">Tight</option>
            </select>
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Email (optional)
            </label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder="your.email@university.edu"
              disabled={loading}
            />
          </div>

          <div>
            <label htmlFor="tags" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Tags (optional)
            </label>
            <input
              type="text"
              id="tags"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder="e.g., organic, aromatic, benchmark"
              disabled={loading}
            />
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Separate multiple tags with commas
            </p>
          </div>

          {error && (
            <div className="rounded-md bg-red-50 dark:bg-red-900/20 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
                    Error
                  </h3>
                  <div className="mt-2 text-sm text-red-700 dark:text-red-300">
                    <p>{error}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={loading}
              className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
                loading
                  ? 'bg-blue-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {loading ? (
                <>
                  <FiLoader className="animate-spin -ml-1 mr-2 h-4 w-4" />
                  Running Calculation...
                </>
              ) : (
                <>
                  <FiSend className="-ml-1 mr-2 h-4 w-4" />
                  Run Calculation
                </>
              )}
            </button>
          </div>
        </form>
      )}
    </div>
  )
}

export default JobForm