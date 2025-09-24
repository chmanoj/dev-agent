"""Multi-language project detection and analysis engine."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from ..models.analysis import (
    CrossLanguageMappings,
    FrameworkInfo,
    Improvement,
    LanguageConventions,
    LanguageInfo,
    UsagePattern,
)
from ..models.enums import FrameworkType, LanguageType
from .framework_detectors import FrameworkDetectorRegistry
from .language_parsers import LanguageParserRegistry


class MultiLanguageAnalyzer:
    """Analyzes projects with multiple programming languages and frameworks."""

    def __init__(self, project_path: str):
        """Initialize the multi-language analyzer.

        Args:
            project_path: Path to the project root directory
        """
        self.project_path = Path(project_path)
        self.language_parsers = LanguageParserRegistry()
        self.framework_detectors = FrameworkDetectorRegistry()
        self._file_cache: dict[str, str] = {}
        self._language_files: dict[LanguageType, list[Path]] = defaultdict(list)

    def detect_project_languages(self) -> list[LanguageInfo]:
        """Detect all programming languages used in the project.

        Returns:
            List of LanguageInfo objects for detected languages
        """
        self._scan_project_files()
        languages = []

        for language_type, files in self._language_files.items():
            if not files:
                continue

            # Calculate metrics for this language
            total_lines = 0
            for file_path in files:
                try:
                    content = self._get_file_content(file_path)
                    total_lines += len(content.splitlines())
                except Exception:
                    continue

            # Detect version if possible
            version = self._detect_language_version(language_type, files)

            # Detect frameworks for this language
            frameworks = self._detect_language_frameworks(language_type, files)

            # Analyze conventions
            conventions = self._analyze_language_conventions(language_type, files)

            # Calculate quality score
            quality_score = self._calculate_language_quality(language_type, files)

            language_info = LanguageInfo(
                language=language_type.value,
                version=version,
                file_count=len(files),
                line_count=total_lines,
                frameworks=[f.value for f in frameworks],
                conventions=conventions.__dict__,
                quality_score=quality_score,
            )
            languages.append(language_info)

        return sorted(languages, key=lambda x: x.line_count, reverse=True)

    def analyze_framework_usage(self) -> list[FrameworkInfo]:
        """Analyze framework usage across the project.

        Returns:
            List of FrameworkInfo objects for detected frameworks
        """
        frameworks = []
        detected_frameworks = set()

        # Detect frameworks for each language
        for language_type, files in self._language_files.items():
            if not files:
                continue

            language_frameworks = self._detect_language_frameworks(language_type, files)
            detected_frameworks.update(language_frameworks)

        # Analyze each detected framework
        for framework in detected_frameworks:
            framework_info = self._analyze_framework(framework)
            if framework_info:
                frameworks.append(framework_info)

        return frameworks

    def extract_language_patterns(self, language: LanguageType) -> dict[str, Any]:
        """Extract patterns specific to a programming language.

        Args:
            language: The programming language to analyze

        Returns:
            Dictionary containing language-specific patterns
        """
        if language not in self._language_files:
            return {}

        files = self._language_files[language]
        parser = self.language_parsers.get_parser(language)

        patterns = {
            "naming_patterns": self._extract_naming_patterns(language, files),
            "structural_patterns": self._extract_structural_patterns(language, files),
            "import_patterns": self._extract_import_patterns(language, files),
            "error_handling_patterns": self._extract_error_handling_patterns(language, files),
            "documentation_patterns": self._extract_documentation_patterns(language, files),
        }

        if parser:
            patterns.update(parser.extract_language_specific_patterns(files))

        return patterns

    def generate_cross_language_mappings(self) -> CrossLanguageMappings:
        """Generate mappings between different languages in the project.

        Returns:
            CrossLanguageMappings object with interaction analysis
        """
        api_interactions = self._analyze_api_interactions()
        data_flow = self._analyze_cross_language_data_flow()
        shared_configurations = self._analyze_shared_configurations()
        build_dependencies = self._analyze_build_dependencies()
        integration_patterns = self._identify_integration_patterns()

        return CrossLanguageMappings(
            api_interactions=api_interactions,
            data_flow=data_flow,
            shared_configurations=shared_configurations,
            build_dependencies=build_dependencies,
            integration_patterns=integration_patterns,
        )

    def _scan_project_files(self) -> None:
        """Scan project directory and categorize files by language."""
        self._language_files.clear()

        # Define file extensions for each language
        language_extensions = {
            LanguageType.PYTHON: {".py", ".pyx", ".pyi"},
            LanguageType.JAVASCRIPT: {".js", ".mjs", ".cjs"},
            LanguageType.TYPESCRIPT: {".ts", ".tsx"},
            LanguageType.JAVA: {".java"},
            LanguageType.HTML: {".html", ".htm"},
            LanguageType.CSS: {".css", ".scss", ".sass", ".less"},
            LanguageType.JSON: {".json"},
            LanguageType.YAML: {".yaml", ".yml"},
            LanguageType.XML: {".xml"},
            LanguageType.SQL: {".sql"},
            LanguageType.DOCKERFILE: {"Dockerfile", ".dockerfile"},
            LanguageType.SHELL: {".sh", ".bash", ".zsh"},
            LanguageType.MAKEFILE: {"Makefile", ".mk"},
        }

        # Scan all files in the project
        for file_path in self.project_path.rglob("*"):
            if not file_path.is_file():
                continue

            # Skip hidden files and common ignore patterns
            if self._should_ignore_file(file_path):
                continue

            # Determine language based on extension
            for language, extensions in language_extensions.items():
                if (
                    file_path.suffix.lower() in extensions
                    or file_path.name in extensions
                ):
                    self._language_files[language].append(file_path)
                    break

    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if a file should be ignored during analysis."""
        ignore_patterns = {
            # Hidden files and directories
            ".*",
            # Build and dependency directories
            "node_modules",
            "__pycache__",
            ".pytest_cache",
            "build",
            "dist",
            "target",
            ".gradle",
            ".mvn",
            # IDE files
            ".vscode",
            ".idea",
            "*.iml",
            # Log files
            "*.log",
            # Binary files
            "*.pyc",
            "*.class",
            "*.jar",
            "*.war",
            # Package files
            "package-lock.json",
            "yarn.lock",
            "Pipfile.lock",
            "poetry.lock",
        }

        # Check if any part of the path matches ignore patterns
        for part in file_path.parts:
            for pattern in ignore_patterns:
                if pattern.startswith("*") and part.endswith(pattern[1:]):
                    return True
                elif part == pattern or part.startswith(pattern):
                    return True

        return False

    def _get_file_content(self, file_path: Path) -> str:
        """Get file content with caching."""
        file_key = str(file_path)
        if file_key not in self._file_cache:
            try:
                with open(file_path, encoding="utf-8") as f:
                    self._file_cache[file_key] = f.read()
            except Exception:
                self._file_cache[file_key] = ""
        return self._file_cache[file_key]

    def _detect_language_version(self, language: LanguageType, files: list[Path]) -> str | None:
        """Detect the version of a programming language."""
        if language == LanguageType.PYTHON:
            return self._detect_python_version(files)
        elif language == LanguageType.JAVASCRIPT:
            return self._detect_javascript_version(files)
        elif language == LanguageType.TYPESCRIPT:
            return self._detect_typescript_version(files)
        elif language == LanguageType.JAVA:
            return self._detect_java_version(files)
        return None

    def _detect_python_version(self, files: list[Path]) -> str | None:
        """Detect Python version from project files."""
        # Check pyproject.toml
        pyproject_path = self.project_path / "pyproject.toml"
        if pyproject_path.exists():
            content = self._get_file_content(pyproject_path)
            # Look for requires-python
            match = re.search(r'requires-python\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)

        # Check setup.py
        setup_path = self.project_path / "setup.py"
        if setup_path.exists():
            content = self._get_file_content(setup_path)
            match = re.search(r'python_requires\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)

        # Check .python-version
        python_version_path = self.project_path / ".python-version"
        if python_version_path.exists():
            return self._get_file_content(python_version_path).strip()

        return None

    def _detect_javascript_version(self, files: list[Path]) -> str | None:
        """Detect JavaScript version from project files."""
        package_json_path = self.project_path / "package.json"
        if package_json_path.exists():
            try:
                content = self._get_file_content(package_json_path)
                package_data = json.loads(content)
                
                # Check engines.node
                if "engines" in package_data and "node" in package_data["engines"]:
                    return package_data["engines"]["node"]
                    
                # Check for ES version indicators
                if "type" in package_data and package_data["type"] == "module":
                    return "ES2015+"
                    
            except json.JSONDecodeError:
                pass

        return None

    def _detect_typescript_version(self, files: list[Path]) -> str | None:
        """Detect TypeScript version from project files."""
        package_json_path = self.project_path / "package.json"
        if package_json_path.exists():
            try:
                content = self._get_file_content(package_json_path)
                package_data = json.loads(content)
                
                # Check devDependencies for typescript
                for deps in ["dependencies", "devDependencies"]:
                    if deps in package_data and "typescript" in package_data[deps]:
                        return package_data[deps]["typescript"]
                        
            except json.JSONDecodeError:
                pass

        return None

    def _detect_java_version(self, files: list[Path]) -> str | None:
        """Detect Java version from project files."""
        # Check pom.xml for Maven projects
        pom_path = self.project_path / "pom.xml"
        if pom_path.exists():
            content = self._get_file_content(pom_path)
            match = re.search(r'<maven\.compiler\.source>([^<]+)</maven\.compiler\.source>', content)
            if match:
                return match.group(1)

        # Check build.gradle for Gradle projects
        gradle_path = self.project_path / "build.gradle"
        if gradle_path.exists():
            content = self._get_file_content(gradle_path)
            match = re.search(r'sourceCompatibility\s*=\s*["\']?([^"\']+)["\']?', content)
            if match:
                return match.group(1)

        return None

    def _detect_language_frameworks(self, language: LanguageType, files: list[Path]) -> list[FrameworkType]:
        """Detect frameworks for a specific language."""
        detector = self.framework_detectors.get_detector(language)
        if detector:
            return detector.detect_frameworks(self.project_path, files)
        return []

    def _analyze_language_conventions(self, language: LanguageType, files: list[Path]) -> LanguageConventions:
        """Analyze coding conventions for a specific language."""
        parser = self.language_parsers.get_parser(language)
        if parser:
            return parser.analyze_conventions(files)
        
        # Default conventions analysis
        return LanguageConventions(
            naming_style={},
            formatting_style={},
            documentation_style={},
            error_handling_style={},
            consistency_score=0.0,
        )

    def _calculate_language_quality(self, language: LanguageType, files: list[Path]) -> float:
        """Calculate quality score for a language's codebase."""
        parser = self.language_parsers.get_parser(language)
        if parser:
            return parser.calculate_quality_score(files)
        return 0.5  # Default neutral score

    def _analyze_framework(self, framework: FrameworkType) -> FrameworkInfo | None:
        """Analyze usage of a specific framework."""
        detector = self.framework_detectors.get_framework_detector(framework)
        if detector:
            return detector.analyze_usage(self.project_path)
        
        # Create a basic framework info if no specific detector
        return FrameworkInfo(
            name=framework.value,
            version="unknown",
            usage_patterns=[],
            configuration_files=[],
            best_practices_compliance=0.5,
            suggested_improvements=[],
        )

    def _extract_naming_patterns(self, language: LanguageType, files: list[Path]) -> dict[str, Any]:
        """Extract naming patterns for a language."""
        patterns = defaultdict(list)
        
        for file_path in files[:10]:  # Limit analysis to avoid performance issues
            content = self._get_file_content(file_path)
            
            if language == LanguageType.PYTHON:
                # Extract Python naming patterns
                patterns["functions"].extend(re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)', content))
                patterns["classes"].extend(re.findall(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)', content))
                patterns["variables"].extend(re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=', content))
            elif language == LanguageType.JAVASCRIPT or language == LanguageType.TYPESCRIPT:
                # Extract JS/TS naming patterns
                patterns["functions"].extend(re.findall(r'function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)', content))
                patterns["functions"].extend(re.findall(r'([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*function', content))
                patterns["classes"].extend(re.findall(r'class\s+([a-zA-Z_$][a-zA-Z0-9_$]*)', content))
            elif language == LanguageType.JAVA:
                # Extract Java naming patterns
                patterns["methods"].extend(re.findall(r'public\s+\w+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', content))
                patterns["classes"].extend(re.findall(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)', content))

        return dict(patterns)

    def _extract_structural_patterns(self, language: LanguageType, files: list[Path]) -> dict[str, Any]:
        """Extract structural patterns for a language."""
        patterns = {}
        
        # Analyze directory structure
        directories = set()
        for file_path in files:
            directories.update(file_path.relative_to(self.project_path).parts[:-1])
        
        patterns["directory_structure"] = list(directories)
        patterns["file_organization"] = self._analyze_file_organization(language, files)
        
        return patterns

    def _extract_import_patterns(self, language: LanguageType, files: list[Path]) -> dict[str, Any]:
        """Extract import patterns for a language."""
        patterns = defaultdict(list)
        
        for file_path in files[:10]:  # Limit analysis
            content = self._get_file_content(file_path)
            
            if language == LanguageType.PYTHON:
                patterns["imports"].extend(re.findall(r'import\s+([a-zA-Z_][a-zA-Z0-9_.]*)', content))
                patterns["from_imports"].extend(re.findall(r'from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import', content))
            elif language == LanguageType.JAVASCRIPT or language == LanguageType.TYPESCRIPT:
                patterns["imports"].extend(re.findall(r'import\s+.*?from\s+["\']([^"\']+)["\']', content))
                patterns["requires"].extend(re.findall(r'require\(["\']([^"\']+)["\']\)', content))
            elif language == LanguageType.JAVA:
                patterns["imports"].extend(re.findall(r'import\s+([a-zA-Z_][a-zA-Z0-9_.]*)', content))

        return dict(patterns)

    def _extract_error_handling_patterns(self, language: LanguageType, files: list[Path]) -> dict[str, Any]:
        """Extract error handling patterns for a language."""
        patterns = defaultdict(int)
        
        for file_path in files[:10]:  # Limit analysis
            content = self._get_file_content(file_path)
            
            if language == LanguageType.PYTHON:
                patterns["try_except"] += len(re.findall(r'try:', content))
                patterns["raise"] += len(re.findall(r'raise\s+', content))
            elif language == LanguageType.JAVASCRIPT or language == LanguageType.TYPESCRIPT:
                patterns["try_catch"] += len(re.findall(r'try\s*{', content))
                patterns["throw"] += len(re.findall(r'throw\s+', content))
            elif language == LanguageType.JAVA:
                patterns["try_catch"] += len(re.findall(r'try\s*{', content))
                patterns["throws"] += len(re.findall(r'throws\s+', content))

        return dict(patterns)

    def _extract_documentation_patterns(self, language: LanguageType, files: list[Path]) -> dict[str, Any]:
        """Extract documentation patterns for a language."""
        patterns = defaultdict(int)
        
        for file_path in files[:10]:  # Limit analysis
            content = self._get_file_content(file_path)
            
            if language == LanguageType.PYTHON:
                patterns["docstrings"] += len(re.findall(r'""".*?"""', content, re.DOTALL))
                patterns["comments"] += len(re.findall(r'#.*', content))
            elif language == LanguageType.JAVASCRIPT or language == LanguageType.TYPESCRIPT:
                patterns["jsdoc"] += len(re.findall(r'/\*\*.*?\*/', content, re.DOTALL))
                patterns["comments"] += len(re.findall(r'//.*', content))
            elif language == LanguageType.JAVA:
                patterns["javadoc"] += len(re.findall(r'/\*\*.*?\*/', content, re.DOTALL))
                patterns["comments"] += len(re.findall(r'//.*', content))

        return dict(patterns)

    def _analyze_file_organization(self, language: LanguageType, files: list[Path]) -> dict[str, Any]:
        """Analyze how files are organized for a language."""
        organization = {
            "total_files": len(files),
            "average_file_size": 0,
            "directory_depth": 0,
        }
        
        total_size = 0
        max_depth = 0
        
        for file_path in files:
            content = self._get_file_content(file_path)
            total_size += len(content.splitlines())
            
            relative_path = file_path.relative_to(self.project_path)
            depth = len(relative_path.parts) - 1
            max_depth = max(max_depth, depth)
        
        if files:
            organization["average_file_size"] = total_size / len(files)
        organization["directory_depth"] = max_depth
        
        return organization

    def _analyze_api_interactions(self) -> dict[str, Any]:
        """Analyze API interactions between different languages."""
        interactions = {}
        
        # Look for REST API endpoints
        if LanguageType.PYTHON in self._language_files:
            interactions["python_apis"] = self._find_python_apis()
        
        if LanguageType.JAVASCRIPT in self._language_files or LanguageType.TYPESCRIPT in self._language_files:
            interactions["js_api_calls"] = self._find_js_api_calls()
        
        return interactions

    def _analyze_cross_language_data_flow(self) -> dict[str, Any]:
        """Analyze data flow between different languages."""
        data_flow = {}
        
        # Look for shared data formats
        if LanguageType.JSON in self._language_files:
            data_flow["json_schemas"] = self._analyze_json_schemas()
        
        if LanguageType.SQL in self._language_files:
            data_flow["database_schemas"] = self._analyze_sql_schemas()
        
        return data_flow

    def _analyze_shared_configurations(self) -> dict[str, Any]:
        """Analyze shared configuration files."""
        configs = {}
        
        # Docker configurations
        if LanguageType.DOCKERFILE in self._language_files:
            configs["docker"] = self._analyze_docker_configs()
        
        # Package configurations
        configs["package_managers"] = self._analyze_package_managers()
        
        return configs

    def _analyze_build_dependencies(self) -> dict[str, Any]:
        """Analyze build system dependencies."""
        dependencies = {}
        
        # Check for various build systems
        if (self.project_path / "package.json").exists():
            dependencies["npm"] = self._analyze_npm_dependencies()
        
        if (self.project_path / "pyproject.toml").exists():
            dependencies["python"] = self._analyze_python_dependencies()
        
        if (self.project_path / "pom.xml").exists():
            dependencies["maven"] = self._analyze_maven_dependencies()
        
        return dependencies

    def _identify_integration_patterns(self) -> list[str]:
        """Identify common integration patterns."""
        patterns = []
        
        # Check for microservices patterns
        if self._has_microservices_structure():
            patterns.append("microservices")
        
        # Check for API Gateway patterns
        if self._has_api_gateway():
            patterns.append("api_gateway")
        
        # Check for event-driven patterns
        if self._has_event_driven_architecture():
            patterns.append("event_driven")
        
        return patterns

    def _find_python_apis(self) -> list[str]:
        """Find Python API endpoints."""
        apis = []
        python_files = self._language_files.get(LanguageType.PYTHON, [])
        
        for file_path in python_files:
            content = self._get_file_content(file_path)
            # Look for Flask/FastAPI/Django routes
            apis.extend(re.findall(r'@app\.route\(["\']([^"\']+)["\']', content))
            apis.extend(re.findall(r'@router\.\w+\(["\']([^"\']+)["\']', content))
        
        return apis

    def _find_js_api_calls(self) -> list[str]:
        """Find JavaScript/TypeScript API calls."""
        api_calls = []
        js_files = self._language_files.get(LanguageType.JAVASCRIPT, [])
        ts_files = self._language_files.get(LanguageType.TYPESCRIPT, [])
        
        for file_path in js_files + ts_files:
            content = self._get_file_content(file_path)
            # Look for fetch/axios calls
            api_calls.extend(re.findall(r'fetch\(["\']([^"\']+)["\']', content))
            api_calls.extend(re.findall(r'axios\.\w+\(["\']([^"\']+)["\']', content))
        
        return api_calls

    def _analyze_json_schemas(self) -> dict[str, Any]:
        """Analyze JSON schema files."""
        schemas = {}
        json_files = self._language_files.get(LanguageType.JSON, [])
        
        for file_path in json_files:
            if "schema" in file_path.name.lower():
                try:
                    content = self._get_file_content(file_path)
                    schema_data = json.loads(content)
                    schemas[file_path.name] = schema_data
                except json.JSONDecodeError:
                    continue
        
        return schemas

    def _analyze_sql_schemas(self) -> dict[str, Any]:
        """Analyze SQL schema files."""
        schemas = {}
        sql_files = self._language_files.get(LanguageType.SQL, [])
        
        for file_path in sql_files:
            content = self._get_file_content(file_path)
            # Extract table definitions
            tables = re.findall(r'CREATE\s+TABLE\s+(\w+)', content, re.IGNORECASE)
            if tables:
                schemas[file_path.name] = tables
        
        return schemas

    def _analyze_docker_configs(self) -> dict[str, Any]:
        """Analyze Docker configurations."""
        configs = {}
        docker_files = self._language_files.get(LanguageType.DOCKERFILE, [])
        
        for file_path in docker_files:
            content = self._get_file_content(file_path)
            # Extract base images
            base_images = re.findall(r'FROM\s+([^\s]+)', content)
            if base_images:
                configs[file_path.name] = {"base_images": base_images}
        
        return configs

    def _analyze_package_managers(self) -> dict[str, Any]:
        """Analyze package manager configurations."""
        managers = {}
        
        # Check for various package managers
        package_files = {
            "npm": "package.json",
            "pip": "requirements.txt",
            "poetry": "pyproject.toml",
            "maven": "pom.xml",
            "gradle": "build.gradle",
        }
        
        for manager, filename in package_files.items():
            if (self.project_path / filename).exists():
                managers[manager] = filename
        
        return managers

    def _analyze_npm_dependencies(self) -> dict[str, Any]:
        """Analyze npm dependencies."""
        package_json_path = self.project_path / "package.json"
        try:
            content = self._get_file_content(package_json_path)
            package_data = json.loads(content)
            return {
                "dependencies": package_data.get("dependencies", {}),
                "devDependencies": package_data.get("devDependencies", {}),
            }
        except json.JSONDecodeError:
            return {}

    def _analyze_python_dependencies(self) -> dict[str, Any]:
        """Analyze Python dependencies."""
        dependencies = {}
        
        # Check pyproject.toml
        pyproject_path = self.project_path / "pyproject.toml"
        if pyproject_path.exists():
            content = self._get_file_content(pyproject_path)
            # Simple extraction - could be enhanced with proper TOML parsing
            deps = re.findall(r'dependencies\s*=\s*\[(.*?)\]', content, re.DOTALL)
            if deps:
                dependencies["pyproject"] = deps[0]
        
        # Check requirements.txt
        req_path = self.project_path / "requirements.txt"
        if req_path.exists():
            content = self._get_file_content(req_path)
            dependencies["requirements"] = content.splitlines()
        
        return dependencies

    def _analyze_maven_dependencies(self) -> dict[str, Any]:
        """Analyze Maven dependencies."""
        pom_path = self.project_path / "pom.xml"
        content = self._get_file_content(pom_path)
        
        # Extract dependencies (simplified)
        dependencies = re.findall(r'<artifactId>([^<]+)</artifactId>', content)
        return {"artifacts": dependencies}

    def _has_microservices_structure(self) -> bool:
        """Check if project has microservices structure."""
        # Look for multiple service directories
        service_indicators = ["service", "api", "microservice", "ms-"]
        service_count = 0
        
        for part in self.project_path.rglob("*"):
            if part.is_dir():
                for indicator in service_indicators:
                    if indicator in part.name.lower():
                        service_count += 1
                        break
        
        return service_count >= 2

    def _has_api_gateway(self) -> bool:
        """Check if project has API gateway patterns."""
        gateway_indicators = ["gateway", "proxy", "router", "nginx"]
        
        for file_path in self.project_path.rglob("*"):
            if file_path.is_file():
                for indicator in gateway_indicators:
                    if indicator in file_path.name.lower():
                        return True
        
        return False

    def _has_event_driven_architecture(self) -> bool:
        """Check if project uses event-driven architecture."""
        event_indicators = ["event", "message", "queue", "kafka", "rabbitmq", "redis"]
        
        # Check configuration files
        for file_path in self.project_path.rglob("*"):
            if file_path.is_file():
                content = self._get_file_content(file_path).lower()
                for indicator in event_indicators:
                    if indicator in content:
                        return True
        
        return False