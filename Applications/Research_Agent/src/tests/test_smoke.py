"""
Smoke tests for basic Research Agent functionality.
Validates core components work correctly.
"""
import sys
from pathlib import Path
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """Test that all core services can be imported"""
    # Services
    from backend.services.llm_client import LLMClient, LLMProvider
    from backend.services.rerank import AdvancedRanker
    from backend.services.chunker import Chunker
    from backend.services.logging import get_logger
    from backend.services.embeddings import EmbeddingsService
    from backend.services.qdrant_store import QdrantStore
    
    # Stores
    from backend.stores.redis_cache import RedisCache
    from backend.stores.postgres_repo import PostgresRepository, Paper
    
    # All imports successful
    assert True


def test_logger_initialization():
    """Test logger initialization"""
    from backend.services.logging import get_logger, setup_application_logging
    
    setup_application_logging()
    logger = get_logger("smoke_test")
    assert logger is not None


def test_embeddings_service():
    """Test embeddings service initialization"""
    from backend.services.embeddings import EmbeddingsService
    
    service = EmbeddingsService()
    assert service is not None
    assert service.model_name is not None


def test_redis_cache_disabled():
    """Test Redis cache with disabled state"""
    from backend.stores.redis_cache import RedisCache
    
    cache = RedisCache(enable=False)
    assert cache.enable == False
    result = cache.set("test_key", "test_value")
    assert result == False


def test_enum_values():
    """Test LLMProvider enum values"""
    from backend.services.llm_client import LLMProvider
    
    assert hasattr(LLMProvider, 'OPENAI')
    assert hasattr(LLMProvider, 'ANTHROPIC')
    assert hasattr(LLMProvider, 'GOOGLE')


def test_chunker_basic():
    """Test basic chunking functionality"""
    from backend.services.chunker import Chunker
    
    chunker = Chunker(chunk_tokens=300, overlap=50)
    text = "This is a test. " * 100
    chunks = chunker.chunk_text(text)
    assert len(chunks) > 0
    assert all(isinstance(c, str) for c in chunks)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
