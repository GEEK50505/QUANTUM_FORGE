'use client'

import { useEffect, useState } from 'react'
import { BatchUpload } from '@/components/BatchUpload'
import { MoleculeRow } from '@/components/MoleculeRow'
import { ThreeDMolPreview } from '@/components/ThreeDMolPreview'

interface Job {
  id: string
  job_key: string
  status: 'queued' | 'running' | 'completed' | 'failed'
  created_at: string
  payload?: {
    result_summary?: {
      energy?: number
    }
  }
}

export default function BatchPage() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [selectedJob, setSelectedJob] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  // Mock initial data
  useEffect(() => {
    const mockJobs: Job[] = [
      {
        id: '1',
        job_key: 'water_001',
        status: 'completed',
        created_at: new Date().toISOString(),
        payload: {
          result_summary: {
            energy: -5.070276993755,
          },
        },
      },
    ]
    setJobs(mockJobs)
  }, [])

  const handleFilesSelected = async (files: File[]) => {
    setIsLoading(true)
    // TODO: Upload files and enqueue jobs via API
    console.log('Files selected:', files)
    setIsLoading(false)
  }

  const selectedJobData = jobs.find((j) => j.id === selectedJob)

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Batch Calculation</h1>
        <p className="text-slate-600 mb-8">
          Upload molecules and run xTB calculations in parallel
        </p>

        <div className="grid grid-cols-3 gap-8">
          {/* Left: Upload and Table */}
          <div className="col-span-2">
            <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900 mb-4">Upload Molecules</h2>
              <BatchUpload onFilesSelected={handleFilesSelected} isLoading={isLoading} />

              <h3 className="text-lg font-semibold text-slate-900 mt-8 mb-4">Jobs</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-slate-200 bg-slate-50">
                      <th className="px-4 py-2 text-left font-semibold text-slate-700">Job Key</th>
                      <th className="px-4 py-2 text-left font-semibold text-slate-700">Status</th>
                      <th className="px-4 py-2 text-left font-semibold text-slate-700">Created</th>
                      <th className="px-4 py-2 text-left font-semibold text-slate-700">Energy (Eh)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {jobs.map((job) => (
                      <MoleculeRow
                        key={job.id}
                        job={job}
                        isSelected={selectedJob === job.id}
                        onSelect={setSelectedJob}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Right: Preview */}
          <div className="col-span-1">
            <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm sticky top-8">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">Preview</h3>
              {selectedJobData ? (
                <div>
                  <ThreeDMolPreview jobKey={selectedJobData.job_key} />
                  <div className="mt-4 space-y-2 text-xs">
                    <div>
                      <span className="text-slate-600">Job:</span>
                      <span className="font-mono ml-2">{selectedJobData.job_key}</span>
                    </div>
                    <div>
                      <span className="text-slate-600">Status:</span>
                      <span className="font-mono ml-2">{selectedJobData.status}</span>
                    </div>
                    {selectedJobData.payload?.result_summary?.energy && (
                      <div>
                        <span className="text-slate-600">Energy:</span>
                        <span className="font-mono ml-2">
                          {selectedJobData.payload.result_summary.energy.toFixed(6)} Eh
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-slate-500 text-center py-12">
                  <div className="text-2xl mb-2">👈</div>
                  <p className="text-xs">Select a job to view details</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
