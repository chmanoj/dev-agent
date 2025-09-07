"""Tests for the CodebaseAnalyzer class."""

from unittest.mock import Mock

import pytest

from dev_agent.analysis.codebase_analyzer import CodebaseAnalyzer
from dev_agent.models.analysis import (
    ArchitectureInfo,
    CodeContext,
    CodeExample,
    CodePatterns,
    DesignAnalysis,
    SpecificationAnalysis,
)
from dev_agent.models.documents import Task
from dev_agent.models.enums import TaskStatus
from dev_agent.models.indexing import (
    ASTIndex,
    ClassDef,
    FunctionDef,
    Import,
    SymbolInfo,
)


class TestCodebaseAnalyzer:
    """Test cases for CodebaseAnalyzer."""

    @pytest.fixture
    def mock_indexing_engine(self):
        """Create a mock indexing engine."""
        engine = Mock()
        engine.get_symbol_map.return_value = {}
        engine.query_similar_code.return_value = []
        engine.ast_index = None
        return engine

    @pytest.fixture
    def sample_ast_index(self):
        """Create a sample AST index for testing."""
        functions = {
            "test_file.py:create_user:10": FunctionDef(
                name="create_user",
                parameters=["name", "email"],
                return_type="User",
                docstring="Create a new user",
                file_path="test_file.py",
                start_line=10,
                end_line=20
            ),
            "test_file.py:get_user:25": FunctionDef(
                name="get_user",
                parameters=["user_id"],
                return_type="User",
                docstring="Get user by ID",
                file_path="test_file.py",
                start_line=25,
                end_line=35
            ),
            "auth.py:login_user:5": FunctionDef(
                name="login_user",
                parameters=["username", "password"],
                return_type="bool",
                docstring="Authenticate user login",
                file_path="auth.py",
                start_line=5,
                end_line=15
            )
        }

        classes = {
            "models.py:User:1": ClassDef(
                name="User",
                base_classes=["BaseModel"],
                methods=[
                    FunctionDef(
                        name="__init__",
                        parameters=["self", "name", "email"],
                        return_type=None,
                        docstring="Initialize user",
                        file_path="models.py",
                        start_line=5,
                        end_line=10
                    )
                ],
                attributes=["name", "email", "id"],
                docstring="User model class",
                file_path="models.py",
                start_line=1,
                end_line=30
            ),
            "models.py:UserManager:35": ClassDef(
                name="UserManager",
                base_classes=[],
                methods=[
                    FunctionDef(
                        name="create_user",
                        parameters=["self", "data"],
                        return_type="User",
                        docstring="Create new user",
                        file_path="models.py",
                        start_line=40,
                        end_line=50
                    )
                ],
                attributes=[],
                docstring="Manages user operations",
                file_path="models.py",
                start_line=35,
                end_line=60
            )
        }

        imports = [
            Import(
                module="os",
                names=["path"],
                alias=None,
                file_path="test_file.py",
                line_number=1
            ),
            Import(
                module="pytest",
                names=["fixture"],
                alias=None,
                file_path="test_user.py",
                line_number=2
            ),
            Import(
                module="flask",
                names=["Flask"],
                alias=None,
                file_path="app.py",
                line_number=1
            )
        ]

        symbols = {
            "test_file.py:USER_CONSTANT:1": SymbolInfo(
                name="USER_CONSTANT",
                symbol_type="variable",
                file_path="test_file.py",
                line_number=1,
                scope="module"
            )
        }

        file_metadata = {
            "test_file.py": {
                "language": "python",
                "line_count": 50,
                "char_count": 1200,
                "function_count": 2,
                "class_count": 0,
                "import_count": 1,
                "symbol_count": 1,
                "file_size_bytes": 1200
            },
            "models.py": {
                "language": "python",
                "line_count": 80,
                "char_count": 2000,
                "function_count": 2,
                "class_count": 2,
                "import_count": 0,
                "symbol_count": 0,
                "file_size_bytes": 2000
            },
            "auth.py": {
                "language": "python",
                "line_count": 30,
                "char_count": 800,
                "function_count": 1,
                "class_count": 0,
                "import_count": 0,
                "symbol_count": 0,
                "file_size_bytes": 800
            },
            "test_user.py": {
                "language": "python",
                "line_count": 40,
                "char_count": 1000,
                "function_count": 0,
                "class_count": 0,
                "import_count": 1,
                "symbol_count": 0,
                "file_size_bytes": 1000
            }
        }

        return ASTIndex(
            functions=functions,
            classes=classes,
            imports=imports,
            symbols=symbols,
            file_metadata=file_metadata
        )

    @pytest.fixture
    def analyzer_with_index(self, mock_indexing_engine, sample_ast_index):
        """Create analyzer with sample AST index."""
        mock_indexing_engine.get_symbol_map.return_value = sample_ast_index.symbols
        mock_indexing_engine.ast_index = sample_ast_index
        analyzer = CodebaseAnalyzer(mock_indexing_engine)
        analyzer.ast_index = sample_ast_index
        return analyzer

    def test_init_with_no_index(self, mock_indexing_engine):
        """Test analyzer initialization with no index."""
        mock_indexing_engine.get_symbol_map.return_value = {}
        analyzer = CodebaseAnalyzer(mock_indexing_engine)
        assert analyzer.ast_index is None

    def test_init_with_index(self, analyzer_with_index, sample_ast_index):
        """Test analyzer initialization with index."""
        assert analyzer_with_index.ast_index == sample_ast_index

    def test_analyze_for_specification_no_index(self, mock_indexing_engine):
        """Test specification analysis with no index."""
        analyzer = CodebaseAnalyzer(mock_indexing_engine)
        result = analyzer.analyze_for_specification()

        assert isinstance(result, SpecificationAnalysis)
        assert result.project_purpose == "Unable to analyze - no index available"
        assert result.confidence_score == 0.0

    def test_analyze_for_specification_with_index(self, analyzer_with_index):
        """Test specification analysis with index."""
        result = analyzer_with_index.analyze_for_specification()

        assert isinstance(result, SpecificationAnalysis)
        assert result.project_purpose != "Unable to analyze - no index available"
        assert result.confidence_score > 0.0
        assert len(result.main_features) > 0
        assert len(result.user_roles) > 0

    def test_analyze_for_design_no_index(self, mock_indexing_engine):
        """Test design analysis with no index."""
        analyzer = CodebaseAnalyzer(mock_indexing_engine)
        result = analyzer.analyze_for_design()

        assert isinstance(result, DesignAnalysis)
        assert result.architecture_overview == "Unable to analyze - no index available"

    def test_analyze_for_design_with_index(self, analyzer_with_index):
        """Test design analysis with index."""
        result = analyzer_with_index.analyze_for_design()

        assert isinstance(result, DesignAnalysis)
        assert result.architecture_overview != "Unable to analyze - no index available"
        assert len(result.components) >= 0
        assert len(result.data_models) > 0  # Should find User class

    def test_extract_architecture_patterns_no_index(self, mock_indexing_engine):
        """Test architecture pattern extraction with no index."""
        analyzer = CodebaseAnalyzer(mock_indexing_engine)
        result = analyzer.extract_architecture_patterns()

        assert isinstance(result, ArchitectureInfo)
        assert len(result.patterns) == 0
        assert len(result.components) == 0

    def test_extract_architecture_patterns_with_index(self, analyzer_with_index):
        """Test architecture pattern extraction with index."""
        result = analyzer_with_index.extract_architecture_patterns()

        assert isinstance(result, ArchitectureInfo)
        assert "Python" in result.technology_stack

    def test_identify_code_patterns_no_index(self, mock_indexing_engine):
        """Test code pattern identification with no index."""
        analyzer = CodebaseAnalyzer(mock_indexing_engine)
        result = analyzer.identify_code_patterns()

        assert isinstance(result, CodePatterns)
        assert len(result.naming_conventions) == 0

    def test_identify_code_patterns_with_index(self, analyzer_with_index):
        """Test code pattern identification with index."""
        result = analyzer_with_index.identify_code_patterns()

        assert isinstance(result, CodePatterns)
        # Should detect snake_case functions and PascalCase classes
        naming_patterns = result.naming_conventions
        assert len(naming_patterns) > 0

    def test_find_similar_implementations_no_matches(self, analyzer_with_index):
        """Test finding similar implementations with no matches."""
        analyzer_with_index.indexing_engine.query_similar_code.return_value = []

        result = analyzer_with_index.find_similar_implementations("test query")
        assert isinstance(result, list)
        assert len(result) == 0

    def test_find_similar_implementations_with_matches(self, analyzer_with_index):
        """Test finding similar implementations with matches."""
        # Mock a similarity match
        mock_chunk = Mock()
        mock_chunk.content = "def test_function():\n    pass"
        mock_chunk.file_path = "test.py"
        mock_chunk.start_line = 1
        mock_chunk.end_line = 2
        mock_chunk.chunk_type = "function"
        mock_chunk.language = "python"

        mock_match = Mock()
        mock_match.chunk = mock_chunk
        mock_match.similarity_score = 0.8

        analyzer_with_index.indexing_engine.query_similar_code.return_value = [mock_match]

        result = analyzer_with_index.find_similar_implementations("test query")
        assert len(result) == 1
        assert isinstance(result[0], CodeExample)
        assert result[0].similarity_score == 0.8

    def test_get_context_for_task_no_index(self, mock_indexing_engine):
        """Test getting context for task with no index."""
        analyzer = CodebaseAnalyzer(mock_indexing_engine)
        task = Task(
            id="test_task",
            title="Test Task",
            description="Create a test function",
            requirements_refs=[],
            subtasks=[],
            status=TaskStatus.NOT_STARTED
        )

        result = analyzer.get_context_for_task(task)
        assert isinstance(result, CodeContext)
        assert result.task_id == "test_task"
        assert len(result.relevant_files) == 0

    def test_get_context_for_task_with_index(self, analyzer_with_index):
        """Test getting context for task with index."""
        task = Task(
            id="user_task",
            title="User Task",
            description="Create user management functionality",
            requirements_refs=[],
            subtasks=[],
            status=TaskStatus.NOT_STARTED
        )

        result = analyzer_with_index.get_context_for_task(task)
        assert isinstance(result, CodeContext)
        assert result.task_id == "user_task"
        # Should find relevant files based on "user" keyword
        assert len(result.relevant_files) > 0

    def test_infer_project_purpose(self, analyzer_with_index):
        """Test project purpose inference."""
        purpose = analyzer_with_index._infer_project_purpose()
        assert isinstance(purpose, str)
        assert purpose != "Unknown project purpose"
        # Should detect user-related functionality
        assert "user" in purpose.lower()

    def test_extract_main_features(self, analyzer_with_index):
        """Test main feature extraction."""
        features = analyzer_with_index._extract_main_features()
        assert isinstance(features, list)
        assert len(features) > 0

    def test_identify_user_roles(self, analyzer_with_index):
        """Test user role identification."""
        roles = analyzer_with_index._identify_user_roles()
        assert isinstance(roles, list)
        assert len(roles) > 0
        # Should find "User" role from function names
        assert any("user" in role.lower() for role in roles)

    def test_gather_requirement_evidence(self, analyzer_with_index):
        """Test requirement evidence gathering."""
        evidence = analyzer_with_index._gather_requirement_evidence()
        assert isinstance(evidence, list)
        # Should find CRUD operations evidence
        assert len(evidence) > 0
        assert any("Data Management" in ev.requirement_type for ev in evidence)

    def test_analyze_technology_constraints(self, analyzer_with_index):
        """Test technology constraint analysis."""
        constraints = analyzer_with_index._analyze_technology_constraints()
        assert isinstance(constraints, list)
        assert "Python 3.x required" in constraints
        # Should detect web framework from Flask import
        assert any("Web framework" in constraint for constraint in constraints)

    def test_analyze_external_dependencies(self, analyzer_with_index):
        """Test external dependency analysis."""
        dependencies = analyzer_with_index._analyze_external_dependencies()
        assert isinstance(dependencies, list)
        # Should find pytest and flask
        assert "pytest" in dependencies
        assert "flask" in dependencies

    def test_calculate_specification_confidence(self, analyzer_with_index):
        """Test specification confidence calculation."""
        confidence = analyzer_with_index._calculate_specification_confidence()
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0
        # With 4 files and 3 functions, should have reasonable confidence
        assert confidence > 0.0

    def test_generate_architecture_overview(self, analyzer_with_index):
        """Test architecture overview generation."""
        overview = analyzer_with_index._generate_architecture_overview()
        assert isinstance(overview, str)
        assert "files" in overview
        assert "functions" in overview
        assert "classes" in overview

    def test_analyze_components(self, analyzer_with_index):
        """Test component analysis."""
        components = analyzer_with_index._analyze_components()
        assert isinstance(components, list)
        # Should identify components based on directory structure
        # Note: With flat file structure in test, may not find multi-file components

    def test_extract_data_models(self, analyzer_with_index):
        """Test data model extraction."""
        models = analyzer_with_index._extract_data_models()
        assert isinstance(models, list)
        assert len(models) > 0
        # Should find User class
        assert any(model["name"] == "User" for model in models)

    def test_identify_api_interfaces(self, analyzer_with_index):
        """Test API interface identification."""
        interfaces = analyzer_with_index._identify_api_interfaces()
        assert isinstance(interfaces, list)
        # May not find API interfaces in test data

    def test_detect_design_patterns(self, analyzer_with_index):
        """Test design pattern detection."""
        patterns = analyzer_with_index._detect_design_patterns()
        assert isinstance(patterns, list)
        # Should detect inheritance hierarchy from User extending BaseModel
        assert any("Inheritance" in pattern for pattern in patterns)

    def test_calculate_quality_metrics(self, analyzer_with_index):
        """Test quality metrics calculation."""
        metrics = analyzer_with_index._calculate_quality_metrics()
        assert isinstance(metrics, dict)
        assert "avg_functions_per_file" in metrics
        assert "avg_methods_per_class" in metrics
        assert "documentation_coverage" in metrics
        # All functions have docstrings in test data
        assert metrics["documentation_coverage"] == 1.0

    def test_identify_technical_debt(self, analyzer_with_index):
        """Test technical debt identification."""
        debt = analyzer_with_index._identify_technical_debt()
        assert isinstance(debt, list)
        # Test data should be clean

    def test_generate_design_recommendations(self, analyzer_with_index):
        """Test design recommendation generation."""
        recommendations = analyzer_with_index._generate_design_recommendations()
        assert isinstance(recommendations, list)
        # Should recommend increasing test coverage (only 1 test file out of 4)
        assert any("test coverage" in rec.lower() for rec in recommendations)

    def test_analyze_naming_conventions(self, analyzer_with_index):
        """Test naming convention analysis."""
        patterns = analyzer_with_index._analyze_naming_conventions()
        assert isinstance(patterns, list)
        assert len(patterns) > 0
        # Should detect snake_case functions and PascalCase classes
        naming_descriptions = [p.description for p in patterns]
        assert any("snake_case" in desc for desc in naming_descriptions)
        assert any("PascalCase" in desc for desc in naming_descriptions)

    def test_detect_structural_patterns(self, analyzer_with_index):
        """Test structural pattern detection."""
        patterns = analyzer_with_index._detect_structural_patterns()
        assert isinstance(patterns, list)
        # Should detect that classes have __init__ methods
        if patterns:
            assert any("__init__" in pattern.description for pattern in patterns)

    def test_analyze_import_patterns(self, analyzer_with_index):
        """Test import pattern analysis."""
        patterns = analyzer_with_index._analyze_import_patterns()
        assert isinstance(patterns, list)
        # Should detect absolute imports and standard library usage
        if patterns:
            descriptions = [p.description for p in patterns]
            assert any("absolute" in desc.lower() for desc in descriptions) or \
                   any("standard library" in desc.lower() for desc in descriptions)

    def test_find_relevant_files(self, analyzer_with_index):
        """Test relevant file finding."""
        task = Task(
            id="user_task",
            title="User Task",
            description="user management functionality",
            requirements_refs=[],
            subtasks=[],
            status=TaskStatus.NOT_STARTED
        )

        files = analyzer_with_index._find_relevant_files(task)
        assert isinstance(files, list)
        # Should find files with user-related content
        assert len(files) > 0

    def test_determine_required_imports(self, analyzer_with_index):
        """Test required import determination."""
        task = Task(
            id="test_task",
            title="Test Task",
            description="create test functionality",
            requirements_refs=[],
            subtasks=[],
            status=TaskStatus.NOT_STARTED
        )

        imports = analyzer_with_index._determine_required_imports(task)
        assert isinstance(imports, list)
        # Should suggest test-related imports
        assert any("test" in imp.lower() for imp in imports)

    def test_extract_style_guidelines(self, analyzer_with_index):
        """Test style guideline extraction."""
        guidelines = analyzer_with_index._extract_style_guidelines()
        assert isinstance(guidelines, dict)
        # Should extract naming conventions
        if "function_naming" in guidelines:
            assert guidelines["function_naming"] in ["snake_case", "camelCase"]
        if "class_naming" in guidelines:
            assert guidelines["class_naming"] == "PascalCase"


if __name__ == "__main__":
    pytest.main([__file__])
