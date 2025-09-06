"""Project state data models."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, List
from .enums import PhaseType, TaskStatus, DocumentType
from .documents import SpecificationDocument, DesignDocument, TaskList


@dataclass
class IndexMetadata:
    """Metadata about the codebase index."""
    total_files: int
    total_lines: int
    languages_detected: List[str]
    index_size_mb: float
    last_indexed: datetime
    index_version: str


@dataclass
class SessionData:
    """Data about the current or last session."""
    session_id: str
    started_at: datetime
    last_activity: datetime
    user_approvals: Dict[str, bool]  # phase -> approved
    pending_approvals: List[str]


@dataclass
class ProjectState:
    """Complete state of a dev-agent project."""
    project_path: str
    current_phase: PhaseType
    indexing_complete: bool
    specification: Optional[SpecificationDocument]
    design: Optional[DesignDocument]
    tasks: Optional[TaskList]
    implementation_progress: Dict[str, TaskStatus]
    index_metadata: Optional[IndexMetadata]
    session_data: SessionData
    created_at: datetime
    updated_at: datetime