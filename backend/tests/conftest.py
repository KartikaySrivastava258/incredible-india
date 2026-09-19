"""
Shared pytest fixtures for Kalaa Setu backend tests.

Uses moto to mock DynamoDB in-memory. Every test gets a fresh set of tables
and a freshly seeded dataset, so tests are isolated and order-independent.

Important: we deliberately do NOT set DYNAMODB_ENDPOINT here, so boto3 talks
to moto's in-process mock rather than to a real LocalStack instance.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

import pytest
from moto import mock_aws

# Make `handlers`, `db`, `clients`, `cedar`, `utils` importable.
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(HERE, "..", "src"))
sys.path.insert(0, SRC)

# Credentials and region only. NO endpoint override — moto handles that.
os.environ.pop("DYNAMODB_ENDPOINT", None)
os.environ.pop("S3_ENDPOINT", None)
os.environ.setdefault("AWS_REGION", "us-east-1")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
os.environ.setdefault(
    "CEDAR_POLICY_PATH",
    os.path.abspath(os.path.join(HERE, "..", "..", "policies")),
)
os.environ.setdefault("CEDAR_MODE", "mock")
os.environ.setdefault("AI_CLIENT_MODE", "mock")
os.environ.setdefault("MATCHING_CLIENT_MODE", "mock")


# ---------------------------------------------------------------------------
# Test data constants
# ---------------------------------------------------------------------------

TP_SCHOOL_ID = "11111111-1111-4111-8111-111111111111"
TP_CSC_ID    = "22222222-2222-4222-8222-222222222222"
SELLER_MEERA_ID  = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
SELLER_RAMESH_ID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
PRODUCT_DIYA_ID   = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
PRODUCT_PICKLE_ID = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
LISTING_DIYA_ID   = "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"
LISTING_PICKLE_ID = "ffffffff-ffff-4fff-8fff-ffffffffffff"
CONTRIB_MEERA_ID  = "99999999-9999-4999-8999-999999999991"
CONTRIB_RAMESH_ID = "99999999-9999-4999-8999-999999999992"
BUYER_ID = "77777777-7777-4777-8777-777777777777"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# moto-backed DynamoDB
# ---------------------------------------------------------------------------

@pytest.fixture()
def aws_credentials(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "test")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "test")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    # Ensure the endpoint override is absent during the test as well.
    monkeypatch.delenv("DYNAMODB_ENDPOINT", raising=False)
    monkeypatch.delenv("S3_ENDPOINT", raising=False)


@pytest.fixture()
def dynamodb_mock(aws_credentials):
    """
    Start moto, then force db.dynamodb to build a fresh boto3 client that
    moto intercepts (no custom endpoint URL).
    """
    with mock_aws():
        import db.dynamodb as dbmod
        # Clear any cached client built before moto was active, and remove the
        # endpoint env var so boto3 talks to moto's in-process mock.
        os.environ.pop("DYNAMODB_ENDPOINT", None)
        dbmod._CLIENT = None
        yield dbmod
        dbmod._CLIENT = None


@pytest.fixture()
def tables(dynamodb_mock):
    ddb = dynamodb_mock.client()
    for name, pk in dynamodb_mock.PK.items():
        ddb.create_table(
            TableName=name,
            KeySchema=[{"AttributeName": pk, "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": pk, "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
    return dynamodb_mock


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------

@pytest.fixture()
def seeded(tables):
    db = tables

    db.put_item(db.TABLE_TOUCHPOINTS, {
        "touchpoint_id": TP_SCHOOL_ID,
        "name": "Govt Primary School, Rampur",
        "type": "school",
        "village": "Rampur",
        "state": "Rajasthan",
        "pickup_address": "Govt Primary School, Main Road, Rampur, Rajasthan 313001",
        "admin_user_id": "admin-rampur-01",
    })
    db.put_item(db.TABLE_TOUCHPOINTS, {
        "touchpoint_id": TP_CSC_ID,
        "name": "CSC Center, Devgaon",
        "type": "csc",
        "village": "Devgaon",
        "state": "Madhya Pradesh",
        "pickup_address": "CSC Center, Bus Stand Road, Devgaon, Madhya Pradesh 451001",
        "admin_user_id": "admin-devgaon-01",
    })

    db.put_item(db.TABLE_SELLERS, {
        "seller_id": SELLER_MEERA_ID,
        "name": "Meera Devi",
        "village": "Rampur",
        "state": "Rajasthan",
        "seller_language": "hi",
        "phone": "+919999999901",
        "touchpoint_id": TP_SCHOOL_ID,
        "created_at": now_iso(),
    })
    db.put_item(db.TABLE_SELLERS, {
        "seller_id": SELLER_RAMESH_ID,
        "name": "Ramesh Kumar",
        "village": "Devgaon",
        "state": "Madhya Pradesh",
        "seller_language": "hi",
        "phone": "+919999999902",
        "touchpoint_id": TP_CSC_ID,
        "created_at": now_iso(),
    })

    db.put_item(db.TABLE_PRODUCTS, {
        "product_id": PRODUCT_DIYA_ID,
        "seller_id": SELLER_MEERA_ID,
        "category": "handicraft",
        "raw_description": "Haath se bani mitti ki diya.",
        "seller_language": "hi",
        "created_at": now_iso(),
    })
    db.put_item(db.TABLE_PRODUCTS, {
        "product_id": PRODUCT_PICKLE_ID,
        "seller_id": SELLER_RAMESH_ID,
        "category": "food",
        "raw_description": "Ghar ka bana hua aam ka achaar.",
        "seller_language": "hi",
        "created_at": now_iso(),
    })

    db.put_item(db.TABLE_LISTINGS, {
        "listing_id": LISTING_DIYA_ID,
        "product_id": PRODUCT_DIYA_ID,
        "category": "handicraft",
        "listing_title": "Handcrafted Terracotta Diya Set",
        "description_en": "Handcrafted diyas made by a rural artisan.",
        "price_suggestion": 299,
        "photo_guidance": ["shoot in daylight"],
        "story": "Supports a rural artisan family.",
        "compliance_flags": [],
        "review_status": "approved",
        "created_at": now_iso(),
    })
    db.put_item(db.TABLE_LISTINGS, {
        "listing_id": LISTING_PICKLE_ID,
        "product_id": PRODUCT_PICKLE_ID,
        "category": "food",
        "listing_title": "Homemade Mango Pickle",
        "description_en": "Sun-dried mango pickle.",
        "price_suggestion": 349,
        "photo_guidance": ["shoot in daylight"],
        "story": "Supports a rural food producer.",
        "compliance_flags": ["food_fssai_recommended"],
        "review_status": "approved",
        "created_at": now_iso(),
    })

    db.put_item(db.TABLE_CONTRIBUTIONS, {
        "contribution_id": CONTRIB_MEERA_ID,
        "seller_id": SELLER_MEERA_ID,
        "opted_in": True,
        "percentage": 5,
        "touchpoint_id": TP_SCHOOL_ID,
        "updated_at": now_iso(),
    })
    db.put_item(db.TABLE_CONTRIBUTIONS, {
        "contribution_id": CONTRIB_RAMESH_ID,
        "seller_id": SELLER_RAMESH_ID,
        "opted_in": False,
        "percentage": 0,
        "touchpoint_id": TP_CSC_ID,
        "updated_at": now_iso(),
    })

    db.put_item(db.TABLE_BUYERS, {
        "buyer_id": BUYER_ID,
        "buyer_language": "en",
    })

    return db


# ---------------------------------------------------------------------------
# Lambda event helper
# ---------------------------------------------------------------------------

def make_event(method: str, path: str, body: dict | None = None,
               path_params: dict | None = None, headers: dict | None = None) -> dict:
    return {
        "httpMethod": method,
        "path": path,
        "pathParameters": path_params,
        "headers": {k.lower(): v for k, v in (headers or {}).items()},
        "body": json.dumps(body) if body is not None else None,
    }


@pytest.fixture()
def event_factory():
    return make_event


def decode(response: dict):
    return response["statusCode"], json.loads(response["body"])


# ---------------------------------------------------------------------------
# Cedar policies — load once per test session
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True, scope="session")
def _load_cedar_policies():
    """Load Cedar policies before any test runs."""
    from cedar import evaluator
    evaluator.load_policies(os.environ["CEDAR_POLICY_PATH"])
    yield
