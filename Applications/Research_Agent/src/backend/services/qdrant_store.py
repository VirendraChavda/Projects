# ...existing code...
from __future__ import annotations
from typing import List, Dict, Any
import uuid
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from backend.config import settings

class QdrantStore:
    def __init__(self, url: str | None = None, collection: str | None = None, dim: int | None = None):
        self.client = QdrantClient(url=url or settings.qdrant_url, prefer_grpc=False)
        self.collection = collection or settings.qdrant_collection
        self.dim = dim
        # only create collection if dim known
        if self.dim is not None:
            self.ensure_collection()

    def ensure_collection(self) -> None:
        try:
            self.client.get_collection(self.collection)
        except Exception:
            self.client.recreate_collection(
                collection_name=self.collection,
                vectors_config=qmodels.VectorParams(size=self.dim, distance=qmodels.Distance.COSINE),
            )
            # Optional: payload indexes for filters added later

    def upsert(self, chunks: list[dict], vecs: np.ndarray) -> int:
        vecs = np.asarray(vecs)
        if vecs.dtype != np.float32:
            vecs = vecs.astype(np.float32)

        # infer dim on first upsert
        if self.dim is None:
            if vecs.ndim != 2:
                raise ValueError("vecs must be 2D array (n_items, dim)")
            self.dim = vecs.shape[1]
            self.ensure_collection()

        assert len(chunks) == len(vecs), "chunks and vecs must have same length"
        points = []
        for i, ch in enumerate(chunks):
            pid = ch.get("chunk_id") or str(uuid.uuid4())
            points.append(qmodels.PointStruct(
                id=pid,
                vector=vecs[i].tolist(),
                payload={
                    "paper_id": ch.get("paper_id"),
                    "section_id": ch.get("section_id"),
                    "chunk_id": ch.get("chunk_id"),
                    "text": ch.get("text"),
                    "order": ch.get("order"),
                    "page_from": ch.get("page_from"),
                    "page_to": ch.get("page_to"),
                }
            ))
        self.client.upsert(collection_name=self.collection, points=points, wait=True)
        return len(points)

    def search(self, qvec: np.ndarray, limit: int = 10) -> list[dict]:
        res = self.client.search(
            collection_name=self.collection,
            query_vector=qvec.tolist(),
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )
        out = []
        for r in res:
            p = r.payload or {}
            out.append({
                "chunk_id": p.get("chunk_id"),
                "paper_id": p.get("paper_id"),
                "section_id": p.get("section_id"),
                "text": p.get("text"),
                "score": float(r.score),
            })
        return out
