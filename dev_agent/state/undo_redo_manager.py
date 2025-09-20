"""Undo/redo manager for workflow state changes and document modifications."""

from __future__ import annotations

import json
import uuid
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

from ..models.enums import PhaseType
from ..models.project_state import ProjectState
from ..models.undo_redo import (
    ActionType,
    CommandHistoryEntry,
    SnapshotType,
    StateSnapshot,
    UndoRedoAction,
    UndoRedoState,
)


class UndoRedoManager:
    """Manages undo/redo functionality for workflow operations."""

    def __init__(self, project_path: str):
        """Initialize UndoRedoManager for a specific project.

        Args:
            project_path: Path to the project directory
        """
        self.project_path = Path(project_path)
        self.dev_agent_dir = self.project_path / ".dev_agent"
        self.undo_redo_file = self.dev_agent_dir / "undo_redo.json"
        self.snapshots_dir = self.dev_agent_dir / "snapshots"

        # Ensure directories exist
        self._ensure_directories()

        # Load or initialize undo/redo state
        self.undo_redo_state = self._load_undo_redo_state()

    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.dev_agent_dir.mkdir(exist_ok=True)
        self.snapshots_dir.mkdir(exist_ok=True)

    def create_snapshot(
        self,
        project_state: ProjectState,
        snapshot_type: SnapshotType,
        description: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Create a snapshot of the current project state.

        Args:
            project_state: Current project state to snapshot
            snapshot_type: Type of snapshot being created
            description: Human-readable description of the snapshot
            metadata: Optional metadata to store with the snapshot

        Returns:
            Snapshot ID
        """
        snapshot_id = str(uuid.uuid4())
        timestamp = datetime.now()

        # Create deep copy of project state to avoid reference issues
        state_copy = deepcopy(project_state)

        snapshot = StateSnapshot(
            id=snapshot_id,
            timestamp=timestamp,
            snapshot_type=snapshot_type,
            description=description,
            project_state=state_copy,
            metadata=metadata or {},
        )

        # Save snapshot to separate file for better performance
        self._save_snapshot_to_file(snapshot)

        # Add to snapshots list (store only metadata in main file)
        snapshot_metadata = StateSnapshot(
            id=snapshot_id,
            timestamp=timestamp,
            snapshot_type=snapshot_type,
            description=description,
            project_state=None,  # Don't store full state in main file
            metadata=metadata or {},
        )

        self.undo_redo_state.snapshots.append(snapshot_metadata)
        self.undo_redo_state.current_snapshot_id = snapshot_id

        # Cleanup old snapshots if needed
        self._cleanup_old_snapshots()

        # Save undo/redo state
        self._save_undo_redo_state()

        return snapshot_id

    def create_action(
        self,
        action_type: ActionType,
        description: str,
        before_snapshot_id: str,
        after_snapshot_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Create an undo/redo action.

        Args:
            action_type: Type of action
            description: Human-readable description
            before_snapshot_id: Snapshot ID before the action
            after_snapshot_id: Snapshot ID after the action
            metadata: Optional metadata

        Returns:
            Action ID
        """
        action_id = str(uuid.uuid4())
        timestamp = datetime.now()

        action = UndoRedoAction(
            id=action_id,
            timestamp=timestamp,
            action_type=action_type,
            description=description,
            before_snapshot_id=before_snapshot_id,
            after_snapshot_id=after_snapshot_id,
            metadata=metadata or {},
        )

        self.undo_redo_state.actions.append(action)
        self._save_undo_redo_state()

        return action_id

    def add_command_history_entry(
        self,
        command: str,
        phase: PhaseType,
        success: bool,
        snapshot_id: str,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Add an entry to the command history.

        Args:
            command: Command that was executed
            phase: Phase during which command was executed
            success: Whether the command succeeded
            snapshot_id: Snapshot ID associated with this command
            error_message: Error message if command failed
            metadata: Optional metadata

        Returns:
            History entry ID
        """
        entry_id = str(uuid.uuid4())
        timestamp = datetime.now()

        entry = CommandHistoryEntry(
            id=entry_id,
            timestamp=timestamp,
            command=command,
            phase=phase,
            success=success,
            snapshot_id=snapshot_id,
            error_message=error_message,
            metadata=metadata or {},
        )

        self.undo_redo_state.command_history.append(entry)

        # Cleanup old history entries if needed
        self._cleanup_old_history()

        self._save_undo_redo_state()

        return entry_id

    def get_available_snapshots(self) -> list[StateSnapshot]:
        """Get list of available snapshots for browsing.

        Returns:
            List of snapshot metadata (without full project state)
        """
        return sorted(
            self.undo_redo_state.snapshots,
            key=lambda s: s.timestamp,
            reverse=True,
        )

    def get_snapshot_by_id(self, snapshot_id: str) -> StateSnapshot | None:
        """Get a specific snapshot by ID, including full project state.

        Args:
            snapshot_id: ID of the snapshot to retrieve

        Returns:
            Complete snapshot with project state, or None if not found
        """
        return self._load_snapshot_from_file(snapshot_id)

    def restore_snapshot(self, snapshot_id: str) -> ProjectState | None:
        """Restore project state from a specific snapshot.

        Args:
            snapshot_id: ID of the snapshot to restore

        Returns:
            Restored project state, or None if snapshot not found
        """
        snapshot = self.get_snapshot_by_id(snapshot_id)
        if not snapshot or not snapshot.project_state:
            return None

        # Update current snapshot ID
        self.undo_redo_state.current_snapshot_id = snapshot_id
        self._save_undo_redo_state()

        return deepcopy(snapshot.project_state)

    def get_undo_actions(self, limit: int = 10) -> list[UndoRedoAction]:
        """Get available undo actions.

        Args:
            limit: Maximum number of actions to return

        Returns:
            List of actions that can be undone
        """
        if not self.undo_redo_state.current_snapshot_id:
            return []

        # Find actions that led to the current state
        current_actions = []
        for action in reversed(self.undo_redo_state.actions):
            if action.after_snapshot_id == self.undo_redo_state.current_snapshot_id:
                current_actions.append(action)
                if len(current_actions) >= limit:
                    break

        return current_actions

    def get_redo_actions(self, limit: int = 10) -> list[UndoRedoAction]:
        """Get available redo actions.

        Args:
            limit: Maximum number of actions to return

        Returns:
            List of actions that can be redone
        """
        if not self.undo_redo_state.current_snapshot_id:
            return []

        # Find actions that can be redone from current state
        redo_actions = []
        for action in self.undo_redo_state.actions:
            if action.before_snapshot_id == self.undo_redo_state.current_snapshot_id:
                redo_actions.append(action)
                if len(redo_actions) >= limit:
                    break

        return redo_actions

    def undo_action(self, action_id: str) -> ProjectState | None:
        """Undo a specific action.

        Args:
            action_id: ID of the action to undo

        Returns:
            Project state after undo, or None if action not found
        """
        action = self._find_action_by_id(action_id)
        if not action:
            return None

        # Restore to the before state
        return self.restore_snapshot(action.before_snapshot_id)

    def redo_action(self, action_id: str) -> ProjectState | None:
        """Redo a specific action.

        Args:
            action_id: ID of the action to redo

        Returns:
            Project state after redo, or None if action not found
        """
        action = self._find_action_by_id(action_id)
        if not action:
            return None

        # Restore to the after state
        return self.restore_snapshot(action.after_snapshot_id)

    def get_command_history(self, limit: int = 20) -> list[CommandHistoryEntry]:
        """Get command history entries.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of command history entries
        """
        return sorted(
            self.undo_redo_state.command_history,
            key=lambda e: e.timestamp,
            reverse=True,
        )[:limit]

    def rollback_to_command(self, entry_id: str) -> ProjectState | None:
        """Rollback to a specific command in history.

        Args:
            entry_id: ID of the command history entry

        Returns:
            Project state at that point, or None if entry not found
        """
        entry = self._find_history_entry_by_id(entry_id)
        if not entry:
            return None

        return self.restore_snapshot(entry.snapshot_id)

    def get_phase_transitions(self) -> list[UndoRedoAction]:
        """Get all phase transition actions.

        Returns:
            List of phase transition actions
        """
        return [
            action
            for action in self.undo_redo_state.actions
            if action.action_type == ActionType.PHASE_TRANSITION
        ]

    def cleanup_snapshots(self, keep_count: int | None = None) -> int:
        """Cleanup old snapshots, keeping only the most recent ones.

        Args:
            keep_count: Number of snapshots to keep (uses default if None)

        Returns:
            Number of snapshots removed
        """
        keep_count = keep_count or self.undo_redo_state.max_snapshots
        
        if len(self.undo_redo_state.snapshots) <= keep_count:
            return 0

        # Sort by timestamp and keep the most recent
        sorted_snapshots = sorted(
            self.undo_redo_state.snapshots,
            key=lambda s: s.timestamp,
            reverse=True,
        )

        snapshots_to_keep = sorted_snapshots[:keep_count]
        snapshots_to_remove = sorted_snapshots[keep_count:]

        # Remove snapshot files
        removed_count = 0
        for snapshot in snapshots_to_remove:
            snapshot_file = self.snapshots_dir / f"{snapshot.id}.json"
            if snapshot_file.exists():
                snapshot_file.unlink()
                removed_count += 1

        # Update snapshots list
        self.undo_redo_state.snapshots = snapshots_to_keep

        # Remove orphaned actions
        valid_snapshot_ids = {s.id for s in snapshots_to_keep}
        self.undo_redo_state.actions = [
            action
            for action in self.undo_redo_state.actions
            if (
                action.before_snapshot_id in valid_snapshot_ids
                and action.after_snapshot_id in valid_snapshot_ids
            )
        ]

        self._save_undo_redo_state()
        return removed_count

    def _save_snapshot_to_file(self, snapshot: StateSnapshot) -> None:
        """Save a snapshot to its own file.

        Args:
            snapshot: Snapshot to save
        """
        snapshot_file = self.snapshots_dir / f"{snapshot.id}.json"
        
        # Convert snapshot to dictionary for JSON serialization
        snapshot_dict = self._serialize_snapshot(snapshot)
        
        with open(snapshot_file, "w", encoding="utf-8") as f:
            json.dump(snapshot_dict, f, indent=2, ensure_ascii=False)

    def _load_snapshot_from_file(self, snapshot_id: str) -> StateSnapshot | None:
        """Load a snapshot from its file.

        Args:
            snapshot_id: ID of the snapshot to load

        Returns:
            Complete snapshot with project state, or None if not found
        """
        snapshot_file = self.snapshots_dir / f"{snapshot_id}.json"
        
        if not snapshot_file.exists():
            return None

        try:
            with open(snapshot_file, encoding="utf-8") as f:
                snapshot_dict = json.load(f)
            
            return self._deserialize_snapshot(snapshot_dict)
        except Exception:
            return None

    def _serialize_snapshot(self, snapshot: StateSnapshot) -> dict[str, Any]:
        """Serialize a snapshot to dictionary for JSON storage.

        Args:
            snapshot: Snapshot to serialize

        Returns:
            Dictionary representation
        """
        from ..state.state_manager import StateManager
        
        # Use StateManager's serialization logic for project state
        state_manager = StateManager(str(self.project_path))
        
        # Serialize metadata, handling enums
        serialized_metadata = {}
        for key, value in snapshot.metadata.items():
            if hasattr(value, 'value'):  # Handle enums
                serialized_metadata[key] = value.value
            else:
                serialized_metadata[key] = value
        
        return {
            "id": snapshot.id,
            "timestamp": snapshot.timestamp.isoformat(),
            "snapshot_type": snapshot.snapshot_type.value,
            "description": snapshot.description,
            "project_state": state_manager._serialize_dataclass(snapshot.project_state) if snapshot.project_state else None,
            "metadata": serialized_metadata,
        }

    def _deserialize_snapshot(self, snapshot_dict: dict[str, Any]) -> StateSnapshot:
        """Deserialize a snapshot from dictionary.

        Args:
            snapshot_dict: Dictionary representation

        Returns:
            StateSnapshot object
        """
        from ..state.state_manager import StateManager
        
        # Use StateManager's deserialization logic for project state
        state_manager = StateManager(str(self.project_path))
        
        project_state = None
        if snapshot_dict["project_state"]:
            project_state = state_manager._reconstruct_project_state(
                snapshot_dict["project_state"]
            )

        # Deserialize metadata, converting phase strings back to enums if needed
        metadata = snapshot_dict["metadata"].copy()
        if "phase" in metadata and isinstance(metadata["phase"], str):
            try:
                metadata["phase"] = PhaseType(metadata["phase"])
            except ValueError:
                pass  # Keep as string if not a valid PhaseType
        
        return StateSnapshot(
            id=snapshot_dict["id"],
            timestamp=datetime.fromisoformat(snapshot_dict["timestamp"]),
            snapshot_type=SnapshotType(snapshot_dict["snapshot_type"]),
            description=snapshot_dict["description"],
            project_state=project_state,
            metadata=metadata,
        )

    def _save_undo_redo_state(self) -> None:
        """Save undo/redo state to file."""
        def serialize_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
            """Serialize metadata, handling enums."""
            serialized = {}
            for key, value in metadata.items():
                if hasattr(value, 'value'):  # Handle enums
                    serialized[key] = value.value
                else:
                    serialized[key] = value
            return serialized
        
        state_dict = {
            "snapshots": [
                {
                    "id": s.id,
                    "timestamp": s.timestamp.isoformat(),
                    "snapshot_type": s.snapshot_type.value,
                    "description": s.description,
                    "metadata": serialize_metadata(s.metadata),
                }
                for s in self.undo_redo_state.snapshots
            ],
            "actions": [
                {
                    "id": a.id,
                    "timestamp": a.timestamp.isoformat(),
                    "action_type": a.action_type.value,
                    "description": a.description,
                    "before_snapshot_id": a.before_snapshot_id,
                    "after_snapshot_id": a.after_snapshot_id,
                    "metadata": serialize_metadata(a.metadata),
                }
                for a in self.undo_redo_state.actions
            ],
            "command_history": [
                {
                    "id": h.id,
                    "timestamp": h.timestamp.isoformat(),
                    "command": h.command,
                    "phase": h.phase.value,
                    "success": h.success,
                    "snapshot_id": h.snapshot_id,
                    "error_message": h.error_message,
                    "metadata": serialize_metadata(h.metadata),
                }
                for h in self.undo_redo_state.command_history
            ],
            "current_snapshot_id": self.undo_redo_state.current_snapshot_id,
            "max_snapshots": self.undo_redo_state.max_snapshots,
            "max_history_entries": self.undo_redo_state.max_history_entries,
        }

        with open(self.undo_redo_file, "w", encoding="utf-8") as f:
            json.dump(state_dict, f, indent=2, ensure_ascii=False)

    def _load_undo_redo_state(self) -> UndoRedoState:
        """Load undo/redo state from file.

        Returns:
            UndoRedoState object
        """
        if not self.undo_redo_file.exists():
            return UndoRedoState()

        try:
            with open(self.undo_redo_file, encoding="utf-8") as f:
                state_dict = json.load(f)

            def deserialize_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
                """Deserialize metadata, converting phase strings back to enums if needed."""
                deserialized = metadata.copy()
                if "phase" in deserialized and isinstance(deserialized["phase"], str):
                    try:
                        deserialized["phase"] = PhaseType(deserialized["phase"])
                    except ValueError:
                        pass  # Keep as string if not a valid PhaseType
                return deserialized

            snapshots = [
                StateSnapshot(
                    id=s["id"],
                    timestamp=datetime.fromisoformat(s["timestamp"]),
                    snapshot_type=SnapshotType(s["snapshot_type"]),
                    description=s["description"],
                    project_state=None,  # Loaded separately when needed
                    metadata=deserialize_metadata(s["metadata"]),
                )
                for s in state_dict.get("snapshots", [])
            ]

            actions = [
                UndoRedoAction(
                    id=a["id"],
                    timestamp=datetime.fromisoformat(a["timestamp"]),
                    action_type=ActionType(a["action_type"]),
                    description=a["description"],
                    before_snapshot_id=a["before_snapshot_id"],
                    after_snapshot_id=a["after_snapshot_id"],
                    metadata=deserialize_metadata(a["metadata"]),
                )
                for a in state_dict.get("actions", [])
            ]

            command_history = [
                CommandHistoryEntry(
                    id=h["id"],
                    timestamp=datetime.fromisoformat(h["timestamp"]),
                    command=h["command"],
                    phase=PhaseType(h["phase"]),
                    success=h["success"],
                    snapshot_id=h["snapshot_id"],
                    error_message=h["error_message"],
                    metadata=deserialize_metadata(h["metadata"]),
                )
                for h in state_dict.get("command_history", [])
            ]

            return UndoRedoState(
                snapshots=snapshots,
                actions=actions,
                command_history=command_history,
                current_snapshot_id=state_dict.get("current_snapshot_id"),
                max_snapshots=state_dict.get("max_snapshots", 50),
                max_history_entries=state_dict.get("max_history_entries", 100),
            )

        except Exception:
            return UndoRedoState()

    def _cleanup_old_snapshots(self) -> None:
        """Cleanup old snapshots if limit exceeded."""
        if len(self.undo_redo_state.snapshots) > self.undo_redo_state.max_snapshots:
            self.cleanup_snapshots()

    def _cleanup_old_history(self) -> None:
        """Cleanup old command history entries if limit exceeded."""
        if len(self.undo_redo_state.command_history) > self.undo_redo_state.max_history_entries:
            # Keep only the most recent entries
            sorted_history = sorted(
                self.undo_redo_state.command_history,
                key=lambda h: h.timestamp,
                reverse=True,
            )
            self.undo_redo_state.command_history = sorted_history[
                : self.undo_redo_state.max_history_entries
            ]

    def _find_action_by_id(self, action_id: str) -> UndoRedoAction | None:
        """Find an action by its ID.

        Args:
            action_id: ID of the action to find

        Returns:
            UndoRedoAction if found, None otherwise
        """
        for action in self.undo_redo_state.actions:
            if action.id == action_id:
                return action
        return None

    def _find_history_entry_by_id(self, entry_id: str) -> CommandHistoryEntry | None:
        """Find a command history entry by its ID.

        Args:
            entry_id: ID of the entry to find

        Returns:
            CommandHistoryEntry if found, None otherwise
        """
        for entry in self.undo_redo_state.command_history:
            if entry.id == entry_id:
                return entry
        return None