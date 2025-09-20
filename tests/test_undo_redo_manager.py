"""Tests for the UndoRedoManager class."""

import json
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

import pytest

from dev_agent.models.enums import PhaseType, TaskStatus
from dev_agent.models.project_state import IndexMetadata, ProjectState, SessionData
from dev_agent.models.undo_redo import ActionType, SnapshotType
from dev_agent.state.undo_redo_manager import UndoRedoManager


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_project_state():
    """Create a sample project state for testing."""
    now = datetime.now()
    session_data = SessionData(
        session_id=str(uuid.uuid4()),
        started_at=now,
        last_activity=now,
        user_approvals={},
        pending_approvals=[],
    )
    
    return ProjectState(
        project_path="/test/project",
        current_phase=PhaseType.INDEXING,
        indexing_complete=False,
        specification=None,
        design=None,
        tasks=None,
        implementation_progress={},
        index_metadata=None,
        session_data=session_data,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def undo_redo_manager(temp_project_dir):
    """Create an UndoRedoManager instance."""
    return UndoRedoManager(temp_project_dir)


class TestUndoRedoManager:
    """Test cases for UndoRedoManager."""

    def test_initialization(self, undo_redo_manager, temp_project_dir):
        """Test UndoRedoManager initialization."""
        assert undo_redo_manager.project_path == Path(temp_project_dir)
        assert undo_redo_manager.dev_agent_dir.exists()
        assert undo_redo_manager.snapshots_dir.exists()
        assert undo_redo_manager.undo_redo_state is not None

    def test_create_snapshot(self, undo_redo_manager, sample_project_state):
        """Test creating a snapshot."""
        snapshot_id = undo_redo_manager.create_snapshot(
            sample_project_state,
            SnapshotType.MANUAL,
            "Test snapshot",
            {"test": "metadata"}
        )
        
        assert snapshot_id is not None
        assert len(undo_redo_manager.undo_redo_state.snapshots) == 1
        
        snapshot = undo_redo_manager.undo_redo_state.snapshots[0]
        assert snapshot.id == snapshot_id
        assert snapshot.description == "Test snapshot"
        assert snapshot.snapshot_type == SnapshotType.MANUAL
        assert snapshot.metadata["test"] == "metadata"

    def test_get_snapshot_by_id(self, undo_redo_manager, sample_project_state):
        """Test retrieving a snapshot by ID."""
        snapshot_id = undo_redo_manager.create_snapshot(
            sample_project_state,
            SnapshotType.AUTOMATIC,
            "Test snapshot"
        )
        
        retrieved_snapshot = undo_redo_manager.get_snapshot_by_id(snapshot_id)
        assert retrieved_snapshot is not None
        assert retrieved_snapshot.id == snapshot_id
        assert retrieved_snapshot.project_state is not None
        assert retrieved_snapshot.project_state.current_phase == PhaseType.INDEXING

    def test_restore_snapshot(self, undo_redo_manager, sample_project_state):
        """Test restoring from a snapshot."""
        # Create initial snapshot
        snapshot_id = undo_redo_manager.create_snapshot(
            sample_project_state,
            SnapshotType.MANUAL,
            "Initial state"
        )
        
        # Modify the project state
        sample_project_state.current_phase = PhaseType.SPECIFICATION
        sample_project_state.indexing_complete = True
        
        # Restore from snapshot
        restored_state = undo_redo_manager.restore_snapshot(snapshot_id)
        
        assert restored_state is not None
        assert restored_state.current_phase == PhaseType.INDEXING
        assert restored_state.indexing_complete is False

    def test_create_action(self, undo_redo_manager, sample_project_state):
        """Test creating an undo/redo action."""
        # Create before and after snapshots
        before_id = undo_redo_manager.create_snapshot(
            sample_project_state,
            SnapshotType.AUTOMATIC,
            "Before action"
        )
        
        sample_project_state.current_phase = PhaseType.SPECIFICATION
        after_id = undo_redo_manager.create_snapshot(
            sample_project_state,
            SnapshotType.AUTOMATIC,
            "After action"
        )
        
        # Create action
        action_id = undo_redo_manager.create_action(
            ActionType.PHASE_TRANSITION,
            "Transition to specification",
            before_id,
            after_id,
            {"test": "metadata"}
        )
        
        assert action_id is not None
        assert len(undo_redo_manager.undo_redo_state.actions) == 1
        
        action = undo_redo_manager.undo_redo_state.actions[0]
        assert action.id == action_id
        assert action.action_type == ActionType.PHASE_TRANSITION
        assert action.before_snapshot_id == before_id
        assert action.after_snapshot_id == after_id

    def test_add_command_history_entry(self, undo_redo_manager, sample_project_state):
        """Test adding command history entries."""
        snapshot_id = undo_redo_manager.create_snapshot(
            sample_project_state,
            SnapshotType.AUTOMATIC,
            "Command snapshot"
        )
        
        entry_id = undo_redo_manager.add_command_history_entry(
            "test_command",
            PhaseType.INDEXING,
            True,
            snapshot_id,
            metadata={"test": "data"}
        )
        
        assert entry_id is not None
        assert len(undo_redo_manager.undo_redo_state.command_history) == 1
        
        entry = undo_redo_manager.undo_redo_state.command_history[0]
        assert entry.id == entry_id
        assert entry.command == "test_command"
        assert entry.phase == PhaseType.INDEXING
        assert entry.success is True
        assert entry.snapshot_id == snapshot_id

    def test_get_available_snapshots(self, undo_redo_manager, sample_project_state):
        """Test getting available snapshots."""
        # Create multiple snapshots
        id1 = undo_redo_manager.create_snapshot(
            sample_project_state,
            SnapshotType.MANUAL,
            "First snapshot"
        )
        
        sample_project_state.current_phase = PhaseType.SPECIFICATION
        id2 = undo_redo_manager.create_snapshot(
            sample_project_state,
            SnapshotType.AUTOMATIC,
            "Second snapshot"
        )
        
        snapshots = undo_redo_manager.get_available_snapshots()
        assert len(snapshots) == 2
        
        # Should be sorted by timestamp (most recent first)
        assert snapshots[0].id == id2
        assert snapshots[1].id == id1

    def test_get_undo_actions(self, undo_redo_manager, sample_project_state):
        """Test getting available undo actions."""
        # Create snapshots and action
        before_id = undo_redo_manager.create_snapshot(
            sample_project_state,
            SnapshotType.AUTOMATIC,
            "Before"
        )
        
        sample_project_state.current_phase = PhaseType.SPECIFICATION
        after_id = undo_redo_manager.create_snapshot(
            sample_project_state,
            SnapshotType.AUTOMATIC,
            "After"
        )
        
        undo_redo_manager.create_action(
            ActionType.PHASE_TRANSITION,
            "Test transition",
            before_id,
            after_id
        )
        
        # Set current snapshot to after state
        undo_redo_manager.undo_redo_state.current_snapshot_id = after_id
        
        undo_actions = undo_redo_manager.get_undo_actions()
        assert len(undo_actions) == 1
        assert undo_actions[0].description == "Test transition"

    def test_get_redo_actions(self, undo_redo_manager, sample_project_state):
        """Test getting available redo actions."""
        # Create snapshots and action
        before_id = undo_redo_manager.create_snapshot(
            sample_project_state,
            SnapshotType.AUTOMATIC,
            "Before"
        )
        
        sample_project_state.current_phase = PhaseType.SPECIFICATION
        after_id = undo_redo_manager.create_snapshot(
            sample_project_state,
            SnapshotType.AUTOMATIC,
            "After"
        )
        
        undo_redo_manager.create_action(
            ActionType.PHASE_TRANSITION,
            "Test transition",
            before_id,
            after_id
        )
        
        # Set current snapshot to before state (as if we undid the action)
        undo_redo_manager.undo_redo_state.current_snapshot_id = before_id
        
        redo_actions = undo_redo_manager.get_redo_actions()
        assert len(redo_actions) == 1
        assert redo_actions[0].description == "Test transition"

    def test_undo_action(self, undo_redo_manager, sample_project_state):
        """Test undoing an action."""
        # Create initial state
        initial_phase = sample_project_state.current_phase
        before_id = undo_redo_manager.create_snapshot(
            sample_project_state,
            SnapshotType.AUTOMATIC,
            "Before"
        )
        
        # Change state
        sample_project_state.current_phase = PhaseType.SPECIFICATION
        after_id = undo_redo_manager.create_snapshot(
            sample_project_state,
            SnapshotType.AUTOMATIC,
            "After"
        )
        
        # Create action
        action_id = undo_redo_manager.create_action(
            ActionType.PHASE_TRANSITION,
            "Test transition",
            before_id,
            after_id
        )
        
        # Set current state to after
        undo_redo_manager.undo_redo_state.current_snapshot_id = after_id
        
        # Undo the action
        restored_state = undo_redo_manager.undo_action(action_id)
        
        assert restored_state is not None
        assert restored_state.current_phase == initial_phase
        assert undo_redo_manager.undo_redo_state.current_snapshot_id == before_id

    def test_redo_action(self, undo_redo_manager, sample_project_state):
        """Test redoing an action."""
        # Create states
        before_id = undo_redo_manager.create_snapshot(
            sample_project_state,
            SnapshotType.AUTOMATIC,
            "Before"
        )
        
        sample_project_state.current_phase = PhaseType.SPECIFICATION
        after_id = undo_redo_manager.create_snapshot(
            sample_project_state,
            SnapshotType.AUTOMATIC,
            "After"
        )
        
        # Create action
        action_id = undo_redo_manager.create_action(
            ActionType.PHASE_TRANSITION,
            "Test transition",
            before_id,
            after_id
        )
        
        # Set current state to before (as if undone)
        undo_redo_manager.undo_redo_state.current_snapshot_id = before_id
        
        # Redo the action
        restored_state = undo_redo_manager.redo_action(action_id)
        
        assert restored_state is not None
        assert restored_state.current_phase == PhaseType.SPECIFICATION
        assert undo_redo_manager.undo_redo_state.current_snapshot_id == after_id

    def test_get_command_history(self, undo_redo_manager, sample_project_state):
        """Test getting command history."""
        snapshot_id = undo_redo_manager.create_snapshot(
            sample_project_state,
            SnapshotType.AUTOMATIC,
            "Test snapshot"
        )
        
        # Add multiple history entries
        undo_redo_manager.add_command_history_entry(
            "command1",
            PhaseType.INDEXING,
            True,
            snapshot_id
        )
        
        undo_redo_manager.add_command_history_entry(
            "command2",
            PhaseType.SPECIFICATION,
            False,
            snapshot_id,
            error_message="Test error"
        )
        
        history = undo_redo_manager.get_command_history()
        assert len(history) == 2
        
        # Should be sorted by timestamp (most recent first)
        assert history[0].command == "command2"
        assert history[0].success is False
        assert history[0].error_message == "Test error"
        
        assert history[1].command == "command1"
        assert history[1].success is True

    def test_rollback_to_command(self, undo_redo_manager, sample_project_state):
        """Test rolling back to a specific command."""
        snapshot_id = undo_redo_manager.create_snapshot(
            sample_project_state,
            SnapshotType.AUTOMATIC,
            "Command snapshot"
        )
        
        entry_id = undo_redo_manager.add_command_history_entry(
            "test_command",
            PhaseType.INDEXING,
            True,
            snapshot_id
        )
        
        # Rollback to the command
        restored_state = undo_redo_manager.rollback_to_command(entry_id)
        
        assert restored_state is not None
        assert restored_state.current_phase == PhaseType.INDEXING
        assert undo_redo_manager.undo_redo_state.current_snapshot_id == snapshot_id

    def test_get_phase_transitions(self, undo_redo_manager, sample_project_state):
        """Test getting phase transition actions."""
        # Create snapshots
        before_id = undo_redo_manager.create_snapshot(
            sample_project_state,
            SnapshotType.AUTOMATIC,
            "Before"
        )
        
        sample_project_state.current_phase = PhaseType.SPECIFICATION
        after_id = undo_redo_manager.create_snapshot(
            sample_project_state,
            SnapshotType.AUTOMATIC,
            "After"
        )
        
        # Create phase transition action
        undo_redo_manager.create_action(
            ActionType.PHASE_TRANSITION,
            "Phase transition",
            before_id,
            after_id
        )
        
        # Create non-phase-transition action
        undo_redo_manager.create_action(
            ActionType.DOCUMENT_MODIFICATION,
            "Document change",
            before_id,
            after_id
        )
        
        transitions = undo_redo_manager.get_phase_transitions()
        assert len(transitions) == 1
        assert transitions[0].action_type == ActionType.PHASE_TRANSITION

    def test_cleanup_snapshots(self, undo_redo_manager, sample_project_state):
        """Test cleaning up old snapshots."""
        # Create multiple snapshots
        snapshot_ids = []
        for i in range(5):
            sample_project_state.current_phase = PhaseType.INDEXING
            snapshot_id = undo_redo_manager.create_snapshot(
                sample_project_state,
                SnapshotType.AUTOMATIC,
                f"Snapshot {i}"
            )
            snapshot_ids.append(snapshot_id)
        
        # Set max snapshots to 3
        undo_redo_manager.undo_redo_state.max_snapshots = 3
        
        # Cleanup
        removed_count = undo_redo_manager.cleanup_snapshots(3)
        
        assert removed_count == 2
        assert len(undo_redo_manager.undo_redo_state.snapshots) == 3
        
        # Check that the most recent snapshots are kept
        remaining_ids = {s.id for s in undo_redo_manager.undo_redo_state.snapshots}
        assert snapshot_ids[-3:] == [s for s in snapshot_ids if s in remaining_ids]

    def test_persistence(self, undo_redo_manager, sample_project_state, temp_project_dir):
        """Test that undo/redo state persists across manager instances."""
        # Create snapshot and action
        snapshot_id = undo_redo_manager.create_snapshot(
            sample_project_state,
            SnapshotType.MANUAL,
            "Persistent snapshot"
        )
        
        # Create new manager instance
        new_manager = UndoRedoManager(temp_project_dir)
        
        # Check that state was loaded
        assert len(new_manager.undo_redo_state.snapshots) == 1
        assert new_manager.undo_redo_state.snapshots[0].id == snapshot_id
        assert new_manager.undo_redo_state.snapshots[0].description == "Persistent snapshot"

    def test_snapshot_file_storage(self, undo_redo_manager, sample_project_state):
        """Test that snapshots are stored in separate files."""
        snapshot_id = undo_redo_manager.create_snapshot(
            sample_project_state,
            SnapshotType.MANUAL,
            "File storage test"
        )
        
        # Check that snapshot file exists
        snapshot_file = undo_redo_manager.snapshots_dir / f"{snapshot_id}.json"
        assert snapshot_file.exists()
        
        # Check that file contains the snapshot data
        with open(snapshot_file) as f:
            snapshot_data = json.load(f)
        
        assert snapshot_data["id"] == snapshot_id
        assert snapshot_data["description"] == "File storage test"
        assert snapshot_data["project_state"] is not None

    def test_error_handling_invalid_snapshot(self, undo_redo_manager):
        """Test error handling for invalid snapshot operations."""
        # Try to restore non-existent snapshot
        restored_state = undo_redo_manager.restore_snapshot("invalid-id")
        assert restored_state is None
        
        # Try to get non-existent snapshot
        snapshot = undo_redo_manager.get_snapshot_by_id("invalid-id")
        assert snapshot is None

    def test_error_handling_invalid_action(self, undo_redo_manager):
        """Test error handling for invalid action operations."""
        # Try to undo non-existent action
        restored_state = undo_redo_manager.undo_action("invalid-id")
        assert restored_state is None
        
        # Try to redo non-existent action
        restored_state = undo_redo_manager.redo_action("invalid-id")
        assert restored_state is None

    def test_error_handling_invalid_command(self, undo_redo_manager):
        """Test error handling for invalid command operations."""
        # Try to rollback to non-existent command
        restored_state = undo_redo_manager.rollback_to_command("invalid-id")
        assert restored_state is None