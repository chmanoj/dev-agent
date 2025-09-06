"""Data models for indexing and code analysis."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union

try:
    import numpy as np
    NDArray = np.ndarray
except ImportError:
    # Fallback for testing without numpy
    NDArray = List[float]


@dataclass
class CodeChunk:
    """A chunk of code for embedding generation."""
    content: str
    file_path: str
    start_line: int
    end_line: int
    language: str
    chunk_type: str  # 'function', 'class', 'module', etc.


@dataclass
class Embedding:
    """Vector embedding for a code chunk."""
    chunk_id: str
    vector: NDArray
    metadata: Dict[str, Any]


@dataclass
class CodeMatch:
    """Result of a similarity search."""
    chunk: CodeChunk
    similarity_score: float
    embedding_id: str


@dataclass
class SymbolInfo:
    """Information about a code symbol (function, class, variable)."""
    name: str
    symbol_type: str  # 'function', 'class', 'variable', 'import'
    file_path: str
    line_number: int
    scope: str
    signature: Optional[str] = None
    docstring: Optional[str] = None


@dataclass
class FunctionDef:
    """Function definition from AST parsing."""
    name: str
    parameters: List[str]
    return_type: Optional[str]
    docstring: Optional[str]
    file_path: str
    start_line: int
    end_line: int


@dataclass
class ClassDef:
    """Class definition from AST parsing."""
    name: str
    base_classes: List[str]
    methods: List[FunctionDef]
    attributes: List[str]
    docstring: Optional[str]
    file_path: str
    start_line: int
    end_line: int


@dataclass
class Import:
    """Import statement from AST parsing."""
    module: str
    names: List[str]
    alias: Optional[str]
    file_path: str
    line_number: int


@dataclass
class ASTIndex:
    """Complete AST index for a codebase."""
    functions: Dict[str, FunctionDef]
    classes: Dict[str, ClassDef]
    imports: List[Import]
    symbols: Dict[str, SymbolInfo]
    file_metadata: Dict[str, Dict[str, Any]]