"""Tests for framework detection functionality."""

import json
import tempfile
from pathlib import Path

import pytest

from dev_agent.analysis.framework_detectors import (
    PythonFrameworkDetector,
    JavaScriptFrameworkDetector,
    TypeScriptFrameworkDetector,
    JavaFrameworkDetector,
    WebFrameworkDetector
)
from dev_agent.models.analysis import FrameworkInfo, UsagePattern


class TestPythonFrameworkDetector:
    """Test suite for PythonFrameworkDetector."""

    @pytest.fixture
    def detector(self):
        """Create a PythonFrameworkDetector instance."""
        return PythonFrameworkDetector()

    @pytest.fixture
    def sample_flask_files(self):
        """Create sample Flask application files."""
        files = []
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Flask app file
            app_file = temp_path / "app.py"
            app_file.write_text('''
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

@app.route('/api/users', methods=['GET'])
def get_users():
    return jsonify({'users': []})

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()
    return jsonify({'message': 'User created'})

if __name__ == '__main__':
    app.run(debug=True)
''')
            files.append(str(app_file))
            
            # Requirements file
            req_file = temp_path / "requirements.txt"
            req_file.write_text('''
Flask==2.3.0
Flask-SQLAlchemy==3.0.0
pytest==7.4.0
pandas==2.0.0
''')
            files.append(str(req_file))
            
            yield files

    @pytest.fixture
    def sample_django_files(self):
        """Create sample Django application files."""
        files = []
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Django settings
            settings_file = temp_path / "settings.py"
            settings_file.write_text('''
import os
from django.conf import settings

DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'myapp',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
''')
            files.append(str(settings_file))
            
            # Django models
            models_file = temp_path / "models.py"
            models_file.write_text('''
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"
''')
            files.append(str(models_file))
            
            # Django views
            views_file = temp_path / "views.py"
            views_file.write_text('''
from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from .models import UserProfile

class UserListView(View):
    def get(self, request):
        profiles = UserProfile.objects.all()
        return JsonResponse({'users': list(profiles.values())})
''')
            files.append(str(views_file))
            
            yield files

    def test_detect_flask_framework(self, detector, sample_flask_files):
        """Test Flask framework detection."""
        frameworks = detector.detect_frameworks(sample_flask_files)
        
        assert 'flask' in frameworks
        assert 'sqlalchemy' in frameworks
        assert 'pytest' in frameworks
        assert 'pandas' in frameworks

    def test_detect_django_framework(self, detector, sample_django_files):
        """Test Django framework detection."""
        frameworks = detector.detect_frameworks(sample_django_files)
        
        assert 'django' in frameworks

    def test_analyze_flask_framework(self, detector, sample_flask_files):
        """Test Flask framework analysis."""
        framework_info = detector.analyze_framework('flask', sample_flask_files)
        
        assert isinstance(framework_info, FrameworkInfo)
        assert framework_info.name == 'flask'
        assert len(framework_info.usage_patterns) > 0
        assert 0.0 <= framework_info.best_practices_compliance <= 1.0
        
        # Check for Flask-specific patterns
        pattern_names = [p.pattern for p in framework_info.usage_patterns]
        assert any('@app.route' in pattern for pattern in pattern_names)

    def test_analyze_django_framework(self, detector, sample_django_files):
        """Test Django framework analysis."""
        framework_info = detector.analyze_framework('django', sample_django_files)
        
        assert isinstance(framework_info, FrameworkInfo)
        assert framework_info.name == 'django'
        assert len(framework_info.usage_patterns) > 0
        
        # Check for Django-specific patterns
        pattern_names = [p.pattern for p in framework_info.usage_patterns]
        assert any('django' in pattern for pattern in pattern_names)

    def test_detect_python_framework_version(self, detector, sample_flask_files):
        """Test Python framework version detection."""
        version = detector._detect_python_framework_version('flask', sample_flask_files)
        
        assert version == '==2.3.0'

    def test_calculate_flask_compliance(self, detector):
        """Test Flask compliance calculation."""
        patterns = [
            UsagePattern(pattern='@app.route', file_path='app.py', occurrences=2, examples=[]),
            UsagePattern(pattern='Flask(__name__)', file_path='app.py', occurrences=1, examples=[])
        ]
        
        compliance = detector._calculate_flask_compliance(patterns)
        
        assert 0.0 <= compliance <= 1.0
        assert compliance > 0.5  # Should be higher due to route patterns

    def test_suggest_flask_improvements(self, detector):
        """Test Flask improvement suggestions."""
        patterns = [
            UsagePattern(pattern='@app.route', file_path='app.py', occurrences=10, examples=[])
        ]
        
        improvements = detector._suggest_flask_improvements(patterns)
        
        # Should suggest blueprints for many routes
        assert len(improvements) > 0
        assert any('Blueprint' in imp.description for imp in improvements)

    def test_unknown_framework(self, detector, sample_flask_files):
        """Test handling of unknown framework."""
        framework_info = detector.analyze_framework('unknown_framework', sample_flask_files)
        
        assert framework_info is None


class TestJavaScriptFrameworkDetector:
    """Test suite for JavaScriptFrameworkDetector."""

    @pytest.fixture
    def detector(self):
        """Create a JavaScriptFrameworkDetector instance."""
        return JavaScriptFrameworkDetector()

    @pytest.fixture
    def sample_react_files(self):
        """Create sample React application files."""
        files = []
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Package.json
            package_file = temp_path / "package.json"
            package_data = {
                "name": "react-app",
                "version": "1.0.0",
                "dependencies": {
                    "react": "^18.2.0",
                    "react-dom": "^18.2.0",
                    "axios": "^1.3.0"
                },
                "devDependencies": {
                    "webpack": "^5.75.0",
                    "babel-loader": "^9.1.0",
                    "@babel/core": "^7.20.0",
                    "jest": "^29.3.0",
                    "eslint": "^8.30.0"
                }
            }
            package_file.write_text(json.dumps(package_data, indent=2))
            files.append(str(package_file))
            
            # React component
            component_file = temp_path / "UserList.jsx"
            component_file.write_text('''
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function UserList() {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(false);
    
    useEffect(() => {
        const fetchUsers = async () => {
            setLoading(true);
            try {
                const response = await axios.get('/api/users');
                setUsers(response.data.users);
            } catch (error) {
                console.error('Failed to fetch users:', error);
            } finally {
                setLoading(false);
            }
        };
        
        fetchUsers();
    }, []);
    
    if (loading) {
        return <div>Loading...</div>;
    }
    
    return (
        <div className="user-list">
            <h2>Users</h2>
            {users.map(user => (
                <div key={user.id} className="user-item">
                    <h3>{user.name}</h3>
                    <p>{user.email}</p>
                </div>
            ))}
        </div>
    );
}

export default UserList;
''')
            files.append(str(component_file))
            
            yield files

    @pytest.fixture
    def sample_express_files(self):
        """Create sample Express application files."""
        files = []
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Express server
            server_file = temp_path / "server.js"
            server_file.write_text('''
const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(express.static('public'));

// Routes
app.get('/api/users', (req, res) => {
    res.json({ users: [] });
});

app.post('/api/users', (req, res) => {
    const userData = req.body;
    // Process user data
    res.status(201).json({ message: 'User created', user: userData });
});

app.put('/api/users/:id', (req, res) => {
    const userId = req.params.id;
    const userData = req.body;
    res.json({ message: 'User updated', id: userId });
});

app.delete('/api/users/:id', (req, res) => {
    const userId = req.params.id;
    res.json({ message: 'User deleted', id: userId });
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({ error: 'Something went wrong!' });
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
''')
            files.append(str(server_file))
            
            # Package.json for Express
            package_file = temp_path / "package.json"
            package_data = {
                "name": "express-api",
                "version": "1.0.0",
                "main": "server.js",
                "dependencies": {
                    "express": "^4.18.0",
                    "cors": "^2.8.5",
                    "body-parser": "^1.20.0"
                },
                "devDependencies": {
                    "jest": "^29.3.0",
                    "supertest": "^6.3.0"
                },
                "scripts": {
                    "start": "node server.js",
                    "test": "jest"
                }
            }
            package_file.write_text(json.dumps(package_data, indent=2))
            files.append(str(package_file))
            
            yield files

    def test_detect_react_framework(self, detector, sample_react_files):
        """Test React framework detection."""
        frameworks = detector.detect_frameworks(sample_react_files)
        
        assert 'react' in frameworks
        assert 'webpack' in frameworks
        assert 'babel' in frameworks
        assert 'jest' in frameworks
        assert 'eslint' in frameworks
        assert 'nodejs' in frameworks

    def test_detect_express_framework(self, detector, sample_express_files):
        """Test Express framework detection."""
        frameworks = detector.detect_frameworks(sample_express_files)
        
        assert 'express' in frameworks
        assert 'nodejs' in frameworks
        assert 'jest' in frameworks

    def test_analyze_react_framework(self, detector, sample_react_files):
        """Test React framework analysis."""
        framework_info = detector.analyze_framework('react', sample_react_files)
        
        assert isinstance(framework_info, FrameworkInfo)
        assert framework_info.name == 'react'
        assert framework_info.version == '^18.2.0'
        assert len(framework_info.usage_patterns) > 0
        
        # Check for React-specific patterns
        pattern_names = [p.pattern for p in framework_info.usage_patterns]
        assert any('React' in pattern for pattern in pattern_names)

    def test_analyze_express_framework(self, detector, sample_express_files):
        """Test Express framework analysis."""
        framework_info = detector.analyze_framework('express', sample_express_files)
        
        assert isinstance(framework_info, FrameworkInfo)
        assert framework_info.name == 'express'
        assert len(framework_info.usage_patterns) > 0
        
        # Check for Express-specific patterns
        pattern_names = [p.pattern for p in framework_info.usage_patterns]
        assert any('app.' in pattern for pattern in pattern_names)

    def test_detect_from_package_json(self, detector, sample_react_files):
        """Test framework detection from package.json."""
        frameworks = detector._detect_from_package_json(sample_react_files)
        
        assert 'react' in frameworks
        assert 'webpack' in frameworks
        assert 'babel' in frameworks
        assert 'jest' in frameworks
        assert 'eslint' in frameworks
        assert 'nodejs' in frameworks

    def test_detect_js_framework_version(self, detector, sample_react_files):
        """Test JavaScript framework version detection."""
        version = detector._detect_js_framework_version('react', sample_react_files)
        
        assert version == '^18.2.0'

    def test_calculate_react_compliance(self, detector):
        """Test React compliance calculation."""
        patterns = [
            UsagePattern(pattern='useState', file_path='component.jsx', occurrences=2, examples=[]),
            UsagePattern(pattern='useEffect', file_path='component.jsx', occurrences=1, examples=[])
        ]
        
        compliance = detector._calculate_react_compliance(patterns)
        
        assert 0.0 <= compliance <= 1.0
        assert compliance > 0.5  # Should be higher due to hooks usage

    def test_suggest_react_improvements(self, detector):
        """Test React improvement suggestions."""
        patterns = [
            UsagePattern(pattern='class', file_path='component.jsx', occurrences=5, examples=[])
        ]
        
        improvements = detector._suggest_react_improvements(patterns)
        
        # Should suggest migrating to hooks
        assert len(improvements) > 0
        assert any('hooks' in imp.description.lower() for imp in improvements)


class TestTypeScriptFrameworkDetector:
    """Test suite for TypeScriptFrameworkDetector."""

    @pytest.fixture
    def detector(self):
        """Create a TypeScriptFrameworkDetector instance."""
        return TypeScriptFrameworkDetector()

    @pytest.fixture
    def sample_nestjs_files(self):
        """Create sample NestJS application files."""
        files = []
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # NestJS controller
            controller_file = temp_path / "user.controller.ts"
            controller_file.write_text('''
import { Controller, Get, Post, Body, Param, Injectable } from '@nestjs/common';
import { UserService } from './user.service';

@Controller('users')
export class UserController {
    constructor(private readonly userService: UserService) {}
    
    @Get()
    async findAll() {
        return this.userService.findAll();
    }
    
    @Get(':id')
    async findOne(@Param('id') id: string) {
        return this.userService.findOne(+id);
    }
    
    @Post()
    async create(@Body() createUserDto: any) {
        return this.userService.create(createUserDto);
    }
}
''')
            files.append(str(controller_file))
            
            # NestJS service
            service_file = temp_path / "user.service.ts"
            service_file.write_text('''
import { Injectable } from '@nestjs/common';

@Injectable()
export class UserService {
    private users = [];
    
    findAll() {
        return this.users;
    }
    
    findOne(id: number) {
        return this.users.find(user => user.id === id);
    }
    
    create(userData: any) {
        const user = { id: Date.now(), ...userData };
        this.users.push(user);
        return user;
    }
}
''')
            files.append(str(service_file))
            
            # NestJS module
            module_file = temp_path / "user.module.ts"
            module_file.write_text('''
import { Module } from '@nestjs/common';
import { UserController } from './user.controller';
import { UserService } from './user.service';

@Module({
    controllers: [UserController],
    providers: [UserService],
    exports: [UserService],
})
export class UserModule {}
''')
            files.append(str(module_file))
            
            yield files

    def test_detect_nestjs_framework(self, detector, sample_nestjs_files):
        """Test NestJS framework detection."""
        frameworks = detector.detect_frameworks(sample_nestjs_files)
        
        assert 'nestjs' in frameworks

    def test_analyze_nestjs_framework(self, detector, sample_nestjs_files):
        """Test NestJS framework analysis."""
        framework_info = detector._analyze_ts_framework('nestjs', sample_nestjs_files)
        
        assert isinstance(framework_info, FrameworkInfo)
        assert framework_info.name == 'nestjs'
        assert len(framework_info.usage_patterns) > 0
        
        # Check for NestJS-specific patterns
        pattern_names = [p.pattern for p in framework_info.usage_patterns]
        assert any('@Controller' in pattern for pattern in pattern_names)
        assert any('@Injectable' in pattern for pattern in pattern_names)


class TestJavaFrameworkDetector:
    """Test suite for JavaFrameworkDetector."""

    @pytest.fixture
    def detector(self):
        """Create a JavaFrameworkDetector instance."""
        return JavaFrameworkDetector()

    @pytest.fixture
    def sample_spring_boot_files(self):
        """Create sample Spring Boot application files."""
        files = []
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Spring Boot main class
            main_file = temp_path / "Application.java"
            main_file.write_text('''
package com.example.demo;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
''')
            files.append(str(main_file))
            
            # Spring Boot controller
            controller_file = temp_path / "UserController.java"
            controller_file.write_text('''
package com.example.demo.controller;

import org.springframework.web.bind.annotation.*;
import org.springframework.beans.factory.annotation.Autowired;
import com.example.demo.service.UserService;

@RestController
@RequestMapping("/api/users")
public class UserController {
    
    @Autowired
    private UserService userService;
    
    @GetMapping
    public ResponseEntity<List<User>> getAllUsers() {
        return ResponseEntity.ok(userService.findAll());
    }
    
    @PostMapping
    public ResponseEntity<User> createUser(@RequestBody User user) {
        User savedUser = userService.save(user);
        return ResponseEntity.status(HttpStatus.CREATED).body(savedUser);
    }
    
    @GetMapping("/{id}")
    public ResponseEntity<User> getUserById(@PathVariable Long id) {
        return userService.findById(id)
            .map(user -> ResponseEntity.ok(user))
            .orElse(ResponseEntity.notFound().build());
    }
}
''')
            files.append(str(controller_file))
            
            # Spring Boot service
            service_file = temp_path / "UserService.java"
            service_file.write_text('''
package com.example.demo.service;

import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Autowired;
import com.example.demo.repository.UserRepository;

@Service
public class UserService {
    
    @Autowired
    private UserRepository userRepository;
    
    public List<User> findAll() {
        return userRepository.findAll();
    }
    
    public Optional<User> findById(Long id) {
        return userRepository.findById(id);
    }
    
    public User save(User user) {
        return userRepository.save(user);
    }
}
''')
            files.append(str(service_file))
            
            # Spring Boot repository
            repository_file = temp_path / "UserRepository.java"
            repository_file.write_text('''
package com.example.demo.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import com.example.demo.model.User;

@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    List<User> findByEmail(String email);
    Optional<User> findByUsername(String username);
}
''')
            files.append(str(repository_file))
            
            # Maven POM file
            pom_file = temp_path / "pom.xml"
            pom_file.write_text('''
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    
    <groupId>com.example</groupId>
    <artifactId>demo</artifactId>
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
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>
''')
            files.append(str(pom_file))
            
            yield files

    def test_detect_spring_boot_framework(self, detector, sample_spring_boot_files):
        """Test Spring Boot framework detection."""
        frameworks = detector.detect_frameworks(sample_spring_boot_files)
        
        assert 'spring_boot' in frameworks
        assert 'spring' in frameworks
        assert 'junit' in frameworks
        assert 'maven' in frameworks

    def test_analyze_spring_boot_framework(self, detector, sample_spring_boot_files):
        """Test Spring Boot framework analysis."""
        framework_info = detector.analyze_framework('spring_boot', sample_spring_boot_files)
        
        assert isinstance(framework_info, FrameworkInfo)
        assert framework_info.name == 'spring_boot'
        assert len(framework_info.usage_patterns) > 0
        
        # Check for Spring Boot-specific patterns
        pattern_names = [p.pattern for p in framework_info.usage_patterns]
        assert any('@SpringBootApplication' in pattern for pattern in pattern_names)
        assert any('@RestController' in pattern for pattern in pattern_names)
        assert any('@Service' in pattern for pattern in pattern_names)
        assert any('@Repository' in pattern for pattern in pattern_names)

    def test_calculate_spring_boot_compliance(self, detector):
        """Test Spring Boot compliance calculation."""
        patterns = [
            UsagePattern(pattern='@RestController', file_path='controller.java', occurrences=1, examples=[]),
            UsagePattern(pattern='@Service', file_path='service.java', occurrences=1, examples=[]),
            UsagePattern(pattern='@Repository', file_path='repository.java', occurrences=1, examples=[])
        ]
        
        compliance = detector._calculate_spring_boot_compliance(patterns)
        
        assert 0.0 <= compliance <= 1.0
        assert compliance > 0.5  # Should be higher due to proper annotations

    def test_suggest_spring_boot_improvements(self, detector):
        """Test Spring Boot improvement suggestions."""
        patterns = [
            UsagePattern(pattern='@RestController', file_path='controller.java', occurrences=1, examples=[])
        ]
        
        improvements = detector._suggest_spring_boot_improvements(patterns)
        
        # Should suggest adding service layer
        assert len(improvements) > 0
        assert any('service' in imp.description.lower() for imp in improvements)


class TestWebFrameworkDetector:
    """Test suite for WebFrameworkDetector."""

    @pytest.fixture
    def detector(self):
        """Create a WebFrameworkDetector instance."""
        return WebFrameworkDetector()

    @pytest.fixture
    def sample_bootstrap_files(self):
        """Create sample Bootstrap files."""
        files = []
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # HTML with Bootstrap classes
            html_file = temp_path / "index.html"
            html_file.write_text('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bootstrap Example</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container">
        <div class="row">
            <div class="col-md-6">
                <h1 class="text-primary">Welcome</h1>
                <button class="btn btn-primary">Click me</button>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">Card title</h5>
                        <p class="card-text">Some quick example text.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
''')
            files.append(str(html_file))
            
            # Package.json with Bootstrap
            package_file = temp_path / "package.json"
            package_data = {
                "name": "bootstrap-app",
                "version": "1.0.0",
                "dependencies": {
                    "bootstrap": "^5.3.0",
                    "jquery": "^3.6.0"
                }
            }
            package_file.write_text(json.dumps(package_data, indent=2))
            files.append(str(package_file))
            
            yield files

    @pytest.fixture
    def sample_tailwind_files(self):
        """Create sample Tailwind CSS files."""
        files = []
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # HTML with Tailwind classes
            html_file = temp_path / "index.html"
            html_file.write_text('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tailwind Example</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100">
    <div class="container mx-auto px-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="bg-white p-6 rounded-lg shadow-md">
                <h1 class="text-3xl font-bold text-blue-600 mb-4">Welcome</h1>
                <button class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                    Click me
                </button>
            </div>
            <div class="bg-white p-6 rounded-lg shadow-md">
                <h2 class="text-xl font-semibold mb-2">Card Title</h2>
                <p class="text-gray-600">Some quick example text.</p>
            </div>
        </div>
    </div>
</body>
</html>
''')
            files.append(str(html_file))
            
            # Tailwind config
            config_file = temp_path / "tailwind.config.js"
            config_file.write_text('''
module.exports = {
    content: ["./src/**/*.{html,js}"],
    theme: {
        extend: {},
    },
    plugins: [],
}
''')
            files.append(str(config_file))
            
            # CSS with Tailwind directives
            css_file = temp_path / "styles.css"
            css_file.write_text('''
@tailwind base;
@tailwind components;
@tailwind utilities;

.custom-button {
    @apply bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded;
}
''')
            files.append(str(css_file))
            
            yield files

    def test_detect_bootstrap_framework(self, detector, sample_bootstrap_files):
        """Test Bootstrap framework detection."""
        frameworks = detector.detect_frameworks(sample_bootstrap_files)
        
        assert 'bootstrap' in frameworks
        assert 'jquery' in frameworks

    def test_detect_tailwind_framework(self, detector, sample_tailwind_files):
        """Test Tailwind CSS framework detection."""
        frameworks = detector.detect_frameworks(sample_tailwind_files)
        
        assert 'tailwind' in frameworks

    def test_analyze_bootstrap_framework(self, detector, sample_bootstrap_files):
        """Test Bootstrap framework analysis."""
        framework_info = detector.analyze_framework('bootstrap', sample_bootstrap_files)
        
        assert isinstance(framework_info, FrameworkInfo)
        assert framework_info.name == 'bootstrap'
        assert len(framework_info.usage_patterns) > 0
        
        # Check for Bootstrap-specific patterns
        pattern_names = [p.pattern for p in framework_info.usage_patterns]
        assert any('btn-' in pattern for pattern in pattern_names)
        assert any('col-' in pattern for pattern in pattern_names)

    def test_analyze_tailwind_framework(self, detector, sample_tailwind_files):
        """Test Tailwind CSS framework analysis."""
        framework_info = detector.analyze_framework('tailwind', sample_tailwind_files)
        
        assert isinstance(framework_info, FrameworkInfo)
        assert framework_info.name == 'tailwind'
        assert len(framework_info.usage_patterns) > 0
        
        # Check for Tailwind-specific patterns
        pattern_names = [p.pattern for p in framework_info.usage_patterns]
        assert any('bg-' in pattern for pattern in pattern_names)
        assert any('text-' in pattern for pattern in pattern_names)

    def test_unknown_web_framework(self, detector, sample_bootstrap_files):
        """Test handling of unknown web framework."""
        framework_info = detector.analyze_framework('unknown_framework', sample_bootstrap_files)
        
        assert framework_info is None