"""Context classes for various operations."""

from dataclasses import dataclass
from typing import Any, Optional

from .indexing import ASTIndex, SymbolInfo
from .language_patterns import LanguageProjectContext
from .project_state import ProjectState


@dataclass
class ProjectContext:
    """Context information for a project."""

    project_state: ProjectState
    ast_index: ASTIndex | None
    codebase_patterns: Optional["CodePatterns"]
    user_preferences: dict[str, Any]
    language_context: LanguageProjectContext | None = None


@dataclass
class CodeContext:
    """Context for code generation tasks."""

    relevant_symbols: list[SymbolInfo]
    similar_implementations: list["CodeExample"]
    existing_patterns: "CodePatterns"
    dependencies: list[str]
    file_structure: dict[str, Any]


@dataclass
class CodeExample:
    """Example of existing code for reference."""

    code: str
    file_path: str
    description: str
    similarity_score: float


@dataclass
class CodePatterns:
    """Patterns identified in existing codebase."""

    naming_conventions: dict[str, str]
    import_patterns: list[str]
    class_patterns: list[str]
    function_patterns: list[str]
    test_patterns: list[str]
    documentation_style: str


@dataclass
class SpecificationAnalysis:
    """Analysis results for specification generation."""

    identified_features: list[str]
    user_workflows: list[str]
    data_entities: list[str]
    external_dependencies: list[str]
    confidence_scores: dict[str, float]


@dataclass
class DesignAnalysis:
    """Analysis results for design generation."""

    architecture_type: str
    component_structure: dict[str, Any]
    data_flow: list[str]
    integration_points: list[str]
    design_patterns: list[str]


@dataclass
class ArchitectureInfo:
    """Information about codebase architecture."""

    pattern_type: str  # MVC, layered, microservices, etc.
    layers: list[str]
    components: list[str]
    communication_patterns: list[str]


@dataclass
class TaskProgress:
    """Progress tracking for implementation tasks."""

    task_id: str
    completion_percentage: float
    files_modified: list[str]
    tests_written: int
    blockers: list[str]
