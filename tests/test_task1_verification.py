"""Verification test for Task 1: Fix datetime serialization in StateManager.

This test demonstrates that the datetime serialization fix works correctly
by creating a complete project state with all document types and verifying
that it can be saved and loaded without errors.
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


def test_task1_datetime_serialization_fix():
    """Verify Task 1: datetime serialization works across all workflow phases.
    
    This test creates a complete project state with:
    - Specification with approval_timestamp
    - Design document
    - Task list
    - Index metadata with last_indexed
    - Session data with started_at and last_activity
    - ProjectState with created_at and updated_at
    
    It verifies that:
    1. All datetime fields are serialized to ISO format strings
    2. The JSON file can be written without errors
    3. The state can be loaded back correctly
    4. All datetime fields are preserved
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)
        state_manager = StateManager(str(project_path))
        
        # Create timestamps for different phases
        index_time = datetime(2024, 10, 9, 13, 0, 0)
        spec_time = datetime(2024, 10, 9, 14, 30, 0)
        session_start = datetime(2024, 10, 9, 14, 0, 0)
        
        # Create specification with approval timestamp
        spec = SpecificationDocument(
            introduction="Test specification",
            key_features=["Feature 1", "Feature 2"],
            functional_requirements=[
                Requirement(
                    id="REQ-1",
                    user_story="As a developer, I want datetime serialization to work",
                    acceptance_criteria=[
                        "WHEN datetime objects are serialized THEN they SHALL be converted to ISO format",
                        "WHEN datetime fields are None THEN they SHALL be preserved as None",
                    ],
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
            overview="Design for datetime serialization fix",
            architecture=ArchitectureDescription(
                overview="Update StateManager to handle datetime correctly",
                patterns=["Check datetime FIRST before other type checks"],
                components=["StateManager"],
            ),
            components=[
                ComponentSpec(
                    name="StateManager",
                    description="Manages project state persistence",
                    interfaces=["_serialize_dataclass", "_deserialize_datetime"],
                    dependencies=["datetime", "json"],
                )
            ],
            data_models=[],
            interfaces=[],
            error_handling=ErrorHandlingStrategy(
                error_categories=["Serialization errors"],
                recovery_mechanisms=["Log and raise"],
                logging_strategy="Log all errors with context",
            ),
            testing_strategy=TestingStrategy(
                unit_testing="Test all document types",
                integration_testing="Test full workflow",
                performance_testing="Verify save < 100ms",
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
                    title="Fix datetime serialization",
                    description="Update _serialize_dataclass to check datetime FIRST",
                    requirements_refs=["REQ-1"],
                    subtasks=[
                        "Check isinstance(obj, datetime) before other checks",
                        "Convert to ISO format using .isoformat()",
                        "Test with all document types",
                    ],
                    status=TaskStatus.COMPLETED,
                    target_language="python",
                    context_requirements=["StateManager implementation"],
                    implementation_notes="Move datetime check to top of method",
                    generated_files=["dev_agent/state/state_manager.py"],
                )
            ],
            dependencies={"TASK-1": []},
            estimated_effort="2 hours",
            version="1.0",
            approved=True,
        )
        
        # Create index metadata
        index_metadata = IndexMetadata(
            total_files=150,
            total_lines=7500,
            languages_detected=["python"],
            index_size_mb=3.2,
            last_indexed=index_time,
            index_version="1.0",
        )
        
        # Create session data
        session_data = SessionData(
            session_id="test-session-task1",
            started_at=session_start,
            last_activity=spec_time,
            user_approvals={"specification": True, "design": True, "tasks": True},
            pending_approvals=[],
        )
        
        # Create complete project state
        state = ProjectState(
            project_path=str(project_path),
            current_phase=PhaseType.IMPLEMENTATION,
            indexing_complete=True,
            specification=spec,
            design=design,
            tasks=tasks,
            implementation_progress={"TASK-1": TaskStatus.COMPLETED},
            index_metadata=index_metadata,
            session_data=session_data,
            created_at=session_start,
            updated_at=spec_time,
        )
        
        # STEP 1: Save the state (this should not raise any errors)
        success = state_manager.save_project_state(state)
        assert success, "Failed to save project state"
        
        # STEP 2: Verify the JSON file contains ISO format datetime strings
        with open(state_manager.state_file) as f:
            raw_data = json.load(f)
        
        # Verify all datetime fields are strings in ISO format
        assert raw_data["created_at"] == "2024-10-09T14:00:00"
        assert raw_data["specification"]["approval_timestamp"] == "2024-10-09T14:30:00"
        assert raw_data["session_data"]["started_at"] == "2024-10-09T14:00:00"
        assert raw_data["session_data"]["last_activity"] == "2024-10-09T14:30:00"
        assert raw_data["index_metadata"]["last_indexed"] == "2024-10-09T13:00:00"
        
        # STEP 3: Load the state back (this should not raise any errors)
        loaded_state = state_manager.load_project_state()
        assert loaded_state is not None, "Failed to load project state"
        
        # STEP 4: Verify all datetime fields are preserved correctly
        assert loaded_state.created_at == session_start
        assert loaded_state.specification.approval_timestamp == spec_time
        assert loaded_state.session_data.started_at == session_start
        assert loaded_state.session_data.last_activity == spec_time
        assert loaded_state.index_metadata.last_indexed == index_time
        
        # STEP 5: Verify the state is complete and correct
        assert loaded_state.current_phase == PhaseType.IMPLEMENTATION
        assert loaded_state.indexing_complete is True
        assert loaded_state.specification is not None
        assert loaded_state.design is not None
        assert loaded_state.tasks is not None
        assert len(loaded_state.tasks.tasks) == 1
        assert loaded_state.tasks.tasks[0].status == TaskStatus.COMPLETED
        
        print("✅ Task 1 verification passed!")
        print("   - datetime objects are serialized to ISO format strings")
        print("   - All document types (specification, design, tasks) work correctly")
        print("   - Nested datetime fields (session_data, index_metadata) work correctly")
        print("   - State can be saved and loaded without errors")


if __name__ == "__main__":
    test_task1_datetime_serialization_fix()
    print("\n✅ All Task 1 requirements verified successfully!")
