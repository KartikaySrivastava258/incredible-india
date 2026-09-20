#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
if [ -f "$ROOT_DIR/.env" ]; then
  set -a; . "$ROOT_DIR/.env"; set +a
else
  set -a; . "$ROOT_DIR/.env.example"; set +a
fi
DYNAMODB_ENDPOINT="${DYNAMODB_ENDPOINT:-http://localhost:4566}"
MATCHING_SERVICE_URL="${MATCHING_SERVICE_URL:-http://localhost:8002}"
case "$DYNAMODB_ENDPOINT" in
  http://localhost:*|http://127.0.0.1:*|http://localstack:*|http://kalaa-localstack:*) ;;
  *) echo "ERROR: refusing reset; DYNAMODB_ENDPOINT=$DYNAMODB_ENDPOINT is not local/LocalStack." >&2; exit 2 ;;
esac
python3 - "$DYNAMODB_ENDPOINT" <<'PY'
import json, sys, urllib.request
url=sys.argv[1].rstrip('/') + '/_localstack/health'
try:
    with urllib.request.urlopen(url, timeout=5) as r: data=json.load(r)
except Exception as exc:
    print(f"ERROR: LocalStack health check failed: {exc}", file=sys.stderr); raise SystemExit(1)
if data.get("services", {}).get("dynamodb") not in {"running", "available"}:
    print("ERROR: LocalStack DynamoDB is not running.", file=sys.stderr); raise SystemExit(1)
print("LocalStack DynamoDB: healthy")
PY
python3 - "$MATCHING_SERVICE_URL" <<'PY'
import json, sys, urllib.request
url=sys.argv[1].rstrip('/') + '/health'
try:
    with urllib.request.urlopen(url, timeout=5) as r: data=json.load(r)
except Exception as exc:
    print(f"ERROR: Matching service health check failed: {exc}", file=sys.stderr); raise SystemExit(1)
if data.get("status") != "ok":
    print("ERROR: Matching service is not healthy.", file=sys.stderr); raise SystemExit(1)
print("Matching service: healthy")
PY
export DYNAMODB_ENDPOINT MATCHING_SERVICE_URL
python3 "$ROOT_DIR/scripts/seed_dynamodb.py" --reset
python3 - "$MATCHING_SERVICE_URL" <<'PY'
import json, sys, urllib.request
url=sys.argv[1].rstrip('/') + '/reset'
req=urllib.request.Request(url, method='POST')
try:
    with urllib.request.urlopen(req, timeout=10) as r: print('Matching reset:', r.read().decode())
except Exception as exc:
    print(f"ERROR: matching reset failed: {exc}", file=sys.stderr); raise SystemExit(1)
PY
python3 "$ROOT_DIR/scripts/seed_opensearch.py"
echo "Demo reset complete: DynamoDB and matching index cleared/reseeded."
echo "AI conversations are in memory; restart the AI service to clear them."
