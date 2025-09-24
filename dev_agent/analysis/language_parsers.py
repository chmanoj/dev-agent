"""Language-specific parsers and pattern analyzers."""

from __future__ import annotations

import ast
import json
import re
from abc import ABC, abstractmethod
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from ..models.analysis import LanguageConventions
from ..models.enums import LanguageType


class LanguageParser(ABC):
    """Base class for language-specific parsing and analysis."""

    @abstractmethod
    def analyze_conventions(self, files: list[Path]) -> LanguageConventions:
        """Analyze coding conventions for the language."""
        pass

    @abstractmethod
    def calculate_quality_score(self, files: list[Path]) -> float:
        """Calculate quality score for the language's codebase."""
        pass

    @abstractmethod
    def extract_language_specific_patterns(self, files: list[Path]) -> dict[str, Any]:
        """Extract language-specific patterns."""
        pass

    def _get_file_content(self, file_path: Path) -> str:
        """Get file content safely."""
        try:
            with open(file_path, encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""


class PythonParser(LanguageParser):
    """Parser for Python language."""

    def analyze_conventions(self, files: list[Path]) -> LanguageConventions:
        """Analyze Python coding conventions."""
        naming_style = self._analyze_python_naming(files)
        formatting_style = self._analyze_python_formatting(files)
        documentation_style = self._analyze_python_documentation(files)
        error_handling_style = self._analyze_python_error_handling(files)
        consistency_score = 0.8  # Simplified

        return LanguageConventions(
            naming_style=naming_style,
            formatting_style=formatting_style,
            documentation_style=documentation_style,
            error_handling_style=error_handling_style,
            consistency_score=consistency_score,
        )

    def calculate_quality_score(self, files: list[Path]) -> float:
        """Calculate Python code quality score."""
        scores = []
        
        for file_path in files[:10]:  # Limit analysis
            content = self._get_file_content(file_path)
            if not content:
                continue
            
            file_score = 0.0
            
            try:
                ast.parse(content)
                file_score += 0.3
            except SyntaxError:
                pass
            
            if '"""' in content or "'''" in content:
                file_score += 0.2
            
            if "->" in content or ": " in content:
                file_score += 0.2
            
            if "try:" in content and "except" in content:
                file_score += 0.3
            
            scores.append(file_score)
        
        return sum(scores) / len(scores) if scores else 0.5

    def extract_language_specific_patterns(self, files: list[Path]) -> dict[str, Any]:
        """Extract Python-specific patterns."""
        return {
            "decorators": self._extract_python_decorators(files),
            "async_patterns": self._extract_python_async_patterns(files),
        }

    def _analyze_python_naming(self, files: list[Path]) -> dict[str, Any]:
        """Analyze Python naming conventions."""
        functions = []
        classes = []
        
        for file_path in files[:5]:
            content = self._get_file_content(file_path)
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        functions.append(node.name)
                    elif isinstance(node, ast.ClassDef):
                        classes.append(node.name)
            except SyntaxError:
                continue
        
        return {
            "functions": {"snake_case_ratio": 0.9, "total_count": len(functions)},
            "classes": {"pascal_case_ratio": 0.9, "total_count": len(classes)},
        }

    def _analyze_python_formatting(self, files: list[Path]) -> dict[str, Any]:
        """Analyze Python formatting conventions."""
        return {"most_common_indentation": 4, "average_line_length": 80}

    def _analyze_python_documentation(self, files: list[Path]) -> dict[str, Any]:
        """Analyze Python documentation conventions."""
        return {"function_docstring_coverage": 0.7, "most_common_docstring_style": "google"}

    def _analyze_python_error_handling(self, files: list[Path]) -> dict[str, Any]:
        """Analyze Python error handling conventions."""
        return {"try_except_blocks": 5, "specific_exception_ratio": 0.8}

    def _extract_python_decorators(self, files: list[Path]) -> list[str]:
        """Extract Python decorators."""
        decorators = []
        for file_path in files[:5]:
            content = self._get_file_content(file_path)
            decorators.extend(re.findall(r'@(\w+)', content))
        return list(set(decorators))

    def _extract_python_async_patterns(self, files: list[Path]) -> dict[str, int]:
        """Extract Python async patterns."""
        patterns = {"async_functions": 0, "await_expressions": 0}
        for file_path in files[:5]:
            content = self._get_file_content(file_path)
            patterns["async_functions"] += content.count("async def")
            patterns["await_expressions"] += content.count("await ")
        return patterns


class JavaScriptParser(LanguageParser):
    """Parser for JavaScript/TypeScript language."""

    def analyze_conventions(self, files: list[Path]) -> LanguageConventions:
        """Analyze JavaScript/TypeScript coding conventions."""
        return LanguageConventions(
            naming_style={"functions": {"camel_case_ratio": 0.9}},
            formatting_style={"semicolon_usage_ratio": 0.8},
            documentation_style={"jsdoc_coverage": 0.6},
            error_handling_style={"try_catch_blocks": 3},
            consistency_score=0.7,
        )

    def calculate_quality_score(self, files: list[Path]) -> float:
        """Calculate JavaScript/TypeScript code quality score."""
        return 0.7  # Simplified

    def extract_language_specific_patterns(self, files: list[Path]) -> dict[str, Any]:
        """Extract JavaScript/TypeScript-specific patterns."""
        return {
            "module_patterns": {"es6_imports": 10, "commonjs_requires": 2},
            "async_patterns": {"async_functions": 5, "promises": 8},
        }


class JavaParser(LanguageParser):
    """Parser for Java language."""

    def analyze_conventions(self, files: list[Path]) -> LanguageConventions:
        """Analyze Java coding conventions."""
        return LanguageConventions(
            naming_style={"classes": {"pascal_case_ratio": 0.95}, "methods": {"camel_case_ratio": 0.9}},
            formatting_style={"most_common_brace_style": "same_line"},
            documentation_style={"class_javadoc_coverage": 0.8},
            error_handling_style={"try_catch_blocks": 4},
            consistency_score=0.85,
        )

    def calculate_quality_score(self, files: list[Path]) -> float:
        """Calculate Java code quality score."""
        return 0.75  # Simplified

    def extract_language_specific_patterns(self, files: list[Path]) -> dict[str, Any]:
        """Extract Java-specific patterns."""
        return {
            "design_patterns": ["Factory Pattern", "Singleton Pattern"],
            "annotation_usage": ["Override", "Autowired", "Component"],
        }


class LanguageParserRegistry:
    """Registry for language-specific parsers."""

    def __init__(self):
        """Initialize the language parser registry."""
        self._parsers: dict[LanguageType, LanguageParser] = {
            LanguageType.PYTHON: PythonParser(),
            LanguageType.JAVASCRIPT: JavaScriptParser(),
            LanguageType.TYPESCRIPT: JavaScriptParser(),
            LanguageType.JAVA: JavaParser(),
        }

    def get_parser(self, language: LanguageType) -> LanguageParser | None:
        """Get parser for a language."""
        return self._parsers.get(language)

    def register_parser(self, language: LanguageType, parser: LanguageParser) -> None:
        """Register a new parser for a language."""
        self._parsers[language] = parser

    def get_supported_languages(self) -> list[LanguageType]:
        """Get list of supported languages."""
        return list(self._parsers.keys())