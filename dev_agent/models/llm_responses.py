"""LLM response models for Azure OpenAI operations.

This module provides dataclasses for representing responses from LLM operations,
including completions and embeddings. These models capture all relevant metadata
such as token usage, costs, and cache statistics.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CompletionResponse:
    """Response from LLM completion operation.
    
    This dataclass encapsulates all information returned from a completion
    request, including the generated content, token usage, and cost estimation.
    
    Attributes:
        content: Generated text content from the LLM
        model: Model name used for generation (e.g., "gpt-4")
        prompt_tokens: Number of tokens in the prompt
        completion_tokens: Number of tokens in the completion
        total_tokens: Total tokens used (prompt + completion)
        finish_reason: Reason completion finished (e.g., "stop", "length")
        estimated_cost: Estimated cost in USD for this operation
    
    Example:
        ```python
        response = CompletionResponse(
            content="Generated code here...",
            model="gpt-4",
            prompt_tokens=150,
            completion_tokens=300,
            total_tokens=450,
            finish_reason="stop",
            estimated_cost=0.027,
        )
        print(f"Cost: ${response.estimated_cost:.4f}")
        ```
    """

    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    finish_reason: str
    estimated_cost: float

    def __post_init__(self) -> None:
        """Validate response data after initialization."""
        if self.prompt_tokens < 0:
            raise ValueError("prompt_tokens must be non-negative")
        if self.completion_tokens < 0:
            raise ValueError("completion_tokens must be non-negative")
        if self.total_tokens != self.prompt_tokens + self.completion_tokens:
            raise ValueError(
                f"total_tokens ({self.total_tokens}) must equal "
                f"prompt_tokens ({self.prompt_tokens}) + "
                f"completion_tokens ({self.completion_tokens})"
            )
        if self.estimated_cost < 0:
            raise ValueError("estimated_cost must be non-negative")


@dataclass
class EmbeddingResponse:
    """Response from embedding generation operation.
    
    This dataclass encapsulates all information returned from an embedding
    request, including the generated embeddings, token usage, cost estimation,
    and cache statistics.
    
    Attributes:
        embeddings: List of embedding vectors (each vector is a list of floats)
        model: Model name used for embeddings (e.g., "text-embedding-ada-002")
        total_tokens: Total tokens used for embedding generation
        dimension: Dimension of each embedding vector (e.g., 1536)
        estimated_cost: Estimated cost in USD for this operation
        cache_hits: Number of embeddings retrieved from cache
        cache_misses: Number of embeddings generated via API call
    
    Example:
        ```python
        response = EmbeddingResponse(
            embeddings=[[0.1, 0.2, ...], [0.3, 0.4, ...]],
            model="text-embedding-ada-002",
            total_tokens=100,
            dimension=1536,
            estimated_cost=0.00001,
            cache_hits=5,
            cache_misses=2,
        )
        print(f"Cache hit rate: {response.cache_hit_rate:.1%}")
        ```
    """

    embeddings: list[list[float]]
    model: str
    total_tokens: int
    dimension: int
    estimated_cost: float
    cache_hits: int
    cache_misses: int

    def __post_init__(self) -> None:
        """Validate response data after initialization."""
        if self.total_tokens < 0:
            raise ValueError("total_tokens must be non-negative")
        if self.dimension <= 0:
            raise ValueError("dimension must be positive")
        if self.estimated_cost < 0:
            raise ValueError("estimated_cost must be non-negative")
        if self.cache_hits < 0:
            raise ValueError("cache_hits must be non-negative")
        if self.cache_misses < 0:
            raise ValueError("cache_misses must be non-negative")
        
        # Validate embedding dimensions
        for i, embedding in enumerate(self.embeddings):
            if len(embedding) != self.dimension:
                raise ValueError(
                    f"Embedding {i} has dimension {len(embedding)}, "
                    f"expected {self.dimension}"
                )

    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate as a percentage.
        
        Returns:
            Cache hit rate between 0.0 and 1.0
        """
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total

    @property
    def total_embeddings(self) -> int:
        """Get total number of embeddings in response.
        
        Returns:
            Number of embedding vectors
        """
        return len(self.embeddings)
