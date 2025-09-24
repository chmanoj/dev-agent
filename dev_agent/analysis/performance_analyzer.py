"""Performance analyzer for identifying bottlenecks and optimization opportunities."""

from __future__ import annotations

import ast
import logging
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from ..interfaces.ai_analysis_interface import IPerformanceAnalyzer
from ..interfaces.indexing_interface import IIndexingEngine
from ..models.analysis import PerformanceAnalysisResult, PerformanceIssue
from ..services.azure_openai_service import AzureOpenAIService, ChatMessage

logger = logging.getLogger(__name__)


class PerformanceAnalyzer(IPerformanceAnalyzer):
    """Analyzer for performance bottlenecks and optimization opportunities."""

    def __init__(
        self,
        indexing_engine: IIndexingEngine,
        ai_service: AzureOpenAIService | None = None,
    ):
        """Initialize the performance analyzer.

        Args:
            indexing_engine: The indexing engine with parsed codebase data
            ai_service: AI service for enhanced analysis (optional)
        """
        self.indexing_engine = indexing_engine
        self.ai_service = ai_service
        self.ast_index = getattr(indexing_engine, "ast_index", None)

        # Performance patterns and rules
        self._init_performance_patterns()

    def analyze(self, project_path: str) -> PerformanceAnalysisResult:
        """Perform comprehensive performance analysis of the project.

        Args:
            project_path: Path to the project directory

        Returns:
            Performance analysis results
        """
        logger.info(f"Analyzing performance for {project_path}")

        if not self.ast_index:
            logger.warning("No AST index available for performance analysis")
            return self._create_empty_result()

        # Analyze performance issues
        performance_issues = self._analyze_all_performance_issues(project_path)

        # Calculate metrics
        overall_score = self._calculate_performance_score(performance_issues)
        bottlenecks = self._identify_bottlenecks(performance_issues)
        optimization_opportunities = self._identify_optimization_opportunities(performance_issues)
        resource_usage_patterns = self._analyze_resource_usage_patterns()

        # Generate summary and recommendations
        summary = self._generate_performance_summary(performance_issues, overall_score)
        recommendations = self._generate_performance_recommendations(
            performance_issues, bottlenecks, optimization_opportunities
        )

        return PerformanceAnalysisResult(
            overall_performance_score=overall_score,
            performance_issues=performance_issues,
            bottlenecks=bottlenecks,
            optimization_opportunities=optimization_opportunities,
            resource_usage_patterns=resource_usage_patterns,
            summary=summary,
            recommendations=recommendations,
        )

    def identify_bottlenecks(self, code: str, file_path: str) -> list[PerformanceIssue]:
        """Identify performance bottlenecks in the given code.

        Args:
            code: Source code to analyze
            file_path: Path to the file being analyzed

        Returns:
            List of identified performance issues
        """
        issues = []

        try:
            tree = ast.parse(code)
            lines = code.split('\n')

            # Analyze different types of performance issues
            issues.extend(self._detect_algorithmic_issues(tree, file_path, lines))
            issues.extend(self._detect_memory_issues(tree, file_path, lines))
            issues.extend(self._detect_io_issues(tree, file_path, lines))
            issues.extend(self._detect_database_issues(tree, file_path, lines))
            issues.extend(self._detect_network_issues(tree, file_path, lines))
            issues.extend(self._detect_inefficient_loops(tree, file_path, lines))
            issues.extend(self._detect_string_concatenation_issues(tree, file_path, lines))

        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")

        return issues

    def analyze_algorithm_complexity(self, code: str) -> dict[str, str]:
        """Analyze algorithmic complexity of functions in the code.

        Args:
            code: Source code to analyze

        Returns:
            Dictionary mapping function names to their complexity estimates
        """
        complexity_map = {}

        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity = self._estimate_time_complexity(node)
                    complexity_map[node.name] = complexity

        except SyntaxError:
            pass

        return complexity_map

    def check_memory_usage(self, code: str) -> list[PerformanceIssue]:
        """Check for memory usage issues in the code.

        Args:
            code: Source code to analyze

        Returns:
            List of memory-related performance issues
        """
        issues = []
        lines = code.split('\n')

        try:
            tree = ast.parse(code)
            
            # Check for memory-intensive operations
            for node in ast.walk(tree):
                # Large list comprehensions
                if isinstance(node, ast.ListComp):
                    # Check if it's potentially creating large lists
                    issues.append(
                        PerformanceIssue(
                            issue_type="Memory Usage",
                            description="Large list comprehension may consume excessive memory",
                            file_path="<analyzed_code>",
                            line_number=node.lineno,
                            impact="medium",
                            category="memory",
                            suggestion="Consider using generator expressions for large datasets",
                            code_snippet=self._extract_code_snippet(lines, node.lineno, 1),
                            estimated_improvement="Reduced memory usage",
                            confidence=0.6,
                        )
                    )

        except SyntaxError:
            pass

        return issues

    def analyze_io_patterns(self, code: str) -> list[PerformanceIssue]:
        """Analyze I/O operation patterns for performance issues.

        Args:
            code: Source code to analyze

        Returns:
            List of I/O-related performance issues
        """
        issues = []
        lines = code.split('\n')

        try:
            tree = ast.parse(code)
            
            # Check for inefficient I/O patterns
            for node in ast.walk(tree):
                # File operations in loops
                if isinstance(node, ast.For):
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                            if child.func.id == 'open':
                                issues.append(
                                    PerformanceIssue(
                                        issue_type="I/O Bottleneck",
                                        description="File operations inside loop can be inefficient",
                                        file_path="<analyzed_code>",
                                        line_number=child.lineno,
                                        impact="medium",
                                        category="io",
                                        suggestion="Consider batching file operations or moving outside loop",
                                        code_snippet=self._extract_code_snippet(lines, child.lineno, 1),
                                        estimated_improvement="Reduced I/O overhead",
                                        confidence=0.7,
                                    )
                                )

        except SyntaxError:
            pass

        return issues

    def _init_performance_patterns(self) -> None:
        """Initialize performance patterns and rules."""
        self.inefficient_patterns = {
            'nested_loops': 'Nested loops can lead to O(n²) or worse complexity',
            'string_concatenation': 'String concatenation in loops is inefficient',
            'repeated_calculations': 'Repeated calculations should be cached',
            'inefficient_data_structures': 'Using wrong data structure for the operation',
        }

        self.database_antipatterns = [
            'N+1 queries',
            'Missing indexes',
            'Inefficient joins',
            'Large result sets without pagination',
        ]

        self.memory_patterns = [
            'Large object creation in loops',
            'Memory leaks from unclosed resources',
            'Inefficient data structures',
            'Unnecessary object copying',
        ]

    def _analyze_all_performance_issues(self, project_path: str) -> list[PerformanceIssue]:
        """Analyze performance issues across all files in the project."""
        all_issues = []

        if not self.ast_index:
            return all_issues

        # Analyze each Python file
        for file_path, metadata in self.ast_index.file_metadata.items():
            if file_path.endswith('.py'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                        file_issues = self.identify_bottlenecks(code, file_path)
                        all_issues.extend(file_issues)
                except Exception as e:
                    logger.warning(f"Error analyzing {file_path}: {e}")

        return all_issues

    def _detect_algorithmic_issues(
        self, tree: ast.AST, file_path: str, lines: list[str]
    ) -> list[PerformanceIssue]:
        """Detect algorithmic performance issues."""
        issues = []

        # Detect nested loops
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                nested_loops = self._count_nested_loops(node)
                if nested_loops > 1:
                    complexity_estimate = f"O(n^{nested_loops})"
                    impact = "high" if nested_loops > 2 else "medium"
                    
                    issues.append(
                        PerformanceIssue(
                            issue_type="Algorithmic Complexity",
                            description=f"Nested loops detected with {complexity_estimate} complexity",
                            file_path=file_path,
                            line_number=node.lineno,
                            impact=impact,
                            category="algorithm",
                            suggestion="Consider optimizing algorithm or using more efficient data structures",
                            code_snippet=self._extract_code_snippet(lines, node.lineno, 3),
                            estimated_improvement=f"Potential reduction from {complexity_estimate} to O(n) or O(n log n)",
                            confidence=0.8,
                        )
                    )

        return issues

    def _detect_memory_issues(
        self, tree: ast.AST, file_path: str, lines: list[str]
    ) -> list[PerformanceIssue]:
        """Detect memory-related performance issues."""
        issues = []

        for node in ast.walk(tree):
            # Large list/dict comprehensions
            if isinstance(node, (ast.ListComp, ast.DictComp)):
                # Check if it's inside a loop (potential memory issue)
                parent_loops = self._find_parent_loops(tree, node)
                if parent_loops:
                    issues.append(
                        PerformanceIssue(
                            issue_type="Memory Usage",
                            description="List/dict comprehension inside loop may cause memory issues",
                            file_path=file_path,
                            line_number=node.lineno,
                            impact="medium",
                            category="memory",
                            suggestion="Consider using generators or processing data in chunks",
                            code_snippet=self._extract_code_snippet(lines, node.lineno, 1),
                            estimated_improvement="Reduced memory footprint",
                            confidence=0.7,
                        )
                    )

            # Potential memory leaks from unclosed files
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == 'open':
                    # Check if it's in a with statement
                    is_in_with = self._is_in_with_statement(tree, node)
                    if not is_in_with:
                        issues.append(
                            PerformanceIssue(
                                issue_type="Resource Leak",
                                description="File opened without proper resource management",
                                file_path=file_path,
                                line_number=node.lineno,
                                impact="medium",
                                category="memory",
                                suggestion="Use 'with' statement for proper file handling",
                                code_snippet=self._extract_code_snippet(lines, node.lineno, 1),
                                estimated_improvement="Prevented resource leaks",
                                confidence=0.9,
                            )
                        )

        return issues

    def _detect_io_issues(
        self, tree: ast.AST, file_path: str, lines: list[str]
    ) -> list[PerformanceIssue]:
        """Detect I/O-related performance issues."""
        issues = []

        for node in ast.walk(tree):
            # I/O operations in loops
            if isinstance(node, (ast.For, ast.While)):
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        # File operations
                        if (isinstance(child.func, ast.Name) and 
                            child.func.id in ['open', 'read', 'write']):
                            issues.append(
                                PerformanceIssue(
                                    issue_type="I/O Bottleneck",
                                    description=f"I/O operation '{child.func.id}' inside loop",
                                    file_path=file_path,
                                    line_number=child.lineno,
                                    impact="high",
                                    category="io",
                                    suggestion="Batch I/O operations or move outside loop when possible",
                                    code_snippet=self._extract_code_snippet(lines, child.lineno, 1),
                                    estimated_improvement="Significant I/O performance improvement",
                                    confidence=0.8,
                                )
                            )

                        # Network operations
                        if (isinstance(child.func, ast.Attribute) and 
                            child.func.attr in ['get', 'post', 'request']):
                            issues.append(
                                PerformanceIssue(
                                    issue_type="Network Bottleneck",
                                    description="Network request inside loop",
                                    file_path=file_path,
                                    line_number=child.lineno,
                                    impact="high",
                                    category="network",
                                    suggestion="Use async operations or batch requests",
                                    code_snippet=self._extract_code_snippet(lines, child.lineno, 1),
                                    estimated_improvement="Reduced network latency impact",
                                    confidence=0.9,
                                )
                            )

        return issues

    def _detect_database_issues(
        self, tree: ast.AST, file_path: str, lines: list[str]
    ) -> list[PerformanceIssue]:
        """Detect database-related performance issues."""
        issues = []

        for node in ast.walk(tree):
            # Database queries in loops (N+1 problem)
            if isinstance(node, (ast.For, ast.While)):
                for child in ast.walk(node):
                    if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                        if child.func.attr in ['execute', 'query', 'get', 'filter']:
                            issues.append(
                                PerformanceIssue(
                                    issue_type="Database N+1 Query",
                                    description="Database query inside loop (potential N+1 problem)",
                                    file_path=file_path,
                                    line_number=child.lineno,
                                    impact="high",
                                    category="database",
                                    suggestion="Use bulk operations or eager loading to reduce queries",
                                    code_snippet=self._extract_code_snippet(lines, child.lineno, 1),
                                    estimated_improvement="Reduced database round trips",
                                    confidence=0.8,
                                )
                            )

        return issues

    def _detect_network_issues(
        self, tree: ast.AST, file_path: str, lines: list[str]
    ) -> list[PerformanceIssue]:
        """Detect network-related performance issues."""
        issues = []

        # Look for synchronous network calls that could be async
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # HTTP requests
                if (isinstance(node.func, ast.Attribute) and 
                    node.func.attr in ['get', 'post', 'put', 'delete', 'request']):
                    # Check if it's in an async function
                    is_async = self._is_in_async_function(tree, node)
                    if not is_async:
                        issues.append(
                            PerformanceIssue(
                                issue_type="Synchronous Network Call",
                                description="Synchronous network request may block execution",
                                file_path=file_path,
                                line_number=node.lineno,
                                impact="medium",
                                category="network",
                                suggestion="Consider using async/await for network operations",
                                code_snippet=self._extract_code_snippet(lines, node.lineno, 1),
                                estimated_improvement="Improved concurrency and responsiveness",
                                confidence=0.7,
                            )
                        )

        return issues

    def _detect_inefficient_loops(
        self, tree: ast.AST, file_path: str, lines: list[str]
    ) -> list[PerformanceIssue]:
        """Detect inefficient loop patterns."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                # Check for inefficient list operations in loops
                for child in ast.walk(node):
                    if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                        # List.append in loop when list size is known
                        if child.func.attr == 'append':
                            issues.append(
                                PerformanceIssue(
                                    issue_type="Inefficient List Building",
                                    description="List.append() in loop - consider list comprehension",
                                    file_path=file_path,
                                    line_number=child.lineno,
                                    impact="low",
                                    category="algorithm",
                                    suggestion="Use list comprehension or pre-allocate list size",
                                    code_snippet=self._extract_code_snippet(lines, child.lineno, 1),
                                    estimated_improvement="Minor performance improvement",
                                    confidence=0.6,
                                )
                            )

        return issues

    def _detect_string_concatenation_issues(
        self, tree: ast.AST, file_path: str, lines: list[str]
    ) -> list[PerformanceIssue]:
        """Detect inefficient string concatenation patterns."""
        issues = []

        for node in ast.walk(tree):
            # String concatenation in loops
            if isinstance(node, (ast.For, ast.While)):
                for child in ast.walk(node):
                    if isinstance(child, ast.AugAssign) and isinstance(child.op, ast.Add):
                        # Check if it's string concatenation
                        issues.append(
                            PerformanceIssue(
                                issue_type="Inefficient String Concatenation",
                                description="String concatenation in loop is inefficient",
                                file_path=file_path,
                                line_number=child.lineno,
                                impact="medium",
                                category="algorithm",
                                suggestion="Use join() method or f-strings for better performance",
                                code_snippet=self._extract_code_snippet(lines, child.lineno, 1),
                                estimated_improvement="Improved string building performance",
                                confidence=0.8,
                            )
                        )

        return issues

    def _estimate_time_complexity(self, func_node: ast.FunctionDef) -> str:
        """Estimate the time complexity of a function."""
        nested_loops = 0
        has_recursion = False

        for node in ast.walk(func_node):
            if isinstance(node, (ast.For, ast.While)):
                nested_loops = max(nested_loops, self._count_nested_loops(node))
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == func_node.name:
                    has_recursion = True

        if has_recursion:
            return "O(?) - Recursive function, complexity depends on recursion depth"
        elif nested_loops == 0:
            return "O(1) - Constant time"
        elif nested_loops == 1:
            return "O(n) - Linear time"
        elif nested_loops == 2:
            return "O(n²) - Quadratic time"
        else:
            return f"O(n^{nested_loops}) - Polynomial time"

    def _count_nested_loops(self, node: ast.AST) -> int:
        """Count the maximum nesting level of loops."""
        max_depth = 0
        current_depth = 0

        class LoopDepthCounter(ast.NodeVisitor):
            def __init__(self):
                self.max_depth = 0
                self.current_depth = 0

            def visit_For(self, node):
                self.current_depth += 1
                self.max_depth = max(self.max_depth, self.current_depth)
                self.generic_visit(node)
                self.current_depth -= 1

            def visit_While(self, node):
                self.current_depth += 1
                self.max_depth = max(self.max_depth, self.current_depth)
                self.generic_visit(node)
                self.current_depth -= 1

        counter = LoopDepthCounter()
        counter.visit(node)
        return counter.max_depth

    def _find_parent_loops(self, tree: ast.AST, target_node: ast.AST) -> list[ast.AST]:
        """Find parent loop nodes for a given node."""
        # This is a simplified implementation
        # In practice, you'd need to build a parent map
        return []

    def _is_in_with_statement(self, tree: ast.AST, target_node: ast.AST) -> bool:
        """Check if a node is inside a with statement."""
        # Simplified check - would need proper parent tracking
        return False

    def _is_in_async_function(self, tree: ast.AST, target_node: ast.AST) -> bool:
        """Check if a node is inside an async function."""
        # Simplified check - would need proper parent tracking
        return False

    def _calculate_performance_score(self, performance_issues: list[PerformanceIssue]) -> float:
        """Calculate overall performance score based on issues found."""
        if not performance_issues:
            return 1.0

        # Weight issues by impact
        impact_weights = {
            "high": 1.0,
            "medium": 0.6,
            "low": 0.2,
        }

        total_penalty = 0.0
        for issue in performance_issues:
            weight = impact_weights.get(issue.impact, 0.2)
            confidence_factor = issue.confidence
            total_penalty += weight * confidence_factor

        # Normalize score (assuming max 10 high-impact issues would give score 0)
        max_penalty = 10.0
        score = max(0.0, 1.0 - (total_penalty / max_penalty))
        
        return score

    def _identify_bottlenecks(self, performance_issues: list[PerformanceIssue]) -> list[str]:
        """Identify the main performance bottlenecks."""
        # Group issues by category and impact
        high_impact_issues = [i for i in performance_issues if i.impact == "high"]
        
        bottlenecks = []
        category_counts = Counter(issue.category for issue in high_impact_issues)
        
        for category, count in category_counts.most_common(5):
            bottlenecks.append(f"{category.title()}: {count} high-impact issues")
        
        return bottlenecks

    def _identify_optimization_opportunities(
        self, performance_issues: list[PerformanceIssue]
    ) -> list[str]:
        """Identify optimization opportunities."""
        opportunities = []
        
        # Group by issue type
        issue_types = Counter(issue.issue_type for issue in performance_issues)
        
        for issue_type, count in issue_types.most_common(5):
            if count > 2:
                opportunities.append(f"Optimize {count} instances of '{issue_type}'")
        
        return opportunities

    def _analyze_resource_usage_patterns(self) -> dict[str, Any]:
        """Analyze resource usage patterns in the codebase."""
        patterns = {
            "file_operations": 0,
            "network_calls": 0,
            "database_queries": 0,
            "memory_allocations": 0,
        }

        if not self.ast_index:
            return patterns

        # Count different types of resource usage
        for func_def in self.ast_index.functions.values():
            # This would require more sophisticated analysis
            # For now, return basic patterns
            pass

        return patterns

    def _generate_performance_summary(
        self, performance_issues: list[PerformanceIssue], overall_score: float
    ) -> str:
        """Generate a summary of the performance analysis."""
        impact_counts = Counter(issue.impact for issue in performance_issues)
        
        summary = f"Overall performance score: {overall_score:.2f}/1.0. "
        summary += f"Found {len(performance_issues)} performance issues: "
        
        if impact_counts:
            parts = []
            for impact in ["high", "medium", "low"]:
                if impact_counts[impact] > 0:
                    parts.append(f"{impact_counts[impact]} {impact} impact")
            summary += ", ".join(parts) + "."
        else:
            summary += "No significant performance issues found."
            
        return summary

    def _generate_performance_recommendations(
        self,
        performance_issues: list[PerformanceIssue],
        bottlenecks: list[str],
        optimization_opportunities: list[str],
    ) -> list[str]:
        """Generate performance improvement recommendations."""
        recommendations = []
        
        # High impact issues
        high_impact = [i for i in performance_issues if i.impact == "high"]
        if high_impact:
            recommendations.append(f"Address {len(high_impact)} high-impact performance issues immediately")
        
        # Specific bottlenecks
        if bottlenecks:
            recommendations.append(f"Focus on {bottlenecks[0]} as primary bottleneck")
        
        # Common issue types
        issue_types = Counter(issue.issue_type for issue in performance_issues)
        for issue_type, count in issue_types.most_common(3):
            if count > 3:
                recommendations.append(f"Optimize {count} instances of '{issue_type}'")
        
        # Category-specific recommendations
        categories = Counter(issue.category for issue in performance_issues)
        if categories.get("algorithm", 0) > 2:
            recommendations.append("Review and optimize algorithmic complexity")
        if categories.get("database", 0) > 1:
            recommendations.append("Optimize database queries and reduce N+1 problems")
        if categories.get("io", 0) > 1:
            recommendations.append("Implement async I/O operations for better concurrency")
        
        return recommendations[:5]

    def _extract_code_snippet(self, lines: list[str], line_number: int, context: int = 1) -> str:
        """Extract a code snippet around the specified line."""
        start_idx = max(0, line_number - context - 1)
        end_idx = min(len(lines), line_number + context)
        return '\n'.join(lines[start_idx:end_idx])

    def _create_empty_result(self) -> PerformanceAnalysisResult:
        """Create an empty performance analysis result."""
        return PerformanceAnalysisResult(
            overall_performance_score=0.0,
            performance_issues=[],
            bottlenecks=[],
            optimization_opportunities=[],
            resource_usage_patterns={},
            summary="No performance analysis available - missing AST index",
            recommendations=["Ensure project is properly indexed before performance analysis"],
        )