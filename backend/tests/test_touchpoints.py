"""Tests for POST /touchpoints."""

from conftest import decode, make_event
from handlers import touchpoints as h_touchpoints


def test_create_touchpoint_happy_path(tables):
    event = make_event("POST", "/touchpoints", {
        "name": "Test School",
        "type": "school",
        "village": "TestVillage",
        "state": "TestState",
        "pickup_address": "123 Test Road",
    })
    status, body = decode(h_touchpoints.lambda_handler(event, None))

    assert status == 201
    assert body["name"] == "Test School"
    assert body["type"] == "school"
    assert "touchpoint_id" in body


def test_create_touchpoint_invalid_type(tables):
    event = make_event("POST", "/touchpoints", {
        "name": "Bad",
        "type": "cafe",
        "village": "V",
        "state": "S",
        "pickup_address": "A",
    })
    status, body = decode(h_touchpoints.lambda_handler(event, None))

    assert status == 400
    assert body["error"]["code"] == "BAD_REQUEST"
    assert "type must be" in body["error"]["message"]


def test_create_touchpoint_missing_field(tables):
    event = make_event("POST", "/touchpoints", {
        "name": "Test",
        "type": "school",
        "village": "V",
        "state": "S",
    })
    status, body = decode(h_touchpoints.lambda_handler(event, None))

    assert status == 400
    assert "pickup_address" in body["error"]["message"]
