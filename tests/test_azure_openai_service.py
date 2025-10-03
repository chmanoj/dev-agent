"""Tests for Azure OpenAI service.

This test suite verifies backward compatibility of the deprecated
AzureOpenAIService class, which now wraps the new LLM client implementations.
"""

import warnings
from unittest.mock import AsyncMock, Mock, patch

import pytest
from pydantic import ValidationError

from dev_agent.errors.exceptions import ServiceError
from dev_agent.models.llm_config import AzureOpenAIConfig
from dev_agent.services.azure_openai_service import (
    AzureOpenAIService,
    ChatMessage,
    ChatResponse,
    EmbeddingResponse,
)


class TestAzureOpenAIService:
    """Test Azure OpenAI service functionality."""

    def test_init_with_valid_config(self):
        """Test initialization with valid configuration."""
        config = AzureOpenAIConfig(
            api_key="test-key",
            endpoint="https://test.openai.azure.com/",
            api_version="2024-02-01",
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )

        # Should issue deprecation warning
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            service = AzureOpenAIService(config)

            # Verify deprecation warning was issued
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message).lower()

        assert service.config.api_key.get_secret_value() == "test-key"
        assert service.config.endpoint == "https://test.openai.azure.com/"

    def test_init_with_env_variables(self):
        """Test initialization with environment variables."""
        with patch.dict(
            "os.environ",
            {
                "AZURE_OPENAI_API_KEY": "env-key",
                "AZURE_OPENAI_ENDPOINT": "https://env.openai.azure.com/",
                "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-35-turbo",
                "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
            },
        ):
            config = AzureOpenAIConfig(
                api_key="env-key",
                endpoint="https://env.openai.azure.com/",
                deployment_name="gpt-35-turbo",
                embedding_deployment="text-embedding-ada-002",
            )

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                service = AzureOpenAIService(config)

            assert service.config.api_key.get_secret_value() == "env-key"
            assert service.config.endpoint == "https://env.openai.azure.com/"
            assert service.config.deployment_name == "gpt-35-turbo"

    def test_init_missing_api_key(self):
        """Test initialization fails with missing API key."""
        # Pydantic will raise ValidationError for missing required fields
        with pytest.raises(ValidationError):
            AzureOpenAIConfig(
                endpoint="https://test.openai.azure.com/",
                deployment_name="gpt-4",
                embedding_deployment="text-embedding-ada-002",
            )

    def test_init_missing_endpoint(self):
        """Test initialization fails with missing endpoint."""
        # Pydantic will raise ValidationError for missing required fields
        with pytest.raises(ValidationError):
            AzureOpenAIConfig(
                api_key="test-key",
                deployment_name="gpt-4",
                embedding_deployment="text-embedding-ada-002",
            )

    def test_init_invalid_endpoint_format(self):
        """Test initialization fails with invalid endpoint format."""
        # Pydantic will raise ValidationError for invalid endpoint format
        with pytest.raises(ValidationError):
            AzureOpenAIConfig(
                api_key="test-key",
                endpoint="invalid-endpoint",
                deployment_name="gpt-4",
                embedding_deployment="text-embedding-ada-002",
            )

    @patch("dev_agent.services.azure_openai_service.AzureOpenAI")
    def test_chat_completion_success(self, mock_azure_openai):
        """Test successful chat completion."""
        # Setup mock
        mock_client = Mock()
        mock_azure_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4"
        mock_response.usage.model_dump.return_value = {"total_tokens": 50}

        mock_client.chat.completions.create.return_value = mock_response

        # Test
        config = AzureOpenAIConfig(
            api_key="test-key",
            endpoint="https://test.openai.azure.com/",
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            service = AzureOpenAIService(config)

        messages = [ChatMessage(role="user", content="Hello")]
        response = service.chat_completion(messages)

        assert isinstance(response, ChatResponse)
        assert response.content == "Test response"
        assert response.model == "gpt-4"
        assert response.finish_reason == "stop"
        assert response.usage == {"total_tokens": 50}

    @patch("dev_agent.services.azure_openai_service.AzureOpenAI")
    def test_chat_completion_with_dict_messages(self, mock_azure_openai):
        """Test chat completion with dictionary messages."""
        # Setup mock
        mock_client = Mock()
        mock_azure_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4"
        mock_response.usage.model_dump.return_value = {}

        mock_client.chat.completions.create.return_value = mock_response

        # Test
        config = AzureOpenAIConfig(
            api_key="test-key",
            endpoint="https://test.openai.azure.com/",
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            service = AzureOpenAIService(config)

        messages = [{"role": "user", "content": "Hello"}]
        service.chat_completion(messages)

        # Verify the call was made with correct format
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]["messages"] == [{"role": "user", "content": "Hello"}]

    @patch("dev_agent.services.azure_openai_service.AzureOpenAI")
    def test_chat_completion_failure(self, mock_azure_openai):
        """Test chat completion failure handling."""
        # Setup mock to raise exception
        mock_client = Mock()
        mock_azure_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        # Test
        config = AzureOpenAIConfig(
            api_key="test-key",
            endpoint="https://test.openai.azure.com/",
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            service = AzureOpenAIService(config)

        messages = [ChatMessage(role="user", content="Hello")]

        with pytest.raises(ServiceError, match="Chat completion failed"):
            service.chat_completion(messages)

    @patch("dev_agent.services.azure_openai_service.AzureOpenAI")
    def test_generate_embeddings_success(self, mock_azure_openai):
        """Test successful embedding generation."""
        # Setup mock
        mock_client = Mock()
        mock_azure_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.1, 0.2, 0.3]),
            Mock(embedding=[0.4, 0.5, 0.6]),
        ]
        mock_response.model = "text-embedding-ada-002"
        mock_response.usage.model_dump.return_value = {"total_tokens": 10}

        mock_client.embeddings.create.return_value = mock_response

        # Test
        config = AzureOpenAIConfig(
            api_key="test-key",
            endpoint="https://test.openai.azure.com/",
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            service = AzureOpenAIService(config)

        texts = ["Hello", "World"]
        response = service.generate_embeddings(texts)

        assert isinstance(response, EmbeddingResponse)
        assert len(response.embeddings) == 2
        assert response.embeddings[0] == [0.1, 0.2, 0.3]
        assert response.embeddings[1] == [0.4, 0.5, 0.6]
        assert response.model == "text-embedding-ada-002"
        assert response.usage == {"total_tokens": 10}

    @patch("dev_agent.services.azure_openai_service.AzureOpenAI")
    def test_generate_embeddings_failure(self, mock_azure_openai):
        """Test embedding generation failure handling."""
        # Setup mock to raise exception
        mock_client = Mock()
        mock_azure_openai.return_value = mock_client
        mock_client.embeddings.create.side_effect = Exception("API Error")

        # Test
        config = AzureOpenAIConfig(
            api_key="test-key",
            endpoint="https://test.openai.azure.com/",
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            service = AzureOpenAIService(config)

        texts = ["Hello", "World"]

        with pytest.raises(ServiceError, match="Embedding generation failed"):
            service.generate_embeddings(texts)

    @patch("dev_agent.services.azure_openai_service.AzureOpenAI")
    def test_test_connection_success(self, mock_azure_openai):
        """Test successful connection test."""
        # Setup mock
        mock_client = Mock()
        mock_azure_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4"
        mock_response.usage.model_dump.return_value = {}

        mock_client.chat.completions.create.return_value = mock_response

        # Test
        config = AzureOpenAIConfig(
            api_key="test-key",
            endpoint="https://test.openai.azure.com/",
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            service = AzureOpenAIService(config)

        result = service.test_connection()
        assert result is True

    @patch("dev_agent.services.azure_openai_service.AzureOpenAI")
    def test_test_connection_failure(self, mock_azure_openai):
        """Test connection test failure."""
        # Setup mock to raise exception
        mock_client = Mock()
        mock_azure_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("Connection Error")

        # Test
        config = AzureOpenAIConfig(
            api_key="test-key",
            endpoint="https://test.openai.azure.com/",
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            service = AzureOpenAIService(config)

        result = service.test_connection()
        assert result is False

    def test_get_available_models(self):
        """Test getting available models."""
        config = AzureOpenAIConfig(
            api_key="test-key",
            endpoint="https://test.openai.azure.com/",
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            service = AzureOpenAIService(config)

        models = service.get_available_models()
        assert "gpt-4" in models
        assert "text-embedding-ada-002" in models

    def test_deprecation_warning(self):
        """Test that deprecation warning is issued on initialization."""
        config = AzureOpenAIConfig(
            api_key="test-key",
            endpoint="https://test.openai.azure.com/",
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            AzureOpenAIService(config)

            # Verify deprecation warning
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "AzureOpenAIService is deprecated" in str(w[0].message)
            assert "AzureOpenAIClient" in str(w[0].message)
            assert "AzureEmbeddingClient" in str(w[0].message)

    def test_new_client_properties(self):
        """Test that new LLM client properties are accessible."""
        config = AzureOpenAIConfig(
            api_key="test-key",
            endpoint="https://test.openai.azure.com/",
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            service = AzureOpenAIService(config)

        # Test that new client properties exist and are accessible
        assert hasattr(service, "llm_client")
        assert hasattr(service, "embedding_client")

        # Access the properties (they should be created lazily)
        llm_client = service.llm_client
        embedding_client = service.embedding_client

        assert llm_client is not None
        assert embedding_client is not None

        # Verify they're the same instance on subsequent access (cached)
        assert service.llm_client is llm_client
        assert service.embedding_client is embedding_client


class TestAsyncAzureOpenAIService:
    """Test async Azure OpenAI service functionality."""

    @pytest.mark.asyncio
    @patch("dev_agent.services.azure_openai_service.AsyncAzureOpenAI")
    async def test_async_chat_completion_success(self, mock_async_azure_openai):
        """Test successful async chat completion."""
        # Setup mock
        mock_client = AsyncMock()
        mock_async_azure_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Async response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4"
        mock_response.usage.model_dump.return_value = {"total_tokens": 25}

        mock_client.chat.completions.create.return_value = mock_response

        # Test
        config = AzureOpenAIConfig(
            api_key="test-key",
            endpoint="https://test.openai.azure.com/",
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            service = AzureOpenAIService(config)

        messages = [{"role": "user", "content": "Hello async"}]
        response = await service.async_chat_completion(messages)

        assert isinstance(response, ChatResponse)
        assert response.content == "Async response"
        assert response.model == "gpt-4"
        assert response.usage == {"total_tokens": 25}

    @pytest.mark.asyncio
    @patch("dev_agent.services.azure_openai_service.AsyncAzureOpenAI")
    async def test_async_generate_embeddings_success(self, mock_async_azure_openai):
        """Test successful async embedding generation."""
        # Setup mock
        mock_client = AsyncMock()
        mock_async_azure_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.7, 0.8, 0.9])]
        mock_response.model = "text-embedding-ada-002"
        mock_response.usage.model_dump.return_value = {"total_tokens": 5}

        mock_client.embeddings.create.return_value = mock_response

        # Test
        config = AzureOpenAIConfig(
            api_key="test-key",
            endpoint="https://test.openai.azure.com/",
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            service = AzureOpenAIService(config)

        texts = ["Async embedding test"]
        response = await service.async_generate_embeddings(texts)

        assert isinstance(response, EmbeddingResponse)
        assert len(response.embeddings) == 1
        assert response.embeddings[0] == [0.7, 0.8, 0.9]
        assert response.model == "text-embedding-ada-002"

    @pytest.mark.asyncio
    @patch("dev_agent.services.azure_openai_service.AsyncAzureOpenAI")
    async def test_async_test_connection_success(self, mock_async_azure_openai):
        """Test successful async connection test."""
        # Setup mock
        mock_client = AsyncMock()
        mock_async_azure_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4"
        mock_response.usage.model_dump.return_value = {}

        mock_client.chat.completions.create.return_value = mock_response

        # Test
        config = AzureOpenAIConfig(
            api_key="test-key",
            endpoint="https://test.openai.azure.com/",
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            service = AzureOpenAIService(config)

        result = await service.async_test_connection()
        assert result is True


class TestChatMessage:
    """Test ChatMessage model."""

    def test_chat_message_creation(self):
        """Test ChatMessage creation."""
        message = ChatMessage(role="user", content="Hello")
        assert message.role == "user"
        assert message.content == "Hello"

    def test_chat_message_validation(self):
        """Test ChatMessage validation."""
        # Valid message
        message = ChatMessage(role="system", content="You are helpful")
        assert message.role == "system"

        # Empty content should be allowed
        message = ChatMessage(role="assistant", content="")
        assert message.content == ""


class TestChatResponse:
    """Test ChatResponse model."""

    def test_chat_response_creation(self):
        """Test ChatResponse creation."""
        response = ChatResponse(
            content="Test response",
            model="gpt-4",
            usage={"total_tokens": 50},
            finish_reason="stop",
        )

        assert response.content == "Test response"
        assert response.model == "gpt-4"
        assert response.usage == {"total_tokens": 50}
        assert response.finish_reason == "stop"

    def test_chat_response_defaults(self):
        """Test ChatResponse with default values."""
        response = ChatResponse(content="Test", model="gpt-4")

        assert response.usage == {}
        assert response.finish_reason is None


class TestEmbeddingResponse:
    """Test EmbeddingResponse model."""

    def test_embedding_response_creation(self):
        """Test EmbeddingResponse creation."""
        response = EmbeddingResponse(
            embeddings=[[0.1, 0.2], [0.3, 0.4]],
            model="text-embedding-ada-002",
            usage={"total_tokens": 10},
        )

        assert len(response.embeddings) == 2
        assert response.embeddings[0] == [0.1, 0.2]
        assert response.model == "text-embedding-ada-002"
        assert response.usage == {"total_tokens": 10}

    def test_embedding_response_defaults(self):
        """Test EmbeddingResponse with default values."""
        response = EmbeddingResponse(embeddings=[[0.1, 0.2]], model="test-model")

        assert response.usage == {}
