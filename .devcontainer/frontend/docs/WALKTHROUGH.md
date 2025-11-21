# Quantum Forge Frontend Walkthrough

## Getting Started for Non-Programmers

This document provides a step-by-step guide for scientists and researchers to use the Quantum Forge frontend application without requiring programming knowledge.

## What is Quantum Forge?

Quantum Forge is a hybrid quantum-classical simulation platform that allows you to:
- Run computational simulations of molecular systems
- Compare different computational methods (classical vs quantum)
- Analyze results and visualize data
- Manage datasets and computational models

Think of it as a sophisticated laboratory notebook for computational chemistry, but with the added power of quantum computing.

## Quick Start Guide

### 1. Starting the Development Server

To run the application locally on your computer:

1. Open your terminal or command prompt
2. Navigate to the project directory:
   ```bash
   cd path/to/quantum-forge-frontend
   ```
3. Install dependencies (only needed the first time):
   ```bash
   npm install
   ```
4. Start the development server:
   ```bash
   npm run dev
   ```

5. Open your web browser and go to: http://localhost:5173

You should see the Quantum Forge dashboard with a "Run Demo" button.

### 2. Running Your First Simulation

1. **Dashboard Overview**
   - The dashboard shows key metrics about your computational work
   - KPI cards display total jobs, running simulations, and recent results
   - The main area has simulation controls to start new jobs

2. **Running a Demo**
   - Click the large "Run Demo" button in the Simulation Controls section
   - A dropdown will appear with three options:
     - **Classical**: Fast CPU-based simulation (good for initial approximations)
     - **Quantum-stub**: Simulated quantum computation (demonstrates quantum workflow)
     - **Hybrid**: Combination of classical and quantum methods
   - Select any option to start a sample simulation

3. **Viewing Simulation Progress**
   - After starting a simulation, you'll see it appear in the Recent Jobs table
   - Click "View All Simulations" to see the complete list
   - Jobs will show status: Queued, Running, Completed, or Failed

### 3. Exploring Simulation Results

1. **Simulation List Page**
   - Navigate to "Simulations" in the left sidebar
   - This page shows all your computational jobs
   - You can filter by status (Completed, Running, etc.)
   - Click any job to see detailed results

2. **Job Detail View**
   - Click on a completed job to see its details
   - The left panel shows metadata (when it ran, what method was used)
   - The right panel has tabs for:
     - **Logs**: Step-by-step record of the computation
     - **Results**: Numerical data in JSON format
     - **Visualizations**: Energy plots (currently placeholders)

3. **Downloading Results**
   - In the job detail view, click "Download Artifact"
   - This would download the raw computational data for further analysis

### 4. Creating New Simulations

1. **Starting the Wizard**
   - From the Simulations page, click "Create New Job"
   - Or from the Dashboard, click "Create New Simulation"

2. **Step 1: Select System**
   - Choose what molecule or system to simulate:
     - **H2**: Simple hydrogen molecule (good for testing)
     - **LiH**: Lithium hydride (small molecule with ionic character)
     - **H2O**: Water molecule (common with bent geometry)
     - **SiCluster**: Silicon nanocluster (more complex system)

3. **Step 2: Configure Parameters**
   - **Computational Backend**:
     - Classical: Fast traditional computing methods
     - Quantum: Uses quantum mechanical principles (more accurate but slower)
     - Hybrid: Combines both for optimal balance
   - **Quantum-specific parameters** (if using quantum or hybrid):
     - **Qubits**: Number of quantum bits (more = larger systems but more resources)
     - **Shots**: Number of measurements (more = better accuracy but longer time)
     - **Optimizer**: Algorithm for finding minimum energy (VQE, QAOA, etc.)

4. **Step 3: Review and Start**
   - Review your configuration choices
   - Click "Start Simulation" to begin the computation
   - The job will appear in your simulations list

### 5. Analyzing Results with Experiments

1. **Comparing Jobs**
   - Navigate to "Experiments" in the sidebar
   - This page lets you compare multiple simulation runs
   - Select 2-3 jobs using the checkboxes
   - View side-by-side comparisons of:
     - Energy results (accuracy comparison)
     - Runtime performance (speed comparison)
     - Method effectiveness

2. **Energy Difference Analysis**
   - The system automatically calculates energy differences
   - This helps determine which method gives the most accurate results
   - Lower energy typically means more stable molecular configuration

### 6. Managing Data and Models

1. **Datasets**
   - Navigate to "Datasets" to manage input data
   - Upload experimental data or computational results
   - Download datasets for use in other software
   - Version control ensures you can track data changes

2. **Models**
   - Navigate to "Models" to see available computational methods
   - Models are like "recipes" for how to perform calculations
   - Deploy models to make them available for new simulations
   - Quantum models use quantum mechanics for higher accuracy
   - Classical models use traditional computing for speed

### 7. Configuration and Settings

1. **Settings Page**
   - Access via "Settings" in the sidebar or user menu
   - **Development Mode**: Toggle between mock data (for testing) and real backend
   - **Backend Endpoint**: Configure where the computational server is located
   - **API Keys**: Manage secure access credentials

2. **User Profile**
   - Access via your user icon in the top right
   - Update your personal information
   - Change your password
   - Manage API keys for programmatic access

## Understanding Key Concepts

### What are Qubits?
Qubits are the basic units of quantum information, similar to bits in classical computers but with quantum properties that allow for more complex calculations.

### What is a VQE?
Variational Quantum Eigensolver (VQE) is a quantum algorithm used to find the lowest energy state of molecules, which is crucial for understanding chemical properties.

### What are Shots?
In quantum computing, shots are repeated measurements of a quantum state. More shots generally lead to more accurate results but take longer to compute.

### What is an Optimizer?
An optimizer is an algorithm that adjusts parameters to minimize or maximize a function. In quantum chemistry, it's used to find the lowest energy configuration of a molecule.

## Troubleshooting Common Issues

### Application Won't Start
1. Ensure Node.js is installed (version 16 or higher)
2. Check that all dependencies installed successfully
3. Make sure port 5173 is not being used by another application

### Simulations Stuck in "Queued" or "Running"
1. In development mode, simulations are simulated and will complete automatically
2. If using real backend, check that the computational server is running
3. Verify backend endpoint in Settings is correct

### No Data Displaying
1. Ensure Development Mode is enabled in Settings for mock data
2. If using real backend, verify API connection and credentials

## Next Steps for Research

1. **Run systematic comparisons** of different methods on the same molecule
2. **Upload your own datasets** for custom simulations
3. **Experiment with different parameters** to understand their effects
4. **Use the Experiments page** to analyze method accuracy
5. **Document your findings** in the job notes for future reference

## Getting Help

- Refer to the educational comments throughout the codebase for detailed explanations
- Check the FRONTEND_README.md for technical documentation
- Review the CHANGELOG.md for recent changes and features
- Contact the development team for feature requests or bug reports

This walkthrough should provide everything you need to start using Quantum Forge for your computational chemistry research, even without programming experience.
