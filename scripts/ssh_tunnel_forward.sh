#!/usr/bin/env bash
set -euo pipefail

# Helper to create an SSH local forward to a remote DB and verify connectivity
# Usage: ./scripts/ssh_tunnel_forward.sh <gateway_user@host> [remote_db_host] [local_port] [container_name]

GATEWAY=${1:-}
REMOTE_DB_HOST=${2:-db.nngouhsytgytiibmufvt.supabase.co}
LOCAL_PORT=${3:-15432}
CONTAINER_NAME=${4:-quantum_dev}

usage(){
  cat <<USAGE
Usage: $0 <gateway_user@host> [remote_db_host] [local_port] [container_name]

Example:
  $0 alice@gateway.example.com db.nngouhsytgytiibmufvt.supabase.co 15432 quantum_dev

If you omit arguments the script will prompt for the gateway (user@host).
USAGE
}

if [[ -z "$GATEWAY" ]]; then
  read -rp "Enter gateway (user@host): " GATEWAY
  if [[ -z "$GATEWAY" ]]; then
    usage
    exit 1
  fi
fi

echo "Using gateway: $GATEWAY"
echo "Remote DB host: $REMOTE_DB_HOST"
echo "Local port: $LOCAL_PORT"
echo "Container name: $CONTAINER_NAME"

# check if something already listening on the local port
if ss -ltnp 2>/dev/null | grep -q ":${LOCAL_PORT} "; then
  echo "Port ${LOCAL_PORT} already has a listener. Showing matching lines:"
  ss -ltnp | grep ":${LOCAL_PORT} " || true
  echo "If that's from a previous ssh tunnel you can skip creating a new one. Exiting."
  exit 0
fi

echo "Starting SSH local forward... (you may be prompted for an SSH password/key passphrase)"
if ! ssh -f -N -L ${LOCAL_PORT}:${REMOTE_DB_HOST}:5432 ${GATEWAY}; then
  echo "Initial ssh -f attempt failed. Retrying in foreground with verbose output for debugging..."
  ssh -v -L ${LOCAL_PORT}:${REMOTE_DB_HOST}:5432 ${GATEWAY}
  exit 1
fi

sleep 1

echo "Verifying listener on devcontainer host..."
if ss -ltnp 2>/dev/null | grep -q ":${LOCAL_PORT} "; then
  ss -ltnp | grep ":${LOCAL_PORT} "
else
  echo "No listener found on port ${LOCAL_PORT}. Tunnel likely failed to start."
  exit 2
fi

echo "Testing TCP connect on host to forwarded port..."
if nc -vz 127.0.0.1 ${LOCAL_PORT}; then
  echo "Host -> forwarded port OK"
else
  echo "Host -> forwarded port FAILED (connection refused or timed out)"
  exit 3
fi

echo "Testing connectivity from inside container '${CONTAINER_NAME}'"
if ! docker ps --filter "name=${CONTAINER_NAME}" --format '{{.Names}}' | grep -q "${CONTAINER_NAME}"; then
  echo "Container ${CONTAINER_NAME} not running or not found. Skipping container tests."
  exit 0
fi

HOST_IP=$(docker exec ${CONTAINER_NAME} sh -c "ip route | awk '/default/ {print \$3; exit}'" || true)
if [[ -z "$HOST_IP" ]]; then
  echo "Could not determine host gateway IP from container. Try using host.docker.internal or inspect 'ip route' inside container."
  docker exec ${CONTAINER_NAME} sh -c "ip route || true"
  exit 0
fi

echo "Container sees host IP: $HOST_IP"
echo "Testing container -> host:$LOCAL_PORT"
if docker exec ${CONTAINER_NAME} sh -c "nc -vz ${HOST_IP} ${LOCAL_PORT}"; then
  echo "Container -> forwarded port OK"
  echo "Tunnel established and verified. You can now start the worker inside the devcontainer and point DATABASE_URL to ${HOST_IP}:${LOCAL_PORT}"
  exit 0
else
  echo "Container -> forwarded port FAILED"
  echo "Try testing 'nc -vz ${HOST_IP} ${LOCAL_PORT}' inside the container to see errors."
  exit 4
fi
