"""Unit tests for StateManager class."""

import tempfile
import unittest
from datetime import datetime
import pytest
from pathlib import Path
from unittest.mock import patch

from dev_agent.errors.exceptions import StateLoadingError
from dev_agent.models.documents import (
    ArchitectureDescription,
    CodeAnalysisRef,
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
    DocumentType,
    PhaseType,
    Priority,
    SpecificationSource,
    TaskStatus,
)
from dev_agent.models.project_state import IndexMetadata, ProjectState, SessionData
from dev_agent.state.state_manager import StateManager


class TestStateManager(unittest.TestCase):
    """Test cases for StateManager functionality."""

    def setUp(self):
        """Set up test environment with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "test_project"
        self.project_path.mkdir()
        self.state_manager = StateManager(str(self.project_path))

        # Create sample data for testing
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

    @pytest.mark.asyncio
    async def test_save_and_load_project_state(self):
        """Test saving and loading project state."""
        # Save the state
        success = await self.state_manager.save_project_state(self.sample_project_state)
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

    @pytest.mark.asyncio
    @patch("dev_agent.state.state_manager.StateManager._get_spec_folder_name", new_callable=unittest.mock.AsyncMock)
    async def test_save_and_load_specification_document(self, mock_get_spec_folder_name):
        """Test saving and loading specification documents."""
        mock_get_spec_folder_name.return_value = "specification-test"
        # Create a sample specification
        requirement = Requirement(
            id="REQ-1",
            user_story="As a user, I want to save state",
            acceptance_criteria=["System shall save state", "System shall load state"],
            priority=Priority.HIGH,
            source_analysis=CodeAnalysisRef(
                file_paths=["test.py"], functions=["save_state"], confidence_score=0.9
            ),
        )

        spec = SpecificationDocument(
            introduction="Test specification",
            key_features=["State management", "Persistence"],
            functional_requirements=[requirement],
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=True,
            approval_timestamp=datetime(2024, 1, 1, 12, 0, 0),
        )

        # Add spec to state and save
        state_with_spec = self.sample_project_state
        state_with_spec.specification = spec

        success = await self.state_manager.save_project_state(state_with_spec)
        self.assertTrue(success)

        # Load and verify
        loaded_state = self.state_manager.load_project_state()
        self.assertIsNotNone(loaded_state.specification)
        self.assertEqual(loaded_state.specification.introduction, spec.introduction)
        self.assertEqual(loaded_state.specification.key_features, spec.key_features)
        self.assertEqual(len(loaded_state.specification.functional_requirements), 1)

        req = loaded_state.specification.functional_requirements[0]
        self.assertEqual(req.id, "REQ-1")
        self.assertEqual(req.priority, Priority.HIGH)
        self.assertIsNotNone(req.source_analysis)
        self.assertEqual(req.source_analysis.confidence_score, 0.9)

    @pytest.mark.asyncio
    async def test_save_and_load_design(self):
        """Test saving and loading design documents."""
        # Create a sample design document
        architecture = ArchitectureDescription(
            overview="Test architecture",
            patterns=["MVC", "Repository"],
            components=["StateManager", "CLI"],
        )

        component = ComponentSpec(
            name="StateManager",
            description="Manages project state",
            interfaces=["IStateManager"],
            dependencies=["FileSystem"],
        )

        data_model = DataModel(
            name="ProjectState",
            fields={"id": "string", "phase": "PhaseType"},
            relationships=["has_many_tasks"],
        )

        interface = InterfaceSpec(
            name="IStateManager",
            methods=["save_state", "load_state"],
            description="State management interface",
        )

        error_handling = ErrorHandlingStrategy(
            error_categories=["IO", "Validation"],
            recovery_mechanisms=["Retry", "Fallback"],
            logging_strategy="Structured logging",
        )

        testing_strategy = TestingStrategy(
            unit_testing="pytest",
            integration_testing="pytest with fixtures",
            performance_testing="pytest-benchmark",
            test_coverage_target=90.0,
        )

        design = DesignDocument(
            overview="Test design overview",
            architecture=architecture,
            components=[component],
            data_models=[data_model],
            interfaces=[interface],
            error_handling=error_handling,
            testing_strategy=testing_strategy,
            version="1.0",
            approved=True,
        )

        # Add design to state and save
        state_with_design = self.sample_project_state
        state_with_design.design = design

        success = await self.state_manager.save_project_state(state_with_design)
        self.assertTrue(success)

        # Load and verify
        loaded_state = self.state_manager.load_project_state()
        self.assertIsNotNone(loaded_state.design)
        self.assertEqual(loaded_state.design.overview, design.overview)
        self.assertEqual(
            loaded_state.design.architecture.overview, architecture.overview
        )
        self.assertEqual(len(loaded_state.design.components), 1)
        self.assertEqual(loaded_state.design.components[0].name, "StateManager")

    @pytest.mark.asyncio
    async def test_save_and_load_task_list(self):
        """Test saving and loading task lists."""
        # Create a sample task list
        task = Task(
            id="TASK-1",
            title="Implement StateManager",
            description="Create state management functionality",
            requirements_refs=["REQ-1"],
            subtasks=["TASK-1.1", "TASK-1.2"],
            status=TaskStatus.IN_PROGRESS,
            target_language="python",
            context_requirements=["existing_patterns"],
            implementation_notes="Use JSON for persistence",
            generated_files=["state_manager.py"],
        )

        task_list = TaskList(
            tasks=[task],
            dependencies={"TASK-1": ["TASK-0"]},
            estimated_effort={"TASK-1": 8},
            version="1.0",
            approved=True,
        )

        # Add tasks to state and save
        state_with_tasks = self.sample_project_state
        state_with_tasks.tasks = task_list

        success = await self.state_manager.save_project_state(state_with_tasks)
        self.assertTrue(success)

        # Load and verify
        loaded_state = self.state_manager.load_project_state()
        self.assertIsNotNone(loaded_state.tasks)
        self.assertEqual(len(loaded_state.tasks.tasks), 1)

        loaded_task = loaded_state.tasks.tasks[0]
        self.assertEqual(loaded_task.id, "TASK-1")
        self.assertEqual(loaded_task.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(loaded_task.generated_files, ["state_manager.py"])

    @pytest.mark.asyncio
    async def test_update_phase_status(self):
        """Test updating phase status."""
        # First save initial state
        await self.state_manager.save_project_state(self.sample_project_state)

        # Update phase
        success = await self.state_manager.update_phase_status(
            PhaseType.DESIGN, "moving to design"
        )
        self.assertTrue(success)

        # Verify update
        loaded_state = self.state_manager.load_project_state()
        self.assertEqual(loaded_state.current_phase, PhaseType.DESIGN)

    @pytest.mark.asyncio
    @patch("dev_agent.state.state_manager.StateManager._get_spec_folder_name", new_callable=unittest.mock.AsyncMock)
    async def test_save_and_load_documents(self, mock_get_spec_folder_name):
        """Test saving and loading markdown documents."""
        mock_get_spec_folder_name.return_value = "specification-test"
        # Test specification document
        spec_content = "# Specification\n\nThis is a test specification."
        success = await self.state_manager.save_document(
            spec_content, DocumentType.SPECIFICATION
        )
        self.assertTrue(success)

        loaded_spec = self.state_manager.load_document(DocumentType.SPECIFICATION)
        self.assertEqual(loaded_spec, spec_content)

        # Test design document
        design_content = "# Design\n\nThis is a test design."
        success = await self.state_manager.save_document(design_content, DocumentType.DESIGN)
        self.assertTrue(success)

        loaded_design = self.state_manager.load_document(DocumentType.DESIGN)
        self.assertEqual(loaded_design, design_content)

        # Test tasks document
        tasks_content = "# Tasks\n\n- [ ] Task 1\n- [ ] Task 2"
        success = await self.state_manager.save_document(tasks_content, DocumentType.TASKS)
        self.assertTrue(success)

        loaded_tasks = self.state_manager.load_document(DocumentType.TASKS)
        self.assertEqual(loaded_tasks, tasks_content)

    def test_load_nonexistent_document(self):
        """Test loading a document that doesn't exist."""
        loaded_doc = self.state_manager.load_document(DocumentType.SPECIFICATION)
        self.assertIsNone(loaded_doc)

    @pytest.mark.asyncio
    async def test_track_task_progress(self):
        """Test tracking task progress."""
        # First save initial state
        await self.state_manager.save_project_state(self.sample_project_state)

        # Track progress for a new task
        success = await self.state_manager.track_task_progress("task3", TaskStatus.COMPLETED)
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

    async def test_create_initial_state(self):
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

    @pytest.mark.asyncio
    async def test_get_project_info(self):
        """Test getting project information."""
        # Test with no existing state
        info = self.state_manager.get_project_info()
        self.assertIsNone(info)

        # Save state and test again
        await self.state_manager.save_project_state(self.sample_project_state)
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

        # Should raise StateLoadingError
        with self.assertRaises(StateLoadingError):
            self.state_manager.load_project_state()

    @pytest.mark.asyncio
    async def test_error_handling_permission_denied(self):
        """Test error handling when file operations fail."""
        # Make the directory read-only to simulate permission issues
        with patch(
            "tempfile.mkstemp", side_effect=PermissionError("Permission denied")
        ) as mock_mkstemp:
            with self.assertRaises(Exception) as context:
                await self.state_manager.save_project_state(self.sample_project_state)
            self.assertIn("Permission denied", str(context.exception))

    @pytest.mark.asyncio
    async def test_datetime_serialization(self):
        """Test that datetime objects are properly serialized and deserialized."""
        # Save state with datetime fields
        await self.state_manager.save_project_state(self.sample_project_state)

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


if __name__ == "__main__":
    unittest.main()
