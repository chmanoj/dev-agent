"""Integration tests for TreeSitterParser with real Python files."""

import unittest
import os
from pathlib import Path

from dev_agent.indexing.tree_sitter_parser import TreeSitterParser


class TestTreeSitterIntegration(unittest.TestCase):
    """Integration tests for TreeSitterParser with sample files."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = TreeSitterParser()
        self.test_dir = Path(__file__).parent
        self.sample_files_dir = self.test_dir / 'sample_files'
    
    def test_parse_simple_module(self):
        """Test parsing the simple module sample file."""
        file_path = str(self.sample_files_dir / 'simple_module.py')
        
        if not os.path.exists(file_path):
            self.skipTest(f"Sample file not found: {file_path}")
        
        # Parse the file
        ast = self.parser.parse_file(file_path, 'python')
        self.assertIsNotNone(ast)
        
        # Extract functions
        functions = self.parser.get_function_definitions(ast, file_path)
        function_names = [f.name for f in functions]
        
        # Should find the expected functions
        self.assertIn('add', function_names)
        self.assertIn('subtract', function_names)
        
        # Extract classes
        classes = self.parser.get_class_definitions(ast, file_path)
        class_names = [c.name for c in classes]
        
        # Should find the Calculator class
        self.assertIn('Calculator', class_names)
        
        # Check Calculator class details
        calc_class = next(c for c in classes if c.name == 'Calculator')
        self.assertEqual(calc_class.file_path, file_path)
        self.assertGreater(calc_class.start_line, 0)
    
    def test_parse_complex_module(self):
        """Test parsing the complex module sample file."""
        file_path = str(self.sample_files_dir / 'complex_module.py')
        
        if not os.path.exists(file_path):
            self.skipTest(f"Sample file not found: {file_path}")
        
        # Parse the file
        ast = self.parser.parse_file(file_path, 'python')
        self.assertIsNotNone(ast)
        
        # Extract all components
        functions = self.parser.get_function_definitions(ast, file_path)
        classes = self.parser.get_class_definitions(ast, file_path)
        imports = self.parser.extract_imports(ast, file_path)
        symbols = self.parser.extract_symbols(ast, file_path)
        
        # Check functions
        function_names = [f.name for f in functions]
        expected_functions = ['retry', 'process_file', 'main']
        for func_name in expected_functions:
            self.assertIn(func_name, function_names)
        
        # Check classes
        class_names = [c.name for c in classes]
        expected_classes = ['Config', 'ProcessorError', 'BaseProcessor', 'TextProcessor', 'JSONProcessor', 'ProcessorFactory']
        for class_name in expected_classes:
            self.assertIn(class_name, class_names)
        
        # Check imports
        import_modules = [imp.module for imp in imports]
        expected_imports = ['os', 'sys', 'typing', 'abc', 'dataclasses', 'functools', 'json']
        for import_name in expected_imports:
            self.assertIn(import_name, import_modules)
        
        # Check inheritance
        base_processor = next((c for c in classes if c.name == 'BaseProcessor'), None)
        self.assertIsNotNone(base_processor)
        
        text_processor = next((c for c in classes if c.name == 'TextProcessor'), None)
        self.assertIsNotNone(text_processor)
        self.assertIn('BaseProcessor', text_processor.base_classes)
        
        # Verify symbol extraction
        symbol_names = [s.name for s in symbols]
        self.assertIn('Config', symbol_names)
        self.assertIn('main', symbol_names)
        self.assertIn('os', symbol_names)  # Import should be in symbols
    
    def test_analyze_multiple_files(self):
        """Test analyzing multiple sample files together."""
        simple_file = str(self.sample_files_dir / 'simple_module.py')
        complex_file = str(self.sample_files_dir / 'complex_module.py')
        
        # Skip if files don't exist
        if not (os.path.exists(simple_file) and os.path.exists(complex_file)):
            self.skipTest("Sample files not found")
        
        # Analyze code structure
        ast_index = self.parser.analyze_code_structure([simple_file, complex_file])
        
        # Verify the index contains data from both files
        self.assertGreater(len(ast_index.functions), 0)
        self.assertGreater(len(ast_index.classes), 0)
        self.assertGreater(len(ast_index.imports), 0)
        self.assertGreater(len(ast_index.symbols), 0)
        
        # Check that both files are in metadata
        self.assertIn(simple_file, ast_index.file_metadata)
        self.assertIn(complex_file, ast_index.file_metadata)
        
        # Verify metadata
        simple_metadata = ast_index.file_metadata[simple_file]
        complex_metadata = ast_index.file_metadata[complex_file]
        
        self.assertEqual(simple_metadata['language'], 'python')
        self.assertEqual(complex_metadata['language'], 'python')
        self.assertGreater(simple_metadata['line_count'], 0)
        self.assertGreater(complex_metadata['line_count'], 0)
        
        # Complex file should have more functions and classes
        self.assertGreater(complex_metadata['function_count'], simple_metadata['function_count'])
        self.assertGreater(complex_metadata['class_count'], simple_metadata['class_count'])
    
    def test_symbol_map_creation(self):
        """Test creating symbol map from sample files."""
        simple_file = str(self.sample_files_dir / 'simple_module.py')
        complex_file = str(self.sample_files_dir / 'complex_module.py')
        
        # Skip if files don't exist
        if not (os.path.exists(simple_file) and os.path.exists(complex_file)):
            self.skipTest("Sample files not found")
        
        # Create symbol map
        symbol_map = self.parser.create_symbol_map([simple_file, complex_file])
        
        # Should have symbols from both files
        self.assertGreater(len(symbol_map), 0)
        
        # Check for specific symbols
        symbol_keys = list(symbol_map.keys())
        
        # Should have Calculator from simple file
        calc_keys = [key for key in symbol_keys if 'Calculator' in key]
        self.assertGreater(len(calc_keys), 0)
        
        # Should have BaseProcessor from complex file
        processor_keys = [key for key in symbol_keys if 'BaseProcessor' in key]
        self.assertGreater(len(processor_keys), 0)
        
        # Verify symbol information
        for symbol_info in symbol_map.values():
            self.assertIsNotNone(symbol_info.name)
            self.assertIsNotNone(symbol_info.symbol_type)
            self.assertIsNotNone(symbol_info.file_path)
            self.assertGreater(symbol_info.line_number, 0)
    
    def test_performance_with_large_file(self):
        """Test parser performance with the complex module."""
        file_path = str(self.sample_files_dir / 'complex_module.py')
        
        if not os.path.exists(file_path):
            self.skipTest(f"Sample file not found: {file_path}")
        
        import time
        
        # Measure parsing time
        start_time = time.time()
        ast = self.parser.parse_file(file_path, 'python')
        parse_time = time.time() - start_time
        
        # Should parse reasonably quickly (less than 1 second for this file)
        self.assertLess(parse_time, 1.0)
        self.assertIsNotNone(ast)
        
        # Measure analysis time
        start_time = time.time()
        ast_index = self.parser.analyze_code_structure([file_path])
        analysis_time = time.time() - start_time
        
        # Should analyze reasonably quickly
        self.assertLess(analysis_time, 2.0)
        self.assertIsNotNone(ast_index)
        
        # Verify completeness
        self.assertGreater(len(ast_index.functions), 5)
        self.assertGreater(len(ast_index.classes), 5)
        self.assertGreater(len(ast_index.imports), 5)


if __name__ == '__main__':
    unittest.main()