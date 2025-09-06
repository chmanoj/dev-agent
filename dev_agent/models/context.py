"""Context classes for various operations."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from .project_state import ProjectState
from .indexing import ASTIndex, SymbolInfo


@dataclass
class ProjectContext:
    """Context information for a project."""
    project_state: ProjectState
    ast_index: Optional[ASTIndex]
    codebase_patterns: Optional['CodePatterns']
    user_preferences: Dict[str, Any]


@dataclass
class CodeContext:
    """Context for code generation tasks."""
    relevant_symbols: List[SymbolInfo]
    similar_implementations: List['CodeExample']
    existing_patterns: 'CodePatterns'
    dependencies: List[str]
    file_structure: Dict[str, Any]


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
    naming_conventions: Dict[str, str]
    import_patterns: List[str]
    class_patterns: List[str]
    function_patterns: List[str]
    test_patterns: List[str]
    documentation_style: str


@dataclass
class SpecificationAnalysis:
    """Analysis results for specification generation."""
    identified_features: List[str]
    user_workflows: List[str]
    data_entities: List[str]
    external_dependencies: List[str]
    confidence_scores: Dict[str, float]


@dataclass
class DesignAnalysis:
    """Analysis results for design generation."""
    architecture_type: str
    component_structure: Dict[str, Any]
    data_flow: List[str]
    integration_points: List[str]
    design_patterns: List[str]


@dataclass
class ArchitectureInfo:
    """Information about codebase architecture."""
    pattern_type: str  # MVC, layered, microservices, etc.
    layers: List[str]
    components: List[str]
    communication_patterns: List[str]


@dataclass
class TaskProgress:
    """Progress tracking for implementation tasks."""
    task_id: str
    completion_percentage: float
    files_modified: List[str]
    tests_written: int
    blockers: List[str]