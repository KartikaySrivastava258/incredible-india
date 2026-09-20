# Integration Notes — Matching Service (Saloni Sharma)

## What I implemented
- `GET /health` — liveness check.
- `POST /index/listing` — embeds an approved Listing's title + description +
  category + village + state, upserts it into the search index.
- `POST /match` — embeds buyer `query_text`, runs real k-NN vector search,
  returns the closest listings with similarity scores.
- A `SearchRepository` interface with two implementations behind the same
  method signatures: `OpenSearchRepository` (real k-NN, used for the demo)
  and `InMemorySearchRepository` (cosine similarity in a Python dict, used
  for tests and dev without Docker). Selected by `MATCHING_BACKEND`, with
  no automatic fallback: if OpenSearch is configured but unavailable, requests
  return HTTP 502 instead of silently switching to a different backend.
- Sample dataset: 10 listings across all four categories (food, textile,
  toy, handicraft) and 8 demo buyer queries, in
  `data/seed/opensearch_seed.json`.
- `scripts/seed_opensearch.py` — loads that dataset through the real
  `/index/listing` endpoint (never writes to OpenSearch directly), with an
  optional `--try-queries` flag to sanity-check all 8 demo queries and print
  their top matches before judges see it.
- `tests/test_matching.py` — covers indexing + finding via a related query,
  upsert-not-duplicate, no-good-match still returns a valid response,
  empty-index returns `[]`, and `/health`.

## Files I added
```
matching/app/models.py
matching/app/repository.py
matching/tests/test_matching.py
matching/README.md
matching/integration-notes.md   (this file)
data/seed/opensearch_seed.json
scripts/seed_opensearch.py
```

## Files I changed
```
matching/app/main.py        - added /index/listing and /match (health already existed)
matching/app/config.py      - added MATCHING_BACKEND
matching/.env.example       - added MATCHING_BACKEND
matching/requirements.txt   - re-saved as UTF-8 (was UTF-16, would have broken
                               `pip install -r requirements.txt` on most setups)
```
`app/embeddings.py` is unchanged from the original skeleton.

## APIs exposed
- `POST /index/listing` — see BRAIN.md Section G / task spec Section 7 for
  exact request/response shape. Implemented exactly as specified.
- `POST /match` — same.
- `GET /health` → `{"status": "ok"}`.

## APIs consumed
None — this service has no outbound dependency on the backend, AI service,
or any database besides its own OpenSearch instance, per task spec Section 8.

## Environment variables
```
OPENSEARCH_URL=http://localhost:9200      (BRAIN.md Section H)
MATCHING_SERVICE_PORT=8002                (BRAIN.md Section H)
MATCHING_BACKEND=opensearch               (new — matching-service-local only, see below)
```
`MATCHING_BACKEND` is not in BRAIN.md Section H because it's an internal
implementation detail of this module only (which repository backend to
construct) — it never crosses the `/index/listing` or `/match` HTTP
contract, so no other module needs to know it exists. Flagging it here per
the "announce new variables" rule anyway.

## Database / index changes
- OpenSearch index name: `kalaa_setu_listings`.
- Mapping: `listing_id` (keyword), `listing_title` (text), `category`
  (keyword), `village` (keyword), `state` (keyword), `searchable_text`
  (text), `embedding` (`knn_vector`, dimension 384, HNSW / cosinesimil,
  nmslib engine).
- Created automatically by the service on startup if it doesn't already
  exist — no manual index setup step needed.
- Embedding model: `all-MiniLM-L6-v2` via `sentence-transformers`, run
  locally, 384-dim, normalized (so plain dot product = cosine similarity).

## Cedar policy changes
None. This module has no access-control decisions to make — it's called
by the backend, which is where Cedar enforcement lives per BRAIN.md.

## Dependencies
See `requirements.txt`: `fastapi`, `uvicorn`, `pydantic`, `python-dotenv`,
`sentence-transformers` (pulls in `torch`/`transformers`), `opensearch-py`,
`numpy`, `requests`, `pytest`, `httpx`.

## How to run my module
See `README.md` for full instructions. Short version:
```bash
docker-compose up -d                       # from repo root — starts OpenSearch
cd matching
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8002
python ../scripts/seed_opensearch.py --try-queries
```

## How to test my module
```bash
cd matching
pytest
```
Runs entirely against the in-memory backend, so no Docker is required to run
the test suite. This verifies the matching *logic*; the real OpenSearch path
should additionally be checked manually with the seed script before the demo.

## What another developer should NOT change
- `matching/app/repository.py`'s `SearchRepository` interface (method
  signatures) — the backend only ever talks to this module over HTTP, so
  there's no reason to touch this file, but flagging it since it's the
  contract other matching-service code depends on.
- `data/seed/opensearch_seed.json` — shared with Dipanshu's DynamoDB seed
  script. If you need to add/change sample listings, keep both loaders in
  sync (same `listing_id`s) rather than forking the file.
- The `/index/listing` and `/match` request/response shapes — any change
  needs a BRAIN.md + `shared/api-contracts.md` update first.

## Known limitations
- Category/village/state are folded into the embedded text as soft signals
  (per task spec 5.2: "can be used as soft signals") rather than a separate
  re-ranking step — pure vector similarity decides ranking. This was the
  simplest approach that still satisfies "real vector search, not
  keyword-only" within the 4-day scope; a script-score boost by matching
  category would be a natural next step if there's time.
- Low-score matches are returned as-is (not filtered by a score threshold)
  per task spec 5.2's explicit choice — "so the demo has *something* to
  show" — rather than silently returning an empty array for weak queries.
- `refresh=True` is set on every OpenSearch write so newly indexed listings
  are searchable immediately. Fine for a small hackathon demo; would be
  removed for real production throughput.
- OpenSearch is not required to be reachable during Python module import/startup.
  The repository connects lazily through normal OpenSearch client calls, so a
  local service can start before Docker is ready. If OpenSearch is unavailable
  when `/index/listing` or `/match` is called, the API returns HTTP 502 instead
  of silently falling back to memory.

## Exact steps for integrating this module

1. Extract `matching/` from my ZIP, unmodified, into `kalaa-setu/matching/`.
2. Extract `data/seed/opensearch_seed.json` and `scripts/seed_opensearch.py`
   into their shared locations — do not overwrite Dipanshu's DynamoDB seed
   script or add a second `opensearch_seed.json`.
3. Add the OpenSearch service block below to the root `docker-compose.yml`
   (Dipanshu owns that file).
4. Confirm `matching/.env.example`'s three variables are present in the root
   `.env.example` union (Section H already lists `OPENSEARCH_URL`;
   `MATCHING_SERVICE_PORT` and `MATCHING_BACKEND` are matching-service-local
   and can live in `matching/.env` only if the team prefers not to add them
   to the root file).
5. Start order per BRAIN.md: infra (`docker-compose up -d`) → this service
   (`uvicorn app.main:app --port 8002`, from inside `matching/` with its own
   venv active) → backend → frontend.
6. Run `python scripts/seed_opensearch.py --try-queries` from the repo root
   once the service is up, to load demo data and confirm matches look good.
7. Backend integration point: on `POST /listings/:id/review` approval, the
   backend should call `POST {MATCHING_SERVICE_URL}/index/listing` with the
   approved Listing + `seller_village`/`seller_state`. On buyer search,
   backend's `POST /search/match` should proxy to
   `POST {MATCHING_SERVICE_URL}/match` and pass the result straight through
   (this service intentionally returns only `listing_id` + `score` +
   `listing_title` — the backend enriches with the noble-cause note etc.
   per task spec Section 9).

### docker-compose.yml OpenSearch service block (hand to Dipanshu verbatim)

```yaml
  opensearch:
    image: opensearchproject/opensearch:2.15.0
    container_name: kalaa-setu-opensearch
    environment:
      - discovery.type=single-node
      - plugins.security.disabled=true
      - "OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m"
      - bootstrap.memory_lock=true
    ulimits:
      memlock:
        soft: -1
        hard: -1
    ports:
      - "9200:9200"
      - "9600:9600"
    volumes:
      - opensearch-data:/usr/share/opensearch/data

volumes:
  opensearch-data:
```
(`plugins.security.disabled=true` is fine here because this only ever runs
on localhost for the demo — never expose this configuration outside a local
machine.)
