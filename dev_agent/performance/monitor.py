"""Performance monitoring and optimization utilities.

This module provides tools for monitoring and optimizing performance
across dev-agent operations.
"""

from __future__ import annotations

import functools
import logging
import time
from contextlib import contextmanager
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class PerformanceMonitor:
    """Monitor and track performance metrics.
    
    This class provides utilities for tracking operation times and
    ensuring performance targets are met.
    
    Attributes:
        metrics: Dictionary of operation names to timing data
        
    Example:
        ```python
        monitor = PerformanceMonitor()
        
        with monitor.measure("indexing"):
            # Perform indexing operation
            pass
        
        stats = monitor.get_stats("indexing")
        print(f"Average time: {stats['avg_ms']:.1f}ms")
        ```
    """
    
    def __init__(self) -> None:
        """Initialize performance monitor."""
        self.metrics: dict[str, list[float]] = {}
    
    @contextmanager
    def measure(self, operation: str, warn_threshold_ms: float | None = None):
        """Context manager to measure operation time.
        
        Args:
            operation: Name of the operation being measured
            warn_threshold_ms: Optional threshold in milliseconds to warn if exceeded
            
        Yields:
            None
            
        Example:
            ```python
            monitor = PerformanceMonitor()
            with monitor.measure("save_state", warn_threshold_ms=100):
                state_manager.save_project_state(state)
            ```
        """
        start_time = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            
            # Record metric
            if operation not in self.metrics:
                self.metrics[operation] = []
            self.metrics[operation].append(elapsed_ms)
            
            # Warn if threshold exceeded
            if warn_threshold_ms and elapsed_ms > warn_threshold_ms:
                logger.warning(
                    f"{operation} took {elapsed_ms:.1f}ms "
                    f"(threshold: {warn_threshold_ms:.1f}ms)"
                )
            else:
                logger.debug(f"{operation} completed in {elapsed_ms:.1f}ms")
    
    def get_stats(self, operation: str) -> dict[str, float]:
        """Get statistics for an operation.
        
        Args:
            operation: Name of the operation
            
        Returns:
            Dictionary with min, max, avg, and total timing statistics
            
        Example:
            ```python
            stats = monitor.get_stats("indexing")
            print(f"Min: {stats['min_ms']:.1f}ms")
            print(f"Max: {stats['max_ms']:.1f}ms")
            print(f"Avg: {stats['avg_ms']:.1f}ms")
            ```
        """
        if operation not in self.metrics or not self.metrics[operation]:
            return {
                "count": 0,
                "min_ms": 0.0,
                "max_ms": 0.0,
                "avg_ms": 0.0,
                "total_ms": 0.0,
            }
        
        times = self.metrics[operation]
        return {
            "count": len(times),
            "min_ms": min(times),
            "max_ms": max(times),
            "avg_ms": sum(times) / len(times),
            "total_ms": sum(times),
        }
    
    def get_all_stats(self) -> dict[str, dict[str, float]]:
        """Get statistics for all operations.
        
        Returns:
            Dictionary mapping operation names to their statistics
        """
        return {op: self.get_stats(op) for op in self.metrics}
    
    def reset(self) -> None:
        """Reset all metrics."""
        self.metrics.clear()
        logger.debug("Performance metrics reset")


def measure_time(
    operation: str | None = None,
    warn_threshold_ms: float | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to measure function execution time.
    
    Args:
        operation: Name of the operation (defaults to function name)
        warn_threshold_ms: Optional threshold in milliseconds to warn if exceeded
        
    Returns:
        Decorated function
        
    Example:
        ```python
        @measure_time("parse_file", warn_threshold_ms=100)
        def parse_file(path: str) -> AST:
            # Parse file
            pass
        ```
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        op_name = operation or func.__name__
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            start_time = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                
                if warn_threshold_ms and elapsed_ms > warn_threshold_ms:
                    logger.warning(
                        f"{op_name} took {elapsed_ms:.1f}ms "
                        f"(threshold: {warn_threshold_ms:.1f}ms)"
                    )
                else:
                    logger.debug(f"{op_name} completed in {elapsed_ms:.1f}ms")
        
        return wrapper
    return decorator


def optimize_batch_size(
    total_items: int,
    target_batch_size: int = 16,
    max_batch_size: int = 100,
    min_batch_size: int = 1,
) -> int:
    """Calculate optimal batch size for processing.
    
    This function determines the best batch size based on the total
    number of items and target batch size, ensuring efficient processing
    while respecting API limits.
    
    Args:
        total_items: Total number of items to process
        target_batch_size: Desired batch size (default: 16 for Azure OpenAI)
        max_batch_size: Maximum allowed batch size (default: 100)
        min_batch_size: Minimum batch size (default: 1)
        
    Returns:
        Optimal batch size
        
    Example:
        ```python
        # For 50 items with target batch size of 16
        batch_size = optimize_batch_size(50, target_batch_size=16)
        # Returns 16 (3 batches of 16, 1 batch of 2)
        
        # For 5 items with target batch size of 16
        batch_size = optimize_batch_size(5, target_batch_size=16)
        # Returns 5 (1 batch of 5)
        ```
    """
    if total_items <= 0:
        return min_batch_size
    
    # If total items less than target, use total items
    if total_items <= target_batch_size:
        return max(min_batch_size, total_items)
    
    # Use target batch size, capped at max
    return min(target_batch_size, max_batch_size)
