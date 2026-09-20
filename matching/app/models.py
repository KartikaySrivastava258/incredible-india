"""Data shapes for the Matching Service.

These mirror the canonical schemas in BRAIN.md Section F / shared/schemas.json.
We only need the fields the matching service actually reads, but we accept
(and ignore) any extra fields the backend sends us, so we never break if the
Listing object gains new optional fields later.
"""
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, UUID4


class Listing(BaseModel):
    """A Listing object as produced by the AI service and reviewed by the backend."""

    model_config = ConfigDict(extra="ignore")

    listing_id: UUID4
    product_id: UUID4
    category: str
    listing_title: str
    description_en: str
    description_local: Optional[str] = None
    price_suggestion: float
    photo_guidance: List[str] = Field(default_factory=list)
    story: Optional[str] = None
    compliance_flags: List[str] = Field(default_factory=list)
    review_status: str
    created_at: str


class IndexRequest(BaseModel):
    """POST /index/listing request body."""

    listing: Listing
    seller_village: str
    seller_state: str


class IndexResponse(BaseModel):
    """POST /index/listing response body."""

    indexed: bool
    listing_id: str


class MatchRequest(BaseModel):
    """POST /match request body."""

    query_text: str = Field(min_length=1)
    buyer_id: Optional[UUID4] = None


class MatchItem(BaseModel):
    listing_id: UUID4
    score: float
    listing_title: str


class MatchResponse(BaseModel):
    """POST /match response body."""

    matches: List[MatchItem]
