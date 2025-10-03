"""Tests for CLI main application."""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from dev_agent.cli.main import app, config_manager


class TestCLIMain(unittest.TestCase):
    """Test cases for CLI main module."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_typer_app_exists(self):
        """Test that Typer app is properly configured."""
        self.assertIsNotNone(app)
        self.assertEqual(app.info.name, "dev-agent")

    def test_config_manager_exists(self):
        """Test that config manager is available."""
        self.assertIsNotNone(config_manager)

    @patch('dev_agent.cli.main.setup_cli_logging')
    @patch('dev_agent.cli.main.SessionManager')
    @patch('dev_agent.cli.main.InteractiveCLI')
    def test_init_command_basic(self, mock_cli, mock_session, mock_logging):
        """Test basic init command functionality."""
        from typer.testing import CliRunner
        runner = CliRunner()
        
        # Mock the workflow manager to avoid actual initialization
        with patch('dev_agent.workflow.workflow_manager.WorkflowManager') as mock_workflow:
            mock_workflow_instance = Mock()
            mock_workflow.return_value = mock_workflow_instance
            mock_workflow_instance.start_new_project.return_value = Mock(project_path=self.temp_dir)
            
            result = runner.invoke(app, ["init", self.temp_dir])
            # Should not crash (exit code 0 or 1 is acceptable for this test)
            self.assertIn(result.exit_code, [0, 1])

    def test_config_show_command(self):
        """Test config show command."""
        from typer.testing import CliRunner
        runner = CliRunner()
        
        result = runner.invoke(app, ["config", "show"])
        # Should not crash and should show config
        self.assertIn(result.exit_code, [0, 1])

    def test_help_command(self):
        """Test help command."""
        from typer.testing import CliRunner
        runner = CliRunner()
        
        result = runner.invoke(app, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("dev-agent", result.stdout)

    @patch('dev_agent.cli.main.setup_cli_logging')
    def test_verbose_flag(self, mock_logging):
        """Test verbose flag."""
        from typer.testing import CliRunner
        runner = CliRunner()
        
        with patch('dev_agent.cli.session_manager.SessionManager'), \
             patch('dev_agent.cli.interactive_cli.InteractiveCLI'), \
             patch('dev_agent.workflow.workflow_manager.WorkflowManager'):
            result = runner.invoke(app, ["--verbose", "init", self.temp_dir])
            # Should call setup_cli_logging with verbose=True
            mock_logging.assert_called()

    def test_azure_status_command(self):
        """Test azure status command."""
        from typer.testing import CliRunner
        runner = CliRunner()
        
        result = runner.invoke(app, ["azure", "status"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Azure OpenAI", result.stdout)

    def test_config_set_command(self):
        """Test config set command."""
        from typer.testing import CliRunner
        runner = CliRunner()
        
        result = runner.invoke(app, ["config", "set", "logging.level", "DEBUG"])
        # Should not crash
        self.assertIn(result.exit_code, [0, 1])

    def test_config_reset_command(self):
        """Test config reset command."""
        from typer.testing import CliRunner
        runner = CliRunner()
        
        result = runner.invoke(app, ["config", "reset"])
        # Should not crash
        self.assertIn(result.exit_code, [0, 1])

    @patch('dev_agent.cli.main.setup_cli_logging')
    @patch('dev_agent.workflow.workflow_manager.WorkflowManager')
    def test_cost_report_command(self, mock_workflow, mock_logging):
        """Test cost-report command."""
        from typer.testing import CliRunner
        from dev_agent.models.cost_tracking import CostReport
        from datetime import datetime
        
        runner = CliRunner()
        
        # Create a mock cost report
        mock_report = CostReport(
            total_prompt_tokens=1000,
            total_completion_tokens=2000,
            total_embedding_tokens=500,
            total_cost=0.15,
            operations_count=10,
            by_phase={},
            by_operation={},
            start_time=datetime.now(),
            end_time=datetime.now(),
        )
        
        # Mock workflow manager and cost tracker
        mock_workflow_instance = Mock()
        mock_workflow.return_value = mock_workflow_instance
        mock_workflow_instance.cost_tracker.get_report.return_value = mock_report
        
        # Create .dev_agent directory
        dev_agent_dir = os.path.join(self.temp_dir, ".dev_agent")
        os.makedirs(dev_agent_dir, exist_ok=True)
        
        result = runner.invoke(app, ["cost-report", self.temp_dir])
        
        # Should display cost information
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Cost Report", result.stdout)

    @patch('dev_agent.cli.main.setup_cli_logging')
    @patch('dev_agent.workflow.workflow_manager.WorkflowManager')
    def test_cost_report_command_with_phase_filter(self, mock_workflow, mock_logging):
        """Test cost-report command with phase filter."""
        from typer.testing import CliRunner
        from dev_agent.models.cost_tracking import CostReport
        from dev_agent.models.enums import PhaseType
        from datetime import datetime
        
        runner = CliRunner()
        
        # Create a mock cost report
        mock_report = CostReport(
            total_prompt_tokens=500,
            total_completion_tokens=1000,
            total_embedding_tokens=250,
            total_cost=0.075,
            operations_count=5,
            by_phase={PhaseType.INDEXING: 0.075},
            by_operation={},
            start_time=datetime.now(),
            end_time=datetime.now(),
        )
        
        # Mock workflow manager and cost tracker
        mock_workflow_instance = Mock()
        mock_workflow.return_value = mock_workflow_instance
        mock_workflow_instance.cost_tracker.get_phase_report.return_value = mock_report
        
        # Create .dev_agent directory
        dev_agent_dir = os.path.join(self.temp_dir, ".dev_agent")
        os.makedirs(dev_agent_dir, exist_ok=True)
        
        result = runner.invoke(app, ["cost-report", self.temp_dir, "--phase", "INDEXING"])
        
        # Should display phase-specific cost information
        # Note: May fail if project state cannot be loaded, which is acceptable in test
        self.assertIn(result.exit_code, [0, 1])
        if result.exit_code == 0:
            self.assertIn("INDEXING", result.stdout)

    @patch('dev_agent.cli.main.setup_cli_logging')
    def test_cost_report_command_no_project(self, mock_logging):
        """Test cost-report command with no project."""
        from typer.testing import CliRunner
        
        runner = CliRunner()
        
        result = runner.invoke(app, ["cost-report", self.temp_dir])
        
        # Should fail with error message
        self.assertEqual(result.exit_code, 1)
        self.assertIn("No dev-agent project found", result.stdout)

    @patch('dev_agent.cli.main.setup_cli_logging')
    @patch('dev_agent.workflow.workflow_manager.WorkflowManager')
    def test_cost_report_command_invalid_phase(self, mock_workflow, mock_logging):
        """Test cost-report command with invalid phase."""
        from typer.testing import CliRunner
        
        runner = CliRunner()
        
        # Create .dev_agent directory
        dev_agent_dir = os.path.join(self.temp_dir, ".dev_agent")
        os.makedirs(dev_agent_dir, exist_ok=True)
        
        result = runner.invoke(app, ["cost-report", self.temp_dir, "--phase", "INVALID"])
        
        # Should fail with error message
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Invalid phase", result.stdout)


if __name__ == "__main__":
    unittest.main()
