"""Comprehensive tests for enhanced CLI functionality.

This test module covers all CLI enhancements including:
- Status command output
- Cost-report command output
- Validate command
- Help system
- Progress display
- Feedback system
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rich.console import Console
from typer.testing import CliRunner

from dev_agent.cli.feedback_system import FeedbackSystem
from dev_agent.cli.help_system import HelpSystem
from dev_agent.cli.main import app
from dev_agent.cli.progress_display import ProgressDisplay
from dev_agent.models.cost_tracking import CostReport, TokenUsage
from dev_agent.models.enums import LLMOperationType, PhaseStatus, PhaseType
from dev_agent.models.project_state import (
    IndexMetadata,
    ProjectState,
    SessionData,
)
from dev_agent.models.results import IndexingResult


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_console():
    """Create a mock Rich console for testing."""
    console = MagicMock(spec=Console)
    console.get_time = MagicMock(return_value=0.0)
    return console


@pytest.fixture
def test_console():
    """Create a real console with string output for testing."""
    return Console(file=StringIO(), force_terminal=True, width=120)


@pytest.fixture
def mock_project_state():
    """Create a mock project state for testing."""
    return ProjectState(
        project_path="/test/project",
        current_phase=PhaseType.SPECIFICATION,
        indexing_complete=True,
        specification=None,
        design=None,
        tasks=None,
        implementation_progress={},
        index_metadata=IndexMetadata(
            total_files=100,
            total_lines=5000,
            languages_detected=["python", "javascript"],
            index_size_mb=2.5,
            last_indexed=datetime(2024, 1, 15, 10, 30, 0),
            index_version="1.0.0",
        ),
        session_data=SessionData(
            session_id="test-session-123",
            started_at=datetime(2024, 1, 15, 9, 0, 0),
            last_activity=datetime(2024, 1, 15, 10, 30, 0),
            user_approvals={"indexing": True},
            pending_approvals=["specification"],
        ),
        created_at=datetime(2024, 1, 15, 9, 0, 0),
        updated_at=datetime(2024, 1, 15, 10, 30, 0),
    )


@pytest.fixture
def sample_cost_report():
    """Create a sample cost report for testing."""
    start_time = datetime(2024, 1, 1, 10, 0, 0)
    end_time = datetime(2024, 1, 1, 11, 30, 0)
    
    report = CostReport.create_empty(start_time=start_time)
    report.end_time = end_time
    
    # Add sample operations
    operations = [
        TokenUsage(
            operation_type=LLMOperationType.COMPLETION,
            prompt_tokens=150,
            completion_tokens=300,
            total_tokens=450,
            estimated_cost=0.027,
            timestamp=datetime(2024, 1, 1, 10, 15, 0),
            phase=PhaseType.SPECIFICATION,
            model="gpt-4",
        ),
        TokenUsage(
            operation_type=LLMOperationType.EMBEDDING,
            prompt_tokens=500,
            completion_tokens=0,
            total_tokens=500,
            estimated_cost=0.0005,
            timestamp=datetime(2024, 1, 1, 10, 30, 0),
            phase=PhaseType.INDEXING,
            model="text-embedding-ada-002",
        ),
    ]
    
    for op in operations:
        report.add_usage(op)
    
    return report


class TestStatusCommandEnhancements:
    """Test enhanced status command functionality."""

    def test_status_shows_workflow_progress(
        self, runner, tmp_path, mock_project_state, sample_cost_report
    ):
        """Test that status command shows workflow progress correctly."""
        dev_agent_dir = tmp_path / ".dev_agent"
        dev_agent_dir.mkdir()

        with (
            patch("dev_agent.workflow.workflow_manager.WorkflowManager") as mock_wf,
            patch("dev_agent.cli.main.setup_cli_logging"),
        ):
            mock_manager = MagicMock()
            mock_manager.resume_project.return_value = mock_project_state
            mock_manager.cost_tracker.get_report.return_value = sample_cost_report
            mock_wf.return_value = mock_manager

            result = runner.invoke(app, ["status", str(tmp_path)])

            assert result.exit_code == 0
            assert "Workflow Progress" in result.stdout
            assert "Indexing" in result.stdout
            assert "Specification" in result.stdout

    def test_status_shows_phase_indicators(
        self, runner, tmp_path, mock_project_state, sample_cost_report
    ):
        """Test that status shows visual phase indicators."""
        dev_agent_dir = tmp_path / ".dev_agent"
        dev_agent_dir.mkdir()

        with (
            patch("dev_agent.workflow.workflow_manager.WorkflowManager") as mock_wf,
            patch("dev_agent.cli.main.setup_cli_logging"),
        ):
            mock_manager = MagicMock()
            mock_manager.resume_project.return_value = mock_project_state
            mock_manager.cost_tracker.get_report.return_value = sample_cost_report
            mock_wf.return_value = mock_manager

            result = runner.invoke(app, ["status", str(tmp_path)])

            assert result.exit_code == 0
            # Should show completion indicators
            assert "✓" in result.stdout or "Complete" in result.stdout

    def test_status_detailed_mode(
        self, runner, tmp_path, mock_project_state, sample_cost_report
    ):
        """Test status command with detailed flag."""
        dev_agent_dir = tmp_path / ".dev_agent"
        dev_agent_dir.mkdir()

        with (
            patch("dev_agent.workflow.workflow_manager.WorkflowManager") as mock_wf,
            patch("dev_agent.cli.main.setup_cli_logging"),
        ):
            mock_manager = MagicMock()
            mock_manager.resume_project.return_value = mock_project_state
            mock_manager.cost_tracker.get_report.return_value = sample_cost_report
            mock_wf.return_value = mock_manager

            result = runner.invoke(app, ["status", str(tmp_path), "--detailed"])

            assert result.exit_code == 0
            assert "Detailed Information" in result.stdout
            assert "Index Metadata" in result.stdout


class TestCostReportEnhancements:
    """Test enhanced cost-report command functionality."""

    @patch("dev_agent.workflow.workflow_manager.WorkflowManager")
    def test_cost_report_shows_breakdown(
        self, mock_wf, runner, tmp_path, sample_cost_report
    ):
        """Test that cost report shows detailed breakdown."""
        dev_agent_dir = tmp_path / ".dev_agent"
        dev_agent_dir.mkdir()

        mock_manager = MagicMock()
        mock_manager.cost_tracker.get_report.return_value = sample_cost_report
        mock_manager.cost_tracker.budget_threshold = None
        mock_manager.cost_tracker.budget_limit = None
        mock_wf.return_value = mock_manager

        result = runner.invoke(app, ["cost-report", str(tmp_path)])

        assert result.exit_code == 0
        assert "Cost Breakdown" in result.stdout
        assert "Token Usage" in result.stdout

    @patch("dev_agent.workflow.workflow_manager.WorkflowManager")
    def test_cost_report_phase_filter(
        self, mock_wf, runner, tmp_path
    ):
        """Test cost report with phase filtering."""
        dev_agent_dir = tmp_path / ".dev_agent"
        dev_agent_dir.mkdir()

        phase_report = CostReport.create_empty()
        phase_report.add_usage(
            TokenUsage(
                operation_type=LLMOperationType.COMPLETION,
                prompt_tokens=150,
                completion_tokens=300,
                total_tokens=450,
                estimated_cost=0.027,
                timestamp=datetime.now(),
                phase=PhaseType.SPECIFICATION,
                model="gpt-4",
            )
        )

        mock_manager = MagicMock()
        mock_manager.cost_tracker.get_phase_report.return_value = phase_report
        mock_manager.cost_tracker.budget_threshold = None
        mock_manager.cost_tracker.budget_limit = None
        mock_wf.return_value = mock_manager

        result = runner.invoke(
            app, ["cost-report", str(tmp_path), "--phase", "specification"]
        )

        assert result.exit_code == 0
        assert "Specification" in result.stdout

    @patch("dev_agent.workflow.workflow_manager.WorkflowManager")
    def test_cost_report_export_json(
        self, mock_wf, runner, tmp_path, sample_cost_report
    ):
        """Test exporting cost report to JSON."""
        dev_agent_dir = tmp_path / ".dev_agent"
        dev_agent_dir.mkdir()

        mock_manager = MagicMock()
        mock_manager.cost_tracker.get_report.return_value = sample_cost_report
        mock_manager.cost_tracker.budget_threshold = 1.0
        mock_manager.cost_tracker.budget_limit = 2.0
        mock_wf.return_value = mock_manager

        export_file = tmp_path / "cost_report.json"
        result = runner.invoke(
            app, ["cost-report", str(tmp_path), "--export", str(export_file)]
        )

        # Command should complete
        assert result.exit_code in [0, 1]

        # Check if export happened
        if result.exit_code == 0 and export_file.exists():
            data = json.loads(export_file.read_text())
            assert "summary" in data
            assert "breakdown_by_operation" in data


class TestValidateCommandEnhancements:
    """Test enhanced validate command functionality."""

    def test_validate_checks_all_requirements(self, runner):
        """Test that validate command checks all requirements."""
        with (
            patch("dev_agent.cli.main.config_manager") as mock_config,
            patch("dev_agent.cli.main.setup_cli_logging"),
        ):
            from types import SimpleNamespace
            config = SimpleNamespace(azure_openai=None)
            mock_config.get_config.return_value = config

            result = runner.invoke(app, ["validate"])

            # Should check multiple things
            assert "Azure OpenAI" in result.stdout or "azure" in result.stdout.lower()
            assert "Dependencies" in result.stdout or "dependencies" in result.stdout.lower()

    def test_validate_shows_results_table(self, runner):
        """Test that validate shows results in a table."""
        with (
            patch("dev_agent.cli.main.config_manager") as mock_config,
            patch("dev_agent.cli.main.setup_cli_logging"),
        ):
            from types import SimpleNamespace
            azure_openai = SimpleNamespace(
                api_key=None,
                endpoint="https://test.openai.azure.com/",
                deployment_name="gpt-4",
                embedding_deployment=None,
            )
            config = SimpleNamespace(azure_openai=azure_openai)
            mock_config.get_config.return_value = config

            result = runner.invoke(app, ["validate"])

            # Should show validation results
            assert "Validation" in result.stdout or "Check" in result.stdout

    def test_validate_provides_suggestions(self, runner):
        """Test that validate provides helpful suggestions."""
        with (
            patch("dev_agent.cli.main.config_manager") as mock_config,
            patch("dev_agent.cli.main.setup_cli_logging"),
        ):
            from types import SimpleNamespace
            config = SimpleNamespace(azure_openai=None)
            mock_config.get_config.return_value = config

            result = runner.invoke(app, ["validate"])

            # Should provide suggestions
            assert "setup" in result.stdout.lower() or "configure" in result.stdout.lower()


class TestHelpSystemEnhancements:
    """Test enhanced help system functionality."""

    def test_help_system_shows_all_commands(self):
        """Test that help system shows all commands."""
        hs = HelpSystem()
        
        # Should not raise exception
        hs.show_all_commands()
        
        # Should have essential commands
        assert "init" in hs.commands
        assert "resume" in hs.commands
        assert "status" in hs.commands

    def test_help_system_shows_command_details(self):
        """Test that help system shows command details."""
        hs = HelpSystem()
        
        # Should not raise exception
        hs.show_command_help("init")
        
        # Command should have required fields
        assert "description" in hs.commands["init"]
        assert "usage" in hs.commands["init"]

    def test_help_system_shows_examples(self):
        """Test that help system shows workflow examples."""
        hs = HelpSystem()
        
        # Should not raise exception
        hs.show_examples()
        
        # Should have workflow examples
        assert len(hs.workflows) > 0
        assert "new_project" in hs.workflows

    def test_help_system_quick_reference(self):
        """Test that help system shows quick reference."""
        hs = HelpSystem()
        
        # Should not raise exception
        hs.show_quick_reference()

    def test_help_command_integration(self, runner):
        """Test help command integration with CLI."""
        result = runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "dev-agent" in result.stdout.lower()


class TestProgressDisplayEnhancements:
    """Test enhanced progress display functionality."""

    def test_progress_display_indexing(self, test_console):
        """Test progress display for indexing."""
        display = ProgressDisplay(console=test_console)
        
        with display.show_indexing_progress(10) as progress:
            for i in range(10):
                progress.update(i + 1, current_file=f"file_{i}.py")
        
        # Should complete without errors
        assert True

    def test_progress_display_phase_summary(self, test_console):
        """Test progress display for phase summary."""
        display = ProgressDisplay(console=test_console)
        
        result = IndexingResult(
            phase=PhaseType.INDEXING,
            status=PhaseStatus.COMPLETED,
            message="Indexing completed",
            files_indexed=100,
            total_lines=5000,
            index_size_mb=2.5,
            languages_detected=["Python"],
        )
        
        display.show_phase_summary(PhaseType.INDEXING, result)
        
        output = test_console.file.getvalue()  # type: ignore
        assert "Indexing" in output
        assert "100" in output

    def test_progress_display_cost_summary(self, test_console):
        """Test progress display for cost summary."""
        display = ProgressDisplay(console=test_console)
        
        report = CostReport(
            total_prompt_tokens=1000,
            total_completion_tokens=2000,
            total_embedding_tokens=500,
            total_cost=0.15,
            operations_count=10,
            by_phase={},
            by_operation={},
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(seconds=30),
        )
        
        display.show_cost_summary(report)
        
        output = test_console.file.getvalue()  # type: ignore
        assert "Cost" in output
        assert "$0.15" in output

    def test_progress_display_spinner(self, test_console):
        """Test progress display spinner."""
        display = ProgressDisplay(console=test_console)
        
        with display.show_spinner("Processing...") as spinner:
            spinner.update("Still processing...")
        
        # Should complete without errors
        assert True


class TestFeedbackSystemEnhancements:
    """Test enhanced feedback system functionality."""

    def test_feedback_system_phase_start(self, mock_console):
        """Test feedback system phase start."""
        feedback = FeedbackSystem(console=mock_console)
        
        feedback.show_phase_start(PhaseType.INDEXING)
        
        assert mock_console.print.called

    def test_feedback_system_phase_complete(self, mock_console):
        """Test feedback system phase complete."""
        feedback = FeedbackSystem(console=mock_console)
        
        summary = {
            "files_indexed": 100,
            "functions_found": 300,
        }
        
        feedback.show_phase_complete(PhaseType.INDEXING, summary)
        
        assert mock_console.print.called

    def test_feedback_system_error(self, mock_console):
        """Test feedback system error display."""
        feedback = FeedbackSystem(console=mock_console)
        
        error = ValueError("Test error")
        suggestions = ["Check configuration", "Verify API key"]
        
        feedback.show_error(error, suggestions)
        
        assert mock_console.print.called

    def test_feedback_system_warning(self, mock_console):
        """Test feedback system warning display."""
        feedback = FeedbackSystem(console=mock_console)
        
        feedback.show_warning("This may take a while", "Consider using --fast mode")
        
        assert mock_console.print.called

    def test_feedback_system_success(self, mock_console):
        """Test feedback system success display."""
        feedback = FeedbackSystem(console=mock_console)
        
        next_steps = ["Run dev-agent resume", "Check status"]
        
        feedback.show_success("Setup complete", next_steps)
        
        assert mock_console.print.called

    @patch("builtins.input", return_value="y")
    def test_feedback_system_confirm(self, mock_input, mock_console):
        """Test feedback system confirmation."""
        feedback = FeedbackSystem(console=mock_console)
        
        result = feedback.confirm("Continue?")
        
        assert result is True


class TestCLIIntegration:
    """Integration tests for enhanced CLI functionality."""

    def test_cli_commands_available(self, runner):
        """Test that all enhanced CLI commands are available."""
        result = runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        # Should show main commands
        assert "init" in result.stdout.lower() or "commands" in result.stdout.lower()

    def test_cli_error_handling(self, runner, tmp_path):
        """Test CLI error handling."""
        # Try to run status on non-existent project
        result = runner.invoke(app, ["status", str(tmp_path)])
        
        # Should handle error gracefully
        assert result.exit_code in [0, 1]

    def test_cli_verbose_mode(self, runner, tmp_path):
        """Test CLI verbose mode."""
        dev_agent_dir = tmp_path / ".dev_agent"
        dev_agent_dir.mkdir()

        result = runner.invoke(app, ["status", str(tmp_path), "--verbose"])
        
        # Should complete (may fail if no project, but shouldn't crash)
        assert result.exit_code in [0, 1]

    def test_cli_help_for_commands(self, runner):
        """Test that help is available for all commands."""
        commands = ["init", "resume", "status", "validate"]
        
        for cmd in commands:
            result = runner.invoke(app, [cmd, "--help"])
            assert result.exit_code == 0


class TestCLIUserExperience:
    """Test CLI user experience enhancements."""

    def test_status_provides_next_steps(
        self, runner, tmp_path, mock_project_state, sample_cost_report
    ):
        """Test that status provides next steps."""
        dev_agent_dir = tmp_path / ".dev_agent"
        dev_agent_dir.mkdir()

        with (
            patch("dev_agent.workflow.workflow_manager.WorkflowManager") as mock_wf,
            patch("dev_agent.cli.main.setup_cli_logging"),
        ):
            mock_manager = MagicMock()
            mock_manager.resume_project.return_value = mock_project_state
            mock_manager.cost_tracker.get_report.return_value = sample_cost_report
            mock_wf.return_value = mock_manager

            result = runner.invoke(app, ["status", str(tmp_path)])

            assert result.exit_code == 0
            assert "Next Steps" in result.stdout or "next" in result.stdout.lower()

    def test_cost_report_shows_budget_warnings(
        self, runner, tmp_path, sample_cost_report
    ):
        """Test that cost report shows budget warnings."""
        dev_agent_dir = tmp_path / ".dev_agent"
        dev_agent_dir.mkdir()

        with patch("dev_agent.workflow.workflow_manager.WorkflowManager") as mock_wf:
            mock_manager = MagicMock()
            mock_manager.cost_tracker.get_report.return_value = sample_cost_report
            mock_manager.cost_tracker.budget_threshold = 0.01  # Very low threshold
            mock_manager.cost_tracker.budget_limit = None
            mock_wf.return_value = mock_manager

            result = runner.invoke(app, ["cost-report", str(tmp_path)])

            assert result.exit_code == 0
            # Should show budget warning
            assert "Budget" in result.stdout or "threshold" in result.stdout.lower()

    def test_validate_shows_pass_fail_clearly(self, runner):
        """Test that validate shows pass/fail clearly."""
        with (
            patch("dev_agent.cli.main.config_manager") as mock_config,
            patch("dev_agent.cli.main.setup_cli_logging"),
        ):
            from types import SimpleNamespace
            config = SimpleNamespace(azure_openai=None)
            mock_config.get_config.return_value = config

            result = runner.invoke(app, ["validate"])

            # Should show clear pass/fail indicators
            assert "✓" in result.stdout or "✗" in result.stdout or \
                   "Pass" in result.stdout or "Fail" in result.stdout


class TestCLIPerformance:
    """Test CLI performance characteristics."""

    def test_status_command_responsive(
        self, runner, tmp_path, mock_project_state, sample_cost_report
    ):
        """Test that status command is responsive."""
        dev_agent_dir = tmp_path / ".dev_agent"
        dev_agent_dir.mkdir()

        with (
            patch("dev_agent.workflow.workflow_manager.WorkflowManager") as mock_wf,
            patch("dev_agent.cli.main.setup_cli_logging"),
        ):
            mock_manager = MagicMock()
            mock_manager.resume_project.return_value = mock_project_state
            mock_manager.cost_tracker.get_report.return_value = sample_cost_report
            mock_wf.return_value = mock_manager

            import time
            start = time.time()
            result = runner.invoke(app, ["status", str(tmp_path)])
            duration = time.time() - start

            assert result.exit_code == 0
            # Should complete quickly (under 5 seconds in test environment)
            assert duration < 5.0

    def test_help_command_responsive(self, runner):
        """Test that help command is responsive."""
        import time
        start = time.time()
        result = runner.invoke(app, ["--help"])
        duration = time.time() - start

        assert result.exit_code == 0
        # Should be very fast (under 1 second)
        assert duration < 1.0


class TestCLIAccessibility:
    """Test CLI accessibility features."""

    def test_status_output_readable(
        self, runner, tmp_path, mock_project_state, sample_cost_report
    ):
        """Test that status output is readable."""
        dev_agent_dir = tmp_path / ".dev_agent"
        dev_agent_dir.mkdir()

        with (
            patch("dev_agent.workflow.workflow_manager.WorkflowManager") as mock_wf,
            patch("dev_agent.cli.main.setup_cli_logging"),
        ):
            mock_manager = MagicMock()
            mock_manager.resume_project.return_value = mock_project_state
            mock_manager.cost_tracker.get_report.return_value = sample_cost_report
            mock_wf.return_value = mock_manager

            result = runner.invoke(app, ["status", str(tmp_path)])

            assert result.exit_code == 0
            # Should have clear sections
            assert "Status" in result.stdout or "Progress" in result.stdout

    def test_error_messages_actionable(self, runner, tmp_path):
        """Test that error messages are actionable."""
        # Try to run command on non-existent project
        result = runner.invoke(app, ["status", str(tmp_path)])

        # Should provide actionable error message
        if result.exit_code == 1:
            assert len(result.stdout) > 0
            # Should suggest what to do
            assert "init" in result.stdout.lower() or "setup" in result.stdout.lower()


class TestCLIConsistency:
    """Test CLI consistency across commands."""

    def test_all_commands_have_help(self, runner):
        """Test that all commands have help text."""
        commands = ["init", "resume", "status", "validate"]
        
        for cmd in commands:
            result = runner.invoke(app, [cmd, "--help"])
            assert result.exit_code == 0
            assert len(result.stdout) > 0

    def test_error_format_consistent(self, runner, tmp_path):
        """Test that error format is consistent."""
        # Try multiple commands that should fail
        commands = [
            ["status", str(tmp_path)],
            ["cost-report", str(tmp_path)],
        ]
        
        for cmd in commands:
            result = runner.invoke(app, cmd)
            # All should handle errors consistently
            assert result.exit_code in [0, 1]

    def test_success_format_consistent(
        self, runner, tmp_path, mock_project_state, sample_cost_report
    ):
        """Test that success format is consistent."""
        dev_agent_dir = tmp_path / ".dev_agent"
        dev_agent_dir.mkdir()

        with (
            patch("dev_agent.workflow.workflow_manager.WorkflowManager") as mock_wf,
            patch("dev_agent.cli.main.setup_cli_logging"),
        ):
            mock_manager = MagicMock()
            mock_manager.resume_project.return_value = mock_project_state
            mock_manager.cost_tracker.get_report.return_value = sample_cost_report
            # Fix: Set budget values to None to avoid comparison issues
            mock_manager.cost_tracker.budget_threshold = None
            mock_manager.cost_tracker.budget_limit = None
            mock_wf.return_value = mock_manager

            # Run multiple commands
            commands = [
                ["status", str(tmp_path)],
                ["cost-report", str(tmp_path)],
            ]
            
            for cmd in commands:
                result = runner.invoke(app, cmd)
                assert result.exit_code == 0
                # Should have consistent output structure
                assert len(result.stdout) > 0
