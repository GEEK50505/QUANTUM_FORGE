'use client'

import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'

interface BatchUploadProps {
  onFilesSelected: (files: File[]) => void
  isLoading?: boolean
}

export function BatchUpload({ onFilesSelected, isLoading }: BatchUploadProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      // Filter for .xyz, .sdf files
      const validFiles = acceptedFiles.filter(
        (f) => f.name.endsWith('.xyz') || f.name.endsWith('.sdf')
      )
      if (validFiles.length > 0) {
        onFilesSelected(validFiles)
      }
    },
    [onFilesSelected]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.xyz'],
      'chemical/x-mdl-sdfile': ['.sdf'],
    },
  })

  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition ${
        isDragActive
          ? 'border-emerald-500 bg-emerald-50'
          : 'border-slate-300 hover:border-slate-400'
      } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      <input {...getInputProps()} disabled={isLoading} />
      <div className="text-4xl mb-2">📤</div>
      <p className="text-sm font-medium text-slate-700">
        {isDragActive
          ? 'Drop files here...'
          : 'Drag XYZ or SDF files here, or click to select'}
      </p>
      <p className="text-xs text-slate-500 mt-1">
        Supports .xyz and .sdf multi-structure files
      </p>
    </div>
  )
}
