"""Tests for multi-language project detection and analysis."""

import json
import tempfile
from pathlib import Path

import pytest

from dev_agent.analysis.multi_language_analyzer import MultiLanguageAnalyzer
from dev_agent.models.enums import FrameworkType, LanguageType


class TestMultiLanguageAnalyzer:
    """Test suite for MultiLanguageAnalyzer."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project with multiple languages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create Python files
            (project_path / "main.py").write_text("""
import flask
from typing import List

class UserService:
    def get_users(self) -> List[str]:
        '''Get all users.'''
        try:
            return ["user1", "user2"]
        except Exception as e:
            raise ValueError("Failed to get users") from e

@app.route('/users')
def users():
    return UserService().get_users()
""")
            
            (project_path / "requirements.txt").write_text("""
flask==2.0.1
pytest==7.1.0
""")
            
            # Create JavaScript files
            (project_path / "app.js").write_text("""
const express = require('express');
const app = express();

class UserController {
    async getUsers() {
        try {
            const users = await fetch('/api/users');
            return users.json();
        } catch (error) {
            throw new Error('Failed to fetch users');
        }
    }
}

app.get('/users', (req, res) => {
    const controller = new UserController();
    controller.getUsers().then(users => res.json(users));
});
""")
            
            (project_path / "package.json").write_text(json.dumps({
                "name": "test-project",
                "version": "1.0.0",
                "dependencies": {
                    "express": "^4.18.0",
                    "react": "^18.0.0"
                },
                "devDependencies": {
                    "jest": "^28.0.0",
                    "eslint": "^8.0.0"
                }
            }))
            
            # Create TypeScript files
            (project_path / "types.ts").write_text("""
interface User {
    id: number;
    name: string;
    email: string;
}

export class UserManager {
    private users: User[] = [];
    
    public addUser(user: User): void {
        this.users.push(user);
    }
    
    public getUsers(): User[] {
        return this.users;
    }
}
""")
            
            # Create Java files
            java_dir = project_path / "src" / "main" / "java" / "com" / "example"
            java_dir.mkdir(parents=True)
            
            (java_dir / "UserService.java").write_text("""
package com.example;

import org.springframework.stereotype.Service;
import java.util.List;
import java.util.ArrayList;

@Service
public class UserService {
    
    /**
     * Get all users from the system.
     * @return List of user names
     */
    public List<String> getUsers() {
        try {
            List<String> users = new ArrayList<>();
            users.add("user1");
            users.add("user2");
            return users;
        } catch (Exception e) {
            throw new RuntimeException("Failed to get users", e);
        }
    }
}
""")
            
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
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.13.2</version>
        </dependency>
    </dependencies>
</project>
""")
            
            # Create HTML/CSS files
            (project_path / "index.html").write_text("""
<!DOCTYPE html>
<html>
<head>
    <title>Test App</title>
    <link rel="stylesheet" href="styles.css">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.0/dist/js/bootstrap.bundle.min.js"></script>
</head>
<body>
    <div class="container">
        <h1>Welcome to Test App</h1>
        <div id="users"></div>
    </div>
    <script src="app.js"></script>
</body>
</html>
""")
            
            (project_path / "styles.css").write_text("""
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

.user-card {
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 0.375rem;
    padding: 1rem;
    margin-bottom: 1rem;
}
""")
            
            # Create configuration files
            (project_path / "docker-compose.yml").write_text("""
version: '3.8'
services:
  app:
    build: .
    ports:
      - "3000:3000"
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: testdb
""")
            
            (project_path / "Dockerfile").write_text("""
FROM node:16
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
""")
            
            yield project_path

    def test_detect_project_languages(self, temp_project):
        """Test language detection."""
        analyzer = MultiLanguageAnalyzer(str(temp_project))
        languages = analyzer.detect_project_languages()
        
        # Should detect multiple languages
        assert len(languages) >= 4
        
        detected_language_names = [lang.language for lang in languages]
        assert LanguageType.PYTHON.value in detected_language_names
        assert LanguageType.JAVASCRIPT.value in detected_language_names
        assert LanguageType.TYPESCRIPT.value in detected_language_names
        assert LanguageType.JAVA.value in detected_language_names
        assert LanguageType.HTML.value in detected_language_names
        assert LanguageType.CSS.value in detected_language_names
        
        # Check Python language info
        python_info = next((lang for lang in languages if lang.language == LanguageType.PYTHON.value), None)
        assert python_info is not None
        assert python_info.file_count >= 1
        assert python_info.line_count > 0
        assert "flask" in python_info.frameworks
        
        # Check JavaScript language info
        js_info = next((lang for lang in languages if lang.language == LanguageType.JAVASCRIPT.value), None)
        assert js_info is not None
        assert js_info.file_count >= 1
        assert "express" in js_info.frameworks or "react" in js_info.frameworks

    def test_analyze_framework_usage(self, temp_project):
        """Test framework detection and analysis."""
        analyzer = MultiLanguageAnalyzer(str(temp_project))
        frameworks = analyzer.analyze_framework_usage()
        
        # Should detect multiple frameworks
        assert len(frameworks) > 0
        
        framework_names = [fw.name for fw in frameworks]
        # Should detect at least some of these frameworks
        expected_frameworks = ["Flask", "Express", "React", "Spring Boot", "Bootstrap"]
        detected_count = sum(1 for fw in expected_frameworks if fw in framework_names)
        assert detected_count > 0

    def test_extract_language_patterns(self, temp_project):
        """Test language-specific pattern extraction."""
        analyzer = MultiLanguageAnalyzer(str(temp_project))
        
        # Test Python patterns
        python_patterns = analyzer.extract_language_patterns(LanguageType.PYTHON)
        assert "naming_patterns" in python_patterns
        assert "import_patterns" in python_patterns
        assert "error_handling_patterns" in python_patterns
        
        # Test JavaScript patterns
        js_patterns = analyzer.extract_language_patterns(LanguageType.JAVASCRIPT)
        assert "naming_patterns" in js_patterns
        assert "import_patterns" in js_patterns

    def test_generate_cross_language_mappings(self, temp_project):
        """Test cross-language mapping generation."""
        analyzer = MultiLanguageAnalyzer(str(temp_project))
        mappings = analyzer.generate_cross_language_mappings()
        
        assert mappings is not None
        assert hasattr(mappings, 'api_interactions')
        assert hasattr(mappings, 'data_flow')
        assert hasattr(mappings, 'shared_configurations')
        assert hasattr(mappings, 'build_dependencies')
        assert hasattr(mappings, 'integration_patterns')

    def test_python_version_detection(self, temp_project):
        """Test Python version detection."""
        # Create pyproject.toml with Python version
        (temp_project / "pyproject.toml").write_text("""
[project]
name = "test-project"
requires-python = ">=3.10"
""")
        
        analyzer = MultiLanguageAnalyzer(str(temp_project))
        languages = analyzer.detect_project_languages()
        
        python_info = next((lang for lang in languages if lang.language == LanguageType.PYTHON.value), None)
        assert python_info is not None
        assert python_info.version == ">=3.10"

    def test_javascript_version_detection(self, temp_project):
        """Test JavaScript version detection."""
        # Update package.json with Node version
        package_json = {
            "name": "test-project",
            "version": "1.0.0",
            "engines": {
                "node": ">=16.0.0"
            },
            "dependencies": {
                "express": "^4.18.0"
            }
        }
        (temp_project / "package.json").write_text(json.dumps(package_json))
        
        analyzer = MultiLanguageAnalyzer(str(temp_project))
        languages = analyzer.detect_project_languages()
        
        js_info = next((lang for lang in languages if lang.language == LanguageType.JAVASCRIPT.value), None)
        assert js_info is not None
        assert js_info.version == ">=16.0.0"

    def test_java_version_detection(self, temp_project):
        """Test Java version detection."""
        # Update pom.xml with Java version
        pom_content = """
<?xml version="1.0" encoding="UTF-8"?>
<project>
    <groupId>com.example</groupId>
    <artifactId>test-project</artifactId>
    <version>1.0.0</version>
    
    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
    </properties>
</project>
"""
        (temp_project / "pom.xml").write_text(pom_content)
        
        analyzer = MultiLanguageAnalyzer(str(temp_project))
        languages = analyzer.detect_project_languages()
        
        java_info = next((lang for lang in languages if lang.language == LanguageType.JAVA.value), None)
        assert java_info is not None
        assert java_info.version == "11"

    def test_file_filtering(self, temp_project):
        """Test that ignored files are properly filtered."""
        # Create files that should be ignored
        (temp_project / "node_modules").mkdir()
        (temp_project / "node_modules" / "test.js").write_text("// should be ignored")
        
        (temp_project / "__pycache__").mkdir()
        (temp_project / "__pycache__" / "test.pyc").write_text("# should be ignored")
        
        (temp_project / ".git").mkdir()
        (temp_project / ".git" / "config").write_text("# should be ignored")
        
        analyzer = MultiLanguageAnalyzer(str(temp_project))
        languages = analyzer.detect_project_languages()
        
        # Should still detect languages from non-ignored files
        detected_language_names = [lang.language for lang in languages]
        assert LanguageType.PYTHON.value in detected_language_names
        assert LanguageType.JAVASCRIPT.value in detected_language_names

    def test_empty_project(self):
        """Test analyzer behavior with empty project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            analyzer = MultiLanguageAnalyzer(temp_dir)
            languages = analyzer.detect_project_languages()
            
            # Should return empty list for empty project
            assert len(languages) == 0

    def test_single_language_project(self):
        """Test analyzer with single-language project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create only Python files
            (project_path / "main.py").write_text("""
def hello():
    print("Hello, World!")

if __name__ == "__main__":
    hello()
""")
            
            analyzer = MultiLanguageAnalyzer(str(project_path))
            languages = analyzer.detect_project_languages()
            
            assert len(languages) == 1
            assert languages[0].language == LanguageType.PYTHON.value
            assert languages[0].file_count == 1

    def test_quality_score_calculation(self, temp_project):
        """Test quality score calculation for different languages."""
        analyzer = MultiLanguageAnalyzer(str(temp_project))
        languages = analyzer.detect_project_languages()
        
        for language_info in languages:
            # Quality score should be between 0 and 1
            assert 0.0 <= language_info.quality_score <= 1.0

    def test_framework_detection_accuracy(self, temp_project):
        """Test accuracy of framework detection."""
        analyzer = MultiLanguageAnalyzer(str(temp_project))
        languages = analyzer.detect_project_languages()
        
        # Check Python frameworks
        python_info = next((lang for lang in languages if lang.language == LanguageType.PYTHON.value), None)
        if python_info:
            assert "flask" in python_info.frameworks
        
        # Check JavaScript frameworks
        js_info = next((lang for lang in languages if lang.language == LanguageType.JAVASCRIPT.value), None)
        if js_info:
            # Should detect either express or react (or both)
            has_expected_framework = any(fw in js_info.frameworks for fw in ["express", "react"])
            assert has_expected_framework

    def test_cross_language_api_detection(self, temp_project):
        """Test detection of cross-language API interactions."""
        analyzer = MultiLanguageAnalyzer(str(temp_project))
        mappings = analyzer.generate_cross_language_mappings()
        
        # Should detect some API interactions
        assert mappings.api_interactions is not None
        
        # Should detect build dependencies
        assert mappings.build_dependencies is not None
        assert len(mappings.build_dependencies) > 0

    def test_configuration_file_analysis(self, temp_project):
        """Test analysis of configuration files."""
        analyzer = MultiLanguageAnalyzer(str(temp_project))
        mappings = analyzer.generate_cross_language_mappings()
        
        # Should detect Docker configuration
        if "docker" in mappings.shared_configurations:
            docker_config = mappings.shared_configurations["docker"]
            assert docker_config is not None
        
        # Should detect package managers
        package_managers = mappings.shared_configurations.get("package_managers", {})
        assert "npm" in package_managers or "python" in package_managers

    def test_integration_pattern_detection(self, temp_project):
        """Test detection of integration patterns."""
        analyzer = MultiLanguageAnalyzer(str(temp_project))
        mappings = analyzer.generate_cross_language_mappings()
        
        # Integration patterns should be a list
        assert isinstance(mappings.integration_patterns, list)
        
        # May detect various patterns depending on project structure
        # This is more of a smoke test to ensure the method runs without error

    def test_language_conventions_analysis(self, temp_project):
        """Test analysis of language-specific conventions."""
        analyzer = MultiLanguageAnalyzer(str(temp_project))
        languages = analyzer.detect_project_languages()
        
        for language_info in languages:
            # Conventions should be a dictionary
            assert isinstance(language_info.conventions, dict)
            
            # Should have consistency score
            if "consistency_score" in language_info.conventions:
                score = language_info.conventions["consistency_score"]
                assert 0.0 <= score <= 1.0

    def test_error_handling_with_invalid_files(self, temp_project):
        """Test error handling with invalid or corrupted files."""
        # Create a file with invalid syntax
        (temp_project / "invalid.py").write_text("def invalid_syntax(:\n    pass")
        
        # Create a binary file with .js extension
        (temp_project / "binary.js").write_bytes(b'\x00\x01\x02\x03')
        
        analyzer = MultiLanguageAnalyzer(str(temp_project))
        
        # Should not crash and should still detect valid languages
        languages = analyzer.detect_project_languages()
        assert len(languages) > 0
        
        # Should handle pattern extraction gracefully
        patterns = analyzer.extract_language_patterns(LanguageType.PYTHON)
        assert patterns is not None