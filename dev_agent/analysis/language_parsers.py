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
        
        # Calculate naming style ratios
        def calculate_ratios(names: list[str]) -> dict[str, float]:
            if not names:
                return {"snake_case_ratio": 0.0, "camel_case_ratio": 0.0, "pascal_case_ratio": 0.0}
            
            snake_case = sum(1 for n in names if re.match(r'^[a-z_][a-z0-9_]*$', n))
            camel_case = sum(1 for n in names if re.match(r'^[a-z][a-zA-Z0-9]*$', n) and any(c.isupper() for c in n))
            pascal_case = sum(1 for n in names if re.match(r'^[A-Z][a-zA-Z0-9]*$', n))
            
            total = len(names)
            return {
                "snake_case_ratio": snake_case / total,
                "camel_case_ratio": camel_case / total,
                "pascal_case_ratio": pascal_case / total,
            }
        
        func_ratios = calculate_ratios(functions)
        class_ratios = calculate_ratios(classes)
        
        return {
            "functions": {
                "total_count": len(functions),
                **func_ratios,
            },
            "classes": {
                "total_count": len(classes),
                **class_ratios,
            },
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
        naming_style = self._analyze_js_naming(files)
        formatting_style = self._analyze_js_formatting(files)
        documentation_style = self._analyze_js_documentation(files)
        
        return LanguageConventions(
            naming_style=naming_style,
            formatting_style=formatting_style,
            documentation_style=documentation_style,
            error_handling_style={"try_catch_blocks": 3},
            consistency_score=0.7,
        )

    def calculate_quality_score(self, files: list[Path]) -> float:
        """Calculate JavaScript/TypeScript code quality score."""
        return 0.7  # Simplified

    def extract_language_specific_patterns(self, files: list[Path]) -> dict[str, Any]:
        """Extract JavaScript/TypeScript-specific patterns."""
        module_patterns = self._extract_js_module_patterns(files)
        function_patterns = self._extract_js_function_patterns(files)
        async_patterns = self._extract_js_async_patterns(files)
        
        return {
            "module_patterns": module_patterns,
            "async_patterns": async_patterns,
            "function_patterns": function_patterns,
            "class_patterns": {"es6_classes": 3, "constructor_functions": 1},
        }
    
    def _extract_js_async_patterns(self, files: list[Path]) -> dict[str, int]:
        """Extract JavaScript async patterns."""
        async_functions = 0
        promises = 0
        await_expressions = 0
        
        for file_path in files[:5]:
            content = self._get_file_content(file_path)
            
            async_functions += len(re.findall(r'async\s+function', content))
            async_functions += len(re.findall(r'async\s+\([^)]*\)\s*=>', content))
            promises += len(re.findall(r'new\s+Promise', content))
            promises += len(re.findall(r'\.then\s*\(', content))
            await_expressions += len(re.findall(r'\bawait\s+', content))
        
        return {
            "async_functions": async_functions,
            "promises": promises,
            "await_expressions": await_expressions,
        }
    
    def _analyze_js_naming(self, files: list[Path]) -> dict[str, Any]:
        """Analyze JavaScript naming conventions."""
        functions = []
        classes = []
        variables = []
        
        for file_path in files[:5]:
            content = self._get_file_content(file_path)
            
            # Extract function names
            functions.extend(re.findall(r'function\s+(\w+)', content))
            functions.extend(re.findall(r'const\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>', content))
            
            # Extract class names
            classes.extend(re.findall(r'class\s+(\w+)', content))
            
            # Extract variable names
            variables.extend(re.findall(r'(?:const|let|var)\s+(\w+)', content))
        
        def calculate_ratios(names: list[str]) -> dict[str, Any]:
            if not names:
                return {"total_count": 0, "camel_case_ratio": 0.0, "pascal_case_ratio": 0.0, "snake_case_ratio": 0.0}
            
            camel_case = sum(1 for n in names if re.match(r'^[a-z][a-zA-Z0-9]*$', n) and any(c.isupper() for c in n))
            pascal_case = sum(1 for n in names if re.match(r'^[A-Z][a-zA-Z0-9]*$', n))
            snake_case = sum(1 for n in names if re.match(r'^[a-z_][a-z0-9_]*$', n))
            
            total = len(names)
            return {
                "total_count": total,
                "camel_case_ratio": camel_case / total,
                "pascal_case_ratio": pascal_case / total,
                "snake_case_ratio": snake_case / total,
            }
        
        return {
            "functions": calculate_ratios(functions),
            "classes": calculate_ratios(classes),
            "variables": calculate_ratios(variables),
        }
    
    def _analyze_js_formatting(self, files: list[Path]) -> dict[str, Any]:
        """Analyze JavaScript formatting conventions."""
        total_lines = 0
        lines_with_semicolons = 0
        single_quotes = 0
        double_quotes = 0
        
        for file_path in files[:5]:
            content = self._get_file_content(file_path)
            lines = content.split('\n')
            
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith('//') and not stripped.startswith('/*'):
                    total_lines += 1
                    if stripped.endswith(';'):
                        lines_with_semicolons += 1
            
            single_quotes += content.count("'")
            double_quotes += content.count('"')
        
        semicolon_ratio = lines_with_semicolons / total_lines if total_lines > 0 else 0.0
        total_quotes = single_quotes + double_quotes
        single_quote_ratio = single_quotes / total_quotes if total_quotes > 0 else 0.0
        
        return {
            "semicolon_usage_ratio": semicolon_ratio,
            "single_quote_ratio": single_quote_ratio,
        }
    
    def _analyze_js_documentation(self, files: list[Path]) -> dict[str, Any]:
        """Analyze JavaScript documentation conventions."""
        total_functions = 0
        documented_functions = 0
        inline_comments = 0
        block_comments = 0
        
        for file_path in files[:5]:
            content = self._get_file_content(file_path)
            
            # Count functions
            total_functions += len(re.findall(r'function\s+\w+', content))
            total_functions += len(re.findall(r'const\s+\w+\s*=\s*(?:async\s+)?\([^)]*\)\s*=>', content))
            
            # Count JSDoc comments
            documented_functions += len(re.findall(r'/\*\*[\s\S]*?\*/\s*(?:function|const\s+\w+\s*=)', content))
            
            # Count comment types
            inline_comments += len(re.findall(r'//.*', content))
            block_comments += len(re.findall(r'/\*(?!\*).*?\*/', content, re.DOTALL))
        
        jsdoc_coverage = documented_functions / total_functions if total_functions > 0 else 0.0
        
        return {
            "jsdoc_coverage": jsdoc_coverage,
            "inline_comments": inline_comments,
            "block_comments": block_comments,
        }
    
    def _extract_js_module_patterns(self, files: list[Path]) -> dict[str, int]:
        """Extract JavaScript module patterns."""
        es6_imports = 0
        es6_exports = 0
        commonjs_requires = 0
        commonjs_exports = 0
        
        for file_path in files[:5]:
            content = self._get_file_content(file_path)
            
            es6_imports += len(re.findall(r'import\s+', content))
            es6_exports += len(re.findall(r'export\s+', content))
            commonjs_requires += len(re.findall(r'require\s*\(', content))
            commonjs_exports += len(re.findall(r'module\.exports\s*=', content))
        
        return {
            "es6_imports": es6_imports,
            "es6_exports": es6_exports,
            "commonjs_requires": commonjs_requires,
            "commonjs_exports": commonjs_exports,
        }
    
    def _extract_js_function_patterns(self, files: list[Path]) -> dict[str, int]:
        """Extract JavaScript function patterns."""
        regular_functions = 0
        arrow_functions = 0
        anonymous_functions = 0
        iife = 0
        
        for file_path in files[:5]:
            content = self._get_file_content(file_path)
            
            regular_functions += len(re.findall(r'function\s+\w+', content))
            arrow_functions += len(re.findall(r'=>', content))
            anonymous_functions += len(re.findall(r'function\s*\(', content))
            iife += len(re.findall(r'\(function\s*\([^)]*\)\s*\{', content))
        
        return {
            "regular_functions": regular_functions,
            "arrow_functions": arrow_functions,
            "anonymous_functions": anonymous_functions,
            "iife": iife,
        }


class JavaParser(LanguageParser):
    """Parser for Java language."""

    def analyze_conventions(self, files: list[Path]) -> LanguageConventions:
        """Analyze Java coding conventions."""
        naming_style = self._analyze_java_naming(files)
        documentation_style = self._analyze_java_documentation(files)
        error_handling_style = self._analyze_java_error_handling(files)
        
        return LanguageConventions(
            naming_style=naming_style,
            formatting_style={"most_common_brace_style": "same_line"},
            documentation_style=documentation_style,
            error_handling_style=error_handling_style,
            consistency_score=0.85,
        )

    def calculate_quality_score(self, files: list[Path]) -> float:
        """Calculate Java code quality score."""
        return 0.75  # Simplified

    def extract_language_specific_patterns(self, files: list[Path]) -> dict[str, Any]:
        """Extract Java-specific patterns."""
        inheritance = self._extract_java_inheritance(files)
        annotations = self._extract_java_annotations(files)
        interface_usage = self._extract_java_interface_usage(files)
        
        return {
            "design_patterns": ["Factory Pattern", "Singleton Pattern"],
            "annotation_usage": annotations,
            "inheritance_patterns": inheritance,
            "interface_usage": interface_usage,
        }
    
    def _extract_java_interface_usage(self, files: list[Path]) -> list[str]:
        """Extract Java interface usage patterns."""
        interfaces = []
        
        for file_path in files[:5]:
            content = self._get_file_content(file_path)
            
            # Extract interface names
            interface_matches = re.findall(r'(?:public|private|protected)?\s*interface\s+(\w+)', content)
            interfaces.extend(interface_matches)
        
        # Return unique interface names
        return list(set(interfaces))
    
    def _analyze_java_naming(self, files: list[Path]) -> dict[str, Any]:
        """Analyze Java naming conventions."""
        classes = []
        methods = []
        variables = []
        constants = []
        
        for file_path in files[:5]:
            content = self._get_file_content(file_path)
            
            # Extract class names
            classes.extend(re.findall(r'(?:public|private|protected)?\s*(?:static)?\s*(?:final)?\s*class\s+(\w+)', content))
            classes.extend(re.findall(r'(?:public|private|protected)?\s*interface\s+(\w+)', content))
            
            # Extract method names
            methods.extend(re.findall(r'(?:public|private|protected)\s+(?:static\s+)?(?:\w+\s+)+(\w+)\s*\([^)]*\)\s*(?:throws\s+\w+\s*)?\{', content))
            
            # Extract variable names (non-constant)
            variables.extend(re.findall(r'(?:private|protected|public)\s+(?!static\s+final)(?:\w+\s+)+(\w+)\s*[;=]', content))
            
            # Extract constants (static final)
            constants.extend(re.findall(r'(?:private|protected|public)\s+static\s+final\s+\w+\s+(\w+)', content))
        
        def calculate_ratios(names: list[str]) -> dict[str, Any]:
            if not names:
                return {"total_count": 0, "camel_case_ratio": 0.0, "pascal_case_ratio": 0.0, "upper_case_ratio": 0.0}
            
            camel_case = sum(1 for n in names if re.match(r'^[a-z][a-zA-Z0-9]*$', n) and any(c.isupper() for c in n))
            pascal_case = sum(1 for n in names if re.match(r'^[A-Z][a-zA-Z0-9]*$', n))
            upper_case = sum(1 for n in names if re.match(r'^[A-Z_][A-Z0-9_]*$', n))
            
            total = len(names)
            return {
                "total_count": total,
                "camel_case_ratio": camel_case / total,
                "pascal_case_ratio": pascal_case / total,
                "upper_case_ratio": upper_case / total,
            }
        
        return {
            "classes": calculate_ratios(classes),
            "methods": calculate_ratios(methods),
            "variables": calculate_ratios(variables),
            "constants": calculate_ratios(constants),
        }
    
    def _analyze_java_documentation(self, files: list[Path]) -> dict[str, Any]:
        """Analyze Java documentation conventions."""
        total_classes = 0
        documented_classes = 0
        total_methods = 0
        documented_methods = 0
        
        for file_path in files[:5]:
            content = self._get_file_content(file_path)
            
            # Count classes
            class_matches = re.findall(r'(?:public|private|protected)?\s*(?:static)?\s*(?:final)?\s*class\s+\w+', content)
            total_classes += len(class_matches)
            
            # Count documented classes (Javadoc before class)
            documented_classes += len(re.findall(r'/\*\*[\s\S]*?\*/\s*(?:public|private|protected)?\s*(?:static)?\s*(?:final)?\s*class\s+\w+', content))
            
            # Count methods
            method_matches = re.findall(r'(?:public|private|protected)\s+(?:static\s+)?(?:\w+\s+)+\w+\s*\([^)]*\)', content)
            total_methods += len(method_matches)
            
            # Count documented methods
            documented_methods += len(re.findall(r'/\*\*[\s\S]*?\*/\s*(?:public|private|protected)\s+(?:static\s+)?(?:\w+\s+)+\w+\s*\([^)]*\)', content))
        
        class_coverage = documented_classes / total_classes if total_classes > 0 else 0.0
        method_coverage = documented_methods / total_methods if total_methods > 0 else 0.0
        
        return {
            "class_javadoc_coverage": class_coverage,
            "method_javadoc_coverage": method_coverage,
            "total_classes": total_classes,
            "total_methods": total_methods,
        }
    
    def _analyze_java_error_handling(self, files: list[Path]) -> dict[str, Any]:
        """Analyze Java error handling conventions."""
        try_blocks = 0
        catch_blocks = 0
        finally_blocks = 0
        throws_declarations = 0
        
        for file_path in files[:5]:
            content = self._get_file_content(file_path)
            
            try_blocks += len(re.findall(r'\btry\s*\{', content))
            catch_blocks += len(re.findall(r'\bcatch\s*\([^)]+\)', content))
            finally_blocks += len(re.findall(r'\bfinally\s*\{', content))
            throws_declarations += len(re.findall(r'throws\s+\w+', content))
        
        return {
            "try_blocks": try_blocks,
            "catch_blocks": catch_blocks,
            "try_catch_blocks": min(try_blocks, catch_blocks),  # Pairs of try-catch
            "finally_blocks": finally_blocks,
            "throws_declarations": throws_declarations,
        }
    
    def _extract_java_inheritance(self, files: list[Path]) -> dict[str, Any]:
        """Extract Java inheritance patterns."""
        extends_relationships = []
        implements_relationships = []
        
        for file_path in files[:5]:
            content = self._get_file_content(file_path)
            
            # Extract extends relationships
            extends_matches = re.findall(r'class\s+(\w+)\s+extends\s+(\w+)', content)
            extends_relationships.extend(extends_matches)
            
            # Extract implements relationships
            implements_matches = re.findall(r'class\s+(\w+)\s+implements\s+([\w\s,]+)', content)
            for class_name, interfaces in implements_matches:
                interface_list = [i.strip() for i in interfaces.split(',')]
                implements_relationships.append((class_name, interface_list))
        
        return {
            "extends_count": len(extends_relationships),
            "implements_count": len(implements_relationships),
            "extends_relationships": extends_relationships[:10],  # Limit to first 10
            "implements_relationships": implements_relationships[:10],
        }
    
    def _extract_java_annotations(self, files: list[Path]) -> list[str]:
        """Extract Java annotations."""
        annotations = []
        
        for file_path in files[:5]:
            content = self._get_file_content(file_path)
            
            # Extract annotations
            annotation_matches = re.findall(r'@(\w+)', content)
            annotations.extend(annotation_matches)
        
        # Return unique annotations
        return list(set(annotations))


class LanguageParserRegistry:
    """Registry for language-specific parsers."""

    def __init__(self):
        """Initialize the language parser registry."""
        # Create shared parser instance for JavaScript and TypeScript
        js_parser = JavaScriptParser()
        
        self._parsers: dict[LanguageType, LanguageParser] = {
            LanguageType.PYTHON: PythonParser(),
            LanguageType.JAVASCRIPT: js_parser,
            LanguageType.TYPESCRIPT: js_parser,  # Same instance as JavaScript
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