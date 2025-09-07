"""Tests for specification generator."""

from unittest.mock import Mock

import pytest

from dev_agent.generation.specification_generator import SpecificationGenerator
from dev_agent.interfaces.cli_interface import ICLIInterface
from dev_agent.models.analysis import (
    RequirementEvidence,
    SpecificationAnalysis,
)
from dev_agent.models.documents import (
    SpecificationDocument,
)
from dev_agent.models.enums import Priority, SpecificationSource


class TestSpecificationGenerator:
    """Test cases for SpecificationGenerator."""

    @pytest.fixture
    def mock_cli(self):
        """Create a mock CLI interface."""
        cli = Mock(spec=ICLIInterface)
        cli.display_message = Mock()
        cli.get_user_input = Mock()
        cli.request_approval = Mock(return_value=True)
        return cli

    @pytest.fixture
    def generator(self, mock_cli):
        """Create a specification generator with mock CLI."""
        return SpecificationGenerator(cli_interface=mock_cli)

    @pytest.fixture
    def generator_no_cli(self):
        """Create a specification generator without CLI."""
        return SpecificationGenerator()

    @pytest.fixture
    def sample_analysis(self):
        """Create sample specification analysis."""
        evidence = RequirementEvidence(
            requirement_type="Data Management",
            description="System provides CRUD operations for data management",
            supporting_files=["models/user.py", "services/user_service.py"],
            supporting_functions=["create_user", "update_user", "delete_user"],
            confidence=0.8,
            code_examples=[]
        )

        return SpecificationAnalysis(
            project_purpose="Web application for user management",
            main_features=["User Registration", "User Authentication", "Profile Management"],
            user_roles=["User", "Admin"],
            functional_areas=["Authentication", "User Management", "Profile"],
            requirement_evidence=[evidence],
            technology_constraints=["Python 3.x required", "Web framework dependency"],
            external_dependencies=["flask", "sqlalchemy"],
            confidence_score=0.8
        )

    def test_generate_from_existing_code(self, generator, sample_analysis):
        """Test generating specification from existing code analysis."""
        spec = generator.generate_from_existing_code(sample_analysis)

        assert isinstance(spec, SpecificationDocument)
        assert spec.source == SpecificationSource.EXISTING_CODE
        assert spec.approved is False
        assert "web application for user management" in spec.introduction
        assert len(spec.key_features) > 0
        assert len(spec.functional_requirements) > 0
        assert spec.version == "1.0"

        # Check that requirements have proper structure
        req = spec.functional_requirements[0]
        assert req.id.startswith("FR-")
        assert "As a" in req.user_story
        assert len(req.acceptance_criteria) >= 2
        assert req.source_analysis is not None
        assert req.source_analysis.confidence_score == 0.8

    def test_generate_from_user_input(self, generator):
        """Test generating specification from user input."""
        user_requirements = [
            "Create user registration system",
            "Implement user authentication",
            "Provide profile management features"
        ]

        spec = generator.generate_from_user_input(user_requirements)

        assert isinstance(spec, SpecificationDocument)
        assert spec.source == SpecificationSource.USER_INPUT
        assert spec.approved is False
        assert len(spec.functional_requirements) == 3
        assert spec.version == "1.0"

        # Check requirements structure
        for i, req in enumerate(spec.functional_requirements):
            assert req.id == f"FR-{i+1}"
            assert "As a user" in req.user_story
            assert len(req.acceptance_criteria) >= 2
            assert req.priority == Priority.MEDIUM

    def test_generate_from_user_input_with_cli_interaction(self, generator, mock_cli):
        """Test generating specification with CLI interaction for requirements."""
        # Mock CLI to return requirements
        mock_cli.get_user_input.side_effect = [
            "Create user accounts",
            "Manage user profiles",
            ""  # Empty input to stop
        ]

        spec = generator.generate_from_user_input([])

        assert len(spec.functional_requirements) == 2
        assert mock_cli.get_user_input.call_count >= 2
        mock_cli.display_message.assert_called()

    def test_refine_specification(self, generator, sample_analysis):
        """Test refining specification based on feedback."""
        original_spec = generator.generate_from_existing_code(sample_analysis)
        feedback = "Add more requirements for security features"

        refined_spec = generator.refine_specification(original_spec, feedback)

        assert refined_spec.version != original_spec.version
        assert refined_spec.approved is False
        assert refined_spec.approval_timestamp is None
        # Should have added requirements based on feedback
        assert len(refined_spec.functional_requirements) >= len(original_spec.functional_requirements)

    def test_format_specification_document(self, generator, sample_analysis):
        """Test formatting specification document as markdown."""
        spec = generator.generate_from_existing_code(sample_analysis)
        formatted = generator.format_specification_document(spec)

        assert "# Requirements Document" in formatted
        assert "## Introduction" in formatted
        assert "## Key Features" in formatted
        assert "## Requirements" in formatted
        assert "### Requirement 1" in formatted
        assert "**User Story:**" in formatted
        assert "#### Acceptance Criteria" in formatted
        assert "## Document Metadata" in formatted
        assert f"**Version:** {spec.version}" in formatted
        assert "**Status:** Draft" in formatted

    def test_format_specification_with_source_analysis(self, generator, sample_analysis):
        """Test formatting specification with source analysis information."""
        spec = generator.generate_from_existing_code(sample_analysis)
        formatted = generator.format_specification_document(spec)

        assert "#### Supporting Code Analysis" in formatted
        assert "**Files:**" in formatted
        assert "**Functions:**" in formatted
        assert "**Confidence:**" in formatted

    def test_request_user_approval_with_cli(self, generator, mock_cli, sample_analysis):
        """Test requesting user approval with CLI interface."""
        spec = generator.generate_from_existing_code(sample_analysis)
        mock_cli.request_approval.return_value = True

        approved = generator.request_user_approval(spec)

        assert approved is True
        assert spec.approved is True
        assert spec.approval_timestamp is not None
        mock_cli.request_approval.assert_called_once()

    def test_request_user_approval_without_cli(self, generator_no_cli, sample_analysis):
        """Test requesting user approval without CLI interface."""
        spec = generator_no_cli.generate_from_existing_code(sample_analysis)

        approved = generator_no_cli.request_user_approval(spec)

        assert approved is True  # Auto-approve when no CLI

    def test_request_user_approval_rejected(self, generator, mock_cli, sample_analysis):
        """Test user rejecting approval."""
        spec = generator.generate_from_existing_code(sample_analysis)
        mock_cli.request_approval.return_value = False

        approved = generator.request_user_approval(spec)

        assert approved is False
        assert spec.approved is False
        assert spec.approval_timestamp is None

    def test_generate_introduction_from_analysis(self, generator, sample_analysis):
        """Test generating introduction from analysis."""
        introduction = generator._generate_introduction_from_analysis(sample_analysis)

        assert "web application for user management" in introduction
        assert "User Registration" in introduction or "User Authentication" in introduction
        assert "User, Admin" in introduction or "User" in introduction
        assert "80%" in introduction  # Confidence score

    def test_extract_key_features_from_analysis(self, generator, sample_analysis):
        """Test extracting key features from analysis."""
        features = generator._extract_key_features_from_analysis(sample_analysis)

        assert len(features) > 0
        assert "User Registration" in features
        assert "User Authentication" in features
        assert "Profile Management" in features

    def test_generate_requirements_from_evidence(self, generator, sample_analysis):
        """Test generating requirements from evidence."""
        requirements = generator._generate_requirements_from_evidence(sample_analysis)

        assert len(requirements) > 0
        req = requirements[0]
        assert req.id == "FR-1"
        assert "As a user" in req.user_story or "As a admin" in req.user_story
        assert len(req.acceptance_criteria) >= 2
        assert req.source_analysis is not None
        assert req.priority in [Priority.LOW, Priority.MEDIUM, Priority.HIGH]

    def test_convert_to_user_story(self, generator):
        """Test converting requirement text to user story format."""
        # Test with non-user story format
        req_text = "Create user registration system"
        user_story = generator._convert_to_user_story(req_text)

        assert user_story.startswith("As a user")
        assert "create" in user_story.lower()

        # Test with existing user story format
        existing_story = "As a user, I want to login, so that I can access my account"
        result = generator._convert_to_user_story(existing_story)
        assert result == existing_story

    def test_generate_acceptance_criteria_from_text(self, generator):
        """Test generating acceptance criteria from requirement text."""
        req_text = "Create user registration system"
        criteria = generator._generate_acceptance_criteria_from_text(req_text)

        assert len(criteria) >= 2
        assert any("WHEN" in criterion and "THEN" in criterion for criterion in criteria)
        assert any("create" in criterion.lower() for criterion in criteria)

    def test_determine_priority_from_evidence(self, generator):
        """Test determining priority from evidence."""
        high_confidence_evidence = RequirementEvidence(
            requirement_type="Critical Feature",
            description="Critical system feature",
            supporting_files=["file1.py"],
            supporting_functions=["func1"],
            confidence=0.9,
            code_examples=[]
        )

        medium_confidence_evidence = RequirementEvidence(
            requirement_type="Standard Feature",
            description="Standard system feature",
            supporting_files=["file1.py"],
            supporting_functions=["func1"],
            confidence=0.7,
            code_examples=[]
        )

        low_confidence_evidence = RequirementEvidence(
            requirement_type="Optional Feature",
            description="Optional system feature",
            supporting_files=["file1.py"],
            supporting_functions=["func1"],
            confidence=0.4,
            code_examples=[]
        )

        assert generator._determine_priority_from_evidence(high_confidence_evidence) == Priority.HIGH
        assert generator._determine_priority_from_evidence(medium_confidence_evidence) == Priority.MEDIUM
        assert generator._determine_priority_from_evidence(low_confidence_evidence) == Priority.LOW

    def test_increment_version(self, generator):
        """Test version incrementing."""
        assert generator._increment_version("1.0") == "1.1"
        assert generator._increment_version("2.5") == "2.6"
        assert generator._increment_version("invalid") == "1.1"
        assert generator._increment_version("1") == "1.1"

    def test_parse_feedback(self, generator):
        """Test parsing user feedback."""
        feedback = "Add more requirements for authentication and remove low priority items"
        refinements = generator._parse_feedback(feedback)

        assert "add_requirements" in refinements
        assert "remove_requirements" in refinements
        assert len(refinements["add_requirements"]) > 0 or len(refinements["remove_requirements"]) > 0

    def test_apply_refinements(self, generator, sample_analysis):
        """Test applying refinements to specification."""
        spec = generator.generate_from_existing_code(sample_analysis)
        original_req_count = len(spec.functional_requirements)

        refinements = {
            "add_requirements": ["New security requirement"],
            "modify_requirements": [],
            "remove_requirements": ["Remove something"],
            "change_introduction": "Updated introduction text",
            "add_features": [],
            "remove_features": []
        }

        refined_spec = generator._apply_refinements(spec, refinements)

        # Should have modified introduction
        assert refined_spec.introduction != spec.introduction
        assert "Updated introduction text" in refined_spec.introduction

        # Should have added and removed requirements
        # Net effect depends on implementation, but should be different
        assert refined_spec != spec

    def test_empty_analysis_handling(self, generator):
        """Test handling of empty or minimal analysis."""
        minimal_analysis = SpecificationAnalysis(
            project_purpose="Unknown project",
            main_features=[],
            user_roles=[],
            functional_areas=[],
            requirement_evidence=[],
            technology_constraints=[],
            external_dependencies=[],
            confidence_score=0.0
        )

        spec = generator.generate_from_existing_code(minimal_analysis)

        assert isinstance(spec, SpecificationDocument)
        assert spec.source == SpecificationSource.EXISTING_CODE
        # Should still generate some basic structure even with minimal input
        assert len(spec.introduction) > 0

    def test_large_user_requirements_handling(self, generator, mock_cli):
        """Test handling of many user requirements."""
        # Simulate user entering many requirements
        many_requirements = [f"Requirement {i}" for i in range(15)]

        spec = generator.generate_from_user_input(many_requirements)

        assert len(spec.functional_requirements) == 15
        assert all(req.id.startswith("FR-") for req in spec.functional_requirements)
        assert all(len(req.acceptance_criteria) >= 2 for req in spec.functional_requirements)


class TestSpecificationGeneratorIntegration:
    """Integration tests for specification generator."""

    @pytest.fixture
    def generator(self):
        """Create generator for integration tests."""
        return SpecificationGenerator()

    def test_full_workflow_existing_code(self, generator):
        """Test full workflow for existing code analysis."""
        # Create comprehensive analysis
        evidence1 = RequirementEvidence(
            requirement_type="User Management",
            description="System manages user accounts and profiles",
            supporting_files=["models/user.py", "controllers/user_controller.py"],
            supporting_functions=["create_user", "update_profile", "authenticate_user"],
            confidence=0.85,
            code_examples=[]
        )

        evidence2 = RequirementEvidence(
            requirement_type="Data Storage",
            description="System provides persistent data storage",
            supporting_files=["models/database.py", "repositories/user_repo.py"],
            supporting_functions=["save_user", "find_user", "delete_user"],
            confidence=0.75,
            code_examples=[]
        )

        analysis = SpecificationAnalysis(
            project_purpose="User management web application with authentication",
            main_features=["User Registration", "Authentication", "Profile Management", "Data Persistence"],
            user_roles=["User", "Admin", "Guest"],
            functional_areas=["Authentication", "User Management", "Data Storage", "Security"],
            requirement_evidence=[evidence1, evidence2],
            technology_constraints=["Python 3.8+", "Flask framework", "SQLAlchemy ORM"],
            external_dependencies=["flask", "sqlalchemy", "bcrypt", "jwt"],
            confidence_score=0.8
        )

        # Generate specification
        spec = generator.generate_from_existing_code(analysis)

        # Verify comprehensive specification
        assert len(spec.functional_requirements) >= 2
        assert len(spec.key_features) >= 3
        assert "user management web application" in spec.introduction
        assert spec.source == SpecificationSource.EXISTING_CODE

        # Format and verify markdown
        formatted = generator.format_specification_document(spec)
        assert "# Requirements Document" in formatted
        assert "User Management" in formatted or "Data Storage" in formatted

        # Test refinement
        refined_spec = generator.refine_specification(spec, "Add security requirements")
        assert refined_spec.version != spec.version
        assert len(refined_spec.functional_requirements) >= len(spec.functional_requirements)

    def test_full_workflow_user_input(self, generator):
        """Test full workflow for user input."""
        user_requirements = [
            "Users should be able to create accounts with email and password",
            "System should authenticate users securely",
            "Users can update their profile information",
            "Admins can manage user accounts",
            "System should log all user activities"
        ]

        # Generate specification
        spec = generator.generate_from_user_input(user_requirements)

        # Verify specification
        assert len(spec.functional_requirements) == 5
        assert spec.source == SpecificationSource.USER_INPUT
        assert all(req.priority == Priority.MEDIUM for req in spec.functional_requirements)

        # Verify user stories are properly formatted
        for req in spec.functional_requirements:
            assert req.user_story.startswith("As a")
            assert "so that" in req.user_story
            assert len(req.acceptance_criteria) >= 2
            assert all("WHEN" in criteria and "THEN" in criteria for criteria in req.acceptance_criteria)

        # Format and verify
        formatted = generator.format_specification_document(spec)
        assert formatted.count("### Requirement") == 5
        assert "**User Story:**" in formatted
        assert "#### Acceptance Criteria" in formatted

        # Test approval workflow (auto-approve without CLI)
        approved = generator.request_user_approval(spec)
        assert approved is True
        assert spec.approved is True
        assert spec.approval_timestamp is not None
