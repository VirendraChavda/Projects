"""
Unit tests for the Research Agent services.
Tests core functionality including LLM client, reranking, embeddings, and utilities.
"""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from typing import List

# Test fixtures
@pytest.fixture
def mock_settings():
    """Mock settings for tests"""
    settings = Mock()
    settings.llm_provider = "openai"
    settings.llm_model = "gpt-4"
    settings.llm_api_key = "test-key"
    settings.rerank_model = "mixedbread-ai/mxbai-rerank-xsmall-v1"
    return settings


@pytest.fixture
def sample_documents():
    """Sample documents for testing"""
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
    """Sample text chunks for testing"""
    return [
        "This is the first chunk of text about machine learning.",
        "This chunk discusses neural network architectures.",
        "This chunk covers attention mechanisms in transformers.",
    ]


# LLM Client Tests
class TestLLMClient:
    """Tests for LLMClient service"""
    
    @patch('backend.services.llm_client.OpenAI')
    def test_init_openai(self, mock_openai, mock_settings):
        """Test OpenAI client initialization"""
        from backend.services.llm_client import LLMClient
        
        client = LLMClient(provider="openai", api_key="test-key")
        assert client.provider == "openai"
        assert client.model is not None
    
    def test_llm_provider_enum(self):
        """Test LLMProvider enum"""
        from backend.services.llm_client import LLMProvider
        
        assert LLMProvider.OPENAI == "openai"
        assert LLMProvider.ANTHROPIC == "anthropic"
        assert LLMProvider.GOOGLE == "google"
    
    def test_unsupported_provider(self):
        """Test initialization with unsupported provider"""
        from backend.services.llm_client import LLMClient
        
        with pytest.raises(ValueError):
            LLMClient(provider="unsupported", api_key="test-key")


# Reranking Tests
class TestAdvancedRanker:
    """Tests for advanced reranking service"""
    
    @pytest.mark.parametrize("strategy", ["cross_encoder", "semantic_diversity", "ensemble"])
    def test_rerank_strategies(self, strategy, sample_documents):
        """Test different reranking strategies"""
        from backend.services.rerank import AdvancedRanker
        
        ranker = AdvancedRanker(strategy=strategy)
        assert ranker.strategy == strategy
    
    def test_fallback_rerank(self, sample_documents):
        """Test fallback reranking (simple sorting)"""
        from backend.services.rerank import AdvancedRanker
        
        ranker = AdvancedRanker()
        # Fallback should return sorted by score
        reranked = ranker._fallback_rerank(sample_documents)
        
        assert len(reranked) == len(sample_documents)
        # Check if sorted by score
        for i in range(len(reranked) - 1):
            assert reranked[i]['score'] >= reranked[i + 1]['score']


# Chunking Tests
class TestChunker:
    """Tests for text chunking service"""
    
    def test_chunker_basic(self, sample_chunks):
        """Test basic chunking functionality"""
        from backend.services.chunker import Chunker
        
        chunker = Chunker(chunk_tokens=300, overlap=50)
        assert chunker.chunk_tokens == 300
        assert chunker.overlap == 50
    
    def test_chunk_text_tokenization(self):
        """Test text chunking with tokenization"""
        from backend.services.chunker import Chunker
        
        chunker = Chunker(chunk_tokens=50, overlap=10)
        text = "This is a longer text that should be split into multiple chunks. " * 5
        
        chunks = chunker.chunk_text(text)
        assert isinstance(chunks, list)
        assert len(chunks) > 0


# Logging Tests
class TestLoggingService:
    """Tests for logging service"""
    
    def test_get_logger(self):
        """Test logger creation"""
        from backend.services.logging import get_logger
        
        logger = get_logger("test_logger")
        assert logger is not None
        assert logger.name == "test_logger"
    
    def test_error_handler(self):
        """Test error handler"""
        from backend.services.logging import ErrorHandler
        
        handler = ErrorHandler()
        error = ValueError("Test error")
        handler.log_error(error, context="test_context")
        
        summary = handler.get_error_summary()
        assert len(summary) > 0
    
    def test_performance_logger(self):
        """Test performance logger"""
        from backend.services.logging import PerformanceLogger
        
        logger = PerformanceLogger()
        logger.log_operation_time("test_op", 0.5)
        
        # Should not raise exception
        assert True


# Redis Cache Tests
class TestRedisCache:
    """Tests for Redis caching service"""
    
    @patch('backend.stores.redis_cache.redis.Redis')
    def test_cache_set_get(self, mock_redis):
        """Test cache set/get operations"""
        from backend.stores.redis_cache import RedisCache
        
        cache = RedisCache(enable=False)  # Disable actual Redis connection
        # When disabled, should not cache
        result = cache.set("key", "value")
        assert result == False
    
    def test_cache_disabled(self):
        """Test cache when disabled"""
        from backend.stores.redis_cache import RedisCache
        
        cache = RedisCache(enable=False)
        assert cache.enable == False
        assert cache.get("any_key") is None


# Embeddings Tests
class TestEmbeddings:
    """Tests for embeddings service"""
    
    def test_embeddings_init(self):
        """Test embeddings initialization"""
        from backend.services.embeddings import EmbeddingsService
        
        service = EmbeddingsService()
        assert service is not None
        assert service.model_name is not None


# Audit Trail Tests
class TestAuditTrail:
    """Tests for audit trail service"""
    
    def test_audit_trail_logging(self):
        """Test audit trail event logging"""
        from backend.services.audit_trail import AuditTrail
        
        trail = AuditTrail()
        trail.log_event("test_event", "test_user", {"data": "test"})
        
        # Should not raise exception
        assert True


# PostgreSQL Repository Tests
class TestPostgresRepository:
    """Tests for PostgreSQL repository"""
    
    def test_paper_model(self):
        """Test Paper SQLAlchemy model"""
        from backend.stores.postgres_repo import Paper
        from datetime import datetime
        
        paper = Paper(
            arxiv_id="2301.00001",
            title="Test Paper",
            authors="Author 1, Author 2",
            fingerprint="test_paper"
        )
        
        assert paper.arxiv_id == "2301.00001"
        assert paper.title == "Test Paper"
    
    @patch('backend.stores.postgres_repo.create_engine')
    def test_repository_init(self, mock_engine):
        """Test repository initialization"""
        from backend.stores.postgres_repo import PostgresRepository
        
        # With mocked engine, should not fail
        with patch.object(PostgresRepository, '_init_db'):
            repo = PostgresRepository("sqlite:///:memory:")
            assert repo.database_url == "sqlite:///:memory:"


# Qdrant Vector Store Tests
class TestQdrantStore:
    """Tests for Qdrant vector store"""
    
    def test_qdrant_client_init(self):
        """Test Qdrant client initialization"""
        from backend.services.qdrant_store import QdrantStore
        
        store = QdrantStore()
        assert store is not None


# Design Suggester Tests
class TestDesignSuggester:
    """Tests for design suggestion service"""
    
    def test_suggest_design_patterns(self):
        """Test design pattern suggestions"""
        from backend.services.design_suggester import DesignSuggester
        
        suggester = DesignSuggester()
        assert suggester is not None


# Gap Analysis Tests
class TestGapAnalysis:
    """Tests for gap analysis service"""
    
    def test_analyze_gaps(self):
        """Test gap analysis functionality"""
        from backend.services.gap_analysis import GapAnalyzer
        
        analyzer = GapAnalyzer()
        assert analyzer is not None


# PDF Parsing Tests
class TestPDFParser:
    """Tests for PDF parsing service"""
    
    def test_pdf_parser_init(self):
        """Test PDF parser initialization"""
        from backend.services.pdf_parse import PDFParser
        
        parser = PDFParser()
        assert parser is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
