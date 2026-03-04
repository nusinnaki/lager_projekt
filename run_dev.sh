#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

# Kill existing dev servers (ignore errors)
pkill -f "uvicorn backend.main:app" >/dev/null 2>&1 || true
pkill -f "http.server 5500" >/dev/null 2>&1 || true

cd "$ROOT"

# Ensure pipenv path (macOS user installs)
export PATH="$HOME/Library/Python/3.9/bin:$PATH"

# Keep virtualenv inside project (.venv)
export PIPENV_VENV_IN_PROJECT=1

# Development admin token
export ADMIN_TOKEN="popsite"

echo "Starting backend on http://127.0.0.1:8000"
pipenv run uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000 &

echo "Starting frontend on http://127.0.0.1:5500"
cd "$ROOT/frontend"
python3 -m http.server 5500