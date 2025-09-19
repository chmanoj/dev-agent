"""Tests for Azure OpenAI service."""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from dev_agent.config.config_manager import AzureOpenAIConfig
from dev_agent.services.azure_openai_service import (
    AzureOpenAIService,
    ChatMessage,
    ChatResponse,
    EmbeddingResponse,
)
from dev_agent.errors.exceptions import ConfigurationError, ServiceError


class TestAzureOpenAIService:
    """Test Azure OpenAI service functionality."""
    
    def test_init_with_valid_config(self):
        """Test initialization with valid configuration."""
        config = AzureOpenAIConfig(
            api_key="test-key",
            endpoint="https://test.openai.azure.com/",
            api_version="2024-02-01",
            chat_model="gpt-4",
            embedding_model="text-embedding-ada-002",
        )
        
        service = AzureOpenAIService(config)
        assert service.config.api_key == "test-key"
        assert service.config.endpoint == "https://test.openai.azure.com/"
    
    def test_init_with_env_variables(self):
        """Test initialization with environment variables."""
        with patch.dict('os.environ', {
            'AZURE_OPENAI_API_KEY': 'env-key',
            'AZURE_OPENAI_ENDPOINT': 'https://env.openai.azure.com/',
            'AZURE_OPENAI_CHAT_MODEL': 'gpt-35-turbo',
        }):
            config = AzureOpenAIConfig()
            service = AzureOpenAIService(config)
            
            assert service.config.api_key == "env-key"
            assert service.config.endpoint == "https://env.openai.azure.com/"
            assert service.config.chat_model == "gpt-35-turbo"
    
    def test_init_missing_api_key(self):
        """Test initialization fails with missing API key."""
        config = AzureOpenAIConfig(
            endpoint="https://test.openai.azure.com/",
        )
        
        with pytest.raises(ConfigurationError, match="API key is required"):
            AzureOpenAIService(config)
    
    def test_init_missing_endpoint(self):
        """Test initialization fails with missing endpoint."""
        config = AzureOpenAIConfig(
            api_key="test-key",
        )
        
        with pytest.raises(ConfigurationError, match="endpoint is required"):
            AzureOpenAIService(config)
    
    def test_init_invalid_endpoint_format(self):
        """Test initialization fails with invalid endpoint format."""
        config = AzureOpenAIConfig(
            api_key="test-key",
            endpoint="invalid-endpoint",
        )
        
        with pytest.raises(ConfigurationError, match="Invalid.*endpoint format"):
            AzureOpenAIService(config)
    
    @patch('dev_agent.services.azure_openai_service.AzureOpenAI')
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
        )
        service = AzureOpenAIService(config)
        
        messages = [ChatMessage(role="user", content="Hello")]
        response = service.chat_completion(messages)
        
        assert isinstance(response, ChatResponse)
        assert response.content == "Test response"
        assert response.model == "gpt-4"
        assert response.finish_reason == "stop"
        assert response.usage == {"total_tokens": 50}
    
    @patch('dev_agent.services.azure_openai_service.AzureOpenAI')
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
        )
        service = AzureOpenAIService(config)
        
        messages = [{"role": "user", "content": "Hello"}]
        response = service.chat_completion(messages)
        
        # Verify the call was made with correct format
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]['messages'] == [{"role": "user", "content": "Hello"}]
    
    @patch('dev_agent.services.azure_openai_service.AzureOpenAI')
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
        )
        service = AzureOpenAIService(config)
        
        messages = [ChatMessage(role="user", content="Hello")]
        
        with pytest.raises(ServiceError, match="Chat completion failed"):
            service.chat_completion(messages)
    
    @patch('dev_agent.services.azure_openai_service.AzureOpenAI')
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
        )
        service = AzureOpenAIService(config)
        
        texts = ["Hello", "World"]
        response = service.generate_embeddings(texts)
        
        assert isinstance(response, EmbeddingResponse)
        assert len(response.embeddings) == 2
        assert response.embeddings[0] == [0.1, 0.2, 0.3]
        assert response.embeddings[1] == [0.4, 0.5, 0.6]
        assert response.model == "text-embedding-ada-002"
        assert response.usage == {"total_tokens": 10}
    
    @patch('dev_agent.services.azure_openai_service.AzureOpenAI')
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
        )
        service = AzureOpenAIService(config)
        
        texts = ["Hello", "World"]
        
        with pytest.raises(ServiceError, match="Embedding generation failed"):
            service.generate_embeddings(texts)
    
    @patch('dev_agent.services.azure_openai_service.AzureOpenAI')
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
        )
        service = AzureOpenAIService(config)
        
        result = service.test_connection()
        assert result is True
    
    @patch('dev_agent.services.azure_openai_service.AzureOpenAI')
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
        )
        service = AzureOpenAIService(config)
        
        result = service.test_connection()
        assert result is False
    
    def test_get_available_models(self):
        """Test getting available models."""
        config = AzureOpenAIConfig(
            api_key="test-key",
            endpoint="https://test.openai.azure.com/",
            chat_model="gpt-4",
            embedding_model="text-embedding-ada-002",
        )
        service = AzureOpenAIService(config)
        
        models = service.get_available_models()
        assert "gpt-4" in models
        assert "text-embedding-ada-002" in models


class TestAsyncAzureOpenAIService:
    """Test async Azure OpenAI service functionality."""
    
    @pytest.mark.asyncio
    @patch('dev_agent.services.azure_openai_service.AsyncAzureOpenAI')
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
        )
        service = AzureOpenAIService(config)
        
        messages = [{"role": "user", "content": "Hello async"}]
        response = await service.async_chat_completion(messages)
        
        assert isinstance(response, ChatResponse)
        assert response.content == "Async response"
        assert response.model == "gpt-4"
        assert response.usage == {"total_tokens": 25}
    
    @pytest.mark.asyncio
    @patch('dev_agent.services.azure_openai_service.AsyncAzureOpenAI')
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
        )
        service = AzureOpenAIService(config)
        
        texts = ["Async embedding test"]
        response = await service.async_generate_embeddings(texts)
        
        assert isinstance(response, EmbeddingResponse)
        assert len(response.embeddings) == 1
        assert response.embeddings[0] == [0.7, 0.8, 0.9]
        assert response.model == "text-embedding-ada-002"
    
    @pytest.mark.asyncio
    @patch('dev_agent.services.azure_openai_service.AsyncAzureOpenAI')
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
        )
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
            finish_reason="stop"
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
            usage={"total_tokens": 10}
        )
        
        assert len(response.embeddings) == 2
        assert response.embeddings[0] == [0.1, 0.2]
        assert response.model == "text-embedding-ada-002"
        assert response.usage == {"total_tokens": 10}
    
    def test_embedding_response_defaults(self):
        """Test EmbeddingResponse with default values."""
        response = EmbeddingResponse(
            embeddings=[[0.1, 0.2]],
            model="test-model"
        )
        
        assert response.usage == {}