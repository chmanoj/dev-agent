"""Token counting and cost estimation for LLM operations.

This module provides token counting and cost estimation for different LLM providers
including Azure OpenAI and Google Gemini.
"""

from __future__ import annotations

import logging
from enum import Enum

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Supported model types across providers."""

    # Azure OpenAI models
    GPT_4 = "gpt-4"
    GPT_4_32K = "gpt-4-32k"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4O = "gpt-4o"
    GPT_35_TURBO = "gpt-3.5-turbo"

    # Gemini models
    GEMINI_PRO = "gemini-pro"
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_2_5_FLASH_LITE = "gemini-2.5-flash-lite"
    GEMINI_2_5_PRO = "gemini-2.5-pro"


class TokenCounter:
    """Token counter for multiple LLM providers.

    Provides token counting and cost estimation for Azure OpenAI and Gemini models.
    Uses tiktoken for OpenAI models and approximation for Gemini models.

    Attributes:
        model: The model type to use for token counting
        provider: The LLM provider (azure_openai or gemini)
        encoding: The tiktoken encoding for OpenAI models (None for Gemini)
    """

    # Context window limits for different models
    CONTEXT_LIMITS = {
        # Azure OpenAI
        ModelType.GPT_4: 8192,
        ModelType.GPT_4_32K: 32768,
        ModelType.GPT_4_TURBO: 128000,
        ModelType.GPT_4O: 128000,
        ModelType.GPT_35_TURBO: 16385,
        # Gemini
        ModelType.GEMINI_PRO: 32768,
        ModelType.GEMINI_2_5_FLASH: 1048576,  # 1M tokens
        ModelType.GEMINI_2_5_FLASH_LITE: 1048576,  # 1M tokens
        ModelType.GEMINI_2_5_PRO: 2097152,  # 2M tokens
    }

    # Pricing per 1K tokens (USD) - approximate values
    PRICING = {
        # Azure OpenAI pricing
        ModelType.GPT_4: {"prompt": 0.03, "completion": 0.06},
        ModelType.GPT_4_32K: {"prompt": 0.06, "completion": 0.12},
        ModelType.GPT_4_TURBO: {"prompt": 0.01, "completion": 0.03},
        ModelType.GPT_4O: {"prompt": 0.005, "completion": 0.015},
        ModelType.GPT_35_TURBO: {"prompt": 0.0015, "completion": 0.002},
        # Gemini pricing (approximate)
        ModelType.GEMINI_PRO: {"prompt": 0.0005, "completion": 0.0015},
        ModelType.GEMINI_2_5_FLASH: {"prompt": 0.000075, "completion": 0.0003},
        ModelType.GEMINI_2_5_FLASH_LITE: {"prompt": 0.000075, "completion": 0.0003},
        ModelType.GEMINI_2_5_PRO: {"prompt": 0.00125, "completion": 0.005},
    }

    def __init__(self, model: str = "gpt-4") -> None:
        """Initialize token counter for specified model.

        Args:
            model: Model name (e.g., "gpt-4", "gemini-2.5-flash")
        """
        try:
            self.model = self._parse_model_type(model)
            self.provider = self._get_provider()
            self.encoding = (
                self._get_encoding() if self.provider == "azure_openai" else None
            )
        except ValueError as e:
            # For unsupported models, use a default configuration
            logger.warning(
                f"Unsupported model '{model}': {e}. Using default configuration."
            )
            self.model = ModelType.GPT_4
            self.provider = "azure_openai"
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

        # Azure OpenAI models
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

        # Gemini models
        elif "gemini-2.5-flash-lite" in model_lower:
            return ModelType.GEMINI_2_5_FLASH_LITE
        elif "gemini-2.5-flash" in model_lower:
            return ModelType.GEMINI_2_5_FLASH
        elif "gemini-2.5-pro" in model_lower:
            return ModelType.GEMINI_2_5_PRO
        elif "gemini-pro" in model_lower:
            return ModelType.GEMINI_PRO

        else:
            raise ValueError(
                f"Unsupported model: {model}. "
                f"Supported models: {[m.value for m in ModelType]}"
            )

    def _get_provider(self) -> str:
        """Get the provider for the current model.

        Returns:
            Provider name ("azure_openai" or "gemini")
        """
        if self.model in [
            ModelType.GPT_4,
            ModelType.GPT_4_32K,
            ModelType.GPT_4_TURBO,
            ModelType.GPT_4O,
            ModelType.GPT_35_TURBO,
        ]:
            return "azure_openai"
        else:
            return "gemini"

    def _get_encoding(self):
        """Get tiktoken encoding for Azure OpenAI models.

        Returns:
            tiktoken.Encoding instance for OpenAI models, None for others

        Raises:
            RuntimeError: If encoding cannot be loaded for OpenAI models
        """
        if self.provider != "azure_openai":
            return None

        try:
            import tiktoken

            # Use cl100k_base encoding for GPT-4 and GPT-3.5-turbo models
            return tiktoken.get_encoding("cl100k_base")
        except ImportError:
            logger.warning(
                "tiktoken not available, using approximation for token counting"
            )
            return None
        except Exception as e:
            logger.error(f"Failed to load tiktoken encoding: {e}")
            raise RuntimeError(f"Failed to initialize token encoding: {e}") from e

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using provider-specific methods.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens in the text

        Raises:
            ValueError: If text is None
        """
        if text is None:
            raise ValueError("Text cannot be None")

        if not text:
            return 0

        try:
            if self.provider == "azure_openai" and self.encoding:
                # Use tiktoken for accurate OpenAI token counting
                tokens = self.encoding.encode(text)
                return len(tokens)
            else:
                # Use approximation for Gemini or when tiktoken is not available
                # Rough approximation: 1 token ≈ 4 characters for English text
                return max(1, len(text) // 4)
        except Exception as e:
            logger.warning(
                f"Failed to count tokens accurately, using approximation: {e}"
            )
            # Fallback to character-based approximation
            return max(1, len(text) // 4)

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

    def get_provider_enum(self) -> LLMProvider:
        """Get the provider as enum.

        Returns:
            LLMProvider enum value
        """
        from ..models.enums import LLMProvider
        if self.provider == "azure_openai":
            return LLMProvider.AZURE_OPENAI
        else:
            return LLMProvider.GEMINI
