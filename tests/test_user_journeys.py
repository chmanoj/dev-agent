"""Comprehensive end-to-end tests for user journeys.

This module tests complete user workflows from start to finish, including:
- New project journey
- Existing codebase journey
- Phase transitions and state management
- Error recovery scenarios
"""

# ruff: noqa: S108, ARG002, PT019

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import SecretStr

from dev_agent.cli.main import app
from dev_agent.models.enums import PhaseStatus, PhaseType, TaskStatus
from dev_agent.models.llm_config import AzureOpenAIConfig
from dev_agent.models.project_state import IndexMetadata, ProjectState, SessionData
from dev_agent.onboarding.journey_manager import JourneyManager
from dev_agent.state.state_manager import StateManager
from dev_agent.workflow.workflow_manager import WorkflowManager


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def new_project_dir(tmp_path: Path) -> Path:
    """Create an empty directory for new project testing."""
    project_dir = tmp_path / "new_project"
    project_dir.mkdir()
    return project_dir


@pytest.fixture
def existing_project_dir(tmp_path: Path) -> Path:
    """Create a directory with existing Python code."""
    project_dir = tmp_path / "existing_project"
    project_dir.mkdir()
    
    # Create Python files
    (project_dir / "main.py").write_text("""
def main():
    '''Main entry point.'''
    print('Hello, world!')
    return 0

if __name__ == '__main__':
    main()
""")
    
    (project_dir / "utils.py").write_text("""
def helper_function(x: int, y: int) -> int:
    '''Add two numbers.'''
    return x + y

class Calculator:
    '''Simple calculator.'''
    
    def add(self, a: int, b: int) -> int:
        '''Add two numbers.'''
        return a + b
""")
    
    # Create test directory
    tests_dir = project_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_main.py").write_text("""
def test_main():
    '''Test main function.'''
    assert True
""")
    
    return project_dir


@pytest.fixture
def mock_cli_interface() -> MagicMock:
    """Create mock CLI interface."""
    cli = MagicMock()
    cli.display_message = MagicMock()
    cli.request_approval = MagicMock(return_value=True)
    cli.display_progress = MagicMock()
    return cli


@pytest.fixture
def mock_azure_config() -> AzureOpenAIConfig:
    """Create mock Azure OpenAI configuration."""
    return AzureOpenAIConfig(
        endpoint="https://test.openai.azure.com/",
        api_key=SecretStr("test-key"),
        api_version="2024-02-15-preview",
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
    )


@pytest.fixture
def mock_phase_manager():
    """Create mock phase manager."""
    with patch("dev_agent.workflow.workflow_manager.PhaseManager") as mock:
        phase_manager = MagicMock()
        
        # Mock successful phase executions
        from dev_agent.models.results import PhaseResult
        
        phase_manager.execute_indexing_phase = MagicMock(
            return_value=PhaseResult(
                phase=PhaseType.INDEXING,
                status=PhaseStatus.COMPLETED,
                message="Indexing completed successfully",
            )
        )
        
        phase_manager.execute_specification_phase = MagicMock(
            return_value=PhaseResult(
                phase=PhaseType.SPECIFICATION,
                status=PhaseStatus.COMPLETED,
                message="Specification generated successfully",
            )
        )
        
        phase_manager.execute_design_phase = MagicMock(
            return_value=PhaseResult(
                phase=PhaseType.DESIGN,
                status=PhaseStatus.COMPLETED,
                message="Design completed successfully",
            )
        )
        
        phase_manager.execute_implementation_phase = MagicMock(
            return_value=PhaseResult(
                phase=PhaseType.IMPLEMENTATION,
                status=PhaseStatus.COMPLETED,
                message="Implementation completed successfully",
            )
        )
        
        mock.return_value = phase_manager
        yield mock


# ============================================================================
# New Project Journey Tests
# ============================================================================


class TestNewProjectJourney:
    """Test complete journey for new project from start to finish."""
    
    def test_new_project_detection(self, new_project_dir: Path):
        """Test that new project is correctly detected."""
        journey_manager = JourneyManager()
        context = journey_manager.detect_project_type(new_project_dir)
        
        assert context.project_type == "new"
        assert not context.has_code
        assert context.file_count == 0
        assert context.estimated_size == "small"
        assert context.complexity == "simple"
    
    def test_new_project_onboarding_flow(self, new_project_dir: Path):
        """Test onboarding flow for new project."""
        journey_manager = JourneyManager()
        context = journey_manager.detect_project_type(new_project_dir)
        flow = journey_manager.get_onboarding_flow(context)
        
        assert len(flow.steps) > 0
        assert any("new project" in step.description.lower() for step in flow.steps)
        assert any("template" in step.title.lower() for step in flow.steps)
        assert len(flow.tips) > 0
    
    def test_new_project_initialization(
        self,
        new_project_dir: Path,
        mock_cli_interface: MagicMock,
    ):
        """Test initializing a new project."""
        workflow_manager = WorkflowManager(cli_interface=mock_cli_interface)
        
        project_state = workflow_manager.start_new_project(str(new_project_dir))
        
        assert project_state is not None
        assert project_state.project_path == str(new_project_dir)
        assert project_state.current_phase == PhaseType.INDEXING
        assert not project_state.indexing_complete
        assert project_state.specification is None
        assert project_state.design is None
        assert project_state.tasks is None
    
    def test_new_project_state_persistence(
        self,
        new_project_dir: Path,
        mock_cli_interface: MagicMock,
    ):
        """Test that new project state is persisted correctly."""
        workflow_manager = WorkflowManager(cli_interface=mock_cli_interface)
        project_state = workflow_manager.start_new_project(str(new_project_dir))
        
        # Verify state file was created
        state_file = new_project_dir / ".dev_agent" / "state.json"
        assert state_file.exists()
        
        # Load and verify state
        state_manager = StateManager(str(new_project_dir))
        loaded_state = state_manager.load_project_state()
        
        assert loaded_state is not None
        assert loaded_state.project_path == project_state.project_path
        assert loaded_state.current_phase == project_state.current_phase
    
    def test_new_project_phase_progression(
        self,
        new_project_dir: Path,
        mock_cli_interface: MagicMock,
        mock_phase_manager: MagicMock,
    ):
        """Test phase progression for new project."""
        workflow_manager = WorkflowManager(cli_interface=mock_cli_interface)
        workflow_manager.start_new_project(str(new_project_dir))
        
        # Progress through phases
        assert workflow_manager.transition_to_phase(PhaseType.INDEXING)
        assert workflow_manager.get_current_phase() == PhaseType.INDEXING
        
        assert workflow_manager.transition_to_phase(PhaseType.SPECIFICATION)
        assert workflow_manager.get_current_phase() == PhaseType.SPECIFICATION
        
        assert workflow_manager.transition_to_phase(PhaseType.DESIGN)
        assert workflow_manager.get_current_phase() == PhaseType.DESIGN
        
        assert workflow_manager.transition_to_phase(PhaseType.IMPLEMENTATION)
        assert workflow_manager.get_current_phase() == PhaseType.IMPLEMENTATION


# ============================================================================
# Existing Codebase Journey Tests
# ============================================================================


class TestExistingCodebaseJourney:
    """Test complete journey for existing codebase from start to finish."""
    
    def test_existing_codebase_detection(self, existing_project_dir: Path):
        """Test that existing codebase is correctly detected."""
        journey_manager = JourneyManager()
        context = journey_manager.detect_project_type(existing_project_dir)
        
        assert context.project_type == "existing"
        assert context.has_code
        assert context.file_count > 0
        assert "Python" in context.languages_detected
    
    def test_existing_codebase_onboarding_flow(self, existing_project_dir: Path):
        """Test onboarding flow for existing codebase."""
        journey_manager = JourneyManager()
        context = journey_manager.detect_project_type(existing_project_dir)
        flow = journey_manager.get_onboarding_flow(context)
        
        assert len(flow.steps) > 0
        assert any("index" in step.title.lower() for step in flow.steps)
        assert len(flow.tips) > 0
        assert len(flow.warnings) > 0
    
    def test_existing_codebase_initialization(
        self,
        existing_project_dir: Path,
        mock_cli_interface: MagicMock,
    ):
        """Test initializing an existing codebase."""
        workflow_manager = WorkflowManager(cli_interface=mock_cli_interface)
        
        project_state = workflow_manager.start_new_project(str(existing_project_dir))
        
        assert project_state is not None
        assert project_state.project_path == str(existing_project_dir)
        assert project_state.current_phase == PhaseType.INDEXING
    
    def test_existing_codebase_indexing_phase(
        self,
        existing_project_dir: Path,
        mock_cli_interface: MagicMock,
        mock_phase_manager: MagicMock,
    ):
        """Test indexing phase for existing codebase."""
        workflow_manager = WorkflowManager(cli_interface=mock_cli_interface)
        workflow_manager.start_new_project(str(existing_project_dir))
        
        # Execute indexing phase
        result = workflow_manager.transition_to_phase(PhaseType.INDEXING)
        
        assert result is True
        assert workflow_manager.get_current_phase() == PhaseType.INDEXING
    
    def test_existing_codebase_complete_workflow(
        self,
        existing_project_dir: Path,
        mock_cli_interface: MagicMock,
        mock_phase_manager: MagicMock,
    ):
        """Test complete workflow for existing codebase."""
        workflow_manager = WorkflowManager(cli_interface=mock_cli_interface)
        workflow_manager.start_new_project(str(existing_project_dir))
        
        # Execute complete workflow
        result = workflow_manager.execute_complete_workflow()
        
        assert result is True
        assert workflow_manager.get_current_phase() == PhaseType.IMPLEMENTATION


# ============================================================================
# Phase Transition Tests
# ============================================================================


class TestPhaseTransitions:
    """Test phase transitions and state management."""
    
    def test_valid_phase_transitions(
        self,
        new_project_dir: Path,
        mock_cli_interface: MagicMock,
        mock_phase_manager: MagicMock,
    ):
        """Test all valid phase transitions."""
        workflow_manager = WorkflowManager(cli_interface=mock_cli_interface)
        workflow_manager.start_new_project(str(new_project_dir))
        
        # Valid forward transitions
        assert workflow_manager.transition_to_phase(PhaseType.INDEXING)
        assert workflow_manager.transition_to_phase(PhaseType.SPECIFICATION)
        assert workflow_manager.transition_to_phase(PhaseType.DESIGN)
        assert workflow_manager.transition_to_phase(PhaseType.IMPLEMENTATION)
        
        # Valid backward transitions
        assert workflow_manager.transition_to_phase(PhaseType.DESIGN)
        assert workflow_manager.transition_to_phase(PhaseType.SPECIFICATION)
    
    def test_invalid_phase_transitions(
        self,
        new_project_dir: Path,
        mock_cli_interface: MagicMock,
    ):
        """Test that invalid phase transitions are rejected."""
        workflow_manager = WorkflowManager(cli_interface=mock_cli_interface)
        workflow_manager.start_new_project(str(new_project_dir))
        
        # Try to skip from INDEXING to DESIGN (should fail)
        result = workflow_manager.transition_to_phase(PhaseType.DESIGN)
        assert result is False
        assert workflow_manager.get_current_phase() == PhaseType.INDEXING
    
    def test_phase_state_persistence(
        self,
        new_project_dir: Path,
        mock_cli_interface: MagicMock,
        mock_phase_manager: MagicMock,
    ):
        """Test that phase transitions are persisted."""
        workflow_manager = WorkflowManager(cli_interface=mock_cli_interface)
        workflow_manager.start_new_project(str(new_project_dir))
        
        # Transition to specification phase
        workflow_manager.transition_to_phase(PhaseType.INDEXING)
        workflow_manager.transition_to_phase(PhaseType.SPECIFICATION)
        
        # Load state and verify
        state_manager = StateManager(str(new_project_dir))
        loaded_state = state_manager.load_project_state()
        
        assert loaded_state is not None
        assert loaded_state.current_phase == PhaseType.SPECIFICATION
    
    def test_resume_project_maintains_phase(
        self,
        new_project_dir: Path,
        mock_cli_interface: MagicMock,
        mock_phase_manager: MagicMock,
    ):
        """Test that resuming a project maintains the current phase."""
        # Start and progress project
        workflow_manager1 = WorkflowManager(cli_interface=mock_cli_interface)
        workflow_manager1.start_new_project(str(new_project_dir))
        workflow_manager1.transition_to_phase(PhaseType.INDEXING)
        workflow_manager1.transition_to_phase(PhaseType.SPECIFICATION)
        
        # Resume project in new workflow manager
        workflow_manager2 = WorkflowManager(cli_interface=mock_cli_interface)
        project_state = workflow_manager2.resume_project(str(new_project_dir))
        
        assert project_state.current_phase == PhaseType.SPECIFICATION
        assert workflow_manager2.get_current_phase() == PhaseType.SPECIFICATION


# ============================================================================
# State Management Tests
# ============================================================================


class TestStateManagement:
    """Test state management across sessions."""
    
    def test_state_creation_and_loading(self, new_project_dir: Path):
        """Test creating and loading project state."""
        state_manager = StateManager(str(new_project_dir))
        
        # Create initial state
        from datetime import datetime
        initial_state = state_manager.create_initial_state(
            str(new_project_dir),
            "test-session-id"
        )
        
        # Save state
        assert state_manager.save_project_state(initial_state)
        
        # Load state
        loaded_state = state_manager.load_project_state()
        
        assert loaded_state is not None
        assert loaded_state.project_path == initial_state.project_path
        assert loaded_state.current_phase == initial_state.current_phase
        assert loaded_state.session_data.session_id == "test-session-id"
    
    def test_state_updates_persist(self, new_project_dir: Path):
        """Test that state updates are persisted."""
        state_manager = StateManager(str(new_project_dir))
        
        # Create and save initial state
        initial_state = state_manager.create_initial_state(
            str(new_project_dir),
            "test-session"
        )
        state_manager.save_project_state(initial_state)
        
        # Update phase
        state_manager.update_phase_status(PhaseType.SPECIFICATION, "in_progress")
        
        # Load and verify
        loaded_state = state_manager.load_project_state()
        assert loaded_state.current_phase == PhaseType.SPECIFICATION
    
    def test_task_progress_tracking(self, new_project_dir: Path):
        """Test tracking task progress."""
        state_manager = StateManager(str(new_project_dir))
        
        # Create initial state
        initial_state = state_manager.create_initial_state(
            str(new_project_dir),
            "test-session"
        )
        state_manager.save_project_state(initial_state)
        
        # Track task progress
        state_manager.track_task_progress("task-1", TaskStatus.IN_PROGRESS)
        state_manager.track_task_progress("task-2", TaskStatus.COMPLETED)
        
        # Load and verify
        loaded_state = state_manager.load_project_state()
        assert loaded_state.implementation_progress["task-1"] == TaskStatus.IN_PROGRESS
        assert loaded_state.implementation_progress["task-2"] == TaskStatus.COMPLETED
    
    def test_session_data_tracking(self, new_project_dir: Path):
        """Test session data tracking."""
        state_manager = StateManager(str(new_project_dir))
        
        # Create initial state
        initial_state = state_manager.create_initial_state(
            str(new_project_dir),
            "test-session"
        )
        
        # Add user approvals
        initial_state.session_data.user_approvals["specification"] = True
        initial_state.session_data.user_approvals["design"] = False
        
        state_manager.save_project_state(initial_state)
        
        # Load and verify
        loaded_state = state_manager.load_project_state()
        assert loaded_state.session_data.user_approvals["specification"] is True
        assert loaded_state.session_data.user_approvals["design"] is False


# ============================================================================
# Error Recovery Tests
# ============================================================================


class TestErrorRecovery:
    """Test error recovery scenarios."""
    
    def test_recovery_from_failed_phase(
        self,
        new_project_dir: Path,
        mock_cli_interface: MagicMock,
    ):
        """Test recovery from a failed phase execution."""
        with patch("dev_agent.workflow.workflow_manager.PhaseManager") as mock_pm:
            phase_manager = MagicMock()
            
            # Mock failed indexing phase
            from dev_agent.models.results import PhaseResult
            phase_manager.execute_indexing_phase = MagicMock(
                return_value=PhaseResult(
                    phase=PhaseType.INDEXING,
                    status=PhaseStatus.FAILED,
                    message="Indexing failed",
                )
            )
            
            mock_pm.return_value = phase_manager
            
            workflow_manager = WorkflowManager(cli_interface=mock_cli_interface)
            workflow_manager.start_new_project(str(new_project_dir))
            
            # Try to execute indexing (should fail)
            result = workflow_manager.transition_to_phase(PhaseType.INDEXING)
            
            assert result is False
            assert workflow_manager.get_current_phase() == PhaseType.INDEXING
            
            # State should still be valid
            state_manager = StateManager(str(new_project_dir))
            loaded_state = state_manager.load_project_state()
            assert loaded_state is not None
    
    def test_recovery_from_corrupted_state(self, new_project_dir: Path):
        """Test recovery from corrupted state file."""
        state_manager = StateManager(str(new_project_dir))
        
        # Create initial state
        initial_state = state_manager.create_initial_state(
            str(new_project_dir),
            "test-session"
        )
        state_manager.save_project_state(initial_state)
        
        # Corrupt the state file
        state_file = new_project_dir / ".dev_agent" / "state.json"
        state_file.write_text("{ invalid json }")
        
        # Try to load (should return None)
        loaded_state = state_manager.load_project_state()
        assert loaded_state is None
    
    def test_resume_after_interruption(
        self,
        new_project_dir: Path,
        mock_cli_interface: MagicMock,
        mock_phase_manager: MagicMock,
    ):
        """Test resuming project after interruption."""
        # Start project and progress
        workflow_manager1 = WorkflowManager(cli_interface=mock_cli_interface)
        workflow_manager1.start_new_project(str(new_project_dir))
        workflow_manager1.transition_to_phase(PhaseType.INDEXING)
        
        # Simulate interruption by creating new workflow manager
        workflow_manager2 = WorkflowManager(cli_interface=mock_cli_interface)
        project_state = workflow_manager2.resume_project(str(new_project_dir))
        
        # Should be able to continue from where we left off
        assert project_state is not None
        assert project_state.current_phase == PhaseType.INDEXING
        
        # Continue workflow
        result = workflow_manager2.transition_to_phase(PhaseType.SPECIFICATION)
        assert result is True
    
    def test_missing_state_directory(
        self,
        new_project_dir: Path,
        mock_cli_interface: MagicMock,
    ):
        """Test handling of missing .dev_agent directory."""
        workflow_manager = WorkflowManager(cli_interface=mock_cli_interface)
        
        # Try to resume non-existent project
        with pytest.raises(Exception) as exc_info:
            workflow_manager.resume_project(str(new_project_dir))
        
        assert "No existing project state found" in str(exc_info.value)
    
    def test_phase_transition_rollback_on_error(
        self,
        new_project_dir: Path,
        mock_cli_interface: MagicMock,
    ):
        """Test that phase transitions rollback on error."""
        with patch("dev_agent.workflow.workflow_manager.PhaseManager") as mock_pm:
            phase_manager = MagicMock()
            
            # Mock successful indexing
            from dev_agent.models.results import PhaseResult
            phase_manager.execute_indexing_phase = MagicMock(
                return_value=PhaseResult(
                    phase=PhaseType.INDEXING,
                    status=PhaseStatus.COMPLETED,
                    message="Success",
                )
            )
            
            # Mock failed specification
            phase_manager.execute_specification_phase = MagicMock(
                return_value=PhaseResult(
                    phase=PhaseType.SPECIFICATION,
                    status=PhaseStatus.FAILED,
                    message="Failed",
                )
            )
            
            mock_pm.return_value = phase_manager
            
            workflow_manager = WorkflowManager(cli_interface=mock_cli_interface)
            workflow_manager.start_new_project(str(new_project_dir))
            
            # Execute indexing (should succeed)
            workflow_manager.transition_to_phase(PhaseType.INDEXING)
            assert workflow_manager.get_current_phase() == PhaseType.INDEXING
            
            # Try specification (should fail and stay in INDEXING)
            result = workflow_manager.transition_to_phase(PhaseType.SPECIFICATION)
            assert result is False
            assert workflow_manager.get_current_phase() == PhaseType.INDEXING


# ============================================================================
# Integration Tests
# ============================================================================


class TestEndToEndIntegration:
    """End-to-end integration tests."""
    
    def test_complete_new_project_workflow(
        self,
        new_project_dir: Path,
        mock_cli_interface: MagicMock,
        mock_phase_manager: MagicMock,
    ):
        """Test complete workflow from new project to implementation."""
        workflow_manager = WorkflowManager(cli_interface=mock_cli_interface)
        
        # Start new project
        project_state = workflow_manager.start_new_project(str(new_project_dir))
        assert project_state is not None
        
        # Execute complete workflow
        result = workflow_manager.execute_complete_workflow()
        assert result is True
        
        # Verify final state
        final_state = workflow_manager.current_project_state
        assert final_state.current_phase == PhaseType.IMPLEMENTATION
        
        # Verify state persistence
        state_manager = StateManager(str(new_project_dir))
        loaded_state = state_manager.load_project_state()
        assert loaded_state.current_phase == PhaseType.IMPLEMENTATION
    
    def test_complete_existing_codebase_workflow(
        self,
        existing_project_dir: Path,
        mock_cli_interface: MagicMock,
        mock_phase_manager: MagicMock,
    ):
        """Test complete workflow for existing codebase."""
        workflow_manager = WorkflowManager(cli_interface=mock_cli_interface)
        
        # Start with existing codebase
        project_state = workflow_manager.start_new_project(str(existing_project_dir))
        assert project_state is not None
        
        # Execute complete workflow
        result = workflow_manager.execute_complete_workflow()
        assert result is True
        
        # Verify final state
        assert workflow_manager.get_current_phase() == PhaseType.IMPLEMENTATION
    
    def test_workflow_with_user_approvals(
        self,
        new_project_dir: Path,
        mock_cli_interface: MagicMock,
        mock_phase_manager: MagicMock,
    ):
        """Test workflow with user approval gates."""
        # Mock user approvals
        mock_cli_interface.request_approval = MagicMock(return_value=True)
        
        workflow_manager = WorkflowManager(cli_interface=mock_cli_interface)
        workflow_manager.start_new_project(str(new_project_dir))
        
        # Execute phases with approvals
        workflow_manager.transition_to_phase(PhaseType.INDEXING)
        workflow_manager.require_user_approval("Test content", PhaseType.INDEXING)
        
        workflow_manager.transition_to_phase(PhaseType.SPECIFICATION)
        workflow_manager.require_user_approval("Test spec", PhaseType.SPECIFICATION)
        
        # Verify approvals were tracked
        state = workflow_manager.current_project_state
        assert state.session_data.user_approvals.get("indexing") is True
        assert state.session_data.user_approvals.get("specification") is True
    
    def test_workflow_with_cost_tracking(
        self,
        new_project_dir: Path,
        mock_cli_interface: MagicMock,
        mock_phase_manager: MagicMock,
    ):
        """Test workflow with cost tracking."""
        workflow_manager = WorkflowManager(
            cli_interface=mock_cli_interface,
            budget_threshold=5.0,
            budget_limit=10.0,
        )
        workflow_manager.start_new_project(str(new_project_dir))
        
        # Execute workflow
        workflow_manager.execute_complete_workflow()
        
        # Verify cost tracking
        cost_report = workflow_manager.generate_cost_report()
        assert "total_cost" in cost_report
        assert "by_phase" in cost_report
        assert "total_tokens" in cost_report
