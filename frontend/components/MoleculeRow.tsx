'use client'

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

interface MoleculeRowProps {
  job: Job
  isSelected?: boolean
  onSelect?: (jobId: string) => void
}

export function MoleculeRow({ job, isSelected, onSelect }: MoleculeRowProps) {
  const statusBgColor: Record<string, string> = {
    queued: 'bg-slate-100',
    running: 'bg-blue-100',
    completed: 'bg-emerald-100',
    failed: 'bg-red-100',
  }

  const statusTextColor: Record<string, string> = {
    queued: 'text-slate-700',
    running: 'text-blue-700',
    completed: 'text-emerald-700',
    failed: 'text-red-700',
  }

  return (
    <tr
      className={`border-b cursor-pointer hover:bg-slate-50 ${isSelected ? 'bg-emerald-50' : ''}`}
      onClick={() => onSelect?.(job.id)}
    >
      <td className="px-4 py-2 text-xs font-mono">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={() => onSelect?.(job.id)}
          className="mr-2"
        />
        {job.job_key}
      </td>
      <td className="px-4 py-2 text-xs">
        <span className={`px-2 py-1 rounded text-xs font-medium ${statusBgColor} ${statusTextColor}`}>
          {job.status}
        </span>
      </td>
      <td className="px-4 py-2 text-xs font-mono text-slate-600">
        {new Date(job.created_at).toLocaleString()}
      </td>
      <td className="px-4 py-2 text-xs font-mono text-slate-600">
        {job.payload?.result_summary?.energy
          ? job.payload.result_summary.energy.toFixed(6)
          : '—'}
      </td>
    </tr>
  )
}
