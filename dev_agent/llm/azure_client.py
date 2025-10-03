"""Azure OpenAI client implementation with retry logic and error handling.

This module provides a robust implementation of the ILLMClient interface for
Azure OpenAI, including async API calls, retry logic with exponential backoff,
streaming support, and comprehensive error handling.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from openai import (
    APIError,
    APITimeoutError,
    AsyncAzureOpenAI,
    AuthenticationError,
    BadRequestError,
    RateLimitError,
)
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from dev_agent.errors.llm_exceptions import (
    LLMAPIError,
    LLMAuthenticationError,
    LLMBadRequestError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMTokenLimitError,
)
from dev_agent.llm.base import ILLMClient
from dev_agent.llm.token_counter import TokenCounter

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from openai.types.chat import ChatCompletion

    from dev_agent.models.llm_config import AzureOpenAIConfig

logger = logging.getLogger(__name__)


class AzureOpenAIClient(ILLMClient):
    """Azure OpenAI client with retry logic and error handling.

    This client implements the ILLMClient interface for Azure OpenAI, providing:
    - Async API calls using AsyncAzureOpenAI
    - Exponential backoff retry for transient errors
    - Streaming support for real-time token generation
    - Token counting and cost estimation
    - Comprehensive error handling with custom exceptions

    Attributes:
        config: Azure OpenAI configuration
        client: AsyncAzureOpenAI client instance
        token_counter: Token counter for the deployment model

    Example:
        ```python
        config = AzureOpenAIConfig(
            endpoint="https://my-resource.openai.azure.com/",
            api_key="sk-...",
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )
        client = AzureOpenAIClient(config)

        # Generate completion
        response = await client.generate_completion(
            prompt="Write a Python function",
            system_prompt="You are a Python expert",
        )

        # Stream completion
        async for token in client.generate_streaming("Write a function"):
            print(token, end="", flush=True)
        ```
    """

    def __init__(
        self,
        config: AzureOpenAIConfig,
        client: AsyncAzureOpenAI | None = None,
    ) -> None:
        """Initialize Azure OpenAI client.

        Args:
            config: Azure OpenAI configuration with credentials and settings
            client: Optional AsyncAzureOpenAI client for testing (dependency injection)
        """
        self.config = config

        # Initialize Azure OpenAI client
        if client is None:
            self.client = AsyncAzureOpenAI(
                api_key=config.api_key.get_secret_value(),
                api_version=config.api_version,
                azure_endpoint=config.endpoint,
                timeout=config.timeout,
                max_retries=0,  # We handle retries ourselves with tenacity
            )
        else:
            self.client = client

        # Initialize token counter for the deployment model
        self.token_counter = TokenCounter(model=config.deployment_name)

        logger.info(
            f"Initialized Azure OpenAI client for deployment: {config.deployment_name}"
        )

    async def generate_completion(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> str:
        """Generate text completion from Azure OpenAI.

        This method validates token limits, makes the API call with retry logic,
        and handles errors appropriately.

        Args:
            prompt: The user prompt to send to the LLM
            system_prompt: Optional system prompt to set context and behavior
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum number of tokens to generate

        Returns:
            The generated text completion as a string

        Raises:
            LLMAuthenticationError: If authentication fails
            LLMRateLimitError: If rate limits are exceeded (after retries)
            LLMTimeoutError: If the request times out (after retries)
            LLMBadRequestError: If request parameters are invalid
            LLMAPIError: For other API-related errors
            LLMTokenLimitError: If token limits are exceeded
        """
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Count tokens and validate context window
        prompt_tokens = self.token_counter.count_messages_tokens(messages)
        is_valid, error_msg = self.token_counter.validate_context_window(
            prompt_tokens=prompt_tokens,
            max_completion_tokens=max_tokens,
        )

        if not is_valid:
            raise LLMTokenLimitError(error_msg)

        # Estimate cost
        estimated_cost = self.token_counter.estimate_cost(
            prompt_tokens=prompt_tokens,
            completion_tokens=max_tokens,
        )
        logger.info(
            f"Generating completion: {prompt_tokens} prompt tokens, "
            f"estimated cost: ${estimated_cost:.4f}"
        )

        # Make API call with retry logic
        try:
            response = await self._call_completion_with_retry(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Log actual usage
            if response.usage:
                actual_cost = self.token_counter.estimate_cost(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                )
                logger.info(
                    f"Completion generated: {response.usage.total_tokens} total tokens, "
                    f"actual cost: ${actual_cost:.4f}"
                )

            return response.choices[0].message.content or ""

        except (AuthenticationError, RateLimitError, APITimeoutError, BadRequestError, APIError):
            # These are handled by _call_completion_with_retry and converted to custom exceptions
            # The exceptions are already converted in _call_completion_with_retry
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((RateLimitError, APITimeoutError)),
        reraise=True,
    )
    async def _call_completion_with_retry(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> ChatCompletion:
        """Call Azure OpenAI completion API with retry logic.

        This method is decorated with tenacity retry logic to handle transient
        errors like rate limits and timeouts.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            OpenAI completion response

        Raises:
            LLMAuthenticationError: If authentication fails
            LLMRateLimitError: If rate limits are exceeded after retries
            LLMTimeoutError: If request times out after retries
            LLMBadRequestError: If request parameters are invalid
            LLMAPIError: For other API errors
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.config.deployment_name,
                messages=messages,  # type: ignore[arg-type]
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response

        except AuthenticationError as e:
            logger.error(f"Azure OpenAI authentication failed: {e}")
            raise LLMAuthenticationError(
                "Failed to authenticate with Azure OpenAI",
                "Check that AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT are set correctly",
            ) from e

        except RateLimitError as e:
            logger.warning(f"Azure OpenAI rate limit hit: {e}")
            # This will be retried by tenacity
            raise

        except APITimeoutError as e:
            logger.warning(f"Azure OpenAI request timed out: {e}")
            # This will be retried by tenacity
            raise

        except BadRequestError as e:
            logger.error(f"Invalid request to Azure OpenAI: {e}")
            raise LLMBadRequestError(
                f"Invalid request parameters: {e}",
                "Check that deployment name and parameters are correct",
            ) from e

        except APIError as e:
            logger.error(f"Azure OpenAI API error: {e}")
            raise LLMAPIError(
                f"Azure OpenAI service error: {e}",
                "Check Azure OpenAI service status at status.azure.com",
            ) from e

    async def generate_streaming(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> AsyncIterator[str]:
        """Stream completion tokens from Azure OpenAI in real-time.

        This method yields tokens as they are generated, enabling real-time
        display in interactive interfaces.

        Args:
            prompt: The user prompt to send to the LLM
            system_prompt: Optional system prompt to set context and behavior
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum number of tokens to generate

        Yields:
            Individual tokens or chunks of text as they are generated

        Raises:
            LLMAuthenticationError: If authentication fails
            LLMRateLimitError: If rate limits are exceeded
            LLMTimeoutError: If the request times out
            LLMBadRequestError: If request parameters are invalid
            LLMAPIError: For other API-related errors
            LLMTokenLimitError: If token limits are exceeded
        """
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Count tokens and validate context window
        prompt_tokens = self.token_counter.count_messages_tokens(messages)
        is_valid, error_msg = self.token_counter.validate_context_window(
            prompt_tokens=prompt_tokens,
            max_completion_tokens=max_tokens,
        )

        if not is_valid:
            raise LLMTokenLimitError(error_msg)

        logger.info(f"Starting streaming completion: {prompt_tokens} prompt tokens")

        # Make streaming API call
        try:
            response = await self.client.chat.completions.create(
                model=self.config.deployment_name,
                messages=messages,  # type: ignore[arg-type]
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            # Yield tokens as they arrive
            async for chunk in response:  # type: ignore[union-attr]
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except AuthenticationError as e:
            logger.error(f"Azure OpenAI authentication failed during streaming: {e}")
            raise LLMAuthenticationError(
                "Failed to authenticate with Azure OpenAI",
                "Check that AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT are set correctly",
            ) from e

        except RateLimitError as e:
            logger.error(f"Azure OpenAI rate limit hit during streaming: {e}")
            raise LLMRateLimitError(
                "Rate limit exceeded during streaming",
            ) from e

        except APITimeoutError as e:
            logger.error(f"Azure OpenAI request timed out during streaming: {e}")
            raise LLMTimeoutError(
                "Request timed out during streaming",
            ) from e

        except BadRequestError as e:
            logger.error(f"Invalid request to Azure OpenAI during streaming: {e}")
            raise LLMBadRequestError(
                f"Invalid request parameters: {e}",
                "Check that deployment name and parameters are correct",
            ) from e

        except APIError as e:
            logger.error(f"Azure OpenAI API error during streaming: {e}")
            raise LLMAPIError(
                f"Azure OpenAI service error: {e}",
                "Check Azure OpenAI service status at status.azure.com",
            ) from e

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in the given text.

        Uses tiktoken with the model's encoding to accurately count tokens.

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
        return self.token_counter.count_tokens(text)

    def estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """Estimate the cost for a given token usage.

        Calculates the estimated cost in USD based on Azure OpenAI pricing
        for the configured deployment model.

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
        return self.token_counter.estimate_cost(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
