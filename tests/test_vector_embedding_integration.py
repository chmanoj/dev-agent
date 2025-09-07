"""Integration tests for the vector embedding system."""

import os
import shutil
import tempfile

from dev_agent.indexing.code_chunker import CodeChunker
from dev_agent.indexing.vector_database import VectorDatabase
from dev_agent.models.indexing import CodeChunk


class TestVectorEmbeddingIntegration:
    """Integration tests for the complete vector embedding pipeline."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.index_path = os.path.join(self.temp_dir, "integration_index")
        self.db = VectorDatabase(self.index_path)
        self.chunker = CodeChunker(max_chunk_size=256, overlap_size=32)

    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_end_to_end_pipeline(self):
        """Test the complete pipeline from code to embeddings to search."""
        # Create a sample Python project
        project_files = {
            "math_utils.py": '''"""Mathematical utility functions."""

import math
from typing import List, Union

def add(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b

def multiply(x: float, y: float) -> float:
    """Multiply two numbers."""
    return x * y

def calculate_average(numbers: List[float]) -> float:
    """Calculate the average of a list of numbers."""
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)

class Calculator:
    """A simple calculator class."""
    
    def __init__(self):
        self.history = []
    
    def compute(self, operation: str, a: float, b: float) -> float:
        """Perform a calculation and store in history."""
        if operation == "add":
            result = add(a, b)
        elif operation == "multiply":
            result = multiply(a, b)
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        self.history.append((operation, a, b, result))
        return result''',

            "string_utils.py": '''"""String utility functions."""

def reverse_string(text: str) -> str:
    """Reverse a string."""
    return text[::-1]

def count_words(text: str) -> int:
    """Count words in a text."""
    return len(text.split())

def capitalize_words(text: str) -> str:
    """Capitalize each word in a text."""
    return ' '.join(word.capitalize() for word in text.split())

class TextProcessor:
    """A text processing utility class."""
    
    def __init__(self, default_case: str = "lower"):
        self.default_case = default_case
    
    def process(self, text: str) -> str:
        """Process text according to default case."""
        if self.default_case == "lower":
            return text.lower()
        elif self.default_case == "upper":
            return text.upper()
        else:
            return text''',

            "main.py": '''"""Main application entry point."""

from math_utils import Calculator, add
from string_utils import TextProcessor

def main():
    """Main function."""
    calc = Calculator()
    result = calc.compute("add", 5, 3)
    print(f"Calculation result: {result}")
    
    processor = TextProcessor("upper")
    text = processor.process("hello world")
    print(f"Processed text: {text}")

if __name__ == "__main__":
    main()'''
        }

        # Write files to temp directory
        file_paths = []
        for filename, content in project_files.items():
            file_path = os.path.join(self.temp_dir, filename)
            with open(file_path, "w") as f:
                f.write(content)
            file_paths.append(file_path)

        # Step 1: Chunk all files
        all_chunks = []
        for file_path in file_paths:
            chunks = self.chunker.chunk_file(file_path, "python")
            all_chunks.extend(chunks)

        assert len(all_chunks) > 0, "Should generate chunks from the project files"

        # Step 2: Store embeddings
        chunk_ids = self.db.store_embeddings(all_chunks)

        assert len(chunk_ids) == len(all_chunks), "Should store all chunks"
        assert self.db.index.ntotal == len(all_chunks), "Index should contain all embeddings"

        # Step 3: Test semantic search

        # Search for mathematical functions
        math_results = self.db.query_similar("addition function", k=5)
        assert len(math_results) > 0, "Should find mathematical functions"

        # Check that math-related chunks are returned
        math_files = [r.chunk.file_path for r in math_results]
        assert any("math_utils.py" in path for path in math_files), "Should find math utilities"

        # Search for string processing
        string_results = self.db.query_similar("text processing", k=5)
        assert len(string_results) > 0, "Should find string processing functions"

        # Check that string-related chunks are returned
        string_files = [r.chunk.file_path for r in string_results]
        assert any("string_utils.py" in path for path in string_files), "Should find string utilities"

        # Search for class definitions
        class_results = self.db.query_similar("class definition", k=5)
        assert len(class_results) > 0, "Should find class definitions"

        # Step 4: Test similarity between related code

        # Create a query similar to existing code
        query_chunk = CodeChunk(
            content="def sum_numbers(a, b): return a + b",
            file_path="query.py",
            start_line=1,
            end_line=1,
            language="python",
            chunk_type="function"
        )

        similar_results = self.db.query_similar_by_chunk(query_chunk, k=3)
        assert len(similar_results) > 0, "Should find similar functions"

        # The add function should be among the most similar
        similar_contents = [r.chunk.file_path for r in similar_results]
        assert any("math_utils.py" in path for path in similar_contents), "Should find the add function"

    def test_chunk_type_distribution(self):
        """Test that different chunk types are properly generated and stored."""
        # Create a comprehensive Python file
        content = '''"""Module for testing chunk types."""

import os
import sys
from pathlib import Path

# Global variable
DEFAULT_VALUE = 42

def utility_function(param):
    """A utility function."""
    return param * 2

class ExampleClass:
    """An example class."""
    
    def __init__(self, value):
        self.value = value
    
    def method(self):
        """A class method."""
        return self.value

# Another function
def another_function():
    pass'''

        file_path = os.path.join(self.temp_dir, "comprehensive.py")
        with open(file_path, "w") as f:
            f.write(content)

        # Chunk the file
        chunks = self.chunker.chunk_file(file_path, "python")

        # Store embeddings
        chunk_ids = self.db.store_embeddings(chunks)

        # Analyze chunk types
        chunk_types = {}
        for chunk_id in chunk_ids:
            metadata = self.db.get_chunk_by_id(chunk_id)
            chunk_type = metadata["chunk_type"]
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1

        # Should have multiple types of chunks
        assert len(chunk_types) > 1, "Should generate multiple types of chunks"

        # Common chunk types should be present
        expected_types = {"function", "class", "imports", "docstring"}
        found_types = set(chunk_types.keys())

        # At least some expected types should be found
        assert len(expected_types.intersection(found_types)) > 0, f"Should find some expected chunk types. Found: {found_types}"

    def test_search_precision_and_recall(self):
        """Test search precision with known similar and dissimilar code."""
        # Create clearly different types of code
        similar_math_functions = [
            "def add_two(x, y): return x + y",
            "def sum_values(a, b): return a + b",
            "def plus(num1, num2): return num1 + num2"
        ]

        different_functions = [
            "def read_file(path): return open(path).read()",
            "def send_email(to, subject): pass",
            "def parse_json(data): return json.loads(data)"
        ]

        # Create chunks
        all_chunks = []

        # Add similar math functions
        for i, func in enumerate(similar_math_functions):
            chunk = CodeChunk(
                content=func,
                file_path=f"math{i}.py",
                start_line=1,
                end_line=1,
                language="python",
                chunk_type="function"
            )
            all_chunks.append(chunk)

        # Add different functions
        for i, func in enumerate(different_functions):
            chunk = CodeChunk(
                content=func,
                file_path=f"other{i}.py",
                start_line=1,
                end_line=1,
                language="python",
                chunk_type="function"
            )
            all_chunks.append(chunk)

        # Store embeddings
        self.db.store_embeddings(all_chunks)

        # Search for addition-like functions
        results = self.db.query_similar("addition function add numbers", k=6)

        assert len(results) > 0, "Should find some results"

        # Check that math functions are ranked higher
        top_results = results[:3]  # Top 3 results

        math_in_top = sum(1 for r in top_results if "math" in r.chunk.file_path)
        other_in_top = sum(1 for r in top_results if "other" in r.chunk.file_path)

        # Math functions should dominate the top results
        assert math_in_top >= other_in_top, "Math functions should be ranked higher for math query"

    def test_persistence_across_sessions(self):
        """Test that embeddings persist across database sessions."""
        # Store some data
        chunks = [
            CodeChunk(
                content="def persistent_func(): return 'persistent'",
                file_path="persistent.py",
                start_line=1,
                end_line=1,
                language="python",
                chunk_type="function"
            )
        ]

        chunk_ids = self.db.store_embeddings(chunks)
        original_count = self.db.index.ntotal

        # Save the index
        self.db.save_index()

        # Create a new database instance
        new_db = VectorDatabase(self.index_path)

        # Check persistence
        assert new_db.index.ntotal == original_count, "Should load the same number of embeddings"

        # Check that we can still search
        results = new_db.query_similar("persistent function", k=1)
        assert len(results) > 0, "Should find the persistent function"

        # Check metadata persistence
        for chunk_id in chunk_ids:
            metadata = new_db.get_chunk_by_id(chunk_id)
            assert metadata is not None, "Metadata should persist"
            assert metadata["file_path"] == "persistent.py"

    def test_large_codebase_simulation(self):
        """Test performance with a larger number of chunks."""
        # Generate many small functions
        chunks = []

        for i in range(50):  # Create 50 functions
            content = f'''def function_{i}(param):
    """Function number {i}."""
    result = param * {i}
    return result + {i % 10}'''

            chunk = CodeChunk(
                content=content,
                file_path=f"module_{i // 10}.py",
                start_line=(i % 10) * 5 + 1,
                end_line=(i % 10) * 5 + 4,
                language="python",
                chunk_type="function"
            )
            chunks.append(chunk)

        # Store all embeddings
        chunk_ids = self.db.store_embeddings(chunks)

        assert len(chunk_ids) == 50, "Should store all 50 functions"
        assert self.db.index.ntotal == 50, "Index should contain 50 embeddings"

        # Test search performance
        results = self.db.query_similar("function with parameter", k=10)

        assert len(results) == 10, "Should return requested number of results"
        assert all(r.similarity_score >= 0 for r in results), "All similarity scores should be non-negative"

        # Test statistics
        stats = self.db.get_stats()
        assert stats["total_embeddings"] == 50
        assert stats["active_chunks"] == 50

    def test_error_handling(self):
        """Test error handling in the embedding pipeline."""
        # Test with invalid file
        chunks = self.chunker.chunk_file("nonexistent.py", "python")
        assert chunks == [], "Should handle nonexistent files gracefully"

        # Test with empty chunk
        empty_chunk = CodeChunk(
            content="",
            file_path="empty.py",
            start_line=1,
            end_line=1,
            language="python",
            chunk_type="empty"
        )

        # Should handle empty content without crashing
        chunk_id = self.db.store_embedding(empty_chunk)
        assert chunk_id is not None, "Should handle empty chunks"

        # Test search with empty query
        results = self.db.query_similar("", k=5)
        # Should not crash, may return empty results or all results
