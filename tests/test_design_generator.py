"""Tests for design generator."""

from unittest.mock import Mock

import pytest

from dev_agent.generation.design_generator import DesignGenerator
from dev_agent.interfaces.analysis_interface import ICodebaseAnalyzer
from dev_agent.interfaces.cli_interface import ICLIInterface
from dev_agent.models.analysis import ComponentAnalysis, DesignAnalysis
from dev_agent.models.documents import (
    ArchitectureDescription,
    DesignDocument,
    ErrorHandlingStrategy,
    Requirement,
    SpecificationDocument,
    TestingStrategy,
)
from dev_agent.models.enums import Priority, SpecificationSource


class TestDesignGenerator:
    """Test cases for DesignGenerator."""

    @pytest.fixture
    def mock_cli(self):
        """Create a mock CLI interface."""
        cli = Mock(spec=ICLIInterface)
        cli.display_message = Mock()
        cli.get_user_input = Mock()
        cli.request_approval = Mock(return_value=True)
        return cli

    @pytest.fixture
    def mock_analyzer(self):
        """Create a mock codebase analyzer."""
        analyzer = Mock(spec=ICodebaseAnalyzer)
        return analyzer

    @pytest.fixture
    def generator(self, mock_analyzer, mock_cli):
        """Create a design generator with mocks."""
        return DesignGenerator(codebase_analyzer=mock_analyzer, cli_interface=mock_cli)

    @pytest.fixture
    def generator_no_cli(self, mock_analyzer):
        """Create a design generator without CLI."""
        return DesignGenerator(codebase_analyzer=mock_analyzer)

    @pytest.fixture
    def sample_specification(self):
        """Create sample specification document."""
        requirements = [
            Requirement(
                id="FR-1",
                user_story="As a user, I want to manage data efficiently, so that I can store and retrieve information",
                acceptance_criteria=[
                    "WHEN I create data THEN the system SHALL validate and store it",
                    "WHEN I retrieve data THEN the system SHALL return accurate information",
                ],
                priority=Priority.HIGH,
            ),
            Requirement(
                id="FR-2",
                user_story="As a user, I want secure authentication, so that my data is protected",
                acceptance_criteria=[
                    "WHEN I login THEN the system SHALL verify my credentials",
                    "WHEN I access protected resources THEN the system SHALL check authorization",
                ],
                priority=Priority.HIGH,
            ),
        ]

        return SpecificationDocument(
            introduction="Test application for data management",
            key_features=["Data Management", "User Authentication", "API Access"],
            functional_requirements=requirements,
            source=SpecificationSource.EXISTING_CODE,
            version="1.0",
            approved=True,
        )

    @pytest.fixture
    def sample_design_analysis(self):
        """Create sample design analysis."""
        component_analysis = ComponentAnalysis(
            name="UserService",
            purpose="Handles user management operations",
            interfaces=["IUserService"],
            dependencies=["UserRepository", "AuthService"],
            internal_structure={"files": 3, "functions": 15, "classes": 2},
            complexity_score=2.5,
        )

        return DesignAnalysis(
            architecture_overview="The system follows a service-oriented architecture with clear separation of concerns",
            components=[component_analysis],
            data_models=[
                {
                    "name": "User",
                    "attributes": ["id", "username", "email", "created_at"],
                    "relationships": ["One-to-many with Session"],
                }
            ],
            api_interfaces=[
                {
                    "name": "user_login",
                    "parameters": ["username", "password"],
                    "return_type": "AuthToken",
                    "docstring": "Authenticate user and return token",
                }
            ],
            design_patterns=["Repository Pattern", "Service Layer Pattern"],
            quality_metrics={
                "documentation_coverage": 0.8,
                "avg_methods_per_class": 7.5,
            },
            technical_debt=["Some functions lack proper error handling"],
            recommendations=[
                "Consider adding more unit tests",
                "Improve error handling",
            ],
        )

    def test_generate_from_specification_with_analysis(
        self, generator, sample_specification, sample_design_analysis
    ):
        """Test generating design from specification with existing analysis."""
        design = generator.generate_from_specification(
            sample_specification, sample_design_analysis
        )

        assert isinstance(design, DesignDocument)
        assert design.version == "1.0"
        assert not design.approved
        assert "service-oriented architecture" in design.overview.lower()
        assert len(design.components) > 0
        assert len(design.data_models) > 0
        assert len(design.interfaces) > 0
        assert design.error_handling is not None
        assert design.testing_strategy is not None

    def test_generate_from_specification_without_analysis(
        self, generator, sample_specification
    ):
        """Test generating design from specification without existing analysis."""
        empty_analysis = DesignAnalysis(
            architecture_overview="",
            components=[],
            data_models=[],
            api_interfaces=[],
            design_patterns=[],
            quality_metrics={},
            technical_debt=[],
            recommendations=[],
        )

        design = generator.generate_from_specification(
            sample_specification, empty_analysis
        )

        assert isinstance(design, DesignDocument)
        assert design.overview is not None
        assert design.architecture is not None
        # Should generate components based on requirements even without analysis
        assert len(design.components) > 0

    def test_architecture_description_generation(
        self, generator, sample_specification, sample_design_analysis
    ):
        """Test architecture description generation."""
        design = generator.generate_from_specification(
            sample_specification, sample_design_analysis
        )

        assert isinstance(design.architecture, ArchitectureDescription)
        assert design.architecture.overview is not None
        assert len(design.architecture.patterns) > 0
        assert "Repository Pattern" in design.architecture.patterns
        assert "Service Layer Pattern" in design.architecture.patterns
        assert len(design.architecture.components) > 0

    def test_component_generation_from_analysis(
        self, generator, sample_specification, sample_design_analysis
    ):
        """Test component generation from existing analysis."""
        design = generator.generate_from_specification(
            sample_specification, sample_design_analysis
        )

        # Should use components from analysis
        user_service_component = next(
            (c for c in design.components if c.name == "UserService"), None
        )
        assert user_service_component is not None
        assert (
            user_service_component.description == "Handles user management operations"
        )
        assert "IUserService" in user_service_component.interfaces
        assert "UserRepository" in user_service_component.dependencies

    def test_component_generation_from_requirements(
        self, generator, sample_specification
    ):
        """Test component generation from requirements when no analysis available."""
        empty_analysis = DesignAnalysis(
            architecture_overview="",
            components=[],
            data_models=[],
            api_interfaces=[],
            design_patterns=[],
            quality_metrics={},
            technical_debt=[],
            recommendations=[],
        )

        design = generator.generate_from_specification(
            sample_specification, empty_analysis
        )

        # Should generate components based on requirements
        component_names = [c.name for c in design.components]
        assert any("Data Management" in name for name in component_names)
        assert any("Authentication" in name for name in component_names)

    def test_data_model_generation(
        self, generator, sample_specification, sample_design_analysis
    ):
        """Test data model generation."""
        design = generator.generate_from_specification(
            sample_specification, sample_design_analysis
        )

        assert len(design.data_models) > 0
        user_model = next((m for m in design.data_models if m.name == "User"), None)
        assert user_model is not None
        assert "id" in user_model.fields
        assert "username" in user_model.fields
        assert user_model.fields["id"] == "int"
        assert user_model.fields["username"] == "str"

    def test_interface_generation_from_analysis(
        self, generator, sample_specification, sample_design_analysis
    ):
        """Test interface generation from analysis."""
        design = generator.generate_from_specification(
            sample_specification, sample_design_analysis
        )

        assert len(design.interfaces) > 0
        # Should generate interfaces based on API data
        interface_names = [i.name for i in design.interfaces]
        assert len(interface_names) > 0

    def test_error_handling_strategy_generation(
        self, generator, sample_specification, sample_design_analysis
    ):
        """Test error handling strategy generation."""
        design = generator.generate_from_specification(
            sample_specification, sample_design_analysis
        )

        assert isinstance(design.error_handling, ErrorHandlingStrategy)
        assert len(design.error_handling.error_categories) > 0
        assert len(design.error_handling.recovery_mechanisms) > 0
        assert design.error_handling.logging_strategy is not None

        # Should include relevant error categories based on requirements
        categories = design.error_handling.error_categories
        assert any(
            "Data" in category or "Storage" in category for category in categories
        )
        assert any("Auth" in category for category in categories)

    def test_testing_strategy_generation(
        self, generator, sample_specification, sample_design_analysis
    ):
        """Test testing strategy generation."""
        design = generator.generate_from_specification(
            sample_specification, sample_design_analysis
        )

        assert isinstance(design.testing_strategy, TestingStrategy)
        assert design.testing_strategy.unit_testing is not None
        assert design.testing_strategy.integration_testing is not None
        assert design.testing_strategy.performance_testing is not None
        assert 0.0 < design.testing_strategy.test_coverage_target <= 1.0

        # Should set high coverage target based on good documentation coverage
        assert design.testing_strategy.test_coverage_target >= 0.8

    def test_refine_design(
        self, generator, sample_specification, sample_design_analysis
    ):
        """Test refining design based on feedback."""
        original_design = generator.generate_from_specification(
            sample_specification, sample_design_analysis
        )

        feedback = "Add more components for better modularity"
        refined_design = generator.refine_design(original_design, feedback)

        assert refined_design.version != original_design.version
        assert not refined_design.approved
        # Should add components based on feedback
        assert len(refined_design.components) > len(original_design.components)

    def test_format_design_document(
        self, generator, sample_specification, sample_design_analysis
    ):
        """Test formatting design document as markdown."""
        design = generator.generate_from_specification(
            sample_specification, sample_design_analysis
        )
        formatted = generator.format_design_document(design)

        assert isinstance(formatted, str)
        assert "# Design Document" in formatted
        assert "## Overview" in formatted
        assert "## Architecture" in formatted
        assert "## Components and Interfaces" in formatted
        assert "## Data Models" in formatted
        assert "## Error Handling" in formatted
        assert "## Testing Strategy" in formatted
        assert "**Status:** Draft" in formatted

    def test_format_design_document_with_components(
        self, generator, sample_specification, sample_design_analysis
    ):
        """Test formatting design document with components."""
        design = generator.generate_from_specification(
            sample_specification, sample_design_analysis
        )
        formatted = generator.format_design_document(design)

        # Should include component information
        assert "UserService" in formatted
        assert "**Interfaces:**" in formatted
        assert "**Dependencies:**" in formatted

    def test_format_design_document_with_data_models(
        self, generator, sample_specification, sample_design_analysis
    ):
        """Test formatting design document with data models."""
        design = generator.generate_from_specification(
            sample_specification, sample_design_analysis
        )
        formatted = generator.format_design_document(design)

        # Should include data model information
        assert "### User" in formatted
        assert "**Fields:**" in formatted
        assert "`id`: int" in formatted
        assert "`username`: str" in formatted

    def test_request_user_approval_with_cli(
        self, generator, sample_specification, sample_design_analysis
    ):
        """Test requesting user approval with CLI interface."""
        design = generator.generate_from_specification(
            sample_specification, sample_design_analysis
        )

        result = generator.request_user_approval(design)

        assert result is True
        assert design.approved is True
        generator.cli_interface.request_approval.assert_called_once()

    def test_request_user_approval_without_cli(
        self, generator_no_cli, sample_specification, sample_design_analysis
    ):
        """Test requesting user approval without CLI interface."""
        design = generator_no_cli.generate_from_specification(
            sample_specification, sample_design_analysis
        )

        result = generator_no_cli.request_user_approval(design)

        assert result is True
        assert design.approved is True

    def test_version_increment(
        self, generator, sample_specification, sample_design_analysis
    ):
        """Test version increment functionality."""
        original_design = generator.generate_from_specification(
            sample_specification, sample_design_analysis
        )
        original_design.version = "1.0"

        refined_design = generator.refine_design(original_design, "Some feedback")

        assert refined_design.version == "1.1"

    def test_basic_field_generation_for_user_model(self, generator):
        """Test basic field generation for User model."""
        fields = generator._generate_basic_fields_for_model("User")

        assert "id" in fields
        assert "username" in fields
        assert "email" in fields
        assert "created_at" in fields
        assert "is_active" in fields
        assert fields["id"] == "int"
        assert fields["username"] == "str"
        assert fields["is_active"] == "bool"

    def test_basic_field_generation_for_generic_model(self, generator):
        """Test basic field generation for generic model."""
        fields = generator._generate_basic_fields_for_model("CustomModel")

        assert "id" in fields
        assert "name" in fields
        assert "description" in fields
        assert "created_at" in fields

    def test_relationship_generation(self, generator):
        """Test relationship generation between models."""
        all_models = {"User", "Session", "DataRecord"}

        user_relationships = generator._generate_basic_relationships_for_model(
            "User", all_models
        )
        session_relationships = generator._generate_basic_relationships_for_model(
            "Session", all_models
        )

        assert any("Session" in rel for rel in user_relationships)
        assert any("User" in rel for rel in session_relationships)


class TestDesignGeneratorIntegration:
    """Integration tests for design generator."""

    @pytest.fixture
    def real_analyzer(self):
        """Create a real codebase analyzer for integration tests."""
        # This would be a real analyzer in integration tests
        analyzer = Mock(spec=ICodebaseAnalyzer)
        return analyzer

    @pytest.fixture
    def integration_generator(self, real_analyzer):
        """Create design generator for integration tests."""
        return DesignGenerator(codebase_analyzer=real_analyzer)

    def test_end_to_end_design_generation(self, integration_generator):
        """Test end-to-end design generation process."""
        # Create a comprehensive specification
        requirements = [
            Requirement(
                id="FR-1",
                user_story="As a developer, I want a CLI interface, so that I can interact with the system",
                acceptance_criteria=[
                    "WHEN I run commands THEN the system SHALL respond appropriately"
                ],
                priority=Priority.HIGH,
            ),
            Requirement(
                id="FR-2",
                user_story="As a user, I want data persistence, so that my information is saved",
                acceptance_criteria=[
                    "WHEN I save data THEN it SHALL be stored permanently"
                ],
                priority=Priority.HIGH,
            ),
            Requirement(
                id="FR-3",
                user_story="As a user, I want API access, so that I can integrate with other systems",
                acceptance_criteria=[
                    "WHEN I make API calls THEN I SHALL receive proper responses"
                ],
                priority=Priority.MEDIUM,
            ),
        ]

        spec = SpecificationDocument(
            introduction="Comprehensive test application",
            key_features=["CLI Interface", "Data Management", "API Integration"],
            functional_requirements=requirements,
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=True,
        )

        # Create comprehensive analysis
        analysis = DesignAnalysis(
            architecture_overview="Multi-layered architecture with clear separation",
            components=[],
            data_models=[],
            api_interfaces=[],
            design_patterns=["MVC", "Repository"],
            quality_metrics={"documentation_coverage": 0.75},
            technical_debt=["Some legacy code needs refactoring"],
            recommendations=["Improve test coverage", "Add more documentation"],
        )

        # Generate design
        design = integration_generator.generate_from_specification(spec, analysis)

        # Verify comprehensive design generation
        assert isinstance(design, DesignDocument)
        assert design.overview is not None
        assert design.architecture is not None
        assert (
            len(design.components) >= 3
        )  # Should generate components for CLI, Data, API
        assert design.error_handling is not None
        assert design.testing_strategy is not None

        # Verify architecture includes patterns from analysis
        assert "MVC" in design.architecture.patterns
        assert "Repository" in design.architecture.patterns

        # Verify components cover all requirement areas
        component_names = [c.name.lower() for c in design.components]
        assert any("data" in name for name in component_names)
        assert any("api" in name for name in component_names)

        # Test formatting
        formatted = integration_generator.format_design_document(design)
        assert len(formatted) > 1000  # Should be comprehensive
        assert "# Design Document" in formatted

        # Test refinement
        refined = integration_generator.refine_design(
            design, "Add more security considerations"
        )
        assert refined.version != design.version
        assert not refined.approved

    def test_design_consistency_across_generations(self, integration_generator):
        """Test that design generation is consistent across multiple runs."""
        spec = SpecificationDocument(
            introduction="Consistent test application",
            key_features=["Feature A", "Feature B"],
            functional_requirements=[
                Requirement(
                    id="FR-1",
                    user_story="As a user, I want feature A, so that I can do task A",
                    acceptance_criteria=["WHEN I use feature A THEN it SHALL work"],
                    priority=Priority.HIGH,
                )
            ],
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=True,
        )

        analysis = DesignAnalysis(
            architecture_overview="Simple architecture",
            components=[],
            data_models=[],
            api_interfaces=[],
            design_patterns=[],
            quality_metrics={},
            technical_debt=[],
            recommendations=[],
        )

        # Generate design multiple times
        design1 = integration_generator.generate_from_specification(spec, analysis)
        design2 = integration_generator.generate_from_specification(spec, analysis)

        # Should be consistent
        assert design1.overview == design2.overview
        assert len(design1.components) == len(design2.components)
        assert design1.architecture.overview == design2.architecture.overview
