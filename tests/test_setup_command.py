"""Tests for the setup CLI command."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from dev_agent.cli.main import app


@pytest.fixture
def cli_runner():
    """Create CLI runner for testing."""
    return CliRunner()


def test_setup_help(cli_runner):
    """Test setup command help text."""
    result = cli_runner.invoke(app, ["setup", "--help"])
    
    assert result.exit_code == 0
    assert "Run interactive setup wizard" in result.stdout
    assert "Azure OpenAI credentials" in result.stdout
    assert "--status" in result.stdout


def test_setup_status_command_exists(cli_runner):
    """Test that setup --status command exists and runs."""
    result = cli_runner.invoke(app, ["setup", "--status"])
    
    # Command should run (may exit with 0 or 1 depending on config state)
    assert result.exit_code in [0, 1]
    # Should show configuration status
    assert "Configuration Status" in result.stdout or "Setup Status" in result.stdout


def test_setup_command_in_main_help(cli_runner):
    """Test that setup command appears in main help."""
    result = cli_runner.invoke(app, ["--help"])
    
    assert result.exit_code == 0
    assert "setup" in result.stdout.lower()
    assert "wizard" in result.stdout.lower() or "configuration" in result.stdout.lower()

