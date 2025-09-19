"""Data models for codebase analysis results."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from .indexing import CodeChunk


@dataclass
class CodeExample:
    """Example of code implementation for reference."""
    code: str
    file_path: str
    function_name: Optional[str]
    class_name: Optional[str]
    description: str
    similarity_score: float
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ArchitecturePattern:
    """Detected architectural pattern in the codebase."""
    name: str
    description: str
    confidence: float
    evidence: List[str]
    files_involved: List[str]


@dataclass
class CodePattern:
    """Detected coding pattern or convention."""
    pattern_type: str  # 'naming', 'structure', 'import', 'error_handling', etc.
    description: str
    examples: List[str]
    frequency: int
    confidence: float


@dataclass
class ArchitectureInfo:
    """Complete architecture analysis of the codebase."""
    patterns: List[ArchitecturePattern]
    layers: List[str]
    components: List[str]
    dependencies: Dict[str, List[str]]
    entry_points: List[str]
    data_flow: Dict[str, Any]
    technology_stack: List[str]


@dataclass
class CodePatterns:
    """Collection of detected code patterns and conventions."""
    naming_conventions: List[CodePattern]
    structural_patterns: List[CodePattern]
    import_patterns: List[CodePattern]
    error_handling_patterns: List[CodePattern]
    testing_patterns: List[CodePattern]
    documentation_patterns: List[CodePattern]
    overall_style: Dict[str, Any]


@dataclass
class RequirementEvidence:
    """Evidence from code analysis supporting a requirement."""
    requirement_type: str
    description: str
    supporting_files: List[str]
    supporting_functions: List[str]
    confidence: float
    code_examples: List[CodeExample]


@dataclass
class SpecificationAnalysis:
    """Analysis results for specification generation."""
    project_purpose: str
    main_features: List[str]
    user_roles: List[str]
    functional_areas: List[str]
    requirement_evidence: List[RequirementEvidence]
    technology_constraints: List[str]
    external_dependencies: List[str]
    confidence_score: float


@dataclass
class ComponentAnalysis:
    """Analysis of a system component."""
    name: str
    purpose: str
    interfaces: List[str]
    dependencies: List[str]
    internal_structure: Dict[str, Any]
    complexity_score: float
    test_coverage: Optional[float] = None


@dataclass
class DesignAnalysis:
    """Analysis results for design document generation."""
    architecture_overview: str
    components: List[ComponentAnalysis]
    data_models: List[Dict[str, Any]]
    api_interfaces: List[Dict[str, Any]]
    design_patterns: List[str]
    quality_metrics: Dict[str, float]
    technical_debt: List[str]
    recommendations: List[str]


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
    relevant_files: List[str]
    similar_implementations: List[ContextualCode]
    required_imports: List[str]
    suggested_patterns: List[CodePattern]
    dependencies: List[str]
    test_examples: List[ContextualCode]
    style_guidelines: Dict[str, Any]


@dataclass
class RequirementEvidence:
    """Evidence for a requirement found in the codebase."""
    requirement_type: str
    description: str
    supporting_files: List[str]
    supporting_functions: List[str]
    confidence: float


@dataclass
class SpecificationAnalysis:
    """Analysis results for specification generation."""
    project_purpose: str
    main_features: List[str]
    user_roles: List[str]
    functional_areas: List[str]
    technology_constraints: List[str]
    requirement_evidence: List[RequirementEvidence]
    confidence_score: float


@dataclass
class ComponentAnalysis:
    """Analysis of a system component."""
    name: str
    purpose: str
    interfaces: List[str]
    dependencies: List[str]


@dataclass
class DesignAnalysis:
    """Analysis results for design generation."""
    architecture_overview: str
    components: List[ComponentAnalysis]
    design_patterns: List[str]
    data_models: List[Dict[str, Any]]
    api_interfaces: List[Dict[str, Any]]
    quality_metrics: Dict[str, float]
    technical_debt: List[str]


@dataclass
class CodeContext:
    """Context information for code generation."""
    task: Any  # Task object
    relevant_patterns: List[str]
    similar_implementations: List[CodeExample]
    dependencies: List[str]
    suggested_approach: str


@dataclass
class ContextualCode:
    """Code with contextual information."""
    code: str
    file_path: str
    start_line: int
    end_line: int
    context_type: str  # 'function', 'class', 'module', etc.
    related_symbols: List[str]
    dependencies: List[str]