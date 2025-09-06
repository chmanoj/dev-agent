"""Base interfaces for all major components."""

from .cli_interface import ICLIInterface
from .workflow_interface import IWorkflowManager, IPhaseManager
from .state_interface import IStateManager
from .indexing_interface import IIndexingEngine, ITreeSitterParser, IVectorDatabase
from .analysis_interface import ICodebaseAnalyzer
from .generation_interface import ISpecificationGenerator, IDesignGenerator, ITaskGenerator, IPythonCodeGenerator

__all__ = [
    'ICLIInterface',
    'IWorkflowManager', 'IPhaseManager',
    'IStateManager',
    'IIndexingEngine', 'ITreeSitterParser', 'IVectorDatabase',
    'ICodebaseAnalyzer',
    'ISpecificationGenerator', 'IDesignGenerator', 'ITaskGenerator', 'IPythonCodeGenerator'
]