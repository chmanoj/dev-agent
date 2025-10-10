"""Integration tests for workflow phase transitions and state persistence.

This module tests the complete workflow across all phases with focus on:
- Datetime serialization/deserialization during phase transitions
- State persistence and recovery across phases
- Approval workflows and state updates
- Provider switching (Azure OpenAI ↔ Gemini) across phases
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

from dev_agent.generation.specification_generator import SpecificationGenerator
from dev_agent.models.documents import (
    ArchitectureDescription,
    DesignDocument,
    Requirement,
    SpecificationDocument,
    Task,
    TaskList,
)
from dev_agent.models.enums import (
    LLMProvider,
    PhaseType,
    Priority,
    SpecificationSource,
    TaskStatus,
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
def sample_specification() -> SpecificationDocument:
    """Create a sample specification document."""
    return SpecificationDocument(
        introduction="Test specification for user management system",
        key_features=["User Registration", "Authentication", "Profile Management"],
        functional_requirements=[
            Requirement(
                id="REQ-1",
                user_story="As a user, I want to register an account, so that I can access the system",
                acceptance_criteria=[
                    "WHEN user provides valid email and password THEN account SHALL be created",
                    "WHEN user provides duplicate email THEN system SHALL reject registration",
                ],
                priority=Priority.HIGH,
            ),
            Requirement(
                id="REQ-2",
                user_story="As a user, I want to login securely, so that I can access my account",
                acceptance_criteria=[
                    "WHEN user provides correct credentials THEN system SHALL grant access",
                    "WHEN user provides incorrect credentials THEN system SHALL deny access",
                ],
                priority=Priority.HIGH,
            ),
            Requirement(
                id="REQ-3",
                user_story="As a user, I want to update my profile, so that I can keep my information current",
                acceptance_criteria=[
                    "WHEN user updates profile THEN changes SHALL be persisted",
                    "WHEN user provides invalid data THEN system SHALL show validation errors",
                ],
                priority=Priority.MEDIUM,
            ),
        ],
        source=SpecificationSource.USER_INPUT,
        version="1.0",
        approved=False,
        approval_timestamp=None,
    )


@pytest.fixture
def sample_design() -> DesignDocument:
    """Create a sample design document."""
    from dev_agent.models.documents import ErrorHandlingStrategy, TestingStrategy
    
    return DesignDocument(
        overview="Design for user management system",
        architecture=ArchitectureDescription(
            overview="Layered architecture with MVC pattern",
            patterns=["MVC", "Repository Pattern"],
            components=["Controllers", "Services", "Repositories"],
        ),
        components=[],
        data_models=[],
        interfaces=[],
        error_handling=ErrorHandlingStrategy(
            error_categories=["ValidationError", "AuthenticationError"],
            recovery_mechanisms=["Retry", "Fallback"],
            logging_strategy="Structured logging with context",
        ),
        testing_strategy=TestingStrategy(
            unit_testing="pytest with fixtures",
            integration_testing="End-to-end API tests",
            performance_testing="Load testing with locust",
            test_coverage_target=0.9,
        ),
        version="1.0",
        approved=False,
    )


@pytest.fixture
def sample_tasks() -> TaskList:
    """Create a sample task list."""
    return TaskList(
        tasks=[
            Task(
                id="TASK-1",
                title="Implement user registration",
                description="Create user registration endpoint",
                requirements_refs=["REQ-1"],
                subtasks=[],
                status=TaskStatus.NOT_STARTED,
            ),
            Task(
                id="TASK-2",
                title="Implement authentication",
                description="Create login/logout functionality",
                requirements_refs=["REQ-2"],
                subtasks=[],
                status=TaskStatus.NOT_STARTED,
            ),
        ],
        dependencies={},
        estimated_effort={},
        version="1.0",
        approved=False,
    )



class TestSpecificationApprovalStatePersistence:
    """Test specification approval and state persistence with datetime handling."""

    def test_specification_approval_saves_state_with_datetime(
        self, state_manager: StateManager, sample_specification: SpecificationDocument
    ):
        """Test that approving specification saves state correctly with datetime."""
        # Arrange: Create initial project state
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
            specification=None,
            design=None,
            tasks=None,
            implementation_progress={},
            index_metadata=None,
            session_data=session_data,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            specification_approved=False,
        )
        
        # Act: Approve specification and save
        sample_specification.approved = True
        sample_specification.approval_timestamp = datetime.now()
        state.specification = sample_specification
        state.specification_approved = True
        
        success = state_manager.save_project_state(state)
        
        # Assert: State saved successfully
        assert success is True
        assert state_manager.state_file.exists()
        
        # Verify JSON contains ISO format datetime strings
        with open(state_manager.state_file, "r") as f:
            saved_data = json.load(f)
        
        assert "specification" in saved_data
        assert saved_data["specification"]["approved"] is True
        assert "approval_timestamp" in saved_data["specification"]
        assert isinstance(saved_data["specification"]["approval_timestamp"], str)
        # Verify it's ISO format
        datetime.fromisoformat(saved_data["specification"]["approval_timestamp"])

    def test_resume_project_after_specification_approval_loads_datetime(
        self, state_manager: StateManager, sample_specification: SpecificationDocument
    ):
        """Test resuming project after specification approval loads datetime correctly."""
        # Arrange: Create and save state with approved specification
        approval_time = datetime.now()
        sample_specification.approved = True
        sample_specification.approval_timestamp = approval_time
        
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
            specification=sample_specification,
            design=None,
            tasks=None,
            implementation_progress={},
            index_metadata=None,
            session_data=session_data,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            specification_approved=True,
        )
        
        state_manager.save_project_state(state)
        
        # Act: Load state
        loaded_state = state_manager.load_project_state()
        
        # Assert: State loaded correctly with datetime objects
        assert loaded_state is not None
        assert loaded_state.specification is not None
        assert loaded_state.specification.approved is True
        assert loaded_state.specification.approval_timestamp is not None
        assert isinstance(loaded_state.specification.approval_timestamp, datetime)
        # Verify timestamp is approximately the same (within 1 second)
        time_diff = abs(
            (loaded_state.specification.approval_timestamp - approval_time).total_seconds()
        )
        assert time_diff < 1.0
        assert loaded_state.specification_approved is True


    def test_specification_without_approval_timestamp_loads_correctly(
        self, state_manager: StateManager, sample_specification: SpecificationDocument
    ):
        """Test that specification without approval_timestamp (None) loads correctly."""
        # Arrange: Create state with unapproved specification (no timestamp)
        sample_specification.approved = False
        sample_specification.approval_timestamp = None
        
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
            specification=sample_specification,
            design=None,
            tasks=None,
            implementation_progress={},
            index_metadata=None,
            session_data=session_data,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            specification_approved=False,
        )
        
        state_manager.save_project_state(state)
        
        # Act: Load state
        loaded_state = state_manager.load_project_state()
        
        # Assert: None timestamp preserved
        assert loaded_state is not None
        assert loaded_state.specification is not None
        assert loaded_state.specification.approved is False
        assert loaded_state.specification.approval_timestamp is None
        assert loaded_state.specification_approved is False


class TestDesignPhaseStatePersistence:
    """Test design phase approval and state persistence."""

    def test_design_approval_saves_state_correctly(
        self,
        state_manager: StateManager,
        sample_specification: SpecificationDocument,
        sample_design: DesignDocument,
    ):
        """Test that approving design saves state correctly with datetime."""
        # Arrange: Create state with approved specification and design
        sample_specification.approved = True
        sample_specification.approval_timestamp = datetime.now()
        
        session_data = SessionData(
            session_id=str(uuid.uuid4()),
            started_at=datetime.now(),
            last_activity=datetime.now(),
            user_approvals={"specification": True},
            pending_approvals=[],
        )
        
        state = ProjectState(
            project_path=str(state_manager.project_path),
            current_phase=PhaseType.DESIGN,
            indexing_complete=True,
            specification=sample_specification,
            design=sample_design,
            tasks=None,
            implementation_progress={},
            index_metadata=None,
            session_data=session_data,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            specification_approved=True,
            design_approved=True,
        )
        
        # Act: Save state
        success = state_manager.save_project_state(state)
        
        # Assert: State saved successfully
        assert success is True
        
        # Load and verify
        loaded_state = state_manager.load_project_state()
        assert loaded_state is not None
        assert loaded_state.current_phase == PhaseType.DESIGN
        assert loaded_state.specification is not None
        assert loaded_state.specification.approved is True
        assert loaded_state.design is not None
        assert loaded_state.design.approved is True
        assert loaded_state.specification_approved is True
        assert loaded_state.design_approved is True



class TestTaskPhaseStatePersistence:
    """Test task phase approval and state persistence."""

    def test_task_approval_saves_state_correctly(
        self,
        state_manager: StateManager,
        sample_specification: SpecificationDocument,
        sample_design: DesignDocument,
        sample_tasks: TaskList,
    ):
        """Test that approving tasks saves state correctly."""
        # Arrange: Create state with all phases approved
        sample_specification.approved = True
        sample_specification.approval_timestamp = datetime.now()
        sample_design.approved = True
        sample_tasks.approved = True
        
        session_data = SessionData(
            session_id=str(uuid.uuid4()),
            started_at=datetime.now(),
            last_activity=datetime.now(),
            user_approvals={
                "specification": True,
                "design": True,
                "tasks": True,
            },
            pending_approvals=[],
        )
        
        state = ProjectState(
            project_path=str(state_manager.project_path),
            current_phase=PhaseType.IMPLEMENTATION,
            indexing_complete=True,
            specification=sample_specification,
            design=sample_design,
            tasks=sample_tasks,
            implementation_progress={},
            index_metadata=None,
            session_data=session_data,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            specification_approved=True,
            design_approved=True,
            tasks_approved=True,
        )
        
        # Act: Save state
        success = state_manager.save_project_state(state)
        
        # Assert: State saved successfully
        assert success is True
        
        # Load and verify
        loaded_state = state_manager.load_project_state()
        assert loaded_state is not None
        assert loaded_state.current_phase == PhaseType.IMPLEMENTATION
        assert loaded_state.specification is not None
        assert loaded_state.design is not None
        assert loaded_state.tasks is not None
        assert loaded_state.tasks.approved is True
        assert loaded_state.specification_approved is True
        assert loaded_state.design_approved is True
        assert loaded_state.tasks_approved is True


class TestFullWorkflowEndToEnd:
    """Test complete workflow end-to-end with all phase transitions."""

    def test_full_workflow_all_phase_transitions(
        self,
        state_manager: StateManager,
        sample_specification: SpecificationDocument,
        sample_design: DesignDocument,
        sample_tasks: TaskList,
    ):
        """Test full workflow through all phases with state persistence."""
        # Phase 1: Indexing
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
            user_approvals={},
            pending_approvals=[],
        )
        
        state = ProjectState(
            project_path=str(state_manager.project_path),
            current_phase=PhaseType.INDEXING,
            indexing_complete=True,
            specification=None,
            design=None,
            tasks=None,
            implementation_progress={},
            index_metadata=index_metadata,
            session_data=session_data,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        state_manager.save_project_state(state)
        loaded = state_manager.load_project_state()
        assert loaded.current_phase == PhaseType.INDEXING
        assert loaded.index_metadata is not None
        assert isinstance(loaded.index_metadata.last_indexed, datetime)
        
        # Phase 2: Specification
        sample_specification.approved = True
        sample_specification.approval_timestamp = datetime.now()
        state.current_phase = PhaseType.SPECIFICATION
        state.specification = sample_specification
        state.specification_approved = True
        state.session_data.user_approvals["specification"] = True
        
        state_manager.save_project_state(state)
        loaded = state_manager.load_project_state()
        assert loaded.current_phase == PhaseType.SPECIFICATION
        assert loaded.specification is not None
        assert loaded.specification.approved is True
        assert isinstance(loaded.specification.approval_timestamp, datetime)
        assert loaded.specification_approved is True
        
        # Phase 3: Design
        sample_design.approved = True
        state.current_phase = PhaseType.DESIGN
        state.design = sample_design
        state.design_approved = True
        state.session_data.user_approvals["design"] = True
        
        state_manager.save_project_state(state)
        loaded = state_manager.load_project_state()
        assert loaded.current_phase == PhaseType.DESIGN
        assert loaded.design is not None
        assert loaded.design.approved is True
        assert loaded.design_approved is True
        
        # Phase 4: Implementation
        sample_tasks.approved = True
        state.current_phase = PhaseType.IMPLEMENTATION
        state.tasks = sample_tasks
        state.tasks_approved = True
        state.session_data.user_approvals["tasks"] = True
        
        state_manager.save_project_state(state)
        loaded = state_manager.load_project_state()
        assert loaded.current_phase == PhaseType.IMPLEMENTATION
        assert loaded.tasks is not None
        assert loaded.tasks.approved is True
        assert loaded.tasks_approved is True
        
        # Verify all datetime fields persisted correctly
        assert isinstance(loaded.created_at, datetime)
        assert isinstance(loaded.updated_at, datetime)
        assert isinstance(loaded.session_data.started_at, datetime)
        assert isinstance(loaded.session_data.last_activity, datetime)
        assert isinstance(loaded.index_metadata.last_indexed, datetime)
        assert isinstance(loaded.specification.approval_timestamp, datetime)



class TestIncompleteSpecificationWarning:
    """Test that incomplete specifications trigger warnings."""

    @pytest.fixture
    def mock_cli_interface(self):
        """Create a mock CLI interface."""
        cli = Mock()
        cli.display_message = Mock()
        cli.get_user_input = Mock()
        cli.request_approval = Mock(return_value=True)
        return cli

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        client = AsyncMock()
        client.generate_completion = AsyncMock(
            return_value="# Requirements\n\n## Requirement 1\n\n**User Story:** As a user, I want to test\n\n### Acceptance Criteria\n1. WHEN test THEN pass"
        )
        return client

    def test_incomplete_specification_triggers_warning(
        self, mock_cli_interface, mock_llm_client, temp_project_dir: Path
    ):
        """Test that specification with fewer than 3 requirements triggers warning."""
        # Arrange: Create generator with mocked dependencies
        generator = SpecificationGenerator(
            cli_interface=mock_cli_interface,
            llm_client=mock_llm_client,
        )
        
        # Create incomplete specification (only 1 requirement)
        incomplete_spec = SpecificationDocument(
            introduction="Test spec",
            key_features=["Feature 1"],
            functional_requirements=[
                Requirement(
                    id="REQ-1",
                    user_story="As a user, I want to test, so that I can verify",
                    acceptance_criteria=["WHEN test THEN pass"],
                    priority=Priority.MEDIUM,
                )
            ],
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=False,
        )
        
        # Act: Validate specification
        is_valid, issues = generator._validate_specification(incomplete_spec)
        
        # Assert: Validation should fail
        assert is_valid is False
        assert len(issues) > 0
        assert any("fewer than 3 requirements" in issue.lower() for issue in issues)

    def test_complete_specification_passes_validation(
        self, mock_cli_interface, mock_llm_client, temp_project_dir: Path
    ):
        """Test that specification with 3+ requirements passes validation."""
        # Arrange: Create generator
        generator = SpecificationGenerator(
            cli_interface=mock_cli_interface,
            llm_client=mock_llm_client,
        )
        
        # Create complete specification (3 requirements)
        complete_spec = SpecificationDocument(
            introduction="Test spec",
            key_features=["Feature 1", "Feature 2", "Feature 3"],
            functional_requirements=[
                Requirement(
                    id=f"REQ-{i}",
                    user_story=f"As a user, I want feature {i}, so that I can use it",
                    acceptance_criteria=[
                        f"WHEN user does action {i} THEN system SHALL respond",
                        f"IF condition {i} THEN system SHALL handle it",
                    ],
                    priority=Priority.MEDIUM,
                )
                for i in range(1, 4)
            ],
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=False,
        )
        
        # Act: Validate specification
        is_valid, issues = generator._validate_specification(complete_spec)
        
        # Assert: Validation should pass
        assert is_valid is True
        assert len(issues) == 0



class TestProviderSwitching:
    """Test provider switching (Azure OpenAI ↔ Gemini) across phases."""

    def test_state_persists_across_provider_switch(
        self,
        state_manager: StateManager,
        sample_specification: SpecificationDocument,
        sample_design: DesignDocument,
    ):
        """Test that state persists correctly when switching providers."""
        # Phase 1: Create state with Azure OpenAI (simulated)
        sample_specification.approved = True
        sample_specification.approval_timestamp = datetime.now()
        
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
            specification=sample_specification,
            design=None,
            tasks=None,
            implementation_progress={},
            index_metadata=None,
            session_data=session_data,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            specification_approved=True,
        )
        
        # Save state (simulating Azure OpenAI provider)
        state_manager.save_project_state(state)
        
        # Phase 2: Load state and continue with Gemini (simulated)
        loaded_state = state_manager.load_project_state()
        assert loaded_state is not None
        assert loaded_state.specification is not None
        assert isinstance(loaded_state.specification.approval_timestamp, datetime)
        
        # Add design (simulating Gemini provider)
        sample_design.approved = True
        loaded_state.current_phase = PhaseType.DESIGN
        loaded_state.design = sample_design
        loaded_state.design_approved = True
        loaded_state.session_data.user_approvals["design"] = True
        
        # Save state (simulating Gemini provider)
        state_manager.save_project_state(loaded_state)
        
        # Phase 3: Load state again (simulating switch back to Azure OpenAI)
        final_state = state_manager.load_project_state()
        assert final_state is not None
        assert final_state.specification is not None
        assert final_state.design is not None
        assert isinstance(final_state.specification.approval_timestamp, datetime)
        assert final_state.specification_approved is True
        assert final_state.design_approved is True
        
        # Verify all datetime fields are datetime objects (not strings)
        assert isinstance(final_state.created_at, datetime)
        assert isinstance(final_state.updated_at, datetime)
        assert isinstance(final_state.session_data.started_at, datetime)
        assert isinstance(final_state.session_data.last_activity, datetime)

    def test_datetime_handling_is_provider_agnostic(
        self, state_manager: StateManager, sample_specification: SpecificationDocument
    ):
        """Test that datetime handling works identically regardless of provider."""
        # Create state with various datetime fields
        approval_time = datetime.now()
        sample_specification.approved = True
        sample_specification.approval_timestamp = approval_time
        
        index_metadata = IndexMetadata(
            total_files=5,
            total_lines=500,
            languages_detected=["python"],
            index_size_mb=0.3,
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
            specification=sample_specification,
            design=None,
            tasks=None,
            implementation_progress={},
            index_metadata=index_metadata,
            session_data=session_data,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            specification_approved=True,
        )
        
        # Save and load multiple times (simulating provider switches)
        for _ in range(3):
            state_manager.save_project_state(state)
            loaded = state_manager.load_project_state()
            
            # Verify all datetime fields remain datetime objects
            assert isinstance(loaded.created_at, datetime)
            assert isinstance(loaded.updated_at, datetime)
            assert isinstance(loaded.session_data.started_at, datetime)
            assert isinstance(loaded.session_data.last_activity, datetime)
            assert isinstance(loaded.index_metadata.last_indexed, datetime)
            assert isinstance(loaded.specification.approval_timestamp, datetime)
            
            # Update state for next iteration
            state = loaded
            state.updated_at = datetime.now()
            state.session_data.last_activity = datetime.now()


class TestSessionDataDatetimeHandling:
    """Test session data datetime field handling."""

    def test_session_data_datetime_fields_persist(self, state_manager: StateManager):
        """Test that session data datetime fields persist correctly."""
        # Arrange: Create state with session data
        started_time = datetime.now()
        activity_time = datetime.now()
        
        session_data = SessionData(
            session_id=str(uuid.uuid4()),
            started_at=started_time,
            last_activity=activity_time,
            user_approvals={},
            pending_approvals=[],
        )
        
        state = ProjectState(
            project_path=str(state_manager.project_path),
            current_phase=PhaseType.INDEXING,
            indexing_complete=False,
            specification=None,
            design=None,
            tasks=None,
            implementation_progress={},
            index_metadata=None,
            session_data=session_data,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        # Act: Save and load
        state_manager.save_project_state(state)
        loaded = state_manager.load_project_state()
        
        # Assert: Session datetime fields are datetime objects
        assert loaded is not None
        assert isinstance(loaded.session_data.started_at, datetime)
        assert isinstance(loaded.session_data.last_activity, datetime)
        
        # Verify times are approximately the same (within 1 second)
        started_diff = abs(
            (loaded.session_data.started_at - started_time).total_seconds()
        )
        activity_diff = abs(
            (loaded.session_data.last_activity - activity_time).total_seconds()
        )
        assert started_diff < 1.0
        assert activity_diff < 1.0


class TestIndexMetadataDatetimeHandling:
    """Test index metadata datetime field handling."""

    def test_index_metadata_datetime_persists(self, state_manager: StateManager):
        """Test that index metadata last_indexed datetime persists correctly."""
        # Arrange: Create state with index metadata
        indexed_time = datetime.now()
        
        index_metadata = IndexMetadata(
            total_files=20,
            total_lines=2000,
            languages_detected=["python", "javascript"],
            index_size_mb=1.5,
            last_indexed=indexed_time,
            index_version="1.0",
        )
        
        session_data = SessionData(
            session_id=str(uuid.uuid4()),
            started_at=datetime.now(),
            last_activity=datetime.now(),
            user_approvals={},
            pending_approvals=[],
        )
        
        state = ProjectState(
            project_path=str(state_manager.project_path),
            current_phase=PhaseType.INDEXING,
            indexing_complete=True,
            specification=None,
            design=None,
            tasks=None,
            implementation_progress={},
            index_metadata=index_metadata,
            session_data=session_data,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        # Act: Save and load
        state_manager.save_project_state(state)
        loaded = state_manager.load_project_state()
        
        # Assert: Index metadata datetime is datetime object
        assert loaded is not None
        assert loaded.index_metadata is not None
        assert isinstance(loaded.index_metadata.last_indexed, datetime)
        
        # Verify time is approximately the same (within 1 second)
        time_diff = abs(
            (loaded.index_metadata.last_indexed - indexed_time).total_seconds()
        )
        assert time_diff < 1.0
