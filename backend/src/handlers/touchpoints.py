"""
POST /touchpoints — register a school/CSC community touchpoint.

Request body (BRAIN.md Section G):
    { name, type ("school"|"csc"), village, state, pickup_address, admin_user_id? }

Response: full CommunityTouchpoint object with generated touchpoint_id.
Errors:   400 missing/invalid fields
"""

from __future__ import annotations

import logging
import uuid

from db import dynamodb
from utils.errors import (
    bad_request,
    ok,
    parse_json_body,
    require_fields,
    server_error,
)

log = logging.getLogger("kalaa.handlers.touchpoints")

VALID_TYPES = {"school", "csc"}


def lambda_handler(event, context):
    try:
        body = parse_json_body(event)
        require_fields(body, "name", "type", "village", "state", "pickup_address")
    except ValueError as exc:
        return bad_request(str(exc))

    tp_type = body["type"]
    if tp_type not in VALID_TYPES:
        return bad_request(f"type must be one of {sorted(VALID_TYPES)}, got '{tp_type}'")

    touchpoint = {
        "touchpoint_id": str(uuid.uuid4()),
        "name": body["name"],
        "type": tp_type,
        "village": body["village"],
        "state": body["state"],
        "pickup_address": body["pickup_address"],
    }
    if body.get("admin_user_id"):
        touchpoint["admin_user_id"] = body["admin_user_id"]

    try:
        dynamodb.put_item(dynamodb.TABLE_TOUCHPOINTS, touchpoint)
    except Exception:  # noqa: BLE001
        log.exception("failed to persist touchpoint")
        return server_error("failed to persist touchpoint")

    return ok(touchpoint, status_code=201)
