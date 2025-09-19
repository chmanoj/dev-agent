"""Performance benchmarks for indexing and query operations."""

import os
import time
import tempfile
import shutil
import psutil
import statistics
from pathlib import Path
import pytest
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from dev_agent.indexing.indexing_engine import IndexingEngine
from dev_agent.indexing.vector_database import VectorDatabase
from dev_agent.indexing.tree_sitter_parser import TreeSitterParser


class TestPerformanceBenchmarks:
    """Performance benchmarks for core components."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "benchmark_project"
        self.project_path.mkdir(parents=True)

        # Track system resources
        self.process = psutil.Process()
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB

    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def create_benchmark_project(
        self, num_files: int = 50, lines_per_file: int = 500
    ) -> Dict[str, Any]:
        """Create a project for benchmarking.

        Args:
            num_files: Number of Python files to create
            lines_per_file: Average lines per file

        Returns:
            Dictionary with project statistics
        """
        # Create directory structure
        directories = ["src", "tests", "utils", "models", "services"]
        for dir_name in directories:
            (self.project_path / dir_name).mkdir(exist_ok=True)

        # Template for Python files with various complexity patterns
        templates = [
            self._get_class_template(),
            self._get_function_template(),
            self._get_async_template(),
            self._get_decorator_template(),
            self._get_dataclass_template(),
        ]

        total_lines = 0
        files_created = 0

        for i in range(num_files):
            # Choose template and directory
            template = templates[i % len(templates)]
            directory = directories[i % len(directories)]

            # Generate file content
            module_name = f"module_{i:03d}"
            class_name = f"BenchmarkClass{i:03d}"

            content = template.format(
                module_name=module_name, class_name=class_name, file_index=i
            )

            # Adjust content length to target lines per file
            current_lines = len(content.split("\n"))
            if current_lines < lines_per_file:
                # Add extra methods to reach target
                extra_methods = []
                for j in range((lines_per_file - current_lines) // 10):
                    extra_methods.append(f'''
    def extra_method_{j}(self, param: Any) -> Any:
        """Extra method {j} for benchmarking."""
        result = param
        for k in range(5):
            result = str(result) + f"_{{k}}"
        return result
''')
                content += "\n".join(extra_methods)

            # Write file
            file_path = self.project_path / directory / f"{module_name}.py"
            with open(file_path, "w") as f:
                f.write(content)

            total_lines += len(content.split("\n"))
            files_created += 1

        return {
            "files_created": files_created,
            "total_lines": total_lines,
            "directories": len(directories),
            "avg_lines_per_file": total_lines / files_created
            if files_created > 0
            else 0,
        }

    def _get_class_template(self) -> str:
        """Get template for class-based modules."""
        return '''"""Module {module_name} - Class-based implementation."""

import os
import sys
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod


class {class_name}(ABC):
    """Abstract base class for {class_name}."""
    
    def __init__(self, name: str, config: Optional[Dict] = None):
        self.name = name
        self.config = config or {{}}
        self._initialized = False
        self._data = {{}}
    
    @abstractmethod
    def process(self, data: Any) -> Any:
        """Process data - must be implemented by subclasses."""
        pass
    
    def initialize(self) -> bool:
        """Initialize the component."""
        try:
            self._initialized = True
            return True
        except Exception:
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status."""
        return {{
            "name": self.name,
            "initialized": self._initialized,
            "data_count": len(self._data)
        }}


class Concrete{class_name}({class_name}):
    """Concrete implementation of {class_name}."""
    
    def process(self, data: Any) -> Any:
        """Process data implementation."""
        if not self._initialized:
            raise RuntimeError("Component not initialized")
        
        # Store data
        key = f"item_{{len(self._data)}}"
        self._data[key] = data
        
        # Process based on type
        if isinstance(data, dict):
            return self._process_dict(data)
        elif isinstance(data, list):
            return self._process_list(data)
        else:
            return self._process_generic(data)
    
    def _process_dict(self, data: Dict) -> Dict:
        """Process dictionary data."""
        result = {{}}
        for key, value in data.items():
            result[f"processed_{{key}}"] = str(value).upper()
        return result
    
    def _process_list(self, data: List) -> List:
        """Process list data."""
        return [f"processed_{{item}}" for item in data]
    
    def _process_generic(self, data: Any) -> str:
        """Process generic data."""
        return f"processed_{{str(data)}}"
'''

    def _get_function_template(self) -> str:
        """Get template for function-based modules."""
        return '''"""Module {module_name} - Function-based implementation."""

import math
import random
from typing import List, Dict, Any, Optional, Callable
from functools import wraps, lru_cache


def benchmark_decorator(func: Callable) -> Callable:
    """Decorator for benchmarking functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            print(f"{{func.__name__}} took {{end_time - start_time:.4f}} seconds")
            return result
        except Exception as e:
            print(f"{{func.__name__}} failed: {{e}}")
            raise
    return wrapper


@lru_cache(maxsize=128)
def fibonacci(n: int) -> int:
    """Calculate fibonacci number with caching."""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


@benchmark_decorator
def complex_calculation(data: List[float]) -> Dict[str, float]:
    """Perform complex mathematical calculations."""
    if not data:
        return {{"error": "No data provided"}}
    
    result = {{
        "sum": sum(data),
        "mean": sum(data) / len(data),
        "min": min(data),
        "max": max(data),
        "std_dev": math.sqrt(sum((x - sum(data)/len(data))**2 for x in data) / len(data))
    }}
    
    # Add some complex calculations
    result["geometric_mean"] = math.pow(math.prod(data), 1/len(data))
    result["harmonic_mean"] = len(data) / sum(1/x for x in data if x != 0)
    
    return result


def process_data_batch(data_list: List[Any], batch_size: int = 10) -> List[Any]:
    """Process data in batches."""
    results = []
    
    for i in range(0, len(data_list), batch_size):
        batch = data_list[i:i + batch_size]
        batch_results = []
        
        for item in batch:
            if isinstance(item, (int, float)):
                # Numerical processing
                processed = {{
                    "original": item,
                    "squared": item ** 2,
                    "sqrt": math.sqrt(abs(item)),
                    "fibonacci": fibonacci(min(abs(int(item)), 30))
                }}
            else:
                # String processing
                processed = {{
                    "original": str(item),
                    "length": len(str(item)),
                    "reversed": str(item)[::-1],
                    "hash": hash(str(item))
                }}
            
            batch_results.append(processed)
        
        results.extend(batch_results)
    
    return results


def generate_test_data(size: int = 1000) -> List[Any]:
    """Generate test data for benchmarking."""
    data = []
    
    for i in range(size):
        if i % 3 == 0:
            data.append(random.randint(1, 100))
        elif i % 3 == 1:
            data.append(random.uniform(0.1, 10.0))
        else:
            data.append(f"test_string_{{i}}")
    
    return data
'''

    def _get_async_template(self) -> str:
        """Get template for async-based modules."""
        return '''"""Module {module_name} - Async implementation."""

import asyncio
import aiohttp
import time
from typing import List, Dict, Any, Optional, Coroutine
from concurrent.futures import ThreadPoolExecutor


class Async{class_name}:
    """Async implementation for {class_name}."""
    
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def process_async(self, data: Any) -> Any:
        """Process data asynchronously."""
        async with self.semaphore:
            # Simulate async processing
            await asyncio.sleep(0.01)  # Small delay
            
            if isinstance(data, dict):
                return await self._process_dict_async(data)
            elif isinstance(data, list):
                return await self._process_list_async(data)
            else:
                return await self._process_generic_async(data)
    
    async def _process_dict_async(self, data: Dict) -> Dict:
        """Process dictionary asynchronously."""
        tasks = []
        for key, value in data.items():
            task = self._process_item_async(key, value)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return dict(results)
    
    async def _process_list_async(self, data: List) -> List:
        """Process list asynchronously."""
        tasks = [self._process_item_async(i, item) for i, item in enumerate(data)]
        results = await asyncio.gather(*tasks)
        return [result[1] for result in results]
    
    async def _process_generic_async(self, data: Any) -> str:
        """Process generic data asynchronously."""
        await asyncio.sleep(0.001)  # Simulate processing
        return f"async_processed_{{str(data)}}"
    
    async def _process_item_async(self, key: Any, value: Any) -> tuple:
        """Process individual item asynchronously."""
        # Simulate CPU-bound work in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor,
            self._cpu_bound_work,
            value
        )
        return (key, result)
    
    def _cpu_bound_work(self, value: Any) -> str:
        """CPU-bound work to run in thread pool."""
        # Simulate some computation
        result = str(value)
        for _ in range(100):
            result = str(hash(result))
        return result
    
    async def process_batch_async(self, data_list: List[Any]) -> List[Any]:
        """Process batch of data asynchronously."""
        tasks = [self.process_async(item) for item in data_list]
        return await asyncio.gather(*tasks)
    
    async def cleanup(self):
        """Cleanup resources."""
        self.executor.shutdown(wait=True)


async def benchmark_async_operations(data_size: int = 100) -> Dict[str, float]:
    """Benchmark async operations."""
    processor = Async{class_name}()
    
    # Generate test data
    test_data = [f"item_{{i}}" for i in range(data_size)]
    
    # Benchmark processing
    start_time = time.time()
    results = await processor.process_batch_async(test_data)
    end_time = time.time()
    
    await processor.cleanup()
    
    return {{
        "total_time": end_time - start_time,
        "items_processed": len(results),
        "items_per_second": len(results) / (end_time - start_time)
    }}
'''

    def _get_decorator_template(self) -> str:
        """Get template for decorator-heavy modules."""
        return '''"""Module {module_name} - Decorator-heavy implementation."""

import time
import functools
from typing import Any, Callable, Dict, List
from dataclasses import dataclass


def timing_decorator(func: Callable) -> Callable:
    """Decorator to measure execution time."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{{func.__name__}} took {{end - start:.4f}} seconds")
        return result
    return wrapper


def retry_decorator(max_attempts: int = 3):
    """Decorator to retry failed operations."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise e
                    time.sleep(0.1 * (2 ** attempt))
            return None
        return wrapper
    return decorator


def cache_decorator(maxsize: int = 128):
    """Custom caching decorator."""
    def decorator(func: Callable) -> Callable:
        cache = {{}}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            key = str(args) + str(sorted(kwargs.items()))
            
            if key in cache:
                return cache[key]
            
            result = func(*args, **kwargs)
            
            # Manage cache size
            if len(cache) >= maxsize:
                # Remove oldest entry
                oldest_key = next(iter(cache))
                del cache[oldest_key]
            
            cache[key] = result
            return result
        
        wrapper.cache_info = lambda: {{"size": len(cache), "maxsize": maxsize}}
        wrapper.cache_clear = lambda: cache.clear()
        
        return wrapper
    return decorator


class {class_name}:
    """Class with heavily decorated methods."""
    
    def __init__(self, name: str):
        self.name = name
        self._call_count = 0
    
    @timing_decorator
    @retry_decorator(max_attempts=3)
    def complex_operation(self, data: Any) -> Any:
        """Complex operation with multiple decorators."""
        self._call_count += 1
        
        # Simulate potential failure
        if self._call_count % 10 == 0:
            raise ValueError("Simulated failure")
        
        # Perform complex processing
        if isinstance(data, (list, tuple)):
            return [self._process_item(item) for item in data]
        else:
            return self._process_item(data)
    
    @cache_decorator(maxsize=64)
    def cached_calculation(self, n: int) -> int:
        """Expensive calculation with caching."""
        if n <= 1:
            return n
        
        # Simulate expensive calculation
        result = 0
        for i in range(n):
            result += i * i
        
        return result
    
    @timing_decorator
    def batch_process(self, items: List[Any]) -> List[Any]:
        """Process items in batch."""
        results = []
        
        for item in items:
            try:
                result = self.complex_operation(item)
                results.append(result)
            except Exception as e:
                results.append(f"Error: {{e}}")
        
        return results
    
    def _process_item(self, item: Any) -> str:
        """Process individual item."""
        # Simulate processing time
        time.sleep(0.001)
        return f"processed_{{self.name}}_{{item}}"
'''

    def _get_dataclass_template(self) -> str:
        """Get template for dataclass-heavy modules."""
        return '''"""Module {module_name} - Dataclass-heavy implementation."""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


@dataclass
class {class_name}Config:
    """Configuration dataclass."""
    name: str
    version: str = "1.0.0"
    debug: bool = False
    max_items: int = 1000
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class {class_name}Item:
    """Data item dataclass."""
    id: int
    name: str
    value: float
    category: str
    active: bool = True
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "{class_name}Item":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class {class_name}Result:
    """Result dataclass."""
    success: bool
    message: str
    data: List[{class_name}Item] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class {class_name}Processor:
    """Processor using dataclasses."""
    
    def __init__(self, config: {class_name}Config):
        self.config = config
        self.items: List[{class_name}Item] = []
    
    def add_item(self, item: {class_name}Item) -> bool:
        """Add item to processor."""
        if len(self.items) >= self.config.max_items:
            return False
        
        self.items.append(item)
        return True
    
    def process_items(self) -> {class_name}Result:
        """Process all items."""
        start_time = time.time()
        errors = []
        processed_items = []
        
        for item in self.items:
            try:
                processed_item = self._process_single_item(item)
                processed_items.append(processed_item)
            except Exception as e:
                errors.append(f"Error processing item {{item.id}}: {{e}}")
        
        end_time = time.time()
        
        return {class_name}Result(
            success=len(errors) == 0,
            message=f"Processed {{len(processed_items)}} items",
            data=processed_items,
            errors=errors,
            processing_time=end_time - start_time
        )
    
    def _process_single_item(self, item: {class_name}Item) -> {class_name}Item:
        """Process a single item."""
        # Create processed copy
        processed = {class_name}Item(
            id=item.id,
            name=f"processed_{{item.name}}",
            value=item.value * 1.1,
            category=item.category.upper(),
            active=item.active,
            properties={{**item.properties, "processed": True}},
            created_at=datetime.now()
        )
        
        return processed
    
    def export_to_json(self) -> str:
        """Export items to JSON."""
        data = {{
            "config": asdict(self.config),
            "items": [item.to_dict() for item in self.items],
            "count": len(self.items)
        }}
        
        return json.dumps(data, indent=2, default=str)
'''

    def test_indexing_performance_scaling(self):
        """Test how indexing performance scales with project size."""
        print("\n=== Testing Indexing Performance Scaling ===")

        # Test different project sizes
        test_sizes = [
            (10, 200),  # Small: 10 files, 200 lines each
            (25, 400),  # Medium: 25 files, 400 lines each
            (50, 600),  # Large: 50 files, 600 lines each
        ]

        scaling_results = []

        for num_files, lines_per_file in test_sizes:
            print(f"\nTesting {num_files} files with {lines_per_file} lines each...")

            # Create project
            project_stats = self.create_benchmark_project(num_files, lines_per_file)
            total_lines = project_stats["total_lines"]

            # Initialize indexing engine
            engine = IndexingEngine(str(self.project_path))

            # Measure indexing performance
            start_time = time.time()
            initial_memory = self.process.memory_info().rss / 1024 / 1024

            result = engine.build_index()

            end_time = time.time()
            peak_memory = self.process.memory_info().rss / 1024 / 1024

            # Calculate metrics
            indexing_time = end_time - start_time
            memory_increase = peak_memory - initial_memory
            lines_per_second = total_lines / indexing_time

            scaling_results.append(
                {
                    "files": num_files,
                    "lines": total_lines,
                    "time": indexing_time,
                    "memory_mb": memory_increase,
                    "lines_per_second": lines_per_second,
                    "functions_found": len(result.ast_index.functions),
                    "classes_found": len(result.ast_index.classes),
                    "embeddings": result.embeddings_count,
                }
            )

            # Assertions
            assert result.success, f"Indexing should succeed for {num_files} files"
            assert indexing_time < 120, f"Indexing too slow: {indexing_time:.2f}s"
            assert memory_increase < 1000, (
                f"Memory usage too high: {memory_increase:.2f}MB"
            )

            print(f"  Time: {indexing_time:.2f}s")
            print(f"  Speed: {lines_per_second:.0f} lines/second")
            print(f"  Memory: {memory_increase:.2f}MB")
            print(f"  Functions: {len(result.ast_index.functions)}")
            print(f"  Classes: {len(result.ast_index.classes)}")

            # Clean up for next iteration
            self.teardown_method()
            self.setup_method()

        # Analyze scaling characteristics
        print(f"\n=== Scaling Analysis ===")
        for i, result in enumerate(scaling_results):
            print(f"Size {i + 1}: {result['files']} files, {result['lines']:,} lines")
            print(f"  Performance: {result['lines_per_second']:.0f} lines/s")
            print(
                f"  Memory efficiency: {result['memory_mb'] / result['lines'] * 1000:.2f} MB/1k lines"
            )

        # Check that performance doesn't degrade significantly
        speeds = [r["lines_per_second"] for r in scaling_results]
        if len(speeds) > 1:
            speed_ratio = min(speeds) / max(speeds)
            assert speed_ratio > 0.3, (
                f"Performance degrades too much: {speed_ratio:.2f}"
            )
            print(f"Performance consistency ratio: {speed_ratio:.2f}")

        print("✓ Indexing performance scaling test passed!")

    def test_query_performance_benchmarks(self):
        """Benchmark vector similarity query performance."""
        print("\n=== Testing Query Performance Benchmarks ===")

        # Create medium-sized project for query testing
        project_stats = self.create_benchmark_project(40, 500)

        engine = IndexingEngine(str(self.project_path))
        result = engine.build_index()
        assert result.success

        # Define different types of queries
        query_categories = {
            "simple": ["function definition", "class method", "import statement"],
            "complex": [
                "async function with error handling",
                "decorator pattern implementation",
                "dataclass with validation methods",
            ],
            "specific": [
                "fibonacci calculation with caching",
                "batch processing with thread pool",
                "configuration management system",
            ],
        }

        benchmark_results = {}

        for category, queries in query_categories.items():
            print(f"\nBenchmarking {category} queries...")

            query_times = []
            total_matches = 0

            for query in queries:
                # Warm up query (not counted)
                engine.query_similar_code(query, limit=5)

                # Benchmark query
                start_time = time.time()
                matches = engine.query_similar_code(query, limit=20)
                end_time = time.time()

                query_time = end_time - start_time
                query_times.append(query_time)
                total_matches += len(matches)

                print(
                    f"  '{query[:40]}...' - {len(matches)} matches in {query_time:.3f}s"
                )

            # Calculate statistics
            avg_time = statistics.mean(query_times)
            median_time = statistics.median(query_times)
            max_time = max(query_times)
            min_time = min(query_times)

            benchmark_results[category] = {
                "avg_time": avg_time,
                "median_time": median_time,
                "max_time": max_time,
                "min_time": min_time,
                "total_matches": total_matches,
                "queries_count": len(queries),
            }

            print(f"  Average: {avg_time:.3f}s, Median: {median_time:.3f}s")
            print(f"  Range: {min_time:.3f}s - {max_time:.3f}s")
            print(f"  Total matches: {total_matches}")

            # Performance assertions
            assert avg_time < 1.0, (
                f"{category} queries too slow: {avg_time:.3f}s average"
            )
            assert max_time < 2.0, f"{category} slowest query too slow: {max_time:.3f}s"

        # Overall performance summary
        print(f"\n=== Query Performance Summary ===")
        all_times = []
        for category, results in benchmark_results.items():
            all_times.extend([results["avg_time"]] * results["queries_count"])
            print(f"{category.capitalize()}: {results['avg_time']:.3f}s average")

        overall_avg = statistics.mean(all_times)
        print(f"Overall average: {overall_avg:.3f}s")

        assert overall_avg < 0.8, (
            f"Overall query performance too slow: {overall_avg:.3f}s"
        )

        print("✓ Query performance benchmarks test passed!")

    def test_concurrent_operations_performance(self):
        """Test performance of concurrent indexing and query operations."""
        print("\n=== Testing Concurrent Operations Performance ===")

        # Create project for concurrent testing
        project_stats = self.create_benchmark_project(30, 400)

        engine = IndexingEngine(str(self.project_path))
        result = engine.build_index()
        assert result.success

        # Test concurrent queries
        queries = [
            "function with parameters",
            "class inheritance pattern",
            "async method implementation",
            "decorator usage example",
            "error handling code",
            "data processing logic",
            "configuration setup",
            "utility function",
            "test case implementation",
            "import and export",
        ]

        # Sequential benchmark
        print("Running sequential queries...")
        start_time = time.time()
        sequential_results = []
        for query in queries:
            matches = engine.query_similar_code(query, limit=10)
            sequential_results.append(len(matches))
        sequential_time = time.time() - start_time

        # Concurrent benchmark
        print("Running concurrent queries...")
        start_time = time.time()

        def run_query(query):
            return engine.query_similar_code(query, limit=10)

        concurrent_results = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_query = {
                executor.submit(run_query, query): query for query in queries
            }

            for future in as_completed(future_to_query):
                matches = future.result()
                concurrent_results.append(len(matches))

        concurrent_time = time.time() - start_time

        # Analyze results
        print(f"\n=== Concurrent Performance Results ===")
        print(f"Sequential time: {sequential_time:.3f}s")
        print(f"Concurrent time: {concurrent_time:.3f}s")

        if concurrent_time < sequential_time:
            speedup = sequential_time / concurrent_time
            print(f"Speedup achieved: {speedup:.2f}x")
        else:
            slowdown = concurrent_time / sequential_time
            print(f"Slowdown: {slowdown:.2f}x")

        # Verify results consistency
        assert len(sequential_results) == len(concurrent_results)

        # Results should be similar (allowing for some variance due to concurrency)
        total_sequential = sum(sequential_results)
        total_concurrent = sum(concurrent_results)
        variance = abs(total_sequential - total_concurrent) / total_sequential

        print(f"Results variance: {variance:.2%}")
        assert variance < 0.1, f"Concurrent results too different: {variance:.2%}"

        # Performance should not degrade significantly
        assert concurrent_time < sequential_time * 1.5, "Concurrent operations too slow"

        print("✓ Concurrent operations performance test passed!")

    def test_memory_usage_optimization(self):
        """Test memory usage optimization during indexing."""
        print("\n=== Testing Memory Usage Optimization ===")

        # Create larger project to test memory optimization
        project_stats = self.create_benchmark_project(60, 800)

        engine = IndexingEngine(str(self.project_path))

        # Track memory usage throughout indexing
        memory_samples = []

        def memory_tracker():
            """Track memory usage in background."""
            while hasattr(memory_tracker, "running"):
                memory_mb = self.process.memory_info().rss / 1024 / 1024
                memory_samples.append((time.time(), memory_mb))
                time.sleep(0.2)  # Sample every 200ms

        # Start memory tracking
        import threading

        memory_tracker.running = True
        memory_thread = threading.Thread(target=memory_tracker)
        memory_thread.start()

        try:
            # Perform indexing
            start_time = time.time()
            result = engine.build_index()
            end_time = time.time()

        finally:
            # Stop memory tracking
            memory_tracker.running = False
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
            print(
                f"Memory efficiency: {memory_increase / project_stats['total_lines'] * 1000:.2f} MB per 1k lines"
            )

            # Memory optimization assertions
            assert result.success, "Indexing should succeed"
            assert memory_increase < 1500, (
                f"Peak memory too high: {memory_increase:.2f}MB"
            )
            assert memory_retained < 800, (
                f"Too much memory retained: {memory_retained:.2f}MB"
            )

            # Memory should be released after indexing
            retention_ratio = (
                memory_retained / memory_increase if memory_increase > 0 else 0
            )
            print(f"Memory retention ratio: {retention_ratio:.2%}")
            assert retention_ratio < 0.7, (
                f"Too much memory retained: {retention_ratio:.2%}"
            )

            # Memory efficiency check
            mb_per_1k_lines = memory_increase / (project_stats["total_lines"] / 1000)
            assert mb_per_1k_lines < 60, (
                f"Memory efficiency too low: {mb_per_1k_lines:.2f} MB/1k lines"
            )

        print("✓ Memory usage optimization test passed!")

    def test_tree_sitter_parsing_performance(self):
        """Benchmark Tree-sitter parsing performance."""
        print("\n=== Testing Tree-sitter Parsing Performance ===")

        # Create project with various Python language features
        project_stats = self.create_benchmark_project(35, 600)

        parser = TreeSitterParser()

        # Get all Python files
        python_files = list(self.project_path.rglob("*.py"))

        # Benchmark parsing performance
        parsing_times = []
        total_functions = 0
        total_classes = 0
        total_symbols = 0

        print(f"Parsing {len(python_files)} Python files...")

        for i, file_path in enumerate(python_files):
            start_time = time.time()

            # Parse file
            ast = parser.parse_file(str(file_path), "python")

            if ast:
                # Extract information
                functions = parser.get_function_definitions(ast, str(file_path))
                classes = parser.get_class_definitions(ast, str(file_path))
                symbols = parser.extract_symbols(ast, str(file_path))

                total_functions += len(functions)
                total_classes += len(classes)
                total_symbols += len(symbols)

            end_time = time.time()
            parsing_time = end_time - start_time
            parsing_times.append(parsing_time)

            if i % 10 == 0:
                print(f"  Parsed {i + 1}/{len(python_files)} files")

        # Calculate statistics
        total_parsing_time = sum(parsing_times)
        avg_parsing_time = statistics.mean(parsing_times)
        median_parsing_time = statistics.median(parsing_times)
        max_parsing_time = max(parsing_times)

        files_per_second = len(python_files) / total_parsing_time
        lines_per_second = project_stats["total_lines"] / total_parsing_time

        print(f"\n=== Tree-sitter Performance Results ===")
        print(f"Total parsing time: {total_parsing_time:.3f}s")
        print(f"Average time per file: {avg_parsing_time:.3f}s")
        print(f"Median time per file: {median_parsing_time:.3f}s")
        print(f"Slowest file: {max_parsing_time:.3f}s")
        print(f"Files per second: {files_per_second:.1f}")
        print(f"Lines per second: {lines_per_second:.0f}")
        print(f"Functions found: {total_functions}")
        print(f"Classes found: {total_classes}")
        print(f"Symbols found: {total_symbols}")

        # Performance assertions
        assert avg_parsing_time < 0.1, (
            f"Average parsing too slow: {avg_parsing_time:.3f}s"
        )
        assert max_parsing_time < 0.5, (
            f"Slowest parsing too slow: {max_parsing_time:.3f}s"
        )
        assert files_per_second > 20, (
            f"File processing too slow: {files_per_second:.1f} files/s"
        )
        assert lines_per_second > 5000, (
            f"Line processing too slow: {lines_per_second:.0f} lines/s"
        )

        # Verify extraction quality
        assert total_functions > 50, (
            f"Should find many functions, found {total_functions}"
        )
        assert total_classes > 20, f"Should find many classes, found {total_classes}"
        assert total_symbols > 100, f"Should find many symbols, found {total_symbols}"

        print("✓ Tree-sitter parsing performance test passed!")

    def test_vector_database_performance(self):
        """Benchmark vector database operations."""
        print("\n=== Testing Vector Database Performance ===")

        # Create project and generate embeddings
        project_stats = self.create_benchmark_project(25, 400)

        engine = IndexingEngine(str(self.project_path))
        result = engine.build_index()
        assert result.success

        vector_db = engine.vector_db

        # Test embedding storage performance
        print("Testing embedding storage performance...")

        # Generate test chunks for storage benchmark
        test_chunks = []
        for i in range(100):
            test_chunks.append(f"def test_function_{i}():\n    return {i} * 2")

        start_time = time.time()
        chunk_ids = vector_db.store_embeddings(test_chunks)
        storage_time = time.time() - start_time

        embeddings_per_second = len(test_chunks) / storage_time

        print(f"Storage performance: {embeddings_per_second:.1f} embeddings/second")
        assert embeddings_per_second > 10, (
            f"Storage too slow: {embeddings_per_second:.1f} emb/s"
        )

        # Test query performance with different result sizes
        query_sizes = [5, 10, 20, 50]
        query_performance = {}

        test_queries = [
            "function definition with parameters",
            "class method implementation",
            "error handling code",
            "data processing logic",
        ]

        for size in query_sizes:
            print(f"Testing queries with {size} results...")

            query_times = []
            for query in test_queries:
                start_time = time.time()
                matches = vector_db.query_similar(query, k=size)
                end_time = time.time()

                query_times.append(end_time - start_time)

            avg_time = statistics.mean(query_times)
            query_performance[size] = avg_time

            print(f"  Average query time: {avg_time:.3f}s")
            assert avg_time < 1.0, f"Query too slow for size {size}: {avg_time:.3f}s"

        # Test batch query performance
        print("Testing batch query performance...")

        start_time = time.time()
        batch_results = []
        for query in test_queries:
            matches = vector_db.query_similar(query, k=10)
            batch_results.append(len(matches))
        batch_time = time.time() - start_time

        queries_per_second = len(test_queries) / batch_time

        print(f"Batch query performance: {queries_per_second:.1f} queries/second")
        assert queries_per_second > 5, (
            f"Batch queries too slow: {queries_per_second:.1f} q/s"
        )

        # Verify query scaling
        print(f"\n=== Vector DB Performance Summary ===")
        print(f"Storage: {embeddings_per_second:.1f} embeddings/second")
        print(f"Batch queries: {queries_per_second:.1f} queries/second")

        for size, time_taken in query_performance.items():
            print(f"Query size {size}: {time_taken:.3f}s average")

        # Check that query time doesn't scale linearly with result size
        small_time = query_performance[5]
        large_time = query_performance[50]
        scaling_factor = large_time / small_time

        print(f"Query scaling factor (50x vs 5x): {scaling_factor:.2f}")
        assert scaling_factor < 5, f"Query scaling too poor: {scaling_factor:.2f}x"

        print("✓ Vector database performance test passed!")


if __name__ == "__main__":
    # Run the benchmarks manually for debugging
    test_instance = TestPerformanceBenchmarks()

    print("Running performance benchmarks...")

    test_instance.setup_method()
    try:
        # Run individual benchmarks
        test_instance.test_indexing_performance_scaling()
        test_instance.test_query_performance_benchmarks()
        test_instance.test_concurrent_operations_performance()
        test_instance.test_memory_usage_optimization()
        test_instance.test_tree_sitter_parsing_performance()
        test_instance.test_vector_database_performance()

        print("\n✅ All performance benchmarks passed!")

    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        raise
    finally:
        test_instance.teardown_method()
