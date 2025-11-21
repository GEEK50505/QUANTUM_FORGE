'use client'

import { useEffect, useRef } from 'react'

interface ThreeDMolPreviewProps {
  xyzContent?: string
  jobKey?: string
}

export function ThreeDMolPreview({ xyzContent, jobKey }: ThreeDMolPreviewProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!containerRef.current || !xyzContent) return

    // Basic 3D preview placeholder
    // Full 3Dmol.js integration would require loading the library dynamically
    containerRef.current.innerHTML = `
      <div style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: #f1f5f9; border-radius: 8px; font-size: 12px; color: #64748b;">
        <div style="text-align: center;">
          <div style="font-size: 24px; margin-bottom: 8px;">🧬</div>
          <div>${jobKey || 'Molecule'}</div>
          <div style="font-size: 10px; margin-top: 4px;">3D Preview (3Dmol.js)</div>
        </div>
      </div>
    `
  }, [xyzContent, jobKey])

  return <div ref={containerRef} className="w-full h-96" />
}
