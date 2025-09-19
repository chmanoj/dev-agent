"""Data models for codebase analysis results."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CodeExample:
    """Example of code implementation for reference."""

    code: str
    file_path: str
    function_name: str | None
    class_name: str | None
    description: str
    similarity_score: float
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class ArchitecturePattern:
    """Detected architectural pattern in the codebase."""

    name: str
    description: str
    confidence: float
    evidence: list[str]
    files_involved: list[str]


@dataclass
class CodePattern:
    """Detected coding pattern or convention."""

    pattern_type: str  # 'naming', 'structure', 'import', 'error_handling', etc.
    description: str
    examples: list[str]
    frequency: int
    confidence: float


@dataclass
class ArchitectureInfo:
    """Complete architecture analysis of the codebase."""

    patterns: list[ArchitecturePattern]
    layers: list[str]
    components: list[str]
    dependencies: dict[str, list[str]]
    entry_points: list[str]
    data_flow: dict[str, Any]
    technology_stack: list[str]


@dataclass
class CodePatterns:
    """Collection of detected code patterns and conventions."""

    naming_conventions: list[CodePattern]
    structural_patterns: list[CodePattern]
    import_patterns: list[CodePattern]
    error_handling_patterns: list[CodePattern]
    testing_patterns: list[CodePattern]
    documentation_patterns: list[CodePattern]
    overall_style: dict[str, Any]


@dataclass
class RequirementEvidence:
    """Evidence from code analysis supporting a requirement."""

    requirement_type: str
    description: str
    supporting_files: list[str]
    supporting_functions: list[str]
    confidence: float
    code_examples: list[CodeExample]


@dataclass
class SpecificationAnalysis:
    """Analysis results for specification generation."""

    project_purpose: str
    main_features: list[str]
    user_roles: list[str]
    functional_areas: list[str]
    requirement_evidence: list[RequirementEvidence]
    technology_constraints: list[str]
    external_dependencies: list[str]
    confidence_score: float


@dataclass
class ComponentAnalysis:
    """Analysis of a system component."""

    name: str
    purpose: str
    interfaces: list[str]
    dependencies: list[str]
    internal_structure: dict[str, Any]
    complexity_score: float
    test_coverage: float | None = None


@dataclass
class DesignAnalysis:
    """Analysis results for design document generation."""

    architecture_overview: str
    components: list[ComponentAnalysis]
    data_models: list[dict[str, Any]]
    api_interfaces: list[dict[str, Any]]
    design_patterns: list[str]
    quality_metrics: dict[str, float]
    technical_debt: list[str]
    recommendations: list[str]


@dataclass
class ContextualCode:
    """Code with contextual information for task implementation."""

    code: str
    file_path: str
    relevance_score: float
    context_type: str  # 'similar_function', 'related_class', 'dependency', etc.
    explanation: str


@dataclass
class CodeContext:
    """Contextual information for implementing a task."""

    task_id: str
    relevant_files: list[str]
    similar_implementations: list[ContextualCode]
    required_imports: list[str]
    suggested_patterns: list[CodePattern]
    dependencies: list[str]
    test_examples: list[ContextualCode]
    style_guidelines: dict[str, Any]


@dataclass
class RequirementEvidence:
    """Evidence for a requirement found in the codebase."""

    requirement_type: str
    description: str
    supporting_files: list[str]
    supporting_functions: list[str]
    confidence: float


@dataclass
class SpecificationAnalysis:
    """Analysis results for specification generation."""

    project_purpose: str
    main_features: list[str]
    user_roles: list[str]
    functional_areas: list[str]
    technology_constraints: list[str]
    requirement_evidence: list[RequirementEvidence]
    confidence_score: float


@dataclass
class ComponentAnalysis:
    """Analysis of a system component."""

    name: str
    purpose: str
    interfaces: list[str]
    dependencies: list[str]


@dataclass
class DesignAnalysis:
    """Analysis results for design generation."""

    architecture_overview: str
    components: list[ComponentAnalysis]
    design_patterns: list[str]
    data_models: list[dict[str, Any]]
    api_interfaces: list[dict[str, Any]]
    quality_metrics: dict[str, float]
    technical_debt: list[str]


@dataclass
class CodeContext:
    """Context information for code generation."""

    task: Any  # Task object
    relevant_patterns: list[str]
    similar_implementations: list[CodeExample]
    dependencies: list[str]
    suggested_approach: str


@dataclass
class ContextualCode:
    """Code with contextual information."""

    code: str
    file_path: str
    start_line: int
    end_line: int
    context_type: str  # 'function', 'class', 'module', etc.
    related_symbols: list[str]
    dependencies: list[str]
