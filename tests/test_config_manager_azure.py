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
from pydantic import ValidationError

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
            assert config.azure_openai.endpoint == "https://env-resource.openai.azure.com/"
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
            assert config.azure_openai.endpoint == "https://file-resource.openai.azure.com/"
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
        assert config_dict["azure_openai"]["endpoint"] == "https://test-resource.openai.azure.com/"
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
            assert config.azure_openai.endpoint == "https://env-resource.openai.azure.com/"
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
            assert config.azure_openai.endpoint == "https://project-resource.openai.azure.com/"
            assert config.azure_openai.deployment_name == "gpt-4-project"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
