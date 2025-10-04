"""Azure OpenAI embedding client with caching and batch processing.

This module provides an implementation of the IEmbeddingClient interface for
Azure OpenAI's text-embedding-ada-002 model. It includes intelligent caching
to avoid redundant API calls and efficient batch processing for large datasets.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from openai import AsyncAzureOpenAI

from dev_agent.errors.llm_exceptions import (
    LLMAPIError,
    LLMAuthenticationError,
    LLMBadRequestError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from dev_agent.llm.base import IEmbeddingClient
from dev_agent.llm.embedding_cache import EmbeddingCache
from dev_agent.models.llm_config import AzureOpenAIConfig

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class AzureEmbeddingClient(IEmbeddingClient):
    """Azure OpenAI embedding client with caching and batch processing.
    
    This client implements the IEmbeddingClient interface for Azure OpenAI's
    text-embedding-ada-002 model. It provides:
    
    - Efficient batch processing (16 texts per API call by default)
    - Disk-based caching to avoid redundant API calls
    - Progress tracking for large batches
    - Comprehensive error handling with automatic retry
    - Cache hit/miss statistics
    
    The client returns 1536-dimensional embedding vectors suitable for
    semantic similarity search and code analysis.
    
    Attributes:
        config: Azure OpenAI configuration
        client: Async Azure OpenAI client
        cache: Embedding cache for storing/retrieving embeddings
        model: Embedding model name (text-embedding-ada-002)
    
    Example:
        ```python
        config = AzureOpenAIConfig(
            endpoint="https://my-resource.openai.azure.com/",
            api_key="sk-...",
            embedding_deployment="text-embedding-ada-002",
        )
        
        client = AzureEmbeddingClient(config)
        
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

    # text-embedding-ada-002 produces 1536-dimensional vectors
    EMBEDDING_DIMENSION = 1536
    
    # Default batch size for API calls (Azure OpenAI supports up to 16)
    DEFAULT_BATCH_SIZE = 16
    
    # Pricing for text-embedding-ada-002 (per 1K tokens)
    EMBEDDING_COST_PER_1K_TOKENS = 0.0001

    def __init__(
        self,
        config: AzureOpenAIConfig,
        cache_dir: Path | str | None = None,
        client: AsyncAzureOpenAI | None = None,
    ) -> None:
        """Initialize Azure embedding client.
        
        Args:
            config: Azure OpenAI configuration with endpoint, API key, and
                   deployment information
            cache_dir: Directory for embedding cache. Defaults to
                      '.dev_agent/embedding_cache'
            client: Optional pre-configured AsyncAzureOpenAI client for testing.
                   If not provided, a new client will be created.
        
        Raises:
            ValueError: If configuration is invalid
        """
        self.config = config
        self.model = config.embedding_deployment
        
        # Initialize cache
        if cache_dir is None:
            cache_dir = ".dev_agent/embedding_cache"
        self.cache = EmbeddingCache(cache_dir)
        
        # Initialize Azure OpenAI client
        if client is None:
            self.client = AsyncAzureOpenAI(
                api_key=config.api_key.get_secret_value(),
                api_version=config.api_version,
                azure_endpoint=config.endpoint,
                timeout=config.timeout,
                max_retries=config.max_retries,
            )
        else:
            self.client = client
        
        logger.info(
            f"Initialized Azure embedding client with model: {self.model}"
        )

    @property
    def dimension(self) -> int:
        """Get the dimension size of embedding vectors.
        
        Returns:
            1536 for text-embedding-ada-002
        """
        return self.EMBEDDING_DIMENSION

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text.
        
        This method first checks the cache for an existing embedding. If not
        found, it calls the Azure OpenAI API to generate a new embedding and
        caches the result.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            1536-dimensional embedding vector
            
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
            
            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
            )
            
            embedding: list[float] = response.data[0].embedding
            
            # Cache the result
            self.cache.set(text, self.model, embedding, self.EMBEDDING_DIMENSION)
            
            logger.debug(
                f"Generated embedding with {response.usage.total_tokens} tokens"
            )
            
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
            List of 1536-dimensional embedding vectors, one per input text,
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
                "Check logs for details about which texts failed"
            )
        
        # Type narrowing: we've verified no None values
        return [emb for emb in embeddings_result if emb is not None]

    async def _process_batches(
        self,
        texts_to_embed: list[tuple[int, str]],
        embeddings_result: list[list[float] | None],
        batch_size: int,
    ) -> None:
        """Process texts in batches with concurrent processing.
        
        This method processes up to 3 batches concurrently for optimal performance.
        
        Args:
            texts_to_embed: List of (index, text) tuples to process
            embeddings_result: Result list to update with embeddings
            batch_size: Number of texts per API call
        """
        total_batches = (len(texts_to_embed) + batch_size - 1) // batch_size
        
        # Process batches with controlled concurrency (up to 3 parallel)
        max_concurrent = 3
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_batch_with_semaphore(batch_num: int) -> None:
            """Process a single batch with semaphore control."""
            async with semaphore:
                start_idx = batch_num * batch_size
                end_idx = min(start_idx + batch_size, len(texts_to_embed))
                batch = texts_to_embed[start_idx:end_idx]
                
                # Log progress for large batches
                if batch_num > 0 and batch_num % 10 == 0:
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
            
            response = await self.client.embeddings.create(
                model=self.model,
                input=batch_texts,
            )
            
            # Store embeddings in result list at correct indices
            for (original_idx, text), embedding_data in zip(batch, response.data):
                embedding: list[float] = embedding_data.embedding
                embeddings_result[original_idx] = embedding
                
                # Cache the embedding
                self.cache.set(text, self.model, embedding, self.EMBEDDING_DIMENSION)
            
            logger.debug(
                f"Generated {len(batch_texts)} embeddings with "
                f"{response.usage.total_tokens} tokens"
            )
            
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

    def _handle_api_error(self, error: Exception) -> None:
        """Handle Azure OpenAI API errors and raise appropriate exceptions.
        
        Args:
            error: Exception from Azure OpenAI API
            
        Raises:
            LLMAuthenticationError: For authentication failures
            LLMRateLimitError: For rate limit errors
            LLMTimeoutError: For timeout errors
            LLMBadRequestError: For bad request errors
            LLMAPIError: For other API errors
        """
        from openai import (
            APIError,
            APITimeoutError,
            AuthenticationError,
            BadRequestError,
            RateLimitError,
        )
        
        if isinstance(error, AuthenticationError):
            logger.error("Azure OpenAI authentication failed")
            raise LLMAuthenticationError(
                "Failed to authenticate with Azure OpenAI",
                "Check that AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT are set correctly"
            ) from error
        
        if isinstance(error, RateLimitError):
            logger.warning("Azure OpenAI rate limit exceeded")
            raise LLMRateLimitError(
                "Azure OpenAI rate limit exceeded",
                "The request will be retried automatically with exponential backoff"
            ) from error
        
        if isinstance(error, APITimeoutError):
            logger.error("Azure OpenAI request timed out")
            raise LLMTimeoutError(
                f"Request to Azure OpenAI timed out after {self.config.timeout} seconds",
                "The request will be retried automatically"
            ) from error
        
        if isinstance(error, BadRequestError):
            logger.error(f"Invalid request to Azure OpenAI: {error}")
            raise LLMBadRequestError(
                f"Invalid request to Azure OpenAI: {error}",
                "Check that the deployment name and model configuration are correct"
            ) from error
        
        if isinstance(error, APIError):
            logger.error(f"Azure OpenAI API error: {error}")
            raise LLMAPIError(
                f"Azure OpenAI API error: {error}",
                "Check Azure OpenAI service status at status.azure.com"
            ) from error
        
        # Re-raise unexpected errors
        logger.error(f"Unexpected error in embedding client: {error}")
        raise LLMAPIError(
            f"Unexpected error: {error}",
            "Check logs for details"
        ) from error
