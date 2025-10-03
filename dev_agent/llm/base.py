"""Abstract base interfaces for LLM and embedding clients.

This module defines provider-agnostic interfaces that allow the system to work
with different LLM providers while maintaining consistent APIs.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


class ILLMClient(ABC):
    """Abstract interface for LLM providers.

    This interface defines the contract that all LLM client implementations
    must follow, enabling provider-agnostic code throughout the application.

    Example:
        ```python
        class AzureOpenAIClient(ILLMClient):
            async def generate_completion(
                self,
                prompt: str,
                system_prompt: str | None = None,
                temperature: float = 0.7,
                max_tokens: int = 4000,
            ) -> str:
                # Implementation here
                pass
        ```
    """

    @abstractmethod
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> str:
        """Generate text completion from the LLM.

        Args:
            prompt: The user prompt to send to the LLM
            system_prompt: Optional system prompt to set context and behavior
            temperature: Sampling temperature (0.0 to 2.0). Higher values make
                output more random, lower values more deterministic
            max_tokens: Maximum number of tokens to generate in the completion

        Returns:
            The generated text completion as a string

        Raises:
            LLMAuthenticationError: If authentication with the provider fails
            LLMRateLimitError: If rate limits are exceeded
            LLMTimeoutError: If the request times out
            LLMBadRequestError: If the request parameters are invalid
            LLMAPIError: For other API-related errors
            LLMTokenLimitError: If token limits are exceeded
        """

    @abstractmethod
    def generate_streaming(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> AsyncIterator[str]:
        """Stream completion tokens from the LLM in real-time.

        This method yields tokens as they are generated, enabling real-time
        display in interactive interfaces like CLI.

        Args:
            prompt: The user prompt to send to the LLM
            system_prompt: Optional system prompt to set context and behavior
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum number of tokens to generate

        Yields:
            Individual tokens or chunks of text as they are generated

        Raises:
            LLMAuthenticationError: If authentication with the provider fails
            LLMRateLimitError: If rate limits are exceeded
            LLMTimeoutError: If the request times out
            LLMBadRequestError: If the request parameters are invalid
            LLMAPIError: For other API-related errors

        Example:
            ```python
            async for token in client.generate_streaming("Write a function"):
                print(token, end="", flush=True)
            ```
        """

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in the given text.

        This method uses the provider's tokenization scheme to accurately
        count tokens, which is essential for cost estimation and context
        window validation.

        Args:
            text: The text to count tokens for

        Returns:
            The number of tokens in the text

        Example:
            ```python
            token_count = client.count_tokens("Hello, world!")
            print(f"Token count: {token_count}")
            ```
        """

    @abstractmethod
    def estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """Estimate the cost for a given token usage.

        Calculates the estimated cost in USD based on the provider's pricing
        for prompt and completion tokens.

        Args:
            prompt_tokens: Number of tokens in the prompt
            completion_tokens: Number of tokens in the completion

        Returns:
            Estimated cost in USD

        Example:
            ```python
            cost = client.estimate_cost(prompt_tokens=100, completion_tokens=200)
            print(f"Estimated cost: ${cost:.4f}")
            ```
        """


class IEmbeddingClient(ABC):
    """Abstract interface for embedding providers.

    This interface defines the contract for generating text embeddings,
    which are used for semantic code search and similarity matching.

    Example:
        ```python
        class AzureEmbeddingClient(IEmbeddingClient):
            async def embed_text(self, text: str) -> list[float]:
                # Implementation here
                pass

            @property
            def dimension(self) -> int:
                return 1536  # text-embedding-ada-002 dimension
        ```
    """

    @abstractmethod
    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding vector for a single text.

        Args:
            text: The text to generate an embedding for

        Returns:
            A list of floats representing the embedding vector

        Raises:
            LLMAuthenticationError: If authentication with the provider fails
            LLMRateLimitError: If rate limits are exceeded
            LLMTimeoutError: If the request times out
            LLMBadRequestError: If the request parameters are invalid
            LLMAPIError: For other API-related errors

        Example:
            ```python
            embedding = await client.embed_text("def hello(): pass")
            print(f"Embedding dimension: {len(embedding)}")
            ```
        """

    @abstractmethod
    async def embed_batch(
        self,
        texts: list[str],
        batch_size: int = 16,
    ) -> list[list[float]]:
        """Generate embeddings for a batch of texts.

        This method processes multiple texts efficiently by batching API
        requests, which reduces latency and API call overhead.

        Args:
            texts: List of texts to generate embeddings for
            batch_size: Number of texts to process per API call. Defaults to
                16 which is optimal for most providers

        Returns:
            List of embedding vectors, one for each input text, in the same
            order as the input

        Raises:
            LLMAuthenticationError: If authentication with the provider fails
            LLMRateLimitError: If rate limits are exceeded
            LLMTimeoutError: If the request times out
            LLMBadRequestError: If the request parameters are invalid
            LLMAPIError: For other API-related errors

        Example:
            ```python
            texts = ["def foo(): pass", "class Bar: pass", "import os"]
            embeddings = await client.embed_batch(texts, batch_size=16)
            print(f"Generated {len(embeddings)} embeddings")
            ```
        """

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Get the dimension size of the embedding vectors.

        Returns:
            The number of dimensions in the embedding vectors produced by
            this client. For example, text-embedding-ada-002 returns 1536
            dimensions.

        Example:
            ```python
            dim = client.dimension
            print(f"Embedding dimension: {dim}")
            ```
        """
