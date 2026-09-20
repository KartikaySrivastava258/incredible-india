"""Tests for POST /sellers."""

import uuid

from conftest import TP_SCHOOL_ID, decode, make_event
from handlers import sellers as h_sellers


def test_create_seller_happy_path(seeded):
    event = make_event("POST", "/sellers", {
        "name": "Test Seller",
        "village": "Rampur",
        "state": "Rajasthan",
        "seller_language": "hi",
        "touchpoint_id": TP_SCHOOL_ID,
        "phone": "+919999999999",
    })
    status, body = decode(h_sellers.lambda_handler(event, None))

    assert status == 201
    assert body["name"] == "Test Seller"
    assert body["village"] == "Rampur"
    assert body["touchpoint_id"] == TP_SCHOOL_ID
    assert "seller_id" in body
    assert "created_at" in body
    # seller_id must be a valid UUID
    uuid.UUID(body["seller_id"])


def test_create_seller_missing_required_field(tables):
    event = make_event("POST", "/sellers", {
        "village": "Rampur",
        "state": "Rajasthan",
        "seller_language": "hi",
        "touchpoint_id": TP_SCHOOL_ID,
    })
    status, body = decode(h_sellers.lambda_handler(event, None))

    assert status == 400
    assert body["error"]["code"] == "BAD_REQUEST"
    assert "name" in body["error"]["message"]


def test_create_seller_unknown_touchpoint(tables):
    event = make_event("POST", "/sellers", {
        "name": "Test Seller",
        "village": "Rampur",
        "state": "Rajasthan",
        "seller_language": "hi",
        "touchpoint_id": str(uuid.uuid4()),
    })
    status, body = decode(h_sellers.lambda_handler(event, None))

    assert status == 400
    assert body["error"]["code"] == "BAD_REQUEST"
    assert "does not exist" in body["error"]["message"]


def test_create_seller_malformed_json(tables):
    event = {
        "httpMethod": "POST",
        "path": "/sellers",
        "pathParameters": None,
        "headers": {},
        "body": "{ not json",
    }
    status, body = decode(h_sellers.lambda_handler(event, None))

    assert status == 400
    assert body["error"]["code"] == "BAD_REQUEST"
