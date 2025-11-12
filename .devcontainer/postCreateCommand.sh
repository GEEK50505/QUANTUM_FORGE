#!/usr/bin/env bash
set -euo pipefail
echo "Running devcontainer post-create setup..."
cd /workspace

# Create and activate virtualenv
if [ ! -d ".venv" ]; then
  python -m venv .venv
fi
. .venv/bin/activate
pip install --upgrade pip

# Install Python deps
if [ -f requirements.txt ]; then
  pip install -r requirements.txt
fi

# Install frontend deps
if [ -d frontend ]; then
  cd frontend
  if [ -f package-lock.json ]; then
    npm ci
  else
    npm install
  fi
  cd ..
fi

# Ensure a real `xtb` binary is available. Prefer an existing system binary, otherwise
# install xTB from conda-forge into a conda env and create a small wrapper at /usr/local/bin/xtb.
if command -v xtb >/dev/null 2>&1; then
  echo "Found xtb at $(command -v xtb) — using system xtb"
else
  echo "No xtb found in PATH — installing Miniconda + xTB (conda-forge)..."
  # Install Miniconda to /opt/miniconda if not present
  if [ ! -d /opt/miniconda ]; then
    curl -fsSL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o /tmp/miniconda.sh
    bash /tmp/miniconda.sh -b -p /opt/miniconda
    rm -f /tmp/miniconda.sh
  fi
  export PATH="/opt/miniconda/bin:$PATH"
  # Initialize conda and make sure conda is usable in non-interactive shells
  /opt/miniconda/bin/conda init bash || true
  /opt/miniconda/bin/conda config --set always_yes yes --set changeps1 no || true
  /opt/miniconda/bin/conda update -n base -c defaults conda || true

  # Create or update an environment that contains xtb
  if /opt/miniconda/bin/conda env list | grep -q "xtb_env"; then
    echo "conda env 'xtb_env' already exists — ensuring xtb is installed"
    /opt/miniconda/bin/conda install -n xtb_env -c conda-forge xtb || true
  else
    /opt/miniconda/bin/conda create -n xtb_env -c conda-forge xtb || true
  fi

  # Create a small wrapper so calling `xtb` activates the conda env and runs the binary
  cat >/usr/local/bin/xtb <<'EOF'
#!/usr/bin/env bash
source /opt/miniconda/etc/profile.d/conda.sh
conda activate xtb_env
xtb "$@"
EOF
  chmod +x /usr/local/bin/xtb || true
  echo "Installed wrapper /usr/local/bin/xtb -> activates conda env 'xtb_env'"
fi

# Ensure jobs dir exists
mkdir -p /workspace/jobs
chown -R vscode:vscode /workspace/jobs || true

echo "Devcontainer post-create completed."
