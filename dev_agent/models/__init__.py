"""Core data models and enums for the dev-agent system."""

from .cost_tracking import CostReport, TokenUsage
from .documents import (
    DesignDocument,
    Requirement,
    SpecificationDocument,
    Task,
    TaskList,
)
from .enums import (
    DocumentType,
    LLMOperationType,
    LLMProvider,
    PhaseStatus,
    PhaseType,
    Priority,
    SpecificationSource,
    TaskStatus,
)

# LLM-related models
from .llm_config import AzureOpenAIConfig, GeminiConfig
from .llm_responses import CompletionResponse, EmbeddingResponse
from .project_state import IndexMetadata, ProjectState, SessionData

# Language pattern models
from .language_patterns import FrameworkPatterns, LanguagePatterns, LanguageProjectContext

# Optional imports that may have external dependencies
try:
    from .indexing import (
        ASTIndex,
        ClassDef,
        CodeChunk,
        CodeMatch,
        Embedding,
        FunctionDef,
        Import,
        SymbolInfo,
    )

    _INDEXING_AVAILABLE = True
except ImportError:
    _INDEXING_AVAILABLE = False

try:
    from .results import (
        DesignResult,
        GeneratedCode,
        ImplementationResult,
        IndexingResult,
        IndexResult,
        PhaseResult,
        SpecificationResult,
    )

    _RESULTS_AVAILABLE = True
except ImportError:
    _RESULTS_AVAILABLE = False

try:
    from .context import (
        ArchitectureInfo,
        CodeContext,
        CodeExample,
        CodePatterns,
        DesignAnalysis,
        ProjectContext,
        SpecificationAnalysis,
        TaskProgress,
    )

    _CONTEXT_AVAILABLE = True
except ImportError:
    _CONTEXT_AVAILABLE = False

try:
    from .visualization import (
        ArchitectureVisualization,
        ComponentVisualization,
        DataFlowVisualization,
        DependencyVisualization,
        DiagramExportOptions,
        DiagramMetadata,
        DiagramTemplate,
        DiagramType,
        DiagramValidationResult,
        ExportFormat,
        FilterCriteria,
        InteractiveDiagram,
        MultiLanguageVisualization,
        VisualizationConfig,
    )

    _VISUALIZATION_AVAILABLE = True
except ImportError:
    _VISUALIZATION_AVAILABLE = False

try:
    from .templates import (
        CustomizationPoint,
        DirectoryTemplate,
        FileTemplate,
        ProjectSpec,
        ProjectTemplate,
        ScaffoldingResult,
        TemplateContext,
        TemplateRegistry,
        TemplateValidationResult,
    )

    _TEMPLATES_AVAILABLE = True
except ImportError:
    _TEMPLATES_AVAILABLE = False

# Base exports that are always available
__all__ = [
    # LLM Models
    "AzureOpenAIConfig",
    "CompletionResponse",
    "CostReport",
    "DesignDocument",
    "DocumentType",
    "EmbeddingResponse",
    # Language Pattern Models
    "FrameworkPatterns",
    "GeminiConfig",
    "IndexMetadata",
    "LanguagePatterns",
    "LanguageProjectContext",
    "LLMOperationType",
    "LLMProvider",
    "PhaseStatus",
    # Enums
    "PhaseType",
    "Priority",
    # Project State
    "ProjectState",
    "Requirement",
    "SessionData",
    # Documents
    "SpecificationDocument",
    "SpecificationSource",
    "Task",
    "TaskList",
    "TaskStatus",
    "TokenUsage",
]

# Add optional exports if available
if _INDEXING_AVAILABLE:
    __all__.extend(
        [
            "ASTIndex",
            "ClassDef",
            "CodeChunk",
            "CodeMatch",
            "Embedding",
            "FunctionDef",
            "Import",
            "SymbolInfo",
        ]
    )

if _RESULTS_AVAILABLE:
    __all__.extend(
        [
            "DesignResult",
            "GeneratedCode",
            "ImplementationResult",
            "IndexResult",
            "IndexingResult",
            "PhaseResult",
            "SpecificationResult",
        ]
    )

if _CONTEXT_AVAILABLE:
    __all__.extend(
        [
            "ArchitectureInfo",
            "CodeContext",
            "CodeExample",
            "CodePatterns",
            "DesignAnalysis",
            "ProjectContext",
            "SpecificationAnalysis",
            "TaskProgress",
        ]
    )

if _VISUALIZATION_AVAILABLE:
    __all__.extend(
        [
            "ArchitectureVisualization",
            "ComponentVisualization",
            "DataFlowVisualization",
            "DependencyVisualization",
            "DiagramExportOptions",
            "DiagramMetadata",
            "DiagramTemplate",
            "DiagramType",
            "DiagramValidationResult",
            "ExportFormat",
            "FilterCriteria",
            "InteractiveDiagram",
            "MultiLanguageVisualization",
            "VisualizationConfig",
        ]
    )

if _TEMPLATES_AVAILABLE:
    __all__.extend(
        [
            "CustomizationPoint",
            "DirectoryTemplate",
            "FileTemplate",
            "ProjectSpec",
            "ProjectTemplate",
            "ScaffoldingResult",
            "TemplateContext",
            "TemplateRegistry",
            "TemplateValidationResult",
        ]
    )
