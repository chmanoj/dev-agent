"""Google Gemini embedding client with caching and batch processing.

This module provides an implementation of the IEmbeddingClient interface for
Google Gemini's embedding models. It includes intelligent caching to avoid
redundant API calls and efficient batch processing for large datasets.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import TYPE_CHECKING, Any, NoReturn

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from dev_agent.errors.llm_exceptions import (
    LLMAPIError,
    LLMAuthenticationError,
    LLMBadRequestError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from dev_agent.llm.base import IEmbeddingClient
from dev_agent.llm.embedding_cache import EmbeddingCache

# Import cost tracker with try/except to handle optional dependency
try:
    from dev_agent.llm.cost_tracker import CostTracker
except ImportError:
    CostTracker = None

if TYPE_CHECKING:
    from pathlib import Path

    from dev_agent.models.llm_config import GeminiConfig

logger = logging.getLogger(__name__)


class GeminiEmbeddingClient(IEmbeddingClient):
    """Google Gemini embedding client with caching and batch processing.

    This client implements the IEmbeddingClient interface for Google Gemini's
    embedding models. It provides:

    - Efficient batch processing (16 texts per API call by default)
    - Disk-based caching to avoid redundant API calls
    - Progress tracking for large batches
    - Comprehensive error handling with automatic retry
    - Cache hit/miss statistics
    - FAISS compatibility

    The client returns 768-dimensional embedding vectors suitable for
    semantic similarity search and code analysis.

    Attributes:
        config: Gemini configuration
        model: Embedding model name (embedding-001 or text-embedding-004)
        cache: Embedding cache for storing/retrieving embeddings

    Example:
        ```python
        config = GeminiConfig(
            api_key="AIza...",
            embedding_model="embedding-001",
        )

        client = GeminiEmbeddingClient(config)

        # Single embedding
        embedding = await client.embed_text("def hello(): pass")

        # Batch embeddings
        texts = ["code1", "code2", "code3"]
        embeddings = await client.embed_batch(texts)

        # Check cache stats
        stats = client.cache.get_stats()
        print(f"Cache hit rate: {stats['hit_rate']:.1f}%")
        ```
    """

    # Gemini embedding models can produce different dimensional vectors
    # Default to 768 but allow configuration via environment variable
    EMBEDDING_DIMENSION = int(os.getenv("GEMINI_EMBEDDING_DIMENSION", "768"))

    # Default batch size for API calls (Gemini supports up to 100)
    DEFAULT_BATCH_SIZE = 16

    # Pricing for Gemini embeddings (per 1K tokens) - approximate
    EMBEDDING_COST_PER_1K_TOKENS = 0.00001

    def __init__(
        self,
        config: GeminiConfig,
        cache_dir: Path | str | None = None,
        cost_tracker: Any | None = None,
    ) -> None:
        """Initialize Gemini embedding client.

        Args:
            config: Gemini configuration with API key and model information
            cache_dir: Directory for embedding cache. Defaults to
                      '.dev_agent/embedding_cache'
            cost_tracker: Optional cost tracker for monitoring token usage

        Raises:
            ValueError: If configuration is invalid
        """
        self.config = config
        self.model = config.embedding_model
        self.cost_tracker = cost_tracker

        # Initialize cache
        if cache_dir is None:
            cache_dir = ".dev_agent/embedding_cache"
        self.cache = EmbeddingCache(cache_dir)

        # Configure Gemini API
        genai.configure(api_key=config.get_api_key_value())

        logger.info(f"Initialized Gemini embedding client with model: {self.model}")

    @property
    def dimension(self) -> int:
        """Get the dimension size of embedding vectors.

        Returns:
            Configurable embedding dimension (default 768, can be set via GEMINI_EMBEDDING_DIMENSION)
        """
        # Always check environment variable for latest value
        return int(os.getenv("GEMINI_EMBEDDING_DIMENSION", "768"))

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        This method first checks the cache for an existing embedding. If not
        found, it calls the Gemini API to generate a new embedding and
        caches the result.

        Args:
            text: Text to generate embedding for

        Returns:
            768-dimensional embedding vector

        Raises:
            LLMAuthenticationError: If authentication fails
            LLMRateLimitError: If rate limits are exceeded
            LLMTimeoutError: If request times out
            LLMBadRequestError: If request parameters are invalid
            LLMAPIError: For other API errors

        Example:
            ```python
            embedding = await client.embed_text("def hello(): pass")
            print(f"Embedding dimension: {len(embedding)}")
            ```
        """
        # Check cache first
        cached_embedding = self.cache.get(text, self.model)
        if cached_embedding is not None:
            logger.debug("Retrieved embedding from cache")
            return cached_embedding

        # Generate new embedding via API
        try:
            logger.debug(f"Generating embedding for text (length: {len(text)})")

            # Use Gemini's embed_content function
            result = genai.embed_content(
                model=f"models/{self.model}",
                content=text,
                task_type="retrieval_document",  # Optimized for document retrieval
            )

            embedding: list[float] = result["embedding"]

            # Validate embedding dimension
            expected_dim = self.dimension
            if len(embedding) != expected_dim:
                raise LLMAPIError(
                    f"Unexpected embedding dimension: {len(embedding)}, expected {expected_dim}",
                    "This may indicate a model configuration issue",
                )

            # Cache the result
            self.cache.set(text, self.model, embedding, self.EMBEDDING_DIMENSION)

            logger.debug("Generated embedding successfully")

            return embedding

        except Exception as e:
            self._handle_api_error(e)

    async def embed_batch(
        self,
        texts: list[str],
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> list[list[float]]:
        """Generate embeddings for a batch of texts.

        This method efficiently processes multiple texts by:
        1. Checking cache for each text
        2. Batching uncached texts into groups (default 16 per API call)
        3. Making parallel API calls for each batch
        4. Caching new embeddings
        5. Returning embeddings in the same order as input

        Progress is logged every 100 texts for large batches.

        Args:
            texts: List of texts to generate embeddings for
            batch_size: Number of texts per API call (1-100, default 16)

        Returns:
            List of 768-dimensional embedding vectors, one per input text,
            in the same order as the input

        Raises:
            LLMAuthenticationError: If authentication fails
            LLMRateLimitError: If rate limits are exceeded
            LLMTimeoutError: If request times out
            LLMBadRequestError: If request parameters are invalid
            LLMAPIError: For other API errors
            ValueError: If batch_size is invalid

        Example:
            ```python
            texts = ["code1", "code2", "code3"]
            embeddings = await client.embed_batch(texts, batch_size=16)
            print(f"Generated {len(embeddings)} embeddings")
            ```
        """
        if batch_size < 1 or batch_size > 100:
            raise ValueError(f"batch_size must be between 1 and 100, got {batch_size}")

        if not texts:
            return []

        logger.info(f"Processing {len(texts)} texts for embedding generation")

        # Track which texts need API calls and their original indices
        embeddings_result: list[list[float] | None] = [None] * len(texts)
        texts_to_embed: list[tuple[int, str]] = []

        # Check cache for each text
        for i, text in enumerate(texts):
            cached_embedding = self.cache.get(text, self.model)
            if cached_embedding is not None:
                embeddings_result[i] = cached_embedding
            else:
                texts_to_embed.append((i, text))

        cache_hits = len(texts) - len(texts_to_embed)
        logger.info(
            f"Cache hits: {cache_hits}/{len(texts)} "
            f"({cache_hits/len(texts)*100:.1f}%)"
        )

        # Process uncached texts in batches
        if texts_to_embed:
            await self._process_batches(
                texts_to_embed,
                embeddings_result,
                batch_size,
            )

        # Verify all embeddings were generated
        if any(emb is None for emb in embeddings_result):
            raise LLMAPIError(
                "Failed to generate embeddings for some texts",
                "Check logs for details about which texts failed",
            )

        # Type narrowing: we've verified no None values
        return [emb for emb in embeddings_result if emb is not None]

    async def _process_batches(
        self,
        texts_to_embed: list[tuple[int, str]],
        embeddings_result: list[list[float] | None],
        batch_size: int,
    ) -> None:
        """Process texts in batches with optimized concurrent processing.

        This method processes up to 5 batches concurrently for optimal performance
        while respecting Gemini API rate limits.

        Args:
            texts_to_embed: List of (index, text) tuples to process
            embeddings_result: Result list to update with embeddings
            batch_size: Number of texts per API call
        """
        total_batches = (len(texts_to_embed) + batch_size - 1) // batch_size

        # Limit concurrency to respect Gemini rate limits (5 parallel batches)
        max_concurrent = 5
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_batch_with_semaphore(batch_num: int) -> None:
            """Process a single batch with semaphore control."""
            async with semaphore:
                start_idx = batch_num * batch_size
                end_idx = min(start_idx + batch_size, len(texts_to_embed))
                batch = texts_to_embed[start_idx:end_idx]

                # Log progress less frequently for better performance
                if batch_num > 0 and batch_num % 20 == 0:
                    logger.info(
                        f"Progress: {batch_num}/{total_batches} batches "
                        f"({batch_num/total_batches*100:.1f}%)"
                    )

                await self._process_single_batch(batch, embeddings_result)

        # Create tasks for all batches
        tasks = [process_batch_with_semaphore(i) for i in range(total_batches)]

        # Execute with controlled concurrency
        await asyncio.gather(*tasks)

    async def _process_single_batch(
        self,
        batch: list[tuple[int, str]],
        embeddings_result: list[list[float] | None],
    ) -> None:
        """Process a single batch of texts.

        Args:
            batch: List of (index, text) tuples to process
            embeddings_result: Result list to update with embeddings
        """
        try:
            # Extract just the texts for API call
            batch_texts = [text for _, text in batch]

            logger.debug(f"Generating embeddings for batch of {len(batch_texts)} texts")

            # Use Gemini's batch embedding function
            result = genai.embed_content(
                model=f"models/{self.model}",
                content=batch_texts,
                task_type="retrieval_document",  # Optimized for document retrieval
            )

            # Handle both single and batch responses
            if isinstance(result["embedding"][0], list):
                # Batch response - list of embeddings
                batch_embeddings = result["embedding"]
            else:
                # Single response - wrap in list
                batch_embeddings = [result["embedding"]]

            # Validate we got the expected number of embeddings
            if len(batch_embeddings) != len(batch_texts):
                raise LLMAPIError(
                    f"Expected {len(batch_texts)} embeddings, got {len(batch_embeddings)}",
                    "This may indicate an API response format issue",
                )

            # Store embeddings in result list at correct indices
            for (original_idx, text), embedding in zip(
                batch, batch_embeddings, strict=False
            ):
                # Validate embedding dimension
                expected_dim = self.dimension
                if len(embedding) != expected_dim:
                    raise LLMAPIError(
                        f"Unexpected embedding dimension: {len(embedding)}, expected {expected_dim}",
                        "This may indicate a model configuration issue",
                    )

                embeddings_result[original_idx] = embedding

                # Cache the embedding
                self.cache.set(text, self.model, embedding, self.EMBEDDING_DIMENSION)

            # Track token usage and cost if cost tracker is available
            if (
                hasattr(self, "cost_tracker")
                and self.cost_tracker
                and CostTracker
                and isinstance(self.cost_tracker, CostTracker)
            ):
                # Estimate token count (Gemini doesn't provide exact counts)
                estimated_tokens = sum(len(text.split()) for text in batch_texts)
                self.cost_tracker.record_embedding(
                    tokens=estimated_tokens,
                    model=self.model,
                )

            logger.debug(f"Generated {len(batch_texts)} embeddings successfully")

        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            self._handle_api_error(e)

    def estimate_cost(self, token_count: int) -> float:
        """Estimate cost for embedding generation.

        Args:
            token_count: Number of tokens to embed

        Returns:
            Estimated cost in USD

        Example:
            ```python
            cost = client.estimate_cost(1000)
            print(f"Estimated cost: ${cost:.6f}")
            ```
        """
        return (token_count / 1000) * self.EMBEDDING_COST_PER_1K_TOKENS

    def _handle_api_error(self, error: Exception) -> NoReturn:
        """Handle Gemini API errors and raise appropriate exceptions.

        Args:
            error: Exception from Gemini API

        Raises:
            LLMAuthenticationError: For authentication failures
            LLMRateLimitError: For rate limit errors
            LLMTimeoutError: For timeout errors
            LLMBadRequestError: For bad request errors
            LLMAPIError: For other API errors
        """
        if isinstance(error, google_exceptions.PermissionDenied):
            logger.error("Gemini API authentication failed")
            raise LLMAuthenticationError(
                "Failed to authenticate with Google Gemini API",
                "Check that GEMINI_API_KEY is set correctly. "
                "Get your API key at: https://makersuite.google.com/app/apikey",
            ) from error

        if isinstance(error, google_exceptions.ResourceExhausted):
            logger.warning("Gemini API rate limit exceeded")
            raise LLMRateLimitError(
                "Gemini API rate limit exceeded",
                "The request will be retried automatically with exponential backoff",
            ) from error

        if isinstance(error, google_exceptions.DeadlineExceeded):
            logger.error("Gemini API request timed out")
            raise LLMTimeoutError(
                f"Request to Gemini API timed out after {self.config.timeout} seconds",
                "The request will be retried automatically",
            ) from error

        if isinstance(error, google_exceptions.InvalidArgument):
            logger.error(f"Invalid request to Gemini API: {error}")
            raise LLMBadRequestError(
                f"Invalid request to Gemini API: {error}",
                "Check that the model name and parameters are correct",
            ) from error

        if isinstance(error, google_exceptions.GoogleAPIError):
            logger.error(f"Gemini API error: {error}")
            raise LLMAPIError(
                f"Gemini API error: {error}",
                "Check Gemini service status or try again later",
            ) from error

        # Re-raise unexpected errors
        logger.error(f"Unexpected error in Gemini embedding client: {error}")
        raise LLMAPIError(
            f"Unexpected error: {error}", "Check logs for details"
        ) from error
