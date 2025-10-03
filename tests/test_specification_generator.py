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
        )

        return SpecificationAnalysis(
            project_purpose="Web application for user management",
            main_features=[
                "User Registration",
                "User Authentication",
                "Profile Management",
            ],
            user_roles=["User", "Admin"],
            functional_areas=["Authentication", "User Management", "Profile"],
            technology_constraints=["Python 3.x required", "Web framework dependency"],
            requirement_evidence=[evidence],
            confidence_score=0.8,
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
            "Provide profile management features",
        ]

        spec = generator.generate_from_user_input(user_requirements)

        assert isinstance(spec, SpecificationDocument)
        assert spec.source == SpecificationSource.USER_INPUT
        assert spec.approved is False
        assert len(spec.functional_requirements) == 3
        assert spec.version == "1.0"

        # Check requirements structure
        for i, req in enumerate(spec.functional_requirements):
            assert req.id == f"FR-{i + 1}"
            assert "As a user" in req.user_story
            assert len(req.acceptance_criteria) >= 2
            assert req.priority == Priority.MEDIUM

    def test_generate_from_user_input_with_cli_interaction(self, generator, mock_cli):
        """Test generating specification with CLI interaction for requirements."""
        # Mock CLI to return requirements
        mock_cli.get_user_input.side_effect = [
            "Create user accounts",
            "Manage user profiles",
            "",  # Empty input to stop
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
        assert len(refined_spec.functional_requirements) >= len(
            original_spec.functional_requirements
        )

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

    def test_format_specification_with_source_analysis(
        self, generator, sample_analysis
    ):
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
        assert (
            "User Registration" in introduction or "User Authentication" in introduction
        )
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
        assert any(
            "WHEN" in criterion and "THEN" in criterion for criterion in criteria
        )
        assert any("create" in criterion.lower() for criterion in criteria)

    def test_determine_priority_from_evidence(self, generator):
        """Test determining priority from evidence."""
        high_confidence_evidence = RequirementEvidence(
            requirement_type="Critical Feature",
            description="Critical system feature",
            supporting_files=["file1.py"],
            supporting_functions=["func1"],
            confidence=0.9,
        )

        medium_confidence_evidence = RequirementEvidence(
            requirement_type="Standard Feature",
            description="Standard system feature",
            supporting_files=["file1.py"],
            supporting_functions=["func1"],
            confidence=0.7,
        )

        low_confidence_evidence = RequirementEvidence(
            requirement_type="Optional Feature",
            description="Optional system feature",
            supporting_files=["file1.py"],
            supporting_functions=["func1"],
            confidence=0.4,
        )

        assert (
            generator._determine_priority_from_evidence(high_confidence_evidence)
            == Priority.HIGH
        )
        assert (
            generator._determine_priority_from_evidence(medium_confidence_evidence)
            == Priority.MEDIUM
        )
        assert (
            generator._determine_priority_from_evidence(low_confidence_evidence)
            == Priority.LOW
        )

    def test_increment_version(self, generator):
        """Test version incrementing."""
        assert generator._increment_version("1.0") == "1.1"
        assert generator._increment_version("2.5") == "2.6"
        assert generator._increment_version("invalid") == "1.1"
        assert generator._increment_version("1") == "1.1"

    def test_parse_feedback(self, generator):
        """Test parsing user feedback."""
        feedback = (
            "Add more requirements for authentication and remove low priority items"
        )
        refinements = generator._parse_feedback(feedback)

        assert "add_requirements" in refinements
        assert "remove_requirements" in refinements
        assert (
            len(refinements["add_requirements"]) > 0
            or len(refinements["remove_requirements"]) > 0
        )

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
            "remove_features": [],
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
            technology_constraints=[],
            requirement_evidence=[],
            confidence_score=0.0,
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
        assert all(
            len(req.acceptance_criteria) >= 2 for req in spec.functional_requirements
        )


class TestSpecificationGeneratorAI:
    """Test cases for AI-powered specification generation."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        from unittest.mock import AsyncMock
        
        client = AsyncMock()
        client.generate_completion = AsyncMock(
            return_value="""## Overview
This feature provides user authentication and authorization capabilities.

## Functional Requirements
1. As a user, I want to register with email and password, so that I can create an account
   - WHEN I provide valid email and password THEN the system SHALL create a new account
   - WHEN I provide invalid email THEN the system SHALL reject the registration

2. As a user, I want to login securely, so that I can access my account
   - WHEN I provide correct credentials THEN the system SHALL authenticate me
   - WHEN I provide incorrect credentials THEN the system SHALL deny access

## Technical Requirements
- Use bcrypt for password hashing
- Implement JWT tokens for session management
- Store user data in PostgreSQL database

## Acceptance Criteria
- All passwords SHALL be hashed before storage
- JWT tokens SHALL expire after 24 hours
- Failed login attempts SHALL be rate limited

## Dependencies
- bcrypt library for password hashing
- PyJWT for token management
- SQLAlchemy for database access

## Error Handling
- Invalid credentials SHALL return 401 Unauthorized
- Rate limit exceeded SHALL return 429 Too Many Requests
- Database errors SHALL be logged and return 500 Internal Server Error

## Testing Strategy
- Unit tests for authentication logic
- Integration tests for API endpoints
- Security tests for password hashing and token validation
"""
        )
        return client

    @pytest.fixture
    def mock_cost_tracker(self):
        """Create a mock cost tracker."""
        from unittest.mock import Mock
        
        tracker = Mock()
        tracker.record_completion = Mock(return_value=0.05)
        return tracker

    @pytest.fixture
    def mock_token_counter(self):
        """Create a mock token counter."""
        from unittest.mock import Mock
        
        counter = Mock()
        counter.count_tokens = Mock(return_value=150)
        counter.validate_context_window = Mock(return_value=(True, ""))
        counter.get_model_name = Mock(return_value="gpt-4")
        return counter

    @pytest.fixture
    def mock_vector_db(self):
        """Create a mock vector database."""
        from unittest.mock import AsyncMock, Mock
        
        from dev_agent.models.indexing import CodeChunk, CodeMatch
        
        db = AsyncMock()
        
        # Mock query_similar to return relevant code chunks
        chunk1 = CodeChunk(
            content="def authenticate_user(email, password):\n    # Authentication logic\n    pass",
            file_path="auth/authentication.py",
            start_line=10,
            end_line=15,
            language="python",
            chunk_type="function",
        )
        
        chunk2 = CodeChunk(
            content="class User(Base):\n    email = Column(String)\n    password_hash = Column(String)",
            file_path="models/user.py",
            start_line=5,
            end_line=10,
            language="python",
            chunk_type="class",
        )
        
        match1 = CodeMatch(chunk=chunk1, similarity_score=0.85, embedding_id="chunk1")
        match2 = CodeMatch(chunk=chunk2, similarity_score=0.75, embedding_id="chunk2")
        
        db.query_similar = AsyncMock(return_value=[match1, match2])
        
        return db

    @pytest.fixture
    def ai_generator(
        self,
        mock_llm_client,
        mock_cost_tracker,
        mock_token_counter,
        mock_vector_db,
    ):
        """Create AI-powered specification generator."""
        return SpecificationGenerator(
            llm_client=mock_llm_client,
            cost_tracker=mock_cost_tracker,
            token_counter=mock_token_counter,
            vector_db=mock_vector_db,
        )

    @pytest.fixture
    def sample_analysis(self):
        """Create sample specification analysis."""
        evidence = RequirementEvidence(
            requirement_type="Authentication",
            description="System provides user authentication",
            supporting_files=["auth/authentication.py"],
            supporting_functions=["authenticate_user", "hash_password"],
            confidence=0.8,
        )

        return SpecificationAnalysis(
            project_purpose="Web application with user authentication",
            main_features=["User Registration", "User Login", "Password Reset"],
            user_roles=["User", "Admin"],
            functional_areas=["Authentication", "User Management"],
            technology_constraints=["Python 3.10+", "FastAPI"],
            requirement_evidence=[evidence],
            confidence_score=0.8,
        )

    @pytest.mark.asyncio
    async def test_generate_from_existing_code_ai(
        self,
        ai_generator,
        sample_analysis,
        mock_llm_client,
    ):
        """Test AI-powered specification generation."""
        spec = await ai_generator.generate_from_existing_code_ai(
            analysis=sample_analysis,
            feature_description="User authentication system",
        )

        assert isinstance(spec, SpecificationDocument)
        assert spec.source == SpecificationSource.EXISTING_CODE
        assert spec.approved is False
        assert len(spec.introduction) > 0
        assert len(spec.functional_requirements) > 0
        
        # Verify LLM client was called
        mock_llm_client.generate_completion.assert_called_once()
        call_args = mock_llm_client.generate_completion.call_args
        assert "prompt" in call_args.kwargs
        assert "system_prompt" in call_args.kwargs

    @pytest.mark.asyncio
    async def test_ai_generation_with_context_retrieval(
        self,
        ai_generator,
        sample_analysis,
        mock_vector_db,
    ):
        """Test that AI generation retrieves relevant context."""
        await ai_generator.generate_from_existing_code_ai(
            analysis=sample_analysis,
            feature_description="User authentication",
        )

        # Verify vector search was called
        mock_vector_db.query_similar.assert_called_once()
        call_args = mock_vector_db.query_similar.call_args
        assert call_args.kwargs["query_text"] == "User authentication"

    @pytest.mark.asyncio
    async def test_ai_generation_with_cost_tracking(
        self,
        ai_generator,
        sample_analysis,
        mock_cost_tracker,
    ):
        """Test that AI generation tracks costs."""
        await ai_generator.generate_from_existing_code_ai(
            analysis=sample_analysis,
            feature_description="User authentication",
        )

        # Verify cost was tracked
        mock_cost_tracker.record_completion.assert_called_once()
        call_args = mock_cost_tracker.record_completion.call_args
        assert call_args.kwargs["prompt_tokens"] > 0
        assert call_args.kwargs["completion_tokens"] > 0

    @pytest.mark.asyncio
    async def test_ai_generation_with_token_validation(
        self,
        ai_generator,
        sample_analysis,
        mock_token_counter,
    ):
        """Test that AI generation validates token limits."""
        await ai_generator.generate_from_existing_code_ai(
            analysis=sample_analysis,
            feature_description="User authentication",
        )

        # Verify token validation was performed
        mock_token_counter.validate_context_window.assert_called_once()

    @pytest.mark.asyncio
    async def test_ai_generation_token_limit_exceeded(
        self,
        ai_generator,
        sample_analysis,
        mock_token_counter,
    ):
        """Test handling of token limit exceeded."""
        from dev_agent.errors.llm_exceptions import LLMTokenLimitError
        
        # Mock token validation to fail
        mock_token_counter.validate_context_window.return_value = (
            False,
            "Token limit exceeded",
        )

        with pytest.raises(LLMTokenLimitError):
            await ai_generator.generate_from_existing_code_ai(
                analysis=sample_analysis,
                feature_description="User authentication",
            )

    @pytest.mark.asyncio
    async def test_ai_generation_without_llm_client(self, sample_analysis):
        """Test that AI generation fails without LLM client."""
        generator = SpecificationGenerator()

        with pytest.raises(ValueError, match="LLM client not configured"):
            await generator.generate_from_existing_code_ai(
                analysis=sample_analysis,
                feature_description="User authentication",
            )

    @pytest.mark.asyncio
    async def test_ai_generation_without_vector_db(
        self,
        mock_llm_client,
        sample_analysis,
    ):
        """Test AI generation works without vector database."""
        generator = SpecificationGenerator(llm_client=mock_llm_client)

        spec = await generator.generate_from_existing_code_ai(
            analysis=sample_analysis,
            feature_description="User authentication",
        )

        assert isinstance(spec, SpecificationDocument)
        # Should still work, just without context retrieval

    @pytest.mark.asyncio
    async def test_ai_generation_llm_authentication_error(
        self,
        ai_generator,
        sample_analysis,
        mock_llm_client,
    ):
        """Test handling of LLM authentication errors."""
        from dev_agent.errors.llm_exceptions import LLMAuthenticationError
        
        mock_llm_client.generate_completion.side_effect = LLMAuthenticationError(
            "Invalid API key"
        )

        with pytest.raises(LLMAuthenticationError):
            await ai_generator.generate_from_existing_code_ai(
                analysis=sample_analysis,
                feature_description="User authentication",
            )

    @pytest.mark.asyncio
    async def test_ai_generation_llm_rate_limit_error(
        self,
        ai_generator,
        sample_analysis,
        mock_llm_client,
    ):
        """Test handling of LLM rate limit errors."""
        from dev_agent.errors.llm_exceptions import LLMRateLimitError
        
        mock_llm_client.generate_completion.side_effect = LLMRateLimitError(
            "Rate limit exceeded"
        )

        with pytest.raises(LLMRateLimitError):
            await ai_generator.generate_from_existing_code_ai(
                analysis=sample_analysis,
                feature_description="User authentication",
            )

    @pytest.mark.asyncio
    async def test_parse_ai_specification(self, ai_generator, sample_analysis):
        """Test parsing of AI-generated specification content."""
        ai_content = """## Overview
This is a test specification for user authentication.

## Functional Requirements
1. As a user, I want to register
   - WHEN I provide email THEN system SHALL create account
2. As a user, I want to login
   - WHEN I provide credentials THEN system SHALL authenticate

## Key Features
- User registration
- Secure login
- Password hashing
"""

        spec = ai_generator._parse_ai_specification(ai_content, sample_analysis)

        assert isinstance(spec, SpecificationDocument)
        assert "test specification" in spec.introduction.lower()
        assert len(spec.key_features) > 0
        assert len(spec.functional_requirements) > 0

    def test_extract_sections(self, ai_generator):
        """Test extraction of sections from markdown."""
        content = """## Overview
This is the overview.

## Requirements
These are requirements.

## Testing
This is testing info.
"""

        sections = ai_generator._extract_sections(content)

        assert "overview" in sections
        assert "requirements" in sections
        assert "testing" in sections
        assert "overview" in sections["overview"].lower()

    def test_extract_list_items(self, ai_generator):
        """Test extraction of list items."""
        content = """
- Item 1
- Item 2
* Item 3
- Item 4
"""

        items = ai_generator._extract_list_items(content)

        assert len(items) == 4
        assert "Item 1" in items
        assert "Item 3" in items

    def test_extract_user_story(self, ai_generator):
        """Test extraction of user story from block."""
        block = """1. As a user, I want to login, so that I can access my account
   - WHEN I provide credentials THEN system SHALL authenticate
"""

        user_story = ai_generator._extract_user_story(block)

        assert "as a user" in user_story.lower()
        assert "login" in user_story.lower()

    def test_extract_acceptance_criteria(self, ai_generator):
        """Test extraction of acceptance criteria."""
        block = """Requirement description
- WHEN I provide valid input THEN system SHALL accept it
- WHEN I provide invalid input THEN system SHALL reject it
- The system SHALL validate all inputs
"""

        criteria = ai_generator._extract_acceptance_criteria(block)

        assert len(criteria) >= 2
        assert any("when" in c.lower() and "then" in c.lower() for c in criteria)
        assert any("shall" in c.lower() for c in criteria)

    @pytest.mark.asyncio
    async def test_build_specification_context(
        self,
        ai_generator,
        sample_analysis,
    ):
        """Test building context for specification prompt."""
        relevant_chunks = [
            "File: auth.py\nLines: 1-10\n```python\ndef authenticate(): pass\n```"
        ]

        context = ai_generator._build_specification_context(
            analysis=sample_analysis,
            feature_description="User authentication",
            relevant_chunks=relevant_chunks,
        )

        assert "codebase_summary" in context
        assert "relevant_code_chunks" in context
        assert "detected_patterns" in context
        assert "feature_description" in context
        assert "User authentication" in context["feature_description"]
        assert "Web application" in context["codebase_summary"]


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
        )

        evidence2 = RequirementEvidence(
            requirement_type="Data Storage",
            description="System provides persistent data storage",
            supporting_files=["models/database.py", "repositories/user_repo.py"],
            supporting_functions=["save_user", "find_user", "delete_user"],
            confidence=0.75,
        )

        analysis = SpecificationAnalysis(
            project_purpose="User management web application with authentication",
            main_features=[
                "User Registration",
                "Authentication",
                "Profile Management",
                "Data Persistence",
            ],
            user_roles=["User", "Admin", "Guest"],
            functional_areas=[
                "Authentication",
                "User Management",
                "Data Storage",
                "Security",
            ],
            technology_constraints=["Python 3.8+", "Flask framework", "SQLAlchemy ORM"],
            requirement_evidence=[evidence1, evidence2],
            confidence_score=0.8,
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
        assert len(refined_spec.functional_requirements) >= len(
            spec.functional_requirements
        )

    def test_full_workflow_user_input(self, generator):
        """Test full workflow for user input."""
        user_requirements = [
            "Users should be able to create accounts with email and password",
            "System should authenticate users securely",
            "Users can update their profile information",
            "Admins can manage user accounts",
            "System should log all user activities",
        ]

        # Generate specification
        spec = generator.generate_from_user_input(user_requirements)

        # Verify specification
        assert len(spec.functional_requirements) == 5
        assert spec.source == SpecificationSource.USER_INPUT
        assert all(
            req.priority == Priority.MEDIUM for req in spec.functional_requirements
        )

        # Verify user stories are properly formatted
        for req in spec.functional_requirements:
            assert req.user_story.startswith("As a")
            assert "so that" in req.user_story
            assert len(req.acceptance_criteria) >= 2
            assert all(
                "WHEN" in criteria and "THEN" in criteria
                for criteria in req.acceptance_criteria
            )

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
