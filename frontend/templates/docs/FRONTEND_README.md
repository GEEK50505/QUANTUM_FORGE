# Quantum Forge Frontend Documentation

## Overview

This is the frontend application for the Quantum Forge platform - a hybrid quantum-classical simulation platform. The frontend is built with React and TypeScript, using Tailwind CSS for styling.

## Component Map

### Core Layout Components
- `AppLayout` - Main application layout with sidebar and content area
- `AppSidebar` - Navigation sidebar with all main sections
- `AppHeader` - Top navigation bar with user controls

### UI Components
- `Button` - Reusable button component with variants
- `Card` - Content container with consistent styling
- `Table` - Data table component for displaying tabular data
- `Modal` - Overlay dialog for forms and confirmations

### Pages
- `Dashboard` - Main overview with KPIs and simulation controls
- `Simulations` - Job management (list, detail, new wizard)
- `Datasets` - Data asset management
- `Models` - Quantum/classical model management
- `Experiments` - Job comparison and analysis
- `Settings` - Application configuration
- `Auth` - Authentication pages (login, profile)

## Data Contract Expectations

### Simulation Job Object
```json
{
  "id": "sim-001",
  "name": "H2 Ground State Calculation",
  "type": "quantum",
  "status": "completed",
  "createdAt": "2025-10-25T10:30:00Z",
  "startedAt": "2025-10-25T10:31:00Z",
  "completedAt": "2025-10-25T10:35:00Z",
  "duration": 240,
  "energy": -1.137,
  "qubits": 4,
  "shots": 1024,
  "optimizer": "VQE"
}
```

### Dataset Object
```json
{
  "id": "ds-001",
  "name": "H2 Binding Energies",
  "size": 2.4,
  "createdAt": "2025-10-20T09:00:00Z",
  "version": "1.0.0",
  "description": "Experimental and calculated binding energies for hydrogen molecule"
}
```

### Model Object
```json
{
  "id": "mdl-001",
  "name": "UCCSD Ansatz",
  "type": "quantum",
  "version": "2.1.0",
  "createdAt": "2025-10-15T11:20:00Z",
  "description": "Unitary Coupled Cluster Singles and Doubles variational form",
  "deployed": true
}
```

## Development Setup

### Prerequisites
- Node.js (version 16 or higher)
- npm or yarn

### Installation
```bash
npm install
```

### Running Development Server
```bash
npm run dev
```

The application will be available at http://localhost:5173

### Building for Production
```bash
npm run build
```

## Switching from Mock to Real API

The application uses mock data in development mode. To switch to a real backend:

1. Set `DEV_MODE` to `false` in `src/utils/constants.ts`
2. Ensure the backend endpoint in Settings matches your backend server
3. Restart the development server

## User Workflow

### Starting a Demo Simulation
1. Navigate to the Dashboard
2. Use the "Run Demo" button in the Simulation Controls section
3. Select simulation type (classical, quantum-stub, hybrid)
4. View the job in the Simulations list

### Creating a New Simulation
1. Go to Simulations → New Job
2. Step 1: Select a molecular system
3. Step 2: Configure backend parameters
4. Step 3: Review settings and start simulation

### Comparing Results
1. Go to Experiments
2. Select multiple jobs from the table
3. View energy and performance comparisons
4. Analyze results side-by-side

## Troubleshooting

### Common Issues
1. **TypeScript errors**: Run `npm run type-check` to see all type issues
2. **Styling issues**: Ensure Tailwind CSS is properly configured
3. **API connection**: Check that DEV_MODE is set correctly in Settings

### Development Tips
- Use the Settings page to toggle development mode
- Mock data is defined in `src/hooks/useMockApi.ts`
- All UI components are in `src/components/ui/`
