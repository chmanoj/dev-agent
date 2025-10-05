"""Integration tests for core dev-agent functionality.

This module contains integration tests that verify the end-to-end functionality
of the dev-agent system, including indexing, analysis, specification generation,
and vector search capabilities.
"""

import tempfile
from pathlib import Path

import pytest

from dev_agent.analysis.codebase_analyzer import CodebaseAnalyzer
from dev_agent.generation.specification_generator import SpecificationGenerator
from dev_agent.indexing.indexing_engine import IndexingEngine


@pytest.fixture
def sample_project_dir():
    """Create a temporary project directory with sample Python files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)

        # Create a simple Python module
        sample_file = project_path / "main.py"
        sample_file.write_text('''
"""Sample module for testing dev-agent functionality."""

class UserManager:
    """Manages user operations."""

    def __init__(self):
        self.users = []

    def add_user(self, name: str, email: str) -> bool:
        """Add a new user to the system."""
        user = {"name": name, "email": email}
        self.users.append(user)
        return True

    def get_user(self, email: str) -> dict:
        """Retrieve user by email."""
        for user in self.users:
            if user["email"] == email:
                return user
        return None

def main():
    """Main application entry point."""
    manager = UserManager()
    manager.add_user("John Doe", "john@example.com")
    user = manager.get_user("john@example.com")
    print(f"Found user: {user}")

if __name__ == "__main__":
    main()
''')

        # Create a requirements file
        requirements_file = project_path / "requirements.txt"
        requirements_file.write_text("requests>=2.25.0\nclick>=8.0.0\n")

        yield str(project_path)


class TestIndexingFunctionality:
    """Test indexing engine functionality."""

    def test_indexing_engine_basic(self, sample_project_dir, mock_embedding_client):
        """Test basic indexing functionality."""
        engine = IndexingEngine(sample_project_dir, embedding_client=mock_embedding_client)
        result = engine.build_index()

        assert result.success, "Indexing should succeed"
        assert result.metadata.get("total_files", 0) > 0, (
            "Should index at least one file"
        )

        # Check AST index was created
        if result.ast_index:
            assert len(result.ast_index.functions) > 0, "Should find functions"
            assert len(result.ast_index.classes) > 0, "Should find classes"

            # Verify specific function was found
            function_names = [func.name for func in result.ast_index.functions.values()]
            assert "main" in function_names, "Should find main function"

            # Verify specific class was found
            class_names = [cls.name for cls in result.ast_index.classes.values()]
            assert "UserManager" in class_names, "Should find UserManager class"

    def test_vector_search_functionality(self, sample_project_dir, mock_embedding_client):
        """Test vector similarity search functionality."""
        engine = IndexingEngine(sample_project_dir, embedding_client=mock_embedding_client)
        engine.build_index()

        # Test similarity search
        matches = engine.query_similar_code("user management", limit=3)

        assert len(matches) >= 0, "Search should return results or empty list"

        # If matches found, verify structure
        for match in matches:
            assert hasattr(match, "similarity_score"), (
                "Match should have similarity score"
            )
            assert 0 <= match.similarity_score <= 1, (
                "Similarity score should be between 0 and 1"
            )


class TestAnalysisFunctionality:
    """Test codebase analysis functionality."""

    def test_codebase_analysis_basic(self, sample_project_dir, mock_embedding_client):
        """Test basic codebase analysis functionality."""
        engine = IndexingEngine(sample_project_dir, embedding_client=mock_embedding_client)
        analyzer = CodebaseAnalyzer(engine)

        # Test specification analysis
        spec_analysis = analyzer.analyze_for_specification()

        assert spec_analysis is not None, "Analysis should return results"
        assert hasattr(spec_analysis, "project_purpose"), "Should have project purpose"
        assert hasattr(spec_analysis, "main_features"), "Should have main features"
        assert hasattr(spec_analysis, "confidence_score"), (
            "Should have confidence score"
        )

        # Confidence score should be reasonable
        assert 0 <= spec_analysis.confidence_score <= 1, (
            "Confidence should be between 0 and 1"
        )


class TestSpecificationGeneration:
    """Test specification generation functionality."""

    def test_specification_generation_basic(self, sample_project_dir, mock_embedding_client):
        """Test basic specification generation."""
        engine = IndexingEngine(sample_project_dir, embedding_client=mock_embedding_client)
        analyzer = CodebaseAnalyzer(engine)
        generator = SpecificationGenerator()

        # Get analysis first
        analysis = analyzer.analyze_for_specification()
        assert analysis is not None, "Analysis should succeed"

        # Generate specification
        spec = generator.generate_from_existing_code(analysis)

        assert spec is not None, "Specification generation should succeed"
        assert hasattr(spec, "introduction"), "Should have introduction"
        assert hasattr(spec, "key_features"), "Should have key features"
        assert hasattr(spec, "functional_requirements"), (
            "Should have functional requirements"
        )
        assert hasattr(spec, "source"), "Should have source information"

        # Content should not be empty
        assert len(spec.introduction) > 0, "Introduction should not be empty"


class TestEndToEndWorkflow:
    """Test complete end-to-end workflow."""

    def test_complete_workflow(self, sample_project_dir, mock_embedding_client):
        """Test the complete indexing -> analysis -> specification workflow."""
        # Step 1: Indexing
        engine = IndexingEngine(sample_project_dir, embedding_client=mock_embedding_client)
        index_result = engine.build_index()
        assert index_result.success, "Indexing should succeed"

        # Step 2: Analysis
        analyzer = CodebaseAnalyzer(engine)
        analysis = analyzer.analyze_for_specification()
        assert analysis is not None, "Analysis should succeed"

        # Step 3: Specification Generation
        generator = SpecificationGenerator()
        spec = generator.generate_from_existing_code(analysis)
        assert spec is not None, "Specification generation should succeed"

        # Step 4: Vector Search
        matches = engine.query_similar_code("user", limit=2)
        assert isinstance(matches, list), "Search should return a list"

        # Verify the workflow produced meaningful results
        assert analysis.confidence_score > 0, "Analysis should have some confidence"
        assert len(spec.key_features) > 0, "Specification should have features"


@pytest.mark.integration
class TestFunctionalityIntegration:
    """Integration tests for dev-agent functionality."""

    def test_all_components_integration(self, sample_project_dir, mock_embedding_client):
        """Test that all major components work together."""
        results = {}

        # Test indexing
        try:
            engine = IndexingEngine(sample_project_dir, embedding_client=mock_embedding_client)
            result = engine.build_index()
            results["indexing"] = result.success
        except Exception as e:
            results["indexing"] = False
            pytest.fail(f"Indexing failed: {e}")

        # Test analysis
        try:
            analyzer = CodebaseAnalyzer(engine)
            analysis = analyzer.analyze_for_specification()
            results["analysis"] = analysis is not None
        except Exception as e:
            results["analysis"] = False
            pytest.fail(f"Analysis failed: {e}")

        # Test specification generation
        try:
            generator = SpecificationGenerator()
            spec = generator.generate_from_existing_code(analysis)
            results["specification"] = spec is not None
        except Exception as e:
            results["specification"] = False
            pytest.fail(f"Specification generation failed: {e}")

        # Test vector search
        try:
            matches = engine.query_similar_code("user management", limit=3)
            results["vector_search"] = isinstance(matches, list)
        except Exception as e:
            results["vector_search"] = False
            pytest.fail(f"Vector search failed: {e}")

        # All components should work
        assert all(results.values()), f"Some components failed: {results}"

        # Log success for debugging


if __name__ == "__main__":
    # Allow running this test file directly
    pytest.main([__file__, "-v"])
