#!/bin/bash
set -e
cd "$(dirname "$0")/.."
cd frontend
python3 -m http.server 5173
