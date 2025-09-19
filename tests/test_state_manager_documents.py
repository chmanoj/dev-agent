"""Tests for StateManager with complex document structures."""

import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

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
    PhaseType,
    Priority,
    SpecificationSource,
    TaskStatus,
)
from dev_agent.models.project_state import IndexMetadata, ProjectState, SessionData
from dev_agent.state.state_manager import StateManager


class TestStateManagerDocuments(unittest.TestCase):
    """Test StateManager with complex document structures."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "test_project"
        self.project_path.mkdir()
        self.state_manager = StateManager(str(self.project_path))

        # Create sample session data
        self.sample_session_data = SessionData(
            session_id="test-session-123",
            started_at=datetime(2024, 1, 1, 10, 0, 0),
            last_activity=datetime(2024, 1, 1, 11, 0, 0),
            user_approvals={"specification": True},
            pending_approvals=["design"],
        )

        # Create sample index metadata
        self.sample_index_metadata = IndexMetadata(
            total_files=100,
            total_lines=5000,
            languages_detected=["python", "javascript"],
            index_size_mb=2.5,
            last_indexed=datetime(2024, 1, 1, 9, 0, 0),
            index_version="1.0.0",
        )

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_specification_document_persistence(self):
        """Test saving and loading specification documents with all fields."""
        # Create a comprehensive specification
        code_analysis = CodeAnalysisRef(
            file_paths=["src/main.py", "src/utils.py"],
            functions=["main", "process_data", "validate_input"],
            confidence_score=0.85,
        )

        requirement1 = Requirement(
            id="REQ-001",
            user_story="As a developer, I want to save project state so that I can resume work later",
            acceptance_criteria=[
                "WHEN I save state THEN it SHALL persist to disk",
                "WHEN I load state THEN it SHALL restore all data",
                "IF state file is corrupted THEN system SHALL handle gracefully",
            ],
            priority=Priority.HIGH,
            source_analysis=code_analysis,
        )

        requirement2 = Requirement(
            id="REQ-002",
            user_story="As a user, I want to track task progress so that I know what's completed",
            acceptance_criteria=[
                "WHEN task status changes THEN it SHALL be persisted",
                "WHEN I query progress THEN it SHALL return current status",
            ],
            priority=Priority.MEDIUM,
            source_analysis=None,
        )

        spec = SpecificationDocument(
            introduction="This specification defines the state management system for dev-agent.",
            key_features=[
                "JSON-based persistence",
                "Document storage",
                "Task progress tracking",
                "Session management",
            ],
            functional_requirements=[requirement1, requirement2],
            source=SpecificationSource.USER_INPUT,
            version="1.0.0",
            approved=True,
            approval_timestamp=datetime(2024, 1, 1, 12, 0, 0),
        )

        # Create project state with specification
        project_state = ProjectState(
            project_path=str(self.project_path),
            current_phase=PhaseType.SPECIFICATION,
            indexing_complete=True,
            specification=spec,
            design=None,
            tasks=None,
            implementation_progress={},
            index_metadata=self.sample_index_metadata,
            session_data=self.sample_session_data,
            created_at=datetime(2024, 1, 1, 9, 0, 0),
            updated_at=datetime(2024, 1, 1, 11, 0, 0),
        )

        # Save and load
        success = self.state_manager.save_project_state(project_state)
        self.assertTrue(success)

        loaded_state = self.state_manager.load_project_state()
        self.assertIsNotNone(loaded_state)
        self.assertIsNotNone(loaded_state.specification)

        # Verify specification details
        loaded_spec = loaded_state.specification
        self.assertEqual(loaded_spec.introduction, spec.introduction)
        self.assertEqual(loaded_spec.key_features, spec.key_features)
        self.assertEqual(loaded_spec.source, SpecificationSource.USER_INPUT)
        self.assertTrue(loaded_spec.approved)
        self.assertEqual(len(loaded_spec.functional_requirements), 2)

        # Verify first requirement
        req1 = loaded_spec.functional_requirements[0]
        self.assertEqual(req1.id, "REQ-001")
        self.assertEqual(req1.priority, Priority.HIGH)
        self.assertIsNotNone(req1.source_analysis)
        self.assertEqual(req1.source_analysis.confidence_score, 0.85)
        self.assertEqual(len(req1.source_analysis.file_paths), 2)

        # Verify second requirement
        req2 = loaded_spec.functional_requirements[1]
        self.assertEqual(req2.id, "REQ-002")
        self.assertEqual(req2.priority, Priority.MEDIUM)
        self.assertIsNone(req2.source_analysis)

    def test_design_document_persistence(self):
        """Test saving and loading design documents with all components."""
        # Create comprehensive design document
        architecture = ArchitectureDescription(
            overview="Layered architecture with clear separation of concerns",
            patterns=["Repository Pattern", "Factory Pattern", "Observer Pattern"],
            components=[
                "StateManager",
                "DocumentStore",
                "TaskTracker",
                "SessionManager",
            ],
        )

        component1 = ComponentSpec(
            name="StateManager",
            description="Core component for managing project state persistence",
            interfaces=["IStateManager", "IDocumentStore"],
            dependencies=["FileSystem", "JSONSerializer"],
        )

        component2 = ComponentSpec(
            name="TaskTracker",
            description="Tracks implementation task progress and status",
            interfaces=["ITaskTracker"],
            dependencies=["StateManager"],
        )

        data_model1 = DataModel(
            name="ProjectState",
            fields={
                "project_path": "str",
                "current_phase": "PhaseType",
                "indexing_complete": "bool",
                "created_at": "datetime",
            },
            relationships=["has_one_specification", "has_one_design", "has_many_tasks"],
        )

        data_model2 = DataModel(
            name="Task",
            fields={
                "id": "str",
                "title": "str",
                "status": "TaskStatus",
                "requirements_refs": "List[str]",
            },
            relationships=["belongs_to_project_state"],
        )

        interface1 = InterfaceSpec(
            name="IStateManager",
            methods=[
                "save_project_state(state: ProjectState) -> bool",
                "load_project_state() -> Optional[ProjectState]",
                "update_phase_status(phase: PhaseType, status: str) -> bool",
            ],
            description="Interface for project state management operations",
        )

        interface2 = InterfaceSpec(
            name="IDocumentStore",
            methods=[
                "save_document(content: str, doc_type: DocumentType) -> bool",
                "load_document(doc_type: DocumentType) -> Optional[str]",
            ],
            description="Interface for document storage operations",
        )

        error_handling = ErrorHandlingStrategy(
            error_categories=[
                "IOError",
                "JSONDecodeError",
                "ValidationError",
                "PermissionError",
            ],
            recovery_mechanisms=[
                "Graceful degradation with partial state",
                "Automatic backup and restore",
                "User notification with recovery options",
                "Fallback to read-only mode",
            ],
            logging_strategy="Structured logging with error categorization and context",
        )

        testing_strategy = TestingStrategy(
            unit_testing="pytest with comprehensive test coverage for all components",
            integration_testing="End-to-end testing with temporary file systems",
            performance_testing="Load testing with large state files and many documents",
            test_coverage_target=95.0,
        )

        design = DesignDocument(
            overview="The state management system provides persistent storage for project state, documents, and task progress using JSON serialization and file-based storage.",
            architecture=architecture,
            components=[component1, component2],
            data_models=[data_model1, data_model2],
            interfaces=[interface1, interface2],
            error_handling=error_handling,
            testing_strategy=testing_strategy,
            version="1.0.0",
            approved=True,
        )

        # Create project state with design
        project_state = ProjectState(
            project_path=str(self.project_path),
            current_phase=PhaseType.DESIGN,
            indexing_complete=True,
            specification=None,
            design=design,
            tasks=None,
            implementation_progress={},
            index_metadata=self.sample_index_metadata,
            session_data=self.sample_session_data,
            created_at=datetime(2024, 1, 1, 9, 0, 0),
            updated_at=datetime(2024, 1, 1, 11, 0, 0),
        )

        # Save and load
        success = self.state_manager.save_project_state(project_state)
        self.assertTrue(success)

        loaded_state = self.state_manager.load_project_state()
        self.assertIsNotNone(loaded_state)
        self.assertIsNotNone(loaded_state.design)

        # Verify design details
        loaded_design = loaded_state.design
        self.assertEqual(loaded_design.overview, design.overview)
        self.assertEqual(loaded_design.version, "1.0.0")
        self.assertTrue(loaded_design.approved)

        # Verify architecture
        arch = loaded_design.architecture
        self.assertEqual(arch.overview, architecture.overview)
        self.assertEqual(len(arch.patterns), 3)
        self.assertEqual(len(arch.components), 4)

        # Verify components
        self.assertEqual(len(loaded_design.components), 2)
        comp1 = loaded_design.components[0]
        self.assertEqual(comp1.name, "StateManager")
        self.assertEqual(len(comp1.interfaces), 2)
        self.assertEqual(len(comp1.dependencies), 2)

        # Verify data models
        self.assertEqual(len(loaded_design.data_models), 2)
        dm1 = loaded_design.data_models[0]
        self.assertEqual(dm1.name, "ProjectState")
        self.assertEqual(len(dm1.fields), 4)
        self.assertEqual(len(dm1.relationships), 3)

        # Verify interfaces
        self.assertEqual(len(loaded_design.interfaces), 2)
        int1 = loaded_design.interfaces[0]
        self.assertEqual(int1.name, "IStateManager")
        self.assertEqual(len(int1.methods), 3)

        # Verify error handling
        eh = loaded_design.error_handling
        self.assertEqual(len(eh.error_categories), 4)
        self.assertEqual(len(eh.recovery_mechanisms), 4)

        # Verify testing strategy
        ts = loaded_design.testing_strategy
        self.assertEqual(ts.test_coverage_target, 95.0)

    def test_task_list_persistence(self):
        """Test saving and loading task lists with all task details."""
        # Create comprehensive task list
        task1 = Task(
            id="TASK-001",
            title="Implement StateManager class",
            description="Create the core StateManager class with JSON persistence",
            requirements_refs=["REQ-001", "REQ-002"],
            subtasks=["TASK-001.1", "TASK-001.2", "TASK-001.3"],
            status=TaskStatus.COMPLETED,
            target_language="python",
            context_requirements=["existing_file_patterns", "json_serialization"],
            implementation_notes="Use dataclasses for type safety and pathlib for file operations",
            generated_files=[
                "dev_agent/state/state_manager.py",
                "tests/test_state_manager.py",
            ],
        )

        task2 = Task(
            id="TASK-002",
            title="Add document storage methods",
            description="Implement methods for storing and retrieving markdown documents",
            requirements_refs=["REQ-003"],
            subtasks=["TASK-002.1"],
            status=TaskStatus.IN_PROGRESS,
            target_language="python",
            context_requirements=["markdown_handling"],
            implementation_notes="Store documents in .dev_agent/documents/ directory",
            generated_files=[],
        )

        task3 = Task(
            id="TASK-003",
            title="Write comprehensive unit tests",
            description="Create unit tests for all StateManager functionality",
            requirements_refs=["REQ-001", "REQ-002", "REQ-003"],
            subtasks=[],
            status=TaskStatus.NOT_STARTED,
            target_language="python",
            context_requirements=["testing_patterns", "mock_objects"],
            implementation_notes="Use pytest and temporary directories for testing",
            generated_files=[],
        )

        task_list = TaskList(
            tasks=[task1, task2, task3],
            dependencies={
                "TASK-002": ["TASK-001"],
                "TASK-003": ["TASK-001", "TASK-002"],
            },
            estimated_effort={"TASK-001": 8, "TASK-002": 4, "TASK-003": 6},
            version="1.0.0",
            approved=True,
        )

        # Create project state with tasks
        project_state = ProjectState(
            project_path=str(self.project_path),
            current_phase=PhaseType.IMPLEMENTATION,
            indexing_complete=True,
            specification=None,
            design=None,
            tasks=task_list,
            implementation_progress={
                "TASK-001": TaskStatus.COMPLETED,
                "TASK-002": TaskStatus.IN_PROGRESS,
                "TASK-003": TaskStatus.NOT_STARTED,
            },
            index_metadata=self.sample_index_metadata,
            session_data=self.sample_session_data,
            created_at=datetime(2024, 1, 1, 9, 0, 0),
            updated_at=datetime(2024, 1, 1, 11, 0, 0),
        )

        # Save and load
        success = self.state_manager.save_project_state(project_state)
        self.assertTrue(success)

        loaded_state = self.state_manager.load_project_state()
        self.assertIsNotNone(loaded_state)
        self.assertIsNotNone(loaded_state.tasks)

        # Verify task list details
        loaded_tasks = loaded_state.tasks
        self.assertEqual(loaded_tasks.version, "1.0.0")
        self.assertTrue(loaded_tasks.approved)
        self.assertEqual(len(loaded_tasks.tasks), 3)

        # Verify dependencies and effort
        self.assertEqual(len(loaded_tasks.dependencies), 2)
        self.assertEqual(loaded_tasks.dependencies["TASK-002"], ["TASK-001"])
        self.assertEqual(loaded_tasks.estimated_effort["TASK-001"], 8)

        # Verify first task
        task1_loaded = loaded_tasks.tasks[0]
        self.assertEqual(task1_loaded.id, "TASK-001")
        self.assertEqual(task1_loaded.status, TaskStatus.COMPLETED)
        self.assertEqual(len(task1_loaded.requirements_refs), 2)
        self.assertEqual(len(task1_loaded.subtasks), 3)
        self.assertEqual(len(task1_loaded.context_requirements), 2)
        self.assertEqual(len(task1_loaded.generated_files), 2)
        self.assertIsNotNone(task1_loaded.implementation_notes)

        # Verify second task
        task2_loaded = loaded_tasks.tasks[1]
        self.assertEqual(task2_loaded.id, "TASK-002")
        self.assertEqual(task2_loaded.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(len(task2_loaded.generated_files), 0)

        # Verify third task
        task3_loaded = loaded_tasks.tasks[2]
        self.assertEqual(task3_loaded.id, "TASK-003")
        self.assertEqual(task3_loaded.status, TaskStatus.NOT_STARTED)
        self.assertEqual(len(task3_loaded.subtasks), 0)

        # Verify implementation progress
        self.assertEqual(len(loaded_state.implementation_progress), 3)
        self.assertEqual(
            loaded_state.implementation_progress["TASK-001"], TaskStatus.COMPLETED
        )
        self.assertEqual(
            loaded_state.implementation_progress["TASK-002"], TaskStatus.IN_PROGRESS
        )
        self.assertEqual(
            loaded_state.implementation_progress["TASK-003"], TaskStatus.NOT_STARTED
        )


if __name__ == "__main__":
    unittest.main()
