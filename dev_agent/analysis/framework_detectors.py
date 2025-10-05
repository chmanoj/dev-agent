"""Framework detection and analysis components."""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ..models.analysis import FrameworkInfo, Improvement, UsagePattern
from ..models.enums import FrameworkType, LanguageType


class FrameworkDetector(ABC):
    """Base class for framework detection and analysis."""

    @abstractmethod
    def detect_frameworks(self, project_path: Path, files: list[Path]) -> list[FrameworkType]:
        """Detect frameworks in the given files.

        Args:
            project_path: Path to the project root
            files: List of files to analyze

        Returns:
            List of detected frameworks
        """
        pass

    @abstractmethod
    def analyze_usage(self, project_path: Path) -> FrameworkInfo | None:
        """Analyze framework usage in the project.

        Args:
            project_path: Path to the project root

        Returns:
            FrameworkInfo object or None if framework not found
        """
        pass


class PythonFrameworkDetector(FrameworkDetector):
    """Detector for Python frameworks."""

    def detect_frameworks(self, project_path: Path, files: list[Path]) -> list[FrameworkType]:
        """Detect Python frameworks."""
        frameworks = []
        
        # Check dependencies
        dependencies = self._get_python_dependencies(project_path)
        
        # Framework detection patterns
        framework_patterns = {
            FrameworkType.DJANGO: ["django"],
            FrameworkType.FLASK: ["flask"],
            FrameworkType.FASTAPI: ["fastapi"],
            FrameworkType.PYTEST: ["pytest"],
            FrameworkType.SQLALCHEMY: ["sqlalchemy"],
            FrameworkType.CELERY: ["celery"],
            FrameworkType.PANDAS: ["pandas"],
            FrameworkType.NUMPY: ["numpy"],
            FrameworkType.TENSORFLOW: ["tensorflow"],
            FrameworkType.PYTORCH: ["torch", "pytorch"],
        }
        
        for framework, patterns in framework_patterns.items():
            if any(pattern in dep.lower() for dep in dependencies for pattern in patterns):
                frameworks.append(framework)
        
        # Check import statements in files
        for file_path in files[:20]:  # Limit to avoid performance issues
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                
                for framework, patterns in framework_patterns.items():
                    if framework not in frameworks:
                        for pattern in patterns:
                            if re.search(rf'\bimport\s+{pattern}\b|\bfrom\s+{pattern}\b', content):
                                frameworks.append(framework)
                                break
            except Exception:
                continue
        
        return frameworks

    def analyze_usage(self, project_path: Path) -> FrameworkInfo | None:
        """Analyze Python framework usage (generic implementation)."""
        # This is a generic implementation - specific frameworks would override this
        return None

    def _get_python_dependencies(self, project_path: Path) -> list[str]:
        """Get Python dependencies from various sources."""
        dependencies = []
        
        # Check pyproject.toml
        pyproject_path = project_path / "pyproject.toml"
        if pyproject_path.exists():
            try:
                with open(pyproject_path, encoding="utf-8") as f:
                    content = f.read()
                # Simple extraction - could be enhanced with proper TOML parsing
                deps = re.findall(r'"([^"]+)"', content)
                dependencies.extend(deps)
            except Exception:
                pass
        
        # Check requirements.txt
        req_path = project_path / "requirements.txt"
        if req_path.exists():
            try:
                with open(req_path, encoding="utf-8") as f:
                    dependencies.extend(f.read().splitlines())
            except Exception:
                pass
        
        # Check setup.py
        setup_path = project_path / "setup.py"
        if setup_path.exists():
            try:
                with open(setup_path, encoding="utf-8") as f:
                    content = f.read()
                # Extract from install_requires
                matches = re.findall(r'install_requires\s*=\s*\[(.*?)\]', content, re.DOTALL)
                for match in matches:
                    deps = re.findall(r'["\']([^"\']+)["\']', match)
                    dependencies.extend(deps)
            except Exception:
                pass
        
        return dependencies


class JavaScriptFrameworkDetector(FrameworkDetector):
    """Detector for JavaScript/TypeScript frameworks."""

    def detect_frameworks(self, project_path: Path, files: list[Path]) -> list[FrameworkType]:
        """Detect JavaScript/TypeScript frameworks."""
        frameworks = []
        
        # Check package.json
        package_json_path = project_path / "package.json"
        if package_json_path.exists():
            try:
                with open(package_json_path, encoding="utf-8") as f:
                    package_data = json.loads(f.read())
                
                all_deps = {}
                all_deps.update(package_data.get("dependencies", {}))
                all_deps.update(package_data.get("devDependencies", {}))
                
                # Framework detection patterns
                framework_patterns = {
                    FrameworkType.REACT: ["react"],
                    FrameworkType.VUE: ["vue"],
                    FrameworkType.ANGULAR: ["@angular/core", "angular"],
                    FrameworkType.EXPRESS: ["express"],
                    FrameworkType.NODEJS: ["node"],
                    FrameworkType.WEBPACK: ["webpack"],
                    FrameworkType.BABEL: ["@babel/core", "babel"],
                    FrameworkType.JEST: ["jest"],
                    FrameworkType.ESLINT: ["eslint"],
                    FrameworkType.NESTJS: ["@nestjs/core"],
                }
                
                for framework, patterns in framework_patterns.items():
                    if any(pattern in dep for dep in all_deps.keys() for pattern in patterns):
                        frameworks.append(framework)
                        
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        # Check import statements in files
        for file_path in files[:20]:  # Limit to avoid performance issues
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                
                # Look for framework imports
                if "import React" in content or "from 'react'" in content:
                    if FrameworkType.REACT not in frameworks:
                        frameworks.append(FrameworkType.REACT)
                
                if "import Vue" in content or "from 'vue'" in content:
                    if FrameworkType.VUE not in frameworks:
                        frameworks.append(FrameworkType.VUE)
                
                if "from '@angular/" in content:
                    if FrameworkType.ANGULAR not in frameworks:
                        frameworks.append(FrameworkType.ANGULAR)
                
                if "import express" in content or "require('express')" in content:
                    if FrameworkType.EXPRESS not in frameworks:
                        frameworks.append(FrameworkType.EXPRESS)
                        
            except Exception:
                continue
        
        return frameworks

    def analyze_usage(self, project_path: Path) -> FrameworkInfo | None:
        """Analyze JavaScript framework usage (generic implementation)."""
        # This is a generic implementation - specific frameworks would override this
        return None


class JavaFrameworkDetector(FrameworkDetector):
    """Detector for Java frameworks."""

    def detect_frameworks(self, project_path: Path, files: list[Path]) -> list[FrameworkType]:
        """Detect Java frameworks."""
        frameworks = []
        
        # Check pom.xml for Maven projects
        pom_path = project_path / "pom.xml"
        if pom_path.exists():
            # Presence of pom.xml indicates Maven project
            frameworks.append(FrameworkType.MAVEN)
            
            try:
                with open(pom_path, encoding="utf-8") as f:
                    content = f.read()
                
                framework_patterns = {
                    FrameworkType.SPRING_BOOT: ["spring-boot"],
                    FrameworkType.SPRING: ["springframework"],
                    FrameworkType.HIBERNATE: ["hibernate"],
                    FrameworkType.JUNIT: ["junit"],
                }
                
                for framework, patterns in framework_patterns.items():
                    if any(pattern in content for pattern in patterns):
                        frameworks.append(framework)
                        
            except Exception:
                pass
        
        # Check build.gradle for Gradle projects
        gradle_path = project_path / "build.gradle"
        if gradle_path.exists():
            try:
                with open(gradle_path, encoding="utf-8") as f:
                    content = f.read()
                
                if "gradle" not in [f.value for f in frameworks]:
                    frameworks.append(FrameworkType.GRADLE)
                
                # Check for other frameworks in Gradle dependencies
                if "spring-boot" in content:
                    frameworks.append(FrameworkType.SPRING_BOOT)
                if "springframework" in content:
                    frameworks.append(FrameworkType.SPRING)
                if "hibernate" in content:
                    frameworks.append(FrameworkType.HIBERNATE)
                if "junit" in content:
                    frameworks.append(FrameworkType.JUNIT)
                    
            except Exception:
                pass
        
        # Check import statements in Java files
        for file_path in files[:20]:  # Limit to avoid performance issues
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                
                if "import org.springframework" in content:
                    if FrameworkType.SPRING not in frameworks:
                        frameworks.append(FrameworkType.SPRING)
                
                if "import org.hibernate" in content:
                    if FrameworkType.HIBERNATE not in frameworks:
                        frameworks.append(FrameworkType.HIBERNATE)
                
                if "import org.junit" in content:
                    if FrameworkType.JUNIT not in frameworks:
                        frameworks.append(FrameworkType.JUNIT)
                        
            except Exception:
                continue
        
        return frameworks

    def analyze_usage(self, project_path: Path) -> FrameworkInfo | None:
        """Analyze Java framework usage (generic implementation)."""
        # This is a generic implementation - specific frameworks would override this
        return None


class WebFrameworkDetector(FrameworkDetector):
    """Detector for web frameworks and libraries."""

    def detect_frameworks(self, project_path: Path, files: list[Path]) -> list[FrameworkType]:
        """Detect web frameworks."""
        frameworks = []
        
        # Check package.json for web frameworks
        package_json_path = project_path / "package.json"
        if package_json_path.exists():
            try:
                with open(package_json_path, encoding="utf-8") as f:
                    package_data = json.loads(f.read())
                
                all_deps = {}
                all_deps.update(package_data.get("dependencies", {}))
                all_deps.update(package_data.get("devDependencies", {}))
                
                framework_patterns = {
                    FrameworkType.BOOTSTRAP: ["bootstrap"],
                    FrameworkType.TAILWIND: ["tailwindcss"],
                    FrameworkType.JQUERY: ["jquery"],
                    FrameworkType.SASS: ["sass", "node-sass"],
                }
                
                for framework, patterns in framework_patterns.items():
                    if any(pattern in dep for dep in all_deps.keys() for pattern in patterns):
                        frameworks.append(framework)
                        
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        # Check HTML and CSS files for framework usage
        html_files = [f for f in files if f.suffix.lower() in [".html", ".htm"]]
        css_files = [f for f in files if f.suffix.lower() in [".css", ".scss", ".sass"]]
        
        for file_path in html_files + css_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                
                # Check for Bootstrap
                if "bootstrap" in content.lower():
                    if FrameworkType.BOOTSTRAP not in frameworks:
                        frameworks.append(FrameworkType.BOOTSTRAP)
                
                # Check for Tailwind
                if "tailwind" in content.lower() or "tw-" in content:
                    if FrameworkType.TAILWIND not in frameworks:
                        frameworks.append(FrameworkType.TAILWIND)
                
                # Check for jQuery
                if "jquery" in content.lower() or "$(document)" in content:
                    if FrameworkType.JQUERY not in frameworks:
                        frameworks.append(FrameworkType.JQUERY)
                        
            except Exception:
                continue
        
        return frameworks

    def analyze_usage(self, project_path: Path) -> FrameworkInfo | None:
        """Analyze web framework usage (generic implementation)."""
        # This is a generic implementation - specific frameworks would override this
        return None


class ReactFrameworkDetector(FrameworkDetector):
    """Specific detector for React framework."""

    def detect_frameworks(self, project_path: Path, files: list[Path]) -> list[FrameworkType]:
        """Detect React framework."""
        # This would be called by JavaScriptFrameworkDetector
        return []

    def analyze_usage(self, project_path: Path) -> FrameworkInfo | None:
        """Analyze React usage in detail."""
        package_json_path = project_path / "package.json"
        if not package_json_path.exists():
            return None
        
        try:
            with open(package_json_path, encoding="utf-8") as f:
                package_data = json.loads(f.read())
            
            all_deps = {}
            all_deps.update(package_data.get("dependencies", {}))
            all_deps.update(package_data.get("devDependencies", {}))
            
            if "react" not in all_deps:
                return None
            
            version = all_deps["react"]
            
            # Analyze usage patterns
            usage_patterns = self._analyze_react_patterns(project_path)
            
            # Find configuration files
            config_files = []
            for config_file in ["package.json", "webpack.config.js", ".babelrc", "tsconfig.json"]:
                if (project_path / config_file).exists():
                    config_files.append(config_file)
            
            # Calculate best practices compliance
            compliance = self._calculate_react_compliance(project_path)
            
            # Generate improvement suggestions
            improvements = self._suggest_react_improvements(project_path, compliance)
            
            return FrameworkInfo(
                name="React",
                version=version,
                usage_patterns=usage_patterns,
                configuration_files=config_files,
                best_practices_compliance=compliance,
                suggested_improvements=improvements,
            )
            
        except (json.JSONDecodeError, FileNotFoundError):
            return None

    def _analyze_react_patterns(self, project_path: Path) -> list[UsagePattern]:
        """Analyze React usage patterns."""
        patterns = []
        
        # Find React component files
        react_files = []
        for file_path in project_path.rglob("*.jsx"):
            react_files.append(file_path)
        for file_path in project_path.rglob("*.tsx"):
            react_files.append(file_path)
        for file_path in project_path.rglob("*.js"):
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                if "import React" in content or "from 'react'" in content:
                    react_files.append(file_path)
            except Exception:
                continue
        
        # Analyze component patterns
        functional_components = 0
        class_components = 0
        hooks_usage = 0
        
        for file_path in react_files[:20]:  # Limit analysis
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                
                # Count functional vs class components
                # Match arrow functions: const Component = () => {}
                if re.search(r'const\s+\w+\s*=\s*\([^)]*\)\s*=>', content):
                    functional_components += 1
                # Match function declarations: function Component() {}
                elif re.search(r'function\s+[A-Z]\w*\s*\([^)]*\)\s*\{', content):
                    functional_components += 1
                # Match class components
                if re.search(r'class\s+\w+\s+extends\s+React\.Component', content):
                    class_components += 1
                
                # Count hooks usage
                hooks_usage += len(re.findall(r'use\w+\(', content))
                
            except Exception:
                continue
        
        if functional_components > 0:
            patterns.append(UsagePattern(
                pattern="Functional Components",
                file_path="Multiple files",
                occurrences=functional_components,
                examples=[f"Found {functional_components} functional components"],
            ))
        
        if class_components > 0:
            patterns.append(UsagePattern(
                pattern="Class Components",
                file_path="Multiple files",
                occurrences=class_components,
                examples=[f"Found {class_components} class components"],
            ))
        
        if hooks_usage > 0:
            patterns.append(UsagePattern(
                pattern="React Hooks",
                file_path="Multiple files",
                occurrences=hooks_usage,
                examples=[f"Found {hooks_usage} hook usages"],
            ))
        
        return patterns

    def _calculate_react_compliance(self, project_path: Path) -> float:
        """Calculate React best practices compliance."""
        score = 0.0
        total_checks = 0
        
        # Check for TypeScript usage
        total_checks += 1
        if (project_path / "tsconfig.json").exists():
            score += 0.2
        
        # Check for ESLint configuration
        total_checks += 1
        eslint_configs = [".eslintrc.js", ".eslintrc.json", ".eslintrc.yml"]
        if any((project_path / config).exists() for config in eslint_configs):
            score += 0.2
        
        # Check for testing setup
        total_checks += 1
        package_json_path = project_path / "package.json"
        if package_json_path.exists():
            try:
                with open(package_json_path, encoding="utf-8") as f:
                    package_data = json.loads(f.read())
                all_deps = {}
                all_deps.update(package_data.get("dependencies", {}))
                all_deps.update(package_data.get("devDependencies", {}))
                
                if any("test" in dep for dep in all_deps.keys()):
                    score += 0.2
            except Exception:
                pass
        
        # Check for proper project structure
        total_checks += 1
        if (project_path / "src").exists():
            score += 0.2
        
        # Check for component organization
        total_checks += 1
        components_dir = project_path / "src" / "components"
        if components_dir.exists():
            score += 0.2
        
        return score

    def _suggest_react_improvements(self, project_path: Path, compliance: float) -> list[Improvement]:
        """Suggest React improvements."""
        improvements = []
        
        # Always check for TypeScript if not present
        if not (project_path / "tsconfig.json").exists():
            improvements.append(Improvement(
                category="Type Safety",
                description="Consider migrating to TypeScript for better type safety",
                priority="medium",
                effort="high",
            ))
        
        # Other improvements if compliance is not perfect
        if compliance < 1.0:
            eslint_configs = [".eslintrc.js", ".eslintrc.json", ".eslintrc.yml"]
            if not any((project_path / config).exists() for config in eslint_configs):
                improvements.append(Improvement(
                    category="Code Quality",
                    description="Add ESLint configuration for consistent code style",
                    priority="medium",
                    effort="low",
                ))
            
            if not (project_path / "src" / "components").exists():
                improvements.append(Improvement(
                    category="Project Structure",
                    description="Organize components in a dedicated components directory",
                    priority="low",
                    effort="low",
                ))
        
        return improvements


class FrameworkDetectorRegistry:
    """Registry for framework detectors."""

    def __init__(self):
        """Initialize the framework detector registry."""
        self._language_detectors: dict[LanguageType, FrameworkDetector] = {
            LanguageType.PYTHON: PythonFrameworkDetector(),
            LanguageType.JAVASCRIPT: JavaScriptFrameworkDetector(),
            LanguageType.TYPESCRIPT: JavaScriptFrameworkDetector(),
            LanguageType.JAVA: JavaFrameworkDetector(),
            LanguageType.HTML: WebFrameworkDetector(),
            LanguageType.CSS: WebFrameworkDetector(),
        }
        
        self._framework_detectors: dict[FrameworkType, FrameworkDetector] = {
            FrameworkType.REACT: ReactFrameworkDetector(),
            # Add more specific framework detectors here
        }

    def get_detector(self, language: LanguageType) -> FrameworkDetector | None:
        """Get framework detector for a language.

        Args:
            language: The programming language

        Returns:
            FrameworkDetector instance or None
        """
        return self._language_detectors.get(language)

    def get_framework_detector(self, framework: FrameworkType) -> FrameworkDetector | None:
        """Get specific framework detector.

        Args:
            framework: The framework type

        Returns:
            FrameworkDetector instance or None
        """
        return self._framework_detectors.get(framework)

    def register_detector(self, language: LanguageType, detector: FrameworkDetector) -> None:
        """Register a new framework detector for a language.

        Args:
            language: The programming language
            detector: The framework detector instance
        """
        self._language_detectors[language] = detector

    def register_framework_detector(self, framework: FrameworkType, detector: FrameworkDetector) -> None:
        """Register a specific framework detector.

        Args:
            framework: The framework type
            detector: The framework detector instance
        """
        self._framework_detectors[framework] = detector