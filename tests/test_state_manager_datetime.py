"""Comprehensive unit tests for datetime handling in StateManager.

This test file verifies Task 8 from workflow-phase-transition-fixes:
- Datetime serialization to ISO format
- Datetime deserialization from ISO format
- None datetime values are preserved during serialization
- None datetime values are handled correctly during deserialization
- Specification with approval_timestamp serialization
- Specification without approval_timestamp (None) serialization
- Design document datetime handling
- Task list datetime handling
- Session data datetime handling
- Index metadata datetime handling

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from dev_agent.models.documents import (
    ArchitectureDescription,
    ComponentSpec,
    DataModel,
    DesignDocument,
    ErrorHandlingStrategy,
    InterfaceSpec,
    Requirement,
    SpecificationDocument,
    Task,
    TaskList,
    TestingStrategy,
)
from dev_agent.models.enums import (
    PhaseType,
    Priority,
    SpecificationSource,
    TaskStatus,
)
from dev_agent.models.project_state import (
    IndexMetadata,
    ProjectState,
    SessionData,
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


# ============================================================================
# Test datetime serialization to ISO format
# ============================================================================

def test_datetime_serialization_to_iso_format(state_manager):
    """Test that datetime objects are serialized to ISO format strings."""
    test_datetime = datetime(2024, 10, 9, 14, 30, 0)
    
    result = state_manager._serialize_dataclass(test_datetime)
    
    assert isinstance(result, str)
    assert result == "2024-10-09T14:30:00"


def test_datetime_serialization_with_microseconds(state_manager):
    """Test datetime serialization preserves microseconds."""
    test_datetime = datetime(2024, 10, 9, 14, 30, 0, 123456)
    
    result = state_manager._serialize_dataclass(test_datetime)
    
    assert isinstance(result, str)
    assert result == "2024-10-09T14:30:00.123456"


def test_datetime_serialization_in_nested_structure(state_manager):
    """Test datetime serialization in nested dictionaries and lists."""
    data = {
        "created_at": datetime(2024, 10, 9, 14, 30, 0),
        "nested": {
            "updated_at": datetime(2024, 10, 9, 15, 0, 0),
            "items": [
                datetime(2024, 10, 9, 16, 0, 0),
                datetime(2024, 10, 9, 17, 0, 0),
            ],
        },
    }
    
    result = state_manager._serialize_dataclass(data)
    
    assert result["created_at"] == "2024-10-09T14:30:00"
    assert result["nested"]["updated_at"] == "2024-10-09T15:00:00"
    assert result["nested"]["items"][0] == "2024-10-09T16:00:00"
    assert result["nested"]["items"][1] == "2024-10-09T17:00:00"


# ============================================================================
# Test datetime deserialization from ISO format
# ============================================================================

def test_datetime_deserialization_from_iso_format(state_manager):
    """Test that ISO format strings are deserialized to datetime objects."""
    iso_string = "2024-10-09T14:30:00"
    
    result = state_manager._deserialize_datetime(iso_string)
    
    assert isinstance(result, datetime)
    assert result.year == 2024
    assert result.month == 10
    assert result.day == 9
    assert result.hour == 14
    assert result.minute == 30
    assert result.second == 0


def test_datetime_deserialization_with_microseconds(state_manager):
    """Test datetime deserialization preserves microseconds."""
    iso_string = "2024-10-09T14:30:00.123456"
    
    result = state_manager._deserialize_datetime(iso_string)
    
    assert isinstance(result, datetime)
    assert result.microsecond == 123456


# ============================================================================
# Test None datetime values are preserved during serialization
# ============================================================================

def test_none_datetime_serialization(state_manager):
    """Test that None datetime values are preserved during serialization."""
    data = {
        "approval_timestamp": None,
        "created_at": datetime(2024, 10, 9, 14, 30, 0),
        "updated_at": None,
    }
    
    result = state_manager._serialize_dataclass(data)
    
    assert result["approval_timestamp"] is None
    assert result["created_at"] == "2024-10-09T14:30:00"
    assert result["updated_at"] is None


def test_none_datetime_in_nested_structure(state_manager):
    """Test None datetime values in nested structures."""
    data = {
        "specification": {
            "approval_timestamp": None,
        },
        "design": {
            "approval_timestamp": None,
        },
        "session_data": {
            "started_at": None,
            "last_activity": None,
        },
    }
    
    result = state_manager._serialize_dataclass(data)
    
    assert result["specification"]["approval_timestamp"] is None
    assert result["design"]["approval_timestamp"] is None
    assert result["session_data"]["started_at"] is None
    assert result["session_data"]["last_activity"] is None


# ============================================================================
# Test None datetime values are handled correctly during deserialization
# ============================================================================

def test_none_datetime_deserialization(state_manager):
    """Test that None values are handled correctly during deserialization."""
    result = state_manager._deserialize_datetime(None)
    
    assert result is None


def test_none_datetime_with_field_context(state_manager):
    """Test None datetime deserialization with field name and path context."""
    result = state_manager._deserialize_datetime(
        None,
        field_name="approval_timestamp",
        field_path="specification.approval_timestamp"
    )
    
    assert result is None


# ============================================================================
# Test specification with approval_timestamp serialization
# ============================================================================

def test_specification_with_approval_timestamp_serialization(state_manager, temp_project_dir):
    """Test specification with approval_timestamp serializes correctly."""
    approval_time = datetime(2024, 10, 9, 14, 30, 0)
    
    spec = SpecificationDocument(
        introduction="Test specification",
        key_features=["Feature 1", "Feature 2"],
        functional_requirements=[
            Requirement(
                id="REQ-1",
                user_story="As a user, I want to test datetime handling",
                acceptance_criteria=["Criterion 1", "Criterion 2"],
                priority=Priority.HIGH,
                source_analysis=None,
            )
        ],
        source=SpecificationSource.USER_INPUT,
        version="1.0",
        approved=True,
        approval_timestamp=approval_time,
    )
    
    session_data = SessionData(
        session_id="test-session",
        started_at=approval_time,
        last_activity=approval_time,
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
        created_at=approval_time,
        updated_at=approval_time,
    )
    
    # Serialize and save
    success = state_manager.save_project_state(state)
    assert success
    
    # Read raw JSON to verify serialization
    with open(state_manager.state_file) as f:
        raw_data = json.load(f)
    
    assert raw_data["specification"]["approval_timestamp"] == "2024-10-09T14:30:00"
    assert raw_data["specification"]["approved"] is True


def test_specification_approval_timestamp_roundtrip(state_manager, temp_project_dir):
    """Test specification approval_timestamp survives save/load cycle."""
    approval_time = datetime(2024, 10, 9, 14, 30, 0)
    
    spec = SpecificationDocument(
        introduction="Test specification",
        key_features=["Feature 1"],
        functional_requirements=[
            Requirement(
                id="REQ-1",
                user_story="As a user, I want to test",
                acceptance_criteria=["Criterion 1"],
                priority=Priority.HIGH,
                source_analysis=None,
            )
        ],
        source=SpecificationSource.USER_INPUT,
        version="1.0",
        approved=True,
        approval_timestamp=approval_time,
    )
    
    session_data = SessionData(
        session_id="test-session",
        started_at=approval_time,
        last_activity=approval_time,
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
        created_at=approval_time,
        updated_at=approval_time,
    )
    
    # Save and load
    state_manager.save_project_state(state)
    loaded_state = state_manager.load_project_state()
    
    assert loaded_state is not None
    assert loaded_state.specification is not None
    assert loaded_state.specification.approval_timestamp is not None
    assert loaded_state.specification.approval_timestamp.isoformat() == "2024-10-09T14:30:00"


# ============================================================================
# Test specification without approval_timestamp (None) serialization
# ============================================================================

def test_specification_without_approval_timestamp_serialization(state_manager, temp_project_dir):
    """Test specification without approval_timestamp (None) serializes correctly."""
    now = datetime(2024, 10, 9, 14, 30, 0)
    
    spec = SpecificationDocument(
        introduction="Test specification",
        key_features=["Feature 1"],
        functional_requirements=[
            Requirement(
                id="REQ-1",
                user_story="As a user, I want to test",
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
    
    # Serialize and save
    success = state_manager.save_project_state(state)
    assert success
    
    # Read raw JSON to verify None is preserved
    with open(state_manager.state_file) as f:
        raw_data = json.load(f)
    
    assert raw_data["specification"]["approval_timestamp"] is None
    assert raw_data["specification"]["approved"] is False


def test_specification_none_approval_timestamp_roundtrip(state_manager, temp_project_dir):
    """Test specification with None approval_timestamp survives save/load cycle."""
    now = datetime(2024, 10, 9, 14, 30, 0)
    
    spec = SpecificationDocument(
        introduction="Test specification",
        key_features=["Feature 1"],
        functional_requirements=[
            Requirement(
                id="REQ-1",
                user_story="As a user, I want to test",
                acceptance_criteria=["Criterion 1"],
                priority=Priority.HIGH,
                source_analysis=None,
            )
        ],
        source=SpecificationSource.USER_INPUT,
        version="1.0",
        approved=False,
        approval_timestamp=None,
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
    
    # Save and load
    state_manager.save_project_state(state)
    loaded_state = state_manager.load_project_state()
    
    assert loaded_state is not None
    assert loaded_state.specification is not None
    assert loaded_state.specification.approval_timestamp is None
    assert loaded_state.specification.approved is False


# ============================================================================
# Test design document datetime handling
# ============================================================================


def test_design_document_datetime_serialization(state_manager, temp_project_dir):
    """Test design document datetime fields serialize correctly."""
    now = datetime(2024, 10, 9, 15, 0, 0)
    
    design = DesignDocument(
        overview="Design overview",
        architecture=ArchitectureDescription(
            overview="Architecture overview",
            patterns=["Pattern 1", "Pattern 2"],
            components=["Component 1", "Component 2"],
        ),
        components=[
            ComponentSpec(
                name="Component 1",
                description="Component description",
                interfaces=["Interface 1"],
                dependencies=["Dependency 1"],
            )
        ],
        data_models=[
            DataModel(
                name="Model 1",
                fields={"field1": "string", "field2": "int"},
                relationships=["Relationship 1"],
            )
        ],
        interfaces=[
            InterfaceSpec(
                name="Interface 1",
                methods=["method1", "method2"],
                description="Interface description",
            )
        ],
        error_handling=ErrorHandlingStrategy(
            error_categories=["Category 1"],
            recovery_mechanisms=["Mechanism 1"],
            logging_strategy="Logging strategy",
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
    
    # Serialize and save
    success = state_manager.save_project_state(state)
    assert success
    
    # Read raw JSON to verify datetime fields are strings
    with open(state_manager.state_file) as f:
        raw_data = json.load(f)
    
    assert raw_data["created_at"] == "2024-10-09T15:00:00"
    assert isinstance(raw_data["updated_at"], str)
    assert "T" in raw_data["updated_at"]


def test_design_document_datetime_roundtrip(state_manager, temp_project_dir):
    """Test design document datetime fields survive save/load cycle."""
    now = datetime(2024, 10, 9, 15, 0, 0)
    
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
    
    # Save and load
    state_manager.save_project_state(state)
    loaded_state = state_manager.load_project_state()
    
    assert loaded_state is not None
    assert loaded_state.design is not None
    assert loaded_state.created_at.isoformat() == "2024-10-09T15:00:00"


# ============================================================================
# Test task list datetime handling
# ============================================================================

def test_task_list_datetime_serialization(state_manager, temp_project_dir):
    """Test task list datetime fields serialize correctly."""
    now = datetime(2024, 10, 9, 15, 30, 0)
    
    tasks = TaskList(
        tasks=[
            Task(
                id="TASK-1",
                title="Task 1",
                description="Task description",
                requirements_refs=["REQ-1"],
                subtasks=["Subtask 1", "Subtask 2"],
                status=TaskStatus.NOT_STARTED,
                target_language="python",
                context_requirements=["Context 1"],
                implementation_notes="Implementation notes",
                generated_files=[],
            ),
            Task(
                id="TASK-2",
                title="Task 2",
                description="Task description 2",
                requirements_refs=["REQ-2"],
                subtasks=[],
                status=TaskStatus.IN_PROGRESS,
                target_language="python",
                context_requirements=[],
                implementation_notes=None,
                generated_files=["file1.py"],
            ),
        ],
        dependencies={"TASK-1": [], "TASK-2": ["TASK-1"]},
        estimated_effort={"TASK-1": 2, "TASK-2": 3},
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
        implementation_progress={"TASK-1": TaskStatus.NOT_STARTED, "TASK-2": TaskStatus.IN_PROGRESS},
        index_metadata=None,
        session_data=session_data,
        created_at=now,
        updated_at=now,
    )
    
    # Serialize and save
    success = state_manager.save_project_state(state)
    assert success
    
    # Read raw JSON to verify datetime fields are strings
    with open(state_manager.state_file) as f:
        raw_data = json.load(f)
    
    assert raw_data["created_at"] == "2024-10-09T15:30:00"
    assert isinstance(raw_data["updated_at"], str)
    assert "T" in raw_data["updated_at"]


def test_task_list_datetime_roundtrip(state_manager, temp_project_dir):
    """Test task list datetime fields survive save/load cycle."""
    now = datetime(2024, 10, 9, 15, 30, 0)
    
    tasks = TaskList(
        tasks=[
            Task(
                id="TASK-1",
                title="Task 1",
                description="Task description",
                requirements_refs=["REQ-1"],
                subtasks=[],
                status=TaskStatus.NOT_STARTED,
                target_language="python",
                context_requirements=[],
                implementation_notes=None,
                generated_files=[],
            )
        ],
        dependencies={"TASK-1": []},
        estimated_effort={"TASK-1": 2},
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
        implementation_progress={"TASK-1": TaskStatus.NOT_STARTED},
        index_metadata=None,
        session_data=session_data,
        created_at=now,
        updated_at=now,
    )
    
    # Save and load
    state_manager.save_project_state(state)
    loaded_state = state_manager.load_project_state()
    
    assert loaded_state is not None
    assert loaded_state.tasks is not None
    assert len(loaded_state.tasks.tasks) == 1
    assert loaded_state.created_at.isoformat() == "2024-10-09T15:30:00"


# ============================================================================
# Test session_data datetime handling
# ============================================================================

def test_session_data_datetime_serialization(state_manager, temp_project_dir):
    """Test session_data datetime fields serialize correctly."""
    started = datetime(2024, 10, 9, 14, 0, 0)
    last_activity = datetime(2024, 10, 9, 15, 30, 0)
    
    session_data = SessionData(
        session_id="test-session-123",
        started_at=started,
        last_activity=last_activity,
        user_approvals={"specification": True, "design": False},
        pending_approvals=["tasks"],
        token_usage={"total_tokens": 1000, "prompt_tokens": 500, "completion_tokens": 500},
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
    
    # Serialize and save
    success = state_manager.save_project_state(state)
    assert success
    
    # Read raw JSON to verify datetime fields are strings
    with open(state_manager.state_file) as f:
        raw_data = json.load(f)
    
    assert raw_data["session_data"]["started_at"] == "2024-10-09T14:00:00"
    assert raw_data["session_data"]["last_activity"] == "2024-10-09T15:30:00"
    assert raw_data["session_data"]["session_id"] == "test-session-123"


def test_session_data_datetime_roundtrip(state_manager, temp_project_dir):
    """Test session_data datetime fields survive save/load cycle."""
    started = datetime(2024, 10, 9, 14, 0, 0)
    last_activity = datetime(2024, 10, 9, 15, 30, 0)
    
    session_data = SessionData(
        session_id="test-session",
        started_at=started,
        last_activity=last_activity,
        user_approvals={},
        pending_approvals=[],
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
    
    # Save and load
    state_manager.save_project_state(state)
    loaded_state = state_manager.load_project_state()
    
    assert loaded_state is not None
    assert loaded_state.session_data.started_at.isoformat() == "2024-10-09T14:00:00"
    assert loaded_state.session_data.last_activity.isoformat() == "2024-10-09T15:30:00"


def test_session_data_with_none_datetime_values(state_manager, temp_project_dir):
    """Test session_data with None datetime values."""
    session_data = SessionData(
        session_id="test-session",
        started_at=None,
        last_activity=None,
        user_approvals={},
        pending_approvals=[],
    )
    
    state = ProjectState(
        project_path=str(temp_project_dir),
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
    
    # Serialize and save
    success = state_manager.save_project_state(state)
    assert success
    
    # Read raw JSON to verify None is preserved
    with open(state_manager.state_file) as f:
        raw_data = json.load(f)
    
    assert raw_data["session_data"]["started_at"] is None
    assert raw_data["session_data"]["last_activity"] is None
    
    # Load and verify
    loaded_state = state_manager.load_project_state()
    assert loaded_state is not None
    assert loaded_state.session_data.started_at is None
    assert loaded_state.session_data.last_activity is None


# ============================================================================
# Test index_metadata datetime handling
# ============================================================================

def test_index_metadata_datetime_serialization(state_manager, temp_project_dir):
    """Test index_metadata last_indexed datetime serializes correctly."""
    indexed_time = datetime(2024, 10, 9, 13, 0, 0)
    
    index_metadata = IndexMetadata(
        total_files=150,
        total_lines=7500,
        languages_detected=["python", "javascript"],
        index_size_mb=3.5,
        last_indexed=indexed_time,
        index_version="1.0.0",
    )
    
    session_data = SessionData(
        session_id="test-session",
        started_at=indexed_time,
        last_activity=indexed_time,
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
        created_at=indexed_time,
        updated_at=indexed_time,
    )
    
    # Serialize and save
    success = state_manager.save_project_state(state)
    assert success
    
    # Read raw JSON to verify datetime fields are strings
    with open(state_manager.state_file) as f:
        raw_data = json.load(f)
    
    assert raw_data["index_metadata"]["last_indexed"] == "2024-10-09T13:00:00"
    assert raw_data["index_metadata"]["total_files"] == 150
    assert raw_data["index_metadata"]["index_size_mb"] == 3.5


def test_index_metadata_datetime_roundtrip(state_manager, temp_project_dir):
    """Test index_metadata last_indexed datetime survives save/load cycle."""
    indexed_time = datetime(2024, 10, 9, 13, 0, 0)
    
    index_metadata = IndexMetadata(
        total_files=100,
        total_lines=5000,
        languages_detected=["python"],
        index_size_mb=2.5,
        last_indexed=indexed_time,
        index_version="1.0",
    )
    
    session_data = SessionData(
        session_id="test-session",
        started_at=indexed_time,
        last_activity=indexed_time,
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
        created_at=indexed_time,
        updated_at=indexed_time,
    )
    
    # Save and load
    state_manager.save_project_state(state)
    loaded_state = state_manager.load_project_state()
    
    assert loaded_state is not None
    assert loaded_state.index_metadata is not None
    assert loaded_state.index_metadata.last_indexed.isoformat() == "2024-10-09T13:00:00"


def test_index_metadata_with_none_last_indexed(state_manager, temp_project_dir):
    """Test index_metadata with None last_indexed value."""
    index_metadata = IndexMetadata(
        total_files=100,
        total_lines=5000,
        languages_detected=["python"],
        index_size_mb=2.5,
        last_indexed=None,
        index_version="1.0",
    )
    
    session_data = SessionData(
        session_id="test-session",
        started_at=datetime.now(),
        last_activity=datetime.now(),
        user_approvals={},
        pending_approvals=[],
    )
    
    state = ProjectState(
        project_path=str(temp_project_dir),
        current_phase=PhaseType.INDEXING,
        indexing_complete=False,
        specification=None,
        design=None,
        tasks=None,
        implementation_progress={},
        index_metadata=index_metadata,
        session_data=session_data,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    # Serialize and save
    success = state_manager.save_project_state(state)
    assert success
    
    # Read raw JSON to verify None is preserved
    with open(state_manager.state_file) as f:
        raw_data = json.load(f)
    
    assert raw_data["index_metadata"]["last_indexed"] is None
    
    # Load and verify
    loaded_state = state_manager.load_project_state()
    assert loaded_state is not None
    assert loaded_state.index_metadata is not None
    assert loaded_state.index_metadata.last_indexed is None


# ============================================================================
# Test comprehensive scenarios with all document types
# ============================================================================


def test_full_state_with_all_documents_and_datetime_fields(state_manager, temp_project_dir):
    """Test complete state with all document types and all datetime fields."""
    base_time = datetime(2024, 10, 9, 14, 0, 0)
    spec_time = datetime(2024, 10, 9, 14, 30, 0)
    design_time = datetime(2024, 10, 9, 15, 0, 0)
    task_time = datetime(2024, 10, 9, 15, 30, 0)
    
    # Create specification with approval timestamp
    spec = SpecificationDocument(
        introduction="Complete test specification",
        key_features=["Feature 1", "Feature 2", "Feature 3"],
        functional_requirements=[
            Requirement(
                id="REQ-1",
                user_story="As a user, I want comprehensive datetime testing",
                acceptance_criteria=["Criterion 1", "Criterion 2", "Criterion 3"],
                priority=Priority.HIGH,
                source_analysis=None,
            )
        ],
        source=SpecificationSource.USER_INPUT,
        version="1.0",
        approved=True,
        approval_timestamp=spec_time,
    )
    
    # Create design document
    design = DesignDocument(
        overview="Complete design overview",
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
    
    # Create task list
    tasks = TaskList(
        tasks=[
            Task(
                id="TASK-1",
                title="Task 1",
                description="Task description",
                requirements_refs=["REQ-1"],
                subtasks=[],
                status=TaskStatus.NOT_STARTED,
                target_language="python",
                context_requirements=[],
                implementation_notes=None,
                generated_files=[],
            )
        ],
        dependencies={},
        estimated_effort={"TASK-1": 2},
        version="1.0",
        approved=True,
    )
    
    # Create index metadata
    index_metadata = IndexMetadata(
        total_files=100,
        total_lines=5000,
        languages_detected=["python"],
        index_size_mb=2.5,
        last_indexed=base_time,
        index_version="1.0",
    )
    
    # Create session data
    session_data = SessionData(
        session_id="test-session",
        started_at=base_time,
        last_activity=task_time,
        user_approvals={"specification": True, "design": True, "tasks": True},
        pending_approvals=[],
    )
    
    # Create complete project state
    state = ProjectState(
        project_path=str(temp_project_dir),
        current_phase=PhaseType.IMPLEMENTATION,
        indexing_complete=True,
        specification=spec,
        design=design,
        tasks=tasks,
        implementation_progress={"TASK-1": TaskStatus.NOT_STARTED},
        index_metadata=index_metadata,
        session_data=session_data,
        created_at=base_time,
        updated_at=task_time,
        specification_approved=True,
        design_approved=True,
        tasks_approved=True,
    )
    
    # Serialize and save
    success = state_manager.save_project_state(state)
    assert success
    
    # Read raw JSON to verify ALL datetime fields are strings
    with open(state_manager.state_file) as f:
        raw_data = json.load(f)
    
    # Verify ProjectState datetime fields
    assert raw_data["created_at"] == "2024-10-09T14:00:00"
    assert isinstance(raw_data["updated_at"], str)
    assert "T" in raw_data["updated_at"]
    
    # Verify Specification datetime fields
    assert raw_data["specification"]["approval_timestamp"] == "2024-10-09T14:30:00"
    
    # Verify SessionData datetime fields
    assert raw_data["session_data"]["started_at"] == "2024-10-09T14:00:00"
    assert raw_data["session_data"]["last_activity"] == "2024-10-09T15:30:00"
    
    # Verify IndexMetadata datetime fields
    assert raw_data["index_metadata"]["last_indexed"] == "2024-10-09T14:00:00"
    
    # Load and verify all datetime fields are correctly deserialized
    loaded_state = state_manager.load_project_state()
    assert loaded_state is not None
    
    # Verify all documents are present
    assert loaded_state.specification is not None
    assert loaded_state.design is not None
    assert loaded_state.tasks is not None
    assert loaded_state.index_metadata is not None
    
    # Verify all datetime fields are datetime objects
    assert isinstance(loaded_state.created_at, datetime)
    assert isinstance(loaded_state.updated_at, datetime)
    assert isinstance(loaded_state.specification.approval_timestamp, datetime)
    assert isinstance(loaded_state.session_data.started_at, datetime)
    assert isinstance(loaded_state.session_data.last_activity, datetime)
    assert isinstance(loaded_state.index_metadata.last_indexed, datetime)
    
    # Verify datetime values are correct
    assert loaded_state.created_at.isoformat() == "2024-10-09T14:00:00"
    assert loaded_state.specification.approval_timestamp.isoformat() == "2024-10-09T14:30:00"
    assert loaded_state.session_data.started_at.isoformat() == "2024-10-09T14:00:00"
    assert loaded_state.session_data.last_activity.isoformat() == "2024-10-09T15:30:00"
    assert loaded_state.index_metadata.last_indexed.isoformat() == "2024-10-09T14:00:00"


def test_mixed_none_and_valid_datetime_values(state_manager, temp_project_dir):
    """Test state with mix of None and valid datetime values."""
    now = datetime(2024, 10, 9, 14, 30, 0)
    
    # Specification with None approval_timestamp
    spec = SpecificationDocument(
        introduction="Test spec",
        key_features=["Feature 1"],
        functional_requirements=[
            Requirement(
                id="REQ-1",
                user_story="As a user, I want to test",
                acceptance_criteria=["Criterion 1"],
                priority=Priority.HIGH,
                source_analysis=None,
            )
        ],
        source=SpecificationSource.USER_INPUT,
        version="1.0",
        approved=False,
        approval_timestamp=None,  # Not approved
    )
    
    # Index metadata with None last_indexed
    index_metadata = IndexMetadata(
        total_files=100,
        total_lines=5000,
        languages_detected=["python"],
        index_size_mb=2.5,
        last_indexed=None,  # Not indexed yet
        index_version="1.0",
    )
    
    # Session data with valid datetime values
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
        indexing_complete=False,
        specification=spec,
        design=None,
        tasks=None,
        implementation_progress={},
        index_metadata=index_metadata,
        session_data=session_data,
        created_at=now,
        updated_at=now,
    )
    
    # Save and load
    state_manager.save_project_state(state)
    loaded_state = state_manager.load_project_state()
    
    assert loaded_state is not None
    
    # Verify None values are preserved
    assert loaded_state.specification.approval_timestamp is None
    assert loaded_state.index_metadata.last_indexed is None
    
    # Verify valid datetime values are correct
    assert loaded_state.session_data.started_at.isoformat() == "2024-10-09T14:30:00"
    assert loaded_state.session_data.last_activity.isoformat() == "2024-10-09T14:30:00"
    assert loaded_state.created_at.isoformat() == "2024-10-09T14:30:00"
