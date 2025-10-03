"""Unit tests for embedding cache."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from dev_agent.llm.embedding_cache import EmbeddingCache

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def temp_cache_dir(tmp_path: Path) -> Path:
    """Create temporary cache directory for testing."""
    cache_dir = tmp_path / "test_cache"
    return cache_dir


@pytest.fixture
def cache(temp_cache_dir: Path) -> EmbeddingCache:
    """Create embedding cache instance for testing."""
    return EmbeddingCache(cache_dir=temp_cache_dir)


def test_cache_initialization(temp_cache_dir: Path) -> None:
    """Test cache initialization creates directory."""
    cache = EmbeddingCache(cache_dir=temp_cache_dir)
    assert cache.cache_dir.exists()
    assert cache.cache_dir.is_dir()
    assert cache.hits == 0
    assert cache.misses == 0


def test_cache_directory_creation(temp_cache_dir: Path) -> None:
    """Test cache directory is created if it doesn't exist."""
    # Ensure directory doesn't exist
    assert not temp_cache_dir.exists()

    # Create cache
    _ = EmbeddingCache(cache_dir=temp_cache_dir)

    # Verify directory was created
    assert temp_cache_dir.exists()
    assert temp_cache_dir.is_dir()


def test_get_cache_key(cache: EmbeddingCache) -> None:
    """Test cache key generation using SHA-256."""
    text = "Hello, world!"
    model = "text-embedding-ada-002"

    key1 = cache._get_cache_key(text, model)

    # Key should be a 64-character hex string (SHA-256)
    assert len(key1) == 64
    assert all(c in "0123456789abcdef" for c in key1)

    # Same input should produce same key
    key2 = cache._get_cache_key(text, model)
    assert key1 == key2

    # Different text should produce different key
    key3 = cache._get_cache_key("Different text", model)
    assert key1 != key3

    # Different model should produce different key
    key4 = cache._get_cache_key(text, "different-model")
    assert key1 != key4


def test_cache_miss(cache: EmbeddingCache) -> None:
    """Test cache miss when embedding not cached."""
    text = "Test text"
    model = "text-embedding-ada-002"

    result = cache.get(text, model)

    assert result is None
    assert cache.misses == 1
    assert cache.hits == 0


def test_cache_hit(cache: EmbeddingCache) -> None:
    """Test cache hit when embedding is cached."""
    text = "Test text"
    model = "text-embedding-ada-002"
    embedding = [0.1, 0.2, 0.3, 0.4, 0.5]

    # Store embedding
    cache.set(text, model, embedding)

    # Retrieve embedding
    result = cache.get(text, model)

    assert result == embedding
    assert cache.hits == 1
    assert cache.misses == 0


def test_cache_set_and_get(cache: EmbeddingCache) -> None:
    """Test storing and retrieving embeddings."""
    text = "Sample text for embedding"
    model = "text-embedding-ada-002"
    embedding = [0.1] * 1536  # Typical embedding dimension

    # Store embedding
    cache.set(text, model, embedding, dimension=1536)

    # Retrieve embedding
    result = cache.get(text, model)

    assert result == embedding
    assert len(result) == 1536


def test_cache_metadata(cache: EmbeddingCache, temp_cache_dir: Path) -> None:
    """Test cache stores metadata correctly."""
    text = "Test text"
    model = "text-embedding-ada-002"
    embedding = [0.1, 0.2, 0.3]
    dimension = 3

    # Store embedding
    cache.set(text, model, embedding, dimension=dimension)

    # Read cache file directly
    cache_key = cache._get_cache_key(text, model)
    cache_path = temp_cache_dir / f"{cache_key}.json"

    assert cache_path.exists()

    with cache_path.open("r") as f:
        data = json.load(f)

    assert data["text_hash"] == cache_key
    assert data["model"] == model
    assert data["dimension"] == dimension
    assert data["embedding"] == embedding
    assert "timestamp" in data


def test_cache_auto_dimension(cache: EmbeddingCache) -> None:
    """Test cache auto-detects dimension if not provided."""
    text = "Test text"
    model = "text-embedding-ada-002"
    embedding = [0.1, 0.2, 0.3, 0.4]

    # Store without explicit dimension
    cache.set(text, model, embedding)

    # Retrieve and verify
    result = cache.get(text, model)
    assert result == embedding


def test_cache_model_mismatch(cache: EmbeddingCache) -> None:
    """Test cache miss when model doesn't match."""
    text = "Test text"
    model1 = "text-embedding-ada-002"
    model2 = "different-model"
    embedding = [0.1, 0.2, 0.3]

    # Store with model1
    cache.set(text, model1, embedding)

    # Try to retrieve with model2
    result = cache.get(text, model2)

    assert result is None
    assert cache.misses == 1


def test_cache_invalidate(cache: EmbeddingCache) -> None:
    """Test cache invalidation for specific entry."""
    text = "Test text"
    model = "text-embedding-ada-002"
    embedding = [0.1, 0.2, 0.3]

    # Store embedding
    cache.set(text, model, embedding)

    # Verify it's cached
    assert cache.get(text, model) == embedding

    # Invalidate
    result = cache.invalidate(text, model)
    assert result is True

    # Verify it's no longer cached
    assert cache.get(text, model) is None


def test_cache_invalidate_nonexistent(cache: EmbeddingCache) -> None:
    """Test invalidating non-existent cache entry."""
    text = "Test text"
    model = "text-embedding-ada-002"

    result = cache.invalidate(text, model)
    assert result is False


def test_cache_invalidate_model(cache: EmbeddingCache) -> None:
    """Test invalidating all entries for a model."""
    model1 = "text-embedding-ada-002"
    model2 = "different-model"
    embedding = [0.1, 0.2, 0.3]

    # Store multiple embeddings with different models
    cache.set("text1", model1, embedding)
    cache.set("text2", model1, embedding)
    cache.set("text3", model2, embedding)

    # Invalidate model1
    count = cache.invalidate_model(model1)

    assert count == 2

    # Verify model1 entries are gone
    assert cache.get("text1", model1) is None
    assert cache.get("text2", model1) is None

    # Verify model2 entry still exists
    assert cache.get("text3", model2) == embedding


def test_cache_clear(cache: EmbeddingCache) -> None:
    """Test clearing all cache entries."""
    model = "text-embedding-ada-002"
    embedding = [0.1, 0.2, 0.3]

    # Store multiple embeddings
    cache.set("text1", model, embedding)
    cache.set("text2", model, embedding)
    cache.set("text3", model, embedding)

    # Clear cache
    count = cache.clear()

    assert count == 3

    # Verify all entries are gone
    assert cache.get("text1", model) is None
    assert cache.get("text2", model) is None
    assert cache.get("text3", model) is None


def test_cache_stats(cache: EmbeddingCache) -> None:
    """Test cache statistics tracking."""
    model = "text-embedding-ada-002"
    embedding = [0.1, 0.2, 0.3]

    # Initial stats
    stats = cache.get_stats()
    assert stats["hits"] == 0
    assert stats["misses"] == 0
    assert stats["total_requests"] == 0
    assert stats["hit_rate"] == 0.0
    assert stats["cached_entries"] == 0

    # Store and retrieve
    cache.set("text1", model, embedding)
    cache.get("text1", model)  # Hit
    cache.get("text2", model)  # Miss

    stats = cache.get_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["total_requests"] == 2
    assert stats["hit_rate"] == 50.0
    assert stats["cached_entries"] == 1


def test_cache_reset_stats(cache: EmbeddingCache) -> None:
    """Test resetting cache statistics."""
    model = "text-embedding-ada-002"
    embedding = [0.1, 0.2, 0.3]

    # Generate some stats
    cache.set("text1", model, embedding)
    cache.get("text1", model)
    cache.get("text2", model)

    assert cache.hits > 0
    assert cache.misses > 0

    # Reset stats
    cache.reset_stats()

    assert cache.hits == 0
    assert cache.misses == 0


def test_cache_corrupted_file(cache: EmbeddingCache, temp_cache_dir: Path) -> None:
    """Test handling of corrupted cache file."""
    text = "Test text"
    model = "text-embedding-ada-002"

    # Create corrupted cache file
    cache_key = cache._get_cache_key(text, model)
    cache_path = temp_cache_dir / f"{cache_key}.json"
    cache_path.write_text("invalid json content")

    # Try to retrieve - should handle gracefully
    result = cache.get(text, model)

    assert result is None
    assert cache.misses == 1


def test_cache_multiple_texts(cache: EmbeddingCache) -> None:
    """Test caching multiple different texts."""
    model = "text-embedding-ada-002"
    texts_and_embeddings = [
        ("First text", [0.1, 0.2, 0.3]),
        ("Second text", [0.4, 0.5, 0.6]),
        ("Third text", [0.7, 0.8, 0.9]),
    ]

    # Store all embeddings
    for text, embedding in texts_and_embeddings:
        cache.set(text, model, embedding)

    # Retrieve and verify all embeddings
    for text, expected_embedding in texts_and_embeddings:
        result = cache.get(text, model)
        assert result == expected_embedding


def test_cache_large_embedding(cache: EmbeddingCache) -> None:
    """Test caching large embedding vectors."""
    text = "Test text"
    model = "text-embedding-ada-002"
    # Typical Azure OpenAI embedding dimension
    embedding = [0.1] * 1536

    cache.set(text, model, embedding)
    result = cache.get(text, model)

    assert result == embedding
    assert len(result) == 1536


def test_cache_special_characters(cache: EmbeddingCache) -> None:
    """Test caching text with special characters."""
    texts = [
        "Text with émojis 🎉🎊",
        "Text with\nnewlines\nand\ttabs",
        "Text with 'quotes' and \"double quotes\"",
        "Text with unicode: 你好世界",
    ]
    model = "text-embedding-ada-002"
    embedding = [0.1, 0.2, 0.3]

    for text in texts:
        cache.set(text, model, embedding)
        result = cache.get(text, model)
        assert result == embedding


@patch("dev_agent.llm.embedding_cache.logger")
def test_cache_logging(mock_logger: MagicMock, cache: EmbeddingCache) -> None:
    """Test cache logging behavior."""
    text = "Test text"
    model = "text-embedding-ada-002"
    embedding = [0.1, 0.2, 0.3]

    # Store embedding
    cache.set(text, model, embedding)

    # Verify debug logging was called
    assert mock_logger.debug.called

    # Get embedding (hit)
    cache.get(text, model)

    # Get non-existent embedding (miss)
    cache.get("different text", model)

    # Verify logging for hits and misses
    assert mock_logger.debug.call_count > 0


def test_cache_concurrent_access(cache: EmbeddingCache) -> None:
    """Test cache handles concurrent-like access patterns."""
    model = "text-embedding-ada-002"
    embedding = [0.1, 0.2, 0.3]

    # Simulate multiple rapid accesses
    for i in range(10):
        text = f"text_{i}"
        cache.set(text, model, embedding)

    # Verify all are cached
    for i in range(10):
        text = f"text_{i}"
        result = cache.get(text, model)
        assert result == embedding


def test_cache_path_generation(cache: EmbeddingCache) -> None:
    """Test cache file path generation."""
    text = "Test text"
    model = "text-embedding-ada-002"

    cache_key = cache._get_cache_key(text, model)
    cache_path = cache._get_cache_path(cache_key)

    assert cache_path.parent == cache.cache_dir
    assert cache_path.name == f"{cache_key}.json"
    assert cache_path.suffix == ".json"
