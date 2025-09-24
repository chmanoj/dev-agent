"""
dev-agent: A high-performance, indexing-first development agent system.

This package implements a four-phase workflow: Indexing, Specification, Design, and Implementation.
The system is built Python-first with a focus on analyzing and working with existing large codebases
through comprehensive local indexing.
"""

__version__ = "0.1.0"

# Import main components for easier access
from .analysis.ai_analysis_engine import AIAnalysisEngine
from .analysis.architectural_analyzer import ArchitecturalAnalyzer
from .analysis.code_quality_analyzer import CodeQualityAnalyzer
from .analysis.performance_analyzer import PerformanceAnalyzer
from .analysis.security_analyzer import SecurityAnalyzer

__all__ = [
    "AIAnalysisEngine",
    "CodeQualityAnalyzer",
    "SecurityAnalyzer", 
    "PerformanceAnalyzer",
    "ArchitecturalAnalyzer",
]
