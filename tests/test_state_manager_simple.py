"""Simple unit tests for StateManager class without numpy dependencies."""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dev_agent.models.enums import DocumentType, PhaseType, TaskStatus
from dev_agent.models.project_state import IndexMetadata, ProjectState, SessionData
from dev_agent.state.state_manager import StateManager


class TestStateManagerSimple(unittest.TestCase):
    """Simple test cases for StateManager functionality."""

    def setUp(self):
        """Set up test environment with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "test_project"
        self.project_path.mkdir()
        self.state_manager = StateManager(str(self.project_path))

        # Create minimal sample data for testing
        self.sample_session_data = SessionData(
            session_id="test-session-123",
            started_at=datetime(2024, 1, 1, 10, 0, 0),
            last_activity=datetime(2024, 1, 1, 11, 0, 0),
            user_approvals={"specification": True},
            pending_approvals=["design"],
        )

        self.sample_index_metadata = IndexMetadata(
            total_files=100,
            total_lines=5000,
            languages_detected=["python", "javascript"],
            index_size_mb=2.5,
            last_indexed=datetime(2024, 1, 1, 9, 0, 0),
            index_version="1.0.0",
        )

        self.sample_project_state = ProjectState(
            project_path=str(self.project_path),
            current_phase=PhaseType.SPECIFICATION,
            indexing_complete=True,
            specification=None,
            design=None,
            tasks=None,
            implementation_progress={
                "task1": TaskStatus.COMPLETED,
                "task2": TaskStatus.IN_PROGRESS,
            },
            index_metadata=self.sample_index_metadata,
            session_data=self.sample_session_data,
            created_at=datetime(2024, 1, 1, 9, 0, 0),
            updated_at=datetime(2024, 1, 1, 11, 0, 0),
        )

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_init_creates_directories(self):
        """Test that StateManager creates necessary directories."""
        self.assertTrue(self.state_manager.dev_agent_dir.exists())
        self.assertTrue(self.state_manager.documents_dir.exists())

    def test_save_and_load_basic_project_state(self):
        """Test saving and loading basic project state without complex documents."""
        # Save the state
        success = self.state_manager.save_project_state(self.sample_project_state)
        self.assertTrue(success)
        self.assertTrue(self.state_manager.state_file.exists())

        # Load the state
        loaded_state = self.state_manager.load_project_state()
        self.assertIsNotNone(loaded_state)

        # Verify the loaded state matches (excluding updated_at which gets modified)
        self.assertEqual(
            loaded_state.project_path, self.sample_project_state.project_path
        )
        self.assertEqual(
            loaded_state.current_phase, self.sample_project_state.current_phase
        )
        self.assertEqual(
            loaded_state.indexing_complete, self.sample_project_state.indexing_complete
        )
        self.assertEqual(
            loaded_state.implementation_progress,
            self.sample_project_state.implementation_progress,
        )

        # Verify session data
        self.assertEqual(
            loaded_state.session_data.session_id, self.sample_session_data.session_id
        )
        self.assertEqual(
            loaded_state.session_data.user_approvals,
            self.sample_session_data.user_approvals,
        )

        # Verify index metadata
        self.assertEqual(
            loaded_state.index_metadata.total_files,
            self.sample_index_metadata.total_files,
        )
        self.assertEqual(
            loaded_state.index_metadata.languages_detected,
            self.sample_index_metadata.languages_detected,
        )

    def test_load_nonexistent_state(self):
        """Test loading state when no state file exists."""
        # Don't save anything, just try to load
        loaded_state = self.state_manager.load_project_state()
        self.assertIsNone(loaded_state)

    def test_update_phase_status(self):
        """Test updating phase status."""
        # First save initial state
        self.state_manager.save_project_state(self.sample_project_state)

        # Update phase
        success = self.state_manager.update_phase_status(
            PhaseType.DESIGN, "moving to design"
        )
        self.assertTrue(success)

        # Verify update
        loaded_state = self.state_manager.load_project_state()
        self.assertEqual(loaded_state.current_phase, PhaseType.DESIGN)

    def test_save_and_load_documents(self):
        """Test saving and loading markdown documents."""
        # Test specification document
        spec_content = "# Specification\n\nThis is a test specification."
        success = self.state_manager.save_document(
            spec_content, DocumentType.SPECIFICATION
        )
        self.assertTrue(success)

        loaded_spec = self.state_manager.load_document(DocumentType.SPECIFICATION)
        self.assertEqual(loaded_spec, spec_content)

        # Test design document
        design_content = "# Design\n\nThis is a test design."
        success = self.state_manager.save_document(design_content, DocumentType.DESIGN)
        self.assertTrue(success)

        loaded_design = self.state_manager.load_document(DocumentType.DESIGN)
        self.assertEqual(loaded_design, design_content)

        # Test tasks document
        tasks_content = "# Tasks\n\n- [ ] Task 1\n- [ ] Task 2"
        success = self.state_manager.save_document(tasks_content, DocumentType.TASKS)
        self.assertTrue(success)

        loaded_tasks = self.state_manager.load_document(DocumentType.TASKS)
        self.assertEqual(loaded_tasks, tasks_content)

    def test_load_nonexistent_document(self):
        """Test loading a document that doesn't exist."""
        loaded_doc = self.state_manager.load_document(DocumentType.SPECIFICATION)
        self.assertIsNone(loaded_doc)

    def test_track_task_progress(self):
        """Test tracking task progress."""
        # First save initial state
        self.state_manager.save_project_state(self.sample_project_state)

        # Track progress for a new task
        success = self.state_manager.track_task_progress("task3", TaskStatus.COMPLETED)
        self.assertTrue(success)

        # Verify update
        loaded_state = self.state_manager.load_project_state()
        self.assertEqual(
            loaded_state.implementation_progress["task3"], TaskStatus.COMPLETED
        )

        # Original tasks should still be there
        self.assertEqual(
            loaded_state.implementation_progress["task1"], TaskStatus.COMPLETED
        )
        self.assertEqual(
            loaded_state.implementation_progress["task2"], TaskStatus.IN_PROGRESS
        )

    def test_create_initial_state(self):
        """Test creating initial project state."""
        session_id = "new-session-456"
        initial_state = self.state_manager.create_initial_state(
            str(self.project_path), session_id
        )

        self.assertEqual(initial_state.project_path, str(self.project_path))
        self.assertEqual(initial_state.current_phase, PhaseType.INDEXING)
        self.assertFalse(initial_state.indexing_complete)
        self.assertIsNone(initial_state.specification)
        self.assertIsNone(initial_state.design)
        self.assertIsNone(initial_state.tasks)
        self.assertEqual(initial_state.session_data.session_id, session_id)
        self.assertEqual(len(initial_state.implementation_progress), 0)

    def test_get_project_info(self):
        """Test getting project information."""
        # Test with no existing state
        info = self.state_manager.get_project_info()
        self.assertIsNone(info)

        # Save state and test again
        self.state_manager.save_project_state(self.sample_project_state)
        info = self.state_manager.get_project_info()

        self.assertIsNotNone(info)
        self.assertEqual(info["project_path"], str(self.project_path))
        self.assertEqual(info["current_phase"], "specification")
        self.assertTrue(info["indexing_complete"])
        self.assertFalse(info["has_specification"])
        self.assertFalse(info["has_design"])
        self.assertFalse(info["has_tasks"])
        self.assertEqual(info["total_tasks"], 2)

    def test_error_handling_invalid_json(self):
        """Test error handling when state file contains invalid JSON."""
        # Create invalid JSON file
        with open(self.state_manager.state_file, "w") as f:
            f.write("invalid json content")

        # Should return None and not crash
        loaded_state = self.state_manager.load_project_state()
        self.assertIsNone(loaded_state)

    def test_datetime_serialization(self):
        """Test that datetime objects are properly serialized and deserialized."""
        # Save state with datetime fields
        self.state_manager.save_project_state(self.sample_project_state)

        # Load and verify datetime fields are preserved
        loaded_state = self.state_manager.load_project_state()
        self.assertIsInstance(loaded_state.created_at, datetime)
        self.assertIsInstance(loaded_state.updated_at, datetime)
        self.assertIsInstance(loaded_state.session_data.started_at, datetime)
        self.assertIsInstance(loaded_state.index_metadata.last_indexed, datetime)

        # Verify the actual datetime values (excluding updated_at which gets modified)
        self.assertEqual(loaded_state.created_at, self.sample_project_state.created_at)
        self.assertEqual(
            loaded_state.session_data.started_at, self.sample_session_data.started_at
        )

    def test_json_file_structure(self):
        """Test that the saved JSON file has the expected structure."""
        # Save state
        self.state_manager.save_project_state(self.sample_project_state)

        # Read and parse the JSON file directly
        with open(self.state_manager.state_file) as f:
            json_data = json.load(f)

        # Verify top-level structure
        expected_keys = [
            "project_path",
            "current_phase",
            "indexing_complete",
            "specification",
            "design",
            "tasks",
            "implementation_progress",
            "index_metadata",
            "session_data",
            "created_at",
            "updated_at",
        ]

        for key in expected_keys:
            self.assertIn(key, json_data)

        # Verify enum serialization
        self.assertEqual(json_data["current_phase"], "specification")

        # Verify nested structure
        self.assertIn("session_id", json_data["session_data"])
        self.assertIn("total_files", json_data["index_metadata"])


if __name__ == "__main__":
    unittest.main()
