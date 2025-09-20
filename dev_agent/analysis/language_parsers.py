"""Language-specific parsers for multi-language analysis."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import yaml


class LanguageParser(ABC):
    """Base class for language-specific parsers."""

    @abstractmethod
    def parse_file(self, file_path: str) -> dict[str, Any]:
        """Parse a single file and extract relevant information.

        Args:
            file_path: Path to the file to parse

        Returns:
            Dictionary containing parsed information
        """

    @abstractmethod
    def extract_symbols(self, file_path: str) -> list[dict[str, Any]]:
        """Extract symbols (functions, classes, variables) from a file.

        Args:
            file_path: Path to the file to analyze

        Returns:
            List of symbol dictionaries
        """

    @abstractmethod
    def analyze_imports(self, file_path: str) -> list[dict[str, Any]]:
        """Analyze import statements in a file.

        Args:
            file_path: Path to the file to analyze

        Returns:
            List of import information dictionaries
        """


class PythonParser(LanguageParser):
    """Parser for Python source files."""

    def parse_file(self, file_path: str) -> dict[str, Any]:
        """Parse a Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                'file_path': file_path,
                'language': 'python',
                'line_count': len(content.splitlines()),
                'symbols': self.extract_symbols(file_path),
                'imports': self.analyze_imports(file_path),
                'docstrings': self._extract_docstrings(content),
                'decorators': self._extract_decorators(content),
                'type_hints': self._has_type_hints(content)
            }
        except (UnicodeDecodeError, IOError) as e:
            return {'error': str(e), 'file_path': file_path}

    def extract_symbols(self, file_path: str) -> list[dict[str, Any]]:
        """Extract Python symbols."""
        symbols = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract classes
            class_pattern = r'^class\s+(\w+)(?:\([^)]*\))?:'
            for match in re.finditer(class_pattern, content, re.MULTILINE):
                symbols.append({
                    'name': match.group(1),
                    'type': 'class',
                    'line': content[:match.start()].count('\n') + 1
                })

            # Extract functions
            func_pattern = r'^(?:\s*)def\s+(\w+)\s*\([^)]*\):'
            for match in re.finditer(func_pattern, content, re.MULTILINE):
                symbols.append({
                    'name': match.group(1),
                    'type': 'function',
                    'line': content[:match.start()].count('\n') + 1
                })

        except (UnicodeDecodeError, IOError):
            pass

        return symbols

    def analyze_imports(self, file_path: str) -> list[dict[str, Any]]:
        """Analyze Python imports."""
        imports = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Standard imports
            import_pattern = r'^import\s+([^\s#]+)'
            for match in re.finditer(import_pattern, content, re.MULTILINE):
                imports.append({
                    'module': match.group(1),
                    'type': 'import',
                    'line': content[:match.start()].count('\n') + 1
                })

            # From imports
            from_pattern = r'^from\s+([^\s]+)\s+import\s+([^#\n]+)'
            for match in re.finditer(from_pattern, content, re.MULTILINE):
                imports.append({
                    'module': match.group(1),
                    'names': [name.strip() for name in match.group(2).split(',')],
                    'type': 'from_import',
                    'line': content[:match.start()].count('\n') + 1
                })

        except (UnicodeDecodeError, IOError):
            pass

        return imports

    def _extract_docstrings(self, content: str) -> list[str]:
        """Extract docstrings from Python code."""
        docstring_pattern = r'"""([^"]*(?:"[^"]*)*?)"""'
        matches = re.findall(docstring_pattern, content, re.DOTALL)
        return [match.strip() for match in matches]

    def _extract_decorators(self, content: str) -> list[str]:
        """Extract decorators from Python code."""
        decorator_pattern = r'@(\w+(?:\.\w+)*)'
        return re.findall(decorator_pattern, content)

    def _has_type_hints(self, content: str) -> bool:
        """Check if the file uses type hints."""
        type_hint_patterns = [
            r':\s*\w+\s*=',  # Variable annotations
            r'def\s+\w+\([^)]*:\s*\w+',  # Function parameter annotations
            r'->\s*\w+:',  # Return type annotations
            r'from typing import',  # Typing imports
        ]
        return any(re.search(pattern, content) for pattern in type_hint_patterns)


class JavaScriptParser(LanguageParser):
    """Parser for JavaScript source files."""

    def parse_file(self, file_path: str) -> dict[str, Any]:
        """Parse a JavaScript file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                'file_path': file_path,
                'language': 'javascript',
                'line_count': len(content.splitlines()),
                'symbols': self.extract_symbols(file_path),
                'imports': self.analyze_imports(file_path),
                'exports': self._extract_exports(content),
                'es6_features': self._detect_es6_features(content),
                'jsx': self._has_jsx(content)
            }
        except (UnicodeDecodeError, IOError) as e:
            return {'error': str(e), 'file_path': file_path}

    def extract_symbols(self, file_path: str) -> list[dict[str, Any]]:
        """Extract JavaScript symbols."""
        symbols = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract functions
            func_patterns = [
                r'function\s+(\w+)\s*\(',  # Function declarations
                r'const\s+(\w+)\s*=\s*(?:async\s+)?function',  # Function expressions
                r'const\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>',  # Arrow functions
                r'(\w+)\s*:\s*(?:async\s+)?function',  # Object methods
            ]

            for pattern in func_patterns:
                for match in re.finditer(pattern, content):
                    symbols.append({
                        'name': match.group(1),
                        'type': 'function',
                        'line': content[:match.start()].count('\n') + 1
                    })

            # Extract classes
            class_pattern = r'class\s+(\w+)(?:\s+extends\s+\w+)?'
            for match in re.finditer(class_pattern, content):
                symbols.append({
                    'name': match.group(1),
                    'type': 'class',
                    'line': content[:match.start()].count('\n') + 1
                })

        except (UnicodeDecodeError, IOError):
            pass

        return symbols

    def analyze_imports(self, file_path: str) -> list[dict[str, Any]]:
        """Analyze JavaScript imports."""
        imports = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # ES6 imports
            import_patterns = [
                r'import\s+(\w+)\s+from\s+[\'"]([^\'"]+)[\'"]',  # Default imports
                r'import\s*\{\s*([^}]+)\s*\}\s*from\s+[\'"]([^\'"]+)[\'"]',  # Named imports
                r'import\s*\*\s*as\s+(\w+)\s+from\s+[\'"]([^\'"]+)[\'"]',  # Namespace imports
            ]

            for pattern in import_patterns:
                for match in re.finditer(pattern, content):
                    imports.append({
                        'module': match.group(2) if len(match.groups()) > 1 else match.group(1),
                        'type': 'es6_import',
                        'line': content[:match.start()].count('\n') + 1
                    })

            # CommonJS requires
            require_pattern = r'(?:const|let|var)\s+(?:\{([^}]+)\}|(\w+))\s*=\s*require\([\'"]([^\'"]+)[\'"]\)'
            for match in re.finditer(require_pattern, content):
                imports.append({
                    'module': match.group(3),
                    'type': 'commonjs_require',
                    'line': content[:match.start()].count('\n') + 1
                })

        except (UnicodeDecodeError, IOError):
            pass

        return imports

    def _extract_exports(self, content: str) -> list[dict[str, Any]]:
        """Extract export statements."""
        exports = []
        
        export_patterns = [
            r'export\s+default\s+(\w+)',  # Default exports
            r'export\s+\{\s*([^}]+)\s*\}',  # Named exports
            r'export\s+(?:const|let|var|function|class)\s+(\w+)',  # Direct exports
        ]

        for pattern in export_patterns:
            for match in re.finditer(pattern, content):
                exports.append({
                    'name': match.group(1),
                    'type': 'export',
                    'line': content[:match.start()].count('\n') + 1
                })

        return exports

    def _detect_es6_features(self, content: str) -> list[str]:
        """Detect ES6+ features in the code."""
        features = []
        
        es6_patterns = {
            'arrow_functions': r'=>',
            'template_literals': r'`[^`]*`',
            'destructuring': r'\{[^}]+\}\s*=',
            'spread_operator': r'\.\.\.',
            'const_let': r'\b(?:const|let)\b',
            'classes': r'\bclass\b',
            'async_await': r'\b(?:async|await)\b',
        }

        for feature, pattern in es6_patterns.items():
            if re.search(pattern, content):
                features.append(feature)

        return features

    def _has_jsx(self, content: str) -> bool:
        """Check if the file contains JSX."""
        jsx_patterns = [
            r'<\w+[^>]*>',  # JSX elements
            r'React\.createElement',  # React createElement calls
            r'import.*React',  # React imports
        ]
        return any(re.search(pattern, content) for pattern in jsx_patterns)


class TypeScriptParser(LanguageParser):
    """Parser for TypeScript source files."""

    def parse_file(self, file_path: str) -> dict[str, Any]:
        """Parse a TypeScript file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                'file_path': file_path,
                'language': 'typescript',
                'line_count': len(content.splitlines()),
                'symbols': self.extract_symbols(file_path),
                'imports': self.analyze_imports(file_path),
                'interfaces': self._extract_interfaces(content),
                'types': self._extract_types(content),
                'generics': self._has_generics(content),
                'decorators': self._extract_decorators(content)
            }
        except (UnicodeDecodeError, IOError) as e:
            return {'error': str(e), 'file_path': file_path}

    def extract_symbols(self, file_path: str) -> list[dict[str, Any]]:
        """Extract TypeScript symbols."""
        # Reuse JavaScript parser and add TypeScript-specific symbols
        js_parser = JavaScriptParser()
        symbols = js_parser.extract_symbols(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract interfaces
            interface_pattern = r'interface\s+(\w+)'
            for match in re.finditer(interface_pattern, content):
                symbols.append({
                    'name': match.group(1),
                    'type': 'interface',
                    'line': content[:match.start()].count('\n') + 1
                })

            # Extract type aliases
            type_pattern = r'type\s+(\w+)\s*='
            for match in re.finditer(type_pattern, content):
                symbols.append({
                    'name': match.group(1),
                    'type': 'type_alias',
                    'line': content[:match.start()].count('\n') + 1
                })

            # Extract enums
            enum_pattern = r'enum\s+(\w+)'
            for match in re.finditer(enum_pattern, content):
                symbols.append({
                    'name': match.group(1),
                    'type': 'enum',
                    'line': content[:match.start()].count('\n') + 1
                })

        except (UnicodeDecodeError, IOError):
            pass

        return symbols

    def analyze_imports(self, file_path: str) -> list[dict[str, Any]]:
        """Analyze TypeScript imports."""
        # Reuse JavaScript parser for basic imports
        js_parser = JavaScriptParser()
        return js_parser.analyze_imports(file_path)

    def _extract_interfaces(self, content: str) -> list[dict[str, Any]]:
        """Extract TypeScript interfaces."""
        interfaces = []
        interface_pattern = r'interface\s+(\w+)(?:\s+extends\s+[\w,\s]+)?\s*\{([^}]*)\}'
        
        for match in re.finditer(interface_pattern, content, re.DOTALL):
            interfaces.append({
                'name': match.group(1),
                'properties': self._parse_interface_properties(match.group(2)),
                'line': content[:match.start()].count('\n') + 1
            })

        return interfaces

    def _extract_types(self, content: str) -> list[dict[str, Any]]:
        """Extract TypeScript type aliases."""
        types = []
        type_pattern = r'type\s+(\w+)\s*=\s*([^;\n]+)'
        
        for match in re.finditer(type_pattern, content):
            types.append({
                'name': match.group(1),
                'definition': match.group(2).strip(),
                'line': content[:match.start()].count('\n') + 1
            })

        return types

    def _parse_interface_properties(self, properties_text: str) -> list[dict[str, Any]]:
        """Parse interface properties."""
        properties = []
        prop_pattern = r'(\w+)(\?)?:\s*([^;\n]+)'
        
        for match in re.finditer(prop_pattern, properties_text):
            properties.append({
                'name': match.group(1),
                'optional': bool(match.group(2)),
                'type': match.group(3).strip()
            })

        return properties

    def _has_generics(self, content: str) -> bool:
        """Check if the file uses generics."""
        generic_patterns = [
            r'<[A-Z]\w*>',  # Generic type parameters
            r'<[A-Z]\w*\s+extends\s+\w+>',  # Constrained generics
            r'Array<\w+>',  # Generic arrays
        ]
        return any(re.search(pattern, content) for pattern in generic_patterns)

    def _extract_decorators(self, content: str) -> list[str]:
        """Extract TypeScript decorators."""
        decorator_pattern = r'@(\w+(?:\.\w+)*)'
        return re.findall(decorator_pattern, content)


class JavaParser(LanguageParser):
    """Parser for Java source files."""

    def parse_file(self, file_path: str) -> dict[str, Any]:
        """Parse a Java file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                'file_path': file_path,
                'language': 'java',
                'line_count': len(content.splitlines()),
                'symbols': self.extract_symbols(file_path),
                'imports': self.analyze_imports(file_path),
                'package': self._extract_package(content),
                'annotations': self._extract_annotations(content),
                'access_modifiers': self._analyze_access_modifiers(content)
            }
        except (UnicodeDecodeError, IOError) as e:
            return {'error': str(e), 'file_path': file_path}

    def extract_symbols(self, file_path: str) -> list[dict[str, Any]]:
        """Extract Java symbols."""
        symbols = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract classes
            class_pattern = r'(?:public\s+|private\s+|protected\s+)?(?:abstract\s+|final\s+)?class\s+(\w+)'
            for match in re.finditer(class_pattern, content):
                symbols.append({
                    'name': match.group(1),
                    'type': 'class',
                    'line': content[:match.start()].count('\n') + 1
                })

            # Extract interfaces
            interface_pattern = r'(?:public\s+)?interface\s+(\w+)'
            for match in re.finditer(interface_pattern, content):
                symbols.append({
                    'name': match.group(1),
                    'type': 'interface',
                    'line': content[:match.start()].count('\n') + 1
                })

            # Extract methods
            method_pattern = r'(?:public\s+|private\s+|protected\s+)?(?:static\s+)?(?:final\s+)?(?:\w+\s+)?(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{'
            for match in re.finditer(method_pattern, content):
                if match.group(1) not in ['if', 'for', 'while', 'switch']:  # Exclude control structures
                    symbols.append({
                        'name': match.group(1),
                        'type': 'method',
                        'line': content[:match.start()].count('\n') + 1
                    })

        except (UnicodeDecodeError, IOError):
            pass

        return symbols

    def analyze_imports(self, file_path: str) -> list[dict[str, Any]]:
        """Analyze Java imports."""
        imports = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            import_pattern = r'import\s+(?:static\s+)?([^;\n]+);'
            for match in re.finditer(import_pattern, content):
                imports.append({
                    'module': match.group(1).strip(),
                    'type': 'import',
                    'line': content[:match.start()].count('\n') + 1
                })

        except (UnicodeDecodeError, IOError):
            pass

        return imports

    def _extract_package(self, content: str) -> str | None:
        """Extract package declaration."""
        package_pattern = r'package\s+([^;\n]+);'
        match = re.search(package_pattern, content)
        return match.group(1).strip() if match else None

    def _extract_annotations(self, content: str) -> list[str]:
        """Extract Java annotations."""
        annotation_pattern = r'@(\w+(?:\.\w+)*)'
        return re.findall(annotation_pattern, content)

    def _analyze_access_modifiers(self, content: str) -> dict[str, int]:
        """Analyze usage of access modifiers."""
        modifiers = {'public': 0, 'private': 0, 'protected': 0}
        
        for modifier in modifiers:
            pattern = rf'\b{modifier}\s+'
            modifiers[modifier] = len(re.findall(pattern, content))

        return modifiers


class HTMLParser(LanguageParser):
    """Parser for HTML files."""

    def parse_file(self, file_path: str) -> dict[str, Any]:
        """Parse an HTML file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                'file_path': file_path,
                'language': 'html',
                'line_count': len(content.splitlines()),
                'symbols': self.extract_symbols(file_path),
                'imports': self.analyze_imports(file_path),
                'elements': self._extract_elements(content),
                'scripts': self._extract_scripts(content),
                'styles': self._extract_styles(content)
            }
        except (UnicodeDecodeError, IOError) as e:
            return {'error': str(e), 'file_path': file_path}

    def extract_symbols(self, file_path: str) -> list[dict[str, Any]]:
        """Extract HTML symbols (IDs, classes)."""
        symbols = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract IDs
            id_pattern = r'id=["\']([^"\']+)["\']'
            for match in re.finditer(id_pattern, content):
                symbols.append({
                    'name': match.group(1),
                    'type': 'id',
                    'line': content[:match.start()].count('\n') + 1
                })

            # Extract classes
            class_pattern = r'class=["\']([^"\']+)["\']'
            for match in re.finditer(class_pattern, content):
                for class_name in match.group(1).split():
                    symbols.append({
                        'name': class_name,
                        'type': 'class',
                        'line': content[:match.start()].count('\n') + 1
                    })

        except (UnicodeDecodeError, IOError):
            pass

        return symbols

    def analyze_imports(self, file_path: str) -> list[dict[str, Any]]:
        """Analyze HTML imports (scripts, stylesheets)."""
        imports = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Script imports
            script_pattern = r'<script[^>]*src=["\']([^"\']+)["\']'
            for match in re.finditer(script_pattern, content):
                imports.append({
                    'module': match.group(1),
                    'type': 'script',
                    'line': content[:match.start()].count('\n') + 1
                })

            # Stylesheet imports
            link_pattern = r'<link[^>]*href=["\']([^"\']+)["\'][^>]*rel=["\']stylesheet["\']'
            for match in re.finditer(link_pattern, content):
                imports.append({
                    'module': match.group(1),
                    'type': 'stylesheet',
                    'line': content[:match.start()].count('\n') + 1
                })

        except (UnicodeDecodeError, IOError):
            pass

        return imports

    def _extract_elements(self, content: str) -> dict[str, int]:
        """Extract HTML element counts."""
        elements = {}
        element_pattern = r'<(\w+)(?:\s|>)'
        
        for match in re.finditer(element_pattern, content):
            element = match.group(1).lower()
            elements[element] = elements.get(element, 0) + 1

        return elements

    def _extract_scripts(self, content: str) -> list[dict[str, Any]]:
        """Extract inline scripts."""
        scripts = []
        script_pattern = r'<script[^>]*>(.*?)</script>'
        
        for match in re.finditer(script_pattern, content, re.DOTALL):
            if match.group(1).strip():
                scripts.append({
                    'content': match.group(1).strip(),
                    'line': content[:match.start()].count('\n') + 1
                })

        return scripts

    def _extract_styles(self, content: str) -> list[dict[str, Any]]:
        """Extract inline styles."""
        styles = []
        style_pattern = r'<style[^>]*>(.*?)</style>'
        
        for match in re.finditer(style_pattern, content, re.DOTALL):
            if match.group(1).strip():
                styles.append({
                    'content': match.group(1).strip(),
                    'line': content[:match.start()].count('\n') + 1
                })

        return styles


class CSSParser(LanguageParser):
    """Parser for CSS files."""

    def parse_file(self, file_path: str) -> dict[str, Any]:
        """Parse a CSS file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                'file_path': file_path,
                'language': 'css',
                'line_count': len(content.splitlines()),
                'symbols': self.extract_symbols(file_path),
                'imports': self.analyze_imports(file_path),
                'selectors': self._extract_selectors(content),
                'properties': self._extract_properties(content),
                'media_queries': self._extract_media_queries(content)
            }
        except (UnicodeDecodeError, IOError) as e:
            return {'error': str(e), 'file_path': file_path}

    def extract_symbols(self, file_path: str) -> list[dict[str, Any]]:
        """Extract CSS symbols (selectors)."""
        return self._extract_selectors_as_symbols(file_path)

    def analyze_imports(self, file_path: str) -> list[dict[str, Any]]:
        """Analyze CSS imports."""
        imports = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            import_pattern = r'@import\s+["\']([^"\']+)["\']'
            for match in re.finditer(import_pattern, content):
                imports.append({
                    'module': match.group(1),
                    'type': 'css_import',
                    'line': content[:match.start()].count('\n') + 1
                })

        except (UnicodeDecodeError, IOError):
            pass

        return imports

    def _extract_selectors(self, content: str) -> list[str]:
        """Extract CSS selectors."""
        selector_pattern = r'([^{}]+)\s*\{'
        selectors = []
        
        for match in re.finditer(selector_pattern, content):
            selector = match.group(1).strip()
            if selector and not selector.startswith('@'):
                selectors.append(selector)

        return selectors

    def _extract_selectors_as_symbols(self, file_path: str) -> list[dict[str, Any]]:
        """Extract CSS selectors as symbols."""
        symbols = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            selector_pattern = r'([^{}]+)\s*\{'
            for match in re.finditer(selector_pattern, content):
                selector = match.group(1).strip()
                if selector and not selector.startswith('@'):
                    symbols.append({
                        'name': selector,
                        'type': 'selector',
                        'line': content[:match.start()].count('\n') + 1
                    })

        except (UnicodeDecodeError, IOError):
            pass

        return symbols

    def _extract_properties(self, content: str) -> dict[str, int]:
        """Extract CSS property usage counts."""
        properties = {}
        property_pattern = r'(\w+(?:-\w+)*)\s*:'
        
        for match in re.finditer(property_pattern, content):
            prop = match.group(1)
            properties[prop] = properties.get(prop, 0) + 1

        return properties

    def _extract_media_queries(self, content: str) -> list[str]:
        """Extract media queries."""
        media_pattern = r'@media\s+([^{]+)'
        return [match.group(1).strip() for match in re.finditer(media_pattern, content)]


class JSONParser(LanguageParser):
    """Parser for JSON files."""

    def parse_file(self, file_path: str) -> dict[str, Any]:
        """Parse a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                data = json.loads(content)

            return {
                'file_path': file_path,
                'language': 'json',
                'line_count': len(content.splitlines()),
                'symbols': self.extract_symbols(file_path),
                'imports': self.analyze_imports(file_path),
                'structure': self._analyze_structure(data),
                'keys': self._extract_keys(data)
            }
        except (json.JSONDecodeError, UnicodeDecodeError, IOError) as e:
            return {'error': str(e), 'file_path': file_path}

    def extract_symbols(self, file_path: str) -> list[dict[str, Any]]:
        """Extract JSON keys as symbols."""
        symbols = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                symbols = self._extract_keys_as_symbols(data)
        except (json.JSONDecodeError, UnicodeDecodeError, IOError):
            pass

        return symbols

    def analyze_imports(self, file_path: str) -> list[dict[str, Any]]:
        """JSON files don't have imports."""
        return []

    def _analyze_structure(self, data: Any) -> dict[str, Any]:
        """Analyze JSON structure."""
        if isinstance(data, dict):
            return {
                'type': 'object',
                'keys': len(data),
                'nested_objects': sum(1 for v in data.values() if isinstance(v, dict)),
                'arrays': sum(1 for v in data.values() if isinstance(v, list))
            }
        elif isinstance(data, list):
            return {
                'type': 'array',
                'length': len(data),
                'item_types': list(set(type(item).__name__ for item in data))
            }
        else:
            return {'type': type(data).__name__}

    def _extract_keys(self, data: Any, prefix: str = '') -> list[str]:
        """Extract all keys from JSON data."""
        keys = []
        if isinstance(data, dict):
            for key, value in data.items():
                full_key = f"{prefix}.{key}" if prefix else key
                keys.append(full_key)
                if isinstance(value, (dict, list)):
                    keys.extend(self._extract_keys(value, full_key))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    keys.extend(self._extract_keys(item, f"{prefix}[{i}]"))
        return keys

    def _extract_keys_as_symbols(self, data: Any, prefix: str = '') -> list[dict[str, Any]]:
        """Extract JSON keys as symbols."""
        symbols = []
        if isinstance(data, dict):
            for key, value in data.items():
                full_key = f"{prefix}.{key}" if prefix else key
                symbols.append({
                    'name': full_key,
                    'type': 'json_key',
                    'value_type': type(value).__name__
                })
                if isinstance(value, (dict, list)):
                    symbols.extend(self._extract_keys_as_symbols(value, full_key))
        return symbols


class YAMLParser(LanguageParser):
    """Parser for YAML files."""

    def parse_file(self, file_path: str) -> dict[str, Any]:
        """Parse a YAML file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                data = yaml.safe_load(content)

            return {
                'file_path': file_path,
                'language': 'yaml',
                'line_count': len(content.splitlines()),
                'symbols': self.extract_symbols(file_path),
                'imports': self.analyze_imports(file_path),
                'structure': self._analyze_structure(data),
                'keys': self._extract_keys(data)
            }
        except (yaml.YAMLError, UnicodeDecodeError, IOError) as e:
            return {'error': str(e), 'file_path': file_path}

    def extract_symbols(self, file_path: str) -> list[dict[str, Any]]:
        """Extract YAML keys as symbols."""
        symbols = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                symbols = self._extract_keys_as_symbols(data)
        except (yaml.YAMLError, UnicodeDecodeError, IOError):
            pass

        return symbols

    def analyze_imports(self, file_path: str) -> list[dict[str, Any]]:
        """YAML files don't have imports."""
        return []

    def _analyze_structure(self, data: Any) -> dict[str, Any]:
        """Analyze YAML structure."""
        if isinstance(data, dict):
            return {
                'type': 'mapping',
                'keys': len(data),
                'nested_mappings': sum(1 for v in data.values() if isinstance(v, dict)),
                'sequences': sum(1 for v in data.values() if isinstance(v, list))
            }
        elif isinstance(data, list):
            return {
                'type': 'sequence',
                'length': len(data),
                'item_types': list(set(type(item).__name__ for item in data))
            }
        else:
            return {'type': type(data).__name__}

    def _extract_keys(self, data: Any, prefix: str = '') -> list[str]:
        """Extract all keys from YAML data."""
        keys = []
        if isinstance(data, dict):
            for key, value in data.items():
                full_key = f"{prefix}.{key}" if prefix else str(key)
                keys.append(full_key)
                if isinstance(value, (dict, list)):
                    keys.extend(self._extract_keys(value, full_key))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    keys.extend(self._extract_keys(item, f"{prefix}[{i}]"))
        return keys

    def _extract_keys_as_symbols(self, data: Any, prefix: str = '') -> list[dict[str, Any]]:
        """Extract YAML keys as symbols."""
        symbols = []
        if isinstance(data, dict):
            for key, value in data.items():
                full_key = f"{prefix}.{key}" if prefix else str(key)
                symbols.append({
                    'name': full_key,
                    'type': 'yaml_key',
                    'value_type': type(value).__name__
                })
                if isinstance(value, (dict, list)):
                    symbols.extend(self._extract_keys_as_symbols(value, full_key))
        return symbols


class XMLParser(LanguageParser):
    """Parser for XML files."""

    def parse_file(self, file_path: str) -> dict[str, Any]:
        """Parse an XML file."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                'file_path': file_path,
                'language': 'xml',
                'line_count': len(content.splitlines()),
                'symbols': self.extract_symbols(file_path),
                'imports': self.analyze_imports(file_path),
                'root_element': root.tag,
                'elements': self._extract_elements(root),
                'namespaces': self._extract_namespaces(root)
            }
        except (ET.ParseError, UnicodeDecodeError, IOError) as e:
            return {'error': str(e), 'file_path': file_path}

    def extract_symbols(self, file_path: str) -> list[dict[str, Any]]:
        """Extract XML elements as symbols."""
        symbols = []
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            symbols = self._extract_elements_as_symbols(root)
        except (ET.ParseError, UnicodeDecodeError, IOError):
            pass

        return symbols

    def analyze_imports(self, file_path: str) -> list[dict[str, Any]]:
        """XML files don't have imports in the traditional sense."""
        return []

    def _extract_elements(self, element: ET.Element) -> dict[str, int]:
        """Extract element counts from XML."""
        elements = {}
        for elem in element.iter():
            tag = elem.tag
            elements[tag] = elements.get(tag, 0) + 1
        return elements

    def _extract_elements_as_symbols(self, element: ET.Element) -> list[dict[str, Any]]:
        """Extract XML elements as symbols."""
        symbols = []
        for elem in element.iter():
            symbols.append({
                'name': elem.tag,
                'type': 'xml_element',
                'attributes': len(elem.attrib)
            })
        return symbols

    def _extract_namespaces(self, element: ET.Element) -> list[str]:
        """Extract XML namespaces."""
        namespaces = set()
        for elem in element.iter():
            if '}' in elem.tag:
                namespace = elem.tag.split('}')[0][1:]
                namespaces.add(namespace)
        return list(namespaces)


class SQLParser(LanguageParser):
    """Parser for SQL files."""

    def parse_file(self, file_path: str) -> dict[str, Any]:
        """Parse a SQL file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                'file_path': file_path,
                'language': 'sql',
                'line_count': len(content.splitlines()),
                'symbols': self.extract_symbols(file_path),
                'imports': self.analyze_imports(file_path),
                'statements': self._extract_statements(content),
                'tables': self._extract_tables(content),
                'functions': self._extract_functions(content)
            }
        except (UnicodeDecodeError, IOError) as e:
            return {'error': str(e), 'file_path': file_path}

    def extract_symbols(self, file_path: str) -> list[dict[str, Any]]:
        """Extract SQL symbols (tables, functions, etc.)."""
        symbols = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract table names
            table_patterns = [
                r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)',
                r'FROM\s+(\w+)',
                r'JOIN\s+(\w+)',
                r'UPDATE\s+(\w+)',
                r'INSERT\s+INTO\s+(\w+)'
            ]

            for pattern in table_patterns:
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    symbols.append({
                        'name': match.group(1),
                        'type': 'table',
                        'line': content[:match.start()].count('\n') + 1
                    })

            # Extract function names
            func_pattern = r'CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+(\w+)'
            for match in re.finditer(func_pattern, content, re.IGNORECASE):
                symbols.append({
                    'name': match.group(1),
                    'type': 'function',
                    'line': content[:match.start()].count('\n') + 1
                })

        except (UnicodeDecodeError, IOError):
            pass

        return symbols

    def analyze_imports(self, file_path: str) -> list[dict[str, Any]]:
        """SQL files don't have imports."""
        return []

    def _extract_statements(self, content: str) -> dict[str, int]:
        """Extract SQL statement types."""
        statements = {}
        statement_patterns = {
            'SELECT': r'\bSELECT\b',
            'INSERT': r'\bINSERT\b',
            'UPDATE': r'\bUPDATE\b',
            'DELETE': r'\bDELETE\b',
            'CREATE': r'\bCREATE\b',
            'DROP': r'\bDROP\b',
            'ALTER': r'\bALTER\b'
        }

        for stmt_type, pattern in statement_patterns.items():
            count = len(re.findall(pattern, content, re.IGNORECASE))
            if count > 0:
                statements[stmt_type] = count

        return statements

    def _extract_tables(self, content: str) -> list[str]:
        """Extract table names from SQL."""
        tables = set()
        table_patterns = [
            r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)',
            r'FROM\s+(\w+)',
            r'JOIN\s+(\w+)',
            r'UPDATE\s+(\w+)',
            r'INSERT\s+INTO\s+(\w+)'
        ]

        for pattern in table_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            tables.update(matches)

        return list(tables)

    def _extract_functions(self, content: str) -> list[str]:
        """Extract function names from SQL."""
        func_pattern = r'CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+(\w+)'
        return re.findall(func_pattern, content, re.IGNORECASE)


class DockerfileParser(LanguageParser):
    """Parser for Dockerfile files."""

    def parse_file(self, file_path: str) -> dict[str, Any]:
        """Parse a Dockerfile."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                'file_path': file_path,
                'language': 'dockerfile',
                'line_count': len(content.splitlines()),
                'symbols': self.extract_symbols(file_path),
                'imports': self.analyze_imports(file_path),
                'instructions': self._extract_instructions(content),
                'base_images': self._extract_base_images(content),
                'ports': self._extract_ports(content)
            }
        except (UnicodeDecodeError, IOError) as e:
            return {'error': str(e), 'file_path': file_path}

    def extract_symbols(self, file_path: str) -> list[dict[str, Any]]:
        """Extract Dockerfile symbols."""
        return []  # Dockerfiles don't have traditional symbols

    def analyze_imports(self, file_path: str) -> list[dict[str, Any]]:
        """Analyze Dockerfile base images as imports."""
        imports = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            from_pattern = r'FROM\s+([^\s\n]+)'
            for match in re.finditer(from_pattern, content, re.IGNORECASE):
                imports.append({
                    'module': match.group(1),
                    'type': 'base_image',
                    'line': content[:match.start()].count('\n') + 1
                })

        except (UnicodeDecodeError, IOError):
            pass

        return imports

    def _extract_instructions(self, content: str) -> dict[str, int]:
        """Extract Dockerfile instruction counts."""
        instructions = {}
        instruction_pattern = r'^(\w+)\s+'
        
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                match = re.match(instruction_pattern, line)
                if match:
                    instruction = match.group(1).upper()
                    instructions[instruction] = instructions.get(instruction, 0) + 1

        return instructions

    def _extract_base_images(self, content: str) -> list[str]:
        """Extract base images from Dockerfile."""
        from_pattern = r'FROM\s+([^\s\n]+)'
        return re.findall(from_pattern, content, re.IGNORECASE)

    def _extract_ports(self, content: str) -> list[str]:
        """Extract exposed ports from Dockerfile."""
        expose_pattern = r'EXPOSE\s+([^\n]+)'
        ports = []
        for match in re.finditer(expose_pattern, content, re.IGNORECASE):
            ports.extend(match.group(1).split())
        return ports


class ShellParser(LanguageParser):
    """Parser for shell script files."""

    def parse_file(self, file_path: str) -> dict[str, Any]:
        """Parse a shell script file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                'file_path': file_path,
                'language': 'shell',
                'line_count': len(content.splitlines()),
                'symbols': self.extract_symbols(file_path),
                'imports': self.analyze_imports(file_path),
                'functions': self._extract_functions(content),
                'variables': self._extract_variables(content),
                'commands': self._extract_commands(content)
            }
        except (UnicodeDecodeError, IOError) as e:
            return {'error': str(e), 'file_path': file_path}

    def extract_symbols(self, file_path: str) -> list[dict[str, Any]]:
        """Extract shell script symbols."""
        symbols = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract functions
            func_pattern = r'^(\w+)\s*\(\s*\)\s*\{'
            for match in re.finditer(func_pattern, content, re.MULTILINE):
                symbols.append({
                    'name': match.group(1),
                    'type': 'function',
                    'line': content[:match.start()].count('\n') + 1
                })

            # Extract variables
            var_pattern = r'^(\w+)='
            for match in re.finditer(var_pattern, content, re.MULTILINE):
                symbols.append({
                    'name': match.group(1),
                    'type': 'variable',
                    'line': content[:match.start()].count('\n') + 1
                })

        except (UnicodeDecodeError, IOError):
            pass

        return symbols

    def analyze_imports(self, file_path: str) -> list[dict[str, Any]]:
        """Analyze shell script imports (source/.)."""
        imports = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Source statements
            source_patterns = [
                r'source\s+([^\s\n]+)',
                r'\.\s+([^\s\n]+)'
            ]

            for pattern in source_patterns:
                for match in re.finditer(pattern, content):
                    imports.append({
                        'module': match.group(1),
                        'type': 'source',
                        'line': content[:match.start()].count('\n') + 1
                    })

        except (UnicodeDecodeError, IOError):
            pass

        return imports

    def _extract_functions(self, content: str) -> list[str]:
        """Extract function names from shell script."""
        func_pattern = r'^(\w+)\s*\(\s*\)\s*\{'
        return re.findall(func_pattern, content, re.MULTILINE)

    def _extract_variables(self, content: str) -> list[str]:
        """Extract variable names from shell script."""
        var_pattern = r'^(\w+)='
        return re.findall(var_pattern, content, re.MULTILINE)

    def _extract_commands(self, content: str) -> dict[str, int]:
        """Extract common command usage."""
        commands = {}
        common_commands = [
            'echo', 'cd', 'ls', 'cp', 'mv', 'rm', 'mkdir', 'chmod', 'chown',
            'grep', 'sed', 'awk', 'sort', 'uniq', 'head', 'tail', 'cat',
            'git', 'npm', 'pip', 'docker', 'kubectl'
        ]

        for command in common_commands:
            pattern = rf'\b{command}\b'
            count = len(re.findall(pattern, content))
            if count > 0:
                commands[command] = count

        return commands