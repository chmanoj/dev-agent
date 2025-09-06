"""Interface for codebase analysis components."""

from abc import ABC, abstractmethod
from typing import List
from ..models.documents import Task


class ICodebaseAnalyzer(ABC):
    """Interface for codebase analysis."""
    
    @abstractmethod
    def analyze_for_specification(self) -> 'SpecificationAnalysis':
        """Analyze codebase to generate specification requirements."""
        pass
    
    @abstractmethod
    def analyze_for_design(self) -> 'DesignAnalysis':
        """Analyze codebase to understand current architecture and design."""
        pass
    
    @abstractmethod
    def extract_architecture_patterns(self) -> 'ArchitectureInfo':
        """Extract architectural patterns from the codebase."""
        pass
    
    @abstractmethod
    def identify_code_patterns(self) -> 'CodePatterns':
        """Identify coding patterns and conventions."""
        pass
    
    @abstractmethod
    def find_similar_implementations(self, query: str) -> List['CodeExample']:
        """Find similar code implementations for reference."""
        pass
    
    @abstractmethod
    def get_context_for_task(self, task: Task) -> 'CodeContext':
        """Get relevant code context for implementing a task."""
        pass