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
class DesignAnalysis:
    """Analysis results for design generation."""

    architecture_overview: str
    components: list[ComponentAnalysis]
    design_patterns: list[str]
    data_models: list[dict[str, Any]]
    api_interfaces: list[dict[str, Any]]
    quality_metrics: dict[str, float]
    technical_debt: list[str]
    recommendations: list[str] = field(default_factory=list)


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

@dataclass
class LanguageInfo:
    """Information about a programming language used in the project."""

    language: str
    version: str | None
    file_count: int
    line_count: int
    frameworks: list[str]
    conventions: dict[str, Any]
    quality_score: float


@dataclass
class UsagePattern:
    """Pattern of framework or library usage."""

    pattern: str
    file_path: str
    occurrences: int
    examples: list[str]


@dataclass
class Improvement:
    """Suggested improvement for code or architecture."""

    category: str
    description: str
    priority: str  # 'low', 'medium', 'high'
    effort: str    # 'low', 'medium', 'high'


@dataclass
class FrameworkInfo:
    """Information about a framework used in the project."""

    name: str
    version: str
    usage_patterns: list[UsagePattern]
    configuration_files: list[str]
    best_practices_compliance: float
    suggested_improvements: list[Improvement]


@dataclass
class CrossLanguageMappings:
    """Mappings and interactions between different languages in the project."""

    api_interactions: dict[str, Any]
    data_flow: dict[str, Any]
    shared_configurations: dict[str, Any]
    build_dependencies: dict[str, Any]
    integration_patterns: list[str]


@dataclass
class LanguageConventions:
    """Coding conventions for a specific language."""

    naming_style: dict[str, Any]
    formatting_style: dict[str, Any]
    documentation_style: dict[str, Any]
    error_handling_style: dict[str, Any]
    consistency_score: float


@dataclass
class CodeSmell:
    """Represents a code smell or anti-pattern."""

    name: str
    description: str
    file_path: str
    line_number: int
    severity: str  # 'low', 'medium', 'high', 'critical'
    category: str  # 'maintainability', 'readability', 'performance', 'design'
    suggestion: str
    code_snippet: str
    confidence: float


@dataclass
class SecurityIssue:
    """Represents a security vulnerability or issue."""

    vulnerability_type: str
    description: str
    file_path: str
    line_number: int
    severity: str  # 'low', 'medium', 'high', 'critical'
    cwe_id: str | None  # Common Weakness Enumeration ID
    suggestion: str
    code_snippet: str
    confidence: float


@dataclass
class PerformanceIssue:
    """Represents a performance bottleneck or optimization opportunity."""

    issue_type: str
    description: str
    file_path: str
    line_number: int
    impact: str  # 'low', 'medium', 'high'
    category: str  # 'algorithm', 'memory', 'io', 'database', 'network'
    suggestion: str
    code_snippet: str
    estimated_improvement: str | None
    confidence: float


@dataclass
class ArchitecturalViolation:
    """Represents an architectural rule violation."""

    rule_name: str
    description: str
    file_path: str
    violation_type: str  # 'dependency', 'layer', 'coupling', 'cohesion'
    severity: str  # 'low', 'medium', 'high'
    suggestion: str
    affected_components: list[str]
    confidence: float


@dataclass
class QualityAnalysisResult:
    """Results from code quality analysis."""

    overall_score: float
    code_smells: list[CodeSmell]
    maintainability_index: float
    cyclomatic_complexity: dict[str, float]
    duplication_percentage: float
    test_coverage_estimate: float
    documentation_coverage: float
    summary: str
    recommendations: list[str]


@dataclass
class SecurityAnalysisResult:
    """Results from security analysis."""

    overall_security_score: float
    security_issues: list[SecurityIssue]
    vulnerability_count_by_severity: dict[str, int]
    security_hotspots: list[str]
    compliance_issues: list[str]
    summary: str
    recommendations: list[str]


@dataclass
class PerformanceAnalysisResult:
    """Results from performance analysis."""

    overall_performance_score: float
    performance_issues: list[PerformanceIssue]
    bottlenecks: list[str]
    optimization_opportunities: list[str]
    resource_usage_patterns: dict[str, Any]
    summary: str
    recommendations: list[str]


@dataclass
class ArchitecturalAnalysisResult:
    """Results from architectural analysis."""

    overall_architecture_score: float
    violations: list[ArchitecturalViolation]
    coupling_metrics: dict[str, float]
    cohesion_metrics: dict[str, float]
    dependency_issues: list[str]
    design_pattern_violations: list[str]
    summary: str
    recommendations: list[str]


@dataclass
class ComprehensiveAnalysisResult:
    """Comprehensive analysis results from all analyzers."""

    quality_analysis: QualityAnalysisResult
    security_analysis: SecurityAnalysisResult
    performance_analysis: PerformanceAnalysisResult
    architectural_analysis: ArchitecturalAnalysisResult
    overall_health_score: float
    critical_issues: list[str]
    priority_recommendations: list[str]
    analysis_timestamp: str
    analysis_duration: float