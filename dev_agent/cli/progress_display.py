"""Progress display system for CLI operations.

This module provides Rich-based progress indicators, streaming displays,
and formatted summaries for long-running operations in the dev-agent CLI.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from dev_agent.models.enums import PhaseType

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from dev_agent.models.cost_tracking import CostReport
    from dev_agent.models.results import PhaseResult


class ProgressDisplay:
    """Rich progress display for long-running operations.

    This class provides various progress indicators and formatted displays
    for CLI operations, ensuring smooth animations and real-time feedback.

    Attributes:
        console: Rich Console instance for output

    Example:
        ```python
        display = ProgressDisplay()

        # Show indexing progress
        with display.show_indexing_progress(total_files=100) as progress:
            for i in range(100):
                progress.update(i + 1, current_file="file.py")

        # Show streaming response
        async for chunk in llm_client.generate_streaming(prompt):
            display.show_streaming_chunk(chunk)
        ```
    """

    def __init__(self, console: Console | None = None) -> None:
        """Initialize progress display.

        Args:
            console: Rich Console instance (creates new one if None)
        """
        self.console = console or Console()

    def show_indexing_progress(
        self, total_files: int, description: str = "Indexing files"
    ) -> IndexingProgressContext:
        """Show progress bar for indexing operations.

        This method creates a context manager that displays a progress bar
        with file count, current file, and time estimates. Updates at least
        10 times per second for smooth animation (requirement 10.5).

        Args:
            total_files: Total number of files to index
            description: Description text for the progress bar

        Returns:
            Context manager for updating progress

        Example:
            ```python
            with display.show_indexing_progress(100) as progress:
                for i, file in enumerate(files):
                    progress.update(i + 1, current_file=file.name)
            ```
        """
        return IndexingProgressContext(
            console=self.console,
            total_files=total_files,
            description=description,
        )

    def show_streaming_response(
        self, stream: AsyncIterator[str], prefix: str = ""
    ) -> str:
        """Display streaming LLM response in real-time.

        This method displays streaming responses from Azure OpenAI without
        buffering delays (requirement 10.6), providing immediate feedback
        to the user.

        Args:
            stream: Async iterator of response chunks
            prefix: Optional prefix text to display before stream

        Returns:
            Complete response text after streaming

        Example:
            ```python
            response = await display.show_streaming_response(
                llm_client.generate_streaming(prompt),
                prefix="Generating specification: "
            )
            ```
        """
        # This is a synchronous wrapper - actual implementation
        # should be called from async context
        return asyncio.run(self._show_streaming_response_async(stream, prefix))

    async def _show_streaming_response_async(
        self, stream: AsyncIterator[str], prefix: str = ""
    ) -> str:
        """Async implementation of streaming response display.

        Args:
            stream: Async iterator of response chunks
            prefix: Optional prefix text to display before stream

        Returns:
            Complete response text after streaming
        """
        if prefix:
            self.console.print(prefix, end="")

        full_response = ""
        try:
            async for chunk in stream:
                # Display chunk immediately without buffering
                self.console.print(chunk, end="", markup=False)
                full_response += chunk
        except Exception as e:
            self.console.print(f"\n[red]Error during streaming: {e}[/red]")
            raise

        self.console.print()  # New line after streaming completes
        return full_response

    def show_streaming_chunk(self, chunk: str) -> None:
        """Display a single streaming chunk.

        This is a simpler alternative for synchronous streaming display.

        Args:
            chunk: Text chunk to display
        """
        self.console.print(chunk, end="", markup=False)

    def show_phase_summary(
        self,
        phase: PhaseType,
        result: PhaseResult,
        duration_seconds: float | None = None,
    ) -> None:
        """Display formatted summary after phase completion.

        Shows a formatted table with phase results, statistics, and status.

        Args:
            phase: Workflow phase that completed
            result: Phase execution result
            duration_seconds: Optional duration in seconds

        Example:
            ```python
            display.show_phase_summary(
                PhaseType.INDEXING,
                indexing_result,
                duration_seconds=45.2
            )
            ```
        """
        # Create summary table
        table = Table(
            title=f"[bold]{phase.value.title()} Phase Summary[/bold]",
            show_header=True,
            header_style="bold cyan",
            border_style="blue",
        )

        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")

        # Add status
        status_color = "green" if result.status.value == "completed" else "yellow"
        table.add_row(
            "Status",
            f"[{status_color}]{result.status.value.upper()}[/{status_color}]",
        )

        # Add message if present
        if result.message:
            table.add_row("Message", result.message)

        # Add phase-specific metrics
        self._add_phase_metrics(table, phase, result)

        # Add duration if provided
        if duration_seconds is not None:
            table.add_row("Duration", f"{duration_seconds:.2f}s")

        # Add errors if any
        if result.errors:
            error_text = "\n".join(f"• {err}" for err in result.errors)
            table.add_row("Errors", f"[red]{error_text}[/red]")

        # Display the table
        self.console.print()
        self.console.print(table)
        self.console.print()

    def _add_phase_metrics(
        self, table: Table, phase: PhaseType, result: PhaseResult
    ) -> None:
        """Add phase-specific metrics to summary table.

        Args:
            table: Rich Table to add rows to
            phase: Workflow phase
            result: Phase result with metrics
        """
        # Import here to avoid circular dependencies
        from dev_agent.models.results import (  # noqa: PLC0415
            DesignResult,
            ImplementationResult,
            IndexingResult,
            SpecificationResult,
        )

        if phase == PhaseType.INDEXING and isinstance(result, IndexingResult):
            table.add_row("Files Indexed", str(result.files_indexed))
            table.add_row("Total Lines", f"{result.total_lines:,}")
            table.add_row("Index Size", f"{result.index_size_mb:.2f} MB")
            if result.languages_detected:
                table.add_row("Languages", ", ".join(result.languages_detected))

        elif phase == PhaseType.SPECIFICATION and isinstance(
            result, SpecificationResult
        ):
            table.add_row("Requirements", str(result.requirements_count))
            if result.source_type:
                table.add_row("Source Type", result.source_type)
            if result.confidence_score > 0:
                table.add_row(
                    "Confidence", f"{result.confidence_score * 100:.1f}%"
                )

        elif phase == PhaseType.DESIGN and isinstance(result, DesignResult):
            table.add_row("Components", str(result.components_count))
            table.add_row("Interfaces", str(result.interfaces_count))
            table.add_row("Data Models", str(result.data_models_count))

        elif phase == PhaseType.IMPLEMENTATION and isinstance(
            result, ImplementationResult
        ):
            table.add_row("Tasks Completed", str(result.tasks_completed))
            table.add_row("Files Generated", str(result.files_generated))
            table.add_row("Tests Generated", str(result.tests_generated))

    def show_cost_summary(
        self, report: CostReport, title: str = "Cost Summary"
    ) -> None:
        """Display formatted cost breakdown.

        Shows detailed token usage and cost information in a formatted table.

        Args:
            report: Cost report with usage data
            title: Title for the cost summary

        Example:
            ```python
            display.show_cost_summary(
                cost_tracker.get_report(),
                title="Indexing Phase Costs"
            )
            ```
        """
        # Create cost summary table
        table = Table(
            title=f"[bold]{title}[/bold]",
            show_header=True,
            header_style="bold magenta",
            border_style="magenta",
        )

        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="yellow", justify="right")

        # Overall statistics
        table.add_row("Total Operations", str(report.operations_count))
        table.add_row("Total Tokens", f"{report.total_tokens:,}")
        table.add_row("Prompt Tokens", f"{report.total_prompt_tokens:,}")
        table.add_row("Completion Tokens", f"{report.total_completion_tokens:,}")
        table.add_row("Embedding Tokens", f"{report.total_embedding_tokens:,}")

        # Cost information
        table.add_row(
            "Total Cost",
            f"[bold green]${report.total_cost:.4f}[/bold green]",
        )

        if report.operations_count > 0:
            table.add_row(
                "Avg Cost/Operation",
                f"${report.average_cost_per_operation:.4f}",
            )
            table.add_row(
                "Avg Tokens/Operation",
                f"{report.average_tokens_per_operation:.1f}",
            )

        # Duration
        if report.duration_seconds > 0:
            table.add_row("Duration", f"{report.duration_seconds:.2f}s")

        self.console.print()
        self.console.print(table)

        # Show breakdown by phase if available
        if report.by_phase:
            self._show_cost_by_phase(report)

        # Show breakdown by operation if available
        if report.by_operation:
            self._show_cost_by_operation(report)

        self.console.print()

    def _show_cost_by_phase(self, report: CostReport) -> None:
        """Display cost breakdown by workflow phase.

        Args:
            report: Cost report with phase breakdown
        """
        table = Table(
            title="Cost by Phase",
            show_header=True,
            header_style="bold cyan",
            border_style="blue",
        )

        table.add_column("Phase", style="cyan")
        table.add_column("Cost", style="yellow", justify="right")
        table.add_column("% of Total", style="green", justify="right")

        for phase, cost in sorted(
            report.by_phase.items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (cost / report.total_cost * 100) if report.total_cost > 0 else 0
            table.add_row(
                phase.value.title(),
                f"${cost:.4f}",
                f"{percentage:.1f}%",
            )

        self.console.print()
        self.console.print(table)

    def _show_cost_by_operation(self, report: CostReport) -> None:
        """Display token usage breakdown by operation type.

        Args:
            report: Cost report with operation breakdown
        """
        table = Table(
            title="Tokens by Operation",
            show_header=True,
            header_style="bold cyan",
            border_style="blue",
        )

        table.add_column("Operation", style="cyan")
        table.add_column("Tokens", style="yellow", justify="right")
        table.add_column("% of Total", style="green", justify="right")

        for operation, tokens in sorted(
            report.by_operation.items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (
                (tokens / report.total_tokens * 100) if report.total_tokens > 0 else 0
            )
            table.add_row(
                operation.title(),
                f"{tokens:,}",
                f"{percentage:.1f}%",
            )

        self.console.print()
        self.console.print(table)

    def show_spinner(self, text: str) -> SpinnerContext:
        """Show a spinner for indeterminate operations.

        Args:
            text: Text to display next to spinner

        Returns:
            Context manager for spinner display

        Example:
            ```python
            with display.show_spinner("Processing..."):
                do_long_operation()
            ```
        """
        return SpinnerContext(console=self.console, text=text)


class IndexingProgressContext:
    """Context manager for indexing progress display.

    Provides a progress bar with file count, current file, and time estimates.
    Updates smoothly for good user experience.
    """

    def __init__(
        self, console: Console, total_files: int, description: str
    ) -> None:
        """Initialize indexing progress context.

        Args:
            console: Rich Console instance
            total_files: Total number of files to index
            description: Description text for progress bar
        """
        self.console = console
        self.total_files = total_files
        self.description = description
        self.progress: Progress | None = None
        self.task_id: TaskID | None = None
        self.current_file: str = ""

    def __enter__(self) -> IndexingProgressContext:
        """Enter context and create progress bar."""
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(complete_style="green", finished_style="bold green"),
            MofNCompleteColumn(),
            TextColumn("•"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            console=self.console,
            refresh_per_second=10,  # Requirement 10.5: Update 10+ times/sec
        )
        self.progress.start()
        self.task_id = self.progress.add_task(
            self.description, total=self.total_files
        )
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit context and stop progress bar."""
        if self.progress:
            self.progress.stop()

    def update(
        self, completed: int, current_file: str | None = None
    ) -> None:
        """Update progress bar.

        Args:
            completed: Number of files completed
            current_file: Optional current file being processed
        """
        if self.progress and self.task_id is not None:
            description = self.description
            if current_file:
                # Truncate long file paths for display
                display_file = (
                    current_file
                    if len(current_file) <= 50
                    else f"...{current_file[-47:]}"
                )
                description = f"{self.description}: {display_file}"

            self.progress.update(
                self.task_id, completed=completed, description=description
            )


class SpinnerContext:
    """Context manager for spinner display.

    Shows a spinner for indeterminate operations.
    """

    def __init__(self, console: Console, text: str) -> None:
        """Initialize spinner context.

        Args:
            console: Rich Console instance
            text: Text to display next to spinner
        """
        self.console = console
        self.text = text
        self.progress: Progress | None = None
        self.task_id: TaskID | None = None

    def __enter__(self) -> SpinnerContext:
        """Enter context and start spinner."""
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            console=self.console,
            refresh_per_second=10,
        )
        self.progress.start()
        self.task_id = self.progress.add_task(self.text, total=None)
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit context and stop spinner."""
        if self.progress:
            self.progress.stop()

    def update(self, text: str) -> None:
        """Update spinner text.

        Args:
            text: New text to display
        """
        if self.progress and self.task_id is not None:
            self.progress.update(self.task_id, description=text)

