"""Python code generator for implementing tasks with pattern consistency."""

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..interfaces.analysis_interface import ICodebaseAnalyzer
from ..interfaces.generation_interface import IPythonCodeGenerator
from ..models.analysis import CodeContext, CodePattern, CodePatterns, ContextualCode
from ..models.documents import Task
from ..models.indexing import ASTIndex
from ..models.results import GeneratedCode

# Utility functions are defined at the end of this file


@dataclass
class StyleGuideline:
    """Style guideline extracted from existing code."""

    category: str
    rule: str
    examples: list[str]
    confidence: float


class PythonCodeGenerator(IPythonCodeGenerator):
    """Generates Python code that maintains consistency with existing codebase patterns."""

    def __init__(self, codebase_analyzer: ICodebaseAnalyzer):
        """Initialize the Python code generator.

        Args:
            codebase_analyzer: Analyzer for extracting codebase patterns
        """
        self.codebase_analyzer = codebase_analyzer
        self.existing_patterns: CodePatterns | None = None
        self.style_guidelines: dict[str, Any] = {}
        self._load_patterns()

    def _load_patterns(self) -> None:
        """Load existing patterns from the codebase."""
        try:
            self.existing_patterns = self.codebase_analyzer.identify_code_patterns()
            self.style_guidelines = (
                self.existing_patterns.overall_style if self.existing_patterns else {}
            )
        except Exception as e:
            print(f"Warning: Could not load existing patterns: {e}")
            self.existing_patterns = None
            self.style_guidelines = {}

    def analyze_existing_patterns(self) -> CodePatterns:
        """Analyze existing codebase patterns for consistency.

        Returns:
            Detected code patterns and conventions
        """
        if self.existing_patterns is None:
            self._load_patterns()

        return self.existing_patterns or CodePatterns(
            naming_conventions=[],
            structural_patterns=[],
            import_patterns=[],
            error_handling_patterns=[],
            testing_patterns=[],
            documentation_patterns=[],
            overall_style={},
        )

    def generate_code_from_task(
        self, task: Task, context: CodeContext
    ) -> GeneratedCode:
        """Generate Python code for a specific task.

        Args:
            task: Task to implement
            context: Code context with relevant information

        Returns:
            Generated code with metadata
        """
        # Determine target file path
        file_path = self._determine_file_path(task, context)

        # Generate imports based on context and patterns
        imports = self._generate_imports(task, context)

        # Generate main code implementation
        code = self._generate_implementation(task, context)

        # Apply consistency checks
        code = self._apply_style_consistency(code, context)

        # Generate dependencies list
        dependencies = self._extract_dependencies(task, context)

        # Generate tests if requested
        tests = None
        if self._should_generate_tests(task):
            tests = self.generate_tests(code, "pytest")

        return GeneratedCode(
            code=code,
            file_path=file_path,
            imports=imports,
            dependencies=dependencies,
            tests=tests,
        )

    def ensure_consistency(self, new_code: str, existing_codebase: ASTIndex) -> str:
        """Ensure new code is consistent with existing patterns.

        Args:
            new_code: Generated code to check
            existing_codebase: Index of existing codebase

        Returns:
            Code adjusted for consistency
        """
        if not self.existing_patterns:
            return new_code

        # Apply naming convention consistency
        new_code = self._apply_naming_conventions(new_code)

        # Apply structural pattern consistency
        new_code = self._apply_structural_patterns(new_code)

        # Apply import pattern consistency
        new_code = self._apply_import_patterns(new_code)

        # Apply documentation pattern consistency
        new_code = self._apply_documentation_patterns(new_code)

        return new_code

    def generate_tests(self, code: str, test_framework: str = "pytest") -> str:
        """Generate tests for the given code.

        Args:
            code: Code to generate tests for
            test_framework: Testing framework to use

        Returns:
            Generated test code
        """
        if test_framework.lower() != "pytest":
            raise ValueError(f"Unsupported test framework: {test_framework}")

        # Parse the code to extract testable elements
        testable_elements = self._extract_testable_elements(code)

        # Generate test imports
        test_imports = self._generate_test_imports(code)

        # Generate test cases
        test_cases = self._generate_test_cases(testable_elements)

        # Combine into complete test file
        test_code = self._combine_test_components(test_imports, test_cases)

        return test_code

    def write_code_to_file(self, code: str, file_path: str) -> bool:
        """Write generated code to a file.

        Args:
            code: Code to write
            file_path: Target file path

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            # Write code to file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)

            return True
        except Exception as e:
            print(f"Error writing code to {file_path}: {e}")
            return False

    # Private helper methods

    def _determine_file_path(self, task: Task, context: CodeContext) -> str:
        """Determine the appropriate file path for the task implementation."""
        # Extract module/component from task description
        task_desc_lower = task.description.lower()
        task_title_lower = task.title.lower()

        # Look for explicit file path hints in task
        if "in file" in task_desc_lower or "to file" in task_desc_lower:
            # Try to extract file path from description
            file_match = re.search(r"(?:in|to)\s+file\s+([^\s]+)", task_desc_lower)
            if file_match:
                return file_match.group(1)

        # Determine from task title and context
        title_words = re.findall(r"\b\w+\b", task_title_lower)
        desc_words = re.findall(r"\b\w+\b", task_desc_lower)
        all_words = title_words + desc_words

        # Check if it's a test file
        if any(word in all_words for word in ["test", "testing"]):
            return f"tests/test_{task.id.replace('.', '_')}.py"

        # Check for specific component types
        if any(word in all_words for word in ["model", "data", "dataclass"]):
            return f"dev_agent/models/{task.id.replace('.', '_')}.py"
        elif any(word in all_words for word in ["interface", "api", "abstract"]):
            return f"dev_agent/interfaces/{task.id.replace('.', '_')}.py"
        elif any(word in all_words for word in ["generator", "generation"]):
            return f"dev_agent/generation/{task.id.replace('.', '_')}.py"
        elif any(word in all_words for word in ["workflow", "manager"]):
            return f"dev_agent/workflow/{task.id.replace('.', '_')}.py"

        # Default to main module
        return f"dev_agent/{task.id.replace('.', '_')}.py"

    def _generate_imports(self, task: Task, context: CodeContext) -> list[str]:
        """Generate appropriate imports for the task."""
        imports = []

        # Add required imports from context
        imports.extend(context.required_imports)

        # Add standard library imports based on task type
        task_desc_lower = task.description.lower()

        if any(keyword in task_desc_lower for keyword in ["file", "path", "directory"]):
            imports.extend(["import os", "from pathlib import Path"])

        if any(keyword in task_desc_lower for keyword in ["json", "serialize"]):
            imports.append("import json")

        if any(keyword in task_desc_lower for keyword in ["date", "time"]):
            imports.extend(["from datetime import datetime", "import time"])

        if any(keyword in task_desc_lower for keyword in ["type", "typing"]):
            imports.append("from typing import List, Dict, Any, Optional")

        if any(keyword in task_desc_lower for keyword in ["dataclass", "model"]):
            imports.append("from dataclasses import dataclass")

        # Add imports based on existing patterns
        if self.existing_patterns and self.existing_patterns.import_patterns:
            for pattern in self.existing_patterns.import_patterns:
                if pattern.confidence > 0.7:
                    imports.extend(pattern.examples[:2])  # Add top examples

        # Remove duplicates while preserving order
        seen = set()
        unique_imports = []
        for imp in imports:
            if imp not in seen:
                seen.add(imp)
                unique_imports.append(imp)

        return unique_imports

    def _generate_implementation(self, task: Task, context: CodeContext) -> str:
        """Generate the main implementation code for the task."""
        # Start with docstring and imports
        code_parts = []

        # Add module docstring
        module_docstring = self._generate_module_docstring(task)
        code_parts.append(module_docstring)

        # Add imports
        imports = self._generate_imports(task, context)
        if imports:
            code_parts.append("\n".join(imports))
            code_parts.append("")  # Empty line after imports

        # Generate main implementation based on task type
        implementation = self._generate_task_specific_code(task, context)
        code_parts.append(implementation)

        return "\n".join(code_parts)

    def _generate_module_docstring(self, task: Task) -> str:
        """Generate module-level docstring."""
        return f'"""{task.title}.\n\n{task.description}\n"""'

    def _generate_task_specific_code(self, task: Task, context: CodeContext) -> str:
        """Generate code specific to the task type."""
        task_desc_lower = task.description.lower()
        task_title_lower = task.title.lower()

        # Determine code generation strategy based on task content
        # Check for specific patterns first, then more general ones
        if any(keyword in task_desc_lower for keyword in ["dataclass"]) or any(
            keyword in task_title_lower for keyword in ["model"]
        ):
            return self._generate_model_code(task, context)
        elif any(
            keyword in task_desc_lower for keyword in ["interface", "abstract"]
        ) or any(keyword in task_title_lower for keyword in ["interface"]):
            return self._generate_interface_code(task, context)
        elif any(keyword in task_desc_lower for keyword in ["test", "testing"]) or any(
            keyword in task_title_lower for keyword in ["test"]
        ):
            return self._generate_test_code(task, context)
        elif any(keyword in task_desc_lower for keyword in ["class"]) or any(
            keyword in task_title_lower for keyword in ["class"]
        ):
            return self._generate_class_code(task, context)
        elif any(
            keyword in task_desc_lower for keyword in ["function", "method"]
        ) or any(keyword in task_title_lower for keyword in ["function", "implement"]):
            return self._generate_function_code(task, context)
        else:
            # Generic implementation
            return self._generate_generic_code(task, context)

    def _generate_class_code(self, task: Task, context: CodeContext) -> str:
        """Generate class implementation code."""
        # Extract class name from task
        class_name = self._extract_class_name(task)

        # Determine base classes from context
        base_classes = self._determine_base_classes(task, context)
        base_class_str = f"({', '.join(base_classes)})" if base_classes else ""

        # Generate class structure
        code_parts = [f"class {class_name}{base_class_str}:"]

        # Add class docstring
        class_docstring = self._generate_class_docstring(task)
        code_parts.append(f'    """{class_docstring}"""')
        code_parts.append("")

        # Add __init__ method
        init_method = self._generate_init_method(task, context)
        code_parts.append(init_method)

        # Add other methods based on task requirements
        methods = self._generate_class_methods(task, context)
        for method in methods:
            code_parts.append("")
            code_parts.append(method)

        return "\n".join(code_parts)

    def _generate_function_code(self, task: Task, context: CodeContext) -> str:
        """Generate standalone function implementation."""
        function_name = self._extract_function_name(task)
        parameters = self._determine_function_parameters(task, context)
        return_type = self._determine_return_type(task, context)

        # Generate function signature
        param_str = ", ".join(parameters) if parameters else ""
        return_annotation = f" -> {return_type}" if return_type else ""

        code_parts = [f"def {function_name}({param_str}){return_annotation}:"]

        # Add function docstring
        func_docstring = self._generate_function_docstring(
            task, parameters, return_type
        )
        code_parts.append(f'    """{func_docstring}"""')

        # Add implementation
        implementation = self._generate_function_body(task, context)
        code_parts.append(implementation)

        return "\n".join(code_parts)

    def _generate_interface_code(self, task: Task, context: CodeContext) -> str:
        """Generate interface/abstract class code."""
        interface_name = self._extract_class_name(task)

        code_parts = [
            "from abc import ABC, abstractmethod",
            "",
            f"class {interface_name}(ABC):",
        ]

        # Add interface docstring
        interface_docstring = self._generate_class_docstring(task)
        code_parts.append(f'    """{interface_docstring}"""')
        code_parts.append("")

        # Generate abstract methods
        methods = self._generate_abstract_methods(task, context)
        for method in methods:
            code_parts.append(method)
            code_parts.append("")

        return "\n".join(code_parts)

    def _generate_test_code(self, task: Task, context: CodeContext) -> str:
        """Generate test class code."""
        test_class_name = self._extract_test_class_name(task)

        code_parts = ["import pytest", "", f"class {test_class_name}:"]

        # Add test class docstring
        test_docstring = f"Test cases for {task.title.replace('test', '').strip()}."
        code_parts.append(f'    """{test_docstring}"""')
        code_parts.append("")

        # Generate test methods
        test_methods = self._generate_test_methods(task, context)
        for method in test_methods:
            code_parts.append(method)
            code_parts.append("")

        return "\n".join(code_parts)

    def _generate_model_code(self, task: Task, context: CodeContext) -> str:
        """Generate data model code."""
        model_name = self._extract_class_name(task)

        code_parts = [
            "from dataclasses import dataclass",
            "from typing import List, Dict, Any, Optional",
            "",
            "@dataclass",
            f"class {model_name}:",
        ]

        # Add model docstring
        model_docstring = self._generate_class_docstring(task)
        code_parts.append(f'    """{model_docstring}"""')

        # Generate fields
        fields = self._generate_model_fields(task, context)
        for field in fields:
            code_parts.append(f"    {field}")

        return "\n".join(code_parts)

    def _generate_generic_code(self, task: Task, context: CodeContext) -> str:
        """Generate generic implementation code."""
        # Try to infer what to generate from similar implementations
        if context.similar_implementations:
            # Use the most relevant similar implementation as a template
            template = context.similar_implementations[0]
            return self._adapt_template_code(template, task, context)

        # Fallback to basic structure
        return f"""# TODO: Implement {task.title}
# {task.description}

def placeholder_implementation():
    \"\"\"Placeholder implementation for {task.title}.\"\"\"
    raise NotImplementedError("Implementation pending")
"""

    def _apply_style_consistency(self, code: str, context: CodeContext) -> str:
        """Apply style consistency based on existing patterns."""
        if not self.existing_patterns:
            return code

        # Apply naming conventions
        code = self._apply_naming_conventions(code)

        # Apply indentation consistency
        code = apply_indentation_consistency(code)

        # Apply line length consistency
        code = apply_line_length_consistency(code)

        return code

    def _apply_naming_conventions(self, code: str) -> str:
        """Apply naming convention consistency."""
        if not self.existing_patterns or not self.existing_patterns.naming_conventions:
            return code

        # Get the most confident naming patterns
        naming_patterns = [
            p for p in self.existing_patterns.naming_conventions if p.confidence > 0.7
        ]

        for pattern in naming_patterns:
            if pattern.pattern_type == "function_naming":
                # Apply function naming patterns
                code = self._apply_function_naming(code, pattern)
            elif pattern.pattern_type == "class_naming":
                # Apply class naming patterns
                code = self._apply_class_naming(code, pattern)
            elif pattern.pattern_type == "variable_naming":
                # Apply variable naming patterns
                code = self._apply_variable_naming(code, pattern)

        return code

    def _apply_structural_patterns(self, code: str) -> str:
        """Apply structural pattern consistency."""
        if not self.existing_patterns or not self.existing_patterns.structural_patterns:
            return code

        # Apply common structural patterns
        for pattern in self.existing_patterns.structural_patterns:
            if pattern.confidence > 0.7:
                if "error_handling" in pattern.description.lower():
                    code = self._apply_error_handling_pattern(code, pattern)
                elif "logging" in pattern.description.lower():
                    code = self._apply_logging_pattern(code, pattern)

        return code

    def _apply_import_patterns(self, code: str) -> str:
        """Apply import pattern consistency."""
        if not self.existing_patterns or not self.existing_patterns.import_patterns:
            return code

        lines = code.split("\n")
        import_lines = []
        other_lines = []

        # Separate imports from other code
        in_imports = True
        for line in lines:
            if line.strip() == "" or line.startswith('"""') or line.startswith("'''"):
                if in_imports:
                    import_lines.append(line)
                else:
                    other_lines.append(line)
            elif line.startswith("import ") or line.startswith("from "):
                import_lines.append(line)
            else:
                in_imports = False
                other_lines.append(line)

        # Apply import ordering patterns
        import_lines = sort_imports_by_pattern(import_lines)

        return "\n".join(import_lines + other_lines)

    def _apply_documentation_patterns(self, code: str) -> str:
        """Apply documentation pattern consistency."""
        if (
            not self.existing_patterns
            or not self.existing_patterns.documentation_patterns
        ):
            return code

        # Apply docstring formatting patterns
        for pattern in self.existing_patterns.documentation_patterns:
            if pattern.confidence > 0.7:
                if "docstring_style" in pattern.description.lower():
                    code = self._apply_docstring_style(code, pattern)

        return code

    def _extract_dependencies(self, task: Task, context: CodeContext) -> list[str]:
        """Extract dependencies for the generated code."""
        dependencies = []

        # Add explicit dependencies from context
        dependencies.extend(context.dependencies)

        # Extract dependencies from task description
        task_desc = task.description.lower()

        if "database" in task_desc or "sql" in task_desc:
            dependencies.append("database")
        if "web" in task_desc or "http" in task_desc:
            dependencies.append("web_framework")
        if "test" in task_desc:
            dependencies.append("pytest")
        if "json" in task_desc:
            dependencies.append("json")

        return list(set(dependencies))  # Remove duplicates

    def _should_generate_tests(self, task: Task) -> bool:
        """Determine if tests should be generated for this task."""
        # Don't generate tests for test tasks themselves
        if "test" in task.title.lower() or "testing" in task.description.lower():
            return False

        # Generate tests for implementation tasks
        return any(
            keyword in task.description.lower()
            for keyword in ["implement", "create", "build", "develop"]
        )

    def _extract_testable_elements(self, code: str) -> list[dict[str, Any]]:
        """Extract testable elements from code."""
        testable_elements = []

        try:
            tree = ast.parse(code)

            # Track which functions are class methods
            class_methods = set()

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = []
                    for item in node.body:
                        if isinstance(
                            item, ast.FunctionDef
                        ) and not item.name.startswith("_"):
                            methods.append(item.name)
                            class_methods.add(item.name)

                    testable_elements.append(
                        {"type": "class", "name": node.name, "methods": methods}
                    )

            # Add standalone functions (not class methods)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if (
                        not node.name.startswith("_") and node.name not in class_methods
                    ):  # Skip private methods and class methods
                        testable_elements.append(
                            {
                                "type": "function",
                                "name": node.name,
                                "args": [arg.arg for arg in node.args.args],
                                "returns": getattr(node.returns, "id", None)
                                if node.returns
                                else None,
                            }
                        )

        except SyntaxError:
            # If code can't be parsed, return empty list
            pass

        return testable_elements

    def _generate_test_imports(self, code: str) -> list[str]:
        """Generate test imports based on the code being tested."""
        imports = ["import pytest"]

        # Extract module imports from the original code
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(f"import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        names = [alias.name for alias in node.names]
                        imports.append(f"from {node.module} import {', '.join(names)}")
        except SyntaxError:
            pass

        return imports

    def _generate_test_cases(
        self, testable_elements: list[dict[str, Any]]
    ) -> list[str]:
        """Generate test cases for testable elements."""
        test_cases = []

        for element in testable_elements:
            if element["type"] == "function":
                test_case = self._generate_function_test(element)
                test_cases.append(test_case)
            elif element["type"] == "class":
                test_case = self._generate_class_test(element)
                test_cases.append(test_case)

        return test_cases

    def _generate_function_test(self, func_info: dict[str, Any]) -> str:
        """Generate test case for a function."""
        func_name = func_info["name"]
        test_name = f"test_{func_name}"

        return f"""def {test_name}():
    \"\"\"Test {func_name} function.\"\"\"
    # TODO: Implement test for {func_name}
    # Add test setup, execution, and assertions
    assert True  # Placeholder assertion"""

    def _generate_class_test(self, class_info: dict[str, Any]) -> str:
        """Generate test case for a class."""
        class_name = class_info["name"]
        test_class_name = f"Test{class_name}"

        test_methods = []
        for method in class_info["methods"]:
            test_method = f"""    def test_{method}(self):
        \"\"\"Test {method} method.\"\"\"
        # TODO: Implement test for {method}
        assert True  # Placeholder assertion"""
            test_methods.append(test_method)

        methods_code = (
            "\n\n".join(test_methods)
            if test_methods
            else """    def test_placeholder(self):
        \"\"\"Placeholder test.\"\"\"
        assert True"""
        )

        return f"""class {test_class_name}:
    \"\"\"Test cases for {class_name}.\"\"\"

{methods_code}"""

    def _combine_test_components(
        self, imports: list[str], test_cases: list[str]
    ) -> str:
        """Combine test components into complete test file."""
        components = []

        # Add imports
        if imports:
            components.append("\n".join(imports))
            components.append("")

        # Add test cases
        components.extend(test_cases)

        return "\n\n".join(components)

    # Additional helper methods for code generation

    def _extract_class_name(self, task: Task) -> str:
        """Extract class name from task."""
        # Look for class name in title or description
        title_words = task.title.split()
        desc_words = task.description.split()

        # First try to find explicit class names (capitalized words)
        for words in [title_words, desc_words]:
            for word in words:
                if word[0].isupper() and word.lower() not in [
                    "create",
                    "implement",
                    "class",
                    "interface",
                    "model",
                    "test",
                ]:
                    return word

        # Common patterns for class names
        for words in [title_words, desc_words]:
            for i, word in enumerate(words):
                if word.lower() in ["class", "create", "implement"]:
                    if i + 1 < len(words):
                        next_word = words[i + 1]
                        if next_word.isalpha():
                            return to_pascal_case(next_word)

        # Fallback: use task ID
        return to_pascal_case(task.id.replace(".", "_"))

    def _extract_function_name(self, task: Task) -> str:
        """Extract function name from task."""
        # Look for function name in title or description
        title_words = task.title.split()
        desc_words = task.description.split()

        # First try to find explicit function names (snake_case or camelCase)
        for words in [title_words, desc_words]:
            for word in words:
                if "_" in word or (
                    word.islower()
                    and word
                    not in [
                        "function",
                        "method",
                        "implement",
                        "create",
                        "to",
                        "for",
                        "with",
                        "and",
                        "the",
                    ]
                ):
                    return to_snake_case(word)

        # Common patterns for function names
        for words in [title_words, desc_words]:
            for i, word in enumerate(words):
                if word.lower() in ["function", "method", "implement", "create"]:
                    if i + 1 < len(words):
                        next_word = words[i + 1]
                        if next_word.isalpha():
                            return to_snake_case(next_word)

        # Fallback: use task ID
        return to_snake_case(task.id.replace(".", "_"))

    def _extract_test_class_name(self, task: Task) -> str:
        """Extract test class name from task."""
        base_name = self._extract_class_name(task)
        if not base_name.startswith("Test"):
            return f"Test{base_name}"
        return base_name

    def _determine_base_classes(self, task: Task, context: CodeContext) -> list[str]:
        """Determine base classes for a class."""
        base_classes = []

        # Check task description for inheritance hints
        desc_lower = task.description.lower()

        if "interface" in desc_lower or "abstract" in desc_lower:
            base_classes.append("ABC")
        elif "exception" in desc_lower or "error" in desc_lower:
            base_classes.append("Exception")

        # Check context for suggested patterns
        for pattern in context.suggested_patterns:
            if "inheritance" in pattern.description.lower():
                # Extract base class from pattern examples
                for example in pattern.examples:
                    if "class" in example and "(" in example:
                        match = re.search(r"class\s+\w+\(([^)]+)\)", example)
                        if match:
                            base_classes.append(match.group(1).strip())

        return base_classes

    def _generate_class_docstring(self, task: Task) -> str:
        """Generate class docstring."""
        return f"{task.title}.\n\n{task.description}"

    def _generate_init_method(self, task: Task, context: CodeContext) -> str:
        """Generate __init__ method for a class."""
        # Determine parameters from context
        params = self._determine_init_parameters(task, context)
        param_str = ", ".join(params) if params else ""

        init_parts = [f"    def __init__(self{', ' + param_str if param_str else ''}):"]
        init_parts.append(
            f'        """Initialize the {self._extract_class_name(task)}."""'
        )

        # Generate parameter assignments
        for param in params:
            if ":" in param:
                param_name = param.split(":")[0].strip()
            else:
                param_name = param
            init_parts.append(f"        self.{param_name} = {param_name}")

        return "\n".join(init_parts)

    def _determine_init_parameters(self, task: Task, context: CodeContext) -> list[str]:
        """Determine __init__ parameters from context."""
        params = []

        # Look for parameter hints in similar implementations
        for impl in context.similar_implementations:
            if "__init__" in impl.code:
                # Extract parameters from similar __init__ methods
                init_match = re.search(r"def __init__\(self,([^)]*)\)", impl.code)
                if init_match:
                    param_str = init_match.group(1).strip()
                    if param_str:
                        params.extend([p.strip() for p in param_str.split(",")])

        # Remove duplicates and limit to reasonable number
        unique_params = []
        seen = set()
        for param in params:
            param_name = param.split(":")[0].strip()
            if param_name not in seen:
                seen.add(param_name)
                unique_params.append(param)

        return unique_params[:5]  # Limit to 5 parameters

    def _generate_class_methods(self, task: Task, context: CodeContext) -> list[str]:
        """Generate class methods based on task requirements."""
        methods = []

        # Generate methods based on task description
        desc_lower = task.description.lower()

        if "crud" in desc_lower or "create" in desc_lower:
            methods.append(self._generate_crud_methods())

        if "process" in desc_lower or "handle" in desc_lower:
            methods.append(self._generate_process_method(task))

        # Generate methods based on similar implementations
        for impl in context.similar_implementations:
            method_names = re.findall(r"def (\w+)\(", impl.code)
            for method_name in method_names:
                if method_name not in ["__init__", "__str__", "__repr__"]:
                    method_code = self._generate_method_stub(method_name, task)
                    methods.append(method_code)
                    break  # Only add one method from each similar implementation

        return methods[:3]  # Limit to 3 methods

    def _generate_crud_methods(self) -> str:
        """Generate basic CRUD methods."""
        return """    def create(self, data: Dict[str, Any]) -> bool:
        \"\"\"Create a new record.\"\"\"
        # TODO: Implement create logic
        raise NotImplementedError("Create method not implemented")
    
    def read(self, id: str) -> Optional[Dict[str, Any]]:
        \"\"\"Read a record by ID.\"\"\"
        # TODO: Implement read logic
        raise NotImplementedError("Read method not implemented")
    
    def update(self, id: str, data: Dict[str, Any]) -> bool:
        \"\"\"Update an existing record.\"\"\"
        # TODO: Implement update logic
        raise NotImplementedError("Update method not implemented")
    
    def delete(self, id: str) -> bool:
        \"\"\"Delete a record by ID.\"\"\"
        # TODO: Implement delete logic
        raise NotImplementedError("Delete method not implemented")"""

    def _generate_process_method(self, task: Task) -> str:
        """Generate a process method."""
        method_name = "process"
        return f"""    def {method_name}(self, data: Any) -> Any:
        \"\"\"Process the given data.\"\"\"
        # TODO: Implement {method_name} logic for {task.title}
        raise NotImplementedError("{method_name} method not implemented")"""

    def _generate_method_stub(self, method_name: str, task: Task) -> str:
        """Generate a method stub."""
        return f"""    def {method_name}(self) -> None:
        \"\"\"Execute {method_name} operation.\"\"\"
        # TODO: Implement {method_name} for {task.title}
        raise NotImplementedError("{method_name} method not implemented")"""

    def _determine_function_parameters(
        self, task: Task, context: CodeContext
    ) -> list[str]:
        """Determine function parameters from context."""
        params = []

        # Look for parameter hints in similar implementations
        for impl in context.similar_implementations:
            func_matches = re.findall(r"def \w+\(([^)]*)\)", impl.code)
            for match in func_matches:
                if match.strip() and match.strip() != "self":
                    param_list = [p.strip() for p in match.split(",")]
                    params.extend(param_list)

        # Remove duplicates and 'self'
        unique_params = []
        seen = set()
        for param in params:
            param_name = param.split(":")[0].strip()
            if param_name not in seen and param_name != "self":
                seen.add(param_name)
                unique_params.append(param)

        return unique_params[:3]  # Limit to 3 parameters

    def _determine_return_type(self, task: Task, context: CodeContext) -> str | None:
        """Determine function return type from context."""
        # Look for return type hints in similar implementations
        for impl in context.similar_implementations:
            return_matches = re.findall(r"def \w+\([^)]*\)\s*->\s*([^:]+):", impl.code)
            if return_matches:
                return return_matches[0].strip()

        # Default return types based on task description
        desc_lower = task.description.lower()
        if "bool" in desc_lower or "true" in desc_lower or "false" in desc_lower:
            return "bool"
        elif "list" in desc_lower:
            return "List[Any]"
        elif "dict" in desc_lower:
            return "Dict[str, Any]"
        elif "string" in desc_lower or "str" in desc_lower:
            return "str"
        elif "int" in desc_lower or "number" in desc_lower:
            return "int"

        return None

    def _generate_function_docstring(
        self, task: Task, parameters: list[str], return_type: str | None
    ) -> str:
        """Generate function docstring."""
        docstring_parts = [f"{task.title}.", "", f"{task.description}"]

        if parameters:
            docstring_parts.extend(["", "Args:"])
            for param in parameters:
                param_name = param.split(":")[0].strip()
                docstring_parts.append(f"    {param_name}: Parameter description")

        if return_type:
            docstring_parts.extend(
                ["", "Returns:", f"    {return_type}: Return value description"]
            )

        return "\n    ".join(docstring_parts)

    def _generate_function_body(self, task: Task, context: CodeContext) -> str:
        """Generate function body implementation."""
        # Try to adapt from similar implementations
        if context.similar_implementations:
            template = context.similar_implementations[0]
            return self._adapt_function_template(template, task)

        # Generate basic implementation
        return f"""    # TODO: Implement {task.title}
    # {task.description}
    raise NotImplementedError("Function implementation pending")"""

    def _generate_abstract_methods(self, task: Task, context: CodeContext) -> list[str]:
        """Generate abstract methods for an interface."""
        methods = []

        # Extract method names from task description
        desc_words = task.description.lower().split()
        method_keywords = [
            "create",
            "read",
            "update",
            "delete",
            "process",
            "handle",
            "execute",
            "run",
        ]

        for keyword in method_keywords:
            if keyword in desc_words:
                method_code = f"""    @abstractmethod
    def {keyword}(self) -> None:
        \"\"\"Abstract method for {keyword} operation.\"\"\"
        pass"""
                methods.append(method_code)

        # If no methods found, add a generic one
        if not methods:
            methods.append("""    @abstractmethod
    def execute(self) -> None:
        \"\"\"Abstract method for execution.\"\"\"
        pass""")

        return methods

    def _generate_test_methods(self, task: Task, context: CodeContext) -> list[str]:
        """Generate test methods for a test class."""
        methods = []

        # Generate setup method
        setup_method = """    def setup_method(self):
        \"\"\"Set up test fixtures before each test method.\"\"\"
        # TODO: Add test setup code
        pass"""
        methods.append(setup_method)

        # Generate basic test method
        test_method = f"""    def test_{to_snake_case(task.title.replace("test", "").strip())}(self):
        \"\"\"Test the main functionality.\"\"\"
        # TODO: Implement test logic
        assert True  # Placeholder assertion"""
        methods.append(test_method)

        return methods

    def _generate_model_fields(self, task: Task, context: CodeContext) -> list[str]:
        """Generate fields for a data model."""
        fields = []

        # Extract field hints from task description
        desc_lower = task.description.lower()

        # Common field patterns
        if "id" in desc_lower:
            fields.append("id: str")
        if "name" in desc_lower:
            fields.append("name: str")
        if "description" in desc_lower:
            fields.append("description: str")
        if "timestamp" in desc_lower or "time" in desc_lower:
            fields.append("created_at: datetime")
        if "status" in desc_lower:
            fields.append("status: str")

        # If no fields found, add generic ones
        if not fields:
            fields = ["id: str", "data: Dict[str, Any]"]

        return fields

    def _adapt_template_code(
        self, template: ContextualCode, task: Task, context: CodeContext
    ) -> str:
        """Adapt template code for the current task."""
        adapted_code = template.code

        # Replace placeholder names with task-specific names
        class_name = self._extract_class_name(task)
        function_name = self._extract_function_name(task)

        # Simple replacements
        adapted_code = re.sub(r"class\s+\w+", f"class {class_name}", adapted_code)
        adapted_code = re.sub(r"def\s+\w+\(", f"def {function_name}(", adapted_code)

        # Add task-specific comments
        adapted_code = f"# Adapted from {template.file_path}\n# {task.description}\n\n{adapted_code}"

        return adapted_code

    def _adapt_function_template(self, template: ContextualCode, task: Task) -> str:
        """Adapt function template for the current task."""
        # Extract function body from template
        lines = template.code.split("\n")
        body_lines = []
        in_function = False

        for line in lines:
            if line.strip().startswith("def "):
                in_function = True
                continue
            elif in_function and line.strip() and not line.startswith(" "):
                break
            elif in_function:
                body_lines.append(line)

        if body_lines:
            return "\n".join(body_lines)
        else:
            return f"""    # TODO: Implement {task.title}
    # {task.description}
    raise NotImplementedError("Function implementation pending")"""

    # Style consistency helper methods

    def _apply_function_naming(self, code: str, pattern: CodePattern) -> str:
        """Apply function naming pattern."""
        # Extract naming style from pattern examples
        if "snake_case" in pattern.description.lower():
            # Convert function names to snake_case
            code = re.sub(
                r"def ([A-Z][a-zA-Z]*)\(",
                lambda m: f"def {to_snake_case(m.group(1))}(",
                code,
            )

        return code

    def _apply_class_naming(self, code: str, pattern: CodePattern) -> str:
        """Apply class naming pattern."""
        # Extract naming style from pattern examples
        if (
            "pascal_case" in pattern.description.lower()
            or "camel_case" in pattern.description.lower()
        ):
            # Convert class names to PascalCase
            code = re.sub(
                r"class ([a-z][a-zA-Z]*)",
                lambda m: f"class {to_pascal_case(m.group(1))}",
                code,
            )

        return code

    def _apply_variable_naming(self, code: str, pattern: CodePattern) -> str:
        """Apply variable naming pattern."""
        # This is complex and would require AST parsing for proper implementation
        # For now, just return the code as is
        return code

    def _apply_error_handling_pattern(self, code: str, pattern: CodePattern) -> str:
        """Apply error handling pattern."""
        # Add try-catch blocks if pattern suggests it
        if (
            "try" in pattern.description.lower()
            and "except" in pattern.description.lower()
        ):
            # Wrap main logic in try-except if not already present
            if "try:" not in code and "raise NotImplementedError" in code:
                code = code.replace(
                    "raise NotImplementedError",
                    "try:\n        # TODO: Implement logic\n        pass\n    except Exception as e:\n        raise NotImplementedError",
                )

        return code

    def _apply_logging_pattern(self, code: str, pattern: CodePattern) -> str:
        """Apply logging pattern."""
        # Add logging imports and calls if pattern suggests it
        if "logging" in pattern.description.lower() and "import logging" not in code:
            code = "import logging\n\n" + code

        return code

    def _apply_docstring_style(self, code: str, pattern: CodePattern) -> str:
        """Apply docstring style pattern."""
        # This would require more sophisticated parsing
        # For now, just return the code as is
        return code


# Utility functions


def to_snake_case(name: str) -> str:
    """Convert name to snake_case."""
    # Insert underscores before uppercase letters
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def to_pascal_case(name: str) -> str:
    """Convert name to PascalCase."""
    # Split on underscores and capitalize each part
    parts = name.split("_")
    return "".join(word.capitalize() for word in parts)


def apply_indentation_consistency(code: str) -> str:
    """Apply consistent indentation."""
    # Use 4 spaces for indentation (Python standard)
    lines = code.split("\n")
    consistent_lines = []

    for line in lines:
        if line.strip():
            # Count leading whitespace
            leading_spaces = len(line) - len(line.lstrip())
            if leading_spaces > 0:
                # Convert to 4-space indentation
                indent_level = leading_spaces // 4
                consistent_line = "    " * indent_level + line.lstrip()
                consistent_lines.append(consistent_line)
            else:
                consistent_lines.append(line)
        else:
            consistent_lines.append(line)

    return "\n".join(consistent_lines)


def apply_line_length_consistency(code: str) -> str:
    """Apply line length consistency (PEP 8: 79 characters)."""
    lines = code.split("\n")
    consistent_lines = []

    for line in lines:
        if len(line) > 79 and not line.strip().startswith("#"):
            # Try to break long lines
            if "," in line and "(" in line:
                # Break function parameters
                consistent_lines.append(break_long_line(line))
            else:
                consistent_lines.append(line)  # Keep as is for now
        else:
            consistent_lines.append(line)

    return "\n".join(consistent_lines)


def break_long_line(line: str) -> str:
    """Break a long line into multiple lines."""
    # Simple line breaking for function calls/definitions
    if "(" in line and ")" in line:
        before_paren = line[: line.index("(") + 1]
        after_paren = line[line.rindex(")") :]
        middle = line[line.index("(") + 1 : line.rindex(")")]

        if "," in middle:
            params = [p.strip() for p in middle.split(",")]
            indent = "    " * (len(before_paren) // 4 + 1)
            broken_params = f",\n{indent}".join(params)
            return f"{before_paren}\n{indent}{broken_params}\n{' ' * (len(before_paren) - 1)}{after_paren}"

    return line


def sort_imports_by_pattern(import_lines: list[str]) -> list[str]:
    """Sort imports according to existing patterns."""
    # Basic import sorting: standard library, third-party, local
    stdlib_imports = []
    thirdparty_imports = []
    local_imports = []
    other_lines = []

    stdlib_modules = {
        "os",
        "sys",
        "json",
        "time",
        "datetime",
        "collections",
        "typing",
        "re",
        "pathlib",
        "ast",
        "dataclasses",
        "abc",
    }

    for line in import_lines:
        if line.strip().startswith("import ") or line.strip().startswith("from "):
            module_match = re.match(
                r"(?:from\s+)?([a-zA-Z_][a-zA-Z0-9_]*)", line.strip()
            )
            if module_match:
                module = module_match.group(1)
                if module in stdlib_modules:
                    stdlib_imports.append(line)
                elif line.strip().startswith("from .") or line.strip().startswith(
                    "from .."
                ):
                    local_imports.append(line)
                else:
                    thirdparty_imports.append(line)
            else:
                other_lines.append(line)
        else:
            other_lines.append(line)

    # Combine in order: stdlib, third-party, local
    sorted_imports = []
    if stdlib_imports:
        sorted_imports.extend(sorted(stdlib_imports))
    if thirdparty_imports:
        if stdlib_imports:
            sorted_imports.append("")
        sorted_imports.extend(sorted(thirdparty_imports))
    if local_imports:
        if stdlib_imports or thirdparty_imports:
            sorted_imports.append("")
        sorted_imports.extend(sorted(local_imports))

    sorted_imports.extend(other_lines)
    return sorted_imports
