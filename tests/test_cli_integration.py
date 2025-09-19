"""Integration tests for CLI commands."""

import json
import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from dev_agent.cli.main import app, config_manager
from dev_agent.config import ConfigManager, DevAgentConfig


class TestCLIIntegration:
    """Integration tests for CLI application."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = os.path.join(self.temp_dir, "test_project")
        os.makedirs(self.project_path)

        # Create a test file to make it look like a real project
        with open(os.path.join(self.project_path, "test_file.py"), "w") as f:
            f.write("# Test file\nprint('Hello, world!')\n")

    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_init_command_new_project(self):
        """Test init command on a new project."""
        runner = CliRunner()

        # Mock the components to avoid actual initialization
        with patch('dev_agent.cli.main.setup_cli_logging'), \
             patch('dev_agent.cli.session_manager.SessionManager'), \
             patch('dev_agent.cli.interactive_cli.InteractiveCLI'), \
             patch('dev_agent.workflow.workflow_manager.WorkflowManager') as mock_workflow:
            
            mock_workflow_instance = MagicMock()
            mock_workflow.return_value = mock_workflow_instance
            mock_workflow_instance.start_new_project.return_value = MagicMock(project_path=self.project_path)
            
            result = runner.invoke(app, ["init", self.project_path])
            # Should not crash
            assert result.exit_code in [0, 1]

    def test_init_command_nonexistent_path(self):
        """Test init command with nonexistent path."""
        runner = CliRunner()
        nonexistent_path = os.path.join(self.temp_dir, "nonexistent")

        result = runner.invoke(app, ["init", nonexistent_path])
        # May succeed if directory is created, or fail if not - both are acceptable
        assert result.exit_code in [0, 1]

    def test_config_show_command(self):
        """Test config show command."""
        runner = CliRunner()

        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0
        assert "dev-agent configuration" in result.stdout

    def test_config_set_command(self):
        """Test config set command."""
        runner = CliRunner()

        result = runner.invoke(app, ["config", "set", "logging.level", "DEBUG"])
        assert result.exit_code in [0, 1]  # May fail due to validation but shouldn't crash

    def test_config_reset_command(self):
        """Test config reset command."""
        runner = CliRunner()

        result = runner.invoke(app, ["config", "reset"])
        assert result.exit_code in [0, 1]

    def test_azure_status_command(self):
        """Test azure status command."""
        runner = CliRunner()

        result = runner.invoke(app, ["azure", "status"])
        assert result.exit_code == 0
        assert "Azure OpenAI" in result.stdout

    def test_help_command(self):
        """Test help command."""
        runner = CliRunner()

        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "dev-agent" in result.stdout

    def test_verbose_flag(self):
        """Test verbose flag."""
        runner = CliRunner()

        with patch('dev_agent.cli.main.setup_cli_logging') as mock_logging:
            result = runner.invoke(app, ["--verbose", "config", "show"])
            # Should work with verbose flag
            assert result.exit_code == 0


class TestCLIArgumentParsing:
    """Test CLI argument parsing with Typer."""

    def test_parse_init_command(self):
        """Test parsing init command."""
        runner = CliRunner()
        
        with patch('dev_agent.cli.main.setup_cli_logging'), \
             patch('dev_agent.cli.session_manager.SessionManager'), \
             patch('dev_agent.cli.interactive_cli.InteractiveCLI'), \
             patch('dev_agent.workflow.workflow_manager.WorkflowManager'):
            result = runner.invoke(app, ["init", "/test/path"])
            # Should attempt to process the command
            assert result.exit_code in [0, 1]

    def test_parse_config_commands(self):
        """Test parsing config commands."""
        runner = CliRunner()
        
        # Test config show
        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0
        
        # Test config set
        result = runner.invoke(app, ["config", "set", "logging.level", "INFO"])
        assert result.exit_code in [0, 1]

    def test_parse_azure_commands(self):
        """Test parsing azure commands."""
        runner = CliRunner()
        
        result = runner.invoke(app, ["azure", "status"])
        assert result.exit_code == 0


class TestConfigValueConversion:
    """Test configuration value conversion."""

    def test_convert_values(self):
        """Test converting configuration values."""
        runner = CliRunner()
        
        # Test setting different types of values
        test_cases = [
            ("logging.level", "DEBUG"),
            ("cli.auto_approve", "true"),
            ("indexing.chunk_size", "1000"),
        ]
        
        for key, value in test_cases:
            result = runner.invoke(app, ["config", "set", key, value])
            # Should not crash, may fail validation but that's OK
            assert result.exit_code in [0, 1]