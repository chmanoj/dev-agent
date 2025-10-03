"""Embedding cache for Azure OpenAI embeddings.

This module provides disk-based caching for embeddings to avoid redundant API calls.
Embeddings are cached using SHA-256 content hashing with model-specific keys.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CacheMetadata:
    """Metadata for cached embedding."""

    text_hash: str
    model: str
    dimension: int
    timestamp: str
    embedding: list[float]


class EmbeddingCache:
    """Disk-based cache for embeddings with SHA-256 content hashing.

    This cache stores embeddings to disk to avoid redundant API calls to Azure OpenAI.
    Each embedding is stored with metadata including the model name, dimension, and
    timestamp. Cache keys are generated using SHA-256 hashing of the content and model.

    Attributes:
        cache_dir: Directory where cache files are stored
        hits: Number of cache hits
        misses: Number of cache misses
    """

    def __init__(self, cache_dir: Path | str = ".dev_agent/embedding_cache") -> None:
        """Initialize embedding cache.

        Args:
            cache_dir: Directory to store cache files. Defaults to
                      '.dev_agent/embedding_cache'
        """
        self.cache_dir = Path(cache_dir)
        self.hits = 0
        self.misses = 0
        self._ensure_cache_dir()

    def _ensure_cache_dir(self) -> None:
        """Create cache directory if it doesn't exist."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Cache directory ensured at: {self.cache_dir}")

    def _get_cache_key(self, text: str, model: str) -> str:
        """Generate SHA-256 hash key for cache lookup.

        The cache key is generated from both the text content and the model name
        to ensure that embeddings from different models are cached separately.

        Args:
            text: Text content to hash
            model: Model name (e.g., 'text-embedding-ada-002')

        Returns:
            SHA-256 hash as hexadecimal string
        """
        content = f"{model}:{text}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get file path for cache entry.

        Args:
            cache_key: SHA-256 hash key

        Returns:
            Path to cache file
        """
        return self.cache_dir / f"{cache_key}.json"

    def get(self, text: str, model: str) -> list[float] | None:
        """Retrieve cached embedding if it exists.

        Args:
            text: Text content to look up
            model: Model name used for embedding

        Returns:
            Cached embedding vector if found, None otherwise
        """
        cache_key = self._get_cache_key(text, model)
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            self.misses += 1
            logger.debug(f"Cache miss for key: {cache_key[:8]}...")
            return None

        try:
            with cache_path.open("r") as f:
                data = json.load(f)

            # Validate model matches
            if data.get("model") != model:
                logger.warning(
                    f"Model mismatch in cache: expected {model}, got {data.get('model')}"
                )
                self.misses += 1
                return None

            self.hits += 1
            logger.debug(f"Cache hit for key: {cache_key[:8]}...")
            embedding: list[float] = data["embedding"]
            return embedding

        except (json.JSONDecodeError, KeyError, OSError) as e:
            logger.error(f"Error reading cache file {cache_path}: {e}")
            self.misses += 1
            return None

    def set(
        self,
        text: str,
        model: str,
        embedding: list[float],
        dimension: int | None = None,
    ) -> None:
        """Store embedding in cache.

        Args:
            text: Text content that was embedded
            model: Model name used for embedding
            embedding: Embedding vector to cache
            dimension: Dimension of embedding vector (auto-detected if None)
        """
        cache_key = self._get_cache_key(text, model)
        cache_path = self._get_cache_path(cache_key)

        if dimension is None:
            dimension = len(embedding)

        cache_data = {
            "text_hash": cache_key,
            "model": model,
            "dimension": dimension,
            "timestamp": datetime.utcnow().isoformat(),
            "embedding": embedding,
        }

        try:
            with cache_path.open("w") as f:
                json.dump(cache_data, f)
            logger.debug(f"Cached embedding for key: {cache_key[:8]}...")
        except OSError as e:
            logger.error(f"Error writing cache file {cache_path}: {e}")

    def invalidate(self, text: str, model: str) -> bool:
        """Invalidate (delete) a cached embedding.

        Args:
            text: Text content to invalidate
            model: Model name

        Returns:
            True if cache entry was deleted, False if it didn't exist
        """
        cache_key = self._get_cache_key(text, model)
        cache_path = self._get_cache_path(cache_key)

        if cache_path.exists():
            try:
                cache_path.unlink()
                logger.debug(f"Invalidated cache for key: {cache_key[:8]}...")
                return True
            except OSError as e:
                logger.error(f"Error deleting cache file {cache_path}: {e}")
                return False

        return False

    def invalidate_model(self, model: str) -> int:
        """Invalidate all cached embeddings for a specific model.

        This is useful when switching to a new model version or when
        embeddings need to be regenerated.

        Args:
            model: Model name to invalidate

        Returns:
            Number of cache entries deleted
        """
        count = 0
        cache_files = list(self.cache_dir.glob("*.json"))

        for cache_file in cache_files:
            try:
                with cache_file.open("r") as f:
                    data = json.load(f)

                if data.get("model") == model:
                    cache_file.unlink()
                    count += 1

            except (json.JSONDecodeError, KeyError, OSError) as e:  # noqa: PERF203
                logger.error(f"Error processing cache file {cache_file}: {e}")

        logger.info(f"Invalidated {count} cache entries for model: {model}")
        return count

    def clear(self) -> int:
        """Clear all cached embeddings.

        Returns:
            Number of cache entries deleted
        """
        count = 0
        cache_files = list(self.cache_dir.glob("*.json"))

        for cache_file in cache_files:
            try:
                cache_file.unlink()
                count += 1
            except OSError as e:  # noqa: PERF203
                logger.error(f"Error deleting cache file {cache_file}: {e}")

        logger.info(f"Cleared {count} cache entries")
        return count

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics including hits, misses, and hit rate
        """
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0.0

        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)

        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total,
            "hit_rate": hit_rate,
            "cached_entries": len(cache_files),
            "total_size_bytes": total_size,
        }

    def reset_stats(self) -> None:
        """Reset hit/miss statistics."""
        self.hits = 0
        self.misses = 0
        logger.debug("Cache statistics reset")
