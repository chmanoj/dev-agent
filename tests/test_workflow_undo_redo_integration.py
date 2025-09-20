"""Integration tests for workflow manager with undo/redo functionality."""

import tempfile
from unittest.mock import MagicMock, patch

import pytest

from dev_agent.interfaces.cli_interface import ICLIInterface
from dev_agent.models.enums import PhaseStatus, PhaseType
from dev_agent.models.results import PhaseResult
from dev_agent.models.undo_redo import ActionType, SnapshotType
from dev_agent.workflow.workflow_manager import WorkflowManager


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def mock_cli_interface():
    """Create a mock CLI interface."""
    mock_cli = MagicMock(spec=ICLIInterface)
    mock_cli.display_message = MagicMock()
    mock_cli.request_approval = MagicMock(return_value=True)
    return mock_cli


@pytest.fixture
def workflow_manager(mock_cli_interface):
    """Create a WorkflowManager instance."""
    return WorkflowManager(mock_cli_interface)


class TestWorkflowUndoRedoIntegration:
    """Integration tests for workflow manager with undo/redo functionality."""

    def test_start_new_project_creates_initial_snapshot(self, workflow_manager, temp_project_dir):
        """Test that starting a new project creates an initial snapshot."""
        project_state = workflow_manager.start_new_project(temp_project_dir)
        
        assert project_state is not None
        assert workflow_manager.undo_redo_manager is not None
        
        # Check that initial snapshot was created
        snapshots = workflow_manager.undo_redo_manager.get_available_snapshots()
        assert len(snapshots) == 1
        assert snapshots[0].description == "Initial project state"
        assert snapshots[0].snapshot_type == SnapshotType.AUTOMATIC

    def test_resume_project_creates_resume_snapshot(self, workflow_manager, temp_project_dir):
        """Test that resuming a project creates a resume snapshot."""
        # First start a project
        workflow_manager.start_new_project(temp_project_dir)
        
        # Create a new workflow manager to simulate resuming
        new_workflow_manager = WorkflowManager(workflow_manager.cli_interface)
        project_state = new_workflow_manager.resume_project(temp_project_dir)
        
        assert project_state is not None
        assert new_workflow_manager.undo_redo_manager is not None
        
        # Check that resume snapshot was created
        snapshots = new_workflow_manager.undo_redo_manager.get_available_snapshots()
        assert len(snapshots) == 2  # Initial + resume
        
        # Find the resume snapshot
        resume_snapshots = [s for s in snapshots if "resumed" in s.description]
        assert len(resume_snapshots) == 1
        assert resume_snapshots[0].snapshot_type == SnapshotType.AUTOMATIC

    def test_create_manual_snapshot(self, workflow_manager, temp_project_dir):
        """Test creating a manual snapshot."""
        workflow_manager.start_new_project(temp_project_dir)
        
        snapshot_id = workflow_manager.create_manual_snapshot("Test manual snapshot")
        
        assert snapshot_id is not None
        
        # Check that manual snapshot was created
        snapshots = workflow_manager.undo_redo_manager.get_available_snapshots()
        manual_snapshots = [s for s in snapshots if s.snapshot_type == SnapshotType.MANUAL]
        assert len(manual_snapshots) == 1
        assert manual_snapshots[0].description == "Test manual snapshot"

    def test_restore_from_snapshot(self, workflow_manager, temp_project_dir):
        """Test restoring from a snapshot."""
        # Start project and create manual snapshot
        project_state = workflow_manager.start_new_project(temp_project_dir)
        initial_phase = project_state.current_phase
        
        snapshot_id = workflow_manager.create_manual_snapshot("Before change")
        
        # Modify the state
        project_state.current_phase = PhaseType.SPECIFICATION
        workflow_manager.state_manager.save_project_state(project_state)
        
        # Restore from snapshot
        success = workflow_manager.restore_from_snapshot(snapshot_id)
        
        assert success is True
        assert workflow_manager.current_project_state.current_phase == initial_phase

    def test_restore_from_invalid_snapshot(self, workflow_manager, temp_project_dir):
        """Test restoring from an invalid snapshot."""
        workflow_manager.start_new_project(temp_project_dir)
        
        success = workflow_manager.restore_from_snapshot("invalid-snapshot-id")
        
        assert success is False

    def test_undo_last_action_no_actions(self, workflow_manager, temp_project_dir):
        """Test undoing when no actions are available."""
        workflow_manager.start_new_project(temp_project_dir)
        
        success = workflow_manager.undo_last_action()
        
        assert success is False

    def test_redo_last_action_no_actions(self, workflow_manager, temp_project_dir):
        """Test redoing when no actions are available."""
        workflow_manager.start_new_project(temp_project_dir)
        
        success = workflow_manager.redo_last_action()
        
        assert success is False

    def test_get_undo_redo_manager(self, workflow_manager, temp_project_dir):
        """Test getting the undo/redo manager."""
        # Before initialization
        assert workflow_manager.get_undo_redo_manager() is None
        
        # After initialization
        workflow_manager.start_new_project(temp_project_dir)
        undo_redo_manager = workflow_manager.get_undo_redo_manager()
        
        assert undo_redo_manager is not None
        assert undo_redo_manager == workflow_manager.undo_redo_manager

    def test_user_approval_creates_approval_snapshot(self, workflow_manager, temp_project_dir):
        """Test that user approval creates an approval point snapshot."""
        workflow_manager.start_new_project(temp_project_dir)
        
        # Mock approval
        approved = workflow_manager.require_user_approval("Test content", PhaseType.INDEXING)
        
        assert approved is True
        
        # Check that approval snapshot was created
        snapshots = workflow_manager.undo_redo_manager.get_available_snapshots()
        approval_snapshots = [s for s in snapshots if s.snapshot_type == SnapshotType.APPROVAL_POINT]
        assert len(approval_snapshots) == 1
        assert "approved" in approval_snapshots[0].description.lower()

    def test_user_rejection_creates_approval_snapshot(self, workflow_manager, temp_project_dir):
        """Test that user rejection also creates an approval point snapshot."""
        workflow_manager.start_new_project(temp_project_dir)
        
        # Mock rejection
        workflow_manager.cli_interface.request_approval.return_value = False
        approved = workflow_manager.require_user_approval("Test content", PhaseType.INDEXING)
        
        assert approved is False
        
        # Check that approval snapshot was created
        snapshots = workflow_manager.undo_redo_manager.get_available_snapshots()
        approval_snapshots = [s for s in snapshots if s.snapshot_type == SnapshotType.APPROVAL_POINT]
        assert len(approval_snapshots) == 1
        assert "rejected" in approval_snapshots[0].description.lower()

    def test_phase_transition_creates_snapshots_and_actions(self, workflow_manager, temp_project_dir):
        """Test that phase transitions create before/after snapshots and actions."""
        workflow_manager.start_new_project(temp_project_dir)
        
        # Mock successful phase execution
        with patch.object(workflow_manager, '_execute_phase') as mock_execute:
            mock_execute.return_value = PhaseResult(
                phase=PhaseType.SPECIFICATION,
                status=PhaseStatus.COMPLETED,
                message="Success"
            )
            
            success = workflow_manager.transition_to_phase(PhaseType.SPECIFICATION)
            
            assert success is True
            
            # Check snapshots were created
            snapshots = workflow_manager.undo_redo_manager.get_available_snapshots()
            before_snapshots = [s for s in snapshots if "Before transition" in s.description]
            after_snapshots = [s for s in snapshots if "After transition" in s.description]
            
            assert len(before_snapshots) == 1
            assert len(after_snapshots) == 1
            
            # Check action was created
            actions = workflow_manager.undo_redo_manager.undo_redo_state.actions
            phase_actions = [a for a in actions if a.action_type == ActionType.PHASE_TRANSITION]
            assert len(phase_actions) == 1
            
            # Check command history entry was created
            history = workflow_manager.undo_redo_manager.get_command_history()
            transition_commands = [h for h in history if "transition_to_phase" in h.command]
            assert len(transition_commands) == 1
            assert transition_commands[0].success is True

    def test_failed_phase_transition_creates_history_entry(self, workflow_manager, temp_project_dir):
        """Test that failed phase transitions create command history entries."""
        workflow_manager.start_new_project(temp_project_dir)
        
        # Mock failed phase execution
        with patch.object(workflow_manager, '_execute_phase') as mock_execute:
            mock_execute.return_value = PhaseResult(
                phase=PhaseType.SPECIFICATION,
                status=PhaseStatus.FAILED,
                message="Execution failed"
            )
            
            success = workflow_manager.transition_to_phase(PhaseType.SPECIFICATION)
            
            assert success is False
            
            # Check command history entry was created for failure
            history = workflow_manager.undo_redo_manager.get_command_history()
            transition_commands = [h for h in history if "transition_to_phase" in h.command]
            assert len(transition_commands) == 1
            assert transition_commands[0].success is False
            assert transition_commands[0].error_message == "Execution failed"

    def test_undo_redo_workflow_consistency(self, workflow_manager, temp_project_dir):
        """Test that undo/redo operations maintain workflow consistency."""
        # Start project
        initial_state = workflow_manager.start_new_project(temp_project_dir)
        initial_phase = initial_state.current_phase
        
        # Create a manual snapshot to have something to undo to
        snapshot_id = workflow_manager.create_manual_snapshot("Before changes")
        
        # Simulate some state changes by creating actions manually
        before_id = workflow_manager.undo_redo_manager.create_snapshot(
            workflow_manager.current_project_state,
            SnapshotType.AUTOMATIC,
            "Before test change"
        )
        
        # Change the phase
        workflow_manager.current_project_state.current_phase = PhaseType.SPECIFICATION
        workflow_manager.state_manager.save_project_state(workflow_manager.current_project_state)
        
        after_id = workflow_manager.undo_redo_manager.create_snapshot(
            workflow_manager.current_project_state,
            SnapshotType.AUTOMATIC,
            "After test change"
        )
        
        # Create an action
        action_id = workflow_manager.undo_redo_manager.create_action(
            ActionType.PHASE_TRANSITION,
            "Test phase change",
            before_id,
            after_id
        )
        
        # Set current snapshot
        workflow_manager.undo_redo_manager.undo_redo_state.current_snapshot_id = after_id
        
        # Verify we're in the changed state
        assert workflow_manager.current_project_state.current_phase == PhaseType.SPECIFICATION
        
        # Undo the action
        restored_state = workflow_manager.undo_redo_manager.undo_action(action_id)
        assert restored_state is not None
        
        # Update workflow manager state
        workflow_manager.current_project_state = restored_state
        workflow_manager.state_manager.save_project_state(restored_state)
        
        # Verify we're back to the original state
        assert workflow_manager.current_project_state.current_phase == initial_phase
        
        # Redo the action
        restored_state = workflow_manager.undo_redo_manager.redo_action(action_id)
        assert restored_state is not None
        
        # Update workflow manager state
        workflow_manager.current_project_state = restored_state
        workflow_manager.state_manager.save_project_state(restored_state)
        
        # Verify we're back to the changed state
        assert workflow_manager.current_project_state.current_phase == PhaseType.SPECIFICATION

    def test_snapshot_cleanup_integration(self, workflow_manager, temp_project_dir):
        """Test that snapshot cleanup works with workflow operations."""
        workflow_manager.start_new_project(temp_project_dir)
        
        # Create many manual snapshots
        for i in range(10):
            workflow_manager.create_manual_snapshot(f"Snapshot {i}")
        
        # Set a low max snapshots limit
        workflow_manager.undo_redo_manager.undo_redo_state.max_snapshots = 5
        
        # Trigger cleanup
        removed_count = workflow_manager.undo_redo_manager.cleanup_snapshots()
        
        assert removed_count > 0
        
        # Verify only the most recent snapshots remain
        snapshots = workflow_manager.undo_redo_manager.get_available_snapshots()
        assert len(snapshots) == 5

    def test_error_handling_without_managers(self, workflow_manager):
        """Test error handling when managers are not initialized."""
        # Try operations without initializing managers
        assert workflow_manager.create_manual_snapshot("Test") is None
        assert workflow_manager.restore_from_snapshot("test-id") is False
        assert workflow_manager.undo_last_action() is False
        assert workflow_manager.redo_last_action() is False