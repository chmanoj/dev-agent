"""Tests for datetime deserialization fixes in StateManager."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from dev_agent.models.documents import SpecificationDocument
from dev_agent.models.enums import PhaseType, Priority, SpecificationSource
from dev_agent.models.project_state import IndexMetadata, ProjectState, SessionData
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


def test_deserialize_datetime_with_none(state_manager):
    """Test that _deserialize_datetime handles None values correctly."""
    # Test with None
    result = state_manager._deserialize_datetime(None)
    assert result is None
    
    # Test with valid ISO string
    iso_string = "2024-10-09T14:30:00"
    result = state_manager._deserialize_datetime(iso_string)
    assert isinstance(result, datetime)
    assert result.isoformat() == iso_string


def test_reconstruct_specification_with_none_approval_timestamp(state_manager):
    """Test that specification reconstruction handles None approval_timestamp."""
    spec_dict = {
        "introduction": "Test introduction",
        "key_features": ["Feature 1", "Feature 2"],
        "functional_requirements": [],
        "source": "user_input",
        "version": "1.0",
        "approved": False,
        "approval_timestamp": None,  # None value
    }
    
    spec = state_manager._reconstruct_specification(spec_dict)
    
    assert spec.introduction == "Test introduction"
    assert spec.approval_timestamp is None
    assert spec.approved is False


def test_reconstruct_specification_with_approval_timestamp(state_manager):
    """Test that specification reconstruction handles valid approval_timestamp."""
    timestamp_str = "2024-10-09T14:30:00"
    spec_dict = {
        "introduction": "Test introduction",
        "key_features": ["Feature 1", "Feature 2"],
        "functional_requirements": [],
        "source": "user_input",
        "version": "1.0",
        "approved": True,
        "approval_timestamp": timestamp_str,
    }
    
    spec = state_manager._reconstruct_specification(spec_dict)
    
    assert spec.introduction == "Test introduction"
    assert spec.approval_timestamp is not None
    assert spec.approval_timestamp.isoformat() == timestamp_str
    assert spec.approved is True


def test_reconstruct_project_state_with_none_datetimes(state_manager, temp_project_dir):
    """Test that project state reconstruction handles None datetime values."""
    state_dict = {
        "project_path": str(temp_project_dir),
        "current_phase": "indexing",
        "indexing_complete": False,
        "specification": None,
        "design": None,
        "tasks": None,
        "implementation_progress": {},
        "index_metadata": None,
        "session_data": {
            "session_id": "test-session",
            "started_at": None,  # None value
            "last_activity": None,  # None value
            "user_approvals": {},
            "pending_approvals": [],
        },
        "created_at": None,  # None value
        "updated_at": None,  # None value
    }
    
    state = state_manager._reconstruct_project_state(state_dict)
    
    assert state.project_path == str(temp_project_dir)
    assert state.created_at is None
    assert state.updated_at is None
    assert state.session_data.started_at is None
    assert state.session_data.last_activity is None


def test_reconstruct_project_state_with_valid_datetimes(state_manager, temp_project_dir):
    """Test that project state reconstruction handles valid datetime values."""
    created_str = "2024-10-09T14:00:00"
    updated_str = "2024-10-09T14:30:00"
    started_str = "2024-10-09T14:00:00"
    activity_str = "2024-10-09T14:30:00"
    
    state_dict = {
        "project_path": str(temp_project_dir),
        "current_phase": "indexing",
        "indexing_complete": False,
        "specification": None,
        "design": None,
        "tasks": None,
        "implementation_progress": {},
        "index_metadata": None,
        "session_data": {
            "session_id": "test-session",
            "started_at": started_str,
            "last_activity": activity_str,
            "user_approvals": {},
            "pending_approvals": [],
        },
        "created_at": created_str,
        "updated_at": updated_str,
    }
    
    state = state_manager._reconstruct_project_state(state_dict)
    
    assert state.created_at.isoformat() == created_str
    assert state.updated_at.isoformat() == updated_str
    assert state.session_data.started_at.isoformat() == started_str
    assert state.session_data.last_activity.isoformat() == activity_str


def test_reconstruct_index_metadata_with_none_last_indexed(state_manager, temp_project_dir):
    """Test that index metadata reconstruction handles None last_indexed."""
    state_dict = {
        "project_path": str(temp_project_dir),
        "current_phase": "indexing",
        "indexing_complete": False,
        "specification": None,
        "design": None,
        "tasks": None,
        "implementation_progress": {},
        "index_metadata": {
            "total_files": 100,
            "total_lines": 5000,
            "languages_detected": ["python"],
            "index_size_mb": 2.5,
            "last_indexed": None,  # None value
            "index_version": "1.0",
        },
        "session_data": {
            "session_id": "test-session",
            "started_at": "2024-10-09T14:00:00",
            "last_activity": "2024-10-09T14:30:00",
            "user_approvals": {},
            "pending_approvals": [],
        },
        "created_at": "2024-10-09T14:00:00",
        "updated_at": "2024-10-09T14:30:00",
    }
    
    state = state_manager._reconstruct_project_state(state_dict)
    
    assert state.index_metadata is not None
    assert state.index_metadata.last_indexed is None
    assert state.index_metadata.total_files == 100


def test_reconstruct_index_metadata_with_valid_last_indexed(state_manager, temp_project_dir):
    """Test that index metadata reconstruction handles valid last_indexed."""
    indexed_str = "2024-10-09T13:00:00"
    
    state_dict = {
        "project_path": str(temp_project_dir),
        "current_phase": "indexing",
        "indexing_complete": True,
        "specification": None,
        "design": None,
        "tasks": None,
        "implementation_progress": {},
        "index_metadata": {
            "total_files": 100,
            "total_lines": 5000,
            "languages_detected": ["python"],
            "index_size_mb": 2.5,
            "last_indexed": indexed_str,
            "index_version": "1.0",
        },
        "session_data": {
            "session_id": "test-session",
            "started_at": "2024-10-09T14:00:00",
            "last_activity": "2024-10-09T14:30:00",
            "user_approvals": {},
            "pending_approvals": [],
        },
        "created_at": "2024-10-09T14:00:00",
        "updated_at": "2024-10-09T14:30:00",
    }
    
    state = state_manager._reconstruct_project_state(state_dict)
    
    assert state.index_metadata is not None
    assert state.index_metadata.last_indexed.isoformat() == indexed_str


def test_full_save_and_load_cycle_with_none_approval_timestamp(state_manager, temp_project_dir):
    """Test full save/load cycle with None approval_timestamp."""
    # Create a state with specification that has None approval_timestamp
    from dev_agent.models.documents import Requirement
    
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
        approval_timestamp=None,  # None value
    )
    
    now = datetime.now()
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
    
    # Save the state
    success = state_manager.save_project_state(state)
    assert success is True
    
    # Load the state
    loaded_state = state_manager.load_project_state()
    assert loaded_state is not None
    assert loaded_state.specification is not None
    assert loaded_state.specification.approval_timestamp is None
    assert loaded_state.specification.approved is False


def test_full_save_and_load_cycle_with_approval_timestamp(state_manager, temp_project_dir):
    """Test full save/load cycle with valid approval_timestamp."""
    from dev_agent.models.documents import Requirement
    
    approval_time = datetime.now()
    
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
        approved=True,
        approval_timestamp=approval_time,
    )
    
    now = datetime.now()
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
    
    # Save the state
    success = state_manager.save_project_state(state)
    assert success is True
    
    # Load the state
    loaded_state = state_manager.load_project_state()
    assert loaded_state is not None
    assert loaded_state.specification is not None
    assert loaded_state.specification.approval_timestamp is not None
    # Compare timestamps (allowing for microsecond precision differences)
    assert abs((loaded_state.specification.approval_timestamp - approval_time).total_seconds()) < 1
    assert loaded_state.specification.approved is True
