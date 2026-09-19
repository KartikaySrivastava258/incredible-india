"""Tests for POST /contributions — Cedar enforcement (MUST rule)."""

from conftest import (
    SELLER_MEERA_ID,
    SELLER_RAMESH_ID,
    TP_SCHOOL_ID,
    decode,
    make_event,
)
from handlers import contributions as h_contributions


def _body(seller_id, principal_seller_id, opted_in=True, percentage=5, touchpoint_id=TP_SCHOOL_ID):
    return {
        "seller_id": seller_id,
        "opted_in": opted_in,
        "percentage": percentage,
        "touchpoint_id": touchpoint_id,
        "principal_seller_id": principal_seller_id,
    }


def test_seller_can_set_their_own_contribution(seeded):
    event = make_event("POST", "/contributions", _body(SELLER_MEERA_ID, SELLER_MEERA_ID))
    status, body = decode(h_contributions.lambda_handler(event, None))

    assert status == 200
    assert body["seller_id"] == SELLER_MEERA_ID
    assert body["opted_in"] is True
    assert body["percentage"] == 5


def test_seller_cannot_set_another_sellers_contribution(seeded):
    """Cedar MUST rule: a seller can only set their own contribution."""
    event = make_event(
        "POST", "/contributions",
        _body(SELLER_RAMESH_ID, SELLER_MEERA_ID),   # Meera is trying to act as Ramesh
    )
    status, body = decode(h_contributions.lambda_handler(event, None))

    assert status == 403
    assert body["error"]["code"] == "FORBIDDEN"
    assert "Cedar" in body["error"]["message"]


def test_percentage_out_of_range_high(seeded):
    event = make_event(
        "POST", "/contributions",
        _body(SELLER_MEERA_ID, SELLER_MEERA_ID, opted_in=True, percentage=150),
    )
    status, body = decode(h_contributions.lambda_handler(event, None))

    assert status == 400
    assert "0 and 100" in body["error"]["message"]


def test_percentage_out_of_range_low(seeded):
    event = make_event(
        "POST", "/contributions",
        _body(SELLER_MEERA_ID, SELLER_MEERA_ID, opted_in=True, percentage=-1),
    )
    status, body = decode(h_contributions.lambda_handler(event, None))

    assert status == 400
    assert "0 and 100" in body["error"]["message"]


def test_opt_in_true_requires_nonzero_percentage(seeded):
    event = make_event(
        "POST", "/contributions",
        _body(SELLER_MEERA_ID, SELLER_MEERA_ID, opted_in=True, percentage=0),
    )
    status, body = decode(h_contributions.lambda_handler(event, None))

    assert status == 400
    assert "> 0" in body["error"]["message"]


def test_unknown_seller_400(seeded):
    import uuid
    event = make_event(
        "POST", "/contributions",
        _body(str(uuid.uuid4()), str(uuid.uuid4())),
    )
    status, body = decode(h_contributions.lambda_handler(event, None))

    assert status == 400
    assert "does not exist" in body["error"]["message"]


def test_missing_field_400(seeded):
    event = make_event("POST", "/contributions", {
        "seller_id": SELLER_MEERA_ID,
        "principal_seller_id": SELLER_MEERA_ID,
        # opted_in, percentage, touchpoint_id all missing
    })
    status, body = decode(h_contributions.lambda_handler(event, None))

    assert status == 400
    assert "opted_in" in body["error"]["message"]
