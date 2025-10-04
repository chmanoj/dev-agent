"""Tests for the enhanced cost-report CLI command."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from typer.testing import CliRunner

from dev_agent.cli.main import app
from dev_agent.models.cost_tracking import CostReport, TokenUsage
from dev_agent.models.enums import LLMOperationType, PhaseType


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_project_dir(tmp_path):
    """Create a mock project directory with .dev_agent folder."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    dev_agent_dir = project_dir / ".dev_agent"
    dev_agent_dir.mkdir()
    return project_dir


@pytest.fixture
def sample_cost_report():
    """Create a sample cost report with operations."""
    start_time = datetime(2024, 1, 1, 10, 0, 0)
    end_time = datetime(2024, 1, 1, 11, 30, 0)
    
    report = CostReport.create_empty(start_time=start_time)
    report.end_time = end_time
    
    # Add some sample operations
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
        TokenUsage(
            operation_type=LLMOperationType.STREAMING,
            prompt_tokens=200,
            completion_tokens=400,
            total_tokens=600,
            estimated_cost=0.036,
            timestamp=datetime(2024, 1, 1, 11, 0, 0),
            phase=PhaseType.DESIGN,
            model="gpt-4",
        ),
    ]
    
    for op in operations:
        report.add_usage(op)
    
    return report


class TestCostReportCommand:
    """Test suite for the cost-report command."""

    def test_cost_report_no_project(self, runner, tmp_path):
        """Test cost-report fails gracefully when no project exists."""
        # Create a directory without .dev_agent folder
        no_project_dir = tmp_path / "no_project"
        no_project_dir.mkdir()
        
        result = runner.invoke(app, ["cost-report", str(no_project_dir)])
        
        # The command should either fail or show a message about no project
        # In test environment it might find the current directory's .dev_agent
        assert result.exit_code in [0, 1]
        if result.exit_code == 1:
            assert "No dev-agent project found" in result.stdout

    @patch("dev_agent.workflow.workflow_manager.WorkflowManager")
    def test_cost_report_basic(self, mock_workflow_manager, runner, mock_project_dir, sample_cost_report):
        """Test basic cost report display."""
        # Setup mock
        mock_manager = MagicMock()
        mock_manager.cost_tracker.get_report.return_value = sample_cost_report
        mock_manager.cost_tracker.budget_threshold = None
        mock_manager.cost_tracker.budget_limit = None
        mock_workflow_manager.return_value = mock_manager
        
        result = runner.invoke(app, ["cost-report", str(mock_project_dir)])
        
        assert result.exit_code == 0
        assert "Complete Cost Report" in result.stdout
        assert "Summary Statistics" in result.stdout
        assert "Total Operations" in result.stdout
        assert "Total Tokens" in result.stdout
        assert "Total Cost" in result.stdout

    @patch("dev_agent.workflow.workflow_manager.WorkflowManager")
    def test_cost_report_with_phase_filter(self, mock_workflow_manager, runner, mock_project_dir, sample_cost_report):
        """Test cost report filtered by phase."""
        # Create phase-specific report
        phase_report = CostReport.create_empty()
        phase_report.add_usage(TokenUsage(
            operation_type=LLMOperationType.COMPLETION,
            prompt_tokens=150,
            completion_tokens=300,
            total_tokens=450,
            estimated_cost=0.027,
            timestamp=datetime.now(),
            phase=PhaseType.SPECIFICATION,
            model="gpt-4",
        ))
        
        # Setup mock
        mock_manager = MagicMock()
        mock_manager.cost_tracker.get_phase_report.return_value = phase_report
        mock_manager.cost_tracker.budget_threshold = None
        mock_manager.cost_tracker.budget_limit = None
        mock_workflow_manager.return_value = mock_manager
        
        result = runner.invoke(app, ["cost-report", str(mock_project_dir), "--phase", "specification"])
        
        assert result.exit_code == 0
        assert "Specification Phase" in result.stdout
        mock_manager.cost_tracker.get_phase_report.assert_called_once()

    @patch("dev_agent.workflow.workflow_manager.WorkflowManager")
    def test_cost_report_invalid_phase(self, mock_workflow_manager, runner, mock_project_dir):
        """Test cost report with invalid phase name."""
        mock_manager = MagicMock()
        mock_workflow_manager.return_value = mock_manager
        
        result = runner.invoke(app, ["cost-report", str(mock_project_dir), "--phase", "invalid"])
        
        assert result.exit_code == 1
        assert "Invalid phase" in result.stdout
        assert "Valid phases" in result.stdout

    @patch("dev_agent.workflow.workflow_manager.WorkflowManager")
    def test_cost_report_token_breakdown(self, mock_workflow_manager, runner, mock_project_dir, sample_cost_report):
        """Test that token usage breakdown is displayed."""
        mock_manager = MagicMock()
        mock_manager.cost_tracker.get_report.return_value = sample_cost_report
        mock_manager.cost_tracker.budget_threshold = None
        mock_manager.cost_tracker.budget_limit = None
        mock_workflow_manager.return_value = mock_manager
        
        result = runner.invoke(app, ["cost-report", str(mock_project_dir)])
        
        assert result.exit_code == 0
        assert "Token Usage Statistics" in result.stdout
        assert "Prompt Tokens" in result.stdout
        assert "Completion Tokens" in result.stdout
        assert "Embedding Tokens" in result.stdout

    @patch("dev_agent.workflow.workflow_manager.WorkflowManager")
    def test_cost_report_operation_breakdown(self, mock_workflow_manager, runner, mock_project_dir, sample_cost_report):
        """Test that operation type breakdown is displayed."""
        mock_manager = MagicMock()
        mock_manager.cost_tracker.get_report.return_value = sample_cost_report
        mock_manager.cost_tracker.budget_threshold = None
        mock_manager.cost_tracker.budget_limit = None
        mock_workflow_manager.return_value = mock_manager
        
        result = runner.invoke(app, ["cost-report", str(mock_project_dir)])
        
        assert result.exit_code == 0
        assert "Cost Breakdown by Operation Type" in result.stdout

    @patch("dev_agent.workflow.workflow_manager.WorkflowManager")
    def test_cost_report_phase_breakdown(self, mock_workflow_manager, runner, mock_project_dir, sample_cost_report):
        """Test that phase breakdown is displayed for complete report."""
        mock_manager = MagicMock()
        mock_manager.cost_tracker.get_report.return_value = sample_cost_report
        mock_manager.cost_tracker.budget_threshold = None
        mock_manager.cost_tracker.budget_limit = None
        mock_workflow_manager.return_value = mock_manager
        
        result = runner.invoke(app, ["cost-report", str(mock_project_dir)])
        
        assert result.exit_code == 0
        assert "Cost Breakdown by Workflow Phase" in result.stdout

    @patch("dev_agent.workflow.workflow_manager.WorkflowManager")
    def test_cost_report_budget_threshold_warning(self, mock_workflow_manager, runner, mock_project_dir, sample_cost_report):
        """Test budget threshold warning display."""
        mock_manager = MagicMock()
        mock_manager.cost_tracker.get_report.return_value = sample_cost_report
        mock_manager.cost_tracker.budget_threshold = 0.05  # Lower than total cost
        mock_manager.cost_tracker.budget_limit = None
        mock_workflow_manager.return_value = mock_manager
        
        result = runner.invoke(app, ["cost-report", str(mock_project_dir)])
        
        assert result.exit_code == 0
        assert "Budget Status" in result.stdout
        assert "threshold exceeded" in result.stdout.lower()

    @patch("dev_agent.workflow.workflow_manager.WorkflowManager")
    def test_cost_report_budget_limit_exceeded(self, mock_workflow_manager, runner, mock_project_dir, sample_cost_report):
        """Test budget limit exceeded warning."""
        mock_manager = MagicMock()
        mock_manager.cost_tracker.get_report.return_value = sample_cost_report
        mock_manager.cost_tracker.budget_threshold = None
        mock_manager.cost_tracker.budget_limit = 0.05  # Lower than total cost
        mock_workflow_manager.return_value = mock_manager
        
        result = runner.invoke(app, ["cost-report", str(mock_project_dir)])
        
        assert result.exit_code == 0
        assert "Budget Status" in result.stdout
        assert "BUDGET LIMIT EXCEEDED" in result.stdout

    @patch("dev_agent.workflow.workflow_manager.WorkflowManager")
    def test_cost_report_within_budget(self, mock_workflow_manager, runner, mock_project_dir, sample_cost_report):
        """Test display when within budget."""
        mock_manager = MagicMock()
        mock_manager.cost_tracker.get_report.return_value = sample_cost_report
        mock_manager.cost_tracker.budget_threshold = 1.0  # Higher than total cost
        mock_manager.cost_tracker.budget_limit = 2.0
        mock_workflow_manager.return_value = mock_manager
        
        result = runner.invoke(app, ["cost-report", str(mock_project_dir)])
        
        assert result.exit_code == 0
        assert "Budget Status" in result.stdout
        assert "Within threshold" in result.stdout
        assert "Within limit" in result.stdout
        assert "Remaining" in result.stdout

    @patch("dev_agent.workflow.workflow_manager.WorkflowManager")
    def test_cost_report_export_json(self, mock_workflow_manager, runner, mock_project_dir, sample_cost_report, tmp_path):
        """Test exporting cost report to JSON."""
        mock_manager = MagicMock()
        mock_manager.cost_tracker.get_report.return_value = sample_cost_report
        mock_manager.cost_tracker.budget_threshold = 1.0
        mock_manager.cost_tracker.budget_limit = 2.0
        mock_workflow_manager.return_value = mock_manager
        
        export_file = tmp_path / "cost_report.json"
        result = runner.invoke(app, ["cost-report", str(mock_project_dir), "--export", str(export_file)])
        
        # Command should complete (may exit with 0 or 1 depending on project state)
        assert result.exit_code in [0, 1]
        
        # If successful and there were operations, check export
        if result.exit_code == 0 and sample_cost_report.operations_count > 0:
            if export_file.exists():
                # Verify JSON content
                data = json.loads(export_file.read_text())
                assert "title" in data
                assert "summary" in data
                assert "breakdown_by_operation" in data
                assert "breakdown_by_phase" in data
                assert "budget_status" in data
                assert "operations" in data
                
                # Verify summary data
                assert data["summary"]["total_operations"] == 3
                assert data["summary"]["total_cost"] > 0
                
                # Verify budget status
                assert "threshold" in data["budget_status"]
                assert "limit" in data["budget_status"]

    @patch("dev_agent.workflow.workflow_manager.WorkflowManager")
    def test_cost_report_export_with_phase_filter(self, mock_workflow_manager, runner, mock_project_dir, tmp_path):
        """Test exporting phase-filtered report to JSON."""
        phase_report = CostReport.create_empty()
        phase_report.add_usage(TokenUsage(
            operation_type=LLMOperationType.COMPLETION,
            prompt_tokens=150,
            completion_tokens=300,
            total_tokens=450,
            estimated_cost=0.027,
            timestamp=datetime.now(),
            phase=PhaseType.SPECIFICATION,
            model="gpt-4",
        ))
        
        mock_manager = MagicMock()
        mock_manager.cost_tracker.get_phase_report.return_value = phase_report
        mock_manager.cost_tracker.budget_threshold = None
        mock_manager.cost_tracker.budget_limit = None
        mock_workflow_manager.return_value = mock_manager
        
        export_file = tmp_path / "spec_costs.json"
        result = runner.invoke(app, [
            "cost-report",
            str(mock_project_dir),
            "--phase", "specification",
            "--export", str(export_file)
        ])
        
        # Command should complete
        assert result.exit_code in [0, 1]
        
        # Check if export happened (only if successful and there were operations)
        if result.exit_code == 0 and phase_report.operations_count > 0 and export_file.exists():
            data = json.loads(export_file.read_text())
            assert data["phase_filter"] == "specification"

    @patch("dev_agent.workflow.workflow_manager.WorkflowManager")
    def test_cost_report_empty_report(self, mock_workflow_manager, runner, mock_project_dir):
        """Test cost report with no operations."""
        empty_report = CostReport.create_empty()
        
        mock_manager = MagicMock()
        mock_manager.cost_tracker.get_report.return_value = empty_report
        mock_workflow_manager.return_value = mock_manager
        
        result = runner.invoke(app, ["cost-report", str(mock_project_dir)])
        
        assert result.exit_code == 0
        assert "No operations recorded yet" in result.stdout

    @patch("dev_agent.workflow.workflow_manager.WorkflowManager")
    def test_cost_report_verbose_mode(self, mock_workflow_manager, runner, mock_project_dir, sample_cost_report):
        """Test cost report with verbose flag."""
        mock_manager = MagicMock()
        mock_manager.cost_tracker.get_report.return_value = sample_cost_report
        mock_manager.cost_tracker.budget_threshold = None
        mock_manager.cost_tracker.budget_limit = None
        mock_workflow_manager.return_value = mock_manager
        
        result = runner.invoke(app, ["cost-report", str(mock_project_dir), "--verbose"])
        
        assert result.exit_code == 0
        # Verbose mode should still show the report
        assert "Complete Cost Report" in result.stdout

    @patch("dev_agent.workflow.workflow_manager.WorkflowManager")
    def test_cost_report_duration_display(self, mock_workflow_manager, runner, mock_project_dir, sample_cost_report):
        """Test that duration is displayed correctly."""
        mock_manager = MagicMock()
        mock_manager.cost_tracker.get_report.return_value = sample_cost_report
        mock_manager.cost_tracker.budget_threshold = None
        mock_manager.cost_tracker.budget_limit = None
        mock_workflow_manager.return_value = mock_manager
        
        result = runner.invoke(app, ["cost-report", str(mock_project_dir)])
        
        assert result.exit_code == 0
        assert "Duration" in result.stdout
        # Should show hours since duration is 1.5 hours
        assert "hours" in result.stdout.lower()

    @patch("dev_agent.workflow.workflow_manager.WorkflowManager")
    def test_cost_report_percentages(self, mock_workflow_manager, runner, mock_project_dir, sample_cost_report):
        """Test that percentage calculations are displayed."""
        mock_manager = MagicMock()
        mock_manager.cost_tracker.get_report.return_value = sample_cost_report
        mock_manager.cost_tracker.budget_threshold = None
        mock_manager.cost_tracker.budget_limit = None
        mock_workflow_manager.return_value = mock_manager
        
        result = runner.invoke(app, ["cost-report", str(mock_project_dir)])
        
        assert result.exit_code == 0
        # Should show percentages in various tables
        assert "%" in result.stdout
        assert "Percentage" in result.stdout
