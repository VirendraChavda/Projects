from __future__ import annotations
import numpy as np
from sentence_transformers import SentenceTransformer
from backend.config import settings

class Embedder:
    def __init__(self, model_name: str | None = None, device: str | None = None):
        self.model = SentenceTransformer(model_name or settings.embed_model, device=device or settings.embed_device)

    def encode(self, texts: list[str]) -> np.ndarray:
        vecs = self.model.encode(texts, normalize_embeddings=True, convert_to_numpy=True, batch_size=64, show_progress_bar=False)
        return vecs.astype("float32")
