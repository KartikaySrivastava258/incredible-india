# Kalaa Setu — API Contracts (mirror of BRAIN.md Section G)

> This file mirrors BRAIN.md Section G exactly. If any contract changes, update
> BRAIN.md and this file together, then notify all four developers.

Base URL: `API_BASE_URL` (e.g. `http://localhost:3000`)
All request/response bodies are JSON.

All errors follow:

    { "error": { "code": "string", "message": "string" } }

Error codes used:
- 400 invalid/missing fields, unknown FK, unapproved listing, non-positive amount
- 403 Cedar denied
- 404 unknown id
- 502 upstream (AI / matching / LLM / OpenSearch) unavailable

## Backend-owned endpoints

| Method | Endpoint | Purpose | Owning module |
|---|---|---|---|
| POST | /sellers | Register a seller | backend |
| POST | /touchpoints | Register a school/CSC | backend |
| POST | /products | Record a seller's raw product description | backend |
| POST | /onboarding/message | One turn of the seller conversation (proxies AI service) | backend -> ai |
| POST | /listings/generate | Finalize a structured listing from a conversation (proxies AI service) | backend -> ai |
| POST | /listings/:id/review | Run the lightweight review, set review_status; on approve, index into matching service | backend -> matching |
| GET  | /listings/:id | Fetch one listing | backend |
| POST | /search/match | Buyer search -> ranked matched listings (proxies matching service) | backend -> matching |
| POST | /contributions | Seller sets/updates opt-in + percentage | backend (Cedar-checked) |
| POST | /sales | Simulate a sale; computes fee/net/contribution, writes ledger | backend (Cedar-checked) |
| GET  | /ledger/:seller_id | Seller's own ledger entries | backend (Cedar-checked) |
| GET  | /impact | Aggregated dashboard numbers | backend |

### POST /sellers
Request:
    { "name": "string", "village": "string", "state": "string", "seller_language": "hi", "phone": "string|null", "touchpoint_id": "uuid" }
Response: full Seller object (with generated seller_id, created_at).

### POST /touchpoints
Request:
    { "name": "string", "type": "school|csc", "village": "string", "state": "string", "pickup_address": "string", "admin_user_id": "string|null" }
Response: full CommunityTouchpoint object.

### POST /products
Request:
    { "seller_id": "uuid", "category": "food|textile|toy|handicraft", "raw_description": "string", "seller_language": "hi" }
Response: full Product object.

### POST /onboarding/message
Request:
    { "seller_id": "uuid", "conversation_id": "uuid|null", "message_text": "string" }
Response:
    { "conversation_id": "uuid", "ai_reply_text": "string", "stage": "idea|procedure|business_model|capture|done", "draft_state": {} }

### POST /listings/generate
Request:
    { "seller_id": "uuid", "conversation_id": "uuid" }
Response: a Listing object with review_status = "pending".

### POST /listings/:id/review
Request:
    { "reviewer": "auto|string", "notes": "string|null" }
Response: the updated Listing object.

### GET /listings/:id
Response: a Listing object.

### POST /search/match
Request:
    { "query_text": "string", "buyer_id": "uuid|null" }
Response:
    { "matches": [ { "listing_id": "uuid", "score": 0.0, "listing_title": "string", "noble_cause_note": "string|null" } ] }

### POST /contributions
Request:
    { "seller_id": "uuid", "opted_in": true, "percentage": 5, "touchpoint_id": "uuid", "principal_seller_id": "uuid" }
Response: the upserted Contribution object.
Note: principal_seller_id is the caller's identity; Cedar denies if it does not match seller_id.

### POST /sales
Request:
    { "listing_id": "uuid", "buyer_id": "uuid|null", "sale_amount": 0, "principal_seller_id": "uuid" }
Response: the created LedgerEntry.

### GET /ledger/:seller_id
Query/header: X-Principal-Seller-Id (the caller).
Response: { "entries": [ LedgerEntry, ... ] }

### GET /impact
Response:
    { "villages_onboarded": 0, "sellers_earning": 0, "total_community_funds": 0, "opt_in_rate": 0.0 }

## Services consumed by the backend

### AI service (AI_SERVICE_URL)
| Method | Endpoint | Purpose |
|---|---|---|
| GET  | /health | health check |
| POST | /agent/converse | one onboarding turn |
| POST | /agent/generate-listing | produce structured Listing |
| POST | /agent/noble-cause-note | produce buyer-facing noble-cause note |

### Matching service (MATCHING_SERVICE_URL)
| Method | Endpoint | Purpose |
|---|---|---|
| GET  | /health | health check |
| POST | /index/listing | index an approved listing |
| POST | /match | ranked matches for a buyer query |
