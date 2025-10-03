"""Token counting and cost estimation for Azure OpenAI operations.

This module provides accurate token counting using tiktoken and cost estimation
based on Azure OpenAI pricing for different models.
"""

from __future__ import annotations

import logging
from enum import Enum

import tiktoken

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Supported Azure OpenAI model types."""

    GPT_4 = "gpt-4"
    GPT_4_32K = "gpt-4-32k"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4O = "gpt-4o"
    GPT_35_TURBO = "gpt-3.5-turbo"


class TokenCounter:
    """Token counter for Azure OpenAI models.

    Provides accurate token counting using tiktoken, cost estimation based on
    Azure OpenAI pricing, and context window validation.

    Attributes:
        model: The model type to use for token counting
        encoding: The tiktoken encoding for the model
    """

    # Context window limits for different models
    CONTEXT_LIMITS = {
        ModelType.GPT_4: 8192,
        ModelType.GPT_4_32K: 32768,
        ModelType.GPT_4_TURBO: 128000,
        ModelType.GPT_4O: 128000,
        ModelType.GPT_35_TURBO: 16385,
    }

    # Azure OpenAI pricing per 1K tokens (USD)
    # Note: Update these values based on current Azure pricing
    PRICING = {
        ModelType.GPT_4: {"prompt": 0.03, "completion": 0.06},
        ModelType.GPT_4_32K: {"prompt": 0.06, "completion": 0.12},
        ModelType.GPT_4_TURBO: {"prompt": 0.01, "completion": 0.03},
        ModelType.GPT_4O: {"prompt": 0.005, "completion": 0.015},
        ModelType.GPT_35_TURBO: {"prompt": 0.0015, "completion": 0.002},
    }

    def __init__(self, model: str = "gpt-4") -> None:
        """Initialize token counter for specified model.

        Args:
            model: Model name (e.g., "gpt-4", "gpt-4-turbo")

        Raises:
            ValueError: If model is not supported
        """
        self.model = self._parse_model_type(model)
        self.encoding = self._get_encoding()

    def _parse_model_type(self, model: str) -> ModelType:
        """Parse model string to ModelType enum.

        Args:
            model: Model name string

        Returns:
            ModelType enum value

        Raises:
            ValueError: If model is not supported
        """
        model_lower = model.lower()

        # Map model strings to ModelType
        if "gpt-4o" in model_lower:
            return ModelType.GPT_4O
        elif "gpt-4-turbo" in model_lower or "gpt-4-1106" in model_lower:
            return ModelType.GPT_4_TURBO
        elif "gpt-4-32k" in model_lower:
            return ModelType.GPT_4_32K
        elif "gpt-4" in model_lower:
            return ModelType.GPT_4
        elif "gpt-3.5-turbo" in model_lower:
            return ModelType.GPT_35_TURBO
        else:
            raise ValueError(
                f"Unsupported model: {model}. "
                f"Supported models: {[m.value for m in ModelType]}"
            )

    def _get_encoding(self) -> tiktoken.Encoding:
        """Get tiktoken encoding for the model.

        Returns:
            tiktoken.Encoding instance

        Raises:
            RuntimeError: If encoding cannot be loaded
        """
        try:
            # Use cl100k_base encoding for GPT-4 and GPT-3.5-turbo models
            return tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.error(f"Failed to load tiktoken encoding: {e}")
            raise RuntimeError(f"Failed to initialize token encoding: {e}") from e

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens in the text

        Raises:
            ValueError: If text is None or encoding fails
        """
        if text is None:
            raise ValueError("Text cannot be None")

        if not text:
            return 0

        try:
            tokens = self.encoding.encode(text)
            return len(tokens)
        except Exception as e:
            logger.error(f"Failed to count tokens: {e}")
            raise ValueError(f"Failed to encode text: {e}") from e

    def count_messages_tokens(
        self,
        messages: list[dict[str, str]],
    ) -> int:
        """Count tokens in a list of chat messages.

        This accounts for the special tokens used in chat format.

        Args:
            messages: List of message dicts with 'role' and 'content' keys

        Returns:
            Total number of tokens including chat formatting

        Raises:
            ValueError: If messages format is invalid
        """
        if not messages:
            return 0

        try:
            # Tokens per message and per name (based on OpenAI's token counting)
            tokens_per_message = 3  # <|start|>role/name\n{content}<|end|>\n
            tokens_per_name = 1

            num_tokens = 0
            for message in messages:
                if not isinstance(message, dict):
                    raise ValueError("Each message must be a dictionary")

                if "role" not in message or "content" not in message:
                    raise ValueError("Each message must have 'role' and 'content'")

                num_tokens += tokens_per_message
                num_tokens += self.count_tokens(message["content"])
                num_tokens += self.count_tokens(message["role"])

                if "name" in message:
                    num_tokens += tokens_per_name
                    num_tokens += self.count_tokens(message["name"])

            num_tokens += 3  # Every reply is primed with <|start|>assistant<|message|>
            return num_tokens

        except Exception as e:
            logger.error(f"Failed to count message tokens: {e}")
            raise ValueError(f"Failed to count message tokens: {e}") from e

    def estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int = 0,
    ) -> float:
        """Estimate cost for token usage based on Azure pricing.

        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens (default: 0)

        Returns:
            Estimated cost in USD

        Raises:
            ValueError: If token counts are negative
        """
        if prompt_tokens < 0 or completion_tokens < 0:
            raise ValueError("Token counts cannot be negative")

        pricing = self.PRICING[self.model]

        prompt_cost = (prompt_tokens / 1000) * pricing["prompt"]
        completion_cost = (completion_tokens / 1000) * pricing["completion"]

        return prompt_cost + completion_cost

    def validate_context_window(
        self,
        prompt_tokens: int,
        max_completion_tokens: int = 4000,
    ) -> tuple[bool, str]:
        """Validate that tokens fit within model's context window.

        Args:
            prompt_tokens: Number of tokens in the prompt
            max_completion_tokens: Maximum tokens for completion (default: 4000)

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if tokens fit within context window
            - error_message: Empty string if valid, error description if invalid

        Raises:
            ValueError: If token counts are negative
        """
        if prompt_tokens < 0 or max_completion_tokens < 0:
            raise ValueError("Token counts cannot be negative")

        context_limit = self.CONTEXT_LIMITS[self.model]
        total_tokens = prompt_tokens + max_completion_tokens

        if total_tokens > context_limit:
            error_msg = (
                f"Token limit exceeded: {total_tokens} tokens "
                f"(prompt: {prompt_tokens}, max completion: {max_completion_tokens}) "
                f"exceeds {self.model.value} context window of {context_limit} tokens. "
                f"Reduce prompt size or max_completion_tokens."
            )
            logger.warning(error_msg)
            return False, error_msg

        return True, ""

    def get_context_limit(self) -> int:
        """Get the context window limit for the current model.

        Returns:
            Maximum number of tokens for the model's context window
        """
        return self.CONTEXT_LIMITS[self.model]

    def get_pricing(self) -> dict[str, float]:
        """Get pricing information for the current model.

        Returns:
            Dictionary with 'prompt' and 'completion' pricing per 1K tokens
        """
        return self.PRICING[self.model].copy()

    def get_model_name(self) -> str:
        """Get the model name.

        Returns:
            Model name string
        """
        return self.model.value
