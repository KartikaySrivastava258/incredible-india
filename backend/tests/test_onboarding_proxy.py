"""Tests for POST /onboarding/message and /listings/generate — AI proxy behavior."""

import pytest

from clients import ai_service as ai_mod
from conftest import (
    SELLER_MEERA_ID,
    decode,
    make_event,
)
from handlers import onboarding as h_onboarding
from handlers import listings as h_listings


class _FailingAIClient(ai_mod.BaseAIClient):
    def health(self): return False
    def converse(self, **kw): raise ai_mod.AIServiceError("simulated outage")
    def generate_listing(self, **kw): raise ai_mod.AIServiceError("simulated outage")
    def noble_cause_note(self, **kw): raise ai_mod.AIServiceError("simulated outage")


@pytest.fixture()
def ai_failing(monkeypatch):
    monkeypatch.setattr(ai_mod, "get_ai_client", lambda: _FailingAIClient())


@pytest.fixture()
def ai_mock(monkeypatch):
    monkeypatch.setattr(ai_mod, "get_ai_client", lambda: ai_mod.MockAIClient())


def test_onboarding_message_happy_path(seeded, ai_mock):
    event = make_event("POST", "/onboarding/message", {
        "seller_id": SELLER_MEERA_ID,
        "conversation_id": None,
        "message_text": "Main mitti ki diya banati hoon",
    })
    status, body = decode(h_onboarding.lambda_handler(event, None))

    assert status == 200
    assert "conversation_id" in body
    assert "ai_reply_text" in body
    assert body["stage"] in ("idea", "procedure", "business_model", "capture", "done")


def test_onboarding_message_ai_unavailable_502(seeded, ai_failing):
    event = make_event("POST", "/onboarding/message", {
        "seller_id": SELLER_MEERA_ID,
        "message_text": "hi",
    })
    status, body = decode(h_onboarding.lambda_handler(event, None))

    assert status == 502
    assert body["error"]["code"] == "UPSTREAM_ERROR"


def test_onboarding_message_unknown_seller_400(seeded, ai_mock):
    import uuid
    event = make_event("POST", "/onboarding/message", {
        "seller_id": str(uuid.uuid4()),
        "message_text": "hi",
    })
    status, body = decode(h_onboarding.lambda_handler(event, None))

    assert status == 400
    assert "does not exist" in body["error"]["message"]


def test_generate_listing_happy_path(seeded, ai_mock):
    event = make_event("POST", "/listings/generate", {
        "seller_id": SELLER_MEERA_ID,
        "conversation_id": "any-conv-id",
    })
    status, body = decode(h_listings.lambda_handler(event, None))

    assert status == 201
    assert body["review_status"] == "pending"
    assert "listing_id" in body
    assert "compliance_flags" in body


def test_generate_listing_ai_unavailable_502(seeded, ai_failing):
    event = make_event("POST", "/listings/generate", {
        "seller_id": SELLER_MEERA_ID,
        "conversation_id": "any-conv-id",
    })
    status, body = decode(h_listings.lambda_handler(event, None))

    assert status == 502
    assert body["error"]["code"] == "UPSTREAM_ERROR"
