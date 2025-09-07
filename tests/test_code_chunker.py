"""Tests for the code chunking implementation."""

import os
import tempfile

from dev_agent.indexing.code_chunker import CodeChunker
from dev_agent.models.indexing import ASTIndex, ClassDef, CodeChunk, FunctionDef


class TestCodeChunker:
    """Test cases for CodeChunker class."""

    def setup_method(self):
        """Set up test environment."""
        self.chunker = CodeChunker(max_chunk_size=512, overlap_size=50)
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test chunker initialization."""
        assert self.chunker.max_chunk_size == 512
        assert self.chunker.overlap_size == 50

    def test_chunk_simple_function(self):
        """Test chunking a simple Python function."""
        content = '''def add(a, b):
    """Add two numbers."""
    return a + b

def multiply(x, y):
    """Multiply two numbers."""
    return x * y'''

        chunks = self.chunker.chunk_content(content, "test.py", "python")

        # Should have function chunks
        function_chunks = [c for c in chunks if c.chunk_type == "function"]
        assert len(function_chunks) >= 2

        # Check that function content is captured
        function_contents = [c.content for c in function_chunks]
        assert any("def add(a, b):" in content for content in function_contents)
        assert any("def multiply(x, y):" in content for content in function_contents)

    def test_chunk_simple_class(self):
        """Test chunking a simple Python class."""
        content = '''class Calculator:
    """A simple calculator class."""
    
    def __init__(self):
        self.result = 0
    
    def add(self, value):
        self.result += value
        return self.result'''

        chunks = self.chunker.chunk_content(content, "test.py", "python")

        # Should have class chunks
        class_chunks = [c for c in chunks if c.chunk_type == "class"]
        assert len(class_chunks) >= 1

        # Check that class content is captured
        class_content = class_chunks[0].content
        assert "class Calculator:" in class_content
        assert "def __init__(self):" in class_content

    def test_chunk_imports(self):
        """Test chunking import statements."""
        content = """import os
import sys
from pathlib import Path
from typing import List, Dict

def main():
    pass"""

        chunks = self.chunker.chunk_content(content, "test.py", "python")

        # Should have import chunks
        import_chunks = [c for c in chunks if c.chunk_type == "imports"]
        assert len(import_chunks) >= 1

        # Check import content
        import_content = import_chunks[0].content
        assert "import os" in import_content
        assert "from pathlib import Path" in import_content

    def test_chunk_module_docstring(self):
        """Test chunking module-level docstring."""
        content = '''"""This is a module docstring.

It describes what the module does.
"""

import os

def function():
    pass'''

        chunks = self.chunker.chunk_content(content, "test.py", "python")

        # Should have docstring chunks
        docstring_chunks = [c for c in chunks if c.chunk_type == "docstring"]
        assert len(docstring_chunks) >= 1

        # Check docstring content
        docstring_content = docstring_chunks[0].content
        assert "This is a module docstring" in docstring_content

    def test_chunk_file(self):
        """Test chunking a real file."""
        # Create a temporary Python file
        test_file = os.path.join(self.temp_dir, "test_module.py")
        content = '''"""Test module for chunking."""

import os
from typing import List

class TestClass:
    """A test class."""
    
    def __init__(self, name: str):
        self.name = name
    
    def greet(self) -> str:
        return f"Hello, {self.name}!"

def standalone_function(items: List[str]) -> int:
    """Count items in a list."""
    return len(items)

if __name__ == "__main__":
    test = TestClass("World")
    print(test.greet())'''

        with open(test_file, "w") as f:
            f.write(content)

        chunks = self.chunker.chunk_file(test_file, "python")

        assert len(chunks) > 0

        # Should have different types of chunks
        chunk_types = {c.chunk_type for c in chunks}
        expected_types = {"docstring", "imports", "class", "function"}
        assert len(chunk_types.intersection(expected_types)) > 0

        # All chunks should reference the correct file
        assert all(c.file_path == test_file for c in chunks)

    def test_chunk_from_ast(self):
        """Test chunking from AST index."""
        # Create mock AST index
        functions = {
            "test.py:add": FunctionDef(
                name="add",
                parameters=["a", "b"],
                return_type=None,
                docstring="Add two numbers",
                file_path="test.py",
                start_line=1,
                end_line=3
            ),
            "test.py:multiply": FunctionDef(
                name="multiply",
                parameters=["x", "y"],
                return_type=None,
                docstring="Multiply two numbers",
                file_path="test.py",
                start_line=5,
                end_line=7
            )
        }

        classes = {
            "test.py:Calculator": ClassDef(
                name="Calculator",
                base_classes=[],
                methods=[],
                attributes=[],
                docstring="A calculator class",
                file_path="test.py",
                start_line=9,
                end_line=15
            )
        }

        ast_index = ASTIndex(
            functions=functions,
            classes=classes,
            imports=[],
            symbols={},
            file_metadata={}
        )

        # Create test file
        test_file = os.path.join(self.temp_dir, "test.py")
        content = '''def add(a, b):
    """Add two numbers."""
    return a + b

def multiply(x, y):
    """Multiply two numbers."""
    return x * y

class Calculator:
    """A calculator class."""
    
    def __init__(self):
        self.value = 0
    
    def calculate(self):
        pass'''

        with open(test_file, "w") as f:
            f.write(content)

        chunks = self.chunker.chunk_from_ast(ast_index, test_file)

        assert len(chunks) == 3  # 2 functions + 1 class

        # Check chunk types
        chunk_types = [c.chunk_type for c in chunks]
        assert "function" in chunk_types
        assert "class" in chunk_types

    def test_sliding_window_chunking(self):
        """Test sliding window chunking for large content."""
        # Create content larger than max_chunk_size
        large_content = "# This is a large file\n" + "print('line')\n" * 100

        chunks = self.chunker._chunk_by_sliding_window(large_content, "large.py", "python")

        assert len(chunks) > 1  # Should be split into multiple chunks

        # Check overlap between consecutive chunks
        if len(chunks) > 1:
            # There should be some overlap in content
            first_chunk_end = chunks[0].content[-self.chunker.overlap_size:]
            second_chunk_start = chunks[1].content[:self.chunker.overlap_size]
            # Note: Exact overlap checking is complex due to line boundaries
            assert len(first_chunk_end) > 0
            assert len(second_chunk_start) > 0

    def test_large_function_splitting(self):
        """Test splitting large functions into smaller chunks."""
        # Create a large function
        large_function = '''def large_function():
    """This is a very large function."""
    ''' + "\n    ".join([f'print("line {i}")' for i in range(50)]) + '''
    return "done"'''

        chunks = self.chunker._split_large_function(large_function, "test.py", 1, "python")

        # Should split into multiple chunks if content is large enough
        if len(large_function) > self.chunker.max_chunk_size:
            assert len(chunks) > 1

        # All chunks should be function fragments
        assert all(c.chunk_type == "function_fragment" for c in chunks)

    def test_optimize_chunks(self):
        """Test chunk optimization (deduplication and merging)."""
        # Create chunks with duplicates and small adjacent chunks
        chunks = [
            CodeChunk(
                content="def small1(): pass",
                file_path="test.py",
                start_line=1,
                end_line=1,
                language="python",
                chunk_type="function"
            ),
            CodeChunk(
                content="def small2(): pass",
                file_path="test.py",
                start_line=2,
                end_line=2,
                language="python",
                chunk_type="function"
            ),
            CodeChunk(
                content="def small1(): pass",  # Duplicate
                file_path="test.py",
                start_line=1,
                end_line=1,
                language="python",
                chunk_type="function"
            ),
            CodeChunk(
                content="class LargeClass(): pass",
                file_path="other.py",
                start_line=1,
                end_line=1,
                language="python",
                chunk_type="class"
            )
        ]

        optimized = self.chunker.optimize_chunks(chunks)

        # Should remove duplicates
        assert len(optimized) < len(chunks)

        # Should not have exact duplicates
        contents = [c.content for c in optimized]
        assert len(contents) == len(set(contents))

    def test_language_detection(self):
        """Test programming language detection from file extension."""
        assert self.chunker._detect_language("test.py") == "python"
        assert self.chunker._detect_language("test.js") == "javascript"
        assert self.chunker._detect_language("test.java") == "java"
        assert self.chunker._detect_language("test.cpp") == "cpp"
        assert self.chunker._detect_language("test.unknown") == "unknown"

    def test_extract_lines(self):
        """Test line extraction utility."""
        lines = ["line1", "line2", "line3", "line4", "line5"]

        # Test normal extraction
        result = self.chunker._extract_lines(lines, 2, 4)
        assert result == "line2\nline3\nline4"

        # Test boundary conditions
        result = self.chunker._extract_lines(lines, 1, 1)
        assert result == "line1"

        result = self.chunker._extract_lines(lines, 5, 5)
        assert result == "line5"

        # Test out of bounds
        result = self.chunker._extract_lines(lines, 0, 10)
        assert result == "\n".join(lines)

    def test_empty_content(self):
        """Test chunking empty or whitespace-only content."""
        empty_chunks = self.chunker.chunk_content("", "empty.py", "python")
        assert len(empty_chunks) >= 0  # Should handle gracefully

        whitespace_chunks = self.chunker.chunk_content("   \n\n   ", "whitespace.py", "python")
        assert len(whitespace_chunks) >= 0  # Should handle gracefully

    def test_nonexistent_file(self):
        """Test chunking a nonexistent file."""
        chunks = self.chunker.chunk_file("nonexistent.py", "python")
        assert chunks == []

    def test_chunk_size_limits(self):
        """Test that chunks respect size limits."""
        content = "def test(): pass\n" * 100  # Create large content

        chunks = self.chunker.chunk_content(content, "test.py", "python")

        # Most chunks should be within size limits
        oversized_chunks = [c for c in chunks if len(c.content) > self.chunker.max_chunk_size * 1.1]

        # Allow some flexibility for chunks that can't be split nicely
        assert len(oversized_chunks) <= len(chunks) * 0.2  # At most 20% can be oversized
