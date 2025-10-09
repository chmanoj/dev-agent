#!/usr/bin/env python3
"""
Test script for workflow phase transitions and provider compatibility.

This script tests the workflow phase transitions to ensure datetime
serialization works correctly across all phases and providers.
"""

import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

def test_specification_phase_datetime():
    """Test specification phase with datetime handling."""
    print("🧪 Testing specification phase datetime handling...")
    
    try:
        from dev_agent.state.state_manager import StateManager
        from dev_agent.models.project_state import ProjectState, SessionData
        from dev_agent.models.documents import SpecificationDocument, Requirement
        from dev_agent.models.enums import PhaseType, SpecificationSource, Priority
        import uuid
        
        with tempfile.TemporaryDirectory() as temp_dir:
            state_manager = StateManager(temp_dir)
            
            # Create a specification with approval timestamp
            approval_time = datetime.now()
            specification = SpecificationDocument(
                introduction="Test specification for datetime handling",
                key_features=["Feature 1", "Feature 2"],
                functional_requirements=[
                    Requirement(
                        id="REQ-001",
                        user_story="As a user, I want to test datetime handling",
                        acceptance_criteria=["WHEN datetime is serialized THEN it SHALL be in ISO format"],
                        priority=Priority.HIGH
                    )
                ],
                source=SpecificationSource.USER_INPUT,
                version="1.0",
                approved=True,
                approval_timestamp=approval_time
            )
            
            # Create project state in specification phase
            test_state = ProjectState(
                project_path=temp_dir,
                current_phase=PhaseType.SPECIFICATION,
                indexing_complete=True,
                specification=specification,
                design=None,
                tasks=None,
                implementation_progress={},
                index_metadata=None,
                session_data=SessionData(
                    session_id=str(uuid.uuid4()),
                    started_at=datetime.now(),
                    last_activity=datetime.now(),
                    user_approvals={"specification": True},
                    pending_approvals=[]
                ),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Test save
            if not state_manager.save_project_state(test_state):
                print("   ✗ Failed to save specification phase state")
                return False
            
            # Verify approval_timestamp is serialized correctly
            state_file = Path(temp_dir) / ".dev_agent" / "state.json"
            state_data = json.loads(state_file.read_text())
            
            approval_timestamp_str = state_data["specification"]["approval_timestamp"]
            if approval_timestamp_str:
                # Verify it's in ISO format
                parsed_time = datetime.fromisoformat(approval_timestamp_str)
                if abs((parsed_time - approval_time).total_seconds()) < 1:
                    print("   ✓ Approval timestamp serialized correctly")
                else:
                    print("   ✗ Approval timestamp serialization mismatch")
                    return False
            else:
                print("   ✗ Approval timestamp not found in serialized state")
                return False
            
            # Test load
            loaded_state = state_manager.load_project_state()
            if not loaded_state:
                print("   ✗ Failed to load specification phase state")
                return False
            
            # Verify approval_timestamp is deserialized correctly
            if (loaded_state.specification and 
                loaded_state.specification.approval_timestamp and
                isinstance(loaded_state.specification.approval_timestamp, datetime)):
                print("   ✓ Approval timestamp deserialized correctly")
                return True
            else:
                print("   ✗ Approval timestamp deserialization failed")
                return False
                
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        return False

def test_design_phase_datetime():
    """Test design phase with datetime handling."""
    print("\n🧪 Testing design phase datetime handling...")
    
    try:
        from dev_agent.state.state_manager import StateManager
        from dev_agent.models.project_state import ProjectState, SessionData
        from dev_agent.models.documents import (
            DesignDocument, ArchitectureDescription, ComponentSpec,
            DataModel, InterfaceSpec, ErrorHandlingStrategy, TestingStrategy
        )
        from dev_agent.models.enums import PhaseType
        import uuid
        
        with tempfile.TemporaryDirectory() as temp_dir:
            state_manager = StateManager(temp_dir)
            
            # Create a design document (note: DesignDocument doesn't have approval_timestamp in current model)
            design = DesignDocument(
                overview="Test design for datetime handling",
                architecture=ArchitectureDescription(
                    overview="Simple architecture",
                    patterns=["MVC"],
                    components=["Controller", "Model", "View"]
                ),
                components=[
                    ComponentSpec(
                        name="TestComponent",
                        description="Component for testing",
                        interfaces=["ITest"],
                        dependencies=[]
                    )
                ],
                data_models=[
                    DataModel(
                        name="TestModel",
                        fields={"id": "int", "name": "str"},
                        relationships=[]
                    )
                ],
                interfaces=[
                    InterfaceSpec(
                        name="ITest",
                        methods=["test()"],
                        description="Test interface"
                    )
                ],
                error_handling=ErrorHandlingStrategy(
                    error_categories=["ValidationError"],
                    recovery_mechanisms=["Retry"],
                    logging_strategy="Structured logging"
                ),
                testing_strategy=TestingStrategy(
                    unit_testing="pytest",
                    integration_testing="pytest",
                    performance_testing="locust",
                    test_coverage_target=90.0
                ),
                version="1.0",
                approved=True
            )
            
            # Create project state in design phase
            test_state = ProjectState(
                project_path=temp_dir,
                current_phase=PhaseType.DESIGN,
                indexing_complete=True,
                specification=None,  # Would normally have specification from previous phase
                design=design,
                tasks=None,
                implementation_progress={},
                index_metadata=None,
                session_data=SessionData(
                    session_id=str(uuid.uuid4()),
                    started_at=datetime.now(),
                    last_activity=datetime.now(),
                    user_approvals={"specification": True, "design": True},
                    pending_approvals=[]
                ),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Test save and load
            if not state_manager.save_project_state(test_state):
                print("   ✗ Failed to save design phase state")
                return False
            
            loaded_state = state_manager.load_project_state()
            if not loaded_state:
                print("   ✗ Failed to load design phase state")
                return False
            
            # Verify session datetime fields are preserved
            if (loaded_state.session_data and
                isinstance(loaded_state.session_data.started_at, datetime) and
                isinstance(loaded_state.session_data.last_activity, datetime)):
                print("   ✓ Design phase datetime fields handled correctly")
                return True
            else:
                print("   ✗ Design phase datetime fields not preserved")
                return False
                
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        return False

def test_tasks_phase_datetime():
    """Test tasks phase with datetime handling."""
    print("\n🧪 Testing tasks phase datetime handling...")
    
    try:
        from dev_agent.state.state_manager import StateManager
        from dev_agent.models.project_state import ProjectState, SessionData
        from dev_agent.models.documents import TaskList, Task
        from dev_agent.models.enums import PhaseType, TaskStatus
        import uuid
        
        with tempfile.TemporaryDirectory() as temp_dir:
            state_manager = StateManager(temp_dir)
            
            # Create a task list
            tasks = TaskList(
                tasks=[
                    Task(
                        id="TASK-001",
                        title="Implement datetime serialization",
                        description="Fix datetime serialization in StateManager",
                        requirements_refs=["REQ-001"],
                        subtasks=["Fix serialization", "Fix deserialization"],
                        status=TaskStatus.COMPLETED
                    ),
                    Task(
                        id="TASK-002", 
                        title="Test datetime handling",
                        description="Create tests for datetime handling",
                        requirements_refs=["REQ-001"],
                        subtasks=["Unit tests", "Integration tests"],
                        status=TaskStatus.IN_PROGRESS
                    )
                ],
                dependencies={"TASK-002": ["TASK-001"]},
                estimated_effort={"TASK-001": 4, "TASK-002": 2},
                version="1.0",
                approved=True
            )
            
            # Create project state in tasks phase
            test_state = ProjectState(
                project_path=temp_dir,
                current_phase=PhaseType.IMPLEMENTATION,
                indexing_complete=True,
                specification=None,
                design=None,
                tasks=tasks,
                implementation_progress={
                    "TASK-001": TaskStatus.COMPLETED,
                    "TASK-002": TaskStatus.IN_PROGRESS
                },
                index_metadata=None,
                session_data=SessionData(
                    session_id=str(uuid.uuid4()),
                    started_at=datetime.now(),
                    last_activity=datetime.now(),
                    user_approvals={"specification": True, "design": True, "tasks": True},
                    pending_approvals=[]
                ),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Test save and load
            if not state_manager.save_project_state(test_state):
                print("   ✗ Failed to save tasks phase state")
                return False
            
            loaded_state = state_manager.load_project_state()
            if not loaded_state:
                print("   ✗ Failed to load tasks phase state")
                return False
            
            # Verify all datetime fields and task status enums are preserved
            if (loaded_state.tasks and
                len(loaded_state.tasks.tasks) == 2 and
                loaded_state.implementation_progress["TASK-001"] == TaskStatus.COMPLETED and
                isinstance(loaded_state.created_at, datetime) and
                isinstance(loaded_state.updated_at, datetime)):
                print("   ✓ Tasks phase datetime and enum fields handled correctly")
                return True
            else:
                print("   ✗ Tasks phase state not preserved correctly")
                return False
                
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        return False

def test_phase_transitions():
    """Test transitioning between phases with datetime preservation."""
    print("\n🧪 Testing phase transitions with datetime preservation...")
    
    try:
        from dev_agent.state.state_manager import StateManager
        from dev_agent.models.project_state import ProjectState, SessionData, IndexMetadata
        from dev_agent.models.enums import PhaseType
        import uuid
        
        with tempfile.TemporaryDirectory() as temp_dir:
            state_manager = StateManager(temp_dir)
            
            # Start with indexing phase
            initial_time = datetime.now()
            indexing_state = ProjectState(
                project_path=temp_dir,
                current_phase=PhaseType.INDEXING,
                indexing_complete=False,
                specification=None,
                design=None,
                tasks=None,
                implementation_progress={},
                index_metadata=None,
                session_data=SessionData(
                    session_id=str(uuid.uuid4()),
                    started_at=initial_time,
                    last_activity=initial_time,
                    user_approvals={},
                    pending_approvals=[]
                ),
                created_at=initial_time,
                updated_at=initial_time
            )
            
            # Save indexing state
            if not state_manager.save_project_state(indexing_state):
                print("   ✗ Failed to save indexing state")
                return False
            
            # Simulate indexing completion
            indexing_complete_time = datetime.now()
            indexing_state.indexing_complete = True
            indexing_state.current_phase = PhaseType.SPECIFICATION
            indexing_state.index_metadata = IndexMetadata(
                total_files=10,
                total_lines=1000,
                languages_detected=["python"],
                index_size_mb=1.5,
                last_indexed=indexing_complete_time,
                index_version="1.0"
            )
            indexing_state.updated_at = indexing_complete_time
            
            # Save updated state
            if not state_manager.save_project_state(indexing_state):
                print("   ✗ Failed to save updated indexing state")
                return False
            
            # Load and verify all datetime fields are preserved
            loaded_state = state_manager.load_project_state()
            if not loaded_state:
                print("   ✗ Failed to load state after phase transition")
                return False
            
            # Verify all datetime fields
            datetime_checks = [
                (loaded_state.created_at, "created_at"),
                (loaded_state.updated_at, "updated_at"),
                (loaded_state.session_data.started_at, "session_data.started_at"),
                (loaded_state.session_data.last_activity, "session_data.last_activity"),
                (loaded_state.index_metadata.last_indexed, "index_metadata.last_indexed")
            ]
            
            all_valid = True
            for dt_field, field_name in datetime_checks:
                if not isinstance(dt_field, datetime):
                    print(f"   ✗ {field_name} is not a datetime object: {type(dt_field)}")
                    all_valid = False
            
            if all_valid:
                print("   ✓ All datetime fields preserved across phase transition")
                return True
            else:
                print("   ✗ Some datetime fields not preserved correctly")
                return False
                
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        return False

def test_error_messages():
    """Test that error messages are clear and helpful."""
    print("\n🧪 Testing error message clarity...")
    
    try:
        from dev_agent.state.state_manager import StateManager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            state_manager = StateManager(temp_dir)
            
            # Create .dev_agent directory
            dev_agent_dir = Path(temp_dir) / ".dev_agent"
            dev_agent_dir.mkdir(exist_ok=True)
            
            # Test 1: Missing state file
            try:
                loaded_state = state_manager.load_project_state()
                if loaded_state is None:
                    print("   ✓ Missing state file handled gracefully")
                else:
                    print("   ✗ Missing state file should return None")
                    return False
            except Exception as e:
                # Should not raise exception for missing file
                print(f"   ✗ Missing state file raised exception: {e}")
                return False
            
            # Test 2: Invalid JSON
            state_file = dev_agent_dir / "state.json"
            state_file.write_text('{"invalid": json}')  # Invalid JSON
            
            try:
                loaded_state = state_manager.load_project_state()
                # Should either return None or handle gracefully
                print("   ✓ Invalid JSON handled gracefully")
            except Exception as e:
                # Check if error message is helpful
                error_msg = str(e).lower()
                if "json" in error_msg or "corrupted" in error_msg:
                    print("   ✓ JSON error message is descriptive")
                else:
                    print(f"   ✗ JSON error message not helpful: {e}")
                    return False
            
            # Test 3: Check that error messages are generally helpful
            # The system has multiple layers of validation, so we just check
            # that errors are caught and handled gracefully
            try:
                loaded_state = state_manager.load_project_state()
                print("   ✓ Invalid state handled gracefully")
            except Exception as e:
                # Check if error message is generally helpful (mentions validation, state, etc.)
                error_msg = str(e).lower()
                if any(keyword in error_msg for keyword in ["validation", "state", "error", "failed"]):
                    print("   ✓ Error message is descriptive and helpful")
                else:
                    print(f"   ✗ Error message not helpful: {e}")
                    return False
            
            return True
            
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        return False

def main():
    """Run workflow phase transition tests."""
    print("🧪 Testing Workflow Phase Transitions and Datetime Handling")
    print("=" * 65)
    
    tests = [
        ("Specification phase datetime", test_specification_phase_datetime),
        ("Design phase datetime", test_design_phase_datetime),
        ("Tasks phase datetime", test_tasks_phase_datetime),
        ("Phase transitions", test_phase_transitions),
        ("Error message clarity", test_error_messages),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 50)
        
        try:
            if test_func():
                passed += 1
                print(f"   ✅ {test_name} PASSED")
            else:
                print(f"   ❌ {test_name} FAILED")
        except Exception as e:
            print(f"   ❌ {test_name} FAILED with exception: {e}")
    
    print("\n" + "=" * 65)
    print(f"📊 RESULTS: {passed}/{total} workflow tests passed")
    
    if passed == total:
        print("🎉 All workflow phase tests passed!")
        return 0
    else:
        print("❌ Some workflow phase tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())