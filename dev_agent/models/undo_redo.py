"""Undo/redo data models for workflow state management."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .enums import PhaseType
from .project_state import ProjectState


class ActionType(Enum):
    """Types of actions that can be undone/redone."""

    PHASE_TRANSITION = "phase_transition"
    DOCUMENT_MODIFICATION = "document_modification"
    USER_APPROVAL = "user_approval"
    TASK_STATUS_CHANGE = "task_status_change"
    INDEX_UPDATE = "index_update"


class SnapshotType(Enum):
    """Types of state snapshots."""

    AUTOMATIC = "automatic"  # Created automatically at phase transitions
    MANUAL = "manual"  # Created manually by user request
    APPROVAL_POINT = "approval_point"  # Created at user approval points


@dataclass
class StateSnapshot:
    """A snapshot of the project state at a specific point in time."""

    id: str
    timestamp: datetime
    snapshot_type: SnapshotType
    description: str
    project_state: ProjectState
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class UndoRedoAction:
    """Represents an action that can be undone or redone."""

    id: str
    timestamp: datetime
    action_type: ActionType
    description: str
    before_snapshot_id: str
    after_snapshot_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CommandHistoryEntry:
    """Entry in the command history for rollback capabilities."""

    id: str
    timestamp: datetime
    command: str
    phase: PhaseType
    success: bool
    snapshot_id: str
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class UndoRedoState:
    """Complete undo/redo state management."""

    snapshots: list[StateSnapshot] = field(default_factory=list)
    actions: list[UndoRedoAction] = field(default_factory=list)
    command_history: list[CommandHistoryEntry] = field(default_factory=list)
    current_snapshot_id: str | None = None
    max_snapshots: int = 50  # Maximum number of snapshots to keep
    max_history_entries: int = 100  # Maximum command history entries