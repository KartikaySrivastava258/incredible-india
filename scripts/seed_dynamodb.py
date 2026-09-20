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

Use:
    python seed_dynamodb.py

For a clean local demo reset:
    python seed_dynamodb.py --reset

The reset operation is deliberately restricted to local/LocalStack
DynamoDB endpoints.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.types import TypeSerializer
from botocore.exceptions import ClientError


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ENDPOINT = os.environ.get(
    "DYNAMODB_ENDPOINT",
    "http://localhost:4566",
)

REGION = os.environ.get(
    "AWS_REGION",
    "us-east-1",
)

SEED_FILE = os.path.join(
    os.path.dirname(__file__),
    "..",
    "data",
    "seed",
    "dynamodb_seed.json",
)

TABLES = {
    "Sellers": "seller_id",
    "CommunityTouchpoints": "touchpoint_id",
    "Products": "product_id",
    "Listings": "listing_id",
    "Buyers": "buyer_id",
    "SearchIntents": "intent_id",
    "Contributions": "contribution_id",
    "LedgerEntries": "ledger_entry_id",
    "Reviews": "review_id",
}

serializer = TypeSerializer()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def now_iso() -> str:
    """Return current UTC time in ISO format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def client():
    """Create a DynamoDB client connected to LocalStack."""
    return boto3.client(
        "dynamodb",
        endpoint_url=ENDPOINT,
        region_name=REGION,
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )


def resource():
    """Create a DynamoDB resource connected to LocalStack."""
    return boto3.resource(
        "dynamodb",
        endpoint_url=ENDPOINT,
        region_name=REGION,
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )


def is_local_endpoint(endpoint: str) -> bool:
    """
    Allow destructive reset only against local/LocalStack endpoints.
    """
    allowed_hosts = {
        "localhost",
        "127.0.0.1",
        "::1",
        "localstack",
        "kalaa-localstack",
    }

    try:
        from urllib.parse import urlparse

        parsed = urlparse(endpoint)
        hostname = parsed.hostname

        return hostname in allowed_hosts

    except Exception:
        return False


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

def ensure_table(ddb, table_name: str, partition_key: str):
    """Create a table if it doesn't already exist."""

    try:
        ddb.describe_table(TableName=table_name)
        return

    except ddb.exceptions.ResourceNotFoundException:
        pass

    print(
        f"  creating table {table_name} "
        f"(pk={partition_key})"
    )

    ddb.create_table(
        TableName=table_name,
        KeySchema=[
            {
                "AttributeName": partition_key,
                "KeyType": "HASH",
            }
        ],
        AttributeDefinitions=[
            {
                "AttributeName": partition_key,
                "AttributeType": "S",
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    waiter = ddb.get_waiter("table_exists")
    waiter.wait(TableName=table_name)


def ensure_tables(ddb):
    """Ensure all Kalaa Setu demo tables exist."""

    for table_name, partition_key in TABLES.items():
        ensure_table(
            ddb,
            table_name,
            partition_key,
        )


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------

def reset_table(ddb, table_name: str, partition_key: str):
    """
    Delete every item from a local DynamoDB table.
    """

    try:
        response = ddb.scan(
            TableName=table_name,
            ProjectionExpression=partition_key,
        )

        items = response.get("Items", [])

        while response.get("LastEvaluatedKey"):
            response = ddb.scan(
                TableName=table_name,
                ProjectionExpression=partition_key,
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )

            items.extend(
                response.get("Items", [])
            )

        if not items:
            print(
                f"  cleared {table_name}: 0 items"
            )
            return

        with ddb.batch_writer(TableName=table_name) as batch:
            for item in items:
                batch.delete_item(
                    Key={
                        partition_key: item[partition_key]
                    }
                )

        print(
            f"  cleared {table_name}: "
            f"{len(items)} items"
        )

    except ddb.exceptions.ResourceNotFoundException:
        print(
            f"  {table_name}: table does not exist"
        )


def reset_tables(ddb):
    """Clear all known Kalaa Setu demo tables."""

    if not is_local_endpoint(ENDPOINT):
        raise RuntimeError(
            "Refusing destructive reset because "
            f"DYNAMODB_ENDPOINT is not local: {ENDPOINT}"
        )

    print(
        "Reset requested: clearing local demo data first ..."
    )

    for table_name, partition_key in TABLES.items():
        reset_table(
            ddb,
            table_name,
            partition_key,
        )


# ---------------------------------------------------------------------------
# DynamoDB write
# ---------------------------------------------------------------------------

def put(ddb, table: str, item: dict):
    """
    Write a normal Python dictionary to DynamoDB.

    boto3's low-level DynamoDB client requires DynamoDB
    AttributeValue objects, so TypeSerializer is used here.
    """

    encoded_item = {
        key: serializer.serialize(value)
        for key, value in item.items()
    }

    ddb.put_item(
        TableName=table,
        Item=encoded_item,
    )


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------

def seed(ddb, data):
    """Insert seed data into DynamoDB."""

    touchpoints = data.get(
        "community_touchpoints",
        data.get("touchpoints", []),
    )

    sellers = data.get(
        "sellers",
        [],
    )

    products = data.get(
        "products",
        [],
    )

    listings = data.get(
        "listings",
        [],
    )

    buyers = data.get(
        "buyers",
        [],
    )

    search_intents = data.get(
        "search_intents",
        [],
    )

    contributions = data.get(
        "contributions",
        [],
    )

    ledger_entries = data.get(
        "ledger_entries",
        [],
    )

    reviews = data.get(
        "reviews",
        [],
    )

    for item in touchpoints:
        put(
            ddb,
            "CommunityTouchpoints",
            item,
        )

    for item in sellers:
        put(
            ddb,
            "Sellers",
            item,
        )

    for item in products:
        put(
            ddb,
            "Products",
            item,
        )

    for item in listings:
        put(
            ddb,
            "Listings",
            item,
        )

    for item in buyers:
        put(
            ddb,
            "Buyers",
            item,
        )

    for item in search_intents:
        put(
            ddb,
            "SearchIntents",
            item,
        )

    for item in contributions:
        put(
            ddb,
            "Contributions",
            item,
        )

    for item in ledger_entries:
        put(
            ddb,
            "LedgerEntries",
            item,
        )

    for item in reviews:
        put(
            ddb,
            "Reviews",
            item,
        )

    print()
    print("DynamoDB seed completed successfully.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Seed Kalaa Setu DynamoDB demo data."
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear existing local demo data before seeding.",
    )

    args = parser.parse_args()

    print(
        f"Seeding DynamoDB at {ENDPOINT} ..."
    )

    ddb = client()

    ensure_tables(ddb)

    if args.reset:
        reset_tables(ddb)

    if not os.path.exists(SEED_FILE):
        print(
            f"ERROR: seed file not found: {SEED_FILE}",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        with open(
            SEED_FILE,
            "r",
            encoding="utf-8",
        ) as f:
            data = json.load(f)

    except json.JSONDecodeError as exc:
        print(
            f"ERROR: invalid JSON in seed file: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)

    except OSError as exc:
        print(
            f"ERROR: unable to read seed file: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        seed(
            ddb,
            data,
        )

    except ClientError as exc:
        print(
            "ERROR: DynamoDB operation failed:",
            file=sys.stderr,
        )
        print(
            exc,
            file=sys.stderr,
        )
        sys.exit(1)

    except Exception as exc:
        print(
            "ERROR: seed failed:",
            file=sys.stderr,
        )
        print(
            exc,
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
