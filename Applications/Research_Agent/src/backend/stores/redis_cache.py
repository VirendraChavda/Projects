"""
Redis caching layer for embeddings, reranking scores, and API results.
Provides efficient caching with TTL, serialization, and cache invalidation.
"""
from __future__ import annotations
import json
import pickle
import os
from typing import Optional, Any, List
from datetime import datetime, timedelta

from backend.services.logging import get_logger

logger = get_logger(__name__)


class RedisCache:
    """
    Redis cache client for storing embeddings, scores, and results.
    Automatically handles serialization and TTL management.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        default_ttl: int = 3600,  # 1 hour default
        enable: bool = True,
    ):
        """
        Initialize Redis cache client.
        
        Args:
            host: Redis server host
            port: Redis server port
            db: Redis database number
            default_ttl: Default time-to-live in seconds
            enable: Whether to enable caching (for easy disable)
        """
        self.host = host
        self.port = port
        self.db = db
        self.default_ttl = default_ttl
        self.enable = enable
        self.client = None
        
        if enable:
            self._connect()
    
    def _connect(self) -> None:
        """Establish connection to Redis"""
        try:
            import redis
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=False,
                socket_connect_timeout=5,
            )
            # Test connection
            self.client.ping()
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
        except ImportError:
            logger.warning("redis-py not installed. Caching disabled.")
            self.enable = False
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Caching disabled.")
            self.enable = False
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage"""
        try:
            # Try JSON first for simple types
            if isinstance(value, (dict, list, str, int, float, bool)):
                return json.dumps(value).encode("utf-8")
        except (TypeError, ValueError):
            pass
        
        # Fall back to pickle for complex objects
        return pickle.dumps(value)
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize value from storage"""
        if not data:
            return None
        
        try:
            # Try JSON first
            return json.loads(data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fall back to pickle
            try:
                return pickle.loads(data)
            except Exception as e:
                logger.error(f"Failed to deserialize cache data: {e}")
                return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not provided)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enable or not self.client:
            return False
        
        try:
            serialized = self._serialize(value)
            ttl = ttl or self.default_ttl
            self.client.setex(
                name=key,
                time=ttl,
                value=serialized
            )
            logger.debug(f"Cached {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set error for {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if not self.enable or not self.client:
            return None
        
        try:
            data = self.client.get(key)
            if data:
                logger.debug(f"Cache hit: {key}")
                return self._deserialize(data)
            else:
                logger.debug(f"Cache miss: {key}")
                return None
        except Exception as e:
            logger.error(f"Cache get error for {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False otherwise
        """
        if not self.enable or not self.client:
            return False
        
        try:
            result = self.client.delete(key)
            logger.debug(f"Deleted cache key: {key}")
            return bool(result)
        except Exception as e:
            logger.error(f"Cache delete error for {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.enable or not self.client:
            return False
        
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for {key}: {e}")
            return False
    
    def expire(self, key: str, ttl: int) -> bool:
        """Update TTL for an existing key"""
        if not self.enable or not self.client:
            return False
        
        try:
            return bool(self.client.expire(key, ttl))
        except Exception as e:
            logger.error(f"Cache expire error for {key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.
        
        Args:
            pattern: Pattern to match (e.g., "embedding:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.enable or not self.client:
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                count = self.client.delete(*keys)
                logger.debug(f"Deleted {count} cache keys matching {pattern}")
                return count
            return 0
        except Exception as e:
            logger.error(f"Cache clear_pattern error: {e}")
            return 0
    
    def flush(self) -> bool:
        """Clear entire cache database"""
        if not self.enable or not self.client:
            return False
        
        try:
            self.client.flushdb()
            logger.info("Cache database flushed")
            return True
        except Exception as e:
            logger.error(f"Cache flush error: {e}")
            return False


class EmbeddingCache(RedisCache):
    """Specialized cache for embedding vectors"""
    
    def cache_embedding(
        self,
        text: str,
        embedding: List[float],
        ttl: int = 86400  # 24 hours
    ) -> bool:
        """Cache an embedding vector"""
        import hashlib
        key = f"embedding:{hashlib.md5(text.encode()).hexdigest()}"
        return self.set(key, embedding, ttl)
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Retrieve cached embedding"""
        import hashlib
        key = f"embedding:{hashlib.md5(text.encode()).hexdigest()}"
        return self.get(key)
    
    def clear_embeddings(self) -> int:
        """Clear all cached embeddings"""
        return self.clear_pattern("embedding:*")


class ResultCache(RedisCache):
    """Specialized cache for API results"""
    
    def cache_result(
        self,
        query: str,
        result: dict,
        ttl: int = 3600  # 1 hour
    ) -> bool:
        """Cache an API result"""
        import hashlib
        key = f"result:{hashlib.md5(query.encode()).hexdigest()}"
        return self.set(key, result, ttl)
    
    def get_result(self, query: str) -> Optional[dict]:
        """Retrieve cached result"""
        import hashlib
        key = f"result:{hashlib.md5(query.encode()).hexdigest()}"
        return self.get(key)
    
    def clear_results(self) -> int:
        """Clear all cached results"""
        return self.clear_pattern("result:*")


class ScoreCache(RedisCache):
    """Specialized cache for reranking scores"""
    
    def cache_scores(
        self,
        doc_id: str,
        scores: dict,
        ttl: int = 7200  # 2 hours
    ) -> bool:
        """Cache reranking scores for a document"""
        key = f"scores:{doc_id}"
        return self.set(key, scores, ttl)
    
    def get_scores(self, doc_id: str) -> Optional[dict]:
        """Retrieve cached scores"""
        key = f"scores:{doc_id}"
        return self.get(key)
    
    def clear_scores(self) -> int:
        """Clear all cached scores"""
        return self.clear_pattern("scores:*")


# Global cache instances
_redis_cache: Optional[RedisCache] = None
_embedding_cache: Optional[EmbeddingCache] = None
_result_cache: Optional[ResultCache] = None
_score_cache: Optional[ScoreCache] = None


def initialize_cache(
    host: str = "localhost",
    port: int = 6379,
    db: int = 0,
    default_ttl: int = 3600,
) -> None:
    """Initialize global cache instances"""
    global _redis_cache, _embedding_cache, _result_cache, _score_cache
    
    # Get settings from environment if available
    host = os.getenv("REDIS_HOST", host)
    port = int(os.getenv("REDIS_PORT", port))
    db = int(os.getenv("REDIS_DB", db))
    
    # Create cache instances
    _redis_cache = RedisCache(host, port, db, default_ttl)
    _embedding_cache = EmbeddingCache(host, port, db, default_ttl)
    _result_cache = ResultCache(host, port, db, default_ttl)
    _score_cache = ScoreCache(host, port, db, default_ttl)


def get_cache() -> RedisCache:
    """Get the global Redis cache instance"""
    if _redis_cache is None:
        initialize_cache()
    return _redis_cache


def get_embedding_cache() -> EmbeddingCache:
    """Get the global embedding cache instance"""
    if _embedding_cache is None:
        initialize_cache()
    return _embedding_cache


def get_result_cache() -> ResultCache:
    """Get the global result cache instance"""
    if _result_cache is None:
        initialize_cache()
    return _result_cache


def get_score_cache() -> ScoreCache:
    """Get the global score cache instance"""
    if _score_cache is None:
        initialize_cache()
    return _score_cache
