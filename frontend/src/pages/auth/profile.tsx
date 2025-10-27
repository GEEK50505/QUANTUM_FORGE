// NOTE (permanent): This file contains educational notes for non-coders.
// Do not remove comments unless explicitly requested in a written instruction.
// These notes explain purpose, props, and data contract shapes.
//
// Module Purpose: User profile management page
// What this file renders: Interface for managing user profile and API keys
// How it fits into the Quantum Forge app: Provides user account management
// Author: Qwen 3 Coder — Scaffold Stage

import React, { useState } from 'react';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';

/**
 * Profile Page
 * 
 * User profile management page for the Quantum Forge application.
 * Allows users to manage their account settings and API keys.
 * 
 * For non-coders: This page lets you manage your user profile and API keys.
 * API keys are like passwords that allow other applications to securely
 * access the Quantum Forge backend on your behalf.
 */
const ProfilePage: React.FC = () => {
  const [name, setName] = useState('John Scientist');
  const [email, setEmail] = useState('john.scientist@example.com');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [apiKeys, setApiKeys] = useState([
    { id: 'key-001', name: 'Development Key', key: 'qf_dev_key_12345', createdAt: '2025-10-20', lastUsed: '2025-10-25' },
    { id: 'key-002', name: 'Production Key', key: 'qf_prod_key_67890', createdAt: '2025-10-22', lastUsed: 'Never' }
  ]);
  const [newKeyName, setNewKeyName] = useState('');

  // Handle profile update
  const handleUpdateProfile = (e: React.FormEvent) => {
    e.preventDefault();
    // In a real app, this would update the user's profile
    console.log('Profile update with:', { name, email });
    alert('Profile updated successfully!');
  };

  // Handle password change
  const handleChangePassword = (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      alert('New passwords do not match!');
      return;
    }
    // In a real app, this would change the user's password
    console.log('Password change with:', { currentPassword, newPassword });
    alert('Password changed successfully!');
    setCurrentPassword('');
    setNewPassword('');
    setConfirmPassword('');
  };

  // Handle generate new API key
  const handleGenerateApiKey = () => {
    if (!newKeyName.trim()) {
      alert('Please enter a name for your API key');
      return;
    }
    
    // In a real app, this would generate a new API key on the backend
    const newKey = {
      id: `key-${String(apiKeys.length + 1).padStart(3, '0')}`,
      name: newKeyName,
      key: `qf_key_${Math.random().toString(36).substr(2, 10)}`,
      createdAt: new Date().toISOString().split('T')[0],
      lastUsed: 'Never'
    };
    
    setApiKeys([...apiKeys, newKey]);
    setNewKeyName('');
    alert(`API key "${newKeyName}" generated successfully!`);
  };

  // Handle revoke API key
  const handleRevokeApiKey = (keyId: string) => {
    // In a real app, this would revoke the API key on the backend
    setApiKeys(apiKeys.filter(key => key.id !== keyId));
    alert('API key revoked successfully!');
  };

  return (
    <div className="p-4 md:p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Profile
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Manage your account settings and API keys
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Profile Information */}
        <Card>
          <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Profile Information
          </h2>
          
          <form onSubmit={handleUpdateProfile} className="space-y-4">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Full Name
              </label>
              <input
                type="text"
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
              />
            </div>
            
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Email Address
              </label>
              <input
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
              />
            </div>
            
            <div>
              <Button type="submit" variant="primary">
                Update Profile
              </Button>
            </div>
          </form>
        </Card>

        {/* Change Password */}
        <Card>
          <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Change Password
          </h2>
          
          <form onSubmit={handleChangePassword} className="space-y-4">
            <div>
              <label htmlFor="current-password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Current Password
              </label>
              <input
                type="password"
                id="current-password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
              />
            </div>
            
            <div>
              <label htmlFor="new-password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                New Password
              </label>
              <input
                type="password"
                id="new-password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
              />
            </div>
            
            <div>
              <label htmlFor="confirm-password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Confirm New Password
              </label>
              <input
                type="password"
                id="confirm-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
              />
            </div>
            
            <div>
              <Button type="submit" variant="primary">
                Change Password
              </Button>
            </div>
          </form>
        </Card>
      </div>

      {/* API Keys */}
      <div className="mt-6">
        <Card>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4">
            <div>
              <h2 className="text-lg font-medium text-gray-900 dark:text-white">
                API Keys
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Manage your API keys for programmatic access
              </p>
            </div>
            <div className="mt-4 sm:mt-0">
              <Button
                variant="primary"
                onClick={handleGenerateApiKey}
              >
                Generate New Key
              </Button>
            </div>
          </div>
          
          <div className="mb-4">
            <label htmlFor="new-key-name" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              New API Key Name
            </label>
            <div className="flex space-x-2">
              <input
                type="text"
                id="new-key-name"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                placeholder="Enter a name for your new API key"
                className="flex-1 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
              />
            </div>
          </div>
          
          <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 rounded-lg">
            <table className="min-w-full divide-y divide-gray-300 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th scope="col" className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 dark:text-white sm:pl-6">
                    Name
                  </th>
                  <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-white">
                    Key
                  </th>
                  <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-white">
                    Created
                  </th>
                  <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-white">
                    Last Used
                  </th>
                  <th scope="col" className="relative py-3.5 pl-3 pr-4 sm:pr-6">
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-900">
                {apiKeys.map((key) => (
                  <tr key={key.id}>
                    <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 dark:text-white sm:pl-6">
                      {key.name}
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500 dark:text-gray-400 font-mono">
                      {key.key}
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500 dark:text-gray-400">
                      {key.createdAt}
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500 dark:text-gray-400">
                      {key.lastUsed}
                    </td>
                    <td className="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-6">
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => handleRevokeApiKey(key.id)}
                      >
                        Revoke
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      {/* Security Note */}
      <div className="mt-6 rounded-lg bg-yellow-50 p-4 dark:bg-yellow-900/20">
        <h3 className="font-medium text-yellow-800 dark:text-yellow-200">
          API Key Security
        </h3>
        <p className="mt-1 text-sm text-yellow-700 dark:text-yellow-300">
          Store your API keys securely and never share them. If you believe a key has been compromised, 
          revoke it immediately and generate a new one. API keys have the same permissions as your account.
        </p>
      </div>
    </div>
  );
};

export default ProfilePage;
