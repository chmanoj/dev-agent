"""Automatic test generation for new code including unit and integration tests.

This module provides comprehensive test generation capabilities that create
both unit tests and integration tests for generated code.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..interfaces.analysis_interface import ICodebaseAnalyzer
from ..models.analysis import CodeContext, ContextualCode
from ..models.results import GeneratedCode


@dataclass
class TestCase:
    """Represents a single test case."""

    name: str
    test_type: str  # 'unit', 'integration', 'functional'
    target_function: str | None
    target_class: str | None
    setup_code: str
    test_code: str
    assertions: list[str]
    mock_requirements: list[str]
    description: str


@dataclass
class TestSuite:
    """Represents a complete test suite."""

    file_path: str
    test_cases: list[TestCase]
    imports: list[str]
    fixtures: list[str]
    setup_methods: list[str]
    teardown_methods: list[str]


class AutomaticTestGenerator:
    """Generates comprehensive tests for new code automatically."""

    def __init__(self, codebase_analyzer: ICodebaseAnalyzer):
        """Initialize the automatic test generator.

        Args:
            codebase_analyzer: Analyzer for extracting codebase patterns
        """
        self.codebase_analyzer = codebase_analyzer
        self.test_patterns = self._load_existing_test_patterns()

    def generate_comprehensive_tests(
        self, primary_code: GeneratedCode, context: Any
    ) -> list[GeneratedCode]:
        """Generate comprehensive unit and integration tests.

        Args:
            primary_code: The generated code to create tests for
            context: Generation context with additional information

        Returns:
            List of generated test files
        """
        generated_tests = []

        # Parse the code to understand its structure
        code_structure = self._analyze_code_structure(primary_code.code)

        # Generate unit tests
        unit_tests = self._generate_unit_tests(code_structure, primary_code, context)
        if unit_tests:
            generated_tests.append(unit_tests)

        # Generate integration tests
        integration_tests = self._generate_integration_tests(
            code_structure, primary_code, context
        )
        if integration_tests:
            generated_tests.append(integration_tests)

        # Generate functional tests if applicable
        functional_tests = self._generate_functional_tests(
            code_structure, primary_code, context
        )
        if functional_tests:
            generated_tests.append(functional_tests)

        return generated_tests

    def generate_unit_tests(
        self, code: str, target_file: str, test_framework: str = "pytest"
    ) -> GeneratedCode:
        """Generate unit tests for specific code.

        Args:
            code: Source code to generate tests for
            target_file: Target file path for the source code
            test_framework: Testing framework to use

        Returns:
            Generated unit test code
        """
        code_structure = self._analyze_code_structure(code)
        
        # Generate test cases for each testable element
        test_cases = []
        
        for class_info in code_structure.get('classes', []):
            test_cases.extend(self._generate_class_unit_tests(class_info))
            
        for function_info in code_structure.get('functions', []):
            test_cases.extend(self._generate_function_unit_tests(function_info))

        # Create test suite
        test_suite = TestSuite(
            file_path=self._get_test_file_path(target_file),
            test_cases=test_cases,
            imports=self._generate_test_imports(code, test_framework),
            fixtures=self._generate_test_fixtures(code_structure),
            setup_methods=self._generate_setup_methods(code_structure),
            teardown_methods=self._generate_teardown_methods(code_structure),
        )

        # Generate the complete test file
        test_code = self._generate_test_file_content(test_suite, test_framework)

        return GeneratedCode(
            code=test_code,
            file_path=test_suite.file_path,
            imports=test_suite.imports,
            dependencies=["pytest", "unittest.mock"],
            tests=None,  # This is the test itself
        )

    def generate_integration_tests(
        self, code: str, target_file: str, dependencies: list[str]
    ) -> GeneratedCode:
        """Generate integration tests for code with external dependencies.

        Args:
            code: Source code to generate tests for
            target_file: Target file path for the source code
            dependencies: List of external dependencies

        Returns:
            Generated integration test code
        """
        code_structure = self._analyze_code_structure(code)
        
        # Identify integration points
        integration_points = self._identify_integration_points(code_structure, dependencies)
        
        # Generate integration test cases
        test_cases = []
        for integration_point in integration_points:
            test_cases.extend(self._generate_integration_test_cases(integration_point))

        # Create integration test suite
        test_suite = TestSuite(
            file_path=self._get_integration_test_file_path(target_file),
            test_cases=test_cases,
            imports=self._generate_integration_test_imports(dependencies),
            fixtures=self._generate_integration_fixtures(integration_points),
            setup_methods=self._generate_integration_setup_methods(integration_points),
            teardown_methods=self._generate_integration_teardown_methods(integration_points),
        )

        # Generate the complete integration test file
        test_code = self._generate_test_file_content(test_suite, "pytest")

        return GeneratedCode(
            code=test_code,
            file_path=test_suite.file_path,
            imports=test_suite.imports,
            dependencies=["pytest", "pytest-asyncio"] + dependencies,
            tests=None,
        )

    def _load_existing_test_patterns(self) -> dict[str, Any]:
        """Load existing test patterns from the codebase."""
        patterns = {
            'naming_conventions': [],
            'setup_patterns': [],
            'assertion_patterns': [],
            'mock_patterns': [],
        }

        try:
            # Analyze existing test files
            test_files = list(Path(".").glob("**/test_*.py")) + list(Path(".").glob("**/*_test.py"))
            
            for test_file in test_files[:10]:  # Limit to avoid performance issues
                try:
                    with open(test_file, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    file_patterns = self._extract_test_patterns(content)
                    self._merge_patterns(patterns, file_patterns)
                    
                except Exception:
                    continue

        except Exception:
            pass

        return patterns

    def _analyze_code_structure(self, code: str) -> dict[str, Any]:
        """Analyze code structure to understand what needs testing."""
        structure = {
            'classes': [],
            'functions': [],
            'imports': [],
            'constants': [],
            'async_functions': [],
        }

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = self._analyze_class(node)
                    structure['classes'].append(class_info)
                elif isinstance(node, ast.FunctionDef):
                    if node.name.startswith('_'):
                        continue  # Skip private functions
                    func_info = self._analyze_function(node)
                    if func_info.get('is_async'):
                        structure['async_functions'].append(func_info)
                    else:
                        structure['functions'].append(func_info)
                elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    import_info = self._analyze_import(node)
                    structure['imports'].append(import_info)
                elif isinstance(node, ast.Assign):
                    const_info = self._analyze_constant(node)
                    if const_info:
                        structure['constants'].append(const_info)

        except SyntaxError:
            pass

        return structure

    def _analyze_class(self, node: ast.ClassDef) -> dict[str, Any]:
        """Analyze a class definition for test generation."""
        methods = []
        properties = []
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if not item.name.startswith('_') or item.name in ['__init__', '__str__', '__repr__']:
                    method_info = self._analyze_function(item)
                    method_info['is_method'] = True
                    methods.append(method_info)
            elif isinstance(item, ast.AnnAssign):
                # Property or class variable
                if hasattr(item.target, 'id'):
                    properties.append({
                        'name': item.target.id,
                        'type': ast.unparse(item.annotation) if item.annotation else 'Any'
                    })

        return {
            'name': node.name,
            'methods': methods,
            'properties': properties,
            'base_classes': [ast.unparse(base) for base in node.bases],
            'decorators': [ast.unparse(dec) for dec in node.decorator_list],
            'line_number': node.lineno,
        }

    def _analyze_function(self, node: ast.FunctionDef) -> dict[str, Any]:
        """Analyze a function definition for test generation."""
        parameters = []
        for arg in node.args.args:
            param_info = {
                'name': arg.arg,
                'type': ast.unparse(arg.annotation) if arg.annotation else 'Any',
                'has_default': False,
            }
            parameters.append(param_info)

        # Check for default values
        defaults_start = len(parameters) - len(node.args.defaults)
        for i, default in enumerate(node.args.defaults):
            if defaults_start + i < len(parameters):
                parameters[defaults_start + i]['has_default'] = True
                parameters[defaults_start + i]['default_value'] = ast.unparse(default)

        return {
            'name': node.name,
            'parameters': parameters,
            'return_type': ast.unparse(node.returns) if node.returns else 'Any',
            'is_async': isinstance(node, ast.AsyncFunctionDef),
            'decorators': [ast.unparse(dec) for dec in node.decorator_list],
            'docstring': ast.get_docstring(node),
            'line_number': node.lineno,
            'complexity': self._calculate_complexity(node),
        }

    def _analyze_import(self, node: ast.Import | ast.ImportFrom) -> dict[str, Any]:
        """Analyze an import statement."""
        if isinstance(node, ast.Import):
            return {
                'type': 'import',
                'modules': [alias.name for alias in node.names],
                'aliases': [alias.asname for alias in node.names if alias.asname],
            }
        else:  # ImportFrom
            return {
                'type': 'from_import',
                'module': node.module,
                'names': [alias.name for alias in node.names],
                'aliases': [alias.asname for alias in node.names if alias.asname],
                'level': node.level,
            }

    def _analyze_constant(self, node: ast.Assign) -> dict[str, Any] | None:
        """Analyze a constant assignment."""
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name.isupper():  # Convention for constants
                return {
                    'name': name,
                    'value': ast.unparse(node.value),
                    'type': type(node.value).__name__,
                }
        return None

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1

        return complexity

    def _generate_unit_tests(
        self, code_structure: dict[str, Any], primary_code: GeneratedCode, context: Any
    ) -> GeneratedCode | None:
        """Generate unit tests for the code structure."""
        test_cases = []

        # Generate tests for classes
        for class_info in code_structure.get('classes', []):
            test_cases.extend(self._generate_class_unit_tests(class_info))

        # Generate tests for functions
        for function_info in code_structure.get('functions', []):
            test_cases.extend(self._generate_function_unit_tests(function_info))

        if not test_cases:
            return None

        # Create test suite
        test_suite = TestSuite(
            file_path=self._get_test_file_path(primary_code.file_path),
            test_cases=test_cases,
            imports=self._generate_test_imports(primary_code.code, "pytest"),
            fixtures=self._generate_test_fixtures(code_structure),
            setup_methods=[],
            teardown_methods=[],
        )

        # Generate the complete test file
        test_code = self._generate_test_file_content(test_suite, "pytest")

        return GeneratedCode(
            code=test_code,
            file_path=test_suite.file_path,
            imports=test_suite.imports,
            dependencies=["pytest", "unittest.mock"],
            tests=None,
        )

    def _generate_integration_tests(
        self, code_structure: dict[str, Any], primary_code: GeneratedCode, context: Any
    ) -> GeneratedCode | None:
        """Generate integration tests for the code structure."""
        # Identify integration points
        integration_points = self._identify_integration_points(
            code_structure, primary_code.dependencies
        )

        if not integration_points:
            return None

        test_cases = []
        for integration_point in integration_points:
            test_cases.extend(self._generate_integration_test_cases(integration_point))

        # Create integration test suite
        test_suite = TestSuite(
            file_path=self._get_integration_test_file_path(primary_code.file_path),
            test_cases=test_cases,
            imports=self._generate_integration_test_imports(primary_code.dependencies),
            fixtures=self._generate_integration_fixtures(integration_points),
            setup_methods=[],
            teardown_methods=[],
        )

        # Generate the complete integration test file
        test_code = self._generate_test_file_content(test_suite, "pytest")

        return GeneratedCode(
            code=test_code,
            file_path=test_suite.file_path,
            imports=test_suite.imports,
            dependencies=["pytest", "pytest-asyncio"] + primary_code.dependencies,
            tests=None,
        )

    def _generate_functional_tests(
        self, code_structure: dict[str, Any], primary_code: GeneratedCode, context: Any
    ) -> GeneratedCode | None:
        """Generate functional tests for end-to-end scenarios."""
        # Only generate functional tests for certain types of code
        if not self._should_generate_functional_tests(code_structure):
            return None

        test_cases = self._generate_functional_test_cases(code_structure, context)

        if not test_cases:
            return None

        test_suite = TestSuite(
            file_path=self._get_functional_test_file_path(primary_code.file_path),
            test_cases=test_cases,
            imports=self._generate_functional_test_imports(),
            fixtures=[],
            setup_methods=[],
            teardown_methods=[],
        )

        test_code = self._generate_test_file_content(test_suite, "pytest")

        return GeneratedCode(
            code=test_code,
            file_path=test_suite.file_path,
            imports=test_suite.imports,
            dependencies=["pytest", "requests", "selenium"],
            tests=None,
        )

    def _generate_class_unit_tests(self, class_info: dict[str, Any]) -> list[TestCase]:
        """Generate unit tests for a class."""
        test_cases = []

        # Test class instantiation
        test_cases.append(self._generate_instantiation_test(class_info))

        # Test each method
        for method in class_info['methods']:
            if method['name'] == '__init__':
                continue  # Already covered by instantiation test
            
            test_cases.extend(self._generate_method_tests(method, class_info['name']))

        return test_cases

    def _generate_function_unit_tests(self, function_info: dict[str, Any]) -> list[TestCase]:
        """Generate unit tests for a function."""
        test_cases = []

        # Generate basic functionality test
        test_cases.append(self._generate_basic_function_test(function_info))

        # Generate edge case tests
        test_cases.extend(self._generate_edge_case_tests(function_info))

        # Generate error case tests
        test_cases.extend(self._generate_error_case_tests(function_info))

        return test_cases

    def _generate_instantiation_test(self, class_info: dict[str, Any]) -> TestCase:
        """Generate a test for class instantiation."""
        class_name = class_info['name']
        
        # Find __init__ method to understand parameters
        init_method = None
        for method in class_info['methods']:
            if method['name'] == '__init__':
                init_method = method
                break

        if init_method and init_method['parameters']:
            # Generate test with parameters
            params = [p for p in init_method['parameters'] if p['name'] != 'self']
            param_values = [self._generate_test_value(p['type']) for p in params]
            param_str = ', '.join(param_values)
            
            setup_code = f"instance = {class_name}({param_str})"
        else:
            setup_code = f"instance = {class_name}()"

        return TestCase(
            name=f"test_{class_name.lower()}_instantiation",
            test_type="unit",
            target_function=None,
            target_class=class_name,
            setup_code=setup_code,
            test_code="# Test that instance is created successfully",
            assertions=["assert instance is not None", f"assert isinstance(instance, {class_name})"],
            mock_requirements=[],
            description=f"Test {class_name} can be instantiated",
        )

    def _generate_method_tests(self, method_info: dict[str, Any], class_name: str) -> list[TestCase]:
        """Generate tests for a class method."""
        test_cases = []
        method_name = method_info['name']

        # Basic functionality test
        test_case = TestCase(
            name=f"test_{method_name}",
            test_type="unit",
            target_function=method_name,
            target_class=class_name,
            setup_code=f"instance = {class_name}()",
            test_code=f"result = instance.{method_name}()",
            assertions=["assert result is not None"],
            mock_requirements=[],
            description=f"Test {method_name} method basic functionality",
        )
        test_cases.append(test_case)

        return test_cases

    def _generate_basic_function_test(self, function_info: dict[str, Any]) -> TestCase:
        """Generate a basic test for a function."""
        function_name = function_info['name']
        
        # Generate test parameters
        params = function_info['parameters']
        if params:
            param_values = [self._generate_test_value(p['type']) for p in params]
            param_str = ', '.join(param_values)
            test_code = f"result = {function_name}({param_str})"
        else:
            test_code = f"result = {function_name}()"

        return TestCase(
            name=f"test_{function_name}",
            test_type="unit",
            target_function=function_name,
            target_class=None,
            setup_code="# Setup test data",
            test_code=test_code,
            assertions=["assert result is not None"],
            mock_requirements=[],
            description=f"Test {function_name} basic functionality",
        )

    def _generate_edge_case_tests(self, function_info: dict[str, Any]) -> list[TestCase]:
        """Generate edge case tests for a function."""
        test_cases = []
        function_name = function_info['name']

        # Test with None values
        if function_info['parameters']:
            test_case = TestCase(
                name=f"test_{function_name}_with_none",
                test_type="unit",
                target_function=function_name,
                target_class=None,
                setup_code="# Test with None values",
                test_code=f"result = {function_name}(None)",
                assertions=["# Add appropriate assertions for None input"],
                mock_requirements=[],
                description=f"Test {function_name} with None input",
            )
            test_cases.append(test_case)

        # Test with empty values
        for param in function_info['parameters']:
            if 'str' in param['type'].lower():
                test_case = TestCase(
                    name=f"test_{function_name}_with_empty_string",
                    test_type="unit",
                    target_function=function_name,
                    target_class=None,
                    setup_code="# Test with empty string",
                    test_code=f"result = {function_name}('')",
                    assertions=["# Add appropriate assertions for empty string"],
                    mock_requirements=[],
                    description=f"Test {function_name} with empty string",
                )
                test_cases.append(test_case)
                break

        return test_cases

    def _generate_error_case_tests(self, function_info: dict[str, Any]) -> list[TestCase]:
        """Generate error case tests for a function."""
        test_cases = []
        function_name = function_info['name']

        # Test with invalid input types
        if function_info['parameters']:
            test_case = TestCase(
                name=f"test_{function_name}_invalid_input",
                test_type="unit",
                target_function=function_name,
                target_class=None,
                setup_code="# Test with invalid input",
                test_code=f"""with pytest.raises(TypeError):
    {function_name}("invalid_input")""",
                assertions=[],
                mock_requirements=[],
                description=f"Test {function_name} raises error with invalid input",
            )
            test_cases.append(test_case)

        return test_cases

    def _generate_test_value(self, type_hint: str) -> str:
        """Generate a test value for a given type hint."""
        type_hint = type_hint.lower()
        
        if 'str' in type_hint:
            return '"test_string"'
        elif 'int' in type_hint:
            return '42'
        elif 'float' in type_hint:
            return '3.14'
        elif 'bool' in type_hint:
            return 'True'
        elif 'list' in type_hint:
            return '[1, 2, 3]'
        elif 'dict' in type_hint:
            return '{"key": "value"}'
        else:
            return 'None'

    def _identify_integration_points(
        self, code_structure: dict[str, Any], dependencies: list[str]
    ) -> list[dict[str, Any]]:
        """Identify integration points that need integration testing."""
        integration_points = []

        # Check for database dependencies
        if any(dep in ['database', 'sql', 'sqlite', 'postgresql', 'mysql'] for dep in dependencies):
            integration_points.append({
                'type': 'database',
                'description': 'Database integration',
                'dependencies': [dep for dep in dependencies if 'sql' in dep.lower() or dep in ['database']],
            })

        # Check for web framework dependencies
        if any(dep in ['web_framework', 'fastapi', 'flask', 'django'] for dep in dependencies):
            integration_points.append({
                'type': 'web_api',
                'description': 'Web API integration',
                'dependencies': [dep for dep in dependencies if dep in ['web_framework', 'fastapi', 'flask', 'django']],
            })

        # Check for external service dependencies
        if any(dep in ['http', 'requests', 'httpx'] for dep in dependencies):
            integration_points.append({
                'type': 'external_service',
                'description': 'External service integration',
                'dependencies': [dep for dep in dependencies if dep in ['http', 'requests', 'httpx']],
            })

        return integration_points

    def _generate_integration_test_cases(self, integration_point: dict[str, Any]) -> list[TestCase]:
        """Generate integration test cases for an integration point."""
        test_cases = []

        if integration_point['type'] == 'database':
            test_cases.extend(self._generate_database_integration_tests(integration_point))
        elif integration_point['type'] == 'web_api':
            test_cases.extend(self._generate_web_api_integration_tests(integration_point))
        elif integration_point['type'] == 'external_service':
            test_cases.extend(self._generate_external_service_integration_tests(integration_point))

        return test_cases

    def _generate_database_integration_tests(self, integration_point: dict[str, Any]) -> list[TestCase]:
        """Generate database integration tests."""
        return [
            TestCase(
                name="test_database_connection",
                test_type="integration",
                target_function=None,
                target_class=None,
                setup_code="# Setup test database",
                test_code="# Test database connection and basic operations",
                assertions=["assert connection is not None"],
                mock_requirements=[],
                description="Test database connection and basic operations",
            )
        ]

    def _generate_web_api_integration_tests(self, integration_point: dict[str, Any]) -> list[TestCase]:
        """Generate web API integration tests."""
        return [
            TestCase(
                name="test_api_endpoint",
                test_type="integration",
                target_function=None,
                target_class=None,
                setup_code="# Setup test client",
                test_code="# Test API endpoint",
                assertions=["assert response.status_code == 200"],
                mock_requirements=[],
                description="Test API endpoint integration",
            )
        ]

    def _generate_external_service_integration_tests(self, integration_point: dict[str, Any]) -> list[TestCase]:
        """Generate external service integration tests."""
        return [
            TestCase(
                name="test_external_service_call",
                test_type="integration",
                target_function=None,
                target_class=None,
                setup_code="# Setup mock external service",
                test_code="# Test external service call",
                assertions=["assert response is not None"],
                mock_requirements=["requests_mock"],
                description="Test external service integration",
            )
        ]

    def _should_generate_functional_tests(self, code_structure: dict[str, Any]) -> bool:
        """Determine if functional tests should be generated."""
        # Generate functional tests for web applications, APIs, or CLI tools
        has_web_components = any(
            'app' in cls['name'].lower() or 'api' in cls['name'].lower() or 'server' in cls['name'].lower()
            for cls in code_structure.get('classes', [])
        )
        
        has_cli_components = any(
            'cli' in func['name'].lower() or 'main' in func['name'].lower()
            for func in code_structure.get('functions', [])
        )

        return has_web_components or has_cli_components

    def _generate_functional_test_cases(
        self, code_structure: dict[str, Any], context: Any
    ) -> list[TestCase]:
        """Generate functional test cases for end-to-end scenarios."""
        test_cases = []

        # Generate web application functional tests
        if any('app' in cls['name'].lower() for cls in code_structure.get('classes', [])):
            test_cases.append(TestCase(
                name="test_web_application_flow",
                test_type="functional",
                target_function=None,
                target_class=None,
                setup_code="# Setup test environment",
                test_code="# Test complete user workflow",
                assertions=["assert workflow_completed"],
                mock_requirements=[],
                description="Test complete web application workflow",
            ))

        return test_cases

    def _get_test_file_path(self, source_file: str) -> str:
        """Get the test file path for a source file."""
        source_path = Path(source_file)
        
        # If source is in dev_agent/, put test in tests/
        if "dev_agent" in source_path.parts:
            relative_path = Path(*source_path.parts[1:])  # Remove dev_agent/
            test_path = Path("tests") / f"test_{relative_path.stem}.py"
        else:
            test_path = source_path.parent / f"test_{source_path.stem}.py"
            
        return str(test_path)

    def _get_integration_test_file_path(self, source_file: str) -> str:
        """Get the integration test file path for a source file."""
        test_path = self._get_test_file_path(source_file)
        return test_path.replace("test_", "test_integration_")

    def _get_functional_test_file_path(self, source_file: str) -> str:
        """Get the functional test file path for a source file."""
        test_path = self._get_test_file_path(source_file)
        return test_path.replace("test_", "test_functional_")

    def _generate_test_imports(self, code: str, test_framework: str) -> list[str]:
        """Generate imports for test files."""
        imports = [f"import {test_framework}"]
        
        if test_framework == "pytest":
            imports.extend([
                "from unittest.mock import Mock, patch, MagicMock",
                "import pytest",
            ])

        # Extract imports from source code
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(f"import {alias.name}")
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [alias.name for alias in node.names]
                    imports.append(f"from {node.module} import {', '.join(names)}")
        except SyntaxError:
            pass

        return list(set(imports))  # Remove duplicates

    def _generate_test_fixtures(self, code_structure: dict[str, Any]) -> list[str]:
        """Generate pytest fixtures for the code structure."""
        fixtures = []

        # Generate fixtures for classes
        for class_info in code_structure.get('classes', []):
            fixture_name = f"{class_info['name'].lower()}_instance"
            fixture_code = f"""@pytest.fixture
def {fixture_name}():
    \"\"\"Fixture for {class_info['name']} instance.\"\"\"
    return {class_info['name']}()"""
            fixtures.append(fixture_code)

        return fixtures

    def _generate_integration_test_imports(self, dependencies: list[str]) -> list[str]:
        """Generate imports for integration tests."""
        imports = [
            "import pytest",
            "from unittest.mock import Mock, patch",
        ]

        # Add specific imports based on dependencies
        if "database" in dependencies:
            imports.extend([
                "import sqlite3",
                "from sqlalchemy import create_engine",
            ])

        if "web_framework" in dependencies or "fastapi" in dependencies:
            imports.extend([
                "from fastapi.testclient import TestClient",
                "import requests",
            ])

        return imports

    def _generate_integration_fixtures(self, integration_points: list[dict[str, Any]]) -> list[str]:
        """Generate fixtures for integration tests."""
        fixtures = []

        for point in integration_points:
            if point['type'] == 'database':
                fixtures.append("""@pytest.fixture
def test_db():
    \"\"\"Fixture for test database.\"\"\"
    # Setup test database
    yield db
    # Cleanup""")

            elif point['type'] == 'web_api':
                fixtures.append("""@pytest.fixture
def test_client():
    \"\"\"Fixture for test client.\"\"\"
    # Setup test client
    yield client
    # Cleanup""")

        return fixtures

    def _generate_functional_test_imports(self) -> list[str]:
        """Generate imports for functional tests."""
        return [
            "import pytest",
            "import requests",
            "from selenium import webdriver",
            "from selenium.webdriver.common.by import By",
        ]

    def _generate_test_file_content(self, test_suite: TestSuite, test_framework: str) -> str:
        """Generate the complete test file content."""
        content_parts = []

        # Add file header
        content_parts.append(f'"""Tests for {test_suite.file_path}."""')
        content_parts.append("")

        # Add imports
        content_parts.extend(test_suite.imports)
        content_parts.append("")

        # Add fixtures
        if test_suite.fixtures:
            content_parts.extend(test_suite.fixtures)
            content_parts.append("")

        # Add test cases
        for test_case in test_suite.test_cases:
            test_function = self._generate_test_function(test_case)
            content_parts.append(test_function)
            content_parts.append("")

        return "\n".join(content_parts)

    def _generate_test_function(self, test_case: TestCase) -> str:
        """Generate a single test function."""
        function_parts = []

        # Function signature
        if test_case.test_type == "integration" and test_case.mock_requirements:
            # Add mock decorators
            for mock_req in test_case.mock_requirements:
                function_parts.append(f"@patch('{mock_req}')")
        
        function_parts.append(f"def {test_case.name}():")
        
        # Docstring
        function_parts.append(f'    """{test_case.description}."""')
        
        # Setup code
        if test_case.setup_code.strip():
            function_parts.append(f"    {test_case.setup_code}")
        
        # Test code
        if test_case.test_code.strip():
            # Handle multi-line test code
            test_lines = test_case.test_code.split('\n')
            for line in test_lines:
                if line.strip():
                    function_parts.append(f"    {line}")
        
        # Assertions
        for assertion in test_case.assertions:
            function_parts.append(f"    {assertion}")

        # If no assertions, add a placeholder
        if not test_case.assertions and not test_case.test_code.strip():
            function_parts.append("    assert True  # TODO: Implement test")

        return "\n".join(function_parts)

    def _extract_test_patterns(self, content: str) -> dict[str, Any]:
        """Extract test patterns from existing test code."""
        patterns = {
            'naming_conventions': [],
            'setup_patterns': [],
            'assertion_patterns': [],
            'mock_patterns': [],
        }

        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                    # Extract naming pattern
                    patterns['naming_conventions'].append(node.name)
                    
                    # Extract setup patterns (look for common setup code)
                    for stmt in node.body[:3]:  # Check first few statements
                        if isinstance(stmt, ast.Assign):
                            patterns['setup_patterns'].append(ast.unparse(stmt))

        except SyntaxError:
            pass

        return patterns

    def _merge_patterns(self, existing: dict[str, Any], new: dict[str, Any]) -> None:
        """Merge new patterns into existing patterns."""
        for key, value in new.items():
            if key in existing:
                existing[key].extend(value)