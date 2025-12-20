from __future__ import annotations
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from backend.config import settings

class Embedder:
    def __init__(self, model_name: str | None = None, device: str | None = None):
        chosen = device or settings.embed_device
        if not chosen:
            chosen = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = chosen
        self.model = SentenceTransformer(model_name or settings.embed_model, device=self.device)

    def encode(self, texts: list[str]) -> np.ndarray:
        vecs = self.model.encode(texts, normalize_embeddings=True, convert_to_numpy=True, batch_size=64, show_progress_bar=False)
        return vecs.astype("float16")
