import os

from dotenv import load_dotenv

load_dotenv()

OPENSEARCH_URL = os.getenv("OPENSEARCH_URL")
MATCHING_SERVICE_PORT = int(os.getenv("MATCHING_SERVICE_PORT", "8002"))

# "opensearch" = real k-NN search (required for the hackathon demo).
# "memory"     = in-process cosine search, explicitly selected for local
#                development/tests when Docker is not running.
MATCHING_BACKEND = os.getenv("MATCHING_BACKEND", "opensearch")
