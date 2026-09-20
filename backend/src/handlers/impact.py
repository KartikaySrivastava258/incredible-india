"""
GET /impact — aggregated dashboard numbers.

Response (BRAIN.md Section G):
    {
      "villages_onboarded": int,
      "sellers_earning": int,
      "total_community_funds": number,
      "opt_in_rate": float   # 0.0 – 1.0
    }

Definition notes:
  - villages_onboarded: distinct villages across touchpoints that have at
    least one seller registered against them.
  - sellers_earning: distinct sellers with at least one LedgerEntry.
  - total_community_funds: sum of contribution_amount across all ledger
    entries (INR).
  - opt_in_rate: opted-in sellers / total sellers.
"""

from __future__ import annotations

import logging

from db import dynamodb
from utils.errors import ok, server_error

log = logging.getLogger("kalaa.handlers.impact")


def lambda_handler(event, context):
    try:
        sellers = dynamodb.scan_all(dynamodb.TABLE_SELLERS)
        touchpoints = dynamodb.scan_all(dynamodb.TABLE_TOUCHPOINTS)
        contributions = dynamodb.scan_all(dynamodb.TABLE_CONTRIBUTIONS)
        ledger_entries = dynamodb.scan_all(dynamodb.TABLE_LEDGER)
    except Exception:  # noqa: BLE001
        log.exception("failed to scan tables for impact aggregates")
        return server_error("failed to compute impact")

    # --- villages onboarded ---------------------------------------------
    tp_by_id = {t["touchpoint_id"]: t for t in touchpoints if t.get("touchpoint_id")}
    villages_with_sellers = set()
    for s in sellers:
        tp = tp_by_id.get(s.get("touchpoint_id"))
        if tp and tp.get("village"):
            villages_with_sellers.add(tp["village"])
    villages_onboarded = len(villages_with_sellers)

    # --- sellers earning -------------------------------------------------
    sellers_earning = len({e.get("seller_id") for e in ledger_entries if e.get("seller_id")})

    # --- total community funds -------------------------------------------
    total_community_funds = round(
        sum(float(e.get("contribution_amount") or 0) for e in ledger_entries), 2
    )

    # --- opt-in rate -----------------------------------------------------
    total_sellers = len(sellers)
    opted_in_seller_ids = {
        c.get("seller_id") for c in contributions if c.get("opted_in") is True
    }
    opt_in_rate = (len(opted_in_seller_ids) / total_sellers) if total_sellers else 0.0

    return ok({
        "villages_onboarded": villages_onboarded,
        "sellers_earning": sellers_earning,
        "total_community_funds": total_community_funds,
        "opt_in_rate": round(opt_in_rate, 4),
    })
