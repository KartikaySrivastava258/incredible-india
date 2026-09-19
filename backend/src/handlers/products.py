"""
POST /products — record a seller's raw product description.

Request body (BRAIN.md Section G):
    { seller_id, category ("food"|"textile"|"toy"|"handicraft"),
      raw_description, seller_language }

Response: full Product object with generated product_id and created_at.
Errors:   400 missing/invalid fields, unknown seller_id
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

log = logging.getLogger("kalaa.handlers.products")

VALID_CATEGORIES = {"food", "textile", "toy", "handicraft"}


def lambda_handler(event, context):
    try:
        body = parse_json_body(event)
        require_fields(body, "seller_id", "category", "raw_description", "seller_language")
    except ValueError as exc:
        return bad_request(str(exc))

    category = body["category"]
    if category not in VALID_CATEGORIES:
        return bad_request(f"category must be one of {sorted(VALID_CATEGORIES)}, got '{category}'")

    seller_id = body["seller_id"]
    seller = dynamodb.get_item(dynamodb.TABLE_SELLERS, "seller_id", seller_id)
    if not seller:
        return bad_request(f"seller_id {seller_id} does not exist")

    product = {
        "product_id": str(uuid.uuid4()),
        "seller_id": seller_id,
        "category": category,
        "raw_description": body["raw_description"],
        "seller_language": body["seller_language"],
        "created_at": _now_iso(),
    }

    try:
        dynamodb.put_item(dynamodb.TABLE_PRODUCTS, product)
    except Exception:  # noqa: BLE001
        log.exception("failed to persist product")
        return server_error("failed to persist product")

    return ok(product, status_code=201)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
