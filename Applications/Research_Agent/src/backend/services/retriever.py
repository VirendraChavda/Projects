from __future__ import annotations
from typing import List, Dict
import numpy as np
from backend.services.embeddings import Embedder
from backend.services.qdrant_store import QdrantStore

class Retriever:
    def __init__(self, embedder: Embedder, store: QdrantStore):
        self.embedder = embedder
        self.store = store

    def search(self, query: str, k: int = 10) -> list[dict]:
        qv = self.embedder.encode([query])[0]
        qv = np.asarray(qv, dtype=np.float16)            # ensure dtype for Qdrant
        return self.store.search(qv, limit=k if k > 0 else 10)
