"""Tests for InteractiveCLI class."""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from dev_agent.cli.interactive_cli import InteractiveCLI
from dev_agent.models.enums import PhaseType


class TestInteractiveCLI(unittest.TestCase):
    """Test cases for InteractiveCLI."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_workflow_manager = Mock()
        self.cli = InteractiveCLI(self.mock_workflow_manager)

    def test_init_without_workflow_manager(self):
        """Test CLI initialization without workflow manager."""
        cli = InteractiveCLI()
        self.assertIsNone(cli.workflow_manager)
        self.assertFalse(cli.session_active)

    def test_init_with_workflow_manager(self):
        """Test CLI initialization with workflow manager."""
        self.assertEqual(self.cli.workflow_manager, self.mock_workflow_manager)
        self.assertFalse(self.cli.session_active)

    @patch("builtins.input")
    @patch("builtins.print")
    def test_start_chat_session_exit_command(self, mock_print, mock_input):
        """Test chat session with exit command."""
        mock_input.return_value = "exit"

        with patch.object(self.cli, "_graceful_exit") as mock_exit:
            self.cli.start_chat_session()
            mock_exit.assert_called_once()

    @patch("builtins.input")
    @patch("builtins.print")
    def test_start_chat_session_help_command(self, mock_print, mock_input):
        """Test chat session with help command."""
        mock_input.side_effect = ["help", "exit"]

        with patch.object(self.cli, "_graceful_exit") as mock_exit:
            with patch.object(self.cli, "_display_help") as mock_help:
                self.cli.start_chat_session()
                mock_help.assert_called_once()
                mock_exit.assert_called_once()

    def test_handle_user_input_empty(self):
        """Test handling empty user input."""
        result = self.cli.handle_user_input("")
        self.assertEqual(result, "")

        result = self.cli.handle_user_input("   ")
        self.assertEqual(result, "")

    def test_handle_user_input_init_command(self):
        """Test handling init command."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(self.cli, "init_command") as mock_init:
                result = self.cli.handle_user_input(f"init {temp_dir}")
                mock_init.assert_called_once_with(temp_dir)
                self.assertIn("Project initialized", result)

    def test_handle_user_input_init_command_current_dir(self):
        """Test handling init command without path."""
        with patch.object(self.cli, "init_command") as mock_init:
            with patch("os.getcwd", return_value="/current/dir"):
                result = self.cli.handle_user_input("init")
                mock_init.assert_called_once_with("/current/dir")
                self.assertIn("Project initialized", result)

    def test_handle_user_input_status_command(self):
        """Test handling status command."""
        self.mock_workflow_manager.get_current_phase.return_value = (
            PhaseType.SPECIFICATION
        )

        result = self.cli.handle_user_input("status")
        self.assertIn("specification", result)
        self.mock_workflow_manager.get_current_phase.assert_called_once()

    def test_handle_user_input_status_no_workflow_manager(self):
        """Test handling status command without workflow manager."""
        cli = InteractiveCLI()
        result = cli.handle_user_input("status")
        self.assertIn("No active project", result)

    def test_handle_user_input_unknown_command(self):
        """Test handling unknown command."""
        result = self.cli.handle_user_input("unknown_command")
        self.assertIn("Unknown command", result)
        self.assertIn("unknown_command", result)

    @patch("builtins.input")
    @patch("builtins.print")
    def test_request_approval_yes(self, mock_print, mock_input):
        """Test request approval with yes response."""
        mock_input.return_value = "y"

        result = self.cli.request_approval("Test document", "specification")
        self.assertTrue(result)

    @patch("builtins.input")
    @patch("builtins.print")
    def test_request_approval_no(self, mock_print, mock_input):
        """Test request approval with no response."""
        mock_input.return_value = "n"

        result = self.cli.request_approval("Test document", "specification")
        self.assertFalse(result)

    @patch("builtins.input")
    @patch("builtins.print")
    def test_request_approval_invalid_then_yes(self, mock_print, mock_input):
        """Test request approval with invalid response then yes."""
        mock_input.side_effect = ["invalid", "yes"]

        result = self.cli.request_approval("Test document", "specification")
        self.assertTrue(result)
        # Should have been called twice due to invalid input
        self.assertEqual(mock_input.call_count, 2)

    @patch("builtins.print")
    def test_display_progress(self, mock_print):
        """Test progress display."""
        self.cli.display_progress(PhaseType.INDEXING, 0.5)
        mock_print.assert_called()

        # Test completion (progress = 1.0)
        self.cli.display_progress(PhaseType.INDEXING, 1.0)
        self.assertEqual(mock_print.call_count, 2)

    def test_init_command_nonexistent_path(self):
        """Test init command with nonexistent path."""
        with self.assertRaises(ValueError):
            self.cli.init_command("/nonexistent/path")

    def test_init_command_existing_project(self):
        """Test init command with existing project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create .dev_agent directory to simulate existing project
            dev_agent_dir = os.path.join(temp_dir, ".dev_agent")
            os.makedirs(dev_agent_dir)

            with patch.object(self.cli, "display_message") as mock_display:
                self.cli.init_command(temp_dir)

                # Should call resume_project on workflow manager
                self.mock_workflow_manager.resume_project.assert_called_once_with(
                    temp_dir
                )
                mock_display.assert_called()

    def test_init_command_new_project(self):
        """Test init command with new project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(self.cli, "display_message") as mock_display:
                self.cli.init_command(temp_dir)

                # Should create directory structure
                self.assertTrue(os.path.exists(os.path.join(temp_dir, ".dev_agent")))
                self.assertTrue(
                    os.path.exists(os.path.join(temp_dir, ".dev_agent", "documents"))
                )
                self.assertTrue(
                    os.path.exists(os.path.join(temp_dir, ".dev_agent", "index"))
                )

                # Should call start_new_project on workflow manager
                self.mock_workflow_manager.start_new_project.assert_called_once_with(
                    temp_dir
                )
                mock_display.assert_called()

    @patch("builtins.print")
    def test_display_message(self, mock_print):
        """Test message display."""
        message = "Test message"
        self.cli.display_message(message)
        mock_print.assert_called_once_with(message)

    @patch("builtins.input")
    def test_get_user_input(self, mock_input):
        """Test getting user input."""
        mock_input.return_value = "test input"

        result = self.cli.get_user_input("Enter something: ")
        self.assertEqual(result, "test input")
        mock_input.assert_called_once_with("Enter something: ")

    @patch("builtins.print")
    def test_display_help(self, mock_print):
        """Test help display."""
        self.cli._display_help()
        mock_print.assert_called()

        # Check that help text contains expected commands
        call_args = mock_print.call_args[0][0]
        self.assertIn("init", call_args)
        self.assertIn("status", call_args)
        self.assertIn("help", call_args)
        self.assertIn("exit", call_args)

    @patch("sys.exit")
    @patch("builtins.print")
    def test_graceful_exit(self, mock_print, mock_exit):
        """Test graceful exit."""
        self.cli.session_active = True
        self.cli._graceful_exit()

        mock_print.assert_called()
        mock_exit.assert_called_once_with(0)
        self.assertFalse(self.cli.session_active)

    @patch.object(InteractiveCLI, "_graceful_exit")
    def test_handle_interrupt(self, mock_graceful_exit):
        """Test interrupt signal handling."""
        self.cli._handle_interrupt(2, None)  # SIGINT
        mock_graceful_exit.assert_called_once()

    def test_handle_user_input_cost_command(self):
        """Test handling cost command."""
        with patch.object(self.cli, "_display_cost_report") as mock_cost_report:
            result = self.cli.handle_user_input("cost")
            mock_cost_report.assert_called_once()
            self.assertEqual(result, "")

    def test_handle_user_input_cost_no_workflow_manager(self):
        """Test handling cost command without workflow manager."""
        cli = InteractiveCLI()
        result = cli.handle_user_input("cost")
        self.assertIn("No active project", result)

    @patch("dev_agent.cli.interactive_cli.console")
    def test_display_cost_summary(self, mock_console):
        """Test cost summary display."""
        from dev_agent.models.cost_tracking import CostReport
        from dev_agent.models.enums import PhaseType
        from datetime import datetime
        
        # Create a mock cost report
        mock_report = CostReport(
            total_prompt_tokens=1000,
            total_completion_tokens=2000,
            total_embedding_tokens=500,
            total_cost=0.15,
            operations_count=10,
            by_phase={PhaseType.INDEXING: 0.075},
            by_operation={},
            start_time=datetime.now(),
            end_time=datetime.now(),
        )
        
        self.mock_workflow_manager.cost_tracker.get_report.return_value = mock_report
        self.mock_workflow_manager.cost_tracker.check_budget_threshold.return_value = False
        
        self.cli.display_cost_summary()
        
        # Should call console.print with table
        mock_console.print.assert_called()

    @patch("dev_agent.cli.interactive_cli.console")
    def test_display_cost_summary_with_phase(self, mock_console):
        """Test cost summary display for specific phase."""
        from dev_agent.models.cost_tracking import CostReport
        from dev_agent.models.enums import PhaseType
        from datetime import datetime
        
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
        
        self.mock_workflow_manager.cost_tracker.get_phase_report.return_value = mock_report
        self.mock_workflow_manager.cost_tracker.check_budget_threshold.return_value = False
        
        self.cli.display_cost_summary(PhaseType.INDEXING)
        
        # Should call console.print with table
        mock_console.print.assert_called()

    @patch("dev_agent.cli.interactive_cli.console")
    def test_display_cost_summary_with_budget_warning(self, mock_console):
        """Test cost summary display with budget warning."""
        from dev_agent.models.cost_tracking import CostReport
        from datetime import datetime
        
        # Create a mock cost report
        mock_report = CostReport(
            total_prompt_tokens=10000,
            total_completion_tokens=20000,
            total_embedding_tokens=5000,
            total_cost=15.0,
            operations_count=100,
            by_phase={},
            by_operation={},
            start_time=datetime.now(),
            end_time=datetime.now(),
        )
        
        self.mock_workflow_manager.cost_tracker.get_report.return_value = mock_report
        self.mock_workflow_manager.cost_tracker.check_budget_threshold.return_value = True
        self.mock_workflow_manager.cost_tracker.get_current_cost.return_value = 15.0
        self.mock_workflow_manager.cost_tracker.budget_limit = 20.0
        
        self.cli.display_cost_summary()
        
        # Should display budget warning
        mock_console.print.assert_called()
        # Check that warning was displayed
        calls = [str(call) for call in mock_console.print.call_args_list]
        self.assertTrue(any("Budget Warning" in str(call) or "warning" in str(call).lower() for call in calls))

    @patch("dev_agent.cli.interactive_cli.console")
    def test_display_cost_report(self, mock_console):
        """Test detailed cost report display."""
        from dev_agent.models.cost_tracking import CostReport
        from dev_agent.models.enums import PhaseType, LLMOperationType
        from datetime import datetime
        
        # Create a mock cost report with detailed breakdown
        mock_report = CostReport(
            total_prompt_tokens=1000,
            total_completion_tokens=2000,
            total_embedding_tokens=500,
            total_cost=0.15,
            operations_count=10,
            by_phase={
                PhaseType.INDEXING: 0.05,
                PhaseType.SPECIFICATION: 0.10,
            },
            by_operation={
                LLMOperationType.COMPLETION.value: 5,
                LLMOperationType.EMBEDDING.value: 5,
            },
            start_time=datetime.now(),
            end_time=datetime.now(),
        )
        
        self.mock_workflow_manager.cost_tracker.get_report.return_value = mock_report
        
        self.cli._display_cost_report()
        
        # Should call console.print multiple times for different tables
        self.assertGreater(mock_console.print.call_count, 1)

    def test_display_cost_report_no_workflow_manager(self):
        """Test cost report display without workflow manager."""
        cli = InteractiveCLI()
        
        with patch("dev_agent.cli.interactive_cli.console") as mock_console:
            cli._display_cost_report()
            
            # Should display "No active project" message
            mock_console.print.assert_called()

    @patch("dev_agent.cli.interactive_cli.console")
    def test_display_streaming_progress(self, mock_console):
        """Test streaming progress display."""
        from dev_agent.models.enums import PhaseType
        
        result = self.cli.display_streaming_progress(PhaseType.SPECIFICATION, "Generating")
        
        # Should return progress and task objects
        self.assertIsNotNone(result)

    def test_handle_user_input_run_with_cost_display(self):
        """Test run command displays cost summary."""
        self.mock_workflow_manager.execute_complete_workflow.return_value = True
        
        with patch.object(self.cli, "display_cost_summary") as mock_cost_summary:
            result = self.cli.handle_user_input("run")
            
            # Should display cost summary after workflow
            mock_cost_summary.assert_called_once()
            self.assertIn("completed successfully", result)

    def test_handle_user_input_phase_with_cost_display(self):
        """Test phase command displays cost summary."""
        self.mock_workflow_manager.transition_to_phase.return_value = True
        
        # Mock display_cost_summary to avoid actual display logic
        with patch.object(self.cli, "display_cost_summary") as mock_cost_summary:
            result = self.cli.handle_user_input("phase INDEXING")
            
            # Verify the result indicates success
            self.assertIn("Successfully transitioned", result)
            # Cost summary should be called after successful phase transition via _display_cost_summary
            mock_cost_summary.assert_called_once()


if __name__ == "__main__":
    unittest.main()
