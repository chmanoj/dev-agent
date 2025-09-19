"""Main error handler for dev-agent system."""

import logging
import time
import traceback
from collections.abc import Callable
from typing import Any

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
    RecoveryAction,
    RecoveryActionType,
    SystemRecoveryAction,
    UserFeedback,
)


class ErrorHandler:
    """Comprehensive error handler for dev-agent system."""

    def __init__(
        self, project_path: str | None = None, logger: logging.Logger | None = None
    ):
        self.project_path = project_path
        self.logger = logger or self._setup_logger()
        self.error_history: list[dict[str, Any]] = []
        self.recovery_strategies: dict[ErrorCategory, list[Callable]] = (
            self._setup_recovery_strategies()
        )
        self.timeout_handlers: dict[str, float] = {}
        self.performance_thresholds = {
            "memory_mb": 1024,  # 1GB memory threshold
            "execution_seconds": 300,  # 5 minute execution threshold
            "file_size_mb": 100,  # 100MB file size threshold
        }

    def _setup_logger(self) -> logging.Logger:
        """Set up error logging."""
        logger = logging.getLogger("dev_agent.errors")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _setup_recovery_strategies(self) -> dict[ErrorCategory, list[Callable]]:
        """Set up recovery strategies for each error category."""
        return {
            ErrorCategory.INDEXING: [
                self._create_indexing_fallback_strategy,
                self._create_indexing_retry_strategy,
                self._create_indexing_optimization_strategy,
            ],
            ErrorCategory.USER_INPUT: [
                self._create_user_input_retry_strategy,
                self._create_user_input_guidance_strategy,
            ],
            ErrorCategory.SYSTEM: [
                self._create_system_recovery_strategy,
                self._create_system_fallback_strategy,
            ],
            ErrorCategory.IMPLEMENTATION: [
                self._create_implementation_fix_strategy,
                self._create_implementation_regeneration_strategy,
            ],
            ErrorCategory.PERFORMANCE: [
                self._create_performance_optimization_strategy,
                self._create_performance_fallback_strategy,
            ],
            ErrorCategory.STATE: [
                self._create_state_recovery_strategy,
                self._create_state_backup_strategy,
            ],
            ErrorCategory.TIMEOUT: [
                self._create_timeout_retry_strategy,
                self._create_timeout_optimization_strategy,
            ],
        }

    def handle_error(self, error: Exception | DevAgentError) -> RecoveryAction | None:
        """Main error handling entry point."""
        try:
            # Convert standard exceptions to DevAgentError if needed
            if not isinstance(error, DevAgentError):
                error = self._convert_to_dev_agent_error(error)

            # Log the error
            self._log_error(error)

            # Add to error history
            self._add_to_history(error)

            # Determine recovery action
            recovery_action = self._determine_recovery_action(error)

            # Execute automatic recovery if possible
            if recovery_action and recovery_action.automatic:
                success = self._execute_recovery_action(recovery_action)
                if success:
                    self.logger.info(
                        f"Automatic recovery successful for {error.category.value} error"
                    )
                else:
                    self.logger.warning(
                        f"Automatic recovery failed for {error.category.value} error"
                    )

            return recovery_action

        except Exception as e:
            self.logger.critical(f"Error in error handler: {e!s}")
            return None

    def handle_indexing_error(self, error: IndexingError) -> IndexingRecoveryAction:
        """Handle indexing-specific errors with graceful degradation."""
        self.logger.error(f"Indexing error: {error.message}")

        if error.partial_success:
            # Use partial index and continue
            return IndexingRecoveryAction(
                action_type=RecoveryActionType.FALLBACK,
                description="Using partial index due to indexing issues",
                use_partial_index=True,
                automatic=True,
                user_message="Indexing completed with some issues. Continuing with partial results.",
            )

        if error.failed_files:
            # Skip failed files and retry
            return IndexingRecoveryAction(
                action_type=RecoveryActionType.RETRY,
                description="Retrying indexing while skipping problematic files",
                failed_files=error.failed_files,
                skip_large_files=True,
                automatic=True,
                user_message="Retrying indexing while skipping problematic files.",
            )

        # Optimize memory usage and retry
        return IndexingRecoveryAction(
            action_type=RecoveryActionType.OPTIMIZE,
            description="Optimizing memory usage and retrying indexing",
            reduce_memory_usage=True,
            chunk_size_reduction=0.5,
            automatic=True,
            user_message="Optimizing indexing process and retrying.",
        )

    def handle_user_input_error(self, error: UserInputError) -> UserFeedback:
        """Handle user input errors with helpful guidance."""
        self.logger.warning(f"User input error: {error.message}")

        prompt_message = error.user_message
        if error.expected_input:
            prompt_message += f" Expected input: {error.expected_input}"

        return UserFeedback(
            description="Request user to provide valid input",
            prompt_message=prompt_message,
            expected_responses=error.expected_input.split("|")
            if error.expected_input
            else None,
            retry_on_invalid=True,
            max_retries=3,
        )

    def handle_system_error(self, error: SystemError) -> SystemRecoveryAction:
        """Handle system errors with recovery mechanisms."""
        self.logger.error(f"System error: {error.message}")

        if "permission" in error.message.lower():
            return SystemRecoveryAction(
                action_type=RecoveryActionType.RETRY,
                description="Checking and fixing file permissions",
                check_permissions=True,
                automatic=True,
                user_message="Checking file permissions and attempting to fix issues.",
            )

        if "directory" in error.message.lower() or "path" in error.message.lower():
            return SystemRecoveryAction(
                action_type=RecoveryActionType.RETRY,
                description="Creating required directories",
                create_directories=True,
                automatic=True,
                user_message="Creating required directories and retrying operation.",
            )

        if "space" in error.message.lower() or "disk" in error.message.lower():
            return SystemRecoveryAction(
                action_type=RecoveryActionType.FALLBACK,
                description="Cleaning up temporary files and checking disk space",
                cleanup_temp_files=True,
                verify_disk_space=True,
                automatic=True,
                user_message="Cleaning up temporary files to free disk space.",
            )

        return SystemRecoveryAction(
            action_type=RecoveryActionType.USER_INTERVENTION,
            description="System error requires manual intervention",
            automatic=False,
            user_message=error.user_message,
        )

    def handle_implementation_error(
        self, error: ImplementationError
    ) -> ImplementationFix:
        """Handle implementation errors with code fixes."""
        self.logger.error(f"Implementation error: {error.message}")

        if error.syntax_errors:
            return ImplementationFix(
                action_type=RecoveryActionType.RETRY,
                description="Fixing syntax errors in generated code",
                fix_syntax_errors=True,
                validate_generated_code=True,
                automatic=True,
                user_message="Fixing syntax errors in generated code.",
            )

        if error.import_errors:
            return ImplementationFix(
                action_type=RecoveryActionType.RETRY,
                description="Fixing import errors in generated code",
                fix_import_errors=True,
                validate_generated_code=True,
                automatic=True,
                user_message="Fixing import statements in generated code.",
            )

        return ImplementationFix(
            action_type=RecoveryActionType.FALLBACK,
            description="Regenerating code with fallback template",
            regenerate_code=True,
            use_fallback_template=True,
            automatic=True,
            user_message="Regenerating code using a more conservative approach.",
        )

    def handle_performance_error(
        self, error: PerformanceError
    ) -> PerformanceOptimization:
        """Handle performance errors with optimization strategies."""
        self.logger.warning(f"Performance error: {error.message}")

        optimizations = PerformanceOptimization(
            action_type=RecoveryActionType.OPTIMIZE,
            description="Applying performance optimizations",
            automatic=True,
            user_message="Optimizing performance and retrying operation.",
        )

        if (
            error.memory_usage_mb
            and error.memory_usage_mb > self.performance_thresholds["memory_mb"]
        ):
            optimizations.reduce_memory_usage = True
            optimizations.use_chunked_processing = True

        if (
            error.execution_time_seconds
            and error.execution_time_seconds
            > self.performance_thresholds["execution_seconds"]
        ):
            optimizations.increase_timeout = True
            optimizations.reduce_batch_size = True

        optimizations.enable_caching = True

        return optimizations

    def handle_state_corruption_error(
        self, error: StateCorruptionError
    ) -> SystemRecoveryAction:
        """Handle state corruption with backup recovery."""
        self.logger.error(f"State corruption error: {error.message}")

        if error.backup_available:
            return SystemRecoveryAction(
                action_type=RecoveryActionType.RESTART,
                description="Restoring from backup due to state corruption",
                backup_files=error.corrupted_files,
                automatic=True,
                user_message="Restoring project state from backup.",
            )

        return SystemRecoveryAction(
            action_type=RecoveryActionType.USER_INTERVENTION,
            description="State corruption requires manual intervention",
            automatic=False,
            user_message=(
                "Project state is corrupted and no backup is available. "
                "You may need to reinitialize the project."
            ),
        )

    def handle_timeout_error(self, error: TimeoutError) -> PerformanceOptimization:
        """Handle timeout errors with retry and optimization."""
        self.logger.warning(f"Timeout error: {error.message}")

        return PerformanceOptimization(
            action_type=RecoveryActionType.RETRY,
            description="Retrying with increased timeout and optimizations",
            increase_timeout=True,
            reduce_batch_size=True,
            use_chunked_processing=True,
            automatic=True,
            user_message="Retrying operation with increased timeout and optimizations.",
        )

    def set_timeout_handler(self, operation: str, timeout_seconds: float) -> None:
        """Set timeout for long-running operations."""
        self.timeout_handlers[operation] = timeout_seconds

    def check_timeout(self, operation: str, start_time: float) -> bool:
        """Check if operation has timed out."""
        if operation not in self.timeout_handlers:
            return False

        elapsed = time.time() - start_time
        return elapsed > self.timeout_handlers[operation]

    def create_timeout_context(self, operation: str, timeout_seconds: float):
        """Create a timeout context manager."""
        return TimeoutContext(self, operation, timeout_seconds)

    def get_error_statistics(self) -> dict[str, Any]:
        """Get error statistics for monitoring."""
        if not self.error_history:
            return {}

        stats = {
            "total_errors": len(self.error_history),
            "by_category": {},
            "by_severity": {},
            "recent_errors": self.error_history[-10:]
            if len(self.error_history) > 10
            else self.error_history,
        }

        for error_record in self.error_history:
            category = error_record.get("category", "unknown")
            severity = error_record.get("severity", "unknown")

            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
            stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1

        return stats

    def clear_error_history(self) -> None:
        """Clear error history."""
        self.error_history.clear()

    def _convert_to_dev_agent_error(self, error: Exception) -> DevAgentError:
        """Convert standard exceptions to DevAgentError."""
        if isinstance(error, FileNotFoundError):
            return SystemError(
                message=f"File not found: {error!s}",
                context=ErrorContext(operation="file_access"),
                severity=ErrorSeverity.HIGH,
            )
        elif isinstance(error, PermissionError):
            return SystemError(
                message=f"Permission denied: {error!s}",
                context=ErrorContext(operation="file_access"),
                severity=ErrorSeverity.HIGH,
            )
        elif isinstance(error, MemoryError):
            return PerformanceError(
                message=f"Memory error: {error!s}",
                context=ErrorContext(operation="memory_allocation"),
                severity=ErrorSeverity.CRITICAL,
            )
        elif isinstance(error, TimeoutError):
            return TimeoutError(
                message=f"Operation timed out: {error!s}",
                context=ErrorContext(operation="timeout"),
                severity=ErrorSeverity.MEDIUM,
            )
        else:
            return DevAgentError(
                message=str(error),
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.MEDIUM,
                context=ErrorContext(operation="unknown"),
            )

    def _log_error(self, error: DevAgentError) -> None:
        """Log error with appropriate level."""
        log_message = f"{error.category.value.upper()}: {error.message}"

        if error.context:
            log_message += f" (Operation: {error.context.operation}"
            if error.context.file_path:
                log_message += f", File: {error.context.file_path}"
            if error.context.phase:
                log_message += f", Phase: {error.context.phase}"
            log_message += ")"

        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

    def _add_to_history(self, error: DevAgentError) -> None:
        """Add error to history for tracking."""
        error_record = error.to_dict()
        error_record["timestamp"] = time.time()
        error_record["traceback"] = traceback.format_exc()
        self.error_history.append(error_record)

        # Keep only last 100 errors to prevent memory issues
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-100:]

    def _determine_recovery_action(self, error: DevAgentError) -> RecoveryAction | None:
        """Determine appropriate recovery action for error."""
        strategies = self.recovery_strategies.get(error.category, [])

        for strategy_func in strategies:
            try:
                recovery_action = strategy_func(error)
                if recovery_action:
                    return recovery_action
            except Exception as e:
                self.logger.warning(f"Recovery strategy failed: {e!s}")

        return None

    def _execute_recovery_action(self, recovery_action: RecoveryAction) -> bool:
        """Execute a recovery action."""
        try:
            return recovery_action.execute()
        except Exception as e:
            self.logger.error(f"Failed to execute recovery action: {e!s}")
            return False

    # Recovery strategy creation methods
    def _create_indexing_fallback_strategy(
        self, error: DevAgentError
    ) -> IndexingRecoveryAction | None:
        """Create indexing fallback strategy."""
        if isinstance(error, IndexingError):
            return self.handle_indexing_error(error)
        return None

    def _create_indexing_retry_strategy(
        self, error: DevAgentError
    ) -> IndexingRecoveryAction | None:
        """Create indexing retry strategy."""
        if isinstance(error, IndexingError) and not error.partial_success:
            return IndexingRecoveryAction(
                action_type=RecoveryActionType.RETRY,
                description="Retrying indexing with reduced parameters",
                reduce_memory_usage=True,
                skip_large_files=True,
                automatic=True,
            )
        return None

    def _create_indexing_optimization_strategy(
        self, error: DevAgentError
    ) -> IndexingRecoveryAction | None:
        """Create indexing optimization strategy."""
        if isinstance(error, IndexingError):
            return IndexingRecoveryAction(
                action_type=RecoveryActionType.OPTIMIZE,
                description="Optimizing indexing process",
                reduce_memory_usage=True,
                chunk_size_reduction=0.3,
                automatic=True,
            )
        return None

    def _create_user_input_retry_strategy(
        self, error: DevAgentError
    ) -> UserFeedback | None:
        """Create user input retry strategy."""
        if isinstance(error, UserInputError):
            return self.handle_user_input_error(error)
        return None

    def _create_user_input_guidance_strategy(
        self, error: DevAgentError
    ) -> UserFeedback | None:
        """Create user input guidance strategy."""
        if isinstance(error, UserInputError):
            return UserFeedback(
                description="Providing guidance for user input",
                prompt_message=f"Invalid input. {error.user_message}",
                retry_on_invalid=True,
                max_retries=5,
            )
        return None

    def _create_system_recovery_strategy(
        self, error: DevAgentError
    ) -> SystemRecoveryAction | None:
        """Create system recovery strategy."""
        if isinstance(error, SystemError):
            return self.handle_system_error(error)
        return None

    def _create_system_fallback_strategy(
        self, error: DevAgentError
    ) -> SystemRecoveryAction | None:
        """Create system fallback strategy."""
        if isinstance(error, SystemError):
            return SystemRecoveryAction(
                action_type=RecoveryActionType.FALLBACK,
                description="Using fallback system operations",
                create_directories=True,
                cleanup_temp_files=True,
                automatic=True,
            )
        return None

    def _create_implementation_fix_strategy(
        self, error: DevAgentError
    ) -> ImplementationFix | None:
        """Create implementation fix strategy."""
        if isinstance(error, ImplementationError):
            return self.handle_implementation_error(error)
        return None

    def _create_implementation_regeneration_strategy(
        self, error: DevAgentError
    ) -> ImplementationFix | None:
        """Create implementation regeneration strategy."""
        if isinstance(error, ImplementationError):
            return ImplementationFix(
                action_type=RecoveryActionType.RETRY,
                description="Regenerating implementation with different approach",
                regenerate_code=True,
                use_fallback_template=True,
                automatic=True,
            )
        return None

    def _create_performance_optimization_strategy(
        self, error: DevAgentError
    ) -> PerformanceOptimization | None:
        """Create performance optimization strategy."""
        if isinstance(error, PerformanceError):
            return self.handle_performance_error(error)
        return None

    def _create_performance_fallback_strategy(
        self, error: DevAgentError
    ) -> PerformanceOptimization | None:
        """Create performance fallback strategy."""
        if isinstance(error, PerformanceError):
            return PerformanceOptimization(
                action_type=RecoveryActionType.FALLBACK,
                description="Using performance fallback strategies",
                reduce_memory_usage=True,
                use_chunked_processing=True,
                skip_expensive_operations=True,
                automatic=True,
            )
        return None

    def _create_state_recovery_strategy(
        self, error: DevAgentError
    ) -> SystemRecoveryAction | None:
        """Create state recovery strategy."""
        if isinstance(error, StateCorruptionError):
            return self.handle_state_corruption_error(error)
        return None

    def _create_state_backup_strategy(
        self, error: DevAgentError
    ) -> SystemRecoveryAction | None:
        """Create state backup strategy."""
        if isinstance(error, StateCorruptionError):
            return SystemRecoveryAction(
                action_type=RecoveryActionType.RESTART,
                description="Creating backup and reinitializing state",
                backup_files=error.corrupted_files
                if hasattr(error, "corrupted_files")
                else [],
                automatic=False,
                user_message="Creating backup before reinitializing project state.",
            )
        return None

    def _create_timeout_retry_strategy(
        self, error: DevAgentError
    ) -> PerformanceOptimization | None:
        """Create timeout retry strategy."""
        if isinstance(error, TimeoutError):
            return self.handle_timeout_error(error)
        return None

    def _create_timeout_optimization_strategy(
        self, error: DevAgentError
    ) -> PerformanceOptimization | None:
        """Create timeout optimization strategy."""
        if isinstance(error, TimeoutError):
            return PerformanceOptimization(
                action_type=RecoveryActionType.OPTIMIZE,
                description="Optimizing operation to prevent timeout",
                increase_timeout=True,
                reduce_batch_size=True,
                use_chunked_processing=True,
                enable_caching=True,
                automatic=True,
            )
        return None


class TimeoutContext:
    """Context manager for timeout handling."""

    def __init__(
        self, error_handler: ErrorHandler, operation: str, timeout_seconds: float
    ):
        self.error_handler = error_handler
        self.operation = operation
        self.timeout_seconds = timeout_seconds
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        self.error_handler.set_timeout_handler(self.operation, self.timeout_seconds)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time and self.error_handler.check_timeout(
            self.operation, self.start_time
        ):
            raise TimeoutError(
                message=f"Operation '{self.operation}' timed out after {self.timeout_seconds} seconds",
                timeout_seconds=self.timeout_seconds,
                operation_type=self.operation,
            )

    def check_timeout(self) -> bool:
        """Check if operation has timed out."""
        if self.start_time:
            return self.error_handler.check_timeout(self.operation, self.start_time)
        return False
