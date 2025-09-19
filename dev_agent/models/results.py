"""Result classes for various operations."""

from dataclasses import dataclass, field
from typing import Any, Optional

from .enums import PhaseStatus, PhaseType


@dataclass
class PhaseResult:
    """Base class for phase execution results."""

    phase: PhaseType
    status: PhaseStatus
    message: str
    errors: list[str] = field(default_factory=list)


@dataclass
class IndexingResult:
    """Result of indexing phase execution."""

    phase: PhaseType = PhaseType.INDEXING
    status: PhaseStatus = PhaseStatus.NOT_STARTED
    message: str = ""
    errors: list[str] = field(default_factory=list)
    files_indexed: int = 0
    total_lines: int = 0
    index_size_mb: float = 0.0
    languages_detected: list[str] = field(default_factory=list)


@dataclass
class SpecificationResult:
    """Result of specification phase execution."""

    phase: PhaseType = PhaseType.SPECIFICATION
    status: PhaseStatus = PhaseStatus.NOT_STARTED
    message: str = ""
    errors: list[str] = field(default_factory=list)
    requirements_count: int = 0
    source_type: str = ""
    confidence_score: float = 0.0


@dataclass
class DesignResult:
    """Result of design phase execution."""

    phase: PhaseType = PhaseType.DESIGN
    status: PhaseStatus = PhaseStatus.NOT_STARTED
    message: str = ""
    errors: list[str] = field(default_factory=list)
    components_count: int = 0
    interfaces_count: int = 0
    data_models_count: int = 0


@dataclass
class ImplementationResult:
    """Result of implementation phase execution."""

    phase: PhaseType = PhaseType.IMPLEMENTATION
    status: PhaseStatus = PhaseStatus.NOT_STARTED
    message: str = ""
    errors: list[str] = field(default_factory=list)
    tasks_completed: int = 0
    files_generated: int = 0
    tests_generated: int = 0


@dataclass
class IndexResult:
    """Result of indexing operation."""

    success: bool
    ast_index: Optional["ASTIndex"]
    embeddings_count: int
    errors: list[str]
    metadata: dict[str, Any]


@dataclass
class GeneratedCode:
    """Result of code generation."""

    code: str
    file_path: str
    imports: list[str]
    dependencies: list[str]
    tests: str | None = None
