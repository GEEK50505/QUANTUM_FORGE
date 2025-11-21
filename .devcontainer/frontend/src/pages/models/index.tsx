// NOTE (permanent): This file contains educational notes for non-coders.
// Do not remove comments unless explicitly requested in a written instruction.
// These notes explain purpose, props, and data contract shapes.
//
// Module Purpose: Quantum/classical models management page
// What this file renders: Interface for viewing and managing simulation models
// How it fits into the Quantum Forge app: Provides model management for simulations
// Author: Qwen 3 Coder — Scaffold Stage

import React, { useState } from 'react';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Table from '../../components/ui/table';

/**
 * Models Page
 * 
 * Manages quantum and classical models used in simulations.
 * Displays model versions and deployment status.
 * 
 * For non-coders: This page shows the different computational models you can use
 * for your simulations. Think of models like different "recipes" for how to 
 * calculate the properties of molecules. Some are classical (traditional computing)
 * and some are quantum (using quantum mechanical principles).
 */
const ModelsPage: React.FC = () => {
  const [models, setModels] = useState([
    {
      id: 'mdl-001',
      name: 'UCCSD Ansatz',
      type: 'quantum',
      version: '2.1.0',
      createdAt: '2025-10-15',
      description: 'Unitary Coupled Cluster Singles and Doubles variational form',
      deployed: true
    },
    {
      id: 'mdl-002',
      name: 'DFT Functional B3LYP',
      type: 'classical',
      version: '1.0.0',
      createdAt: '2025-10-18',
      description: 'Becke three-parameter Lee-Yang-Parr density functional',
      deployed: true
    },
    {
      id: 'mdl-003',
      name: 'VQE with ADAPT',
      type: 'quantum',
      version: '1.2.3',
      createdAt: '2025-10-20',
      description: 'Adaptive Variational Quantum Eigensolver implementation',
      deployed: false
    }
  ]);
  
  const [showDeployModal, setShowDeployModal] = useState(false);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);

  // Handle deploy model
  const handleDeployModel = (modelId: string) => {
    // In a real app, this would deploy the model to the backend
    setModels(models.map(model => 
      model.id === modelId ? { ...model, deployed: true } : model
    ));
    setShowDeployModal(false);
    setSelectedModel(null);
    alert(`Model deployed successfully!`);
  };

  // Handle undeploy model
  const handleUndeployModel = (modelId: string) => {
    // In a real app, this would undeploy the model from the backend
    setModels(models.map(model => 
      model.id === modelId ? { ...model, deployed: false } : model
    ));
    alert(`Model undeployed successfully!`);
  };

  return (
    <div className="p-4 md:p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Models
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Quantum and classical models for simulations
        </p>
      </div>

      {/* Models Table */}
      <Card>
        <Table>
          <Table.Head>
            <Table.Row>
              <Table.HeaderCell>Name</Table.HeaderCell>
              <Table.HeaderCell>Type</Table.HeaderCell>
              <Table.HeaderCell>Description</Table.HeaderCell>
              <Table.HeaderCell>Version</Table.HeaderCell>
              <Table.HeaderCell>Created</Table.HeaderCell>
              <Table.HeaderCell>Status</Table.HeaderCell>
              <Table.HeaderCell>Actions</Table.HeaderCell>
            </Table.Row>
          </Table.Head>
          <Table.Body>
            {models.map((model) => (
              <Table.Row key={model.id}>
                <Table.Cell className="font-medium">{model.name}</Table.Cell>
                <Table.Cell>
                  <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    model.type === 'quantum' 
                      ? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-100' 
                      : 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100'
                  }`}>
                    {model.type}
                  </span>
                </Table.Cell>
                <Table.Cell>{model.description}</Table.Cell>
                <Table.Cell>v{model.version}</Table.Cell>
                <Table.Cell>{model.createdAt}</Table.Cell>
                <Table.Cell>
                  <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    model.deployed 
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100' 
                      : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100'
                  }`}>
                    {model.deployed ? 'Deployed' : 'Not Deployed'}
                  </span>
                </Table.Cell>
                <Table.Cell>
                  {model.deployed ? (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleUndeployModel(model.id)}
                    >
                      Undeploy
                    </Button>
                  ) : (
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => {
                        setSelectedModel(model.id);
                        setShowDeployModal(true);
                      }}
                    >
                      Deploy
                    </Button>
                  )}
                </Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table>
      </Card>
      
      {/* Model Information */}
      <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-2">
        <Card>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            Quantum Models
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Quantum models use quantum mechanical principles for more accurate 
            modeling of molecular systems. These are typically used for systems 
            where classical methods are insufficient.
          </p>
        </Card>
        
        <Card>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            Classical Models
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Classical models use traditional computing methods. They're fast and 
            reliable for many systems, especially larger molecules where quantum 
            effects are less important.
          </p>
        </Card>
      </div>
      
      {/* Deploy Confirmation Modal */}
      {showDeployModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
          <Card className="w-full max-w-md">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Deploy Model
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Are you sure you want to deploy this model? Deploying will make 
              it available for new simulations.
            </p>
            <div className="flex justify-end space-x-3">
              <Button
                variant="secondary"
                onClick={() => {
                  setShowDeployModal(false);
                  setSelectedModel(null);
                }}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={() => selectedModel && handleDeployModel(selectedModel)}
              >
                Deploy
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};

export default ModelsPage;
