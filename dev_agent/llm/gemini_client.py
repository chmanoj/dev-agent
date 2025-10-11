"""Google Gemini client implementation with retry logic and error handling.

This module provides a robust implementation of the ILLMClient interface for
Google Gemini, including async API calls, retry logic with exponential backoff,
streaming support, and comprehensive error handling.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import google.generativeai as genai
import tiktoken
from google.api_core import exceptions as google_exceptions
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

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from dev_agent.models.llm_config import GeminiConfig

logger = logging.getLogger(__name__)


class GeminiClient(ILLMClient):
    """Google Gemini client with retry logic and error handling.

    This client implements the ILLMClient interface for Google Gemini, providing:
    - Async API calls using google-generativeai SDK
    - Exponential backoff retry for transient errors
    - Streaming support for real-time token generation
    - Token counting and cost estimation
    - Comprehensive error handling with custom exceptions

    Attributes:
        config: Gemini configuration
        model: Gemini GenerativeModel instance
        tokenizer: tiktoken encoder for token counting (fallback)

    Example:
        ```python
        config = GeminiConfig(
            api_key="AIza...",
            model_name="gemini-pro",
            temperature=0.7,
        )
        client = GeminiClient(config)

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

    def __init__(self, config: GeminiConfig) -> None:
        """Initialize Gemini client.

        Args:
            config: Gemini configuration with credentials and settings
        """
        self.config = config

        # Configure Gemini API
        genai.configure(api_key=config.get_api_key_value())

        # Initialize the generative model
        self.model = genai.GenerativeModel(
            model_name=config.model_name,
            generation_config=genai.types.GenerationConfig(
                temperature=config.temperature,
                top_p=config.top_p,
                top_k=config.top_k,
                max_output_tokens=config.max_output_tokens,
            ),
            safety_settings=self._build_safety_settings(),
        )

        # Initialize tiktoken encoder for token counting fallback
        # Use GPT-4 encoding as a reasonable approximation for Gemini
        self.tokenizer = tiktoken.encoding_for_model("gpt-4")

        logger.info(
            f"Initialized Gemini client for model: {config.model_name} "
            f"with temperature: {config.temperature}"
        )

    def _build_safety_settings(self) -> list[dict[str, str]] | None:
        """Build safety settings from configuration.

        Returns:
            List of safety settings or None if not configured
        """
        if not self.config.safety_settings:
            # Use permissive defaults for code generation
            return [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]

        safety_settings = []
        for category, threshold in self.config.safety_settings.items():
            safety_settings.append({
                "category": category,
                "threshold": threshold,
            })

        return safety_settings

    async def generate_completion(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> str:
        """Generate text completion from Gemini.

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
        # Build the full prompt
        full_prompt = self._build_prompt(prompt, system_prompt)

        # Count tokens and validate limits
        prompt_tokens = self.count_tokens(full_prompt)
        
        # Gemini Pro has a context window of ~30k tokens
        max_context_tokens = 30000
        if prompt_tokens > max_context_tokens:
            raise LLMTokenLimitError(
                f"Prompt contains {prompt_tokens} tokens, exceeds Gemini limit of {max_context_tokens}",
                "Reduce the prompt size or split into multiple requests"
            )

        # Estimate cost
        estimated_cost = self.estimate_cost(prompt_tokens, max_tokens)
        logger.info(
            f"Generating completion: {prompt_tokens} prompt tokens, "
            f"estimated cost: ${estimated_cost:.4f}"
        )

        # Make API call with retry logic
        try:
            response = await self._call_completion_with_retry(
                prompt=full_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Extract text from response, handling blocked responses
            try:
                response_text = response.text
                if not response_text:
                    logger.warning("Gemini returned empty response")
                    return ""
            except ValueError as e:
                # Handle blocked responses (finish_reason = 2 or other safety blocks)
                logger.warning(f"Gemini response was blocked or invalid: {e}")
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'finish_reason'):
                        logger.warning(f"Response finish_reason: {candidate.finish_reason}")
                return ""

            # Log actual usage (Gemini doesn't provide detailed token counts in response)
            completion_tokens = self.count_tokens(response_text)
            actual_cost = self.estimate_cost(prompt_tokens, completion_tokens)
            logger.info(
                f"Completion generated: ~{prompt_tokens + completion_tokens} total tokens, "
                f"actual cost: ${actual_cost:.4f}"
            )

            return response_text

        except (
            google_exceptions.PermissionDenied,
            google_exceptions.ResourceExhausted,
            google_exceptions.DeadlineExceeded,
            google_exceptions.InvalidArgument,
            google_exceptions.GoogleAPIError,
        ):
            # These are handled by _call_completion_with_retry and converted to custom exceptions
            raise

    def _build_prompt(self, prompt: str, system_prompt: str | None = None) -> str:
        """Build the full prompt from user and system prompts.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt

        Returns:
            Combined prompt string
        """
        if system_prompt:
            return f"{system_prompt}\n\n{prompt}"
        return prompt

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((
            google_exceptions.ResourceExhausted,
            google_exceptions.DeadlineExceeded,
        )),
        reraise=True,
    )
    async def _call_completion_with_retry(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> genai.types.GenerateContentResponse:
        """Call Gemini completion API with retry logic.

        This method is decorated with tenacity retry logic to handle transient
        errors like rate limits and timeouts.

        Args:
            prompt: Full prompt to send to Gemini
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Gemini completion response

        Raises:
            LLMAuthenticationError: If authentication fails
            LLMRateLimitError: If rate limits are exceeded after retries
            LLMTimeoutError: If request times out after retries
            LLMBadRequestError: If request parameters are invalid
            LLMAPIError: For other API errors
        """
        try:
            # Update generation config for this specific request
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                top_p=self.config.top_p,
                top_k=self.config.top_k,
                max_output_tokens=min(max_tokens, self.config.max_output_tokens),
            )

            response = await self.model.generate_content_async(
                contents=prompt,
                generation_config=generation_config,
            )

            return response

        except google_exceptions.PermissionDenied as e:
            logger.error(f"Gemini authentication failed: {e}")
            raise LLMAuthenticationError(
                "Failed to authenticate with Google Gemini API",
                "Check that GEMINI_API_KEY is set correctly. "
                "Get your API key at: https://makersuite.google.com/app/apikey"
            ) from e

        except google_exceptions.ResourceExhausted as e:
            logger.warning(f"Gemini rate limit hit: {e}")
            # This will be retried by tenacity
            raise

        except google_exceptions.DeadlineExceeded as e:
            logger.warning(f"Gemini request timed out: {e}")
            # This will be retried by tenacity
            raise

        except google_exceptions.InvalidArgument as e:
            logger.error(f"Invalid request to Gemini: {e}")
            raise LLMBadRequestError(
                f"Invalid request parameters: {e}",
                "Check that model name and parameters are correct"
            ) from e

        except google_exceptions.GoogleAPIError as e:
            logger.error(f"Gemini API error: {e}")
            raise LLMAPIError(
                f"Gemini service error: {e}",
                "Check Gemini service status or try again later"
            ) from e

    async def generate_streaming(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> AsyncIterator[str]:
        """Stream completion tokens from Gemini in real-time.

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
        # Build the full prompt
        full_prompt = self._build_prompt(prompt, system_prompt)

        # Count tokens and validate limits
        prompt_tokens = self.count_tokens(full_prompt)
        
        # Gemini Pro has a context window of ~30k tokens
        max_context_tokens = 30000
        if prompt_tokens > max_context_tokens:
            raise LLMTokenLimitError(
                f"Prompt contains {prompt_tokens} tokens, exceeds Gemini limit of {max_context_tokens}",
                "Reduce the prompt size or split into multiple requests"
            )

        logger.info(f"Starting streaming completion: {prompt_tokens} prompt tokens")

        # Make streaming API call
        try:
            # Update generation config for this specific request
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                top_p=self.config.top_p,
                top_k=self.config.top_k,
                max_output_tokens=min(max_tokens, self.config.max_output_tokens),
            )

            response = await self.model.generate_content_async(
                contents=full_prompt,
                generation_config=generation_config,
                stream=True,
            )

            # Yield tokens as they arrive
            async for chunk in response:
                if chunk.text:
                    yield chunk.text

        except google_exceptions.PermissionDenied as e:
            logger.error(f"Gemini authentication failed during streaming: {e}")
            raise LLMAuthenticationError(
                "Failed to authenticate with Google Gemini API",
                "Check that GEMINI_API_KEY is set correctly. "
                "Get your API key at: https://makersuite.google.com/app/apikey"
            ) from e

        except google_exceptions.ResourceExhausted as e:
            logger.error(f"Gemini rate limit hit during streaming: {e}")
            raise LLMRateLimitError(
                "Rate limit exceeded during streaming",
            ) from e

        except google_exceptions.DeadlineExceeded as e:
            logger.error(f"Gemini request timed out during streaming: {e}")
            raise LLMTimeoutError(
                "Request timed out during streaming",
            ) from e

        except google_exceptions.InvalidArgument as e:
            logger.error(f"Invalid request to Gemini during streaming: {e}")
            raise LLMBadRequestError(
                f"Invalid request parameters: {e}",
                "Check that model name and parameters are correct"
            ) from e

        except google_exceptions.GoogleAPIError as e:
            logger.error(f"Gemini API error during streaming: {e}")
            raise LLMAPIError(
                f"Gemini service error: {e}",
                "Check Gemini service status or try again later"
            ) from e

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in the given text.

        Uses Gemini's token counting API if available, falls back to tiktoken
        with GPT-4 encoding as an approximation.

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
        try:
            # Try to use Gemini's token counting API
            response = genai.count_tokens(
                model=self.config.model_name,
                contents=text,
            )
            return response.total_tokens
        except Exception as e:
            # Fall back to tiktoken approximation
            logger.debug(f"Gemini token counting failed, using tiktoken fallback: {e}")
            return len(self.tokenizer.encode(text))

    def estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """Estimate the cost for a given token usage.

        Calculates the estimated cost in USD based on Gemini pricing.
        
        Current Gemini Pro pricing (as of 2024):
        - Input: $0.50 per 1M tokens
        - Output: $1.50 per 1M tokens

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
        # Gemini Pro pricing (per 1M tokens)
        input_cost_per_1m = 0.50
        output_cost_per_1m = 1.50

        # Calculate costs
        input_cost = (prompt_tokens / 1_000_000) * input_cost_per_1m
        output_cost = (completion_tokens / 1_000_000) * output_cost_per_1m

        return input_cost + output_cost