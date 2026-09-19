"""
Kalaa Setu — local dev HTTP server for the backend.

This file is OPTIONAL. The canonical way to run the backend is:

    cd backend && sam local start-api --env-vars ../.env.example

But for quick iteration without SAM, this module starts a tiny HTTP server
that dispatches the same Lambda handlers to the same routes. Same contracts,
same responses — just no SAM/LocalStack in the loop for the API Gateway part.

Usage:
    cd backend
    export $(grep -v '^#' ../.env.example | xargs)
    PYTHONPATH=src python src/app.py

Then:
    curl -X POST http://localhost:3000/sellers -d '...'

The server uses only Python stdlib (http.server) so no extra dependency is
required for local dev.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

# Make `handlers`, `db`, `clients`, `cedar`, `utils` importable when run as a script.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load .env.example automatically if present (simple KEY=VALUE parser).
def _load_env_file(path: str) -> None:
    if not os.path.isfile(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

_here = os.path.dirname(os.path.abspath(__file__))
_load_env_file(os.path.join(_here, "..", "..", ".env.example"))
_load_env_file(os.path.join(_here, "..", ".env.example"))

logging.basicConfig(level=logging.INFO, format="[backend] %(levelname)s %(message)s")
log = logging.getLogger("kalaa.app")

# Import handlers after env is loaded.
from handlers import (  # noqa: E402
    contributions as h_contributions,
    impact as h_impact,
    ledger as h_ledger,
    listings as h_listings,
    onboarding as h_onboarding,
    products as h_products,
    sales as h_sales,
    search as h_search,
    sellers as h_sellers,
    touchpoints as h_touchpoints,
)


# Route table: (method, path pattern) → handler.
# :id and :seller_id are simple single-segment params.
ROUTES = [
    ("POST", "/sellers",                     h_sellers.lambda_handler),
    ("POST", "/touchpoints",                 h_touchpoints.lambda_handler),
    ("POST", "/products",                    h_products.lambda_handler),
    ("POST", "/onboarding/message",          h_onboarding.lambda_handler),
    ("POST", "/listings/generate",           h_listings.lambda_handler),
    ("POST", "/listings/:id/review",         h_listings.lambda_handler),
    ("GET",  "/listings/:id",                h_listings.lambda_handler),
    ("POST", "/search/match",                h_search.lambda_handler),
    ("POST", "/contributions",               h_contributions.lambda_handler),
    ("POST", "/sales",                       h_sales.lambda_handler),
    ("GET",  "/ledger/:seller_id",           h_ledger.lambda_handler),
    ("GET",  "/impact",                      h_impact.lambda_handler),
]


def _match_route(method: str, path: str):
    parts = [p for p in path.split("/") if p]
    for r_method, r_path, handler in ROUTES:
        if r_method != method:
            continue
        r_parts = [p for p in r_path.split("/") if p]
        if len(r_parts) != len(parts):
            continue
        params = {}
        ok = True
        for rp, ap in zip(r_parts, parts):
            if rp.startswith(":"):
                params[rp[1:]] = ap
            elif rp != ap:
                ok = False
                break
        if ok:
            return handler, params
    return None, None


class Handler(BaseHTTPRequestHandler):
    def _respond(self, result: dict) -> None:
        self.send_response(result.get("statusCode", 200))
        for k, v in (result.get("headers") or {}).items():
            self.send_header(k, v)
        if not (result.get("headers") or {}).get("Content-Type"):
            self.send_header("Content-Type", "application/json")
        self.end_headers()
        body = result.get("body", "")
        if not isinstance(body, (str, bytes)):
            body = json.dumps(body)
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.wfile.write(body)

    def _handle(self, method: str) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        handler, params = _match_route(method, path)

        if handler is None:
            self._respond({
                "statusCode": 404,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": {"code": "NOT_FOUND", "message": f"no route {method} {path}"}}),
            })
            return

        length = int(self.headers.get("Content-Length") or 0)
        raw_body = self.rfile.read(length).decode("utf-8") if length else ""

        event = {
            "httpMethod": method,
            "path": path,
            "pathParameters": params or None,
            "headers": {k.lower(): v for k, v in self.headers.items()},
            "body": raw_body or None,
            "queryStringParameters": dict(
                (kv.split("=", 1) + [""])[:2] for kv in (parsed.query.split("&") if parsed.query else [])
            ) or None,
        }
        result = handler(event, None)
        self._respond(result)

    def do_GET(self):    self._handle("GET")
    def do_POST(self):   self._handle("POST")
    def do_PUT(self):    self._handle("PUT")
    def do_DELETE(self): self._handle("DELETE")

    def log_message(self, fmt, *args):
        log.info("%s - %s", self.address_string(), fmt % args)


def main():
    port = int(os.environ.get("PORT", "3000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    log.info("backend listening on http://localhost:%d", port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("shutting down")
        server.server_close()


if __name__ == "__main__":
    main()
