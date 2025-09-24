"""AI-powered code analysis engine for comprehensive codebase analysis."""

from __future__ import annotations

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from ..interfaces.ai_analysis_interface import IAIAnalysisEngine
from ..interfaces.indexing_interface import IIndexingEngine
from ..models.analysis import (
    ArchitecturalAnalysisResult,
    ComprehensiveAnalysisResult,
    PerformanceAnalysisResult,
    QualityAnalysisResult,
    SecurityAnalysisResult,
)
from ..services.azure_openai_service import AzureOpenAIService
from .architectural_analyzer import ArchitecturalAnalyzer
from .code_quality_analyzer import CodeQualityAnalyzer
from .performance_analyzer import PerformanceAnalyzer
from .security_analyzer import SecurityAnalyzer

logger = logging.getLogger(__name__)


class AIAnalysisEngine(IAIAnalysisEngine):
    """AI-powered code analysis engine that integrates multiple analyzers."""

    def __init__(
        self,
        indexing_engine: IIndexingEngine,
        ai_service: AzureOpenAIService | None = None,
    ):
        """Initialize the AI analysis engine.

        Args:
            indexing_engine: The indexing engine with parsed codebase data
            ai_service: AI service for enhanced analysis (optional)
        """
        self.indexing_engine = indexing_engine
        self.ai_service = ai_service  # Can be None
        
        # Initialize specialized analyzers
        self.quality_analyzer = CodeQualityAnalyzer(indexing_engine, ai_service)
        self.security_analyzer = SecurityAnalyzer(indexing_engine, ai_service)
        self.performance_analyzer = PerformanceAnalyzer(indexing_engine, ai_service)
        self.architectural_analyzer = ArchitecturalAnalyzer(indexing_engine, ai_service)

    def analyze_comprehensive(self, project_path: str) -> ComprehensiveAnalysisResult:
        """Perform comprehensive analysis of the codebase.

        Args:
            project_path: Path to the project directory

        Returns:
            Comprehensive analysis results from all analyzers
        """
        logger.info(f"Starting comprehensive analysis of {project_path}")
        start_time = time.time()

        try:
            # Run all analyses in parallel (could be optimized with asyncio)
            quality_analysis = self.analyze_quality(project_path)
            security_analysis = self.analyze_security(project_path)
            performance_analysis = self.analyze_performance(project_path)
            architectural_analysis = self.analyze_architecture(project_path)

            # Calculate overall health score
            overall_health_score = self._calculate_overall_health_score(
                quality_analysis,
                security_analysis,
                performance_analysis,
                architectural_analysis,
            )

            # Identify critical issues across all analyses
            critical_issues = self._identify_critical_issues(
                quality_analysis,
                security_analysis,
                performance_analysis,
                architectural_analysis,
            )

            # Generate priority recommendations
            priority_recommendations = self._generate_priority_recommendations(
                quality_analysis,
                security_analysis,
                performance_analysis,
                architectural_analysis,
            )

            analysis_duration = time.time() - start_time
            logger.info(f"Comprehensive analysis completed in {analysis_duration:.2f}s")

            return ComprehensiveAnalysisResult(
                quality_analysis=quality_analysis,
                security_analysis=security_analysis,
                performance_analysis=performance_analysis,
                architectural_analysis=architectural_analysis,
                overall_health_score=overall_health_score,
                critical_issues=critical_issues,
                priority_recommendations=priority_recommendations,
                analysis_timestamp=datetime.now().isoformat(),
                analysis_duration=analysis_duration,
            )

        except Exception as e:
            logger.error(f"Comprehensive analysis failed: {e}")
            raise

    def analyze_quality(self, project_path: str) -> QualityAnalysisResult:
        """Analyze code quality and identify issues.

        Args:
            project_path: Path to the project directory

        Returns:
            Quality analysis results
        """
        logger.info(f"Starting quality analysis of {project_path}")
        return self.quality_analyzer.analyze(project_path)

    def analyze_security(self, project_path: str) -> SecurityAnalysisResult:
        """Analyze security vulnerabilities and issues.

        Args:
            project_path: Path to the project directory

        Returns:
            Security analysis results
        """
        logger.info(f"Starting security analysis of {project_path}")
        return self.security_analyzer.analyze(project_path)

    def analyze_performance(self, project_path: str) -> PerformanceAnalysisResult:
        """Analyze performance bottlenecks and optimization opportunities.

        Args:
            project_path: Path to the project directory

        Returns:
            Performance analysis results
        """
        logger.info(f"Starting performance analysis of {project_path}")
        return self.performance_analyzer.analyze(project_path)

    def analyze_architecture(self, project_path: str) -> ArchitecturalAnalysisResult:
        """Analyze architectural violations and design issues.

        Args:
            project_path: Path to the project directory

        Returns:
            Architectural analysis results
        """
        logger.info(f"Starting architectural analysis of {project_path}")
        return self.architectural_analyzer.analyze(project_path)

    def _calculate_overall_health_score(
        self,
        quality: QualityAnalysisResult,
        security: SecurityAnalysisResult,
        performance: PerformanceAnalysisResult,
        architecture: ArchitecturalAnalysisResult,
    ) -> float:
        """Calculate overall health score from individual analysis results.

        Args:
            quality: Quality analysis results
            security: Security analysis results
            performance: Performance analysis results
            architecture: Architectural analysis results

        Returns:
            Overall health score (0.0 to 1.0)
        """
        # Weighted average of all scores
        weights = {
            "quality": 0.3,
            "security": 0.3,
            "performance": 0.2,
            "architecture": 0.2,
        }

        weighted_score = (
            quality.overall_score * weights["quality"]
            + security.overall_security_score * weights["security"]
            + performance.overall_performance_score * weights["performance"]
            + architecture.overall_architecture_score * weights["architecture"]
        )

        return min(max(weighted_score, 0.0), 1.0)

    def _identify_critical_issues(
        self,
        quality: QualityAnalysisResult,
        security: SecurityAnalysisResult,
        performance: PerformanceAnalysisResult,
        architecture: ArchitecturalAnalysisResult,
    ) -> list[str]:
        """Identify critical issues across all analyses.

        Args:
            quality: Quality analysis results
            security: Security analysis results
            performance: Performance analysis results
            architecture: Architectural analysis results

        Returns:
            List of critical issues
        """
        critical_issues = []

        # Critical security issues
        critical_security = [
            issue for issue in security.security_issues
            if issue.severity == "critical"
        ]
        if critical_security:
            critical_issues.append(
                f"Found {len(critical_security)} critical security vulnerabilities"
            )

        # Critical code smells
        critical_quality = [
            smell for smell in quality.code_smells
            if smell.severity == "critical"
        ]
        if critical_quality:
            critical_issues.append(
                f"Found {len(critical_quality)} critical code quality issues"
            )

        # High impact performance issues
        high_impact_performance = [
            issue for issue in performance.performance_issues
            if issue.impact == "high"
        ]
        if high_impact_performance:
            critical_issues.append(
                f"Found {len(high_impact_performance)} high-impact performance issues"
            )

        # High severity architectural violations
        high_severity_arch = [
            violation for violation in architecture.violations
            if violation.severity == "high"
        ]
        if high_severity_arch:
            critical_issues.append(
                f"Found {len(high_severity_arch)} high-severity architectural violations"
            )

        return critical_issues

    def _generate_priority_recommendations(
        self,
        quality: QualityAnalysisResult,
        security: SecurityAnalysisResult,
        performance: PerformanceAnalysisResult,
        architecture: ArchitecturalAnalysisResult,
    ) -> list[str]:
        """Generate priority recommendations based on all analyses.

        Args:
            quality: Quality analysis results
            security: Security analysis results
            performance: Performance analysis results
            architecture: Architectural analysis results

        Returns:
            List of priority recommendations
        """
        recommendations = []

        # Security first
        if security.overall_security_score < 0.7:
            recommendations.append(
                "Address security vulnerabilities immediately - security score is below acceptable threshold"
            )

        # Quality issues
        if quality.overall_score < 0.6:
            recommendations.append(
                "Improve code quality through refactoring and addressing code smells"
            )

        # Performance issues
        if performance.overall_performance_score < 0.7:
            recommendations.append(
                "Optimize performance bottlenecks to improve system responsiveness"
            )

        # Architectural issues
        if architecture.overall_architecture_score < 0.6:
            recommendations.append(
                "Refactor architecture to reduce coupling and improve maintainability"
            )

        # Test coverage
        if quality.test_coverage_estimate < 0.8:
            recommendations.append(
                "Increase test coverage to improve code reliability and maintainability"
            )

        # Documentation
        if quality.documentation_coverage < 0.7:
            recommendations.append(
                "Improve code documentation to enhance maintainability"
            )

        return recommendations[:5]  # Return top 5 recommendations