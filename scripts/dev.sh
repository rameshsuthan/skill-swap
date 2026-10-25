#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -d .tools/node/bin ]]; then export PATH="$PWD/.tools/node/bin:$PATH"; fi
if [[ ! -x .venv/bin/python ]]; then echo 'Run the README setup steps first.'; exit 1; fi
.venv/bin/python -m uvicorn skillswap.api:app --host 127.0.0.1 --port 8000 &
backend_pid=$!
trap 'kill "$backend_pid" 2>/dev/null || true' EXIT INT TERM
npm --prefix frontend run dev
