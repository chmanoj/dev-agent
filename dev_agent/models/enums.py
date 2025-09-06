"""Core enums for the dev-agent system."""

from enum import Enum, auto


class PhaseType(Enum):
    """Represents the four phases of the development workflow."""
    INDEXING = "indexing"
    SPECIFICATION = "specification"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"


class PhaseStatus(Enum):
    """Status of a workflow phase."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_APPROVAL = "requires_approval"


class TaskStatus(Enum):
    """Status of an implementation task."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class Priority(Enum):
    """Priority level for requirements and tasks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DocumentType(Enum):
    """Types of documents managed by the system."""
    SPECIFICATION = "specification"
    DESIGN = "design"
    TASKS = "tasks"


class SpecificationSource(Enum):
    """Source of specification generation."""
    EXISTING_CODE = "existing_code"
    USER_INPUT = "user_input"