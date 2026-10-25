#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$PWD/.tools/node/bin:$PATH"
export PLAYWRIGHT_BROWSERS_PATH="$PWD/.tools/browsers"
export SKILLSWAP_DOMAIN_DB="$PWD/storage/browser-domain.sqlite"
export SKILLSWAP_CHECKPOINT_DB="$PWD/storage/browser-checkpoints.sqlite"
if curl -fsS http://127.0.0.1:8000/api/providers >/dev/null 2>&1 || curl -fsS http://127.0.0.1:5173/ >/dev/null 2>&1; then
  echo 'Ports 8000/5173 must be free; stop existing dev servers first.'
  exit 1
fi
.venv/bin/python -m uvicorn browser_server:app --app-dir backend/tests --host 127.0.0.1 --port 8000 &
backend_pid=$!
npm --prefix frontend run dev &
frontend_pid=$!
trap 'kill "$backend_pid" "$frontend_pid" 2>/dev/null || true' EXIT INT TERM
for attempt in {1..40}; do
  if curl -fsS http://127.0.0.1:8000/api/providers >/dev/null 2>&1 && curl -fsS http://127.0.0.1:5173/ >/dev/null 2>&1; then break; fi
  sleep .25
done
cd frontend
npm test
