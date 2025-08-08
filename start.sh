#!/usr/bin/env bash
set -euo pipefail

echo "\n🚀 Starting Trade Strategies Dev Environment"
echo "=========================================="

# Load environment variables if present
if [[ -f .env ]]; then
  echo "📋 Loading backend env from .env"
  set -a; source .env; set +a
fi
if [[ -f .env.local ]]; then
  echo "📋 Loading frontend env from .env.local"
  set -a; source .env.local; set +a
fi

# Helper: find a free TCP port starting from given one
find_free_port() {
  local port="$1"
  while lsof -iTCP:"${port}" -sTCP:LISTEN >/dev/null 2>&1; do
    port=$((port+1))
  done
  echo "$port"
}

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_BIN="$ROOT_DIR/.venv/bin"

if [[ ! -x "$VENV_BIN/uvicorn" ]]; then
  echo "⚠️  Python venv not found or uvicorn missing at $VENV_BIN/uvicorn"
  echo "   Create venv and install deps: python3 -m venv .venv && .venv/bin/pip install -U pip && .venv/bin/pip install -r requirements.txt"
  exit 1
fi

# Ports (allow override via API_PORT and PORT)
REQ_BACKEND_PORT="${API_PORT:-8000}"
REQ_FRONTEND_PORT="${PORT:-3000}"
BACKEND_PORT="$(find_free_port "$REQ_BACKEND_PORT")"
FRONTEND_PORT="$(find_free_port "$REQ_FRONTEND_PORT")"

# Decide DB mode: default to SQLite unless Postgres env is provided
if [[ -n "${DB_USER:-}" || -n "${DATABASE_URL:-}" ]]; then
  export USE_SQLITE="false"
  export AUTO_CREATE_TABLES="${AUTO_CREATE_TABLES:-true}"
  echo "🗄️  Using Postgres (AUTO_CREATE_TABLES=${AUTO_CREATE_TABLES})"
else
  export USE_SQLITE="${USE_SQLITE:-true}"
  echo "🗄️  Using SQLite (USE_SQLITE=${USE_SQLITE})"
fi

# Graceful shutdown
PIDS=()
cleanup() {
  echo "\n🧹 Shutting down..."
  for pid in "${PIDS[@]:-}"; do
    if kill -0 "$pid" >/dev/null 2>&1; then
      kill "$pid" >/dev/null 2>&1 || true
      wait "$pid" 2>/dev/null || true
    fi
  done
  echo "✅ Stopped"
}
trap cleanup INT TERM EXIT

# Start Backend (FastAPI)
echo "\n📡 Starting Backend on http://127.0.0.1:${BACKEND_PORT}"
BACKEND_APP="api.main:app"
"$VENV_BIN/uvicorn" "$BACKEND_APP" --host 127.0.0.1 --port "$BACKEND_PORT" --log-level warning &
PIDS+=("$!")

# Wait briefly for backend
sleep 1
if command -v curl >/dev/null 2>&1; then
  if curl -fsS "http://127.0.0.1:${BACKEND_PORT}/health" >/dev/null 2>&1; then
    echo "   ✅ Backend healthy"
  else
    echo "   ⚠️  Backend starting... (health not ready yet)"
  fi
fi

# Start Frontend (Vite)
if [[ -f package.json ]]; then
  echo "\n🎨 Starting Frontend on http://localhost:${FRONTEND_PORT}"
  # Prefer existing install; do not block on installs here
  (VITE_API_URL="http://127.0.0.1:${BACKEND_PORT}" PORT="$FRONTEND_PORT" npm run dev >/dev/null 2>&1 &)
  PIDS+=("$!")
else
  echo "\n⚠️  Frontend not found (missing package.json)."
fi

echo "\n✅ Services"
echo "   API:      http://127.0.0.1:${BACKEND_PORT}"
echo "   Health:   http://127.0.0.1:${BACKEND_PORT}/health"
[[ -f package.json ]] && echo "   Frontend: http://localhost:${FRONTEND_PORT}"
echo "\nPress Ctrl+C to stop."

# Keep script alive to manage background jobs
wait