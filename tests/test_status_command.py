"""Tests for the status command."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from dev_agent.cli.main import app
from dev_agent.models.cost_tracking import CostReport
from dev_agent.models.enums import PhaseType, TaskStatus
from dev_agent.models.project_state import (
    IndexMetadata,
    ProjectState,
    SessionData,
)


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


@pytest.fixture
def mock_project_state():
    """Create a mock project state."""
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
def mock_cost_report():
    """Create a mock cost report."""
    report = CostReport.create_empty(start_time=datetime(2024, 1, 15, 9, 0, 0))
    report.total_prompt_tokens = 1000
    report.total_completion_tokens = 500
    report.total_embedding_tokens = 2000
    report.total_cost = 0.15
    report.operations_count = 10
    report.by_phase = {
        PhaseType.INDEXING: 0.05,
        PhaseType.SPECIFICATION: 0.10,
    }
    return report


def test_status_command_no_project(runner, tmp_path):
    """Test status command when no project exists."""
    result = runner.invoke(app, ["status", str(tmp_path)])

    assert result.exit_code == 1
    assert ("No dev-agent project found" in result.stdout or 
            "Could not load project state" in result.stdout)


def test_status_command_basic(runner, tmp_path, mock_project_state, mock_cost_report):
    """Test basic status command output."""
    # Create .dev_agent directory
    dev_agent_dir = tmp_path / ".dev_agent"
    dev_agent_dir.mkdir()

    with (
        patch("dev_agent.workflow.workflow_manager.WorkflowManager") as mock_wf_manager,
        patch("dev_agent.cli.main.setup_cli_logging"),
    ):
        # Setup mocks
        mock_manager_instance = MagicMock()
        mock_manager_instance.resume_project.return_value = mock_project_state
        mock_manager_instance.cost_tracker.get_report.return_value = mock_cost_report
        mock_wf_manager.return_value = mock_manager_instance

        result = runner.invoke(app, ["status", str(tmp_path)])

        assert result.exit_code == 0
        assert "Project Status" in result.stdout
        assert "Workflow Progress" in result.stdout
        assert "Cost Summary" in result.stdout
        assert "Indexing" in result.stdout
        assert "Specification" in result.stdout
        assert "Design" in result.stdout
        assert "Implementation" in result.stdout


def test_status_command_shows_completed_phases(
    runner, tmp_path, mock_project_state, mock_cost_report
):
    """Test that status command shows completed phases with checkmarks."""
    dev_agent_dir = tmp_path / ".dev_agent"
    dev_agent_dir.mkdir()

    # Set current phase to DESIGN (so INDEXING and SPECIFICATION are complete)
    mock_project_state.current_phase = PhaseType.DESIGN
    mock_project_state.specification = MagicMock()

    with (
        patch("dev_agent.workflow.workflow_manager.WorkflowManager") as mock_wf_manager,
        patch("dev_agent.cli.main.setup_cli_logging"),
    ):
        mock_manager_instance = MagicMock()
        mock_manager_instance.resume_project.return_value = mock_project_state
        mock_manager_instance.cost_tracker.get_report.return_value = mock_cost_report
        mock_wf_manager.return_value = mock_manager_instance

        result = runner.invoke(app, ["status", str(tmp_path)])

        assert result.exit_code == 0
        assert "✓ Complete" in result.stdout
        assert "⚡ In Progress" in result.stdout


def test_status_command_shows_progress_percentage(
    runner, tmp_path, mock_project_state, mock_cost_report
):
    """Test that status command shows progress percentages."""
    dev_agent_dir = tmp_path / ".dev_agent"
    dev_agent_dir.mkdir()

    with (
        patch("dev_agent.workflow.workflow_manager.WorkflowManager") as mock_wf_manager,
        patch("dev_agent.cli.main.setup_cli_logging"),
    ):
        mock_manager_instance = MagicMock()
        mock_manager_instance.resume_project.return_value = mock_project_state
        mock_manager_instance.cost_tracker.get_report.return_value = mock_cost_report
        mock_wf_manager.return_value = mock_manager_instance

        result = runner.invoke(app, ["status", str(tmp_path)])

        assert result.exit_code == 0
        # Should show percentages
        assert "100%" in result.stdout or "50%" in result.stdout or "0%" in result.stdout


def test_status_command_shows_cost_information(
    runner, tmp_path, mock_project_state, mock_cost_report
):
    """Test that status command displays cost information."""
    dev_agent_dir = tmp_path / ".dev_agent"
    dev_agent_dir.mkdir()

    with (
        patch("dev_agent.workflow.workflow_manager.WorkflowManager") as mock_wf_manager,
        patch("dev_agent.cli.main.setup_cli_logging"),
    ):
        mock_manager_instance = MagicMock()
        mock_manager_instance.resume_project.return_value = mock_project_state
        mock_manager_instance.cost_tracker.get_report.return_value = mock_cost_report
        mock_wf_manager.return_value = mock_manager_instance

        result = runner.invoke(app, ["status", str(tmp_path)])

        assert result.exit_code == 0
        assert "Cost Summary" in result.stdout
        assert "Total Operations" in result.stdout
        assert "Total Tokens" in result.stdout
        assert "Total Cost" in result.stdout
        assert "$0.15" in result.stdout or "0.1500" in result.stdout


def test_status_command_shows_cost_by_phase(
    runner, tmp_path, mock_project_state, mock_cost_report
):
    """Test that status command shows cost breakdown by phase."""
    dev_agent_dir = tmp_path / ".dev_agent"
    dev_agent_dir.mkdir()

    with (
        patch("dev_agent.workflow.workflow_manager.WorkflowManager") as mock_wf_manager,
        patch("dev_agent.cli.main.setup_cli_logging"),
    ):
        mock_manager_instance = MagicMock()
        mock_manager_instance.resume_project.return_value = mock_project_state
        mock_manager_instance.cost_tracker.get_report.return_value = mock_cost_report
        mock_wf_manager.return_value = mock_manager_instance

        result = runner.invoke(app, ["status", str(tmp_path)])

        assert result.exit_code == 0
        # Should show phase-specific costs
        assert "Indexing Phase" in result.stdout or "indexing" in result.stdout.lower()


def test_status_command_shows_last_activity(
    runner, tmp_path, mock_project_state, mock_cost_report
):
    """Test that status command displays last activity timestamp."""
    dev_agent_dir = tmp_path / ".dev_agent"
    dev_agent_dir.mkdir()

    with (
        patch("dev_agent.workflow.workflow_manager.WorkflowManager") as mock_wf_manager,
        patch("dev_agent.cli.main.setup_cli_logging"),
    ):
        mock_manager_instance = MagicMock()
        mock_manager_instance.resume_project.return_value = mock_project_state
        mock_manager_instance.cost_tracker.get_report.return_value = mock_cost_report
        mock_wf_manager.return_value = mock_manager_instance

        result = runner.invoke(app, ["status", str(tmp_path)])

        assert result.exit_code == 0
        assert "Last Activity" in result.stdout
        assert "2024-01-15" in result.stdout


def test_status_command_detailed_flag(
    runner, tmp_path, mock_project_state, mock_cost_report
):
    """Test status command with --detailed flag."""
    dev_agent_dir = tmp_path / ".dev_agent"
    dev_agent_dir.mkdir()

    with (
        patch("dev_agent.workflow.workflow_manager.WorkflowManager") as mock_wf_manager,
        patch("dev_agent.cli.main.setup_cli_logging"),
    ):
        mock_manager_instance = MagicMock()
        mock_manager_instance.resume_project.return_value = mock_project_state
        mock_manager_instance.cost_tracker.get_report.return_value = mock_cost_report
        mock_wf_manager.return_value = mock_manager_instance

        result = runner.invoke(app, ["status", str(tmp_path), "--detailed"])

        assert result.exit_code == 0
        assert "Detailed Information" in result.stdout
        assert "Index Metadata" in result.stdout
        assert "Session Information" in result.stdout
        assert "Token Usage Breakdown" in result.stdout
        assert "Total Files" in result.stdout
        assert "Session ID" in result.stdout


def test_status_command_shows_next_steps(
    runner, tmp_path, mock_project_state, mock_cost_report
):
    """Test that status command provides next steps guidance."""
    dev_agent_dir = tmp_path / ".dev_agent"
    dev_agent_dir.mkdir()

    with (
        patch("dev_agent.workflow.workflow_manager.WorkflowManager") as mock_wf_manager,
        patch("dev_agent.cli.main.setup_cli_logging"),
    ):
        mock_manager_instance = MagicMock()
        mock_manager_instance.resume_project.return_value = mock_project_state
        mock_manager_instance.cost_tracker.get_report.return_value = mock_cost_report
        mock_wf_manager.return_value = mock_manager_instance

        result = runner.invoke(app, ["status", str(tmp_path)])

        assert result.exit_code == 0
        assert "Next Steps" in result.stdout
        assert "dev-agent resume" in result.stdout


def test_status_command_implementation_progress(
    runner, tmp_path, mock_project_state, mock_cost_report
):
    """Test status command shows implementation progress correctly."""
    dev_agent_dir = tmp_path / ".dev_agent"
    dev_agent_dir.mkdir()

    # Set to implementation phase with some completed tasks
    mock_project_state.current_phase = PhaseType.IMPLEMENTATION
    mock_project_state.tasks = MagicMock()
    mock_project_state.implementation_progress = {
        "task1": TaskStatus.COMPLETED,
        "task2": TaskStatus.COMPLETED,
        "task3": TaskStatus.IN_PROGRESS,
        "task4": TaskStatus.NOT_STARTED,
    }

    with (
        patch("dev_agent.workflow.workflow_manager.WorkflowManager") as mock_wf_manager,
        patch("dev_agent.cli.main.setup_cli_logging"),
    ):
        mock_manager_instance = MagicMock()
        mock_manager_instance.resume_project.return_value = mock_project_state
        mock_manager_instance.cost_tracker.get_report.return_value = mock_cost_report
        mock_wf_manager.return_value = mock_manager_instance

        result = runner.invoke(app, ["status", str(tmp_path)])

        assert result.exit_code == 0
        # Should show implementation progress
        assert "Implementation" in result.stdout
        # Should calculate progress (2/4 = 50%)
        assert "50%" in result.stdout or "2/4" in result.stdout


def test_status_command_uses_current_directory_by_default(
    runner, mock_project_state, mock_cost_report, monkeypatch, tmp_path
):
    """Test that status command uses current directory when no path provided."""
    dev_agent_dir = tmp_path / ".dev_agent"
    dev_agent_dir.mkdir()

    # Change to tmp_path
    monkeypatch.chdir(tmp_path)

    with (
        patch("dev_agent.workflow.workflow_manager.WorkflowManager") as mock_wf_manager,
        patch("dev_agent.cli.main.setup_cli_logging"),
    ):
        mock_manager_instance = MagicMock()
        mock_manager_instance.resume_project.return_value = mock_project_state
        mock_manager_instance.cost_tracker.get_report.return_value = mock_cost_report
        mock_wf_manager.return_value = mock_manager_instance

        result = runner.invoke(app, ["status"])

        assert result.exit_code == 0
        assert "Project Status" in result.stdout


def test_status_command_handles_load_error(runner, tmp_path):
    """Test status command handles project state load errors gracefully."""
    dev_agent_dir = tmp_path / ".dev_agent"
    dev_agent_dir.mkdir()

    with (
        patch("dev_agent.workflow.workflow_manager.WorkflowManager") as mock_wf_manager,
        patch("dev_agent.cli.main.setup_cli_logging"),
    ):
        mock_manager_instance = MagicMock()
        mock_manager_instance.resume_project.side_effect = Exception("Load failed")
        mock_wf_manager.return_value = mock_manager_instance

        result = runner.invoke(app, ["status", str(tmp_path)])

        assert result.exit_code == 1
        assert "Could not load project state" in result.stdout
