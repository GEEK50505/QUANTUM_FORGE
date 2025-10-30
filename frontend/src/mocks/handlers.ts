import { rest } from 'msw';

// Mock API handlers
export const handlers = [
  // Mock quantum simulation job submission
  rest.post('/api/simulations', (req, res, ctx) => {
    return res(
      ctx.status(201),
      ctx.json({
        id: Math.random().toString(36).substr(2, 9),
        status: 'queued',
        createdAt: new Date().toISOString(),
      })
    );
  }),

  // Mock simulation results
  rest.get('/api/simulations/:id', (req, res, ctx) => {
    const { id } = req.params;
    return res(
      ctx.status(200),
      ctx.json({
        id,
        status: 'completed',
        results: {
          eigenvalues: [-1.5, 0.5, 1.0],
          probabilities: [0.25, 0.5, 0.25],
          quantum_state: '|ψ⟩ = 0.5|0⟩ + 0.707|1⟩ + 0.5|2⟩',
        },
        createdAt: new Date().toISOString(),
        completedAt: new Date().toISOString(),
      })
    );
  }),

  // Mock quantum system configurations
  rest.get('/api/configs', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json([
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
      ])
    );
  }),
];