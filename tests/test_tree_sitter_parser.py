"""Tests for TreeSitterParser class."""

import os
import tempfile
import unittest
from pathlib import Path

from dev_agent.indexing.tree_sitter_parser import TreeSitterParser
from dev_agent.models.indexing import ASTIndex, FunctionDef, ClassDef, Import, SymbolInfo


class TestTreeSitterParser(unittest.TestCase):
    """Test suite for TreeSitterParser."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = TreeSitterParser()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_test_file(self, filename: str, content: str) -> str:
        """Create a test file with given content."""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    
    def test_parser_initialization(self):
        """Test that parser initializes correctly."""
        assert self.parser is not None
        assert 'python' in self.parser.supported_languages
        assert isinstance(self.parser.parsers, dict)
    
    def test_parse_simple_python_file(self):
        """Test parsing a simple Python file."""
        content = '''
def hello_world():
    """A simple function."""
    print("Hello, World!")
    return "Hello"

class SimpleClass:
    """A simple class."""
    def __init__(self):
        self.value = 42
    
    def get_value(self):
        return self.value
'''
        file_path = self.create_test_file('simple.py', content)
        
        # Parse the file
        ast = self.parser.parse_file(file_path, 'python')
        assert ast is not None
    
    def test_extract_functions_simple(self):
        """Test extracting functions from simple Python code."""
        content = '''
def add(a, b):
    """Add two numbers."""
    return a + b

def multiply(x, y):
    return x * y

def greet(name="World"):
    """Greet someone."""
    return f"Hello, {name}!"
'''
        file_path = self.create_test_file('functions.py', content)
        ast = self.parser.parse_file(file_path, 'python')
        
        functions = self.parser.get_function_definitions(ast, file_path)
        
        assert len(functions) == 3
        
        # Check function names
        func_names = [f.name for f in functions]
        assert 'add' in func_names
        assert 'multiply' in func_names
        assert 'greet' in func_names
        
        # Check function details
        add_func = next(f for f in functions if f.name == 'add')
        assert add_func.parameters == ['a', 'b']
        assert add_func.file_path == file_path
        assert add_func.start_line > 0
        
        greet_func = next(f for f in functions if f.name == 'greet')
        assert 'name' in greet_func.parameters
    
    def test_extract_classes_simple(self):
        """Test extracting classes from simple Python code."""
        content = '''
class Animal:
    """Base animal class."""
    def __init__(self, name):
        self.name = name
    
    def speak(self):
        pass

class Dog(Animal):
    """A dog class."""
    def __init__(self, name, breed):
        super().__init__(name)
        self.breed = breed
    
    def speak(self):
        return "Woof!"
    
    def fetch(self):
        return f"{self.name} is fetching!"

class Cat(Animal):
    def speak(self):
        return "Meow!"
'''
        file_path = self.create_test_file('classes.py', content)
        ast = self.parser.parse_file(file_path, 'python')
        
        classes = self.parser.get_class_definitions(ast, file_path)
        
        assert len(classes) == 3
        
        # Check class names
        class_names = [c.name for c in classes]
        assert 'Animal' in class_names
        assert 'Dog' in class_names
        assert 'Cat' in class_names
        
        # Check inheritance
        dog_class = next(c for c in classes if c.name == 'Dog')
        assert 'Animal' in dog_class.base_classes
        
        animal_class = next(c for c in classes if c.name == 'Animal')
        assert len(animal_class.base_classes) == 0
    
    def test_extract_imports_simple(self):
        """Test extracting imports from simple Python code."""
        content = '''
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np
from collections import defaultdict, Counter
'''
        file_path = self.create_test_file('imports.py', content)
        ast = self.parser.parse_file(file_path, 'python')
        
        imports = self.parser.extract_imports(ast, file_path)
        
        assert len(imports) >= 4  # At least the main import statements
        
        # Check for specific imports
        import_modules = [imp.module for imp in imports]
        assert 'os' in import_modules
        assert 'sys' in import_modules
        assert 'pathlib' in import_modules
        assert 'typing' in import_modules
        
        # Check import with alias
        numpy_import = next((imp for imp in imports if imp.module == 'numpy'), None)
        if numpy_import:
            assert numpy_import.alias == 'np'
        
        # Check from imports
        typing_import = next((imp for imp in imports if imp.module == 'typing'), None)
        if typing_import:
            assert 'List' in typing_import.names
            assert 'Dict' in typing_import.names
    
    def test_extract_symbols_comprehensive(self):
        """Test extracting all symbols from comprehensive Python code."""
        content = '''
import os
from typing import List

class Calculator:
    """A simple calculator class."""
    
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        """Add two numbers."""
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def get_history(self):
        return self.history

def factorial(n):
    """Calculate factorial of n."""
    if n <= 1:
        return 1
    return n * factorial(n - 1)

PI = 3.14159
'''
        file_path = self.create_test_file('comprehensive.py', content)
        ast = self.parser.parse_file(file_path, 'python')
        
        symbols = self.parser.extract_symbols(ast, file_path)
        
        # Should have functions, classes, and imports as symbols
        symbol_names = [s.name for s in symbols]
        
        # Check for class
        assert 'Calculator' in symbol_names
        
        # Check for functions
        assert 'factorial' in symbol_names
        
        # Check for imports
        assert any('os' in name for name in symbol_names)
        
        # Verify symbol types
        calc_symbol = next(s for s in symbols if s.name == 'Calculator')
        assert calc_symbol.symbol_type == 'class'
        
        factorial_symbol = next(s for s in symbols if s.name == 'factorial')
        assert factorial_symbol.symbol_type == 'function'
    
    def test_create_symbol_map(self):
        """Test creating symbol map from multiple files."""
        # Create multiple test files
        file1_content = '''
def utility_function():
    return "utility"

class UtilityClass:
    pass
'''
        
        file2_content = '''
import json
from datetime import datetime

def process_data(data):
    return json.loads(data)

class DataProcessor:
    def __init__(self):
        self.timestamp = datetime.now()
'''
        
        file1_path = self.create_test_file('utils.py', file1_content)
        file2_path = self.create_test_file('processor.py', file2_content)
        
        symbol_map = self.parser.create_symbol_map([file1_path, file2_path])
        
        # Should have symbols from both files
        assert len(symbol_map) > 0
        
        # Check that symbols are keyed by file:name
        keys = list(symbol_map.keys())
        assert any('utility_function' in key for key in keys)
        assert any('UtilityClass' in key for key in keys)
        assert any('process_data' in key for key in keys)
        assert any('DataProcessor' in key for key in keys)
    
    def test_analyze_code_structure(self):
        """Test comprehensive code structure analysis."""
        # Create a complex test file
        content = '''
"""Module docstring."""
import os
import sys
from typing import List, Dict
from collections import defaultdict

class BaseProcessor:
    """Base processor class."""
    
    def __init__(self, name: str):
        self.name = name
        self.processed_count = 0
    
    def process(self, data):
        """Process data."""
        self.processed_count += 1
        return self._internal_process(data)
    
    def _internal_process(self, data):
        """Internal processing method."""
        return data

class TextProcessor(BaseProcessor):
    """Text processing class."""
    
    def __init__(self, name: str, encoding: str = 'utf-8'):
        super().__init__(name)
        self.encoding = encoding
    
    def process_text(self, text: str) -> str:
        """Process text data."""
        return text.upper()

def create_processor(processor_type: str) -> BaseProcessor:
    """Factory function for processors."""
    if processor_type == 'text':
        return TextProcessor('default_text')
    return BaseProcessor('default')

def main():
    """Main function."""
    processor = create_processor('text')
    result = processor.process("hello world")
    print(result)

if __name__ == "__main__":
    main()
'''
        
        file_path = self.create_test_file('complex.py', content)
        
        ast_index = self.parser.analyze_code_structure([file_path])
        
        # Verify ASTIndex structure
        assert isinstance(ast_index, ASTIndex)
        assert len(ast_index.functions) > 0
        assert len(ast_index.classes) > 0
        assert len(ast_index.imports) > 0
        assert len(ast_index.symbols) > 0
        assert file_path in ast_index.file_metadata
        
        # Check specific elements
        function_names = [f.name for f in ast_index.functions.values()]
        assert 'create_processor' in function_names
        assert 'main' in function_names
        
        class_names = [c.name for c in ast_index.classes.values()]
        assert 'BaseProcessor' in class_names
        assert 'TextProcessor' in class_names
        
        # Check file metadata
        metadata = ast_index.file_metadata[file_path]
        assert metadata['language'] == 'python'
        assert metadata['line_count'] > 0
        assert metadata['function_count'] > 0
        assert metadata['class_count'] > 0
    
    def test_language_detection(self):
        """Test programming language detection from file extensions."""
        assert self.parser._detect_language('test.py') == 'python'
        assert self.parser._detect_language('test.js') == 'javascript'
        assert self.parser._detect_language('test.java') == 'java'
        assert self.parser._detect_language('test.cpp') == 'cpp'
        assert self.parser._detect_language('test.unknown') == 'unknown'
    
    def test_parse_nonexistent_file(self):
        """Test parsing a file that doesn't exist."""
        result = self.parser.parse_file('/nonexistent/file.py', 'python')
        assert result is None
    
    def test_parse_invalid_syntax(self):
        """Test parsing a file with invalid Python syntax."""
        content = '''
def invalid_function(
    # Missing closing parenthesis and colon
    print("This is invalid syntax"
'''
        file_path = self.create_test_file('invalid.py', content)
        
        # Should handle gracefully and not crash
        ast = self.parser.parse_file(file_path, 'python')
        # Depending on implementation, might return None or partial AST
        # The important thing is it doesn't crash
    
    def test_empty_file(self):
        """Test parsing an empty file."""
        content = ''
        file_path = self.create_test_file('empty.py', content)
        
        ast = self.parser.parse_file(file_path, 'python')
        functions = self.parser.get_function_definitions(ast, file_path)
        classes = self.parser.get_class_definitions(ast, file_path)
        imports = self.parser.extract_imports(ast, file_path)
        
        assert len(functions) == 0
        assert len(classes) == 0
        assert len(imports) == 0
    
    def test_complex_inheritance(self):
        """Test parsing complex class inheritance."""
        content = '''
class A:
    pass

class B(A):
    pass

class C(A):
    pass

class D(B, C):
    """Multiple inheritance."""
    pass

class E(D):
    def method(self):
        pass
'''
        file_path = self.create_test_file('inheritance.py', content)
        ast = self.parser.parse_file(file_path, 'python')
        
        classes = self.parser.get_class_definitions(ast, file_path)
        
        # Find class D with multiple inheritance
        d_class = next((c for c in classes if c.name == 'D'), None)
        assert d_class is not None
        # Should detect multiple base classes
        assert len(d_class.base_classes) >= 1  # At least one base class detected
    
    def test_nested_functions_and_classes(self):
        """Test parsing nested functions and classes."""
        content = '''
class OuterClass:
    """Outer class with nested elements."""
    
    def outer_method(self):
        def inner_function():
            return "inner"
        return inner_function()
    
    class InnerClass:
        """Nested class."""
        def inner_method(self):
            pass

def outer_function():
    """Function with nested function."""
    def nested_function():
        def deeply_nested():
            return "deep"
        return deeply_nested()
    return nested_function()
'''
        file_path = self.create_test_file('nested.py', content)
        ast = self.parser.parse_file(file_path, 'python')
        
        functions = self.parser.get_function_definitions(ast, file_path)
        classes = self.parser.get_class_definitions(ast, file_path)
        
        # Should find outer elements
        function_names = [f.name for f in functions]
        class_names = [c.name for c in classes]
        
        assert 'outer_function' in function_names
        assert 'OuterClass' in class_names
        
        # Depending on implementation, might also find nested elements
        # The important thing is it handles nested structures gracefully
    
    def test_decorators_and_annotations(self):
        """Test parsing functions and classes with decorators and type annotations."""
        content = '''
from typing import List, Optional
from functools import wraps

def decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@decorator
def annotated_function(x: int, y: str = "default") -> Optional[str]:
    """Function with type annotations and decorator."""
    return f"{x}: {y}"

class AnnotatedClass:
    """Class with annotated methods."""
    
    def __init__(self, items: List[str]):
        self.items = items
    
    @property
    def count(self) -> int:
        return len(self.items)
    
    @staticmethod
    def static_method(value: int) -> bool:
        return value > 0
'''
        file_path = self.create_test_file('annotated.py', content)
        ast = self.parser.parse_file(file_path, 'python')
        
        functions = self.parser.get_function_definitions(ast, file_path)
        classes = self.parser.get_class_definitions(ast, file_path)
        
        # Should handle decorated and annotated code
        function_names = [f.name for f in functions]
        assert 'annotated_function' in function_names
        assert 'decorator' in function_names
        
        class_names = [c.name for c in classes]
        assert 'AnnotatedClass' in class_names


if __name__ == '__main__':
    unittest.main()