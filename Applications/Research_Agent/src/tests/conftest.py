"""
Pytest configuration and fixtures for Research Agent tests.
Provides shared test utilities and configurations.
"""
import os
import sys
import asyncio
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_data_dir():
    """Get test data directory"""
    return Path(__file__).parent / "data"


@pytest.fixture
def mock_llm_client():
    """Mock LLM client"""
    from backend.services.llm_client import LLMClient
    
    with patch.object(LLMClient, '_init_openai'):
        with patch.object(LLMClient, '_init_anthropic'):
            with patch.object(LLMClient, '_init_google'):
                client = LLMClient(provider="openai", api_key="test-key")
                client.client = Mock()
                return client


@pytest.fixture
def mock_database():
    """Mock database connection"""
    from backend.stores.postgres_repo import PostgresRepository
    
    with patch.object(PostgresRepository, '_init_db'):
        repo = PostgresRepository("sqlite:///:memory:")
        return repo


@pytest.fixture
def mock_vector_store():
    """Mock Qdrant vector store"""
    from backend.services.qdrant_store import QdrantStore
    
    with patch.object(QdrantStore, '_connect'):
        store = QdrantStore()
        store.client = Mock()
        return store


@pytest.fixture
def sample_paper():
    """Sample paper for testing"""
    return {
        "arxiv_id": "2301.00001",
        "title": "A Survey on Machine Learning",
        "authors": "John Doe, Jane Smith",
        "published_date": "2023-01-01",
        "pdf_path": "/data/papers/2301.00001.pdf",
        "fingerprint": "survey_machine_learning",
        "chunks_count": 10,
    }


@pytest.fixture
def sample_documents():
    """Sample documents for retrieval tests"""
    return [
        {
            "id": "doc1",
            "content": "Machine learning is a subset of artificial intelligence",
            "score": 0.85
        },
        {
            "id": "doc2",
            "content": "Deep learning uses neural networks with multiple layers",
            "score": 0.75
        },
        {
            "id": "doc3",
            "content": "Transformers have revolutionized NLP",
            "score": 0.65
        },
    ]


@pytest.fixture
def sample_chunks():
    """Sample text chunks"""
    return [
        "Machine learning is a subset of artificial intelligence that enables systems to learn from data.",
        "Deep learning uses neural networks with multiple layers to extract features from raw input.",
        "Transformers use attention mechanisms to process sequential data more efficiently than RNNs.",
    ]


@pytest.fixture
def sample_embedding():
    """Sample embedding vector"""
    import numpy as np
    return np.random.randn(384).tolist()  # 384-dim embedding


@pytest.fixture
def mock_settings():
    """Mock application settings"""
    settings = Mock()
    settings.llm_provider = "openai"
    settings.llm_model = "gpt-4"
    settings.llm_api_key = "test-key"
    settings.rerank_model = "mixedbread-ai/mxbai-rerank-xsmall-v1"
    settings.rerank_strategy = "ensemble"
    settings.qdrant_url = "http://localhost:6333"
    settings.qdrant_collection = "ai_core"
    settings.embed_model = "BAAI/bge-small-en-v1.5"
    return settings


@pytest.fixture
def mock_cache():
    """Mock Redis cache"""
    from backend.stores.redis_cache import RedisCache
    
    cache = RedisCache(enable=False)
    return cache


# pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify collected tests"""
    for item in items:
        # Add asyncio marker to async tests
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)
