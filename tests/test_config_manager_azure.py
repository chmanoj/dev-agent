"""Unit tests for Azure OpenAI configuration management.

This module tests the enhanced ConfigManager with Pydantic-based Azure OpenAI
configuration, environment variable loading, and validation.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from dev_agent.config.config_manager import ConfigManager, DevAgentConfig
from dev_agent.models.llm_config import AzureOpenAIConfig


class TestAzureConfigEnvironmentVariables:
    """Test Azure OpenAI configuration loading from environment variables."""

    def test_load_azure_config_from_env_all_required(self):
        """Test loading Azure config when all required env vars are set."""
        env_vars = {
            "AZURE_OPENAI_ENDPOINT": "https://test-resource.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "test-api-key-12345",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4-test",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002-test",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = ConfigManager._load_azure_config_from_env()

            assert config is not None
            assert config.endpoint == "https://test-resource.openai.azure.com/"
            assert config.api_key.get_secret_value() == "test-api-key-12345"
            assert config.deployment_name == "gpt-4-test"
            assert config.embedding_deployment == "text-embedding-ada-002-test"
            # Check defaults
            assert config.api_version == "2024-02-15-preview"
            assert config.max_tokens == 4000
            assert config.temperature == 0.7

    def test_load_azure_config_from_env_with_optional(self):
        """Test loading Azure config with optional env vars."""
        env_vars = {
            "AZURE_OPENAI_ENDPOINT": "https://test-resource.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "test-api-key",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
            "AZURE_OPENAI_API_VERSION": "2024-03-01-preview",
            "AZURE_OPENAI_MAX_TOKENS": "8000",
            "AZURE_OPENAI_TEMPERATURE": "0.5",
            "AZURE_OPENAI_MAX_RETRIES": "5",
            "AZURE_OPENAI_TIMEOUT": "120",
            "AZURE_OPENAI_BATCH_SIZE": "32",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = ConfigManager._load_azure_config_from_env()

            assert config is not None
            assert config.api_version == "2024-03-01-preview"
            assert config.max_tokens == 8000
            assert config.temperature == 0.5
            assert config.max_retries == 5
            assert config.timeout == 120
            assert config.batch_size == 32

    def test_load_azure_config_from_env_missing_required(self):
        """Test that None is returned when required env vars are missing."""
        # Missing AZURE_OPENAI_API_KEY
        env_vars = {
            "AZURE_OPENAI_ENDPOINT": "https://test-resource.openai.azure.com/",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = ConfigManager._load_azure_config_from_env()
            assert config is None

    def test_load_azure_config_from_env_invalid_values(self):
        """Test handling of invalid env var values."""
        env_vars = {
            "AZURE_OPENAI_ENDPOINT": "https://test-resource.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "test-api-key",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
            "AZURE_OPENAI_MAX_TOKENS": "invalid",  # Should be int
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = ConfigManager._load_azure_config_from_env()
            # Should return None due to validation error
            assert config is None

    def test_load_azure_config_from_env_invalid_endpoint(self):
        """Test validation of endpoint URL format."""
        env_vars = {
            "AZURE_OPENAI_ENDPOINT": "not-a-valid-url",  # Missing http(s)://
            "AZURE_OPENAI_API_KEY": "test-api-key",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = ConfigManager._load_azure_config_from_env()
            # Should return None due to validation error
            assert config is None


class TestConfigManagerAzureIntegration:
    """Test ConfigManager integration with Azure OpenAI configuration."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.json"
        self.config_manager = ConfigManager(str(self.config_path))

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_load_config_with_env_vars_precedence(self):
        """Test that env vars take precedence over config file."""
        # Create config file with Azure config
        file_config = DevAgentConfig.default()
        file_config.azure_openai = AzureOpenAIConfig(
            endpoint="https://file-resource.openai.azure.com/",
            api_key="file-api-key",
            deployment_name="gpt-4-file",
            embedding_deployment="text-embedding-file",
        )
        self.config_manager.save_config(file_config)

        # Set environment variables
        env_vars = {
            "AZURE_OPENAI_ENDPOINT": "https://env-resource.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "env-api-key",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4-env",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-env",
        }

        # Clear cached config
        self.config_manager._config = None

        with patch.dict(os.environ, env_vars, clear=False):
            config = self.config_manager.load_config()

            # Env vars should take precedence
            assert config.azure_openai is not None
            assert (
                config.azure_openai.endpoint == "https://env-resource.openai.azure.com/"
            )
            assert config.azure_openai.api_key.get_secret_value() == "env-api-key"
            assert config.azure_openai.deployment_name == "gpt-4-env"

    def test_load_config_without_env_vars_uses_file(self):
        """Test that config file is used when env vars are not set."""
        # Create config file with Azure config
        file_config = DevAgentConfig.default()
        file_config.azure_openai = AzureOpenAIConfig(
            endpoint="https://file-resource.openai.azure.com/",
            api_key="file-api-key",
            deployment_name="gpt-4-file",
            embedding_deployment="text-embedding-file",
        )
        self.config_manager.save_config(file_config)

        # Clear cached config and ensure no Azure env vars
        self.config_manager._config = None
        env_clear = {
            "AZURE_OPENAI_ENDPOINT": "",
            "AZURE_OPENAI_API_KEY": "",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "",
        }

        with patch.dict(os.environ, env_clear, clear=False):
            # Remove the env vars completely
            for key in env_clear:
                os.environ.pop(key, None)

            config = self.config_manager.load_config()

            # Should use file config
            assert config.azure_openai is not None
            assert (
                config.azure_openai.endpoint
                == "https://file-resource.openai.azure.com/"
            )
            assert config.azure_openai.deployment_name == "gpt-4-file"

    def test_load_config_default_no_azure(self):
        """Test that default config has no Azure config without env vars."""
        # Ensure no Azure env vars
        env_clear = {
            "AZURE_OPENAI_ENDPOINT": "",
            "AZURE_OPENAI_API_KEY": "",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "",
        }

        with patch.dict(os.environ, env_clear, clear=False):
            for key in env_clear:
                os.environ.pop(key, None)

            config = self.config_manager.load_config()

            # Default config should have None for Azure
            assert config.azure_openai is None

    def test_get_azure_openai_config_success(self):
        """Test getting Azure OpenAI config when configured."""
        env_vars = {
            "AZURE_OPENAI_ENDPOINT": "https://test-resource.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "test-api-key",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
        }

        self.config_manager._config = None

        with patch.dict(os.environ, env_vars, clear=False):
            azure_config = self.config_manager.get_azure_openai_config()

            assert azure_config is not None
            assert azure_config.endpoint == "https://test-resource.openai.azure.com/"
            assert azure_config.deployment_name == "gpt-4"

    def test_get_azure_openai_config_not_configured(self):
        """Test getting Azure OpenAI config when not configured."""
        # Ensure no Azure env vars
        env_clear = {
            "AZURE_OPENAI_ENDPOINT": "",
            "AZURE_OPENAI_API_KEY": "",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "",
        }

        self.config_manager._config = None

        with patch.dict(os.environ, env_clear, clear=False):
            for key in env_clear:
                os.environ.pop(key, None)

            with pytest.raises(ValueError, match="Azure OpenAI is not configured"):
                self.config_manager.get_azure_openai_config()

    def test_validate_azure_config_valid(self):
        """Test validation of valid Azure config."""
        env_vars = {
            "AZURE_OPENAI_ENDPOINT": "https://test-resource.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "test-api-key",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
        }

        self.config_manager._config = None

        with patch.dict(os.environ, env_vars, clear=False):
            is_valid, error_msg = self.config_manager.validate_azure_config()

            assert is_valid is True
            assert error_msg == ""

    def test_validate_azure_config_not_configured(self):
        """Test validation when Azure config is not set."""
        # Ensure no Azure env vars
        env_clear = {
            "AZURE_OPENAI_ENDPOINT": "",
            "AZURE_OPENAI_API_KEY": "",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "",
        }

        self.config_manager._config = None

        with patch.dict(os.environ, env_clear, clear=False):
            for key in env_clear:
                os.environ.pop(key, None)

            is_valid, error_msg = self.config_manager.validate_azure_config()

            assert is_valid is False
            assert "not configured" in error_msg


class TestConfigSerialization:
    """Test configuration serialization with Pydantic models."""

    def test_config_to_dict_with_azure(self):
        """Test converting config with Azure OpenAI to dictionary."""
        config = DevAgentConfig.default()
        config.azure_openai = AzureOpenAIConfig(
            endpoint="https://test-resource.openai.azure.com/",
            api_key="test-api-key",
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )

        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert "azure_openai" in config_dict
        # API key should be redacted
        assert config_dict["azure_openai"]["api_key"] == "***REDACTED***"
        assert (
            config_dict["azure_openai"]["endpoint"]
            == "https://test-resource.openai.azure.com/"
        )
        assert config_dict["azure_openai"]["deployment_name"] == "gpt-4"

    def test_config_to_dict_without_azure(self):
        """Test converting config without Azure OpenAI to dictionary."""
        config = DevAgentConfig.default()
        config.azure_openai = None

        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert "azure_openai" not in config_dict

    def test_config_from_dict_with_azure(self):
        """Test creating config from dictionary with Azure OpenAI."""
        config_dict = {
            "version": "0.1.0",
            "logging": {"level": "INFO"},
            "cli": {"auto_approve": False},
            "indexing": {"chunk_size": 1000},
            "azure_openai": {
                "endpoint": "https://test-resource.openai.azure.com/",
                "api_key": "test-api-key",
                "deployment_name": "gpt-4",
                "embedding_deployment": "text-embedding-ada-002",
            },
        }

        config = DevAgentConfig.from_dict(config_dict)

        assert config.azure_openai is not None
        assert config.azure_openai.endpoint == "https://test-resource.openai.azure.com/"
        assert config.azure_openai.deployment_name == "gpt-4"

    def test_config_from_dict_legacy_field_names(self):
        """Test backward compatibility with legacy field names."""
        config_dict = {
            "version": "0.1.0",
            "logging": {"level": "INFO"},
            "cli": {"auto_approve": False},
            "indexing": {"chunk_size": 1000},
            "azure_openai": {
                "endpoint": "https://test-resource.openai.azure.com/",
                "api_key": "test-api-key",
                "chat_model": "gpt-4",  # Legacy field name
                "embedding_model": "text-embedding-ada-002",  # Legacy field name
            },
        }

        config = DevAgentConfig.from_dict(config_dict)

        assert config.azure_openai is not None
        assert config.azure_openai.deployment_name == "gpt-4"
        assert config.azure_openai.embedding_deployment == "text-embedding-ada-002"

    def test_config_from_dict_redacted_api_key(self):
        """Test that redacted API keys are skipped."""
        config_dict = {
            "version": "0.1.0",
            "logging": {"level": "INFO"},
            "cli": {"auto_approve": False},
            "indexing": {"chunk_size": 1000},
            "azure_openai": {
                "endpoint": "https://test-resource.openai.azure.com/",
                "api_key": "***REDACTED***",  # Redacted key
                "deployment_name": "gpt-4",
                "embedding_deployment": "text-embedding-ada-002",
            },
        }

        config = DevAgentConfig.from_dict(config_dict)

        # Should skip Azure config with redacted key
        assert config.azure_openai is None

    def test_config_from_dict_invalid_azure_config(self):
        """Test handling of invalid Azure config in dictionary."""
        config_dict = {
            "version": "0.1.0",
            "logging": {"level": "INFO"},
            "cli": {"auto_approve": False},
            "indexing": {"chunk_size": 1000},
            "azure_openai": {
                "endpoint": "invalid-url",  # Invalid endpoint
                "api_key": "test-api-key",
                "deployment_name": "gpt-4",
                "embedding_deployment": "text-embedding-ada-002",
            },
        }

        config = DevAgentConfig.from_dict(config_dict)

        # Should skip invalid Azure config
        assert config.azure_openai is None


class TestProjectConfigWithAzure:
    """Test project-specific configuration with Azure OpenAI."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.json"
        self.project_path = Path(self.temp_dir) / "test_project"
        self.project_path.mkdir()
        self.config_manager = ConfigManager(str(self.config_path))

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_load_project_config_with_env_precedence(self):
        """Test that env vars take precedence over project config."""
        # Create project config
        project_config = DevAgentConfig.default()
        project_config.azure_openai = AzureOpenAIConfig(
            endpoint="https://project-resource.openai.azure.com/",
            api_key="project-api-key",
            deployment_name="gpt-4-project",
            embedding_deployment="text-embedding-project",
        )
        self.config_manager.save_project_config(str(self.project_path), project_config)

        # Set environment variables
        env_vars = {
            "AZURE_OPENAI_ENDPOINT": "https://env-resource.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "env-api-key",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4-env",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-env",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = self.config_manager.load_project_config(str(self.project_path))

            # Env vars should take precedence
            assert config.azure_openai is not None
            assert (
                config.azure_openai.endpoint == "https://env-resource.openai.azure.com/"
            )
            assert config.azure_openai.deployment_name == "gpt-4-env"

    def test_load_project_config_without_env_uses_project(self):
        """Test that project config is used when env vars are not set."""
        # Create project config
        project_config = DevAgentConfig.default()
        project_config.azure_openai = AzureOpenAIConfig(
            endpoint="https://project-resource.openai.azure.com/",
            api_key="project-api-key",
            deployment_name="gpt-4-project",
            embedding_deployment="text-embedding-project",
        )
        self.config_manager.save_project_config(str(self.project_path), project_config)

        # Ensure no Azure env vars
        env_clear = {
            "AZURE_OPENAI_ENDPOINT": "",
            "AZURE_OPENAI_API_KEY": "",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "",
        }

        with patch.dict(os.environ, env_clear, clear=False):
            for key in env_clear:
                os.environ.pop(key, None)

            config = self.config_manager.load_project_config(str(self.project_path))

            # Should use project config
            assert config.azure_openai is not None
            assert (
                config.azure_openai.endpoint
                == "https://project-resource.openai.azure.com/"
            )
            assert config.azure_openai.deployment_name == "gpt-4-project"


class TestGeminiConfigEnvironmentVariables:
    """Test Gemini configuration loading from environment variables."""

    def test_load_gemini_config_from_env_all_required(self):
        """Test loading Gemini config when all required env vars are set."""
        env_vars = {
            "GEMINI_API_KEY": "AIzaSyTest123456789012345678901234567890",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config_manager = ConfigManager()
            config = config_manager.load_gemini_config()

            assert config is not None
            assert (
                config.api_key.get_secret_value()
                == "AIzaSyTest123456789012345678901234567890"
            )
            # Check defaults
            assert config.model_name == "gemini-pro"
            assert config.embedding_model == "embedding-001"
            assert config.api_endpoint == "generativelanguage.googleapis.com"
            assert config.max_output_tokens == 2048
            assert config.temperature == 0.7

    def test_load_gemini_config_from_env_with_optional(self):
        """Test loading Gemini config with optional env vars."""
        env_vars = {
            "GEMINI_API_KEY": "AIzaSyTest123456789012345678901234567890",
            "GEMINI_MODEL_NAME": "gemini-2.5-pro",
            "GEMINI_EMBEDDING_MODEL": "gemini-embedding-001",
            "GEMINI_API_ENDPOINT": "custom.googleapis.com",
            "GEMINI_MAX_OUTPUT_TOKENS": "4096",
            "GEMINI_TEMPERATURE": "0.3",
            "GEMINI_TOP_P": "0.8",
            "GEMINI_TOP_K": "20",
            "GEMINI_MAX_RETRIES": "5",
            "GEMINI_TIMEOUT": "120",
            "GEMINI_BATCH_SIZE": "32",
            "GEMINI_SAFETY_SETTINGS": '{"HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE"}',
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config_manager = ConfigManager()
            config = config_manager.load_gemini_config()

            assert config is not None
            assert config.model_name == "gemini-2.5-pro"
            assert config.embedding_model == "gemini-embedding-001"
            assert config.api_endpoint == "custom.googleapis.com"
            assert config.max_output_tokens == 4096
            assert config.temperature == 0.3
            assert config.top_p == 0.8
            assert config.top_k == 20
            assert config.max_retries == 5
            assert config.timeout == 120
            assert config.batch_size == 32
            assert config.safety_settings == {
                "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE"
            }

    def test_load_gemini_config_from_env_missing_required(self):
        """Test that ValueError is raised when required env vars are missing."""
        # Missing GEMINI_API_KEY
        env_vars = {}

        with patch.dict(os.environ, env_vars, clear=True):
            config_manager = ConfigManager()
            with pytest.raises(
                ValueError, match="GEMINI_API_KEY environment variable is required"
            ):
                config_manager.load_gemini_config()

    def test_load_gemini_config_from_env_invalid_values(self):
        """Test handling of invalid env var values."""
        env_vars = {
            "GEMINI_API_KEY": "AIzaSyTest123456789012345678901234567890",
            "GEMINI_MAX_OUTPUT_TOKENS": "invalid",  # Should be int
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config_manager = ConfigManager()
            with pytest.raises(
                ValueError, match="Failed to load Gemini config from environment"
            ):
                config_manager.load_gemini_config()

    def test_load_gemini_config_from_env_invalid_api_key(self):
        """Test validation of Gemini API key format."""
        env_vars = {
            "GEMINI_API_KEY": "invalid-key-format",  # Should start with "AI"
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config_manager = ConfigManager()
            with pytest.raises(
                ValueError, match="Failed to load Gemini config from environment"
            ):
                config_manager.load_gemini_config()

    def test_load_gemini_config_from_env_invalid_safety_settings(self):
        """Test handling of invalid safety settings JSON."""
        env_vars = {
            "GEMINI_API_KEY": "AIzaSyTest123456789012345678901234567890",
            "GEMINI_SAFETY_SETTINGS": "invalid-json",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config_manager = ConfigManager()
            # Should still work but with default safety settings
            config = config_manager.load_gemini_config()
            assert config.safety_settings == {}


class TestLLMProviderSelection:
    """Test LLM provider selection and validation."""

    def test_get_llm_provider_default_azure(self):
        """Test that Azure OpenAI is the default provider."""
        env_vars = {
            "AZURE_OPENAI_ENDPOINT": "https://test-resource.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "test-api-key",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            # Remove PREFERRED_LLM_PROVIDER if set
            os.environ.pop("PREFERRED_LLM_PROVIDER", None)

            config_manager = ConfigManager()
            provider = config_manager.get_llm_provider()

            from dev_agent.models.enums import LLMProvider

            assert provider == LLMProvider.AZURE_OPENAI

    def test_get_llm_provider_explicit_azure(self):
        """Test explicit Azure OpenAI provider selection."""
        env_vars = {
            "PREFERRED_LLM_PROVIDER": "azure_openai",
            "AZURE_OPENAI_ENDPOINT": "https://test-resource.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "test-api-key",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config_manager = ConfigManager()
            provider = config_manager.get_llm_provider()

            from dev_agent.models.enums import LLMProvider

            assert provider == LLMProvider.AZURE_OPENAI

    def test_get_llm_provider_explicit_gemini(self):
        """Test explicit Gemini provider selection."""
        env_vars = {
            "PREFERRED_LLM_PROVIDER": "gemini",
            "GEMINI_API_KEY": "AIzaSyTest123456789012345678901234567890",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config_manager = ConfigManager()
            provider = config_manager.get_llm_provider()

            from dev_agent.models.enums import LLMProvider

            assert provider == LLMProvider.GEMINI

    def test_get_llm_provider_azure_alias(self):
        """Test that 'azure' is accepted as alias for 'azure_openai'."""
        env_vars = {
            "PREFERRED_LLM_PROVIDER": "azure",
            "AZURE_OPENAI_ENDPOINT": "https://test-resource.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "test-api-key",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config_manager = ConfigManager()
            provider = config_manager.get_llm_provider()

            from dev_agent.models.enums import LLMProvider

            assert provider == LLMProvider.AZURE_OPENAI

    def test_get_llm_provider_unsupported(self):
        """Test error handling for unsupported provider."""
        env_vars = {
            "PREFERRED_LLM_PROVIDER": "unsupported_provider",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config_manager = ConfigManager()
            with pytest.raises(
                ValueError, match="Unsupported LLM provider: unsupported_provider"
            ):
                config_manager.get_llm_provider()

    def test_get_llm_provider_fallback_to_working_provider(self):
        """Test fallback to working provider when preferred is not configured."""
        env_vars = {
            "PREFERRED_LLM_PROVIDER": "gemini",
            # Gemini not configured, but Azure is
            "AZURE_OPENAI_ENDPOINT": "https://test-resource.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "test-api-key",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            # Remove Gemini API key if set
            os.environ.pop("GEMINI_API_KEY", None)

            config_manager = ConfigManager()
            provider = config_manager.get_llm_provider()

            from dev_agent.models.enums import LLMProvider

            assert provider == LLMProvider.AZURE_OPENAI

    def test_get_llm_provider_no_valid_providers(self):
        """Test error when no valid providers are configured."""
        env_vars = {
            "PREFERRED_LLM_PROVIDER": "gemini",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            # Clear all provider env vars
            for key in list(os.environ.keys()):
                if key.startswith(("AZURE_OPENAI_", "GEMINI_")):
                    os.environ.pop(key, None)

            config_manager = ConfigManager()
            with pytest.raises(
                ValueError, match="No valid LLM provider configuration found"
            ):
                config_manager.get_llm_provider()


class TestProviderConfigValidation:
    """Test provider configuration validation."""

    def test_validate_provider_config_azure_valid(self):
        """Test validation of valid Azure OpenAI config."""
        env_vars = {
            "AZURE_OPENAI_ENDPOINT": "https://test-resource.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "test-api-key",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config_manager = ConfigManager()
            from dev_agent.models.enums import LLMProvider

            is_valid, error_msg = config_manager.validate_provider_config(
                LLMProvider.AZURE_OPENAI
            )

            assert is_valid is True
            assert error_msg == ""

    def test_validate_provider_config_azure_invalid(self):
        """Test validation of invalid Azure OpenAI config."""
        # Clear Azure env vars
        env_clear = {
            "AZURE_OPENAI_ENDPOINT": "",
            "AZURE_OPENAI_API_KEY": "",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "",
        }

        with patch.dict(os.environ, env_clear, clear=False):
            for key in env_clear:
                os.environ.pop(key, None)

            config_manager = ConfigManager()
            from dev_agent.models.enums import LLMProvider

            is_valid, error_msg = config_manager.validate_provider_config(
                LLMProvider.AZURE_OPENAI
            )

            assert is_valid is False
            assert "not available" in error_msg

    def test_validate_provider_config_gemini_valid(self):
        """Test validation of valid Gemini config."""
        env_vars = {
            "GEMINI_API_KEY": "AIzaSyTest123456789012345678901234567890",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config_manager = ConfigManager()
            from dev_agent.models.enums import LLMProvider

            is_valid, error_msg = config_manager.validate_provider_config(
                LLMProvider.GEMINI
            )

            assert is_valid is True
            assert error_msg == ""

    def test_validate_provider_config_gemini_invalid(self):
        """Test validation of invalid Gemini config."""
        # Clear Gemini env vars
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("GEMINI_API_KEY", None)

            config_manager = ConfigManager()
            from dev_agent.models.enums import LLMProvider

            is_valid, error_msg = config_manager.validate_provider_config(
                LLMProvider.GEMINI
            )

            assert is_valid is False
            assert "GEMINI_API_KEY environment variable is required" in error_msg

    def test_validate_provider_config_unsupported(self):
        """Test validation of unsupported provider."""
        config_manager = ConfigManager()

        # Create a mock unsupported provider
        class UnsupportedProvider:
            value = "unsupported"

        is_valid, error_msg = config_manager.validate_provider_config(
            UnsupportedProvider()
        )

        assert is_valid is False
        assert "Unsupported provider: unsupported" in error_msg


class TestMultiProviderConfigManager:
    """Test ConfigManager with multi-provider support."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.json"
        self.config_manager = ConfigManager(str(self.config_path))

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_get_llm_config_azure(self):
        """Test getting Azure OpenAI config via get_llm_config."""
        env_vars = {
            "AZURE_OPENAI_ENDPOINT": "https://test-resource.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "test-api-key",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            from dev_agent.models.enums import LLMProvider

            config = self.config_manager.get_llm_config(LLMProvider.AZURE_OPENAI)

            assert config is not None
            assert hasattr(config, "endpoint")
            assert config.endpoint == "https://test-resource.openai.azure.com/"

    def test_get_llm_config_gemini(self):
        """Test getting Gemini config via get_llm_config."""
        env_vars = {
            "GEMINI_API_KEY": "AIzaSyTest123456789012345678901234567890",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            from dev_agent.models.enums import LLMProvider

            config = self.config_manager.get_llm_config(LLMProvider.GEMINI)

            assert config is not None
            assert hasattr(config, "api_key")
            assert (
                config.api_key.get_secret_value()
                == "AIzaSyTest123456789012345678901234567890"
            )

    def test_get_llm_config_auto_detect(self):
        """Test getting config for auto-detected provider."""
        env_vars = {
            "PREFERRED_LLM_PROVIDER": "gemini",
            "GEMINI_API_KEY": "AIzaSyTest123456789012345678901234567890",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = self.config_manager.get_llm_config()

            assert config is not None
            assert hasattr(config, "api_key")
            assert (
                config.api_key.get_secret_value()
                == "AIzaSyTest123456789012345678901234567890"
            )

    def test_get_gemini_config_from_env(self):
        """Test getting Gemini config when available from env."""
        env_vars = {
            "GEMINI_API_KEY": "AIzaSyTest123456789012345678901234567890",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = self.config_manager.get_gemini_config()

            assert config is not None
            assert (
                config.api_key.get_secret_value()
                == "AIzaSyTest123456789012345678901234567890"
            )

    def test_get_gemini_config_not_configured(self):
        """Test getting Gemini config when not configured."""
        # Clear Gemini env vars
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("GEMINI_API_KEY", None)

            self.config_manager._config = None

            with pytest.raises(ValueError, match="Gemini is not configured"):
                self.config_manager.get_gemini_config()

    def test_load_config_with_both_providers(self):
        """Test loading config with both Azure and Gemini configured."""
        env_vars = {
            "AZURE_OPENAI_ENDPOINT": "https://test-resource.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "test-api-key",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
            "GEMINI_API_KEY": "AIzaSyTest123456789012345678901234567890",
        }

        self.config_manager._config = None

        with patch.dict(os.environ, env_vars, clear=False):
            config = self.config_manager.load_config()

            assert config.azure_openai is not None
            assert config.gemini is not None
            assert (
                config.azure_openai.endpoint
                == "https://test-resource.openai.azure.com/"
            )
            assert (
                config.gemini.api_key.get_secret_value()
                == "AIzaSyTest123456789012345678901234567890"
            )

    def test_load_config_with_only_azure(self):
        """Test loading config with only Azure configured."""
        env_vars = {
            "AZURE_OPENAI_ENDPOINT": "https://test-resource.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "test-api-key",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
        }

        self.config_manager._config = None

        with patch.dict(os.environ, env_vars, clear=False):
            # Remove Gemini API key if set
            os.environ.pop("GEMINI_API_KEY", None)

            config = self.config_manager.load_config()

            assert config.azure_openai is not None
            assert config.gemini is None

    def test_load_config_with_only_gemini(self):
        """Test loading config with only Gemini configured."""
        env_vars = {
            "GEMINI_API_KEY": "AIzaSyTest123456789012345678901234567890",
        }

        self.config_manager._config = None

        with patch.dict(os.environ, env_vars, clear=False):
            # Clear Azure env vars
            for key in list(os.environ.keys()):
                if key.startswith("AZURE_OPENAI_"):
                    os.environ.pop(key, None)

            config = self.config_manager.load_config()

            assert config.azure_openai is None
            assert config.gemini is not None


class TestBackwardCompatibility:
    """Test backward compatibility with existing Azure-only configuration."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.json"
        self.config_manager = ConfigManager(str(self.config_path))

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_existing_azure_config_still_works(self):
        """Test that existing Azure-only configurations continue to work."""
        # Create old-style config file (without gemini field)
        old_config_dict = {
            "version": "0.1.0",
            "logging": {"level": "INFO"},
            "cli": {"auto_approve": False},
            "indexing": {"chunk_size": 1000},
            "azure_openai": {
                "endpoint": "https://test-resource.openai.azure.com/",
                "api_key": "test-api-key",
                "deployment_name": "gpt-4",
                "embedding_deployment": "text-embedding-ada-002",
            },
        }

        # Save old config format
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(old_config_dict, f, indent=2)

        # Load config should work and add gemini field as None
        config = self.config_manager.load_config()

        assert config.azure_openai is not None
        assert config.gemini is None
        assert config.azure_openai.endpoint == "https://test-resource.openai.azure.com/"

    def test_default_provider_is_azure(self):
        """Test that Azure OpenAI remains the default provider."""
        env_vars = {
            "AZURE_OPENAI_ENDPOINT": "https://test-resource.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "test-api-key",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            # Ensure no PREFERRED_LLM_PROVIDER is set
            os.environ.pop("PREFERRED_LLM_PROVIDER", None)

            provider = self.config_manager.get_llm_provider()

            from dev_agent.models.enums import LLMProvider

            assert provider == LLMProvider.AZURE_OPENAI

    def test_existing_methods_still_work(self):
        """Test that existing Azure-specific methods still work."""
        env_vars = {
            "AZURE_OPENAI_ENDPOINT": "https://test-resource.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "test-api-key",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            # These methods should continue to work
            azure_config = self.config_manager.get_azure_openai_config()
            assert azure_config is not None

            is_valid, error_msg = self.config_manager.validate_azure_config()
            assert is_valid is True
            assert error_msg == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
