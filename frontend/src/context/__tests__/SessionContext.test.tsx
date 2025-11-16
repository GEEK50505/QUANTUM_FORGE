/**
 * frontend/src/context/__tests__/SessionContext.test.tsx
 *
 * Purpose:
 *  - Unit tests for SessionContext to verify auto-save, restoration,
 *    and state management functionality.
 *
 * Tests:
 *  - SessionProvider renders children
 *  - useSession hook returns correct initial state
 *  - updateEditorState updates session
 *  - updateUIPreferences updates preferences
 *  - localStorage persistence (mock)
 *  - Auto-save debounce behavior
 */

import React from 'react'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SessionProvider, useSession } from '../SessionContext'
import '@testing-library/jest-dom'

// Mock component that uses the hook
const TestComponent = () => {
  const { session, updateEditorState, updateUIPreferences, clearSession } = useSession()

  return (
    <div>
      <div data-testid="molecule-name">{session.editorState.moleculeName}</div>
      <div data-testid="xyz-content">{session.editorState.xyzContent}</div>
      <div data-testid="sidebar-expanded">{session.uiPreferences.sidebarExpanded ? 'expanded' : 'collapsed'}</div>
      <div data-testid="font-size">{session.uiPreferences.fontSizePercent}</div>

      <button
        data-testid="update-molecule"
        onClick={() => updateEditorState({ moleculeName: 'Water' })}
      >
        Set Molecule
      </button>

      <button
        data-testid="update-xyz"
        onClick={() => updateEditorState({ xyzContent: 'O 0 0 0\nH 1 0 0' })}
      >
        Set XYZ
      </button>

      <button
        data-testid="toggle-sidebar"
        onClick={() => updateUIPreferences({ sidebarExpanded: !session.uiPreferences.sidebarExpanded })}
      >
        Toggle Sidebar
      </button>

      <button
        data-testid="clear-session"
        onClick={clearSession}
      >
        Clear Session
      </button>
    </div>
  )
}

describe('SessionContext', () => {
  // Save original localStorage
  const localStorageMock = (() => {
    let store: Record<string, string> = {}

    return {
      getItem: (key: string) => store[key] || null,
      setItem: (key: string, value: string) => {
        store[key] = value.toString()
      },
      removeItem: (key: string) => {
        delete store[key]
      },
      clear: () => {
        store = {}
      }
    }
  })()

  beforeEach(() => {
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock
    })
    localStorageMock.clear()
  })

  test('SessionProvider renders children', () => {
    render(
      <SessionProvider>
        <div>Test Content</div>
      </SessionProvider>
    )
    expect(screen.getByText('Test Content')).toBeInTheDocument()
  })

  test('useSession hook returns correct initial state', () => {
    render(
      <SessionProvider>
        <TestComponent />
      </SessionProvider>
    )

    expect(screen.getByTestId('molecule-name')).toHaveTextContent('')
    expect(screen.getByTestId('xyz-content')).toHaveTextContent('')
    expect(screen.getByTestId('sidebar-expanded')).toHaveTextContent('expanded')
    expect(screen.getByTestId('font-size')).toHaveTextContent('100')
  })

  test('updateEditorState updates molecule name', async () => {
    const user = userEvent.setup()
    render(
      <SessionProvider>
        <TestComponent />
      </SessionProvider>
    )

    const button = screen.getByTestId('update-molecule')
    await user.click(button)

    expect(screen.getByTestId('molecule-name')).toHaveTextContent('Water')
  })

  test('updateEditorState updates XYZ content', async () => {
    const user = userEvent.setup()
    render(
      <SessionProvider>
        <TestComponent />
      </SessionProvider>
    )

    const button = screen.getByTestId('update-xyz')
    await user.click(button)

    expect(screen.getByTestId('xyz-content')).toHaveTextContent('O 0 0 0\nH 1 0 0')
  })

  test('updateUIPreferences toggles sidebar', async () => {
    const user = userEvent.setup()
    render(
      <SessionProvider>
        <TestComponent />
      </SessionProvider>
    )

    expect(screen.getByTestId('sidebar-expanded')).toHaveTextContent('expanded')

    const toggleButton = screen.getByTestId('toggle-sidebar')
    await user.click(toggleButton)

    expect(screen.getByTestId('sidebar-expanded')).toHaveTextContent('collapsed')
  })

  test('clearSession resets all state', async () => {
    const user = userEvent.setup()
    render(
      <SessionProvider>
        <TestComponent />
      </SessionProvider>
    )

    // Set some state
    await user.click(screen.getByTestId('update-molecule'))

    // Clear it
    await user.click(screen.getByTestId('clear-session'))

    // Verify it's cleared
    expect(screen.getByTestId('molecule-name')).toHaveTextContent('')
  })

  test('localStorage is updated with debounce', async () => {
    render(
      <SessionProvider>
        <TestComponent />
      </SessionProvider>
    )

    const user = userEvent.setup()
    await user.click(screen.getByTestId('update-molecule'))

    // Immediately after click, localStorage might not be updated yet (debounce)
    // Wait for debounce to complete
    await waitFor(
      () => {
        const stored = localStorageMock.getItem('quantumForgeSession')
        expect(stored).toBeTruthy()
        if (stored) {
          const parsed = JSON.parse(stored)
          expect(parsed.editorState.moleculeName).toBe('Water')
        }
      },
      { timeout: 3000 } // Wait up to 3 seconds for debounce
    )
  })

  test('session restores from localStorage on mount', () => {
    const sessionData = {
      editorState: {
        xyzContent: 'C 0 0 0',
        moleculeName: 'Methane',
        lastModified: Date.now()
      },
      activeCalculationId: null,
      activeMoleculeId: null,
      uiPreferences: {
        sidebarExpanded: false,
        activeTab: 'results',
        fontSizePercent: 110
      }
    }

    localStorageMock.setItem('quantumForgeSession', JSON.stringify(sessionData))

    render(
      <SessionProvider>
        <TestComponent />
      </SessionProvider>
    )

    expect(screen.getByTestId('molecule-name')).toHaveTextContent('Methane')
    expect(screen.getByTestId('xyz-content')).toHaveTextContent('C 0 0 0')
    expect(screen.getByTestId('sidebar-expanded')).toHaveTextContent('collapsed')
    expect(screen.getByTestId('font-size')).toHaveTextContent('110')
  })

  test('handles corrupted localStorage gracefully', () => {
    localStorageMock.setItem('quantumForgeSession', 'corrupted-data')

    render(
      <SessionProvider>
        <TestComponent />
      </SessionProvider>
    )

    // Should fall back to default state
    expect(screen.getByTestId('molecule-name')).toHaveTextContent('')
    expect(screen.getByTestId('font-size')).toHaveTextContent('100')
  })
})
