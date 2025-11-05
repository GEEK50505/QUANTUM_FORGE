import { http } from 'msw';

// Mock API handlers
export const handlers = [
  // Mock quantum simulation job submission
  http.post('/api/simulations', () => {
    return Response.json({
      id: Math.random().toString(36).substr(2, 9),
      status: 'queued',
      createdAt: new Date().toISOString(),
    }, { status: 201 });
  }),

  // Mock simulation results
  http.get('/api/simulations/:id', ({ params }) => {
    const { id } = params;
    return Response.json({
      id,
      status: 'completed',
      results: {
        eigenvalues: [-1.5, 0.5, 1.0],
        probabilities: [0.25, 0.5, 0.25],
        quantum_state: '|ψ⟩ = 0.5|0⟩ + 0.707|1⟩ + 0.5|2⟩',
      },
      createdAt: new Date().toISOString(),
      completedAt: new Date().toISOString(),
    });
  }),

  // Mock quantum system configurations
  http.get('/api/configs', () => {
    return Response.json([
      {
        id: 'config1',
        name: 'Two-qubit system',
        description: 'Basic two-qubit quantum system simulation',
        parameters: {
          qubits: 2,
          gates: ['H', 'CNOT', 'X', 'Y', 'Z'],
          measurements: ['Z', 'X'],
        },
      },
      {
        id: 'config2',
        name: 'Three-qubit error correction',
        description: 'Three-qubit quantum error correction circuit',
        parameters: {
          qubits: 3,
          gates: ['H', 'CNOT', 'X', 'Y', 'Z', 'T'],
          measurements: ['Z'],
        },
      },
    ]);
  }),
];