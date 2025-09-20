"""Tests for language-specific parsers."""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from dev_agent.analysis.language_parsers import (
    PythonParser,
    JavaScriptParser,
    TypeScriptParser,
    JavaParser,
    HTMLParser,
    CSSParser,
    JSONParser,
    YAMLParser,
    XMLParser,
    SQLParser,
    DockerfileParser,
    ShellParser
)


class TestPythonParser:
    """Test suite for PythonParser."""

    @pytest.fixture
    def parser(self):
        """Create a PythonParser instance."""
        return PythonParser()

    @pytest.fixture
    def sample_python_file(self):
        """Create a sample Python file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
"""Sample Python module for testing."""

import os
import sys
from typing import List, Dict
from collections import defaultdict

class UserManager:
    """Manages user operations."""
    
    def __init__(self, database_url: str):
        """Initialize the user manager.
        
        Args:
            database_url: URL to the database
        """
        self.database_url = database_url
        self.users = []
    
    @property
    def user_count(self) -> int:
        """Get the number of users."""
        return len(self.users)
    
    def add_user(self, name: str, email: str) -> bool:
        """Add a new user.
        
        Args:
            name: User's name
            email: User's email
            
        Returns:
            True if user was added successfully
        """
        try:
            user = {"name": name, "email": email}
            self.users.append(user)
            return True
        except Exception as e:
            print(f"Error adding user: {e}")
            return False

def process_data(data: List[Dict]) -> Dict:
    """Process user data."""
    result = defaultdict(int)
    for item in data:
        result[item.get('type', 'unknown')] += 1
    return dict(result)

async def fetch_users() -> List[Dict]:
    """Fetch users asynchronously."""
    # Simulate async operation
    return []

if __name__ == "__main__":
    manager = UserManager("sqlite:///users.db")
    print(f"User count: {manager.user_count}")
''')
            yield f.name
        
        # Cleanup
        Path(f.name).unlink()

    def test_parse_file(self, parser, sample_python_file):
        """Test Python file parsing."""
        result = parser.parse_file(sample_python_file)
        
        assert result['language'] == 'python'
        assert result['line_count'] > 0
        assert 'symbols' in result
        assert 'imports' in result
        assert 'docstrings' in result
        assert 'decorators' in result
        assert 'type_hints' in result

    def test_extract_symbols(self, parser, sample_python_file):
        """Test Python symbol extraction."""
        symbols = parser.extract_symbols(sample_python_file)
        
        # Should find classes and functions
        symbol_names = [s['name'] for s in symbols]
        assert 'UserManager' in symbol_names
        assert 'process_data' in symbol_names
        assert 'fetch_users' in symbol_names
        
        # Check symbol types
        class_symbols = [s for s in symbols if s['type'] == 'class']
        function_symbols = [s for s in symbols if s['type'] == 'function']
        
        assert len(class_symbols) >= 1
        assert len(function_symbols) >= 2

    def test_analyze_imports(self, parser, sample_python_file):
        """Test Python import analysis."""
        imports = parser.analyze_imports(sample_python_file)
        
        # Should find various import types
        import_modules = [imp.get('module') for imp in imports]
        assert 'os' in import_modules
        assert 'sys' in import_modules
        assert 'typing' in import_modules

    def test_extract_docstrings(self, parser, sample_python_file):
        """Test docstring extraction."""
        with open(sample_python_file, 'r') as f:
            content = f.read()
        
        docstrings = parser._extract_docstrings(content)
        assert len(docstrings) > 0
        assert any('Sample Python module' in doc for doc in docstrings)

    def test_extract_decorators(self, parser, sample_python_file):
        """Test decorator extraction."""
        with open(sample_python_file, 'r') as f:
            content = f.read()
        
        decorators = parser._extract_decorators(content)
        assert 'property' in decorators

    def test_has_type_hints(self, parser, sample_python_file):
        """Test type hint detection."""
        with open(sample_python_file, 'r') as f:
            content = f.read()
        
        has_hints = parser._has_type_hints(content)
        assert has_hints is True


class TestJavaScriptParser:
    """Test suite for JavaScriptParser."""

    @pytest.fixture
    def parser(self):
        """Create a JavaScriptParser instance."""
        return JavaScriptParser()

    @pytest.fixture
    def sample_js_file(self):
        """Create a sample JavaScript file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write('''
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const UserService = {
    async getUsers() {
        const response = await fetch('/api/users');
        return response.json();
    },
    
    createUser: function(userData) {
        return axios.post('/api/users', userData);
    }
};

class UserManager {
    constructor(apiUrl) {
        this.apiUrl = apiUrl;
        this.users = [];
    }
    
    async loadUsers() {
        try {
            this.users = await UserService.getUsers();
        } catch (error) {
            console.error('Failed to load users:', error);
        }
    }
}

function UserList({ users }) {
    const [loading, setLoading] = useState(false);
    
    useEffect(() => {
        setLoading(true);
        // Load users
        setLoading(false);
    }, []);
    
    const handleClick = (user) => {
        console.log('User clicked:', user);
    };
    
    return (
        <div>
            {users.map(user => (
                <div key={user.id} onClick={() => handleClick(user)}>
                    {user.name}
                </div>
            ))}
        </div>
    );
}

const processUsers = (users) => users.filter(u => u.active);

export default UserList;
export { UserManager, UserService };
''')
            yield f.name
        
        Path(f.name).unlink()

    def test_parse_file(self, parser, sample_js_file):
        """Test JavaScript file parsing."""
        result = parser.parse_file(sample_js_file)
        
        assert result['language'] == 'javascript'
        assert result['line_count'] > 0
        assert 'symbols' in result
        assert 'imports' in result
        assert 'exports' in result
        assert 'es6_features' in result
        assert 'jsx' in result

    def test_extract_symbols(self, parser, sample_js_file):
        """Test JavaScript symbol extraction."""
        symbols = parser.extract_symbols(sample_js_file)
        
        symbol_names = [s['name'] for s in symbols]
        assert 'UserManager' in symbol_names
        assert 'UserList' in symbol_names
        assert 'processUsers' in symbol_names

    def test_analyze_imports(self, parser, sample_js_file):
        """Test JavaScript import analysis."""
        imports = parser.analyze_imports(sample_js_file)
        
        # Should find ES6 imports
        assert len(imports) > 0
        import_modules = [imp.get('module') for imp in imports if imp.get('module')]
        assert 'react' in import_modules
        assert 'axios' in import_modules

    def test_detect_es6_features(self, parser, sample_js_file):
        """Test ES6 feature detection."""
        with open(sample_js_file, 'r') as f:
            content = f.read()
        
        features = parser._detect_es6_features(content)
        assert 'arrow_functions' in features
        assert 'const_let' in features
        assert 'classes' in features
        assert 'async_await' in features

    def test_has_jsx(self, parser, sample_js_file):
        """Test JSX detection."""
        with open(sample_js_file, 'r') as f:
            content = f.read()
        
        has_jsx = parser._has_jsx(content)
        assert has_jsx is True


class TestTypeScriptParser:
    """Test suite for TypeScriptParser."""

    @pytest.fixture
    def parser(self):
        """Create a TypeScriptParser instance."""
        return TypeScriptParser()

    @pytest.fixture
    def sample_ts_file(self):
        """Create a sample TypeScript file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
            f.write('''
interface User {
    id: number;
    name: string;
    email: string;
    active?: boolean;
}

type UserResponse = {
    users: User[];
    total: number;
};

enum UserRole {
    ADMIN = 'admin',
    USER = 'user',
    GUEST = 'guest'
}

class UserService<T extends User> {
    private apiUrl: string;
    
    constructor(apiUrl: string) {
        this.apiUrl = apiUrl;
    }
    
    @deprecated
    async getUsers(): Promise<UserResponse> {
        const response = await fetch(`${this.apiUrl}/users`);
        return response.json();
    }
    
    async createUser(user: Omit<User, 'id'>): Promise<User> {
        const response = await fetch(`${this.apiUrl}/users`, {
            method: 'POST',
            body: JSON.stringify(user)
        });
        return response.json();
    }
}

function processUsers<T extends User>(users: T[]): T[] {
    return users.filter(user => user.active !== false);
}

export { User, UserResponse, UserService, UserRole };
export default processUsers;
''')
            yield f.name
        
        Path(f.name).unlink()

    def test_parse_file(self, parser, sample_ts_file):
        """Test TypeScript file parsing."""
        result = parser.parse_file(sample_ts_file)
        
        assert result['language'] == 'typescript'
        assert result['line_count'] > 0
        assert 'symbols' in result
        assert 'imports' in result
        assert 'interfaces' in result
        assert 'types' in result
        assert 'generics' in result
        assert 'decorators' in result

    def test_extract_symbols(self, parser, sample_ts_file):
        """Test TypeScript symbol extraction."""
        symbols = parser.extract_symbols(sample_ts_file)
        
        symbol_names = [s['name'] for s in symbols]
        symbol_types = [s['type'] for s in symbols]
        
        assert 'User' in symbol_names
        assert 'UserService' in symbol_names
        assert 'UserRole' in symbol_names
        assert 'processUsers' in symbol_names
        
        assert 'interface' in symbol_types
        assert 'enum' in symbol_types
        assert 'type_alias' in symbol_types

    def test_extract_interfaces(self, parser, sample_ts_file):
        """Test TypeScript interface extraction."""
        with open(sample_ts_file, 'r') as f:
            content = f.read()
        
        interfaces = parser._extract_interfaces(content)
        assert len(interfaces) > 0
        
        user_interface = next((i for i in interfaces if i['name'] == 'User'), None)
        assert user_interface is not None
        assert len(user_interface['properties']) > 0

    def test_extract_types(self, parser, sample_ts_file):
        """Test TypeScript type alias extraction."""
        with open(sample_ts_file, 'r') as f:
            content = f.read()
        
        types = parser._extract_types(content)
        assert len(types) > 0
        
        user_response_type = next((t for t in types if t['name'] == 'UserResponse'), None)
        assert user_response_type is not None

    def test_has_generics(self, parser, sample_ts_file):
        """Test generic type detection."""
        with open(sample_ts_file, 'r') as f:
            content = f.read()
        
        has_generics = parser._has_generics(content)
        assert has_generics is True

    def test_extract_decorators(self, parser, sample_ts_file):
        """Test TypeScript decorator extraction."""
        with open(sample_ts_file, 'r') as f:
            content = f.read()
        
        decorators = parser._extract_decorators(content)
        assert 'deprecated' in decorators


class TestJavaParser:
    """Test suite for JavaParser."""

    @pytest.fixture
    def parser(self):
        """Create a JavaParser instance."""
        return JavaParser()

    @pytest.fixture
    def sample_java_file(self):
        """Create a sample Java file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write('''
package com.example.service;

import java.util.List;
import java.util.ArrayList;
import javax.persistence.Entity;
import javax.persistence.Id;
import org.springframework.stereotype.Service;

@Entity
@Service
public class UserService {
    
    @Id
    private Long id;
    private String name;
    
    public UserService() {
        // Default constructor
    }
    
    public UserService(String name) {
        this.name = name;
    }
    
    public List<String> getUsers() throws ServiceException {
        List<String> users = new ArrayList<>();
        try {
            // Fetch users from database
            return users;
        } catch (Exception e) {
            throw new ServiceException("Failed to fetch users", e);
        }
    }
    
    private void validateUser(String user) {
        if (user == null || user.isEmpty()) {
            throw new IllegalArgumentException("User cannot be null or empty");
        }
    }
    
    protected static boolean isValidEmail(String email) {
        return email != null && email.contains("@");
    }
}

interface UserRepository {
    List<String> findAll();
    void save(String user);
}

abstract class BaseService {
    protected abstract void initialize();
}
''')
            yield f.name
        
        Path(f.name).unlink()

    def test_parse_file(self, parser, sample_java_file):
        """Test Java file parsing."""
        result = parser.parse_file(sample_java_file)
        
        assert result['language'] == 'java'
        assert result['line_count'] > 0
        assert 'symbols' in result
        assert 'imports' in result
        assert 'package' in result
        assert 'annotations' in result
        assert 'access_modifiers' in result

    def test_extract_symbols(self, parser, sample_java_file):
        """Test Java symbol extraction."""
        symbols = parser.extract_symbols(sample_java_file)
        
        symbol_names = [s['name'] for s in symbols]
        symbol_types = [s['type'] for s in symbols]
        
        assert 'UserService' in symbol_names
        assert 'UserRepository' in symbol_names
        assert 'BaseService' in symbol_names
        assert 'getUsers' in symbol_names
        
        assert 'class' in symbol_types
        assert 'interface' in symbol_types
        assert 'method' in symbol_types

    def test_analyze_imports(self, parser, sample_java_file):
        """Test Java import analysis."""
        imports = parser.analyze_imports(sample_java_file)
        
        import_modules = [imp['module'] for imp in imports]
        assert 'java.util.List' in import_modules
        assert 'javax.persistence.Entity' in import_modules
        assert 'org.springframework.stereotype.Service' in import_modules

    def test_extract_package(self, parser, sample_java_file):
        """Test Java package extraction."""
        with open(sample_java_file, 'r') as f:
            content = f.read()
        
        package = parser._extract_package(content)
        assert package == 'com.example.service'

    def test_extract_annotations(self, parser, sample_java_file):
        """Test Java annotation extraction."""
        with open(sample_java_file, 'r') as f:
            content = f.read()
        
        annotations = parser._extract_annotations(content)
        assert 'Entity' in annotations
        assert 'Service' in annotations
        assert 'Id' in annotations

    def test_analyze_access_modifiers(self, parser, sample_java_file):
        """Test Java access modifier analysis."""
        with open(sample_java_file, 'r') as f:
            content = f.read()
        
        modifiers = parser._analyze_access_modifiers(content)
        assert modifiers['public'] > 0
        assert modifiers['private'] > 0
        assert modifiers['protected'] > 0


class TestHTMLParser:
    """Test suite for HTMLParser."""

    @pytest.fixture
    def parser(self):
        """Create an HTMLParser instance."""
        return HTMLParser()

    @pytest.fixture
    def sample_html_file(self):
        """Create a sample HTML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>User Management</title>
    <link rel="stylesheet" href="styles.css">
    <script src="app.js"></script>
</head>
<body>
    <header id="main-header" class="header primary">
        <nav class="navigation">
            <ul class="nav-list">
                <li><a href="#home">Home</a></li>
                <li><a href="#users">Users</a></li>
            </ul>
        </nav>
    </header>
    
    <main class="main-content">
        <section id="user-section" class="content-section">
            <h1>User Management</h1>
            <div class="user-list" data-testid="user-list">
                <!-- Users will be loaded here -->
            </div>
        </section>
    </main>
    
    <script>
        console.log('Page loaded');
        document.addEventListener('DOMContentLoaded', function() {
            // Initialize app
        });
    </script>
    
    <style>
        .header { background: #333; }
        .primary { color: white; }
    </style>
</body>
</html>
''')
            yield f.name
        
        Path(f.name).unlink()

    def test_parse_file(self, parser, sample_html_file):
        """Test HTML file parsing."""
        result = parser.parse_file(sample_html_file)
        
        assert result['language'] == 'html'
        assert result['line_count'] > 0
        assert 'symbols' in result
        assert 'imports' in result
        assert 'elements' in result
        assert 'scripts' in result
        assert 'styles' in result

    def test_extract_symbols(self, parser, sample_html_file):
        """Test HTML symbol extraction."""
        symbols = parser.extract_symbols(sample_html_file)
        
        symbol_names = [s['name'] for s in symbols]
        symbol_types = [s['type'] for s in symbols]
        
        # Should find IDs and classes
        assert 'main-header' in symbol_names
        assert 'user-section' in symbol_names
        assert 'header' in symbol_names
        assert 'navigation' in symbol_names
        
        assert 'id' in symbol_types
        assert 'class' in symbol_types

    def test_analyze_imports(self, parser, sample_html_file):
        """Test HTML import analysis."""
        imports = parser.analyze_imports(sample_html_file)
        
        import_modules = [imp['module'] for imp in imports]
        import_types = [imp['type'] for imp in imports]
        
        assert 'styles.css' in import_modules
        assert 'app.js' in import_modules
        assert 'stylesheet' in import_types
        assert 'script' in import_types

    def test_extract_elements(self, parser, sample_html_file):
        """Test HTML element extraction."""
        with open(sample_html_file, 'r') as f:
            content = f.read()
        
        elements = parser._extract_elements(content)
        
        # Should count various HTML elements
        assert 'html' in elements
        assert 'head' in elements
        assert 'body' in elements
        assert 'div' in elements
        assert elements['div'] > 0

    def test_extract_scripts(self, parser, sample_html_file):
        """Test inline script extraction."""
        with open(sample_html_file, 'r') as f:
            content = f.read()
        
        scripts = parser._extract_scripts(content)
        assert len(scripts) > 0
        assert any('console.log' in script['content'] for script in scripts)

    def test_extract_styles(self, parser, sample_html_file):
        """Test inline style extraction."""
        with open(sample_html_file, 'r') as f:
            content = f.read()
        
        styles = parser._extract_styles(content)
        assert len(styles) > 0
        assert any('.header' in style['content'] for style in styles)


class TestCSSParser:
    """Test suite for CSSParser."""

    @pytest.fixture
    def parser(self):
        """Create a CSSParser instance."""
        return CSSParser()

    @pytest.fixture
    def sample_css_file(self):
        """Create a sample CSS file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.css', delete=False) as f:
            f.write('''
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');

/* Reset styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Roboto', sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f4f4f4;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

.header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem 0;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.nav-list {
    display: flex;
    list-style: none;
    gap: 2rem;
}

.nav-list li a {
    color: white;
    text-decoration: none;
    transition: opacity 0.3s ease;
}

.nav-list li a:hover {
    opacity: 0.8;
}

#main-content {
    padding: 2rem 0;
}

.user-card {
    background: white;
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    transition: transform 0.2s ease;
}

.user-card:hover {
    transform: translateY(-2px);
}

@media (max-width: 768px) {
    .container {
        padding: 0 10px;
    }
    
    .nav-list {
        flex-direction: column;
        gap: 1rem;
    }
    
    .user-card {
        padding: 1rem;
    }
}

@media (min-width: 1200px) {
    .container {
        max-width: 1400px;
    }
}
''')
            yield f.name
        
        Path(f.name).unlink()

    def test_parse_file(self, parser, sample_css_file):
        """Test CSS file parsing."""
        result = parser.parse_file(sample_css_file)
        
        assert result['language'] == 'css'
        assert result['line_count'] > 0
        assert 'symbols' in result
        assert 'imports' in result
        assert 'selectors' in result
        assert 'properties' in result
        assert 'media_queries' in result

    def test_extract_symbols(self, parser, sample_css_file):
        """Test CSS symbol extraction."""
        symbols = parser.extract_symbols(sample_css_file)
        
        symbol_names = [s['name'] for s in symbols]
        
        # Should find various selectors
        assert any('body' in name for name in symbol_names)
        assert any('.container' in name for name in symbol_names)
        assert any('.header' in name for name in symbol_names)
        assert any('#main-content' in name for name in symbol_names)

    def test_analyze_imports(self, parser, sample_css_file):
        """Test CSS import analysis."""
        imports = parser.analyze_imports(sample_css_file)
        
        # Should find @import statements
        assert len(imports) > 0
        import_modules = [imp['module'] for imp in imports]
        assert any('fonts.googleapis.com' in module for module in import_modules)

    def test_extract_selectors(self, parser, sample_css_file):
        """Test CSS selector extraction."""
        with open(sample_css_file, 'r') as f:
            content = f.read()
        
        selectors = parser._extract_selectors(content)
        
        # Should find various selector types
        assert any('body' in selector for selector in selectors)
        assert any('.container' in selector for selector in selectors)
        assert any('#main-content' in selector for selector in selectors)

    def test_extract_properties(self, parser, sample_css_file):
        """Test CSS property extraction."""
        with open(sample_css_file, 'r') as f:
            content = f.read()
        
        properties = parser._extract_properties(content)
        
        # Should count property usage
        assert 'margin' in properties
        assert 'padding' in properties
        assert 'background' in properties
        assert 'color' in properties
        assert properties['margin'] > 0

    def test_extract_media_queries(self, parser, sample_css_file):
        """Test media query extraction."""
        with open(sample_css_file, 'r') as f:
            content = f.read()
        
        media_queries = parser._extract_media_queries(content)
        
        assert len(media_queries) > 0
        assert any('max-width: 768px' in query for query in media_queries)
        assert any('min-width: 1200px' in query for query in media_queries)


class TestJSONParser:
    """Test suite for JSONParser."""

    @pytest.fixture
    def parser(self):
        """Create a JSONParser instance."""
        return JSONParser()

    @pytest.fixture
    def sample_json_file(self):
        """Create a sample JSON file."""
        data = {
            "name": "user-management",
            "version": "1.0.0",
            "description": "A user management application",
            "main": "app.js",
            "scripts": {
                "start": "node app.js",
                "test": "jest",
                "build": "webpack"
            },
            "dependencies": {
                "express": "^4.18.0",
                "react": "^18.2.0",
                "axios": "^1.3.0"
            },
            "devDependencies": {
                "jest": "^29.3.0",
                "webpack": "^5.75.0"
            },
            "keywords": ["user", "management", "api"],
            "author": "Test Author",
            "license": "MIT"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f, indent=2)
            yield f.name
        
        Path(f.name).unlink()

    def test_parse_file(self, parser, sample_json_file):
        """Test JSON file parsing."""
        result = parser.parse_file(sample_json_file)
        
        assert result['language'] == 'json'
        assert result['line_count'] > 0
        assert 'symbols' in result
        assert 'imports' in result
        assert 'structure' in result
        assert 'keys' in result

    def test_extract_symbols(self, parser, sample_json_file):
        """Test JSON symbol extraction."""
        symbols = parser.extract_symbols(sample_json_file)
        
        symbol_names = [s['name'] for s in symbols]
        
        # Should find top-level keys
        assert 'name' in symbol_names
        assert 'version' in symbol_names
        assert 'dependencies' in symbol_names
        assert 'scripts.start' in symbol_names

    def test_analyze_structure(self, parser, sample_json_file):
        """Test JSON structure analysis."""
        with open(sample_json_file, 'r') as f:
            data = json.load(f)
        
        structure = parser._analyze_structure(data)
        
        assert structure['type'] == 'object'
        assert structure['keys'] > 0
        assert structure['nested_objects'] > 0

    def test_extract_keys(self, parser, sample_json_file):
        """Test JSON key extraction."""
        with open(sample_json_file, 'r') as f:
            data = json.load(f)
        
        keys = parser._extract_keys(data)
        
        assert 'name' in keys
        assert 'scripts.start' in keys
        assert 'dependencies.express' in keys


class TestYAMLParser:
    """Test suite for YAMLParser."""

    @pytest.fixture
    def parser(self):
        """Create a YAMLParser instance."""
        return YAMLParser()

    @pytest.fixture
    def sample_yaml_file(self):
        """Create a sample YAML file."""
        data = {
            'version': '3.8',
            'services': {
                'web': {
                    'build': '.',
                    'ports': ['3000:3000'],
                    'environment': {
                        'NODE_ENV': 'production',
                        'DATABASE_URL': 'postgres://localhost/mydb'
                    },
                    'depends_on': ['db']
                },
                'db': {
                    'image': 'postgres:13',
                    'environment': {
                        'POSTGRES_DB': 'mydb',
                        'POSTGRES_USER': 'user',
                        'POSTGRES_PASSWORD': 'password'
                    },
                    'volumes': ['postgres_data:/var/lib/postgresql/data']
                }
            },
            'volumes': {
                'postgres_data': None
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(data, f, default_flow_style=False)
            yield f.name
        
        Path(f.name).unlink()

    def test_parse_file(self, parser, sample_yaml_file):
        """Test YAML file parsing."""
        result = parser.parse_file(sample_yaml_file)
        
        assert result['language'] == 'yaml'
        assert result['line_count'] > 0
        assert 'symbols' in result
        assert 'imports' in result
        assert 'structure' in result
        assert 'keys' in result

    def test_extract_symbols(self, parser, sample_yaml_file):
        """Test YAML symbol extraction."""
        symbols = parser.extract_symbols(sample_yaml_file)
        
        symbol_names = [s['name'] for s in symbols]
        
        # Should find keys at various levels
        assert 'version' in symbol_names
        assert 'services' in symbol_names
        assert 'services.web' in symbol_names
        assert 'services.web.build' in symbol_names

    def test_analyze_structure(self, parser, sample_yaml_file):
        """Test YAML structure analysis."""
        with open(sample_yaml_file, 'r') as f:
            data = yaml.safe_load(f)
        
        structure = parser._analyze_structure(data)
        
        assert structure['type'] == 'mapping'
        assert structure['keys'] > 0
        assert structure['nested_mappings'] > 0


class TestSQLParser:
    """Test suite for SQLParser."""

    @pytest.fixture
    def parser(self):
        """Create an SQLParser instance."""
        return SQLParser()

    @pytest.fixture
    def sample_sql_file(self):
        """Create a sample SQL file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
            f.write('''
-- User management database schema

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    bio TEXT,
    avatar_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);

-- Insert sample data
INSERT INTO users (name, email, password_hash) VALUES 
    ('John Doe', 'john@example.com', 'hashed_password_1'),
    ('Jane Smith', 'jane@example.com', 'hashed_password_2'),
    ('Bob Johnson', 'bob@example.com', 'hashed_password_3');

-- Sample queries
SELECT u.name, u.email, p.bio 
FROM users u 
LEFT JOIN user_profiles p ON u.id = p.user_id 
WHERE u.created_at > '2023-01-01';

UPDATE users 
SET updated_at = CURRENT_TIMESTAMP 
WHERE id = 1;

DELETE FROM users 
WHERE created_at < '2022-01-01';

-- Create a function
CREATE OR REPLACE FUNCTION get_user_count() 
RETURNS INTEGER AS $$
BEGIN
    RETURN (SELECT COUNT(*) FROM users);
END;
$$ LANGUAGE plpgsql;

-- Create a view
CREATE VIEW active_users AS
SELECT id, name, email
FROM users
WHERE created_at > CURRENT_DATE - INTERVAL '30 days';
''')
            yield f.name
        
        Path(f.name).unlink()

    def test_parse_file(self, parser, sample_sql_file):
        """Test SQL file parsing."""
        result = parser.parse_file(sample_sql_file)
        
        assert result['language'] == 'sql'
        assert result['line_count'] > 0
        assert 'symbols' in result
        assert 'imports' in result
        assert 'statements' in result
        assert 'tables' in result
        assert 'functions' in result

    def test_extract_symbols(self, parser, sample_sql_file):
        """Test SQL symbol extraction."""
        symbols = parser.extract_symbols(sample_sql_file)
        
        symbol_names = [s['name'] for s in symbols]
        symbol_types = [s['type'] for s in symbols]
        
        # Should find tables and functions
        assert 'users' in symbol_names
        assert 'user_profiles' in symbol_names
        assert 'get_user_count' in symbol_names
        
        assert 'table' in symbol_types
        assert 'function' in symbol_types

    def test_extract_statements(self, parser, sample_sql_file):
        """Test SQL statement extraction."""
        with open(sample_sql_file, 'r') as f:
            content = f.read()
        
        statements = parser._extract_statements(content)
        
        # Should count different statement types
        assert 'CREATE' in statements
        assert 'INSERT' in statements
        assert 'SELECT' in statements
        assert 'UPDATE' in statements
        assert 'DELETE' in statements
        
        assert statements['CREATE'] > 0
        assert statements['INSERT'] > 0

    def test_extract_tables(self, parser, sample_sql_file):
        """Test SQL table extraction."""
        with open(sample_sql_file, 'r') as f:
            content = f.read()
        
        tables = parser._extract_tables(content)
        
        assert 'users' in tables
        assert 'user_profiles' in tables

    def test_extract_functions(self, parser, sample_sql_file):
        """Test SQL function extraction."""
        with open(sample_sql_file, 'r') as f:
            content = f.read()
        
        functions = parser._extract_functions(content)
        
        assert 'get_user_count' in functions


class TestDockerfileParser:
    """Test suite for DockerfileParser."""

    @pytest.fixture
    def parser(self):
        """Create a DockerfileParser instance."""
        return DockerfileParser()

    @pytest.fixture
    def sample_dockerfile(self):
        """Create a sample Dockerfile."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='', delete=False) as f:
            f.write('''
# Use official Node.js runtime as base image
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# Change ownership of app directory
RUN chown -R nextjs:nodejs /app
USER nextjs

# Expose port
EXPOSE 3000

# Set environment variables
ENV NODE_ENV=production
ENV PORT=3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Start the application
CMD ["npm", "start"]
''')
            yield f.name
        
        Path(f.name).unlink()

    def test_parse_file(self, parser, sample_dockerfile):
        """Test Dockerfile parsing."""
        result = parser.parse_file(sample_dockerfile)
        
        assert result['language'] == 'dockerfile'
        assert result['line_count'] > 0
        assert 'symbols' in result
        assert 'imports' in result
        assert 'instructions' in result
        assert 'base_images' in result
        assert 'ports' in result

    def test_analyze_imports(self, parser, sample_dockerfile):
        """Test Dockerfile base image analysis."""
        imports = parser.analyze_imports(sample_dockerfile)
        
        # Should find FROM statements
        assert len(imports) > 0
        import_modules = [imp['module'] for imp in imports]
        assert 'node:18-alpine' in import_modules

    def test_extract_instructions(self, parser, sample_dockerfile):
        """Test Dockerfile instruction extraction."""
        with open(sample_dockerfile, 'r') as f:
            content = f.read()
        
        instructions = parser._extract_instructions(content)
        
        # Should count different instruction types
        assert 'FROM' in instructions
        assert 'RUN' in instructions
        assert 'COPY' in instructions
        assert 'EXPOSE' in instructions
        assert 'CMD' in instructions
        
        assert instructions['RUN'] > 0
        assert instructions['COPY'] > 0

    def test_extract_base_images(self, parser, sample_dockerfile):
        """Test base image extraction."""
        with open(sample_dockerfile, 'r') as f:
            content = f.read()
        
        base_images = parser._extract_base_images(content)
        
        assert 'node:18-alpine' in base_images

    def test_extract_ports(self, parser, sample_dockerfile):
        """Test port extraction."""
        with open(sample_dockerfile, 'r') as f:
            content = f.read()
        
        ports = parser._extract_ports(content)
        
        assert '3000' in ports


class TestShellParser:
    """Test suite for ShellParser."""

    @pytest.fixture
    def parser(self):
        """Create a ShellParser instance."""
        return ShellParser()

    @pytest.fixture
    def sample_shell_file(self):
        """Create a sample shell script."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write('''#!/bin/bash

# User management deployment script

set -e

# Configuration
APP_NAME="user-management"
DOCKER_IMAGE="$APP_NAME:latest"
CONTAINER_NAME="$APP_NAME-container"
PORT=3000

# Source environment variables
source .env

# Functions
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "Docker is not installed"
        exit 1
    fi
}

build_image() {
    echo "Building Docker image..."
    docker build -t "$DOCKER_IMAGE" .
}

stop_container() {
    if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        echo "Stopping existing container..."
        docker stop "$CONTAINER_NAME"
        docker rm "$CONTAINER_NAME"
    fi
}

start_container() {
    echo "Starting new container..."
    docker run -d \
        --name "$CONTAINER_NAME" \
        -p "$PORT:3000" \
        -e NODE_ENV=production \
        "$DOCKER_IMAGE"
}

cleanup() {
    echo "Cleaning up old images..."
    docker image prune -f
}

# Main deployment process
main() {
    echo "Starting deployment of $APP_NAME"
    
    check_docker
    build_image
    stop_container
    start_container
    cleanup
    
    echo "Deployment completed successfully!"
    echo "Application is running on port $PORT"
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
''')
            yield f.name
        
        Path(f.name).unlink()

    def test_parse_file(self, parser, sample_shell_file):
        """Test shell script parsing."""
        result = parser.parse_file(sample_shell_file)
        
        assert result['language'] == 'shell'
        assert result['line_count'] > 0
        assert 'symbols' in result
        assert 'imports' in result
        assert 'functions' in result
        assert 'variables' in result
        assert 'commands' in result

    def test_extract_symbols(self, parser, sample_shell_file):
        """Test shell script symbol extraction."""
        symbols = parser.extract_symbols(sample_shell_file)
        
        symbol_names = [s['name'] for s in symbols]
        symbol_types = [s['type'] for s in symbols]
        
        # Should find functions and variables
        assert 'check_docker' in symbol_names
        assert 'build_image' in symbol_names
        assert 'main' in symbol_names
        assert 'APP_NAME' in symbol_names
        assert 'PORT' in symbol_names
        
        assert 'function' in symbol_types
        assert 'variable' in symbol_types

    def test_analyze_imports(self, parser, sample_shell_file):
        """Test shell script import analysis."""
        imports = parser.analyze_imports(sample_shell_file)
        
        # Should find source statements
        import_modules = [imp['module'] for imp in imports]
        assert '.env' in import_modules

    def test_extract_functions(self, parser, sample_shell_file):
        """Test shell function extraction."""
        with open(sample_shell_file, 'r') as f:
            content = f.read()
        
        functions = parser._extract_functions(content)
        
        assert 'check_docker' in functions
        assert 'build_image' in functions
        assert 'main' in functions

    def test_extract_variables(self, parser, sample_shell_file):
        """Test shell variable extraction."""
        with open(sample_shell_file, 'r') as f:
            content = f.read()
        
        variables = parser._extract_variables(content)
        
        assert 'APP_NAME' in variables
        assert 'DOCKER_IMAGE' in variables
        assert 'PORT' in variables

    def test_extract_commands(self, parser, sample_shell_file):
        """Test shell command extraction."""
        with open(sample_shell_file, 'r') as f:
            content = f.read()
        
        commands = parser._extract_commands(content)
        
        # Should find common commands
        assert 'echo' in commands
        assert 'docker' in commands
        assert commands['echo'] > 0
        assert commands['docker'] > 0