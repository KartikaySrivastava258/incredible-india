"""
Handles three routes on the same Lambda function:

  POST /listings/generate     → AI service, persist pending listing
  POST /listings/:id/review   → rule-based review, index on approval
  GET  /listings/:id          → fetch one listing

The route is distinguished by `event["httpMethod"]` and the `pathParameters`
that API Gateway populates for `/listings/{id}`.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from clients import ai_service, matching_service
from db import dynamodb
from utils.errors import (
    bad_request,
    not_found,
    ok,
    parse_json_body,
    require_fields,
    server_error,
    upstream_error,
)

log = logging.getLogger("kalaa.handlers.listings")

BANNED_WORDS = {"cure", "miracle", "guaranteed cure", "100% cure"}


def lambda_handler(event, context):
    method = (event.get("httpMethod") or "").upper()
    path_params = event.get("pathParameters") or {}
    listing_id = path_params.get("id")

    if method == "POST" and listing_id is None:
        return _generate(event)
    if method == "POST" and listing_id is not None:
        return _review(event, listing_id)
    if method == "GET" and listing_id is not None:
        return _get(listing_id)

    return bad_request(f"unsupported route: {method} {event.get('path')}")


# ---------------------------------------------------------------------------
# POST /listings/generate
# ---------------------------------------------------------------------------

def _generate(event):
    try:
        body = parse_json_body(event)
        require_fields(body, "seller_id", "conversation_id")
    except ValueError as exc:
        return bad_request(str(exc))

    seller_id = body["seller_id"]
    conversation_id = body["conversation_id"]

    seller = dynamodb.get_item(dynamodb.TABLE_SELLERS, "seller_id", seller_id)
    if not seller:
        return bad_request(f"seller_id {seller_id} does not exist")

    ai = ai_service.get_ai_client()
    try:
        listing = ai.generate_listing(seller_id=seller_id, conversation_id=conversation_id)
    except ai_service.AIServiceError as exc:
        log.warning("AI service error during listing generation: %s", exc)
        return upstream_error("AI service unavailable or returned malformed listing")

    # Force server-controlled defaults. The AI service should already provide
    # these, but the backend is the source of truth.
    listing.setdefault("listing_id", str(uuid.uuid4()))
    listing["review_status"] = "pending"
    listing.setdefault("created_at", _now_iso())
    listing.setdefault("compliance_flags", [])

    try:
        dynamodb.put_item(dynamodb.TABLE_LISTINGS, listing)
    except Exception:  # noqa: BLE001
        log.exception("failed to persist listing")
        return server_error("failed to persist listing")

    return ok(listing, status_code=201)


# ---------------------------------------------------------------------------
# POST /listings/:id/review
# ---------------------------------------------------------------------------

def _review(event, listing_id):
    try:
        body = parse_json_body(event) if event.get("body") else {}
    except ValueError as exc:
        return bad_request(str(exc))

    reviewer = body.get("reviewer", "auto")
    notes = body.get("notes")

    listing = dynamodb.get_item(dynamodb.TABLE_LISTINGS, "listing_id", listing_id)
    if not listing:
        return not_found(f"listing {listing_id} not found")

    decision, reasons = _run_review(listing)
    listing["review_status"] = "approved" if decision == "approved" else "rejected"
    existing_flags = list(listing.get("compliance_flags") or [])
    listing["compliance_flags"] = existing_flags + reasons

    review = {
        "review_id": str(uuid.uuid4()),
        "listing_id": listing_id,
        "reviewer": reviewer,
        "decision": decision,
        "created_at": _now_iso(),
    }
    if notes:
        review["notes"] = notes

    try:
        dynamodb.put_item(dynamodb.TABLE_LISTINGS, listing)
        dynamodb.put_item(dynamodb.TABLE_REVIEWS, review)
    except Exception:  # noqa: BLE001
        log.exception("failed to persist review")
        return server_error("failed to persist review")

    # On approval, index into the matching service. If the matching service is
    # unavailable, keep the approval and add a compliance flag for retry.
    if listing["review_status"] == "approved":
        matching = matching_service.get_matching_client()
        try:
            matching.index_listing(listing)
        except matching_service.MatchingServiceError as exc:
            log.warning("matching service unavailable during indexing: %s", exc)
            flags = list(listing.get("compliance_flags") or [])
            flags.append("indexing_pending")
            listing["compliance_flags"] = flags
            try:
                dynamodb.put_item(dynamodb.TABLE_LISTINGS, listing)
            except Exception:  # noqa: BLE001
                log.exception("failed to persist indexing_pending flag")

    return ok(listing)


# ---------------------------------------------------------------------------
# GET /listings/:id
# ---------------------------------------------------------------------------

def _get(listing_id):
    listing = dynamodb.get_item(dynamodb.TABLE_LISTINGS, "listing_id", listing_id)
    if not listing:
        return not_found(f"listing {listing_id} not found")
    return ok(listing)


# ---------------------------------------------------------------------------
# Rule-based review
# ---------------------------------------------------------------------------

def _run_review(listing: dict) -> tuple[str, list[str]]:
    """
    Returns (decision, reasons).
    decision is "approved" or "rejected".
    reasons is a list of compliance flags explaining a rejection.
    """
    reasons: list[str] = []

    required = ("listing_id", "product_id", "category", "listing_title",
                "description_en", "price_suggestion")
    for field in required:
        if not listing.get(field):
            reasons.append(f"missing_{field}")

    if reasons:
        return "rejected", reasons

    text = " ".join(str(listing.get(k, "")).lower() for k in ("listing_title", "description_en"))
    for bad in BANNED_WORDS:
        if bad in text:
            reasons.append(f"banned_word:{bad}")

    # Category-specific checks (surface AI-set flags; do not invent new rules).
    category = listing.get("category")
    if category == "food" and "food_fssai_recommended" not in (listing.get("compliance_flags") or []):
        # Not a rejection — informational flag for the listing.
        reasons.append("food_fssai_recommended")

    # Only banned words or missing fields cause rejection; flags alone do not.
    decision = "approved" if not any(r.startswith("banned_word") or r.startswith("missing_") for r in reasons) else "rejected"
    return decision, reasons


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
