/**
 * frontend/src/components/SessionDebugger.tsx
 *
 * Purpose:
 *  - Development component to visualize and debug SessionContext state.
 *  - Shows current session values, triggers manual saves, clears data.
 *  - Useful for verifying localStorage persistence and auto-save functionality.
 *
 * Usage:
 *  - Import in Dashboard or layout during development
 *  - Toggle visibility with dev tools
 *  - Remove before production
 *
 * Features:
 *  - Display all session state values
 *  - Trigger manual save to localStorage
 *  - Clear session completely
 *  - Show localStorage content
 *  - Copy JSON to clipboard
 */

import React, { useState, useEffect } from 'react'
import { useSession } from '../context/SessionContext'

interface StorageData {
  editorState?: Record<string, unknown>
  activeCalculationId?: string | null
  activeMoleculeId?: string | null
  uiPreferences?: Record<string, unknown>
}

const SessionDebugger: React.FC = () => {
  const { session, saveSession, clearSession } = useSession()
  const [storageData, setStorageData] = useState<StorageData | null>(null)
  const [isOpen, setIsOpen] = useState(false)

  // Load storage data
  const loadStorageData = () => {
    if (typeof window !== 'undefined') {
      const data = localStorage.getItem('quantumForgeSession')
      setStorageData(data ? JSON.parse(data) : null)
    }
  }

  useEffect(() => {
    loadStorageData()
  }, [session])

  const copyToClipboard = () => {
    if (storageData) {
      navigator.clipboard.writeText(JSON.stringify(storageData, null, 2))
      alert('Session data copied to clipboard')
    }
  }

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-4 right-4 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg shadow-lg text-sm font-medium z-50"
        title="Open session debugger (dev only)"
      >
        🐛 Session Debug
      </button>
    )
  }

  return (
    <div className="fixed bottom-4 right-4 w-96 max-h-96 bg-gray-900 text-white rounded-lg shadow-2xl border border-gray-700 p-4 z-50 overflow-y-auto font-mono text-xs">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-sm font-bold">📊 Session Debugger</h3>
        <button
          onClick={() => setIsOpen(false)}
          className="text-gray-400 hover:text-white text-lg"
        >
          ✕
        </button>
      </div>

      {/* Current Session State */}
      <div className="mb-4 p-3 bg-gray-800 rounded border border-gray-700">
        <div className="font-bold text-blue-400 mb-2">Current Session State:</div>
        <div className="space-y-1 text-gray-300">
          <div>
            <span className="text-yellow-400">moleculeName:</span> "{session.editorState.moleculeName}"
          </div>
          <div>
            <span className="text-yellow-400">xyzContent:</span> {session.editorState.xyzContent.length} chars
          </div>
          <div>
            <span className="text-yellow-400">lastModified:</span> {new Date(session.editorState.lastModified).toLocaleTimeString()}
          </div>
          <div>
            <span className="text-yellow-400">activeCalculationId:</span> {session.activeCalculationId || 'null'}
          </div>
          <div>
            <span className="text-yellow-400">activeMoleculeId:</span> {session.activeMoleculeId || 'null'}
          </div>
          <div>
            <span className="text-yellow-400">sidebarExpanded:</span> {String(session.uiPreferences.sidebarExpanded)}
          </div>
          <div>
            <span className="text-yellow-400">activeTab:</span> "{session.uiPreferences.activeTab}"
          </div>
          <div>
            <span className="text-yellow-400">fontSizePercent:</span> {session.uiPreferences.fontSizePercent}%
          </div>
        </div>
      </div>

      {/* localStorage Data */}
      <div className="mb-4 p-3 bg-gray-800 rounded border border-gray-700">
        <div className="font-bold text-green-400 mb-2">localStorage Data:</div>
        {storageData ? (
          <div className="text-gray-300 break-words whitespace-pre-wrap text-xs max-h-32 overflow-y-auto">
            {JSON.stringify(storageData, null, 2)}
          </div>
        ) : (
          <div className="text-gray-500">No data in localStorage</div>
        )}
      </div>

      {/* Controls */}
      <div className="flex gap-2 justify-between">
        <button
          onClick={() => {
            loadStorageData()
          }}
          className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded text-xs font-medium"
        >
          🔄 Refresh
        </button>

        <button
          onClick={saveSession}
          className="flex-1 bg-green-600 hover:bg-green-700 text-white px-2 py-1 rounded text-xs font-medium"
        >
          💾 Save Now
        </button>

        <button
          onClick={copyToClipboard}
          className="flex-1 bg-purple-600 hover:bg-purple-700 text-white px-2 py-1 rounded text-xs font-medium"
        >
          📋 Copy
        </button>

        <button
          onClick={() => {
            clearSession()
            loadStorageData()
          }}
          className="flex-1 bg-red-600 hover:bg-red-700 text-white px-2 py-1 rounded text-xs font-medium"
        >
          🗑️ Clear
        </button>
      </div>

      {/* Info */}
      <div className="mt-3 text-gray-500 text-xs">
        💡 Tip: Check DevTools Console for additional debugging.
        <br />
        Auto-save: 2s debounce
      </div>
    </div>
  )
}

export default SessionDebugger
