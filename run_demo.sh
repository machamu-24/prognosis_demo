#!/bin/zsh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
FRONTEND_DIR="$ROOT_DIR/frontend"
MPL_DIR="${MPLCONFIGDIR:-/tmp/mpl}"
API_HOST="127.0.0.1"
API_PORT="8000"
WEB_HOST="127.0.0.1"
WEB_PORT="3000"
BACKEND_LOG="$ROOT_DIR/.demo_backend.log"
REFRESH_MODELS=false


usage() {
  cat <<'EOF'
Usage:
  ./run_demo.sh
  ./run_demo.sh --train

Options:
  --train    Regenerate metrics and resave the trained models before starting the demo.
  --help     Show this help message.
EOF
}


port_in_use() {
  local port="$1"
  lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
}


wait_for_api() {
  local attempts=30
  while (( attempts > 0 )); do
    if curl -s "http://${API_HOST}:${API_PORT}/health" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
    ((attempts--))
  done
  return 1
}


cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]] && kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
    wait "$BACKEND_PID" 2>/dev/null || true
  fi
}


while [[ $# -gt 0 ]]; do
  case "$1" in
    --train)
      REFRESH_MODELS=true
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
  shift
done


if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python virtual environment was not found at $PYTHON_BIN" >&2
  exit 1
fi

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  echo "Frontend dependencies are missing. Run 'cd frontend && npm install' first." >&2
  exit 1
fi

if port_in_use "$API_PORT"; then
  echo "Port $API_PORT is already in use. Stop the existing process and try again." >&2
  exit 1
fi

if port_in_use "$WEB_PORT"; then
  echo "Port $WEB_PORT is already in use. Stop the existing process and try again." >&2
  exit 1
fi

mkdir -p "$MPL_DIR"
cd "$ROOT_DIR"

if $REFRESH_MODELS || [[ ! -f "$ROOT_DIR/logistic_model.joblib" || ! -f "$ROOT_DIR/tree_model.joblib" || ! -f "$ROOT_DIR/model_metrics.json" ]]; then
  echo "Refreshing models and metrics..."
  MPLCONFIGDIR="$MPL_DIR" "$PYTHON_BIN" prognosis_demo.py
fi

trap cleanup EXIT INT TERM

echo "Starting backend API on http://${API_HOST}:${API_PORT}"
MPLCONFIGDIR="$MPL_DIR" "$PYTHON_BIN" -m uvicorn backend.app.main:app --host "$API_HOST" --port "$API_PORT" >"$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!

if ! wait_for_api; then
  echo "Backend failed to start. Check $BACKEND_LOG for details." >&2
  exit 1
fi

echo "Starting frontend on http://${WEB_HOST}:${WEB_PORT}"
echo "Press Ctrl+C to stop both servers."

cd "$FRONTEND_DIR"
NEXT_PUBLIC_API_BASE="http://${API_HOST}:${API_PORT}" npm run dev -- --hostname "$WEB_HOST" --port "$WEB_PORT"
