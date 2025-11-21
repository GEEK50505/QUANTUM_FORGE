# Development Environment Setup

This guide explains how to set up your development environment for QUANTUM_FORGE.

## Prerequisites

1. VS Code with recommended extensions:
   - Python
   - Jupyter
   - ESLint
   - Prettier

2. Python 3.8+ with venv

3. Node.js 16+

## Initial Setup

1. Clone the repository and navigate to it:
```bash
git clone https://github.com/GEEK50505/QUANTUM_FORGE.git
cd QUANTUM_FORGE
```

2. Copy development environment templates:
```bash
cp .devtools/vscode/settings.json.example .vscode/settings.json
cp .devtools/vscode/launch.json.example .vscode/launch.json
```

3. Create Python virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Extension Setup

### Roo Code Setup
1. Copy the example configuration:
```bash
cp .devtools/extensions/roo/config.example.json .devtools/extensions/roo/config.json
```

2. Set up your API key:
```bash
.devtools/scripts/setup_roo_key.sh
```

### Cline Setup
1. Initialize Cline configuration:
```bash
cp .devtools/extensions/cline/config.example.yaml .devtools/extensions/cline/config.yaml
```

## Development Workflow

1. Start the backend:
   - Use VS Code's Run and Debug panel
   - Select "Python: FastAPI" configuration
   - Press F5 or click "Start Debugging"

2. Start the frontend:
```bash
cd frontend
npm install
npm run dev
```

3. Access the application:
   - Backend API: http://localhost:8000
   - Frontend: http://localhost:3000
   - API Documentation: http://localhost:8000/docs

## Troubleshooting

If you encounter issues:

1. Check the logs in `.devtools/logs/`
2. Verify your Python virtual environment is activated
3. Ensure all required extensions are installed
4. Review the configuration files in `.devtools/`

## Additional Tools

- `scripts/setup_environment.sh`: Full environment setup
- `scripts/run_tests.sh`: Run test suite
- `scripts/clean.sh`: Clean temporary files