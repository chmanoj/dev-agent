"""Error handling module for dev-agent system."""

from .error_handler import ErrorHandler
from .exceptions import (
    DevAgentError,
    IndexingError,
    UserInputError,
    SystemError,
    ImplementationError,
    PerformanceError,
    StateCorruptionError,
    TimeoutError,
    ErrorSeverity,
    ErrorCategory,
    ErrorContext,
)
from .recovery import (
    IndexingRecoveryAction,
    UserFeedback,
    SystemRecoveryAction,
    ImplementationFix,
    PerformanceOptimization,
    RecoveryActionType,
)

__all__ = [
    'ErrorHandler',
    'DevAgentError',
    'IndexingError',
    'UserInputError',
    'SystemError',
    'ImplementationError',
    'PerformanceError',
    'StateCorruptionError',
    'TimeoutError',
    'ErrorSeverity',
    'ErrorCategory',
    'ErrorContext',
    'IndexingRecoveryAction',
    'UserFeedback',
    'SystemRecoveryAction',
    'ImplementationFix',
    'PerformanceOptimization',
    'RecoveryActionType',
]