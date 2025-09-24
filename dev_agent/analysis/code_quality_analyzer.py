"""Code quality analyzer for identifying code smells and quality issues."""

from __future__ import annotations

import ast
import logging
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from ..interfaces.ai_analysis_interface import ICodeQualityAnalyzer
from ..interfaces.indexing_interface import IIndexingEngine
from ..models.analysis import CodeSmell, QualityAnalysisResult
from ..services.azure_openai_service import AzureOpenAIService, ChatMessage

logger = logging.getLogger(__name__)


class CodeQualityAnalyzer(ICodeQualityAnalyzer):
    """Analyzer for code quality issues, smells, and maintainability metrics."""

    def __init__(
        self,
        indexing_engine: IIndexingEngine,
        ai_service: AzureOpenAIService | None = None,
    ):
        """Initialize the code quality analyzer.

        Args:
            indexing_engine: The indexing engine with parsed codebase data
            ai_service: AI service for enhanced analysis (optional)
        """
        self.indexing_engine = indexing_engine
        self.ai_service = ai_service
        self.ast_index = getattr(indexing_engine, "ast_index", None)

    def analyze(self, project_path: str) -> QualityAnalysisResult:
        """Perform comprehensive quality analysis of the project.

        Args:
            project_path: Path to the project directory

        Returns:
            Quality analysis results
        """
        logger.info(f"Analyzing code quality for {project_path}")

        if not self.ast_index:
            logger.warning("No AST index available for quality analysis")
            return self._create_empty_result()

        # Analyze code smells
        code_smells = self._analyze_all_code_smells(project_path)

        # Calculate metrics
        maintainability_index = self._calculate_maintainability_index()
        complexity_metrics = self._calculate_complexity_metrics()
        duplication_percentage = self.detect_duplication(project_path)
        test_coverage_estimate = self._estimate_test_coverage()
        documentation_coverage = self._calculate_documentation_coverage()

        # Calculate overall score
        overall_score = self._calculate_overall_quality_score(
            code_smells,
            maintainability_index,
            complexity_metrics,
            duplication_percentage,
            test_coverage_estimate,
            documentation_coverage,
        )

        # Generate summary and recommendations
        summary = self._generate_quality_summary(code_smells, overall_score)
        recommendations = self._generate_quality_recommendations(
            code_smells, complexity_metrics, test_coverage_estimate, documentation_coverage
        )

        return QualityAnalysisResult(
            overall_score=overall_score,
            code_smells=code_smells,
            maintainability_index=maintainability_index,
            cyclomatic_complexity=complexity_metrics,
            duplication_percentage=duplication_percentage,
            test_coverage_estimate=test_coverage_estimate,
            documentation_coverage=documentation_coverage,
            summary=summary,
            recommendations=recommendations,
        )

    def analyze_code_smells(self, code: str, file_path: str) -> list[CodeSmell]:
        """Identify code smells and anti-patterns in the given code.

        Args:
            code: Source code to analyze
            file_path: Path to the file being analyzed

        Returns:
            List of identified code smells
        """
        smells = []

        try:
            tree = ast.parse(code)
            
            # Analyze different types of code smells
            smells.extend(self._detect_long_methods(tree, file_path, code))
            smells.extend(self._detect_large_classes(tree, file_path, code))
            smells.extend(self._detect_long_parameter_lists(tree, file_path, code))
            smells.extend(self._detect_duplicate_code(tree, file_path, code))
            smells.extend(self._detect_dead_code(tree, file_path, code))
            smells.extend(self._detect_god_objects(tree, file_path, code))
            smells.extend(self._detect_feature_envy(tree, file_path, code))
            smells.extend(self._detect_data_clumps(tree, file_path, code))

        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
            smells.append(
                CodeSmell(
                    name="Syntax Error",
                    description=f"File contains syntax errors: {e}",
                    file_path=file_path,
                    line_number=getattr(e, "lineno", 1),
                    severity="high",
                    category="maintainability",
                    suggestion="Fix syntax errors to enable proper analysis",
                    code_snippet="",
                    confidence=1.0,
                )
            )

        return smells

    def calculate_complexity_metrics(self, code: str) -> dict[str, float]:
        """Calculate complexity metrics for the given code.

        Args:
            code: Source code to analyze

        Returns:
            Dictionary of complexity metrics
        """
        try:
            tree = ast.parse(code)
            
            # Calculate cyclomatic complexity
            complexity_calculator = CyclomaticComplexityCalculator()
            complexity_calculator.visit(tree)
            
            return {
                "cyclomatic_complexity": complexity_calculator.complexity,
                "cognitive_complexity": self._calculate_cognitive_complexity(tree),
                "nesting_depth": self._calculate_max_nesting_depth(tree),
                "function_count": len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
                "class_count": len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
            }
        except SyntaxError:
            return {"error": "Syntax error in code"}

    def analyze_maintainability(self, code: str) -> float:
        """Calculate maintainability index for the given code.

        Args:
            code: Source code to analyze

        Returns:
            Maintainability index (0.0 to 1.0)
        """
        try:
            tree = ast.parse(code)
            
            # Calculate various metrics
            lines_of_code = len([line for line in code.split('\n') if line.strip()])
            complexity_metrics = self.calculate_complexity_metrics(code)
            
            # Simplified maintainability index calculation
            # Based on Halstead metrics and cyclomatic complexity
            cyclomatic_complexity = complexity_metrics.get("cyclomatic_complexity", 1)
            
            # Normalize to 0-1 scale
            maintainability = max(0.0, min(1.0, 1.0 - (cyclomatic_complexity / 50.0)))
            
            return maintainability
        except SyntaxError:
            return 0.0

    def detect_duplication(self, project_path: str) -> float:
        """Detect code duplication percentage in the project.

        Args:
            project_path: Path to the project directory

        Returns:
            Percentage of duplicated code (0.0 to 1.0)
        """
        if not self.ast_index:
            return 0.0

        # Simple duplication detection based on function signatures and structure
        function_signatures = []
        total_functions = 0

        for func_def in self.ast_index.functions.values():
            signature = f"{func_def.name}({','.join(func_def.parameters)})"
            function_signatures.append(signature)
            total_functions += 1

        if total_functions == 0:
            return 0.0

        # Count duplicates
        signature_counts = Counter(function_signatures)
        duplicates = sum(count - 1 for count in signature_counts.values() if count > 1)

        return duplicates / total_functions if total_functions > 0 else 0.0

    def _analyze_all_code_smells(self, project_path: str) -> list[CodeSmell]:
        """Analyze code smells across all files in the project."""
        all_smells = []

        if not self.ast_index:
            return all_smells

        # Analyze each file
        for file_path, metadata in self.ast_index.file_metadata.items():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                    file_smells = self.analyze_code_smells(code, file_path)
                    all_smells.extend(file_smells)
            except Exception as e:
                logger.warning(f"Error analyzing {file_path}: {e}")

        return all_smells

    def _detect_long_methods(self, tree: ast.AST, file_path: str, code: str) -> list[CodeSmell]:
        """Detect methods that are too long."""
        smells = []
        lines = code.split('\n')

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                method_length = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                
                if method_length > 50:  # Threshold for long methods
                    severity = "high" if method_length > 100 else "medium"
                    smells.append(
                        CodeSmell(
                            name="Long Method",
                            description=f"Method '{node.name}' is {method_length} lines long",
                            file_path=file_path,
                            line_number=node.lineno,
                            severity=severity,
                            category="maintainability",
                            suggestion="Consider breaking this method into smaller, more focused methods",
                            code_snippet=self._extract_code_snippet(lines, node.lineno, method_length),
                            confidence=0.9,
                        )
                    )

        return smells

    def _detect_large_classes(self, tree: ast.AST, file_path: str, code: str) -> list[CodeSmell]:
        """Detect classes that are too large."""
        smells = []
        lines = code.split('\n')

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                method_count = len([n for n in node.body if isinstance(n, ast.FunctionDef)])
                
                if method_count > 20:  # Threshold for large classes
                    severity = "high" if method_count > 30 else "medium"
                    smells.append(
                        CodeSmell(
                            name="Large Class",
                            description=f"Class '{node.name}' has {method_count} methods",
                            file_path=file_path,
                            line_number=node.lineno,
                            severity=severity,
                            category="design",
                            suggestion="Consider splitting this class into smaller, more cohesive classes",
                            code_snippet=self._extract_code_snippet(lines, node.lineno, 10),
                            confidence=0.8,
                        )
                    )

        return smells

    def _detect_long_parameter_lists(self, tree: ast.AST, file_path: str, code: str) -> list[CodeSmell]:
        """Detect methods with too many parameters."""
        smells = []
        lines = code.split('\n')

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                param_count = len(node.args.args)
                
                if param_count > 5:  # Threshold for long parameter lists
                    severity = "medium" if param_count <= 8 else "high"
                    smells.append(
                        CodeSmell(
                            name="Long Parameter List",
                            description=f"Method '{node.name}' has {param_count} parameters",
                            file_path=file_path,
                            line_number=node.lineno,
                            severity=severity,
                            category="design",
                            suggestion="Consider using parameter objects or reducing the number of parameters",
                            code_snippet=self._extract_code_snippet(lines, node.lineno, 3),
                            confidence=0.9,
                        )
                    )

        return smells

    def _detect_duplicate_code(self, tree: ast.AST, file_path: str, code: str) -> list[CodeSmell]:
        """Detect duplicate code blocks."""
        # This is a simplified implementation
        # In practice, you'd want more sophisticated duplicate detection
        return []

    def _detect_dead_code(self, tree: ast.AST, file_path: str, code: str) -> list[CodeSmell]:
        """Detect potentially dead/unused code."""
        smells = []
        lines = code.split('\n')

        # Look for functions that are never called (simplified)
        defined_functions = set()
        called_functions = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                defined_functions.add(node.name)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                called_functions.add(node.func.id)

        # Find potentially unused functions
        unused_functions = defined_functions - called_functions
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in unused_functions:
                # Skip special methods and test methods
                if not (node.name.startswith('_') or node.name.startswith('test_')):
                    smells.append(
                        CodeSmell(
                            name="Dead Code",
                            description=f"Function '{node.name}' appears to be unused",
                            file_path=file_path,
                            line_number=node.lineno,
                            severity="low",
                            category="maintainability",
                            suggestion="Consider removing unused code or verify if it's actually used",
                            code_snippet=self._extract_code_snippet(lines, node.lineno, 5),
                            confidence=0.6,
                        )
                    )

        return smells

    def _detect_god_objects(self, tree: ast.AST, file_path: str, code: str) -> list[CodeSmell]:
        """Detect god objects (classes that do too much)."""
        smells = []
        lines = code.split('\n')

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Count different types of responsibilities
                method_count = len([n for n in node.body if isinstance(n, ast.FunctionDef)])
                attribute_count = len([n for n in node.body if isinstance(n, ast.Assign)])
                
                # Simple heuristic for god objects
                if method_count > 15 and attribute_count > 10:
                    smells.append(
                        CodeSmell(
                            name="God Object",
                            description=f"Class '{node.name}' has too many responsibilities ({method_count} methods, {attribute_count} attributes)",
                            file_path=file_path,
                            line_number=node.lineno,
                            severity="high",
                            category="design",
                            suggestion="Consider splitting this class based on single responsibility principle",
                            code_snippet=self._extract_code_snippet(lines, node.lineno, 10),
                            confidence=0.7,
                        )
                    )

        return smells

    def _detect_feature_envy(self, tree: ast.AST, file_path: str, code: str) -> list[CodeSmell]:
        """Detect feature envy (methods that use other classes more than their own)."""
        # This would require more sophisticated analysis of method calls and dependencies
        return []

    def _detect_data_clumps(self, tree: ast.AST, file_path: str, code: str) -> list[CodeSmell]:
        """Detect data clumps (groups of data that appear together frequently)."""
        # This would require analysis across multiple methods and classes
        return []

    def _calculate_maintainability_index(self) -> float:
        """Calculate overall maintainability index for the project."""
        if not self.ast_index:
            return 0.0

        total_maintainability = 0.0
        file_count = 0

        for file_path in self.ast_index.file_metadata.keys():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                    maintainability = self.analyze_maintainability(code)
                    total_maintainability += maintainability
                    file_count += 1
            except Exception as e:
                logger.warning(f"Error calculating maintainability for {file_path}: {e}")

        return total_maintainability / file_count if file_count > 0 else 0.0

    def _calculate_complexity_metrics(self) -> dict[str, float]:
        """Calculate complexity metrics for the entire project."""
        if not self.ast_index:
            return {}

        total_complexity = 0.0
        max_complexity = 0.0
        function_count = 0

        for func_def in self.ast_index.functions.values():
            # Simplified complexity calculation
            # In practice, you'd want to parse the actual function body
            complexity = len(func_def.parameters) + 1  # Basic complexity estimate
            total_complexity += complexity
            max_complexity = max(max_complexity, complexity)
            function_count += 1

        avg_complexity = total_complexity / function_count if function_count > 0 else 0.0

        return {
            "average_complexity": avg_complexity,
            "max_complexity": max_complexity,
            "total_functions": function_count,
        }

    def _estimate_test_coverage(self) -> float:
        """Estimate test coverage based on test files and functions."""
        if not self.ast_index:
            return 0.0

        test_functions = 0
        total_functions = len(self.ast_index.functions)

        for func_def in self.ast_index.functions.values():
            if (func_def.name.startswith('test_') or 
                'test' in Path(func_def.file_path).name.lower()):
                test_functions += 1

        # Simple heuristic: assume each test function covers 2-3 regular functions
        estimated_coverage = min(1.0, (test_functions * 2.5) / total_functions) if total_functions > 0 else 0.0
        return estimated_coverage

    def _calculate_documentation_coverage(self) -> float:
        """Calculate documentation coverage based on docstrings."""
        if not self.ast_index:
            return 0.0

        documented_functions = 0
        total_functions = len(self.ast_index.functions)

        for func_def in self.ast_index.functions.values():
            if func_def.docstring:
                documented_functions += 1

        return documented_functions / total_functions if total_functions > 0 else 0.0

    def _calculate_overall_quality_score(
        self,
        code_smells: list[CodeSmell],
        maintainability_index: float,
        complexity_metrics: dict[str, float],
        duplication_percentage: float,
        test_coverage_estimate: float,
        documentation_coverage: float,
    ) -> float:
        """Calculate overall quality score."""
        # Count critical and high severity issues
        critical_issues = len([s for s in code_smells if s.severity == "critical"])
        high_issues = len([s for s in code_smells if s.severity == "high"])
        
        # Penalty for issues
        issue_penalty = (critical_issues * 0.1) + (high_issues * 0.05)
        
        # Base score from maintainability
        base_score = maintainability_index
        
        # Bonus for good practices
        coverage_bonus = test_coverage_estimate * 0.2
        documentation_bonus = documentation_coverage * 0.1
        
        # Penalty for duplication
        duplication_penalty = duplication_percentage * 0.3
        
        overall_score = base_score + coverage_bonus + documentation_bonus - issue_penalty - duplication_penalty
        
        return max(0.0, min(1.0, overall_score))

    def _generate_quality_summary(self, code_smells: list[CodeSmell], overall_score: float) -> str:
        """Generate a summary of the quality analysis."""
        severity_counts = Counter(smell.severity for smell in code_smells)
        
        summary = f"Overall quality score: {overall_score:.2f}/1.0. "
        summary += f"Found {len(code_smells)} code quality issues: "
        
        if severity_counts:
            parts = []
            for severity in ["critical", "high", "medium", "low"]:
                if severity_counts[severity] > 0:
                    parts.append(f"{severity_counts[severity]} {severity}")
            summary += ", ".join(parts) + "."
        else:
            summary += "No significant issues found."
            
        return summary

    def _generate_quality_recommendations(
        self,
        code_smells: list[CodeSmell],
        complexity_metrics: dict[str, float],
        test_coverage: float,
        documentation_coverage: float,
    ) -> list[str]:
        """Generate quality improvement recommendations."""
        recommendations = []
        
        # Critical and high severity issues
        critical_high = [s for s in code_smells if s.severity in ["critical", "high"]]
        if critical_high:
            recommendations.append(f"Address {len(critical_high)} critical/high severity code quality issues")
        
        # Test coverage
        if test_coverage < 0.8:
            recommendations.append(f"Increase test coverage from {test_coverage:.1%} to at least 80%")
        
        # Documentation
        if documentation_coverage < 0.7:
            recommendations.append(f"Improve documentation coverage from {documentation_coverage:.1%} to at least 70%")
        
        # Complexity
        avg_complexity = complexity_metrics.get("average_complexity", 0)
        if avg_complexity > 10:
            recommendations.append("Reduce code complexity by refactoring complex methods")
        
        # Common code smells
        smell_types = Counter(smell.name for smell in code_smells)
        for smell_type, count in smell_types.most_common(3):
            if count > 5:
                recommendations.append(f"Address {count} instances of '{smell_type}' code smell")
        
        return recommendations[:5]

    def _extract_code_snippet(self, lines: list[str], start_line: int, length: int) -> str:
        """Extract a code snippet from the given lines."""
        start_idx = max(0, start_line - 1)
        end_idx = min(len(lines), start_idx + length)
        return '\n'.join(lines[start_idx:end_idx])

    def _calculate_cognitive_complexity(self, tree: ast.AST) -> float:
        """Calculate cognitive complexity of the code."""
        # Simplified cognitive complexity calculation
        complexity = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(node, ast.Try):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
                
        return complexity

    def _calculate_max_nesting_depth(self, tree: ast.AST) -> int:
        """Calculate maximum nesting depth in the code."""
        class NestingDepthCalculator(ast.NodeVisitor):
            def __init__(self):
                self.max_depth = 0
                self.current_depth = 0
                
            def visit_If(self, node):
                self.current_depth += 1
                self.max_depth = max(self.max_depth, self.current_depth)
                self.generic_visit(node)
                self.current_depth -= 1
                
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
        
        calculator = NestingDepthCalculator()
        calculator.visit(tree)
        return calculator.max_depth

    def _create_empty_result(self) -> QualityAnalysisResult:
        """Create an empty quality analysis result."""
        return QualityAnalysisResult(
            overall_score=0.0,
            code_smells=[],
            maintainability_index=0.0,
            cyclomatic_complexity={},
            duplication_percentage=0.0,
            test_coverage_estimate=0.0,
            documentation_coverage=0.0,
            summary="No analysis available - missing AST index",
            recommendations=["Ensure project is properly indexed before analysis"],
        )


class CyclomaticComplexityCalculator(ast.NodeVisitor):
    """Calculator for cyclomatic complexity."""

    def __init__(self):
        self.complexity = 1  # Base complexity

    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_With(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_Assert(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        # Add complexity for each additional boolean operation
        self.complexity += len(node.values) - 1
        self.generic_visit(node)