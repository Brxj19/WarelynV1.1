#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR/backend"
python3 -m compileall app
.venv/bin/python -m pytest
.venv/bin/alembic upgrade head

cd "$ROOT_DIR/frontend"
npm run build

cd "$ROOT_DIR"
docker compose config >/dev/null

git status --short
