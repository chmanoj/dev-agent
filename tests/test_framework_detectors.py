"""Tests for framework detection components."""

import json
import tempfile
from pathlib import Path

import pytest

from dev_agent.analysis.framework_detectors import (
    FrameworkDetectorRegistry,
    JavaFrameworkDetector,
    JavaScriptFrameworkDetector,
    PythonFrameworkDetector,
    ReactFrameworkDetector,
    WebFrameworkDetector,
)
from dev_agent.models.enums import FrameworkType, LanguageType


class TestPythonFrameworkDetector:
    """Test suite for PythonFrameworkDetector."""

    @pytest.fixture
    def temp_python_project(self):
        """Create a temporary Python project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create requirements.txt
            (project_path / "requirements.txt").write_text("""
flask==2.0.1
pytest==7.1.0
sqlalchemy==1.4.0
celery==5.2.0
""")
            
            # Create Python files with imports
            (project_path / "app.py").write_text("""
from flask import Flask, request
import sqlalchemy
from celery import Celery

app = Flask(__name__)
celery = Celery('app')

@app.route('/')
def hello():
    return 'Hello World!'
""")
            
            # Create pyproject.toml
            (project_path / "pyproject.toml").write_text("""
[project]
dependencies = [
    "django>=4.0",
    "fastapi>=0.70.0",
    "pandas>=1.3.0"
]
""")
            
            yield project_path

    def test_detect_frameworks_from_requirements(self, temp_python_project):
        """Test framework detection from requirements.txt."""
        detector = PythonFrameworkDetector()
        files = list(temp_python_project.glob("*.py"))
        
        frameworks = detector.detect_frameworks(temp_python_project, files)
        
        assert FrameworkType.FLASK in frameworks
        assert FrameworkType.PYTEST in frameworks
        assert FrameworkType.SQLALCHEMY in frameworks
        assert FrameworkType.CELERY in frameworks

    def test_detect_frameworks_from_imports(self, temp_python_project):
        """Test framework detection from import statements."""
        detector = PythonFrameworkDetector()
        files = list(temp_python_project.glob("*.py"))
        
        frameworks = detector.detect_frameworks(temp_python_project, files)
        
        # Should detect Flask from import statement
        assert FrameworkType.FLASK in frameworks
        assert FrameworkType.SQLALCHEMY in frameworks
        assert FrameworkType.CELERY in frameworks

    def test_detect_frameworks_from_pyproject_toml(self, temp_python_project):
        """Test framework detection from pyproject.toml."""
        # Remove requirements.txt to test pyproject.toml only
        (temp_python_project / "requirements.txt").unlink()
        
        detector = PythonFrameworkDetector()
        files = list(temp_python_project.glob("*.py"))
        
        frameworks = detector.detect_frameworks(temp_python_project, files)
        
        # Should detect frameworks from pyproject.toml
        assert FrameworkType.DJANGO in frameworks
        assert FrameworkType.FASTAPI in frameworks
        assert FrameworkType.PANDAS in frameworks

    def test_no_frameworks_detected(self):
        """Test behavior when no frameworks are detected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create a simple Python file without framework imports
            (project_path / "simple.py").write_text("""
def add(a, b):
    return a + b

if __name__ == "__main__":
    print(add(2, 3))
""")
            
            detector = PythonFrameworkDetector()
            files = list(project_path.glob("*.py"))
            
            frameworks = detector.detect_frameworks(project_path, files)
            
            assert len(frameworks) == 0


class TestJavaScriptFrameworkDetector:
    """Test suite for JavaScriptFrameworkDetector."""

    @pytest.fixture
    def temp_js_project(self):
        """Create a temporary JavaScript project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create package.json
            package_json = {
                "name": "test-project",
                "version": "1.0.0",
                "dependencies": {
                    "react": "^18.0.0",
                    "express": "^4.18.0",
                    "@nestjs/core": "^9.0.0"
                },
                "devDependencies": {
                    "jest": "^28.0.0",
                    "eslint": "^8.0.0",
                    "webpack": "^5.0.0",
                    "@babel/core": "^7.0.0"
                }
            }
            (project_path / "package.json").write_text(json.dumps(package_json))
            
            # Create JavaScript files with imports
            (project_path / "app.js").write_text("""
const express = require('express');
const app = express();

app.get('/', (req, res) => {
    res.send('Hello World!');
});

app.listen(3000);
""")
            
            (project_path / "component.jsx").write_text("""
import React from 'react';

function MyComponent() {
    return <div>Hello React!</div>;
}

export default MyComponent;
""")
            
            yield project_path

    def test_detect_frameworks_from_package_json(self, temp_js_project):
        """Test framework detection from package.json."""
        detector = JavaScriptFrameworkDetector()
        files = list(temp_js_project.glob("*.js")) + list(temp_js_project.glob("*.jsx"))
        
        frameworks = detector.detect_frameworks(temp_js_project, files)
        
        assert FrameworkType.REACT in frameworks
        assert FrameworkType.EXPRESS in frameworks
        assert FrameworkType.NESTJS in frameworks
        assert FrameworkType.JEST in frameworks
        assert FrameworkType.ESLINT in frameworks
        assert FrameworkType.WEBPACK in frameworks
        assert FrameworkType.BABEL in frameworks

    def test_detect_frameworks_from_imports(self, temp_js_project):
        """Test framework detection from import statements."""
        # Remove package.json to test import detection only
        (temp_js_project / "package.json").unlink()
        
        detector = JavaScriptFrameworkDetector()
        files = list(temp_js_project.glob("*.js")) + list(temp_js_project.glob("*.jsx"))
        
        frameworks = detector.detect_frameworks(temp_js_project, files)
        
        # Should detect React and Express from imports
        assert FrameworkType.REACT in frameworks
        assert FrameworkType.EXPRESS in frameworks

    def test_typescript_detection(self, temp_js_project):
        """Test TypeScript framework detection."""
        # Create TypeScript files
        (temp_js_project / "app.ts").write_text("""
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';

async function bootstrap() {
    const app = await NestFactory.create(AppModule);
    await app.listen(3000);
}
bootstrap();
""")
        
        detector = JavaScriptFrameworkDetector()
        files = list(temp_js_project.glob("*.ts"))
        
        frameworks = detector.detect_frameworks(temp_js_project, files)
        
        # Should detect NestJS from TypeScript imports
        assert FrameworkType.NESTJS in frameworks


class TestJavaFrameworkDetector:
    """Test suite for JavaFrameworkDetector."""

    @pytest.fixture
    def temp_java_project(self):
        """Create a temporary Java project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create pom.xml
            (project_path / "pom.xml").write_text("""
<?xml version="1.0" encoding="UTF-8"?>
<project>
    <groupId>com.example</groupId>
    <artifactId>test-project</artifactId>
    <version>1.0.0</version>
    
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter</artifactId>
            <version>2.7.0</version>
        </dependency>
        <dependency>
            <groupId>org.springframework</groupId>
            <artifactId>spring-core</artifactId>
            <version>5.3.0</version>
        </dependency>
        <dependency>
            <groupId>org.hibernate</groupId>
            <artifactId>hibernate-core</artifactId>
            <version>5.6.0</version>
        </dependency>
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.13.2</version>
        </dependency>
    </dependencies>
</project>
""")
            
            # Create Java files
            java_dir = project_path / "src" / "main" / "java" / "com" / "example"
            java_dir.mkdir(parents=True)
            
            (java_dir / "Application.java").write_text("""
package com.example;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.stereotype.Service;
import org.hibernate.Session;

@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
""")
            
            yield project_path

    def test_detect_frameworks_from_pom_xml(self, temp_java_project):
        """Test framework detection from pom.xml."""
        detector = JavaFrameworkDetector()
        files = list(temp_java_project.rglob("*.java"))
        
        frameworks = detector.detect_frameworks(temp_java_project, files)
        
        assert FrameworkType.SPRING_BOOT in frameworks
        assert FrameworkType.SPRING in frameworks
        assert FrameworkType.HIBERNATE in frameworks
        assert FrameworkType.JUNIT in frameworks
        assert FrameworkType.MAVEN in frameworks

    def test_detect_frameworks_from_imports(self, temp_java_project):
        """Test framework detection from import statements."""
        detector = JavaFrameworkDetector()
        files = list(temp_java_project.rglob("*.java"))
        
        frameworks = detector.detect_frameworks(temp_java_project, files)
        
        # Should detect Spring and Hibernate from imports
        assert FrameworkType.SPRING in frameworks
        assert FrameworkType.HIBERNATE in frameworks

    def test_gradle_project_detection(self, temp_java_project):
        """Test Gradle project detection."""
        # Remove pom.xml and create build.gradle
        (temp_java_project / "pom.xml").unlink()
        
        (temp_java_project / "build.gradle").write_text("""
plugins {
    id 'java'
    id 'org.springframework.boot' version '2.7.0'
}

dependencies {
    implementation 'org.springframework.boot:spring-boot-starter'
    implementation 'org.hibernate:hibernate-core:5.6.0'
    testImplementation 'junit:junit:4.13.2'
}
""")
        
        detector = JavaFrameworkDetector()
        files = list(temp_java_project.rglob("*.java"))
        
        frameworks = detector.detect_frameworks(temp_java_project, files)
        
        assert FrameworkType.GRADLE in frameworks
        assert FrameworkType.SPRING_BOOT in frameworks
        assert FrameworkType.HIBERNATE in frameworks
        assert FrameworkType.JUNIT in frameworks


class TestWebFrameworkDetector:
    """Test suite for WebFrameworkDetector."""

    @pytest.fixture
    def temp_web_project(self):
        """Create a temporary web project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create package.json with web frameworks
            package_json = {
                "name": "web-project",
                "dependencies": {
                    "bootstrap": "^5.1.0",
                    "tailwindcss": "^3.0.0",
                    "jquery": "^3.6.0"
                },
                "devDependencies": {
                    "sass": "^1.50.0"
                }
            }
            (project_path / "package.json").write_text(json.dumps(package_json))
            
            # Create HTML file
            (project_path / "index.html").write_text("""
<!DOCTYPE html>
<html>
<head>
    <title>Test</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
</head>
<body>
    <div class="container">
        <h1 class="text-primary">Hello Bootstrap!</h1>
        <div class="bg-blue-500 text-white p-4">Tailwind CSS</div>
    </div>
    <script>
        $(document).ready(function() {
            console.log("jQuery loaded");
        });
    </script>
</body>
</html>
""")
            
            # Create CSS file
            (project_path / "styles.css").write_text("""
@import 'bootstrap/dist/css/bootstrap.min.css';
@import 'tailwindcss/base';
@import 'tailwindcss/components';
@import 'tailwindcss/utilities';

.custom-class {
    @apply bg-blue-500 text-white;
}
""")
            
            yield project_path

    def test_detect_frameworks_from_package_json(self, temp_web_project):
        """Test web framework detection from package.json."""
        detector = WebFrameworkDetector()
        files = list(temp_web_project.glob("*.html")) + list(temp_web_project.glob("*.css"))
        
        frameworks = detector.detect_frameworks(temp_web_project, files)
        
        assert FrameworkType.BOOTSTRAP in frameworks
        assert FrameworkType.TAILWIND in frameworks
        assert FrameworkType.JQUERY in frameworks
        assert FrameworkType.SASS in frameworks

    def test_detect_frameworks_from_html_content(self, temp_web_project):
        """Test web framework detection from HTML content."""
        # Remove package.json to test content detection only
        (temp_web_project / "package.json").unlink()
        
        detector = WebFrameworkDetector()
        files = list(temp_web_project.glob("*.html")) + list(temp_web_project.glob("*.css"))
        
        frameworks = detector.detect_frameworks(temp_web_project, files)
        
        # Should detect Bootstrap, Tailwind, and jQuery from content
        assert FrameworkType.BOOTSTRAP in frameworks
        assert FrameworkType.TAILWIND in frameworks
        assert FrameworkType.JQUERY in frameworks

    def test_detect_frameworks_from_css_content(self, temp_web_project):
        """Test web framework detection from CSS content."""
        detector = WebFrameworkDetector()
        files = list(temp_web_project.glob("*.css"))
        
        frameworks = detector.detect_frameworks(temp_web_project, files)
        
        # Should detect Bootstrap and Tailwind from CSS imports
        assert FrameworkType.BOOTSTRAP in frameworks
        assert FrameworkType.TAILWIND in frameworks


class TestReactFrameworkDetector:
    """Test suite for ReactFrameworkDetector."""

    @pytest.fixture
    def temp_react_project(self):
        """Create a temporary React project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create package.json
            package_json = {
                "name": "react-project",
                "version": "1.0.0",
                "dependencies": {
                    "react": "^18.0.0",
                    "react-dom": "^18.0.0"
                },
                "devDependencies": {
                    "@testing-library/react": "^13.0.0",
                    "eslint": "^8.0.0"
                },
                "scripts": {
                    "start": "react-scripts start",
                    "test": "react-scripts test"
                }
            }
            (project_path / "package.json").write_text(json.dumps(package_json))
            
            # Create TypeScript config
            (project_path / "tsconfig.json").write_text(json.dumps({
                "compilerOptions": {
                    "target": "es5",
                    "lib": ["dom", "dom.iterable"],
                    "allowJs": True,
                    "skipLibCheck": True,
                    "esModuleInterop": True,
                    "allowSyntheticDefaultImports": True,
                    "strict": True,
                    "forceConsistentCasingInFileNames": True,
                    "moduleResolution": "node",
                    "resolveJsonModule": True,
                    "isolatedModules": True,
                    "noEmit": True,
                    "jsx": "react-jsx"
                },
                "include": ["src"]
            }))
            
            # Create ESLint config
            (project_path / ".eslintrc.json").write_text(json.dumps({
                "extends": [
                    "react-app",
                    "react-app/jest"
                ]
            }))
            
            # Create src directory with components
            src_dir = project_path / "src"
            src_dir.mkdir()
            components_dir = src_dir / "components"
            components_dir.mkdir()
            
            (src_dir / "App.jsx").write_text("""
import React, { useState, useEffect } from 'react';

function App() {
    const [count, setCount] = useState(0);
    
    useEffect(() => {
        document.title = `Count: ${count}`;
    }, [count]);
    
    return (
        <div className="App">
            <h1>React App</h1>
            <p>Count: {count}</p>
            <button onClick={() => setCount(count + 1)}>
                Increment
            </button>
        </div>
    );
}

export default App;
""")
            
            (src_dir / "components" / "Header.tsx").write_text("""
import React from 'react';

interface HeaderProps {
    title: string;
}

const Header: React.FC<HeaderProps> = ({ title }) => {
    return (
        <header>
            <h1>{title}</h1>
        </header>
    );
};

export default Header;
""")
            
            yield project_path

    def test_analyze_react_usage(self, temp_react_project):
        """Test detailed React usage analysis."""
        detector = ReactFrameworkDetector()
        framework_info = detector.analyze_usage(temp_react_project)
        
        assert framework_info is not None
        assert framework_info.name == "React"
        assert framework_info.version == "^18.0.0"
        
        # Should have usage patterns
        assert len(framework_info.usage_patterns) > 0
        
        # Should have configuration files
        assert "package.json" in framework_info.configuration_files
        assert "tsconfig.json" in framework_info.configuration_files
        
        # Should have compliance score
        assert 0.0 <= framework_info.best_practices_compliance <= 1.0
        
        # Should have improvement suggestions
        assert isinstance(framework_info.suggested_improvements, list)

    def test_react_patterns_analysis(self, temp_react_project):
        """Test React pattern analysis."""
        detector = ReactFrameworkDetector()
        framework_info = detector.analyze_usage(temp_react_project)
        
        # Should detect functional components and hooks
        pattern_names = [pattern.pattern for pattern in framework_info.usage_patterns]
        assert "Functional Components" in pattern_names
        assert "React Hooks" in pattern_names

    def test_react_compliance_calculation(self, temp_react_project):
        """Test React best practices compliance calculation."""
        detector = ReactFrameworkDetector()
        framework_info = detector.analyze_usage(temp_react_project)
        
        # Should have high compliance due to TypeScript, ESLint, etc.
        assert framework_info.best_practices_compliance > 0.5

    def test_react_without_typescript(self, temp_react_project):
        """Test React analysis without TypeScript."""
        # Remove TypeScript config
        (temp_react_project / "tsconfig.json").unlink()
        
        detector = ReactFrameworkDetector()
        framework_info = detector.analyze_usage(temp_react_project)
        
        assert framework_info is not None
        # Compliance should be lower without TypeScript
        assert framework_info.best_practices_compliance < 1.0
        
        # Should suggest TypeScript migration
        improvement_descriptions = [imp.description for imp in framework_info.suggested_improvements]
        typescript_suggestion = any("TypeScript" in desc for desc in improvement_descriptions)
        assert typescript_suggestion


class TestFrameworkDetectorRegistry:
    """Test suite for FrameworkDetectorRegistry."""

    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = FrameworkDetectorRegistry()
        
        # Should have detectors for major languages
        assert registry.get_detector(LanguageType.PYTHON) is not None
        assert registry.get_detector(LanguageType.JAVASCRIPT) is not None
        assert registry.get_detector(LanguageType.TYPESCRIPT) is not None
        assert registry.get_detector(LanguageType.JAVA) is not None
        assert registry.get_detector(LanguageType.HTML) is not None
        assert registry.get_detector(LanguageType.CSS) is not None

    def test_framework_detector_registration(self):
        """Test framework-specific detector registration."""
        registry = FrameworkDetectorRegistry()
        
        # Should have React detector
        react_detector = registry.get_framework_detector(FrameworkType.REACT)
        assert react_detector is not None
        assert isinstance(react_detector, ReactFrameworkDetector)

    def test_custom_detector_registration(self):
        """Test custom detector registration."""
        registry = FrameworkDetectorRegistry()
        
        # Register a custom detector
        custom_detector = PythonFrameworkDetector()
        registry.register_detector(LanguageType.PYTHON, custom_detector)
        
        # Should return the custom detector
        assert registry.get_detector(LanguageType.PYTHON) is custom_detector

    def test_unsupported_language(self):
        """Test behavior with unsupported language."""
        registry = FrameworkDetectorRegistry()
        
        # Should return None for unsupported language
        assert registry.get_detector(LanguageType.SQL) is None

    def test_unsupported_framework(self):
        """Test behavior with unsupported framework."""
        registry = FrameworkDetectorRegistry()
        
        # Should return None for unsupported framework
        assert registry.get_framework_detector(FrameworkType.DJANGO) is None