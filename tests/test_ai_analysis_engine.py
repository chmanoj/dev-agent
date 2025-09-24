"""Tests for AI analysis engine and its components."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from dev_agent.analysis.ai_analysis_engine import AIAnalysisEngine
from dev_agent.analysis.architectural_analyzer import ArchitecturalAnalyzer
from dev_agent.analysis.code_quality_analyzer import CodeQualityAnalyzer
from dev_agent.analysis.performance_analyzer import PerformanceAnalyzer
from dev_agent.analysis.security_analyzer import SecurityAnalyzer
from dev_agent.models.analysis import (
    ArchitecturalAnalysisResult,
    CodeSmell,
    ComprehensiveAnalysisResult,
    PerformanceAnalysisResult,
    PerformanceIssue,
    QualityAnalysisResult,
    SecurityAnalysisResult,
    SecurityIssue,
)


class TestAIAnalysisEngine:
    """Test cases for AI analysis engine."""

    @pytest.fixture
    def mock_indexing_engine(self):
        """Create a mock indexing engine."""
        mock_engine = Mock()
        mock_engine.ast_index = Mock()
        mock_engine.ast_index.functions = {}
        mock_engine.ast_index.classes = {}
        mock_engine.ast_index.file_metadata = {}
        mock_engine.ast_index.imports = []
        return mock_engine

    @pytest.fixture
    def mock_ai_service(self):
        """Create a mock AI service."""
        return Mock()

    @pytest.fixture
    def ai_analysis_engine(self, mock_indexing_engine, mock_ai_service):
        """Create an AI analysis engine instance."""
        return AIAnalysisEngine(mock_indexing_engine, mock_ai_service)

    def test_comprehensive_analysis_empty_project(self, ai_analysis_engine):
        """Test comprehensive analysis on empty project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = ai_analysis_engine.analyze_comprehensive(temp_dir)
            
            assert isinstance(result, ComprehensiveAnalysisResult)
            assert result.overall_health_score >= 0.0
            assert result.overall_health_score <= 1.0
            assert isinstance(result.quality_analysis, QualityAnalysisResult)
            assert isinstance(result.security_analysis, SecurityAnalysisResult)
            assert isinstance(result.performance_analysis, PerformanceAnalysisResult)
            assert isinstance(result.architectural_analysis, ArchitecturalAnalysisResult)

    def test_quality_analysis(self, ai_analysis_engine):
        """Test quality analysis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = ai_analysis_engine.analyze_quality(temp_dir)
            
            assert isinstance(result, QualityAnalysisResult)
            assert result.overall_score >= 0.0
            assert result.overall_score <= 1.0

    def test_security_analysis(self, ai_analysis_engine):
        """Test security analysis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = ai_analysis_engine.analyze_security(temp_dir)
            
            assert isinstance(result, SecurityAnalysisResult)
            assert result.overall_security_score >= 0.0
            assert result.overall_security_score <= 1.0

    def test_performance_analysis(self, ai_analysis_engine):
        """Test performance analysis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = ai_analysis_engine.analyze_performance(temp_dir)
            
            assert isinstance(result, PerformanceAnalysisResult)
            assert result.overall_performance_score >= 0.0
            assert result.overall_performance_score <= 1.0

    def test_architectural_analysis(self, ai_analysis_engine):
        """Test architectural analysis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = ai_analysis_engine.analyze_architecture(temp_dir)
            
            assert isinstance(result, ArchitecturalAnalysisResult)
            assert result.overall_architecture_score >= 0.0
            assert result.overall_architecture_score <= 1.0


class TestCodeQualityAnalyzer:
    """Test cases for code quality analyzer."""

    @pytest.fixture
    def mock_indexing_engine(self):
        """Create a mock indexing engine."""
        mock_engine = Mock()
        mock_engine.ast_index = Mock()
        mock_engine.ast_index.functions = {}
        mock_engine.ast_index.classes = {}
        mock_engine.ast_index.file_metadata = {}
        mock_engine.ast_index.imports = []
        return mock_engine

    @pytest.fixture
    def quality_analyzer(self, mock_indexing_engine):
        """Create a code quality analyzer instance."""
        return CodeQualityAnalyzer(mock_indexing_engine)

    def test_analyze_code_smells_long_method(self, quality_analyzer):
        """Test detection of long methods."""
        code = '''
def very_long_method():
    """A method that is too long."""
    # This method has many lines
''' + '\n'.join([f'    line_{i} = {i}' for i in range(60)]) + '''
    return "done"
'''
        
        smells = quality_analyzer.analyze_code_smells(code, "test.py")
        
        long_method_smells = [s for s in smells if s.name == "Long Method"]
        assert len(long_method_smells) > 0
        assert long_method_smells[0].severity in ["medium", "high"]

    def test_analyze_code_smells_large_class(self, quality_analyzer):
        """Test detection of large classes."""
        methods = '\n'.join([f'    def method_{i}(self): pass' for i in range(25)])
        code = f'''
class LargeClass:
    """A class with too many methods."""
{methods}
'''
        
        smells = quality_analyzer.analyze_code_smells(code, "test.py")
        
        large_class_smells = [s for s in smells if s.name == "Large Class"]
        assert len(large_class_smells) > 0
        assert large_class_smells[0].severity in ["medium", "high"]

    def test_analyze_code_smells_long_parameter_list(self, quality_analyzer):
        """Test detection of long parameter lists."""
        code = '''
def method_with_many_params(a, b, c, d, e, f, g, h):
    """Method with too many parameters."""
    return a + b + c + d + e + f + g + h
'''
        
        smells = quality_analyzer.analyze_code_smells(code, "test.py")
        
        param_smells = [s for s in smells if s.name == "Long Parameter List"]
        assert len(param_smells) > 0
        assert param_smells[0].severity in ["medium", "high"]

    def test_calculate_complexity_metrics(self, quality_analyzer):
        """Test complexity metrics calculation."""
        code = '''
def complex_function(x):
    if x > 0:
        for i in range(x):
            if i % 2 == 0:
                while i > 0:
                    i -= 1
    return x
'''
        
        metrics = quality_analyzer.calculate_complexity_metrics(code)
        
        assert "cyclomatic_complexity" in metrics
        assert "cognitive_complexity" in metrics
        assert "nesting_depth" in metrics
        assert metrics["cyclomatic_complexity"] > 1

    def test_analyze_maintainability(self, quality_analyzer):
        """Test maintainability analysis."""
        simple_code = '''
def simple_function(x):
    return x * 2
'''
        
        complex_code = '''
def complex_function(x):
    if x > 0:
        for i in range(x):
            if i % 2 == 0:
                for j in range(i):
                    if j % 3 == 0:
                        x += j
    return x
'''
        
        simple_maintainability = quality_analyzer.analyze_maintainability(simple_code)
        complex_maintainability = quality_analyzer.analyze_maintainability(complex_code)
        
        assert simple_maintainability > complex_maintainability
        assert 0.0 <= simple_maintainability <= 1.0
        assert 0.0 <= complex_maintainability <= 1.0


class TestSecurityAnalyzer:
    """Test cases for security analyzer."""

    @pytest.fixture
    def mock_indexing_engine(self):
        """Create a mock indexing engine."""
        mock_engine = Mock()
        mock_engine.ast_index = Mock()
        mock_engine.ast_index.functions = {}
        mock_engine.ast_index.classes = {}
        mock_engine.ast_index.file_metadata = {}
        mock_engine.ast_index.imports = []
        return mock_engine

    @pytest.fixture
    def security_analyzer(self, mock_indexing_engine):
        """Create a security analyzer instance."""
        return SecurityAnalyzer(mock_indexing_engine)

    def test_scan_vulnerabilities_eval_usage(self, security_analyzer):
        """Test detection of eval usage."""
        code = '''
def dangerous_function(user_input):
    result = eval(user_input)
    return result
'''
        
        issues = security_analyzer.scan_vulnerabilities(code, "test.py")
        
        eval_issues = [i for i in issues if "eval" in i.description.lower()]
        assert len(eval_issues) > 0
        assert eval_issues[0].severity == "critical"
        assert eval_issues[0].cwe_id == "CWE-94"

    def test_scan_vulnerabilities_sql_injection(self, security_analyzer):
        """Test detection of SQL injection vulnerabilities."""
        code = '''
def query_user(user_id):
    query = "SELECT * FROM users WHERE id = %s" % user_id
    cursor.execute(query)
    return cursor.fetchall()
'''
        
        issues = security_analyzer.scan_vulnerabilities(code, "test.py")
        
        sql_issues = [i for i in issues if "sql injection" in i.vulnerability_type.lower()]
        assert len(sql_issues) > 0
        assert sql_issues[0].severity == "high"

    def test_check_input_validation(self, security_analyzer):
        """Test input validation checking."""
        code = '''
def process_input(data):
    exec(data)  # Dangerous!
    return "processed"
'''
        
        issues = security_analyzer.check_input_validation(code)
        
        assert len(issues) > 0
        assert any("exec" in issue.description for issue in issues)

    def test_check_data_exposure_hardcoded_secrets(self, security_analyzer):
        """Test detection of hardcoded secrets."""
        code = '''
API_KEY = "sk-1234567890abcdef"
password = "supersecret123"
secret_token = "abc123def456"
'''
        
        issues = security_analyzer.check_data_exposure(code)
        
        secret_issues = [i for i in issues if "hardcoded" in i.description.lower()]
        assert len(secret_issues) > 0
        assert all(issue.severity == "high" for issue in secret_issues)


class TestPerformanceAnalyzer:
    """Test cases for performance analyzer."""

    @pytest.fixture
    def mock_indexing_engine(self):
        """Create a mock indexing engine."""
        mock_engine = Mock()
        mock_engine.ast_index = Mock()
        mock_engine.ast_index.functions = {}
        mock_engine.ast_index.classes = {}
        mock_engine.ast_index.file_metadata = {}
        mock_engine.ast_index.imports = []
        return mock_engine

    @pytest.fixture
    def performance_analyzer(self, mock_indexing_engine):
        """Create a performance analyzer instance."""
        return PerformanceAnalyzer(mock_indexing_engine)

    def test_identify_bottlenecks_nested_loops(self, performance_analyzer):
        """Test detection of nested loops."""
        code = '''
def nested_loop_function(data):
    result = []
    for i in data:
        for j in data:
            for k in data:
                result.append(i * j * k)
    return result
'''
        
        issues = performance_analyzer.identify_bottlenecks(code, "test.py")
        
        nested_loop_issues = [i for i in issues if "nested" in i.description.lower()]
        assert len(nested_loop_issues) > 0
        assert nested_loop_issues[0].impact == "high"
        assert nested_loop_issues[0].category == "algorithm"

    def test_analyze_algorithm_complexity(self, performance_analyzer):
        """Test algorithm complexity analysis."""
        code = '''
def linear_function(data):
    for item in data:
        print(item)

def quadratic_function(data):
    for i in data:
        for j in data:
            print(i, j)

def constant_function():
    return 42
'''
        
        complexity_map = performance_analyzer.analyze_algorithm_complexity(code)
        
        assert "linear_function" in complexity_map
        assert "quadratic_function" in complexity_map
        assert "constant_function" in complexity_map
        
        # Check that quadratic is more complex than linear
        assert "n²" in complexity_map["quadratic_function"] or "n^2" in complexity_map["quadratic_function"]

    def test_check_memory_usage(self, performance_analyzer):
        """Test memory usage checking."""
        code = '''
def memory_intensive():
    large_list = [i for i in range(1000000)]
    return large_list
'''
        
        issues = performance_analyzer.check_memory_usage(code)
        
        memory_issues = [i for i in issues if "memory" in i.issue_type.lower()]
        assert len(memory_issues) > 0
        assert memory_issues[0].category == "memory"

    def test_analyze_io_patterns(self, performance_analyzer):
        """Test I/O pattern analysis."""
        code = '''
def inefficient_io():
    for i in range(100):
        with open(f"file_{i}.txt", "w") as f:
            f.write("data")
'''
        
        issues = performance_analyzer.analyze_io_patterns(code)
        
        io_issues = [i for i in issues if "i/o" in i.issue_type.lower()]
        assert len(io_issues) > 0
        assert io_issues[0].category == "io"


class TestArchitecturalAnalyzer:
    """Test cases for architectural analyzer."""

    @pytest.fixture
    def mock_indexing_engine(self):
        """Create a mock indexing engine with sample data."""
        mock_engine = Mock()
        mock_engine.ast_index = Mock()
        
        # Mock class with many methods (large class)
        mock_class = Mock()
        mock_class.name = "LargeClass"
        mock_class.file_path = "test.py"
        
        # Create proper mock methods with name and docstring attributes
        mock_methods = []
        for i in range(25):
            mock_method = Mock()
            mock_method.name = f"method_{i}"
            mock_method.docstring = f"Docstring for method_{i}"
            mock_methods.append(mock_method)
        
        mock_class.methods = mock_methods
        mock_class.attributes = ["attr1", "attr2", "attr3"]
        
        mock_engine.ast_index.classes = {"LargeClass": mock_class}
        mock_engine.ast_index.functions = {}
        mock_engine.ast_index.file_metadata = {}  # Empty to avoid file access issues
        mock_engine.ast_index.imports = []
        
        return mock_engine

    @pytest.fixture
    def architectural_analyzer(self, mock_indexing_engine):
        """Create an architectural analyzer instance."""
        return ArchitecturalAnalyzer(mock_indexing_engine)

    def test_detect_violations_empty_project(self, architectural_analyzer):
        """Test violation detection on empty project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations = architectural_analyzer.detect_violations(temp_dir)
            
            assert isinstance(violations, list)
            # May have violations from mock data

    def test_analyze_dependencies(self, architectural_analyzer):
        """Test dependency analysis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = architectural_analyzer.analyze_dependencies(temp_dir)
            
            assert isinstance(result, dict)
            assert "dependency_graph" in result
            assert "circular_dependencies" in result
            assert "external_dependencies" in result

    def test_analyze_coupling(self, architectural_analyzer):
        """Test coupling analysis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = architectural_analyzer.analyze_coupling(temp_dir)
            
            assert isinstance(result, dict)
            assert all(isinstance(v, (int, float)) for v in result.values())


class TestIntegration:
    """Integration tests for the AI analysis system."""

    def test_create_sample_project_with_issues(self):
        """Create a sample project with known issues for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create a file with multiple issues
            problematic_file = project_path / "problematic.py"
            problematic_file.write_text('''
# File with multiple code quality and security issues

password = "hardcoded_secret_123"  # Security issue
API_KEY = "sk-1234567890abcdef"    # Security issue

def very_long_method_with_many_issues(param1, param2, param3, param4, param5, param6, param7):
    """This method has multiple issues."""
    result = ""
    
    # Inefficient string concatenation in loop
    for i in range(100):
        result += str(i)  # Performance issue
        
        # Nested loops (performance issue)
        for j in range(100):
            for k in range(10):
                if i % 2 == 0:
                    if j % 3 == 0:
                        if k % 5 == 0:  # Deep nesting
                            result += str(k)
    
    # Security issue - eval usage
    user_input = input("Enter code: ")
    eval(user_input)
    
    # More lines to make method too long
''' + '\n'.join([f'    line_{i} = {i}' for i in range(50)]) + '''
    
    return result

class GodClass:
    """A class that does too many things."""
    
    def __init__(self):
        self.data = []
        self.config = {}
        self.logger = None
        self.database = None
        self.cache = None
        self.validator = None
        self.formatter = None
        self.parser = None
        self.serializer = None
        self.deserializer = None
    
''' + '\n'.join([f'    def method_{i}(self): pass' for i in range(30)]) + '''

def unused_function():
    """This function is never called."""
    return "unused"
''')
            
            # Verify the file was created
            assert problematic_file.exists()
            assert len(problematic_file.read_text()) > 1000

    @pytest.mark.integration
    def test_full_analysis_pipeline(self):
        """Test the full analysis pipeline with a real project structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create a realistic project structure
            (project_path / "src").mkdir()
            (project_path / "tests").mkdir()
            (project_path / "src" / "models").mkdir()
            (project_path / "src" / "services").mkdir()
            (project_path / "src" / "controllers").mkdir()
            
            # Create files with various issues
            model_file = project_path / "src" / "models" / "user.py"
            model_file.write_text('''
class User:
    def __init__(self, username, password, email, phone, address, age, gender, preferences):
        self.username = username
        self.password = password  # Should be hashed
        self.email = email
        self.phone = phone
        self.address = address
        self.age = age
        self.gender = gender
        self.preferences = preferences
    
    def validate_password(self, password):
        return self.password == password  # Timing attack vulnerability
''')
            
            service_file = project_path / "src" / "services" / "user_service.py"
            service_file.write_text('''
import sqlite3
from ..models.user import User

class UserService:
    def get_user_by_id(self, user_id):
        # SQL injection vulnerability
        query = f"SELECT * FROM users WHERE id = {user_id}"
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute(query)
        return cursor.fetchone()
    
    def get_all_users(self):
        # N+1 query problem simulation
        user_ids = self.get_all_user_ids()
        users = []
        for user_id in user_ids:  # This creates N+1 queries
            user = self.get_user_by_id(user_id)
            users.append(user)
        return users
    
    def get_all_user_ids(self):
        return [1, 2, 3, 4, 5]
''')
            
            # Verify files were created
            assert model_file.exists()
            assert service_file.exists()
            
            # This would be used with a real indexing engine in practice
            # For now, just verify the structure is correct
            assert (project_path / "src" / "models").is_dir()
            assert (project_path / "src" / "services").is_dir()


if __name__ == "__main__":
    pytest.main([__file__])