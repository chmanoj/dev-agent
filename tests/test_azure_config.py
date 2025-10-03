"""Tests for Azure OpenAI CLI configuration commands."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from pydantic import SecretStr
from typer.testing import CliRunner

from dev_agent.cli.azure_config import app
from dev_agent.errors.llm_exceptions import (
    LLMAPIError,
    LLMAuthenticationError,
    LLMBadRequestError,
)
from dev_agent.models.llm_config import AzureOpenAIConfig


@pytest.fixture
def cli_runner():
    """Create CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_config():
    """Create mock Azure OpenAI configuration."""
    return AzureOpenAIConfig(
        endpoint="https://test-resource.openai.azure.com/",
        api_key="test-api-key-12345678901234567890",
        api_version="2024-02-15-preview",
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
        max_tokens=4000,
        temperature=0.7,
        max_retries=3,
        timeout=60,
        batch_size=16,
    )


@pytest.fixture
def mock_config_manager(mock_config):
    """Create mock configuration manager."""
    manager = Mock()
    dev_config = Mock()
    dev_config.azure_openai = mock_config
    dev_config.indexing = Mock()
    dev_config.indexing.use_azure_embeddings = True
    manager.get_config.return_value = dev_config
    manager.save_config = Mock()
    return manager


class TestConfigureCommand:
    """Tests for the configure command."""

    def test_configure_non_interactive_success(
        self, cli_runner, mock_config_manager
    ):
        """Test non-interactive configuration with all parameters."""
        with patch(
            "dev_agent.cli.azure_config.ConfigManager",
            return_value=mock_config_manager,
        ):
            result = cli_runner.invoke(
                app,
                [
                    "configure",
                    "--no-interactive",
                    "--api-key",
                    "new-api-key-12345678901234567890",
                    "--endpoint",
                    "https://new-resource.openai.azure.com/",
                    "--deployment-name",
                    "gpt-4-turbo",
                    "--embedding-deployment",
                    "text-embedding-ada-002",
                ],
            )

            assert result.exit_code == 0
            assert "saved successfully" in result.stdout
            mock_config_manager.save_config.assert_called_once()

    def test_configure_missing_api_key(self, cli_runner, mock_config_manager):
        """Test configuration fails without API key."""
        with patch(
            "dev_agent.cli.azure_config.ConfigManager",
            return_value=mock_config_manager,
        ):
            result = cli_runner.invoke(
                app,
                [
                    "configure",
                    "--no-interactive",
                    "--endpoint",
                    "https://test.openai.azure.com/",
                ],
            )

            assert result.exit_code == 1
            assert "API key is required" in result.stdout

    def test_configure_missing_endpoint(self, cli_runner, mock_config_manager):
        """Test configuration fails without endpoint."""
        with patch(
            "dev_agent.cli.azure_config.ConfigManager",
            return_value=mock_config_manager,
        ):
            result = cli_runner.invoke(
                app,
                [
                    "configure",
                    "--no-interactive",
                    "--api-key",
                    "test-key-12345678901234567890",
                ],
            )

            assert result.exit_code == 1
            assert "Endpoint URL is required" in result.stdout

    def test_configure_missing_deployment_name(
        self, cli_runner, mock_config_manager
    ):
        """Test configuration fails without deployment name."""
        # Set deployment_name to empty in mock
        mock_config_manager.get_config.return_value.azure_openai.deployment_name = ""
        
        with patch(
            "dev_agent.cli.azure_config.ConfigManager",
            return_value=mock_config_manager,
        ):
            result = cli_runner.invoke(
                app,
                [
                    "configure",
                    "--no-interactive",
                    "--api-key",
                    "test-key-12345678901234567890",
                    "--endpoint",
                    "https://test.openai.azure.com/",
                ],
            )

            assert result.exit_code == 1
            assert "Deployment name is required" in result.stdout

    def test_configure_interactive_cancel(self, cli_runner, mock_config_manager):
        """Test interactive configuration can be cancelled."""
        with patch(
            "dev_agent.cli.azure_config.ConfigManager",
            return_value=mock_config_manager,
        ):
            result = cli_runner.invoke(
                app,
                ["configure"],
                input="n\n",  # Answer no to update prompt
            )

            assert result.exit_code == 0
            assert "Configuration unchanged" in result.stdout
            mock_config_manager.save_config.assert_not_called()

    def test_configure_validation_error(self, cli_runner, mock_config_manager):
        """Test configuration with invalid endpoint format."""
        with patch(
            "dev_agent.cli.azure_config.ConfigManager",
            return_value=mock_config_manager,
        ):
            result = cli_runner.invoke(
                app,
                [
                    "configure",
                    "--no-interactive",
                    "--api-key",
                    "test-key-12345678901234567890",
                    "--endpoint",
                    "invalid-endpoint",  # Missing http://
                    "--deployment-name",
                    "gpt-4",
                    "--embedding-deployment",
                    "text-embedding-ada-002",
                ],
            )

            assert result.exit_code == 1
            assert "Validation Error" in result.stdout


class TestTestCommand:
    """Tests for the test command."""

    def test_test_connection_success(self, cli_runner, mock_config_manager):
        """Test successful connection test."""
        # Create a mock that returns a coroutine
        async def mock_completion(*args, **kwargs):
            return "test successful"
        
        async def mock_embeddings(*args, **kwargs):
            return [[0.1] * 1536]
        
        mock_llm_client = Mock()
        mock_llm_client.generate_completion = mock_completion

        mock_embedding_client = Mock()
        mock_embedding_client.embed_batch = mock_embeddings

        with patch(
            "dev_agent.cli.azure_config.ConfigManager",
            return_value=mock_config_manager,
        ), patch(
            "dev_agent.cli.azure_config.AzureOpenAIClient",
            return_value=mock_llm_client,
        ), patch(
            "dev_agent.cli.azure_config.AzureEmbeddingClient",
            return_value=mock_embedding_client,
        ), patch(
            "dev_agent.cli.azure_config._run_async_test",
            side_effect=lambda coro: asyncio.run(coro),
        ):
            result = cli_runner.invoke(app, ["test"])

            assert result.exit_code == 0
            assert "All tests passed" in result.stdout
            assert "Chat completion test successful" in result.stdout
            assert "Embeddings test successful" in result.stdout

    def test_test_connection_authentication_error(
        self, cli_runner, mock_config_manager
    ):
        """Test connection test with authentication error."""
        async def mock_completion(*args, **kwargs):
            raise LLMAuthenticationError("Invalid API key")
        
        mock_llm_client = Mock()
        mock_llm_client.generate_completion = mock_completion

        with patch(
            "dev_agent.cli.azure_config.ConfigManager",
            return_value=mock_config_manager,
        ), patch(
            "dev_agent.cli.azure_config.AzureOpenAIClient",
            return_value=mock_llm_client,
        ), patch(
            "dev_agent.cli.azure_config._run_async_test",
            side_effect=lambda coro: asyncio.run(coro),
        ):
            result = cli_runner.invoke(app, ["test"])

            assert result.exit_code == 1
            assert "Authentication" in result.stdout

    def test_test_connection_bad_deployment(
        self, cli_runner, mock_config_manager
    ):
        """Test connection test with invalid deployment."""
        async def mock_completion(*args, **kwargs):
            raise LLMBadRequestError("Deployment not found")
        
        mock_llm_client = Mock()
        mock_llm_client.generate_completion = mock_completion

        with patch(
            "dev_agent.cli.azure_config.ConfigManager",
            return_value=mock_config_manager,
        ), patch(
            "dev_agent.cli.azure_config.AzureOpenAIClient",
            return_value=mock_llm_client,
        ), patch(
            "dev_agent.cli.azure_config._run_async_test",
            side_effect=lambda coro: asyncio.run(coro),
        ):
            result = cli_runner.invoke(app, ["test"])

            assert result.exit_code == 1
            assert "Deployment" in result.stdout

    def test_test_connection_not_configured(self, cli_runner):
        """Test connection test when not configured."""
        mock_manager = Mock()
        dev_config = Mock()
        dev_config.azure_openai = Mock()
        dev_config.azure_openai.api_key = None
        dev_config.azure_openai.endpoint = None
        mock_manager.get_config.return_value = dev_config

        with patch(
            "dev_agent.cli.azure_config.ConfigManager",
            return_value=mock_manager,
        ):
            result = cli_runner.invoke(app, ["test"])

            assert result.exit_code == 1
            assert "Configuration Missing" in result.stdout


class TestStatusCommand:
    """Tests for the status command."""

    def test_status_fully_configured(self, cli_runner, mock_config_manager):
        """Test status display when fully configured."""
        with patch(
            "dev_agent.cli.azure_config.ConfigManager",
            return_value=mock_config_manager,
        ):
            result = cli_runner.invoke(app, ["status"])

            assert result.exit_code == 0
            assert "Azure OpenAI Status" in result.stdout
            assert "✓ Configured" in result.stdout
            assert "fully configured" in result.stdout

    def test_status_partially_configured(self, cli_runner):
        """Test status display when partially configured."""
        mock_manager = Mock()
        dev_config = Mock()
        dev_config.azure_openai = Mock()
        dev_config.azure_openai.api_key = SecretStr("test-key")
        dev_config.azure_openai.endpoint = "https://test.openai.azure.com/"
        dev_config.azure_openai.api_version = "2024-02-15-preview"
        dev_config.azure_openai.deployment_name = None  # Missing
        dev_config.azure_openai.embedding_deployment = "text-embedding-ada-002"
        dev_config.azure_openai.max_tokens = 4000
        dev_config.azure_openai.temperature = 0.7
        dev_config.azure_openai.max_retries = 3
        dev_config.azure_openai.timeout = 60
        dev_config.azure_openai.batch_size = 16
        dev_config.indexing = Mock()
        dev_config.indexing.use_azure_embeddings = True
        mock_manager.get_config.return_value = dev_config

        with patch(
            "dev_agent.cli.azure_config.ConfigManager",
            return_value=mock_manager,
        ):
            result = cli_runner.invoke(app, ["status"])

            assert result.exit_code == 0
            assert "not fully configured" in result.stdout
            assert "Deployment Name" in result.stdout


class TestModelsCommand:
    """Tests for the models command."""

    def test_list_models(self, cli_runner):
        """Test listing available models."""
        result = cli_runner.invoke(app, ["models"])

        assert result.exit_code == 0
        assert "Azure OpenAI Models" in result.stdout
        assert "gpt-4" in result.stdout
        assert "text-embedding-ada-002" in result.stdout


class TestEnvCommand:
    """Tests for the env command."""

    def test_show_env_variables(self, cli_runner):
        """Test showing environment variables."""
        with patch.dict(
            "os.environ",
            {
                "AZURE_OPENAI_API_KEY": "test-key",
                "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            },
        ):
            result = cli_runner.invoke(app, ["env"])

            assert result.exit_code == 0
            assert "Environment Variables" in result.stdout
            # Check for partial match since table may truncate
            assert "AZURE_OPENAI" in result.stdout or "API_K" in result.stdout
            assert "***" in result.stdout  # API key should be masked

    def test_show_env_variables_not_set(self, cli_runner):
        """Test showing environment variables when not set."""
        with patch.dict("os.environ", {}, clear=True):
            result = cli_runner.invoke(app, ["env"])

            assert result.exit_code == 0
            assert "Not set" in result.stdout


class TestExportCommand:
    """Tests for the export command."""

    def test_export_without_secrets(
        self, cli_runner, mock_config_manager, tmp_path
    ):
        """Test exporting configuration without API key."""
        output_file = tmp_path / "config.json"

        with patch(
            "dev_agent.cli.azure_config.ConfigManager",
            return_value=mock_config_manager,
        ):
            result = cli_runner.invoke(
                app,
                ["export", "--output", str(output_file)],
            )

            assert result.exit_code == 0
            assert output_file.exists()

            # Verify exported data
            exported = json.loads(output_file.read_text())
            assert "REDACTED" in exported["api_key"]
            assert exported["endpoint"] == "https://test-resource.openai.azure.com/"
            assert exported["deployment_name"] == "gpt-4"

    def test_export_with_secrets(
        self, cli_runner, mock_config_manager, tmp_path
    ):
        """Test exporting configuration with API key."""
        output_file = tmp_path / "config.json"

        with patch(
            "dev_agent.cli.azure_config.ConfigManager",
            return_value=mock_config_manager,
        ):
            result = cli_runner.invoke(
                app,
                ["export", "--output", str(output_file), "--include-secrets"],
            )

            assert result.exit_code == 0
            assert output_file.exists()

            # Verify exported data includes API key
            exported = json.loads(output_file.read_text())
            assert "REDACTED" not in exported["api_key"]
            assert exported["api_key"] == "test-api-key-12345678901234567890"


class TestImportCommand:
    """Tests for the import command."""

    def test_import_success(self, cli_runner, mock_config_manager, tmp_path):
        """Test importing configuration successfully."""
        # Create import file
        import_file = tmp_path / "import.json"
        import_data = {
            "endpoint": "https://imported.openai.azure.com/",
            "api_key": "imported-key-12345678901234567890",
            "api_version": "2024-02-15-preview",
            "deployment_name": "gpt-4-turbo",
            "embedding_deployment": "text-embedding-ada-002",
            "max_tokens": 8000,
            "temperature": 0.5,
            "max_retries": 5,
            "timeout": 120,
            "batch_size": 32,
        }
        import_file.write_text(json.dumps(import_data))

        with patch(
            "dev_agent.cli.azure_config.ConfigManager",
            return_value=mock_config_manager,
        ):
            result = cli_runner.invoke(
                app,
                ["import", str(import_file)],
                input="y\n",  # Confirm import
            )

            assert result.exit_code == 0
            assert "imported successfully" in result.stdout
            mock_config_manager.save_config.assert_called_once()

    def test_import_file_not_found(self, cli_runner):
        """Test importing from non-existent file."""
        result = cli_runner.invoke(
            app,
            ["import", "nonexistent.json"],
        )

        assert result.exit_code == 1
        assert "File not found" in result.stdout

    def test_import_invalid_json(self, cli_runner, tmp_path):
        """Test importing invalid JSON file."""
        import_file = tmp_path / "invalid.json"
        import_file.write_text("not valid json {")

        result = cli_runner.invoke(
            app,
            ["import", str(import_file)],
        )

        assert result.exit_code == 1
        assert "Parse Error" in result.stdout

    def test_import_cancel(self, cli_runner, tmp_path):
        """Test cancelling import."""
        import_file = tmp_path / "import.json"
        import_data = {
            "endpoint": "https://test.openai.azure.com/",
            "api_key": "test-key",
        }
        import_file.write_text(json.dumps(import_data))

        result = cli_runner.invoke(
            app,
            ["import", str(import_file)],
            input="n\n",  # Cancel import
        )

        assert result.exit_code == 0
        assert "cancelled" in result.stdout

    def test_import_merge(self, cli_runner, mock_config_manager, tmp_path):
        """Test importing with merge option."""
        import_file = tmp_path / "import.json"
        import_data = {
            "endpoint": "https://new.openai.azure.com/",
            "max_tokens": 8000,
        }
        import_file.write_text(json.dumps(import_data))

        with patch(
            "dev_agent.cli.azure_config.ConfigManager",
            return_value=mock_config_manager,
        ):
            result = cli_runner.invoke(
                app,
                ["import", str(import_file), "--merge"],
                input="y\n",  # Confirm import
            )

            assert result.exit_code == 0
            assert "imported successfully" in result.stdout


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_display_current_config(self, mock_config):
        """Test displaying current configuration."""
        from dev_agent.cli.azure_config import _display_current_config

        # Should not raise any exceptions
        _display_current_config(mock_config)

    def test_prompt_for_api_key_keep_current(self, mock_config):
        """Test prompting for API key when keeping current."""
        from dev_agent.cli.azure_config import _prompt_for_api_key

        with patch("dev_agent.cli.azure_config.Confirm.ask", return_value=True):
            result = _prompt_for_api_key("current-key")
            assert result == "current-key"

    def test_prompt_for_endpoint_validation(self):
        """Test endpoint validation in prompt."""
        from dev_agent.cli.azure_config import _prompt_for_endpoint

        with patch(
            "dev_agent.cli.azure_config.Prompt.ask",
            return_value="https://test.openai.azure.com/",
        ):
            result = _prompt_for_endpoint(None)
            assert result == "https://test.openai.azure.com/"
