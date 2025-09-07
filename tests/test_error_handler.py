"""Tests for error handling system."""

import tempfile
import time

import pytest

from dev_agent.errors import (
    DevAgentError,
    ErrorCategory,
    ErrorContext,
    ErrorHandler,
    ErrorSeverity,
    ImplementationError,
    ImplementationFix,
    IndexingError,
    IndexingRecoveryAction,
    PerformanceError,
    PerformanceOptimization,
    RecoveryActionType,
    StateCorruptionError,
    SystemError,
    SystemRecoveryAction,
    TimeoutError,
    UserFeedback,
    UserInputError,
)


class TestErrorHandler:
    """Test cases for ErrorHandler class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.error_handler = ErrorHandler(project_path=self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_error_handler_initialization(self):
        """Test ErrorHandler initialization."""
        assert self.error_handler.project_path == self.temp_dir
        assert self.error_handler.logger is not None
        assert len(self.error_handler.error_history) == 0
        assert len(self.error_handler.recovery_strategies) > 0

    def test_handle_indexing_error_with_partial_success(self):
        """Test handling indexing error with partial success."""
        error = IndexingError(
            message="Some files failed to index",
            partial_success=True,
            failed_files=["file1.py", "file2.py"]
        )

        recovery_action = self.error_handler.handle_indexing_error(error)

        assert isinstance(recovery_action, IndexingRecoveryAction)
        assert recovery_action.action_type == RecoveryActionType.FALLBACK
        assert recovery_action.use_partial_index is True
        assert recovery_action.automatic is True

    def test_handle_indexing_error_with_failed_files(self):
        """Test handling indexing error with failed files."""
        error = IndexingError(
            message="Failed to index large files",
            partial_success=False,
            failed_files=["large_file1.py", "large_file2.py"]
        )

        recovery_action = self.error_handler.handle_indexing_error(error)

        assert isinstance(recovery_action, IndexingRecoveryAction)
        assert recovery_action.action_type == RecoveryActionType.RETRY
        assert recovery_action.failed_files == ["large_file1.py", "large_file2.py"]
        assert recovery_action.skip_large_files is True

    def test_handle_indexing_error_memory_optimization(self):
        """Test handling indexing error with memory optimization."""
        error = IndexingError(
            message="Memory exhausted during indexing",
            partial_success=False
        )

        recovery_action = self.error_handler.handle_indexing_error(error)

        assert isinstance(recovery_action, IndexingRecoveryAction)
        assert recovery_action.action_type == RecoveryActionType.OPTIMIZE
        assert recovery_action.reduce_memory_usage is True
        assert recovery_action.chunk_size_reduction == 0.5

    def test_handle_user_input_error(self):
        """Test handling user input error."""
        error = UserInputError(
            message="Invalid response",
            expected_input="y|n|yes|no",
            received_input="maybe"
        )

        recovery_action = self.error_handler.handle_user_input_error(error)

        assert isinstance(recovery_action, UserFeedback)
        assert recovery_action.action_type == RecoveryActionType.USER_INTERVENTION
        assert recovery_action.retry_on_invalid is True
        assert recovery_action.max_retries == 3

    def test_handle_system_error_permission(self):
        """Test handling system error with permission issues."""
        error = SystemError(
            message="Permission denied accessing file",
            context=ErrorContext(operation="file_write", file_path="/test/file.py")
        )

        recovery_action = self.error_handler.handle_system_error(error)

        assert isinstance(recovery_action, SystemRecoveryAction)
        assert recovery_action.action_type == RecoveryActionType.RETRY
        assert recovery_action.check_permissions is True

    def test_handle_system_error_directory(self):
        """Test handling system error with directory issues."""
        error = SystemError(
            message="Directory does not exist",
            context=ErrorContext(operation="directory_access")
        )

        recovery_action = self.error_handler.handle_system_error(error)

        assert isinstance(recovery_action, SystemRecoveryAction)
        assert recovery_action.action_type == RecoveryActionType.RETRY
        assert recovery_action.create_directories is True

    def test_handle_system_error_disk_space(self):
        """Test handling system error with disk space issues."""
        error = SystemError(
            message="No space left on device",
            context=ErrorContext(operation="file_write")
        )

        recovery_action = self.error_handler.handle_system_error(error)

        assert isinstance(recovery_action, SystemRecoveryAction)
        assert recovery_action.action_type == RecoveryActionType.FALLBACK
        assert recovery_action.cleanup_temp_files is True
        assert recovery_action.verify_disk_space is True

    def test_handle_implementation_error_syntax(self):
        """Test handling implementation error with syntax issues."""
        error = ImplementationError(
            message="Syntax error in generated code",
            syntax_errors=["Missing colon on line 5", "Indentation error on line 10"]
        )

        recovery_action = self.error_handler.handle_implementation_error(error)

        assert isinstance(recovery_action, ImplementationFix)
        assert recovery_action.action_type == RecoveryActionType.RETRY
        assert recovery_action.fix_syntax_errors is True
        assert recovery_action.validate_generated_code is True

    def test_handle_implementation_error_imports(self):
        """Test handling implementation error with import issues."""
        error = ImplementationError(
            message="Import error in generated code",
            import_errors=["Module 'nonexistent' not found"]
        )

        recovery_action = self.error_handler.handle_implementation_error(error)

        assert isinstance(recovery_action, ImplementationFix)
        assert recovery_action.action_type == RecoveryActionType.RETRY
        assert recovery_action.fix_import_errors is True

    def test_handle_performance_error_memory(self):
        """Test handling performance error with memory issues."""
        error = PerformanceError(
            message="High memory usage detected",
            memory_usage_mb=2048,  # Above threshold
            execution_time_seconds=100
        )

        recovery_action = self.error_handler.handle_performance_error(error)

        assert isinstance(recovery_action, PerformanceOptimization)
        assert recovery_action.action_type == RecoveryActionType.OPTIMIZE
        assert recovery_action.reduce_memory_usage is True
        assert recovery_action.use_chunked_processing is True

    def test_handle_performance_error_timeout(self):
        """Test handling performance error with timeout issues."""
        error = PerformanceError(
            message="Operation taking too long",
            execution_time_seconds=400,  # Above threshold
            memory_usage_mb=500
        )

        recovery_action = self.error_handler.handle_performance_error(error)

        assert isinstance(recovery_action, PerformanceOptimization)
        assert recovery_action.increase_timeout is True
        assert recovery_action.reduce_batch_size is True

    def test_handle_state_corruption_with_backup(self):
        """Test handling state corruption with backup available."""
        error = StateCorruptionError(
            message="State file corrupted",
            corrupted_files=["state.json"],
            backup_available=True
        )

        recovery_action = self.error_handler.handle_state_corruption_error(error)

        assert isinstance(recovery_action, SystemRecoveryAction)
        assert recovery_action.action_type == RecoveryActionType.RESTART
        assert recovery_action.backup_files == ["state.json"]
        assert recovery_action.automatic is True

    def test_handle_state_corruption_without_backup(self):
        """Test handling state corruption without backup."""
        error = StateCorruptionError(
            message="State file corrupted",
            corrupted_files=["state.json"],
            backup_available=False
        )

        recovery_action = self.error_handler.handle_state_corruption_error(error)

        assert isinstance(recovery_action, SystemRecoveryAction)
        assert recovery_action.action_type == RecoveryActionType.USER_INTERVENTION
        assert recovery_action.automatic is False

    def test_handle_timeout_error(self):
        """Test handling timeout error."""
        error = TimeoutError(
            message="Operation timed out",
            timeout_seconds=300,
            operation_type="indexing"
        )

        recovery_action = self.error_handler.handle_timeout_error(error)

        assert isinstance(recovery_action, PerformanceOptimization)
        assert recovery_action.action_type == RecoveryActionType.RETRY
        assert recovery_action.increase_timeout is True
        assert recovery_action.use_chunked_processing is True

    def test_convert_standard_exceptions(self):
        """Test conversion of standard exceptions to DevAgentError."""
        # Test FileNotFoundError
        file_error = FileNotFoundError("File not found")
        converted = self.error_handler._convert_to_dev_agent_error(file_error)
        assert isinstance(converted, SystemError)
        assert converted.category == ErrorCategory.SYSTEM

        # Test PermissionError
        perm_error = PermissionError("Permission denied")
        converted = self.error_handler._convert_to_dev_agent_error(perm_error)
        assert isinstance(converted, SystemError)

        # Test MemoryError
        mem_error = MemoryError("Out of memory")
        converted = self.error_handler._convert_to_dev_agent_error(mem_error)
        assert isinstance(converted, PerformanceError)
        assert converted.severity == ErrorSeverity.CRITICAL

    def test_error_history_tracking(self):
        """Test error history tracking."""
        error1 = DevAgentError("Test error 1", ErrorCategory.SYSTEM)
        error2 = DevAgentError("Test error 2", ErrorCategory.INDEXING)

        self.error_handler.handle_error(error1)
        self.error_handler.handle_error(error2)

        assert len(self.error_handler.error_history) == 2
        assert self.error_handler.error_history[0]["message"] == "Test error 1"
        assert self.error_handler.error_history[1]["message"] == "Test error 2"

    def test_error_statistics(self):
        """Test error statistics generation."""
        error1 = DevAgentError("Test error 1", ErrorCategory.SYSTEM, ErrorSeverity.HIGH)
        error2 = DevAgentError("Test error 2", ErrorCategory.INDEXING, ErrorSeverity.MEDIUM)
        error3 = DevAgentError("Test error 3", ErrorCategory.SYSTEM, ErrorSeverity.LOW)

        self.error_handler.handle_error(error1)
        self.error_handler.handle_error(error2)
        self.error_handler.handle_error(error3)

        stats = self.error_handler.get_error_statistics()

        assert stats["total_errors"] == 3
        assert stats["by_category"]["system"] == 2
        assert stats["by_category"]["indexing"] == 1
        assert stats["by_severity"]["high"] == 1
        assert stats["by_severity"]["medium"] == 1
        assert stats["by_severity"]["low"] == 1

    def test_timeout_context_manager(self):
        """Test timeout context manager."""
        with pytest.raises(TimeoutError):
            with self.error_handler.create_timeout_context("test_operation", 0.1):
                time.sleep(0.2)  # Sleep longer than timeout

    def test_timeout_context_manager_success(self):
        """Test timeout context manager with successful operation."""
        with self.error_handler.create_timeout_context("test_operation", 1.0):
            time.sleep(0.1)  # Sleep less than timeout
        # Should not raise exception

    def test_clear_error_history(self):
        """Test clearing error history."""
        error = DevAgentError("Test error", ErrorCategory.SYSTEM)
        self.error_handler.handle_error(error)

        assert len(self.error_handler.error_history) == 1

        self.error_handler.clear_error_history()

        assert len(self.error_handler.error_history) == 0

    def test_error_history_size_limit(self):
        """Test error history size limit."""
        # Add more than 100 errors
        for i in range(105):
            error = DevAgentError(f"Test error {i}", ErrorCategory.SYSTEM)
            self.error_handler.handle_error(error)

        # Should keep only last 100 errors
        assert len(self.error_handler.error_history) == 100
        assert self.error_handler.error_history[0]["message"] == "Test error 5"
        assert self.error_handler.error_history[-1]["message"] == "Test error 104"


class TestRecoveryActions:
    """Test cases for recovery action classes."""

    def test_indexing_recovery_action_fallback(self):
        """Test indexing recovery action fallback execution."""
        action = IndexingRecoveryAction(
            action_type=RecoveryActionType.FALLBACK,
            description="Use partial index",
            use_partial_index=True
        )

        result = action.execute()
        assert result is True

    def test_indexing_recovery_action_retry(self):
        """Test indexing recovery action retry execution."""
        action = IndexingRecoveryAction(
            action_type=RecoveryActionType.RETRY,
            description="Retry with failed files",
            failed_files=["file1.py", "file2.py"]
        )

        result = action.execute()
        assert result is True

    def test_indexing_recovery_action_optimize(self):
        """Test indexing recovery action optimize execution."""
        action = IndexingRecoveryAction(
            action_type=RecoveryActionType.OPTIMIZE,
            description="Optimize memory usage",
            reduce_memory_usage=True,
            skip_large_files=True
        )

        result = action.execute()
        assert result is True

    def test_user_feedback_validation(self):
        """Test user feedback response validation."""
        feedback = UserFeedback(
            description="Get user approval",
            prompt_message="Do you want to continue?",
            expected_responses=["y", "n", "yes", "no"]
        )

        assert feedback.validate_response("y") is True
        assert feedback.validate_response("YES") is True
        assert feedback.validate_response("maybe") is False
        assert feedback.validate_response("") is False

    def test_user_feedback_retry_logic(self):
        """Test user feedback retry logic."""
        feedback = UserFeedback(
            description="Get user approval",
            prompt_message="Do you want to continue?",
            max_retries=3
        )

        assert feedback.should_retry() is True

        feedback.current_retries = 3
        assert feedback.should_retry() is False

    def test_system_recovery_action_execution(self):
        """Test system recovery action execution."""
        action = SystemRecoveryAction(
            action_type=RecoveryActionType.RETRY,
            description="Fix system issues",
            create_directories=True,
            check_permissions=True,
            cleanup_temp_files=True,
            verify_disk_space=True
        )

        result = action.execute()
        assert result is True

    def test_implementation_fix_execution(self):
        """Test implementation fix execution."""
        fix = ImplementationFix(
            action_type=RecoveryActionType.RETRY,
            description="Fix code issues",
            fix_syntax_errors=True,
            fix_import_errors=True,
            validate_generated_code=True
        )

        result = fix.execute()
        assert result is True

    def test_performance_optimization_execution(self):
        """Test performance optimization execution."""
        optimization = PerformanceOptimization(
            action_type=RecoveryActionType.OPTIMIZE,
            description="Optimize performance",
            reduce_memory_usage=True,
            increase_timeout=True,
            use_chunked_processing=True,
            enable_caching=True,
            reduce_batch_size=True
        )

        result = optimization.execute()
        assert result is True


class TestErrorExceptions:
    """Test cases for error exception classes."""

    def test_dev_agent_error_creation(self):
        """Test DevAgentError creation and properties."""
        context = ErrorContext(
            operation="test_operation",
            file_path="/test/file.py",
            phase="indexing"
        )

        error = DevAgentError(
            message="Test error message",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.HIGH,
            context=context,
            recoverable=True
        )

        assert error.message == "Test error message"
        assert error.category == ErrorCategory.SYSTEM
        assert error.severity == ErrorSeverity.HIGH
        assert error.context == context
        assert error.recoverable is True
        assert "Test error message" in error.user_message

    def test_error_to_dict_conversion(self):
        """Test error to dictionary conversion."""
        context = ErrorContext(operation="test_op", file_path="/test.py")
        error = DevAgentError(
            message="Test error",
            category=ErrorCategory.INDEXING,
            severity=ErrorSeverity.MEDIUM,
            context=context
        )

        error_dict = error.to_dict()

        assert error_dict["message"] == "Test error"
        assert error_dict["category"] == "indexing"
        assert error_dict["severity"] == "medium"
        assert error_dict["recoverable"] is True
        assert error_dict["context"]["operation"] == "test_op"
        assert error_dict["context"]["file_path"] == "/test.py"

    def test_indexing_error_user_messages(self):
        """Test IndexingError user message generation."""
        # Test partial success message
        error1 = IndexingError(
            message="Some files failed",
            partial_success=True
        )
        assert "partial results" in error1.user_message.lower()

        # Test complete failure message
        error2 = IndexingError(
            message="Indexing failed completely",
            partial_success=False
        )
        assert "indexing failed" in error2.user_message.lower()

    def test_user_input_error_with_expected_input(self):
        """Test UserInputError with expected input."""
        error = UserInputError(
            message="Invalid choice",
            expected_input="y|n",
            received_input="maybe"
        )

        assert "Expected: y|n" in error.user_message
        assert "Invalid input" in error.user_message

    def test_performance_error_with_metrics(self):
        """Test PerformanceError with performance metrics."""
        error = PerformanceError(
            message="High resource usage",
            memory_usage_mb=2048,
            execution_time_seconds=300
        )

        assert error.memory_usage_mb == 2048
        assert error.execution_time_seconds == 300
        assert "performance issue" in error.user_message.lower()

    def test_state_corruption_error_with_backup(self):
        """Test StateCorruptionError with backup information."""
        error = StateCorruptionError(
            message="State corrupted",
            corrupted_files=["state.json", "index.db"],
            backup_available=True
        )

        assert error.corrupted_files == ["state.json", "index.db"]
        assert error.backup_available is True
        assert "restore from backup" in error.user_message.lower()

    def test_timeout_error_with_operation_info(self):
        """Test TimeoutError with operation information."""
        error = TimeoutError(
            message="Operation timed out",
            timeout_seconds=300,
            operation_type="indexing"
        )

        assert error.timeout_seconds == 300
        assert error.operation_type == "indexing"
        assert "timed out" in error.user_message.lower()


if __name__ == "__main__":
    pytest.main([__file__])
