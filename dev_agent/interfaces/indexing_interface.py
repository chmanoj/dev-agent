"""Interfaces for indexing engine components."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from ..models.indexing import CodeChunk, Embedding, CodeMatch, SymbolInfo, ASTIndex, FunctionDef, ClassDef, Import


class IIndexingEngine(ABC):
    """Interface for the main indexing engine."""
    
    @abstractmethod
    def build_index(self) -> 'IndexResult':
        """Build a complete index of the codebase."""
        pass
    
    @abstractmethod
    def parse_codebase_ast(self) -> ASTIndex:
        """Parse the entire codebase into an AST index."""
        pass
    
    @abstractmethod
    def generate_embeddings(self, code_chunks: List[CodeChunk]) -> List[Embedding]:
        """Generate vector embeddings for code chunks."""
        pass
    
    @abstractmethod
    def store_embeddings(self, embeddings: List[Embedding]) -> bool:
        """Store embeddings in the vector database."""
        pass
    
    @abstractmethod
    def query_similar_code(self, query: str, limit: int = 10) -> List[CodeMatch]:
        """Query for similar code using vector similarity."""
        pass
    
    @abstractmethod
    def get_symbol_map(self) -> Dict[str, SymbolInfo]:
        """Get a map of all symbols in the codebase."""
        pass


class ITreeSitterParser(ABC):
    """Interface for Tree-sitter AST parsing."""
    
    @abstractmethod
    def parse_file(self, file_path: str, language: str) -> 'AST':
        """Parse a single file into an AST."""
        pass
    
    @abstractmethod
    def extract_symbols(self, ast: 'AST') -> List[SymbolInfo]:
        """Extract symbols from an AST."""
        pass
    
    @abstractmethod
    def get_function_definitions(self, ast: 'AST') -> List[FunctionDef]:
        """Extract function definitions from an AST."""
        pass
    
    @abstractmethod
    def get_class_definitions(self, ast: 'AST') -> List[ClassDef]:
        """Extract class definitions from an AST."""
        pass
    
    @abstractmethod
    def extract_imports(self, ast: 'AST') -> List[Import]:
        """Extract import statements from an AST."""
        pass


class IVectorDatabase(ABC):
    """Interface for vector database operations."""
    
    @abstractmethod
    def store_embeddings(self, embeddings: List['CodeEmbedding']) -> bool:
        """Store code embeddings in the database."""
        pass
    
    @abstractmethod
    def query_similar(self, query_embedding: 'Embedding', k: int = 10) -> List['Match']:
        """Query for similar embeddings."""
        pass
    
    @abstractmethod
    def update_embedding(self, code_id: str, embedding: 'Embedding') -> bool:
        """Update an existing embedding."""
        pass
    
    @abstractmethod
    def get_embedding_stats(self) -> 'EmbeddingStats':
        """Get statistics about stored embeddings."""
        pass
    
    @abstractmethod
    def initialize_database(self) -> bool:
        """Initialize the vector database."""
        pass