#!/usr/bin/env python3
"""
Kalaa Setu — seed DynamoDB (LocalStack) with sample data.

Creates the nine tables defined in shared/schemas.json, then loads:
  - 2 community touchpoints (school + csc)
  - 2 sellers
  - 2 products
  - 2 listings (one approved, one pending)
  - 2 contributions (one opted in, one not)
  - 1 buyer
  - 1 impact-friendly ledger entry (optional, commented)

Safe to re-run: tables are created only if missing, items are upserted.
"""

import json
import os
import sys
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT", "http://localhost:4566")
REGION = os.environ.get("AWS_REGION", "us-east-1")
SEED_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "seed", "dynamodb_seed.json")

TABLES = {
    "Sellers":              "seller_id",
    "CommunityTouchpoints": "touchpoint_id",
    "Products":             "product_id",
    "Listings":             "listing_id",
    "Buyers":               "buyer_id",
    "SearchIntents":        "intent_id",
    "Contributions":        "contribution_id",
    "LedgerEntries":        "ledger_entry_id",
    "Reviews":              "review_id",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def client():
    return boto3.client(
        "dynamodb",
        endpoint_url=ENDPOINT,
        region_name=REGION,
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )


def resource():
    return boto3.resource(
        "dynamodb",
        endpoint_url=ENDPOINT,
        region_name=REGION,
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )


def create_tables(ddb):
    existing = set(ddb.list_tables().get("TableNames", []))
    for name, pk in TABLES.items():
        if name in existing:
            print(f"  table {name} exists")
            continue
        ddb.create_table(
            TableName=name,
            KeySchema=[{"AttributeName": pk, "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": pk, "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        print(f"  created table {name} (pk={pk})")
        ddb.get_waiter("table_exists").wait(TableName=name)


def put(ddb, table, item):
    ddb.put_item(TableName=table, Item=item)


def seed(ddb, data):
    for tp in data.get("touchpoints", []):
        put(ddb, "CommunityTouchpoints", tp)
    for seller in data.get("sellers", []):
        put(ddb, "Sellers", seller)
    for prod in data.get("products", []):
        put(ddb, "Products", prod)
    for lst in data.get("listings", []):
        put(ddb, "Listings", lst)
    for c in data.get("contributions", []):
        put(ddb, "Contributions", c)
    for b in data.get("buyers", []):
        put(ddb, "Buyers", b)
    for le in data.get("ledger_entries", []):
        put(ddb, "LedgerEntries", le)


def main():
    print(f"Seeding DynamoDB at {ENDPOINT} ...")
    ddb = client()
    create_tables(ddb)

    with open(SEED_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    seed(ddb, data)
    print("Seed complete.")


if __name__ == "__main__":
    try:
        main()
    except ClientError as e:
        print(f"DynamoDB error: {e}", file=sys.stderr)
        sys.exit(1)
