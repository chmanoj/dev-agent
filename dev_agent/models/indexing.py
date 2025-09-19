"""Data models for indexing and code analysis."""

from dataclasses import dataclass
from typing import Any

try:
    import numpy as np

    NDArray = np.ndarray
except ImportError:
    # Fallback for testing without numpy
    NDArray = list[float]


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
    metadata: dict[str, Any]


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
    signature: str | None = None
    docstring: str | None = None


@dataclass
class FunctionDef:
    """Function definition from AST parsing."""

    name: str
    parameters: list[str]
    return_type: str | None
    docstring: str | None
    file_path: str
    start_line: int
    end_line: int


@dataclass
class ClassDef:
    """Class definition from AST parsing."""

    name: str
    base_classes: list[str]
    methods: list[FunctionDef]
    attributes: list[str]
    docstring: str | None
    file_path: str
    start_line: int
    end_line: int


@dataclass
class Import:
    """Import statement from AST parsing."""

    module: str
    names: list[str]
    alias: str | None
    file_path: str
    line_number: int


@dataclass
class ASTIndex:
    """Complete AST index for a codebase."""

    functions: dict[str, FunctionDef]
    classes: dict[str, ClassDef]
    imports: list[Import]
    symbols: dict[str, SymbolInfo]
    file_metadata: dict[str, dict[str, Any]]
