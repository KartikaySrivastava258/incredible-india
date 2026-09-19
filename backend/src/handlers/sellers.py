"""
POST /sellers — register a seller.

Request body (BRAIN.md Section G):
    { name, village, state, seller_language, phone?, touchpoint_id }

Response: full Seller object with generated seller_id and created_at.
Errors:   400 missing/invalid fields, unknown touchpoint_id
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from db import dynamodb
from utils.errors import (
    bad_request,
    ok,
    parse_json_body,
    require_fields,
    server_error,
)

log = logging.getLogger("kalaa.handlers.sellers")


def lambda_handler(event, context):
    try:
        body = parse_json_body(event)
        require_fields(body, "name", "village", "state", "seller_language", "touchpoint_id")
    except ValueError as exc:
        return bad_request(str(exc))

    touchpoint_id = body["touchpoint_id"]

    # FK check: touchpoint must exist
    touchpoint = dynamodb.get_item(dynamodb.TABLE_TOUCHPOINTS, "touchpoint_id", touchpoint_id)
    if not touchpoint:
        return bad_request(f"touchpoint_id {touchpoint_id} does not exist")

    seller = {
        "seller_id": str(uuid.uuid4()),
        "name": body["name"],
        "village": body["village"],
        "state": body["state"],
        "seller_language": body["seller_language"],
        "touchpoint_id": touchpoint_id,
        "created_at": _now_iso(),
    }
    if body.get("phone"):
        seller["phone"] = body["phone"]

    try:
        dynamodb.put_item(dynamodb.TABLE_SELLERS, seller)
    except Exception as exc:  # noqa: BLE001 — surface as 500, do not leak internals
        log.exception("failed to persist seller")
        return server_error("failed to persist seller")

    return ok(seller, status_code=201)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
