from __future__ import annotations
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv(override=False)

@dataclass
class Settings:
    # Qdrant configuration
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "ai_core")

    # Embeddings configuration
    embed_model: str = os.getenv("EMBED_MODEL", "nomic-embed-text")
    embed_device: str = os.getenv("EMBED_DEVICE", "cpu")
    embed_api_url: str = os.getenv("EMBED_API_URL", "http://localhost:11434/api/embeddings")

    # Chunking configuration
    chunk_tokens: int = int(os.getenv("CHUNK_TOKENS", "300"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "50"))

    # Data paths
    data_raw: str = os.getenv("DATA_RAW")
    data_processed: str = os.getenv("DATA_PROCESSED")

    # arXiv configuration
    arxiv_categories: list[str] = field(
        default_factory=lambda: os.getenv(
            "ARXIV_CATEGORIES", "cs.LG,cs.AI,cs.CL,cs.CV,cs.IR,stat.ML"
        ).split(",")
    )
    arxiv_max_results: int = int(os.getenv("ARXIV_MAX_RESULTS", "100"))
    arxiv_days_back: int = int(os.getenv("ARXIV_DAYS_BACK", "7"))

    # LangGraph & Reranking configuration
    rerank_strategy: str = os.getenv("RERANK_STRATEGY", "ensemble")
    rerank_model: str = os.getenv("RERANK_MODEL", "mixedbread-ai/mxbai-rerank-xsmall-v1")
    rerank_top_k: int = int(os.getenv("RERANK_TOP_K", "20"))
    
    # MCP configuration
    mcp_enable: bool = os.getenv("MCP_ENABLE", "true").lower() == "true"
    mcp_timeout: int = int(os.getenv("MCP_TIMEOUT", "30"))
    
    # LLM configuration (OLLAMA local models)
    llm_provider: str = os.getenv("LLM_PROVIDER", "ollama")
    llm_model: str = os.getenv("LLM_MODEL", "qwen3:4b")
    llm_api_url: str = os.getenv("LLM_API_URL", "http://localhost:11434/api/generate")
    
    # Reasoning model for advanced analysis
    reasoning_model: str = os.getenv("REASONING_MODEL", "deepseek-r1:1.5b")
    reasoning_api_url: str = os.getenv("REASONING_API_URL", "http://localhost:11434/api/generate")
    
    # Ingestion configuration
    ingestion_batch_size: int = int(os.getenv("INGESTION_BATCH_SIZE", "5"))
    ingestion_progress_interval: float = float(os.getenv("INGESTION_PROGRESS_INTERVAL", "0.5"))

settings = Settings()
