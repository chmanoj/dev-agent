"""Core data models and enums for the dev-agent system."""

from .enums import PhaseType, PhaseStatus, TaskStatus, Priority, DocumentType, SpecificationSource
from .project_state import ProjectState, IndexMetadata, SessionData
from .documents import SpecificationDocument, DesignDocument, TaskList, Requirement, Task

# Optional imports that may have external dependencies
try:
    from .indexing import CodeChunk, Embedding, CodeMatch, SymbolInfo, ASTIndex, FunctionDef, ClassDef, Import
    _INDEXING_AVAILABLE = True
except ImportError:
    _INDEXING_AVAILABLE = False

try:
    from .results import PhaseResult, IndexingResult, SpecificationResult, DesignResult, ImplementationResult, IndexResult, GeneratedCode
    _RESULTS_AVAILABLE = True
except ImportError:
    _RESULTS_AVAILABLE = False

try:
    from .context import ProjectContext, CodeContext, CodeExample, CodePatterns, SpecificationAnalysis, DesignAnalysis, ArchitectureInfo, TaskProgress
    _CONTEXT_AVAILABLE = True
except ImportError:
    _CONTEXT_AVAILABLE = False

# Base exports that are always available
__all__ = [
    # Enums
    'PhaseType', 'PhaseStatus', 'TaskStatus', 'Priority', 'DocumentType', 'SpecificationSource',
    # Project State
    'ProjectState', 'IndexMetadata', 'SessionData',
    # Documents
    'SpecificationDocument', 'DesignDocument', 'TaskList', 'Requirement', 'Task',
]

# Add optional exports if available
if _INDEXING_AVAILABLE:
    __all__.extend(['CodeChunk', 'Embedding', 'CodeMatch', 'SymbolInfo', 'ASTIndex', 'FunctionDef', 'ClassDef', 'Import'])

if _RESULTS_AVAILABLE:
    __all__.extend(['PhaseResult', 'IndexingResult', 'SpecificationResult', 'DesignResult', 'ImplementationResult', 'IndexResult', 'GeneratedCode'])

if _CONTEXT_AVAILABLE:
    __all__.extend(['ProjectContext', 'CodeContext', 'CodeExample', 'CodePatterns', 'SpecificationAnalysis', 'DesignAnalysis', 'ArchitectureInfo', 'TaskProgress'])