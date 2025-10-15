"""Codebase analyzer for extracting architecture patterns and code conventions."""

import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from ..interfaces.analysis_interface import ICodebaseAnalyzer
from ..interfaces.indexing_interface import IIndexingEngine
from ..models.analysis import (
    ArchitectureInfo,
    ArchitecturePattern,
    CodeContext,
    CodeExample,
    CodePattern,
    CodePatterns,
    ComponentAnalysis,
    ContextualCode,
    DesignAnalysis,
    RequirementEvidence,
    SpecificationAnalysis,
)
from ..models.documents import Task
from ..models.indexing import ASTIndex


class CodebaseAnalyzer(ICodebaseAnalyzer):
    """Analyzes codebase to extract patterns, architecture, and context for code generation."""

    def __init__(self, indexing_engine: IIndexingEngine):
        """Initialize the codebase analyzer.

        Args:
            indexing_engine: The indexing engine with parsed codebase data
        """
        self.indexing_engine = indexing_engine
        self.ast_index: ASTIndex | None = None
        self._load_index()

    def _load_index(self) -> None:
        """Load the AST index from the indexing engine."""
        try:
            symbol_map = self.indexing_engine.get_symbol_map()
            if symbol_map:
                if (
                    hasattr(self.indexing_engine, "ast_index")
                    and self.indexing_engine.ast_index
                ):
                    self.ast_index = self.indexing_engine.ast_index
                else:
                    print(
                        "Warning: No AST index available. Some analysis features may be limited."
                    )
            else:
                print("Warning: No symbol map available. Index may need to be built.")
        except Exception as e:
            print(f"Warning: Error loading index: {e}")

    def analyze_for_specification(self) -> SpecificationAnalysis:
        """Analyze codebase to generate specification requirements."""
        if not self.ast_index:
            return SpecificationAnalysis(
                project_purpose="New software project",
                main_features=[],
                user_roles=["User"],
                functional_areas=[],
                technology_constraints=["Python 3.x"],
                requirement_evidence=[],
                external_dependencies=[],
                confidence_score=0.1,
            )

        # Analyze project structure and patterns
        project_purpose = self._infer_project_purpose()
        main_features = self._extract_main_features()
        user_roles = self._identify_user_roles()
        functional_areas = self._identify_functional_areas()
        technology_constraints = self._identify_technology_constraints()
        requirement_evidence = self._extract_requirement_evidence()
        external_dependencies = self._analyze_external_dependencies()

        # Calculate confidence based on available information
        confidence_score = self._calculate_specification_confidence(
            main_features, functional_areas, requirement_evidence
        )

        return SpecificationAnalysis(
            project_purpose=project_purpose,
            main_features=main_features,
            user_roles=user_roles,
            functional_areas=functional_areas,
            technology_constraints=technology_constraints,
            requirement_evidence=requirement_evidence,
            external_dependencies=external_dependencies,
            confidence_score=confidence_score,
        )

    def analyze_for_design(self) -> DesignAnalysis:
        """Analyze codebase to understand current architecture and design."""
        if not self.ast_index:
            return DesignAnalysis(
                architecture_overview="Unable to analyze - no index available",
                components=[],
                data_models=[],
                api_interfaces=[],
                design_patterns=[],
                quality_metrics={},
                technical_debt=[],
                recommendations=[],
            )

        architecture_overview = self._generate_architecture_overview()
        components = self._analyze_components()
        data_models = self._extract_data_models()
        api_interfaces = self._identify_api_interfaces()
        design_patterns = self._detect_design_patterns()
        quality_metrics = self._calculate_quality_metrics()
        technical_debt = self._identify_technical_debt()
        recommendations = self._generate_design_recommendations()

        return DesignAnalysis(
            architecture_overview=architecture_overview,
            components=components,
            data_models=data_models,
            api_interfaces=api_interfaces,
            design_patterns=design_patterns,
            quality_metrics=quality_metrics,
            technical_debt=technical_debt,
            recommendations=recommendations,
        )

    def extract_architecture_patterns(self) -> ArchitectureInfo:
        """Extract architectural patterns from the codebase."""
        if not self.ast_index:
            return ArchitectureInfo(
                patterns=[],
                layers=[],
                components=[],
                dependencies={},
                entry_points=[],
                data_flow={},
                technology_stack=[],
            )

        patterns = self._detect_architecture_patterns()
        layers = self._identify_layers()
        components = self._extract_components()
        dependencies = self._analyze_component_dependencies()
        entry_points = self._find_entry_points()
        data_flow = self._analyze_data_flow()
        technology_stack = self._identify_technology_stack()

        return ArchitectureInfo(
            patterns=patterns,
            layers=layers,
            components=components,
            dependencies=dependencies,
            entry_points=entry_points,
            data_flow=data_flow,
            technology_stack=technology_stack,
        )

    def identify_code_patterns(self) -> CodePatterns:
        """Identify coding patterns and conventions."""
        if not self.ast_index:
            return CodePatterns(
                naming_conventions=[],
                structural_patterns=[],
                import_patterns=[],
                error_handling_patterns=[],
                testing_patterns=[],
                documentation_patterns=[],
                overall_style={},
            )

        naming_conventions = self._analyze_naming_conventions()
        structural_patterns = self._detect_structural_patterns()
        import_patterns = self._analyze_import_patterns()
        error_handling_patterns = self._detect_error_handling_patterns()
        testing_patterns = self._analyze_testing_patterns()
        documentation_patterns = self._detect_documentation_patterns()
        overall_style = self._determine_overall_style()

        return CodePatterns(
            naming_conventions=naming_conventions,
            structural_patterns=structural_patterns,
            import_patterns=import_patterns,
            error_handling_patterns=error_handling_patterns,
            testing_patterns=testing_patterns,
            documentation_patterns=documentation_patterns,
            overall_style=overall_style,
        )

    def find_similar_implementations(self, query: str) -> list[CodeExample]:
        """Find similar code implementations for reference."""
        try:
            matches = self.indexing_engine.query_similar_code(query, limit=10)
            examples = []

            for match in matches:
                if hasattr(match, "chunk") and hasattr(match, "similarity_score"):
                    chunk = match.chunk
                    function_name, class_name = self._extract_code_context(
                        chunk.file_path, chunk.start_line
                    )

                    example = CodeExample(
                        code=chunk.content,
                        file_path=chunk.file_path,
                        function_name=function_name,
                        class_name=class_name,
                        description=f"Similar implementation in {Path(chunk.file_path).name}",
                        similarity_score=match.similarity_score,
                        context={
                            "chunk_type": chunk.chunk_type,
                            "language": chunk.language,
                            "start_line": chunk.start_line,
                            "end_line": chunk.end_line,
                        },
                    )
                    examples.append(example)

            return examples
        except Exception as e:
            print(f"Warning: Error finding similar implementations: {e}")
            return []

    def get_context_for_task(self, task: Task) -> CodeContext:
        """Get relevant code context for implementing a task."""
        if not self.ast_index:
            return CodeContext(
                task_id=task.id,
                relevant_files=[],
                similar_implementations=[],
                required_imports=[],
                suggested_patterns=[],
                dependencies=[],
                test_examples=[],
                style_guidelines={},
            )

        relevant_files = self._find_relevant_files(task)
        similar_implementations = self._find_similar_implementations_for_task(task)
        required_imports = self._determine_required_imports(task)
        suggested_patterns = self._suggest_patterns_for_task(task)
        dependencies = self._identify_task_dependencies(task)
        test_examples = self._find_test_examples(task)
        style_guidelines = self._extract_style_guidelines()

        return CodeContext(
            task_id=task.id,
            relevant_files=relevant_files,
            similar_implementations=similar_implementations,
            required_imports=required_imports,
            suggested_patterns=suggested_patterns,
            dependencies=dependencies,
            test_examples=test_examples,
            style_guidelines=style_guidelines,
        )

    # Private helper methods

    def _infer_project_purpose(self) -> str:
        """Infer the project's purpose from code analysis."""
        if not self.ast_index:
            return "Unknown project purpose"

        domain_keywords = Counter()
        for func_def in self.ast_index.functions.values():
            words = re.findall(r"[A-Z][a-z]+|[a-z]+", func_def.name)
            domain_keywords.update(word.lower() for word in words)

        for class_def in self.ast_index.classes.values():
            words = re.findall(r"[A-Z][a-z]+|[a-z]+", class_def.name)
            domain_keywords.update(word.lower() for word in words)

        common_words = [
            word for word, count in domain_keywords.most_common(10) if count > 1
        ]

        if "test" in common_words:
            return "Testing framework or test suite"
        elif any(word in common_words for word in ["web", "server", "api", "http"]):
            return "Web application or API service"
        elif any(word in common_words for word in ["cli", "command", "arg"]):
            return "Command-line interface application"
        elif any(word in common_words for word in ["data", "analysis", "process"]):
            return "Data processing or analysis tool"
        else:
            return f"Software application with focus on {', '.join(common_words[:3])}"

    def _extract_main_features(self) -> list[str]:
        """Extract main features from the codebase."""
        if not self.ast_index:
            return []

        features = []

        # Analyze class names for feature hints
        class_features = set()
        for class_def in self.ast_index.classes.values():
            words = re.findall(r"[A-Z][a-z]+", class_def.name)
            if len(words) > 1:
                feature = " ".join(words[:-1]).lower()
                if feature not in ["base", "abstract", "interface"]:
                    class_features.add(feature)

        features.extend(list(class_features)[:5])

        # Analyze function names for action-based features
        action_features = set()
        for func_def in self.ast_index.functions.values():
            if func_def.name.startswith(
                ("create", "update", "delete", "get", "set", "process", "handle")
            ):
                words = re.findall(r"[A-Z][a-z]+|[a-z]+", func_def.name)
                if len(words) > 1:
                    feature = " ".join(words[1:]).lower()
                    action_features.add(feature)

        features.extend(list(action_features)[:3])
        return features[:8]

    def _identify_user_roles(self) -> list[str]:
        """Identify potential user roles from the codebase."""
        roles = set()

        if not self.ast_index:
            return ["User", "Developer"]

        role_keywords = [
            "user",
            "admin",
            "client",
            "customer",
            "manager",
            "operator",
            "developer",
        ]

        for class_def in self.ast_index.classes.values():
            name_lower = class_def.name.lower()
            for keyword in role_keywords:
                if keyword in name_lower:
                    roles.add(keyword.title())

        for func_def in self.ast_index.functions.values():
            name_lower = func_def.name.lower()
            for keyword in role_keywords:
                if keyword in name_lower:
                    roles.add(keyword.title())

        if not roles:
            roles = {"User", "Developer"}

        return list(roles)

    def _identify_functional_areas(self) -> list[str]:
        """Identify functional areas of the application."""
        if not self.ast_index:
            return []

        areas = set()

        for file_path in self.ast_index.file_metadata.keys():
            path_parts = Path(file_path).parts
            for part in path_parts:
                if part not in [
                    ".",
                    "..",
                    "__pycache__",
                    ".git",
                ] and not part.startswith("."):
                    areas.add(part.replace("_", " ").title())

        for import_stmt in self.ast_index.imports:
            module_parts = import_stmt.module.split(".")
            for part in module_parts:
                if len(part) > 3 and part not in ["main", "init", "test"]:
                    areas.add(part.replace("_", " ").title())

        return list(areas)[:10]

    def _gather_requirement_evidence(self) -> list[RequirementEvidence]:
        """Gather evidence for potential requirements."""
        if not self.ast_index:
            return []

        evidence = []

        # Look for CRUD operations
        crud_functions = []
        for func_def in self.ast_index.functions.values():
            if any(
                func_def.name.lower().startswith(op)
                for op in ["create", "read", "update", "delete", "get", "set"]
            ):
                crud_functions.append(func_def.name)

        if crud_functions:
            evidence.append(
                RequirementEvidence(
                    requirement_type="Data Management",
                    description="System provides CRUD operations for data management",
                    supporting_files=list(
                        set(
                            func.file_path
                            for func in self.ast_index.functions.values()
                            if func.name in crud_functions
                        )
                    ),
                    supporting_functions=crud_functions[:5],
                    confidence=0.8,
                    code_examples=[],
                )
            )

        # Look for authentication/authorization
        auth_indicators = []
        for func_def in self.ast_index.functions.values():
            if any(
                keyword in func_def.name.lower()
                for keyword in ["auth", "login", "logout", "permission", "access"]
            ):
                auth_indicators.append(func_def.name)

        if auth_indicators:
            evidence.append(
                RequirementEvidence(
                    requirement_type="Authentication & Authorization",
                    description="System implements user authentication and authorization",
                    supporting_files=list(
                        set(
                            func.file_path
                            for func in self.ast_index.functions.values()
                            if func.name in auth_indicators
                        )
                    ),
                    supporting_functions=auth_indicators[:5],
                    confidence=0.7,
                    code_examples=[],
                )
            )

        return evidence

    def _analyze_technology_constraints(self) -> list[str]:
        """Analyze technology constraints from the codebase."""
        constraints = []

        if not self.ast_index:
            return ["Python 3.x required"]

        frameworks = set()
        for import_stmt in self.ast_index.imports:
            module = import_stmt.module.lower()
            if any(fw in module for fw in ["django", "flask", "fastapi"]):
                frameworks.add("Web framework dependency")
            elif any(db in module for db in ["sqlite", "postgres", "mysql", "mongo"]):
                frameworks.add("Database dependency")
            elif any(test in module for test in ["pytest", "unittest", "nose"]):
                frameworks.add("Testing framework dependency")

        constraints.extend(list(frameworks))
        constraints.append("Python 3.x required")
        return constraints

    def _analyze_external_dependencies(self) -> list[str]:
        """Analyze external dependencies."""
        dependencies = set()

        if not self.ast_index:
            return []

        for import_stmt in self.ast_index.imports:
            module = import_stmt.module.split(".")[0]
            if module not in [
                "os",
                "sys",
                "json",
                "time",
                "datetime",
                "collections",
                "typing",
                "re",
            ]:
                if not module.startswith(".") and module != "__future__":
                    dependencies.add(module)

        return list(dependencies)[:10]

    def _calculate_specification_confidence(self) -> float:
        """Calculate confidence score for specification analysis."""
        if not self.ast_index:
            return 0.0

        total_functions = len(self.ast_index.functions)
        total_classes = len(self.ast_index.classes)
        total_files = len(self.ast_index.file_metadata)

        if total_files > 10 and total_functions > 20:
            return 0.8
        elif total_files > 5 and total_functions > 10:
            return 0.6
        elif total_files > 2:
            return 0.4
        else:
            return 0.2

    def _generate_architecture_overview(self) -> str:
        """Generate an overview of the current architecture."""
        if not self.ast_index:
            return "Unable to analyze architecture - no index available"

        total_files = len(self.ast_index.file_metadata)
        total_functions = len(self.ast_index.functions)
        total_classes = len(self.ast_index.classes)

        directories = set()
        for file_path in self.ast_index.file_metadata.keys():
            directories.update(Path(file_path).parts[:-1])

        overview = f"The codebase consists of {total_files} files organized into {len(directories)} directories, "
        overview += f"with {total_classes} classes and {total_functions} functions. "

        if any("controller" in path.lower() for path in directories):
            overview += "The architecture follows an MVC pattern with separate controller components. "
        elif any("service" in path.lower() for path in directories):
            overview += "The architecture uses a service-oriented approach with dedicated service layers. "
        elif any("model" in path.lower() for path in directories):
            overview += "The architecture separates data models from business logic. "

        return overview

    def _analyze_components(self) -> list[ComponentAnalysis]:
        """Analyze system components."""
        if not self.ast_index:
            return []

        components = []
        component_files = defaultdict(list)

        for file_path in self.ast_index.file_metadata.keys():
            path_obj = Path(file_path)
            if len(path_obj.parts) > 1:
                component_name = path_obj.parts[-2]
                component_files[component_name].append(file_path)

        for component_name, files in component_files.items():
            if len(files) > 1:
                func_count = sum(
                    1
                    for func in self.ast_index.functions.values()
                    if func.file_path in files
                )
                class_count = sum(
                    1
                    for cls in self.ast_index.classes.values()
                    if cls.file_path in files
                )

                complexity_score = (func_count + class_count * 2) / len(files)

                component = ComponentAnalysis(
                    name=component_name,
                    purpose=f"Component handling {component_name.replace('_', ' ')} functionality",
                    interfaces=[],
                    dependencies=[],
                    internal_structure={
                        "files": len(files),
                        "functions": func_count,
                        "classes": class_count,
                    },
                    complexity_score=complexity_score,
                )
                components.append(component)

        return components[:10]

    def _extract_data_models(self) -> list[dict[str, Any]]:
        """Extract data models from the codebase."""
        if not self.ast_index:
            return []

        models = []
        for class_def in self.ast_index.classes.values():
            if (
                any(
                    keyword in class_def.name.lower()
                    for keyword in ["model", "entity", "data"]
                )
                or len(class_def.methods) < 5
            ):
                model = {
                    "name": class_def.name,
                    "file_path": class_def.file_path,
                    "attributes": class_def.attributes,
                    "methods": [method.name for method in class_def.methods],
                    "base_classes": class_def.base_classes,
                }
                models.append(model)

        return models[:10]

    def _identify_api_interfaces(self) -> list[dict[str, Any]]:
        """Identify API interfaces in the codebase."""
        if not self.ast_index:
            return []

        interfaces = []
        for func_def in self.ast_index.functions.values():
            if any(
                keyword in func_def.name.lower()
                for keyword in ["api", "endpoint", "route", "handler"]
            ) or any(
                param in func_def.parameters
                for param in ["request", "response", "req", "res"]
            ):
                interface = {
                    "name": func_def.name,
                    "file_path": func_def.file_path,
                    "parameters": func_def.parameters,
                    "return_type": func_def.return_type,
                    "docstring": func_def.docstring,
                }
                interfaces.append(interface)

        return interfaces[:10]

    def _detect_design_patterns(self) -> list[str]:
        """Detect design patterns in the codebase."""
        patterns = []

        if not self.ast_index:
            return patterns

        class_names = [cls.name.lower() for cls in self.ast_index.classes.values()]

        if any("factory" in name for name in class_names):
            patterns.append("Factory Pattern")
        if any("singleton" in name for name in class_names):
            patterns.append("Singleton Pattern")
        if any("observer" in name for name in class_names):
            patterns.append("Observer Pattern")
        if any("adapter" in name for name in class_names):
            patterns.append("Adapter Pattern")
        if any("builder" in name for name in class_names):
            patterns.append("Builder Pattern")

        inheritance_depth = 0
        for cls in self.ast_index.classes.values():
            if cls.base_classes:
                inheritance_depth = max(inheritance_depth, len(cls.base_classes))

        if inheritance_depth > 1:
            patterns.append("Inheritance Hierarchy")

        return patterns

    def _calculate_quality_metrics(self) -> dict[str, float]:
        """Calculate code quality metrics."""
        if not self.ast_index:
            return {}

        metrics = {}

        total_files = len(self.ast_index.file_metadata)
        total_functions = len(self.ast_index.functions)
        metrics["avg_functions_per_file"] = (
            total_functions / total_files if total_files > 0 else 0
        )

        total_classes = len(self.ast_index.classes)
        total_methods = sum(len(cls.methods) for cls in self.ast_index.classes.values())
        metrics["avg_methods_per_class"] = (
            total_methods / total_classes if total_classes > 0 else 0
        )

        documented_functions = sum(
            1 for func in self.ast_index.functions.values() if func.docstring
        )
        metrics["documentation_coverage"] = (
            documented_functions / total_functions if total_functions > 0 else 0
        )

        return metrics

    def _identify_technical_debt(self) -> list[str]:
        """Identify potential technical debt."""
        debt = []

        if not self.ast_index:
            return debt

        todo_count = 0
        for func in self.ast_index.functions.values():
            if func.docstring and any(
                keyword in func.docstring.upper()
                for keyword in ["TODO", "FIXME", "HACK"]
            ):
                todo_count += 1

        if todo_count > 0:
            debt.append(f"{todo_count} functions contain TODO/FIXME comments")

        large_functions = []
        for func in self.ast_index.functions.values():
            if func.end_line - func.start_line > 50:
                large_functions.append(func.name)

        if large_functions:
            debt.append(f"{len(large_functions)} functions are potentially too large")

        complex_classes = []
        for cls in self.ast_index.classes.values():
            if len(cls.methods) > 20:
                complex_classes.append(cls.name)

        if complex_classes:
            debt.append(f"{len(complex_classes)} classes have high method count")

        return debt

    def _generate_design_recommendations(self) -> list[str]:
        """Generate design recommendations."""
        recommendations = []

        if not self.ast_index:
            return recommendations

        test_files = sum(
            1
            for path in self.ast_index.file_metadata.keys()
            if "test" in Path(path).name.lower()
        )
        total_files = len(self.ast_index.file_metadata)

        if test_files / total_files < 0.3:
            recommendations.append("Consider increasing test coverage")

        documented_functions = sum(
            1 for func in self.ast_index.functions.values() if func.docstring
        )
        total_functions = len(self.ast_index.functions)

        if documented_functions / total_functions < 0.5:
            recommendations.append("Consider adding more function documentation")

        large_files = sum(
            1
            for metadata in self.ast_index.file_metadata.values()
            if metadata.get("line_count", 0) > 500
        )

        if large_files > 0:
            recommendations.append(
                "Consider breaking down large files for better maintainability"
            )

        return recommendations

    def _detect_architecture_patterns(self) -> list[ArchitecturePattern]:
        """Detect architectural patterns."""
        patterns = []

        if not self.ast_index:
            return patterns

        mvc_evidence = []
        directories = set()
        for file_path in self.ast_index.file_metadata.keys():
            directories.update(Path(file_path).parts)

        if any("model" in dir_name.lower() for dir_name in directories):
            mvc_evidence.append("Model directory found")
        if any("view" in dir_name.lower() for dir_name in directories):
            mvc_evidence.append("View directory found")
        if any("controller" in dir_name.lower() for dir_name in directories):
            mvc_evidence.append("Controller directory found")

        if len(mvc_evidence) >= 2:
            patterns.append(
                ArchitecturePattern(
                    name="Model-View-Controller (MVC)",
                    description="Separation of concerns using MVC pattern",
                    confidence=0.7,
                    evidence=mvc_evidence,
                    files_involved=list(self.ast_index.file_metadata.keys())[:5],
                )
            )

        return patterns

    def _identify_layers(self) -> list[str]:
        """Identify architectural layers."""
        layers = []

        if not self.ast_index:
            return layers

        directories = set()
        for file_path in self.ast_index.file_metadata.keys():
            directories.update(Path(file_path).parts)

        layer_keywords = {
            "presentation": ["view", "ui", "frontend", "template"],
            "business": ["service", "business", "logic", "core"],
            "data": ["model", "data", "repository", "dao"],
            "infrastructure": ["config", "util", "helper", "infrastructure"],
        }

        for layer_name, keywords in layer_keywords.items():
            if any(
                keyword in dir_name.lower()
                for dir_name in directories
                for keyword in keywords
            ):
                layers.append(layer_name.title() + " Layer")

        return layers

    def _extract_components(self) -> list[str]:
        """Extract system components."""
        components = []

        if not self.ast_index:
            return components

        directories = set()
        for file_path in self.ast_index.file_metadata.keys():
            path_parts = Path(file_path).parts
            if len(path_parts) > 1:
                directories.add(path_parts[-2])

        skip_dirs = {"__pycache__", ".git", "test", "tests", ".pytest_cache"}
        components = [
            d for d in directories if d not in skip_dirs and not d.startswith(".")
        ]

        return components[:10]

    def _analyze_component_dependencies(self) -> dict[str, list[str]]:
        """Analyze dependencies between components."""
        dependencies = defaultdict(list)

        if not self.ast_index:
            return dict(dependencies)

        for import_stmt in self.ast_index.imports:
            source_file = Path(import_stmt.file_path)
            if len(source_file.parts) > 1:
                source_component = source_file.parts[-2]

                if "." in import_stmt.module and not import_stmt.module.startswith("."):
                    target_parts = import_stmt.module.split(".")
                    if len(target_parts) > 1:
                        target_component = target_parts[-2]
                        if target_component != source_component:
                            dependencies[source_component].append(target_component)

        for component in dependencies:
            dependencies[component] = list(set(dependencies[component]))

        return dict(dependencies)

    def _find_entry_points(self) -> list[str]:
        """Find application entry points."""
        entry_points = []

        if not self.ast_index:
            return entry_points

        for func_def in self.ast_index.functions.values():
            if func_def.name == "main" or func_def.name == "__main__":
                entry_points.append(f"{func_def.file_path}:{func_def.name}")

        for file_path in self.ast_index.file_metadata.keys():
            file_name = Path(file_path).stem.lower()
            if file_name in ["main", "app", "server", "cli", "run"]:
                entry_points.append(file_path)

        return entry_points[:5]

    def _analyze_data_flow(self) -> dict[str, Any]:
        """Analyze data flow in the application."""
        data_flow = {}

        if not self.ast_index:
            return data_flow

        data_flow["input_sources"] = []
        data_flow["output_destinations"] = []
        data_flow["processing_stages"] = []

        for func_def in self.ast_index.functions.values():
            name_lower = func_def.name.lower()
            if any(
                keyword in name_lower for keyword in ["read", "load", "input", "fetch"]
            ):
                data_flow["input_sources"].append(func_def.name)
            elif any(
                keyword in name_lower
                for keyword in ["write", "save", "output", "export"]
            ):
                data_flow["output_destinations"].append(func_def.name)
            elif any(
                keyword in name_lower
                for keyword in ["process", "transform", "convert", "parse"]
            ):
                data_flow["processing_stages"].append(func_def.name)

        return data_flow

    def _identify_technology_stack(self) -> list[str]:
        """Identify the technology stack."""
        stack = ["Python"]

        if not self.ast_index:
            return stack

        frameworks = set()
        for import_stmt in self.ast_index.imports:
            module = import_stmt.module.lower()

            if any(fw in module for fw in ["django", "flask", "fastapi", "tornado"]):
                frameworks.add("Web Framework")
            elif any(
                db in module
                for db in ["sqlite", "postgres", "mysql", "mongo", "sqlalchemy"]
            ):
                frameworks.add("Database")
            elif any(test in module for test in ["pytest", "unittest", "nose"]):
                frameworks.add("Testing Framework")
            elif any(data in module for data in ["pandas", "numpy", "scipy"]):
                frameworks.add("Data Processing")
            elif any(web in module for web in ["requests", "urllib", "beautifulsoup"]):
                frameworks.add("HTTP/Web Client")

        stack.extend(list(frameworks))
        return stack

    def _analyze_naming_conventions(self) -> list[CodePattern]:
        """Analyze naming conventions in the codebase."""
        patterns = []

        if not self.ast_index:
            return patterns

        function_names = [func.name for func in self.ast_index.functions.values()]
        snake_case_funcs = sum(
            1 for name in function_names if "_" in name and name.islower()
        )
        camel_case_funcs = sum(
            1
            for name in function_names
            if name[0].islower() and any(c.isupper() for c in name)
        )

        if snake_case_funcs > camel_case_funcs:
            patterns.append(
                CodePattern(
                    pattern_type="naming",
                    description="Functions use snake_case naming convention",
                    examples=function_names[:3],
                    frequency=snake_case_funcs,
                    confidence=0.8,
                )
            )
        elif camel_case_funcs > snake_case_funcs:
            patterns.append(
                CodePattern(
                    pattern_type="naming",
                    description="Functions use camelCase naming convention",
                    examples=function_names[:3],
                    frequency=camel_case_funcs,
                    confidence=0.8,
                )
            )

        class_names = [cls.name for cls in self.ast_index.classes.values()]
        pascal_case_classes = sum(1 for name in class_names if name[0].isupper())

        if pascal_case_classes > 0:
            patterns.append(
                CodePattern(
                    pattern_type="naming",
                    description="Classes use PascalCase naming convention",
                    examples=class_names[:3],
                    frequency=pascal_case_classes,
                    confidence=0.9,
                )
            )

        return patterns

    def _detect_structural_patterns(self) -> list[CodePattern]:
        """Detect structural patterns in the code."""
        patterns = []

        if not self.ast_index:
            return patterns

        classes_with_init = sum(
            1
            for cls in self.ast_index.classes.values()
            if any(method.name == "__init__" for method in cls.methods)
        )
        total_classes = len(self.ast_index.classes)

        if total_classes > 0 and classes_with_init / total_classes > 0.7:
            patterns.append(
                CodePattern(
                    pattern_type="structure",
                    description="Most classes have explicit __init__ methods",
                    examples=[],
                    frequency=classes_with_init,
                    confidence=0.8,
                )
            )

        long_functions = sum(
            1
            for func in self.ast_index.functions.values()
            if func.end_line - func.start_line > 20
        )
        total_functions = len(self.ast_index.functions)

        if total_functions > 0 and long_functions / total_functions < 0.3:
            patterns.append(
                CodePattern(
                    pattern_type="structure",
                    description="Functions are generally kept short (< 20 lines)",
                    examples=[],
                    frequency=total_functions - long_functions,
                    confidence=0.7,
                )
            )

        return patterns

    def _analyze_import_patterns(self) -> list[CodePattern]:
        """Analyze import patterns."""
        patterns = []

        if not self.ast_index:
            return patterns

        absolute_imports = sum(
            1 for imp in self.ast_index.imports if not imp.module.startswith(".")
        )
        relative_imports = sum(
            1 for imp in self.ast_index.imports if imp.module.startswith(".")
        )

        if absolute_imports > relative_imports * 2:
            patterns.append(
                CodePattern(
                    pattern_type="import",
                    description="Prefers absolute imports over relative imports",
                    examples=[
                        imp.module
                        for imp in self.ast_index.imports
                        if not imp.module.startswith(".")
                    ][:3],
                    frequency=absolute_imports,
                    confidence=0.8,
                )
            )

        stdlib_imports = sum(
            1
            for imp in self.ast_index.imports
            if imp.module.split(".")[0] in ["os", "sys", "json", "time", "datetime"]
        )

        if stdlib_imports > 0:
            patterns.append(
                CodePattern(
                    pattern_type="import",
                    description="Uses standard library modules",
                    examples=[
                        imp.module
                        for imp in self.ast_index.imports
                        if imp.module.split(".")[0]
                        in ["os", "sys", "json", "time", "datetime"]
                    ][:3],
                    frequency=stdlib_imports,
                    confidence=0.9,
                )
            )

        return patterns

    def _detect_error_handling_patterns(self) -> list[CodePattern]:
        """Detect error handling patterns."""
        patterns = []

        if not self.ast_index:
            return patterns

        error_handling_funcs = []
        for func in self.ast_index.functions.values():
            if any(
                keyword in func.name.lower()
                for keyword in ["error", "exception", "handle", "catch"]
            ) or (
                func.docstring
                and any(
                    keyword in func.docstring.lower()
                    for keyword in ["raise", "except", "error"]
                )
            ):
                error_handling_funcs.append(func.name)

        if error_handling_funcs:
            patterns.append(
                CodePattern(
                    pattern_type="error_handling",
                    description="Explicit error handling functions present",
                    examples=error_handling_funcs[:3],
                    frequency=len(error_handling_funcs),
                    confidence=0.6,
                )
            )

        return patterns

    def _analyze_testing_patterns(self) -> list[CodePattern]:
        """Analyze testing patterns."""
        patterns = []

        if not self.ast_index:
            return patterns

        test_files = [
            path
            for path in self.ast_index.file_metadata.keys()
            if "test" in Path(path).name.lower()
        ]
        test_functions = [
            func.name
            for func in self.ast_index.functions.values()
            if func.name.startswith("test_")
        ]

        if test_files:
            patterns.append(
                CodePattern(
                    pattern_type="testing",
                    description="Dedicated test files present",
                    examples=[Path(f).name for f in test_files[:3]],
                    frequency=len(test_files),
                    confidence=0.9,
                )
            )

        if test_functions:
            patterns.append(
                CodePattern(
                    pattern_type="testing",
                    description="Test functions follow test_ naming convention",
                    examples=test_functions[:3],
                    frequency=len(test_functions),
                    confidence=0.9,
                )
            )

        return patterns

    def _detect_documentation_patterns(self) -> list[CodePattern]:
        """Detect documentation patterns."""
        patterns = []

        if not self.ast_index:
            return patterns

        functions_with_docstrings = sum(
            1 for func in self.ast_index.functions.values() if func.docstring
        )
        total_functions = len(self.ast_index.functions)

        if total_functions > 0 and functions_with_docstrings / total_functions > 0.5:
            patterns.append(
                CodePattern(
                    pattern_type="documentation",
                    description="Good docstring coverage for functions",
                    examples=[],
                    frequency=functions_with_docstrings,
                    confidence=0.8,
                )
            )

        classes_with_docstrings = sum(
            1 for cls in self.ast_index.classes.values() if cls.docstring
        )
        total_classes = len(self.ast_index.classes)

        if total_classes > 0 and classes_with_docstrings / total_classes > 0.5:
            patterns.append(
                CodePattern(
                    pattern_type="documentation",
                    description="Good docstring coverage for classes",
                    examples=[],
                    frequency=classes_with_docstrings,
                    confidence=0.8,
                )
            )

        return patterns

    def _determine_overall_style(self) -> dict[str, Any]:
        """Determine overall coding style."""
        style = {}

        if not self.ast_index:
            return style

        style["indentation"] = "spaces"
        style["max_line_length"] = "standard"

        function_names = [func.name for func in self.ast_index.functions.values()]
        snake_case_count = sum(
            1 for name in function_names if "_" in name and name.islower()
        )

        if len(function_names) > 0 and snake_case_count > len(function_names) * 0.7:
            style["function_naming"] = "snake_case"
        else:
            style["function_naming"] = "mixed"

        class_names = [cls.name for cls in self.ast_index.classes.values()]
        pascal_case_count = sum(1 for name in class_names if name[0].isupper())

        if len(class_names) > 0 and pascal_case_count > len(class_names) * 0.8:
            style["class_naming"] = "PascalCase"
        else:
            style["class_naming"] = "mixed"

        return style

    def _extract_code_context(
        self, file_path: str, line_number: int
    ) -> tuple[str | None, str | None]:
        """Extract function and class context for a given line."""
        if not self.ast_index:
            return None, None

        function_name = None
        class_name = None

        for func in self.ast_index.functions.values():
            if (
                func.file_path == file_path
                and func.start_line <= line_number <= func.end_line
            ):
                function_name = func.name
                break

        for cls in self.ast_index.classes.values():
            if (
                cls.file_path == file_path
                and cls.start_line <= line_number <= cls.end_line
            ):
                class_name = cls.name
                break

        return function_name, class_name

    def _find_relevant_files(self, task: Task) -> list[str]:
        """Find files relevant to a task."""
        if not self.ast_index:
            return []

        relevant_files = []
        task_keywords = task.description.lower().split()

        file_scores = {}
        for file_path in self.ast_index.file_metadata.keys():
            score = 0
            file_name = Path(file_path).stem.lower()

            for keyword in task_keywords:
                if keyword in file_name:
                    score += 2

            for func in self.ast_index.functions.values():
                if func.file_path == file_path:
                    for keyword in task_keywords:
                        if keyword in func.name.lower():
                            score += 1

            for cls in self.ast_index.classes.values():
                if cls.file_path == file_path:
                    for keyword in task_keywords:
                        if keyword in cls.name.lower():
                            score += 1

            if score > 0:
                file_scores[file_path] = score

        sorted_files = sorted(file_scores.items(), key=lambda x: x[1], reverse=True)
        relevant_files = [file_path for file_path, score in sorted_files[:5]]

        return relevant_files

    def _find_similar_implementations_for_task(
        self, task: Task
    ) -> list[ContextualCode]:
        """Find similar implementations for a task."""
        similar_implementations = []

        try:
            code_examples = self.find_similar_implementations(task.description)

            for example in code_examples[:3]:
                contextual_code = ContextualCode(
                    code=example.code,
                    file_path=example.file_path,
                    relevance_score=example.similarity_score,
                    context_type="similar_implementation",
                    explanation=f"Similar implementation found in {Path(example.file_path).name}",
                )
                similar_implementations.append(contextual_code)

        except Exception as e:
            print(f"Warning: Error finding similar implementations: {e}")

        return similar_implementations

    def _determine_required_imports(self, task: Task) -> list[str]:
        """Determine required imports for a task."""
        if not self.ast_index:
            return []

        required_imports = []
        task_keywords = task.description.lower().split()

        import_suggestions = {
            "test": ["pytest", "unittest"],
            "json": ["json"],
            "file": ["os", "pathlib"],
            "time": ["datetime", "time"],
            "http": ["requests", "urllib"],
            "database": ["sqlite3", "sqlalchemy"],
            "web": ["flask", "django", "fastapi"],
        }

        for keyword in task_keywords:
            if keyword in import_suggestions:
                required_imports.extend(import_suggestions[keyword])

        relevant_files = self._find_relevant_files(task)
        for file_path in relevant_files:
            for import_stmt in self.ast_index.imports:
                if import_stmt.file_path == file_path:
                    required_imports.append(import_stmt.module)

        return list(set(required_imports))[:5]

    def _suggest_patterns_for_task(self, task: Task) -> list[CodePattern]:
        """Suggest patterns for implementing a task."""
        patterns = self.identify_code_patterns()

        relevant_patterns = []
        task_keywords = task.description.lower().split()

        for pattern_list in [
            patterns.naming_conventions,
            patterns.structural_patterns,
            patterns.import_patterns,
            patterns.error_handling_patterns,
        ]:
            for pattern in pattern_list:
                if any(
                    keyword in pattern.description.lower() for keyword in task_keywords
                ):
                    relevant_patterns.append(pattern)

        return relevant_patterns[:3]

    def _identify_task_dependencies(self, task: Task) -> list[str]:
        """Identify dependencies for a task."""
        dependencies = []

        if task.requirements_refs:
            dependencies.extend(task.requirements_refs)

        if task.subtasks:
            dependencies.extend(task.subtasks)

        task_desc = task.description.lower()
        if "database" in task_desc:
            dependencies.append("database_connection")
        if "api" in task_desc:
            dependencies.append("api_framework")
        if "test" in task_desc:
            dependencies.append("testing_framework")

        return dependencies

    def _find_test_examples(self, task: Task) -> list[ContextualCode]:
        """Find test examples relevant to a task."""
        test_examples = []

        if not self.ast_index:
            return test_examples

        for func in self.ast_index.functions.values():
            if func.name.startswith("test_"):
                task_keywords = task.description.lower().split()
                if any(keyword in func.name.lower() for keyword in task_keywords):
                    test_example = ContextualCode(
                        code=f"def {func.name}({', '.join(func.parameters)}):",
                        file_path=func.file_path,
                        relevance_score=0.7,
                        context_type="test_example",
                        explanation=f"Test example from {Path(func.file_path).name}",
                    )
                    test_examples.append(test_example)

        return test_examples[:3]

    def _extract_style_guidelines(self) -> dict[str, Any]:
        """Extract style guidelines from the codebase."""
        if not self.ast_index:
            return {}

        patterns = self.identify_code_patterns()

        guidelines = {}

        for pattern in patterns.naming_conventions:
            if "snake_case" in pattern.description:
                guidelines["function_naming"] = "snake_case"
            elif "camelCase" in pattern.description:
                guidelines["function_naming"] = "camelCase"
            elif "PascalCase" in pattern.description:
                guidelines["class_naming"] = "PascalCase"

        for pattern in patterns.structural_patterns:
            if "short" in pattern.description:
                guidelines["function_length"] = "keep_short"
            elif "__init__" in pattern.description:
                guidelines["class_structure"] = "explicit_init"

        for pattern in patterns.import_patterns:
            if "absolute" in pattern.description:
                guidelines["import_style"] = "absolute_preferred"

        return guidelines

    def _infer_project_purpose(self) -> str:
        """Infer the main purpose of the project from code analysis."""
        if not self.ast_index:
            return "Software application"

        # Analyze imports and class names to infer purpose
        imports = [imp.module.lower() for imp in self.ast_index.imports]
        class_names = [cls.name.lower() for cls in self.ast_index.classes.values()]
        function_names = [
            func.name.lower() for func in self.ast_index.functions.values()
        ]

        # Web application indicators
        web_indicators = ["flask", "django", "fastapi", "tornado", "bottle", "pyramid"]
        if any(indicator in " ".join(imports) for indicator in web_indicators):
            return "Web application providing HTTP API services"

        # CLI application indicators
        cli_indicators = ["argparse", "click", "typer", "fire"]
        if any(indicator in " ".join(imports) for indicator in cli_indicators):
            return "Command-line application for task automation"

        # Data processing indicators
        data_indicators = [
            "pandas",
            "numpy",
            "scipy",
            "sklearn",
            "tensorflow",
            "pytorch",
        ]
        if any(indicator in " ".join(imports) for indicator in data_indicators):
            return "Data processing and analysis application"

        # Default based on class/function analysis
        if any(
            "server" in name or "api" in name for name in class_names + function_names
        ):
            return "Server application providing services"
        elif any("client" in name for name in class_names + function_names):
            return "Client application for interacting with services"
        else:
            return "General-purpose software application"

    def _extract_main_features(self) -> list[str]:
        """Extract main features from code analysis."""
        if not self.ast_index:
            return []

        features = []

        # Analyze class names for feature indicators
        class_names = [cls.name for cls in self.ast_index.classes.values()]

        for class_name in class_names:
            name_lower = class_name.lower()

            if "auth" in name_lower or "login" in name_lower:
                features.append("User Authentication")
            elif "user" in name_lower and "manage" in name_lower:
                features.append("User Management")
            elif "data" in name_lower or "model" in name_lower:
                features.append("Data Management")
            elif "api" in name_lower or "endpoint" in name_lower:
                features.append("API Services")
            elif "config" in name_lower or "setting" in name_lower:
                features.append("Configuration Management")
            elif "log" in name_lower:
                features.append("Logging and Monitoring")
            elif "test" in name_lower:
                features.append("Testing Framework")
            elif "cache" in name_lower:
                features.append("Caching System")
            elif "queue" in name_lower or "task" in name_lower:
                features.append("Task Processing")
            elif "file" in name_lower or "storage" in name_lower:
                features.append("File Management")

        # Remove duplicates and limit
        features = list(dict.fromkeys(features))[:8]

        # Add generic features if none found
        if not features:
            features = ["Core Application Logic", "Data Processing", "User Interface"]

        return features

    def _identify_user_roles(self) -> list[str]:
        """Identify potential user roles from code analysis."""
        roles = ["User"]  # Default role

        if not self.ast_index:
            return roles

        # Look for role-related classes or functions
        all_names = []
        all_names.extend([cls.name.lower() for cls in self.ast_index.classes.values()])
        all_names.extend(
            [func.name.lower() for func in self.ast_index.functions.values()]
        )

        role_indicators = {
            "admin": "Administrator",
            "manager": "Manager",
            "operator": "Operator",
            "developer": "Developer",
            "customer": "Customer",
            "client": "Client",
            "guest": "Guest User",
            "moderator": "Moderator",
            "editor": "Editor",
        }

        for name in all_names:
            for indicator, role in role_indicators.items():
                if indicator in name and role not in roles:
                    roles.append(role)

        return roles[:5]  # Limit to 5 roles

    def _identify_functional_areas(self) -> list[str]:
        """Identify functional areas from code structure."""
        if not self.ast_index:
            return []

        areas = set()

        # Analyze file paths for functional grouping
        file_paths = list(self.ast_index.file_metadata.keys())

        for file_path in file_paths:
            path_parts = Path(file_path).parts

            for part in path_parts:
                part_lower = part.lower()

                if part_lower in ["auth", "authentication"]:
                    areas.add("Authentication & Authorization")
                elif part_lower in ["api", "endpoints", "routes"]:
                    areas.add("API Management")
                elif part_lower in ["data", "models", "database", "db"]:
                    areas.add("Data Management")
                elif part_lower in ["ui", "interface", "frontend", "views"]:
                    areas.add("User Interface")
                elif part_lower in ["config", "settings", "configuration"]:
                    areas.add("Configuration")
                elif part_lower in ["utils", "utilities", "helpers"]:
                    areas.add("Utility Functions")
                elif part_lower in ["tests", "testing"]:
                    areas.add("Testing")
                elif part_lower in ["docs", "documentation"]:
                    areas.add("Documentation")

        # Analyze class names for additional areas
        class_names = [cls.name.lower() for cls in self.ast_index.classes.values()]

        for name in class_names:
            if "service" in name:
                areas.add("Service Layer")
            elif "controller" in name:
                areas.add("Request Handling")
            elif "repository" in name or "dao" in name:
                areas.add("Data Access")
            elif "validator" in name:
                areas.add("Data Validation")
            elif "processor" in name:
                areas.add("Data Processing")

        return list(areas)[:10]  # Limit to 10 areas

    def _identify_technology_constraints(self) -> list[str]:
        """Identify technology constraints from imports and dependencies."""
        if not self.ast_index:
            return ["Python 3.x"]

        constraints = ["Python 3.x"]  # Base constraint

        # Analyze imports for technology stack
        imports = [imp.module for imp in self.ast_index.imports]

        # Web frameworks
        web_frameworks = {
            "flask": "Flask web framework",
            "django": "Django web framework",
            "fastapi": "FastAPI framework",
            "tornado": "Tornado web server",
            "bottle": "Bottle micro-framework",
        }

        for imp in imports:
            imp_lower = imp.lower()
            for framework, constraint in web_frameworks.items():
                if framework in imp_lower:
                    constraints.append(constraint)

        # Database technologies
        db_technologies = {
            "sqlite3": "SQLite database",
            "psycopg2": "PostgreSQL database",
            "pymongo": "MongoDB database",
            "redis": "Redis cache/database",
            "sqlalchemy": "SQLAlchemy ORM",
        }

        for imp in imports:
            imp_lower = imp.lower()
            for tech, constraint in db_technologies.items():
                if tech in imp_lower:
                    constraints.append(constraint)

        # Remove duplicates
        constraints = list(dict.fromkeys(constraints))

        return constraints[:8]  # Limit to 8 constraints

    def _extract_requirement_evidence(self) -> list[RequirementEvidence]:
        """Extract evidence for requirements from code analysis."""
        if not self.ast_index:
            return []

        evidence = []

        # Analyze functions for requirement evidence
        functions = list(self.ast_index.functions.values())

        # Group functions by type/purpose
        function_groups = defaultdict(list)

        for func in functions:
            name_lower = func.name.lower()

            if any(
                keyword in name_lower for keyword in ["create", "add", "insert", "save"]
            ):
                function_groups["Data Creation"].append(func)
            elif any(
                keyword in name_lower
                for keyword in ["read", "get", "fetch", "load", "find"]
            ):
                function_groups["Data Retrieval"].append(func)
            elif any(
                keyword in name_lower
                for keyword in ["update", "modify", "edit", "change"]
            ):
                function_groups["Data Modification"].append(func)
            elif any(
                keyword in name_lower for keyword in ["delete", "remove", "destroy"]
            ):
                function_groups["Data Deletion"].append(func)
            elif any(
                keyword in name_lower
                for keyword in ["auth", "login", "verify", "validate"]
            ):
                function_groups["Authentication"].append(func)
            elif any(
                keyword in name_lower for keyword in ["process", "handle", "execute"]
            ):
                function_groups["Business Logic"].append(func)

        # Create evidence for each group
        for req_type, funcs in function_groups.items():
            if funcs:
                evidence_item = RequirementEvidence(
                    requirement_type=req_type,
                    description=f"System provides {req_type.lower()} functionality",
                    supporting_files=list(set(func.file_path for func in funcs)),
                    supporting_functions=[
                        func.name for func in funcs[:5]
                    ],  # Limit to 5
                    confidence=min(
                        0.9, 0.5 + (len(funcs) * 0.1)
                    ),  # Higher confidence with more functions
                    code_examples=[],
                )
                evidence.append(evidence_item)

        return evidence[:8]  # Limit to 8 evidence items

    def _calculate_specification_confidence(
        self, features: list[str], areas: list[str], evidence: list[RequirementEvidence]
    ) -> float:
        """Calculate confidence score for specification analysis."""
        base_confidence = 0.3

        # Increase confidence based on available information
        if features:
            base_confidence += min(0.3, len(features) * 0.05)

        if areas:
            base_confidence += min(0.2, len(areas) * 0.03)

        if evidence:
            avg_evidence_confidence = sum(e.confidence for e in evidence) / len(
                evidence
            )
            base_confidence += avg_evidence_confidence * 0.3

        return min(0.95, base_confidence)
