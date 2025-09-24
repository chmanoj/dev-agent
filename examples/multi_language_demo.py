"""Demo script for multi-language project analysis."""

import json
import tempfile
from pathlib import Path

from dev_agent.analysis.multi_language_analyzer import MultiLanguageAnalyzer
from dev_agent.models.enums import LanguageType


def create_sample_project() -> Path:
    """Create a sample multi-language project for demonstration."""
    temp_dir = Path(tempfile.mkdtemp())
    print(f"Creating sample project in: {temp_dir}")
    
    # Python backend
    (temp_dir / "backend" / "app.py").parent.mkdir(parents=True)
    (temp_dir / "backend" / "app.py").write_text("""
from flask import Flask, jsonify
from typing import List, Dict
import logging

app = Flask(__name__)
logger = logging.getLogger(__name__)

class UserService:
    '''Service for managing users.'''
    
    def __init__(self):
        self.users: List[Dict[str, str]] = [
            {"id": "1", "name": "Alice", "email": "alice@example.com"},
            {"id": "2", "name": "Bob", "email": "bob@example.com"}
        ]
    
    async def get_users(self) -> List[Dict[str, str]]:
        '''Get all users asynchronously.'''
        try:
            return self.users
        except Exception as e:
            logger.error(f"Failed to get users: {e}")
            raise

user_service = UserService()

@app.route('/api/users')
async def get_users():
    '''API endpoint to get users.'''
    try:
        users = await user_service.get_users()
        return jsonify(users)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
""")
    
    (temp_dir / "backend" / "requirements.txt").write_text("""
flask==2.3.0
pytest==7.4.0
black==23.7.0
mypy==1.5.0
""")
    
    # React frontend
    (temp_dir / "frontend" / "src" / "App.jsx").parent.mkdir(parents=True)
    (temp_dir / "frontend" / "src" / "App.jsx").write_text("""
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

/**
 * Main application component
 * @returns {JSX.Element} The main app component
 */
function App() {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    
    useEffect(() => {
        fetchUsers();
    }, []);
    
    /**
     * Fetch users from the API
     */
    const fetchUsers = async () => {
        try {
            setLoading(true);
            const response = await axios.get('/api/users');
            setUsers(response.data);
        } catch (err) {
            setError('Failed to fetch users');
            console.error('Error fetching users:', err);
        } finally {
            setLoading(false);
        }
    };
    
    if (loading) return <div className="loading">Loading...</div>;
    if (error) return <div className="error">{error}</div>;
    
    return (
        <div className="App">
            <header className="App-header">
                <h1>User Management</h1>
            </header>
            <main>
                <UserList users={users} />
            </main>
        </div>
    );
}

const UserList = ({ users }) => (
    <div className="user-list">
        {users.map(user => (
            <UserCard key={user.id} user={user} />
        ))}
    </div>
);

const UserCard = ({ user }) => (
    <div className="user-card">
        <h3>{user.name}</h3>
        <p>{user.email}</p>
    </div>
);

export default App;
""")
    
    (temp_dir / "frontend" / "package.json").write_text(json.dumps({
        "name": "user-management-frontend",
        "version": "1.0.0",
        "dependencies": {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "axios": "^1.4.0"
        },
        "devDependencies": {
            "@testing-library/react": "^13.4.0",
            "eslint": "^8.45.0",
            "prettier": "^3.0.0",
            "jest": "^29.6.0"
        },
        "scripts": {
            "start": "react-scripts start",
            "build": "react-scripts build",
            "test": "react-scripts test"
        }
    }))
    
    # Java microservice
    java_dir = temp_dir / "microservice" / "src" / "main" / "java" / "com" / "example"
    java_dir.mkdir(parents=True)
    
    (java_dir / "UserController.java").write_text("""
package com.example;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.*;
import org.springframework.beans.factory.annotation.Autowired;
import java.util.List;
import java.util.ArrayList;

/**
 * Main application class for the user microservice
 * @author Development Team
 * @version 1.0
 */
@SpringBootApplication
@RestController
@RequestMapping("/api/v2")
public class UserController {
    
    @Autowired
    private UserService userService;
    
    /**
     * Main method to start the application
     * @param args command line arguments
     */
    public static void main(String[] args) {
        SpringApplication.run(UserController.class, args);
    }
    
    /**
     * Get all users
     * @return List of users
     */
    @GetMapping("/users")
    public List<User> getUsers() {
        try {
            return userService.getAllUsers();
        } catch (Exception e) {
            throw new RuntimeException("Failed to retrieve users", e);
        }
    }
    
    /**
     * Create a new user
     * @param user the user to create
     * @return the created user
     */
    @PostMapping("/users")
    public User createUser(@RequestBody User user) {
        try {
            return userService.createUser(user);
        } catch (Exception e) {
            throw new RuntimeException("Failed to create user", e);
        }
    }
}
""")
    
    (temp_dir / "microservice" / "pom.xml").write_text("""
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    
    <groupId>com.example</groupId>
    <artifactId>user-microservice</artifactId>
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
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>
""")
    
    # Configuration files
    (temp_dir / "docker-compose.yml").write_text("""
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
  
  microservice:
    build: ./microservice
    ports:
      - "8080:8080"
    depends_on:
      - backend
""")
    
    (temp_dir / "README.md").write_text("""
# Multi-Language User Management System

This is a demonstration project showcasing a multi-language architecture:

- **Backend**: Python Flask API
- **Frontend**: React.js application  
- **Microservice**: Java Spring Boot service
- **Deployment**: Docker Compose

## Architecture

The system follows a microservices architecture with:
- RESTful APIs for communication
- Containerized deployment
- Modern development practices
""")
    
    return temp_dir


def analyze_project(project_path: Path) -> None:
    """Analyze the multi-language project."""
    print(f"\n🔍 Analyzing project: {project_path}")
    print("=" * 60)
    
    analyzer = MultiLanguageAnalyzer(str(project_path))
    
    # Detect languages
    print("\n📋 DETECTED LANGUAGES:")
    languages = analyzer.detect_project_languages()
    
    for i, lang in enumerate(languages, 1):
        print(f"{i}. {lang.language.upper()}")
        print(f"   Files: {lang.file_count}")
        print(f"   Lines: {lang.line_count}")
        print(f"   Quality Score: {lang.quality_score:.2f}")
        if lang.frameworks:
            print(f"   Frameworks: {', '.join(lang.frameworks)}")
        if lang.version:
            print(f"   Version: {lang.version}")
        print()
    
    # Analyze frameworks
    print("🛠️  DETECTED FRAMEWORKS:")
    frameworks = analyzer.analyze_framework_usage()
    
    if frameworks:
        for i, fw in enumerate(frameworks, 1):
            print(f"{i}. {fw.name} (v{fw.version})")
            print(f"   Compliance: {fw.best_practices_compliance:.2f}")
            if fw.configuration_files:
                print(f"   Config Files: {', '.join(fw.configuration_files)}")
            print()
    else:
        print("   No specific framework analysis available")
    
    # Cross-language analysis
    print("🔗 CROSS-LANGUAGE ANALYSIS:")
    mappings = analyzer.generate_cross_language_mappings()
    
    if mappings.build_dependencies:
        print("   Build Dependencies:")
        for manager, deps in mappings.build_dependencies.items():
            print(f"     {manager}: {type(deps).__name__}")
    
    if mappings.shared_configurations:
        print("   Shared Configurations:")
        for config_type, details in mappings.shared_configurations.items():
            print(f"     {config_type}: {type(details).__name__}")
    
    if mappings.integration_patterns:
        print("   Integration Patterns:")
        for pattern in mappings.integration_patterns:
            print(f"     - {pattern}")
    
    # Language-specific patterns
    print("\n🎯 LANGUAGE PATTERNS:")
    for lang in languages:
        language_type = LanguageType(lang.language)
        patterns = analyzer.extract_language_patterns(language_type)
        
        if patterns:
            print(f"   {lang.language.upper()}:")
            for pattern_type, pattern_data in patterns.items():
                if isinstance(pattern_data, dict) and pattern_data:
                    print(f"     {pattern_type}: {len(pattern_data)} items")
                elif isinstance(pattern_data, list) and pattern_data:
                    print(f"     {pattern_type}: {len(pattern_data)} items")


def main():
    """Main demo function."""
    print("🚀 Multi-Language Project Analyzer Demo")
    print("=" * 60)
    
    # Create sample project
    project_path = create_sample_project()
    
    try:
        # Analyze the project
        analyze_project(project_path)
        
        print("\n✅ Analysis complete!")
        print(f"\nSample project created at: {project_path}")
        print("You can explore the generated files to see the multi-language structure.")
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()