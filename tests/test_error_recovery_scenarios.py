"""Tests for error recovery scenarios and integration."""

import tempfile
import time
from unittest.mock import Mock, patch

import pytest

from dev_agent.errors import (
    ErrorContext,
    ErrorHandler,
    ErrorSeverity,
    IndexingError,
    PerformanceError,
    StateCorruptionError,
    SystemError,
    TimeoutError,
)


class TestErrorRecoveryScenarios:
    """Test comprehensive error recovery scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.error_handler = ErrorHandler(project_path=self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_indexing_failure_graceful_degradation(self):
        """Test graceful degradation when indexing fails."""
        # Simulate indexing failure with some successful files
        error = IndexingError(
            message="Failed to index 20% of files due to memory constraints",
            partial_success=True,
            failed_files=["large_file1.py", "corrupted_file2.py"],
            severity=ErrorSeverity.MEDIUM
        )

        recovery_action = self.error_handler.handle_error(error)

        # Should get fallback action to use partial index
        assert recovery_action is not None
        assert recovery_action.automatic is True
        assert hasattr(recovery_action, "use_partial_index")
        assert recovery_action.use_partial_index is True

        # Verify error is logged and tracked
        assert len(self.error_handler.error_history) == 1
        assert self.error_handler.error_history[0]["category"] == "indexing"

    def test_memory_exhaustion_recovery(self):
        """Test recovery from memory exhaustion during indexing."""
        error = PerformanceError(
            message="Memory usage exceeded 2GB during indexing",
            memory_usage_mb=2048,
            execution_time_seconds=180,
            severity=ErrorSeverity.HIGH,
            context=ErrorContext(operation="indexing", phase="embedding_generation")
        )

        recovery_action = self.error_handler.handle_error(error)

        # Should get optimization action
        assert recovery_action is not None
        assert recovery_action.reduce_memory_usage is True
        assert recovery_action.use_chunked_processing is True
        assert recovery_action.enable_caching is True

    def test_file_permission_recovery(self):
        """Test recovery from file permission errors."""
        error = SystemError(
            message="Permission denied: cannot write to .dev_agent directory",
            severity=ErrorSeverity.HIGH,
            context=ErrorContext(operation="state_save", file_path=".dev_agent/state.json"),
            system_errno=13  # EACCES
        )

        recovery_action = self.error_handler.handle_error(error)

        # Should get system recovery action
        assert recovery_action is not None
        assert recovery_action.check_permissions is True
        assert recovery_action.automatic is True

    def test_disk_space_recovery(self):
        """Test recovery from disk space issues."""
        error = SystemError(
            message="No space left on device",
            severity=ErrorSeverity.CRITICAL,
            context=ErrorContext(operation="index_write"),
            system_errno=28  # ENOSPC
        )

        recovery_action = self.error_handler.handle_error(error)

        # Should get cleanup action
        assert recovery_action is not None
        assert recovery_action.cleanup_temp_files is True
        assert recovery_action.verify_disk_space is True

    def test_state_corruption_with_backup_recovery(self):
        """Test recovery from state corruption when backup exists."""
        error = StateCorruptionError(
            message="State file corrupted: invalid JSON format",
            corrupted_files=[".dev_agent/state.json"],
            backup_available=True,
            severity=ErrorSeverity.HIGH
        )

        recovery_action = self.error_handler.handle_error(error)

        # Should get automatic restore action
        assert recovery_action is not None
        assert recovery_action.automatic is True
        assert ".dev_agent/state.json" in recovery_action.backup_files

    def test_state_corruption_without_backup_recovery(self):
        """Test recovery from state corruption when no backup exists."""
        error = StateCorruptionError(
            message="State file corrupted and no backup available",
            corrupted_files=[".dev_agent/state.json", ".dev_agent/index.db"],
            backup_available=False,
            severity=ErrorSeverity.CRITICAL
        )

        recovery_action = self.error_handler.handle_error(error)

        # Should require user intervention
        assert recovery_action is not None
        assert recovery_action.automatic is False
        assert "reinitialize" in recovery_action.user_message.lower()

    def test_timeout_recovery_with_optimization(self):
        """Test recovery from timeout with performance optimization."""
        error = TimeoutError(
            message="Indexing operation timed out after 300 seconds",
            timeout_seconds=300,
            operation_type="indexing",
            severity=ErrorSeverity.MEDIUM,
            context=ErrorContext(operation="full_codebase_indexing")
        )

        recovery_action = self.error_handler.handle_error(error)

        # Should get retry with optimization
        assert recovery_action is not None
        assert recovery_action.increase_timeout is True
        assert recovery_action.use_chunked_processing is True
        assert recovery_action.reduce_batch_size is True

    def test_cascading_error_recovery(self):
        """Test recovery from cascading errors."""
        # First error: indexing failure
        error1 = IndexingError(
            message="Initial indexing failed",
            partial_success=False,
            severity=ErrorSeverity.HIGH
        )

        recovery1 = self.error_handler.handle_error(error1)

        # Second error: system error during recovery
        error2 = SystemError(
            message="Cannot create recovery directory",
            severity=ErrorSeverity.HIGH,
            context=ErrorContext(operation="recovery_setup")
        )

        recovery2 = self.error_handler.handle_error(error2)

        # Should have both errors in history
        assert len(self.error_handler.error_history) == 2

        # Both should have recovery actions
        assert recovery1 is not None
        assert recovery2 is not None

        # Check error statistics
        stats = self.error_handler.get_error_statistics()
        assert stats["total_errors"] == 2
        assert stats["by_category"]["indexing"] == 1
        assert stats["by_category"]["system"] == 1

    def test_error_recovery_execution_failure(self):
        """Test handling when recovery action execution fails."""
        # Create a mock recovery action that fails
        with patch.object(self.error_handler, "_execute_recovery_action", return_value=False):
            error = SystemError(
                message="Test system error",
                severity=ErrorSeverity.MEDIUM
            )

            recovery_action = self.error_handler.handle_error(error)

            # Should still return recovery action even if execution fails
            assert recovery_action is not None

            # Error should still be logged
            assert len(self.error_handler.error_history) == 1

    def test_performance_threshold_monitoring(self):
        """Test performance threshold monitoring and alerts."""
        # Test memory threshold
        error1 = PerformanceError(
            message="High memory usage",
            memory_usage_mb=1500,  # Above 1GB threshold
            execution_time_seconds=100
        )

        recovery1 = self.error_handler.handle_performance_error(error1)
        assert recovery1.reduce_memory_usage is True

        # Test execution time threshold
        error2 = PerformanceError(
            message="Long execution time",
            memory_usage_mb=500,
            execution_time_seconds=400  # Above 5 minute threshold
        )

        recovery2 = self.error_handler.handle_performance_error(error2)
        assert recovery2.increase_timeout is True
        assert recovery2.reduce_batch_size is True

    def test_timeout_context_integration(self):
        """Test timeout context manager integration with error handler."""
        def long_running_operation():
            """Simulate a long-running operation."""
            time.sleep(0.2)
            return "completed"

        # Test timeout occurs
        with pytest.raises(TimeoutError):
            with self.error_handler.create_timeout_context("test_op", 0.1):
                long_running_operation()

        # Test successful operation within timeout
        with self.error_handler.create_timeout_context("test_op", 0.5):
            result = long_running_operation()
            assert result == "completed"

    def test_error_recovery_strategy_selection(self):
        """Test that appropriate recovery strategies are selected."""
        # Test indexing error gets indexing strategies
        indexing_error = IndexingError("Test indexing error")
        recovery = self.error_handler.handle_error(indexing_error)
        assert hasattr(recovery, "use_partial_index") or hasattr(recovery, "reduce_memory_usage")

        # Test system error gets system strategies
        system_error = SystemError("Test system error")
        recovery = self.error_handler.handle_error(system_error)
        assert hasattr(recovery, "check_permissions") or hasattr(recovery, "create_directories")

        # Test performance error gets performance strategies
        perf_error = PerformanceError("Test performance error")
        recovery = self.error_handler.handle_error(perf_error)
        assert hasattr(recovery, "reduce_memory_usage") or hasattr(recovery, "increase_timeout")

    def test_error_severity_handling(self):
        """Test that error severity affects recovery strategies."""
        # Critical error should have different handling
        critical_error = SystemError(
            message="Critical system failure",
            severity=ErrorSeverity.CRITICAL
        )

        recovery = self.error_handler.handle_error(critical_error)

        # Critical errors should be less likely to be automatically recoverable
        if recovery:
            # If there is a recovery, it should be carefully considered
            assert recovery.description is not None

    def test_error_context_preservation(self):
        """Test that error context is preserved through recovery."""
        context = ErrorContext(
            operation="test_operation",
            file_path="/test/file.py",
            phase="implementation",
            additional_info={"task_id": "task_123", "attempt": 2}
        )

        error = SystemError(
            message="Test error with context",
            context=context,
            severity=ErrorSeverity.MEDIUM
        )

        self.error_handler.handle_error(error)

        # Check that context is preserved in error history
        error_record = self.error_handler.error_history[0]
        assert error_record["context"]["operation"] == "test_operation"
        assert error_record["context"]["file_path"] == "/test/file.py"
        assert error_record["context"]["phase"] == "implementation"
        assert error_record["context"]["additional_info"]["task_id"] == "task_123"

    def test_error_history_size_management(self):
        """Test that error history is properly managed for size."""
        # Add many errors to test size limit
        for i in range(150):
            error = SystemError(f"Test error {i}")
            self.error_handler.handle_error(error)

        # Should maintain only last 100 errors
        assert len(self.error_handler.error_history) == 100

        # Should have the most recent errors
        assert "Test error 149" in self.error_handler.error_history[-1]["message"]
        assert "Test error 50" in self.error_handler.error_history[0]["message"]

    def test_logging_integration(self):
        """Test that errors are properly logged."""
        with patch.object(self.error_handler.logger, "error") as mock_error:
            with patch.object(self.error_handler.logger, "warning") as mock_warning:
                with patch.object(self.error_handler.logger, "critical") as mock_critical:

                    # Test different severity levels
                    error1 = SystemError("High severity error", severity=ErrorSeverity.HIGH)
                    error2 = PerformanceError("Medium severity error", severity=ErrorSeverity.MEDIUM)
                    error3 = SystemError("Critical error", severity=ErrorSeverity.CRITICAL)

                    self.error_handler.handle_error(error1)
                    self.error_handler.handle_error(error2)
                    self.error_handler.handle_error(error3)

                    # Verify appropriate logging methods were called
                    mock_error.assert_called()
                    mock_warning.assert_called()
                    mock_critical.assert_called()


class TestErrorHandlerIntegration:
    """Test error handler integration with other components."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.error_handler = ErrorHandler(project_path=self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_error_handler_with_mock_indexing_engine(self):
        """Test error handler integration with indexing engine."""
        # Mock an indexing engine that fails
        mock_indexing_engine = Mock()
        mock_indexing_engine.build_index.side_effect = IndexingError(
            "Mock indexing failure",
            failed_files=["test.py"],
            partial_success=True
        )

        try:
            mock_indexing_engine.build_index()
        except IndexingError as e:
            recovery_action = self.error_handler.handle_error(e)

            assert recovery_action is not None
            assert recovery_action.use_partial_index is True

    def test_error_handler_with_mock_state_manager(self):
        """Test error handler integration with state manager."""
        # Mock a state manager that has corruption
        mock_state_manager = Mock()
        mock_state_manager.load_project_state.side_effect = StateCorruptionError(
            "Mock state corruption",
            corrupted_files=["state.json"],
            backup_available=False
        )

        try:
            mock_state_manager.load_project_state()
        except StateCorruptionError as e:
            recovery_action = self.error_handler.handle_error(e)

            assert recovery_action is not None
            assert recovery_action.automatic is False  # Requires user intervention

    def test_error_handler_statistics_monitoring(self):
        """Test error handler statistics for system monitoring."""
        # Generate various types of errors
        errors = [
            IndexingError("Indexing error 1"),
            IndexingError("Indexing error 2"),
            SystemError("System error 1"),
            PerformanceError("Performance error 1"),
            TimeoutError("Timeout error 1"),
        ]

        for error in errors:
            self.error_handler.handle_error(error)

        stats = self.error_handler.get_error_statistics()

        # Verify statistics are accurate
        assert stats["total_errors"] == 5
        assert stats["by_category"]["indexing"] == 2
        assert stats["by_category"]["system"] == 1
        assert stats["by_category"]["performance"] == 1
        assert stats["by_category"]["timeout"] == 1

        # Verify recent errors are tracked
        assert len(stats["recent_errors"]) == 5


if __name__ == "__main__":
    pytest.main([__file__])
