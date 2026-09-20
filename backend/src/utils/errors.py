"""
Kalaa Setu — shared error helpers for backend handlers.

Every handler returns either:
  - a normal successful payload, or
  - one of these error responses, in the exact shape BRAIN.md Section G requires:
        { "error": { "code": "string", "message": "string" } }

Usage:
    return bad_request("seller_id is required")
    return forbidden("Cedar denied: seller cannot edit another seller's listing")
    return not_found("listing not found")
    return upstream_error("AI service unavailable")
"""

from __future__ import annotations

import json
from typing import Any


def _response(status_code: int, code: str, message: str, details: dict | None = None) -> dict:
    error = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"error": error}),
    }


def ok(payload: Any, status_code: int = 200) -> dict:
    """Success response. Not an error, but kept here so handlers import one module."""
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload),
    }


def bad_request(message: str) -> dict:
    return _response(400, "BAD_REQUEST", message)


def forbidden(message: str, details: dict | None = None) -> dict:
    return _response(403, "FORBIDDEN", message, details)


def not_found(message: str) -> dict:
    return _response(404, "NOT_FOUND", message)


def upstream_error(message: str) -> dict:
    return _response(502, "UPSTREAM_ERROR", message)


def server_error(message: str) -> dict:
    return _response(500, "SERVER_ERROR", message)


def parse_json_body(event: dict) -> dict:
    """
    Parse the JSON body from a Lambda/API Gateway event.

    Raises ValueError if body is missing or malformed.
    Handlers are expected to catch ValueError and return bad_request(...).
    """
    raw = event.get("body")
    if raw is None:
        raise ValueError("request body is required")
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON body: {exc}") from exc


def require_fields(body: dict, *fields: str) -> None:
    """
    Raise ValueError if any required field is missing or empty.

    Treats None and empty string as missing.
    """
    missing = [f for f in fields if body.get(f) in (None, "")]
    if missing:
        raise ValueError(f"missing required field(s): {', '.join(missing)}")
