"""Integration tests for large codebase indexing (100k+ lines)."""

import os
import time
import tempfile
import shutil
import psutil
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from dev_agent.indexing.indexing_engine import IndexingEngine
from dev_agent.models.indexing import CodeChunk, ASTIndex


class TestLargeCodebaseIntegration:
    """Integration tests for large codebase handling."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "large_project"
        self.project_path.mkdir(parents=True)

        # Track memory usage
        self.process = psutil.Process()
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB

    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def create_large_python_project(self, target_lines: int = 100000) -> dict:
        """Create a large Python project with target lines of code.

        Args:
            target_lines: Target number of lines of code

        Returns:
            Dictionary with project statistics
        """
        # Calculate files needed (average 1000 lines per file)
        lines_per_file = 1000
        num_files = max(100, target_lines // lines_per_file)

        # Create directory structure
        directories = [
            "src/core",
            "src/utils",
            "src/models",
            "src/services",
            "src/api",
            "tests/unit",
            "tests/integration",
            "tests/performance",
            "scripts",
            "tools",
        ]

        for dir_path in directories:
            (self.project_path / dir_path).mkdir(parents=True, exist_ok=True)

        # Template for generating realistic Python code
        class_template = '''"""Module {module_name} - Generated for large codebase testing."""

import os
import sys
import json
import time
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from functools import wraps, lru_cache
from concurrent.futures import ThreadPoolExecutor
import asyncio
import threading
from pathlib import Path

# Module constants
DEFAULT_CONFIG = {{
    "timeout": 30,
    "max_retries": 3,
    "batch_size": 100,
    "debug": False
}}

logger = logging.getLogger(__name__)


@dataclass
class {class_name}Config:
    """Configuration for {class_name}."""
    
    timeout: int = 30
    max_retries: int = 3
    batch_size: int = 100
    debug: bool = False
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "{class_name}Config":
        """Create config from dictionary."""
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {{
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "batch_size": self.batch_size,
            "debug": self.debug,
            "custom_settings": self.custom_settings
        }}


class {class_name}Error(Exception):
    """Custom exception for {class_name} operations."""
    
    def __init__(self, message: str, error_code: int = 500, details: Optional[Dict] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {{}}
        self.timestamp = time.time()


def retry_on_failure(max_attempts: int = 3, delay: float = 1.0):
    """Decorator for retrying failed operations."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay * (2 ** attempt))  # Exponential backoff
                        logger.warning(f"Attempt {{attempt + 1}} failed: {{e}}")
                    else:
                        logger.error(f"All {{max_attempts}} attempts failed")
            
            raise last_exception
        return wrapper
    return decorator


def measure_performance(func):
    """Decorator to measure function performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{{func.__name__}} executed in {{execution_time:.4f}} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{{func.__name__}} failed after {{execution_time:.4f}} seconds: {{e}}")
            raise
    return wrapper


class Base{class_name}Interface(ABC):
    """Abstract base interface for {class_name} implementations."""
    
    @abstractmethod
    def initialize(self, config: {class_name}Config) -> bool:
        """Initialize the component."""
        pass
    
    @abstractmethod
    def process(self, data: Any) -> Any:
        """Process data."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup resources."""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get current status."""
        pass


class {class_name}(Base{class_name}Interface):
    """Main implementation of {class_name}."""
    
    def __init__(self, name: str, config: Optional[{class_name}Config] = None):
        """Initialize {class_name}.
        
        Args:
            name: Name identifier for this instance
            config: Configuration object
        """
        self.name = name
        self.config = config or {class_name}Config()
        self._initialized = False
        self._processing_count = 0
        self._error_count = 0
        self._start_time = None
        self._cache = {{}}
        self._lock = threading.RLock()
        self._executor = None
        
        logger.info(f"Created {{self.__class__.__name__}} instance: {{name}}")
    
    def initialize(self, config: Optional[{class_name}Config] = None) -> bool:
        """Initialize the component."""
        try:
            if config:
                self.config = config
            
            self._start_time = time.time()
            self._executor = ThreadPoolExecutor(max_workers=4)
            self._initialized = True
            
            logger.info(f"{{self.name}} initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize {{self.name}}: {{e}}")
            return False
    
    @measure_performance
    @retry_on_failure(max_attempts=3)
    def process(self, data: Any) -> Any:
        """Process data with error handling and retries."""
        if not self._initialized:
            raise {class_name}Error("Component not initialized", 400)
        
        with self._lock:
            self._processing_count += 1
        
        try:
            # Validate input
            if not self._validate_input(data):
                raise {class_name}Error("Invalid input data", 400)
            
            # Check cache first
            cache_key = self._generate_cache_key(data)
            if cache_key in self._cache:
                logger.debug(f"Cache hit for key: {{cache_key}}")
                return self._cache[cache_key]
            
            # Process the data
            result = self._process_internal(data)
            
            # Cache the result
            self._cache[cache_key] = result
            
            # Cleanup cache if it gets too large
            if len(self._cache) > 1000:
                self._cleanup_cache()
            
            logger.debug(f"Processed data successfully: {{type(data).__name__}}")
            return result
            
        except Exception as e:
            with self._lock:
                self._error_count += 1
            logger.error(f"Error processing data: {{e}}")
            raise
    
    def _validate_input(self, data: Any) -> bool:
        """Validate input data."""
        if data is None:
            return False
        
        # Type-specific validation
        if isinstance(data, dict):
            return len(data) > 0
        elif isinstance(data, (list, tuple)):
            return len(data) > 0
        elif isinstance(data, str):
            return len(data.strip()) > 0
        
        return True
    
    def _generate_cache_key(self, data: Any) -> str:
        """Generate cache key for data."""
        try:
            if isinstance(data, dict):
                return f"dict_{{hash(frozenset(data.items()))}}"
            elif isinstance(data, (list, tuple)):
                return f"list_{{hash(tuple(data))}}"
            else:
                return f"{{type(data).__name__}}_{{hash(str(data))}}"
        except:
            return f"uncacheable_{{id(data)}}"
    
    def _process_internal(self, data: Any) -> Any:
        """Internal processing logic."""
        # Simulate complex processing
        if isinstance(data, dict):
            return self._process_dict(data)
        elif isinstance(data, list):
            return self._process_list(data)
        elif isinstance(data, str):
            return self._process_string(data)
        else:
            return self._process_generic(data)
    
    def _process_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process dictionary data."""
        result = {{}}
        
        for key, value in data.items():
            # Transform key
            new_key = key.lower().replace(" ", "_")
            
            # Transform value
            if isinstance(value, str):
                result[new_key] = value.strip().title()
            elif isinstance(value, (int, float)):
                result[new_key] = value * 1.1  # Apply some transformation
            else:
                result[new_key] = str(value)
        
        # Add metadata
        result["_processed_at"] = time.time()
        result["_processor"] = self.name
        result["_item_count"] = len(data)
        
        return result
    
    def _process_list(self, data: List[Any]) -> List[Any]:
        """Process list data."""
        result = []
        
        for i, item in enumerate(data):
            processed_item = {{
                "index": i,
                "original": item,
                "processed": str(item).upper() if isinstance(item, str) else item,
                "timestamp": time.time()
            }}
            result.append(processed_item)
        
        return result
    
    def _process_string(self, data: str) -> Dict[str, Any]:
        """Process string data."""
        words = data.split()
        
        return {{
            "original": data,
            "length": len(data),
            "word_count": len(words),
            "uppercase": data.upper(),
            "lowercase": data.lower(),
            "title_case": data.title(),
            "reversed": data[::-1],
            "processed_at": time.time(),
            "processor": self.name
        }}
    
    def _process_generic(self, data: Any) -> Dict[str, Any]:
        """Process generic data."""
        return {{
            "original": data,
            "type": type(data).__name__,
            "string_repr": str(data),
            "processed_at": time.time(),
            "processor": self.name
        }}
    
    def _cleanup_cache(self) -> None:
        """Cleanup old cache entries."""
        # Keep only the most recent 500 entries
        if len(self._cache) > 500:
            # Simple cleanup - remove half the entries
            keys_to_remove = list(self._cache.keys())[::2]
            for key in keys_to_remove:
                self._cache.pop(key, None)
            
            logger.info(f"Cache cleaned up, {{len(self._cache)}} entries remaining")
    
    async def process_async(self, data: Any) -> Any:
        """Asynchronous processing method."""
        loop = asyncio.get_event_loop()
        
        # Run the synchronous process method in a thread pool
        return await loop.run_in_executor(self._executor, self.process, data)
    
    def process_batch(self, data_list: List[Any]) -> List[Any]:
        """Process a batch of data items."""
        if not self._initialized:
            raise {class_name}Error("Component not initialized", 400)
        
        results = []
        batch_size = self.config.batch_size
        
        # Process in batches
        for i in range(0, len(data_list), batch_size):
            batch = data_list[i:i + batch_size]
            
            # Use thread pool for parallel processing
            if self._executor:
                futures = [self._executor.submit(self.process, item) for item in batch]
                batch_results = [future.result() for future in futures]
            else:
                batch_results = [self.process(item) for item in batch]
            
            results.extend(batch_results)
            
            # Log progress
            if i % (batch_size * 10) == 0:
                logger.info(f"Processed {{i + len(batch)}}/{{len(data_list)}} items")
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status."""
        uptime = time.time() - self._start_time if self._start_time else 0
        
        return {{
            "name": self.name,
            "initialized": self._initialized,
            "processing_count": self._processing_count,
            "error_count": self._error_count,
            "cache_size": len(self._cache),
            "uptime_seconds": uptime,
            "config": self.config.to_dict()
        }}
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            if self._executor:
                self._executor.shutdown(wait=True)
                self._executor = None
            
            self._cache.clear()
            self._initialized = False
            
            logger.info(f"{{self.name}} cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {{e}}")
    
    def __enter__(self):
        """Context manager entry."""
        if not self._initialized:
            self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create and test {class_name}
    processor = {class_name}("test_processor")
    
    with processor:
        # Test with different data types
        test_data = [
            {{"name": "test", "value": 42}},
            ["item1", "item2", "item3"],
            "Hello, World!",
            12345
        ]
        
        for data in test_data:
            try:
                result = processor.process(data)
                print(f"Processed {{type(data).__name__}}: {{result}}")
            except Exception as e:
                print(f"Error processing {{type(data).__name__}}: {{e}}")
        
        # Show status
        status = processor.get_status()
        print(f"Final status: {{status}}")
'''

        total_lines = 0
        files_created = 0

        # Generate files across different directories
        for i in range(num_files):
            # Determine directory and file name
            if i < num_files * 0.4:  # 40% in src/
                if i % 5 == 0:
                    dir_name = "src/core"
                elif i % 5 == 1:
                    dir_name = "src/models"
                elif i % 5 == 2:
                    dir_name = "src/services"
                elif i % 5 == 3:
                    dir_name = "src/utils"
                else:
                    dir_name = "src/api"
            elif i < num_files * 0.7:  # 30% in tests/
                if i % 3 == 0:
                    dir_name = "tests/unit"
                elif i % 3 == 1:
                    dir_name = "tests/integration"
                else:
                    dir_name = "tests/performance"
            else:  # 30% in scripts/ and tools/
                dir_name = "scripts" if i % 2 == 0 else "tools"

            module_name = f"module_{i:04d}"
            class_name = f"Component{i:04d}"

            file_path = self.project_path / dir_name / f"{module_name}.py"

            # Generate content
            content = class_template.format(
                module_name=module_name, class_name=class_name
            )

            # Write file
            with open(file_path, "w") as f:
                f.write(content)

            # Count lines
            file_lines = len(content.split("\n"))
            total_lines += file_lines
            files_created += 1

            # Progress update
            if i % 50 == 0:
                print(f"Generated {i}/{num_files} files ({total_lines:,} lines so far)")

        print(
            f"Created large Python project: {files_created} files, {total_lines:,} lines of code"
        )

        return {
            "files_created": files_created,
            "total_lines": total_lines,
            "directories": len(directories),
            "project_size_mb": self._calculate_project_size(),
        }

    def _calculate_project_size(self) -> float:
        """Calculate project size in MB."""
        total_size = 0
        for root, dirs, files in os.walk(self.project_path):
            for file in files:
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path)
        return total_size / (1024 * 1024)

    @pytest.mark.slow
    def test_100k_lines_indexing_performance(self):
        """Test indexing performance on 100k+ lines of code."""
        print("\n=== Testing 100k+ Lines Indexing Performance ===")

        # Create large project
        project_stats = self.create_large_python_project(target_lines=100000)
        print(f"Created project: {project_stats}")

        # Initialize indexing engine
        engine = IndexingEngine(str(self.project_path))

        # Track memory usage
        initial_memory = self.process.memory_info().rss / 1024 / 1024

        # Track progress
        progress_updates = []

        def progress_callback(current, total, message):
            progress_updates.append((current, total, message, time.time()))
            if current % 20 == 0 or current == total:
                print(f"Progress: {current}/{total} - {message}")

        engine.set_progress_callback(progress_callback)

        # Perform indexing
        start_time = time.time()
        result = engine.build_index()
        end_time = time.time()

        # Calculate metrics
        indexing_time = end_time - start_time
        peak_memory = self.process.memory_info().rss / 1024 / 1024
        memory_increase = peak_memory - initial_memory

        # Assertions
        assert result.success, f"Indexing failed: {result.errors}"
        assert result.ast_index is not None
        assert result.embeddings_count > 0

        # Performance assertions
        assert indexing_time < 600, f"Indexing took too long: {indexing_time:.2f}s"
        assert memory_increase < 2000, f"Memory usage too high: {memory_increase:.2f}MB"

        # Verify comprehensive indexing
        assert len(result.ast_index.functions) > 1000, "Should find many functions"
        assert len(result.ast_index.classes) > 100, "Should find many classes"
        assert result.embeddings_count > 500, "Should generate many embeddings"

        # Performance metrics
        lines_per_second = project_stats["total_lines"] / indexing_time
        files_per_second = project_stats["files_created"] / indexing_time

        print(f"\n=== Performance Results ===")
        print(f"Total indexing time: {indexing_time:.2f} seconds")
        print(f"Memory increase: {memory_increase:.2f} MB")
        print(f"Lines indexed: {project_stats['total_lines']:,}")
        print(f"Files indexed: {project_stats['files_created']}")
        print(f"Functions found: {len(result.ast_index.functions):,}")
        print(f"Classes found: {len(result.ast_index.classes):,}")
        print(f"Embeddings generated: {result.embeddings_count:,}")
        print(f"Processing speed: {lines_per_second:.0f} lines/second")
        print(f"File processing speed: {files_per_second:.1f} files/second")
        print(f"Progress updates: {len(progress_updates)}")

        # Verify index persistence
        metadata = engine.get_index_metadata()
        assert metadata is not None
        assert metadata.total_files == project_stats["files_created"]
        assert (
            metadata.total_lines >= project_stats["total_lines"] * 0.9
        )  # Allow some variance

        print("✓ Large codebase indexing test passed!")

    @pytest.mark.slow
    def test_memory_usage_profiling(self):
        """Test memory usage during indexing with profiling."""
        print("\n=== Testing Memory Usage Profiling ===")

        # Create medium-sized project for detailed memory tracking
        project_stats = self.create_large_python_project(target_lines=50000)

        engine = IndexingEngine(str(self.project_path))

        # Memory tracking
        memory_samples = []

        def track_memory():
            """Track memory usage over time."""
            while hasattr(track_memory, "running"):
                memory_mb = self.process.memory_info().rss / 1024 / 1024
                memory_samples.append((time.time(), memory_mb))
                time.sleep(0.5)  # Sample every 500ms

        # Start memory tracking in background
        import threading

        track_memory.running = True
        memory_thread = threading.Thread(target=track_memory)
        memory_thread.start()

        try:
            # Perform indexing
            start_time = time.time()
            result = engine.build_index()
            end_time = time.time()

        finally:
            # Stop memory tracking
            track_memory.running = False
            memory_thread.join()

        # Analyze memory usage
        if memory_samples:
            initial_memory = memory_samples[0][1]
            peak_memory = max(sample[1] for sample in memory_samples)
            final_memory = memory_samples[-1][1]

            memory_increase = peak_memory - initial_memory
            memory_retained = final_memory - initial_memory

            print(f"\n=== Memory Usage Analysis ===")
            print(f"Initial memory: {initial_memory:.2f} MB")
            print(f"Peak memory: {peak_memory:.2f} MB")
            print(f"Final memory: {final_memory:.2f} MB")
            print(f"Peak increase: {memory_increase:.2f} MB")
            print(f"Memory retained: {memory_retained:.2f} MB")
            print(f"Memory samples collected: {len(memory_samples)}")

            # Assertions
            assert result.success
            assert memory_increase < 1500, (
                f"Peak memory usage too high: {memory_increase:.2f}MB"
            )
            assert memory_retained < 500, (
                f"Too much memory retained: {memory_retained:.2f}MB"
            )

            # Memory efficiency check
            mb_per_1k_lines = memory_increase / (project_stats["total_lines"] / 1000)
            print(f"Memory efficiency: {mb_per_1k_lines:.2f} MB per 1k lines")
            assert mb_per_1k_lines < 50, (
                f"Memory efficiency too low: {mb_per_1k_lines:.2f} MB/1k lines"
            )

        print("✓ Memory usage profiling test passed!")

    def test_incremental_indexing_performance(self):
        """Test performance of incremental indexing updates."""
        print("\n=== Testing Incremental Indexing Performance ===")

        # Create initial project
        project_stats = self.create_large_python_project(target_lines=30000)

        engine = IndexingEngine(str(self.project_path))

        # Initial indexing
        print("Performing initial indexing...")
        start_time = time.time()
        result1 = engine.build_index()
        initial_time = time.time() - start_time

        assert result1.success
        initial_functions = len(result1.ast_index.functions)
        initial_classes = len(result1.ast_index.classes)

        # Modify some files
        print("Modifying files...")
        src_dir = self.project_path / "src" / "core"
        modified_files = list(src_dir.glob("*.py"))[:5]  # Modify first 5 files

        for i, file_path in enumerate(modified_files):
            with open(file_path, "a") as f:
                f.write(f'''

# Added during incremental test
class IncrementalClass{i}:
    """Class added during incremental indexing test."""
    
    def __init__(self, value: int = {i}):
        self.value = value
    
    def incremental_method_{i}(self) -> int:
        """Method added during incremental test."""
        return self.value * {i + 1}

def incremental_function_{i}(x: int) -> int:
    """Function added during incremental test."""
    return x + {i * 10}
''')

        # Re-index
        print("Performing incremental indexing...")
        start_time = time.time()
        result2 = engine.build_index()
        reindex_time = time.time() - start_time

        assert result2.success

        # Verify changes were detected
        new_functions = len(result2.ast_index.functions) - initial_functions
        new_classes = len(result2.ast_index.classes) - initial_classes

        print(f"\n=== Incremental Indexing Results ===")
        print(f"Initial indexing time: {initial_time:.2f} seconds")
        print(f"Re-indexing time: {reindex_time:.2f} seconds")
        print(f"Speedup ratio: {initial_time / reindex_time:.2f}x")
        print(f"New functions found: {new_functions}")
        print(f"New classes found: {new_classes}")

        # Assertions
        assert new_functions >= 5, (
            f"Should find at least 5 new functions, found {new_functions}"
        )
        assert new_classes >= 5, (
            f"Should find at least 5 new classes, found {new_classes}"
        )

        # Performance assertion - re-indexing should be reasonably fast
        # (not necessarily faster due to the overhead of change detection)
        assert reindex_time < initial_time * 2, (
            "Re-indexing took too long compared to initial"
        )

        print("✓ Incremental indexing performance test passed!")

    def test_query_performance_at_scale(self):
        """Test vector similarity query performance on large index."""
        print("\n=== Testing Query Performance at Scale ===")

        # Create large project
        project_stats = self.create_large_python_project(target_lines=75000)

        engine = IndexingEngine(str(self.project_path))

        # Build index
        print("Building index for query testing...")
        result = engine.build_index()
        assert result.success

        # Test various query types and measure performance
        queries = [
            "class definition with methods",
            "function that processes data",
            "error handling and exceptions",
            "async function with await",
            "decorator pattern implementation",
            "factory method pattern",
            "configuration management",
            "database connection handling",
            "logging and monitoring",
            "batch processing algorithm",
        ]

        query_times = []
        total_matches = 0

        print("Running query performance tests...")
        for i, query in enumerate(queries):
            start_time = time.time()
            matches = engine.query_similar_code(query, limit=20)
            query_time = time.time() - start_time

            query_times.append(query_time)
            total_matches += len(matches)

            print(
                f"Query {i + 1}: '{query[:30]}...' - {len(matches)} matches in {query_time:.3f}s"
            )

            # Each query should complete quickly
            assert query_time < 2.0, f"Query took too long: {query_time:.3f}s"

        # Calculate statistics
        avg_query_time = sum(query_times) / len(query_times)
        max_query_time = max(query_times)
        min_query_time = min(query_times)

        print(f"\n=== Query Performance Results ===")
        print(f"Total queries: {len(queries)}")
        print(f"Average query time: {avg_query_time:.3f} seconds")
        print(f"Min query time: {min_query_time:.3f} seconds")
        print(f"Max query time: {max_query_time:.3f} seconds")
        print(f"Total matches found: {total_matches}")
        print(f"Average matches per query: {total_matches / len(queries):.1f}")

        # Performance assertions
        assert avg_query_time < 1.0, (
            f"Average query time too slow: {avg_query_time:.3f}s"
        )
        assert max_query_time < 2.0, f"Slowest query too slow: {max_query_time:.3f}s"
        assert total_matches > 0, "Should find some matches"

        print("✓ Query performance at scale test passed!")


if __name__ == "__main__":
    # Run the tests manually for debugging
    test_instance = TestLargeCodebaseIntegration()

    print("Running large codebase integration tests...")

    test_instance.setup_method()
    try:
        # Run individual tests
        test_instance.test_100k_lines_indexing_performance()
        test_instance.test_memory_usage_profiling()
        test_instance.test_incremental_indexing_performance()
        test_instance.test_query_performance_at_scale()

        print("\n✅ All large codebase integration tests passed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise
    finally:
        test_instance.teardown_method()
