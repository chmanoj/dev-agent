"""Intelligent code generator with refactoring capabilities.

This module provides advanced code generation that not only creates new code
but also refactors existing codebase to maintain consistency and reduce duplication.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..interfaces.analysis_interface import ICodebaseAnalyzer
from ..interfaces.generation_interface import IPythonCodeGenerator
from ..models.analysis import (
    CodeContext,
    CodePattern,
    CodePatterns,
    ContextualCode,
    LanguageInfo,
)
from ..models.documents import Task
from ..models.indexing import ASTIndex
from ..models.results import GeneratedCode


@dataclass
class RefactoringOpportunity:
    """Represents a refactoring opportunity in the codebase."""

    file_path: str
    line_start: int
    line_end: int
    refactoring_type: str  # 'extract_method', 'remove_duplication', 'rename', etc.
    description: str
    suggested_change: str
    confidence: float
    impact_files: list[str]


@dataclass
class RelatedFileUpdate:
    """Represents an update needed in a related file."""

    file_path: str
    update_type: str  # 'import', 'configuration', 'dependency', 'api_client'
    old_content: str
    new_content: str
    line_number: int | None = None
    reason: str = ""


@dataclass
class GenerationContext:
    """Extended context for intelligent code generation."""

    task: Task
    target_language: str
    framework_context: dict[str, Any]
    existing_patterns: list[CodePattern]
    architectural_constraints: list[str]
    quality_requirements: dict[str, Any]
    team_conventions: dict[str, Any]
    integration_requirements: list[str]
    refactoring_opportunities: list[RefactoringOpportunity]
    related_files: list[str]


@dataclass
class IntelligentGenerationResult:
    """Result of intelligent code generation with refactoring."""

    primary_code: GeneratedCode
    refactored_files: list[tuple[str, str]]  # (file_path, new_content)
    related_updates: list[RelatedFileUpdate]
    generated_tests: list[GeneratedCode]
    documentation_updates: list[tuple[str, str]]  # (file_path, new_content)
    migration_scripts: list[GeneratedCode]
    api_changes: list[dict[str, Any]]
    summary: str


class IntelligentCodeGenerator:
    """Advanced code generator with refactoring and consistency maintenance."""

    def __init__(
        self,
        codebase_analyzer: ICodebaseAnalyzer,
        base_generator: IPythonCodeGenerator,
    ):
        """Initialize the intelligent code generator.

        Args:
            codebase_analyzer: Analyzer for extracting codebase patterns
            base_generator: Base code generator for standard generation
        """
        self.codebase_analyzer = codebase_analyzer
        self.base_generator = base_generator
        self.refactoring_engine = RefactoringEngine(codebase_analyzer)
        self.test_generator = AutomaticTestGenerator(codebase_analyzer)
        self.file_updater = RelatedFileUpdater(codebase_analyzer)
        self.api_propagator = APIUpdatePropagator(codebase_analyzer)
        self.db_manager = DatabaseChangeManager(codebase_analyzer)

    def generate_with_refactoring(
        self, task: Task, context: CodeContext
    ) -> IntelligentGenerationResult:
        """Generate code while refactoring existing codebase for consistency.

        Args:
            task: Task to implement
            context: Code context with relevant information

        Returns:
            Comprehensive generation result with refactoring
        """
        # Create extended generation context
        generation_context = self._create_generation_context(task, context)

        # Generate primary code
        primary_code = self.base_generator.generate_code_from_task(task, context)

        # Identify refactoring opportunities
        refactoring_opportunities = self.refactoring_engine.identify_opportunities(
            primary_code, generation_context
        )

        # Apply refactoring to existing code
        refactored_files = self.refactoring_engine.apply_refactoring(
            refactoring_opportunities, generation_context
        )

        # Generate comprehensive tests
        generated_tests = self.test_generator.generate_comprehensive_tests(
            primary_code, generation_context
        )

        # Update related files
        related_updates = self.file_updater.update_related_files(
            primary_code, generation_context
        )

        # Handle API changes and propagation
        api_changes = self.api_propagator.propagate_api_changes(
            primary_code, generation_context
        )

        # Generate database migrations if needed
        migration_scripts = self.db_manager.generate_migrations(
            primary_code, generation_context
        )

        # Update documentation
        documentation_updates = self._update_documentation(
            primary_code, generation_context
        )

        # Create summary
        summary = self._create_generation_summary(
            primary_code, refactored_files, related_updates, generated_tests
        )

        return IntelligentGenerationResult(
            primary_code=primary_code,
            refactored_files=refactored_files,
            related_updates=related_updates,
            generated_tests=generated_tests,
            documentation_updates=documentation_updates,
            migration_scripts=migration_scripts,
            api_changes=api_changes,
            summary=summary,
        )

    def ensure_architectural_consistency(
        self, new_code: str, architecture: dict[str, Any]
    ) -> str:
        """Ensure new code follows architectural patterns and constraints.

        Args:
            new_code: Generated code to validate
            architecture: Architecture information and constraints

        Returns:
            Code adjusted for architectural consistency
        """
        # Validate against architectural patterns
        violations = self._detect_architectural_violations(new_code, architecture)

        # Apply architectural fixes
        for violation in violations:
            new_code = self._fix_architectural_violation(new_code, violation)

        # Ensure layer separation
        new_code = self._enforce_layer_separation(new_code, architecture)

        # Validate dependency direction
        new_code = self._validate_dependency_direction(new_code, architecture)

        return new_code

    def _create_generation_context(
        self, task: Task, context: CodeContext
    ) -> GenerationContext:
        """Create extended generation context with additional information."""
        # Analyze existing patterns
        patterns = self.base_generator.analyze_existing_patterns()

        # Identify architectural constraints
        architectural_constraints = self._identify_architectural_constraints(task)

        # Determine quality requirements
        quality_requirements = self._determine_quality_requirements(task)

        # Extract team conventions
        team_conventions = self._extract_team_conventions()

        # Identify integration requirements
        integration_requirements = self._identify_integration_requirements(task)

        # Find related files
        related_files = self._find_related_files(task, context)

        return GenerationContext(
            task=task,
            target_language="python",  # Default to Python for now
            framework_context={},
            existing_patterns=patterns.structural_patterns if patterns else [],
            architectural_constraints=architectural_constraints,
            quality_requirements=quality_requirements,
            team_conventions=team_conventions,
            integration_requirements=integration_requirements,
            refactoring_opportunities=[],
            related_files=related_files,
        )

    def _identify_architectural_constraints(self, task: Task) -> list[str]:
        """Identify architectural constraints for the task."""
        constraints = []

        task_desc = task.description.lower()

        # Layer constraints
        if "model" in task_desc or "data" in task_desc:
            constraints.append("data_layer_only")
        elif "service" in task_desc or "business" in task_desc:
            constraints.append("service_layer_only")
        elif "controller" in task_desc or "api" in task_desc:
            constraints.append("presentation_layer_only")

        # Dependency constraints
        if "interface" in task_desc:
            constraints.append("no_concrete_dependencies")
        if "test" in task_desc:
            constraints.append("test_isolation")

        return constraints

    def _determine_quality_requirements(self, task: Task) -> dict[str, Any]:
        """Determine quality requirements for the task."""
        requirements = {
            "test_coverage": 90.0,
            "complexity_limit": 10,
            "documentation_required": True,
            "type_hints_required": True,
            "error_handling_required": True,
        }

        task_desc = task.description.lower()

        # Adjust based on task type
        if "critical" in task_desc or "security" in task_desc:
            requirements["test_coverage"] = 100.0
            requirements["complexity_limit"] = 5

        if "utility" in task_desc or "helper" in task_desc:
            requirements["test_coverage"] = 80.0

        return requirements

    def _extract_team_conventions(self) -> dict[str, Any]:
        """Extract team coding conventions from existing codebase."""
        patterns = self.base_generator.analyze_existing_patterns()

        conventions = {
            "naming_style": "snake_case",
            "docstring_style": "google",
            "import_style": "absolute",
            "error_handling_style": "explicit",
            "logging_style": "structured",
        }

        if patterns and patterns.naming_conventions:
            # Extract actual conventions from patterns
            for pattern in patterns.naming_conventions:
                if pattern.confidence > 0.8:
                    if "function" in pattern.pattern_type:
                        conventions["function_naming"] = pattern.description
                    elif "class" in pattern.pattern_type:
                        conventions["class_naming"] = pattern.description

        return conventions

    def _identify_integration_requirements(self, task: Task) -> list[str]:
        """Identify integration requirements for the task."""
        requirements = []

        task_desc = task.description.lower()

        if "database" in task_desc or "sql" in task_desc:
            requirements.append("database_integration")
        if "api" in task_desc or "rest" in task_desc:
            requirements.append("api_integration")
        if "config" in task_desc or "settings" in task_desc:
            requirements.append("configuration_integration")
        if "log" in task_desc:
            requirements.append("logging_integration")
        if "cache" in task_desc:
            requirements.append("caching_integration")

        return requirements

    def _find_related_files(self, task: Task, context: CodeContext) -> list[str]:
        """Find files related to the task implementation."""
        related_files = []

        # Add files from context
        related_files.extend(context.relevant_files)

        # Find files based on task content
        task_desc = task.description.lower()

        if "test" in task_desc:
            # Find corresponding source files
            test_files = [f for f in context.relevant_files if "test" in f]
            for test_file in test_files:
                source_file = test_file.replace("test_", "").replace("tests/", "")
                if Path(source_file).exists():
                    related_files.append(source_file)

        # Find configuration files
        config_extensions = [".json", ".yaml", ".yml", ".toml", ".ini"]
        for ext in config_extensions:
            config_files = list(Path(".").glob(f"**/*{ext}"))
            related_files.extend([str(f) for f in config_files[:5]])  # Limit to 5

        return list(set(related_files))  # Remove duplicates

    def _update_documentation(
        self, primary_code: GeneratedCode, context: GenerationContext
    ) -> list[tuple[str, str]]:
        """Update documentation based on generated code."""
        documentation_updates = []

        # Update README if it exists
        readme_files = ["README.md", "README.rst", "README.txt"]
        for readme_file in readme_files:
            if Path(readme_file).exists():
                updated_content = self._update_readme(readme_file, primary_code, context)
                if updated_content:
                    documentation_updates.append((readme_file, updated_content))

        # Update API documentation
        api_doc_files = list(Path("docs").glob("**/*.md")) if Path("docs").exists() else []
        for doc_file in api_doc_files:
            if "api" in doc_file.name.lower():
                updated_content = self._update_api_docs(str(doc_file), primary_code, context)
                if updated_content:
                    documentation_updates.append((str(doc_file), updated_content))

        return documentation_updates

    def _update_readme(
        self, readme_file: str, primary_code: GeneratedCode, context: GenerationContext
    ) -> str | None:
        """Update README file with new feature information."""
        try:
            with open(readme_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Add feature description if it's a significant addition
            if self._is_significant_feature(context.task):
                feature_section = self._generate_feature_section(context.task, primary_code)
                
                # Find appropriate place to insert
                if "## Features" in content:
                    content = content.replace(
                        "## Features",
                        f"## Features\n\n{feature_section}"
                    )
                elif "# Features" in content:
                    content = content.replace(
                        "# Features",
                        f"# Features\n\n{feature_section}"
                    )
                else:
                    # Add at the end
                    content += f"\n\n## Features\n\n{feature_section}"

            return content

        except Exception:
            return None

    def _update_api_docs(
        self, doc_file: str, primary_code: GeneratedCode, context: GenerationContext
    ) -> str | None:
        """Update API documentation with new endpoints or changes."""
        try:
            with open(doc_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract API information from generated code
            api_info = self._extract_api_info(primary_code.code)
            
            if api_info:
                api_section = self._generate_api_section(api_info)
                content += f"\n\n{api_section}"

            return content

        except Exception:
            return None

    def _create_generation_summary(
        self,
        primary_code: GeneratedCode,
        refactored_files: list[tuple[str, str]],
        related_updates: list[RelatedFileUpdate],
        generated_tests: list[GeneratedCode],
    ) -> str:
        """Create a summary of the generation process."""
        summary_parts = []

        summary_parts.append(f"Generated primary code: {primary_code.file_path}")
        
        if refactored_files:
            summary_parts.append(f"Refactored {len(refactored_files)} existing files")
            
        if related_updates:
            summary_parts.append(f"Updated {len(related_updates)} related files")
            
        if generated_tests:
            summary_parts.append(f"Generated {len(generated_tests)} test files")

        return "; ".join(summary_parts)

    def _detect_architectural_violations(
        self, code: str, architecture: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Detect violations of architectural patterns."""
        violations = []

        try:
            tree = ast.parse(code)
            
            # Check for layer violations
            for node in ast.walk(tree):
                if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    violation = self._check_layer_violation(node, architecture)
                    if violation:
                        violations.append(violation)

        except SyntaxError:
            pass

        return violations

    def _check_layer_violation(
        self, import_node: ast.Import | ast.ImportFrom, architecture: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Check if an import violates layer architecture."""
        # This is a simplified implementation
        # In practice, you'd have more sophisticated layer rules
        
        if isinstance(import_node, ast.ImportFrom) and import_node.module:
            module = import_node.module
            
            # Example: data layer shouldn't import from presentation layer
            if "models" in module and ("controllers" in module or "views" in module):
                return {
                    "type": "layer_violation",
                    "description": "Data layer importing from presentation layer",
                    "module": module,
                    "line": import_node.lineno,
                }

        return None

    def _fix_architectural_violation(
        self, code: str, violation: dict[str, Any]
    ) -> str:
        """Fix an architectural violation in the code."""
        # This would implement specific fixes based on violation type
        # For now, just return the original code
        return code

    def _enforce_layer_separation(
        self, code: str, architecture: dict[str, Any]
    ) -> str:
        """Enforce proper layer separation in the code."""
        # Implementation would reorganize imports and dependencies
        # to respect layer boundaries
        return code

    def _validate_dependency_direction(
        self, code: str, architecture: dict[str, Any]
    ) -> str:
        """Validate and fix dependency direction issues."""
        # Implementation would ensure dependencies flow in the correct direction
        # (e.g., from higher to lower layers)
        return code

    def _is_significant_feature(self, task: Task) -> bool:
        """Determine if the task represents a significant feature."""
        significant_keywords = [
            "implement", "create", "build", "add", "new", "feature",
            "system", "service", "component", "module"
        ]
        
        task_text = f"{task.title} {task.description}".lower()
        return any(keyword in task_text for keyword in significant_keywords)

    def _generate_feature_section(self, task: Task, primary_code: GeneratedCode) -> str:
        """Generate a feature section for documentation."""
        return f"- **{task.title}**: {task.description}"

    def _extract_api_info(self, code: str) -> dict[str, Any] | None:
        """Extract API information from generated code."""
        try:
            tree = ast.parse(code)
            
            # Look for FastAPI decorators or similar patterns
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call) and hasattr(decorator.func, 'attr'):
                            if decorator.func.attr in ['get', 'post', 'put', 'delete']:
                                return {
                                    "method": decorator.func.attr.upper(),
                                    "function": node.name,
                                    "endpoint": self._extract_endpoint_path(decorator)
                                }
        except SyntaxError:
            pass
            
        return None

    def _extract_endpoint_path(self, decorator: ast.Call) -> str:
        """Extract endpoint path from decorator."""
        if decorator.args and isinstance(decorator.args[0], ast.Constant):
            return decorator.args[0].value
        return "/"

    def _generate_api_section(self, api_info: dict[str, Any]) -> str:
        """Generate API documentation section."""
        return f"""### {api_info['method']} {api_info['endpoint']}

**Function**: `{api_info['function']}`

Description: Auto-generated endpoint.
"""


class RefactoringEngine:
    """Engine for identifying and applying refactoring opportunities."""

    def __init__(self, codebase_analyzer: ICodebaseAnalyzer):
        """Initialize the refactoring engine."""
        self.codebase_analyzer = codebase_analyzer

    def identify_opportunities(
        self, primary_code: GeneratedCode, context: GenerationContext
    ) -> list[RefactoringOpportunity]:
        """Identify refactoring opportunities in existing code."""
        opportunities = []

        # Find code duplication
        opportunities.extend(self._find_code_duplication(primary_code, context))

        # Find long methods/functions
        opportunities.extend(self._find_long_methods(context))

        # Find naming inconsistencies
        opportunities.extend(self._find_naming_inconsistencies(primary_code, context))

        return opportunities

    def apply_refactoring(
        self, opportunities: list[RefactoringOpportunity], context: GenerationContext
    ) -> list[tuple[str, str]]:
        """Apply refactoring opportunities to existing files."""
        refactored_files = []

        for opportunity in opportunities:
            if opportunity.confidence > 0.7:  # Only apply high-confidence refactoring
                refactored_content = self._apply_single_refactoring(opportunity)
                if refactored_content:
                    refactored_files.append((opportunity.file_path, refactored_content))

        return refactored_files

    def _find_code_duplication(
        self, primary_code: GeneratedCode, context: GenerationContext
    ) -> list[RefactoringOpportunity]:
        """Find code duplication opportunities."""
        opportunities = []

        # This is a simplified implementation
        # In practice, you'd use more sophisticated duplication detection
        
        for file_path in context.related_files:
            if Path(file_path).exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        existing_code = f.read()
                    
                    # Simple similarity check
                    similarity = self._calculate_similarity(primary_code.code, existing_code)
                    
                    if similarity > 0.8:
                        opportunities.append(RefactoringOpportunity(
                            file_path=file_path,
                            line_start=1,
                            line_end=len(existing_code.split('\n')),
                            refactoring_type="remove_duplication",
                            description=f"High similarity with new code: {similarity:.2f}",
                            suggested_change="Extract common functionality",
                            confidence=similarity,
                            impact_files=[file_path, primary_code.file_path]
                        ))
                except Exception:
                    continue

        return opportunities

    def _find_long_methods(self, context: GenerationContext) -> list[RefactoringOpportunity]:
        """Find methods that are too long and should be refactored."""
        opportunities = []

        for file_path in context.related_files:
            if Path(file_path).exists() and file_path.endswith('.py'):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            method_length = node.end_lineno - node.lineno if node.end_lineno else 0
                            
                            if method_length > 50:  # Arbitrary threshold
                                opportunities.append(RefactoringOpportunity(
                                    file_path=file_path,
                                    line_start=node.lineno,
                                    line_end=node.end_lineno or node.lineno,
                                    refactoring_type="extract_method",
                                    description=f"Method {node.name} is too long ({method_length} lines)",
                                    suggested_change="Break into smaller methods",
                                    confidence=0.8,
                                    impact_files=[file_path]
                                ))
                except Exception:
                    continue

        return opportunities

    def _find_naming_inconsistencies(
        self, primary_code: GeneratedCode, context: GenerationContext
    ) -> list[RefactoringOpportunity]:
        """Find naming inconsistencies that should be fixed."""
        opportunities = []

        # Extract naming patterns from new code
        new_patterns = self._extract_naming_patterns(primary_code.code)

        for file_path in context.related_files:
            if Path(file_path).exists() and file_path.endswith('.py'):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    existing_patterns = self._extract_naming_patterns(content)
                    
                    # Compare patterns and find inconsistencies
                    inconsistencies = self._compare_naming_patterns(new_patterns, existing_patterns)
                    
                    for inconsistency in inconsistencies:
                        opportunities.append(RefactoringOpportunity(
                            file_path=file_path,
                            line_start=inconsistency.get('line', 1),
                            line_end=inconsistency.get('line', 1),
                            refactoring_type="rename",
                            description=f"Naming inconsistency: {inconsistency['description']}",
                            suggested_change=inconsistency['suggestion'],
                            confidence=0.6,
                            impact_files=[file_path]
                        ))
                except Exception:
                    continue

        return opportunities

    def _apply_single_refactoring(self, opportunity: RefactoringOpportunity) -> str | None:
        """Apply a single refactoring opportunity."""
        try:
            with open(opportunity.file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if opportunity.refactoring_type == "remove_duplication":
                return self._remove_duplication(content, opportunity)
            elif opportunity.refactoring_type == "extract_method":
                return self._extract_method(content, opportunity)
            elif opportunity.refactoring_type == "rename":
                return self._apply_rename(content, opportunity)

        except Exception:
            pass

        return None

    def _calculate_similarity(self, code1: str, code2: str) -> float:
        """Calculate similarity between two code snippets."""
        # Simple implementation using line-by-line comparison
        lines1 = set(line.strip() for line in code1.split('\n') if line.strip())
        lines2 = set(line.strip() for line in code2.split('\n') if line.strip())
        
        if not lines1 or not lines2:
            return 0.0
        
        intersection = len(lines1.intersection(lines2))
        union = len(lines1.union(lines2))
        
        return intersection / union if union > 0 else 0.0

    def _extract_naming_patterns(self, code: str) -> dict[str, list[str]]:
        """Extract naming patterns from code."""
        patterns = {
            'functions': [],
            'classes': [],
            'variables': []
        }

        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    patterns['functions'].append(node.name)
                elif isinstance(node, ast.ClassDef):
                    patterns['classes'].append(node.name)
                elif isinstance(node, ast.Name):
                    patterns['variables'].append(node.id)
        except SyntaxError:
            pass

        return patterns

    def _compare_naming_patterns(
        self, new_patterns: dict[str, list[str]], existing_patterns: dict[str, list[str]]
    ) -> list[dict[str, Any]]:
        """Compare naming patterns and find inconsistencies."""
        inconsistencies = []

        # Check function naming consistency
        new_func_style = self._detect_naming_style(new_patterns.get('functions', []))
        existing_func_style = self._detect_naming_style(existing_patterns.get('functions', []))

        if new_func_style != existing_func_style and both_styles_detected(new_func_style, existing_func_style):
            inconsistencies.append({
                'description': f'Function naming style mismatch: {new_func_style} vs {existing_func_style}',
                'suggestion': f'Use consistent {new_func_style} style',
                'line': 1
            })

        return inconsistencies

    def _detect_naming_style(self, names: list[str]) -> str:
        """Detect the naming style used in a list of names."""
        if not names:
            return 'unknown'

        snake_case_count = sum(1 for name in names if '_' in name and name.islower())
        camel_case_count = sum(1 for name in names if any(c.isupper() for c in name[1:]) and '_' not in name)

        if snake_case_count > camel_case_count:
            return 'snake_case'
        elif camel_case_count > snake_case_count:
            return 'camelCase'
        else:
            return 'mixed'

    def _remove_duplication(self, content: str, opportunity: RefactoringOpportunity) -> str:
        """Remove code duplication."""
        # Simplified implementation - in practice, this would be more sophisticated
        return content

    def _extract_method(self, content: str, opportunity: RefactoringOpportunity) -> str:
        """Extract long method into smaller methods."""
        # Simplified implementation - in practice, this would analyze the method
        # and extract logical chunks into separate methods
        return content

    def _apply_rename(self, content: str, opportunity: RefactoringOpportunity) -> str:
        """Apply renaming refactoring."""
        # Simplified implementation - in practice, this would use AST manipulation
        # to safely rename symbols
        return content


def both_styles_detected(style1: str, style2: str) -> bool:
    """Check if both naming styles are actually detected (not unknown/mixed)."""
    valid_styles = {'snake_case', 'camelCase'}
    return style1 in valid_styles and style2 in valid_styles