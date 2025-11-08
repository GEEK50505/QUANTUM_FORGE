/**
 * frontend/src/components/MoleculeViewer.tsx
 *
 * Purpose:
 *  - Render a simple 2D/2.5D canvas-based visualization of an XYZ molecule.
 *    Parses XYZ content and draws atoms and bonds. Optionally toggles between
 *    input and optimized geometries when provided.
 *
 * Exports:
 *  - default: MoleculeViewer component
 *
 * Usage:
 *  <MoleculeViewer xyz_content={xyz} optimized_geometry={opt_xyz} />
 */

import React, { useEffect, useRef } from 'react'

interface MoleculeViewerProps {
  xyz_content: string
  optimized_geometry?: string
}

const MoleculeViewer: React.FC<MoleculeViewerProps> = ({ xyz_content, optimized_geometry }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [showOptimized, setShowOptimized] = React.useState(false)

  // Parse XYZ file content
  const parseXYZ = (content: string) => {
    if (!content) return { atoms: [], bonds: [] }
    
    const lines = content.trim().split('\n')
    if (lines.length < 2) return { atoms: [], bonds: [] }
    
    const atomLines = lines.slice(2) // Skip first two lines (atom count and comment)
    const atoms: { element: string; x: number; y: number; z: number }[] = []
    
    atomLines.forEach(line => {
      const parts = line.trim().split(/\s+/)
      if (parts.length >= 4) {
        atoms.push({
          element: parts[0],
          x: parseFloat(parts[1]),
          y: parseFloat(parts[2]),
          z: parseFloat(parts[3])
        })
      }
    })
    
    // Simple bond detection based on distance
    const bonds: [number, number][] = []
    const bondThreshold = 1.8 // Angstroms
    
    for (let i = 0; i < atoms.length; i++) {
      for (let j = i + 1; j < atoms.length; j++) {
        const dx = atoms[i].x - atoms[j].x
        const dy = atoms[i].y - atoms[j].y
        const dz = atoms[i].z - atoms[j].z
        const distance = Math.sqrt(dx * dx + dy * dy + dz * dz)
        
        if (distance < bondThreshold) {
          bonds.push([i, j])
        }
      }
    }
    
    return { atoms, bonds }
  }

  // Get color for element
  const getElementColor = (element: string): string => {
    const colors: Record<string, string> = {
      'H': '#FFFFFF',  // White
      'C': '#404040',  // Dark gray
      'N': '#3050F8',  // Blue
      'O': '#FF0D0D',  // Red
      'F': '#90E050',  // Green
      'Cl': '#1FF01F', // Green
      'Br': '#A62929', // Dark red
      'I': '#940094',  // Purple
      'S': '#FFFF30',  // Yellow
      'P': '#FF8000',  // Orange
      'default': '#808080' // Gray
    }
    return colors[element] || colors['default']
  }

  // Draw molecule on canvas
  const drawMolecule = () => {
    const canvas = canvasRef.current
    if (!canvas) return
    
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    
    const content = showOptimized && optimized_geometry ? optimized_geometry : xyz_content
    const { atoms, bonds } = parseXYZ(content)
    
    if (atoms.length === 0) return
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    
    // Set canvas size
    canvas.width = canvas.clientWidth
    canvas.height = canvas.clientHeight
    
    // Find molecule bounds for centering
    let minX = Infinity, minY = Infinity, minZ = Infinity
    let maxX = -Infinity, maxY = -Infinity, maxZ = -Infinity
    
    atoms.forEach(atom => {
      minX = Math.min(minX, atom.x)
      minY = Math.min(minY, atom.y)
      minZ = Math.min(minZ, atom.z)
      maxX = Math.max(maxX, atom.x)
      maxY = Math.max(maxY, atom.y)
      maxZ = Math.max(maxZ, atom.z)
    })
    
    const centerX = (minX + maxX) / 2
    const centerY = (minY + maxY) / 2
    const centerZ = (minZ + maxZ) / 2
    
    const scale = Math.min(canvas.width, canvas.height) / Math.max(maxX - minX, maxY - minY, 1) * 0.8
    
    // Draw bonds first (behind atoms)
    ctx.lineWidth = 2
    bonds.forEach(([i, j]) => {
      const atom1 = atoms[i]
      const atom2 = atoms[j]
      
      const x1 = (atom1.x - centerX) * scale + canvas.width / 2
      const y1 = (atom1.y - centerY) * scale + canvas.height / 2
      const x2 = (atom2.x - centerX) * scale + canvas.width / 2
      const y2 = (atom2.y - centerY) * scale + canvas.height / 2
      
      ctx.beginPath()
      ctx.moveTo(x1, y1)
      ctx.lineTo(x2, y2)
      ctx.strokeStyle = '#808080'
      ctx.stroke()
    })
    
    // Draw atoms
    atoms.forEach(atom => {
      const x = (atom.x - centerX) * scale + canvas.width / 2
      const y = (atom.y - centerY) * scale + canvas.height / 2
      
      const radius = 15
      ctx.beginPath()
      ctx.arc(x, y, radius, 0, 2 * Math.PI)
      ctx.fillStyle = getElementColor(atom.element)
      ctx.fill()
      ctx.strokeStyle = '#000000'
      ctx.lineWidth = 1
      ctx.stroke()
      
      // Draw element symbol
      ctx.fillStyle = '#000000'
      ctx.font = '12px Arial'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(atom.element, x, y)
    })
  }

  useEffect(() => {
    drawMolecule()
    
    const handleResize = () => {
      drawMolecule()
    }
    
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [xyz_content, optimized_geometry, showOptimized])

  if (!xyz_content) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 text-center">
        <p className="text-gray-500 dark:text-gray-400">
          No molecule data available
        </p>
      </div>
    )
  }

  const { atoms } = parseXYZ(xyz_content)
  const hasOptimized = !!optimized_geometry

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">
          Molecule Viewer
        </h3>
        
        {hasOptimized && (
          <div className="flex items-center">
            <span className="text-sm text-gray-600 dark:text-gray-400 mr-2">
              Input
            </span>
            <button
              onClick={() => setShowOptimized(!showOptimized)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                showOptimized ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                  showOptimized ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
            <span className="text-sm text-gray-600 dark:text-gray-400 ml-2">
              Optimized
            </span>
          </div>
        )}
      </div>
      
      <div className="p-4">
        <div className="relative bg-gray-50 dark:bg-gray-900 rounded-lg overflow-hidden" style={{ height: '400px' }}>
          <canvas 
            ref={canvasRef} 
            className="w-full h-full"
          />
        </div>
        
        <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
          <p>
            {atoms.length} atoms displayed. 
            {hasOptimized && (
              <span className="ml-2">
                Showing {showOptimized ? 'optimized' : 'input'} geometry.
              </span>
            )}
          </p>
        </div>
      </div>
    </div>
  )
}

export default MoleculeViewer