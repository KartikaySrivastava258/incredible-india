"""
Kalaa Setu — client for the Matching service.

Real client: HTTP calls to MATCHING_SERVICE_URL.
Mock client: in-process, schema-accurate canned responses, selected when
             MATCHING_SERVICE_URL is unreachable and MATCHING_CLIENT_MODE=auto.

Both implement the exact same methods with the exact same return shapes.
Handlers import get_matching_client() and never know which one is in use.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import requests

log = logging.getLogger("kalaa.matching_client")

DEFAULT_TIMEOUT = 15


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------

class MatchingServiceError(Exception):
    """Raised when the Matching service is unavailable or returns malformed data."""


class BaseMatchingClient:
    def health(self) -> bool: ...
    def index_listing(self, listing: dict) -> dict: ...
    def match(self, query_text: str, buyer_id: str | None) -> dict: ...


# ---------------------------------------------------------------------------
# Real HTTP client
# ---------------------------------------------------------------------------

class HttpMatchingClient(BaseMatchingClient):
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}"
        try:
            resp = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
        except requests.RequestException as exc:
            raise MatchingServiceError(f"Matching service unreachable at {url}: {exc}") from exc

        if resp.status_code >= 500:
            raise MatchingServiceError(f"Matching service {path} returned {resp.status_code}")
        try:
            return resp.json()
        except ValueError as exc:
            raise MatchingServiceError(f"Matching service {path} returned non-JSON") from exc

    def health(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/health", timeout=5)
            return r.status_code == 200
        except requests.RequestException:
            return False

    def index_listing(self, listing: dict) -> dict:
        body = self._post("/index/listing", {"listing": listing})
        if "indexed" not in body:
            raise MatchingServiceError("Matching index/listing response missing 'indexed'")
        return body

    def match(self, query_text: str, buyer_id: str | None) -> dict:
        body = self._post(
            "/match",
            {"query_text": query_text, "buyer_id": buyer_id},
        )
        _validate_match(body)
        return body


# ---------------------------------------------------------------------------
# Mock client (schema-accurate)
# ---------------------------------------------------------------------------

class MockMatchingClient(BaseMatchingClient):
    """
    In-process stub. Backed by a tiny in-memory list of sample listings.
    Returns payloads with the same keys and value types as the real service.
    """

    def __init__(self):
        # Sample listings the mock can "find". Shaped like Listing objects.
        self._indexed: list[dict] = []

    def health(self) -> bool:
        return True

    def index_listing(self, listing: dict) -> dict:
        self._indexed.append(listing)
        return {
            "indexed": True,
            "listing_id": listing.get("listing_id"),
            "index_name": "kalaa-listings-mock",
        }

    def match(self, query_text: str, buyer_id: str | None) -> dict:
        q = (query_text or "").lower()
        matches: list[dict] = []

        for listing in self._indexed:
            title = (listing.get("listing_title") or "").lower()
            desc = (listing.get("description_en") or "").lower()
            # Extremely simple relevance: any word overlap counts.
            if any(w in title or w in desc for w in q.split() if w):
                matches.append({
                    "listing_id": listing.get("listing_id"),
                    "score": 0.9,
                    "listing_title": listing.get("listing_title"),
                    "noble_cause_note": None,  # backend fills this in
                })

        return {"matches": matches}


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_matching_client() -> BaseMatchingClient:
    """
    Return the Matching client based on env:
      - MATCHING_CLIENT_MODE=http  -> HttpMatchingClient (default)
      - MATCHING_CLIENT_MODE=mock  -> MockMatchingClient
      - MATCHING_CLIENT_MODE=auto  -> try http /health once; fall back to mock
    """
    mode = os.environ.get("MATCHING_CLIENT_MODE", "auto").lower()
    base_url = os.environ.get("MATCHING_SERVICE_URL", "http://localhost:8002")

    if mode == "mock":
        log.info("using MockMatchingClient (forced)")
        return MockMatchingClient()

    if mode == "http":
        log.info("using HttpMatchingClient -> %s", base_url)
        return HttpMatchingClient(base_url)

    client = HttpMatchingClient(base_url)
    if client.health():
        log.info("using HttpMatchingClient -> %s", base_url)
        return client
    log.warning("Matching service at %s not reachable; falling back to MockMatchingClient", base_url)
    return MockMatchingClient()


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------

def _validate_match(body: dict) -> None:
    if "matches" not in body or not isinstance(body["matches"], list):
        raise MatchingServiceError("Matching /match response missing 'matches' list")
    for m in body["matches"]:
        for k in ("listing_id", "score", "listing_title"):
            if k not in m:
                raise MatchingServiceError(f"Matching match item missing '{k}'")
