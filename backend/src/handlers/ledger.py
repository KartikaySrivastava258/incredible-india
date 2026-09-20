"""
GET /ledger/:seller_id — return the ledger entries for one seller.

Identity comes from headers:
    X-Principal-Type:        "Seller" | "TouchpointAdmin"
    X-Principal-Seller-Id:   required if X-Principal-Type == "Seller"
    X-Principal-Touchpoint-Id: required if X-Principal-Type == "TouchpointAdmin"

Cedar enforces:
  - A seller can read only their own ledger.
  - A touchpoint admin can read only the ledger of sellers in their own
    touchpoint (village).

Response: { "entries": [ LedgerEntry, ... ] }
Errors:
    400 missing headers
    403 Cedar denied
    404 seller not found
"""

from __future__ import annotations

import logging

from cedar.evaluator import Request, authorize
from db import dynamodb
from utils.errors import (
    bad_request,
    forbidden,
    not_found,
    ok,
    server_error,
)

log = logging.getLogger("kalaa.handlers.ledger")


def lambda_handler(event, context):
    path_params = event.get("pathParameters") or {}
    seller_id = path_params.get("seller_id")
    if not seller_id:
        return bad_request("seller_id path parameter is required")

    seller = dynamodb.get_item(dynamodb.TABLE_SELLERS, "seller_id", seller_id)
    if not seller:
        return not_found(f"seller {seller_id} not found")

    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    principal_type = headers.get("x-principal-type")

    if not principal_type:
        return bad_request("X-Principal-Type header is required")

    if principal_type == "Seller":
        principal_seller_id = headers.get("x-principal-seller-id")
        if not principal_seller_id:
            return bad_request("X-Principal-Seller-Id header is required for Seller principals")
        cedar_request = Request(
            principal_type="Seller",
            principal_attrs={"seller_id": principal_seller_id},
            action="viewLedger",
            resource_type="LedgerEntry",
            resource_attrs={"seller_id": seller_id},
        )

    elif principal_type == "TouchpointAdmin":
        principal_touchpoint_id = headers.get("x-principal-touchpoint-id")
        if not principal_touchpoint_id:
            return bad_request(
                "X-Principal-Touchpoint-Id header is required for TouchpointAdmin principals"
            )
        cedar_request = Request(
            principal_type="TouchpointAdmin",
            principal_attrs={"touchpoint_id": principal_touchpoint_id},
            action="viewLedgerData",
            resource_type="LedgerEntry",
            resource_attrs={
                "touchpoint_id": seller.get("touchpoint_id"),
                "seller_id": seller_id,
            },
        )
    else:
        return bad_request(f"unsupported X-Principal-Type '{principal_type}'")

    decision = authorize(cedar_request)
    if not decision.allowed:
        log.warning(
            "Cedar denied ledger read: principal_type=%s seller_id=%s",
            principal_type, seller_id,
        )
        details = None
        if principal_type == "TouchpointAdmin":
            details = {
                "policy": "touchpoint_admin_scope.cedar",
                "action": cedar_request.action,
                "principal_touchpoint_id": cedar_request.principal_attrs.get("touchpoint_id"),
                "resource_touchpoint_id": cedar_request.resource_attrs.get("touchpoint_id"),
            }
        return forbidden("Cedar denied: you cannot view this seller's ledger", details)

    try:
        entries = dynamodb.scan_filter(dynamodb.TABLE_LEDGER, "seller_id", seller_id)
    except Exception:  # noqa: BLE001
        log.exception("failed to scan ledger entries")
        return server_error("failed to read ledger")

    # Sort by created_at ascending for stable output.
    entries.sort(key=lambda e: e.get("created_at", ""))
    return ok({"entries": entries})
