# Kalaa Setu — Backend

Serverless backend (SAM + LocalStack) for Kalaa Setu. This module owns:

- the API Gateway surface (all endpoints in `BRAIN.md` Section G),
- DynamoDB persistence for every model in Section F,
- Cedar policy enforcement for access control,
- contribution + ledger math,
- the shared local infrastructure (`docker-compose.yml`, `policies/`, `scripts/`).

The frontend never calls the AI or Matching services directly. It calls this
backend only. This backend is the only module that talks to DynamoDB and the
only module that evaluates Cedar policies.

---

## 1. Layout

    backend/
    ├── template.yaml          SAM template
    ├── requirements.txt
    ├── pytest.ini             sets pythonpath = src tests
    ├── README.md
    ├── .env.example
    ├── integration-notes.md
    ├── src/
    │   ├── app.py             optional local HTTP server (no SAM needed)
    │   ├── handlers/          one module per endpoint group
    │   ├── clients/           AI service + Matching service HTTP clients + mocks
    │   ├── cedar/             policy loader + evaluator
    │   ├── db/                DynamoDB access layer
    │   └── utils/             error helpers, JSON body parsing
    └── tests/                 pytest suite (34 tests)

---

## 2. Prerequisites

- Python 3.11+
- Docker (for LocalStack + OpenSearch, defined at repo root)
- AWS SAM CLI
- LocalStack (started by the root `docker-compose.yml`)

Everything runs locally. No AWS account, no paid services, no external LLM.

---

## 3. Environment variables

Copy the root `.env.example` and edit only if needed:

    cp ../.env.example ../.env
    cd backend
    cp .env.example .env

Every variable is documented in `BRAIN.md` Section H. Do not invent new
variable names — add them to `BRAIN.md` and `.env.example` if a module
genuinely needs one.

---

## 4. Setup

    cd backend
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

---

## 5. Run the tests

    pytest -v

Expected output: **34 passed**.

Tests use `moto` to mock DynamoDB in-memory. No LocalStack is required for
the unit test suite. Cedar policies are loaded from `../policies/`.

For coverage:

    pytest --cov=src --cov-report=term-missing

---

## 6. Run the backend locally

There are two ways. Use whichever fits your loop.

### 6a. Without SAM — quick dev server

    cd backend
    source .venv/bin/activate
    PYTHONPATH=src python src/app.py

Serves every endpoint on `http://localhost:3000`. Uses only the Python
standard library. Good for curl-based poking and for the seed script.

Requires DynamoDB to be reachable — start LocalStack first:

    cd .. && docker-compose up -d localstack

### 6b. With SAM — canonical

    cd backend
    source .venv/bin/activate
    sam local start-api --env-vars ../.env.example

Same endpoints, same contracts. Also requires LocalStack for DynamoDB.

---

## 7. Start LocalStack + OpenSearch

From the repo root:

    docker-compose up -d

Verify:

    curl -s http://localhost:4566/_localstack/health | head -c 200
    curl -s http://localhost:9200/_cluster/health

---

## 8. Seed DynamoDB

From the repo root:

    python3 scripts/seed_dynamodb.py

Creates the nine DynamoDB tables if missing, then loads sample data:

- 2 touchpoints (school in Rampur, CSC in Devgaon)
- 2 sellers (Meera opted in, Ramesh not)
- 2 products (handicraft diya, food pickle)
- 2 listings (both approved so they can be sold)
- 2 contributions
- 1 buyer

Safe to re-run.

---

## 9. Endpoints

All requests and responses are JSON. All errors follow:

    { "error": { "code": "string", "message": "string" } }

| Method | Endpoint | Notes |
|---|---|---|
| POST | `/sellers` | register a seller |
| POST | `/touchpoints` | register a school/CSC |
| POST | `/products` | record a raw product description |
| POST | `/onboarding/message` | one turn of the seller conversation (proxies AI service) |
| POST | `/listings/generate` | structured listing draft (proxies AI service) |
| POST | `/listings/{id}/review` | rule-based review, index on approval |
| GET  | `/listings/{id}` | fetch one listing |
| POST | `/search/match` | buyer search (proxies matching service) |
| POST | `/contributions` | Cedar-enforced: seller can only set their own |
| POST | `/sales` | Cedar-enforced: contribution routing requires opt-in |
| GET  | `/ledger/{seller_id}` | Cedar-enforced: seller own, admin own village |
| GET  | `/impact` | aggregate dashboard numbers |

Full request/response shapes: `shared/api-contracts.md`.

---

## 10. Cedar enforcement

Policies live in `../policies/*.cedar` and are loaded from `CEDAR_POLICY_PATH`
at startup. The loader logs every file it loads.

MUST-level:
- a seller can edit only their own listing
- a seller can only set their own contribution record
- a contribution can be routed only if the seller opted in

SHOULD-level:
- a touchpoint admin can only read their own touchpoint's data
- a buyer cannot access private seller financial data

`CEDAR_MODE=mock` uses a Python evaluator that matches Cedar's semantics
(default deny, forbid always wins). `CEDAR_MODE=engine` is reserved for a
real Cedar binary — not wired in this demo.

---

## 11. Mocking strategy

`AI_CLIENT_MODE` and `MATCHING_CLIENT_MODE` control how this backend talks to
those services:

- `auto` (default) — try HTTP `/health`; fall back to mock on failure
- `http` — always use the HTTP client
- `mock` — always use the in-process mock

Mocks return schema-accurate payloads matching the real contracts, so no
calling code has to change when the real services come online.

Tests force `mock` mode so they never depend on the AI or Matching services.

---

## 12. What this module does NOT do

- It does not implement the AI reasoning engine (that is `ai/`).
- It does not implement vector search (that is `matching/`).
- It does not render any UI (that is `frontend/`).
- It does not run Ollama, OpenSearch, or any LLM. Those are separate processes.

---

## 13. Troubleshooting

**`EndpointConnectionError: http://localhost:4566/` in tests**
You have `DYNAMODB_ENDPOINT` set in your shell. Tests force moto. Unset it:

    unset DYNAMODB_ENDPOINT

**`Cedar denied` on a request you think should succeed**
Check `policies/*.cedar` — the `when` block might not match. Enable debug
logging on the `kalaa.cedar` logger to see which policy matched.

**`sam local start-api` complains about the template**
SAM templates use custom tags (`!Ref`, `!Sub`) that plain YAML parsers
reject. Use `sam validate --template template.yaml` instead of `python -c
"import yaml..."`.

**Tests can’t import `conftest` or `handlers`**
`backend/pytest.ini` sets `pythonpath = src tests`. Run `pytest` from
`backend/`, not from the repo root.
