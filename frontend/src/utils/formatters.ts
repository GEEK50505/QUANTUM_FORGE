import { formatDistanceToNow, parseISO } from 'date-fns'

export const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return bytes + ' bytes'
  else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  else return (bytes / 1048576).toFixed(1) + ' MB'
}

export const formatDateTime = (iso: string): string => {
  return new Date(iso).toLocaleString()
}

export const formatRelativeTime = (iso: string): string => {
  try {
    const date = parseISO(iso)
    return formatDistanceToNow(date, { addSuffix: true })
  } catch (error) {
    return 'Unknown time'
  }
}

export const formatEnergy = (hartree: number): string => {
  // Convert Hartree to eV (1 Hartree = 27.2114 eV)
  const ev = hartree * 27.2114
  return `${hartree.toFixed(6)} Ha (${ev.toFixed(6)} eV)`
}

export const formatGap = (ev: number): string => {
  return ev.toFixed(3) + ' eV'
}

export const truncateJobId = (jobId: string): string => {
  if (jobId.length <= 8) return jobId
  return jobId.substring(0, 8) + '...'
}