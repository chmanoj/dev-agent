"""Interfaces for document and code generation components."""

from abc import ABC, abstractmethod
from typing import List
from ..models.documents import SpecificationDocument, DesignDocument, TaskList, Task


class ISpecificationGenerator(ABC):
    """Interface for specification document generation."""
    
    @abstractmethod
    def generate_from_existing_code(self, analysis: 'SpecificationAnalysis') -> SpecificationDocument:
        """Generate specification from existing codebase analysis."""
        pass
    
    @abstractmethod
    def generate_from_user_input(self, user_requirements: List[str]) -> SpecificationDocument:
        """Generate specification from user input and requirements."""
        pass
    
    @abstractmethod
    def refine_specification(self, spec: SpecificationDocument, feedback: str) -> SpecificationDocument:
        """Refine specification based on user feedback."""
        pass


class IDesignGenerator(ABC):
    """Interface for design document generation."""
    
    @abstractmethod
    def generate_from_specification(self, spec: SpecificationDocument, analysis: 'DesignAnalysis') -> DesignDocument:
        """Generate design document from specification and codebase analysis."""
        pass
    
    @abstractmethod
    def refine_design(self, design: DesignDocument, feedback: str) -> DesignDocument:
        """Refine design based on user feedback."""
        pass


class ITaskGenerator(ABC):
    """Interface for task list generation."""
    
    @abstractmethod
    def generate_from_design(self, design: DesignDocument) -> TaskList:
        """Generate implementation tasks from design document."""
        pass
    
    @abstractmethod
    def refine_tasks(self, tasks: TaskList, feedback: str) -> TaskList:
        """Refine task list based on user feedback."""
        pass


class IPythonCodeGenerator(ABC):
    """Interface for Python code generation."""
    
    @abstractmethod
    def analyze_existing_patterns(self) -> 'CodePatterns':
        """Analyze existing codebase patterns for consistency."""
        pass
    
    @abstractmethod
    def generate_code_from_task(self, task: Task, context: 'CodeContext') -> 'GeneratedCode':
        """Generate Python code for a specific task."""
        pass
    
    @abstractmethod
    def ensure_consistency(self, new_code: str, existing_codebase: 'CodebaseIndex') -> str:
        """Ensure new code is consistent with existing patterns."""
        pass
    
    @abstractmethod
    def generate_tests(self, code: str, test_framework: str = "pytest") -> str:
        """Generate tests for the given code."""
        pass
    
    @abstractmethod
    def write_code_to_file(self, code: str, file_path: str) -> bool:
        """Write generated code to a file."""
        pass