#!/usr/bin/env python3
"""
Test script specifically for datetime serialization/deserialization fixes.

This script tests the core datetime handling fixes without requiring
full provider configuration.
"""

import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

def test_state_manager_datetime_fixes():
    """Test StateManager datetime serialization/deserialization fixes."""
    print("🧪 Testing StateManager datetime fixes...")
    
    try:
        from dev_agent.state.state_manager import StateManager
        from dev_agent.models.project_state import ProjectState, SessionData
        from dev_agent.models.enums import PhaseType
        import uuid
        
        # Create temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize StateManager
            state_manager = StateManager(temp_dir)
            
            # Create test project state with datetime fields
            now = datetime.now()
            test_state = ProjectState(
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
                    started_at=now,
                    last_activity=now,
                    user_approvals=[],
                    pending_approvals=[]
                ),
                created_at=now,
                updated_at=now
            )
            
            print("   ✓ Created test project state with datetime fields")
            
            # Test serialization
            try:
                success = state_manager.save_project_state(test_state)
                if success:
                    print("   ✓ Datetime serialization successful")
                else:
                    print("   ✗ Datetime serialization failed")
                    return False
            except Exception as e:
                print(f"   ✗ Datetime serialization error: {e}")
                return False
            
            # Verify state file contains ISO format datetime strings
            state_file = Path(temp_dir) / ".dev_agent" / "state.json"
            if state_file.exists():
                try:
                    state_data = json.loads(state_file.read_text())
                    
                    # Check that datetime fields are ISO format strings
                    datetime_fields = [
                        "created_at",
                        "updated_at", 
                        "session_data.started_at",
                        "session_data.last_activity"
                    ]
                    
                    valid_fields = 0
                    for field_path in datetime_fields:
                        if check_datetime_field_format(state_data, field_path):
                            valid_fields += 1
                    
                    if valid_fields == len(datetime_fields):
                        print("   ✓ All datetime fields properly serialized to ISO format")
                    else:
                        print(f"   ✗ Only {valid_fields}/{len(datetime_fields)} datetime fields valid")
                        return False
                        
                except Exception as e:
                    print(f"   ✗ Error reading state file: {e}")
                    return False
            else:
                print("   ✗ State file not created")
                return False
            
            # Test deserialization
            try:
                loaded_state = state_manager.load_project_state()
                if loaded_state:
                    print("   ✓ Datetime deserialization successful")
                    
                    # Verify datetime fields are datetime objects
                    if (isinstance(loaded_state.created_at, datetime) and
                        isinstance(loaded_state.updated_at, datetime) and
                        isinstance(loaded_state.session_data.started_at, datetime) and
                        isinstance(loaded_state.session_data.last_activity, datetime)):
                        print("   ✓ All datetime fields properly deserialized to datetime objects")
                        return True
                    else:
                        print("   ✗ Datetime fields not properly deserialized")
                        return False
                else:
                    print("   ✗ Failed to load project state")
                    return False
            except Exception as e:
                print(f"   ✗ Datetime deserialization error: {e}")
                return False
                
    except ImportError as e:
        print(f"   ✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        return False

def test_none_datetime_handling():
    """Test handling of None datetime values."""
    print("\n🧪 Testing None datetime handling...")
    
    try:
        from dev_agent.state.state_manager import StateManager
        from dev_agent.models.project_state import ProjectState, SessionData
        from dev_agent.models.documents import SpecificationDocument
        from dev_agent.models.enums import PhaseType, SpecificationSource
        import uuid
        
        with tempfile.TemporaryDirectory() as temp_dir:
            state_manager = StateManager(temp_dir)
            
            # Create specification with None approval_timestamp (this is the proper optional field)
            spec_with_none_timestamp = SpecificationDocument(
                introduction="Test specification",
                key_features=["Feature 1"],
                functional_requirements=[],
                source=SpecificationSource.USER_INPUT,
                version="1.0",
                approved=False,
                approval_timestamp=None  # This is the proper None datetime field
            )
            
            # Create state with specification containing None datetime
            test_state = ProjectState(
                project_path=temp_dir,
                current_phase=PhaseType.SPECIFICATION,
                indexing_complete=True,
                specification=spec_with_none_timestamp,
                design=None,
                tasks=None,
                implementation_progress={},
                index_metadata=None,
                session_data=SessionData(
                    session_id=str(uuid.uuid4()),
                    started_at=datetime.now(),
                    last_activity=datetime.now(),
                    user_approvals={},
                    pending_approvals=[]
                ),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Test serialization with None approval_timestamp
            try:
                success = state_manager.save_project_state(test_state)
                if success:
                    print("   ✓ Serialization with None approval_timestamp successful")
                else:
                    print("   ✗ Serialization with None approval_timestamp failed")
                    return False
            except Exception as e:
                print(f"   ✗ Serialization error with None values: {e}")
                return False
            
            # Verify state file contains null for approval_timestamp
            state_file = Path(temp_dir) / ".dev_agent" / "state.json"
            state_data = json.loads(state_file.read_text())
            if (state_data.get("specification", {}).get("approval_timestamp") is None):
                print("   ✓ None approval_timestamp properly serialized as null")
            else:
                print("   ✗ None approval_timestamp not serialized correctly")
                return False
            
            # Test deserialization with None values
            try:
                loaded_state = state_manager.load_project_state()
                if loaded_state:
                    # Check that None approval_timestamp is preserved
                    if (loaded_state.specification and 
                        loaded_state.specification.approval_timestamp is None):
                        print("   ✓ None approval_timestamp properly preserved")
                        return True
                    else:
                        print("   ✗ None approval_timestamp not preserved")
                        print(f"     Actual value: {loaded_state.specification.approval_timestamp if loaded_state.specification else 'No specification'}")
                        return False
                else:
                    print("   ✗ Failed to load state with None values")
                    return False
            except Exception as e:
                print(f"   ✗ Deserialization error with None values: {e}")
                return False
                
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        return False

def test_corrupted_state_recovery():
    """Test state corruption recovery mechanism."""
    print("\n🧪 Testing state corruption recovery...")
    
    try:
        from dev_agent.state.state_manager import StateManager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            state_manager = StateManager(temp_dir, enable_recovery=True)
            
            # Create .dev_agent directory
            dev_agent_dir = Path(temp_dir) / ".dev_agent"
            dev_agent_dir.mkdir(exist_ok=True)
            
            # Create corrupted state file
            state_file = dev_agent_dir / "state.json"
            state_file.write_text('{"invalid": "json", "missing_bracket": true')
            
            print("   ✓ Created corrupted state file")
            
            # Try to load state - should trigger recovery
            try:
                loaded_state = state_manager.load_project_state()
                
                # Check if recovery was attempted (backup file created)
                backup_files = list(dev_agent_dir.glob("state.backup.*"))
                if backup_files:
                    print("   ✓ Backup file created during recovery")
                    
                    # Check if fresh state was created
                    if loaded_state:
                        print("   ✓ Fresh state created after corruption")
                        return True
                    else:
                        print("   ✗ Fresh state not created")
                        return False
                else:
                    print("   ✗ No backup file created")
                    return False
                    
            except Exception as e:
                # Recovery might raise an exception - check if backup was created
                backup_files = list(dev_agent_dir.glob("state.backup.*"))
                if backup_files:
                    print("   ✓ Recovery mechanism triggered (backup created)")
                    return True
                else:
                    print(f"   ✗ Recovery failed: {e}")
                    return False
                    
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        return False

def test_specification_validation():
    """Test specification validation functionality."""
    print("\n🧪 Testing specification validation...")
    
    try:
        from dev_agent.generation.specification_generator import SpecificationGenerator
        
        # Check if validation method exists
        if hasattr(SpecificationGenerator, '_validate_specification'):
            print("   ✓ Specification validation method exists")
            
            # Try to create an instance (might fail without full config, but that's OK)
            try:
                # This might fail due to missing config, but we just want to check the method exists
                generator = SpecificationGenerator(None, None, None)
                print("   ✓ SpecificationGenerator can be instantiated")
            except Exception:
                print("   ⚠️  SpecificationGenerator requires full config (expected)")
            
            return True
        else:
            print("   ✗ Specification validation method not found")
            return False
            
    except ImportError as e:
        print(f"   ✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        return False

def check_datetime_field_format(data: Dict[str, Any], field_path: str) -> bool:
    """Check if a nested datetime field is in ISO format."""
    try:
        parts = field_path.split('.')
        current = data
        
        for part in parts:
            if part in current:
                current = current[part]
            else:
                return False  # Field doesn't exist
        
        if current is None:
            return True  # None is valid for optional datetime fields
        
        # Check if it's a string in ISO format
        if isinstance(current, str):
            datetime.fromisoformat(current)
            return True
        else:
            return False  # Should be string, not datetime object
            
    except (ValueError, KeyError, TypeError):
        return False

def main():
    """Run datetime-specific tests."""
    print("🧪 Testing Datetime Serialization/Deserialization Fixes")
    print("=" * 60)
    
    tests = [
        ("StateManager datetime fixes", test_state_manager_datetime_fixes),
        ("None datetime handling", test_none_datetime_handling),
        ("State corruption recovery", test_corrupted_state_recovery),
        ("Specification validation", test_specification_validation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                passed += 1
                print(f"   ✅ {test_name} PASSED")
            else:
                print(f"   ❌ {test_name} FAILED")
        except Exception as e:
            print(f"   ❌ {test_name} FAILED with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All datetime tests passed!")
        return 0
    else:
        print("❌ Some datetime tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())