// NOTE (permanent): This file contains educational notes for non-coders.
// Do not remove comments unless explicitly requested in a written instruction.
// These notes explain purpose, props, and data contract shapes.
//
// Module Purpose: Datasets management page
// What this file renders: Interface for uploading, viewing, and managing data assets
// How it fits into the Quantum Forge app: Provides dataset management for simulations
// Author: Qwen 3 Coder — Scaffold Stage

import React, { useState } from 'react';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Table from '../../components/ui/table';

/**
 * Datasets Page
 * 
 * Manages data assets used in quantum-classical simulations.
 * Provides upload, preview, and versioning capabilities for datasets.
 * 
 * For non-coders: This page lets you manage the data files that your simulations use.
 * You can upload new datasets, see existing ones, and download them. Each dataset
 * can have multiple versions, which is useful for tracking changes over time.
 */
const DatasetsPage: React.FC = () => {
  const [datasets, setDatasets] = useState([
    {
      id: 'ds-001',
      name: 'H2 Binding Energies',
      size: '2.4 MB',
      createdAt: '2025-10-20',
      version: '1.0.0',
      description: 'Experimental and calculated binding energies for hydrogen molecule'
    },
    {
      id: 'ds-002',
      name: 'LiH Geometry Scan',
      size: '5.7 MB',
      createdAt: '2025-10-22',
      version: '1.1.0',
      description: 'Complete geometry scan of lithium hydride molecule'
    }
  ]);
  
  const [showUpload, setShowUpload] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  // Handle file upload
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setUploadFile(e.target.files[0]);
    }
  };

  // Handle upload submission
  const handleUploadSubmit = () => {
    if (uploadFile) {
      // In a real app, this would upload the file to the server
      const newDataset = {
        id: `ds-${String(datasets.length + 1).padStart(3, '0')}`,
        name: uploadFile.name,
        size: `${(uploadFile.size / (1024 * 1024)).toFixed(1)} MB`,
        createdAt: new Date().toISOString().split('T')[0],
        version: '1.0.0',
        description: 'Newly uploaded dataset'
      };
      
      setDatasets([newDataset, ...datasets]);
      setUploadFile(null);
      setShowUpload(false);
      alert(`Dataset "${uploadFile.name}" uploaded successfully!`);
    }
  };

  return (
    <div className="p-4 md:p-6">
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Datasets
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Manage data assets for simulations
          </p>
        </div>
        <div className="mt-4 sm:mt-0">
          <Button 
            variant="primary"
            onClick={() => setShowUpload(true)}
            aria-label="Upload new dataset"
          >
            Upload Dataset
          </Button>
        </div>
      </div>

      {/* Upload Form (Hidden by default) */}
      {showUpload && (
        <Card className="mb-6">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Upload New Dataset
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Select File
              </label>
              <div className="flex items-center space-x-4">
                <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer bg-gray-50 dark:bg-gray-800 dark:border-gray-600">
                  <div className="flex flex-col items-center justify-center pt-5 pb-6">
                    <svg className="w-8 h-8 mb-4 text-gray-500 dark:text-gray-400" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 20 16">
                      <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 13h3a3 3 0 0 0 0-6h-.025A5.56 5.56 0 0 0 16 6.5 5.5 5.5 0 0 0 5.207 5.021C5.137 5.017 5.071 5 5 5a4 4 0 0 0 0 8h2.167M10 15V6m0 0L8 8m2-2 2 2"/>
                    </svg>
                    <p className="mb-2 text-sm text-gray-500 dark:text-gray-400">
                      <span className="font-semibold">Click to upload</span> or drag and drop
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      CSV, JSON, HDF5, or XYZ files (MAX. 100MB)
                    </p>
                  </div>
                  <input 
                    type="file" 
                    className="hidden" 
                    onChange={handleFileUpload}
                  />
                </label>
                
                {uploadFile && (
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-600 dark:text-gray-300">
                      {uploadFile.name}
                    </span>
                  </div>
                )}
              </div>
            </div>
            
            <div className="flex justify-end space-x-3">
              <Button
                variant="secondary"
                onClick={() => {
                  setShowUpload(false);
                  setUploadFile(null);
                }}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleUploadSubmit}
                disabled={!uploadFile}
              >
                Upload
              </Button>
            </div>
          </div>
        </Card>
      )}
      
      {/* Datasets Table */}
      <Card>
        <Table>
          <Table.Head>
            <Table.Row>
              <Table.HeaderCell>Name</Table.HeaderCell>
              <Table.HeaderCell>Description</Table.HeaderCell>
              <Table.HeaderCell>Size</Table.HeaderCell>
              <Table.HeaderCell>Version</Table.HeaderCell>
              <Table.HeaderCell>Created</Table.HeaderCell>
              <Table.HeaderCell>Actions</Table.HeaderCell>
            </Table.Row>
          </Table.Head>
          <Table.Body>
            {datasets.map((dataset) => (
              <Table.Row key={dataset.id}>
                <Table.Cell className="font-medium">{dataset.name}</Table.Cell>
                <Table.Cell>{dataset.description}</Table.Cell>
                <Table.Cell>{dataset.size}</Table.Cell>
                <Table.Cell>
                  <span className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800 dark:bg-blue-900 dark:text-blue-100">
                    v{dataset.version}
                  </span>
                </Table.Cell>
                <Table.Cell>{dataset.createdAt}</Table.Cell>
                <Table.Cell>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => alert(`Downloading ${dataset.name}...`)}
                  >
                    Download
                  </Button>
                </Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table>
      </Card>
      
      {/* Versioning Note */}
      <div className="mt-6 rounded-lg bg-blue-50 p-4 dark:bg-blue-900/20">
        <h3 className="font-medium text-blue-800 dark:text-blue-200">Dataset Versioning</h3>
        <p className="mt-1 text-sm text-blue-700 dark:text-blue-300">
          Each dataset can have multiple versions. When you upload a file with the same name,
          it will create a new version rather than replacing the existing dataset.
        </p>
      </div>
    </div>
  );
};

export default DatasetsPage;
