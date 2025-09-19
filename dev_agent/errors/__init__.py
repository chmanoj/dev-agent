"""Error handling module for dev-agent system."""

from .error_handler import ErrorHandler
from .exceptions import (
    DevAgentError,
    ErrorCategory,
    ErrorContext,
    ErrorSeverity,
    ImplementationError,
    IndexingError,
    PerformanceError,
    StateCorruptionError,
    SystemError,
    TimeoutError,
    UserInputError,
)
from .recovery import (
    ImplementationFix,
    IndexingRecoveryAction,
    PerformanceOptimization,
    RecoveryActionType,
    SystemRecoveryAction,
    UserFeedback,
)

__all__ = [
    "DevAgentError",
    "ErrorCategory",
    "ErrorContext",
    "ErrorHandler",
    "ErrorSeverity",
    "ImplementationError",
    "ImplementationFix",
    "IndexingError",
    "IndexingRecoveryAction",
    "PerformanceError",
    "PerformanceOptimization",
    "RecoveryActionType",
    "StateCorruptionError",
    "SystemError",
    "SystemRecoveryAction",
    "TimeoutError",
    "UserFeedback",
    "UserInputError",
]
