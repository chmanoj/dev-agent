"""Multi-provider workflow tests for Azure OpenAI and Gemini.

This module tests that the workflow system works correctly with both
Azure OpenAI and Gemini providers, ensuring:
- Specification generation works with both providers
- State persistence is provider-agnostic
- Validation works with output from both providers
- Datetime handling is provider-agnostic
- Provider switching during workflow is seamless

Requirements tested:
- 7.1: Comprehensive testing for state management
- 7.2: Testing state loading with datetime deserialization
- 7.3: Testing with None datetime values
- 7.4: Testing backward compatibility
- 7.5: Testing all state management without datetime errors
"""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from dev_agent.generation.specification_generator import SpecificationGenerator
from dev_agent.models.documents import (
    Requirement,
    SpecificationDocument,
)
from dev_agent.models.enums import (
    LLMProvider,
    PhaseType,
    Priority,
    SpecificationSource,
)
from dev_agent.models.project_state import IndexMetadata, ProjectState, SessionData
from dev_agent.state.state_manager import StateManager


@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Path:
    """Create a temporary project directory."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir


@pytest.fixture
def state_manager(temp_project_dir: Path) -> StateManager:
    """Create a StateManager instance."""
    return StateManager(str(temp_project_dir))


@pytest.fixture
def mock_azure_config():
    """Create mock Azure OpenAI configuration."""
    from pydantic import SecretStr

    from dev_agent.models.llm_config import AzureOpenAIConfig

    return AzureOpenAIConfig(
        endpoint="https://test.openai.azure.com/",
        api_key=SecretStr("test-api-key"),
        api_version="2024-02-15-preview",
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
    )


@pytest.fixture
def mock_gemini_config():
    """Create mock Gemini configuration."""
    from pydantic import SecretStr

    from dev_agent.models.llm_config import GeminiConfig

    return GeminiConfig(
        api_key=SecretStr("AIzaSyTest123456789012345678901234567890"),
        model_name="gemini-pro",
        embedding_model="embedding-001",
        max_output_tokens=2048,
        temperature=0.7,
    )


@pytest.fixture
def mock_cli_interface():
    """Create a mock CLI interface."""
    cli = Mock()
    cli.display_message = Mock()
    cli.get_user_input = Mock()
    cli.request_approval = Mock(return_value=True)
    return cli


class TestSpecificationGenerationWithProviders:
    """Test specification generation with both Azure OpenAI and Gemini providers."""

    @pytest.mark.asyncio
    async def test_specification_generation_with_azure_openai(
        self,
        mock_azure_config,
        mock_cli_interface,
        temp_project_dir: Path,
    ):
        """Test specification generation with Azure OpenAI provider.

        Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
        """
        with patch("openai.AsyncAzureOpenAI") as mock_azure_client:
            # Setup Azure mock
            mock_azure_instance = MagicMock()
            mock_azure_completion = MagicMock()
            mock_azure_completion.choices = [
                MagicMock(
                    message=MagicMock(
                        content="""# Requirements Document

## Introduction

This specification defines a user authentication system.

## Requirements

### Requirement 1

**User Story:** As a user, I want to register an account, so that I can access the system

#### Acceptance Criteria

1. WHEN user provides valid email and password THEN system SHALL create account
2. WHEN user provides duplicate email THEN system SHALL reject registration
3. IF email format is invalid THEN system SHALL show validation error

### Requirement 2

**User Story:** As a user, I want to login securely, so that I can access my account

#### Acceptance Criteria

1. WHEN user provides correct credentials THEN system SHALL grant access
2. WHEN user provides incorrect credentials THEN system SHALL deny access
3. IF account is locked THEN system SHALL show locked message

### Requirement 3

**User Story:** As a user, I want to reset my password, so that I can recover my account

#### Acceptance Criteria

1. WHEN user requests password reset THEN system SHALL send reset email
2. WHEN user clicks reset link THEN system SHALL allow password change
3. IF reset link is expired THEN system SHALL show error message
"""
                    )
                )
            ]
            mock_azure_completion.usage = MagicMock(
                prompt_tokens=100, completion_tokens=200, total_tokens=300
            )
            mock_azure_instance.chat.completions.create = AsyncMock(
                return_value=mock_azure_completion
            )
            mock_azure_client.return_value = mock_azure_instance

            # Create Azure OpenAI client
            from dev_agent.llm.azure_client import AzureOpenAIClient

            azure_client = AzureOpenAIClient(mock_azure_config, client=mock_azure_instance)

            # Create specification generator
            generator = SpecificationGenerator(
                cli_interface=mock_cli_interface,
                llm_client=azure_client,
            )

            # Generate specification
            spec_doc = await generator._generate_from_user_input(
                "Create a user authentication system"
            )

            # Assert: Specification generated successfully
            assert spec_doc is not None
            assert isinstance(spec_doc, SpecificationDocument)
            assert len(spec_doc.functional_requirements) >= 3
            assert spec_doc.source == SpecificationSource.USER_INPUT

            # Verify all requirements have proper structure
            for req in spec_doc.functional_requirements:
                assert req.user_story is not None
                assert len(req.acceptance_criteria) >= 2

    @pytest.mark.asyncio
    async def test_specification_generation_with_gemini(
        self,
        mock_gemini_config,
        mock_cli_interface,
        temp_project_dir: Path,
    ):
        """Test specification generation with Gemini provider.

        Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
        """
        with patch("google.generativeai.configure"), patch(
            "google.generativeai.GenerativeModel"
        ) as mock_model:
            # Setup Gemini mock
            mock_response = MagicMock()
            mock_response.text = """# Requirements Document

## Introduction

This specification defines a user authentication system.

## Requirements

### Requirement 1

**User Story:** As a user, I want to register an account, so that I can access the system

#### Acceptance Criteria

1. WHEN user provides valid email and password THEN system SHALL create account
2. WHEN user provides duplicate email THEN system SHALL reject registration
3. IF email format is invalid THEN system SHALL show validation error

### Requirement 2

**User Story:** As a user, I want to login securely, so that I can access my account

#### Acceptance Criteria

1. WHEN user provides correct credentials THEN system SHALL grant access
2. WHEN user provides incorrect credentials THEN system SHALL deny access
3. IF account is locked THEN system SHALL show locked message

### Requirement 3

**User Story:** As a user, I want to reset my password, so that I can recover my account

#### Acceptance Criteria

1. WHEN user requests password reset THEN system SHALL send reset email
2. WHEN user clicks reset link THEN system SHALL allow password change
3. IF reset link is expired THEN system SHALL show error message
"""
            mock_model.return_value.generate_content_async = AsyncMock(
                return_value=mock_response
            )

            # Create Gemini client
            from dev_agent.llm.gemini_client import GeminiClient

            gemini_client = GeminiClient(mock_gemini_config)

            # Create specification generator
            generator = SpecificationGenerator(
                cli_interface=mock_cli_interface,
                llm_client=gemini_client,
            )

            # Generate specification
            spec_doc = await generator._generate_from_user_input(
                "Create a user authentication system"
            )

            # Assert: Specification generated successfully
            assert spec_doc is not None
            assert isinstance(spec_doc, SpecificationDocument)
            assert len(spec_doc.functional_requirements) >= 3
            assert spec_doc.source == SpecificationSource.USER_INPUT

            # Verify all requirements have proper structure
            for req in spec_doc.functional_requirements:
                assert req.user_story is not None
                assert len(req.acceptance_criteria) >= 2


class TestStatePersistenceWithProviders:
    """Test state persistence works with both providers."""

    def test_state_persistence_with_azure_openai_generated_spec(
        self,
        state_manager: StateManager,
    ):
        """Test state persistence with specification generated by Azure OpenAI.

        Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
        """
        # Create specification (simulating Azure OpenAI generation)
        specification = SpecificationDocument(
            introduction="Azure OpenAI generated specification",
            key_features=["Feature 1", "Feature 2", "Feature 3"],
            functional_requirements=[
                Requirement(
                    id=f"REQ-{i}",
                    user_story=f"As a user, I want feature {i}, so that I can use it",
                    acceptance_criteria=[
                        f"WHEN user does action {i} THEN system SHALL respond",
                        f"IF condition {i} THEN system SHALL handle it",
                    ],
                    priority=Priority.HIGH,
                )
                for i in range(1, 4)
            ],
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=True,
            approval_timestamp=datetime.now(),
        )

        # Create project state
        session_data = SessionData(
            session_id=str(uuid.uuid4()),
            started_at=datetime.now(),
            last_activity=datetime.now(),
            user_approvals={"specification": True},
            pending_approvals=[],
        )

        state = ProjectState(
            project_path=str(state_manager.project_path),
            current_phase=PhaseType.SPECIFICATION,
            indexing_complete=True,
            specification=specification,
            design=None,
            tasks=None,
            implementation_progress={},
            index_metadata=None,
            session_data=session_data,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            specification_approved=True,
        )

        # Save state
        success = state_manager.save_project_state(state)
        assert success is True

        # Load state
        loaded_state = state_manager.load_project_state()
        assert loaded_state is not None
        assert loaded_state.specification is not None
        assert loaded_state.specification.introduction == "Azure OpenAI generated specification"
        assert isinstance(loaded_state.specification.approval_timestamp, datetime)
        assert loaded_state.specification_approved is True

    def test_state_persistence_with_gemini_generated_spec(
        self,
        state_manager: StateManager,
    ):
        """Test state persistence with specification generated by Gemini.

        Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
        """
        # Create specification (simulating Gemini generation)
        specification = SpecificationDocument(
            introduction="Gemini generated specification",
            key_features=["Feature A", "Feature B", "Feature C"],
            functional_requirements=[
                Requirement(
                    id=f"REQ-{i}",
                    user_story=f"As a developer, I want feature {i}, so that I can build it",
                    acceptance_criteria=[
                        f"WHEN developer uses feature {i} THEN system SHALL work",
                        f"IF error occurs in feature {i} THEN system SHALL handle gracefully",
                    ],
                    priority=Priority.MEDIUM,
                )
                for i in range(1, 4)
            ],
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=True,
            approval_timestamp=datetime.now(),
        )

        # Create project state
        session_data = SessionData(
            session_id=str(uuid.uuid4()),
            started_at=datetime.now(),
            last_activity=datetime.now(),
            user_approvals={"specification": True},
            pending_approvals=[],
        )

        state = ProjectState(
            project_path=str(state_manager.project_path),
            current_phase=PhaseType.SPECIFICATION,
            indexing_complete=True,
            specification=specification,
            design=None,
            tasks=None,
            implementation_progress={},
            index_metadata=None,
            session_data=session_data,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            specification_approved=True,
        )

        # Save state
        success = state_manager.save_project_state(state)
        assert success is True

        # Load state
        loaded_state = state_manager.load_project_state()
        assert loaded_state is not None
        assert loaded_state.specification is not None
        assert loaded_state.specification.introduction == "Gemini generated specification"
        assert isinstance(loaded_state.specification.approval_timestamp, datetime)
        assert loaded_state.specification_approved is True


class TestValidationWithProviders:
    """Test validation works with output from both providers."""

    def test_validation_with_azure_openai_output(
        self,
        mock_cli_interface,
    ):
        """Test validation works with Azure OpenAI generated output.

        Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
        """
        from dev_agent.llm.azure_client import AzureOpenAIClient

        # Create mock Azure client
        mock_client = Mock(spec=AzureOpenAIClient)

        # Create specification generator
        generator = SpecificationGenerator(
            cli_interface=mock_cli_interface,
            llm_client=mock_client,
        )

        # Create complete specification (Azure OpenAI style)
        complete_spec = SpecificationDocument(
            introduction="Complete Azure OpenAI specification",
            key_features=["Auth", "Profile", "Settings"],
            functional_requirements=[
                Requirement(
                    id=f"REQ-{i}",
                    user_story=f"As a user, I want feature {i}, so that I can use it",
                    acceptance_criteria=[
                        f"WHEN user performs action {i} THEN system SHALL respond appropriately",
                        f"IF error occurs in feature {i} THEN system SHALL handle gracefully",
                        f"WHERE user has permission THEN system SHALL allow access to feature {i}",
                    ],
                    priority=Priority.HIGH,
                )
                for i in range(1, 4)
            ],
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=False,
        )

        # Validate
        is_valid, issues = generator._validate_specification(complete_spec)

        # Assert: Validation passes
        assert is_valid is True
        assert len(issues) == 0

    def test_validation_with_gemini_output(
        self,
        mock_cli_interface,
    ):
        """Test validation works with Gemini generated output.

        Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
        """
        from dev_agent.llm.gemini_client import GeminiClient

        # Create mock Gemini client
        mock_client = Mock(spec=GeminiClient)

        # Create specification generator
        generator = SpecificationGenerator(
            cli_interface=mock_cli_interface,
            llm_client=mock_client,
        )

        # Create complete specification (Gemini style)
        complete_spec = SpecificationDocument(
            introduction="Complete Gemini specification",
            key_features=["Login", "Logout", "Session Management"],
            functional_requirements=[
                Requirement(
                    id=f"REQ-{i}",
                    user_story=f"As a developer, I want to implement feature {i}, so that users can benefit",
                    acceptance_criteria=[
                        f"WHEN feature {i} is triggered THEN system SHALL execute correctly",
                        f"IF validation fails for feature {i} THEN system SHALL show error",
                    ],
                    priority=Priority.MEDIUM,
                )
                for i in range(1, 4)
            ],
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=False,
        )

        # Validate
        is_valid, issues = generator._validate_specification(complete_spec)

        # Assert: Validation passes
        assert is_valid is True
        assert len(issues) == 0

    def test_validation_fails_for_incomplete_spec_regardless_of_provider(
        self,
        mock_cli_interface,
    ):
        """Test validation fails for incomplete spec from any provider.

        Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
        """
        # Create mock client (provider-agnostic)
        mock_client = Mock()

        # Create specification generator
        generator = SpecificationGenerator(
            cli_interface=mock_cli_interface,
            llm_client=mock_client,
        )

        # Create incomplete specification (only 1 requirement)
        incomplete_spec = SpecificationDocument(
            introduction="Incomplete specification",
            key_features=["Feature 1"],
            functional_requirements=[
                Requirement(
                    id="REQ-1",
                    user_story="As a user, I want feature 1, so that I can use it",
                    acceptance_criteria=["WHEN user does action THEN system SHALL respond"],
                    priority=Priority.LOW,
                )
            ],
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=False,
        )

        # Validate
        is_valid, issues = generator._validate_specification(incomplete_spec)

        # Assert: Validation fails
        assert is_valid is False
        assert len(issues) > 0
        assert any("fewer than 3 requirements" in issue.lower() for issue in issues)


class TestDatetimeHandlingIsProviderAgnostic:
    """Test datetime handling is provider-agnostic."""

    def test_datetime_serialization_works_for_azure_openai_spec(
        self,
        state_manager: StateManager,
    ):
        """Test datetime serialization for Azure OpenAI generated spec.

        Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
        """
        # Create specification with datetime
        approval_time = datetime.now()
        specification = SpecificationDocument(
            introduction="Azure OpenAI spec with datetime",
            key_features=["Feature 1"],
            functional_requirements=[
                Requirement(
                    id="REQ-1",
                    user_story="As a user, I want feature, so that I can use it",
                    acceptance_criteria=["WHEN action THEN response"],
                    priority=Priority.HIGH,
                )
            ],
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=True,
            approval_timestamp=approval_time,
        )

        # Create state
        session_data = SessionData(
            session_id=str(uuid.uuid4()),
            started_at=datetime.now(),
            last_activity=datetime.now(),
            user_approvals={},
            pending_approvals=[],
        )

        state = ProjectState(
            project_path=str(state_manager.project_path),
            current_phase=PhaseType.SPECIFICATION,
            indexing_complete=True,
            specification=specification,
            design=None,
            tasks=None,
            implementation_progress={},
            index_metadata=None,
            session_data=session_data,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            specification_approved=True,
        )

        # Save and load
        state_manager.save_project_state(state)
        loaded = state_manager.load_project_state()

        # Assert: Datetime preserved correctly
        assert loaded is not None
        assert loaded.specification is not None
        assert isinstance(loaded.specification.approval_timestamp, datetime)
        time_diff = abs(
            (loaded.specification.approval_timestamp - approval_time).total_seconds()
        )
        assert time_diff < 1.0

    def test_datetime_serialization_works_for_gemini_spec(
        self,
        state_manager: StateManager,
    ):
        """Test datetime serialization for Gemini generated spec.

        Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
        """
        # Create specification with datetime
        approval_time = datetime.now()
        specification = SpecificationDocument(
            introduction="Gemini spec with datetime",
            key_features=["Feature A"],
            functional_requirements=[
                Requirement(
                    id="REQ-A",
                    user_story="As a developer, I want feature, so that I can build",
                    acceptance_criteria=["WHEN action THEN response"],
                    priority=Priority.MEDIUM,
                )
            ],
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=True,
            approval_timestamp=approval_time,
        )

        # Create state
        session_data = SessionData(
            session_id=str(uuid.uuid4()),
            started_at=datetime.now(),
            last_activity=datetime.now(),
            user_approvals={},
            pending_approvals=[],
        )

        state = ProjectState(
            project_path=str(state_manager.project_path),
            current_phase=PhaseType.SPECIFICATION,
            indexing_complete=True,
            specification=specification,
            design=None,
            tasks=None,
            implementation_progress={},
            index_metadata=None,
            session_data=session_data,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            specification_approved=True,
        )

        # Save and load
        state_manager.save_project_state(state)
        loaded = state_manager.load_project_state()

        # Assert: Datetime preserved correctly
        assert loaded is not None
        assert loaded.specification is not None
        assert isinstance(loaded.specification.approval_timestamp, datetime)
        time_diff = abs(
            (loaded.specification.approval_timestamp - approval_time).total_seconds()
        )
        assert time_diff < 1.0

    def test_none_datetime_handling_is_provider_agnostic(
        self,
        state_manager: StateManager,
    ):
        """Test None datetime handling works regardless of provider.

        Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
        """
        # Create specification without approval (None timestamp)
        specification = SpecificationDocument(
            introduction="Unapproved spec from any provider",
            key_features=["Feature X"],
            functional_requirements=[
                Requirement(
                    id="REQ-X",
                    user_story="As a user, I want feature, so that I can use it",
                    acceptance_criteria=["WHEN action THEN response"],
                    priority=Priority.LOW,
                )
            ],
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=False,
            approval_timestamp=None,  # Not approved yet
        )

        # Create state
        session_data = SessionData(
            session_id=str(uuid.uuid4()),
            started_at=datetime.now(),
            last_activity=datetime.now(),
            user_approvals={},
            pending_approvals=["specification"],
        )

        state = ProjectState(
            project_path=str(state_manager.project_path),
            current_phase=PhaseType.SPECIFICATION,
            indexing_complete=True,
            specification=specification,
            design=None,
            tasks=None,
            implementation_progress={},
            index_metadata=None,
            session_data=session_data,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            specification_approved=False,
        )

        # Save and load
        state_manager.save_project_state(state)
        loaded = state_manager.load_project_state()

        # Assert: None timestamp preserved
        assert loaded is not None
        assert loaded.specification is not None
        assert loaded.specification.approval_timestamp is None
        assert loaded.specification_approved is False

    def test_provider_switching_preserves_datetime_fields(
        self,
        state_manager: StateManager,
    ):
        """Test switching providers preserves all datetime fields.

        Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
        """
        # Phase 1: Create state with Azure OpenAI (simulated)
        azure_spec = SpecificationDocument(
            introduction="Azure OpenAI specification",
            key_features=["Auth"],
            functional_requirements=[
                Requirement(
                    id="REQ-1",
                    user_story="As a user, I want auth, so that I can login",
                    acceptance_criteria=["WHEN login THEN grant access"],
                    priority=Priority.HIGH,
                )
            ],
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=True,
            approval_timestamp=datetime.now(),
        )

        index_metadata = IndexMetadata(
            total_files=10,
            total_lines=1000,
            languages_detected=["python"],
            index_size_mb=0.5,
            last_indexed=datetime.now(),
            index_version="1.0",
        )

        session_data = SessionData(
            session_id=str(uuid.uuid4()),
            started_at=datetime.now(),
            last_activity=datetime.now(),
            user_approvals={"specification": True},
            pending_approvals=[],
        )

        state = ProjectState(
            project_path=str(state_manager.project_path),
            current_phase=PhaseType.SPECIFICATION,
            indexing_complete=True,
            specification=azure_spec,
            design=None,
            tasks=None,
            implementation_progress={},
            index_metadata=index_metadata,
            session_data=session_data,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            specification_approved=True,
        )

        # Save state (Azure OpenAI phase)
        state_manager.save_project_state(state)

        # Phase 2: Load state and continue with Gemini (simulated)
        loaded_state = state_manager.load_project_state()
        assert loaded_state is not None

        # Verify all datetime fields are datetime objects
        assert isinstance(loaded_state.created_at, datetime)
        assert isinstance(loaded_state.updated_at, datetime)
        assert isinstance(loaded_state.session_data.started_at, datetime)
        assert isinstance(loaded_state.session_data.last_activity, datetime)
        assert isinstance(loaded_state.index_metadata.last_indexed, datetime)
        assert isinstance(loaded_state.specification.approval_timestamp, datetime)

        # Update state (simulating Gemini phase)
        loaded_state.updated_at = datetime.now()
        loaded_state.session_data.last_activity = datetime.now()

        # Save again (Gemini phase)
        state_manager.save_project_state(loaded_state)

        # Phase 3: Load again (switch back to Azure OpenAI)
        final_state = state_manager.load_project_state()
        assert final_state is not None

        # Verify all datetime fields still datetime objects
        assert isinstance(final_state.created_at, datetime)
        assert isinstance(final_state.updated_at, datetime)
        assert isinstance(final_state.session_data.started_at, datetime)
        assert isinstance(final_state.session_data.last_activity, datetime)
        assert isinstance(final_state.index_metadata.last_indexed, datetime)
        assert isinstance(final_state.specification.approval_timestamp, datetime)
