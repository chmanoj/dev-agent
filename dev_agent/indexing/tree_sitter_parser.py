"""Tree-sitter based AST parser for code analysis."""

import ast
import os
import re
from pathlib import Path
from typing import Any

from ..models.indexing import (
    ASTIndex,
    ClassDef,
    FunctionDef,
    Import,
    SymbolInfo,
)

# Use Python's built-in AST as fallback when tree-sitter isn't available
try:
    import tree_sitter
    from tree_sitter import Language, Node, Parser

    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


class TreeSitterParser:
    """High-performance AST parser using Python's AST module with Tree-sitter fallback."""

    def __init__(self):
        """Initialize the parser with support for Python language."""
        self.supported_languages = ["python", "javascript", "typescript"]
        self.parsers: dict[str, Any] = {}
        self.languages: dict[str, Any] = {}

        # Always use Python's AST for Python files as it's more reliable
        self._initialize_python_parser()

    def _initialize_python_parser(self) -> None:
        """Initialize Python AST parser."""
        # Python AST is built-in, no initialization needed
        pass

    def parse_file(self, file_path: str, language: str = "python") -> ast.AST | None:
        """Parse a single file into an AST.

        Args:
            file_path: Path to the file to parse
            language: Programming language of the file

        Returns:
            AST object or None if parsing fails
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            if language == "python":
                return ast.parse(content, filename=file_path)
            else:
                # For non-Python files, return a simple mock AST
                # In a full implementation, you'd use tree-sitter here
                return self._create_mock_ast(content, file_path, language)

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None

    def _create_mock_ast(self, content: str, file_path: str, language: str) -> Any:
        """Create a mock AST for non-Python files."""

        # Simple mock AST that can be extended
        class MockAST:
            def __init__(self, content: str, file_path: str, language: str):
                self.content = content
                self.file_path = file_path
                self.language = language
                self.functions = self._extract_functions(content, language)
                self.classes = self._extract_classes(content, language)
                self.imports = self._extract_imports(content, language)

            def _extract_functions(self, content: str, language: str) -> list[str]:
                if language == "javascript" or language == "typescript":
                    # Simple regex for JS/TS functions
                    pattern = r"function\s+(\w+)\s*\("
                    return re.findall(pattern, content)
                return []

            def _extract_classes(self, content: str, language: str) -> list[str]:
                if language == "javascript" or language == "typescript":
                    pattern = r"class\s+(\w+)"
                    return re.findall(pattern, content)
                return []

            def _extract_imports(self, content: str, language: str) -> list[str]:
                if language == "javascript" or language == "typescript":
                    pattern = r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]'
                    return re.findall(pattern, content)
                return []

        return MockAST(content, file_path, language)

    def _extract_symbols_from_python_ast(
        self, ast_obj: ast.AST, file_path: str = ""
    ) -> list[SymbolInfo]:
        """Extract symbols from an AST.

        Args:
            ast_obj: AST object to analyze
            file_path: Path to the source file

        Returns:
            List of SymbolInfo objects
        """
        symbols = []

        if isinstance(ast_obj, ast.AST):
            # Python AST
            for node in ast.walk(ast_obj):
                if isinstance(node, ast.FunctionDef):
                    symbol = SymbolInfo(
                        name=node.name,
                        symbol_type="function",
                        file_path=file_path,
                        line_number=getattr(node, "lineno", 0),
                        scope="global",  # Could be enhanced to detect actual scope
                        docstring=ast.get_docstring(node) or "",
                    )
                    symbols.append(symbol)

                elif isinstance(node, ast.ClassDef):
                    symbol = SymbolInfo(
                        name=node.name,
                        symbol_type="class",
                        file_path=file_path,
                        line_number=getattr(node, "lineno", 0),
                        scope="global",  # Could be enhanced to detect actual scope
                        docstring=ast.get_docstring(node) or "",
                    )
                    symbols.append(symbol)

                elif isinstance(node, ast.Assign):
                    # Extract variable assignments
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            symbol = SymbolInfo(
                                name=target.id,
                                symbol_type="variable",
                                file_path=file_path,
                                line_number=getattr(node, "lineno", 0),
                                scope="global",
                                docstring="",
                            )
                            symbols.append(symbol)

                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    # Variable assignments
                    symbol = SymbolInfo(
                        name=node.id,
                        symbol_type="variable",
                        file_path=file_path,
                        line_number=getattr(node, "lineno", 0),
                        scope="global",
                        docstring="",
                    )
                    symbols.append(symbol)

                elif isinstance(node, ast.Import):
                    # Import statements
                    for alias in node.names:
                        symbol = SymbolInfo(
                            name=alias.name,
                            symbol_type="import",
                            file_path=file_path,
                            line_number=getattr(node, "lineno", 0),
                            scope="global",
                            docstring="",
                        )
                        symbols.append(symbol)

                elif isinstance(node, ast.ImportFrom):
                    # From import statements
                    module = node.module or ""
                    for alias in node.names:
                        symbol = SymbolInfo(
                            name=f"{module}.{alias.name}" if module else alias.name,
                            symbol_type="import",
                            file_path=file_path,
                            line_number=getattr(node, "lineno", 0),
                            scope="global",
                            docstring="",
                        )
                        symbols.append(symbol)
        # Mock AST for other languages
        elif hasattr(ast_obj, "functions"):
            for func_name in ast_obj.functions:
                symbol = SymbolInfo(
                    name=func_name,
                    symbol_type="function",
                    file_path=file_path,
                    line_number=0,
                    scope="global",
                    docstring="",
                )
                symbols.append(symbol)

        return symbols

    def extract_symbols(self, ast_obj: Any, file_path: str = "") -> list[SymbolInfo]:
        """Extract symbols from an AST.

        Args:
            ast_obj: AST object to analyze (Python ast.AST or Tree-sitter)
            file_path: Path to the source file

        Returns:
            List of SymbolInfo objects
        """
        if isinstance(ast_obj, ast.AST):
            return self._extract_symbols_from_python_ast(ast_obj, file_path)
        else:
            return self._extract_symbols_from_tree_sitter(ast_obj, file_path)

    def get_function_definitions(
        self, ast_obj: ast.AST, file_path: str = ""
    ) -> list[FunctionDef]:
        """Extract function definitions from an AST.

        Args:
            ast_obj: AST object to analyze
            file_path: Path to the source file

        Returns:
            List of FunctionDef objects
        """
        functions = []

        if isinstance(ast_obj, ast.AST):
            for node in ast.walk(ast_obj):
                if isinstance(node, ast.FunctionDef):
                    try:
                        # Extract parameters
                        params = []
                        for arg in node.args.args:
                            params.append(arg.arg)

                        # Extract return type annotation if available
                        return_type = ""
                        if node.returns:
                            if isinstance(node.returns, ast.Name):
                                return_type = node.returns.id
                            elif isinstance(node.returns, ast.Constant):
                                return_type = str(node.returns.value)

                        func_def = FunctionDef(
                            name=node.name,
                            parameters=params,
                            return_type=return_type,
                            docstring=ast.get_docstring(node) or "",
                            start_line=getattr(node, "lineno", 0),
                            end_line=getattr(node, "end_lineno", 0)
                            or getattr(node, "lineno", 0),
                            file_path=file_path,
                        )
                        functions.append(func_def)
                    except Exception as e:
                        print(f"Error processing function {node.name}: {e}")
                        continue

        return functions

    def get_class_definitions(
        self, ast_obj: ast.AST, file_path: str = ""
    ) -> list[ClassDef]:
        """Extract class definitions from an AST.

        Args:
            ast_obj: AST object to analyze
            file_path: Path to the source file

        Returns:
            List of ClassDef objects
        """
        classes = []

        if isinstance(ast_obj, ast.AST):
            for node in ast.walk(ast_obj):
                if isinstance(node, ast.ClassDef):
                    # Extract base classes
                    bases = []
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            bases.append(base.id)
                        elif isinstance(base, ast.Attribute):
                            bases.append(f"{base.value.id}.{base.attr}")

                    # Extract methods as FunctionDef objects
                    methods = []
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            # Create FunctionDef for method
                            method_params = [arg.arg for arg in item.args.args]
                            method_def = FunctionDef(
                                name=item.name,
                                parameters=method_params,
                                return_type="",
                                docstring=ast.get_docstring(item) or "",
                                start_line=getattr(item, "lineno", 0),
                                end_line=getattr(item, "end_lineno", 0)
                                or getattr(item, "lineno", 0),
                                file_path=file_path,
                            )
                            methods.append(method_def)

                    # Extract attributes (simplified)
                    attributes = []
                    for item in node.body:
                        if isinstance(item, ast.Assign):
                            for target in item.targets:
                                if isinstance(target, ast.Name):
                                    attributes.append(target.id)

                    class_def = ClassDef(
                        name=node.name,
                        base_classes=bases,
                        methods=methods,
                        attributes=attributes,
                        docstring=ast.get_docstring(node) or "",
                        start_line=getattr(node, "lineno", 0),
                        end_line=getattr(node, "end_lineno", 0)
                        or getattr(node, "lineno", 0),
                        file_path=file_path,
                    )
                    classes.append(class_def)

        return classes

    def _extract_imports_from_python_ast(self, ast_obj: ast.AST, file_path: str = "") -> list[Import]:
        """Extract import statements from an AST.

        Args:
            ast_obj: AST object to analyze
            file_path: Path to the source file

        Returns:
            List of Import objects
        """
        imports = []

        if isinstance(ast_obj, ast.AST):
            for node in ast.walk(ast_obj):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        import_obj = Import(
                            module=alias.name,
                            names=[],
                            alias=alias.asname or "",
                            line_number=getattr(node, "lineno", 0),
                            file_path=file_path,
                        )
                        imports.append(import_obj)

                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    # Group all names from the same import statement
                    names = []
                    aliases = []
                    for alias in node.names:
                        names.append(alias.name)
                        if alias.asname:
                            aliases.append(alias.asname)

                    import_obj = Import(
                        module=module,
                        names=names,
                        alias=", ".join(aliases) if aliases else "",
                        line_number=getattr(node, "lineno", 0),
                        file_path=file_path,
                    )
                    imports.append(import_obj)

        return imports

    def extract_imports(self, ast_obj: Any, file_path: str = "") -> list[Import]:
        """Extract import statements from an AST.

        Args:
            ast_obj: AST object to analyze (Python ast.AST or Tree-sitter)
            file_path: Path to the source file

        Returns:
            List of Import objects
        """
        if isinstance(ast_obj, ast.AST):
            return self._extract_imports_from_python_ast(ast_obj, file_path)
        else:
            return self._extract_imports_from_tree_sitter(ast_obj, file_path)

    def _get_decorator_name(self, decorator_node: ast.AST) -> str:
        """Extract decorator name from AST node."""
        if isinstance(decorator_node, ast.Name):
            return decorator_node.id
        elif isinstance(decorator_node, ast.Attribute):
            return f"{decorator_node.value.id}.{decorator_node.attr}"
        elif isinstance(decorator_node, ast.Call):
            if isinstance(decorator_node.func, ast.Name):
                return decorator_node.func.id
            elif isinstance(decorator_node.func, ast.Attribute):
                return f"{decorator_node.func.value.id}.{decorator_node.func.attr}"
        return "unknown_decorator"
        """Parse a single file and return its AST.
        
        Args:
            file_path: Path to the file to parse
            language: Programming language of the file
            
        Returns:
            AST object or None if parsing fails
        """
        if not TREE_SITTER_AVAILABLE:
            return self._mock_parse_file(file_path, language)

        if language not in self.supported_languages:
            raise ValueError(f"Unsupported language: {language}")

        try:
            with open(file_path, encoding="utf-8") as f:
                source_code = f.read()

            parser = self.parsers.get(language)
            if not parser:
                return None

            # Parse the source code
            tree = parser.parse(bytes(source_code, "utf8"))
            return tree

        except Exception as e:
            print(f"Error parsing file {file_path}: {e}")
            return None

    def _mock_parse_file(self, file_path: str, language: str) -> dict[str, Any] | None:
        """Mock implementation for testing without tree-sitter."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Simple mock AST structure
            return {
                "type": "module",
                "content": content,
                "file_path": file_path,
                "language": language,
            }
        except Exception:
            return None

    def _extract_symbols_from_tree_sitter(self, ast: Any, file_path: str) -> list[SymbolInfo]:
        """Extract all symbols (functions, classes, variables) from AST.

        Args:
            ast: The AST to analyze
            file_path: Path to the source file

        Returns:
            List of SymbolInfo objects
        """
        if not TREE_SITTER_AVAILABLE:
            return self._mock_extract_symbols(ast, file_path)

        symbols = []

        if ast and hasattr(ast, "root_node"):
            self._traverse_node_for_symbols(ast.root_node, file_path, symbols)

        return symbols

    def _mock_extract_symbols(self, ast: Any, file_path: str) -> list[SymbolInfo]:
        """Mock symbol extraction for testing."""
        symbols = []

        if not ast or not isinstance(ast, dict):
            return symbols

        content = ast.get("content", "")
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            line = line.strip()

            # Simple pattern matching for Python symbols
            if line.startswith("def "):
                func_name = line.split("(")[0].replace("def ", "").strip()
                symbols.append(
                    SymbolInfo(
                        name=func_name,
                        symbol_type="function",
                        file_path=file_path,
                        line_number=i,
                        scope="module",
                        signature=line,
                    )
                )
            elif line.startswith("class "):
                class_name = (
                    line.split("(")[0].split(":")[0].replace("class ", "").strip()
                )
                symbols.append(
                    SymbolInfo(
                        name=class_name,
                        symbol_type="class",
                        file_path=file_path,
                        line_number=i,
                        scope="module",
                    )
                )
            elif line.startswith("import ") or line.startswith("from "):
                symbols.append(
                    SymbolInfo(
                        name=line.split()[1] if len(line.split()) > 1 else "unknown",
                        symbol_type="import",
                        file_path=file_path,
                        line_number=i,
                        scope="module",
                    )
                )

        return symbols

    def _traverse_node_for_symbols(
        self, node: Any, file_path: str, symbols: list[SymbolInfo]
    ) -> None:
        """Recursively traverse AST node to extract symbols."""
        # This method is for tree-sitter integration which is not fully implemented
        # For now, we use Python's AST module which is handled in extract_symbols
        pass

    def _get_function_definitions_tree_sitter(
        self, ast: Any, file_path: str
    ) -> list[FunctionDef]:
        """Extract function definitions from tree-sitter AST (not used)."""
        # This method was for tree-sitter integration which is not fully implemented
        return []

        return functions

    def _mock_get_functions(self, ast: Any, file_path: str) -> list[FunctionDef]:
        """Mock function extraction for testing."""
        functions = []

        if not ast or not isinstance(ast, dict):
            return functions

        content = ast.get("content", "")
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            line = line.strip()
            if line.startswith("def "):
                # Extract function name and parameters
                func_signature = line.replace("def ", "").split(":")[0]
                if "(" in func_signature:
                    func_name = func_signature.split("(")[0].strip()
                    params_str = func_signature.split("(")[1].split(")")[0]
                    parameters = [
                        p.split("=")[0].strip()
                        for p in params_str.split(",")
                        if p.strip()
                    ]
                else:
                    func_name = func_signature.strip()
                    parameters = []

                # Look for docstring
                docstring = None
                if i < len(lines):
                    next_lines = lines[i : i + 3]
                    for next_line in next_lines:
                        if '"""' in next_line or "'''" in next_line:
                            docstring = (
                                next_line.strip().replace('"""', "").replace("'''", "")
                            )
                            break

                functions.append(
                    FunctionDef(
                        name=func_name,
                        parameters=parameters,
                        return_type=None,
                        docstring=docstring,
                        file_path=file_path,
                        start_line=i,
                        end_line=i,  # Simplified for mock
                    )
                )

        return functions

    def _traverse_node_for_functions(
        self, node: Any, file_path: str, functions: list[FunctionDef]
    ) -> None:
        """Recursively traverse AST node to extract function definitions."""
        # Tree-sitter specific implementation - not used with Python AST
        pass

    def _extract_function_info(self, node: Any, file_path: str) -> FunctionDef | None:
        """Extract detailed function information from a function node."""
        # Tree-sitter specific implementation - not used with Python AST
        return None

    def _get_class_definitions_tree_sitter(
        self, ast: Any, file_path: str
    ) -> list[ClassDef]:
        """Extract class definitions from tree-sitter AST (not used)."""
        # This method was for tree-sitter integration which is not fully implemented
        return []

    def _mock_get_classes(self, ast: Any, file_path: str) -> list[ClassDef]:
        """Mock class extraction for testing."""
        classes = []

        if not ast or not isinstance(ast, dict):
            return classes

        content = ast.get("content", "")
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            line = line.strip()
            if line.startswith("class "):
                # Extract class name and base classes
                class_signature = line.replace("class ", "").split(":")[0]
                if "(" in class_signature:
                    class_name = class_signature.split("(")[0].strip()
                    bases_str = class_signature.split("(")[1].split(")")[0]
                    base_classes = [
                        b.strip() for b in bases_str.split(",") if b.strip()
                    ]
                else:
                    class_name = class_signature.strip()
                    base_classes = []

                # Look for docstring
                docstring = None
                if i < len(lines):
                    next_lines = lines[i : i + 3]
                    for next_line in next_lines:
                        if '"""' in next_line or "'''" in next_line:
                            docstring = (
                                next_line.strip().replace('"""', "").replace("'''", "")
                            )
                            break

                classes.append(
                    ClassDef(
                        name=class_name,
                        base_classes=base_classes,
                        methods=[],  # Simplified for mock
                        attributes=[],  # Simplified for mock
                        docstring=docstring,
                        file_path=file_path,
                        start_line=i,
                        end_line=i,  # Simplified for mock
                    )
                )

        return classes

    def _traverse_node_for_classes(
        self, node: Any, file_path: str, classes: list[ClassDef]
    ) -> None:
        """Recursively traverse AST node to extract class definitions."""
        # Tree-sitter specific implementation - not used with Python AST
        pass

    def _extract_class_info(self, node: Any, file_path: str) -> ClassDef | None:
        """Extract detailed class information from a class node."""
        # Tree-sitter specific implementation - not used with Python AST
        return None

    def _extract_imports_from_tree_sitter(self, ast: Any, file_path: str) -> list[Import]:
        """Extract import statements from AST.

        Args:
            ast: The AST to analyze
            file_path: Path to the source file

        Returns:
            List of Import objects
        """
        if not TREE_SITTER_AVAILABLE:
            return self._mock_extract_imports(ast, file_path)

        imports = []

        if ast and hasattr(ast, "root_node"):
            self._traverse_node_for_imports(ast.root_node, file_path, imports)

        return imports

    def _mock_extract_imports(self, ast: Any, file_path: str) -> list[Import]:
        """Mock import extraction for testing."""
        imports = []

        if not ast or not isinstance(ast, dict):
            return imports

        content = ast.get("content", "")
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            line = line.strip()

            if line.startswith("import "):
                # Handle "import module" or "import module as alias"
                parts = line.replace("import ", "").split(" as ")
                module = parts[0].strip()
                alias = parts[1].strip() if len(parts) > 1 else None

                imports.append(
                    Import(
                        module=module,
                        names=[],
                        alias=alias,
                        file_path=file_path,
                        line_number=i,
                    )
                )

            elif line.startswith("from "):
                # Handle "from module import name1, name2"
                if " import " in line:
                    module_part = line.split(" import ")[0].replace("from ", "").strip()
                    names_part = line.split(" import ")[1].strip()
                    names = [n.strip() for n in names_part.split(",")]

                    imports.append(
                        Import(
                            module=module_part,
                            names=names,
                            alias=None,
                            file_path=file_path,
                            line_number=i,
                        )
                    )

        return imports

    def _traverse_node_for_imports(
        self, node: Any, file_path: str, imports: list[Import]
    ) -> None:
        """Recursively traverse AST node to extract import statements."""
        # Tree-sitter specific implementation - not used with Python AST
        pass

    def _extract_import_info(self, node: Any, file_path: str) -> Import | None:
        """Extract detailed import information from an import node."""
        # Tree-sitter specific implementation - not used with Python AST
        return None

    def create_symbol_map(self, file_paths: list[str]) -> dict[str, SymbolInfo]:
        """Create a comprehensive symbol map for multiple files.

        Args:
            file_paths: List of file paths to analyze

        Returns:
            Dictionary mapping symbol names to SymbolInfo objects
        """
        symbol_map = {}

        for file_path in file_paths:
            if not os.path.exists(file_path):
                continue

            # Determine language from file extension
            language = self._detect_language(file_path)
            if language not in self.supported_languages:
                continue

            # Parse the file
            ast = self.parse_file(file_path, language)
            if not ast:
                continue

            # Extract symbols
            symbols = self.extract_symbols(ast, file_path)

            # Add to symbol map
            for symbol in symbols:
                # Create unique key for symbol
                key = f"{symbol.file_path}:{symbol.name}"
                symbol_map[key] = symbol

        return symbol_map

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext = Path(file_path).suffix.lower()

        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".h": "c",
            ".hpp": "cpp",
        }

        return language_map.get(ext, "unknown")

    def analyze_code_structure(self, file_paths: list[str]) -> ASTIndex:
        """Analyze code structure across multiple files and create comprehensive index.

        Args:
            file_paths: List of file paths to analyze

        Returns:
            ASTIndex containing all extracted information
        """
        functions = {}
        classes = {}
        imports = []
        symbols = {}
        file_metadata = {}

        for file_path in file_paths:
            if not os.path.exists(file_path):
                continue

            # Determine language
            language = self._detect_language(file_path)
            if language not in self.supported_languages:
                continue

            # Parse the file
            ast = self.parse_file(file_path, language)
            if not ast:
                continue

            # Extract all information
            file_functions = self.get_function_definitions(ast, file_path)
            file_classes = self.get_class_definitions(ast, file_path)
            file_imports = self.extract_imports(ast, file_path)
            file_symbols = self.extract_symbols(ast, file_path)

            # Add to collections
            for func in file_functions:
                key = f"{file_path}:{func.name}"
                functions[key] = func

            for cls in file_classes:
                key = f"{file_path}:{cls.name}"
                classes[key] = cls

            imports.extend(file_imports)

            for symbol in file_symbols:
                key = f"{file_path}:{symbol.name}"
                symbols[key] = symbol

            # Store file metadata
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                file_metadata[file_path] = {
                    "language": language,
                    "line_count": len(content.split("\n")),
                    "char_count": len(content),
                    "function_count": len(file_functions),
                    "class_count": len(file_classes),
                    "import_count": len(file_imports),
                }
            except Exception as e:
                file_metadata[file_path] = {"language": language, "error": str(e)}

        return ASTIndex(
            functions=functions,
            classes=classes,
            imports=imports,
            symbols=symbols,
            file_metadata=file_metadata,
        )
