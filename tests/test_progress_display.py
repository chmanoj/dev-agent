"""Tests for progress display system."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from io import StringIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rich.console import Console

from dev_agent.cli.progress_display import (
    IndexingProgressContext,
    ProgressDisplay,
    SpinnerContext,
)
from dev_agent.models.cost_tracking import CostReport, TokenUsage
from dev_agent.models.enums import LLMOperationType, PhaseStatus, PhaseType
from dev_agent.models.results import (
    DesignResult,
    ImplementationResult,
    IndexingResult,
    PhaseResult,
    SpecificationResult,
)


@pytest.fixture
def console() -> Console:
    """Create a Rich Console with string output for testing."""
    return Console(file=StringIO(), force_terminal=True, width=120)


@pytest.fixture
def progress_display(console: Console) -> ProgressDisplay:
    """Create a ProgressDisplay instance for testing."""
    return ProgressDisplay(console=console)


class TestProgressDisplay:
    """Test suite for ProgressDisplay class."""

    def test_init_default_console(self) -> None:
        """Test initialization with default console."""
        display = ProgressDisplay()
        assert display.console is not None

    def test_init_custom_console(self, console: Console) -> None:
        """Test initialization with custom console."""
        display = ProgressDisplay(console=console)
        assert display.console is console

    def test_show_indexing_progress_context(
        self, progress_display: ProgressDisplay
    ) -> None:
        """Test indexing progress context manager."""
        context = progress_display.show_indexing_progress(
            total_files=100, description="Indexing"
        )
        assert isinstance(context, IndexingProgressContext)
        assert context.total_files == 100
        assert context.description == "Indexing"

    def test_show_indexing_progress_with_updates(
        self, progress_display: ProgressDisplay
    ) -> None:
        """Test indexing progress with file updates."""
        with progress_display.show_indexing_progress(10) as progress:
            for i in range(10):
                progress.update(i + 1, current_file=f"file_{i}.py")

        # Verify no exceptions were raised
        assert True

    def test_show_indexing_progress_long_filename(
        self, progress_display: ProgressDisplay
    ) -> None:
        """Test indexing progress with long filename truncation."""
        long_filename = "a" * 100 + ".py"
        with progress_display.show_indexing_progress(1) as progress:
            progress.update(1, current_file=long_filename)

        # Verify no exceptions were raised
        assert True

    @pytest.mark.asyncio
    async def test_show_streaming_response_async(
        self, progress_display: ProgressDisplay
    ) -> None:
        """Test async streaming response display."""

        async def mock_stream() -> AsyncMock:
            """Create mock async stream."""
            for chunk in ["Hello", " ", "world", "!"]:
                yield chunk

        result = await progress_display._show_streaming_response_async(
            mock_stream(), prefix="Response: "
        )

        assert result == "Hello world!"

    @pytest.mark.asyncio
    async def test_show_streaming_response_with_error(
        self, progress_display: ProgressDisplay
    ) -> None:
        """Test streaming response with error handling."""

        async def error_stream() -> AsyncMock:
            """Create mock stream that raises error."""
            yield "Start"
            raise ValueError("Stream error")

        with pytest.raises(ValueError, match="Stream error"):
            await progress_display._show_streaming_response_async(error_stream())

    def test_show_streaming_chunk(
        self, progress_display: ProgressDisplay, console: Console
    ) -> None:
        """Test displaying single streaming chunk."""
        progress_display.show_streaming_chunk("test chunk")

        output = console.file.getvalue()  # type: ignore
        assert "test chunk" in output

    def test_show_phase_summary_indexing(
        self, progress_display: ProgressDisplay
    ) -> None:
        """Test phase summary for indexing phase."""
        result = IndexingResult(
            phase=PhaseType.INDEXING,
            status=PhaseStatus.COMPLETED,
            message="Indexing completed successfully",
            files_indexed=150,
            total_lines=5000,
            index_size_mb=2.5,
            languages_detected=["Python", "JavaScript"],
        )

        progress_display.show_phase_summary(
            PhaseType.INDEXING, result, duration_seconds=45.2
        )

        output = progress_display.console.file.getvalue()  # type: ignore
        assert "Indexing Phase Summary" in output
        assert "150" in output  # files_indexed
        assert "5,000" in output  # total_lines
        assert "2.50 MB" in output  # index_size_mb
        assert "Python" in output
        assert "45.2" in output  # duration

    def test_show_phase_summary_specification(
        self, progress_display: ProgressDisplay
    ) -> None:
        """Test phase summary for specification phase."""
        result = SpecificationResult(
            phase=PhaseType.SPECIFICATION,
            status=PhaseStatus.COMPLETED,
            message="Specification generated",
            requirements_count=25,
            source_type="existing_codebase",
            confidence_score=0.92,
        )

        progress_display.show_phase_summary(PhaseType.SPECIFICATION, result)

        output = progress_display.console.file.getvalue()  # type: ignore
        assert "Specification Phase Summary" in output
        assert "25" in output  # requirements_count
        assert "92.0%" in output  # confidence_score

    def test_show_phase_summary_design(
        self, progress_display: ProgressDisplay
    ) -> None:
        """Test phase summary for design phase."""
        result = DesignResult(
            phase=PhaseType.DESIGN,
            status=PhaseStatus.COMPLETED,
            message="Design completed",
            components_count=12,
            interfaces_count=8,
            data_models_count=15,
        )

        progress_display.show_phase_summary(PhaseType.DESIGN, result)

        output = progress_display.console.file.getvalue()  # type: ignore
        assert "Design Phase Summary" in output
        assert "12" in output  # components_count
        assert "8" in output  # interfaces_count
        assert "15" in output  # data_models_count

    def test_show_phase_summary_implementation(
        self, progress_display: ProgressDisplay
    ) -> None:
        """Test phase summary for implementation phase."""
        result = ImplementationResult(
            phase=PhaseType.IMPLEMENTATION,
            status=PhaseStatus.COMPLETED,
            message="Implementation completed",
            tasks_completed=30,
            files_generated=45,
            tests_generated=60,
        )

        progress_display.show_phase_summary(PhaseType.IMPLEMENTATION, result)

        output = progress_display.console.file.getvalue()  # type: ignore
        assert "Implementation Phase Summary" in output
        assert "30" in output  # tasks_completed
        assert "45" in output  # files_generated
        assert "60" in output  # tests_generated

    def test_show_phase_summary_with_errors(
        self, progress_display: ProgressDisplay
    ) -> None:
        """Test phase summary with errors."""
        result = PhaseResult(
            phase=PhaseType.INDEXING,
            status=PhaseStatus.FAILED,
            message="Phase failed",
            errors=["Error 1", "Error 2"],
        )

        progress_display.show_phase_summary(PhaseType.INDEXING, result)

        output = progress_display.console.file.getvalue()  # type: ignore
        assert "Error 1" in output
        assert "Error 2" in output

    def test_show_cost_summary_basic(
        self, progress_display: ProgressDisplay
    ) -> None:
        """Test basic cost summary display."""
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

        progress_display.show_cost_summary(report)

        output = progress_display.console.file.getvalue()  # type: ignore
        assert "Cost Summary" in output
        assert "10" in output  # operations_count
        assert "3,500" in output  # total_tokens
        assert "1,000" in output  # prompt_tokens
        assert "2,000" in output  # completion_tokens
        assert "500" in output  # embedding_tokens
        assert "$0.15" in output  # total_cost

    def test_show_cost_summary_with_phase_breakdown(
        self, progress_display: ProgressDisplay
    ) -> None:
        """Test cost summary with phase breakdown."""
        report = CostReport(
            total_prompt_tokens=1000,
            total_completion_tokens=2000,
            total_embedding_tokens=500,
            total_cost=0.15,
            operations_count=10,
            by_phase={
                PhaseType.INDEXING: 0.05,
                PhaseType.SPECIFICATION: 0.06,
                PhaseType.DESIGN: 0.04,
            },
            by_operation={},
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(seconds=30),
        )

        progress_display.show_cost_summary(report)

        output = progress_display.console.file.getvalue()  # type: ignore
        assert "Cost by Phase" in output
        assert "Indexing" in output
        assert "Specification" in output
        assert "Design" in output

    def test_show_cost_summary_with_operation_breakdown(
        self, progress_display: ProgressDisplay
    ) -> None:
        """Test cost summary with operation breakdown."""
        report = CostReport(
            total_prompt_tokens=1000,
            total_completion_tokens=2000,
            total_embedding_tokens=500,
            total_cost=0.15,
            operations_count=10,
            by_phase={},
            by_operation={
                "completion": 3000,
                "embedding": 500,
            },
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(seconds=30),
        )

        progress_display.show_cost_summary(report)

        output = progress_display.console.file.getvalue()  # type: ignore
        assert "Tokens by Operation" in output
        assert "Completion" in output
        assert "Embedding" in output

    def test_show_cost_summary_custom_title(
        self, progress_display: ProgressDisplay
    ) -> None:
        """Test cost summary with custom title."""
        report = CostReport.create_empty()

        progress_display.show_cost_summary(report, title="Custom Title")

        output = progress_display.console.file.getvalue()  # type: ignore
        assert "Custom Title" in output

    def test_show_spinner_context(self, progress_display: ProgressDisplay) -> None:
        """Test spinner context manager."""
        context = progress_display.show_spinner("Processing...")
        assert isinstance(context, SpinnerContext)
        assert context.text == "Processing..."

    def test_show_spinner_with_updates(
        self, progress_display: ProgressDisplay
    ) -> None:
        """Test spinner with text updates."""
        with progress_display.show_spinner("Initial") as spinner:
            spinner.update("Updated text")

        # Verify no exceptions were raised
        assert True


class TestIndexingProgressContext:
    """Test suite for IndexingProgressContext."""

    def test_init(self, console: Console) -> None:
        """Test context initialization."""
        context = IndexingProgressContext(
            console=console, total_files=100, description="Test"
        )
        assert context.console is console
        assert context.total_files == 100
        assert context.description == "Test"
        assert context.progress is None
        assert context.task_id is None

    def test_context_manager(self, console: Console) -> None:
        """Test context manager enter and exit."""
        context = IndexingProgressContext(
            console=console, total_files=10, description="Test"
        )

        with context:
            assert context.progress is not None
            assert context.task_id is not None

        # Progress should be stopped after exit
        assert context.progress is not None  # Object still exists

    def test_update_without_file(self, console: Console) -> None:
        """Test update without current file."""
        context = IndexingProgressContext(
            console=console, total_files=10, description="Test"
        )

        with context:
            context.update(5)

        # Verify no exceptions were raised
        assert True

    def test_update_with_file(self, console: Console) -> None:
        """Test update with current file."""
        context = IndexingProgressContext(
            console=console, total_files=10, description="Test"
        )

        with context:
            context.update(5, current_file="test.py")

        # Verify no exceptions were raised
        assert True

    def test_update_with_long_file(self, console: Console) -> None:
        """Test update with long filename."""
        context = IndexingProgressContext(
            console=console, total_files=10, description="Test"
        )

        long_file = "a" * 100 + ".py"
        with context:
            context.update(5, current_file=long_file)

        # Verify no exceptions were raised
        assert True


class TestSpinnerContext:
    """Test suite for SpinnerContext."""

    def test_init(self, console: Console) -> None:
        """Test context initialization."""
        context = SpinnerContext(console=console, text="Loading")
        assert context.console is console
        assert context.text == "Loading"
        assert context.progress is None
        assert context.task_id is None

    def test_context_manager(self, console: Console) -> None:
        """Test context manager enter and exit."""
        context = SpinnerContext(console=console, text="Loading")

        with context:
            assert context.progress is not None
            assert context.task_id is not None

        # Progress should be stopped after exit
        assert context.progress is not None  # Object still exists

    def test_update(self, console: Console) -> None:
        """Test spinner text update."""
        context = SpinnerContext(console=console, text="Initial")

        with context:
            context.update("Updated")

        # Verify no exceptions were raised
        assert True


class TestProgressDisplayIntegration:
    """Integration tests for progress display system."""

    def test_complete_indexing_workflow(
        self, progress_display: ProgressDisplay
    ) -> None:
        """Test complete indexing workflow with progress and summary."""
        # Show progress
        with progress_display.show_indexing_progress(5) as progress:
            for i in range(5):
                progress.update(i + 1, current_file=f"file_{i}.py")

        # Show summary
        result = IndexingResult(
            phase=PhaseType.INDEXING,
            status=PhaseStatus.COMPLETED,
            message="Success",
            files_indexed=5,
            total_lines=500,
            index_size_mb=0.5,
            languages_detected=["Python"],
        )
        progress_display.show_phase_summary(PhaseType.INDEXING, result)

        # Show cost
        report = CostReport.create_empty()
        progress_display.show_cost_summary(report, title="Indexing Costs")

        # Verify no exceptions were raised
        assert True

    def test_multiple_phases_workflow(
        self, progress_display: ProgressDisplay
    ) -> None:
        """Test displaying summaries for multiple phases."""
        phases_results = [
            (
                PhaseType.INDEXING,
                IndexingResult(
                    phase=PhaseType.INDEXING,
                    status=PhaseStatus.COMPLETED,
                    message="Indexed",
                    files_indexed=10,
                ),
            ),
            (
                PhaseType.SPECIFICATION,
                SpecificationResult(
                    phase=PhaseType.SPECIFICATION,
                    status=PhaseStatus.COMPLETED,
                    message="Generated",
                    requirements_count=5,
                ),
            ),
            (
                PhaseType.DESIGN,
                DesignResult(
                    phase=PhaseType.DESIGN,
                    status=PhaseStatus.COMPLETED,
                    message="Designed",
                    components_count=3,
                ),
            ),
        ]

        for phase, result in phases_results:
            progress_display.show_phase_summary(phase, result)

        # Verify no exceptions were raised
        assert True

    def test_error_handling_display(
        self, progress_display: ProgressDisplay
    ) -> None:
        """Test displaying errors in phase summary."""
        result = PhaseResult(
            phase=PhaseType.INDEXING,
            status=PhaseStatus.FAILED,
            message="Failed to index",
            errors=[
                "File not found: missing.py",
                "Permission denied: protected.py",
            ],
        )

        progress_display.show_phase_summary(PhaseType.INDEXING, result)

        output = progress_display.console.file.getvalue()  # type: ignore
        assert "File not found" in output
        assert "Permission denied" in output

