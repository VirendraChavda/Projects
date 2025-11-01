from __future__ import annotations
from typing import List, Dict, Any
import uuid
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from backend.config import settings

class QdrantStore:
    def __init__(self, url: str | None = None, collection: str | None = None, dim: int = 384):
        self.client = QdrantClient(url=url or settings.qdrant_url, prefer_grpc=False)
        self.collection = collection or settings.qdrant_collection
        self.dim = dim
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
        assert len(chunks) == len(vecs)
        points = []
        for i, ch in enumerate(chunks):
            pid = ch["chunk_id"]
            points.append(qmodels.PointStruct(
                id=pid,
                vector=vecs[i].tolist(),
                payload={
                    "paper_id": ch["paper_id"],
                    "section_id": ch["section_id"],
                    "chunk_id": ch["chunk_id"],
                    "text": ch["text"],
                    "order": ch["order"],
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
