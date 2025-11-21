#!/bin/bash

echo "[$(date)] Starting Quantum_Forge development environment..."

# Activate conda environment (requires sudo access to root anaconda)
echo "[$(date)] Activating conda environment..."
sudo /root/anaconda3/bin/conda activate quantum_forge

# Verify xTB is available
echo "[$(date)] Verifying xTB installation..."
if sudo /root/anaconda3/bin/conda run -n quantum_forge xtb --version; then
    echo "[$(date)] xTB installation verified"
else
    echo "ERROR: xTB not available. Run setup_environment.sh first."
    exit 1
fi

# Create necessary directories
mkdir -p logs jobs runs

# Start backend server
echo "[$(date)] Starting FastAPI backend on http://localhost:8000"
cd backend
sudo /root/anaconda3/bin/conda run -n quantum_forge uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to be ready
sleep 3

# Start frontend server (if not already running)
echo "[$(date)] Starting React frontend on http://localhost:5173"
cd ../frontend
npm run dev &
FRONTEND_PID=$!

# Trap to cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID" EXIT

echo "[$(date)] ✓ Both servers running!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"

wait