class EmbeddingService:
    """Local sentence embedding service. The model is loaded lazily so the
    FastAPI module can be imported for tests without downloading/loading a
    model until an embedding is actually needed."""

    MODEL_NAME = "all-MiniLM-L6-v2"

    def __init__(self):
        self.model = None

    def _get_model(self):
        if self.model is None:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.MODEL_NAME)
        return self.model

    def embed(self, text: str) -> list[float]:
        return self._get_model().encode(text, normalize_embeddings=True).tolist()
