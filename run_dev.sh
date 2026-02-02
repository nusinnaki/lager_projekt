#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

pkill -f uvicorn >/dev/null 2>&1 || true
pkill -f http.server >/dev/null 2>&1 || true

cd "$ROOT"
source .venv/bin/activate
export ADMIN_TOKEN="popsite"

python3 -m uvicorn backend.main:app --reload &
cd "$ROOT/frontend"
python3 -m http.server 3000
