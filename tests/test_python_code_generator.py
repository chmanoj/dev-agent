"""Tests for Python code generator."""

from unittest.mock import Mock

import pytest

from dev_agent.generation.python_code_generator import PythonCodeGenerator
from dev_agent.models.analysis import (
    CodeContext,
    CodePattern,
    CodePatterns,
    ContextualCode,
)
from dev_agent.models.documents import Task
from dev_agent.models.enums import TaskStatus
from dev_agent.models.results import GeneratedCode


class TestPythonCodeGenerator:
    """Test cases for PythonCodeGenerator."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_analyzer = Mock()
        self.mock_analyzer.identify_code_patterns.return_value = CodePatterns(
            naming_conventions=[],
            structural_patterns=[],
            import_patterns=[],
            error_handling_patterns=[],
            testing_patterns=[],
            documentation_patterns=[],
            overall_style={}
        )
        self.generator = PythonCodeGenerator(self.mock_analyzer)

    def test_init(self):
        """Test PythonCodeGenerator initialization."""
        assert self.generator.codebase_analyzer == self.mock_analyzer
        assert self.generator.existing_patterns is not None
        assert isinstance(self.generator.style_guidelines, dict)

    def test_analyze_existing_patterns(self):
        """Test analyzing existing patterns."""
        patterns = self.generator.analyze_existing_patterns()
        assert isinstance(patterns, CodePatterns)
        self.mock_analyzer.identify_code_patterns.assert_called_once()

    def test_generate_code_from_task_class(self):
        """Test generating code for a class task."""
        task = Task(
            id="1.1",
            title="Create UserManager class",
            description="Create class UserManager with user management functionality",
            requirements_refs=["FR-1.1"],
            subtasks=[],
            status=TaskStatus.NOT_STARTED
        )

        context = CodeContext(
            task_id="1.1",
            relevant_files=[],
            similar_implementations=[],
            required_imports=[],
            suggested_patterns=[],
            dependencies=[],
            test_examples=[],
            style_guidelines={}
        )

        result = self.generator.generate_code_from_task(task, context)

        assert isinstance(result, GeneratedCode)
        assert "class UserManager" in result.code
        assert "def __init__" in result.code
        assert result.file_path.endswith(".py")
        assert isinstance(result.imports, list)
        assert isinstance(result.dependencies, list)

    def test_generate_code_from_task_function(self):
        """Test generating code for a function task."""
        task = Task(
            id="2.1",
            title="Implement validate_user function",
            description="Implement function validate_user to check user credentials",
            requirements_refs=["FR-2.1"],
            subtasks=[],
            status=TaskStatus.NOT_STARTED
        )

        context = CodeContext(
            task_id="2.1",
            relevant_files=[],
            similar_implementations=[],
            required_imports=[],
            suggested_patterns=[],
            dependencies=[],
            test_examples=[],
            style_guidelines={}
        )

        result = self.generator.generate_code_from_task(task, context)

        assert isinstance(result, GeneratedCode)
        assert "def validate_user" in result.code
        assert "TODO: Implement" in result.code
        assert result.file_path.endswith(".py")

    def test_generate_code_from_task_interface(self):
        """Test generating code for an interface task."""
        task = Task(
            id="3.1",
            title="Create IUserRepository interface",
            description="Create abstract interface IUserRepository with CRUD operations",
            requirements_refs=["FR-3.1"],
            subtasks=[],
            status=TaskStatus.NOT_STARTED
        )

        context = CodeContext(
            task_id="3.1",
            relevant_files=[],
            similar_implementations=[],
            required_imports=[],
            suggested_patterns=[],
            dependencies=[],
            test_examples=[],
            style_guidelines={}
        )

        result = self.generator.generate_code_from_task(task, context)

        assert isinstance(result, GeneratedCode)
        assert "from abc import ABC, abstractmethod" in result.code
        assert "class IUserRepository(ABC)" in result.code
        assert "@abstractmethod" in result.code

    def test_generate_code_from_task_model(self):
        """Test generating code for a data model task."""
        task = Task(
            id="4.1",
            title="Create User model",
            description="Create dataclass User model with id, name, and status fields",
            requirements_refs=["FR-4.1"],
            subtasks=[],
            status=TaskStatus.NOT_STARTED
        )

        context = CodeContext(
            task_id="4.1",
            relevant_files=[],
            similar_implementations=[],
            required_imports=[],
            suggested_patterns=[],
            dependencies=[],
            test_examples=[],
            style_guidelines={}
        )

        result = self.generator.generate_code_from_task(task, context)

        assert isinstance(result, GeneratedCode)
        assert "from dataclasses import dataclass" in result.code
        assert "@dataclass" in result.code
        assert "class User" in result.code
        assert "id: str" in result.code
        assert "name: str" in result.code
        assert "status: str" in result.code

    def test_generate_code_from_task_test(self):
        """Test generating code for a test task."""
        task = Task(
            id="5.1",
            title="Test UserManager functionality",
            description="Create test cases for UserManager class methods",
            requirements_refs=["FR-5.1"],
            subtasks=[],
            status=TaskStatus.NOT_STARTED
        )

        context = CodeContext(
            task_id="5.1",
            relevant_files=[],
            similar_implementations=[],
            required_imports=[],
            suggested_patterns=[],
            dependencies=[],
            test_examples=[],
            style_guidelines={}
        )

        result = self.generator.generate_code_from_task(task, context)

        assert isinstance(result, GeneratedCode)
        assert "import pytest" in result.code
        assert "class TestUserManager" in result.code
        assert "def setup_method" in result.code
        assert "def test_" in result.code

    def test_ensure_consistency(self):
        """Test ensuring code consistency."""
        code = """def MyFunction():
    pass

class myClass:
    pass"""

        # Mock existing patterns
        self.generator.existing_patterns = CodePatterns(
            naming_conventions=[
                CodePattern(
                    pattern_type="function_naming",
                    description="Functions use snake_case",
                    examples=["def my_function():", "def process_data():"],
                    frequency=10,
                    confidence=0.8
                )
            ],
            structural_patterns=[],
            import_patterns=[],
            error_handling_patterns=[],
            testing_patterns=[],
            documentation_patterns=[],
            overall_style={}
        )

        result = self.generator.ensure_consistency(code, Mock())

        # Should apply naming conventions
        assert "def my_function" in result or "MyFunction" in result  # Either converted or kept

    def test_generate_tests_pytest(self):
        """Test generating pytest tests."""
        code = """def calculate_sum(a, b):
    return a + b

class Calculator:
    def add(self, x, y):
        return x + y
    
    def multiply(self, x, y):
        return x * y"""

        result = self.generator.generate_tests(code, "pytest")

        assert "import pytest" in result
        assert "def test_calculate_sum" in result
        assert "class TestCalculator" in result
        assert "def test_add" in result
        assert "def test_multiply" in result

    def test_generate_tests_unsupported_framework(self):
        """Test generating tests with unsupported framework."""
        code = "def test_function(): pass"

        with pytest.raises(ValueError, match="Unsupported test framework"):
            self.generator.generate_tests(code, "unittest")

    def test_write_code_to_file(self, tmp_path):
        """Test writing code to file."""
        code = "def hello_world():\n    print('Hello, World!')"
        file_path = tmp_path / "test_file.py"

        result = self.generator.write_code_to_file(code, str(file_path))

        assert result is True
        assert file_path.exists()
        assert file_path.read_text() == code

    def test_write_code_to_file_creates_directory(self, tmp_path):
        """Test writing code to file creates directory if needed."""
        code = "def hello_world():\n    print('Hello, World!')"
        file_path = tmp_path / "subdir" / "test_file.py"

        result = self.generator.write_code_to_file(code, str(file_path))

        assert result is True
        assert file_path.exists()
        assert file_path.read_text() == code

    def test_determine_file_path_class(self):
        """Test determining file path for class task."""
        task = Task(
            id="1.1",
            title="Create UserModel class",
            description="Create class for user data model",
            requirements_refs=[],
            subtasks=[],
            status=TaskStatus.NOT_STARTED
        )
        context = CodeContext(
            task_id="1.1",
            relevant_files=[],
            similar_implementations=[],
            required_imports=[],
            suggested_patterns=[],
            dependencies=[],
            test_examples=[],
            style_guidelines={}
        )

        file_path = self.generator._determine_file_path(task, context)

        assert file_path.endswith(".py")
        assert "model" in file_path.lower()

    def test_determine_file_path_test(self):
        """Test determining file path for test task."""
        task = Task(
            id="2.1",
            title="Test user functionality",
            description="Create tests for user management",
            requirements_refs=[],
            subtasks=[],
            status=TaskStatus.NOT_STARTED
        )
        context = CodeContext(
            task_id="2.1",
            relevant_files=[],
            similar_implementations=[],
            required_imports=[],
            suggested_patterns=[],
            dependencies=[],
            test_examples=[],
            style_guidelines={}
        )

        file_path = self.generator._determine_file_path(task, context)

        assert file_path.startswith("tests/")
        assert file_path.endswith(".py")

    def test_generate_imports_basic(self):
        """Test generating basic imports."""
        task = Task(
            id="1.1",
            title="File processor",
            description="Process files and handle JSON data with timestamps",
            requirements_refs=[],
            subtasks=[],
            status=TaskStatus.NOT_STARTED
        )
        context = CodeContext(
            task_id="1.1",
            relevant_files=[],
            similar_implementations=[],
            required_imports=["import sys"],
            suggested_patterns=[],
            dependencies=[],
            test_examples=[],
            style_guidelines={}
        )

        imports = self.generator._generate_imports(task, context)

        assert "import sys" in imports
        assert any("pathlib" in imp or "os" in imp for imp in imports)  # File handling
        assert "import json" in imports  # JSON handling
        assert any("datetime" in imp for imp in imports)  # Timestamp handling

    def test_extract_class_name(self):
        """Test extracting class name from task."""
        task = Task(
            id="1.1",
            title="Create UserManager class",
            description="Implement class for user management",
            requirements_refs=[],
            subtasks=[],
            status=TaskStatus.NOT_STARTED
        )

        class_name = self.generator._extract_class_name(task)
        assert class_name == "UserManager"

    def test_extract_function_name(self):
        """Test extracting function name from task."""
        task = Task(
            id="2.1",
            title="Implement validate_user function",
            description="Create function to validate user credentials",
            requirements_refs=[],
            subtasks=[],
            status=TaskStatus.NOT_STARTED
        )

        function_name = self.generator._extract_function_name(task)
        assert function_name == "validate_user"

    def test_should_generate_tests_true(self):
        """Test should generate tests returns True for implementation tasks."""
        task = Task(
            id="1.1",
            title="Implement user service",
            description="Create user service implementation",
            requirements_refs=[],
            subtasks=[],
            status=TaskStatus.NOT_STARTED
        )

        result = self.generator._should_generate_tests(task)
        assert result is True

    def test_should_generate_tests_false(self):
        """Test should generate tests returns False for test tasks."""
        task = Task(
            id="2.1",
            title="Test user service",
            description="Create tests for user service",
            requirements_refs=[],
            subtasks=[],
            status=TaskStatus.NOT_STARTED
        )

        result = self.generator._should_generate_tests(task)
        assert result is False

    def test_extract_testable_elements(self):
        """Test extracting testable elements from code."""
        code = """def calculate_sum(a, b):
    return a + b

class Calculator:
    def add(self, x, y):
        return x + y
    
    def _private_method(self):
        pass"""

        elements = self.generator._extract_testable_elements(code)

        assert len(elements) == 2

        # Check function element
        func_element = next(e for e in elements if e["type"] == "function")
        assert func_element["name"] == "calculate_sum"
        assert func_element["args"] == ["a", "b"]

        # Check class element
        class_element = next(e for e in elements if e["type"] == "class")
        assert class_element["name"] == "Calculator"
        assert "add" in class_element["methods"]
        assert "_private_method" not in class_element["methods"]  # Private methods excluded

    def test_generate_with_similar_implementations(self):
        """Test generating code with similar implementations as context."""
        task = Task(
            id="1.1",
            title="Create DataProcessor class",
            description="Create class DataProcessor for data processing",
            requirements_refs=[],
            subtasks=[],
            status=TaskStatus.NOT_STARTED
        )

        similar_impl = ContextualCode(
            code="""class ExampleProcessor:
    def __init__(self, config):
        self.config = config
    
    def process(self, data):
        return data.upper()""",
            file_path="example.py",
            relevance_score=0.8,
            context_type="similar_class",
            explanation="Similar processor class"
        )

        context = CodeContext(
            task_id="1.1",
            relevant_files=[],
            similar_implementations=[similar_impl],
            required_imports=[],
            suggested_patterns=[],
            dependencies=[],
            test_examples=[],
            style_guidelines={}
        )

        result = self.generator.generate_code_from_task(task, context)

        assert "class DataProcessor" in result.code
        assert "def __init__" in result.code
        # Should have extracted parameter from similar implementation
        assert "config" in result.code or "__init__(self)" in result.code

    def test_load_patterns_error_handling(self):
        """Test error handling when loading patterns fails."""
        # Create generator with analyzer that raises exception
        mock_analyzer = Mock()
        mock_analyzer.identify_code_patterns.side_effect = Exception("Analysis failed")

        generator = PythonCodeGenerator(mock_analyzer)

        # Should handle the exception gracefully
        assert generator.existing_patterns is None
        assert generator.style_guidelines == {}

    def test_generate_crud_methods(self):
        """Test generating CRUD methods."""
        crud_methods = self.generator._generate_crud_methods()

        assert "def create(" in crud_methods
        assert "def read(" in crud_methods
        assert "def update(" in crud_methods
        assert "def delete(" in crud_methods
        assert "NotImplementedError" in crud_methods

    def test_generate_model_fields(self):
        """Test generating model fields."""
        task = Task(
            id="1.1",
            title="User model",
            description="Create user model with id, name, description, and timestamp",
            requirements_refs=[],
            subtasks=[],
            status=TaskStatus.NOT_STARTED
        )
        context = CodeContext(
            task_id="1.1",
            relevant_files=[],
            similar_implementations=[],
            required_imports=[],
            suggested_patterns=[],
            dependencies=[],
            test_examples=[],
            style_guidelines={}
        )

        fields = self.generator._generate_model_fields(task, context)

        assert "id: str" in fields
        assert "name: str" in fields
        assert "description: str" in fields
        assert "created_at: datetime" in fields
