"""Tests for the UndoRedoCLI class."""

import tempfile
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from dev_agent.cli.undo_redo_cli import UndoRedoCLI
from dev_agent.models.enums import PhaseType, TaskStatus
from dev_agent.models.project_state import ProjectState, SessionData
from dev_agent.models.undo_redo import ActionType, SnapshotType, StateSnapshot, UndoRedoAction
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
def mock_undo_redo_manager():
    """Create a mock UndoRedoManager."""
    return MagicMock(spec=UndoRedoManager)


@pytest.fixture
def undo_redo_cli(mock_undo_redo_manager):
    """Create an UndoRedoCLI instance with mock manager."""
    return UndoRedoCLI(mock_undo_redo_manager)


class TestUndoRedoCLI:
    """Test cases for UndoRedoCLI."""

    def test_initialization(self, undo_redo_cli, mock_undo_redo_manager):
        """Test UndoRedoCLI initialization."""
        assert undo_redo_cli.undo_redo_manager == mock_undo_redo_manager
        assert undo_redo_cli.console is not None

    @patch('dev_agent.cli.undo_redo_cli.IntPrompt.ask')
    @patch('dev_agent.cli.undo_redo_cli.Confirm.ask')
    def test_show_snapshots_browser_with_selection(self, mock_confirm, mock_int_prompt, undo_redo_cli, mock_undo_redo_manager):
        """Test showing snapshots browser with user selection."""
        # Setup mock snapshots
        now = datetime.now()
        snapshots = [
            StateSnapshot(
                id="snapshot1",
                timestamp=now,
                snapshot_type=SnapshotType.MANUAL,
                description="Test snapshot 1",
                project_state=None,
                metadata={"phase": PhaseType.INDEXING}
            ),
            StateSnapshot(
                id="snapshot2",
                timestamp=now,
                snapshot_type=SnapshotType.AUTOMATIC,
                description="Test snapshot 2",
                project_state=None,
                metadata={"phase": PhaseType.SPECIFICATION}
            )
        ]
        
        mock_undo_redo_manager.get_available_snapshots.return_value = snapshots
        mock_int_prompt.return_value = 1  # Select first snapshot
        mock_confirm.return_value = True  # Confirm restoration
        
        result = undo_redo_cli.show_snapshots_browser()
        
        assert result == "snapshot1"
        mock_undo_redo_manager.get_available_snapshots.assert_called_once()

    @patch('dev_agent.cli.undo_redo_cli.IntPrompt.ask')
    def test_show_snapshots_browser_cancel(self, mock_int_prompt, undo_redo_cli, mock_undo_redo_manager):
        """Test cancelling snapshots browser."""
        snapshots = [
            StateSnapshot(
                id="snapshot1",
                timestamp=datetime.now(),
                snapshot_type=SnapshotType.MANUAL,
                description="Test snapshot",
                project_state=None,
                metadata={}
            )
        ]
        
        mock_undo_redo_manager.get_available_snapshots.return_value = snapshots
        mock_int_prompt.return_value = 0  # Cancel
        
        result = undo_redo_cli.show_snapshots_browser()
        
        assert result is None

    def test_show_snapshots_browser_no_snapshots(self, undo_redo_cli, mock_undo_redo_manager):
        """Test showing snapshots browser with no snapshots."""
        mock_undo_redo_manager.get_available_snapshots.return_value = []
        
        result = undo_redo_cli.show_snapshots_browser()
        
        assert result is None

    @patch('dev_agent.cli.undo_redo_cli.IntPrompt.ask')
    @patch('dev_agent.cli.undo_redo_cli.Confirm.ask')
    def test_show_undo_actions_with_selection(self, mock_confirm, mock_int_prompt, undo_redo_cli, mock_undo_redo_manager):
        """Test showing undo actions with user selection."""
        actions = [
            UndoRedoAction(
                id="action1",
                timestamp=datetime.now(),
                action_type=ActionType.PHASE_TRANSITION,
                description="Test transition",
                before_snapshot_id="before1",
                after_snapshot_id="after1",
                metadata={}
            )
        ]
        
        mock_undo_redo_manager.get_undo_actions.return_value = actions
        mock_int_prompt.return_value = 1  # Select first action
        mock_confirm.return_value = True  # Confirm undo
        
        result = undo_redo_cli.show_undo_actions()
        
        assert result == "action1"
        mock_undo_redo_manager.get_undo_actions.assert_called_once()

    def test_show_undo_actions_no_actions(self, undo_redo_cli, mock_undo_redo_manager):
        """Test showing undo actions with no actions available."""
        mock_undo_redo_manager.get_undo_actions.return_value = []
        
        result = undo_redo_cli.show_undo_actions()
        
        assert result is None

    @patch('dev_agent.cli.undo_redo_cli.IntPrompt.ask')
    @patch('dev_agent.cli.undo_redo_cli.Confirm.ask')
    def test_show_redo_actions_with_selection(self, mock_confirm, mock_int_prompt, undo_redo_cli, mock_undo_redo_manager):
        """Test showing redo actions with user selection."""
        actions = [
            UndoRedoAction(
                id="action1",
                timestamp=datetime.now(),
                action_type=ActionType.DOCUMENT_MODIFICATION,
                description="Test modification",
                before_snapshot_id="before1",
                after_snapshot_id="after1",
                metadata={}
            )
        ]
        
        mock_undo_redo_manager.get_redo_actions.return_value = actions
        mock_int_prompt.return_value = 1  # Select first action
        mock_confirm.return_value = True  # Confirm redo
        
        result = undo_redo_cli.show_redo_actions()
        
        assert result == "action1"
        mock_undo_redo_manager.get_redo_actions.assert_called_once()

    def test_show_redo_actions_no_actions(self, undo_redo_cli, mock_undo_redo_manager):
        """Test showing redo actions with no actions available."""
        mock_undo_redo_manager.get_redo_actions.return_value = []
        
        result = undo_redo_cli.show_redo_actions()
        
        assert result is None

    @patch('dev_agent.cli.undo_redo_cli.IntPrompt.ask')
    @patch('dev_agent.cli.undo_redo_cli.Confirm.ask')
    def test_show_command_history_with_selection(self, mock_confirm, mock_int_prompt, undo_redo_cli, mock_undo_redo_manager):
        """Test showing command history with user selection."""
        from dev_agent.models.undo_redo import CommandHistoryEntry
        
        history = [
            CommandHistoryEntry(
                id="entry1",
                timestamp=datetime.now(),
                command="test_command",
                phase=PhaseType.INDEXING,
                success=True,
                snapshot_id="snapshot1",
                metadata={}
            )
        ]
        
        mock_undo_redo_manager.get_command_history.return_value = history
        mock_int_prompt.return_value = 1  # Select first entry
        mock_confirm.return_value = True  # Confirm rollback
        
        result = undo_redo_cli.show_command_history()
        
        assert result == "entry1"
        mock_undo_redo_manager.get_command_history.assert_called_once()

    def test_show_command_history_no_history(self, undo_redo_cli, mock_undo_redo_manager):
        """Test showing command history with no history available."""
        mock_undo_redo_manager.get_command_history.return_value = []
        
        result = undo_redo_cli.show_command_history()
        
        assert result is None

    def test_show_phase_transitions(self, undo_redo_cli, mock_undo_redo_manager):
        """Test showing phase transitions."""
        transitions = [
            UndoRedoAction(
                id="transition1",
                timestamp=datetime.now(),
                action_type=ActionType.PHASE_TRANSITION,
                description="Transition to specification",
                before_snapshot_id="before1",
                after_snapshot_id="after1",
                metadata={}
            )
        ]
        
        mock_undo_redo_manager.get_phase_transitions.return_value = transitions
        
        # Should not raise any exceptions
        undo_redo_cli.show_phase_transitions()
        
        mock_undo_redo_manager.get_phase_transitions.assert_called_once()

    def test_show_phase_transitions_no_transitions(self, undo_redo_cli, mock_undo_redo_manager):
        """Test showing phase transitions with no transitions available."""
        mock_undo_redo_manager.get_phase_transitions.return_value = []
        
        # Should not raise any exceptions
        undo_redo_cli.show_phase_transitions()
        
        mock_undo_redo_manager.get_phase_transitions.assert_called_once()

    def test_display_operation_result_success(self, undo_redo_cli):
        """Test displaying successful operation result."""
        # Should not raise any exceptions
        undo_redo_cli.display_operation_result("undo", True, "Operation completed")

    def test_display_operation_result_failure(self, undo_redo_cli):
        """Test displaying failed operation result."""
        # Should not raise any exceptions
        undo_redo_cli.display_operation_result("redo", False, "Operation failed")

    def test_display_current_state_info_with_snapshot(self, undo_redo_cli, mock_undo_redo_manager, sample_project_state):
        """Test displaying current state info with valid snapshot."""
        snapshot = StateSnapshot(
            id="current1",
            timestamp=datetime.now(),
            snapshot_type=SnapshotType.AUTOMATIC,
            description="Current state",
            project_state=sample_project_state,
            metadata={}
        )
        
        mock_undo_redo_manager.get_snapshot_by_id.return_value = snapshot
        
        # Should not raise any exceptions
        undo_redo_cli.display_current_state_info("current1")
        
        mock_undo_redo_manager.get_snapshot_by_id.assert_called_once_with("current1")

    def test_display_current_state_info_no_snapshot(self, undo_redo_cli):
        """Test displaying current state info with no snapshot."""
        # Should not raise any exceptions
        undo_redo_cli.display_current_state_info(None)

    def test_display_current_state_info_invalid_snapshot(self, undo_redo_cli, mock_undo_redo_manager):
        """Test displaying current state info with invalid snapshot."""
        mock_undo_redo_manager.get_snapshot_by_id.return_value = None
        
        # Should not raise any exceptions
        undo_redo_cli.display_current_state_info("invalid")
        
        mock_undo_redo_manager.get_snapshot_by_id.assert_called_once_with("invalid")

    @patch('dev_agent.cli.undo_redo_cli.IntPrompt.ask')
    def test_keyboard_interrupt_handling(self, mock_int_prompt, undo_redo_cli, mock_undo_redo_manager):
        """Test handling of keyboard interrupts."""
        snapshots = [
            StateSnapshot(
                id="snapshot1",
                timestamp=datetime.now(),
                snapshot_type=SnapshotType.MANUAL,
                description="Test snapshot",
                project_state=None,
                metadata={}
            )
        ]
        
        mock_undo_redo_manager.get_available_snapshots.return_value = snapshots
        mock_int_prompt.side_effect = KeyboardInterrupt()
        
        result = undo_redo_cli.show_snapshots_browser()
        
        assert result is None

    @patch('dev_agent.cli.undo_redo_cli.IntPrompt.ask')
    def test_eof_error_handling(self, mock_int_prompt, undo_redo_cli, mock_undo_redo_manager):
        """Test handling of EOF errors."""
        snapshots = [
            StateSnapshot(
                id="snapshot1",
                timestamp=datetime.now(),
                snapshot_type=SnapshotType.MANUAL,
                description="Test snapshot",
                project_state=None,
                metadata={}
            )
        ]
        
        mock_undo_redo_manager.get_available_snapshots.return_value = snapshots
        mock_int_prompt.side_effect = EOFError()
        
        result = undo_redo_cli.show_snapshots_browser()
        
        assert result is None