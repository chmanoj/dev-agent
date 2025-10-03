"""Azure OpenAI service for dev-agent.

DEPRECATED: This service is maintained for backward compatibility only.
New code should use AzureOpenAIClient and AzureEmbeddingClient directly
from dev_agent.llm module.
"""

from __future__ import annotations

import asyncio
import logging
import warnings
from typing import Any

from openai import AsyncAzureOpenAI, AzureOpenAI
from pydantic import BaseModel, Field

from dev_agent.errors.exceptions import ConfigurationError, ServiceError
from dev_agent.errors.llm_exceptions import (
    LLMAPIError,
    LLMAuthenticationError,
    LLMBadRequestError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from dev_agent.llm.azure_client import AzureOpenAIClient
from dev_agent.llm.embeddings import AzureEmbeddingClient
from dev_agent.models.llm_config import AzureOpenAIConfig

logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    """Represents a chat message."""

    role: str = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Content of the message")


class ChatResponse(BaseModel):
    """Response from chat completion."""

    content: str = Field(..., description="Generated content")
    model: str = Field(..., description="Model used for generation")
    usage: dict[str, int] = Field(
        default_factory=dict, description="Token usage information"
    )
    finish_reason: str | None = Field(None, description="Reason for completion finish")


class EmbeddingResponse(BaseModel):
    """Response from embedding generation."""

    embeddings: list[list[float]] = Field(..., description="Generated embeddings")
    model: str = Field(..., description="Model used for embeddings")
    usage: dict[str, int] = Field(
        default_factory=dict, description="Token usage information"
    )


class AzureOpenAIService:
    """Service for interacting with Azure OpenAI.

    DEPRECATED: This service is maintained for backward compatibility only.
    New code should use AzureOpenAIClient and AzureEmbeddingClient directly
    from dev_agent.llm module.

    This service now wraps the new LLM client implementations internally
    while maintaining the same public API for backward compatibility.
    """

    def __init__(self, config: AzureOpenAIConfig | None = None):
        """Initialize Azure OpenAI service.

        Args:
            config: Azure OpenAI configuration

        Raises:
            ConfigurationError: If configuration is invalid
        """
        # Issue deprecation warning
        warnings.warn(
            "AzureOpenAIService is deprecated. Use AzureOpenAIClient and "
            "AzureEmbeddingClient from dev_agent.llm module instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        self.config = config or AzureOpenAIConfig()
        self._client: AzureOpenAI | None = None
        self._async_client: AsyncAzureOpenAI | None = None

        # Initialize new LLM clients
        self._llm_client: AzureOpenAIClient | None = None
        self._embedding_client: AzureEmbeddingClient | None = None

        # Load configuration from environment if not provided
        self._load_env_config()
        self._validate_config()

    def _load_env_config(self) -> None:
        """Load configuration from environment variables."""
        # Note: Environment variable loading is now handled by AzureOpenAIConfig
        # This method is kept for backward compatibility but is mostly a no-op
        pass

    def _validate_config(self) -> None:
        """Validate configuration.

        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not self.config.api_key:
            raise ConfigurationError(
                "Azure OpenAI API key is required. Set AZURE_OPENAI_API_KEY environment variable "
                "or provide it in configuration."
            )

        if not self.config.endpoint:
            raise ConfigurationError(
                "Azure OpenAI endpoint is required. Set AZURE_OPENAI_ENDPOINT environment variable "
                "or provide it in configuration."
            )

        if not self.config.endpoint.startswith(("http://", "https://")):
            raise ConfigurationError(
                f"Invalid Azure OpenAI endpoint format: {self.config.endpoint}. "
                "Must start with http:// or https://"
            )

    @property
    def client(self) -> AzureOpenAI:
        """Get synchronous Azure OpenAI client."""
        if self._client is None:
            self._client = AzureOpenAI(
                api_key=self.config.api_key,
                azure_endpoint=self.config.endpoint,
                api_version=self.config.api_version,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            )
        return self._client

    @property
    def async_client(self) -> AsyncAzureOpenAI:
        """Get asynchronous Azure OpenAI client."""
        if self._async_client is None:
            self._async_client = AsyncAzureOpenAI(
                api_key=self.config.api_key,
                azure_endpoint=self.config.endpoint,
                api_version=self.config.api_version,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            )
        return self._async_client

    @property
    def llm_client(self) -> AzureOpenAIClient:
        """Get the new LLM client implementation.

        Returns:
            AzureOpenAIClient instance for completions
        """
        if self._llm_client is None:
            self._llm_client = AzureOpenAIClient(self.config)
        return self._llm_client

    @property
    def embedding_client(self) -> AzureEmbeddingClient:
        """Get the new embedding client implementation.

        Returns:
            AzureEmbeddingClient instance for embeddings
        """
        if self._embedding_client is None:
            self._embedding_client = AzureEmbeddingClient(self.config)
        return self._embedding_client

    def chat_completion(
        self,
        messages: list[ChatMessage | dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> ChatResponse:
        """Generate chat completion.

        Args:
            messages: List of chat messages
            model: Model to use (defaults to config.deployment_name)
            temperature: Sampling temperature (defaults to config.temperature)
            max_tokens: Maximum tokens to generate (defaults to config.max_tokens)
            **kwargs: Additional parameters for the API call

        Returns:
            Chat completion response

        Raises:
            ServiceError: If the API call fails
        """
        try:
            # Convert messages to dict format if needed
            formatted_messages = []
            for msg in messages:
                if isinstance(msg, ChatMessage):
                    formatted_messages.append(
                        {"role": msg.role, "content": msg.content}
                    )
                else:
                    formatted_messages.append(msg)

            response = self.client.chat.completions.create(
                model=model or self.config.deployment_name,
                messages=formatted_messages,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
                **kwargs,
            )

            choice = response.choices[0]
            usage_dict = response.usage.model_dump() if response.usage else {}

            return ChatResponse(
                content=choice.message.content or "",
                model=response.model,
                usage=usage_dict,
                finish_reason=choice.finish_reason,
            )

        except (
            LLMAuthenticationError,
            LLMRateLimitError,
            LLMTimeoutError,
            LLMBadRequestError,
            LLMAPIError,
        ) as e:
            # Convert LLM exceptions to ServiceError for backward compatibility
            logger.error(f"Azure OpenAI chat completion failed: {e}")
            raise ServiceError(f"Chat completion failed: {e}") from e
        except Exception as e:
            logger.error(f"Azure OpenAI chat completion failed: {e}")
            raise ServiceError(f"Chat completion failed: {e}") from e

    async def async_chat_completion(
        self,
        messages: list[ChatMessage | dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> ChatResponse:
        """Generate chat completion asynchronously.

        Args:
            messages: List of chat messages
            model: Model to use (defaults to config.deployment_name)
            temperature: Sampling temperature (defaults to config.temperature)
            max_tokens: Maximum tokens to generate (defaults to config.max_tokens)
            **kwargs: Additional parameters for the API call

        Returns:
            Chat completion response

        Raises:
            ServiceError: If the API call fails
        """
        try:
            # Convert messages to dict format if needed
            formatted_messages = []
            for msg in messages:
                if isinstance(msg, ChatMessage):
                    formatted_messages.append(
                        {"role": msg.role, "content": msg.content}
                    )
                else:
                    formatted_messages.append(msg)

            response = await self.async_client.chat.completions.create(
                model=model or self.config.deployment_name,
                messages=formatted_messages,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
                **kwargs,
            )

            choice = response.choices[0]
            usage_dict = response.usage.model_dump() if response.usage else {}

            return ChatResponse(
                content=choice.message.content or "",
                model=response.model,
                usage=usage_dict,
                finish_reason=choice.finish_reason,
            )

        except (
            LLMAuthenticationError,
            LLMRateLimitError,
            LLMTimeoutError,
            LLMBadRequestError,
            LLMAPIError,
        ) as e:
            # Convert LLM exceptions to ServiceError for backward compatibility
            logger.error(f"Azure OpenAI async chat completion failed: {e}")
            raise ServiceError(f"Async chat completion failed: {e}") from e
        except Exception as e:
            logger.error(f"Azure OpenAI async chat completion failed: {e}")
            raise ServiceError(f"Async chat completion failed: {e}") from e

    def generate_embeddings(
        self,
        texts: list[str],
        model: str | None = None,
        **kwargs: Any,
    ) -> EmbeddingResponse:
        """Generate embeddings for texts.

        Args:
            texts: List of texts to embed
            model: Model to use (defaults to config.embedding_deployment)
            **kwargs: Additional parameters for the API call

        Returns:
            Embedding response

        Raises:
            ServiceError: If the API call fails
        """
        try:
            response = self.client.embeddings.create(
                model=model or self.config.embedding_deployment,
                input=texts,
                **kwargs,
            )

            embeddings = [item.embedding for item in response.data]
            usage_dict = response.usage.model_dump() if response.usage else {}

            return EmbeddingResponse(
                embeddings=embeddings,
                model=response.model,
                usage=usage_dict,
            )

        except (
            LLMAuthenticationError,
            LLMRateLimitError,
            LLMTimeoutError,
            LLMBadRequestError,
            LLMAPIError,
        ) as e:
            # Convert LLM exceptions to ServiceError for backward compatibility
            logger.error(f"Azure OpenAI embedding generation failed: {e}")
            raise ServiceError(f"Embedding generation failed: {e}") from e
        except Exception as e:
            logger.error(f"Azure OpenAI embedding generation failed: {e}")
            raise ServiceError(f"Embedding generation failed: {e}") from e

    async def async_generate_embeddings(
        self,
        texts: list[str],
        model: str | None = None,
        **kwargs: Any,
    ) -> EmbeddingResponse:
        """Generate embeddings for texts asynchronously.

        Args:
            texts: List of texts to embed
            model: Model to use (defaults to config.embedding_deployment)
            **kwargs: Additional parameters for the API call

        Returns:
            Embedding response

        Raises:
            ServiceError: If the API call fails
        """
        try:
            response = await self.async_client.embeddings.create(
                model=model or self.config.embedding_deployment,
                input=texts,
                **kwargs,
            )

            embeddings = [item.embedding for item in response.data]
            usage_dict = response.usage.model_dump() if response.usage else {}

            return EmbeddingResponse(
                embeddings=embeddings,
                model=response.model,
                usage=usage_dict,
            )

        except (
            LLMAuthenticationError,
            LLMRateLimitError,
            LLMTimeoutError,
            LLMBadRequestError,
            LLMAPIError,
        ) as e:
            # Convert LLM exceptions to ServiceError for backward compatibility
            logger.error(f"Azure OpenAI async embedding generation failed: {e}")
            raise ServiceError(f"Async embedding generation failed: {e}") from e
        except Exception as e:
            logger.error(f"Azure OpenAI async embedding generation failed: {e}")
            raise ServiceError(f"Async embedding generation failed: {e}") from e

    def test_connection(self) -> bool:
        """Test connection to Azure OpenAI.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Test with a simple chat completion
            self.chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
            )
            logger.info("Azure OpenAI connection test successful")
            return True
        except Exception as e:
            logger.error(f"Azure OpenAI connection test failed: {e}")
            return False

    async def async_test_connection(self) -> bool:
        """Test connection to Azure OpenAI asynchronously.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Test with a simple chat completion
            await self.async_chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
            )
            logger.info("Azure OpenAI async connection test successful")
            return True
        except Exception as e:
            logger.error(f"Azure OpenAI async connection test failed: {e}")
            return False

    def get_available_models(self) -> list[str]:
        """Get list of available models.

        Returns:
            List of available model names

        Note:
            Azure OpenAI doesn't provide a direct way to list models,
            so this returns the configured models.
        """
        return [self.config.deployment_name, self.config.embedding_deployment]

    def close(self) -> None:
        """Close the clients."""
        if self._client:
            self._client.close()
        if self._async_client:
            # Store task reference to avoid warning (intentionally not awaited)
            _task = asyncio.create_task(self._async_client.close())  # noqa: RUF006
