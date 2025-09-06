"""Tree-sitter based AST parser for code analysis."""

import os
from typing import List, Dict, Optional, Any, Set
from pathlib import Path

from ..models.indexing import (
    ASTIndex, FunctionDef, ClassDef, Import, SymbolInfo, CodeChunk
)

try:
    import tree_sitter
    from tree_sitter import Language, Parser, Node
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    # Mock classes for testing without tree-sitter
    class Language:
        pass
    class Parser:
        pass
    class Node:
        pass


class TreeSitterParser:
    """High-performance AST parser using Tree-sitter for multiple languages."""
    
    def __init__(self):
        """Initialize the parser with support for Python language."""
        self.supported_languages = ['python']
        self.parsers: Dict[str, Any] = {}
        self.languages: Dict[str, Any] = {}
        
        if TREE_SITTER_AVAILABLE:
            self._initialize_parsers()
    
    def _initialize_parsers(self) -> None:
        """Initialize Tree-sitter parsers for supported languages."""
        try:
            # Try to load Python language
            # Note: In a real implementation, you would need to build the language
            # For now, we'll create a mock implementation that can be extended
            python_parser = Parser()
            self.parsers['python'] = python_parser
        except Exception as e:
            # Graceful fallback if tree-sitter languages aren't available
            print(f"Warning: Could not initialize Tree-sitter parser: {e}")
    
    def parse_file(self, file_path: str, language: str = 'python') -> Optional['AST']:
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
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            parser = self.parsers.get(language)
            if not parser:
                return None
                
            # Parse the source code
            tree = parser.parse(bytes(source_code, 'utf8'))
            return tree
            
        except Exception as e:
            print(f"Error parsing file {file_path}: {e}")
            return None
    
    def _mock_parse_file(self, file_path: str, language: str) -> Optional[Dict[str, Any]]:
        """Mock implementation for testing without tree-sitter."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple mock AST structure
            return {
                'type': 'module',
                'content': content,
                'file_path': file_path,
                'language': language
            }
        except Exception:
            return None
    
    def extract_symbols(self, ast: Any, file_path: str) -> List[SymbolInfo]:
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
        
        if ast and hasattr(ast, 'root_node'):
            self._traverse_node_for_symbols(ast.root_node, file_path, symbols)
        
        return symbols
    
    def _mock_extract_symbols(self, ast: Any, file_path: str) -> List[SymbolInfo]:
        """Mock symbol extraction for testing."""
        symbols = []
        
        if not ast or not isinstance(ast, dict):
            return symbols
            
        content = ast.get('content', '')
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Simple pattern matching for Python symbols
            if line.startswith('def '):
                func_name = line.split('(')[0].replace('def ', '').strip()
                symbols.append(SymbolInfo(
                    name=func_name,
                    symbol_type='function',
                    file_path=file_path,
                    line_number=i,
                    scope='module',
                    signature=line
                ))
            elif line.startswith('class '):
                class_name = line.split('(')[0].split(':')[0].replace('class ', '').strip()
                symbols.append(SymbolInfo(
                    name=class_name,
                    symbol_type='class',
                    file_path=file_path,
                    line_number=i,
                    scope='module'
                ))
            elif line.startswith('import ') or line.startswith('from '):
                symbols.append(SymbolInfo(
                    name=line.split()[1] if len(line.split()) > 1 else 'unknown',
                    symbol_type='import',
                    file_path=file_path,
                    line_number=i,
                    scope='module'
                ))
        
        return symbols
    
    def _traverse_node_for_symbols(self, node: Node, file_path: str, symbols: List[SymbolInfo]) -> None:
        """Recursively traverse AST node to extract symbols."""
        if not node:
            return
            
        # Extract different types of symbols based on node type
        if node.type == 'function_definition':
            func_info = self._extract_function_info(node, file_path)
            if func_info:
                symbols.append(SymbolInfo(
                    name=func_info.name,
                    symbol_type='function',
                    file_path=file_path,
                    line_number=func_info.start_line,
                    scope='module',
                    signature=f"def {func_info.name}({', '.join(func_info.parameters)})",
                    docstring=func_info.docstring
                ))
        
        elif node.type == 'class_definition':
            class_info = self._extract_class_info(node, file_path)
            if class_info:
                symbols.append(SymbolInfo(
                    name=class_info.name,
                    symbol_type='class',
                    file_path=file_path,
                    line_number=class_info.start_line,
                    scope='module',
                    docstring=class_info.docstring
                ))
        
        # Recursively process child nodes
        for child in node.children:
            self._traverse_node_for_symbols(child, file_path, symbols)
    
    def get_function_definitions(self, ast: Any, file_path: str) -> List[FunctionDef]:
        """Extract function definitions from AST.
        
        Args:
            ast: The AST to analyze
            file_path: Path to the source file
            
        Returns:
            List of FunctionDef objects
        """
        if not TREE_SITTER_AVAILABLE:
            return self._mock_get_functions(ast, file_path)
            
        functions = []
        
        if ast and hasattr(ast, 'root_node'):
            self._traverse_node_for_functions(ast.root_node, file_path, functions)
        
        return functions
    
    def _mock_get_functions(self, ast: Any, file_path: str) -> List[FunctionDef]:
        """Mock function extraction for testing."""
        functions = []
        
        if not ast or not isinstance(ast, dict):
            return functions
            
        content = ast.get('content', '')
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if line.startswith('def '):
                # Extract function name and parameters
                func_signature = line.replace('def ', '').split(':')[0]
                if '(' in func_signature:
                    func_name = func_signature.split('(')[0].strip()
                    params_str = func_signature.split('(')[1].split(')')[0]
                    parameters = [p.split('=')[0].strip() for p in params_str.split(',') if p.strip()]
                else:
                    func_name = func_signature.strip()
                    parameters = []
                
                # Look for docstring
                docstring = None
                if i < len(lines):
                    next_lines = lines[i:i+3]
                    for next_line in next_lines:
                        if '"""' in next_line or "'''" in next_line:
                            docstring = next_line.strip().replace('"""', '').replace("'''", '')
                            break
                
                functions.append(FunctionDef(
                    name=func_name,
                    parameters=parameters,
                    return_type=None,
                    docstring=docstring,
                    file_path=file_path,
                    start_line=i,
                    end_line=i  # Simplified for mock
                ))
        
        return functions
    
    def _traverse_node_for_functions(self, node: Node, file_path: str, functions: List[FunctionDef]) -> None:
        """Recursively traverse AST node to extract function definitions."""
        if not node:
            return
            
        if node.type == 'function_definition':
            func_info = self._extract_function_info(node, file_path)
            if func_info:
                functions.append(func_info)
        
        # Recursively process child nodes
        for child in node.children:
            self._traverse_node_for_functions(child, file_path, functions)
    
    def _extract_function_info(self, node: Node, file_path: str) -> Optional[FunctionDef]:
        """Extract detailed function information from a function node."""
        try:
            # Extract function name
            name_node = None
            for child in node.children:
                if child.type == 'identifier':
                    name_node = child
                    break
            
            if not name_node:
                return None
                
            func_name = name_node.text.decode('utf-8')
            
            # Extract parameters
            parameters = []
            param_node = None
            for child in node.children:
                if child.type == 'parameters':
                    param_node = child
                    break
            
            if param_node:
                for param_child in param_node.children:
                    if param_child.type == 'identifier':
                        parameters.append(param_child.text.decode('utf-8'))
            
            # Extract docstring
            docstring = None
            for child in node.children:
                if child.type == 'block':
                    for block_child in child.children:
                        if block_child.type == 'expression_statement':
                            for expr_child in block_child.children:
                                if expr_child.type == 'string':
                                    docstring = expr_child.text.decode('utf-8').strip('"\'')
                                    break
                            break
                    break
            
            return FunctionDef(
                name=func_name,
                parameters=parameters,
                return_type=None,  # TODO: Extract return type annotation
                docstring=docstring,
                file_path=file_path,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1
            )
            
        except Exception as e:
            print(f"Error extracting function info: {e}")
            return None
    
    def get_class_definitions(self, ast: Any, file_path: str) -> List[ClassDef]:
        """Extract class definitions from AST.
        
        Args:
            ast: The AST to analyze
            file_path: Path to the source file
            
        Returns:
            List of ClassDef objects
        """
        if not TREE_SITTER_AVAILABLE:
            return self._mock_get_classes(ast, file_path)
            
        classes = []
        
        if ast and hasattr(ast, 'root_node'):
            self._traverse_node_for_classes(ast.root_node, file_path, classes)
        
        return classes
    
    def _mock_get_classes(self, ast: Any, file_path: str) -> List[ClassDef]:
        """Mock class extraction for testing."""
        classes = []
        
        if not ast or not isinstance(ast, dict):
            return classes
            
        content = ast.get('content', '')
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if line.startswith('class '):
                # Extract class name and base classes
                class_signature = line.replace('class ', '').split(':')[0]
                if '(' in class_signature:
                    class_name = class_signature.split('(')[0].strip()
                    bases_str = class_signature.split('(')[1].split(')')[0]
                    base_classes = [b.strip() for b in bases_str.split(',') if b.strip()]
                else:
                    class_name = class_signature.strip()
                    base_classes = []
                
                # Look for docstring
                docstring = None
                if i < len(lines):
                    next_lines = lines[i:i+3]
                    for next_line in next_lines:
                        if '"""' in next_line or "'''" in next_line:
                            docstring = next_line.strip().replace('"""', '').replace("'''", '')
                            break
                
                classes.append(ClassDef(
                    name=class_name,
                    base_classes=base_classes,
                    methods=[],  # Simplified for mock
                    attributes=[],  # Simplified for mock
                    docstring=docstring,
                    file_path=file_path,
                    start_line=i,
                    end_line=i  # Simplified for mock
                ))
        
        return classes
    
    def _traverse_node_for_classes(self, node: Node, file_path: str, classes: List[ClassDef]) -> None:
        """Recursively traverse AST node to extract class definitions."""
        if not node:
            return
            
        if node.type == 'class_definition':
            class_info = self._extract_class_info(node, file_path)
            if class_info:
                classes.append(class_info)
        
        # Recursively process child nodes
        for child in node.children:
            self._traverse_node_for_classes(child, file_path, classes)
    
    def _extract_class_info(self, node: Node, file_path: str) -> Optional[ClassDef]:
        """Extract detailed class information from a class node."""
        try:
            # Extract class name
            name_node = None
            for child in node.children:
                if child.type == 'identifier':
                    name_node = child
                    break
            
            if not name_node:
                return None
                
            class_name = name_node.text.decode('utf-8')
            
            # Extract base classes
            base_classes = []
            for child in node.children:
                if child.type == 'argument_list':
                    for arg_child in child.children:
                        if arg_child.type == 'identifier':
                            base_classes.append(arg_child.text.decode('utf-8'))
            
            # Extract methods
            methods = []
            for child in node.children:
                if child.type == 'block':
                    self._traverse_node_for_functions(child, file_path, methods)
            
            # Extract docstring
            docstring = None
            for child in node.children:
                if child.type == 'block':
                    for block_child in child.children:
                        if block_child.type == 'expression_statement':
                            for expr_child in block_child.children:
                                if expr_child.type == 'string':
                                    docstring = expr_child.text.decode('utf-8').strip('"\'')
                                    break
                            break
                    break
            
            return ClassDef(
                name=class_name,
                base_classes=base_classes,
                methods=methods,
                attributes=[],  # TODO: Extract class attributes
                docstring=docstring,
                file_path=file_path,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1
            )
            
        except Exception as e:
            print(f"Error extracting class info: {e}")
            return None
    
    def extract_imports(self, ast: Any, file_path: str) -> List[Import]:
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
        
        if ast and hasattr(ast, 'root_node'):
            self._traverse_node_for_imports(ast.root_node, file_path, imports)
        
        return imports
    
    def _mock_extract_imports(self, ast: Any, file_path: str) -> List[Import]:
        """Mock import extraction for testing."""
        imports = []
        
        if not ast or not isinstance(ast, dict):
            return imports
            
        content = ast.get('content', '')
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            if line.startswith('import '):
                # Handle "import module" or "import module as alias"
                parts = line.replace('import ', '').split(' as ')
                module = parts[0].strip()
                alias = parts[1].strip() if len(parts) > 1 else None
                
                imports.append(Import(
                    module=module,
                    names=[],
                    alias=alias,
                    file_path=file_path,
                    line_number=i
                ))
            
            elif line.startswith('from '):
                # Handle "from module import name1, name2"
                if ' import ' in line:
                    module_part = line.split(' import ')[0].replace('from ', '').strip()
                    names_part = line.split(' import ')[1].strip()
                    names = [n.strip() for n in names_part.split(',')]
                    
                    imports.append(Import(
                        module=module_part,
                        names=names,
                        alias=None,
                        file_path=file_path,
                        line_number=i
                    ))
        
        return imports
    
    def _traverse_node_for_imports(self, node: Node, file_path: str, imports: List[Import]) -> None:
        """Recursively traverse AST node to extract import statements."""
        if not node:
            return
            
        if node.type in ['import_statement', 'import_from_statement']:
            import_info = self._extract_import_info(node, file_path)
            if import_info:
                imports.append(import_info)
        
        # Recursively process child nodes
        for child in node.children:
            self._traverse_node_for_imports(child, file_path, imports)
    
    def _extract_import_info(self, node: Node, file_path: str) -> Optional[Import]:
        """Extract detailed import information from an import node."""
        try:
            if node.type == 'import_statement':
                # Handle "import module" statements
                module_name = None
                alias = None
                
                for child in node.children:
                    if child.type == 'dotted_name':
                        module_name = child.text.decode('utf-8')
                    elif child.type == 'aliased_import':
                        # Handle "import module as alias"
                        for alias_child in child.children:
                            if alias_child.type == 'dotted_name':
                                module_name = alias_child.text.decode('utf-8')
                            elif alias_child.type == 'identifier':
                                alias = alias_child.text.decode('utf-8')
                
                if module_name:
                    return Import(
                        module=module_name,
                        names=[],
                        alias=alias,
                        file_path=file_path,
                        line_number=node.start_point[0] + 1
                    )
            
            elif node.type == 'import_from_statement':
                # Handle "from module import name1, name2" statements
                module_name = None
                names = []
                
                for child in node.children:
                    if child.type == 'dotted_name':
                        module_name = child.text.decode('utf-8')
                    elif child.type == 'import_list':
                        for import_child in child.children:
                            if import_child.type == 'identifier':
                                names.append(import_child.text.decode('utf-8'))
                
                if module_name:
                    return Import(
                        module=module_name,
                        names=names,
                        alias=None,
                        file_path=file_path,
                        line_number=node.start_point[0] + 1
                    )
            
            return None
            
        except Exception as e:
            print(f"Error extracting import info: {e}")
            return None
    
    def create_symbol_map(self, file_paths: List[str]) -> Dict[str, SymbolInfo]:
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
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp'
        }
        
        return language_map.get(ext, 'unknown')
    
    def analyze_code_structure(self, file_paths: List[str]) -> ASTIndex:
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
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                file_metadata[file_path] = {
                    'language': language,
                    'line_count': len(content.split('\n')),
                    'char_count': len(content),
                    'function_count': len(file_functions),
                    'class_count': len(file_classes),
                    'import_count': len(file_imports)
                }
            except Exception as e:
                file_metadata[file_path] = {
                    'language': language,
                    'error': str(e)
                }
        
        return ASTIndex(
            functions=functions,
            classes=classes,
            imports=imports,
            symbols=symbols,
            file_metadata=file_metadata
        )