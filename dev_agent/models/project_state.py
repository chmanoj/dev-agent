"""Project state data models."""

from dataclasses import dataclass
from datetime import datetime

from .documents import DesignDocument, SpecificationDocument, TaskList
from .enums import PhaseType, TaskStatus


@dataclass
class IndexMetadata:
    """Metadata about the codebase index."""

    total_files: int
    total_lines: int
    languages_detected: list[str]
    index_size_mb: float
    last_indexed: datetime
    index_version: str


@dataclass
class SessionData:
    """Data about the current or last session."""

    session_id: str
    started_at: datetime
    last_activity: datetime
    user_approvals: dict[str, bool]  # phase -> approved
    pending_approvals: list[str]


@dataclass
class ProjectState:
    """Complete state of a dev-agent project."""

    project_path: str
    current_phase: PhaseType
    indexing_complete: bool
    specification: SpecificationDocument | None
    design: DesignDocument | None
    tasks: TaskList | None
    implementation_progress: dict[str, TaskStatus]
    index_metadata: IndexMetadata | None
    session_data: SessionData
    created_at: datetime
    updated_at: datetime
