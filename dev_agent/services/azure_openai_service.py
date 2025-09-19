"""Azure OpenAI service for dev-agent."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional, Union

from openai import AsyncAzureOpenAI, AzureOpenAI
from pydantic import BaseModel, Field

from dev_agent.config.config_manager import AzureOpenAIConfig
from dev_agent.errors.exceptions import ConfigurationError, ServiceError

logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    """Represents a chat message."""
    
    role: str = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Content of the message")


class ChatResponse(BaseModel):
    """Response from chat completion."""
    
    content: str = Field(..., description="Generated content")
    model: str = Field(..., description="Model used for generation")
    usage: Dict[str, int] = Field(default_factory=dict, description="Token usage information")
    finish_reason: Optional[str] = Field(None, description="Reason for completion finish")


class EmbeddingResponse(BaseModel):
    """Response from embedding generation."""
    
    embeddings: List[List[float]] = Field(..., description="Generated embeddings")
    model: str = Field(..., description="Model used for embeddings")
    usage: Dict[str, int] = Field(default_factory=dict, description="Token usage information")


class AzureOpenAIService:
    """Service for interacting with Azure OpenAI."""
    
    def __init__(self, config: Optional[AzureOpenAIConfig] = None):
        """Initialize Azure OpenAI service.
        
        Args:
            config: Azure OpenAI configuration
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        self.config = config or AzureOpenAIConfig()
        self._client: Optional[AzureOpenAI] = None
        self._async_client: Optional[AsyncAzureOpenAI] = None
        
        # Load configuration from environment if not provided
        self._load_env_config()
        self._validate_config()
    
    def _load_env_config(self) -> None:
        """Load configuration from environment variables."""
        if not self.config.api_key:
            self.config.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        
        if not self.config.endpoint:
            self.config.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        
        # Allow override of other settings via environment
        if api_version := os.getenv("AZURE_OPENAI_API_VERSION"):
            self.config.api_version = api_version
        
        if chat_model := os.getenv("AZURE_OPENAI_CHAT_MODEL"):
            self.config.chat_model = chat_model
        
        if embedding_model := os.getenv("AZURE_OPENAI_EMBEDDING_MODEL"):
            self.config.embedding_model = embedding_model
    
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
    
    def chat_completion(
        self,
        messages: List[Union[ChatMessage, Dict[str, str]]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> ChatResponse:
        """Generate chat completion.
        
        Args:
            messages: List of chat messages
            model: Model to use (defaults to config.chat_model)
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
                    formatted_messages.append({"role": msg.role, "content": msg.content})
                else:
                    formatted_messages.append(msg)
            
            response = self.client.chat.completions.create(
                model=model or self.config.chat_model,
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
            
        except Exception as e:
            logger.error(f"Azure OpenAI chat completion failed: {e}")
            raise ServiceError(f"Chat completion failed: {e}") from e
    
    async def async_chat_completion(
        self,
        messages: List[Union[ChatMessage, Dict[str, str]]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> ChatResponse:
        """Generate chat completion asynchronously.
        
        Args:
            messages: List of chat messages
            model: Model to use (defaults to config.chat_model)
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
                    formatted_messages.append({"role": msg.role, "content": msg.content})
                else:
                    formatted_messages.append(msg)
            
            response = await self.async_client.chat.completions.create(
                model=model or self.config.chat_model,
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
            
        except Exception as e:
            logger.error(f"Azure OpenAI async chat completion failed: {e}")
            raise ServiceError(f"Async chat completion failed: {e}") from e
    
    def generate_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> EmbeddingResponse:
        """Generate embeddings for texts.
        
        Args:
            texts: List of texts to embed
            model: Model to use (defaults to config.embedding_model)
            **kwargs: Additional parameters for the API call
            
        Returns:
            Embedding response
            
        Raises:
            ServiceError: If the API call fails
        """
        try:
            response = self.client.embeddings.create(
                model=model or self.config.embedding_model,
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
            
        except Exception as e:
            logger.error(f"Azure OpenAI embedding generation failed: {e}")
            raise ServiceError(f"Embedding generation failed: {e}") from e
    
    async def async_generate_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> EmbeddingResponse:
        """Generate embeddings for texts asynchronously.
        
        Args:
            texts: List of texts to embed
            model: Model to use (defaults to config.embedding_model)
            **kwargs: Additional parameters for the API call
            
        Returns:
            Embedding response
            
        Raises:
            ServiceError: If the API call fails
        """
        try:
            response = await self.async_client.embeddings.create(
                model=model or self.config.embedding_model,
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
            response = self.chat_completion(
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
            response = await self.async_chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
            )
            logger.info("Azure OpenAI async connection test successful")
            return True
        except Exception as e:
            logger.error(f"Azure OpenAI async connection test failed: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available models.
        
        Returns:
            List of available model names
            
        Note:
            Azure OpenAI doesn't provide a direct way to list models,
            so this returns the configured models.
        """
        return [self.config.chat_model, self.config.embedding_model]
    
    def close(self) -> None:
        """Close the clients."""
        if self._client:
            self._client.close()
        if self._async_client:
            asyncio.create_task(self._async_client.close())