"""Integration test for multi-language analyzer functionality."""

import json
import tempfile
from pathlib import Path

import pytest

from dev_agent.analysis.multi_language_analyzer import MultiLanguageAnalyzer
from dev_agent.models.enums import LanguageType


def test_multi_language_analyzer_integration():
    """Test the core multi-language analyzer functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)
        
        # Create a simple multi-language project
        
        # Python file
        (project_path / "app.py").write_text("""
import flask
from typing import List

def get_users() -> List[str]:
    '''Get all users.'''
    return ["user1", "user2"]

app = flask.Flask(__name__)

@app.route('/users')
def users():
    return get_users()
""")
        
        (project_path / "requirements.txt").write_text("flask==2.0.1\npytest==7.1.0")
        
        # JavaScript file
        (project_path / "client.js").write_text("""
const express = require('express');
const app = express();

async function fetchUsers() {
    try {
        const response = await fetch('/users');
        return await response.json();
    } catch (error) {
        console.error('Failed to fetch users:', error);
        return [];
    }
}

app.listen(3000);
""")
        
        (project_path / "package.json").write_text(json.dumps({
            "name": "test-app",
            "dependencies": {
                "express": "^4.18.0"
            }
        }))
        
        # Java file
        java_dir = project_path / "src" / "main" / "java"
        java_dir.mkdir(parents=True)
        
        (java_dir / "App.java").write_text("""
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class App {
    public static void main(String[] args) {
        SpringApplication.run(App.class, args);
    }
}
""")
        
        # Test the analyzer
        analyzer = MultiLanguageAnalyzer(str(project_path))
        
        # Test language detection
        languages = analyzer.detect_project_languages()
        assert len(languages) >= 2  # Should detect at least Python and JavaScript
        
        language_names = [lang.language for lang in languages]
        assert LanguageType.PYTHON.value in language_names
        assert LanguageType.JAVASCRIPT.value in language_names
        
        # Test framework detection
        frameworks = analyzer.analyze_framework_usage()
        # Should detect some frameworks (even if basic info)
        assert isinstance(frameworks, list)
        
        # Test cross-language mappings
        mappings = analyzer.generate_cross_language_mappings()
        assert mappings is not None
        assert hasattr(mappings, 'api_interactions')
        assert hasattr(mappings, 'build_dependencies')
        
        # Test language patterns (should not crash)
        for language_info in languages:
            language_type = LanguageType(language_info.language)
            patterns = analyzer.extract_language_patterns(language_type)
            assert isinstance(patterns, dict)
        
        print("✅ Multi-language analyzer integration test passed!")
        print(f"Detected languages: {language_names}")
        print(f"Detected {len(frameworks)} frameworks")


if __name__ == "__main__":
    test_multi_language_analyzer_integration()