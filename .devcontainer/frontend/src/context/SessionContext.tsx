/*
Purpose: Session state management for editor persistence
Description: 
  Manages editor state (XYZ content, molecule name), calculation state, and UI preferences.
  Auto-saves to localStorage with 2-second debounce to avoid excessive writes.
  Restores state on page reload for seamless user experience.

Exports: SessionProvider, useSession
Notes: 
  - Uses debouncing to batch state updates (every 2 seconds)
  - localStorage used for client-side persistence
  - Can be extended to sync with backend user_sessions table
*/

"use client";

import type React from "react";
import {
  createContext,
  useState,
  useContext,
  useEffect,
  useCallback,
  useRef,
} from "react";

// Session state type definition
export type EditorState = {
  xyzContent: string;
  moleculeName: string;
  lastModified: number; // timestamp
};

export type SessionState = {
  editorState: EditorState;
  activeCalculationId: string | null;
  activeMoleculeId: string | null;
  uiPreferences: {
    sidebarExpanded: boolean;
    activeTab: string;
    fontSizePercent: number;
  };
};

type SessionContextType = {
  session: SessionState;
  updateEditorState: (state: Partial<EditorState>) => void;
  updateCalculationId: (id: string | null) => void;
  updateMoleculeId: (id: string | null) => void;
  updateUIPreferences: (prefs: Partial<SessionState["uiPreferences"]>) => void;
  clearSession: () => void;
  saveSession: () => void;
};

// Default session state
const defaultSession: SessionState = {
  editorState: {
    xyzContent: "",
    moleculeName: "Untitled Molecule",
    lastModified: Date.now(),
  },
  activeCalculationId: null,
  activeMoleculeId: null,
  uiPreferences: {
    sidebarExpanded: true,
    activeTab: "editor",
    fontSizePercent: 100,
  },
};

const SessionContext = createContext<SessionContextType | undefined>(undefined);

export const SessionProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [session, setSession] = useState<SessionState>(defaultSession);
  const [isInitialized, setIsInitialized] = useState(false);

  // Debounce timer ref for auto-save
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Load session from localStorage on mount
  useEffect(() => {
    if (typeof window === "undefined") return; // SSR guard

    try {
      const savedSession = localStorage.getItem("quantumForgeSession");
      if (savedSession) {
        const parsedSession = JSON.parse(savedSession) as SessionState;
        setSession(parsedSession);
      }
    } catch (error) {
      console.error("Failed to load session from localStorage:", error);
      // Fall back to default session
      setSession(defaultSession);
    }
    setIsInitialized(true);
  }, []);

  // Debounced save to localStorage
  const debouncedSave = useCallback(() => {
    // Clear existing timeout
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }

    // Set new timeout (2 second debounce)
    saveTimeoutRef.current = setTimeout(() => {
      try {
        localStorage.setItem("quantumForgeSession", JSON.stringify(session));
        console.debug("Session auto-saved to localStorage");
      } catch (error) {
        console.error("Failed to save session to localStorage:", error);
      }
    }, 2000);
  }, [session]);

  // Auto-save on session changes (debounced)
  useEffect(() => {
    if (isInitialized) {
      debouncedSave();
    }
  }, [session, isInitialized, debouncedSave]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, []);

  // Update editor state
  const updateEditorState = useCallback(
    (state: Partial<EditorState>) => {
      setSession((prev) => ({
        ...prev,
        editorState: {
          ...prev.editorState,
          ...state,
          lastModified: Date.now(),
        },
      }));
    },
    []
  );

  // Update active calculation ID
  const updateCalculationId = useCallback((id: string | null) => {
    setSession((prev) => ({
      ...prev,
      activeCalculationId: id,
    }));
  }, []);

  // Update active molecule ID
  const updateMoleculeId = useCallback((id: string | null) => {
    setSession((prev) => ({
      ...prev,
      activeMoleculeId: id,
    }));
  }, []);

  // Update UI preferences
  const updateUIPreferences = useCallback(
    (prefs: Partial<SessionState["uiPreferences"]>) => {
      setSession((prev) => ({
        ...prev,
        uiPreferences: {
          ...prev.uiPreferences,
          ...prefs,
        },
      }));
    },
    []
  );

  // Clear session (logout)
  const clearSession = useCallback(() => {
    try {
      localStorage.removeItem("quantumForgeSession");
      setSession(defaultSession);
    } catch (error) {
      console.error("Failed to clear session:", error);
    }
  }, []);

  // Manual save (can be called before unloading)
  const saveSession = useCallback(() => {
    try {
      localStorage.setItem("quantumForgeSession", JSON.stringify(session));
      console.debug("Session manually saved");
    } catch (error) {
      console.error("Failed to save session:", error);
    }
  }, [session]);

  return (
    <SessionContext.Provider
      value={{
        session,
        updateEditorState,
        updateCalculationId,
        updateMoleculeId,
        updateUIPreferences,
        clearSession,
        saveSession,
      }}
    >
      {children}
    </SessionContext.Provider>
  );
};

// Hook to use session context
export const useSession = (): SessionContextType => {
  const context = useContext(SessionContext);
  if (context === undefined) {
    throw new Error("useSession must be used within SessionProvider");
  }
  return context;
};
