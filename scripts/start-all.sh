#!/usr/bin/env bash
# Kalaa Setu — bring up the full local stack in the documented order.
# Usage:  bash scripts/start-all.sh
#
# Order (per BRAIN.md):
#   1. docker-compose up -d          (LocalStack + OpenSearch)
#   2. ollama serve                  (local LLM host)
#   3. ai/                            (AI service)
#   4. matching/                      (Matching service)
#   5. backend/                       (SAM local start-api)
#   6. frontend/                      (npm run dev)
#
# This script does NOT block on all services running; it starts each in the
# background and prints where to look for logs. Ctrl+C will not kill the
# services you started; use scripts/stop-all.sh (or docker-compose down) for that.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

LOG_DIR="$ROOT_DIR/.logs"
mkdir -p "$LOG_DIR"

if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD=(docker-compose)
else
    echo "Docker Compose is required. Install Docker Compose v2 and try again." >&2
    exit 1
fi

echo "==> [1/6] docker-compose up -d (LocalStack + OpenSearch)"
"${COMPOSE_CMD[@]}" up -d

echo "==> [2/6] ollama serve (background)"
if ! pgrep -x "ollama" >/dev/null 2>&1; then
    ollama serve >"$LOG_DIR/ollama.log" 2>&1 &
    sleep 2
else
    echo "    ollama already running"
fi

echo "==> [3/6] starting AI service (ai/)"
if [ -d "$ROOT_DIR/ai" ]; then
    AI_PYTHON="$ROOT_DIR/ai/venv/bin/python"
    [ -x "$AI_PYTHON" ] || AI_PYTHON="$ROOT_DIR/ai/.venv/bin/python"
    [ -x "$AI_PYTHON" ] || AI_PYTHON="$(command -v python3 || true)"
    (cd "$ROOT_DIR/ai" && \
        [ -n "$AI_PYTHON" ] && "$AI_PYTHON" -m pip install -q -r requirements.txt && \
        "$AI_PYTHON" -m src.app >"$LOG_DIR/ai.log" 2>&1 &
    )
else
    echo "    ai/ not present yet — skipping"
fi

echo "==> [4/6] starting Matching service (matching/)"
if [ -d "$ROOT_DIR/matching" ]; then
    MATCHING_PYTHON="$ROOT_DIR/matching/.venv/bin/python"
    [ -x "$MATCHING_PYTHON" ] || MATCHING_PYTHON="$(command -v python3 || true)"
    (cd "$ROOT_DIR/matching" && \
        [ -n "$MATCHING_PYTHON" ] && "$MATCHING_PYTHON" -m pip install -q -r requirements.txt && \
        "$MATCHING_PYTHON" -m uvicorn app.main:app --host 0.0.0.0 --port 8002 >"$LOG_DIR/matching.log" 2>&1 &
    )
else
    echo "    matching/ not present yet — skipping"
fi

echo "==> [5/6] starting backend (sam local start-api)"
if [ -d "$ROOT_DIR/backend" ]; then
    if command -v sam >/dev/null 2>&1; then
        (cd "$ROOT_DIR/backend" && \
            sam local start-api --env-vars ../.env.example >"$LOG_DIR/backend.log" 2>&1 &
        ) || echo "    backend failed to start — check $LOG_DIR/backend.log"
    else
        echo "    backend skipped — AWS SAM CLI is not installed"
    fi
else
    echo "    backend/ not present yet — skipping"
fi

echo "==> [6/6] starting frontend (npm run dev)"
if [ -d "$ROOT_DIR/frontend" ]; then
    (cd "$ROOT_DIR/frontend" && \
        { [ -f package.json ] && npm install --silent && npm run dev >"$LOG_DIR/frontend.log" 2>&1 & } || true
    )
else
    echo "    frontend/ not present yet — skipping"
fi

echo
echo "All services launched. Logs in $LOG_DIR/"
echo "  AI        -> http://localhost:8001/health"
echo "  Matching  -> http://localhost:8002/health"
echo "  Backend   -> http://localhost:3000"
echo "  Frontend  -> http://localhost:5173 (default Vite port)"
echo "  LocalStack-> http://localhost:4566"
echo "  OpenSearch-> http://localhost:9200"
