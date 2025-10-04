"""Feedback system for providing user feedback during operations.

This module provides a comprehensive feedback system for the CLI, including
phase transitions, operation progress, error handling, warnings, and success
messages with actionable next steps.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from dev_agent.models.enums import PhaseType


class FeedbackLevel(Enum):
    """Feedback message levels."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class FeedbackSystem:
    """Provides user feedback during operations.

    This class handles all user-facing feedback including phase transitions,
    progress indicators, error messages, warnings, and success confirmations.
    All messages are formatted using Rich for enhanced terminal output.
    """

    def __init__(self, console: Console | None = None) -> None:
        """Initialize the feedback system.

        Args:
            console: Rich console instance. If None, creates a new one.
        """
        self.console = console or Console()
        self._current_progress: Progress | None = None

    def show_phase_start(
        self,
        phase: PhaseType,
        description: str | None = None,
    ) -> None:
        """Display phase start message with description.

        Args:
            phase: The phase being started
            description: Optional detailed description of the phase
        """
        phase_descriptions = {
            PhaseType.INDEXING: (
                "Analyzing your codebase structure, parsing code with Tree-sitter, "
                "and generating semantic embeddings via Azure OpenAI."
            ),
            PhaseType.SPECIFICATION: (
                "Generating detailed specifications based on your codebase analysis. "
                "GPT-4 will create context-aware specifications using indexed code."
            ),
            PhaseType.DESIGN: (
                "Creating technical design documents that reference your specifications "
                "and existing architectural patterns from the codebase."
            ),
            PhaseType.IMPLEMENTATION: (
                "Generating actionable implementation tasks based on the design document. "
                "Tasks will be broken down into manageable, sequential steps."
            ),
        }

        desc = description or phase_descriptions.get(
            phase,
            f"Starting {phase.value} phase",
        )

        # Create phase start panel
        panel = Panel(
            Text(desc, style="cyan"),
            title=f"[bold blue]🚀 Starting {phase.value.title()} Phase[/bold blue]",
            border_style="blue",
            padding=(1, 2),
        )

        self.console.print()
        self.console.print(panel)
        self.console.print()

    def show_operation_progress(
        self,
        operation: str,
        details: str | None = None,
    ) -> Progress:
        """Show operation progress with spinner.

        Args:
            operation: Name of the operation being performed
            details: Optional additional details about the operation

        Returns:
            Progress context manager for tracking progress
        """
        # Create progress display with spinner
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        )

        description = operation
        if details:
            description = f"{operation} - {details}"

        progress.add_task(description, total=None)
        self._current_progress = progress

        return progress

    def show_phase_complete(
        self,
        phase: PhaseType,
        summary: dict[str, Any],
    ) -> None:
        """Display phase completion message with summary.

        Args:
            phase: The phase that completed
            summary: Dictionary containing phase results and metrics
        """
        # Create summary table
        table = Table(
            title=f"[bold green]✓ {phase.value.title()} Phase Complete[/bold green]",
            show_header=False,
            border_style="green",
            padding=(0, 1),
        )

        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        # Add summary items
        for key, value in summary.items():
            # Format key nicely
            formatted_key = key.replace("_", " ").title()
            table.add_row(formatted_key, str(value))

        self.console.print()
        self.console.print(table)
        self.console.print()

        # Show next steps based on phase
        next_steps = self._get_next_steps(phase)
        if next_steps:
            self.console.print("[bold cyan]Next Steps:[/bold cyan]")
            for i, step in enumerate(next_steps, 1):
                self.console.print(f"  {i}. {step}")
            self.console.print()

    def show_error(
        self,
        error: Exception | str,
        suggestions: list[str] | None = None,
    ) -> None:
        """Display error message with suggestions.

        Args:
            error: The error that occurred (Exception or string message)
            suggestions: Optional list of suggested solutions
        """
        error_msg = str(error)

        # Create error panel
        error_text = Text()
        error_text.append("❌ Error: ", style="bold red")
        error_text.append(error_msg, style="red")

        if suggestions:
            error_text.append("\n\n")
            error_text.append("Possible solutions:\n", style="bold yellow")
            for i, suggestion in enumerate(suggestions, 1):
                error_text.append(f"{i}. {suggestion}\n", style="yellow")

        panel = Panel(
            error_text,
            title="[bold red]Error Occurred[/bold red]",
            border_style="red",
            padding=(1, 2),
        )

        self.console.print()
        self.console.print(panel)
        self.console.print()

    def show_warning(
        self,
        message: str,
        action: str | None = None,
    ) -> None:
        """Display warning message with optional action prompt.

        Args:
            message: The warning message
            action: Optional suggested action to take
        """
        warning_text = Text()
        warning_text.append("⚠️  Warning: ", style="bold yellow")
        warning_text.append(message, style="yellow")

        if action:
            warning_text.append("\n\n")
            warning_text.append("Recommended action: ", style="bold yellow")
            warning_text.append(action, style="yellow")

        panel = Panel(
            warning_text,
            title="[bold yellow]Warning[/bold yellow]",
            border_style="yellow",
            padding=(1, 2),
        )

        self.console.print()
        self.console.print(panel)
        self.console.print()

    def show_success(
        self,
        message: str,
        next_steps: list[str] | None = None,
    ) -> None:
        """Display success message with next steps.

        Args:
            message: The success message
            next_steps: Optional list of next steps to take
        """
        success_text = Text()
        success_text.append("✓ Success: ", style="bold green")
        success_text.append(message, style="green")

        if next_steps:
            success_text.append("\n\n")
            success_text.append("Next steps:\n", style="bold cyan")
            for i, step in enumerate(next_steps, 1):
                success_text.append(f"{i}. {step}\n", style="cyan")

        panel = Panel(
            success_text,
            title="[bold green]Success[/bold green]",
            border_style="green",
            padding=(1, 2),
        )

        self.console.print()
        self.console.print(panel)
        self.console.print()

    def show_info(
        self,
        message: str,
        title: str = "Information",
    ) -> None:
        """Display informational message.

        Args:
            message: The informational message
            title: Optional title for the info panel
        """
        panel = Panel(
            Text(message, style="blue"),
            title=f"[bold blue]{title}[/bold blue]",
            border_style="blue",
            padding=(1, 2),
        )

        self.console.print()
        self.console.print(panel)
        self.console.print()

    def show_cost_summary(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        total_cost: float,
    ) -> None:
        """Display cost summary for an operation.

        Args:
            prompt_tokens: Number of prompt tokens used
            completion_tokens: Number of completion tokens used
            total_cost: Total cost in USD
        """
        table = Table(
            title="[bold cyan]💰 Cost Summary[/bold cyan]",
            show_header=False,
            border_style="cyan",
            padding=(0, 1),
        )

        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        table.add_row("Prompt Tokens", f"{prompt_tokens:,}")
        table.add_row("Completion Tokens", f"{completion_tokens:,}")
        table.add_row("Total Tokens", f"{prompt_tokens + completion_tokens:,}")
        table.add_row("Estimated Cost", f"${total_cost:.4f}")

        self.console.print()
        self.console.print(table)
        self.console.print()

    def confirm(
        self,
        message: str,
        default: bool = False,
    ) -> bool:
        """Prompt user for confirmation.

        Args:
            message: The confirmation message
            default: Default value if user just presses Enter

        Returns:
            True if user confirms, False otherwise
        """
        default_str = "Y/n" if default else "y/N"
        prompt = f"{message} [{default_str}]: "

        self.console.print(f"[bold yellow]{prompt}[/bold yellow]", end="")

        try:
            response = input().strip().lower()
        except (KeyboardInterrupt, EOFError):
            self.console.print()
            return False

        if not response:
            return default

        return response in ("y", "yes")

    def _get_next_steps(self, phase: PhaseType) -> list[str]:
        """Get next steps for a completed phase.

        Args:
            phase: The phase that completed

        Returns:
            List of next step descriptions
        """
        next_steps_map = {
            PhaseType.INDEXING: [
                "Review the indexing summary to understand what was analyzed",
                "Run 'dev-agent phase specification' to generate specifications",
                "Check cost report with 'dev-agent cost' to track usage",
            ],
            PhaseType.SPECIFICATION: [
                "Review the generated specification in .dev_agent/documents/",
                "Make any necessary edits to the specification",
                "Run 'dev-agent phase design' to create the design document",
            ],
            PhaseType.DESIGN: [
                "Review the design document in .dev_agent/documents/",
                "Verify the design aligns with your requirements",
                "Run 'dev-agent phase implementation' to generate tasks",
            ],
            PhaseType.IMPLEMENTATION: [
                "Review the implementation tasks in .dev_agent/documents/",
                "Begin implementing tasks in order",
                "Use 'dev-agent status' to track progress",
            ],
        }

        return next_steps_map.get(phase, [])


# Global feedback system instance
_feedback_system: FeedbackSystem | None = None


def get_feedback_system() -> FeedbackSystem:
    """Get the global feedback system instance.

    Returns:
        The global FeedbackSystem instance
    """
    global _feedback_system  # noqa: PLW0603
    if _feedback_system is None:
        _feedback_system = FeedbackSystem()
    return _feedback_system


def show_phase_start(phase: PhaseType, description: str | None = None) -> None:
    """Show phase start message.

    Args:
        phase: The phase being started
        description: Optional phase description
    """
    get_feedback_system().show_phase_start(phase, description)


def show_operation_progress(operation: str, details: str | None = None) -> Progress:
    """Show operation progress with spinner.

    Args:
        operation: Operation name
        details: Optional operation details

    Returns:
        Progress context manager
    """
    return get_feedback_system().show_operation_progress(operation, details)


def show_phase_complete(phase: PhaseType, summary: dict[str, Any]) -> None:
    """Show phase completion message.

    Args:
        phase: The completed phase
        summary: Phase summary data
    """
    get_feedback_system().show_phase_complete(phase, summary)


def show_error(error: Exception | str, suggestions: list[str] | None = None) -> None:
    """Show error message with suggestions.

    Args:
        error: The error that occurred
        suggestions: Optional solution suggestions
    """
    get_feedback_system().show_error(error, suggestions)


def show_warning(message: str, action: str | None = None) -> None:
    """Show warning message.

    Args:
        message: Warning message
        action: Optional recommended action
    """
    get_feedback_system().show_warning(message, action)


def show_success(message: str, next_steps: list[str] | None = None) -> None:
    """Show success message with next steps.

    Args:
        message: Success message
        next_steps: Optional next steps
    """
    get_feedback_system().show_success(message, next_steps)
