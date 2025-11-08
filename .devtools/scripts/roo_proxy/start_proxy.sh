#!/bin/bash

# Roo Code proxy startup script - starts the proxy and key tester
# This script runs when VS Code opens the workspace via tasks.json

set -e

# Ensure we're in the project root
cd "$(dirname "$0")/../.."

# Create Python venv if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Install required packages if not present
if ! python3 -c "import aiohttp" 2>/dev/null; then
    echo "Installing required packages..."
    pip install aiohttp
fi

# Start key tester in background
echo "Starting key tester..."
BEST_ENV="scripts/roo_proxy/.env"
# If .env created by key_tester exists, source it to get OPENROUTER_API_KEY
if [ -f "$BEST_ENV" ]; then
    # shellcheck disable=SC1090
    source "$BEST_ENV"
fi

if [ -n "$OPENROUTER_API_KEY" ]; then
    export ROO_CODE_API_KEY="$OPENROUTER_API_KEY"
    echo "Loaded API key from $BEST_ENV and exported to ROO_CODE_API_KEY"
else
    # Run tester to obtain best key (best_only prints key string)
    mkdir -p .vscode
    python3 scripts/roo_proxy/key_tester.py --keys-file scripts/roo_proxy/keys.json --best-only > .vscode/current_key.txt || true

    if [ -s ".vscode/current_key.txt" ]; then
        export ROO_CODE_API_KEY=$(cat .vscode/current_key.txt)
        echo "Best key selected and exported to ROO_CODE_API_KEY"
    else
        echo "No valid keys found!"
        # If there is a persisted best_key.json, try to load it
        if [ -f "scripts/roo_proxy/best_key.json" ]; then
            export ROO_CODE_API_KEY=$(python3 -c "import json;print(json.load(open('scripts/roo_proxy/best_key.json'))['best_key'])")
            if [ -n "$ROO_CODE_API_KEY" ]; then
                echo "Loaded persisted best key into ROO_CODE_API_KEY"
            else
                echo "No usable persisted key either. Exiting."
                exit 1
            fi
        else
            exit 1
        fi
    fi
fi

# Start background watcher (periodic re-check) if not already running
LOG_FILE="scripts/roo_proxy/key_tester.log"
PID_FILE=".vscode/roo_key_tester.pid"
if [ -f "$PID_FILE" ]; then
    pid=$(cat "$PID_FILE")
    if ps -p "$pid" > /dev/null 2>&1; then
        echo "Key tester watcher already running (pid=$pid)"
    else
        rm -f "$PID_FILE"
    fi
fi

if [ ! -f "$PID_FILE" ]; then
    # start watcher in background: probe every 300s (5min)
    nohup python3 scripts/roo_proxy/key_tester.py --keys-file scripts/roo_proxy/keys.json --interval 300 --working-file scripts/roo_proxy/working_keys.json --verbose > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    echo "Started key tester watcher (logging to $LOG_FILE), pid=$(cat $PID_FILE)"
fi