"""Tests for POST /sales — Cedar enforcement (MUST rule #2) and ledger math."""

from conftest import (
    BUYER_ID,
    LISTING_DIYA_ID,
    LISTING_PICKLE_ID,
    SELLER_MEERA_ID,
    SELLER_RAMESH_ID,
    decode,
    make_event,
)
from handlers import sales as h_sales


def _body(listing_id, principal_seller_id, sale_amount=1000, buyer_id=BUYER_ID):
    return {
        "listing_id": listing_id,
        "buyer_id": buyer_id,
        "sale_amount": sale_amount,
        "principal_seller_id": principal_seller_id,
    }


def test_sale_with_opted_in_seller_computes_contribution(seeded):
    """Meera is opted in at 5%. Sale 1000 → fee 50, net 950, contribution 47.5."""
    event = make_event("POST", "/sales", _body(LISTING_DIYA_ID, SELLER_MEERA_ID, sale_amount=1000))
    status, body = decode(h_sales.lambda_handler(event, None))

    assert status == 201
    assert body["sale_amount"] == 1000
    assert body["platform_fee"] == 50.0
    assert body["seller_net"] == 950.0
    assert body["contribution_amount"] == 47.5
    assert body["buyer_visible"] is True
    assert body["seller_id"] == SELLER_MEERA_ID
    assert "ledger_entry_id" in body


def test_sale_with_not_opted_in_seller_forces_zero_contribution(seeded):
    """Ramesh is NOT opted in. contribution_amount must be 0 — Cedar-enforced."""
    event = make_event("POST", "/sales", _body(LISTING_PICKLE_ID, SELLER_RAMESH_ID, sale_amount=1000))
    status, body = decode(h_sales.lambda_handler(event, None))

    assert status == 201
    assert body["contribution_amount"] == 0.0
    assert body["buyer_visible"] is False
    assert body["seller_id"] == SELLER_RAMESH_ID


def test_sale_amount_zero_rejected(seeded):
    event = make_event("POST", "/sales", _body(LISTING_DIYA_ID, SELLER_MEERA_ID, sale_amount=0))
    status, body = decode(h_sales.lambda_handler(event, None))

    assert status == 400
    assert "> 0" in body["error"]["message"]


def test_sale_amount_negative_rejected(seeded):
    event = make_event("POST", "/sales", _body(LISTING_DIYA_ID, SELLER_MEERA_ID, sale_amount=-10))
    status, body = decode(h_sales.lambda_handler(event, None))

    assert status == 400


def test_sale_listing_not_approved_rejected(tables):
    """Create a pending listing and try to sell it — must be 400."""
    db = tables
    from conftest import (
        PRODUCT_DIYA_ID, SELLER_MEERA_ID, TP_SCHOOL_ID, now_iso,
    )
    db.put_item(db.TABLE_SELLERS, {
        "seller_id": SELLER_MEERA_ID, "name": "Meera", "village": "R", "state": "RJ",
        "seller_language": "hi", "touchpoint_id": TP_SCHOOL_ID, "created_at": now_iso(),
    })
    db.put_item(db.TABLE_PRODUCTS, {
        "product_id": PRODUCT_DIYA_ID, "seller_id": SELLER_MEERA_ID, "category": "handicraft",
        "raw_description": "x", "seller_language": "hi", "created_at": now_iso(),
    })
    db.put_item(db.TABLE_LISTINGS, {
        "listing_id": "pending-listing-1", "product_id": PRODUCT_DIYA_ID, "category": "handicraft",
        "listing_title": "T", "description_en": "D", "price_suggestion": 100,
        "compliance_flags": [], "review_status": "pending", "created_at": now_iso(),
    })
    event = make_event("POST", "/sales", _body("pending-listing-1", SELLER_MEERA_ID))
    status, body = decode(h_sales.lambda_handler(event, None))

    assert status == 400
    assert "approved" in body["error"]["message"]


def test_sale_listing_not_found_404(seeded):
    event = make_event("POST", "/sales", _body("no-such-listing", SELLER_MEERA_ID))
    status, body = decode(h_sales.lambda_handler(event, None))

    assert status == 404
