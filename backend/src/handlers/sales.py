"""
POST /sales — simulate a purchase; compute fee/net/contribution; write ledger.

Request body (BRAIN.md Section G):
    { listing_id, buyer_id (uuid|null), sale_amount, principal_seller_id }

Response: the created LedgerEntry.

Cedar enforcement (MUST rule #2):
    contribution_amount MUST be 0 unless the seller of the listing has
    Contribution.opted_in == true. This is enforced by evaluating the actual
    Cedar policy, not by an app-code if. If Cedar denies a non-zero routing,
    the endpoint returns 403.

Errors:
    400 missing/invalid fields, listing not approved, sale_amount <= 0
    403 Cedar denied (contribution routing when seller not opted in)
    404 listing not found
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
    not_found,
    ok,
    parse_json_body,
    require_fields,
    server_error,
)

log = logging.getLogger("kalaa.handlers.sales")

PLATFORM_FEE_RATE = 0.05  # 5% flat platform fee for the demo


def lambda_handler(event, context):
    try:
        body = parse_json_body(event)
        require_fields(body, "listing_id", "sale_amount", "principal_seller_id")
    except ValueError as exc:
        return bad_request(str(exc))

    listing_id = body["listing_id"]
    buyer_id = body.get("buyer_id")
    sale_amount = body["sale_amount"]

    if not isinstance(sale_amount, (int, float)) or isinstance(sale_amount, bool):
        return bad_request("sale_amount must be a number")
    if sale_amount <= 0:
        return bad_request("sale_amount must be > 0")

    listing = dynamodb.get_item(dynamodb.TABLE_LISTINGS, "listing_id", listing_id)
    if not listing:
        return not_found(f"listing {listing_id} not found")
    if listing.get("review_status") != "approved":
        return bad_request("listing must be approved before it can be sold")

    product = dynamodb.get_item(dynamodb.TABLE_PRODUCTS, "product_id", listing.get("product_id"))
    if not product:
        return not_found("product for listing not found")

    seller_id = product.get("seller_id")
    if not seller_id:
        return server_error("listing has no owning seller")

    # Locate the seller's touchpoint for the ledger entry.
    seller = dynamodb.get_item(dynamodb.TABLE_SELLERS, "seller_id", seller_id) or {}
    touchpoint_id = seller.get("touchpoint_id")
    if not touchpoint_id:
        return server_error("seller has no touchpoint_id")

    # Contribution setting (if any).
    contribs = dynamodb.scan_filter(dynamodb.TABLE_CONTRIBUTIONS, "seller_id", seller_id)
    contribution = contribs[0] if contribs else None
    opted_in = bool(contribution and contribution.get("opted_in") is True)
    percentage = float(contribution.get("percentage", 0)) if contribution else 0.0

    # --- Ledger math -----------------------------------------------------
    platform_fee = round(sale_amount * PLATFORM_FEE_RATE, 2)
    seller_net = round(sale_amount - platform_fee, 2)
    contribution_amount = round(seller_net * (percentage / 100.0), 2) if opted_in else 0.0

    # --- Cedar: enforce rule #2 -----------------------------------------
    cedar_request = Request(
        principal_type="Seller",
        principal_attrs={"seller_id": body["principal_seller_id"]},
        action="routeContribution",
        resource_type="Contribution",
        resource_attrs={
            "seller_id": seller_id,
            "opted_in": opted_in,
            "percentage": percentage,
        },
    )

    # If contribution_amount is non-zero, Cedar must allow it.
    # If Cedar denies, reject the sale (403). If Cedar allows, proceed.
    if contribution_amount > 0:
        if not is_authorized(cedar_request):
            log.warning(
                "Cedar denied contribution routing: seller=%s principal=%s",
                seller_id, body["principal_seller_id"],
            )
            return forbidden("Cedar denied: contribution routing requires seller opt-in")

    # --- Write the ledger entry -----------------------------------------
    ledger_entry = {
        "ledger_entry_id": str(uuid.uuid4()),
        "sale_id": str(uuid.uuid4()),
        "seller_id": seller_id,
        "listing_id": listing_id,
        "sale_amount": round(float(sale_amount), 2),
        "platform_fee": platform_fee,
        "seller_net": seller_net,
        "contribution_amount": contribution_amount,
        "touchpoint_id": touchpoint_id,
        "buyer_visible": opted_in,
        "created_at": _now_iso(),
    }
    if buyer_id:
        ledger_entry["buyer_id"] = buyer_id

    try:
        dynamodb.put_item(dynamodb.TABLE_LEDGER, ledger_entry)
    except Exception:  # noqa: BLE001
        log.exception("failed to persist ledger entry")
        return server_error("failed to persist ledger entry")

    return ok(ledger_entry, status_code=201)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
