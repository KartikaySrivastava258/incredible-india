#!/usr/bin/env bash
# Kalaa Setu — stop all local services started by start-all.sh.
# Usage:  bash scripts/stop-all.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD=(docker-compose)
else
    echo "Docker Compose not found — skipping container teardown." >&2
fi

echo "==> Stopping LocalStack + OpenSearch"
if [ -n "${COMPOSE_CMD+x}" ]; then
    (cd "$ROOT_DIR" && "${COMPOSE_CMD[@]}" down)
fi

echo "==> Killing AI / Matching / Backend (SAM) / Frontend processes"
pkill -f "src.app" 2>/dev/null || true
pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "sam local start-api" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true

echo "==> Stopping Ollama (if started by start-all.sh)"
pkill -x ollama 2>/dev/null || true

echo "All services stopped."
