"""Integration tests for CLI commands."""

import json
import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from dev_agent.cli.main import CLIApplication
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
        app = CLIApplication()

        # Mock the interactive session to avoid hanging
        with patch.object(app, "_start_interactive_mode", return_value=0):
            result = app.run(["init", self.project_path])

        assert result == 0

        # Check that .dev_agent directory was created
        dev_agent_dir = os.path.join(self.project_path, ".dev_agent")
        assert os.path.exists(dev_agent_dir)
        assert os.path.exists(os.path.join(dev_agent_dir, "documents"))
        assert os.path.exists(os.path.join(dev_agent_dir, "index"))

    def test_init_command_nonexistent_path(self):
        """Test init command with nonexistent path."""
        app = CLIApplication()
        nonexistent_path = os.path.join(self.temp_dir, "nonexistent")

        result = app.run(["init", nonexistent_path])

        assert result == 1

    def test_resume_command_existing_project(self):
        """Test resume command on existing project."""
        app = CLIApplication()

        # First initialize the project
        with patch.object(app, "_start_interactive_mode", return_value=0):
            app.run(["init", self.project_path])

        # Then try to resume
        app2 = CLIApplication()
        with patch.object(app2, "_start_interactive_mode", return_value=0):
            result = app2.run(["resume", self.project_path])

        assert result == 0

    def test_resume_command_no_project(self):
        """Test resume command with no existing project."""
        app = CLIApplication()

        result = app.run(["resume", self.project_path])

        assert result == 1

    def test_config_show_command(self):
        """Test config show command."""
        app = CLIApplication()

        with patch("builtins.print") as mock_print:
            result = app.run(["config", "show"])

        assert result == 0
        mock_print.assert_called()

    def test_config_set_command(self):
        """Test config set command."""
        app = CLIApplication()

        with patch("builtins.print") as mock_print:
            result = app.run(["config", "set", "logging.level", "DEBUG"])

        assert result == 0
        mock_print.assert_called_with("Configuration updated: logging.level = DEBUG")

        # Verify the configuration was actually updated
        config = app.config_manager.get_config()
        assert config.logging.level == "DEBUG"

    def test_config_set_invalid_key(self):
        """Test config set command with invalid key format."""
        app = CLIApplication()

        result = app.run(["config", "set", "invalid_key", "value"])

        assert result == 1

    def test_config_reset_command(self):
        """Test config reset command."""
        app = CLIApplication()

        # First modify the config
        app.run(["config", "set", "logging.level", "DEBUG"])

        # Then reset it
        with patch("builtins.print") as mock_print:
            result = app.run(["config", "reset"])

        assert result == 0
        mock_print.assert_called_with("Configuration reset to defaults.")

        # Verify the configuration was reset
        config = app.config_manager.get_config()
        assert config.logging.level == "INFO"  # Default value

    def test_verbose_flag(self):
        """Test verbose flag enables debug logging."""
        app = CLIApplication()

        with patch("dev_agent.cli.main.setup_logging") as mock_setup:
            with patch.object(app, "_start_interactive_mode", return_value=0):
                result = app.run(["--verbose", "init", self.project_path])

        assert result == 0
        mock_setup.assert_called_once()
        # Check that verbose=True was passed
        call_args = mock_setup.call_args
        assert call_args[1]["verbose"] is True

    def test_config_path_argument(self):
        """Test custom config path argument."""
        custom_config_path = os.path.join(self.temp_dir, "custom_config.json")

        # Create a custom config file
        custom_config = DevAgentConfig.default()
        custom_config.logging.level = "WARNING"

        with open(custom_config_path, "w") as f:
            json.dump(custom_config.to_dict(), f)

        app = CLIApplication()
        app.config_manager = ConfigManager(custom_config_path)

        with patch("builtins.print") as mock_print:
            result = app.run(["config", "show"])

        assert result == 0
        # Verify the custom config was loaded
        config = app.config_manager.get_config()
        assert config.logging.level == "WARNING"

    def test_keyboard_interrupt_handling(self):
        """Test graceful handling of keyboard interrupt."""
        app = CLIApplication()

        with patch.object(app, "_start_interactive_mode", side_effect=KeyboardInterrupt):
            result = app.run(["init", self.project_path])

        assert result == 1

    def test_unexpected_exception_handling(self):
        """Test handling of unexpected exceptions."""
        app = CLIApplication()

        with patch.object(app, "_parse_arguments", side_effect=Exception("Test error")):
            result = app.run(["init", self.project_path])

        assert result == 1

    @patch("dev_agent.cli.main.InteractiveCLI")
    @patch("dev_agent.cli.main.SessionManager")
    def test_interactive_mode_default(self, mock_session_manager, mock_cli):
        """Test that interactive mode is started by default."""
        app = CLIApplication()

        # Mock the CLI to avoid hanging
        mock_cli_instance = MagicMock()
        mock_cli.return_value = mock_cli_instance

        result = app.run([self.project_path])

        assert result == 0
        mock_cli_instance.start_chat_session.assert_called_once()

    def test_project_config_loading(self):
        """Test loading of project-specific configuration."""
        app = CLIApplication()

        # Create project-specific config
        project_config_dir = os.path.join(self.project_path, ".dev_agent")
        os.makedirs(project_config_dir, exist_ok=True)

        project_config = DevAgentConfig.default()
        project_config.cli.auto_approve = True

        project_config_path = os.path.join(project_config_dir, "config.json")
        with open(project_config_path, "w") as f:
            json.dump(project_config.to_dict(), f)

        # Initialize project
        with patch.object(app, "_start_interactive_mode", return_value=0):
            result = app.run(["init", self.project_path])

        assert result == 0

        # Verify project config was loaded
        loaded_config = app.config_manager.load_project_config(self.project_path)
        assert loaded_config.cli.auto_approve is True


class TestCLIArgumentParsing:
    """Test CLI argument parsing."""

    def test_parse_init_command(self):
        """Test parsing init command."""
        app = CLIApplication()
        args = app._parse_arguments(["init", "/path/to/project"])

        assert args.command == "init"
        assert args.project_path == "/path/to/project"

    def test_parse_resume_command(self):
        """Test parsing resume command."""
        app = CLIApplication()
        args = app._parse_arguments(["resume"])

        assert args.command == "resume"
        assert args.project_path == os.getcwd()  # Default to current directory

    def test_parse_config_show(self):
        """Test parsing config show command."""
        app = CLIApplication()
        args = app._parse_arguments(["config", "show"])

        assert args.command == "config"
        assert args.config_action == "show"

    def test_parse_config_set(self):
        """Test parsing config set command."""
        app = CLIApplication()
        args = app._parse_arguments(["config", "set", "logging.level", "DEBUG"])

        assert args.command == "config"
        assert args.config_action == "set"
        assert args.key == "logging.level"
        assert args.value == "DEBUG"

    def test_parse_verbose_flag(self):
        """Test parsing verbose flag."""
        app = CLIApplication()
        args = app._parse_arguments(["--verbose", "init"])

        assert args.verbose is True
        assert args.command == "init"

    def test_parse_debug_flag(self):
        """Test parsing debug flag."""
        app = CLIApplication()
        args = app._parse_arguments(["--debug", "init"])

        assert args.debug is True
        assert args.command == "init"

    def test_parse_config_path(self):
        """Test parsing config path argument."""
        app = CLIApplication()
        args = app._parse_arguments(["--config-path", "/custom/config.json", "init"])

        assert args.config_path == "/custom/config.json"
        assert args.command == "init"

    def test_parse_default_interactive(self):
        """Test parsing with no command defaults to interactive."""
        app = CLIApplication()
        args = app._parse_arguments(["/path/to/project"])

        assert args.command is None
        assert args.project_path == "/path/to/project"


class TestConfigValueConversion:
    """Test configuration value conversion."""

    def test_convert_boolean_true(self):
        """Test converting 'true' to boolean."""
        app = CLIApplication()
        result = app._convert_config_value("true")
        assert result is True

    def test_convert_boolean_false(self):
        """Test converting 'false' to boolean."""
        app = CLIApplication()
        result = app._convert_config_value("false")
        assert result is False

    def test_convert_integer(self):
        """Test converting integer string."""
        app = CLIApplication()
        result = app._convert_config_value("42")
        assert result == 42
        assert isinstance(result, int)

    def test_convert_float(self):
        """Test converting float string."""
        app = CLIApplication()
        result = app._convert_config_value("3.14")
        assert result == 3.14
        assert isinstance(result, float)

    def test_convert_string(self):
        """Test converting regular string."""
        app = CLIApplication()
        result = app._convert_config_value("hello")
        assert result == "hello"
        assert isinstance(result, str)


if __name__ == "__main__":
    pytest.main([__file__])
