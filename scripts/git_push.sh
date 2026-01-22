#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

git status --porcelain
git add -A
MSG="${1:-daily update}"
git commit -m "$MSG" || true
git push
