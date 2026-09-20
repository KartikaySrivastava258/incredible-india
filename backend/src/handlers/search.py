"""
POST /search/match — buyer search → ranked matched listings.

Request body (BRAIN.md Section G):
    { query_text, buyer_id (uuid|null) }

Response:
    { "matches": [ { listing_id, score, listing_title, noble_cause_note } ] }

Enrichment rule (from BRAIN.md + task file):
    noble_cause_note is populated ONLY if the seller of the matched listing
    has Contribution.opted_in == true. Otherwise it is null.

Errors:
    400 missing/invalid fields
    502 matching service unavailable, or AI service (for the noble-cause note)
        unavailable while the seller HAS opted in
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from clients import ai_service, matching_service
from db import dynamodb
from utils.errors import (
    bad_request,
    ok,
    parse_json_body,
    require_fields,
    server_error,
    upstream_error,
)

log = logging.getLogger("kalaa.handlers.search")


def lambda_handler(event, context):
    try:
        body = parse_json_body(event)
        require_fields(body, "query_text")
    except ValueError as exc:
        return bad_request(str(exc))

    query_text = body["query_text"]
    buyer_id = body.get("buyer_id")

    # Best-effort: record the search intent. Non-fatal if it fails.
    _record_intent(query_text, buyer_id)

    matching = matching_service.get_matching_client()
    try:
        result = matching.match(query_text=query_text, buyer_id=buyer_id)
    except matching_service.MatchingServiceError as exc:
        log.warning("matching service error: %s", exc)
        return upstream_error("matching service unavailable")

    matches = result.get("matches") or []
    enriched = [_enrich(m) for m in matches]
    return ok({"matches": enriched})


def _record_intent(query_text: str, buyer_id: str | None) -> None:
    intent = {
        "intent_id": str(uuid.uuid4()),
        "query_text": query_text,
        "created_at": _now_iso(),
    }
    if buyer_id:
        intent["buyer_id"] = buyer_id
    try:
        dynamodb.put_item(dynamodb.TABLE_SEARCH_INTENTS, intent)
    except Exception:  # noqa: BLE001
        log.warning("failed to persist search intent (non-fatal)")


def _enrich(match: dict) -> dict:
    """
    Given a match from the matching service, attach noble_cause_note when the
    listing's seller has opted in.
    """
    listing_id = match.get("listing_id")
    base = {
        "listing_id": listing_id,
        "score": match.get("score"),
        "listing_title": match.get("listing_title"),
        "noble_cause_note": None,
    }

    listing = dynamodb.get_item(dynamodb.TABLE_LISTINGS, "listing_id", listing_id) if listing_id else None
    if not listing:
        return base

    product = dynamodb.get_item(dynamodb.TABLE_PRODUCTS, "product_id", listing.get("product_id"))
    if not product:
        return base

    seller_id = product.get("seller_id")
    if not seller_id:
        return base

    # Check the seller's Contribution record
    contribs = dynamodb.scan_filter(dynamodb.TABLE_CONTRIBUTIONS, "seller_id", seller_id)
    opted_in = any(c.get("opted_in") is True for c in contribs)
    if not opted_in:
        return base

    # Seller opted in — fetch the noble-cause note from the AI service.
    ai = ai_service.get_ai_client()
    try:
        note = ai.noble_cause_note(listing_id=listing_id, seller_id=seller_id)
    except ai_service.AIServiceError as exc:
        log.warning("AI noble-cause-note failed for listing %s: %s", listing_id, exc)
        return base  # graceful: matches still returned, note omitted

    base["noble_cause_note"] = note
    return base


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
