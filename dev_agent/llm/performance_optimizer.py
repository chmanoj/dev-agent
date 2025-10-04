"""Performance optimization utilities for LLM operations.

This module provides utilities for optimizing batch processing, caching,
and concurrent operations for Azure OpenAI API calls.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from dev_agent.llm.base import IEmbeddingClient
    from dev_agent.models.indexing import CodeChunk

logger = logging.getLogger(__name__)


class BatchOptimizer:
    """Optimizer for batch processing of embeddings.

    This class provides utilities for optimizing batch sizes and
    concurrent processing of embedding generation.
    """

    # Optimal batch sizes based on empirical testing
    OPTIMAL_BATCH_SIZE = 16  # Azure OpenAI supports up to 16 texts per call
    MAX_CONCURRENT_BATCHES = 3  # Maximum parallel API calls

    def __init__(
        self,
        embedding_client: IEmbeddingClient,
        batch_size: int = OPTIMAL_BATCH_SIZE,
        max_concurrent: int = MAX_CONCURRENT_BATCHES,
    ) -> None:
        """Initialize batch optimizer.

        Args:
            embedding_client: Embedding client to use
            batch_size: Number of texts per batch (default: 16)
            max_concurrent: Maximum concurrent batches (default: 3)
        """
        self.embedding_client = embedding_client
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent

    async def process_chunks_optimized(
        self,
        chunks: list[CodeChunk],
        progress_callback: Any = None,
    ) -> list[list[float]]:
        """Process chunks with optimized batching and concurrency.

        This method:
        1. Splits chunks into optimal batch sizes
        2. Processes up to max_concurrent batches in parallel
        3. Reports progress periodically

        Args:
            chunks: List of code chunks to process
            progress_callback: Optional callback for progress updates

        Returns:
            List of embeddings in same order as input chunks
        """
        if not chunks:
            return []

        total_chunks = len(chunks)
        logger.info(
            f"Processing {total_chunks} chunks with batch_size={self.batch_size}, "
            f"max_concurrent={self.max_concurrent}"
        )

        # Extract texts from chunks
        texts = [chunk.content for chunk in chunks]

        # Split into batches
        batches = [
            texts[i : i + self.batch_size]
            for i in range(0, len(texts), self.batch_size)
        ]

        # Process batches with controlled concurrency
        embeddings = []
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def process_batch_with_semaphore(
            batch: list[str],
            batch_idx: int,
        ) -> tuple[int, list[list[float]]]:
            """Process a single batch with semaphore control."""
            async with semaphore:
                batch_embeddings = await self.embedding_client.embed_batch(
                    batch,
                    batch_size=len(batch),
                )

                # Report progress
                if progress_callback and (
                    batch_idx % 10 == 0 or batch_idx == len(batches) - 1
                ):
                    processed = min((batch_idx + 1) * self.batch_size, total_chunks)
                    progress_callback(processed, total_chunks)

                return batch_idx, batch_embeddings

        # Create tasks for all batches
        tasks = [
            process_batch_with_semaphore(batch, idx)
            for idx, batch in enumerate(batches)
        ]

        # Execute with controlled concurrency
        results = await asyncio.gather(*tasks)

        # Sort results by batch index and flatten
        results.sort(key=lambda x: x[0])
        for _, batch_embeddings in results:
            embeddings.extend(batch_embeddings)

        logger.info(f"Processed {len(embeddings)} embeddings successfully")
        return embeddings


class CacheWarmer:
    """Utility for warming up the embedding cache with common queries.

    This class pre-generates embeddings for frequently used code patterns
    to improve cache hit rates.
    """

    # Common code patterns to pre-cache
    COMMON_PATTERNS: ClassVar[list[str]] = [
        "def __init__(self",
        "class ",
        "import ",
        "from ",
        "async def ",
        "return ",
        "if __name__ == '__main__':",
        "@property",
        "@staticmethod",
        "@classmethod",
    ]

    def __init__(self, embedding_client: IEmbeddingClient) -> None:
        """Initialize cache warmer.

        Args:
            embedding_client: Embedding client with cache
        """
        self.embedding_client = embedding_client

    async def warm_cache(self, additional_patterns: list[str] | None = None) -> int:
        """Warm up the cache with common patterns.

        Args:
            additional_patterns: Additional patterns to cache

        Returns:
            Number of patterns cached
        """
        patterns = self.COMMON_PATTERNS.copy()
        if additional_patterns:
            patterns.extend(additional_patterns)

        logger.info(f"Warming cache with {len(patterns)} patterns")

        # Generate embeddings for all patterns
        await self.embedding_client.embed_batch(patterns)

        logger.info(f"Cache warmed with {len(patterns)} patterns")
        return len(patterns)


class CacheOptimizer:
    """Optimizer for cache performance.

    This class provides utilities for analyzing and optimizing
    cache performance.
    """

    def __init__(self, cache: Any) -> None:
        """Initialize cache optimizer.

        Args:
            cache: Embedding cache instance
        """
        self.cache = cache

    def analyze_cache_performance(self) -> dict[str, Any]:
        """Analyze cache performance metrics.

        Returns:
            Dictionary with cache performance metrics
        """
        stats = self.cache.get_stats()

        # Calculate additional metrics
        hit_rate = stats["hit_rate"]

        # Estimate time saved (assuming 100ms per API call)
        time_saved_ms = stats["hits"] * 100

        # Estimate cost saved (assuming $0.0001 per 1K tokens, ~100 tokens per embedding)
        cost_saved = stats["hits"] * 0.00001

        return {
            **stats,
            "time_saved_seconds": time_saved_ms / 1000,
            "estimated_cost_saved_usd": cost_saved,
            "efficiency_rating": self._calculate_efficiency_rating(hit_rate),
        }

    def _calculate_efficiency_rating(self, hit_rate: float) -> str:
        """Calculate efficiency rating based on hit rate.

        Args:
            hit_rate: Cache hit rate percentage

        Returns:
            Efficiency rating string
        """
        if hit_rate >= 80:
            return "Excellent"
        elif hit_rate >= 60:
            return "Good"
        elif hit_rate >= 40:
            return "Fair"
        elif hit_rate >= 20:
            return "Poor"
        else:
            return "Very Poor"

    def get_optimization_recommendations(self) -> list[str]:
        """Get recommendations for cache optimization.

        Returns:
            List of optimization recommendations
        """
        stats = self.cache.get_stats()
        recommendations = []

        hit_rate = stats["hit_rate"]

        if hit_rate < 50:
            recommendations.append(
                "Cache hit rate is low. Consider warming the cache with common patterns."
            )

        if stats["cached_entries"] > 10000:
            recommendations.append(
                "Cache has many entries. Consider implementing LRU eviction."
            )

        cache_size_mb = stats["total_size_bytes"] / (1024 * 1024)
        if cache_size_mb > 100:
            recommendations.append(
                f"Cache size is {cache_size_mb:.1f}MB. Consider clearing old entries."
            )

        if not recommendations:
            recommendations.append("Cache performance is optimal.")

        return recommendations
