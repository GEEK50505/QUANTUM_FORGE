// NOTE (permanent): This file contains educational notes for non-coders.
// Do not remove comments unless explicitly requested in a written instruction.
// These notes explain purpose, props, and data contract shapes.
//
// Module Purpose: Application settings page
// What this file renders: Interface for configuring app settings and backend endpoints
// How it fits into the Quantum Forge app: Provides configuration management
// Author: Qwen 3 Coder — Scaffold Stage

import React, { useState, useEffect } from 'react';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';

/**
 * Settings Page
 * 
 * Manages application configuration including backend endpoints and development mode.
 * 
 * For non-coders: This page lets you configure how the application connects to
 * the backend services. You can change where it looks for the simulation server,
 * toggle development mode, and manage API keys for secure access.
 */
const SettingsPage: React.FC = () => {
  const [backendEndpoint, setBackendEndpoint] = useState('http://localhost:8000/api');
  const [apiKey, setApiKey] = useState('');
  const [devMode, setDevMode] = useState(true);
  const [saved, setSaved] = useState(false);

  // Load settings from localStorage on mount
  useEffect(() => {
    const savedSettings = localStorage.getItem('quantum-forge-settings');
    if (savedSettings) {
      const settings = JSON.parse(savedSettings);
      setBackendEndpoint(settings.backendEndpoint || 'http://localhost:8000/api');
      setApiKey(settings.apiKey || '');
      setDevMode(settings.devMode !== undefined ? settings.devMode : true);
    }
  }, []);

  // Save settings to localStorage
  const saveSettings = () => {
    const settings = {
      backendEndpoint,
      apiKey,
      devMode
    };
    localStorage.setItem('quantum-forge-settings', JSON.stringify(settings));
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="p-4 md:p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Settings
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Configure application settings and backend connections
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Backend Configuration */}
        <Card>
          <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Backend Configuration
          </h2>
          
          <div className="space-y-4">
            <div>
              <label htmlFor="backend-endpoint" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Backend Endpoint
              </label>
              <input
                type="text"
                id="backend-endpoint"
                value={backendEndpoint}
                onChange={(e) => setBackendEndpoint(e.target.value)}
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
                placeholder="http://localhost:8000/api"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                The URL where the Quantum Forge backend server is running
              </p>
            </div>
            
            <div>
              <label htmlFor="api-key" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                API Key
              </label>
              <input
                type="password"
                id="api-key"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
                placeholder="Enter your API key"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Authentication key for secure API access (optional in dev mode)
              </p>
            </div>
          </div>
        </Card>

        {/* Development Settings */}
        <Card>
          <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Development Settings
          </h2>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                  Development Mode
                </h3>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Use mock data instead of real API calls
                </p>
              </div>
              <button
                type="button"
                className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                  devMode ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'
                }`}
                onClick={() => setDevMode(!devMode)}
              >
                <span
                  className={`pointer-events-none relative inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                    devMode ? 'translate-x-5' : 'translate-x-0'
                  }`}
                >
                  <span
                    className={`absolute inset-0 flex h-full w-full items-center justify-center transition-opacity ${
                      devMode ? 'opacity-0 duration-100 ease-out' : 'opacity-100 duration-200 ease-in'
                    }`}
                  >
                    <svg className="h-3 w-3 text-gray-400" fill="none" viewBox="0 0 12 12">
                      <path
                        d="M4 8l2-2m0 0l2-2M6 6L4 4m2 2l2 2"
                        stroke="currentColor"
                        strokeWidth={2}
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </span>
                  <span
                    className={`absolute inset-0 flex h-full w-full items-center justify-center transition-opacity ${
                      devMode ? 'opacity-100 duration-200 ease-in' : 'opacity-0 duration-100 ease-out'
                    }`}
                  >
                    <svg className="h-3 w-3 text-blue-600" fill="currentColor" viewBox="0 0 12 12">
                      <path d="M3.707 5.293a1 1 0 00-1.414 1.414l1.414-1.414zM5 8l-.707.707a1 1 0 001.414 0L5 8zm4.707-4.293a1 1 0 00-1.414-1.414l1.414 1.414zm-7.414 2l2 2 1.414-1.414-2-2-1.414 1.414zm3.414 2l4-4-1.414-1.414-4 4 1.414 1.414z" />
                    </svg>
                  </span>
                </span>
              </button>
            </div>
            
            <div className="rounded-lg bg-blue-50 p-4 dark:bg-blue-900/20">
              <h3 className="font-medium text-blue-800 dark:text-blue-200">
                Development Mode Information
              </h3>
              <p className="mt-1 text-sm text-blue-700 dark:text-blue-300">
                {devMode 
                  ? 'Development mode is ON. The application is using mock data for UI testing.' 
                  : 'Development mode is OFF. The application will connect to the real backend server.'}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Save Button */}
      <div className="mt-6">
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-medium text-gray-900 dark:text-white">
                Save Configuration
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Settings are automatically saved to your browser's local storage
              </p>
            </div>
            <Button
              variant="primary"
              onClick={saveSettings}
            >
              {saved ? 'Saved!' : 'Save Settings'}
            </Button>
          </div>
        </Card>
      </div>

      {/* Security Note */}
      <div className="mt-6 rounded-lg bg-yellow-50 p-4 dark:bg-yellow-900/20">
        <h3 className="font-medium text-yellow-800 dark:text-yellow-200">
          Security Notice
        </h3>
        <p className="mt-1 text-sm text-yellow-700 dark:text-yellow-300">
          API keys are stored locally in your browser. Never share your API key or commit 
          it to version control. In production environments, always use HTTPS to encrypt 
          communication between the frontend and backend.
        </p>
      </div>
    </div>
  );
};

export default SettingsPage;
