"""Tests for the feedback system."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from dev_agent.cli.feedback_system import (
    FeedbackSystem,
    get_feedback_system,
    show_error,
    show_phase_complete,
    show_phase_start,
    show_success,
    show_warning,
)
from dev_agent.models.enums import PhaseType


@pytest.fixture
def mock_console() -> MagicMock:
    """Create a mock Rich console."""
    console = MagicMock(spec=Console)
    # Add get_time method for Progress compatibility
    console.get_time = MagicMock(return_value=0.0)
    return console


@pytest.fixture
def feedback_system(mock_console: MagicMock) -> FeedbackSystem:
    """Create a feedback system with mock console."""
    return FeedbackSystem(console=mock_console)


class TestFeedbackSystem:
    """Test the FeedbackSystem class."""

    def test_init_default_console(self) -> None:
        """Test initialization with default console."""
        system = FeedbackSystem()
        assert system.console is not None
        assert isinstance(system.console, Console)

    def test_init_custom_console(self, mock_console: MagicMock) -> None:
        """Test initialization with custom console."""
        system = FeedbackSystem(console=mock_console)
        assert system.console is mock_console

    def test_show_phase_start_indexing(
        self,
        feedback_system: FeedbackSystem,
        mock_console: MagicMock,
    ) -> None:
        """Test showing indexing phase start."""
        feedback_system.show_phase_start(PhaseType.INDEXING)

        # Verify console.print was called
        assert mock_console.print.called
        # Should print empty line, panel, and another empty line
        assert mock_console.print.call_count >= 3

    def test_show_phase_start_specification(
        self,
        feedback_system: FeedbackSystem,
        mock_console: MagicMock,
    ) -> None:
        """Test showing specification phase start."""
        feedback_system.show_phase_start(PhaseType.SPECIFICATION)

        assert mock_console.print.called
        assert mock_console.print.call_count >= 3

    def test_show_phase_start_design(
        self,
        feedback_system: FeedbackSystem,
        mock_console: MagicMock,
    ) -> None:
        """Test showing design phase start."""
        feedback_system.show_phase_start(PhaseType.DESIGN)

        assert mock_console.print.called
        assert mock_console.print.call_count >= 3

    def test_show_phase_start_implementation(
        self,
        feedback_system: FeedbackSystem,
        mock_console: MagicMock,
    ) -> None:
        """Test showing implementation phase start."""
        feedback_system.show_phase_start(PhaseType.IMPLEMENTATION)

        assert mock_console.print.called
        assert mock_console.print.call_count >= 3

    def test_show_phase_start_custom_description(
        self,
        feedback_system: FeedbackSystem,
        mock_console: MagicMock,
    ) -> None:
        """Test showing phase start with custom description."""
        custom_desc = "Custom phase description"
        feedback_system.show_phase_start(PhaseType.INDEXING, description=custom_desc)

        assert mock_console.print.called

    def test_show_operation_progress(
        self,
        feedback_system: FeedbackSystem,
        mock_console: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test showing operation progress."""
        progress = feedback_system.show_operation_progress("Processing files")

        assert progress is not None
        assert feedback_system._current_progress is progress

    def test_show_operation_progress_with_details(
        self,
        feedback_system: FeedbackSystem,
        mock_console: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test showing operation progress with details."""
        progress = feedback_system.show_operation_progress(
            "Processing files",
            details="Analyzing Python code",
        )

        assert progress is not None

    def test_show_phase_complete_indexing(
        self,
        feedback_system: FeedbackSystem,
        mock_console: MagicMock,
    ) -> None:
        """Test showing indexing phase completion."""
        summary = {
            "files_indexed": 150,
            "functions_found": 450,
            "classes_found": 75,
            "total_tokens": 50000,
        }

        feedback_system.show_phase_complete(PhaseType.INDEXING, summary)

        assert mock_console.print.called
        # Should print empty line, table, empty line, next steps
        assert mock_console.print.call_count >= 4

    def test_show_phase_complete_specification(
        self,
        feedback_system: FeedbackSystem,
        mock_console: MagicMock,
    ) -> None:
        """Test showing specification phase completion."""
        summary = {
            "requirements_generated": 25,
            "tokens_used": 3500,
            "cost": 0.15,
        }

        feedback_system.show_phase_complete(PhaseType.SPECIFICATION, summary)

        assert mock_console.print.called

    def test_show_phase_complete_design(
        self,
        feedback_system: FeedbackSystem,
        mock_console: MagicMock,
    ) -> None:
        """Test showing design phase completion."""
        summary = {
            "components_designed": 12,
            "interfaces_defined": 8,
            "tokens_used": 4200,
        }

        feedback_system.show_phase_complete(PhaseType.DESIGN, summary)

        assert mock_console.print.called

    def test_show_phase_complete_implementation(
        self,
        feedback_system: FeedbackSystem,
        mock_console: MagicMock,
    ) -> None:
        """Test showing implementation phase completion."""
        summary = {
            "tasks_generated": 35,
            "estimated_hours": 40,
            "tokens_used": 3800,
        }

        feedback_system.show_phase_complete(PhaseType.IMPLEMENTATION, summary)

        assert mock_console.print.called

    def test_show_error_with_exception(
        self,
        feedback_system: FeedbackSystem,
        mock_console: MagicMock,
    ) -> None:
        """Test showing error with exception."""
        error = ValueError("Invalid configuration")
        feedback_system.show_error(error)

        assert mock_console.print.called
        assert mock_console.print.call_count >= 3

    def test_show_error_with_string(
        self,
        feedback_system: FeedbackSystem,
        mock_console: MagicMock,
    ) -> None:
        """Test showing error with string message."""
        feedback_system.show_error("Something went wrong")

        assert mock_console.print.called

    def test_show_error_with_suggestions(
        self,
        feedback_system: FeedbackSystem,
        mock_console: MagicMock,
    ) -> None:
        """Test showing error with suggestions."""
        suggestions = [
            "Check your Azure OpenAI configuration",
            "Verify your API key is valid",
            "Ensure you have network connectivity",
        ]

        feedback_system.show_error("API connection failed", suggestions=suggestions)

        assert mock_console.print.called

    def test_show_warning_simple(
        self,
        feedback_system: FeedbackSystem,
        mock_console: MagicMock,
    ) -> None:
        """Test showing simple warning."""
        feedback_system.show_warning("This operation may take a while")

        assert mock_console.print.called
        assert mock_console.print.call_count >= 3

    def test_show_warning_with_action(
        self,
        feedback_system: FeedbackSystem,
        mock_console: MagicMock,
    ) -> None:
        """Test showing warning with action."""
        feedback_system.show_warning(
            "Azure OpenAI costs may be high",
            action="Consider setting a budget limit",
        )

        assert mock_console.print.called

    def test_show_success_simple(
        self,
        feedback_system: FeedbackSystem,
        mock_console: MagicMock,
    ) -> None:
        """Test showing simple success message."""
        feedback_system.show_success("Configuration saved successfully")

        assert mock_console.print.called
        assert mock_console.print.call_count >= 3

    def test_show_success_with_next_steps(
        self,
        feedback_system: FeedbackSystem,
        mock_console: MagicMock,
    ) -> None:
        """Test showing success with next steps."""
        next_steps = [
            "Run 'dev-agent init' to start indexing",
            "Check status with 'dev-agent status'",
            "View costs with 'dev-agent cost'",
        ]

        feedback_system.show_success("Setup complete", next_steps=next_steps)

        assert mock_console.print.called

    def test_show_info(
        self,
        feedback_system: FeedbackSystem,
        mock_console: MagicMock,
    ) -> None:
        """Test showing informational message."""
        feedback_system.show_info("This is an informational message")

        assert mock_console.print.called
        assert mock_console.print.call_count >= 3

    def test_show_info_custom_title(
        self,
        feedback_system: FeedbackSystem,
        mock_console: MagicMock,
    ) -> None:
        """Test showing info with custom title."""
        feedback_system.show_info("Custom info", title="Custom Title")

        assert mock_console.print.called

    def test_show_cost_summary(
        self,
        feedback_system: FeedbackSystem,
        mock_console: MagicMock,
    ) -> None:
        """Test showing cost summary."""
        feedback_system.show_cost_summary(
            prompt_tokens=1500,
            completion_tokens=2500,
            total_cost=0.25,
        )

        assert mock_console.print.called
        assert mock_console.print.call_count >= 3

    @patch("builtins.input", return_value="y")
    def test_confirm_yes(
        self,
        mock_input: MagicMock,  # noqa: ARG002
        feedback_system: FeedbackSystem,
        mock_console: MagicMock,
    ) -> None:
        """Test confirmation with yes response."""
        result = feedback_system.confirm("Continue?")

        assert result is True
        assert mock_console.print.called

    @patch("builtins.input", return_value="n")
    def test_confirm_no(
        self,
        mock_input: MagicMock,  # noqa: ARG002
        feedback_system: FeedbackSystem,
        mock_console: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test confirmation with no response."""
        result = feedback_system.confirm("Continue?")

        assert result is False

    @patch("builtins.input", return_value="")
    def test_confirm_default_true(
        self,
        mock_input: MagicMock,  # noqa: ARG002
        feedback_system: FeedbackSystem,
        mock_console: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test confirmation with default true."""
        result = feedback_system.confirm("Continue?", default=True)

        assert result is True

    @patch("builtins.input", return_value="")
    def test_confirm_default_false(
        self,
        mock_input: MagicMock,  # noqa: ARG002
        feedback_system: FeedbackSystem,
        mock_console: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test confirmation with default false."""
        result = feedback_system.confirm("Continue?", default=False)

        assert result is False

    @patch("builtins.input", side_effect=KeyboardInterrupt)
    def test_confirm_keyboard_interrupt(
        self,
        mock_input: MagicMock,  # noqa: ARG002
        feedback_system: FeedbackSystem,
        mock_console: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test confirmation with keyboard interrupt."""
        result = feedback_system.confirm("Continue?")

        assert result is False

    @patch("builtins.input", side_effect=EOFError)
    def test_confirm_eof_error(
        self,
        mock_input: MagicMock,  # noqa: ARG002
        feedback_system: FeedbackSystem,
        mock_console: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test confirmation with EOF error."""
        result = feedback_system.confirm("Continue?")

        assert result is False


class TestGlobalFunctions:
    """Test global convenience functions."""

    def test_get_feedback_system(self) -> None:
        """Test getting global feedback system."""
        system1 = get_feedback_system()
        system2 = get_feedback_system()

        assert system1 is system2  # Should be singleton

    @patch("dev_agent.cli.feedback_system.get_feedback_system")
    def test_show_phase_start_function(
        self,
        mock_get_system: MagicMock,
    ) -> None:
        """Test show_phase_start convenience function."""
        mock_system = MagicMock()
        mock_get_system.return_value = mock_system

        show_phase_start(PhaseType.INDEXING)

        mock_system.show_phase_start.assert_called_once_with(PhaseType.INDEXING, None)

    @patch("dev_agent.cli.feedback_system.get_feedback_system")
    def test_show_phase_complete_function(
        self,
        mock_get_system: MagicMock,
    ) -> None:
        """Test show_phase_complete convenience function."""
        mock_system = MagicMock()
        mock_get_system.return_value = mock_system

        summary = {"files": 100}
        show_phase_complete(PhaseType.INDEXING, summary)

        mock_system.show_phase_complete.assert_called_once_with(
            PhaseType.INDEXING,
            summary,
        )

    @patch("dev_agent.cli.feedback_system.get_feedback_system")
    def test_show_error_function(
        self,
        mock_get_system: MagicMock,
    ) -> None:
        """Test show_error convenience function."""
        mock_system = MagicMock()
        mock_get_system.return_value = mock_system

        error = ValueError("Test error")
        suggestions = ["Fix it"]
        show_error(error, suggestions)

        mock_system.show_error.assert_called_once_with(error, suggestions)

    @patch("dev_agent.cli.feedback_system.get_feedback_system")
    def test_show_warning_function(
        self,
        mock_get_system: MagicMock,
    ) -> None:
        """Test show_warning convenience function."""
        mock_system = MagicMock()
        mock_get_system.return_value = mock_system

        show_warning("Warning message", "Take action")

        mock_system.show_warning.assert_called_once_with("Warning message", "Take action")

    @patch("dev_agent.cli.feedback_system.get_feedback_system")
    def test_show_success_function(
        self,
        mock_get_system: MagicMock,
    ) -> None:
        """Test show_success convenience function."""
        mock_system = MagicMock()
        mock_get_system.return_value = mock_system

        next_steps = ["Step 1", "Step 2"]
        show_success("Success!", next_steps)

        mock_system.show_success.assert_called_once_with("Success!", next_steps)


class TestNextSteps:
    """Test next steps generation."""

    def test_get_next_steps_indexing(
        self,
        feedback_system: FeedbackSystem,
    ) -> None:
        """Test getting next steps for indexing phase."""
        steps = feedback_system._get_next_steps(PhaseType.INDEXING)

        assert len(steps) > 0
        assert any("specification" in step.lower() for step in steps)

    def test_get_next_steps_specification(
        self,
        feedback_system: FeedbackSystem,
    ) -> None:
        """Test getting next steps for specification phase."""
        steps = feedback_system._get_next_steps(PhaseType.SPECIFICATION)

        assert len(steps) > 0
        assert any("design" in step.lower() for step in steps)

    def test_get_next_steps_design(
        self,
        feedback_system: FeedbackSystem,
    ) -> None:
        """Test getting next steps for design phase."""
        steps = feedback_system._get_next_steps(PhaseType.DESIGN)

        assert len(steps) > 0
        assert any("implementation" in step.lower() for step in steps)

    def test_get_next_steps_implementation(
        self,
        feedback_system: FeedbackSystem,
    ) -> None:
        """Test getting next steps for implementation phase."""
        steps = feedback_system._get_next_steps(PhaseType.IMPLEMENTATION)

        assert len(steps) > 0
        assert any("task" in step.lower() for step in steps)
