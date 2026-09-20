"""Tests for GET /ledger/:seller_id — Cedar enforcement (MUST + SHOULD rules)."""

from conftest import (
    BUYER_ID,
    LISTING_DIYA_ID,
    LISTING_PICKLE_ID,
    SELLER_MEERA_ID,
    SELLER_RAMESH_ID,
    TP_CSC_ID,
    TP_SCHOOL_ID,
    decode,
    make_event,
)
from handlers import ledger as h_ledger
from handlers import sales as h_sales


def _make_sale(listing_id, seller_id, amount=1000):
    event = make_event("POST", "/sales", {
        "listing_id": listing_id,
        "buyer_id": BUYER_ID,
        "sale_amount": amount,
        "principal_seller_id": seller_id,
    })
    status, body = decode(h_sales.lambda_handler(event, None))
    assert status == 201
    return body


def _ledger_event(seller_id, principal_type, principal_value):
    if principal_type == "Seller":
        headers = {
            "X-Principal-Type": "Seller",
            "X-Principal-Seller-Id": principal_value,
        }
    else:
        headers = {
            "X-Principal-Type": "TouchpointAdmin",
            "X-Principal-Touchpoint-Id": principal_value,
        }
    return make_event(
        "GET", f"/ledger/{seller_id}",
        path_params={"seller_id": seller_id},
        headers=headers,
    )


def test_seller_can_read_own_ledger(seeded):
    sale = _make_sale(LISTING_DIYA_ID, SELLER_MEERA_ID, amount=500)

    event = _ledger_event(SELLER_MEERA_ID, "Seller", SELLER_MEERA_ID)
    status, body = decode(h_ledger.lambda_handler(event, None))

    assert status == 200
    assert len(body["entries"]) == 1
    assert body["entries"][0]["ledger_entry_id"] == sale["ledger_entry_id"]


def test_seller_cannot_read_another_sellers_ledger(seeded):
    _make_sale(LISTING_DIYA_ID, SELLER_MEERA_ID, amount=500)

    # Ramesh tries to read Meera's ledger → Cedar denies 403
    event = _ledger_event(SELLER_MEERA_ID, "Seller", SELLER_RAMESH_ID)
    status, body = decode(h_ledger.lambda_handler(event, None))

    assert status == 403
    assert body["error"]["code"] == "FORBIDDEN"


def test_touchpoint_admin_can_read_their_village_ledger(seeded):
    _make_sale(LISTING_DIYA_ID, SELLER_MEERA_ID, amount=500)

    # School admin (Rampur) reads Meera's ledger
    event = _ledger_event(SELLER_MEERA_ID, "TouchpointAdmin", TP_SCHOOL_ID)
    status, body = decode(h_ledger.lambda_handler(event, None))

    assert status == 200
    assert len(body["entries"]) == 1


def test_touchpoint_admin_cannot_read_other_village_ledger(seeded):
    _make_sale(LISTING_DIYA_ID, SELLER_MEERA_ID, amount=500)

    # CSC admin (Devgaon) tries to read Meera's (Rampur) ledger → 403
    event = _ledger_event(SELLER_MEERA_ID, "TouchpointAdmin", TP_CSC_ID)
    status, body = decode(h_ledger.lambda_handler(event, None))

    assert status == 403
    assert body["error"]["code"] == "FORBIDDEN"
    assert body["error"]["message"].startswith("Cedar denied:")
    assert body["error"]["details"]["policy"] == "touchpoint_admin_scope.cedar"
    assert body["error"]["details"]["action"] == "viewLedgerData"
    assert body["error"]["details"]["principal_touchpoint_id"] == TP_CSC_ID
    assert body["error"]["details"]["resource_touchpoint_id"] == TP_SCHOOL_ID


def test_unknown_seller_404(seeded):
    event = _ledger_event("no-such-seller", "Seller", "no-such-seller")
    status, body = decode(h_ledger.lambda_handler(event, None))

    assert status == 404


def test_missing_principal_header_400(seeded):
    event = make_event(
        "GET", f"/ledger/{SELLER_MEERA_ID}",
        path_params={"seller_id": SELLER_MEERA_ID},
        headers={},
    )
    status, body = decode(h_ledger.lambda_handler(event, None))

    assert status == 400
