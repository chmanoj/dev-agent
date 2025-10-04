"""Tests for the validate CLI command."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from pydantic import SecretStr
from typer.testing import CliRunner

from dev_agent.cli.main import app


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_config_manager():
    """Mock configuration manager."""
    with patch("dev_agent.cli.main.config_manager") as mock, \
         patch("dev_agent.cli.main.setup_cli_logging"):
        # Mock get_config to return a simple config
        from types import SimpleNamespace
        default_config = SimpleNamespace(azure_openai=None)
        mock.get_config.return_value = default_config
        yield mock


@pytest.fixture
def mock_azure_config():
    """Create mock Azure OpenAI configuration."""
    config = MagicMock()
    azure_openai = MagicMock()
    
    # Properly mock the api_key as SecretStr
    azure_openai.api_key = SecretStr("test-key")
    azure_openai.endpoint = "https://test.openai.azure.com/"
    azure_openai.deployment_name = "gpt-4"
    azure_openai.embedding_deployment = "text-embedding-ada-002"
    
    config.azure_openai = azure_openai
    return config


def test_validate_command_all_checks_pass(runner, mock_config_manager, mock_azure_config):
    """Test validate command when all checks pass."""
    # Setup mocks
    mock_config_manager.get_config.return_value = mock_azure_config

    # Mock Azure client test - patch where it's imported in the validate function
    with patch("dev_agent.llm.azure_client.AzureOpenAIClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.generate_completion = AsyncMock(return_value="OK")
        mock_client_class.return_value = mock_client

        # Mock file system operations
        with patch("pathlib.Path.write_text"), patch("pathlib.Path.unlink"), patch(
            "pathlib.Path.iterdir", return_value=[]
        ):
            result = runner.invoke(app, ["validate"])

    # Verify success
    assert result.exit_code == 0
    assert "All validation checks passed" in result.stdout
    assert "✓ Pass" in result.stdout


def test_validate_command_missing_azure_config(runner, mock_config_manager):
    """Test validate command with missing Azure OpenAI configuration."""
    # Setup mock with missing config - use a real-like object
    from types import SimpleNamespace
    config = SimpleNamespace(azure_openai=None)
    mock_config_manager.get_config.return_value = config

    result = runner.invoke(app, ["validate"])

    # Verify failure
    assert result.exit_code == 1
    # Check for key indicators of validation failure
    assert "Azure OpenAI" in result.stdout or "azure" in result.stdout.lower()
    assert "setup" in result.stdout.lower()


def test_validate_command_partial_azure_config(runner, mock_config_manager):
    """Test validate command with partial Azure OpenAI configuration."""
    # Setup mock with partial config - use a real-like object
    from types import SimpleNamespace
    azure_openai = SimpleNamespace(
        api_key=None,  # Missing API key
        endpoint="https://test.openai.azure.com/",
        deployment_name="gpt-4",
        embedding_deployment=None  # Missing embedding deployment
    )
    config = SimpleNamespace(azure_openai=azure_openai)
    mock_config_manager.get_config.return_value = config

    result = runner.invoke(app, ["validate"])

    # Verify failure
    assert result.exit_code == 1
    assert "Missing" in result.stdout or "missing" in result.stdout.lower()


def test_validate_command_api_connection_failure(runner, mock_config_manager, mock_azure_config):
    """Test validate command when API connection fails."""
    # Setup mocks
    mock_config_manager.get_config.return_value = mock_azure_config

    # Mock Azure client to raise exception
    with patch("dev_agent.llm.azure_client.AzureOpenAIClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.generate_completion = AsyncMock(
            side_effect=Exception("Connection timeout")
        )
        mock_client_class.return_value = mock_client

        # Mock file system operations
        with patch("pathlib.Path.write_text"), patch("pathlib.Path.unlink"), patch(
            "pathlib.Path.iterdir", return_value=[]
        ):
            result = runner.invoke(app, ["validate"])

    # Verify failure
    assert result.exit_code == 1
    assert "✗ Fail" in result.stdout
    assert "API Connectivity" in result.stdout


def test_validate_command_missing_dependencies(runner, mock_config_manager, mock_azure_config):
    """Test validate command with missing dependencies."""
    # Setup mocks
    mock_config_manager.get_config.return_value = mock_azure_config

    # Mock missing package
    with patch("importlib.util.find_spec", return_value=None):
        # Mock Azure client test
        with patch("dev_agent.llm.azure_client.AzureOpenAIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.generate_completion = AsyncMock(return_value="OK")
            mock_client_class.return_value = mock_client

            # Mock file system operations
            with patch("pathlib.Path.write_text"), patch("pathlib.Path.unlink"), patch(
                "pathlib.Path.iterdir", return_value=[]
            ):
                result = runner.invoke(app, ["validate"])

    # Verify failure
    assert result.exit_code == 1
    assert "Required Dependencies" in result.stdout
    assert "uv sync" in result.stdout


def test_validate_command_python_version_check(runner, mock_config_manager, mock_azure_config):
    """Test validate command checks Python version."""
    # Setup mocks
    mock_config_manager.get_config.return_value = mock_azure_config

    # Mock Azure client test
    with patch("dev_agent.llm.azure_client.AzureOpenAIClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.generate_completion = AsyncMock(return_value="OK")
        mock_client_class.return_value = mock_client

        # Mock file system operations
        with patch("pathlib.Path.write_text"), patch("pathlib.Path.unlink"), patch(
            "pathlib.Path.iterdir", return_value=[]
        ):
            result = runner.invoke(app, ["validate"])

    # Verify Python version is checked
    assert "Python Version" in result.stdout
    # Current Python should pass (we're running tests)
    if sys.version_info >= (3, 10):
        assert "✓ Pass" in result.stdout


def test_validate_command_file_system_permissions(runner, mock_config_manager, mock_azure_config):
    """Test validate command checks file system permissions."""
    # Setup mocks
    mock_config_manager.get_config.return_value = mock_azure_config

    # Mock Azure client test
    with patch("dev_agent.llm.azure_client.AzureOpenAIClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.generate_completion = AsyncMock(return_value="OK")
        mock_client_class.return_value = mock_client

        # Mock file system permission error
        with patch("pathlib.Path.write_text", side_effect=PermissionError("Access denied")):
            result = runner.invoke(app, ["validate"])

    # Verify failure
    assert result.exit_code == 1
    assert "File System Permissions" in result.stdout
    assert "✗ Fail" in result.stdout


def test_validate_command_verbose_output(runner, mock_config_manager, mock_azure_config):
    """Test validate command with verbose flag."""
    # Setup mocks
    mock_config_manager.get_config.return_value = mock_azure_config

    # Mock Azure client test
    with patch("dev_agent.llm.azure_client.AzureOpenAIClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.generate_completion = AsyncMock(return_value="OK")
        mock_client_class.return_value = mock_client

        # Mock file system operations
        with patch("pathlib.Path.write_text"), patch("pathlib.Path.unlink"), patch(
            "pathlib.Path.iterdir", return_value=[]
        ):
            result = runner.invoke(app, ["validate", "--verbose"])

    # Verify verbose output
    assert "Checking Azure OpenAI configuration" in result.stdout
    assert "Checking required dependencies" in result.stdout


def test_validate_command_keyboard_interrupt(runner, mock_config_manager):
    """Test validate command handles keyboard interrupt gracefully."""
    # Setup mock to raise KeyboardInterrupt during execution
    config = MagicMock(spec=['azure_openai'])
    config.azure_openai = None
    mock_config_manager.get_config.return_value = config
    
    # Simulate keyboard interrupt by patching console.print
    with patch("dev_agent.cli.main.console.print", side_effect=[None, KeyboardInterrupt()]):
        result = runner.invoke(app, ["validate"])

    # Verify graceful exit
    assert result.exit_code == 1


def test_validate_command_displays_suggestions(runner, mock_config_manager):
    """Test validate command displays helpful suggestions on failure."""
    # Setup mock with missing config
    from types import SimpleNamespace
    config = SimpleNamespace(azure_openai=None)
    mock_config_manager.get_config.return_value = config

    result = runner.invoke(app, ["validate"])

    # Verify suggestions are displayed
    assert "Suggested Solutions" in result.stdout or "suggestion" in result.stdout.lower()
    assert "setup" in result.stdout.lower()


def test_validate_command_skips_api_test_without_config(runner, mock_config_manager):
    """Test validate command skips API test when config is missing."""
    # Setup mock with missing config
    from types import SimpleNamespace
    config = SimpleNamespace(azure_openai=None)
    mock_config_manager.get_config.return_value = config

    result = runner.invoke(app, ["validate"])

    # Verify API test is skipped
    assert "Skip" in result.stdout or "skip" in result.stdout.lower()


def test_validate_command_shows_validation_table(runner, mock_config_manager, mock_azure_config):
    """Test validate command displays validation results table."""
    # Setup mocks
    mock_config_manager.get_config.return_value = mock_azure_config

    # Mock Azure client test
    with patch("dev_agent.llm.azure_client.AzureOpenAIClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.generate_completion = AsyncMock(return_value="OK")
        mock_client_class.return_value = mock_client

        # Mock file system operations
        with patch("pathlib.Path.write_text"), patch("pathlib.Path.unlink"), patch(
            "pathlib.Path.iterdir", return_value=[]
        ):
            result = runner.invoke(app, ["validate"])

    # Verify table is displayed
    assert "Validation Results" in result.stdout
    assert "Check" in result.stdout
    assert "Status" in result.stdout
    assert "Details" in result.stdout
