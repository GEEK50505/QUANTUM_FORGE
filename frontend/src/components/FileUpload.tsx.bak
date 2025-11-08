import React, { useState, useCallback, DragEvent } from 'react'
import { FiUpload, FiX, FiFile } from 'react-icons/fi'

interface FileUploadProps {
  onFileSelect: (content: string, fileName: string) => void
}

const FileUpload: React.FC<FileUploadProps> = ({ onFileSelect }) => {
  const [isDragging, setIsDragging] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [fileContent, setFileContent] = useState<string>('')
  const [error, setError] = useState<string>('')

  const validateXYZFile = (content: string): boolean => {
    const lines = content.trim().split('\n')
    if (lines.length < 2) return false
    
    // First line should be number of atoms
    const firstLine = lines[0].trim()
    if (!/^\d+$/.test(firstLine)) return false
    
    const atomCount = parseInt(firstLine)
    if (isNaN(atomCount) || atomCount <= 0) return false
    
    // Check if we have enough lines (comment line + atom lines)
    if (lines.length < atomCount + 2) return false
    
    return true
  }

  const readFileContent = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        const content = e.target?.result as string || ''
        resolve(content)
      }
      reader.onerror = () => reject(new Error('Failed to read file'))
      reader.readAsText(file)
    })
  }

  const handleFile = async (selectedFile: File) => {
    if (selectedFile.type !== 'chemical/x-xyz' && !selectedFile.name.endsWith('.xyz')) {
      setError('Please upload a valid .xyz file')
      return
    }

    try {
      const content = await readFileContent(selectedFile)
      
      if (!validateXYZFile(content)) {
        setError('Invalid XYZ file format. File must start with number of atoms.')
        return
      }

      setFile(selectedFile)
      setFileContent(content)
      setError('')
      onFileSelect(content, selectedFile.name)
    } catch (err) {
      setError('Failed to read file content')
      console.error('File read error:', err)
    }
  }

  const handleDragEnter = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }, [])

  const handleDragOver = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])

  const handleDrop = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }, [])

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }

  const removeFile = () => {
    setFile(null)
    setFileContent('')
    setError('')
    onFileSelect('', '')
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' bytes'
    else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
    else return (bytes / 1048576).toFixed(1) + ' MB'
  }

  const getPreviewLines = (): string[] => {
    if (!fileContent) return []
    return fileContent.split('\n').slice(0, 10)
  }

  return (
    <div className="w-full">
      <div
        className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-all duration-200 ${
          isDragging 
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
            : 'border-gray-300 hover:border-blue-400 dark:border-gray-600 dark:hover:border-blue-500'
        }`}
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => document.getElementById('file-input')?.click()}
      >
        <input
          id="file-input"
          type="file"
          className="hidden"
          accept=".xyz"
          onChange={handleFileInput}
        />
        
        <div className="flex flex-col items-center justify-center space-y-2">
          <FiUpload className="text-3xl text-gray-400 dark:text-gray-500" />
          <div className="text-center">
            <p className="font-medium text-gray-900 dark:text-white">
              Drop your XYZ file here, or <span className="text-blue-600 dark:text-blue-400">browse</span>
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Supports .xyz files only
            </p>
          </div>
        </div>
      </div>

      {error && (
        <div className="mt-2 text-sm text-red-600 dark:text-red-400">
          {error}
        </div>
      )}

      {file && (
        <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <FiFile className="text-gray-500 dark:text-gray-400" />
              <div>
                <p className="font-medium text-gray-900 dark:text-white">{file.name}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {formatFileSize(file.size)}
                </p>
              </div>
            </div>
            <button
              onClick={removeFile}
              className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              aria-label="Remove file"
            >
              <FiX className="w-5 h-5" />
            </button>
          </div>

          {fileContent && (
            <div className="mt-3">
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                File Preview:
              </h4>
              <div className="bg-white dark:bg-gray-900 p-3 rounded border text-xs font-mono max-h-32 overflow-y-auto">
                {getPreviewLines().map((line, index) => (
                  <div key={index} className="text-gray-800 dark:text-gray-200">
                    {line}
                  </div>
                ))}
                {fileContent.split('\n').length > 10 && (
                  <div className="text-gray-500 dark:text-gray-400">
                    ... and {fileContent.split('\n').length - 10} more lines
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default FileUpload