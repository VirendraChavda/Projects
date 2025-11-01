from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv(override=False)

@dataclass
class Settings:
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "ai_core")

    embed_model: str = os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5")
    embed_device: str = os.getenv("EMBED_DEVICE", "cpu")

    chunk_tokens: int = int(os.getenv("CHUNK_TOKENS", "300"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "50"))

    data_raw: str = os.getenv("DATA_RAW")
    data_processed: str = os.getenv("DATA_PROCESSED")

    arxiv_categories: list[str] = os.getenv(
        "ARXIV_CATEGORIES", "cs.LG,cs.AI,cs.CL,cs.CV,cs.IR,stat.ML"
    ).split(",")
    arxiv_max_results: int = int(os.getenv("ARXIV_MAX_RESULTS"))
    arxiv_days_back: int = int(os.getenv("ARXIV_DAYS_BACK"))

settings = Settings()
