"""Unit tests for LLM factory functions.

This module tests the factory functions for creating LLM and embedding clients,
including provider selection, credential validation, and error handling.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr

from dev_agent.llm import (
    create_embedding_client,
    create_llm_client,
    get_preferred_provider,
    validate_provider_credentials,
)
from dev_agent.llm.azure_client import AzureOpenAIClient
from dev_agent.llm.embeddings import AzureEmbeddingClient
from dev_agent.models.enums import LLMProvider
from dev_agent.models.llm_config import AzureOpenAIConfig, GeminiConfig


class TestGetPreferredProvider:
    """Test provider auto-detection from environment variables."""

    def test_default_provider_azure_openai(self):
        """Test that Azure OpenAI is the default provider."""
        with patch.dict(os.environ, {}, clear=True):
            provider = get_preferred_provider()
            assert provider == LLMProvider.AZURE_OPENAI

    def test_azure_provider_variants(self):
        """Test various Azure provider environment variable values."""
        test_cases = [
            ("azure", LLMProvider.AZURE_OPENAI),
            ("azure_openai", LLMProvider.AZURE_OPENAI),
            ("AZURE", LLMProvider.AZURE_OPENAI),
            ("Azure_OpenAI", LLMProvider.AZURE_OPENAI),
        ]

        for env_value, expected_provider in test_cases:
            with patch.dict(os.environ, {"PREFERRED_LLM_PROVIDER": env_value}):
                provider = get_preferred_provider()
                assert provider == expected_provider

    def test_gemini_provider_variants(self):
        """Test various Gemini provider environment variable values."""
        test_cases = [
            ("gemini", LLMProvider.GEMINI),
            ("google", LLMProvider.GEMINI),
            ("google_gemini", LLMProvider.GEMINI),
            ("GEMINI", LLMProvider.GEMINI),
            ("Google", LLMProvider.GEMINI),
        ]

        for env_value, expected_provider in test_cases:
            with patch.dict(os.environ, {"PREFERRED_LLM_PROVIDER": env_value}):
                provider = get_preferred_provider()
                assert provider == expected_provider

    def test_unknown_provider_defaults_to_azure(self):
        """Test that unknown provider values default to Azure OpenAI."""
        with patch.dict(os.environ, {"PREFERRED_LLM_PROVIDER": "unknown_provider"}):
            provider = get_preferred_provider()
            assert provider == LLMProvider.AZURE_OPENAI


class TestValidateProviderCredentials:
    """Test credential validation for different providers."""

    def test_azure_openai_valid_credentials_api_key(self):
        """Test Azure OpenAI credential validation with API key."""
        env_vars = {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "test-api-key",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            is_valid, error = validate_provider_credentials(LLMProvider.AZURE_OPENAI)
            assert is_valid
            assert error == ""

    def test_azure_openai_valid_credentials_bearer_token(self):
        """Test Azure OpenAI credential validation with bearer token."""
        env_vars = {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_TOKEN": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            is_valid, error = validate_provider_credentials(LLMProvider.AZURE_OPENAI)
            assert is_valid
            assert error == ""

    def test_azure_openai_valid_credentials_chat_deployment_alias(self):
        """Test Azure OpenAI credential validation with AZURE_CHAT_DEPLOYMENT_NAME alias."""
        env_vars = {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "test-api-key",
            "AZURE_CHAT_DEPLOYMENT_NAME": "gpt-4",  # Using alias
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            is_valid, error = validate_provider_credentials(LLMProvider.AZURE_OPENAI)
            assert is_valid
            assert error == ""

    def test_azure_openai_missing_endpoint(self):
        """Test Azure OpenAI credential validation with missing endpoint."""
        env_vars = {
            "AZURE_OPENAI_API_KEY": "test-api-key",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            is_valid, error = validate_provider_credentials(LLMProvider.AZURE_OPENAI)
            assert not is_valid
            assert "AZURE_OPENAI_ENDPOINT" in error

    def test_azure_openai_missing_credentials(self):
        """Test Azure OpenAI credential validation with missing credentials."""
        env_vars = {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            is_valid, error = validate_provider_credentials(LLMProvider.AZURE_OPENAI)
            assert not is_valid
            assert "AZURE_OPENAI_API_KEY" in error
            assert "AZURE_OPENAI_TOKEN" in error

    def test_azure_openai_missing_deployment(self):
        """Test Azure OpenAI credential validation with missing deployment."""
        env_vars = {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "test-api-key",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            is_valid, error = validate_provider_credentials(LLMProvider.AZURE_OPENAI)
            assert not is_valid
            assert "AZURE_OPENAI_DEPLOYMENT_NAME" in error

    def test_azure_openai_missing_embedding_deployment(self):
        """Test Azure OpenAI credential validation with missing embedding deployment."""
        env_vars = {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "test-api-key",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            is_valid, error = validate_provider_credentials(LLMProvider.AZURE_OPENAI)
            assert not is_valid
            assert "AZURE_OPENAI_EMBEDDING_DEPLOYMENT" in error

    def test_gemini_valid_credentials(self):
        """Test Gemini credential validation with valid API key."""
        env_vars = {
            "GEMINI_API_KEY": "AIzaSyDaGmWKa4JsXZ-HjGw463W12aB3456cDEF",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            is_valid, error = validate_provider_credentials(LLMProvider.GEMINI)
            assert is_valid
            assert error == ""

    def test_gemini_missing_api_key(self):
        """Test Gemini credential validation with missing API key."""
        with patch.dict(os.environ, {}, clear=True):
            is_valid, error = validate_provider_credentials(LLMProvider.GEMINI)
            assert not is_valid
            assert "GEMINI_API_KEY" in error
            assert "makersuite.google.com" in error

    def test_gemini_invalid_api_key_format(self):
        """Test Gemini credential validation with invalid API key format."""
        env_vars = {
            "GEMINI_API_KEY": "invalid-api-key-format",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            is_valid, error = validate_provider_credentials(LLMProvider.GEMINI)
            assert not is_valid
            assert "Invalid Gemini API key format" in error
            assert "should start with 'AI'" in error

    def test_unsupported_provider(self):
        """Test credential validation with unsupported provider."""
        # Test with a string that doesn't map to any provider
        # This will be handled by the factory functions, not validate_provider_credentials
        # So we test with an actual enum value that's not handled
        class UnsupportedProvider:
            value = "unsupported"
        
        unsupported = UnsupportedProvider()
        is_valid, error = validate_provider_credentials(unsupported)  # type: ignore[arg-type]
        assert not is_valid
        assert "Unsupported provider" in error


class TestCreateLLMClient:
    """Test LLM client creation with different providers."""

    @patch("dev_agent.llm.validate_provider_credentials")
    @patch("dev_agent.config.config_manager.ConfigManager.load_azure_config")
    def test_create_azure_client_auto_detection(self, mock_load_azure, mock_validate):
        """Test creating Azure OpenAI client with auto-detection."""
        # Mock credential validation
        mock_validate.return_value = (True, "")
        
        # Mock Azure config
        mock_config = AzureOpenAIConfig(
            endpoint="https://test.openai.azure.com/",
            api_key=SecretStr("test-key"),
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )
        mock_load_azure.return_value = mock_config

        with patch.dict(os.environ, {"PREFERRED_LLM_PROVIDER": "azure"}):
            client = create_llm_client()
            
            assert isinstance(client, AzureOpenAIClient)
            mock_validate.assert_called_once_with(LLMProvider.AZURE_OPENAI)
            mock_load_azure.assert_called_once()

    @patch("dev_agent.llm.validate_provider_credentials")
    @patch("dev_agent.config.config_manager.ConfigManager.load_azure_config")
    def test_create_azure_client_explicit_provider(self, mock_load_azure, mock_validate):
        """Test creating Azure OpenAI client with explicit provider."""
        # Mock credential validation
        mock_validate.return_value = (True, "")
        
        # Mock Azure config
        mock_config = AzureOpenAIConfig(
            endpoint="https://test.openai.azure.com/",
            api_key=SecretStr("test-key"),
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )
        mock_load_azure.return_value = mock_config

        client = create_llm_client(provider="azure_openai")
        
        assert isinstance(client, AzureOpenAIClient)
        mock_validate.assert_called_once_with(LLMProvider.AZURE_OPENAI)
        mock_load_azure.assert_called_once()

    @patch("dev_agent.llm.validate_provider_credentials")
    def test_create_azure_client_with_config(self, mock_validate):
        """Test creating Azure OpenAI client with provided config."""
        # Mock credential validation
        mock_validate.return_value = (True, "")
        
        config = AzureOpenAIConfig(
            endpoint="https://test.openai.azure.com/",
            api_key=SecretStr("test-key"),
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )

        client = create_llm_client(provider="azure", config=config)
        
        assert isinstance(client, AzureOpenAIClient)
        mock_validate.assert_called_once_with(LLMProvider.AZURE_OPENAI)

    @patch("dev_agent.llm.validate_provider_credentials")
    @patch("dev_agent.config.config_manager.ConfigManager.load_gemini_config")
    @patch("dev_agent.llm.gemini_client.GeminiClient")
    def test_create_gemini_client_explicit_provider(self, mock_gemini_client, mock_load_gemini, mock_validate):
        """Test creating Gemini client with explicit provider."""
        # Mock credential validation
        mock_validate.return_value = (True, "")
        
        # Mock Gemini config
        mock_config = GeminiConfig(
            api_key=SecretStr("AIzaSyDaGmWKa4JsXZ-HjGw463W12aB3456cDEF"),
            model_name="gemini-pro",
        )
        mock_load_gemini.return_value = mock_config
        
        # Mock Gemini client instance
        mock_client_instance = MagicMock()
        mock_gemini_client.return_value = mock_client_instance

        client = create_llm_client(provider="gemini")
        
        assert client == mock_client_instance
        mock_validate.assert_called_once_with(LLMProvider.GEMINI)
        mock_load_gemini.assert_called_once()
        mock_gemini_client.assert_called_once_with(mock_config)

    @patch("dev_agent.llm.validate_provider_credentials")
    @patch("dev_agent.llm.gemini_client.GeminiClient")
    def test_create_gemini_client_with_config(self, mock_gemini_client, mock_validate):
        """Test creating Gemini client with provided config."""
        # Mock credential validation
        mock_validate.return_value = (True, "")
        
        # Mock Gemini client instance
        mock_client_instance = MagicMock()
        mock_gemini_client.return_value = mock_client_instance
        
        config = GeminiConfig(
            api_key=SecretStr("AIzaSyDaGmWKa4JsXZ-HjGw463W12aB3456cDEF"),
            model_name="gemini-pro",
        )

        client = create_llm_client(provider="gemini", config=config)
        
        assert client == mock_client_instance
        mock_validate.assert_called_once_with(LLMProvider.GEMINI)
        mock_gemini_client.assert_called_once_with(config)

    def test_create_client_unsupported_provider_string(self):
        """Test creating client with unsupported provider string."""
        with pytest.raises(ValueError, match="Unsupported provider: 'unsupported'"):
            create_llm_client(provider="unsupported")

    @patch("dev_agent.llm.validate_provider_credentials")
    def test_create_client_credential_validation_failure(self, mock_validate):
        """Test creating client with credential validation failure."""
        mock_validate.return_value = (False, "Missing API key")

        with pytest.raises(ValueError, match="Provider credential validation failed: Missing API key"):
            create_llm_client(provider="azure")

    @patch("dev_agent.llm.validate_provider_credentials")
    @patch("dev_agent.config.config_manager.ConfigManager.load_azure_config")
    def test_create_client_wrong_config_type(self, mock_load_azure, mock_validate):
        """Test creating client with wrong config type."""
        # Mock credential validation
        mock_validate.return_value = (True, "")
        
        # Mock Azure config loading
        mock_load_azure.return_value = AzureOpenAIConfig(
            endpoint="https://test.openai.azure.com/",
            api_key=SecretStr("test-key"),
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )

        # Try to create Azure client with Gemini config
        gemini_config = GeminiConfig(
            api_key=SecretStr("AIzaSyDaGmWKa4JsXZ-HjGw463W12aB3456cDEF"),
        )

        with pytest.raises(ValueError, match="Expected AzureOpenAIConfig for Azure OpenAI provider"):
            create_llm_client(provider="azure", config=gemini_config)

    def test_create_gemini_client_missing_dependencies(self):
        """Test creating Gemini client with missing dependencies."""
        with patch("dev_agent.llm.validate_provider_credentials", return_value=(True, "")):
            # Mock the config loading to return a proper GeminiConfig
            with patch("dev_agent.config.config_manager.ConfigManager.load_gemini_config") as mock_load:
                mock_config = GeminiConfig(
                    api_key=SecretStr("AIzaSyDaGmWKa4JsXZ-HjGw463W12aB3456cDEF"),
                )
                mock_load.return_value = mock_config
                # Mock the Gemini client import to raise ImportError
                with patch("dev_agent.llm.gemini_client.GeminiClient", side_effect=ImportError("No module named 'google.generativeai'")):
                    with pytest.raises(ImportError, match="Gemini dependencies not installed"):
                        create_llm_client(provider="gemini")


class TestCreateEmbeddingClient:
    """Test embedding client creation with different providers."""

    @patch("dev_agent.llm.validate_provider_credentials")
    @patch("dev_agent.config.config_manager.ConfigManager.load_azure_config")
    def test_create_azure_embedding_client_auto_detection(self, mock_load_azure, mock_validate):
        """Test creating Azure embedding client with auto-detection."""
        # Mock credential validation
        mock_validate.return_value = (True, "")
        
        # Mock Azure config
        mock_config = AzureOpenAIConfig(
            endpoint="https://test.openai.azure.com/",
            api_key=SecretStr("test-key"),
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )
        mock_load_azure.return_value = mock_config

        with patch.dict(os.environ, {"PREFERRED_LLM_PROVIDER": "azure"}):
            client = create_embedding_client()
            
            assert isinstance(client, AzureEmbeddingClient)
            mock_validate.assert_called_once_with(LLMProvider.AZURE_OPENAI)
            mock_load_azure.assert_called_once()

    @patch("dev_agent.llm.validate_provider_credentials")
    @patch("dev_agent.config.config_manager.ConfigManager.load_azure_config")
    def test_create_azure_embedding_client_with_cache_dir(self, mock_load_azure, mock_validate):
        """Test creating Azure embedding client with custom cache directory."""
        # Mock credential validation
        mock_validate.return_value = (True, "")
        
        # Mock Azure config
        mock_config = AzureOpenAIConfig(
            endpoint="https://test.openai.azure.com/",
            api_key=SecretStr("test-key"),
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )
        mock_load_azure.return_value = mock_config

        # Use a temporary directory that we can create
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = f"{temp_dir}/cache"
            client = create_embedding_client(provider="azure", cache_dir=cache_dir)
            
            assert isinstance(client, AzureEmbeddingClient)
            mock_validate.assert_called_once_with(LLMProvider.AZURE_OPENAI)
            mock_load_azure.assert_called_once()

    @patch("dev_agent.llm.validate_provider_credentials")
    @patch("dev_agent.config.config_manager.ConfigManager.load_gemini_config")
    @patch("dev_agent.llm.gemini_embeddings.GeminiEmbeddingClient")
    def test_create_gemini_embedding_client_explicit_provider(self, mock_gemini_client, mock_load_gemini, mock_validate):
        """Test creating Gemini embedding client with explicit provider."""
        # Mock credential validation
        mock_validate.return_value = (True, "")
        
        # Mock Gemini config
        mock_config = GeminiConfig(
            api_key=SecretStr("AIzaSyDaGmWKa4JsXZ-HjGw463W12aB3456cDEF"),
            embedding_model="embedding-001",
        )
        mock_load_gemini.return_value = mock_config
        
        # Mock Gemini client instance
        mock_client_instance = MagicMock()
        mock_gemini_client.return_value = mock_client_instance

        client = create_embedding_client(provider="gemini")
        
        assert client == mock_client_instance
        mock_validate.assert_called_once_with(LLMProvider.GEMINI)
        mock_load_gemini.assert_called_once()
        mock_gemini_client.assert_called_once_with(mock_config, cache_dir=None)

    @patch("dev_agent.llm.validate_provider_credentials")
    @patch("dev_agent.llm.gemini_embeddings.GeminiEmbeddingClient")
    def test_create_gemini_embedding_client_with_config_and_cache(self, mock_gemini_client, mock_validate):
        """Test creating Gemini embedding client with provided config and cache directory."""
        # Mock credential validation
        mock_validate.return_value = (True, "")
        
        # Mock Gemini client instance
        mock_client_instance = MagicMock()
        mock_gemini_client.return_value = mock_client_instance
        
        config = GeminiConfig(
            api_key=SecretStr("AIzaSyDaGmWKa4JsXZ-HjGw463W12aB3456cDEF"),
            embedding_model="embedding-001",
        )

        client = create_embedding_client(provider="gemini", config=config, cache_dir="/custom/cache")
        
        assert client == mock_client_instance
        mock_validate.assert_called_once_with(LLMProvider.GEMINI)
        mock_gemini_client.assert_called_once_with(config, cache_dir="/custom/cache")

    def test_create_embedding_client_unsupported_provider_string(self):
        """Test creating embedding client with unsupported provider string."""
        with pytest.raises(ValueError, match="Unsupported provider: 'unsupported'"):
            create_embedding_client(provider="unsupported")

    @patch("dev_agent.llm.validate_provider_credentials")
    def test_create_embedding_client_credential_validation_failure(self, mock_validate):
        """Test creating embedding client with credential validation failure."""
        mock_validate.return_value = (False, "Missing API key")

        with pytest.raises(ValueError, match="Provider credential validation failed: Missing API key"):
            create_embedding_client(provider="gemini")

    @patch("dev_agent.llm.validate_provider_credentials")
    @patch("dev_agent.config.config_manager.ConfigManager.load_gemini_config")
    def test_create_embedding_client_wrong_config_type(self, mock_load_gemini, mock_validate):
        """Test creating embedding client with wrong config type."""
        # Mock credential validation
        mock_validate.return_value = (True, "")
        
        # Mock Gemini config loading
        mock_load_gemini.return_value = GeminiConfig(
            api_key=SecretStr("AIzaSyDaGmWKa4JsXZ-HjGw463W12aB3456cDEF"),
        )

        # Try to create Gemini client with Azure config
        azure_config = AzureOpenAIConfig(
            endpoint="https://test.openai.azure.com/",
            api_key=SecretStr("test-key"),
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )

        with pytest.raises(ValueError, match="Expected GeminiConfig for Gemini provider"):
            create_embedding_client(provider="gemini", config=azure_config)

    def test_create_gemini_embedding_client_missing_dependencies(self):
        """Test creating Gemini embedding client with missing dependencies."""
        with patch("dev_agent.llm.validate_provider_credentials", return_value=(True, "")):
            # Mock the config loading to return a proper GeminiConfig
            with patch("dev_agent.config.config_manager.ConfigManager.load_gemini_config") as mock_load:
                mock_config = GeminiConfig(
                    api_key=SecretStr("AIzaSyDaGmWKa4JsXZ-HjGw463W12aB3456cDEF"),
                )
                mock_load.return_value = mock_config
                # Mock the Gemini embedding client import to raise ImportError
                with patch("dev_agent.llm.gemini_embeddings.GeminiEmbeddingClient", side_effect=ImportError("No module named 'google.generativeai'")):
                    with pytest.raises(ImportError, match="Gemini dependencies not installed"):
                        create_embedding_client(provider="gemini")


class TestProviderStringMapping:
    """Test provider string to enum mapping."""

    def test_azure_provider_string_variants(self):
        """Test that various Azure provider strings map correctly."""
        test_cases = [
            "azure",
            "azure_openai", 
            "AZURE",
            "Azure_OpenAI",
        ]

        for provider_str in test_cases:
            with patch("dev_agent.llm.validate_provider_credentials", return_value=(True, "")):
                with patch("dev_agent.config.config_manager.ConfigManager.load_azure_config") as mock_load:
                    mock_load.return_value = AzureOpenAIConfig(
                        endpoint="https://test.openai.azure.com/",
                        api_key=SecretStr("test-key"),
                        deployment_name="gpt-4",
                        embedding_deployment="text-embedding-ada-002",
                    )
                    
                    client = create_llm_client(provider=provider_str)
                    assert isinstance(client, AzureOpenAIClient)

    def test_gemini_provider_string_variants(self):
        """Test that various Gemini provider strings map correctly."""
        test_cases = [
            "gemini",
            "google",
            "google_gemini",
            "GEMINI",
            "Google",
        ]

        for provider_str in test_cases:
            with patch("dev_agent.llm.validate_provider_credentials", return_value=(True, "")):
                with patch("dev_agent.config.config_manager.ConfigManager.load_gemini_config") as mock_load:
                    with patch("dev_agent.llm.gemini_client.GeminiClient") as mock_client:
                        mock_load.return_value = GeminiConfig(
                            api_key=SecretStr("AIzaSyDaGmWKa4JsXZ-HjGw463W12aB3456cDEF"),
                        )
                        mock_client.return_value = MagicMock()
                        
                        client = create_llm_client(provider=provider_str)
                        assert client is not None
                        mock_client.assert_called_once()


class TestIntegrationScenarios:
    """Test integration scenarios with multiple providers."""

    @patch("dev_agent.llm.validate_provider_credentials")
    @patch("dev_agent.config.config_manager.ConfigManager.load_azure_config")
    @patch("dev_agent.config.config_manager.ConfigManager.load_gemini_config")
    @patch("dev_agent.llm.gemini_client.GeminiClient")
    def test_provider_switching_scenario(self, mock_gemini_client, mock_load_gemini, mock_load_azure, mock_validate):
        """Test switching between providers in the same session."""
        # Mock credential validation to always succeed
        mock_validate.return_value = (True, "")
        
        # Mock Azure config
        azure_config = AzureOpenAIConfig(
            endpoint="https://test.openai.azure.com/",
            api_key=SecretStr("test-key"),
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )
        mock_load_azure.return_value = azure_config
        
        # Mock Gemini config
        gemini_config = GeminiConfig(
            api_key=SecretStr("AIzaSyDaGmWKa4JsXZ-HjGw463W12aB3456cDEF"),
        )
        mock_load_gemini.return_value = gemini_config
        
        # Mock Gemini client
        mock_gemini_instance = MagicMock()
        mock_gemini_client.return_value = mock_gemini_instance

        # Create Azure client
        azure_client = create_llm_client(provider="azure")
        assert isinstance(azure_client, AzureOpenAIClient)

        # Create Gemini client
        gemini_client = create_llm_client(provider="gemini")
        assert gemini_client == mock_gemini_instance

        # Verify both configs were loaded
        mock_load_azure.assert_called_once()
        mock_load_gemini.assert_called_once()

    @patch("dev_agent.llm.validate_provider_credentials")
    def test_mixed_provider_embedding_and_llm_clients(self, mock_validate):
        """Test creating LLM and embedding clients with different providers."""
        # Mock credential validation to always succeed
        mock_validate.return_value = (True, "")
        
        # Mock Azure config
        azure_config = AzureOpenAIConfig(
            endpoint="https://test.openai.azure.com/",
            api_key=SecretStr("test-key"),
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )
        
        # Mock Gemini config
        gemini_config = GeminiConfig(
            api_key=SecretStr("AIzaSyDaGmWKa4JsXZ-HjGw463W12aB3456cDEF"),
        )

        with patch("dev_agent.llm.gemini_client.GeminiClient") as mock_gemini_llm:
            with patch("dev_agent.llm.gemini_embeddings.GeminiEmbeddingClient") as mock_gemini_embed:
                mock_gemini_llm.return_value = MagicMock()
                mock_gemini_embed.return_value = MagicMock()

                # Create Azure LLM client and Gemini embedding client
                llm_client = create_llm_client(provider="azure", config=azure_config)
                embedding_client = create_embedding_client(provider="gemini", config=gemini_config)

                assert isinstance(llm_client, AzureOpenAIClient)
                assert embedding_client is not None
                
                # Verify both clients were created with correct configs
                mock_gemini_embed.assert_called_once_with(gemini_config, cache_dir=None)