"""Test datetime serialization fix in StateManager.

This test verifies that Task 1 from workflow-phase-transition-fixes is correctly implemented:
- datetime objects are checked FIRST before other type checks
- datetime objects are converted to ISO format strings
- Recursive handling works for nested structures
- All document types serialize correctly
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from dev_agent.models.documents import (
    DesignDocument,
    SpecificationDocument,
    TaskList,
    Task,
    Requirement,
    ArchitectureDescription,
    ComponentSpec,
    DataModel,
    InterfaceSpec,
    ErrorHandlingStrategy,
    TestingStrategy,
)
from dev_agent.models.enums import (
    PhaseType,
    TaskStatus,
    Priority,
    SpecificationSource,
)
from dev_agent.models.project_state import (
    ProjectState,
    SessionData,
    IndexMetadata,
)
from dev_agent.state.state_manager import StateManager


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def state_manager(temp_project_dir):
    """Create a StateManager instance."""
    return StateManager(str(temp_project_dir))


def test_datetime_serialization_direct(state_manager):
    """Test that datetime objects are serialized to ISO format strings."""
    now = datetime(2024, 10, 9, 14, 30, 0)
    
    # Test direct datetime serialization
    result = state_manager._serialize_dataclass(now)
    
    assert isinstance(result, str)
    assert result == "2024-10-09T14:30:00"


def test_datetime_in_nested_dict(state_manager):
    """Test datetime serialization in nested dictionaries."""
    data = {
        "created_at": datetime(2024, 10, 9, 14, 30, 0),
        "nested": {
            "updated_at": datetime(2024, 10, 9, 15, 0, 0),
        },
    }
    
    result = state_manager._serialize_dataclass(data)
    
    assert result["created_at"] == "2024-10-09T14:30:00"
    assert result["nested"]["updated_at"] == "2024-10-09T15:00:00"


def test_datetime_in_list(state_manager):
    """Test datetime serialization in lists."""
    data = [
        datetime(2024, 10, 9, 14, 30, 0),
        datetime(2024, 10, 9, 15, 0, 0),
    ]
    
    result = state_manager._serialize_dataclass(data)
    
    assert result[0] == "2024-10-09T14:30:00"
    assert result[1] == "2024-10-09T15:00:00"


def test_specification_with_approval_timestamp(state_manager, temp_project_dir):
    """Test specification with approval_timestamp serializes correctly."""
    now = datetime(2024, 10, 9, 14, 30, 0)
    
    spec = SpecificationDocument(
        introduction="Test spec",
        key_features=["Feature 1"],
        functional_requirements=[
            Requirement(
                id="REQ-1",
                user_story="As a user, I want X",
                acceptance_criteria=["Criterion 1"],
                priority=Priority.HIGH,
                source_analysis=None,
            )
        ],
        source=SpecificationSource.USER_INPUT,
        version="1.0",
        approved=True,
        approval_timestamp=now,
    )
    
    session_data = SessionData(
        session_id="test-session",
        started_at=now,
        last_activity=now,
        user_approvals={},
        pending_approvals=[],
    )
    
    state = ProjectState(
        project_path=str(temp_project_dir),
        current_phase=PhaseType.SPECIFICATION,
        indexing_complete=True,
        specification=spec,
        design=None,
        tasks=None,
        implementation_progress={},
        index_metadata=None,
        session_data=session_data,
        created_at=now,
        updated_at=now,
    )
    
    # Save and verify JSON is valid
    success = state_manager.save_project_state(state)
    assert success
    
    # Read the raw JSON to verify datetime is serialized as string
    with open(state_manager.state_file) as f:
        raw_data = json.load(f)
    
    assert raw_data["specification"]["approval_timestamp"] == "2024-10-09T14:30:00"
    assert raw_data["created_at"] == "2024-10-09T14:30:00"
    # updated_at is set to current time by save_project_state, just verify it's a string
    assert isinstance(raw_data["updated_at"], str)
    assert "T" in raw_data["updated_at"]  # ISO format check
    assert raw_data["session_data"]["started_at"] == "2024-10-09T14:30:00"
    assert raw_data["session_data"]["last_activity"] == "2024-10-09T14:30:00"


def test_specification_without_approval_timestamp(state_manager, temp_project_dir):
    """Test specification without approval_timestamp (None) serializes correctly."""
    now = datetime(2024, 10, 9, 14, 30, 0)
    
    spec = SpecificationDocument(
        introduction="Test spec",
        key_features=["Feature 1"],
        functional_requirements=[
            Requirement(
                id="REQ-1",
                user_story="As a user, I want X",
                acceptance_criteria=["Criterion 1"],
                priority=Priority.HIGH,
                source_analysis=None,
            )
        ],
        source=SpecificationSource.USER_INPUT,
        version="1.0",
        approved=False,
        approval_timestamp=None,  # Not approved yet
    )
    
    session_data = SessionData(
        session_id="test-session",
        started_at=now,
        last_activity=now,
        user_approvals={},
        pending_approvals=[],
    )
    
    state = ProjectState(
        project_path=str(temp_project_dir),
        current_phase=PhaseType.SPECIFICATION,
        indexing_complete=True,
        specification=spec,
        design=None,
        tasks=None,
        implementation_progress={},
        index_metadata=None,
        session_data=session_data,
        created_at=now,
        updated_at=now,
    )
    
    # Save and verify JSON is valid
    success = state_manager.save_project_state(state)
    assert success
    
    # Read the raw JSON to verify None is preserved
    with open(state_manager.state_file) as f:
        raw_data = json.load(f)
    
    assert raw_data["specification"]["approval_timestamp"] is None


def test_design_document_serialization(state_manager, temp_project_dir):
    """Test design document with datetime fields serializes correctly."""
    now = datetime(2024, 10, 9, 15, 0, 0)
    
    design = DesignDocument(
        overview="Design overview",
        architecture=ArchitectureDescription(
            overview="Architecture overview",
            patterns=["Pattern 1"],
            components=["Component 1"],
        ),
        components=[
            ComponentSpec(
                name="Component 1",
                description="Description",
                interfaces=["Interface 1"],
                dependencies=["Dep 1"],
            )
        ],
        data_models=[
            DataModel(
                name="Model 1",
                fields={"field1": "string"},
                relationships=["Rel 1"],
            )
        ],
        interfaces=[
            InterfaceSpec(
                name="Interface 1",
                methods=["method1"],
                description="Description",
            )
        ],
        error_handling=ErrorHandlingStrategy(
            error_categories=["Category 1"],
            recovery_mechanisms=["Mechanism 1"],
            logging_strategy="Strategy 1",
        ),
        testing_strategy=TestingStrategy(
            unit_testing="Unit testing approach",
            integration_testing="Integration testing approach",
            performance_testing="Performance testing approach",
            test_coverage_target=90.0,
        ),
        version="1.0",
        approved=True,
    )
    
    session_data = SessionData(
        session_id="test-session",
        started_at=now,
        last_activity=now,
        user_approvals={},
        pending_approvals=[],
    )
    
    state = ProjectState(
        project_path=str(temp_project_dir),
        current_phase=PhaseType.DESIGN,
        indexing_complete=True,
        specification=None,
        design=design,
        tasks=None,
        implementation_progress={},
        index_metadata=None,
        session_data=session_data,
        created_at=now,
        updated_at=now,
    )
    
    # Save and verify JSON is valid
    success = state_manager.save_project_state(state)
    assert success
    
    # Read the raw JSON to verify datetime fields are strings
    with open(state_manager.state_file) as f:
        raw_data = json.load(f)
    
    assert raw_data["created_at"] == "2024-10-09T15:00:00"
    # updated_at is set to current time by save_project_state, just verify it's a string
    assert isinstance(raw_data["updated_at"], str)
    assert "T" in raw_data["updated_at"]  # ISO format check


def test_task_list_serialization(state_manager, temp_project_dir):
    """Test task list with datetime fields serializes correctly."""
    now = datetime(2024, 10, 9, 15, 30, 0)
    
    tasks = TaskList(
        tasks=[
            Task(
                id="TASK-1",
                title="Task 1",
                description="Description",
                requirements_refs=["REQ-1"],
                subtasks=["Subtask 1"],
                status=TaskStatus.NOT_STARTED,
                target_language="python",
                context_requirements=["Context 1"],
                implementation_notes="Notes",
                generated_files=[],
            )
        ],
        dependencies={"TASK-1": []},
        estimated_effort="2 hours",
        version="1.0",
        approved=True,
    )
    
    session_data = SessionData(
        session_id="test-session",
        started_at=now,
        last_activity=now,
        user_approvals={},
        pending_approvals=[],
    )
    
    state = ProjectState(
        project_path=str(temp_project_dir),
        current_phase=PhaseType.IMPLEMENTATION,
        indexing_complete=True,
        specification=None,
        design=None,
        tasks=tasks,
        implementation_progress={"TASK-1": TaskStatus.IN_PROGRESS},
        index_metadata=None,
        session_data=session_data,
        created_at=now,
        updated_at=now,
    )
    
    # Save and verify JSON is valid
    success = state_manager.save_project_state(state)
    assert success
    
    # Read the raw JSON to verify datetime fields are strings
    with open(state_manager.state_file) as f:
        raw_data = json.load(f)
    
    assert raw_data["created_at"] == "2024-10-09T15:30:00"
    # updated_at is set to current time by save_project_state, just verify it's a string
    assert isinstance(raw_data["updated_at"], str)
    assert "T" in raw_data["updated_at"]  # ISO format check


def test_index_metadata_serialization(state_manager, temp_project_dir):
    """Test index metadata with last_indexed datetime serializes correctly."""
    now = datetime(2024, 10, 9, 13, 0, 0)
    
    index_metadata = IndexMetadata(
        total_files=100,
        total_lines=5000,
        languages_detected=["python"],
        index_size_mb=2.5,
        last_indexed=now,
        index_version="1.0",
    )
    
    session_data = SessionData(
        session_id="test-session",
        started_at=now,
        last_activity=now,
        user_approvals={},
        pending_approvals=[],
    )
    
    state = ProjectState(
        project_path=str(temp_project_dir),
        current_phase=PhaseType.INDEXING,
        indexing_complete=True,
        specification=None,
        design=None,
        tasks=None,
        implementation_progress={},
        index_metadata=index_metadata,
        session_data=session_data,
        created_at=now,
        updated_at=now,
    )
    
    # Save and verify JSON is valid
    success = state_manager.save_project_state(state)
    assert success
    
    # Read the raw JSON to verify datetime fields are strings
    with open(state_manager.state_file) as f:
        raw_data = json.load(f)
    
    assert raw_data["index_metadata"]["last_indexed"] == "2024-10-09T13:00:00"


def test_session_data_datetime_serialization(state_manager, temp_project_dir):
    """Test session data datetime fields serialize correctly."""
    started = datetime(2024, 10, 9, 14, 0, 0)
    last_activity = datetime(2024, 10, 9, 15, 30, 0)
    
    session_data = SessionData(
        session_id="test-session",
        started_at=started,
        last_activity=last_activity,
        user_approvals={"spec": True},
        pending_approvals=["design"],
    )
    
    state = ProjectState(
        project_path=str(temp_project_dir),
        current_phase=PhaseType.SPECIFICATION,
        indexing_complete=True,
        specification=None,
        design=None,
        tasks=None,
        implementation_progress={},
        index_metadata=None,
        session_data=session_data,
        created_at=started,
        updated_at=last_activity,
    )
    
    # Save and verify JSON is valid
    success = state_manager.save_project_state(state)
    assert success
    
    # Read the raw JSON to verify datetime fields are strings
    with open(state_manager.state_file) as f:
        raw_data = json.load(f)
    
    assert raw_data["session_data"]["started_at"] == "2024-10-09T14:00:00"
    assert raw_data["session_data"]["last_activity"] == "2024-10-09T15:30:00"


def test_full_state_with_all_documents(state_manager, temp_project_dir):
    """Test complete state with all document types and datetime fields."""
    base_time = datetime(2024, 10, 9, 14, 0, 0)
    spec_time = datetime(2024, 10, 9, 14, 30, 0)
    design_time = datetime(2024, 10, 9, 15, 0, 0)
    task_time = datetime(2024, 10, 9, 15, 30, 0)
    
    spec = SpecificationDocument(
        introduction="Test spec",
        key_features=["Feature 1"],
        functional_requirements=[
            Requirement(
                id="REQ-1",
                user_story="As a user, I want X",
                acceptance_criteria=["Criterion 1"],
                priority=Priority.HIGH,
                source_analysis=None,
            )
        ],
        source=SpecificationSource.USER_INPUT,
        version="1.0",
        approved=True,
        approval_timestamp=spec_time,
    )
    
    design = DesignDocument(
        overview="Design overview",
        architecture=ArchitectureDescription(
            overview="Architecture overview",
            patterns=["Pattern 1"],
            components=["Component 1"],
        ),
        components=[],
        data_models=[],
        interfaces=[],
        error_handling=ErrorHandlingStrategy(
            error_categories=[],
            recovery_mechanisms=[],
            logging_strategy="",
        ),
        testing_strategy=TestingStrategy(
            unit_testing="",
            integration_testing="",
            performance_testing="",
            test_coverage_target=90.0,
        ),
        version="1.0",
        approved=True,
    )
    
    tasks = TaskList(
        tasks=[
            Task(
                id="TASK-1",
                title="Task 1",
                description="Description",
                requirements_refs=["REQ-1"],
                subtasks=[],
                status=TaskStatus.NOT_STARTED,
                target_language="python",
                context_requirements=[],
                implementation_notes="",
                generated_files=[],
            )
        ],
        dependencies={},
        estimated_effort="2 hours",
        version="1.0",
        approved=True,
    )
    
    index_metadata = IndexMetadata(
        total_files=100,
        total_lines=5000,
        languages_detected=["python"],
        index_size_mb=2.5,
        last_indexed=base_time,
        index_version="1.0",
    )
    
    session_data = SessionData(
        session_id="test-session",
        started_at=base_time,
        last_activity=task_time,
        user_approvals={},
        pending_approvals=[],
    )
    
    state = ProjectState(
        project_path=str(temp_project_dir),
        current_phase=PhaseType.IMPLEMENTATION,
        indexing_complete=True,
        specification=spec,
        design=design,
        tasks=tasks,
        implementation_progress={},
        index_metadata=index_metadata,
        session_data=session_data,
        created_at=base_time,
        updated_at=task_time,
    )
    
    # Save and verify JSON is valid
    success = state_manager.save_project_state(state)
    assert success
    
    # Read the raw JSON to verify ALL datetime fields are strings
    with open(state_manager.state_file) as f:
        raw_data = json.load(f)
    
    # Verify ProjectState datetime fields
    assert raw_data["created_at"] == "2024-10-09T14:00:00"
    # updated_at is set to current time by save_project_state, just verify it's a string
    assert isinstance(raw_data["updated_at"], str)
    assert "T" in raw_data["updated_at"]  # ISO format check
    
    # Verify Specification datetime fields
    assert raw_data["specification"]["approval_timestamp"] == "2024-10-09T14:30:00"
    
    # Verify SessionData datetime fields
    assert raw_data["session_data"]["started_at"] == "2024-10-09T14:00:00"
    assert raw_data["session_data"]["last_activity"] == "2024-10-09T15:30:00"
    
    # Verify IndexMetadata datetime fields
    assert raw_data["index_metadata"]["last_indexed"] == "2024-10-09T14:00:00"
    
    # Verify the JSON is valid and can be parsed
    assert isinstance(raw_data, dict)
