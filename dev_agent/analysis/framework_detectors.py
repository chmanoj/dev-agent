"""Framework detection for different programming languages."""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ..models.analysis import FrameworkInfo, UsagePattern, Improvement


class FrameworkDetector(ABC):
    """Base class for framework detection."""

    @abstractmethod
    def detect_frameworks(self, files: list[str]) -> list[str]:
        """Detect frameworks used in the given files.

        Args:
            files: List of file paths to analyze

        Returns:
            List of detected framework names
        """

    @abstractmethod
    def analyze_framework(self, framework_name: str, files: list[str]) -> FrameworkInfo | None:
        """Analyze detailed information about a specific framework.

        Args:
            framework_name: Name of the framework to analyze
            files: List of file paths to analyze

        Returns:
            FrameworkInfo object with detailed analysis or None if not found
        """


class PythonFrameworkDetector(FrameworkDetector):
    """Detector for Python frameworks."""

    def __init__(self):
        """Initialize Python framework detector."""
        self.framework_indicators = {
            'django': {
                'imports': ['django', 'django.conf', 'django.urls', 'django.views'],
                'files': ['manage.py', 'settings.py', 'urls.py', 'models.py'],
                'patterns': [r'from django', r'import django', r'DJANGO_SETTINGS_MODULE']
            },
            'flask': {
                'imports': ['flask', 'Flask'],
                'files': ['app.py', 'wsgi.py'],
                'patterns': [r'from flask import', r'Flask\(__name__\)', r'@app\.route']
            },
            'fastapi': {
                'imports': ['fastapi', 'FastAPI'],
                'files': ['main.py', 'app.py'],
                'patterns': [r'from fastapi import', r'FastAPI\(', r'@app\.(get|post|put|delete)']
            },
            'pytest': {
                'imports': ['pytest'],
                'files': ['conftest.py', 'pytest.ini'],
                'patterns': [r'import pytest', r'def test_', r'@pytest\.(fixture|mark)']
            },
            'sqlalchemy': {
                'imports': ['sqlalchemy', 'SQLAlchemy'],
                'files': ['models.py', 'database.py'],
                'patterns': [r'from sqlalchemy', r'declarative_base', r'Column\(']
            },
            'celery': {
                'imports': ['celery', 'Celery'],
                'files': ['celeryconfig.py', 'tasks.py'],
                'patterns': [r'from celery import', r'Celery\(', r'@app\.task']
            },
            'pandas': {
                'imports': ['pandas', 'pd'],
                'files': [],
                'patterns': [r'import pandas', r'pd\.DataFrame', r'pd\.read_']
            },
            'numpy': {
                'imports': ['numpy', 'np'],
                'files': [],
                'patterns': [r'import numpy', r'np\.array', r'np\.']
            },
            'tensorflow': {
                'imports': ['tensorflow', 'tf'],
                'files': [],
                'patterns': [r'import tensorflow', r'tf\.', r'keras']
            },
            'pytorch': {
                'imports': ['torch', 'pytorch'],
                'files': [],
                'patterns': [r'import torch', r'torch\.', r'nn\.Module']
            }
        }

    def detect_frameworks(self, files: list[str]) -> list[str]:
        """Detect Python frameworks."""
        detected = set()
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_name = Path(file_path).name
                
                for framework, indicators in self.framework_indicators.items():
                    # Check file names
                    if file_name in indicators['files']:
                        detected.add(framework)
                        continue
                    
                    # Check import patterns
                    for import_name in indicators['imports']:
                        if re.search(rf'\b{re.escape(import_name)}\b', content):
                            detected.add(framework)
                            break
                    
                    # Check code patterns
                    for pattern in indicators['patterns']:
                        if re.search(pattern, content):
                            detected.add(framework)
                            break
                            
            except (UnicodeDecodeError, IOError):
                continue
        
        return list(detected)

    def analyze_framework(self, framework_name: str, files: list[str]) -> FrameworkInfo | None:
        """Analyze Python framework usage."""
        if framework_name not in self.framework_indicators:
            return None
        
        indicators = self.framework_indicators[framework_name]
        usage_patterns = []
        config_files = []
        version = None
        
        # Analyze usage patterns
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_name = Path(file_path).name
                
                # Check for configuration files
                if file_name in indicators['files']:
                    config_files.append(file_path)
                
                # Analyze patterns
                for pattern in indicators['patterns']:
                    matches = re.findall(pattern, content)
                    if matches:
                        usage_patterns.append(UsagePattern(
                            pattern=pattern,
                            file_path=file_path,
                            occurrences=len(matches),
                            examples=matches[:3]  # First 3 examples
                        ))
                        
            except (UnicodeDecodeError, IOError):
                continue
        
        # Try to detect version from requirements files
        version = self._detect_python_framework_version(framework_name, files)
        
        # Calculate compliance score
        compliance_score = self._calculate_python_compliance(framework_name, usage_patterns)
        
        # Generate improvements
        improvements = self._suggest_python_improvements(framework_name, usage_patterns)
        
        return FrameworkInfo(
            name=framework_name,
            version=version or 'unknown',
            usage_patterns=usage_patterns,
            configuration_files=config_files,
            best_practices_compliance=compliance_score,
            suggested_improvements=improvements
        )

    def _detect_python_framework_version(self, framework_name: str, files: list[str]) -> str | None:
        """Detect framework version from requirements files."""
        req_files = ['requirements.txt', 'pyproject.toml', 'setup.py', 'Pipfile']
        
        for file_path in files:
            file_name = Path(file_path).name
            if file_name in req_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check for version in requirements.txt
                    if file_name == 'requirements.txt':
                        pattern = rf'{re.escape(framework_name)}([>=<~!]+[\d.]+)'
                        match = re.search(pattern, content, re.IGNORECASE)
                        if match:
                            return match.group(1)
                    
                    # Check for version in pyproject.toml
                    elif file_name == 'pyproject.toml':
                        pattern = rf'"{re.escape(framework_name)}"\s*=\s*"([^"]+)"'
                        match = re.search(pattern, content, re.IGNORECASE)
                        if match:
                            return match.group(1)
                            
                except (UnicodeDecodeError, IOError):
                    continue
        
        return None

    def _calculate_python_compliance(self, framework_name: str, patterns: list[UsagePattern]) -> float:
        """Calculate best practices compliance score."""
        base_score = 0.5
        
        # Framework-specific compliance checks
        if framework_name == 'django':
            return self._calculate_django_compliance(patterns)
        elif framework_name == 'flask':
            return self._calculate_flask_compliance(patterns)
        elif framework_name == 'fastapi':
            return self._calculate_fastapi_compliance(patterns)
        
        return base_score

    def _calculate_django_compliance(self, patterns: list[UsagePattern]) -> float:
        """Calculate Django best practices compliance."""
        score = 0.5
        
        # Check for proper URL patterns
        url_patterns = [p for p in patterns if 'urls.py' in p.file_path]
        if url_patterns:
            score += 0.1
        
        # Check for model usage
        model_patterns = [p for p in patterns if 'models.py' in p.file_path]
        if model_patterns:
            score += 0.1
        
        # Check for proper view structure
        view_patterns = [p for p in patterns if any(keyword in p.pattern for keyword in ['views', 'View'])]
        if view_patterns:
            score += 0.1
        
        return min(score, 1.0)

    def _calculate_flask_compliance(self, patterns: list[UsagePattern]) -> float:
        """Calculate Flask best practices compliance."""
        score = 0.5
        
        # Check for proper route decorators
        route_patterns = [p for p in patterns if '@app.route' in p.pattern]
        if route_patterns:
            score += 0.2
        
        # Check for blueprint usage (advanced pattern)
        blueprint_patterns = [p for p in patterns if 'Blueprint' in p.pattern]
        if blueprint_patterns:
            score += 0.2
        
        return min(score, 1.0)

    def _calculate_fastapi_compliance(self, patterns: list[UsagePattern]) -> float:
        """Calculate FastAPI best practices compliance."""
        score = 0.5
        
        # Check for proper route decorators
        route_patterns = [p for p in patterns if any(method in p.pattern for method in ['get', 'post', 'put', 'delete'])]
        if route_patterns:
            score += 0.2
        
        # Check for dependency injection
        dependency_patterns = [p for p in patterns if 'Depends' in p.pattern]
        if dependency_patterns:
            score += 0.2
        
        return min(score, 1.0)

    def _suggest_python_improvements(self, framework_name: str, patterns: list[UsagePattern]) -> list[Improvement]:
        """Suggest improvements for Python frameworks."""
        improvements = []
        
        if framework_name == 'django':
            improvements.extend(self._suggest_django_improvements(patterns))
        elif framework_name == 'flask':
            improvements.extend(self._suggest_flask_improvements(patterns))
        elif framework_name == 'fastapi':
            improvements.extend(self._suggest_fastapi_improvements(patterns))
        
        return improvements

    def _suggest_django_improvements(self, patterns: list[UsagePattern]) -> list[Improvement]:
        """Suggest Django-specific improvements."""
        improvements = []
        
        # Check for missing migrations
        model_patterns = [p for p in patterns if 'models.py' in p.file_path]
        if model_patterns and not any('migrations' in p.file_path for p in patterns):
            improvements.append(Improvement(
                category='Database',
                description='Consider creating database migrations for your models',
                priority='medium',
                effort='low'
            ))
        
        return improvements

    def _suggest_flask_improvements(self, patterns: list[UsagePattern]) -> list[Improvement]:
        """Suggest Flask-specific improvements."""
        improvements = []
        
        # Check for blueprint usage
        route_patterns = [p for p in patterns if '@app.route' in p.pattern]
        blueprint_patterns = [p for p in patterns if 'Blueprint' in p.pattern]
        
        if len(route_patterns) > 5 and not blueprint_patterns:
            improvements.append(Improvement(
                category='Architecture',
                description='Consider using Flask Blueprints to organize your routes',
                priority='medium',
                effort='medium'
            ))
        
        return improvements

    def _suggest_fastapi_improvements(self, patterns: list[UsagePattern]) -> list[Improvement]:
        """Suggest FastAPI-specific improvements."""
        improvements = []
        
        # Check for dependency injection usage
        route_patterns = [p for p in patterns if any(method in p.pattern for method in ['get', 'post', 'put', 'delete'])]
        dependency_patterns = [p for p in patterns if 'Depends' in p.pattern]
        
        if len(route_patterns) > 3 and not dependency_patterns:
            improvements.append(Improvement(
                category='Architecture',
                description='Consider using FastAPI dependency injection for better code organization',
                priority='low',
                effort='medium'
            ))
        
        return improvements


class JavaScriptFrameworkDetector(FrameworkDetector):
    """Detector for JavaScript frameworks."""

    def __init__(self):
        """Initialize JavaScript framework detector."""
        self.framework_indicators = {
            'react': {
                'imports': ['react', 'React'],
                'files': ['package.json'],
                'patterns': [r'import.*React', r'from [\'"]react[\'"]', r'React\.', r'jsx?']
            },
            'vue': {
                'imports': ['vue', 'Vue'],
                'files': ['package.json', 'vue.config.js'],
                'patterns': [r'import.*Vue', r'from [\'"]vue[\'"]', r'Vue\.', r'<template>']
            },
            'angular': {
                'imports': ['@angular', 'angular'],
                'files': ['angular.json', 'package.json'],
                'patterns': [r'from [\'"]@angular', r'@Component', r'@Injectable', r'ng ']
            },
            'express': {
                'imports': ['express'],
                'files': ['package.json', 'server.js', 'app.js'],
                'patterns': [r'require\([\'"]express[\'"]\)', r'express\(\)', r'app\.(get|post|put|delete)']
            },
            'nodejs': {
                'imports': ['fs', 'path', 'http', 'https'],
                'files': ['package.json', 'server.js'],
                'patterns': [r'require\([\'"]fs[\'"]\)', r'require\([\'"]path[\'"]\)', r'process\.']
            },
            'webpack': {
                'imports': ['webpack'],
                'files': ['webpack.config.js', 'package.json'],
                'patterns': [r'module\.exports', r'webpack', r'entry:', r'output:']
            },
            'babel': {
                'imports': ['@babel'],
                'files': ['.babelrc', 'babel.config.js', 'package.json'],
                'patterns': [r'@babel', r'babel-', r'presets:', r'plugins:']
            },
            'jest': {
                'imports': ['jest'],
                'files': ['jest.config.js', 'package.json'],
                'patterns': [r'describe\(', r'test\(', r'it\(', r'expect\(']
            },
            'eslint': {
                'imports': ['eslint'],
                'files': ['.eslintrc.js', '.eslintrc.json', 'package.json'],
                'patterns': [r'eslint', r'rules:', r'extends:']
            }
        }

    def detect_frameworks(self, files: list[str]) -> list[str]:
        """Detect JavaScript frameworks."""
        detected = set()
        
        # First check package.json for dependencies
        package_json_frameworks = self._detect_from_package_json(files)
        detected.update(package_json_frameworks)
        
        # Then check source files
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_name = Path(file_path).name
                
                for framework, indicators in self.framework_indicators.items():
                    # Check file names
                    if file_name in indicators['files']:
                        detected.add(framework)
                        continue
                    
                    # Check import patterns
                    for import_name in indicators['imports']:
                        if re.search(rf'\b{re.escape(import_name)}\b', content):
                            detected.add(framework)
                            break
                    
                    # Check code patterns
                    for pattern in indicators['patterns']:
                        if re.search(pattern, content):
                            detected.add(framework)
                            break
                            
            except (UnicodeDecodeError, IOError):
                continue
        
        return list(detected)

    def analyze_framework(self, framework_name: str, files: list[str]) -> FrameworkInfo | None:
        """Analyze JavaScript framework usage."""
        if framework_name not in self.framework_indicators:
            return None
        
        indicators = self.framework_indicators[framework_name]
        usage_patterns = []
        config_files = []
        version = None
        
        # Analyze usage patterns
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_name = Path(file_path).name
                
                # Check for configuration files
                if file_name in indicators['files']:
                    config_files.append(file_path)
                
                # Analyze patterns
                for pattern in indicators['patterns']:
                    matches = re.findall(pattern, content)
                    if matches:
                        usage_patterns.append(UsagePattern(
                            pattern=pattern,
                            file_path=file_path,
                            occurrences=len(matches),
                            examples=matches[:3]
                        ))
                        
            except (UnicodeDecodeError, IOError):
                continue
        
        # Try to detect version from package.json
        version = self._detect_js_framework_version(framework_name, files)
        
        # Calculate compliance score
        compliance_score = self._calculate_js_compliance(framework_name, usage_patterns)
        
        # Generate improvements
        improvements = self._suggest_js_improvements(framework_name, usage_patterns)
        
        return FrameworkInfo(
            name=framework_name,
            version=version or 'unknown',
            usage_patterns=usage_patterns,
            configuration_files=config_files,
            best_practices_compliance=compliance_score,
            suggested_improvements=improvements
        )

    def _detect_from_package_json(self, files: list[str]) -> list[str]:
        """Detect frameworks from package.json."""
        detected = []
        
        for file_path in files:
            if Path(file_path).name == 'package.json':
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    dependencies = {}
                    dependencies.update(data.get('dependencies', {}))
                    dependencies.update(data.get('devDependencies', {}))
                    
                    for dep_name in dependencies:
                        if 'react' in dep_name.lower():
                            detected.append('react')
                        elif 'vue' in dep_name.lower():
                            detected.append('vue')
                        elif 'angular' in dep_name.lower() or '@angular' in dep_name:
                            detected.append('angular')
                        elif dep_name == 'express':
                            detected.append('express')
                        elif 'webpack' in dep_name.lower():
                            detected.append('webpack')
                        elif 'babel' in dep_name.lower() or '@babel' in dep_name:
                            detected.append('babel')
                        elif 'jest' in dep_name.lower():
                            detected.append('jest')
                        elif 'eslint' in dep_name.lower():
                            detected.append('eslint')
                    
                    # Check for Node.js indicators
                    if 'main' in data or 'scripts' in data:
                        detected.append('nodejs')
                        
                except (json.JSONDecodeError, UnicodeDecodeError, IOError):
                    continue
        
        return list(set(detected))

    def _detect_js_framework_version(self, framework_name: str, files: list[str]) -> str | None:
        """Detect framework version from package.json."""
        for file_path in files:
            if Path(file_path).name == 'package.json':
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    dependencies = {}
                    dependencies.update(data.get('dependencies', {}))
                    dependencies.update(data.get('devDependencies', {}))
                    
                    # Direct framework name match
                    if framework_name in dependencies:
                        return dependencies[framework_name]
                    
                    # Check for framework-specific packages
                    framework_packages = {
                        'react': ['react'],
                        'vue': ['vue'],
                        'angular': ['@angular/core'],
                        'express': ['express'],
                        'webpack': ['webpack'],
                        'babel': ['@babel/core'],
                        'jest': ['jest'],
                        'eslint': ['eslint']
                    }
                    
                    if framework_name in framework_packages:
                        for package in framework_packages[framework_name]:
                            if package in dependencies:
                                return dependencies[package]
                                
                except (json.JSONDecodeError, UnicodeDecodeError, IOError):
                    continue
        
        return None

    def _calculate_js_compliance(self, framework_name: str, patterns: list[UsagePattern]) -> float:
        """Calculate JavaScript framework compliance score."""
        base_score = 0.5
        
        if framework_name == 'react':
            return self._calculate_react_compliance(patterns)
        elif framework_name == 'vue':
            return self._calculate_vue_compliance(patterns)
        elif framework_name == 'angular':
            return self._calculate_angular_compliance(patterns)
        elif framework_name == 'express':
            return self._calculate_express_compliance(patterns)
        
        return base_score

    def _calculate_react_compliance(self, patterns: list[UsagePattern]) -> float:
        """Calculate React best practices compliance."""
        score = 0.5
        
        # Check for proper component structure
        component_patterns = [p for p in patterns if any(keyword in p.pattern for keyword in ['Component', 'function', 'const'])]
        if component_patterns:
            score += 0.2
        
        # Check for hooks usage (modern React)
        hook_patterns = [p for p in patterns if any(hook in p.pattern for hook in ['useState', 'useEffect', 'useContext'])]
        if hook_patterns:
            score += 0.2
        
        return min(score, 1.0)

    def _calculate_vue_compliance(self, patterns: list[UsagePattern]) -> float:
        """Calculate Vue.js best practices compliance."""
        score = 0.5
        
        # Check for single file components
        sfc_patterns = [p for p in patterns if '<template>' in p.pattern]
        if sfc_patterns:
            score += 0.3
        
        return min(score, 1.0)

    def _calculate_angular_compliance(self, patterns: list[UsagePattern]) -> float:
        """Calculate Angular best practices compliance."""
        score = 0.5
        
        # Check for proper decorators
        decorator_patterns = [p for p in patterns if any(dec in p.pattern for dec in ['@Component', '@Injectable', '@NgModule'])]
        if decorator_patterns:
            score += 0.3
        
        return min(score, 1.0)

    def _calculate_express_compliance(self, patterns: list[UsagePattern]) -> float:
        """Calculate Express.js best practices compliance."""
        score = 0.5
        
        # Check for proper route handling
        route_patterns = [p for p in patterns if 'app.' in p.pattern and any(method in p.pattern for method in ['get', 'post', 'put', 'delete'])]
        if route_patterns:
            score += 0.2
        
        # Check for middleware usage
        middleware_patterns = [p for p in patterns if 'use(' in p.pattern]
        if middleware_patterns:
            score += 0.2
        
        return min(score, 1.0)

    def _suggest_js_improvements(self, framework_name: str, patterns: list[UsagePattern]) -> list[Improvement]:
        """Suggest improvements for JavaScript frameworks."""
        improvements = []
        
        if framework_name == 'react':
            improvements.extend(self._suggest_react_improvements(patterns))
        elif framework_name == 'vue':
            improvements.extend(self._suggest_vue_improvements(patterns))
        elif framework_name == 'angular':
            improvements.extend(self._suggest_angular_improvements(patterns))
        elif framework_name == 'express':
            improvements.extend(self._suggest_express_improvements(patterns))
        
        return improvements

    def _suggest_react_improvements(self, patterns: list[UsagePattern]) -> list[Improvement]:
        """Suggest React-specific improvements."""
        improvements = []
        
        # Check for modern hooks usage
        hook_patterns = [p for p in patterns if any(hook in p.pattern for hook in ['useState', 'useEffect'])]
        class_patterns = [p for p in patterns if 'class' in p.pattern and 'Component' in p.pattern]
        
        if class_patterns and not hook_patterns:
            improvements.append(Improvement(
                category='Modernization',
                description='Consider migrating class components to functional components with hooks',
                priority='medium',
                effort='medium'
            ))
        
        return improvements

    def _suggest_vue_improvements(self, patterns: list[UsagePattern]) -> list[Improvement]:
        """Suggest Vue.js-specific improvements."""
        improvements = []
        
        # Check for Composition API usage (Vue 3)
        composition_patterns = [p for p in patterns if any(api in p.pattern for api in ['setup()', 'ref(', 'reactive('])]
        
        if not composition_patterns:
            improvements.append(Improvement(
                category='Modernization',
                description='Consider using Vue 3 Composition API for better code organization',
                priority='low',
                effort='high'
            ))
        
        return improvements

    def _suggest_angular_improvements(self, patterns: list[UsagePattern]) -> list[Improvement]:
        """Suggest Angular-specific improvements."""
        improvements = []
        
        # Check for proper service usage
        service_patterns = [p for p in patterns if '@Injectable' in p.pattern]
        component_patterns = [p for p in patterns if '@Component' in p.pattern]
        
        if len(component_patterns) > 3 and not service_patterns:
            improvements.append(Improvement(
                category='Architecture',
                description='Consider creating services to share data and logic between components',
                priority='medium',
                effort='medium'
            ))
        
        return improvements

    def _suggest_express_improvements(self, patterns: list[UsagePattern]) -> list[Improvement]:
        """Suggest Express.js-specific improvements."""
        improvements = []
        
        # Check for error handling middleware
        error_patterns = [p for p in patterns if 'error' in p.pattern.lower()]
        route_patterns = [p for p in patterns if 'app.' in p.pattern]
        
        if len(route_patterns) > 5 and not error_patterns:
            improvements.append(Improvement(
                category='Error Handling',
                description='Consider adding error handling middleware for better error management',
                priority='high',
                effort='low'
            ))
        
        return improvements


class TypeScriptFrameworkDetector(FrameworkDetector):
    """Detector for TypeScript frameworks."""

    def __init__(self):
        """Initialize TypeScript framework detector."""
        # TypeScript frameworks often overlap with JavaScript frameworks
        self.js_detector = JavaScriptFrameworkDetector()
        
        self.ts_specific_indicators = {
            'nestjs': {
                'imports': ['@nestjs'],
                'files': ['nest-cli.json', 'package.json'],
                'patterns': [r'@Controller', r'@Injectable', r'@Module', r'from [\'"]@nestjs']
            },
            'angular': {
                'imports': ['@angular'],
                'files': ['angular.json', 'tsconfig.json'],
                'patterns': [r'@Component', r'@Injectable', r'@NgModule']
            }
        }

    def detect_frameworks(self, files: list[str]) -> list[str]:
        """Detect TypeScript frameworks."""
        # Start with JavaScript framework detection
        detected = set(self.js_detector.detect_frameworks(files))
        
        # Add TypeScript-specific frameworks
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_name = Path(file_path).name
                
                for framework, indicators in self.ts_specific_indicators.items():
                    # Check file names
                    if file_name in indicators['files']:
                        detected.add(framework)
                        continue
                    
                    # Check import patterns
                    for import_name in indicators['imports']:
                        if re.search(rf'\b{re.escape(import_name)}\b', content):
                            detected.add(framework)
                            break
                    
                    # Check code patterns
                    for pattern in indicators['patterns']:
                        if re.search(pattern, content):
                            detected.add(framework)
                            break
                            
            except (UnicodeDecodeError, IOError):
                continue
        
        return list(detected)

    def analyze_framework(self, framework_name: str, files: list[str]) -> FrameworkInfo | None:
        """Analyze TypeScript framework usage."""
        # For TypeScript-specific frameworks
        if framework_name in self.ts_specific_indicators:
            return self._analyze_ts_framework(framework_name, files)
        
        # For JavaScript frameworks used in TypeScript
        return self.js_detector.analyze_framework(framework_name, files)

    def _analyze_ts_framework(self, framework_name: str, files: list[str]) -> FrameworkInfo | None:
        """Analyze TypeScript-specific framework."""
        if framework_name not in self.ts_specific_indicators:
            return None
        
        indicators = self.ts_specific_indicators[framework_name]
        usage_patterns = []
        config_files = []
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_name = Path(file_path).name
                
                if file_name in indicators['files']:
                    config_files.append(file_path)
                
                for pattern in indicators['patterns']:
                    matches = re.findall(pattern, content)
                    if matches:
                        usage_patterns.append(UsagePattern(
                            pattern=pattern,
                            file_path=file_path,
                            occurrences=len(matches),
                            examples=matches[:3]
                        ))
                        
            except (UnicodeDecodeError, IOError):
                continue
        
        return FrameworkInfo(
            name=framework_name,
            version='unknown',
            usage_patterns=usage_patterns,
            configuration_files=config_files,
            best_practices_compliance=0.7,  # Default score
            suggested_improvements=[]
        )


class JavaFrameworkDetector(FrameworkDetector):
    """Detector for Java frameworks."""

    def __init__(self):
        """Initialize Java framework detector."""
        self.framework_indicators = {
            'spring_boot': {
                'imports': ['org.springframework.boot', 'SpringBootApplication'],
                'files': ['pom.xml', 'build.gradle', 'application.properties'],
                'patterns': [r'@SpringBootApplication', r'@RestController', r'@Service', r'@Repository']
            },
            'spring': {
                'imports': ['org.springframework', 'springframework'],
                'files': ['applicationContext.xml', 'pom.xml'],
                'patterns': [r'@Component', r'@Autowired', r'@Configuration', r'ApplicationContext']
            },
            'hibernate': {
                'imports': ['org.hibernate', 'hibernate'],
                'files': ['hibernate.cfg.xml', 'pom.xml'],
                'patterns': [r'@Entity', r'@Table', r'@Column', r'SessionFactory']
            },
            'junit': {
                'imports': ['org.junit', 'junit'],
                'files': ['pom.xml', 'build.gradle'],
                'patterns': [r'@Test', r'@Before', r'@After', r'Assert\.']
            },
            'maven': {
                'imports': [],
                'files': ['pom.xml'],
                'patterns': [r'<groupId>', r'<artifactId>', r'<version>']
            },
            'gradle': {
                'imports': [],
                'files': ['build.gradle', 'settings.gradle'],
                'patterns': [r'dependencies \{', r'apply plugin:', r'implementation ']
            }
        }

    def detect_frameworks(self, files: list[str]) -> list[str]:
        """Detect Java frameworks."""
        detected = set()
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_name = Path(file_path).name
                
                for framework, indicators in self.framework_indicators.items():
                    # Check file names
                    if file_name in indicators['files']:
                        detected.add(framework)
                        continue
                    
                    # Check import patterns
                    for import_name in indicators['imports']:
                        if re.search(rf'\b{re.escape(import_name)}\b', content):
                            detected.add(framework)
                            break
                    
                    # Check code patterns
                    for pattern in indicators['patterns']:
                        if re.search(pattern, content):
                            detected.add(framework)
                            break
                            
            except (UnicodeDecodeError, IOError):
                continue
        
        return list(detected)

    def analyze_framework(self, framework_name: str, files: list[str]) -> FrameworkInfo | None:
        """Analyze Java framework usage."""
        if framework_name not in self.framework_indicators:
            return None
        
        indicators = self.framework_indicators[framework_name]
        usage_patterns = []
        config_files = []
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_name = Path(file_path).name
                
                if file_name in indicators['files']:
                    config_files.append(file_path)
                
                for pattern in indicators['patterns']:
                    matches = re.findall(pattern, content)
                    if matches:
                        usage_patterns.append(UsagePattern(
                            pattern=pattern,
                            file_path=file_path,
                            occurrences=len(matches),
                            examples=matches[:3]
                        ))
                        
            except (UnicodeDecodeError, IOError):
                continue
        
        # Calculate compliance score
        compliance_score = self._calculate_java_compliance(framework_name, usage_patterns)
        
        # Generate improvements
        improvements = self._suggest_java_improvements(framework_name, usage_patterns)
        
        return FrameworkInfo(
            name=framework_name,
            version='unknown',
            usage_patterns=usage_patterns,
            configuration_files=config_files,
            best_practices_compliance=compliance_score,
            suggested_improvements=improvements
        )

    def _calculate_java_compliance(self, framework_name: str, patterns: list[UsagePattern]) -> float:
        """Calculate Java framework compliance score."""
        base_score = 0.5
        
        if framework_name == 'spring_boot':
            return self._calculate_spring_boot_compliance(patterns)
        elif framework_name == 'spring':
            return self._calculate_spring_compliance(patterns)
        
        return base_score

    def _calculate_spring_boot_compliance(self, patterns: list[UsagePattern]) -> float:
        """Calculate Spring Boot compliance score."""
        score = 0.5
        
        # Check for proper annotations
        annotation_patterns = [p for p in patterns if any(ann in p.pattern for ann in ['@RestController', '@Service', '@Repository'])]
        if annotation_patterns:
            score += 0.3
        
        return min(score, 1.0)

    def _calculate_spring_compliance(self, patterns: list[UsagePattern]) -> float:
        """Calculate Spring framework compliance score."""
        score = 0.5
        
        # Check for dependency injection
        di_patterns = [p for p in patterns if '@Autowired' in p.pattern]
        if di_patterns:
            score += 0.2
        
        # Check for configuration
        config_patterns = [p for p in patterns if '@Configuration' in p.pattern]
        if config_patterns:
            score += 0.2
        
        return min(score, 1.0)

    def _suggest_java_improvements(self, framework_name: str, patterns: list[UsagePattern]) -> list[Improvement]:
        """Suggest improvements for Java frameworks."""
        improvements = []
        
        if framework_name == 'spring_boot':
            improvements.extend(self._suggest_spring_boot_improvements(patterns))
        elif framework_name == 'spring':
            improvements.extend(self._suggest_spring_improvements(patterns))
        
        return improvements

    def _suggest_spring_boot_improvements(self, patterns: list[UsagePattern]) -> list[Improvement]:
        """Suggest Spring Boot improvements."""
        improvements = []
        
        # Check for proper layered architecture
        controller_patterns = [p for p in patterns if '@RestController' in p.pattern]
        service_patterns = [p for p in patterns if '@Service' in p.pattern]
        repository_patterns = [p for p in patterns if '@Repository' in p.pattern]
        
        if controller_patterns and not service_patterns:
            improvements.append(Improvement(
                category='Architecture',
                description='Consider adding service layer for business logic separation',
                priority='medium',
                effort='medium'
            ))
        
        if service_patterns and not repository_patterns:
            improvements.append(Improvement(
                category='Architecture',
                description='Consider adding repository layer for data access separation',
                priority='medium',
                effort='medium'
            ))
        
        return improvements

    def _suggest_spring_improvements(self, patterns: list[UsagePattern]) -> list[Improvement]:
        """Suggest Spring framework improvements."""
        improvements = []
        
        # Check for modern annotation usage
        autowired_patterns = [p for p in patterns if '@Autowired' in p.pattern]
        component_patterns = [p for p in patterns if '@Component' in p.pattern]
        
        if len(component_patterns) > 5 and not autowired_patterns:
            improvements.append(Improvement(
                category='Dependency Injection',
                description='Consider using @Autowired for dependency injection',
                priority='medium',
                effort='low'
            ))
        
        return improvements


class WebFrameworkDetector(FrameworkDetector):
    """Detector for web-specific frameworks and technologies."""

    def __init__(self):
        """Initialize web framework detector."""
        self.framework_indicators = {
            'bootstrap': {
                'imports': ['bootstrap'],
                'files': ['package.json'],
                'patterns': [r'bootstrap', r'btn-', r'col-', r'container-']
            },
            'tailwind': {
                'imports': ['tailwindcss'],
                'files': ['tailwind.config.js', 'package.json'],
                'patterns': [r'@tailwind', r'bg-', r'text-', r'p-\d', r'm-\d']
            },
            'jquery': {
                'imports': ['jquery'],
                'files': ['package.json'],
                'patterns': [r'\$\(', r'jQuery', r'\.click\(', r'\.ready\(']
            },
            'sass': {
                'imports': ['sass', 'node-sass'],
                'files': ['package.json'],
                'patterns': [r'\$\w+:', r'@mixin', r'@include', r'@extend']
            }
        }

    def detect_frameworks(self, files: list[str]) -> list[str]:
        """Detect web frameworks."""
        detected = set()
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_name = Path(file_path).name
                
                for framework, indicators in self.framework_indicators.items():
                    # Check file names
                    if file_name in indicators['files']:
                        # For package.json, check dependencies
                        if file_name == 'package.json':
                            try:
                                data = json.loads(content)
                                dependencies = {}
                                dependencies.update(data.get('dependencies', {}))
                                dependencies.update(data.get('devDependencies', {}))
                                
                                for import_name in indicators['imports']:
                                    if import_name in dependencies:
                                        detected.add(framework)
                                        break
                            except json.JSONDecodeError:
                                pass
                        else:
                            detected.add(framework)
                        continue
                    
                    # Check code patterns
                    for pattern in indicators['patterns']:
                        if re.search(pattern, content):
                            detected.add(framework)
                            break
                            
            except (UnicodeDecodeError, IOError):
                continue
        
        return list(detected)

    def analyze_framework(self, framework_name: str, files: list[str]) -> FrameworkInfo | None:
        """Analyze web framework usage."""
        if framework_name not in self.framework_indicators:
            return None
        
        indicators = self.framework_indicators[framework_name]
        usage_patterns = []
        config_files = []
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_name = Path(file_path).name
                
                if file_name in indicators['files']:
                    config_files.append(file_path)
                
                for pattern in indicators['patterns']:
                    matches = re.findall(pattern, content)
                    if matches:
                        usage_patterns.append(UsagePattern(
                            pattern=pattern,
                            file_path=file_path,
                            occurrences=len(matches),
                            examples=matches[:3]
                        ))
                        
            except (UnicodeDecodeError, IOError):
                continue
        
        return FrameworkInfo(
            name=framework_name,
            version='unknown',
            usage_patterns=usage_patterns,
            configuration_files=config_files,
            best_practices_compliance=0.7,  # Default score
            suggested_improvements=[]
        )