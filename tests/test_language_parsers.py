"""Tests for language-specific parsers."""

import tempfile
from pathlib import Path

import pytest

from dev_agent.analysis.language_parsers import (
    JavaParser,
    JavaScriptParser,
    LanguageParserRegistry,
    PythonParser,
)
from dev_agent.models.enums import LanguageType


class TestPythonParser:
    """Test suite for PythonParser."""

    @pytest.fixture
    def temp_python_files(self):
        """Create temporary Python files for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create a well-structured Python file
            (project_path / "good_code.py").write_text('''
"""Module for user management."""

from typing import List, Optional
import logging


class UserManager:
    """Manages user operations."""
    
    def __init__(self):
        """Initialize the user manager."""
        self.users: List[str] = []
        self.logger = logging.getLogger(__name__)
    
    def add_user(self, username: str) -> bool:
        """Add a new user.
        
        Args:
            username: The username to add
            
        Returns:
            True if user was added successfully
            
        Raises:
            ValueError: If username is invalid
        """
        try:
            if not username or len(username) < 3:
                raise ValueError("Username must be at least 3 characters")
            
            self.users.append(username)
            self.logger.info(f"Added user: {username}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add user: {e}")
            raise
    
    @property
    def user_count(self) -> int:
        """Get the number of users."""
        return len(self.users)


async def fetch_user_data(user_id: int) -> Optional[dict]:
    """Fetch user data asynchronously."""
    try:
        # Simulate async operation
        await asyncio.sleep(0.1)
        return {"id": user_id, "name": f"User {user_id}"}
    except Exception:
        return None


# Constants
MAX_USERS = 1000
DEFAULT_TIMEOUT = 30
''')
            
            # Create a file with different style
            (project_path / "different_style.py").write_text('''
import os
import sys

def getUserList():
    return ["user1", "user2"]

class userService:
    def __init__(self):
        self.userList = []
    
    def addUser(self, userName):
        self.userList.append(userName)
        return True

def processUsers():
    users = getUserList()
    for user in users:
        print(user)

if __name__ == "__main__":
    processUsers()
''')
            
            # Create a file with syntax errors for error handling test
            (project_path / "syntax_error.py").write_text('''
def invalid_function(
    # Missing closing parenthesis and colon
    pass
''')
            
            yield list(project_path.glob("*.py"))

    def test_analyze_conventions(self, temp_python_files):
        """Test Python convention analysis."""
        parser = PythonParser()
        conventions = parser.analyze_conventions(temp_python_files)
        
        assert conventions is not None
        assert hasattr(conventions, 'naming_style')
        assert hasattr(conventions, 'formatting_style')
        assert hasattr(conventions, 'documentation_style')
        assert hasattr(conventions, 'error_handling_style')
        assert hasattr(conventions, 'consistency_score')
        
        # Check naming style analysis
        naming = conventions.naming_style
        assert "functions" in naming
        assert "classes" in naming
        
        # Should detect snake_case functions and PascalCase classes
        if naming["functions"]["total_count"] > 0:
            assert naming["functions"]["snake_case_ratio"] >= 0
        if naming["classes"]["total_count"] > 0:
            assert naming["classes"]["pascal_case_ratio"] >= 0

    def test_calculate_quality_score(self, temp_python_files):
        """Test Python quality score calculation."""
        parser = PythonParser()
        score = parser.calculate_quality_score(temp_python_files)
        
        # Score should be between 0 and 1
        assert 0.0 <= score <= 1.0
        
        # Should be reasonably high for well-structured code
        assert score > 0.3

    def test_extract_language_specific_patterns(self, temp_python_files):
        """Test Python-specific pattern extraction."""
        parser = PythonParser()
        patterns = parser.extract_language_specific_patterns(temp_python_files)
        
        assert "decorators" in patterns
        assert "async_patterns" in patterns
        
        # Should detect decorators
        decorators = patterns["decorators"]
        assert isinstance(decorators, list)
        assert "property" in decorators
        
        # Should detect async patterns
        async_patterns = patterns["async_patterns"]
        assert isinstance(async_patterns, dict)
        assert "async_functions" in async_patterns
        assert "await_expressions" in async_patterns

    def test_naming_analysis_details(self, temp_python_files):
        """Test detailed naming analysis."""
        parser = PythonParser()
        naming = parser._analyze_python_naming(temp_python_files)
        
        # Should analyze different naming categories
        assert "functions" in naming
        assert "classes" in naming
        
        # Should provide statistics
        for category, stats in naming.items():
            if stats["total_count"] > 0:
                assert "snake_case_ratio" in stats
                assert "camel_case_ratio" in stats
                assert "pascal_case_ratio" in stats
                assert 0 <= stats["snake_case_ratio"] <= 1
                assert 0 <= stats["camel_case_ratio"] <= 1
                assert 0 <= stats["pascal_case_ratio"] <= 1

    def test_formatting_analysis(self, temp_python_files):
        """Test formatting analysis."""
        parser = PythonParser()
        formatting = parser._analyze_python_formatting(temp_python_files)
        
        # Should analyze formatting aspects
        assert "most_common_indentation" in formatting
        assert formatting["most_common_indentation"] in [2, 4, "tab"]

    def test_documentation_analysis(self, temp_python_files):
        """Test documentation analysis."""
        parser = PythonParser()
        documentation = parser._analyze_python_documentation(temp_python_files)
        
        # Should analyze documentation coverage
        assert "function_docstring_coverage" in documentation
        assert 0 <= documentation["function_docstring_coverage"] <= 1
        
        if "most_common_docstring_style" in documentation:
            assert documentation["most_common_docstring_style"] in ["google", "sphinx", "basic"]

    def test_error_handling_analysis(self, temp_python_files):
        """Test error handling analysis."""
        parser = PythonParser()
        error_handling = parser._analyze_python_error_handling(temp_python_files)
        
        # Should analyze error handling patterns
        assert "try_except_blocks" in error_handling
        assert "specific_exception_ratio" in error_handling
        assert error_handling["try_except_blocks"] >= 0
        assert 0 <= error_handling["specific_exception_ratio"] <= 1

    def test_error_handling_with_syntax_errors(self, temp_python_files):
        """Test parser behavior with syntax errors."""
        parser = PythonParser()
        
        # Should not crash with syntax errors
        conventions = parser.analyze_conventions(temp_python_files)
        assert conventions is not None
        
        score = parser.calculate_quality_score(temp_python_files)
        assert 0.0 <= score <= 1.0


class TestJavaScriptParser:
    """Test suite for JavaScriptParser."""

    @pytest.fixture
    def temp_js_files(self):
        """Create temporary JavaScript files for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create modern JavaScript file
            (project_path / "modern.js").write_text('''
/**
 * User management module
 * @module UserManager
 */

import { EventEmitter } from 'events';
import axios from 'axios';

/**
 * Manages user operations
 * @class UserManager
 */
class UserManager extends EventEmitter {
    constructor() {
        super();
        this.users = [];
        this.apiClient = axios.create({
            baseURL: 'https://api.example.com'
        });
    }
    
    /**
     * Add a new user
     * @param {string} username - The username to add
     * @returns {Promise<boolean>} True if user was added
     */
    async addUser(username) {
        try {
            if (!username || username.length < 3) {
                throw new Error('Username must be at least 3 characters');
            }
            
            const response = await this.apiClient.post('/users', { username });
            this.users.push(response.data);
            this.emit('userAdded', response.data);
            return true;
        } catch (error) {
            console.error('Failed to add user:', error);
            throw error;
        }
    }
    
    /**
     * Get user count
     * @returns {number} Number of users
     */
    get userCount() {
        return this.users.length;
    }
}

// Arrow functions
const processUsers = (users) => {
    return users.map(user => ({
        ...user,
        displayName: `${user.firstName} ${user.lastName}`
    }));
};

// Async arrow function
const fetchUserData = async (userId) => {
    try {
        const response = await fetch(`/api/users/${userId}`);
        return await response.json();
    } catch (error) {
        return null;
    }
};

// IIFE
(function() {
    console.log('Module initialized');
})();

export { UserManager, processUsers, fetchUserData };
''')
            
            # Create older style JavaScript
            (project_path / "legacy.js").write_text('''
'use strict';

var UserService = function() {
    this.user_list = [];
};

UserService.prototype.add_user = function(user_name) {
    this.user_list.push(user_name);
    return true;
};

function process_users() {
    var users = get_user_list();
    for (var i = 0; i < users.length; i++) {
        console.log(users[i]);
    }
}

function get_user_list() {
    return ["user1", "user2"];
}

// No semicolons style
var noSemicolonFunction = function() {
    console.log('No semicolons here')
    return true
}
''')
            
            yield list(project_path.glob("*.js"))

    def test_analyze_conventions(self, temp_js_files):
        """Test JavaScript convention analysis."""
        parser = JavaScriptParser()
        conventions = parser.analyze_conventions(temp_js_files)
        
        assert conventions is not None
        assert hasattr(conventions, 'naming_style')
        assert hasattr(conventions, 'formatting_style')
        assert hasattr(conventions, 'documentation_style')
        assert hasattr(conventions, 'error_handling_style')
        assert hasattr(conventions, 'consistency_score')

    def test_calculate_quality_score(self, temp_js_files):
        """Test JavaScript quality score calculation."""
        parser = JavaScriptParser()
        score = parser.calculate_quality_score(temp_js_files)
        
        # Score should be between 0 and 1
        assert 0.0 <= score <= 1.0

    def test_extract_language_specific_patterns(self, temp_js_files):
        """Test JavaScript-specific pattern extraction."""
        parser = JavaScriptParser()
        patterns = parser.extract_language_specific_patterns(temp_js_files)
        
        assert "module_patterns" in patterns
        assert "async_patterns" in patterns
        assert "class_patterns" in patterns
        assert "function_patterns" in patterns
        
        # Should detect ES6 modules
        module_patterns = patterns["module_patterns"]
        assert "es6_imports" in module_patterns
        assert "es6_exports" in module_patterns
        
        # Should detect async patterns
        async_patterns = patterns["async_patterns"]
        assert "async_functions" in async_patterns
        assert "await_expressions" in async_patterns

    def test_naming_analysis(self, temp_js_files):
        """Test JavaScript naming analysis."""
        parser = JavaScriptParser()
        naming = parser._analyze_js_naming(temp_js_files)
        
        # Should analyze different naming categories
        assert "functions" in naming
        assert "classes" in naming
        assert "variables" in naming
        
        # Should detect camelCase and other patterns
        for category, stats in naming.items():
            if stats["total_count"] > 0:
                assert "camel_case_ratio" in stats
                assert "pascal_case_ratio" in stats
                assert "snake_case_ratio" in stats

    def test_formatting_analysis(self, temp_js_files):
        """Test JavaScript formatting analysis."""
        parser = JavaScriptParser()
        formatting = parser._analyze_js_formatting(temp_js_files)
        
        # Should analyze semicolon usage
        if "semicolon_usage_ratio" in formatting:
            assert 0 <= formatting["semicolon_usage_ratio"] <= 1
        
        # Should analyze quote usage
        if "single_quote_ratio" in formatting:
            assert 0 <= formatting["single_quote_ratio"] <= 1

    def test_documentation_analysis(self, temp_js_files):
        """Test JavaScript documentation analysis."""
        parser = JavaScriptParser()
        documentation = parser._analyze_js_documentation(temp_js_files)
        
        # Should analyze JSDoc coverage
        assert "jsdoc_coverage" in documentation
        assert 0 <= documentation["jsdoc_coverage"] <= 1
        
        # Should count different comment types
        assert "inline_comments" in documentation
        assert "block_comments" in documentation

    def test_module_pattern_extraction(self, temp_js_files):
        """Test module pattern extraction."""
        parser = JavaScriptParser()
        patterns = parser._extract_js_module_patterns(temp_js_files)
        
        # Should detect ES6 imports/exports
        assert "es6_imports" in patterns
        assert "es6_exports" in patterns
        assert patterns["es6_imports"] > 0
        assert patterns["es6_exports"] > 0

    def test_function_pattern_extraction(self, temp_js_files):
        """Test function pattern extraction."""
        parser = JavaScriptParser()
        patterns = parser._extract_js_function_patterns(temp_js_files)
        
        # Should detect different function types
        assert "regular_functions" in patterns
        assert "arrow_functions" in patterns
        assert "anonymous_functions" in patterns
        assert "iife" in patterns


class TestJavaParser:
    """Test suite for JavaParser."""

    @pytest.fixture
    def temp_java_files(self):
        """Create temporary Java files for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create well-structured Java file
            (project_path / "UserService.java").write_text('''
package com.example.service;

import java.util.List;
import java.util.ArrayList;
import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Autowired;

/**
 * Service for managing users
 * @author Developer
 * @version 1.0
 */
@Service
public class UserService implements IUserService {
    
    private static final int MAX_USERS = 1000;
    private static final String DEFAULT_ROLE = "USER";
    
    @Autowired
    private UserRepository userRepository;
    
    private List<User> users;
    
    /**
     * Constructor for UserService
     */
    public UserService() {
        this.users = new ArrayList<>();
    }
    
    /**
     * Add a new user to the system
     * @param username The username to add
     * @return true if user was added successfully
     * @throws IllegalArgumentException if username is invalid
     */
    public boolean addUser(String username) throws IllegalArgumentException {
        try {
            if (username == null || username.length() < 3) {
                throw new IllegalArgumentException("Username must be at least 3 characters");
            }
            
            User newUser = new User(username, DEFAULT_ROLE);
            users.add(newUser);
            userRepository.save(newUser);
            return true;
        } catch (Exception e) {
            logger.error("Failed to add user: " + username, e);
            throw new RuntimeException("User creation failed", e);
        } finally {
            // Cleanup resources if needed
        }
    }
    
    /**
     * Get the number of users
     * @return user count
     */
    public int getUserCount() {
        return users.size();
    }
}
''')
            
            # Create interface
            (project_path / "IUserService.java").write_text('''
package com.example.service;

import java.util.List;

/**
 * Interface for user service operations
 */
public interface IUserService {
    
    /**
     * Add a user
     * @param username the username
     * @return success status
     */
    boolean addUser(String username);
    
    /**
     * Get user count
     * @return number of users
     */
    int getUserCount();
}
''')
            
            # Create different style Java file
            (project_path / "different_style.java").write_text('''
package com.example;

import java.util.*;

public class user_manager 
{
    private ArrayList user_list;
    
    public user_manager() 
    {
        user_list = new ArrayList();
    }
    
    public void add_user(String user_name) 
    {
        user_list.add(user_name);
    }
}
''')
            
            yield list(project_path.glob("*.java"))

    def test_analyze_conventions(self, temp_java_files):
        """Test Java convention analysis."""
        parser = JavaParser()
        conventions = parser.analyze_conventions(temp_java_files)
        
        assert conventions is not None
        assert hasattr(conventions, 'naming_style')
        assert hasattr(conventions, 'formatting_style')
        assert hasattr(conventions, 'documentation_style')
        assert hasattr(conventions, 'error_handling_style')
        assert hasattr(conventions, 'consistency_score')

    def test_calculate_quality_score(self, temp_java_files):
        """Test Java quality score calculation."""
        parser = JavaParser()
        score = parser.calculate_quality_score(temp_java_files)
        
        # Score should be between 0 and 1
        assert 0.0 <= score <= 1.0
        
        # Should be reasonably high for well-structured code
        assert score > 0.3

    def test_extract_language_specific_patterns(self, temp_java_files):
        """Test Java-specific pattern extraction."""
        parser = JavaParser()
        patterns = parser.extract_language_specific_patterns(temp_java_files)
        
        assert "design_patterns" in patterns
        assert "annotation_usage" in patterns
        assert "inheritance_patterns" in patterns
        assert "interface_usage" in patterns
        
        # Should detect annotations
        annotations = patterns["annotation_usage"]
        assert isinstance(annotations, list)
        assert "Service" in annotations
        assert "Autowired" in annotations
        
        # Should detect interfaces
        interfaces = patterns["interface_usage"]
        assert isinstance(interfaces, list)
        assert "IUserService" in interfaces

    def test_naming_analysis(self, temp_java_files):
        """Test Java naming analysis."""
        parser = JavaParser()
        naming = parser._analyze_java_naming(temp_java_files)
        
        # Should analyze different naming categories
        assert "classes" in naming
        assert "methods" in naming
        assert "constants" in naming
        
        # Should detect PascalCase classes
        if naming["classes"]["total_count"] > 0:
            assert "pascal_case_ratio" in naming["classes"]
        
        # Should detect camelCase methods
        if naming["methods"]["total_count"] > 0:
            assert "camel_case_ratio" in naming["methods"]

    def test_documentation_analysis(self, temp_java_files):
        """Test Java documentation analysis."""
        parser = JavaParser()
        documentation = parser._analyze_java_documentation(temp_java_files)
        
        # Should analyze Javadoc coverage
        assert "class_javadoc_coverage" in documentation
        assert "method_javadoc_coverage" in documentation
        assert 0 <= documentation["class_javadoc_coverage"] <= 1
        assert 0 <= documentation["method_javadoc_coverage"] <= 1

    def test_error_handling_analysis(self, temp_java_files):
        """Test Java error handling analysis."""
        parser = JavaParser()
        error_handling = parser._analyze_java_error_handling(temp_java_files)
        
        # Should analyze error handling patterns
        assert "try_catch_blocks" in error_handling
        assert "throws_declarations" in error_handling
        assert "finally_blocks" in error_handling
        assert error_handling["try_catch_blocks"] >= 0

    def test_inheritance_extraction(self, temp_java_files):
        """Test inheritance pattern extraction."""
        parser = JavaParser()
        inheritance = parser._extract_java_inheritance(temp_java_files)
        
        # Should detect inheritance relationships
        assert isinstance(inheritance, dict)
        # UserService extends nothing in our test, but implements interface

    def test_annotation_extraction(self, temp_java_files):
        """Test annotation extraction."""
        parser = JavaParser()
        annotations = parser._extract_java_annotations(temp_java_files)
        
        # Should detect Spring annotations
        assert isinstance(annotations, list)
        assert "Service" in annotations
        assert "Autowired" in annotations


class TestLanguageParserRegistry:
    """Test suite for LanguageParserRegistry."""

    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = LanguageParserRegistry()
        
        # Should have parsers for supported languages
        assert registry.get_parser(LanguageType.PYTHON) is not None
        assert registry.get_parser(LanguageType.JAVASCRIPT) is not None
        assert registry.get_parser(LanguageType.TYPESCRIPT) is not None
        assert registry.get_parser(LanguageType.JAVA) is not None

    def test_get_supported_languages(self):
        """Test getting supported languages."""
        registry = LanguageParserRegistry()
        languages = registry.get_supported_languages()
        
        assert LanguageType.PYTHON in languages
        assert LanguageType.JAVASCRIPT in languages
        assert LanguageType.JAVA in languages
        assert len(languages) >= 3

    def test_parser_types(self):
        """Test that correct parser types are returned."""
        registry = LanguageParserRegistry()
        
        python_parser = registry.get_parser(LanguageType.PYTHON)
        assert isinstance(python_parser, PythonParser)
        
        js_parser = registry.get_parser(LanguageType.JAVASCRIPT)
        assert isinstance(js_parser, JavaScriptParser)
        
        java_parser = registry.get_parser(LanguageType.JAVA)
        assert isinstance(java_parser, JavaParser)

    def test_typescript_uses_js_parser(self):
        """Test that TypeScript uses JavaScript parser."""
        registry = LanguageParserRegistry()
        
        js_parser = registry.get_parser(LanguageType.JAVASCRIPT)
        ts_parser = registry.get_parser(LanguageType.TYPESCRIPT)
        
        # Should be the same parser instance
        assert js_parser is ts_parser

    def test_custom_parser_registration(self):
        """Test custom parser registration."""
        registry = LanguageParserRegistry()
        
        # Register a custom parser
        custom_parser = PythonParser()
        registry.register_parser(LanguageType.PYTHON, custom_parser)
        
        # Should return the custom parser
        assert registry.get_parser(LanguageType.PYTHON) is custom_parser

    def test_unsupported_language(self):
        """Test behavior with unsupported language."""
        registry = LanguageParserRegistry()
        
        # Should return None for unsupported language
        assert registry.get_parser(LanguageType.SQL) is None