"""Interface for AI-powered code analysis components."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models.analysis import (
    ArchitecturalAnalysisResult,
    ComprehensiveAnalysisResult,
    PerformanceAnalysisResult,
    QualityAnalysisResult,
    SecurityAnalysisResult,
)


class IAIAnalysisEngine(ABC):
    """Interface for AI-powered code analysis engine."""

    @abstractmethod
    def analyze_comprehensive(self, project_path: str) -> ComprehensiveAnalysisResult:
        """Perform comprehensive analysis of the codebase.

        Args:
            project_path: Path to the project directory

        Returns:
            Comprehensive analysis results from all analyzers
        """
        pass

    @abstractmethod
    def analyze_quality(self, project_path: str) -> QualityAnalysisResult:
        """Analyze code quality and identify issues.

        Args:
            project_path: Path to the project directory

        Returns:
            Quality analysis results
        """
        pass

    @abstractmethod
    def analyze_security(self, project_path: str) -> SecurityAnalysisResult:
        """Analyze security vulnerabilities and issues.

        Args:
            project_path: Path to the project directory

        Returns:
            Security analysis results
        """
        pass

    @abstractmethod
    def analyze_performance(self, project_path: str) -> PerformanceAnalysisResult:
        """Analyze performance bottlenecks and optimization opportunities.

        Args:
            project_path: Path to the project directory

        Returns:
            Performance analysis results
        """
        pass

    @abstractmethod
    def analyze_architecture(self, project_path: str) -> ArchitecturalAnalysisResult:
        """Analyze architectural violations and design issues.

        Args:
            project_path: Path to the project directory

        Returns:
            Architectural analysis results
        """
        pass


class ICodeQualityAnalyzer(ABC):
    """Interface for code quality analyzer."""

    @abstractmethod
    def analyze_code_smells(self, code: str, file_path: str) -> list:
        """Identify code smells and anti-patterns."""
        pass

    @abstractmethod
    def calculate_complexity_metrics(self, code: str) -> dict[str, float]:
        """Calculate complexity metrics for code."""
        pass

    @abstractmethod
    def analyze_maintainability(self, code: str) -> float:
        """Calculate maintainability index."""
        pass

    @abstractmethod
    def detect_duplication(self, project_path: str) -> float:
        """Detect code duplication percentage."""
        pass


class ISecurityAnalyzer(ABC):
    """Interface for security analyzer."""

    @abstractmethod
    def scan_vulnerabilities(self, code: str, file_path: str) -> list:
        """Scan for security vulnerabilities."""
        pass

    @abstractmethod
    def check_input_validation(self, code: str) -> list:
        """Check for input validation issues."""
        pass

    @abstractmethod
    def analyze_authentication(self, project_path: str) -> list:
        """Analyze authentication and authorization patterns."""
        pass

    @abstractmethod
    def check_data_exposure(self, code: str) -> list:
        """Check for potential data exposure issues."""
        pass


class IPerformanceAnalyzer(ABC):
    """Interface for performance analyzer."""

    @abstractmethod
    def identify_bottlenecks(self, code: str, file_path: str) -> list:
        """Identify performance bottlenecks."""
        pass

    @abstractmethod
    def analyze_algorithm_complexity(self, code: str) -> dict[str, str]:
        """Analyze algorithmic complexity."""
        pass

    @abstractmethod
    def check_memory_usage(self, code: str) -> list:
        """Check for memory usage issues."""
        pass

    @abstractmethod
    def analyze_io_patterns(self, code: str) -> list:
        """Analyze I/O operation patterns."""
        pass


class IArchitecturalAnalyzer(ABC):
    """Interface for architectural analyzer."""

    @abstractmethod
    def detect_violations(self, project_path: str) -> list:
        """Detect architectural violations."""
        pass

    @abstractmethod
    def analyze_dependencies(self, project_path: str) -> dict[str, Any]:
        """Analyze dependency structure."""
        pass

    @abstractmethod
    def check_layer_violations(self, project_path: str) -> list:
        """Check for layer violations."""
        pass

    @abstractmethod
    def analyze_coupling(self, project_path: str) -> dict[str, float]:
        """Analyze coupling metrics."""
        pass