"""Framework detection service for identifying project frameworks and patterns."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set

import tomllib

from dev_agent.models.enums import FrameworkType, LanguageType
from dev_agent.models.language_patterns import FrameworkPatterns

logger = logging.getLogger(__name__)


class FrameworkDetector:
    """Detects frameworks and applies framework-specific patterns.
    
    This class analyzes project dependencies, configuration files, and code
    structure to identify frameworks and provide appropriate patterns for
    code generation and task creation.
    """
    
    # Framework detection patterns based on dependencies
    DEPENDENCY_PATTERNS: Dict[FrameworkType, List[str]] = {
        # Python frameworks
        FrameworkType.FASTAPI: ["fastapi", "uvicorn", "starlette"],
        FrameworkType.DJANGO: ["django", "Django"],
        FrameworkType.FLASK: ["flask", "Flask"],
        FrameworkType.STREAMLIT: ["streamlit"],
        FrameworkType.PYTEST: ["pytest", "pytest-cov"],
        FrameworkType.SQLALCHEMY: ["sqlalchemy", "SQLAlchemy"],
        FrameworkType.CELERY: ["celery", "Celery"],
        FrameworkType.PANDAS: ["pandas"],
        FrameworkType.NUMPY: ["numpy"],
        FrameworkType.TENSORFLOW: ["tensorflow", "tensorflow-gpu"],
        FrameworkType.PYTORCH: ["torch", "pytorch"],
        
        # JavaScript/TypeScript frameworks
        FrameworkType.REACT: ["react", "@types/react", "react-dom"],
        FrameworkType.VUE: ["vue", "@vue/cli", "vuejs"],
        FrameworkType.ANGULAR: ["@angular/core", "@angular/cli", "angular"],
        FrameworkType.EXPRESS: ["express", "@types/express"],
        FrameworkType.NODEJS: ["node", "nodejs"],
        FrameworkType.NESTJS: ["@nestjs/core", "@nestjs/common"],
        FrameworkType.WEBPACK: ["webpack", "webpack-cli"],
        FrameworkType.BABEL: ["@babel/core", "@babel/preset-env"],
        FrameworkType.JEST: ["jest", "@types/jest"],
        FrameworkType.ESLINT: ["eslint", "@typescript-eslint/parser"],
        
        # Java frameworks
        FrameworkType.SPRING_BOOT: ["spring-boot-starter", "org.springframework.boot"],
        FrameworkType.SPRING: ["springframework", "org.springframework"],
        FrameworkType.HIBERNATE: ["hibernate-core", "org.hibernate"],
        FrameworkType.JUNIT: ["junit", "org.junit"],
        FrameworkType.MAVEN: ["maven"],
        FrameworkType.GRADLE: ["gradle"],
        
        # Web frameworks
        FrameworkType.BOOTSTRAP: ["bootstrap", "@types/bootstrap"],
        FrameworkType.TAILWIND: ["tailwindcss", "@tailwindcss/forms"],
        FrameworkType.JQUERY: ["jquery", "@types/jquery"],
        FrameworkType.SASS: ["sass", "node-sass"],
    }
    
    # File patterns that indicate specific frameworks
    FILE_PATTERNS: Dict[FrameworkType, List[str]] = {
        FrameworkType.FASTAPI: ["main.py", "app.py", "api.py"],
        FrameworkType.DJANGO: ["manage.py", "settings.py", "wsgi.py", "asgi.py"],
        FrameworkType.FLASK: ["app.py", "run.py", "wsgi.py"],
        FrameworkType.STREAMLIT: ["main.py", "app.py", "streamlit_app.py"],
        FrameworkType.REACT: ["App.jsx", "App.tsx", "index.jsx", "index.tsx"],
        FrameworkType.VUE: ["App.vue", "main.js", "vue.config.js"],
        FrameworkType.ANGULAR: ["angular.json", "app.module.ts", "main.ts"],
        FrameworkType.EXPRESS: ["server.js", "app.js", "index.js"],
        FrameworkType.NESTJS: ["main.ts", "app.module.ts", "nest-cli.json"],
        FrameworkType.SPRING_BOOT: ["Application.java", "pom.xml", "application.properties"],
        FrameworkType.WEBPACK: ["webpack.config.js", "webpack.config.ts"],
        FrameworkType.JEST: ["jest.config.js", "jest.config.ts"],
    }
    
    # Configuration file patterns
    CONFIG_PATTERNS: Dict[FrameworkType, List[str]] = {
        FrameworkType.REACT: ["package.json", "tsconfig.json", ".eslintrc"],
        FrameworkType.VUE: ["vue.config.js", "package.json"],
        FrameworkType.ANGULAR: ["angular.json", "tsconfig.json", "package.json"],
        FrameworkType.NESTJS: ["nest-cli.json", "tsconfig.json", "package.json"],
        FrameworkType.DJANGO: ["settings.py", "requirements.txt", "pyproject.toml"],
        FrameworkType.FASTAPI: ["pyproject.toml", "requirements.txt"],
        FrameworkType.FLASK: ["config.py", "requirements.txt", "pyproject.toml"],
        FrameworkType.STREAMLIT: ["pyproject.toml", "requirements.txt", ".streamlit/config.toml"],
        FrameworkType.SPRING_BOOT: ["application.properties", "application.yml", "pom.xml"],
        FrameworkType.WEBPACK: ["webpack.config.js", "package.json"],
        FrameworkType.JEST: ["jest.config.js", "package.json"],
        FrameworkType.ESLINT: [".eslintrc.js", ".eslintrc.json", "package.json"],
    }
    
    # Predefined framework patterns
    FRAMEWORK_PATTERNS: Dict[FrameworkType, FrameworkPatterns] = {
        FrameworkType.FASTAPI: FrameworkPatterns(
            framework=FrameworkType.FASTAPI,
            preferred_structure={
                "root": ["app", "tests", "docs", "scripts"],
                "app": ["api", "core", "models", "services", "utils"],
                "api": ["v1", "dependencies.py", "errors.py"],
                "core": ["config.py", "security.py", "database.py"],
                "tests": ["unit", "integration", "conftest.py"],
            },
            entry_point_files=["main.py", "app.py", "run.py"],
            config_file_patterns=["pyproject.toml", "requirements.txt", ".env"],
            component_suffix=None,
            service_patterns=["*_service.py", "services/*.py"],
            common_dependencies=[
                "fastapi", "uvicorn", "pydantic", "python-multipart",
                "python-jose", "passlib", "sqlalchemy", "alembic"
            ],
            import_patterns={
                "fastapi": "from fastapi import FastAPI, Depends, HTTPException",
                "pydantic": "from pydantic import BaseModel, Field",
                "sqlalchemy": "from sqlalchemy import Column, Integer, String",
            },
            test_file_patterns=["test_*.py", "*_test.py"],
            test_directory_structure="tests/",
        ),
        
        FrameworkType.DJANGO: FrameworkPatterns(
            framework=FrameworkType.DJANGO,
            preferred_structure={
                "root": ["manage.py", "requirements.txt", "static", "media", "templates"],
                "project": ["settings.py", "urls.py", "wsgi.py", "asgi.py"],
                "apps": ["models.py", "views.py", "urls.py", "admin.py", "apps.py"],
                "tests": ["test_models.py", "test_views.py", "test_forms.py"],
            },
            entry_point_files=["manage.py", "wsgi.py", "asgi.py"],
            config_file_patterns=["settings.py", "requirements.txt", "pyproject.toml"],
            component_suffix=None,
            service_patterns=["services.py", "services/*.py"],
            common_dependencies=[
                "django", "djangorestframework", "django-cors-headers",
                "celery", "redis", "psycopg2-binary", "pillow"
            ],
            import_patterns={
                "django": "from django.db import models",
                "rest_framework": "from rest_framework import serializers, viewsets",
                "django_views": "from django.views.generic import ListView, DetailView",
            },
            test_file_patterns=["test_*.py", "tests.py"],
            test_directory_structure="tests/",
        ),
        
        FrameworkType.FLASK: FrameworkPatterns(
            framework=FrameworkType.FLASK,
            preferred_structure={
                "root": ["app.py", "run.py", "config.py", "requirements.txt"],
                "app": ["__init__.py", "models.py", "views.py", "forms.py"],
                "templates": ["base.html", "index.html"],
                "static": ["css", "js", "images"],
                "tests": ["test_app.py", "test_models.py"],
            },
            entry_point_files=["app.py", "run.py", "wsgi.py"],
            config_file_patterns=["config.py", "requirements.txt", ".env"],
            component_suffix=None,
            service_patterns=["services.py", "services/*.py"],
            common_dependencies=[
                "flask", "flask-sqlalchemy", "flask-migrate", "flask-login",
                "flask-wtf", "flask-cors", "gunicorn"
            ],
            import_patterns={
                "flask": "from flask import Flask, request, jsonify, render_template",
                "sqlalchemy": "from flask_sqlalchemy import SQLAlchemy",
                "wtf": "from flask_wtf import FlaskForm",
            },
            test_file_patterns=["test_*.py", "*_test.py"],
            test_directory_structure="tests/",
        ),
        
        FrameworkType.STREAMLIT: FrameworkPatterns(
            framework=FrameworkType.STREAMLIT,
            preferred_structure={
                "root": ["main.py", "requirements.txt", "pages", "utils", ".streamlit"],
                "pages": ["1_About.py", "2_Contact.py"],
                "utils": ["helpers.py", "data_processing.py"],
                ".streamlit": ["config.toml", "secrets.toml"],
                "tests": ["test_app.py", "test_pages.py"],
            },
            entry_point_files=["main.py", "app.py", "streamlit_app.py"],
            config_file_patterns=[".streamlit/config.toml", "requirements.txt", "pyproject.toml"],
            component_suffix=None,
            service_patterns=["utils/*.py", "helpers/*.py"],
            common_dependencies=[
                "streamlit", "pandas", "numpy", "plotly", "altair",
                "matplotlib", "seaborn", "requests", "pillow"
            ],
            import_patterns={
                "streamlit": "import streamlit as st",
                "pandas": "import pandas as pd",
                "plotly": "import plotly.express as px",
            },
            test_file_patterns=["test_*.py", "*_test.py"],
            test_directory_structure="tests/",
        ),
        
        FrameworkType.REACT: FrameworkPatterns(
            framework=FrameworkType.REACT,
            preferred_structure={
                "root": ["src", "public", "package.json", "README.md"],
                "src": ["components", "pages", "hooks", "utils", "services", "types"],
                "components": ["common", "ui"],
                "public": ["index.html", "favicon.ico"],
                "tests": ["__tests__", "*.test.tsx", "*.test.ts"],
            },
            entry_point_files=["index.tsx", "index.jsx", "App.tsx", "App.jsx"],
            config_file_patterns=["package.json", "tsconfig.json", ".eslintrc.json"],
            component_suffix="Component",
            service_patterns=["*Service.ts", "services/*.ts"],
            common_dependencies=[
                "react", "react-dom", "@types/react", "@types/react-dom",
                "typescript", "react-router-dom", "axios", "styled-components"
            ],
            import_patterns={
                "react": "import React from 'react'",
                "component": "import { FC } from 'react'",
                "router": "import { BrowserRouter, Route, Routes } from 'react-router-dom'",
            },
            test_file_patterns=["*.test.tsx", "*.test.ts", "*.spec.tsx"],
            test_directory_structure="src/__tests__/",
        ),
        
        FrameworkType.EXPRESS: FrameworkPatterns(
            framework=FrameworkType.EXPRESS,
            preferred_structure={
                "root": ["src", "package.json", "tsconfig.json"],
                "src": ["routes", "controllers", "middleware", "models", "services", "utils"],
                "routes": ["index.ts", "api.ts"],
                "controllers": ["*.controller.ts"],
                "tests": ["__tests__", "*.test.ts"],
            },
            entry_point_files=["server.ts", "app.ts", "index.ts"],
            config_file_patterns=["package.json", "tsconfig.json", ".env"],
            component_suffix=None,
            service_patterns=["*.service.ts", "services/*.ts"],
            common_dependencies=[
                "express", "@types/express", "cors", "helmet", "morgan",
                "dotenv", "joi", "bcryptjs", "jsonwebtoken"
            ],
            import_patterns={
                "express": "import express from 'express'",
                "middleware": "import { Request, Response, NextFunction } from 'express'",
                "cors": "import cors from 'cors'",
            },
            test_file_patterns=["*.test.ts", "*.spec.ts"],
            test_directory_structure="src/__tests__/",
        ),
    }
    
    def __init__(self):
        """Initialize the framework detector."""
        self._cache: Dict[str, List[FrameworkType]] = {}
    
    def detect_frameworks(self, project_path: Path, language: LanguageType) -> List[FrameworkType]:
        """Detect frameworks used in a project.
        
        Args:
            project_path: Path to the project directory
            language: Primary language of the project
            
        Returns:
            List of detected frameworks
            
        Raises:
            ValueError: If project path is invalid
        """
        if not project_path.exists() or not project_path.is_dir():
            raise ValueError(f"Project path does not exist or is not a directory: {project_path}")
        
        project_key = f"{project_path.resolve()}:{language.value}"
        
        # Check cache first
        if project_key in self._cache:
            return self._cache[project_key]
        
        detected_frameworks = []
        
        # Detect from dependencies
        dependency_frameworks = self._detect_from_dependencies(project_path, language)
        detected_frameworks.extend(dependency_frameworks)
        
        # Detect from file patterns
        file_frameworks = self._detect_from_files(project_path, language)
        detected_frameworks.extend(file_frameworks)
        
        # Detect from configuration files
        config_frameworks = self._detect_from_config(project_path, language)
        detected_frameworks.extend(config_frameworks)
        
        # Remove duplicates and filter by language compatibility
        unique_frameworks = list(set(detected_frameworks))
        compatible_frameworks = self._filter_by_language_compatibility(unique_frameworks, language)
        
        # Cache the result
        self._cache[project_key] = compatible_frameworks
        
        logger.info(f"Detected frameworks for {language.value}: {[f.value for f in compatible_frameworks]}")
        
        return compatible_frameworks
    
    def get_framework_patterns(self, framework: FrameworkType) -> FrameworkPatterns:
        """Get framework-specific patterns.
        
        Args:
            framework: The framework to get patterns for
            
        Returns:
            Framework patterns for the specified framework
            
        Raises:
            ValueError: If framework patterns are not available
        """
        if framework not in self.FRAMEWORK_PATTERNS:
            raise ValueError(f"No patterns available for framework: {framework.value}")
        
        return self.FRAMEWORK_PATTERNS[framework]
    
    def get_directory_structure(self, framework: FrameworkType) -> Dict[str, List[str]]:
        """Get recommended directory structure for a framework.
        
        Args:
            framework: The framework to get directory structure for
            
        Returns:
            Dictionary mapping directory names to their contents
            
        Raises:
            ValueError: If framework is not supported
        """
        patterns = self.get_framework_patterns(framework)
        return patterns.preferred_structure
    
    def analyze_existing_structure(self, project_path: Path, frameworks: List[FrameworkType]) -> Dict[str, any]:
        """Analyze existing project structure against framework conventions.
        
        Args:
            project_path: Path to the project directory
            frameworks: List of detected frameworks
            
        Returns:
            Analysis results including compliance and recommendations
        """
        analysis = {
            "compliant_frameworks": [],
            "non_compliant_frameworks": [],
            "missing_directories": [],
            "unexpected_files": [],
            "recommendations": [],
        }
        
        for framework in frameworks:
            try:
                patterns = self.get_framework_patterns(framework)
                compliance = self._check_structure_compliance(project_path, patterns)
                
                if compliance["is_compliant"]:
                    analysis["compliant_frameworks"].append(framework)
                else:
                    analysis["non_compliant_frameworks"].append(framework)
                    analysis["missing_directories"].extend(compliance["missing_directories"])
                    analysis["recommendations"].extend(compliance["recommendations"])
                    
            except ValueError:
                logger.warning(f"No patterns available for framework: {framework.value}")
        
        return analysis
    
    def _detect_from_dependencies(self, project_path: Path, language: LanguageType) -> List[FrameworkType]:
        """Detect frameworks from project dependencies.
        
        Args:
            project_path: Path to the project directory
            language: Primary language of the project
            
        Returns:
            List of frameworks detected from dependencies
        """
        detected = []
        
        if language == LanguageType.PYTHON:
            detected.extend(self._detect_python_dependencies(project_path))
        elif language in [LanguageType.JAVASCRIPT, LanguageType.TYPESCRIPT]:
            detected.extend(self._detect_js_dependencies(project_path))
        elif language == LanguageType.JAVA:
            detected.extend(self._detect_java_dependencies(project_path))
        
        return detected
    
    def _detect_python_dependencies(self, project_path: Path) -> List[FrameworkType]:
        """Detect Python frameworks from dependencies.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            List of detected Python frameworks
        """
        detected = []
        dependencies = set()
        
        # Check pyproject.toml
        pyproject_file = project_path / "pyproject.toml"
        if pyproject_file.exists():
            try:
                with open(pyproject_file, "rb") as f:
                    pyproject_data = tomllib.load(f)
                    
                # Get dependencies from different sections
                if "project" in pyproject_data and "dependencies" in pyproject_data["project"]:
                    dependencies.update(pyproject_data["project"]["dependencies"])
                
                if "tool" in pyproject_data and "poetry" in pyproject_data["tool"]:
                    poetry_deps = pyproject_data["tool"]["poetry"].get("dependencies", {})
                    dependencies.update(poetry_deps.keys())
                    
            except Exception as e:
                logger.debug(f"Error reading pyproject.toml: {e}")
        
        # Check requirements.txt
        requirements_file = project_path / "requirements.txt"
        if requirements_file.exists():
            try:
                with open(requirements_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            # Extract package name (before version specifiers)
                            package_name = line.split("==")[0].split(">=")[0].split("<=")[0].split("~=")[0].strip()
                            dependencies.add(package_name)
            except Exception as e:
                logger.debug(f"Error reading requirements.txt: {e}")
        
        # Match dependencies to frameworks
        for framework, patterns in self.DEPENDENCY_PATTERNS.items():
            if any(dep in dependencies for dep in patterns):
                detected.append(framework)
        
        return detected
    
    def _detect_js_dependencies(self, project_path: Path) -> List[FrameworkType]:
        """Detect JavaScript/TypeScript frameworks from dependencies.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            List of detected JS/TS frameworks
        """
        detected = []
        dependencies = set()
        
        # Check package.json
        package_file = project_path / "package.json"
        if package_file.exists():
            try:
                with open(package_file, "r") as f:
                    package_data = json.load(f)
                    
                # Get dependencies from different sections
                for dep_section in ["dependencies", "devDependencies", "peerDependencies"]:
                    if dep_section in package_data:
                        dependencies.update(package_data[dep_section].keys())
                        
            except Exception as e:
                logger.debug(f"Error reading package.json: {e}")
        
        # Match dependencies to frameworks
        for framework, patterns in self.DEPENDENCY_PATTERNS.items():
            if any(dep in dependencies for dep in patterns):
                detected.append(framework)
        
        return detected
    
    def _detect_java_dependencies(self, project_path: Path) -> List[FrameworkType]:
        """Detect Java frameworks from dependencies.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            List of detected Java frameworks
        """
        detected = []
        
        # Check pom.xml (Maven)
        pom_file = project_path / "pom.xml"
        if pom_file.exists():
            try:
                with open(pom_file, "r") as f:
                    content = f.read()
                    
                # Simple string matching for common frameworks
                for framework, patterns in self.DEPENDENCY_PATTERNS.items():
                    if any(pattern in content for pattern in patterns):
                        detected.append(framework)
                        
            except Exception as e:
                logger.debug(f"Error reading pom.xml: {e}")
        
        # Check build.gradle (Gradle)
        gradle_files = [project_path / "build.gradle", project_path / "build.gradle.kts"]
        for gradle_file in gradle_files:
            if gradle_file.exists():
                try:
                    with open(gradle_file, "r") as f:
                        content = f.read()
                        
                    # Simple string matching for common frameworks
                    for framework, patterns in self.DEPENDENCY_PATTERNS.items():
                        if any(pattern in content for pattern in patterns):
                            detected.append(framework)
                            
                except Exception as e:
                    logger.debug(f"Error reading {gradle_file.name}: {e}")
        
        return detected
    
    def _detect_from_files(self, project_path: Path, language: LanguageType) -> List[FrameworkType]:
        """Detect frameworks from file patterns.
        
        Args:
            project_path: Path to the project directory
            language: Primary language of the project
            
        Returns:
            List of frameworks detected from file patterns
        """
        detected = []
        
        # Get all files in the project (excluding common ignore directories)
        exclude_dirs = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", "dist", "build"}
        project_files = set()
        
        for file_path in project_path.rglob("*"):
            if file_path.is_file() and not any(part in exclude_dirs for part in file_path.parts):
                relative_path = file_path.relative_to(project_path)
                project_files.add(str(relative_path))
                project_files.add(file_path.name)
        
        # Match file patterns to frameworks
        for framework, patterns in self.FILE_PATTERNS.items():
            if any(pattern in project_files for pattern in patterns):
                detected.append(framework)
        
        return detected
    
    def _detect_from_config(self, project_path: Path, language: LanguageType) -> List[FrameworkType]:
        """Detect frameworks from configuration files.
        
        Args:
            project_path: Path to the project directory
            language: Primary language of the project
            
        Returns:
            List of frameworks detected from configuration files
        """
        detected = []
        
        # Get all config files in the project
        config_files = set()
        for file_path in project_path.rglob("*"):
            if file_path.is_file():
                config_files.add(file_path.name)
        
        # Match config patterns to frameworks
        for framework, patterns in self.CONFIG_PATTERNS.items():
            if any(pattern in config_files for pattern in patterns):
                detected.append(framework)
        
        return detected
    
    def _filter_by_language_compatibility(self, frameworks: List[FrameworkType], language: LanguageType) -> List[FrameworkType]:
        """Filter frameworks by language compatibility.
        
        Args:
            frameworks: List of detected frameworks
            language: Primary language of the project
            
        Returns:
            List of frameworks compatible with the language
        """
        # Define language compatibility
        language_compatibility = {
            LanguageType.PYTHON: [
                FrameworkType.DJANGO, FrameworkType.FLASK, FrameworkType.FASTAPI,
                FrameworkType.STREAMLIT, FrameworkType.PYTEST, FrameworkType.SQLALCHEMY, 
                FrameworkType.CELERY, FrameworkType.PANDAS, FrameworkType.NUMPY, 
                FrameworkType.TENSORFLOW, FrameworkType.PYTORCH,
            ],
            LanguageType.JAVASCRIPT: [
                FrameworkType.REACT, FrameworkType.VUE, FrameworkType.ANGULAR,
                FrameworkType.EXPRESS, FrameworkType.NODEJS, FrameworkType.WEBPACK,
                FrameworkType.BABEL, FrameworkType.JEST, FrameworkType.ESLINT,
                FrameworkType.BOOTSTRAP, FrameworkType.TAILWIND, FrameworkType.JQUERY,
                FrameworkType.SASS,
            ],
            LanguageType.TYPESCRIPT: [
                FrameworkType.REACT, FrameworkType.VUE, FrameworkType.ANGULAR,
                FrameworkType.EXPRESS, FrameworkType.NODEJS, FrameworkType.NESTJS,
                FrameworkType.WEBPACK, FrameworkType.BABEL, FrameworkType.JEST,
                FrameworkType.ESLINT, FrameworkType.BOOTSTRAP, FrameworkType.TAILWIND,
                FrameworkType.JQUERY, FrameworkType.SASS,
            ],
            LanguageType.JAVA: [
                FrameworkType.SPRING_BOOT, FrameworkType.SPRING, FrameworkType.HIBERNATE,
                FrameworkType.JUNIT, FrameworkType.MAVEN, FrameworkType.GRADLE,
            ],
        }
        
        compatible = language_compatibility.get(language, [])
        return [f for f in frameworks if f in compatible]
    
    def _check_structure_compliance(self, project_path: Path, patterns: FrameworkPatterns) -> Dict[str, any]:
        """Check if project structure complies with framework patterns.
        
        Args:
            project_path: Path to the project directory
            patterns: Framework patterns to check against
            
        Returns:
            Compliance analysis results
        """
        compliance = {
            "is_compliant": True,
            "missing_directories": [],
            "recommendations": [],
        }
        
        # Check for expected directories
        for parent_dir, expected_contents in patterns.preferred_structure.items():
            if parent_dir == "root":
                base_path = project_path
            else:
                base_path = project_path / parent_dir
            
            for expected_item in expected_contents:
                expected_path = base_path / expected_item
                if not expected_path.exists():
                    compliance["is_compliant"] = False
                    compliance["missing_directories"].append(str(expected_path.relative_to(project_path)))
                    compliance["recommendations"].append(
                        f"Consider creating {expected_item} in {parent_dir} directory"
                    )
        
        return compliance