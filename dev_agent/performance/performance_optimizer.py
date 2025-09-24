"""Performance optimizer with intelligent caching and parallel processing."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import multiprocessing
import os
import pickle
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union

from ..config.config_manager import ConfigManager
from ..models.enums import PhaseType
from ..models.project_state import ProjectState

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    
    data: Any
    timestamp: float
    access_count: int
    file_hash: str
    dependencies: List[str]


@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring."""
    
    cache_hit_rate: float
    average_response_time: float
    memory_usage_mb: float
    cpu_utilization: float
    parallel_efficiency: float
    throughput_ops_per_sec: float


@dataclass
class OptimizationConfig:
    """Configuration for performance optimization."""
    
    enable_caching: bool = True
    cache_size_mb: int = 512
    cache_ttl_seconds: int = 3600
    max_parallel_workers: int = 0  # 0 = auto-detect
    enable_memory_mapping: bool = True
    memory_map_threshold_mb: int = 10
    enable_compression: bool = True
    prefetch_enabled: bool = True
    adaptive_batching: bool = True


class PerformanceOptimizer:
    """Intelligent performance optimizer with caching and parallel processing."""

    def __init__(
        self,
        config: Optional[OptimizationConfig] = None,
        cache_dir: Optional[str] = None,
    ):
        """Initialize the performance optimizer.
        
        Args:
            config: Optimization configuration
            cache_dir: Directory for cache storage
        """
        self.config = config or OptimizationConfig()
        self.cache_dir = Path(cache_dir) if cache_dir else Path.cwd() / ".dev_agent" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize cache
        self._cache: Dict[str, CacheEntry] = {}
        self._cache_size_bytes = 0
        self._max_cache_size_bytes = self.config.cache_size_mb * 1024 * 1024
        
        # Performance tracking
        self._metrics = PerformanceMetrics(
            cache_hit_rate=0.0,
            average_response_time=0.0,
            memory_usage_mb=0.0,
            cpu_utilization=0.0,
            parallel_efficiency=0.0,
            throughput_ops_per_sec=0.0,
        )
        self._operation_times: List[float] = []
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Parallel processing
        self.max_workers = (
            self.config.max_parallel_workers
            if self.config.max_parallel_workers > 0
            else min(32, (os.cpu_count() or 1) + 4)
        )
        
        # Load persistent cache
        self._load_persistent_cache()
        
        logger.info(f"PerformanceOptimizer initialized with {self.max_workers} workers")

    def optimize_operation(
        self,
        operation: Callable[..., T],
        *args,
        cache_key: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        **kwargs,
    ) -> T:
        """Optimize a single operation with caching and monitoring.
        
        Args:
            operation: Function to optimize
            *args: Arguments for the operation
            cache_key: Custom cache key (auto-generated if None)
            dependencies: List of file dependencies for cache invalidation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            Result of the operation
        """
        start_time = time.time()
        
        # Generate cache key if not provided
        if cache_key is None:
            cache_key = self._generate_cache_key(operation, args, kwargs)
        
        # Check cache first
        if self.config.enable_caching:
            cached_result = self._get_from_cache(cache_key, dependencies)
            if cached_result is not None:
                self._cache_hits += 1
                self._record_operation_time(time.time() - start_time)
                return cached_result
        
        # Execute operation
        try:
            result = operation(*args, **kwargs)
            
            # Cache the result
            if self.config.enable_caching:
                self._store_in_cache(cache_key, result, dependencies)
            
            self._cache_misses += 1
            self._record_operation_time(time.time() - start_time)
            
            return result
            
        except Exception as e:
            logger.error(f"Operation failed: {e}")
            raise

    def optimize_batch_operations(
        self,
        operations: List[Tuple[Callable, tuple, dict]],
        batch_size: Optional[int] = None,
        use_processes: bool = False,
    ) -> List[Any]:
        """Optimize batch operations with intelligent parallelization.
        
        Args:
            operations: List of (function, args, kwargs) tuples
            batch_size: Size of batches for processing (auto-calculated if None)
            use_processes: Use process pool instead of thread pool
            
        Returns:
            List of results in the same order as operations
        """
        if not operations:
            return []
        
        start_time = time.time()
        
        # Determine optimal batch size
        if batch_size is None:
            batch_size = self._calculate_optimal_batch_size(len(operations))
        
        # Choose executor type
        executor_class = ProcessPoolExecutor if use_processes else ThreadPoolExecutor
        
        results = [None] * len(operations)
        
        with executor_class(max_workers=self.max_workers) as executor:
            # Submit operations in batches
            future_to_index = {}
            
            for i, (func, args, kwargs) in enumerate(operations):
                future = executor.submit(self._execute_with_monitoring, func, args, kwargs)
                future_to_index[future] = i
            
            # Collect results
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    results[index] = future.result()
                except Exception as e:
                    logger.error(f"Batch operation {index} failed: {e}")
                    results[index] = None
        
        total_time = time.time() - start_time
        self._update_parallel_efficiency(len(operations), total_time)
        
        return results

    async def optimize_async_operations(
        self,
        operations: List[Callable],
        *args_list,
        concurrency_limit: int = 10,
        **kwargs,
    ) -> List[Any]:
        """Optimize asynchronous operations with concurrency control.
        
        Args:
            operations: List of async functions
            *args_list: Arguments for each operation
            concurrency_limit: Maximum concurrent operations
            **kwargs: Common keyword arguments
            
        Returns:
            List of results
        """
        semaphore = asyncio.Semaphore(concurrency_limit)
        
        async def bounded_operation(op, args):
            async with semaphore:
                return await op(*args, **kwargs)
        
        tasks = [
            bounded_operation(op, args)
            for op, args in zip(operations, args_list)
        ]
        
        return await asyncio.gather(*tasks, return_exceptions=True)

    def optimize_memory_usage(
        self,
        data_processor: Callable[[Any], Any],
        data_source: Union[List[Any], Callable[[], Any]],
        chunk_size: int = 1000,
    ) -> Any:
        """Optimize memory usage for large data processing.
        
        Args:
            data_processor: Function to process data chunks
            data_source: Data source (list or generator function)
            chunk_size: Size of processing chunks
            
        Returns:
            Processed results
        """
        if isinstance(data_source, list):
            # Process list in chunks
            results = []
            for i in range(0, len(data_source), chunk_size):
                chunk = data_source[i:i + chunk_size]
                chunk_result = data_processor(chunk)
                results.append(chunk_result)
            return results
        else:
            # Process generator in chunks
            results = []
            chunk = []
            
            for item in data_source():
                chunk.append(item)
                if len(chunk) >= chunk_size:
                    chunk_result = data_processor(chunk)
                    results.append(chunk_result)
                    chunk = []
            
            # Process remaining items
            if chunk:
                chunk_result = data_processor(chunk)
                results.append(chunk_result)
            
            return results

    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics.
        
        Returns:
            Current performance metrics
        """
        # Update cache hit rate
        total_requests = self._cache_hits + self._cache_misses
        self._metrics.cache_hit_rate = (
            self._cache_hits / total_requests if total_requests > 0 else 0.0
        )
        
        # Update average response time
        if self._operation_times:
            self._metrics.average_response_time = sum(self._operation_times) / len(self._operation_times)
        
        # Update memory usage
        self._metrics.memory_usage_mb = self._cache_size_bytes / (1024 * 1024)
        
        # Update throughput
        if self._operation_times:
            self._metrics.throughput_ops_per_sec = len(self._operation_times) / sum(self._operation_times)
        
        return self._metrics

    def clear_cache(self, pattern: Optional[str] = None) -> None:
        """Clear cache entries.
        
        Args:
            pattern: Pattern to match cache keys (clears all if None)
        """
        if pattern is None:
            self._cache.clear()
            self._cache_size_bytes = 0
        else:
            keys_to_remove = [key for key in self._cache.keys() if pattern in key]
            for key in keys_to_remove:
                entry = self._cache.pop(key)
                self._cache_size_bytes -= len(pickle.dumps(entry.data))
        
        logger.info(f"Cache cleared (pattern: {pattern})")

    def invalidate_cache_by_dependencies(self, changed_files: List[str]) -> None:
        """Invalidate cache entries based on file dependencies.
        
        Args:
            changed_files: List of changed file paths
        """
        keys_to_remove = []
        
        for key, entry in self._cache.items():
            if any(dep in changed_files for dep in entry.dependencies):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            entry = self._cache.pop(key)
            self._cache_size_bytes -= len(pickle.dumps(entry.data))
        
        logger.info(f"Invalidated {len(keys_to_remove)} cache entries due to file changes")

    def _generate_cache_key(
        self,
        operation: Callable,
        args: tuple,
        kwargs: dict,
    ) -> str:
        """Generate a cache key for an operation."""
        # Create a hash of the operation signature and arguments
        key_data = {
            'function': f"{operation.__module__}.{operation.__name__}",
            'args': str(args),
            'kwargs': str(sorted(kwargs.items())),
        }
        
        key_string = str(key_data)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_from_cache(
        self,
        cache_key: str,
        dependencies: Optional[List[str]] = None,
    ) -> Any:
        """Get result from cache if valid."""
        if cache_key not in self._cache:
            return None
        
        entry = self._cache[cache_key]
        
        # Check TTL
        if time.time() - entry.timestamp > self.config.cache_ttl_seconds:
            self._remove_from_cache(cache_key)
            return None
        
        # Check dependencies
        if dependencies and self._are_dependencies_stale(entry, dependencies):
            self._remove_from_cache(cache_key)
            return None
        
        # Update access count
        entry.access_count += 1
        
        return entry.data

    def _store_in_cache(
        self,
        cache_key: str,
        data: Any,
        dependencies: Optional[List[str]] = None,
    ) -> None:
        """Store result in cache."""
        # Serialize data to calculate size
        serialized_data = pickle.dumps(data)
        data_size = len(serialized_data)
        
        # Check if we need to evict entries
        while (self._cache_size_bytes + data_size > self._max_cache_size_bytes and 
               self._cache):
            self._evict_lru_entry()
        
        # Calculate file hash for dependencies
        file_hash = ""
        if dependencies:
            file_hash = self._calculate_dependencies_hash(dependencies)
        
        # Store entry
        entry = CacheEntry(
            data=data,
            timestamp=time.time(),
            access_count=1,
            file_hash=file_hash,
            dependencies=dependencies or [],
        )
        
        self._cache[cache_key] = entry
        self._cache_size_bytes += data_size

    def _remove_from_cache(self, cache_key: str) -> None:
        """Remove entry from cache."""
        if cache_key in self._cache:
            entry = self._cache.pop(cache_key)
            self._cache_size_bytes -= len(pickle.dumps(entry.data))

    def _evict_lru_entry(self) -> None:
        """Evict least recently used cache entry."""
        if not self._cache:
            return
        
        # Find entry with lowest access count and oldest timestamp
        lru_key = min(
            self._cache.keys(),
            key=lambda k: (self._cache[k].access_count, self._cache[k].timestamp)
        )
        
        self._remove_from_cache(lru_key)

    def _are_dependencies_stale(
        self,
        entry: CacheEntry,
        current_dependencies: List[str],
    ) -> bool:
        """Check if cache entry dependencies are stale."""
        if not entry.dependencies:
            return False
        
        current_hash = self._calculate_dependencies_hash(current_dependencies)
        return current_hash != entry.file_hash

    def _calculate_dependencies_hash(self, dependencies: List[str]) -> str:
        """Calculate hash of dependency files."""
        hash_md5 = hashlib.md5()
        
        for dep_path in sorted(dependencies):
            try:
                path = Path(dep_path)
                if path.exists():
                    # Use file modification time and size for hash
                    stat = path.stat()
                    hash_md5.update(f"{dep_path}:{stat.st_mtime}:{stat.st_size}".encode())
            except Exception:
                # If file doesn't exist or can't be accessed, include path only
                hash_md5.update(dep_path.encode())
        
        return hash_md5.hexdigest()

    def _calculate_optimal_batch_size(self, total_operations: int) -> int:
        """Calculate optimal batch size based on system resources."""
        if not self.config.adaptive_batching:
            return max(1, total_operations // self.max_workers)
        
        # Adaptive batch sizing based on operation count and system resources
        base_batch_size = max(1, total_operations // (self.max_workers * 2))
        
        # Adjust based on available memory
        available_memory_mb = self._get_available_memory_mb()
        if available_memory_mb < 1024:  # Less than 1GB
            base_batch_size = max(1, base_batch_size // 2)
        elif available_memory_mb > 4096:  # More than 4GB
            base_batch_size = min(total_operations, base_batch_size * 2)
        
        return base_batch_size

    def _get_available_memory_mb(self) -> float:
        """Get available system memory in MB."""
        try:
            import psutil
            return psutil.virtual_memory().available / (1024 * 1024)
        except ImportError:
            # Fallback estimation
            return 2048.0  # Assume 2GB available

    def _execute_with_monitoring(
        self,
        func: Callable,
        args: tuple,
        kwargs: dict,
    ) -> Any:
        """Execute function with performance monitoring."""
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            self._record_operation_time(time.time() - start_time)
            return result
        except Exception as e:
            logger.error(f"Monitored operation failed: {e}")
            raise

    def _record_operation_time(self, duration: float) -> None:
        """Record operation time for metrics."""
        self._operation_times.append(duration)
        
        # Keep only recent measurements (last 1000)
        if len(self._operation_times) > 1000:
            self._operation_times = self._operation_times[-1000:]

    def _update_parallel_efficiency(self, operation_count: int, total_time: float) -> None:
        """Update parallel processing efficiency metrics."""
        if total_time > 0:
            # Estimate sequential time (rough approximation)
            avg_op_time = sum(self._operation_times[-operation_count:]) / operation_count if self._operation_times else 0.1
            estimated_sequential_time = avg_op_time * operation_count
            
            # Calculate efficiency
            self._metrics.parallel_efficiency = min(1.0, estimated_sequential_time / total_time)

    def _load_persistent_cache(self) -> None:
        """Load cache from persistent storage."""
        cache_file = self.cache_dir / "performance_cache.pkl"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                    
                # Validate and load cache entries
                current_time = time.time()
                for key, entry in cached_data.items():
                    if current_time - entry.timestamp < self.config.cache_ttl_seconds:
                        self._cache[key] = entry
                        self._cache_size_bytes += len(pickle.dumps(entry.data))
                
                logger.info(f"Loaded {len(self._cache)} cache entries from persistent storage")
                
            except Exception as e:
                logger.warning(f"Failed to load persistent cache: {e}")

    def save_persistent_cache(self) -> None:
        """Save cache to persistent storage."""
        cache_file = self.cache_dir / "performance_cache.pkl"
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(self._cache, f)
            
            logger.info(f"Saved {len(self._cache)} cache entries to persistent storage")
            
        except Exception as e:
            logger.error(f"Failed to save persistent cache: {e}")

    def __del__(self):
        """Cleanup when optimizer is destroyed."""
        try:
            self.save_persistent_cache()
        except Exception:
            pass  # Ignore errors during cleanup