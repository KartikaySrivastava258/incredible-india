"""
Kalaa Setu — client for the AI service.

Real client: HTTP calls to AI_SERVICE_URL.
Mock client: in-process, schema-accurate canned responses, selected when
             AI_SERVICE_URL is unreachable and USE_AI_MOCK=1 (or by explicit env).

Both implement the exact same methods with the exact same return shapes.
Handlers import get_ai_client() and never know which one is in use.
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any

import requests

log = logging.getLogger("kalaa.ai_client")

DEFAULT_TIMEOUT = 15


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------

class AIServiceError(Exception):
    """Raised when the AI service is unavailable or returns malformed data."""


class BaseAIClient:
    def health(self) -> bool: ...
    def converse(self, seller_id: str, conversation_id: str | None, message_text: str) -> dict: ...
    def generate_listing(self, seller_id: str, conversation_id: str) -> dict: ...
    def noble_cause_note(self, listing_id: str, seller_id: str) -> str: ...


# ---------------------------------------------------------------------------
# Real HTTP client
# ---------------------------------------------------------------------------

class HttpAIClient(BaseAIClient):
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}"
        try:
            resp = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
        except requests.RequestException as exc:
            raise AIServiceError(f"AI service unreachable at {url}: {exc}") from exc

        if resp.status_code >= 500:
            raise AIServiceError(f"AI service {path} returned {resp.status_code}")
        try:
            return resp.json()
        except ValueError as exc:
            raise AIServiceError(f"AI service {path} returned non-JSON") from exc

    def health(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/health", timeout=5)
            return r.status_code == 200
        except requests.RequestException:
            return False

    def converse(self, seller_id: str, conversation_id: str | None, message_text: str) -> dict:
        body = self._post(
            "/agent/converse",
            {
                "seller_id": seller_id,
                "conversation_id": conversation_id,
                "message_text": message_text,
            },
        )
        _validate_converse(body)
        return body

    def generate_listing(self, seller_id: str, conversation_id: str) -> dict:
        body = self._post(
            "/agent/generate-listing",
            {"seller_id": seller_id, "conversation_id": conversation_id},
        )
        _validate_listing(body)
        return body

    def noble_cause_note(self, listing_id: str, seller_id: str) -> str:
        body = self._post(
            "/agent/noble-cause-note",
            {"listing_id": listing_id, "seller_id": seller_id},
        )
        note = body.get("noble_cause_note")
        if not isinstance(note, str):
            raise AIServiceError("AI service noble-cause-note returned malformed payload")
        return note


# ---------------------------------------------------------------------------
# Mock client (schema-accurate)
# ---------------------------------------------------------------------------

class MockAIClient(BaseAIClient):
    """
    In-process stub. Returns payloads with the same keys and value types as
    the real service, so no calling code has to change when the real service
    is swapped in.
    """

    def health(self) -> bool:
        return True

    def converse(self, seller_id: str, conversation_id: str | None, message_text: str) -> dict:
        stage = _guess_stage(message_text)
        reply = {
            "idea":           "Aap kya banate hain? Apne product ke baare mein bataiye.",
            "procedure":      "Amazon par bikri ke liye hum aapki photo, description aur category lete hain.",
            "business_model": "Aap chahein to apne net kamai ka ek hissa apne school/CSC fund mein de sakte hain.",
            "capture":        "Dhanyavaad. Ab main aapki listing bana raha hoon.",
            "done":           "Aapki listing taiyaar hai.",
        }.get(stage, "Bataiye aage.")

        return {
            "conversation_id": conversation_id or str(uuid.uuid4()),
            "ai_reply_text": reply,
            "stage": stage,
            "draft_state": {
                "seller_id": seller_id,
                "last_message": message_text,
            },
        }

    def generate_listing(self, seller_id: str, conversation_id: str) -> dict:
        # Schema-accurate Listing shape (BRAIN.md Section F).
        return {
            "listing_id": str(uuid.uuid4()),
            "product_id": str(uuid.uuid4()),
            "category": "handicraft",
            "listing_title": "Handmade Terracotta Diya Set",
            "description_en": "A set of handcrafted terracotta diyas made by a rural artisan.",
            "description_local": "Haath se banayi gayi mitti ki diya.",
            "price_suggestion": 299,
            "photo_guidance": [
                "shoot in daylight",
                "show size next to a coin",
            ],
            "story": "Your purchase supports a rural artisan family and their local school fund.",
            "compliance_flags": [],
            "review_status": "pending",
            "created_at": _now_iso(),
        }

    def noble_cause_note(self, listing_id: str, seller_id: str) -> str:
        return "This purchase supports a rural artisan family and their local community fund."


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_ai_client() -> BaseAIClient:
    """
    Return the AI client based on env:
      - AI_CLIENT_MODE=http  -> HttpAIClient (default)
      - AI_CLIENT_MODE=mock  -> MockAIClient
      - AI_CLIENT_MODE=auto  -> try http /health once; fall back to mock
    """
    mode = os.environ.get("AI_CLIENT_MODE", "auto").lower()
    base_url = os.environ.get("AI_SERVICE_URL", "http://localhost:8001")

    if mode == "mock":
        log.info("using MockAIClient (forced)")
        return MockAIClient()

    if mode == "http":
        log.info("using HttpAIClient -> %s", base_url)
        return HttpAIClient(base_url)

    # auto
    client = HttpAIClient(base_url)
    if client.health():
        log.info("using HttpAIClient -> %s", base_url)
        return client
    log.warning("AI service at %s not reachable; falling back to MockAIClient", base_url)
    return MockAIClient()


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------

def _validate_converse(body: dict) -> None:
    required = ("conversation_id", "ai_reply_text", "stage", "draft_state")
    for k in required:
        if k not in body:
            raise AIServiceError(f"AI converse response missing '{k}'")


def _validate_listing(body: dict) -> None:
    required = ("listing_id", "product_id", "category", "listing_title", "description_en",
                "price_suggestion", "compliance_flags", "review_status", "created_at")
    for k in required:
        if k not in body:
            raise AIServiceError(f"AI listing response missing '{k}'")
    if body["review_status"] not in ("pending", "approved", "rejected"):
        raise AIServiceError("AI listing review_status invalid")


def _guess_stage(message_text: str) -> str:
    t = (message_text or "").lower()
    if any(w in t for w in ("banat", "product", "diya", "achaar", "kapda")):
        return "procedure"
    if any(w in t for w in ("paisa", "kitna", "keemat")):
        return "business_model"
    if any(w in t for w in ("haan", "theek", "ok")):
        return "capture"
    return "idea"


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
