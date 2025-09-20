"""Tests for multi-language project detection and analysis."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from dev_agent.analysis.multi_language_analyzer import MultiLanguageAnalyzer
from dev_agent.models.analysis import LanguageInfo, FrameworkInfo, CrossLanguageMappings


class TestMultiLanguageAnalyzer:
    """Test suite for MultiLanguageAnalyzer."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory with sample files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create Python files
            (project_path / "main.py").write_text("""
import flask
from flask import Flask, request
import pandas as pd

app = Flask(__name__)

@app.route('/api/data')
def get_data():
    return {'message': 'Hello World'}

if __name__ == '__main__':
    app.run()
""")
            
            (project_path / "models.py").write_text("""
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    email = Column(String(100))
""")
            
            # Create JavaScript files
            (project_path / "app.js").write_text("""
const express = require('express');
const app = express();

app.get('/api/users', (req, res) => {
    res.json({ users: [] });
});

app.listen(3000, () => {
    console.log('Server running on port 3000');
});
""")
            
            (project_path / "frontend.js").write_text("""
import React from 'react';
import { useState, useEffect } from 'react';

function UserList() {
    const [users, setUsers] = useState([]);
    
    useEffect(() => {
        fetch('/api/users')
            .then(response => response.json())
            .then(data => setUsers(data.users));
    }, []);
    
    return (
        <div>
            {users.map(user => (
                <div key={user.id}>{user.name}</div>
            ))}
        </div>
    );
}

export default UserList;
""")
            
            # Create TypeScript files
            (project_path / "types.ts").write_text("""
interface User {
    id: number;
    name: string;
    email: string;
}

type UserResponse = {
    users: User[];
    total: number;
};

class UserService {
    async getUsers(): Promise<UserResponse> {
        const response = await fetch('/api/users');
        return response.json();
    }
}

export { User, UserResponse, UserService };
""")
            
            # Create Java files
            (project_path / "User.java").write_text("""
package com.example.model;

import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.Table;

@Entity
@Table(name = "users")
public class User {
    @Id
    private Long id;
    private String name;
    private String email;
    
    // Getters and setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
}
""")
            
            (project_path / "UserController.java").write_text("""
package com.example.controller;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
@RestController
public class UserController {
    
    @GetMapping("/api/users")
    public String getUsers() {
        return "[]";
    }
    
    public static void main(String[] args) {
        SpringApplication.run(UserController.class, args);
    }
}
""")
            
            # Create HTML files
            (project_path / "index.html").write_text("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>User Management</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <nav>
            <ul>
                <li><a href="#home">Home</a></li>
                <li><a href="#users">Users</a></li>
            </ul>
        </nav>
    </header>
    
    <main>
        <section id="user-list">
            <h1>Users</h1>
            <div class="user-container"></div>
        </section>
    </main>
    
    <script src="app.js"></script>
</body>
</html>
""")
            
            # Create CSS files
            (project_path / "styles.css").write_text("""
/* Reset and base styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Arial', sans-serif;
    line-height: 1.6;
    color: #333;
}

/* Header styles */
header {
    background-color: #2c3e50;
    color: white;
    padding: 1rem 0;
}

nav ul {
    list-style: none;
    display: flex;
    justify-content: center;
}

nav li {
    margin: 0 1rem;
}

nav a {
    color: white;
    text-decoration: none;
    transition: color 0.3s ease;
}

nav a:hover {
    color: #3498db;
}

/* Main content */
main {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
}

.user-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1rem;
    margin-top: 1rem;
}

/* Responsive design */
@media (max-width: 768px) {
    nav ul {
        flex-direction: column;
        align-items: center;
    }
    
    nav li {
        margin: 0.5rem 0;
    }
    
    .user-container {
        grid-template-columns: 1fr;
    }
}
""")
            
            # Create configuration files
            (project_path / "package.json").write_text(json.dumps({
                "name": "user-management",
                "version": "1.0.0",
                "dependencies": {
                    "express": "^4.18.0",
                    "react": "^18.2.0",
                    "react-dom": "^18.2.0"
                },
                "devDependencies": {
                    "webpack": "^5.75.0",
                    "babel-loader": "^9.1.0",
                    "@babel/core": "^7.20.0",
                    "jest": "^29.3.0",
                    "eslint": "^8.30.0"
                },
                "scripts": {
                    "start": "node app.js",
                    "build": "webpack",
                    "test": "jest"
                }
            }, indent=2))
            
            (project_path / "requirements.txt").write_text("""
Flask==2.3.0
SQLAlchemy==2.0.0
pandas==2.0.0
pytest==7.4.0
""")
            
            (project_path / "pom.xml").write_text("""
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    
    <groupId>com.example</groupId>
    <artifactId>user-management</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>
    
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.1.0</version>
    </parent>
    
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>
""")
            
            # Create SQL files
            (project_path / "schema.sql").write_text("""
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);

INSERT INTO users (name, email) VALUES 
    ('John Doe', 'john@example.com'),
    ('Jane Smith', 'jane@example.com');
""")
            
            # Create Docker files
            (project_path / "Dockerfile").write_text("""
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
""")
            
            (project_path / "docker-compose.yml").write_text("""
version: '3.8'

services:
  web:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: userdb
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
""")
            
            yield project_path

    @pytest.fixture
    def analyzer(self, temp_project):
        """Create a MultiLanguageAnalyzer instance."""
        return MultiLanguageAnalyzer(str(temp_project))

    def test_detect_project_languages(self, analyzer):
        """Test language detection functionality."""
        languages = analyzer.detect_project_languages()
        
        # Should detect multiple languages
        assert len(languages) > 0
        
        # Check that major languages are detected
        language_names = [lang.language for lang in languages]
        assert 'python' in language_names
        assert 'javascript' in language_names
        assert 'typescript' in language_names
        assert 'java' in language_names
        assert 'html' in language_names
        assert 'css' in language_names
        
        # Check language info structure
        for lang in languages:
            assert isinstance(lang, LanguageInfo)
            assert lang.language is not None
            assert lang.file_count > 0
            assert lang.line_count > 0
            assert isinstance(lang.frameworks, list)
            assert isinstance(lang.conventions, dict)
            assert 0.0 <= lang.quality_score <= 1.0

    def test_analyze_framework_usage(self, analyzer):
        """Test framework detection and analysis."""
        frameworks = analyzer.analyze_framework_usage()
        
        # Should detect frameworks
        assert len(frameworks) > 0
        
        # Check for expected frameworks
        framework_names = [fw.name for fw in frameworks]
        assert 'flask' in framework_names
        assert 'react' in framework_names
        assert 'spring_boot' in framework_names
        
        # Check framework info structure
        for framework in frameworks:
            assert isinstance(framework, FrameworkInfo)
            assert framework.name is not None
            assert framework.version is not None
            assert isinstance(framework.usage_patterns, list)
            assert isinstance(framework.configuration_files, list)
            assert 0.0 <= framework.best_practices_compliance <= 1.0
            assert isinstance(framework.suggested_improvements, list)

    def test_extract_language_patterns(self, analyzer):
        """Test language-specific pattern extraction."""
        # Test Python patterns
        python_files = [str(f) for f in analyzer.project_path.glob('*.py')]
        python_patterns = analyzer.extract_language_patterns('python', python_files)
        
        assert isinstance(python_patterns, dict)
        # Should have extracted some patterns
        assert len(python_patterns) > 0

    def test_generate_cross_language_mappings(self, analyzer):
        """Test cross-language interaction analysis."""
        mappings = analyzer.generate_cross_language_mappings()
        
        assert isinstance(mappings, CrossLanguageMappings)
        assert isinstance(mappings.api_interactions, dict)
        assert isinstance(mappings.data_flow, dict)
        assert isinstance(mappings.shared_configurations, dict)
        assert isinstance(mappings.build_dependencies, dict)
        assert isinstance(mappings.integration_patterns, list)

    def test_get_source_files(self, analyzer):
        """Test source file discovery."""
        source_files = analyzer._get_source_files()
        
        # Should find multiple source files
        assert len(source_files) > 0
        
        # Check file extensions
        extensions = {f.suffix for f in source_files}
        expected_extensions = {'.py', '.js', '.ts', '.java', '.html', '.css', '.sql'}
        assert expected_extensions.issubset(extensions)

    def test_detect_file_language(self, analyzer):
        """Test individual file language detection."""
        # Test various file types
        test_cases = [
            ('test.py', 'python'),
            ('test.js', 'javascript'),
            ('test.ts', 'typescript'),
            ('test.java', 'java'),
            ('test.html', 'html'),
            ('test.css', 'css'),
            ('test.json', 'json'),
            ('test.sql', 'sql'),
            ('Dockerfile', 'dockerfile'),
            ('unknown.xyz', None)
        ]
        
        for filename, expected_language in test_cases:
            file_path = Path(filename)
            detected_language = analyzer._detect_file_language(file_path)
            assert detected_language == expected_language

    def test_detect_python_version(self, analyzer):
        """Test Python version detection."""
        # Create test files with version indicators
        test_files = []
        
        # Test f-string detection (Python 3.6+)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('name = "world"\nprint(f"Hello {name}")')
            test_files.append(f.name)
        
        version = analyzer._detect_python_version(test_files)
        assert version == '3.6+'
        
        # Clean up
        for file_path in test_files:
            Path(file_path).unlink()

    def test_detect_js_version(self, analyzer):
        """Test JavaScript version detection."""
        # Should detect version from package.json if available
        version = analyzer._detect_js_version([])
        # Default version when no specific indicators found
        assert version == 'ES6+'

    def test_framework_detection_python(self, analyzer):
        """Test Python framework detection."""
        python_files = [str(f) for f in analyzer.project_path.glob('*.py')]
        frameworks = analyzer._detect_language_frameworks('python', python_files)
        
        assert 'flask' in frameworks
        assert 'sqlalchemy' in frameworks
        assert 'pandas' in frameworks

    def test_framework_detection_javascript(self, analyzer):
        """Test JavaScript framework detection."""
        js_files = [str(f) for f in analyzer.project_path.glob('*.js')]
        js_files.extend([str(f) for f in analyzer.project_path.glob('package.json')])
        frameworks = analyzer._detect_language_frameworks('javascript', js_files)
        
        assert 'express' in frameworks
        assert 'react' in frameworks
        assert 'nodejs' in frameworks

    def test_framework_detection_java(self, analyzer):
        """Test Java framework detection."""
        java_files = [str(f) for f in analyzer.project_path.glob('*.java')]
        java_files.extend([str(f) for f in analyzer.project_path.glob('pom.xml')])
        frameworks = analyzer._detect_language_frameworks('java', java_files)
        
        assert 'spring_boot' in frameworks
        assert 'maven' in frameworks

    def test_analyze_api_interactions(self, analyzer):
        """Test API interaction analysis."""
        languages = analyzer.detect_project_languages()
        interactions = analyzer._analyze_api_interactions(languages)
        
        assert isinstance(interactions, dict)
        # Should detect REST API patterns
        if 'rest_apis' in interactions:
            assert isinstance(interactions['rest_apis'], dict)

    def test_analyze_shared_configurations(self, analyzer):
        """Test shared configuration analysis."""
        languages = analyzer.detect_project_languages()
        configs = analyzer._analyze_shared_configurations(languages)
        
        assert isinstance(configs, dict)
        # Should find Docker configuration
        assert any('docker' in key.lower() for key in configs.keys())

    def test_analyze_build_dependencies(self, analyzer):
        """Test build dependency analysis."""
        languages = analyzer.detect_project_languages()
        dependencies = analyzer._analyze_build_dependencies(languages)
        
        assert isinstance(dependencies, dict)
        # Should find package.json (npm), requirements.txt (pip), pom.xml (maven)
        assert 'npm/yarn' in dependencies
        assert 'pip' in dependencies
        assert 'maven' in dependencies

    def test_identify_integration_patterns(self, analyzer):
        """Test integration pattern identification."""
        languages = analyzer.detect_project_languages()
        patterns = analyzer._identify_integration_patterns(languages)
        
        assert isinstance(patterns, list)
        # Should identify full-stack pattern
        assert any('full-stack' in pattern.lower() for pattern in patterns)
        # Should identify polyglot architecture
        assert any('polyglot' in pattern.lower() for pattern in patterns)

    def test_language_quality_calculation(self, analyzer):
        """Test language quality score calculation."""
        stats = {
            'file_count': 5,
            'line_count': 500,
            'frameworks': ['flask', 'sqlalchemy']
        }
        
        quality_score = analyzer._calculate_language_quality('python', stats)
        
        assert 0.0 <= quality_score <= 1.0
        # Should be higher than base score due to multiple files and frameworks
        assert quality_score > 0.5

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
            (project_path / "main.py").write_text("print('Hello World')")
            (project_path / "utils.py").write_text("def helper(): pass")
            
            analyzer = MultiLanguageAnalyzer(temp_dir)
            languages = analyzer.detect_project_languages()
            
            assert len(languages) == 1
            assert languages[0].language == 'python'

    def test_error_handling_invalid_files(self, analyzer):
        """Test error handling with invalid or corrupted files."""
        # Create a file with invalid encoding
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.py', delete=False) as f:
            f.write(b'\xff\xfe\x00\x00invalid content')
            invalid_file = f.name
        
        try:
            # Should not crash on invalid files
            languages = analyzer.detect_project_languages()
            assert isinstance(languages, list)
        finally:
            Path(invalid_file).unlink()

    def test_large_project_performance(self):
        """Test analyzer performance with larger project structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create a larger project structure
            for i in range(50):
                (project_path / f"file_{i}.py").write_text(f"# File {i}\ndef function_{i}(): pass")
                (project_path / f"script_{i}.js").write_text(f"// File {i}\nfunction func{i}() {{}}")
            
            analyzer = MultiLanguageAnalyzer(temp_dir)
            
            # Should complete in reasonable time
            import time
            start_time = time.time()
            languages = analyzer.detect_project_languages()
            end_time = time.time()
            
            assert len(languages) >= 2  # At least Python and JavaScript
            assert end_time - start_time < 10  # Should complete within 10 seconds

    def test_framework_version_detection(self, analyzer):
        """Test framework version detection from configuration files."""
        # Test Python framework version detection
        python_files = [str(f) for f in analyzer.project_path.glob('requirements.txt')]
        version = analyzer._detect_python_framework_version('flask', python_files)
        assert version == '==2.3.0'

    def test_cross_language_data_flow_analysis(self, analyzer):
        """Test cross-language data flow analysis."""
        languages = analyzer.detect_project_languages()
        data_flow = analyzer._analyze_cross_language_data_flow(languages)
        
        assert isinstance(data_flow, dict)
        # Should detect shared data formats
        if 'shared_formats' in data_flow:
            assert isinstance(data_flow['shared_formats'], dict)

    def test_find_shared_data_formats(self, analyzer):
        """Test shared data format detection."""
        languages = analyzer.detect_project_languages()
        formats = analyzer._find_shared_data_formats(languages)
        
        assert isinstance(formats, dict)
        # Should find JSON files (package.json)
        assert 'json' in formats
        assert formats['json'] > 0

    def test_find_database_interactions(self, analyzer):
        """Test database interaction pattern detection."""
        languages = analyzer.detect_project_languages()
        interactions = analyzer._find_database_interactions(languages)
        
        assert isinstance(interactions, dict)
        # Should find SQL files
        assert 'sql_files' in interactions
        assert interactions['sql_files'] > 0