"""Verification test for Task 2: Fix datetime deserialization in StateManager.

This test verifies that all datetime deserialization fixes work correctly:
- _deserialize_datetime() handles None values
- _reconstruct_specification() handles None approval_timestamp
- _reconstruct_design() handles None approval_timestamp (future-proofing)
- _reconstruct_tasks() handles None approval_timestamp (future-proofing)
- SessionData datetime deserialization (started_at, last_activity)
- IndexMetadata datetime deserialization (last_indexed)
- ProjectState datetime deserialization (created_at, updated_at)
"""

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


def test_task2_datetime_deserialization_fix(state_manager, temp_project_dir):
    """Comprehensive test for Task 2: datetime deserialization fixes.
    
    This test verifies:
    1. Specification with None approval_timestamp can be saved and loaded
    2. Specification with valid approval_timestamp can be saved and loaded
    3. SessionData datetime fields (started_at, last_activity) are handled correctly
    4. IndexMetadata datetime field (last_indexed) is handled correctly
    5. ProjectState datetime fields (created_at, updated_at) are handled correctly
    6. Full save/load cycle preserves all datetime values correctly
    """
    # Create timestamps
    now = datetime.now()
    approval_time = datetime(2024, 10, 9, 14, 30, 0)
    indexed_time = datetime(2024, 10, 9, 13, 0, 0)
    
    # Create specification with approval_timestamp
    spec = SpecificationDocument(
        introduction="Test specification for datetime deserialization",
        key_features=["Feature 1", "Feature 2"],
        functional_requirements=[
            Requirement(
                id="REQ-1",
                user_story="As a developer, I want datetime deserialization to work",
                acceptance_criteria=[
                    "WHEN loading state THEN datetime fields SHALL be deserialized correctly",
                    "WHEN datetime is None THEN it SHALL remain None after deserialization",
                ],
                priority=Priority.HIGH,
                source_analysis=None,
            )
        ],
        source=SpecificationSource.USER_INPUT,
        version="1.0",
        approved=True,
        approval_timestamp=approval_time,
    )
    
    # Create design document
    design = DesignDocument(
        overview="Test design document",
        architecture=ArchitectureDescription(
            overview="Architecture overview",
            patterns=["Pattern 1"],
            components=["Component 1"],
        ),
        components=[
            ComponentSpec(
                name="TestComponent",
                description="Test component",
                interfaces=["ITest"],
                dependencies=["dep1"],
            )
        ],
        data_models=[
            DataModel(
                name="TestModel",
                fields={"field1": "string"},
                relationships=["rel1"],
            )
        ],
        interfaces=[
            InterfaceSpec(
                name="ITest",
                methods=["method1"],
                description="Test interface",
            )
        ],
        error_handling=ErrorHandlingStrategy(
            error_categories=["cat1"],
            recovery_mechanisms=["mech1"],
            logging_strategy="strategy1",
        ),
        testing_strategy=TestingStrategy(
            unit_testing="Unit test strategy",
            integration_testing="Integration test strategy",
            performance_testing="Performance test strategy",
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
                title="Test task",
                description="Test task description",
                requirements_refs=["REQ-1"],
                subtasks=["subtask1"],
                status=TaskStatus.NOT_STARTED,
                target_language="python",
                context_requirements=["context1"],
                implementation_notes="Notes",
                generated_files=["file1.py"],
            )
        ],
        dependencies={"TASK-1": []},
        estimated_effort={"TASK-1": 2},
        version="1.0",
        approved=True,
    )
    
    # Create index metadata with last_indexed
    index_metadata = IndexMetadata(
        total_files=100,
        total_lines=5000,
        languages_detected=["python"],
        index_size_mb=2.5,
        last_indexed=indexed_time,
        index_version="1.0",
    )
    
    # Create session data with datetime fields
    session_data = SessionData(
        session_id="test-session-123",
        started_at=now,
        last_activity=now,
        user_approvals={"specification": True},
        pending_approvals=[],
    )
    
    # Create project state with all datetime fields
    state = ProjectState(
        project_path=str(temp_project_dir),
        current_phase=PhaseType.DESIGN,
        indexing_complete=True,
        specification=spec,
        design=design,
        tasks=tasks,
        implementation_progress={"TASK-1": TaskStatus.NOT_STARTED},
        index_metadata=index_metadata,
        session_data=session_data,
        created_at=now,
        updated_at=now,
    )
    
    # Save the state
    success = state_manager.save_project_state(state)
    assert success is True, "Failed to save project state"
    
    # Load the state
    loaded_state = state_manager.load_project_state()
    assert loaded_state is not None, "Failed to load project state"
    
    # Verify ProjectState datetime fields
    assert loaded_state.created_at is not None, "created_at should not be None"
    assert loaded_state.updated_at is not None, "updated_at should not be None"
    assert abs((loaded_state.created_at - now).total_seconds()) < 1, "created_at mismatch"
    assert abs((loaded_state.updated_at - now).total_seconds()) < 1, "updated_at mismatch"
    
    # Verify SessionData datetime fields
    assert loaded_state.session_data.started_at is not None, "started_at should not be None"
    assert loaded_state.session_data.last_activity is not None, "last_activity should not be None"
    assert abs((loaded_state.session_data.started_at - now).total_seconds()) < 1, "started_at mismatch"
    assert abs((loaded_state.session_data.last_activity - now).total_seconds()) < 1, "last_activity mismatch"
    
    # Verify IndexMetadata datetime field
    assert loaded_state.index_metadata is not None, "index_metadata should not be None"
    assert loaded_state.index_metadata.last_indexed is not None, "last_indexed should not be None"
    assert loaded_state.index_metadata.last_indexed == indexed_time, "last_indexed mismatch"
    
    # Verify Specification approval_timestamp
    assert loaded_state.specification is not None, "specification should not be None"
    assert loaded_state.specification.approval_timestamp is not None, "approval_timestamp should not be None"
    assert loaded_state.specification.approval_timestamp == approval_time, "approval_timestamp mismatch"
    
    # Verify Design document loaded correctly
    assert loaded_state.design is not None, "design should not be None"
    assert loaded_state.design.approved is True, "design should be approved"
    
    # Verify Tasks loaded correctly
    assert loaded_state.tasks is not None, "tasks should not be None"
    assert loaded_state.tasks.approved is True, "tasks should be approved"
    
    print("✅ Task 2 verification passed: All datetime deserialization fixes work correctly")


def test_task2_none_datetime_handling(state_manager, temp_project_dir):
    """Test that None datetime values are handled correctly throughout the system."""
    # Create specification with None approval_timestamp
    spec = SpecificationDocument(
        introduction="Test specification",
        key_features=["Feature 1"],
        functional_requirements=[
            Requirement(
                id="REQ-1",
                user_story="As a user, I want to test None handling",
                acceptance_criteria=["Criterion 1"],
                priority=Priority.MEDIUM,
                source_analysis=None,
            )
        ],
        source=SpecificationSource.USER_INPUT,
        version="1.0",
        approved=False,
        approval_timestamp=None,  # Explicitly None
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
    
    # Save and load
    success = state_manager.save_project_state(state)
    assert success is True
    
    loaded_state = state_manager.load_project_state()
    assert loaded_state is not None
    
    # Verify None approval_timestamp is preserved
    assert loaded_state.specification is not None
    assert loaded_state.specification.approval_timestamp is None, "approval_timestamp should be None"
    assert loaded_state.specification.approved is False
    
    # Verify None index_metadata is preserved
    assert loaded_state.index_metadata is None, "index_metadata should be None"
    
    print("✅ Task 2 None handling verification passed")


def test_task2_mixed_none_and_valid_datetimes(state_manager, temp_project_dir):
    """Test handling of mixed None and valid datetime values."""
    approval_time = datetime(2024, 10, 9, 15, 0, 0)
    
    # Specification with approval_timestamp
    spec = SpecificationDocument(
        introduction="Test specification",
        key_features=["Feature 1"],
        functional_requirements=[
            Requirement(
                id="REQ-1",
                user_story="As a user, I want mixed datetime handling",
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
        user_approvals={"specification": True},
        pending_approvals=[],
    )
    
    # No index_metadata (None)
    state = ProjectState(
        project_path=str(temp_project_dir),
        current_phase=PhaseType.SPECIFICATION,
        indexing_complete=False,
        specification=spec,
        design=None,
        tasks=None,
        implementation_progress={},
        index_metadata=None,  # None
        session_data=session_data,
        created_at=now,
        updated_at=now,
    )
    
    # Save and load
    success = state_manager.save_project_state(state)
    assert success is True
    
    loaded_state = state_manager.load_project_state()
    assert loaded_state is not None
    
    # Verify mixed datetime handling
    assert loaded_state.specification.approval_timestamp == approval_time, "approval_timestamp should be preserved"
    assert loaded_state.index_metadata is None, "index_metadata should be None"
    assert loaded_state.session_data.started_at is not None, "started_at should not be None"
    assert loaded_state.created_at is not None, "created_at should not be None"
    
    print("✅ Task 2 mixed datetime handling verification passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
