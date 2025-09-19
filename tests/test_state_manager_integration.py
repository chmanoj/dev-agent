"""Integration test for StateManager demonstrating end-to-end functionality."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dev_agent.models.enums import DocumentType, PhaseType, TaskStatus
from dev_agent.state.state_manager import StateManager


class TestStateManagerIntegration(unittest.TestCase):
    """Integration test demonstrating complete StateManager workflow."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "integration_test_project"
        self.project_path.mkdir()
        self.state_manager = StateManager(str(self.project_path))

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_complete_workflow(self):
        """Test a complete workflow from project initialization to task completion."""

        # Step 1: Initialize new project
        session_id = "integration-test-session"
        initial_state = self.state_manager.create_initial_state(
            str(self.project_path), session_id
        )

        # Verify initial state
        self.assertEqual(initial_state.current_phase, PhaseType.INDEXING)
        self.assertFalse(initial_state.indexing_complete)
        self.assertIsNone(initial_state.specification)

        # Step 2: Save initial state
        success = self.state_manager.save_project_state(initial_state)
        self.assertTrue(success)

        # Step 3: Simulate indexing completion
        success = self.state_manager.update_phase_status(
            PhaseType.SPECIFICATION, "indexing completed"
        )
        self.assertTrue(success)

        # Verify phase update
        loaded_state = self.state_manager.load_project_state()
        self.assertEqual(loaded_state.current_phase, PhaseType.SPECIFICATION)

        # Step 4: Save specification document
        spec_content = """# Project Specification
        
## Introduction
This is a test project for demonstrating state management.

## Requirements
- REQ-1: System shall save state
- REQ-2: System shall load state
- REQ-3: System shall track progress
"""
        success = self.state_manager.save_document(
            spec_content, DocumentType.SPECIFICATION
        )
        self.assertTrue(success)

        # Step 5: Move to design phase
        success = self.state_manager.update_phase_status(
            PhaseType.DESIGN, "specification approved"
        )
        self.assertTrue(success)

        # Step 6: Save design document
        design_content = """# Project Design
        
## Architecture
- StateManager: Core component for persistence
- DocumentStore: Handles markdown documents
- TaskTracker: Manages task progress

## Implementation Plan
The system will use JSON for state persistence and file-based storage for documents.
"""
        success = self.state_manager.save_document(design_content, DocumentType.DESIGN)
        self.assertTrue(success)

        # Step 7: Move to implementation phase
        success = self.state_manager.update_phase_status(
            PhaseType.IMPLEMENTATION, "design approved"
        )
        self.assertTrue(success)

        # Step 8: Save tasks document
        tasks_content = """# Implementation Tasks
        
- [ ] 1. Implement StateManager
- [ ] 2. Add document storage
- [ ] 3. Create unit tests
- [ ] 4. Add error handling
"""
        success = self.state_manager.save_document(tasks_content, DocumentType.TASKS)
        self.assertTrue(success)

        # Step 9: Track task progress
        success = self.state_manager.track_task_progress(
            "task-1", TaskStatus.IN_PROGRESS
        )
        self.assertTrue(success)

        success = self.state_manager.track_task_progress("task-2", TaskStatus.COMPLETED)
        self.assertTrue(success)

        success = self.state_manager.track_task_progress(
            "task-3", TaskStatus.NOT_STARTED
        )
        self.assertTrue(success)

        # Step 10: Verify final state
        final_state = self.state_manager.load_project_state()

        # Verify phase progression
        self.assertEqual(final_state.current_phase, PhaseType.IMPLEMENTATION)

        # Verify task progress
        self.assertEqual(
            final_state.implementation_progress["task-1"], TaskStatus.IN_PROGRESS
        )
        self.assertEqual(
            final_state.implementation_progress["task-2"], TaskStatus.COMPLETED
        )
        self.assertEqual(
            final_state.implementation_progress["task-3"], TaskStatus.NOT_STARTED
        )

        # Step 11: Verify all documents are saved and loadable
        loaded_spec = self.state_manager.load_document(DocumentType.SPECIFICATION)
        self.assertIsNotNone(loaded_spec)
        self.assertIn("Project Specification", loaded_spec)

        loaded_design = self.state_manager.load_document(DocumentType.DESIGN)
        self.assertIsNotNone(loaded_design)
        self.assertIn("Project Design", loaded_design)

        loaded_tasks = self.state_manager.load_document(DocumentType.TASKS)
        self.assertIsNotNone(loaded_tasks)
        self.assertIn("Implementation Tasks", loaded_tasks)

        # Step 12: Verify project info
        project_info = self.state_manager.get_project_info()
        self.assertIsNotNone(project_info)
        self.assertEqual(project_info["current_phase"], "implementation")
        self.assertEqual(project_info["total_tasks"], 3)

        # Step 13: Verify file structure was created correctly
        self.assertTrue(self.state_manager.dev_agent_dir.exists())
        self.assertTrue(self.state_manager.documents_dir.exists())
        self.assertTrue(self.state_manager.state_file.exists())

        spec_file = self.state_manager.documents_dir / "SPECIFICATION.md"
        design_file = self.state_manager.documents_dir / "DESIGN.md"
        tasks_file = self.state_manager.documents_dir / "TASKS.md"

        self.assertTrue(spec_file.exists())
        self.assertTrue(design_file.exists())
        self.assertTrue(tasks_file.exists())

        print("✅ Integration test completed successfully!")
        print(f"📁 Project directory: {self.project_path}")
        print(f"💾 State file: {self.state_manager.state_file}")
        print(f"📄 Documents directory: {self.state_manager.documents_dir}")
        print(f"🎯 Final phase: {final_state.current_phase.value}")
        print(f"📊 Tasks tracked: {len(final_state.implementation_progress)}")


if __name__ == "__main__":
    unittest.main()
