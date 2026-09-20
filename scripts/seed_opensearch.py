"""Seed script for the matching service demo data.

Loads data/seed/opensearch_seed.json through the *real* running
POST /index/listing endpoint (never writes to OpenSearch directly) so the
seed path exercises exactly the same code as production indexing, per task
spec Section 5.3.

Usage (from anywhere, with the matching service already running):
    python scripts/seed_opensearch.py

Then, to sanity-check the demo queries before showing judges:
    python scripts/seed_opensearch.py --try-queries
"""
import argparse
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "seed" / "opensearch_seed.json"
MATCHING_SERVICE_URL = os.getenv("MATCHING_SERVICE_URL")


def load_seed_data() -> dict:
    with open(SEED_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def wait_for_health(url: str, timeout_seconds: int = 30) -> None:
    import time

    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            resp = requests.get(f"{url}/health", timeout=2)
            if resp.status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(1)
    print(f"Matching service at {url} never became healthy. Is it running?", file=sys.stderr)
    sys.exit(1)


def seed_listings(url: str, listings: list) -> None:
    print(f"Indexing {len(listings)} sample listings through {url}/index/listing ...")
    failures = 0
    for entry in listings:
        resp = requests.post(f"{url}/index/listing", json=entry, timeout=30)
        title = entry["listing"]["listing_title"]
        if resp.status_code == 200:
            print(f"  [ok] {title}")
        else:
            failures += 1
            print(f"  [FAILED {resp.status_code}] {title} -> {resp.text}", file=sys.stderr)
    if failures:
        raise SystemExit(f"Seed failed: {failures} listing(s) were not indexed")


def try_queries(url: str, queries: list) -> None:
    print("\nRunning demo buyer queries against POST /match:")
    for query_text in queries:
        resp = requests.post(f"{url}/match", json={"query_text": query_text}, timeout=30)
        print(f"\n  Query: \"{query_text}\"")
        if resp.status_code != 200:
            print(f"    [FAILED {resp.status_code}] {resp.text}")
            continue
        matches = resp.json().get("matches", [])
        if not matches:
            print("    (no matches yet — did the seed step run first?)")
        for m in matches[:3]:
            print(f"    -> {m['listing_title']}  (score={m['score']:.3f})")


def main() -> None:
    if not MATCHING_SERVICE_URL:
        print("MATCHING_SERVICE_URL is not set. Add it to the root .env before seeding.", file=sys.stderr)
        raise SystemExit(2)

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--try-queries",
        action="store_true",
        help="After seeding, run the sample demo_queries against /match and print top matches.",
    )
    args = parser.parse_args()

    data = load_seed_data()
    wait_for_health(MATCHING_SERVICE_URL)
    seed_listings(MATCHING_SERVICE_URL, data["listings"])

    if args.try_queries:
        try_queries(MATCHING_SERVICE_URL, data.get("demo_queries", []))


if __name__ == "__main__":
    main()
