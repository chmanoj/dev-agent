"""Language detection service for analyzing project files and configuration."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set

import tomllib

from dev_agent.models.enums import FrameworkType, LanguageType
from dev_agent.models.language_patterns import LanguagePatterns, LanguageProjectContext

logger = logging.getLogger(__name__)


class LanguageDetector:
    """Detects programming language and patterns from project files.
    
    This class analyzes project structure, configuration files, and source code
    to determine the primary programming language and establish appropriate
    naming conventions and patterns.
    """
    
    # File extension mappings to languages
    EXTENSION_MAPPING: Dict[str, LanguageType] = {
        ".py": LanguageType.PYTHON,
        ".js": LanguageType.JAVASCRIPT,
        ".jsx": LanguageType.JAVASCRIPT,
        ".ts": LanguageType.TYPESCRIPT,
        ".tsx": LanguageType.TYPESCRIPT,
        ".java": LanguageType.JAVA,
        ".html": LanguageType.HTML,
        ".css": LanguageType.CSS,
        ".json": LanguageType.JSON,
        ".yml": LanguageType.YAML,
        ".yaml": LanguageType.YAML,
        ".xml": LanguageType.XML,
        ".sql": LanguageType.SQL,
        ".sh": LanguageType.SHELL,
        ".bash": LanguageType.SHELL,
        ".zsh": LanguageType.SHELL,
    }
    
    # Configuration files that indicate specific languages
    CONFIG_FILE_INDICATORS: Dict[str, LanguageType] = {
        "pyproject.toml": LanguageType.PYTHON,
        "setup.py": LanguageType.PYTHON,
        "requirements.txt": LanguageType.PYTHON,
        "Pipfile": LanguageType.PYTHON,
        "poetry.lock": LanguageType.PYTHON,
        "package.json": LanguageType.JAVASCRIPT,
        "yarn.lock": LanguageType.JAVASCRIPT,
        "package-lock.json": LanguageType.JAVASCRIPT,
        "tsconfig.json": LanguageType.TYPESCRIPT,
        "pom.xml": LanguageType.JAVA,
        "build.gradle": LanguageType.JAVA,
        "Dockerfile": LanguageType.DOCKERFILE,
        "Makefile": LanguageType.MAKEFILE,
        "makefile": LanguageType.MAKEFILE,
    }
    
    # Predefined language patterns
    LANGUAGE_PATTERNS: Dict[LanguageType, LanguagePatterns] = {
        LanguageType.PYTHON: LanguagePatterns(
            file_extension=".py",
            test_file_suffix="_test.py",
            config_files=["pyproject.toml", "setup.py", "requirements.txt", "setup.cfg"],
            class_naming="PascalCase",
            method_naming="snake_case",
            variable_naming="snake_case",
            constant_naming="UPPER_CASE",
            file_naming="snake_case",
            service_suffix="_service",
            interface_prefix="",
            abstract_prefix="Abstract",
            source_directory="",
            test_directory="tests",
            config_directory="config",
            import_style="explicit",
            module_separator=".",
        ),
        LanguageType.TYPESCRIPT: LanguagePatterns(
            file_extension=".ts",
            test_file_suffix=".test.ts",
            config_files=["tsconfig.json", "package.json", "webpack.config.js"],
            class_naming="PascalCase",
            method_naming="camelCase",
            variable_naming="camelCase",
            constant_naming="UPPER_CASE",
            file_naming="kebab-case",
            service_suffix="Service",
            interface_prefix="I",
            abstract_prefix="Abstract",
            source_directory="src",
            test_directory="__tests__",
            config_directory="config",
            import_style="explicit",
            module_separator="/",
        ),
        LanguageType.JAVASCRIPT: LanguagePatterns(
            file_extension=".js",
            test_file_suffix=".test.js",
            config_files=["package.json", "webpack.config.js", ".eslintrc.js"],
            class_naming="PascalCase",
            method_naming="camelCase",
            variable_naming="camelCase",
            constant_naming="UPPER_CASE",
            file_naming="kebab-case",
            service_suffix="Service",
            interface_prefix="",
            abstract_prefix="Abstract",
            source_directory="src",
            test_directory="__tests__",
            config_directory="config",
            import_style="explicit",
            module_separator="/",
        ),
        LanguageType.JAVA: LanguagePatterns(
            file_extension=".java",
            test_file_suffix="Test.java",
            config_files=["pom.xml", "build.gradle", "build.xml"],
            class_naming="PascalCase",
            method_naming="camelCase",
            variable_naming="camelCase",
            constant_naming="UPPER_CASE",
            file_naming="PascalCase",
            service_suffix="Service",
            interface_prefix="I",
            abstract_prefix="Abstract",
            source_directory="src/main/java",
            test_directory="src/test/java",
            config_directory="src/main/resources",
            import_style="explicit",
            module_separator=".",
        ),
    }
    
    def __init__(self):
        """Initialize the language detector."""
        self._cache: Dict[str, LanguageProjectContext] = {}
    
    def detect_primary_language(self, project_path: Path) -> LanguageType:
        """Detect the primary programming language of a project.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            The detected primary language
            
        Raises:
            ValueError: If no language can be detected
        """
        if not project_path.exists() or not project_path.is_dir():
            raise ValueError(f"Project path does not exist or is not a directory: {project_path}")
        
        # Check configuration files first (most reliable)
        config_language = self._detect_from_config_files(project_path)
        if config_language:
            logger.info(f"Detected language from config files: {config_language.value}")
            return config_language
        
        # Analyze source files by extension
        file_language = self._detect_from_file_extensions(project_path)
        if file_language:
            logger.info(f"Detected language from file extensions: {file_language.value}")
            return file_language
        
        # Default fallback
        logger.warning("Could not detect language, defaulting to Python")
        return LanguageType.PYTHON
    
    def get_language_patterns(self, language: LanguageType) -> LanguagePatterns:
        """Get the language patterns for a specific language.
        
        Args:
            language: The programming language
            
        Returns:
            Language patterns for the specified language
            
        Raises:
            ValueError: If language patterns are not available
        """
        if language not in self.LANGUAGE_PATTERNS:
            raise ValueError(f"No patterns available for language: {language.value}")
        
        return self.LANGUAGE_PATTERNS[language]
    
    def analyze_project_context(self, project_path: Path) -> LanguageProjectContext:
        """Analyze a project and return comprehensive context information.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Complete project context including language and framework information
        """
        project_key = str(project_path.resolve())
        
        # Check cache first
        if project_key in self._cache:
            return self._cache[project_key]
        
        # Detect primary language
        primary_language = self.detect_primary_language(project_path)
        
        # Get language patterns
        language_patterns = self.get_language_patterns(primary_language)
        
        # Analyze project structure
        source_dirs = self._find_source_directories(project_path, language_patterns)
        test_dirs = self._find_test_directories(project_path, language_patterns)
        config_files = self._find_config_files(project_path)
        
        # Detect package manager and build tools
        package_manager = self._detect_package_manager(project_path)
        build_tools = self._detect_build_tools(project_path)
        
        # Create project context
        context = LanguageProjectContext(
            primary_language=primary_language,
            detected_frameworks=[],  # Will be populated by framework detector
            language_patterns=language_patterns,
            framework_patterns=[],  # Will be populated by framework detector
            source_directories=source_dirs,
            test_directories=test_dirs,
            config_files=config_files,
            package_manager=package_manager,
            build_tools=build_tools,
        )
        
        # Cache the result
        self._cache[project_key] = context
        
        return context
    
    def validate_naming_convention(self, name: str, convention_type: str, language: LanguageType) -> bool:
        """Validate if a name follows the language's naming conventions.
        
        Args:
            name: The name to validate
            convention_type: Type of naming convention ('class', 'method', 'file', etc.)
            language: The programming language
            
        Returns:
            True if the name follows conventions, False otherwise
        """
        patterns = self.get_language_patterns(language)
        
        if convention_type == "class":
            return patterns.validate_class_name(name)
        elif convention_type == "method":
            return patterns.validate_method_name(name)
        elif convention_type == "file":
            return patterns.validate_file_name(name)
        else:
            logger.warning(f"Unknown convention type: {convention_type}")
            return True
    
    def _detect_from_config_files(self, project_path: Path) -> Optional[LanguageType]:
        """Detect language from configuration files.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Detected language or None if not found
        """
        for file_name, language in self.CONFIG_FILE_INDICATORS.items():
            config_file = project_path / file_name
            if config_file.exists():
                logger.debug(f"Found config file: {file_name} -> {language.value}")
                return language
        
        return None
    
    def _detect_from_file_extensions(self, project_path: Path) -> Optional[LanguageType]:
        """Detect language from file extensions in the project.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Most common language based on file extensions
        """
        extension_counts: Dict[LanguageType, int] = {}
        
        # Count files by extension (excluding common directories)
        exclude_dirs = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache"}
        
        for file_path in project_path.rglob("*"):
            if file_path.is_file() and not any(part in exclude_dirs for part in file_path.parts):
                extension = file_path.suffix.lower()
                if extension in self.EXTENSION_MAPPING:
                    language = self.EXTENSION_MAPPING[extension]
                    extension_counts[language] = extension_counts.get(language, 0) + 1
        
        if not extension_counts:
            return None
        
        # Return the most common language
        most_common_language = max(extension_counts, key=extension_counts.get)
        logger.debug(f"File extension analysis: {extension_counts}")
        
        return most_common_language
    
    def _find_source_directories(self, project_path: Path, patterns: LanguagePatterns) -> List[str]:
        """Find source code directories in the project.
        
        Args:
            project_path: Path to the project directory
            patterns: Language patterns to guide detection
            
        Returns:
            List of source directory paths relative to project root
        """
        source_dirs = []
        
        # Check for pattern-specific source directory
        if patterns.source_directory:
            src_path = project_path / patterns.source_directory
            if src_path.exists() and src_path.is_dir():
                source_dirs.append(patterns.source_directory)
        
        # Common source directory names
        common_src_dirs = ["src", "lib", "app", "source"]
        for dir_name in common_src_dirs:
            src_path = project_path / dir_name
            if src_path.exists() and src_path.is_dir():
                source_dirs.append(dir_name)
        
        # If no specific source directories found, assume root is source
        if not source_dirs:
            source_dirs.append(".")
        
        return list(set(source_dirs))  # Remove duplicates
    
    def _find_test_directories(self, project_path: Path, patterns: LanguagePatterns) -> List[str]:
        """Find test directories in the project.
        
        Args:
            project_path: Path to the project directory
            patterns: Language patterns to guide detection
            
        Returns:
            List of test directory paths relative to project root
        """
        test_dirs = []
        
        # Check for pattern-specific test directory
        if patterns.test_directory:
            test_path = project_path / patterns.test_directory
            if test_path.exists() and test_path.is_dir():
                test_dirs.append(patterns.test_directory)
        
        # Common test directory names
        common_test_dirs = ["tests", "test", "__tests__", "spec", "specs"]
        for dir_name in common_test_dirs:
            test_path = project_path / dir_name
            if test_path.exists() and test_path.is_dir():
                test_dirs.append(dir_name)
        
        return list(set(test_dirs))  # Remove duplicates
    
    def _find_config_files(self, project_path: Path) -> List[str]:
        """Find configuration files in the project.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            List of configuration file paths relative to project root
        """
        config_files = []
        
        # Check for known configuration files
        for config_file in self.CONFIG_FILE_INDICATORS.keys():
            file_path = project_path / config_file
            if file_path.exists():
                config_files.append(config_file)
        
        # Additional common config files
        additional_configs = [
            ".gitignore", ".env", ".env.example", "README.md", "LICENSE",
            ".eslintrc.json", ".prettierrc", "jest.config.js", "pytest.ini",
            "tox.ini", ".flake8", "mypy.ini", ".pre-commit-config.yaml"
        ]
        
        for config_file in additional_configs:
            file_path = project_path / config_file
            if file_path.exists():
                config_files.append(config_file)
        
        return config_files
    
    def _detect_package_manager(self, project_path: Path) -> Optional[str]:
        """Detect the package manager used in the project.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Detected package manager name or None
        """
        # Python package managers
        if (project_path / "pyproject.toml").exists():
            # Check if using uv, poetry, or other modern tools
            try:
                with open(project_path / "pyproject.toml", "rb") as f:
                    pyproject_data = tomllib.load(f)
                    
                if "tool" in pyproject_data:
                    if "poetry" in pyproject_data["tool"]:
                        return "poetry"
                    elif "hatch" in pyproject_data["tool"]:
                        return "hatch"
                    elif "setuptools" in pyproject_data["tool"]:
                        return "setuptools"
                
                # Check for uv.lock
                if (project_path / "uv.lock").exists():
                    return "uv"
                    
                return "pip"  # Default for pyproject.toml
            except Exception as e:
                logger.debug(f"Error reading pyproject.toml: {e}")
                return "pip"
        
        if (project_path / "Pipfile").exists():
            return "pipenv"
        
        if (project_path / "poetry.lock").exists():
            return "poetry"
        
        if (project_path / "requirements.txt").exists():
            return "pip"
        
        # JavaScript/TypeScript package managers
        if (project_path / "yarn.lock").exists():
            return "yarn"
        
        if (project_path / "package-lock.json").exists():
            return "npm"
        
        if (project_path / "pnpm-lock.yaml").exists():
            return "pnpm"
        
        if (project_path / "package.json").exists():
            return "npm"  # Default for package.json
        
        # Java build tools
        if (project_path / "pom.xml").exists():
            return "maven"
        
        if (project_path / "build.gradle").exists() or (project_path / "build.gradle.kts").exists():
            return "gradle"
        
        return None
    
    def _detect_build_tools(self, project_path: Path) -> List[str]:
        """Detect build tools used in the project.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            List of detected build tools
        """
        build_tools = []
        
        # Check for various build tool indicators
        build_indicators = {
            "Makefile": "make",
            "makefile": "make",
            "Dockerfile": "docker",
            "docker-compose.yml": "docker-compose",
            "docker-compose.yaml": "docker-compose",
            "webpack.config.js": "webpack",
            "rollup.config.js": "rollup",
            "vite.config.js": "vite",
            "vite.config.ts": "vite",
            "gulpfile.js": "gulp",
            "Gruntfile.js": "grunt",
            ".github/workflows": "github-actions",
            ".gitlab-ci.yml": "gitlab-ci",
            "Jenkinsfile": "jenkins",
            "tox.ini": "tox",
            ".pre-commit-config.yaml": "pre-commit",
        }
        
        for indicator, tool in build_indicators.items():
            path = project_path / indicator
            if path.exists():
                build_tools.append(tool)
        
        return build_tools