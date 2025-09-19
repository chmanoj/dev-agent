"""Custom exception classes for dev-agent system."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ErrorSeverity(Enum):
    """Error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""

    INDEXING = "indexing"
    USER_INPUT = "user_input"
    SYSTEM = "system"
    IMPLEMENTATION = "implementation"
    PERFORMANCE = "performance"
    STATE = "state"
    TIMEOUT = "timeout"


@dataclass
class ErrorContext:
    """Context information for errors."""

    operation: str
    file_path: str | None = None
    phase: str | None = None
    additional_info: dict[str, Any] | None = None


class DevAgentError(Exception):
    """Base exception class for all dev-agent errors."""

    def __init__(
        self,
        message: str,
        category: ErrorCategory,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: ErrorContext | None = None,
        recoverable: bool = True,
        user_message: str | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.context = context
        self.recoverable = recoverable
        self.user_message = user_message or self._generate_user_message()

    def _generate_user_message(self) -> str:
        """Generate a user-friendly error message."""
        return f"An error occurred: {self.message}"

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for logging/serialization."""
        return {
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "recoverable": self.recoverable,
            "user_message": self.user_message,
            "context": {
                "operation": self.context.operation if self.context else None,
                "file_path": self.context.file_path if self.context else None,
                "phase": self.context.phase if self.context else None,
                "additional_info": self.context.additional_info
                if self.context
                else None,
            },
        }


class IndexingError(DevAgentError):
    """Errors related to codebase indexing operations."""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.HIGH,
        context: ErrorContext | None = None,
        failed_files: list[str] | None = None,
        partial_success: bool = False,
    ):
        self.failed_files = failed_files or []
        self.partial_success = partial_success
        super().__init__(
            message=message,
            category=ErrorCategory.INDEXING,
            severity=severity,
            context=context,
            recoverable=True,
        )

    def _generate_user_message(self) -> str:
        if self.partial_success:
            return (
                f"Indexing completed with some issues: {self.message}. "
                f"The system can continue with partial results."
            )
        return (
            f"Indexing failed: {self.message}. "
            f"Please check the project structure and try again."
        )


class UserInputError(DevAgentError):
    """Errors related to user input validation and processing."""

    def __init__(
        self,
        message: str,
        expected_input: str | None = None,
        received_input: str | None = None,
        context: ErrorContext | None = None,
    ):
        self.expected_input = expected_input
        self.received_input = received_input
        super().__init__(
            message=message,
            category=ErrorCategory.USER_INPUT,
            severity=ErrorSeverity.LOW,
            context=context,
            recoverable=True,
        )

    def _generate_user_message(self) -> str:
        if self.expected_input:
            return (
                f"Invalid input: {self.message}. "
                f"Expected: {self.expected_input}. Please try again."
            )
        return f"Invalid input: {self.message}. Please try again."


class SystemError(DevAgentError):
    """Errors related to system operations (file I/O, permissions, etc.)."""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.HIGH,
        context: ErrorContext | None = None,
        system_errno: int | None = None,
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.SYSTEM,
            severity=severity,
            context=context,
            recoverable=severity != ErrorSeverity.CRITICAL,
        )
        self.system_errno = system_errno

    def _generate_user_message(self) -> str:
        return (
            f"System error: {self.message}. "
            f"Please check file permissions and disk space."
        )


class ImplementationError(DevAgentError):
    """Errors related to code generation and implementation."""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: ErrorContext | None = None,
        syntax_errors: list[str] | None = None,
        import_errors: list[str] | None = None,
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.IMPLEMENTATION,
            severity=severity,
            context=context,
            recoverable=True,
        )
        self.syntax_errors = syntax_errors or []
        self.import_errors = import_errors or []

    def _generate_user_message(self) -> str:
        return (
            f"Code generation error: {self.message}. "
            f"The generated code will be reviewed and corrected."
        )


class PerformanceError(DevAgentError):
    """Errors related to performance issues and resource constraints."""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: ErrorContext | None = None,
        memory_usage_mb: float | None = None,
        execution_time_seconds: float | None = None,
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.PERFORMANCE,
            severity=severity,
            context=context,
            recoverable=True,
        )
        self.memory_usage_mb = memory_usage_mb
        self.execution_time_seconds = execution_time_seconds

    def _generate_user_message(self) -> str:
        return (
            f"Performance issue: {self.message}. "
            f"The system will attempt to optimize resource usage."
        )


class StateCorruptionError(DevAgentError):
    """Errors related to corrupted or invalid state data."""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.HIGH,
        context: ErrorContext | None = None,
        corrupted_files: list[str] | None = None,
        backup_available: bool = False,
    ):
        self.corrupted_files = corrupted_files or []
        self.backup_available = backup_available
        super().__init__(
            message=message,
            category=ErrorCategory.STATE,
            severity=severity,
            context=context,
            recoverable=backup_available,
        )

    def _generate_user_message(self) -> str:
        if self.backup_available:
            return (
                f"State corruption detected: {self.message}. "
                f"The system will attempt to restore from backup."
            )
        return (
            f"State corruption detected: {self.message}. "
            f"You may need to reinitialize the project."
        )


class TimeoutError(DevAgentError):
    """Errors related to operation timeouts."""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: ErrorContext | None = None,
        timeout_seconds: float | None = None,
        operation_type: str | None = None,
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.TIMEOUT,
            severity=severity,
            context=context,
            recoverable=True,
        )
        self.timeout_seconds = timeout_seconds
        self.operation_type = operation_type

    def _generate_user_message(self) -> str:
        return (
            f"Operation timed out: {self.message}. "
            f"The system will retry with optimized settings."
        )


class ConfigurationError(DevAgentError):
    """Errors related to configuration issues."""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.HIGH,
        context: ErrorContext | None = None,
        config_key: str | None = None,
        expected_value: str | None = None,
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.SYSTEM,
            severity=severity,
            context=context,
            recoverable=True,
        )
        self.config_key = config_key
        self.expected_value = expected_value

    def _generate_user_message(self) -> str:
        return (
            f"Configuration error: {self.message}. "
            f"Please check your configuration settings."
        )


class ServiceError(DevAgentError):
    """Errors related to external service operations."""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.HIGH,
        context: ErrorContext | None = None,
        service_name: str | None = None,
        status_code: int | None = None,
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.SYSTEM,
            severity=severity,
            context=context,
            recoverable=True,
        )
        self.service_name = service_name
        self.status_code = status_code

    def _generate_user_message(self) -> str:
        return (
            f"Service error: {self.message}. "
            f"Please check your network connection and service configuration."
        )


class GenerationError(DevAgentError):
    """Errors related to AI-powered generation operations."""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: ErrorContext | None = None,
        generation_type: str | None = None,
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.IMPLEMENTATION,
            severity=severity,
            context=context,
            recoverable=True,
        )
        self.generation_type = generation_type

    def _generate_user_message(self) -> str:
        return (
            f"Generation error: {self.message}. "
            f"The system will attempt to use fallback generation methods."
        )
