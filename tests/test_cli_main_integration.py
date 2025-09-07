"""Integration tests for main CLI entry point."""

import os
import shutil
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from dev_agent.cli.main import CLIApplication, main


class TestMainEntryPoint:
    """Test the main entry point function."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = os.path.join(self.temp_dir, "test_project")
        os.makedirs(self.project_path)

    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch("sys.argv", ["dev-agent", "config", "show"])
    def test_main_function_config_show(self):
        """Test main function with config show command."""
        with patch("builtins.print"):
            result = main()

        assert result == 0

    @patch("sys.argv", ["dev-agent", "--help"])
    def test_main_function_help(self):
        """Test main function with help argument."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        # argparse exits with code 0 for help
        assert exc_info.value.code == 0

    @patch("sys.argv", ["dev-agent", "config", "set", "logging.level", "DEBUG"])
    def test_main_function_config_set(self):
        """Test main function with config set command."""
        with patch("builtins.print"):
            result = main()

        assert result == 0

    def test_main_function_with_args(self):
        """Test main function with custom arguments."""
        # Create a temporary config to avoid modifying global config
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"version": "0.1.0", "logging": {"level": "INFO"}, "cli": {"auto_approve": false}, "indexing": {"embedding_model": "test"}}')
            temp_config = f.name

        try:
            with patch("dev_agent.cli.main.CLIApplication") as mock_app_class:
                mock_app = MagicMock()
                mock_app.run.return_value = 0
                mock_app_class.return_value = mock_app

                # Patch sys.argv to simulate command line arguments
                with patch.object(sys, "argv", ["dev-agent", "--config-path", temp_config, "config", "show"]):
                    result = main()

                assert result == 0
                mock_app.run.assert_called_once()
        finally:
            os.unlink(temp_config)

    def test_main_function_exception_handling(self):
        """Test main function handles exceptions properly."""
        with patch("dev_agent.cli.main.CLIApplication") as mock_app_class:
            mock_app = MagicMock()
            mock_app.run.side_effect = Exception("Test error")
            mock_app_class.return_value = mock_app

            with patch.object(sys, "argv", ["dev-agent", "config", "show"]):
                result = main()

            assert result == 1


class TestCLIApplicationLogging:
    """Test CLI application logging functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = os.path.join(self.temp_dir, "test_project")
        os.makedirs(self.project_path)

    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_logging_setup_verbose(self):
        """Test logging setup with verbose flag."""
        app = CLIApplication()

        with patch("dev_agent.config.logging_config.setup_logging") as mock_setup:
            with patch.object(app, "_start_interactive_mode", return_value=0):
                result = app.run(["--verbose", "init", self.project_path])

        assert result == 0
        mock_setup.assert_called_once()

        # Verify verbose=True was passed
        call_args = mock_setup.call_args
        assert call_args[1]["verbose"] is True

    def test_logging_setup_normal(self):
        """Test logging setup without verbose flag."""
        app = CLIApplication()

        with patch("dev_agent.config.logging_config.setup_logging") as mock_setup:
            with patch.object(app, "_start_interactive_mode", return_value=0):
                result = app.run(["init", self.project_path])

        assert result == 0
        mock_setup.assert_called_once()

        # Verify verbose=False was passed
        call_args = mock_setup.call_args
        assert call_args[1]["verbose"] is False

    def test_system_info_logging_verbose(self):
        """Test system info logging in verbose mode."""
        app = CLIApplication()

        with patch("dev_agent.config.logging_config.log_system_info") as mock_log_sys:
            with patch("dev_agent.config.logging_config.log_config_info") as mock_log_config:
                with patch.object(app, "_start_interactive_mode", return_value=0):
                    result = app.run(["--verbose", "init", self.project_path])

        assert result == 0
        mock_log_sys.assert_called_once()
        mock_log_config.assert_called_once()

    def test_no_system_info_logging_normal(self):
        """Test no system info logging in normal mode."""
        app = CLIApplication()

        with patch("dev_agent.config.logging_config.log_system_info") as mock_log_sys:
            with patch("dev_agent.config.logging_config.log_config_info") as mock_log_config:
                with patch.object(app, "_start_interactive_mode", return_value=0):
                    result = app.run(["init", self.project_path])

        assert result == 0
        mock_log_sys.assert_not_called()
        mock_log_config.assert_not_called()

    def test_logger_creation(self):
        """Test logger is created after setup."""
        app = CLIApplication()

        with patch.object(app, "_start_interactive_mode", return_value=0):
            result = app.run(["init", self.project_path])

        assert result == 0
        assert app.logger is not None

    def test_error_logging(self):
        """Test error logging functionality."""
        app = CLIApplication()

        with patch.object(app, "_parse_arguments", side_effect=Exception("Test error")):
            with patch("dev_agent.config.logging_config.setup_logging"):
                with patch("dev_agent.config.logging_config.get_logger") as mock_get_logger:
                    mock_logger = MagicMock()
                    mock_get_logger.return_value = mock_logger

                    result = app.run(["init", self.project_path])

        assert result == 1
        # Logger should be created and error should be logged
        mock_get_logger.assert_called()


class TestCLIApplicationConfiguration:
    """Test CLI application configuration management."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = os.path.join(self.temp_dir, "test_project")
        os.makedirs(self.project_path)

    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_config_loading_on_startup(self):
        """Test configuration is loaded on application startup."""
        app = CLIApplication()

        with patch.object(app.config_manager, "load_config") as mock_load:
            with patch.object(app, "_start_interactive_mode", return_value=0):
                result = app.run(["init", self.project_path])

        assert result == 0
        mock_load.assert_called_once()

    def test_project_config_loading_init(self):
        """Test project-specific config loading during init."""
        app = CLIApplication()

        with patch.object(app.config_manager, "load_project_config") as mock_load_project:
            with patch.object(app, "_start_interactive_mode", return_value=0):
                result = app.run(["init", self.project_path])

        assert result == 0
        mock_load_project.assert_called_once_with(self.project_path)

    def test_project_config_loading_resume(self):
        """Test project-specific config loading during resume."""
        # Create .dev_agent directory to simulate existing project
        dev_agent_dir = os.path.join(self.project_path, ".dev_agent")
        os.makedirs(dev_agent_dir)

        app = CLIApplication()

        with patch.object(app.config_manager, "load_project_config") as mock_load_project:
            with patch("dev_agent.cli.main.SessionManager") as mock_session_manager:
                mock_session = MagicMock()
                mock_session.resume_session.return_value = MagicMock()
                mock_session_manager.return_value = mock_session

                with patch.object(app, "_start_interactive_mode", return_value=0):
                    result = app.run(["resume", self.project_path])

        assert result == 0
        mock_load_project.assert_called_once_with(self.project_path)

    def test_version_logging(self):
        """Test version is logged on startup."""
        app = CLIApplication()

        with patch("dev_agent.config.logging_config.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            with patch.object(app, "_start_interactive_mode", return_value=0):
                result = app.run(["init", self.project_path])

        assert result == 0
        # Check that version was logged
        mock_logger.info.assert_any_call("Starting dev-agent v0.1.0")


class TestCLIApplicationErrorHandling:
    """Test CLI application error handling."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = os.path.join(self.temp_dir, "test_project")
        os.makedirs(self.project_path)

    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_keyboard_interrupt_logging(self):
        """Test keyboard interrupt is logged properly."""
        app = CLIApplication()

        with patch("dev_agent.config.logging_config.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            with patch.object(app, "_start_interactive_mode", side_effect=KeyboardInterrupt):
                result = app.run(["init", self.project_path])

        assert result == 1
        mock_logger.info.assert_any_call("Operation cancelled by user")

    def test_exception_logging(self):
        """Test exceptions are logged with traceback."""
        app = CLIApplication()

        with patch("dev_agent.config.logging_config.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            with patch.object(app, "_parse_arguments", side_effect=Exception("Test error")):
                result = app.run(["init", self.project_path])

        assert result == 1
        # Check that error was logged with traceback
        mock_logger.error.assert_called_with("Unexpected error: Test error", exc_info=True)

    def test_init_error_logging(self):
        """Test init command errors are logged."""
        app = CLIApplication()

        with patch("dev_agent.config.logging_config.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            with patch.object(app, "_start_interactive_mode", side_effect=Exception("Init error")):
                result = app.run(["init", self.project_path])

        assert result == 1
        mock_logger.error.assert_called()

    def test_resume_error_logging(self):
        """Test resume command errors are logged."""
        # Create .dev_agent directory to simulate existing project
        dev_agent_dir = os.path.join(self.project_path, ".dev_agent")
        os.makedirs(dev_agent_dir)

        app = CLIApplication()

        with patch("dev_agent.config.logging_config.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            with patch("dev_agent.cli.main.SessionManager", side_effect=Exception("Resume error")):
                result = app.run(["resume", self.project_path])

        assert result == 1
        mock_logger.error.assert_called()

    def test_config_error_logging(self):
        """Test config command errors are logged."""
        app = CLIApplication()

        with patch("dev_agent.config.logging_config.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            with patch.object(app, "_show_config", side_effect=Exception("Config error")):
                result = app.run(["config", "show"])

        assert result == 1
        mock_logger.error.assert_called()


if __name__ == "__main__":
    pytest.main([__file__])
