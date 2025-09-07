#!/usr/bin/env python3
"""
Demo script showing error handling capabilities in dev-agent.

This script demonstrates various error scenarios and how the ErrorHandler
provides graceful degradation and recovery mechanisms.
"""

import sys
import os
import tempfile
import time
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dev_agent.errors import (
    ErrorHandler,
    IndexingError,
    SystemError,
    PerformanceError,
    StateCorruptionError,
    TimeoutError,
    UserInputError,
    ImplementationError,
    ErrorSeverity,
    ErrorContext,
)


def demo_indexing_error_recovery():
    """Demo indexing error with graceful degradation."""
    print("\n=== Indexing Error Recovery Demo ===")
    
    error_handler = ErrorHandler()
    
    # Simulate indexing failure with partial success
    error = IndexingError(
        message="Failed to index 15% of files due to memory constraints",
        partial_success=True,
        failed_files=["large_file1.py", "corrupted_file2.py", "binary_file3.so"],
        severity=ErrorSeverity.MEDIUM,
        context=ErrorContext(
            operation="full_codebase_indexing",
            phase="indexing",
            additional_info={"total_files": 1000, "failed_files": 150}
        )
    )
    
    print(f"Error occurred: {error.message}")
    print(f"User message: {error.user_message}")
    
    recovery_action = error_handler.handle_error(error)
    
    if recovery_action:
        print(f"Recovery action: {recovery_action.description}")
        print(f"Automatic recovery: {recovery_action.automatic}")
        print(f"Use partial index: {recovery_action.use_partial_index}")
        
        if recovery_action.execute():
            print("✅ Recovery successful - continuing with partial index")
        else:
            print("❌ Recovery failed")
    
    # Show error statistics
    stats = error_handler.get_error_statistics()
    print(f"Total errors handled: {stats['total_errors']}")


def demo_performance_error_optimization():
    """Demo performance error with optimization."""
    print("\n=== Performance Error Optimization Demo ===")
    
    error_handler = ErrorHandler()
    
    # Simulate memory exhaustion
    error = PerformanceError(
        message="Memory usage exceeded 2GB during vector embedding generation",
        memory_usage_mb=2048,
        execution_time_seconds=450,
        severity=ErrorSeverity.HIGH,
        context=ErrorContext(
            operation="vector_embedding_generation",
            phase="indexing",
            additional_info={"chunk_size": 1000, "batch_size": 100}
        )
    )
    
    print(f"Error occurred: {error.message}")
    print(f"Memory usage: {error.memory_usage_mb}MB")
    print(f"Execution time: {error.execution_time_seconds}s")
    
    recovery_action = error_handler.handle_error(error)
    
    if recovery_action:
        print(f"Recovery action: {recovery_action.description}")
        print(f"Reduce memory usage: {recovery_action.reduce_memory_usage}")
        print(f"Use chunked processing: {recovery_action.use_chunked_processing}")
        print(f"Enable caching: {recovery_action.enable_caching}")
        
        if recovery_action.execute():
            print("✅ Performance optimization applied")
        else:
            print("❌ Optimization failed")


def demo_system_error_recovery():
    """Demo system error with file permission recovery."""
    print("\n=== System Error Recovery Demo ===")
    
    error_handler = ErrorHandler()
    
    # Simulate permission error
    error = SystemError(
        message="Permission denied: cannot write to .dev_agent/state.json",
        severity=ErrorSeverity.HIGH,
        context=ErrorContext(
            operation="state_save",
            file_path=".dev_agent/state.json",
            phase="state_management"
        ),
        system_errno=13  # EACCES
    )
    
    print(f"Error occurred: {error.message}")
    print(f"System errno: {error.system_errno}")
    
    recovery_action = error_handler.handle_error(error)
    
    if recovery_action:
        print(f"Recovery action: {recovery_action.description}")
        print(f"Check permissions: {recovery_action.check_permissions}")
        print(f"Automatic recovery: {recovery_action.automatic}")
        
        if recovery_action.execute():
            print("✅ File permissions checked and fixed")
        else:
            print("❌ Permission fix failed")


def demo_state_corruption_recovery():
    """Demo state corruption with backup recovery."""
    print("\n=== State Corruption Recovery Demo ===")
    
    error_handler = ErrorHandler()
    
    # Simulate state corruption with backup available
    error = StateCorruptionError(
        message="State file corrupted: invalid JSON format detected",
        corrupted_files=[".dev_agent/state.json", ".dev_agent/index.db"],
        backup_available=True,
        severity=ErrorSeverity.HIGH,
        context=ErrorContext(
            operation="state_load",
            phase="initialization"
        )
    )
    
    print(f"Error occurred: {error.message}")
    print(f"Corrupted files: {error.corrupted_files}")
    print(f"Backup available: {error.backup_available}")
    
    recovery_action = error_handler.handle_error(error)
    
    if recovery_action:
        print(f"Recovery action: {recovery_action.description}")
        print(f"Backup files: {recovery_action.backup_files}")
        print(f"Automatic recovery: {recovery_action.automatic}")
        
        if recovery_action.execute():
            print("✅ State restored from backup")
        else:
            print("❌ Backup restoration failed")


def demo_timeout_handling():
    """Demo timeout handling with context manager."""
    print("\n=== Timeout Handling Demo ===")
    
    error_handler = ErrorHandler()
    
    def simulate_long_operation():
        """Simulate a long-running operation."""
        print("Starting long operation...")
        time.sleep(0.3)  # Simulate work
        return "Operation completed"
    
    try:
        # This should timeout
        with error_handler.create_timeout_context("demo_operation", 0.1):
            result = simulate_long_operation()
            print(f"Result: {result}")
    except TimeoutError as e:
        print(f"Timeout occurred: {e.message}")
        
        recovery_action = error_handler.handle_error(e)
        if recovery_action:
            print(f"Recovery action: {recovery_action.description}")
            print(f"Increase timeout: {recovery_action.increase_timeout}")
            print(f"Use chunked processing: {recovery_action.use_chunked_processing}")
    
    # Now try with sufficient timeout
    try:
        print("\nRetrying with increased timeout...")
        with error_handler.create_timeout_context("demo_operation", 0.5):
            result = simulate_long_operation()
            print(f"✅ {result}")
    except TimeoutError:
        print("❌ Still timed out")


def demo_user_input_error():
    """Demo user input error handling."""
    print("\n=== User Input Error Demo ===")
    
    error_handler = ErrorHandler()
    
    # Simulate invalid user input
    error = UserInputError(
        message="Invalid approval response",
        expected_input="y|n|yes|no",
        received_input="maybe",
        context=ErrorContext(
            operation="user_approval",
            phase="specification_review"
        )
    )
    
    print(f"Error occurred: {error.message}")
    print(f"Expected: {error.expected_input}")
    print(f"Received: {error.received_input}")
    
    recovery_action = error_handler.handle_error(error)
    
    if recovery_action:
        print(f"Recovery action: {recovery_action.description}")
        print(f"Prompt message: {recovery_action.prompt_message}")
        print(f"Expected responses: {recovery_action.expected_responses}")
        print(f"Max retries: {recovery_action.max_retries}")
        
        # Test response validation
        print(f"Validate 'y': {recovery_action.validate_response('y')}")
        print(f"Validate 'maybe': {recovery_action.validate_response('maybe')}")


def demo_cascading_errors():
    """Demo handling of cascading errors."""
    print("\n=== Cascading Errors Demo ===")
    
    error_handler = ErrorHandler()
    
    # First error: indexing failure
    error1 = IndexingError(
        message="Initial indexing failed due to memory constraints",
        partial_success=False,
        severity=ErrorSeverity.HIGH
    )
    
    # Second error: system error during recovery attempt
    error2 = SystemError(
        message="Cannot create recovery directory: disk full",
        severity=ErrorSeverity.CRITICAL,
        context=ErrorContext(operation="recovery_setup")
    )
    
    # Third error: performance issue during fallback
    error3 = PerformanceError(
        message="Fallback operation consuming too much memory",
        memory_usage_mb=1500,
        severity=ErrorSeverity.MEDIUM
    )
    
    errors = [error1, error2, error3]
    
    for i, error in enumerate(errors, 1):
        print(f"\nHandling error {i}: {error.message}")
        recovery_action = error_handler.handle_error(error)
        
        if recovery_action:
            print(f"  Recovery: {recovery_action.description}")
            print(f"  Automatic: {recovery_action.automatic}")
    
    # Show comprehensive error statistics
    stats = error_handler.get_error_statistics()
    print(f"\n📊 Error Statistics:")
    print(f"  Total errors: {stats['total_errors']}")
    print(f"  By category: {stats['by_category']}")
    print(f"  By severity: {stats['by_severity']}")


def main():
    """Run all error handling demos."""
    print("🔧 Dev-Agent Error Handling System Demo")
    print("=" * 50)
    
    try:
        demo_indexing_error_recovery()
        demo_performance_error_optimization()
        demo_system_error_recovery()
        demo_state_corruption_recovery()
        demo_timeout_handling()
        demo_user_input_error()
        demo_cascading_errors()
        
        print("\n✅ All error handling demos completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Demo failed with unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()