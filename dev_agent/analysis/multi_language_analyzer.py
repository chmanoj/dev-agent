"""Multi-language project detection and analysis engine."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from ..interfaces.analysis_interface import ICodebaseAnalyzer
from ..models.analysis import LanguageInfo, FrameworkInfo, CrossLanguageMappings
from ..models.enums import LanguageType, FrameworkType
from .language_parsers import (
    PythonParser, JavaScriptParser, TypeScriptParser, JavaParser,
    HTMLParser, CSSParser, JSONParser, YAMLParser, XMLParser,
    SQLParser, DockerfileParser, ShellParser
)
from .framework_detectors import (
    PythonFrameworkDetector, JavaScriptFrameworkDetector,
    TypeScriptFrameworkDetector, JavaFrameworkDetector, WebFrameworkDetector
)
from .pattern_analyzers import (
    PythonPatternAnalyzer, JavaScriptPatternAnalyzer,
    TypeScriptPatternAnalyzer, JavaPatternAnalyzer, WebPatternAnalyzer
)


class MultiLanguageAnalyzer:
    """Analyzes projects with multiple programming languages and frameworks."""

    def __init__(self, project_path: str):
        """Initialize the multi-language analyzer.

        Args:
            project_path: Path to the project root directory
        """
        self.project_path = Path(project_path)
        self.language_parsers: dict[str, LanguageParser] = {}
        self.framework_detectors: dict[str, FrameworkDetector] = {}
        self.pattern_analyzers: dict[str, PatternAnalyzer] = {}
        
        # Initialize language-specific components
        self._initialize_language_support()
        self._initialize_framework_detection()
        self._initialize_pattern_analysis()

    def detect_project_languages(self) -> list[LanguageInfo]:
        """Detect all programming languages used in the project.

        Returns:
            List of LanguageInfo objects with detected languages and metadata
        """
        language_stats = defaultdict(lambda: {
            'file_count': 0,
            'line_count': 0,
            'files': [],
            'frameworks': set(),
            'conventions': {}
        })

        # Scan all files in the project
        for file_path in self._get_source_files():
            language = self._detect_file_language(file_path)
            if language:
                stats = language_stats[language]
                stats['file_count'] += 1
                stats['files'].append(str(file_path))
                
                # Count lines of code
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = len([line for line in f if line.strip()])
                        stats['line_count'] += lines
                except (UnicodeDecodeError, IOError):
                    continue

        # Convert to LanguageInfo objects
        languages = []
        for lang, stats in language_stats.items():
            if stats['file_count'] > 0:
                # Detect frameworks for this language
                frameworks = self._detect_language_frameworks(lang, stats['files'])
                
                # Analyze conventions
                conventions = self._analyze_language_conventions(lang, stats['files'])
                
                # Calculate quality score
                quality_score = self._calculate_language_quality(lang, stats)
                
                language_info = LanguageInfo(
                    language=lang,
                    version=self._detect_language_version(lang, stats['files']),
                    file_count=stats['file_count'],
                    line_count=stats['line_count'],
                    frameworks=frameworks,
                    conventions=conventions,
                    quality_score=quality_score
                )
                languages.append(language_info)

        return sorted(languages, key=lambda x: x.line_count, reverse=True)

    def analyze_framework_usage(self) -> list[FrameworkInfo]:
        """Analyze framework usage across all detected languages.

        Returns:
            List of FrameworkInfo objects with framework details
        """
        frameworks = []
        
        # Get all source files grouped by language
        language_files = defaultdict(list)
        for file_path in self._get_source_files():
            language = self._detect_file_language(file_path)
            if language:
                language_files[language].append(file_path)

        # Analyze frameworks for each language
        for language, files in language_files.items():
            lang_frameworks = self._detect_language_frameworks(language, files)
            
            for framework_name in lang_frameworks:
                framework_info = self._analyze_framework_details(
                    framework_name, language, files
                )
                if framework_info:
                    frameworks.append(framework_info)

        return frameworks

    def extract_language_patterns(self, language: str, files: list[str]) -> dict[str, Any]:
        """Extract language-specific patterns from source files.

        Args:
            language: Programming language name
            files: List of file paths for the language

        Returns:
            Dictionary containing extracted patterns
        """
        if language not in self.pattern_analyzers:
            return {}

        analyzer = self.pattern_analyzers[language]
        return analyzer.extract_patterns(files)

    def generate_cross_language_mappings(self) -> CrossLanguageMappings:
        """Generate mappings between different languages in the project.

        Returns:
            CrossLanguageMappings object with interaction analysis
        """
        languages = self.detect_project_languages()
        
        # Analyze API interactions
        api_interactions = self._analyze_api_interactions(languages)
        
        # Analyze data flow between languages
        data_flow = self._analyze_cross_language_data_flow(languages)
        
        # Analyze shared configurations
        shared_configs = self._analyze_shared_configurations(languages)
        
        # Analyze build dependencies
        build_dependencies = self._analyze_build_dependencies(languages)

        return CrossLanguageMappings(
            api_interactions=api_interactions,
            data_flow=data_flow,
            shared_configurations=shared_configs,
            build_dependencies=build_dependencies,
            integration_patterns=self._identify_integration_patterns(languages)
        )

    def _initialize_language_support(self) -> None:
        """Initialize language-specific parsers."""
        self.language_parsers = {
            'python': PythonParser(),
            'javascript': JavaScriptParser(),
            'typescript': TypeScriptParser(),
            'java': JavaParser(),
            'html': HTMLParser(),
            'css': CSSParser(),
            'json': JSONParser(),
            'yaml': YAMLParser(),
            'xml': XMLParser(),
            'sql': SQLParser(),
            'dockerfile': DockerfileParser(),
            'shell': ShellParser()
        }

    def _initialize_framework_detection(self) -> None:
        """Initialize framework detection capabilities."""
        self.framework_detectors = {
            'python': PythonFrameworkDetector(),
            'javascript': JavaScriptFrameworkDetector(),
            'typescript': TypeScriptFrameworkDetector(),
            'java': JavaFrameworkDetector(),
            'web': WebFrameworkDetector()
        }

    def _initialize_pattern_analysis(self) -> None:
        """Initialize pattern analysis for each language."""
        self.pattern_analyzers = {
            'python': PythonPatternAnalyzer(),
            'javascript': JavaScriptPatternAnalyzer(),
            'typescript': TypeScriptPatternAnalyzer(),
            'java': JavaPatternAnalyzer(),
            'web': WebPatternAnalyzer()
        }

    def _get_source_files(self) -> list[Path]:
        """Get all source files in the project."""
        source_files = []
        
        # Define file extensions for different languages
        extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.html': 'html',
            '.htm': 'html',
            '.css': 'css',
            '.scss': 'css',
            '.sass': 'css',
            '.less': 'css',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.xml': 'xml',
            '.sql': 'sql',
            '.sh': 'shell',
            '.bash': 'shell',
            '.zsh': 'shell'
        }

        # Exclude common non-source directories
        exclude_dirs = {
            '.git', '.svn', '.hg',
            'node_modules', '__pycache__', '.pytest_cache',
            'build', 'dist', 'target', 'out',
            '.venv', 'venv', 'env',
            '.idea', '.vscode'
        }

        for file_path in self.project_path.rglob('*'):
            if file_path.is_file():
                # Skip files in excluded directories
                if any(excluded in file_path.parts for excluded in exclude_dirs):
                    continue
                
                # Check if file has a supported extension
                if file_path.suffix.lower() in extensions:
                    source_files.append(file_path)
                elif file_path.name.lower() in ['dockerfile', 'makefile', 'rakefile']:
                    source_files.append(file_path)

        return source_files

    def _detect_file_language(self, file_path: Path) -> str | None:
        """Detect the programming language of a file."""
        extension = file_path.suffix.lower()
        name = file_path.name.lower()

        # Extension-based detection
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.html': 'html',
            '.htm': 'html',
            '.css': 'css',
            '.scss': 'css',
            '.sass': 'css',
            '.less': 'css',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.xml': 'xml',
            '.sql': 'sql',
            '.sh': 'shell',
            '.bash': 'shell',
            '.zsh': 'shell'
        }

        if extension in extension_map:
            return extension_map[extension]

        # Name-based detection for files without extensions
        if name in ['dockerfile']:
            return 'dockerfile'
        elif name in ['makefile', 'rakefile']:
            return 'makefile'

        return None

    def _detect_language_frameworks(self, language: str, files: list[str]) -> list[str]:
        """Detect frameworks used for a specific language."""
        if language not in self.framework_detectors:
            return []

        detector = self.framework_detectors[language]
        return detector.detect_frameworks(files)

    def _analyze_language_conventions(self, language: str, files: list[str]) -> dict[str, Any]:
        """Analyze coding conventions for a language."""
        if language not in self.pattern_analyzers:
            return {}

        analyzer = self.pattern_analyzers[language]
        return analyzer.analyze_conventions(files)

    def _calculate_language_quality(self, language: str, stats: dict[str, Any]) -> float:
        """Calculate a quality score for language usage."""
        base_score = 0.5
        
        # Factor in file count (more files = more established)
        file_factor = min(stats['file_count'] / 10, 1.0) * 0.2
        
        # Factor in line count (more code = more established)
        line_factor = min(stats['line_count'] / 1000, 1.0) * 0.2
        
        # Factor in framework usage (frameworks indicate mature usage)
        framework_factor = min(len(stats['frameworks']) / 3, 1.0) * 0.1
        
        return base_score + file_factor + line_factor + framework_factor

    def _detect_language_version(self, language: str, files: list[str]) -> str | None:
        """Detect the version of a programming language."""
        if language == 'python':
            return self._detect_python_version(files)
        elif language in ['javascript', 'typescript']:
            return self._detect_js_version(files)
        elif language == 'java':
            return self._detect_java_version(files)
        
        return None

    def _detect_python_version(self, files: list[str]) -> str | None:
        """Detect Python version from source files."""
        version_indicators = {
            'f"': '3.6+',
            ':=': '3.8+',
            'match ': '3.10+',
            'from __future__ import annotations': '3.7+'
        }

        for file_path in files[:10]:  # Check first 10 files
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for indicator, version in version_indicators.items():
                        if indicator in content:
                            return version
            except (UnicodeDecodeError, IOError):
                continue

        return '3.x'

    def _detect_js_version(self, files: list[str]) -> str | None:
        """Detect JavaScript/TypeScript version."""
        # Look for package.json to determine version
        package_json = self.project_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'engines' in data and 'node' in data['engines']:
                        return data['engines']['node']
            except (json.JSONDecodeError, IOError):
                pass

        return 'ES6+'

    def _detect_java_version(self, files: list[str]) -> str | None:
        """Detect Java version from source files."""
        version_indicators = {
            'var ': '10+',
            'record ': '14+',
            'sealed ': '17+',
            'switch.*->': '14+'
        }

        for file_path in files[:10]:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for pattern, version in version_indicators.items():
                        if re.search(pattern, content):
                            return version
            except (UnicodeDecodeError, IOError):
                continue

        return '8+'

    def _analyze_framework_details(self, framework_name: str, language: str, files: list[str]) -> FrameworkInfo | None:
        """Analyze detailed information about a framework."""
        if language not in self.framework_detectors:
            return None

        detector = self.framework_detectors[language]
        return detector.analyze_framework(framework_name, files)

    def _analyze_api_interactions(self, languages: list[LanguageInfo]) -> dict[str, Any]:
        """Analyze API interactions between different languages."""
        interactions = {}
        
        # Look for REST API patterns
        rest_patterns = self._find_rest_api_patterns(languages)
        if rest_patterns:
            interactions['rest_apis'] = rest_patterns

        # Look for GraphQL patterns
        graphql_patterns = self._find_graphql_patterns(languages)
        if graphql_patterns:
            interactions['graphql'] = graphql_patterns

        # Look for RPC patterns
        rpc_patterns = self._find_rpc_patterns(languages)
        if rpc_patterns:
            interactions['rpc'] = rpc_patterns

        return interactions

    def _analyze_cross_language_data_flow(self, languages: list[LanguageInfo]) -> dict[str, Any]:
        """Analyze data flow between different languages."""
        data_flow = {}
        
        # Look for shared data formats
        shared_formats = self._find_shared_data_formats(languages)
        if shared_formats:
            data_flow['shared_formats'] = shared_formats

        # Look for database interactions
        db_interactions = self._find_database_interactions(languages)
        if db_interactions:
            data_flow['database'] = db_interactions

        return data_flow

    def _analyze_shared_configurations(self, languages: list[LanguageInfo]) -> dict[str, Any]:
        """Analyze shared configuration files."""
        configs = {}
        
        # Look for common config files
        config_files = [
            'docker-compose.yml', 'Dockerfile',
            '.env', '.env.example',
            'nginx.conf', 'apache.conf',
            'kubernetes.yaml', 'k8s.yaml'
        ]

        for config_file in config_files:
            config_path = self.project_path / config_file
            if config_path.exists():
                configs[config_file] = str(config_path)

        return configs

    def _analyze_build_dependencies(self, languages: list[LanguageInfo]) -> dict[str, Any]:
        """Analyze build system dependencies."""
        dependencies = {}
        
        # Look for build files
        build_files = {
            'package.json': 'npm/yarn',
            'requirements.txt': 'pip',
            'pyproject.toml': 'pip/poetry',
            'pom.xml': 'maven',
            'build.gradle': 'gradle',
            'Makefile': 'make',
            'CMakeLists.txt': 'cmake'
        }

        for build_file, build_system in build_files.items():
            build_path = self.project_path / build_file
            if build_path.exists():
                dependencies[build_system] = str(build_path)

        return dependencies

    def _identify_integration_patterns(self, languages: list[LanguageInfo]) -> list[str]:
        """Identify common integration patterns."""
        patterns = []
        
        lang_names = [lang.language for lang in languages]
        
        # Common patterns
        if 'python' in lang_names and 'javascript' in lang_names:
            patterns.append('Full-stack web application')
        
        if 'java' in lang_names and 'javascript' in lang_names:
            patterns.append('Enterprise web application')
        
        if 'python' in lang_names and 'sql' in lang_names:
            patterns.append('Data-driven application')
        
        if 'dockerfile' in lang_names:
            patterns.append('Containerized application')
        
        if len(lang_names) >= 3:
            patterns.append('Polyglot architecture')

        return patterns

    def _find_rest_api_patterns(self, languages: list[LanguageInfo]) -> dict[str, Any]:
        """Find REST API patterns in the codebase."""
        patterns = {}
        
        # Look for common REST patterns in different languages
        rest_indicators = {
            'python': ['@app.route', 'FastAPI', 'flask', 'django'],
            'javascript': ['express', 'app.get', 'app.post', 'router'],
            'java': ['@RestController', '@RequestMapping', 'Spring']
        }

        for lang_info in languages:
            if lang_info.language in rest_indicators:
                indicators = rest_indicators[lang_info.language]
                # This would need actual file content analysis
                patterns[lang_info.language] = indicators

        return patterns

    def _find_graphql_patterns(self, languages: list[LanguageInfo]) -> dict[str, Any]:
        """Find GraphQL patterns in the codebase."""
        patterns = {}
        
        # Look for GraphQL files and patterns
        graphql_files = list(self.project_path.rglob('*.graphql'))
        graphql_files.extend(list(self.project_path.rglob('*.gql')))
        
        if graphql_files:
            patterns['schema_files'] = [str(f) for f in graphql_files]

        return patterns

    def _find_rpc_patterns(self, languages: list[LanguageInfo]) -> dict[str, Any]:
        """Find RPC patterns in the codebase."""
        patterns = {}
        
        # Look for gRPC and other RPC patterns
        proto_files = list(self.project_path.rglob('*.proto'))
        if proto_files:
            patterns['grpc'] = [str(f) for f in proto_files]

        return patterns

    def _find_shared_data_formats(self, languages: list[LanguageInfo]) -> dict[str, Any]:
        """Find shared data formats between languages."""
        formats = {}
        
        # Look for common data format files
        json_files = list(self.project_path.rglob('*.json'))
        if json_files:
            formats['json'] = len(json_files)

        yaml_files = list(self.project_path.rglob('*.yaml'))
        yaml_files.extend(list(self.project_path.rglob('*.yml')))
        if yaml_files:
            formats['yaml'] = len(yaml_files)

        xml_files = list(self.project_path.rglob('*.xml'))
        if xml_files:
            formats['xml'] = len(xml_files)

        return formats

    def _find_database_interactions(self, languages: list[LanguageInfo]) -> dict[str, Any]:
        """Find database interaction patterns."""
        interactions = {}
        
        # Look for database-related files
        sql_files = list(self.project_path.rglob('*.sql'))
        if sql_files:
            interactions['sql_files'] = len(sql_files)

        # Look for migration directories
        migration_dirs = [
            'migrations', 'migrate', 'db/migrate',
            'alembic/versions', 'flyway/sql'
        ]
        
        for migration_dir in migration_dirs:
            migration_path = self.project_path / migration_dir
            if migration_path.exists() and migration_path.is_dir():
                interactions['migrations'] = str(migration_path)
                break

        return interactions