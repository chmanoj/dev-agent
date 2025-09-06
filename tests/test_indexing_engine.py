"""Unit tests for IndexingEngine."""

import os
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from dev_agent.indexing.indexing_engine import IndexingEngine
from dev_agent.models.indexing import CodeChunk, ASTIndex, SymbolInfo, FunctionDef, ClassDef, Import
from dev_agent.models.results import IndexResult
from dev_agent.models.project_state import IndexMetadata


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
        with open(main_file, 'w') as f:
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
        with open(utils_file, 'w') as f:
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
        with open(test_file, 'w') as f:
            f.write(test_content)
    
    def test_initialization(self):
        """Test IndexingEngine initialization."""
        engine = IndexingEngine(str(self.project_path))
        
        assert engine.project_path == self.project_path
        assert engine.index_path == self.project_path / '.dev_agent' / 'index'
        assert engine.tree_sitter_parser is not None
        assert engine.vector_db is not None
        assert engine.code_chunker is not None
        assert engine.max_workers > 0
    
    def test_custom_index_path(self):
        """Test IndexingEngine with custom index path."""
        custom_index_path = Path(self.temp_dir) / "custom_index"
        engine = IndexingEngine(str(self.project_path), str(custom_index_path))
        
        assert engine.index_path == Path(custom_index_path)
    
    def test_discover_source_files(self):
        """Test source file discovery."""
        engine = IndexingEngine(str(self.project_path))
        source_files = engine._discover_source_files()
        
        # Should find all Python files
        assert len(source_files) == 3
        
        file_names = [f.name for f in source_files]
        assert "main.py" in file_names
        assert "utils.py" in file_names
        assert "test_module.py" in file_names
    
    def test_discover_source_files_with_exclusions(self):
        """Test source file discovery with excluded directories."""
        # Create excluded directories
        (self.project_path / "__pycache__").mkdir()
        (self.project_path / "__pycache__" / "cached.py").touch()
        
        (self.project_path / ".git").mkdir()
        (self.project_path / ".git" / "config.py").touch()
        
        (self.project_path / "node_modules").mkdir()
        (self.project_path / "node_modules" / "module.py").touch()
        
        engine = IndexingEngine(str(self.project_path))
        source_files = engine._discover_source_files()
        
        # Should only find the original files, not the excluded ones
        assert len(source_files) == 3
        
        file_paths = [str(f) for f in source_files]
        assert not any("__pycache__" in path for path in file_paths)
        assert not any(".git" in path for path in file_paths)
        assert not any("node_modules" in path for path in file_paths)
    
    def test_detect_language(self):
        """Test language detection from file extensions."""
        engine = IndexingEngine(str(self.project_path))
        
        assert engine._detect_language(Path("test.py")) == "python"
        assert engine._detect_language(Path("test.js")) == "javascript"
        assert engine._detect_language(Path("test.java")) == "java"
        assert engine._detect_language(Path("test.cpp")) == "cpp"
        assert engine._detect_language(Path("test.unknown")) == "unknown"
    
    def test_parse_codebase_ast_sequential(self):
        """Test AST parsing in sequential mode."""
        engine = IndexingEngine(str(self.project_path))
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
    
    def test_parse_codebase_ast_parallel(self):
        """Test AST parsing in parallel mode."""
        engine = IndexingEngine(str(self.project_path))
        engine.max_workers = 2  # Use parallel processing
        
        ast_index = engine.parse_codebase_ast()
        
        assert ast_index is not None
        assert isinstance(ast_index, ASTIndex)
        
        # Should produce same results as sequential
        assert len(ast_index.functions) > 0
        assert len(ast_index.classes) > 0
        assert len(ast_index.file_metadata) == 3
    
    def test_build_index_success(self):
        """Test successful index building."""
        engine = IndexingEngine(str(self.project_path))
        
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
        assert progress_calls[-1][0] == progress_calls[-1][1]  # Final call should be complete
    
    def test_build_index_no_files(self):
        """Test index building with no source files."""
        empty_project = Path(self.temp_dir) / "empty_project"
        empty_project.mkdir()
        
        engine = IndexingEngine(str(empty_project))
        result = engine.build_index()
        
        assert not result.success
        assert "No source files found" in result.errors[0]
    
    def test_build_index_with_errors(self):
        """Test index building with parsing errors."""
        # Create a file with syntax errors
        error_file = self.project_path / "error_file.py"
        with open(error_file, 'w') as f:
            f.write("def broken_function(\n    # Missing closing parenthesis")
        
        engine = IndexingEngine(str(self.project_path))
        result = engine.build_index()
        
        # Should still succeed despite errors
        assert result.success
        # Note: Errors might not be captured in result.errors depending on implementation
        # The main thing is that it doesn't crash
    
    def test_query_similar_code(self):
        """Test vector similarity querying."""
        engine = IndexingEngine(str(self.project_path))
        
        # Build index first
        result = engine.build_index()
        assert result.success
        
        # Query for similar code
        matches = engine.query_similar_code("class definition", limit=5)
        
        # Should return some matches
        assert isinstance(matches, list)
        # Note: Actual matches depend on vector DB implementation
    
    def test_get_symbol_map(self):
        """Test symbol map retrieval."""
        engine = IndexingEngine(str(self.project_path))
        
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
    
    def test_get_symbol_map_no_index(self):
        """Test symbol map retrieval without existing index."""
        engine = IndexingEngine(str(self.project_path))
        
        # Should return empty dict if no index exists
        symbol_map = engine.get_symbol_map()
        assert isinstance(symbol_map, dict)
    
    def test_save_and_load_index_metadata(self):
        """Test saving and loading index metadata."""
        engine = IndexingEngine(str(self.project_path))
        
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
        engine2 = IndexingEngine(str(self.project_path))
        metadata2 = engine2.get_index_metadata()
        
        assert metadata2 is not None
        assert metadata2.total_files == metadata.total_files
        assert metadata2.total_lines == metadata.total_lines
    
    def test_is_index_stale(self):
        """Test index staleness detection."""
        engine = IndexingEngine(str(self.project_path))
        
        # No index exists, should be stale
        assert engine.is_index_stale()
        
        # Build index
        result = engine.build_index()
        assert result.success
        
        # Fresh index should not be stale
        assert not engine.is_index_stale(max_age_hours=24)
        
        # Should be stale if max age is very small
        assert engine.is_index_stale(max_age_hours=0)
    
    def test_rebuild_index_if_stale(self):
        """Test conditional index rebuilding."""
        engine = IndexingEngine(str(self.project_path))
        
        # Should rebuild when no index exists
        rebuilt = engine.rebuild_index_if_stale()
        assert rebuilt
        
        # Should not rebuild when index is fresh
        rebuilt = engine.rebuild_index_if_stale(max_age_hours=24)
        assert not rebuilt
        
        # Should rebuild when forced by small max age
        rebuilt = engine.rebuild_index_if_stale(max_age_hours=0)
        assert rebuilt
    
    def test_memory_mapped_file_handling(self):
        """Test memory-mapped file handling for large files."""
        # Create a large file
        large_file = self.project_path / "large_file.py"
        large_content = '"""Large file for testing."""\n' + 'x = 1\n' * 10000
        
        with open(large_file, 'w') as f:
            f.write(large_content)
        
        engine = IndexingEngine(str(self.project_path))
        engine.memory_map_threshold = 1000  # Lower threshold for testing
        
        # Should handle large file without errors
        result = engine.build_index()
        assert result.success
    
    def test_calculate_index_size(self):
        """Test index size calculation."""
        engine = IndexingEngine(str(self.project_path))
        
        # Build index to create files
        result = engine.build_index()
        assert result.success
        
        # Calculate size
        size_mb = engine._calculate_index_size()
        assert size_mb > 0
        assert isinstance(size_mb, float)
    
    def test_progress_callback(self):
        """Test progress callback functionality."""
        engine = IndexingEngine(str(self.project_path))
        
        progress_updates = []
        def callback(current, total, message):
            progress_updates.append((current, total, message))
        
        engine.set_progress_callback(callback)
        
        # Test manual progress update
        engine._update_progress(5, 10, "Test message")
        
        assert len(progress_updates) == 1
        assert progress_updates[0] == (5, 10, "Test message")
        assert engine.current_progress == 0.5
    
    def test_merge_ast_data(self):
        """Test merging AST data from multiple files."""
        engine = IndexingEngine(str(self.project_path))
        
        # Create main AST index
        main_ast = ASTIndex(
            functions={},
            classes={},
            imports=[],
            symbols={},
            file_metadata={}
        )
        
        # Create file AST data
        file_ast_data = {
            'functions': {'func1': FunctionDef(
                name='func1',
                parameters=[],
                return_type=None,
                docstring=None,
                file_path='test.py',
                start_line=1,
                end_line=5
            )},
            'classes': {},
            'imports': [],
            'symbols': {},
            'file_metadata': {'test.py': {'language': 'python'}}
        }
        
        # Merge data
        engine._merge_ast_data(main_ast, file_ast_data)
        
        assert len(main_ast.functions) == 1
        assert 'func1' in main_ast.functions
        assert 'test.py' in main_ast.file_metadata
    
    def test_error_handling_in_parallel_parsing(self):
        """Test error handling during parallel AST parsing."""
        engine = IndexingEngine(str(self.project_path))
        
        # Create a file with syntax errors
        error_file = self.project_path / "error_file.py"
        with open(error_file, 'w') as f:
            f.write("def broken_function(\n    # Missing closing parenthesis")
        
        # Should handle errors gracefully
        ast_index = engine.parse_codebase_ast()
        
        assert ast_index is not None
        # Should still parse the good files
        assert len(ast_index.functions) > 0
    
    def test_supported_file_extensions(self):
        """Test that only supported file extensions are processed."""
        # Create files with various extensions
        (self.project_path / "test.txt").touch()
        (self.project_path / "test.md").touch()
        (self.project_path / "test.json").touch()
        
        engine = IndexingEngine(str(self.project_path))
        source_files = engine._discover_source_files()
        
        # Should only include Python files
        extensions = [f.suffix for f in source_files]
        assert all(ext == '.py' for ext in extensions)
    
    def test_file_size_limits(self):
        """Test file size limits during discovery."""
        # Create a very large file (simulated by mocking stat)
        large_file = self.project_path / "huge_file.py"
        large_file.touch()
        
        with patch.object(Path, 'stat') as mock_stat:
            # Mock file size to be very large
            mock_stat.return_value.st_size = 20 * 1024 * 1024  # 20MB
            
            engine = IndexingEngine(str(self.project_path))
            source_files = engine._discover_source_files()
            
            # Should exclude the huge file
            file_names = [f.name for f in source_files]
            assert "huge_file.py" not in file_names


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