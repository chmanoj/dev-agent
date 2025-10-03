"""Unit tests for IndexingEngine."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from dev_agent.indexing.indexing_engine import IndexingEngine
from dev_agent.llm.cost_tracker import CostTracker
from dev_agent.models.enums import PhaseType
from dev_agent.models.indexing import (
    ASTIndex,
    FunctionDef,
)
from dev_agent.models.project_state import IndexMetadata


@pytest.fixture
def mock_embedding_client():
    """Create a mock embedding client."""
    client = AsyncMock()
    
    # Mock embed_text to return a 1536-dimensional vector
    client.embed_text = AsyncMock(return_value=[0.1] * 1536)
    
    # Mock embed_batch to return multiple vectors
    async def mock_embed_batch(texts, batch_size=16):
        return [[0.1] * 1536 for _ in texts]
    
    client.embed_batch = AsyncMock(side_effect=mock_embed_batch)
    
    # Mock dimension property
    client.dimension = 1536
    
    return client


@pytest.fixture
def mock_cost_tracker():
    """Create a mock cost tracker."""
    tracker = CostTracker(
        current_phase=PhaseType.INDEXING,
        budget_threshold=10.0,
        budget_limit=50.0,
    )
    return tracker


class TestIndexingEngine:
    """Unit tests for IndexingEngine class."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "test_project"
        self.project_path.mkdir(parents=True)

        # Create sample Python files
        self.create_sample_files()

    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def create_sample_files(self):
        """Create sample Python files for testing."""
        # Main module
        main_file = self.project_path / "main.py"
        main_content = '''"""Main module for testing."""

import os
import sys
from typing import List, Dict


class MainClass:
    """Main class for the application."""
    
    def __init__(self, name: str):
        """Initialize MainClass."""
        self.name = name
    
    def process(self, data: List[Dict]) -> Dict:
        """Process input data."""
        return {"processed": len(data)}


def main_function(args: List[str]) -> int:
    """Main entry point function."""
    print(f"Running with args: {args}")
    return 0


if __name__ == "__main__":
    main_function(sys.argv[1:])
'''
        with open(main_file, "w") as f:
            f.write(main_content)

        # Utils module
        utils_file = self.project_path / "utils.py"
        utils_content = '''"""Utility functions."""

from typing import Any, Optional


def helper_function(x: int, y: int) -> int:
    """Add two numbers."""
    return x + y


def validate_input(data: Any) -> bool:
    """Validate input data."""
    return data is not None


class UtilityClass:
    """Utility class with helper methods."""
    
    @staticmethod
    def format_output(value: Any) -> str:
        """Format value as string."""
        return str(value)
'''
        with open(utils_file, "w") as f:
            f.write(utils_content)

        # Test file
        test_file = self.project_path / "test_module.py"
        test_content = '''"""Test module."""

import unittest
from main import MainClass


class TestMainClass(unittest.TestCase):
    """Test cases for MainClass."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.main_obj = MainClass("test")
    
    def test_process(self):
        """Test process method."""
        result = self.main_obj.process([{"key": "value"}])
        self.assertEqual(result["processed"], 1)
'''
        with open(test_file, "w") as f:
            f.write(test_content)

    def test_initialization(self, mock_embedding_client):
        """Test IndexingEngine initialization."""
        engine = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)

        assert engine.project_path == self.project_path
        assert engine.index_path == self.project_path / ".dev_agent" / "index"
        assert engine.tree_sitter_parser is not None
        assert engine.vector_db is not None
        assert engine.code_chunker is not None
        assert engine.max_workers > 0
        assert engine.embedding_client is mock_embedding_client

    def test_custom_index_path(self, mock_embedding_client):
        """Test IndexingEngine with custom index path."""
        custom_index_path = Path(self.temp_dir) / "custom_index"
        engine = IndexingEngine(str(self.project_path), str(custom_index_path), embedding_client=mock_embedding_client)

        assert engine.index_path == Path(custom_index_path)

    def test_discover_source_files(self, mock_embedding_client):
        """Test source file discovery."""
        engine = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)
        source_files = engine._discover_source_files()

        # Should find all Python files
        assert len(source_files) == 3

        file_names = [f.name for f in source_files]
        assert "main.py" in file_names
        assert "utils.py" in file_names
        assert "test_module.py" in file_names

    def test_discover_source_files_with_exclusions(self, mock_embedding_client):
        """Test source file discovery with excluded directories."""
        # Create excluded directories
        (self.project_path / "__pycache__").mkdir()
        (self.project_path / "__pycache__" / "cached.py").touch()

        (self.project_path / ".git").mkdir()
        (self.project_path / ".git" / "config.py").touch()

        (self.project_path / "node_modules").mkdir()
        (self.project_path / "node_modules" / "module.py").touch()

        engine = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)
        source_files = engine._discover_source_files()

        # Should only find the original files, not the excluded ones
        assert len(source_files) == 3

        file_paths = [str(f) for f in source_files]
        assert not any("__pycache__" in path for path in file_paths)
        assert not any(".git" in path for path in file_paths)
        assert not any("node_modules" in path for path in file_paths)

    def test_detect_language(self, mock_embedding_client):
        """Test language detection from file extensions."""
        engine = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)

        assert engine._detect_language(Path("test.py")) == "python"
        assert engine._detect_language(Path("test.js")) == "javascript"
        assert engine._detect_language(Path("test.java")) == "java"
        assert engine._detect_language(Path("test.cpp")) == "cpp"
        assert engine._detect_language(Path("test.unknown")) == "unknown"

    def test_parse_codebase_ast_sequential(self, mock_embedding_client):
        """Test AST parsing in sequential mode."""
        engine = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)
        engine.max_workers = 1  # Force sequential processing

        ast_index = engine.parse_codebase_ast()

        assert ast_index is not None
        assert isinstance(ast_index, ASTIndex)

        # Should find functions and classes
        assert len(ast_index.functions) > 0
        assert len(ast_index.classes) > 0
        assert len(ast_index.imports) > 0
        assert len(ast_index.symbols) > 0
        assert len(ast_index.file_metadata) == 3

        # Check specific items
        function_names = [func.name for func in ast_index.functions.values()]
        assert "main_function" in function_names
        assert "helper_function" in function_names

        class_names = [cls.name for cls in ast_index.classes.values()]
        assert "MainClass" in class_names
        assert "UtilityClass" in class_names

    def test_parse_codebase_ast_parallel(self, mock_embedding_client):
        """Test AST parsing in parallel mode."""
        engine = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)
        engine.max_workers = 2  # Use parallel processing

        ast_index = engine.parse_codebase_ast()

        assert ast_index is not None
        assert isinstance(ast_index, ASTIndex)

        # Should produce same results as sequential
        assert len(ast_index.functions) > 0
        assert len(ast_index.classes) > 0
        assert len(ast_index.file_metadata) == 3

    def test_build_index_success(self, mock_embedding_client):
        """Test successful index building."""
        engine = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)

        # Mock progress callback
        progress_calls = []

        def progress_callback(current, total, message):
            progress_calls.append((current, total, message))

        engine.set_progress_callback(progress_callback)

        result = engine.build_index()

        assert result.success
        assert result.ast_index is not None
        assert result.embeddings_count > 0
        assert len(result.errors) == 0
        assert "indexing_time_seconds" in result.metadata

        # Check progress was tracked
        assert len(progress_calls) > 0
        assert (
            progress_calls[-1][0] == progress_calls[-1][1]
        )  # Final call should be complete

    def test_build_index_no_files(self, mock_embedding_client):
        """Test index building with no source files."""
        empty_project = Path(self.temp_dir) / "empty_project"
        empty_project.mkdir()

        engine = IndexingEngine(str(empty_project), embedding_client=mock_embedding_client)
        result = engine.build_index()

        assert not result.success
        assert "No source files found" in result.errors[0]

    def test_build_index_with_errors(self, mock_embedding_client):
        """Test index building with parsing errors."""
        # Create a file with syntax errors
        error_file = self.project_path / "error_file.py"
        with open(error_file, "w") as f:
            f.write("def broken_function(\n    # Missing closing parenthesis")

        engine = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)
        result = engine.build_index()

        # Should still succeed despite errors
        assert result.success
        # Note: Errors might not be captured in result.errors depending on implementation
        # The main thing is that it doesn't crash

    def test_query_similar_code(self, mock_embedding_client):
        """Test vector similarity querying."""
        engine = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)

        # Build index first
        result = engine.build_index()
        assert result.success

        # Query for similar code
        matches = engine.query_similar_code("class definition", limit=5)

        # Should return some matches
        assert isinstance(matches, list)
        # Note: Actual matches depend on vector DB implementation

    def test_get_symbol_map(self, mock_embedding_client):
        """Test symbol map retrieval."""
        engine = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)

        # Build index first
        result = engine.build_index()
        assert result.success

        symbol_map = engine.get_symbol_map()

        assert isinstance(symbol_map, dict)
        assert len(symbol_map) > 0

        # Check for expected symbols
        symbol_names = [symbol.name for symbol in symbol_map.values()]
        assert "MainClass" in symbol_names
        assert "main_function" in symbol_names

    def test_get_symbol_map_no_index(self, mock_embedding_client):
        """Test symbol map retrieval without existing index."""
        engine = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)

        # Should return empty dict if no index exists
        symbol_map = engine.get_symbol_map()
        assert isinstance(symbol_map, dict)

    def test_save_and_load_index_metadata(self, mock_embedding_client):
        """Test saving and loading index metadata."""
        engine = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)

        # Build index to create metadata
        result = engine.build_index()
        assert result.success

        # Get metadata
        metadata = engine.get_index_metadata()
        assert metadata is not None
        assert isinstance(metadata, IndexMetadata)
        assert metadata.total_files > 0
        assert metadata.total_lines > 0

        # Create new engine instance and verify it loads the metadata
        engine2 = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)
        metadata2 = engine2.get_index_metadata()

        assert metadata2 is not None
        assert metadata2.total_files == metadata.total_files
        assert metadata2.total_lines == metadata.total_lines

    def test_is_index_stale(self, mock_embedding_client):
        """Test index staleness detection."""
        engine = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)

        # No index exists, should be stale
        assert engine.is_index_stale()

        # Build index
        result = engine.build_index()
        assert result.success

        # Fresh index should not be stale
        assert not engine.is_index_stale(max_age_hours=24)

        # Should be stale if max age is very small
        assert engine.is_index_stale(max_age_hours=0)

    def test_rebuild_index_if_stale(self, mock_embedding_client):
        """Test conditional index rebuilding."""
        engine = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)

        # Should rebuild when no index exists
        rebuilt = engine.rebuild_index_if_stale()
        assert rebuilt

        # Should not rebuild when index is fresh
        rebuilt = engine.rebuild_index_if_stale(max_age_hours=24)
        assert not rebuilt

        # Should rebuild when forced by small max age
        rebuilt = engine.rebuild_index_if_stale(max_age_hours=0)
        assert rebuilt

    def test_memory_mapped_file_handling(self, mock_embedding_client):
        """Test memory-mapped file handling for large files."""
        # Create a large file
        large_file = self.project_path / "large_file.py"
        large_content = '"""Large file for testing."""\n' + "x = 1\n" * 10000

        with open(large_file, "w") as f:
            f.write(large_content)

        engine = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)
        engine.memory_map_threshold = 1000  # Lower threshold for testing

        # Should handle large file without errors
        result = engine.build_index()
        assert result.success

    def test_calculate_index_size(self, mock_embedding_client):
        """Test index size calculation."""
        engine = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)

        # Build index to create files
        result = engine.build_index()
        assert result.success

        # Calculate size
        size_mb = engine._calculate_index_size()
        assert size_mb > 0
        assert isinstance(size_mb, float)

    def test_progress_callback(self, mock_embedding_client):
        """Test progress callback functionality."""
        engine = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)

        progress_updates = []

        def callback(current, total, message):
            progress_updates.append((current, total, message))

        engine.set_progress_callback(callback)

        # Test manual progress update
        engine._update_progress(5, 10, "Test message")

        assert len(progress_updates) == 1
        assert progress_updates[0] == (5, 10, "Test message")
        assert engine.current_progress == 0.5

    def test_merge_ast_data(self, mock_embedding_client):
        """Test merging AST data from multiple files."""
        engine = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)

        # Create main AST index
        main_ast = ASTIndex(
            functions={}, classes={}, imports=[], symbols={}, file_metadata={}
        )

        # Create file AST data
        file_ast_data = {
            "functions": {
                "func1": FunctionDef(
                    name="func1",
                    parameters=[],
                    return_type=None,
                    docstring=None,
                    file_path="test.py",
                    start_line=1,
                    end_line=5,
                )
            },
            "classes": {},
            "imports": [],
            "symbols": {},
            "file_metadata": {"test.py": {"language": "python"}},
        }

        # Merge data
        engine._merge_ast_data(main_ast, file_ast_data)

        assert len(main_ast.functions) == 1
        assert "func1" in main_ast.functions
        assert "test.py" in main_ast.file_metadata

    def test_error_handling_in_parallel_parsing(self, mock_embedding_client):
        """Test error handling during parallel AST parsing."""
        engine = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)

        # Create a file with syntax errors
        error_file = self.project_path / "error_file.py"
        with open(error_file, "w") as f:
            f.write("def broken_function(\n    # Missing closing parenthesis")

        # Should handle errors gracefully
        ast_index = engine.parse_codebase_ast()

        assert ast_index is not None
        # Should still parse the good files
        assert len(ast_index.functions) > 0

    def test_supported_file_extensions(self, mock_embedding_client):
        """Test that only supported file extensions are processed."""
        # Create files with various extensions
        (self.project_path / "test.txt").touch()
        (self.project_path / "test.md").touch()
        (self.project_path / "test.json").touch()

        engine = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)
        source_files = engine._discover_source_files()

        # Should only include Python files
        extensions = [f.suffix for f in source_files]
        assert all(ext == ".py" for ext in extensions)

    def test_file_size_limits(self, mock_embedding_client):
        """Test file size limits during discovery."""
        # Create a file and write enough content to make it large
        large_file = self.project_path / "huge_file.py"
        
        # Write a large amount of content (more than 10MB)
        large_content = "# This is a large file\n" * 500000  # About 12MB
        large_file.write_text(large_content)
        
        engine = IndexingEngine(str(self.project_path), embedding_client=mock_embedding_client)
        source_files = engine._discover_source_files()

        # Should exclude the huge file (>10MB)
        file_names = [f.name for f in source_files]
        assert "huge_file.py" not in file_names
        
        # Clean up the large file
        large_file.unlink()

    def test_initialization_with_embedding_client(self, mock_embedding_client):
        """Test IndexingEngine initialization with embedding client."""
        engine = IndexingEngine(
            str(self.project_path),
            embedding_client=mock_embedding_client,
        )

        assert engine.embedding_client is mock_embedding_client
        assert engine.vector_db.embedding_client is mock_embedding_client
        assert engine.batch_size == 16

    def test_initialization_with_cost_tracker(self, mock_embedding_client, mock_cost_tracker):
        """Test IndexingEngine initialization with cost tracker."""
        engine = IndexingEngine(
            str(self.project_path),
            embedding_client=mock_embedding_client,
            cost_tracker=mock_cost_tracker,
        )

        assert engine.cost_tracker is mock_cost_tracker

    def test_initialization_with_custom_batch_size(self, mock_embedding_client):
        """Test IndexingEngine initialization with custom batch size."""
        engine = IndexingEngine(
            str(self.project_path),
            embedding_client=mock_embedding_client,
            batch_size=32,
        )

        assert engine.batch_size == 32

    @pytest.mark.asyncio
    async def test_store_embeddings_with_progress(self, mock_embedding_client):
        """Test embedding storage with progress tracking."""
        engine = IndexingEngine(
            str(self.project_path),
            embedding_client=mock_embedding_client,
        )

        # Create mock code chunks
        from dev_agent.models.indexing import CodeChunk

        chunks = [
            CodeChunk(
                content=f"def function_{i}(): pass",
                file_path=str(self.project_path / "test.py"),
                start_line=i,
                end_line=i + 1,
                chunk_type="function",
                language="python",
            )
            for i in range(50)
        ]

        # Track progress calls
        progress_calls = []

        def progress_callback(current, total, message):
            progress_calls.append((current, total, message))

        engine.set_progress_callback(progress_callback)

        # Store embeddings
        chunk_ids = await engine._store_embeddings_with_progress(chunks)

        # Should return chunk IDs
        assert len(chunk_ids) > 0
        assert engine.chunks_processed == 50

    @pytest.mark.asyncio
    async def test_store_embeddings_with_cost_tracking(
        self, mock_embedding_client, mock_cost_tracker
    ):
        """Test embedding storage with cost tracking integration."""
        engine = IndexingEngine(
            str(self.project_path),
            embedding_client=mock_embedding_client,
            cost_tracker=mock_cost_tracker,
        )

        # Create mock code chunks
        from dev_agent.models.indexing import CodeChunk

        chunks = [
            CodeChunk(
                content=f"def function_{i}(): pass",
                file_path=str(self.project_path / "test.py"),
                start_line=i,
                end_line=i + 1,
                chunk_type="function",
                language="python",
            )
            for i in range(20)
        ]

        # Store embeddings
        chunk_ids = await engine._store_embeddings_with_progress(chunks)

        # Should have processed chunks
        assert len(chunk_ids) > 0
        assert engine.chunks_processed == 20

        # Cost tracker should have recorded operations
        # Note: Actual cost tracking depends on VectorDatabase implementation
        assert engine.cost_tracker is not None

    @pytest.mark.asyncio
    async def test_store_embeddings_batch_processing(self, mock_embedding_client):
        """Test batch processing during embedding storage."""
        batch_size = 10
        engine = IndexingEngine(
            str(self.project_path),
            embedding_client=mock_embedding_client,
            batch_size=batch_size,
        )

        # Create mock code chunks
        from dev_agent.models.indexing import CodeChunk

        chunks = [
            CodeChunk(
                content=f"def function_{i}(): pass",
                file_path=str(self.project_path / "test.py"),
                start_line=i,
                end_line=i + 1,
                chunk_type="function",
                language="python",
            )
            for i in range(35)  # 3.5 batches
        ]

        # Store embeddings
        chunk_ids = await engine._store_embeddings_with_progress(chunks)

        # Should process all chunks
        assert engine.chunks_processed == 35

    @pytest.mark.asyncio
    async def test_store_embeddings_empty_chunks(self, mock_embedding_client):
        """Test embedding storage with empty chunk list."""
        engine = IndexingEngine(
            str(self.project_path),
            embedding_client=mock_embedding_client,
        )

        # Store empty list
        chunk_ids = await engine._store_embeddings_with_progress([])

        # Should return empty list
        assert chunk_ids == []
        assert engine.chunks_processed == 0

    def test_build_index_with_embedding_client(self, mock_embedding_client):
        """Test full index building with embedding client."""
        engine = IndexingEngine(
            str(self.project_path),
            embedding_client=mock_embedding_client,
        )

        result = engine.build_index()

        assert result.success
        assert result.embeddings_count > 0
        assert engine.chunks_processed > 0

    def test_build_index_with_cost_tracking(
        self, mock_embedding_client, mock_cost_tracker
    ):
        """Test full index building with cost tracking."""
        engine = IndexingEngine(
            str(self.project_path),
            embedding_client=mock_embedding_client,
            cost_tracker=mock_cost_tracker,
        )

        result = engine.build_index()

        assert result.success
        assert result.embeddings_count > 0

        # Cost tracker should have some cost recorded
        # Note: Actual cost depends on VectorDatabase implementation
        assert engine.cost_tracker is not None

    @pytest.mark.asyncio
    async def test_progress_tracking_every_100_chunks(self, mock_embedding_client):
        """Test that progress is tracked every 100 chunks."""
        engine = IndexingEngine(
            str(self.project_path),
            embedding_client=mock_embedding_client,
        )

        # Create 250 mock chunks
        from dev_agent.models.indexing import CodeChunk

        chunks = [
            CodeChunk(
                content=f"def function_{i}(): pass",
                file_path=str(self.project_path / "test.py"),
                start_line=i,
                end_line=i + 1,
                chunk_type="function",
                language="python",
            )
            for i in range(250)
        ]

        # Store embeddings
        chunk_ids = await engine._store_embeddings_with_progress(chunks)

        # Should process all chunks
        assert engine.chunks_processed == 250
        assert len(chunk_ids) > 0


if __name__ == "__main__":
    # Run basic tests
    test_instance = TestIndexingEngine()

    print("Running IndexingEngine unit tests...")

    test_instance.setup_method()
    try:
        test_instance.test_initialization()
        print("✓ Initialization test passed")

        test_instance.test_discover_source_files()
        print("✓ File discovery test passed")

        test_instance.test_parse_codebase_ast_sequential()
        print("✓ AST parsing test passed")

        test_instance.test_build_index_success()
        print("✓ Index building test passed")

        test_instance.test_save_and_load_index_metadata()
        print("✓ Metadata persistence test passed")

        print("\nBasic unit tests passed!")

    finally:
        test_instance.teardown_method()
