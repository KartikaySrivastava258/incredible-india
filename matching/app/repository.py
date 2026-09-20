"""SearchRepository: the swappable storage layer for the matching service.

Two implementations share the exact same method signatures, so the rest of
the app (main.py) never knows or cares which one is actually running:

- InMemorySearchRepository — pure Python + numpy, zero external services.
  Used automatically if OpenSearch isn't reachable, and used by the test
  suite so tests never need Docker running.
- OpenSearchRepository — the real thing: a k-NN vector index in local
  OpenSearch. This is what must be running for the hackathon demo, because
  BRAIN.md requires "real vector search, not `if query == X`".

Which one main.py picks is controlled by MATCHING_BACKEND in .env
("opensearch" or "memory"). There is deliberately no automatic fallback:
when OpenSearch is configured but unavailable, requests return a clear 502
instead of silently indexing/searching a different backend.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import numpy as np

EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 output size
INDEX_NAME = "kalaa_setu_listings"


class SearchRepository(ABC):
    """Interface every backend must implement."""

    @abstractmethod
    def index(
        self,
        listing_id: str,
        embedding: List[float],
        listing_title: str,
        category: str,
        village: str,
        state: str,
        searchable_text: str,
    ) -> None:
        """Upsert one listing. Calling this again with the same listing_id
        must overwrite the previous document, never create a duplicate."""

    @abstractmethod
    def query(self, embedding: List[float], k: int = 5) -> List[Dict[str, Any]]:
        """Return up to k nearest listings as
        [{"listing_id": ..., "score": ..., "listing_title": ...}, ...],
        ordered best-match first. Returns [] if nothing is indexed yet —
        never raises just because there are zero results."""

    @abstractmethod
    def health(self) -> bool:
        """True if the backend is reachable right now."""


class InMemorySearchRepository(SearchRepository):
    """Cosine-similarity search over an in-process dict. Good enough for
    local dev without Docker, and for unit tests."""

    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, Any]] = {}

    def index(
        self,
        listing_id: str,
        embedding: List[float],
        listing_title: str,
        category: str,
        village: str,
        state: str,
        searchable_text: str,
    ) -> None:
        # Assigning by key is itself the upsert: a second call with the same
        # listing_id just overwrites the old entry, so no duplicates.
        self._store[listing_id] = {
            "embedding": np.array(embedding, dtype=np.float32),
            "listing_title": listing_title,
            "category": category,
            "village": village,
            "state": state,
        }

    def query(self, embedding: List[float], k: int = 5) -> List[Dict[str, Any]]:
        if not self._store:
            return []
        ids = list(self._store.keys())
        vectors = np.stack([self._store[i]["embedding"] for i in ids])
        q = np.array(embedding, dtype=np.float32)
        # Embeddings are pre-normalized (see EmbeddingService), so a plain
        # dot product IS cosine similarity here.
        scores = vectors @ q
        order = np.argsort(-scores)[:k]
        return [
            {
                "listing_id": ids[i],
                "score": float(scores[i]),
                "listing_title": self._store[ids[i]]["listing_title"],
            }
            for i in order
        ]

    def health(self) -> bool:
        return True


class OpenSearchRepository(SearchRepository):
    """Real k-NN vector search backed by local OpenSearch."""

    def __init__(self, url: str) -> None:
        from opensearchpy import OpenSearch

        self._client = OpenSearch(hosts=[url], use_ssl=False, verify_certs=False)

    def _ensure_index(self) -> None:
        if self._client.indices.exists(index=INDEX_NAME):
            return
        self._client.indices.create(
            index=INDEX_NAME,
            body={
                "settings": {"index": {"knn": True}},
                "mappings": {
                    "properties": {
                        "listing_id": {"type": "keyword"},
                        "listing_title": {"type": "text"},
                        "category": {"type": "keyword"},
                        "village": {"type": "keyword"},
                        "state": {"type": "keyword"},
                        "searchable_text": {"type": "text"},
                        "embedding": {
                            "type": "knn_vector",
                            "dimension": EMBEDDING_DIM,
                            "method": {
                                "name": "hnsw",
                                "space_type": "cosinesimil",
                                "engine": "nmslib",
                            },
                        },
                    }
                },
            },
        )

    def index(
        self,
        listing_id: str,
        embedding: List[float],
        listing_title: str,
        category: str,
        village: str,
        state: str,
        searchable_text: str,
    ) -> None:
        self._ensure_index()
        self._client.index(
            index=INDEX_NAME,
            id=listing_id,
            body={
                "listing_id": listing_id,
                "listing_title": listing_title,
                "category": category,
                "village": village,
                "state": state,
                "searchable_text": searchable_text,
                "embedding": embedding,
            },
            refresh=True,
        )

    def query(self, embedding: List[float], k: int = 5) -> List[Dict[str, Any]]:
        if not self._client.indices.exists(index=INDEX_NAME):
            return []
        body = {
            "size": k,
            "query": {"knn": {"embedding": {"vector": embedding, "k": k}}},
        }
        resp = self._client.search(index=INDEX_NAME, body=body)
        return [
            {
                "listing_id": hit["_source"]["listing_id"],
                "score": float(hit["_score"]),
                "listing_title": hit["_source"]["listing_title"],
            }
            for hit in resp["hits"]["hits"]
        ]

    def health(self) -> bool:
        try:
            return bool(self._client.ping())
        except Exception:
            return False

def build_repository(backend: str, opensearch_url: Optional[str]) -> SearchRepository:
    """Build the configured repository without making startup depend on a live cluster."""
    if backend == "opensearch":
        if not opensearch_url:
            raise ValueError("OPENSEARCH_URL is required when MATCHING_BACKEND=opensearch")
        return OpenSearchRepository(opensearch_url)
    if backend == "memory":
        return InMemorySearchRepository()
    raise ValueError("MATCHING_BACKEND must be 'opensearch' or 'memory'")
