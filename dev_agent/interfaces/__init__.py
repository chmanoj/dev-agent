"""Base interfaces for all major components."""

from .analysis_interface import ICodebaseAnalyzer
from .cli_interface import ICLIInterface
from .generation_interface import (
    IDesignGenerator,
    IPythonCodeGenerator,
    ISpecificationGenerator,
    ITaskGenerator,
)
from .indexing_interface import IIndexingEngine, ITreeSitterParser, IVectorDatabase
from .state_interface import IStateManager
from .workflow_interface import IPhaseManager, IWorkflowManager

__all__ = [
    "ICLIInterface",
    "ICodebaseAnalyzer",
    "IDesignGenerator",
    "IIndexingEngine",
    "IPhaseManager",
    "IPythonCodeGenerator",
    "ISpecificationGenerator",
    "IStateManager",
    "ITaskGenerator",
    "ITreeSitterParser",
    "IVectorDatabase",
    "IWorkflowManager",
]
