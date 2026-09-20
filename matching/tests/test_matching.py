"""Tests for the matching service.

These run against InMemorySearchRepository directly, so `pytest` works with
no Docker/OpenSearch running — exactly the "mock behind a repository
interface" strategy described in the task file (Section 11). The real
OpenSearchRepository shares the same interface and isn't re-tested here
since exercising it needs a live cluster; verify it manually with
docker-compose up + scripts/seed_opensearch.py before the demo.
"""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import main as main_module  # noqa: E402
from app.repository import InMemorySearchRepository  # noqa: E402


class FakeEmbeddingService:
    """Small deterministic embedding stub for API tests.

    It deliberately avoids loading the production transformer model during
    pytest while preserving normalized-vector semantics.
    """

    def embed(self, text):
        vocabulary = ["handmade", "clay", "showpiece", "pottery", "pushkar", "steel", "faucet"]
        values = [1.0 if token in text.lower() else 0.0 for token in vocabulary]
        norm = sum(v * v for v in values) ** 0.5
        if norm == 0:
            return [0.0] * len(values)
        return [v / norm for v in values]


SAMPLE_LISTING = {
    "listing_id": "11111111-1111-4111-8111-111111111111",
    "product_id": "22222222-2222-4222-8222-222222222222",
    "category": "handicraft",
    "listing_title": "Handmade Blue Pottery Clay Showpiece",
    "description_en": "A hand-painted blue pottery showpiece, shaped and fired by a Pushkar artisan family.",
    "price_suggestion": 650,
    "compliance_flags": [],
    "review_status": "approved",
    "created_at": "2026-09-14T10:00:00Z",
}


@pytest.fixture(autouse=True)
def in_memory_repository(monkeypatch):
    """Force every test onto a fresh in-memory repository, regardless of
    whatever MATCHING_BACKEND is set to in the environment."""
    repo = InMemorySearchRepository()
    monkeypatch.setattr(main_module, "repository", repo)
    monkeypatch.setattr(main_module, "embedding_service", FakeEmbeddingService())
    return repo


@pytest.fixture
def client():
    return TestClient(main_module.app)


def _index(client, listing=None, village="Pushkar", state="Rajasthan"):
    body = {
        "listing": listing or SAMPLE_LISTING,
        "seller_village": village,
        "seller_state": state,
    }
    return client.post("/index/listing", json=body)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_index_then_find_via_related_query(client):
    resp = _index(client)
    assert resp.status_code == 200
    assert resp.json() == {"indexed": True, "listing_id": SAMPLE_LISTING["listing_id"]}

    resp = client.post("/match", json={"query_text": "handmade clay showpiece for home decor"})
    assert resp.status_code == 200
    matches = resp.json()["matches"]
    assert len(matches) >= 1
    assert matches[0]["listing_id"] == SAMPLE_LISTING["listing_id"]
    assert matches[0]["score"] > 0  # the real model should score this clearly above zero


def test_upsert_same_listing_id_does_not_duplicate(client, in_memory_repository):
    _index(client)
    updated = dict(SAMPLE_LISTING, listing_title="Hand-Painted Blue Pottery Showpiece (Updated)")
    _index(client, listing=updated)

    assert len(in_memory_repository._store) == 1
    resp = client.post("/match", json={"query_text": "clay showpiece"})
    titles = [m["listing_title"] for m in resp.json()["matches"]]
    assert titles == ["Hand-Painted Blue Pottery Showpiece (Updated)"]


def test_query_with_no_good_match_still_returns_valid_response(client):
    _index(client)
    resp = client.post("/match", json={"query_text": "stainless steel kitchen faucet spare part"})
    assert resp.status_code == 200
    # Still a valid response with the closest (low-score) results, not an error.
    assert isinstance(resp.json()["matches"], list)


def test_rejects_non_approved_listing(client):
    pending = dict(SAMPLE_LISTING, review_status="pending")
    resp = _index(client, listing=pending)
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Only approved listings can be indexed"


def test_match_with_nothing_indexed_returns_empty_list(client):
    resp = client.post("/match", json={"query_text": "anything at all"})
    assert resp.status_code == 200
    assert resp.json() == {"matches": []}
