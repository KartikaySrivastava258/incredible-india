"""
POST /contributions — seller sets/updates opt-in + percentage.

Request body (BRAIN.md Section G):
    { seller_id, opted_in, percentage, touchpoint_id, principal_seller_id }

Cedar enforcement (MUST rule: seller can only set their own contribution):
    The principal identified by principal_seller_id must be the same seller as
    seller_id in the body. If not, Cedar denies → HTTP 403.

Order of checks (important):
    1. Parse + require fields
    2. Type + range validation on percentage / opted_in
    3. FK checks (seller exists, touchpoint exists)
    4. Cedar authorization
    5. Upsert

This order matters: unknown entities must 400, not 403.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from cedar.evaluator import Request, is_authorized
from db import dynamodb
from utils.errors import (
    bad_request,
    forbidden,
    ok,
    parse_json_body,
    require_fields,
    server_error,
)

log = logging.getLogger("kalaa.handlers.contributions")


def lambda_handler(event, context):
    # 1. Parse + require
    try:
        body = parse_json_body(event)
        require_fields(
            body,
            "seller_id",
            "opted_in",
            "percentage",
            "touchpoint_id",
            "principal_seller_id",
        )
    except ValueError as exc:
        return bad_request(str(exc))

    seller_id = body["seller_id"]
    principal_seller_id = body["principal_seller_id"]
    touchpoint_id = body["touchpoint_id"]
    opted_in = body["opted_in"]
    percentage = body["percentage"]

    # 2. Type + range validation
    if not isinstance(opted_in, bool):
        return bad_request("opted_in must be a boolean")
    if not isinstance(percentage, (int, float)) or isinstance(percentage, bool):
        return bad_request("percentage must be a number")
    if percentage < 0 or percentage > 100:
        return bad_request("percentage must be between 0 and 100 (inclusive)")
    if opted_in and percentage <= 0:
        return bad_request("percentage must be > 0 when opted_in is true")

    # 3. FK checks
    seller = dynamodb.get_item(dynamodb.TABLE_SELLERS, "seller_id", seller_id)
    if not seller:
        return bad_request(f"seller_id {seller_id} does not exist")

    touchpoint = dynamodb.get_item(dynamodb.TABLE_TOUCHPOINTS, "touchpoint_id", touchpoint_id)
    if not touchpoint:
        return bad_request(f"touchpoint_id {touchpoint_id} does not exist")

    # 4. Cedar: a seller can only set their own contribution
    cedar_request = Request(
        principal_type="Seller",
        principal_attrs={"seller_id": principal_seller_id},
        action="setContribution",
        resource_type="Contribution",
        resource_attrs={"seller_id": seller_id},
    )
    if not is_authorized(cedar_request):
        log.warning(
            "Cedar denied: principal=%s tried to set contribution for seller=%s",
            principal_seller_id,
            seller_id,
        )
        return forbidden("Cedar denied: a seller can only set their own contribution")

    # 5. Upsert the Contribution record
    existing = dynamodb.scan_filter(dynamodb.TABLE_CONTRIBUTIONS, "seller_id", seller_id)
    if existing:
        contribution = dict(existing[0])
        contribution["opted_in"] = opted_in
        contribution["percentage"] = percentage
        contribution["touchpoint_id"] = touchpoint_id
        contribution["updated_at"] = _now_iso()
    else:
        contribution = {
            "contribution_id": str(uuid.uuid4()),
            "seller_id": seller_id,
            "opted_in": opted_in,
            "percentage": percentage,
            "touchpoint_id": touchpoint_id,
            "updated_at": _now_iso(),
        }

    try:
        dynamodb.put_item(dynamodb.TABLE_CONTRIBUTIONS, contribution)
    except Exception:  # noqa: BLE001
        log.exception("failed to persist contribution")
        return server_error("failed to persist contribution")

    return ok(contribution)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
