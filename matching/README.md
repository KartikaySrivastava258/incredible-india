# Kalaa Setu — Matching Service

Demand-matching engine for Kalaa Setu. Given a buyer's search text, this
service finds the hyperlocal listings that actually match it — using real
vector (k-NN) search over embeddings, not keyword matching or hardcoded
rules. See `BRAIN.md` and `SALONI_SHARMA_TASK.md` at the repo root for the
full picture; this README only covers running *this* module.

Owned by Saloni Sharma. Port `8002` (`MATCHING_SERVICE_URL`).

## What it does

- `POST /index/listing` — takes an approved `Listing` (plus the seller's
  village/state), embeds its title + description + category + location, and
  upserts it into the search index.
- `POST /match` — takes a buyer's `query_text`, embeds it, and returns the
  closest listings by vector similarity.
- `GET /health` — liveness check.

## Setup

1. Python 3.11+ recommended.
2. From this folder:
   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and adjust if needed (defaults are fine for
   local dev).

The first run downloads the `all-MiniLM-L6-v2` embedding model
(~90MB) from Hugging Face, so you need internet access once. After that it's
cached locally and works offline.

## Running it

**With real OpenSearch (what the demo must use):**

```bash
# from the repo root — starts OpenSearch (see docker-compose.yml)
docker-compose up -d

# from this folder
uvicorn app.main:app --reload --port 8002
```

Check `MATCHING_BACKEND=opensearch` in `.env` (the default). On startup the
service creates its own OpenSearch index (`kalaa_setu_listings`) if it
doesn't already exist — nothing else to set up by hand.

**Without Docker, for quick local dev:**

Set `MATCHING_BACKEND=memory` in `.env`. This selects the in-memory repository
explicitly for API/test work. There is no automatic fallback from OpenSearch
to memory: if OpenSearch is configured but unavailable, indexing/search requests
return HTTP 502 so the service never silently switches away from real vector
search. The judge demo must run against real OpenSearch.

## Loading the demo data

With the service running:

```bash
# from the repo root
python scripts/seed_opensearch.py --try-queries
```

This loads the 10 sample listings from `data/seed/opensearch_seed.json`
through the real `/index/listing` endpoint (never writes to OpenSearch
directly), then runs the 8 sample buyer queries against `/match` and prints
the top matches — a quick way to confirm the demo will land before judges
see it.

## Testing

```bash
pytest
```

Tests run against the in-memory backend directly (no Docker/OpenSearch
needed to run `pytest`) — see `tests/test_matching.py`. This checks the
matching *logic*; verify the real OpenSearch path manually with the seed
script above before the demo.

## Files

```
matching/
├── app/
│   ├── main.py         FastAPI app: /health, /index/listing, /match
│   ├── models.py        Request/response + Listing shapes
│   ├── repository.py    SearchRepository interface + in-memory/OpenSearch impls
│   ├── embeddings.py     Local embedding model wrapper (sentence-transformers)
│   └── config.py         Env var loading
├── tests/
│   └── test_matching.py
├── requirements.txt
├── .env.example
└── integration-notes.md
```

## Known limitations

See `integration-notes.md` for the full list — short version: no
category/location re-ranking beyond folding them into the embedded text
(pure vector similarity), and low-score results are returned as-is rather
than filtered out, by design (see task spec 5.2).
