"""Tests for GET /impact — aggregate dashboard numbers."""

from conftest import (
    BUYER_ID,
    LISTING_DIYA_ID,
    LISTING_PICKLE_ID,
    SELLER_MEERA_ID,
    SELLER_RAMESH_ID,
    decode,
    make_event,
)
from handlers import impact as h_impact
from handlers import sales as h_sales


def _sale(listing_id, seller_id, amount=1000):
    event = make_event("POST", "/sales", {
        "listing_id": listing_id,
        "buyer_id": BUYER_ID,
        "sale_amount": amount,
        "principal_seller_id": seller_id,
    })
    status, _ = decode(h_sales.lambda_handler(event, None))
    assert status == 201


def test_impact_empty_seed(seeded):
    """No sales yet → zeros except opt-in rate."""
    event = make_event("GET", "/impact")
    status, body = decode(h_impact.lambda_handler(event, None))

    assert status == 200
    assert body["villages_onboarded"] == 2        # Rampur + Devgaon
    assert body["sellers_earning"] == 0
    assert body["total_community_funds"] == 0.0
    assert body["opt_in_rate"] == 0.5             # Meera in, Ramesh not


def test_impact_after_sales(seeded):
    """Meera opted in at 5%. Sale 1000 → contribution 47.5. Ramesh not opted in → 0."""
    _sale(LISTING_DIYA_ID, SELLER_MEERA_ID, amount=1000)
    _sale(LISTING_PICKLE_ID, SELLER_RAMESH_ID, amount=1000)

    event = make_event("GET", "/impact")
    status, body = decode(h_impact.lambda_handler(event, None))

    assert status == 200
    assert body["sellers_earning"] == 2
    assert body["total_community_funds"] == 47.5
    assert body["opt_in_rate"] == 0.5


def test_impact_villages_only_counts_touchpoints_with_sellers(seeded):
    """Both seeded touchpoints have sellers, so both villages count."""
    event = make_event("GET", "/impact")
    status, body = decode(h_impact.lambda_handler(event, None))

    assert body["villages_onboarded"] == 2
