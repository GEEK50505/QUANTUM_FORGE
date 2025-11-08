#!/bin/bash
# Setup script for Quantum_Forge on Ubuntu with Anaconda

set -e  # Exit on error

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Quantum_Forge environment setup..."

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Check Conda in ~/anaconda3
if [ -f "$HOME/anaconda3/bin/conda" ]; then
    log_message "Conda found at $HOME/anaconda3/bin/conda"
    export PATH="$HOME/anaconda3/bin:$PATH"
    
    # Initialize conda for bash
    if [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
        source "$HOME/anaconda3/etc/profile.d/conda.sh"
    fi
else
    log_message "ERROR: Conda not found in $HOME/anaconda3"
    exit 1
fi

# Check if environment already exists
if conda env list | grep -q "quantum_forge"; then
    log_message "Environment 'quantum_forge' already exists. Updating..."
else
    log_message "Creating conda environment..."
    conda create -n quantum_forge python=3.11 -y
fi

log_message "Activating environment..."
conda activate quantum_forge

log_message "Installing xTB from conda-forge..."
conda install -c conda-forge xtb -y

log_message "Verifying xTB installation..."
if xtb --version; then
    log_message "✓ xTB installation verified successfully"
else
    log_message "ERROR: xTB installation failed"
    exit 1
fi

log_message "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    log_message "WARNING: requirements.txt not found, installing core dependencies..."
    pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 pydantic==2.5.0 python-multipart==0.0.6 python-dotenv==1.0.0 aiofiles==23.2.1 numpy==1.24.3 scipy==1.11.2 pandas==2.0.3
fi

log_message "Setting up environment variables..."
# Create logs, jobs, and runs directories
mkdir -p logs jobs runs

# Export environment variables
export PYTHONPATH="${PWD}:${PYTHONPATH}"
export XTB_PATH=$(which xtb)

log_message "PYTHONPATH set to: $PYTHONPATH"
log_message "XTB_PATH set to: $XTB_PATH"

log_message "✓ Environment setup complete!"
log_message "To activate the environment, run: source ~/anaconda3/etc/profile.d/conda.sh && conda activate quantum_forge"