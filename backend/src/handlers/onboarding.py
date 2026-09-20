"""
POST /onboarding/message — one turn of the seller conversation.

Request body (BRAIN.md Section G):
    { seller_id, conversation_id (uuid|null), message_text }

Response (from AI service, passed through):
    { conversation_id, ai_reply_text, stage, draft_state }

Errors:
    400 missing/invalid fields, unknown seller_id
    502 AI service unavailable or returned malformed data
"""

from __future__ import annotations

import logging

from clients import ai_service
from db import dynamodb
from utils.errors import (
    bad_request,
    ok,
    parse_json_body,
    require_fields,
    upstream_error,
)

log = logging.getLogger("kalaa.handlers.onboarding")


def lambda_handler(event, context):
    try:
        body = parse_json_body(event)
        require_fields(body, "seller_id", "message_text")
    except ValueError as exc:
        return bad_request(str(exc))

    seller_id = body["seller_id"]
    conversation_id = body.get("conversation_id")
    message_text = body["message_text"]

    seller = dynamodb.get_item(dynamodb.TABLE_SELLERS, "seller_id", seller_id)
    if not seller:
        return bad_request(f"seller_id {seller_id} does not exist")

    ai = ai_service.get_ai_client()
    try:
        reply = ai.converse(
            seller_id=seller_id,
            conversation_id=conversation_id,
            message_text=message_text,
            seller_language=seller.get("seller_language", "hi"),
        )
    except ai_service.AIServiceError as exc:
        log.warning("AI service error: %s", exc)
        return upstream_error("AI service unavailable")

    return ok(reply)
