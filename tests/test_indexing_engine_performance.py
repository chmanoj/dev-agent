"""Performance tests for the IndexingEngine."""

import os
import shutil
import tempfile
import time
from pathlib import Path

import pytest

from dev_agent.indexing.indexing_engine import IndexingEngine


class TestIndexingEnginePerformance:
    """Performance tests for IndexingEngine with large sample codebases."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "test_project"
        self.project_path.mkdir(parents=True)

    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def create_large_python_project(
        self, num_files: int = 100, lines_per_file: int = 1000
    ) -> None:
        """Create a large Python project for testing.

        Args:
            num_files: Number of Python files to create
            lines_per_file: Approximate lines of code per file
        """
        # Create directory structure
        src_dir = self.project_path / "src"
        tests_dir = self.project_path / "tests"
        src_dir.mkdir()
        tests_dir.mkdir()

        # Template for Python files
        class_template = '''"""Module {module_name} - Auto-generated for testing."""

import os
import sys
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class {class_name}:
    """A sample class for testing indexing performance."""
    
    def __init__(self, name: str, value: int = 0):
        """Initialize the {class_name}.
        
        Args:
            name: Name of the instance
            value: Initial value
        """
        self.name = name
        self.value = value
        self.data = {{}}
    
    def process_data(self, input_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process input data and return results.
        
        Args:
            input_data: List of data dictionaries to process
            
        Returns:
            Dictionary with processed results
        """
        results = {{}}
        
        for i, item in enumerate(input_data):
            if not isinstance(item, dict):
                continue
            
            # Process each item
            processed_item = self._process_single_item(item)
            results[f"item_{{i}}"] = processed_item
            
            # Update internal state
            self.value += processed_item.get("score", 0)
        
        return results
    
    def _process_single_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single data item.
        
        Args:
            item: Data item to process
            
        Returns:
            Processed item dictionary
        """
        processed = {{
            "original": item,
            "score": len(str(item)),
            "processed_at": time.time(),
            "processor": self.name
        }}
        
        # Add some complexity
        if "value" in item:
            processed["doubled_value"] = item["value"] * 2
        
        if "text" in item:
            processed["text_length"] = len(item["text"])
            processed["word_count"] = len(item["text"].split())
        
        return processed
    
    def validate_data(self, data: Any) -> bool:
        """Validate input data format.
        
        Args:
            data: Data to validate
            
        Returns:
            True if data is valid
        """
        if not data:
            return False
        
        if isinstance(data, list):
            return all(isinstance(item, dict) for item in data)
        
        if isinstance(data, dict):
            required_keys = {{"name", "value"}}
            return required_keys.issubset(data.keys())
        
        return False
    
    def export_results(self, results: Dict[str, Any], format_type: str = "json") -> str:
        """Export results in specified format.
        
        Args:
            results: Results dictionary to export
            format_type: Export format ("json", "csv", "xml")
            
        Returns:
            Formatted results string
        """
        if format_type == "json":
            return json.dumps(results, indent=2)
        
        elif format_type == "csv":
            # Simple CSV export
            lines = ["key,value"]
            for key, value in results.items():
                lines.append(f"{{key}},{{value}}")
            return "\\n".join(lines)
        
        elif format_type == "xml":
            # Simple XML export
            xml_lines = ["<results>"]
            for key, value in results.items():
                xml_lines.append(f"  <item key='{{key}}'>{{value}}</item>")
            xml_lines.append("</results>")
            return "\\n".join(xml_lines)
        
        else:
            raise ValueError(f"Unsupported format: {{format_type}}")
    
    @staticmethod
    def utility_function(data: List[Any]) -> int:
        """A utility function for data processing.
        
        Args:
            data: List of data items
            
        Returns:
            Total count of processed items
        """
        count = 0
        for item in data:
            if item is not None:
                count += 1
        return count
    
    @classmethod
    def create_from_config(cls, config: Dict[str, Any]) -> "{class_name}":
        """Create instance from configuration dictionary.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            New {class_name} instance
        """
        name = config.get("name", "default")
        value = config.get("value", 0)
        return cls(name, value)


def helper_function(x: int, y: int) -> int:
    """A helper function for mathematical operations.
    
    Args:
        x: First number
        y: Second number
        
    Returns:
        Sum of x and y
    """
    return x + y


def complex_algorithm(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """A complex algorithm for data analysis.
    
    Args:
        data: Input data for analysis
        
    Returns:
        Analysis results
    """
    if not data:
        return {{"error": "No data provided"}}
    
    # Initialize analysis variables
    total_items = len(data)
    numeric_values = []
    text_values = []
    
    # Process each data item
    for item in data:
        if "value" in item and isinstance(item["value"], (int, float)):
            numeric_values.append(item["value"])
        
        if "text" in item and isinstance(item["text"], str):
            text_values.append(item["text"])
    
    # Calculate statistics
    results = {{
        "total_items": total_items,
        "numeric_count": len(numeric_values),
        "text_count": len(text_values)
    }}
    
    if numeric_values:
        results["numeric_stats"] = {{
            "min": min(numeric_values),
            "max": max(numeric_values),
            "avg": sum(numeric_values) / len(numeric_values)
        }}
    
    if text_values:
        total_chars = sum(len(text) for text in text_values)
        results["text_stats"] = {{
            "total_chars": total_chars,
            "avg_length": total_chars / len(text_values)
        }}
    
    return results
'''

        # Generate files
        for i in range(num_files):
            module_name = f"module_{i:03d}"
            class_name = f"TestClass{i:03d}"

            # Determine file location
            if i % 4 == 0:  # 25% in tests directory
                file_path = tests_dir / f"test_{module_name}.py"
            else:
                file_path = src_dir / f"{module_name}.py"

            # Generate file content
            content = class_template.format(
                module_name=module_name, class_name=class_name
            )

            # Add extra content to reach target line count
            current_lines = len(content.split("\n"))
            if current_lines < lines_per_file:
                extra_lines_needed = lines_per_file - current_lines

                # Add extra methods
                for j in range(extra_lines_needed // 20):  # ~20 lines per method
                    method_content = f'''
    def extra_method_{j}(self, param_{j}: Any) -> Any:
        """Extra method {j} for testing purposes."""
        result = param_{j}
        for k in range(10):
            result = str(result) + f"_{{k}}"
        return result
'''
                    content += method_content

            # Write file
            with open(file_path, "w") as f:
                f.write(content)

        print(f"Created {num_files} Python files with ~{lines_per_file} lines each")

    def test_small_codebase_performance(self, mock_embedding_client):
        """Test indexing performance on a small codebase (10 files)."""
        self.create_large_python_project(num_files=10, lines_per_file=100)

        engine = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)

        start_time = time.time()
        result = engine.build_index()
        end_time = time.time()

        # Assertions
        assert result.success
        assert result.ast_index is not None
        assert result.embeddings_count > 0

        # Performance assertions
        indexing_time = end_time - start_time
        assert indexing_time < 30  # Should complete within 30 seconds

        # Verify index content
        assert len(result.ast_index.functions) > 0
        assert len(result.ast_index.classes) > 0

        print(f"Small codebase indexed in {indexing_time:.2f} seconds")
        print(f"Functions: {len(result.ast_index.functions)}")
        print(f"Classes: {len(result.ast_index.classes)}")
        print(f"Embeddings: {result.embeddings_count}")

    def test_medium_codebase_performance(self, mock_embedding_client):
        """Test indexing performance on a medium codebase (50 files)."""
        self.create_large_python_project(num_files=50, lines_per_file=500)

        engine = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)

        # Track progress
        progress_updates = []

        def progress_callback(current, total, message):
            progress_updates.append((current, total, message))

        engine.set_progress_callback(progress_callback)

        start_time = time.time()
        result = engine.build_index()
        end_time = time.time()

        # Assertions
        assert result.success
        assert result.ast_index is not None
        assert result.embeddings_count > 0

        # Performance assertions
        indexing_time = end_time - start_time
        assert indexing_time < 120  # Should complete within 2 minutes

        # Verify progress tracking
        assert len(progress_updates) > 0
        assert (
            progress_updates[-1][0] == progress_updates[-1][1]
        )  # Final progress should be complete

        print(f"Medium codebase indexed in {indexing_time:.2f} seconds")
        print(f"Functions: {len(result.ast_index.functions)}")
        print(f"Classes: {len(result.ast_index.classes)}")
        print(f"Embeddings: {result.embeddings_count}")
        print(f"Progress updates: {len(progress_updates)}")

    @pytest.mark.slow
    def test_large_codebase_performance(self, mock_embedding_client):
        """Test indexing performance on a large codebase (100+ files, 100k+ lines)."""
        self.create_large_python_project(num_files=100, lines_per_file=1000)

        engine = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)

        # Monitor memory usage (simplified)
        import psutil

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        start_time = time.time()
        result = engine.build_index()
        end_time = time.time()

        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory

        # Assertions
        assert result.success
        assert result.ast_index is not None
        assert result.embeddings_count > 0

        # Performance assertions
        indexing_time = end_time - start_time
        assert indexing_time < 600  # Should complete within 10 minutes
        assert memory_increase < 1000  # Should not use more than 1GB additional memory

        # Verify comprehensive indexing
        assert len(result.ast_index.functions) > 100
        assert len(result.ast_index.classes) > 50
        assert result.embeddings_count > 200

        print(f"Large codebase indexed in {indexing_time:.2f} seconds")
        print(f"Memory increase: {memory_increase:.2f} MB")
        print(f"Functions: {len(result.ast_index.functions)}")
        print(f"Classes: {len(result.ast_index.classes)}")
        print(f"Embeddings: {result.embeddings_count}")

    def test_memory_mapped_file_handling(self, mock_embedding_client):
        """Test memory-mapped file handling for large files."""
        # Create a large Python file (>1MB)
        large_file = self.project_path / "large_module.py"

        # Generate large content
        content_lines = []
        content_lines.append('"""Large module for testing memory mapping."""')
        content_lines.append("")

        # Add many classes and functions
        for i in range(1000):
            content_lines.extend(
                [
                    f"class LargeClass{i}:",
                    f'    """Class {i} for testing."""',
                    "    ",
                    f"    def method_{i}(self):",
                    f'        """Method {i}."""',
                    f"        return {i}",
                    "    ",
                    f"def function_{i}():",
                    f'    """Function {i}."""',
                    f'    return "result_{i}"',
                    "",
                ]
            )

        content = "\n".join(content_lines)

        with open(large_file, "w") as f:
            f.write(content)

        # Verify file is large enough to trigger memory mapping
        file_size = large_file.stat().st_size
        assert file_size > 1024 * 1024  # > 1MB

        engine = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)

        start_time = time.time()
        result = engine.build_index()
        end_time = time.time()

        # Assertions
        assert result.success
        assert result.ast_index is not None

        # Verify large file was processed
        large_file_functions = [
            func
            for func in result.ast_index.functions.values()
            if func.file_path == str(large_file)
        ]
        assert len(large_file_functions) > 500  # Should find many functions

        print(
            f"Large file ({file_size / 1024 / 1024:.2f} MB) processed in {end_time - start_time:.2f} seconds"
        )
        print(f"Functions found: {len(large_file_functions)}")

    def test_parallel_processing_performance(self, mock_embedding_client):
        """Test parallel processing performance improvement."""
        self.create_large_python_project(num_files=30, lines_per_file=200)

        engine = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)

        # Test with parallel processing (default)
        start_time = time.time()
        result_parallel = engine.build_index()
        parallel_time = time.time() - start_time

        # Reset engine for sequential test
        engine = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)
        engine.max_workers = 1  # Force sequential processing

        start_time = time.time()
        result_sequential = engine.build_index()
        sequential_time = time.time() - start_time

        # Assertions
        assert result_parallel.success
        assert result_sequential.success

        # Both should produce similar results
        assert len(result_parallel.ast_index.functions) == len(
            result_sequential.ast_index.functions
        )
        assert len(result_parallel.ast_index.classes) == len(
            result_sequential.ast_index.classes
        )

        # Parallel should be faster (or at least not significantly slower)
        # Note: For small codebases, parallel might be slower due to overhead
        print(f"Parallel processing: {parallel_time:.2f} seconds")
        print(f"Sequential processing: {sequential_time:.2f} seconds")

        if parallel_time < sequential_time:
            speedup = sequential_time / parallel_time
            print(f"Speedup: {speedup:.2f}x")

    def test_index_persistence_performance(self, mock_embedding_client):
        """Test index persistence and loading performance."""
        self.create_large_python_project(num_files=20, lines_per_file=300)

        engine = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)

        # Build and save index
        start_time = time.time()
        result = engine.build_index()
        build_time = time.time() - start_time

        assert result.success

        # Create new engine instance and load existing index
        engine2 = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)

        start_time = time.time()
        metadata = engine2.get_index_metadata()
        symbol_map = engine2.get_symbol_map()
        load_time = time.time() - start_time

        # Assertions
        assert metadata is not None
        assert len(symbol_map) > 0

        # Loading should be much faster than building
        assert load_time < build_time / 5  # At least 5x faster

        print(f"Index build time: {build_time:.2f} seconds")
        print(f"Index load time: {load_time:.2f} seconds")
        print(f"Load speedup: {build_time / load_time:.2f}x")

    def test_query_performance(self, mock_embedding_client):
        """Test vector similarity query performance."""
        self.create_large_python_project(num_files=25, lines_per_file=400)

        engine = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)
        result = engine.build_index()

        assert result.success
        assert result.embeddings_count > 0

        # Test various query types
        queries = [
            "class definition with methods",
            "function that processes data",
            "import statements",
            "error handling code",
            "data validation logic",
        ]

        total_query_time = 0

        for query in queries:
            start_time = time.time()
            matches = engine.query_similar_code(query, limit=10)
            query_time = time.time() - start_time

            total_query_time += query_time

            # Each query should complete quickly
            assert query_time < 1.0  # Less than 1 second per query

            print(
                f"Query '{query}': {len(matches)} matches in {query_time:.3f} seconds"
            )

        avg_query_time = total_query_time / len(queries)
        print(f"Average query time: {avg_query_time:.3f} seconds")

        # Average query time should be very fast
        assert avg_query_time < 0.5

    def test_incremental_indexing_performance(self, mock_embedding_client):
        """Test performance of incremental indexing updates."""
        self.create_large_python_project(num_files=15, lines_per_file=200)

        engine = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)

        # Initial indexing
        start_time = time.time()
        result1 = engine.build_index()
        initial_time = time.time() - start_time

        assert result1.success

        # Modify a few files
        src_dir = self.project_path / "src"
        modified_files = list(src_dir.glob("*.py"))[:3]  # Modify first 3 files

        for file_path in modified_files:
            with open(file_path, "a") as f:
                f.write(
                    '\n\ndef new_function():\n    """Newly added function."""\n    pass\n'
                )

        # Re-index (should detect changes)
        start_time = time.time()
        result2 = engine.build_index()
        reindex_time = time.time() - start_time

        assert result2.success

        # Re-indexing should find the new functions
        new_functions = len(result2.ast_index.functions) - len(
            result1.ast_index.functions
        )
        assert new_functions >= 3  # At least one new function per modified file

        print(f"Initial indexing: {initial_time:.2f} seconds")
        print(f"Re-indexing: {reindex_time:.2f} seconds")
        print(f"New functions found: {new_functions}")

    def test_error_handling_performance(self, mock_embedding_client):
        """Test performance when handling files with errors."""
        # Create project with some problematic files
        self.create_large_python_project(num_files=10, lines_per_file=100)

        # Add some files with syntax errors
        error_files = []
        for i in range(3):
            error_file = self.project_path / f"error_file_{i}.py"
            with open(error_file, "w") as f:
                f.write("""
# File with syntax errors
def broken_function(
    # Missing closing parenthesis and colon
    
class BrokenClass
    # Missing colon
    def method(self):
        return "incomplete
        # Missing closing quote
""")
            error_files.append(error_file)

        engine = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)

        start_time = time.time()
        result = engine.build_index()
        end_time = time.time()

        # Should still succeed despite errors
        assert result.success

        # Should have some errors reported
        assert len(result.errors) > 0

        # Should still index the good files
        assert result.ast_index is not None
        assert len(result.ast_index.functions) > 0

        # Performance should not be significantly impacted
        indexing_time = end_time - start_time
        assert indexing_time < 60  # Should complete within 1 minute

        print(f"Indexing with errors completed in {indexing_time:.2f} seconds")
        print(f"Errors encountered: {len(result.errors)}")
        print(f"Functions indexed: {len(result.ast_index.functions)}")


if __name__ == "__main__":
    # Run performance tests
    test_instance = TestIndexingEnginePerformance()

    print("Running IndexingEngine performance tests...")

    test_instance.setup_method()
    try:
        test_instance.test_small_codebase_performance()
        print("✓ Small codebase test passed")

        test_instance.test_medium_codebase_performance()
        print("✓ Medium codebase test passed")

        test_instance.test_memory_mapped_file_handling()
        print("✓ Memory mapping test passed")

        test_instance.test_parallel_processing_performance()
        print("✓ Parallel processing test passed")

        test_instance.test_index_persistence_performance()
        print("✓ Index persistence test passed")

        test_instance.test_query_performance()
        print("✓ Query performance test passed")

        test_instance.test_incremental_indexing_performance()
        print("✓ Incremental indexing test passed")

        test_instance.test_error_handling_performance()
        print("✓ Error handling test passed")

        print("\nAll performance tests passed!")

    finally:
        test_instance.teardown_method()
