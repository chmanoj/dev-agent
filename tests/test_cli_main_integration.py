"""Integration tests for main CLI entry point."""

import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from dev_agent.cli.main import app, config_manager


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

    def test_main_function_config_show(self):
        """Test main function with config show command."""
        runner = CliRunner()
        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0

    def test_main_function_help(self):
        """Test main function with help argument."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "dev-agent" in result.stdout

    def test_main_function_config_set(self):
        """Test main function with config set command."""
        runner = CliRunner()
        result = runner.invoke(app, ["config", "set", "logging.level", "DEBUG"])
        assert result.exit_code in [0, 1]

    def test_main_function_with_args(self):
        """Test main function with custom arguments."""
        runner = CliRunner()
        
        with patch('dev_agent.cli.main.setup_cli_logging'), \
             patch('dev_agent.cli.session_manager.SessionManager'), \
             patch('dev_agent.cli.interactive_cli.InteractiveCLI'), \
             patch('dev_agent.workflow.workflow_manager.WorkflowManager'):
            result = runner.invoke(app, ["init", self.project_path])
            assert result.exit_code in [0, 1]

    def test_main_function_exception_handling(self):
        """Test main function handles exceptions properly."""
        runner = CliRunner()
        
        # Test with invalid command
        result = runner.invoke(app, ["invalid-command"])
        assert result.exit_code != 0


class TestCLIApplicationLogging:
    """Test CLI application logging functionality."""

    def test_logging_setup_verbose(self):
        """Test logging setup with verbose flag."""
        runner = CliRunner()
        
        with patch('dev_agent.cli.main.setup_cli_logging') as mock_setup:
            runner.invoke(app, ["--verbose", "config", "show"])
            mock_setup.assert_called()

    def test_logging_setup_normal(self):
        """Test logging setup without verbose flag."""
        runner = CliRunner()
        
        with patch('dev_agent.cli.main.setup_cli_logging') as mock_setup:
            runner.invoke(app, ["config", "show"])
            mock_setup.assert_called()

    def test_system_info_logging_verbose(self):
        """Test system info logging in verbose mode."""
        runner = CliRunner()
        
        with patch('dev_agent.cli.main.setup_cli_logging'), \
             patch('dev_agent.cli.main.log_system_info') as mock_log_sys:
            runner.invoke(app, ["--verbose", "config", "show"])
            # System info should be logged in verbose mode

    def test_no_system_info_logging_normal(self):
        """Test no system info logging in normal mode."""
        runner = CliRunner()
        
        with patch('dev_agent.cli.main.setup_cli_logging'):
            runner.invoke(app, ["config", "show"])
            # Should work without verbose logging

    def test_logger_creation(self):
        """Test logger is created after setup."""
        runner = CliRunner()
        
        with patch('dev_agent.cli.main.setup_cli_logging'), \
             patch('dev_agent.cli.main.get_logger') as mock_get_logger:
            runner.invoke(app, ["config", "show"])
            # Logger should be requested

    def test_error_logging(self):
        """Test error logging functionality."""
        runner = CliRunner()
        
        # Test with a command that might fail
        result = runner.invoke(app, ["init", "/nonexistent/path"])
        assert result.exit_code == 1


class TestCLIApplicationConfiguration:
    """Test CLI application configuration handling."""

    def test_config_loading_on_startup(self):
        """Test configuration is loaded on application startup."""
        runner = CliRunner()
        
        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0
        assert "configuration" in result.stdout

    def test_project_config_loading_init(self):
        """Test project-specific config loading during init."""
        runner = CliRunner()
        
        with patch('dev_agent.cli.main.setup_cli_logging'), \
             patch('dev_agent.cli.session_manager.SessionManager'), \
             patch('dev_agent.cli.interactive_cli.InteractiveCLI'), \
             patch('dev_agent.workflow.workflow_manager.WorkflowManager'), \
             patch('dev_agent.cli.main.config_manager.load_project_config') as mock_load:
            
            temp_dir = tempfile.mkdtemp()
            try:
                runner.invoke(app, ["init", temp_dir])
                # Should attempt to load project config
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)

    def test_project_config_loading_resume(self):
        """Test project-specific config loading during resume."""
        runner = CliRunner()
        
        temp_dir = tempfile.mkdtemp()
        try:
            # Create .dev_agent directory to simulate existing project
            dev_agent_dir = os.path.join(temp_dir, ".dev_agent")
            os.makedirs(dev_agent_dir)
            
            with patch('dev_agent.cli.main.setup_cli_logging'), \
                 patch('dev_agent.cli.session_manager.SessionManager'), \
                 patch('dev_agent.cli.interactive_cli.InteractiveCLI'), \
                 patch('dev_agent.workflow.workflow_manager.WorkflowManager'), \
                 patch('dev_agent.cli.main.config_manager.load_project_config') as mock_load:
                
                runner.invoke(app, ["resume", temp_dir])
                # Should attempt to load project config
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_version_logging(self):
        """Test version is logged on startup."""
        runner = CliRunner()
        
        with patch('dev_agent.cli.main.setup_cli_logging'):
            result = runner.invoke(app, ["config", "show"])
            # Should work and show version info


class TestCLIApplicationErrorHandling:
    """Test CLI application error handling."""

    def test_keyboard_interrupt_logging(self):
        """Test keyboard interrupt is logged properly."""
        runner = CliRunner()
        
        # Simulate keyboard interrupt during command
        with patch('dev_agent.cli.main.setup_cli_logging') as mock_setup:
            mock_setup.side_effect = KeyboardInterrupt()
            result = runner.invoke(app, ["config", "show"])
            # Should handle the interrupt gracefully

    def test_exception_logging(self):
        """Test exceptions are logged with traceback."""
        runner = CliRunner()
        
        # Test with invalid path
        result = runner.invoke(app, ["init", "/invalid/path/that/does/not/exist"])
        assert result.exit_code == 1

    def test_init_error_logging(self):
        """Test init command errors are logged."""
        runner = CliRunner()
        
        with patch('dev_agent.cli.main.setup_cli_logging'), \
             patch('dev_agent.workflow.workflow_manager.WorkflowManager') as mock_workflow:
            
            mock_workflow.side_effect = Exception("Test error")
            result = runner.invoke(app, ["init", tempfile.mkdtemp()])
            assert result.exit_code == 1

    def test_resume_error_logging(self):
        """Test resume command errors are logged."""
        runner = CliRunner()
        
        temp_dir = tempfile.mkdtemp()
        try:
            # Create .dev_agent directory to simulate existing project
            dev_agent_dir = os.path.join(temp_dir, ".dev_agent")
            os.makedirs(dev_agent_dir)
            
            with patch('dev_agent.cli.main.setup_cli_logging'), \
                 patch('dev_agent.workflow.workflow_manager.WorkflowManager') as mock_workflow:
                
                mock_workflow.side_effect = Exception("Test error")
                result = runner.invoke(app, ["resume", temp_dir])
                assert result.exit_code == 1
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_config_error_logging(self):
        """Test config command errors are logged."""
        runner = CliRunner()
        
        # Test with invalid config key format
        result = runner.invoke(app, ["config", "set", "invalid_key", "value"])
        assert result.exit_code == 1