# Kalaa Setu — Backend Integration Notes

**Owner:** Dipanshu
**Module:** `backend/` (plus root-level `docker-compose.yml`, `.env.example`, `policies/`, `scripts/`, `shared/`, `data/seed/`)
**Contract source:** `BRAIN.md` (this file describes what was built against it — BRAIN.md always wins on conflicts)

---

## 1. What I implemented

A complete serverless backend that every other module talks through.

- **API Gateway surface**: all twelve endpoints from BRAIN.md Section G.
- **DynamoDB persistence**: one table per model, partition key = `*_id`.
- **Cedar enforcement**: MUST rules (seller-only-own-contribution, opt-in-required-for-routing, seller-only-own-listing) plus SHOULD rules (touchpoint admin scoping, buyer financial privacy). Policies loaded from `CEDAR_POLICY_PATH` at startup.
- **Ledger + contribution math**: platform fee, seller net, contribution amount, with `contribution_amount` forced to 0 when `opted_in` is false — enforced via Cedar, not just an app-code if.
- **Lightweight review**: rule-based check (required fields, banned words, category-specific flags) that sets `review_status` and, on approval, indexes the listing into the Matching service.
- **Search enrichment**: attaches `noble_cause_note` to each match only if the listing’s seller opted in.
- **Impact aggregates**: villages onboarded, sellers earning, total community funds, opt-in rate.
- **Mocks** for AI and Matching services, swappable via env, schema-accurate so call sites don’t change when the real services arrive.
- **Local infra**: `docker-compose.yml` (LocalStack + OpenSearch), `scripts/start-all.sh`, `scripts/seed_dynamodb.py`, `data/seed/dynamodb_seed.json`.
- **Tests**: 34 pytest tests covering every endpoint, Cedar denials, contribution math, upstream failure modes.

---

## 2. Files I added

### Root level
- `.env.example` — canonical env template, matches BRAIN.md Section H
- `docker-compose.yml` — LocalStack + OpenSearch
- `shared/schemas.json` — machine-readable mirror of BRAIN.md Section F
- `shared/api-contracts.md` — mirror of BRAIN.md Section G
- `scripts/start-all.sh` — brings up infra + AI + Matching + Backend + Frontend in order
- `scripts/seed_dynamodb.py` — creates tables + loads sample data
- `data/seed/dynamodb_seed.json` — sample data (touchpoints, sellers, products, listings, contributions, buyers)

### Policies
- `policies/seller_edit_own_listing.cedar` — MUST: seller can only edit own listing
- `policies/contribution_opt_in.cedar` — MUST: seller can only set own contribution; routing requires opt-in
- `policies/touchpoint_admin_scope.cedar` — SHOULD: touchpoint admin scoped to own village; seller can read own ledger
- `policies/buyer_financial_privacy.cedar` — SHOULD: buyer cannot read seller financial data

### Backend
- `backend/template.yaml` — SAM template, all endpoints wired
- `backend/requirements.txt`
- `backend/pytest.ini` — `pythonpath = src tests`
- `backend/.env.example`
- `backend/README.md`
- `backend/integration-notes.md` (this file)
- `backend/src/app.py` — optional dev HTTP server (no SAM needed)
- `backend/src/utils/errors.py` — `ok`, `bad_request`, `forbidden`, `not_found`, `upstream_error`, `server_error`, `parse_json_body`, `require_fields`
- `backend/src/db/dynamodb.py` — table names, `client()`, `put_item`, `get_item`, `delete_item`, `scan_all`, `scan_filter`, `_to_dynamo`, `_from_dynamo`
- `backend/src/cedar/evaluator.py` — `load_policies`, `is_authorized`, `Request`
- `backend/src/clients/ai_service.py` — HTTP client + `MockAIClient` + `get_ai_client`
- `backend/src/clients/matching_service.py` — HTTP client + `MockMatchingClient` + `get_matching_client`
- `backend/src/handlers/sellers.py`
- `backend/src/handlers/touchpoints.py`
- `backend/src/handlers/products.py`
- `backend/src/handlers/onboarding.py`
- `backend/src/handlers/listings.py` (generate + review + get)
- `backend/src/handlers/search.py`
- `backend/src/handlers/contributions.py`
- `backend/src/handlers/sales.py`
- `backend/src/handlers/ledger.py`
- `backend/src/handlers/impact.py`
- Package markers: `backend/src/{handlers,clients,cedar,db,utils}/__init__.py`
- `backend/tests/__init__.py`
- `backend/tests/conftest.py` — moto fixtures + seed + `make_event`/`decode`
- `backend/tests/test_sellers.py`
- `backend/tests/test_touchpoints.py`
- `backend/tests/test_contributions.py`
- `backend/tests/test_sales.py`
- `backend/tests/test_ledger.py`
- `backend/tests/test_onboarding_proxy.py`
- `backend/tests/test_impact.py`

---

## 3. Files I changed

None outside my own module. This is a clean first drop.

---

## 4. APIs exposed

Every endpoint in BRAIN.md Section G, exactly as specified. See `shared/api-contracts.md` for the full request/response shapes. Summary:

- `POST /sellers`
- `POST /touchpoints`
- `POST /products`
- `POST /onboarding/message`
- `POST /listings/generate`
- `POST /listings/{id}/review`
- `GET  /listings/{id}`
- `POST /search/match`
- `POST /contributions`
- `POST /sales`
- `GET  /ledger/{seller_id}`
- `GET  /impact`

---

## 5. APIs consumed

### AI service (`AI_SERVICE_URL`, default `http://localhost:8001`)
- `GET  /health`
- `POST /agent/converse`
- `POST /agent/generate-listing`
- `POST /agent/noble-cause-note`

### Matching service (`MATCHING_SERVICE_URL`, default `http://localhost:8002`)
- `GET  /health`
- `POST /index/listing`
- `POST /match`

Both clients validate response shapes and raise a service-specific exception on malformed data (→ backend returns 502).

---

## 6. Environment variables

Per BRAIN.md Section H. Variables this backend reads:


The `*_CLIENT_MODE` variables are backend-local and documented in `backend/.env.example`. If the integrator prefers, they can be unset — `auto` is the default and works.

---

## 7. DynamoDB tables created

| Table | Partition key |
|---|---|
| `Sellers` | `seller_id` |
| `CommunityTouchpoints` | `touchpoint_id` |
| `Products` | `product_id` |
| `Listings` | `listing_id` |
| `Buyers` | `buyer_id` |
| `SearchIntents` | `intent_id` |
| `Contributions` | `contribution_id` |
| `LedgerEntries` | `ledger_entry_id` |
| `Reviews` | `review_id` |

`scripts/seed_dynamodb.py` creates them if missing and loads the sample data. It is idempotent.

---

## 8. Cedar policy changes

Every `.cedar` file and what it enforces:

### `policies/seller_edit_own_listing.cedar`
- **permit** `Seller` `editListing` on `Listing` when `principal.seller_id == resource.seller_id`
- **forbid** `Seller` `editListing` on `Listing` when `principal.seller_id != resource.seller_id`

### `policies/contribution_opt_in.cedar`
- **permit** `Seller` `setContribution` on `Contribution` when `principal.seller_id == resource.seller_id`
- **forbid** `Seller` `setContribution` on `Contribution` when `principal.seller_id != resource.seller_id`
- **permit** `Seller` `routeContribution` on `Contribution` when `resource.opted_in == true`
- **forbid** `Seller` `routeContribution` on `Contribution` when `resource.opted_in == false`
- **forbid** `Seller` `routeContribution` on `Contribution` when `resource.percentage < 0 || resource.percentage > 100`

### `policies/touchpoint_admin_scope.cedar`
- **permit** `Seller` `viewLedger` on `LedgerEntry` when `principal.seller_id == resource.seller_id`
- **forbid** `Seller` `viewLedger` on `LedgerEntry` when `principal.seller_id != resource.seller_id`
- **permit** `TouchpointAdmin` `viewSellerData` | `viewListingData` | `viewLedgerData` on `Seller`/`Listing`/`LedgerEntry` when `principal.touchpoint_id == resource.touchpoint_id`
- **forbid** the same actions on the same resources when `principal.touchpoint_id != resource.touchpoint_id`

### `policies/buyer_financial_privacy.cedar`
- **forbid** `Buyer` `viewLedger` | `viewSellerNet` | `viewPlatformFee` | `viewContributionAmount` on `LedgerEntry`
- **forbid** the same actions on `Seller`
- **permit** `Buyer` `viewImpactAggregate` on `ImpactAggregate`

---

## 9. Dependencies

### Python (`backend/requirements.txt`)

### External processes
- LocalStack 3.4.0 (`docker-compose.yml`)
- OpenSearch 2.13.0 (`docker-compose.yml`)

### Not required for backend unit tests
- LocalStack is not needed for `pytest`.
- Ollama is not needed at all — the AI service owns that.

---

## 10. How to run my module

### Tests

### Dev server (no SAM)Serves on `http://localhost:3000`. Requires LocalStack for DynamoDB.

### SAM (canonical)

### Seed
Requires LocalStack running (`docker-compose up -d localstack`).

---

## 11. How to test my module

`pytest -v` should print **34 passed**. Tests use moto, so no LocalStack, no Ollama, no OpenSearch needed. They cover:

- CRUD happy paths + missing fields + unknown FKs
- Cedar denials: cross-seller contribution set, cross-seller ledger read, cross-village admin read
- Ledger math with opted-in (contribution computed) and opted-out (contribution forced to 0)
- AI and Matching upstream failure (mocked down) → 502, no crash
- `/impact` aggregates with and without sales

---

## 12. What another developer should NOT change

- Table names in `backend/src/db/dynamodb.py`. They match `shared/schemas.json`.
- Endpoint paths or request/response shapes in `shared/api-contracts.md`. Change these only by updating `BRAIN.md` first, then the mirror, then code.
- `policies/*.cedar` semantics. If a policy needs to change, propose it, update `BRAIN.md`, then update the file.
- `backend/pytest.ini`. It sets `pythonpath = src tests`, which is required for imports to work.

If you find a bug that requires changing any of the above, write it in `integration-notes.md` (yours) and notify the team before editing.

---

## 13. Known limitations

- **Cedar evaluation is mocked.** `CEDAR_MODE=mock` uses a Python evaluator that mirrors Cedar’s semantics (default deny, forbid always wins). It is not the real Cedar engine. The policies are real `.cedar` files and would load into a real Cedar engine without modification.
- **The Cedar parser in `cedar/evaluator.py` is intentionally limited.** It reads effect, principal type, action list, resource type, and the `when` clause. It supports the subset of conditions our policies use. It does NOT support multi-line `action in [...]` — keep those on one line (I did).
- **DynamoDB access uses `scan` and `scan_filter`** for non-key queries (e.g., finding a seller’s contribution record, listing ledger entries). Fine for hackathon-scale data. Not for production. A GSI on `seller_id` would be the production fix.
- **`app.py` is dev-only.** It uses Python stdlib `http.server`, single-process-ish, no auth, no rate limiting. The canonical run mode is `sam local start-api`.
- **`AI_CLIENT_MODE=auto` swallows the first /health failure.** If you want a hard failure when the AI service is down, set `AI_CLIENT_MODE=http`.
- **`S3` is declared in `docker-compose.yml` but the backend does not use it yet.** Photos/audio (voice stretch) would use it later.

---

## 14. Exact steps for integrating this module

1. **Extract** `dipanshu.zip` into the repo root as-is. It produces:

2. **Reconcile shared files** against the other three ZIPs. If another dev’s copy of `shared/schemas.json`, `shared/api-contracts.md`, `.env.example`, or `docker-compose.yml` differs, compare against `BRAIN.md` Section F/G/H and keep the version that matches. Do not average.

3. **Merge `docker-compose.yml`.** Saloni Sharma’s ZIP may add an OpenSearch service block. Add it only if it differs from what is already present; the OpenSearch block in this drop is already the canonical one.

4. **Create the root `.env`.**

5. **Install backend deps.**

6. **Run backend tests.**
Expect 34 passed.

7. **Bring up infra.**

8. **Bring up AI and Matching services** (from their own modules, per their READMEs).

9. **Start the backend.**
or, if SAM isn’t set up:

10. **Seed.**

11. **Bring up the frontend** per Kartikay’s README, pointed at `API_BASE_URL=http://localhost:3000`.

12. **Run the End-to-End Acceptance Test** from `BRAIN.md`. All 20 rows must pass.

---

## 15. Contact / escalation

If a fix requires changing an endpoint contract, a table name, or a Cedar policy semantic, escalate before doing it. The rules are in `BRAIN.md` Section I (“Integration Rules — DO NOT BREAK”).
