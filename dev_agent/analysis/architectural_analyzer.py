"""Architectural analyzer for detecting violations and design issues."""

from __future__ import annotations

import ast
import logging
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from ..interfaces.ai_analysis_interface import IArchitecturalAnalyzer
from ..interfaces.indexing_interface import IIndexingEngine
from ..models.analysis import ArchitecturalAnalysisResult, ArchitecturalViolation
from ..services.azure_openai_service import AzureOpenAIService, ChatMessage

logger = logging.getLogger(__name__)


class ArchitecturalAnalyzer(IArchitecturalAnalyzer):
    """Analyzer for architectural violations and design issues."""

    def __init__(
        self,
        indexing_engine: IIndexingEngine,
        ai_service: AzureOpenAIService | None = None,
    ):
        """Initialize the architectural analyzer.

        Args:
            indexing_engine: The indexing engine with parsed codebase data
            ai_service: AI service for enhanced analysis (optional)
        """
        self.indexing_engine = indexing_engine
        self.ai_service = ai_service
        self.ast_index = getattr(indexing_engine, "ast_index", None)

        # Architectural patterns and rules
        self._init_architectural_rules()

    def analyze(self, project_path: str) -> ArchitecturalAnalysisResult:
        """Perform comprehensive architectural analysis of the project.

        Args:
            project_path: Path to the project directory

        Returns:
            Architectural analysis results
        """
        logger.info(f"Analyzing architecture for {project_path}")

        if not self.ast_index:
            logger.warning("No AST index available for architectural analysis")
            return self._create_empty_result()

        # Analyze architectural violations
        violations = self.detect_violations(project_path)

        # Calculate metrics
        overall_score = self._calculate_architecture_score(violations)
        coupling_metrics = self.analyze_coupling(project_path)
        cohesion_metrics = self._analyze_cohesion(project_path)
        dependency_issues = self._analyze_dependency_issues(project_path)
        design_pattern_violations = self._detect_design_pattern_violations(project_path)

        # Generate summary and recommendations
        summary = self._generate_architecture_summary(violations, overall_score)
        recommendations = self._generate_architecture_recommendations(
            violations, coupling_metrics, cohesion_metrics, dependency_issues
        )

        return ArchitecturalAnalysisResult(
            overall_architecture_score=overall_score,
            violations=violations,
            coupling_metrics=coupling_metrics,
            cohesion_metrics=cohesion_metrics,
            dependency_issues=dependency_issues,
            design_pattern_violations=design_pattern_violations,
            summary=summary,
            recommendations=recommendations,
        )

    def detect_violations(self, project_path: str) -> list[ArchitecturalViolation]:
        """Detect architectural violations in the project.

        Args:
            project_path: Path to the project directory

        Returns:
            List of architectural violations
        """
        violations = []

        if not self.ast_index:
            return violations

        # Detect different types of violations
        violations.extend(self._detect_layer_violations(project_path))
        violations.extend(self._detect_dependency_violations(project_path))
        violations.extend(self._detect_coupling_violations(project_path))
        violations.extend(self._detect_cohesion_violations(project_path))
        violations.extend(self._detect_interface_violations(project_path))
        violations.extend(self._detect_separation_of_concerns_violations(project_path))

        return violations

    def analyze_dependencies(self, project_path: str) -> dict[str, Any]:
        """Analyze dependency structure of the project.

        Args:
            project_path: Path to the project directory

        Returns:
            Dictionary containing dependency analysis results
        """
        if not self.ast_index:
            return {}

        # Build dependency graph
        dependency_graph = self._build_dependency_graph()
        
        # Analyze dependency patterns
        circular_dependencies = self._detect_circular_dependencies(dependency_graph)
        dependency_depth = self._calculate_dependency_depth(dependency_graph)
        external_dependencies = self._analyze_external_dependencies()
        
        return {
            "dependency_graph": dependency_graph,
            "circular_dependencies": circular_dependencies,
            "dependency_depth": dependency_depth,
            "external_dependencies": external_dependencies,
            "total_internal_dependencies": len(dependency_graph),
        }

    def check_layer_violations(self, project_path: str) -> list[ArchitecturalViolation]:
        """Check for layer violations in the architecture.

        Args:
            project_path: Path to the project directory

        Returns:
            List of layer violations
        """
        violations = []

        if not self.ast_index:
            return violations

        # Define typical layers
        layers = self._identify_architectural_layers(project_path)
        
        # Check for violations between layers
        for file_path, metadata in self.ast_index.file_metadata.items():
            file_layer = self._determine_file_layer(file_path, layers)
            
            # Analyze imports to detect layer violations
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                    tree = ast.parse(code)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.Import, ast.ImportFrom)):
                            violation = self._check_import_layer_violation(
                                node, file_path, file_layer, layers
                            )
                            if violation:
                                violations.append(violation)
                                
            except Exception as e:
                logger.warning(f"Error analyzing layer violations in {file_path}: {e}")

        return violations

    def analyze_coupling(self, project_path: str) -> dict[str, float]:
        """Analyze coupling metrics for the project.

        Args:
            project_path: Path to the project directory

        Returns:
            Dictionary of coupling metrics
        """
        if not self.ast_index:
            return {}

        # Calculate different coupling metrics
        afferent_coupling = self._calculate_afferent_coupling()
        efferent_coupling = self._calculate_efferent_coupling()
        instability = self._calculate_instability(afferent_coupling, efferent_coupling)
        
        return {
            "average_afferent_coupling": sum(afferent_coupling.values()) / len(afferent_coupling) if afferent_coupling else 0,
            "average_efferent_coupling": sum(efferent_coupling.values()) / len(efferent_coupling) if efferent_coupling else 0,
            "average_instability": sum(instability.values()) / len(instability) if instability else 0,
            "max_afferent_coupling": max(afferent_coupling.values()) if afferent_coupling else 0,
            "max_efferent_coupling": max(efferent_coupling.values()) if efferent_coupling else 0,
        }

    def _init_architectural_rules(self) -> None:
        """Initialize architectural rules and patterns."""
        self.layer_hierarchy = {
            "presentation": ["business", "data"],
            "business": ["data"],
            "data": [],
        }
        
        self.forbidden_dependencies = [
            ("data", "presentation"),
            ("data", "business"),
        ]
        
        self.coupling_thresholds = {
            "high_afferent": 10,
            "high_efferent": 7,
            "high_instability": 0.8,
        }

    def _detect_layer_violations(self, project_path: str) -> list[ArchitecturalViolation]:
        """Detect violations of layered architecture."""
        violations = []
        
        # Identify layers based on directory structure
        layers = self._identify_architectural_layers(project_path)
        
        # Check each file for layer violations
        for file_path in self.ast_index.file_metadata.keys():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                    tree = ast.parse(code)
                    
                    current_layer = self._determine_file_layer(file_path, layers)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.Import, ast.ImportFrom)):
                            imported_module = self._get_imported_module(node)
                            if imported_module:
                                imported_layer = self._determine_module_layer(imported_module, layers)
                                
                                if self._is_layer_violation(current_layer, imported_layer):
                                    violations.append(
                                        ArchitecturalViolation(
                                            rule_name="Layer Separation",
                                            description=f"Layer '{current_layer}' should not depend on '{imported_layer}'",
                                            file_path=file_path,
                                            violation_type="layer",
                                            severity="medium",
                                            suggestion=f"Refactor to remove dependency from {current_layer} to {imported_layer}",
                                            affected_components=[current_layer, imported_layer],
                                            confidence=0.8,
                                        )
                                    )
                                    
            except Exception as e:
                logger.warning(f"Error detecting layer violations in {file_path}: {e}")
        
        return violations

    def _detect_dependency_violations(self, project_path: str) -> list[ArchitecturalViolation]:
        """Detect dependency-related violations."""
        violations = []
        
        # Build dependency graph
        dependency_graph = self._build_dependency_graph()
        
        # Detect circular dependencies
        circular_deps = self._detect_circular_dependencies(dependency_graph)
        for cycle in circular_deps:
            violations.append(
                ArchitecturalViolation(
                    rule_name="No Circular Dependencies",
                    description=f"Circular dependency detected: {' -> '.join(cycle)}",
                    file_path=cycle[0] if cycle else "",
                    violation_type="dependency",
                    severity="high",
                    suggestion="Break circular dependency by introducing interfaces or refactoring",
                    affected_components=cycle,
                    confidence=0.9,
                )
            )
        
        return violations

    def _detect_coupling_violations(self, project_path: str) -> list[ArchitecturalViolation]:
        """Detect high coupling violations."""
        violations = []
        
        # Calculate coupling metrics
        afferent_coupling = self._calculate_afferent_coupling()
        efferent_coupling = self._calculate_efferent_coupling()
        
        # Check for high coupling
        for module, coupling in efferent_coupling.items():
            if coupling > self.coupling_thresholds["high_efferent"]:
                violations.append(
                    ArchitecturalViolation(
                        rule_name="Low Coupling",
                        description=f"Module has high efferent coupling: {coupling}",
                        file_path=module,
                        violation_type="coupling",
                        severity="medium",
                        suggestion="Reduce dependencies by refactoring or using dependency injection",
                        affected_components=[module],
                        confidence=0.7,
                    )
                )
        
        for module, coupling in afferent_coupling.items():
            if coupling > self.coupling_thresholds["high_afferent"]:
                violations.append(
                    ArchitecturalViolation(
                        rule_name="Stable Dependencies",
                        description=f"Module has high afferent coupling: {coupling}",
                        file_path=module,
                        violation_type="coupling",
                        severity="low",
                        suggestion="Consider if this module should be split or if high coupling is justified",
                        affected_components=[module],
                        confidence=0.6,
                    )
                )
        
        return violations

    def _detect_cohesion_violations(self, project_path: str) -> list[ArchitecturalViolation]:
        """Detect low cohesion violations."""
        violations = []
        
        # Analyze cohesion for each class
        for class_def in self.ast_index.classes.values():
            cohesion_score = self._calculate_class_cohesion(class_def)
            
            if cohesion_score < 0.3:  # Low cohesion threshold
                violations.append(
                    ArchitecturalViolation(
                        rule_name="High Cohesion",
                        description=f"Class '{class_def.name}' has low cohesion: {cohesion_score:.2f}",
                        file_path=class_def.file_path,
                        violation_type="cohesion",
                        severity="medium",
                        suggestion="Consider splitting class based on single responsibility principle",
                        affected_components=[class_def.name],
                        confidence=0.7,
                    )
                )
        
        return violations

    def _detect_interface_violations(self, project_path: str) -> list[ArchitecturalViolation]:
        """Detect interface segregation violations."""
        violations = []
        
        # Look for large interfaces (many methods)
        for class_def in self.ast_index.classes.values():
            if len(class_def.methods) > 10:  # Large interface threshold
                # Check if it's likely an interface (abstract methods)
                abstract_methods = sum(1 for method in class_def.methods 
                                     if 'abstract' in method.name.lower() or 
                                        method.docstring and 'abstract' in method.docstring.lower())
                
                if abstract_methods > 5:
                    violations.append(
                        ArchitecturalViolation(
                            rule_name="Interface Segregation",
                            description=f"Interface '{class_def.name}' is too large with {len(class_def.methods)} methods",
                            file_path=class_def.file_path,
                            violation_type="interface",
                            severity="medium",
                            suggestion="Split large interface into smaller, more focused interfaces",
                            affected_components=[class_def.name],
                            confidence=0.6,
                        )
                    )
        
        return violations

    def _detect_separation_of_concerns_violations(self, project_path: str) -> list[ArchitecturalViolation]:
        """Detect separation of concerns violations."""
        violations = []
        
        # Look for classes that mix different concerns
        for class_def in self.ast_index.classes.values():
            concerns = self._identify_class_concerns(class_def)
            
            if len(concerns) > 2:  # Multiple concerns in one class
                violations.append(
                    ArchitecturalViolation(
                        rule_name="Separation of Concerns",
                        description=f"Class '{class_def.name}' mixes multiple concerns: {', '.join(concerns)}",
                        file_path=class_def.file_path,
                        violation_type="separation",
                        severity="medium",
                        suggestion="Split class to separate different concerns",
                        affected_components=[class_def.name],
                        confidence=0.6,
                    )
                )
        
        return violations

    def _identify_architectural_layers(self, project_path: str) -> dict[str, list[str]]:
        """Identify architectural layers based on directory structure."""
        layers = defaultdict(list)
        
        for file_path in self.ast_index.file_metadata.keys():
            path_parts = Path(file_path).parts
            
            # Common layer patterns
            for part in path_parts:
                if part.lower() in ['models', 'entities', 'data']:
                    layers['data'].append(file_path)
                elif part.lower() in ['services', 'business', 'logic', 'core']:
                    layers['business'].append(file_path)
                elif part.lower() in ['views', 'controllers', 'handlers', 'api', 'ui']:
                    layers['presentation'].append(file_path)
                elif part.lower() in ['utils', 'helpers', 'common']:
                    layers['utility'].append(file_path)
        
        return dict(layers)

    def _determine_file_layer(self, file_path: str, layers: dict[str, list[str]]) -> str:
        """Determine which layer a file belongs to."""
        for layer, files in layers.items():
            if file_path in files:
                return layer
        return "unknown"

    def _determine_module_layer(self, module_name: str, layers: dict[str, list[str]]) -> str:
        """Determine which layer a module belongs to based on its name."""
        # Simple heuristic based on module name
        module_lower = module_name.lower()
        
        if any(keyword in module_lower for keyword in ['model', 'entity', 'data']):
            return 'data'
        elif any(keyword in module_lower for keyword in ['service', 'business', 'logic']):
            return 'business'
        elif any(keyword in module_lower for keyword in ['view', 'controller', 'handler', 'api']):
            return 'presentation'
        else:
            return 'unknown'

    def _get_imported_module(self, node: ast.AST) -> str | None:
        """Get the module name from an import node."""
        if isinstance(node, ast.Import):
            return node.names[0].name if node.names else None
        elif isinstance(node, ast.ImportFrom):
            return node.module
        return None

    def _is_layer_violation(self, from_layer: str, to_layer: str) -> bool:
        """Check if importing from one layer to another violates architecture."""
        if from_layer == "unknown" or to_layer == "unknown":
            return False
        
        # Check forbidden dependencies
        return (from_layer, to_layer) in self.forbidden_dependencies

    def _build_dependency_graph(self) -> dict[str, list[str]]:
        """Build a dependency graph of the project."""
        dependency_graph = defaultdict(list)
        
        for file_path in self.ast_index.file_metadata.keys():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                    tree = ast.parse(code)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.Import, ast.ImportFrom)):
                            imported_module = self._get_imported_module(node)
                            if imported_module and not imported_module.startswith('.'):
                                # Only track internal dependencies
                                if any(imported_module.startswith(part) 
                                      for part in Path(file_path).parts):
                                    dependency_graph[file_path].append(imported_module)
                                    
            except Exception as e:
                logger.warning(f"Error building dependency graph for {file_path}: {e}")
        
        return dict(dependency_graph)

    def _detect_circular_dependencies(self, dependency_graph: dict[str, list[str]]) -> list[list[str]]:
        """Detect circular dependencies in the dependency graph."""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node: str, path: list[str]) -> None:
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in dependency_graph.get(node, []):
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        for node in dependency_graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles

    def _calculate_dependency_depth(self, dependency_graph: dict[str, list[str]]) -> dict[str, int]:
        """Calculate the dependency depth for each module."""
        depths = {}
        
        def calculate_depth(node: str, visited: set) -> int:
            if node in visited:
                return 0  # Circular dependency
            if node in depths:
                return depths[node]
            
            visited.add(node)
            max_depth = 0
            
            for dep in dependency_graph.get(node, []):
                depth = calculate_depth(dep, visited.copy())
                max_depth = max(max_depth, depth + 1)
            
            depths[node] = max_depth
            return max_depth
        
        for node in dependency_graph:
            calculate_depth(node, set())
        
        return depths

    def _analyze_external_dependencies(self) -> dict[str, int]:
        """Analyze external dependencies."""
        external_deps = Counter()
        
        for import_stmt in self.ast_index.imports:
            module = import_stmt.module.split('.')[0]
            # Check if it's an external dependency (not in standard library)
            if not module.startswith('.') and module not in ['os', 'sys', 'json', 'time', 'datetime']:
                external_deps[module] += 1
        
        return dict(external_deps)

    def _calculate_afferent_coupling(self) -> dict[str, int]:
        """Calculate afferent coupling (incoming dependencies) for each module."""
        afferent = defaultdict(int)
        
        for file_path in self.ast_index.file_metadata.keys():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                    tree = ast.parse(code)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.Import, ast.ImportFrom)):
                            imported_module = self._get_imported_module(node)
                            if imported_module:
                                afferent[imported_module] += 1
                                
            except Exception as e:
                logger.warning(f"Error calculating afferent coupling for {file_path}: {e}")
        
        return dict(afferent)

    def _calculate_efferent_coupling(self) -> dict[str, int]:
        """Calculate efferent coupling (outgoing dependencies) for each module."""
        efferent = defaultdict(int)
        
        for file_path in self.ast_index.file_metadata.keys():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                    tree = ast.parse(code)
                    
                    imports = 0
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.Import, ast.ImportFrom)):
                            imports += 1
                    
                    efferent[file_path] = imports
                    
            except Exception as e:
                logger.warning(f"Error calculating efferent coupling for {file_path}: {e}")
        
        return dict(efferent)

    def _calculate_instability(
        self, afferent: dict[str, int], efferent: dict[str, int]
    ) -> dict[str, float]:
        """Calculate instability metric (Ce / (Ca + Ce))."""
        instability = {}
        
        all_modules = set(afferent.keys()) | set(efferent.keys())
        
        for module in all_modules:
            ca = afferent.get(module, 0)  # Afferent coupling
            ce = efferent.get(module, 0)  # Efferent coupling
            
            if ca + ce == 0:
                instability[module] = 0.0
            else:
                instability[module] = ce / (ca + ce)
        
        return instability

    def _analyze_cohesion(self, project_path: str) -> dict[str, float]:
        """Analyze cohesion metrics for the project."""
        cohesion_scores = {}
        
        for class_def in self.ast_index.classes.values():
            cohesion_score = self._calculate_class_cohesion(class_def)
            cohesion_scores[class_def.name] = cohesion_score
        
        if cohesion_scores:
            return {
                "average_cohesion": sum(cohesion_scores.values()) / len(cohesion_scores),
                "min_cohesion": min(cohesion_scores.values()),
                "max_cohesion": max(cohesion_scores.values()),
            }
        else:
            return {"average_cohesion": 0.0, "min_cohesion": 0.0, "max_cohesion": 0.0}

    def _calculate_class_cohesion(self, class_def: Any) -> float:
        """Calculate cohesion score for a class using LCOM metric."""
        # Simplified LCOM (Lack of Cohesion of Methods) calculation
        methods = class_def.methods
        attributes = class_def.attributes
        
        if len(methods) <= 1:
            return 1.0  # Single method is perfectly cohesive
        
        # Count method pairs that share attributes
        shared_pairs = 0
        total_pairs = 0
        
        for i, method1 in enumerate(methods):
            for method2 in methods[i+1:]:
                total_pairs += 1
                # Simplified: assume methods share attributes if they have similar names
                # In practice, you'd analyze method bodies for attribute usage
                method1_name = getattr(method1, 'name', str(method1))
                method2_name = getattr(method2, 'name', str(method2))
                if any(str(attr) in method1_name.lower() or str(attr) in method2_name.lower() 
                       for attr in attributes):
                    shared_pairs += 1
        
        if total_pairs == 0:
            return 1.0
        
        cohesion = shared_pairs / total_pairs
        return cohesion

    def _analyze_dependency_issues(self, project_path: str) -> list[str]:
        """Analyze dependency-related issues."""
        issues = []
        
        # Build dependency graph
        dependency_graph = self._build_dependency_graph()
        
        # Check for common dependency issues
        circular_deps = self._detect_circular_dependencies(dependency_graph)
        if circular_deps:
            issues.append(f"Found {len(circular_deps)} circular dependencies")
        
        # Check dependency depth
        depths = self._calculate_dependency_depth(dependency_graph)
        max_depth = max(depths.values()) if depths else 0
        if max_depth > 5:
            issues.append(f"Deep dependency chains detected (max depth: {max_depth})")
        
        # Check for too many external dependencies
        external_deps = self._analyze_external_dependencies()
        if len(external_deps) > 20:
            issues.append(f"High number of external dependencies: {len(external_deps)}")
        
        return issues

    def _detect_design_pattern_violations(self, project_path: str) -> list[str]:
        """Detect violations of common design patterns."""
        violations = []
        
        # Check for singleton violations
        singletons = [cls for cls in self.ast_index.classes.values() 
                     if 'singleton' in cls.name.lower()]
        
        for singleton in singletons:
            # Check if singleton is properly implemented
            # This is a simplified check
            violations.append(f"Potential singleton pattern issue in {singleton.name}")
        
        return violations

    def _identify_class_concerns(self, class_def: Any) -> list[str]:
        """Identify the different concerns handled by a class."""
        concerns = set()
        
        # Analyze method names to identify concerns
        for method in class_def.methods:
            method_name = method.name.lower()
            
            if any(keyword in method_name for keyword in ['save', 'load', 'read', 'write']):
                concerns.add('data_access')
            if any(keyword in method_name for keyword in ['validate', 'check', 'verify']):
                concerns.add('validation')
            if any(keyword in method_name for keyword in ['format', 'render', 'display']):
                concerns.add('presentation')
            if any(keyword in method_name for keyword in ['calculate', 'compute', 'process']):
                concerns.add('business_logic')
            if any(keyword in method_name for keyword in ['log', 'audit', 'track']):
                concerns.add('logging')
        
        return list(concerns)

    def _calculate_architecture_score(self, violations: list[ArchitecturalViolation]) -> float:
        """Calculate overall architecture score based on violations."""
        if not violations:
            return 1.0

        # Weight violations by severity
        severity_weights = {
            "high": 1.0,
            "medium": 0.6,
            "low": 0.2,
        }

        total_penalty = 0.0
        for violation in violations:
            weight = severity_weights.get(violation.severity, 0.2)
            confidence_factor = violation.confidence
            total_penalty += weight * confidence_factor

        # Normalize score (assuming max 10 high-severity violations would give score 0)
        max_penalty = 10.0
        score = max(0.0, 1.0 - (total_penalty / max_penalty))
        
        return score

    def _generate_architecture_summary(
        self, violations: list[ArchitecturalViolation], overall_score: float
    ) -> str:
        """Generate a summary of the architectural analysis."""
        severity_counts = Counter(violation.severity for violation in violations)
        
        summary = f"Overall architecture score: {overall_score:.2f}/1.0. "
        summary += f"Found {len(violations)} architectural violations: "
        
        if severity_counts:
            parts = []
            for severity in ["high", "medium", "low"]:
                if severity_counts[severity] > 0:
                    parts.append(f"{severity_counts[severity]} {severity}")
            summary += ", ".join(parts) + "."
        else:
            summary += "No significant architectural violations found."
            
        return summary

    def _generate_architecture_recommendations(
        self,
        violations: list[ArchitecturalViolation],
        coupling_metrics: dict[str, float],
        cohesion_metrics: dict[str, float],
        dependency_issues: list[str],
    ) -> list[str]:
        """Generate architectural improvement recommendations."""
        recommendations = []
        
        # High severity violations
        high_severity = [v for v in violations if v.severity == "high"]
        if high_severity:
            recommendations.append(f"Address {len(high_severity)} high-severity architectural violations")
        
        # Coupling issues
        if coupling_metrics.get("average_efferent_coupling", 0) > 5:
            recommendations.append("Reduce coupling by implementing dependency injection or interfaces")
        
        # Cohesion issues
        if cohesion_metrics.get("average_cohesion", 1.0) < 0.5:
            recommendations.append("Improve class cohesion by following single responsibility principle")
        
        # Dependency issues
        if dependency_issues:
            recommendations.append("Resolve dependency issues to improve maintainability")
        
        # Common violation types
        violation_types = Counter(violation.violation_type for violation in violations)
        for violation_type, count in violation_types.most_common(3):
            if count > 2:
                recommendations.append(f"Address {count} instances of '{violation_type}' violations")
        
        return recommendations[:5]

    def _create_empty_result(self) -> ArchitecturalAnalysisResult:
        """Create an empty architectural analysis result."""
        return ArchitecturalAnalysisResult(
            overall_architecture_score=0.0,
            violations=[],
            coupling_metrics={},
            cohesion_metrics={},
            dependency_issues=[],
            design_pattern_violations=[],
            summary="No architectural analysis available - missing AST index",
            recommendations=["Ensure project is properly indexed before architectural analysis"],
        )