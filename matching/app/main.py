from fastapi import FastAPI, HTTPException

from app.config import MATCHING_BACKEND, OPENSEARCH_URL
from app.embeddings import EmbeddingService
from app.models import IndexRequest, IndexResponse, Listing, MatchItem, MatchRequest, MatchResponse
from app.repository import build_repository

app = FastAPI(title="Kalaa Setu Matching Service")

# Built once at startup and reused for every request — loading the embedding
# model and connecting to OpenSearch on every call would be far too slow.
embedding_service = EmbeddingService()
repository = build_repository(MATCHING_BACKEND, OPENSEARCH_URL)


def _searchable_text(listing: Listing, seller_village: str, seller_state: str) -> str:
    """Title + description + category + village, per Section 5.1 of the task
    spec — this is the text we actually embed and search over."""
    parts = [listing.listing_title, listing.description_en, listing.category, seller_village, seller_state]
    return " ".join(p for p in parts if p)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/index/listing", response_model=IndexResponse)
def index_listing(payload: IndexRequest):
    listing = payload.listing
    if listing.review_status != "approved":
        raise HTTPException(
            status_code=400,
            detail="Only approved listings can be indexed",
        )
    text = _searchable_text(listing, payload.seller_village, payload.seller_state)
    try:
        embedding = embedding_service.embed(text)
        repository.index(
            listing_id=listing.listing_id,
            embedding=embedding,
            listing_title=listing.listing_title,
            category=listing.category,
            village=payload.seller_village,
            state=payload.seller_state,
            searchable_text=text,
        )
    except Exception as exc:
        # BRAIN.md: OpenSearch unreachable -> a clear 502, never a silent drop.
        raise HTTPException(status_code=502, detail=f"Search index unavailable: {exc}") from exc
    return IndexResponse(indexed=True, listing_id=str(listing.listing_id))


@app.post("/match", response_model=MatchResponse)
def match(payload: MatchRequest):
    try:
        embedding = embedding_service.embed(payload.query_text)
        # k=5: if nothing indexed yet this is simply [] (see repository.py);
        # if there are matches but none are great, we still return the
        # closest few with their (low) scores instead of an empty result,
        # per task spec 5.2 — documented in integration-notes.md.
        results = repository.query(embedding, k=5)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Search index unavailable: {exc}") from exc
    matches = [MatchItem(**r) for r in results]
    return MatchResponse(matches=matches)
