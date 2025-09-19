"""Core data models and enums for the dev-agent system."""

from .documents import (
    DesignDocument,
    Requirement,
    SpecificationDocument,
    Task,
    TaskList,
)
from .enums import (
    DocumentType,
    PhaseStatus,
    PhaseType,
    Priority,
    SpecificationSource,
    TaskStatus,
)
from .project_state import IndexMetadata, ProjectState, SessionData

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

# Base exports that are always available
__all__ = [
    # Enums
    "PhaseType",
    "PhaseStatus",
    "TaskStatus",
    "Priority",
    "DocumentType",
    "SpecificationSource",
    # Project State
    "ProjectState",
    "IndexMetadata",
    "SessionData",
    # Documents
    "SpecificationDocument",
    "DesignDocument",
    "TaskList",
    "Requirement",
    "Task",
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
