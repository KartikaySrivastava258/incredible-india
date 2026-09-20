"""
Kalaa Setu — DynamoDB access layer.

Single source of truth for table names and low-level boto3 usage.
Handlers should call these helpers, never construct their own boto3 clients.

Uses DYNAMODB_ENDPOINT (defaults to LocalStack at http://localhost:4566).
"""

from __future__ import annotations

import os
from typing import Any, Iterable

import boto3
from botocore.exceptions import ClientError

# Canonical table names — must match shared/schemas.json
TABLE_SELLERS = "Sellers"
TABLE_TOUCHPOINTS = "CommunityTouchpoints"
TABLE_PRODUCTS = "Products"
TABLE_LISTINGS = "Listings"
TABLE_BUYERS = "Buyers"
TABLE_SEARCH_INTENTS = "SearchIntents"
TABLE_CONTRIBUTIONS = "Contributions"
TABLE_LEDGER = "LedgerEntries"
TABLE_REVIEWS = "Reviews"

# Partition keys — must match shared/schemas.json
PK = {
    TABLE_SELLERS: "seller_id",
    TABLE_TOUCHPOINTS: "touchpoint_id",
    TABLE_PRODUCTS: "product_id",
    TABLE_LISTINGS: "listing_id",
    TABLE_BUYERS: "buyer_id",
    TABLE_SEARCH_INTENTS: "intent_id",
    TABLE_CONTRIBUTIONS: "contribution_id",
    TABLE_LEDGER: "ledger_entry_id",
    TABLE_REVIEWS: "review_id",
}

_CLIENT = None


def _endpoint() -> str | None:
    """Return the DynamoDB endpoint, or None to use the real AWS endpoint.

    In tests, DYNAMODB_ENDPOINT is unset so boto3 talks to moto's in-process
    mock. In local dev, it is set to LocalStack (http://localhost:4566).
    """
    return os.environ.get("DYNAMODB_ENDPOINT") or None


def _region() -> str:
    return os.environ.get("AWS_REGION", "us-east-1")


def client():
    """Lazily construct and cache the DynamoDB client."""
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = boto3.client(
            "dynamodb",
            endpoint_url=_endpoint(),
            region_name=_region(),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "test"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "test"),
        )
    return _CLIENT


def put_item(table: str, item: dict) -> None:
    """Write (upsert) one item. Item keys must already match the table schema."""
    client().put_item(TableName=table, Item=_to_dynamo(item))


def get_item(table: str, key_name: str, key_value: str) -> dict | None:
    """Read one item by primary key. Returns None if not found."""
    try:
        resp = client().get_item(
            TableName=table,
            Key={key_name: {"S": key_value}},
        )
    except ClientError:
        return None
    raw = resp.get("Item")
    return _from_dynamo(raw) if raw else None


def delete_item(table: str, key_name: str, key_value: str) -> None:
    client().delete_item(TableName=table, Key={key_name: {"S": key_value}})


def scan_all(table: str) -> list[dict]:
    """
    Scan the whole table. Acceptable for hackathon-scale data.
    Never use at production scale.
    """
    items: list[dict] = []
    last_key = None
    while True:
        kwargs = {"TableName": table}
        if last_key:
            kwargs["ExclusiveStartKey"] = last_key
        resp = client().scan(**kwargs)
        items.extend(_from_dynamo(i) for i in resp.get("Items", []))
        last_key = resp.get("LastEvaluatedKey")
        if not last_key:
            break
    return items


def scan_filter(table: str, field: str, value: Any) -> list[dict]:
    """
    Scan with a simple equality filter on a non-key attribute.

    Uses the low-level client API, which expects a string FilterExpression
    and a raw ExpressionAttributeValues map. Acceptable at hackathon scale;
    not for production.
    """
    items: list[dict] = []
    last_key = None

    filter_expr = "#f = :v"
    expr_names = {"#f": field}
    expr_values = {":v": _to_dynamo(value)}

    while True:
        kwargs = {
            "TableName": table,
            "FilterExpression": filter_expr,
            "ExpressionAttributeNames": expr_names,
            "ExpressionAttributeValues": expr_values,
        }
        if last_key:
            kwargs["ExclusiveStartKey"] = last_key
        resp = client().scan(**kwargs)
        items.extend(_from_dynamo(i) for i in resp.get("Items", []))
        last_key = resp.get("LastEvaluatedKey")
        if not last_key:
            break
    return items


def batch_put(table: str, items: Iterable[dict]) -> None:
    """Put multiple items one by one. Fine for seed-size batches."""
    for item in items:
        put_item(table, item)


# ---------------------------------------------------------------------------
# DynamoDB type marshalling.
# The low-level client expects {"S": "value"}, {"N": "1"}, {"BOOL": true}, etc.
# These two helpers convert between plain Python dicts and that shape.
# ---------------------------------------------------------------------------

def _to_dynamo(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _to_dynamo(v) for k, v in value.items()}
    if isinstance(value, list):
        return {"L": [_to_dynamo(v) for v in value]}
    if isinstance(value, bool):
        return {"BOOL": value}
    if isinstance(value, (int, float)):
        return {"N": str(value)}
    if value is None:
        return {"NULL": True}
    return {"S": str(value)}


def _from_dynamo(value: Any) -> Any:
    if not isinstance(value, dict):
        return value
    if "S" in value:
        return value["S"]
    if "N" in value:
        n = value["N"]
        return float(n) if "." in n else int(n)
    if "BOOL" in value:
        return value["BOOL"]
    if "NULL" in value:
        return None
    if "L" in value:
        return [_from_dynamo(v) for v in value["L"]]
    # Plain map (nested attribute) — recurse on each key
    return {k: _from_dynamo(v) for k, v in value.items()}
