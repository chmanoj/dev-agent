"""End-to-end tests for workflow orchestration system."""

import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from dev_agent.models.context import ProjectContext
from dev_agent.models.documents import (
    SpecificationDocument,
)
from dev_agent.models.enums import PhaseStatus, PhaseType
from dev_agent.models.project_state import ProjectState, SessionData
from dev_agent.models.results import (
    IndexingResult,
)
from dev_agent.state.state_manager import StateManager
from dev_agent.workflow.phase_manager import PhaseManager
from dev_agent.workflow.workflow_manager import WorkflowException, WorkflowManager


class TestWorkflowManager:
    """Test cases for WorkflowManager."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_cli_interface(self):
        """Create a mock CLI interface."""
        cli = Mock()
        cli.display_message = Mock()
        cli.display_progress = Mock()
        cli.request_approval = Mock(return_value=True)
        cli.get_user_input = Mock(return_value="test input")
        return cli

    @pytest.fixture
    def workflow_manager(self, mock_cli_interface):
        """Create a WorkflowManager instance."""
        return WorkflowManager(mock_cli_interface)

    def test_start_new_project(self, workflow_manager, temp_project_dir, mock_cli_interface):
        """Test starting a new project."""
        # Execute
        project_state = workflow_manager.start_new_project(temp_project_dir)

        # Verify
        assert project_state is not None
        assert project_state.project_path == temp_project_dir
        assert project_state.current_phase == PhaseType.INDEXING
        assert not project_state.indexing_complete
        assert project_state.specification is None
        assert project_state.design is None
        assert project_state.tasks is None

        # Verify CLI messages
        mock_cli_interface.display_message.assert_called()

        # Verify state manager was initialized
        assert workflow_manager.state_manager is not None
        assert workflow_manager.phase_manager is not None

        # Verify state file was created
        state_file = Path(temp_project_dir) / ".dev_agent" / "state.json"
        assert state_file.exists()

    def test_resume_project(self, workflow_manager, temp_project_dir, mock_cli_interface):
        """Test resuming an existing project."""
        # Setup - create initial project
        initial_state = workflow_manager.start_new_project(temp_project_dir)

        # Create a new workflow manager to simulate resuming
        new_workflow_manager = WorkflowManager(mock_cli_interface)

        # Execute
        resumed_state = new_workflow_manager.resume_project(temp_project_dir)

        # Verify
        assert resumed_state is not None
        assert resumed_state.project_path == temp_project_dir
        assert resumed_state.current_phase == PhaseType.INDEXING
        assert resumed_state.session_data.session_id == initial_state.session_data.session_id

        # Verify CLI messages
        mock_cli_interface.display_message.assert_called()

    def test_resume_nonexistent_project(self, workflow_manager, temp_project_dir, mock_cli_interface):
        """Test resuming a project that doesn't exist."""
        # Execute and verify exception
        with pytest.raises(WorkflowException):
            workflow_manager.resume_project(temp_project_dir)

    def test_get_current_phase(self, workflow_manager, temp_project_dir):
        """Test getting current phase."""
        # Before project initialization
        assert workflow_manager.get_current_phase() == PhaseType.INDEXING

        # After project initialization
        workflow_manager.start_new_project(temp_project_dir)
        assert workflow_manager.get_current_phase() == PhaseType.INDEXING

    def test_require_user_approval(self, workflow_manager, temp_project_dir, mock_cli_interface):
        """Test user approval workflow."""
        # Setup
        workflow_manager.start_new_project(temp_project_dir)
        mock_cli_interface.request_approval.return_value = True

        # Execute
        approved = workflow_manager.require_user_approval("test content", PhaseType.SPECIFICATION)

        # Verify
        assert approved is True
        mock_cli_interface.request_approval.assert_called_with("test content", "specification")

        # Verify approval was tracked
        state = workflow_manager.state_manager.load_project_state()
        assert state.session_data.user_approvals["specification"] is True

    def test_require_user_approval_denied(self, workflow_manager, temp_project_dir, mock_cli_interface):
        """Test user approval denial."""
        # Setup
        workflow_manager.start_new_project(temp_project_dir)
        mock_cli_interface.request_approval.return_value = False

        # Execute
        approved = workflow_manager.require_user_approval("test content", PhaseType.SPECIFICATION)

        # Verify
        assert approved is False

        # Verify denial was tracked
        state = workflow_manager.state_manager.load_project_state()
        assert state.session_data.user_approvals["specification"] is False

    def test_transition_to_phase_success(self, workflow_manager, temp_project_dir, mock_cli_interface):
        """Test successful phase transition."""
        # Setup
        workflow_manager.start_new_project(temp_project_dir)

        # Mock the _execute_phase method directly
        mock_result = Mock()
        mock_result.status = PhaseStatus.COMPLETED
        mock_result.message = "Phase completed successfully"

        with patch.object(workflow_manager, "_execute_phase", return_value=mock_result):
            # Execute
            success = workflow_manager.transition_to_phase(PhaseType.SPECIFICATION)

            # Verify
            assert success is True
            assert workflow_manager.current_project_state.current_phase == PhaseType.SPECIFICATION
            mock_cli_interface.display_message.assert_called()

    def test_transition_to_phase_failure(self, workflow_manager, temp_project_dir, mock_cli_interface):
        """Test failed phase transition."""
        # Setup
        workflow_manager.start_new_project(temp_project_dir)

        # Mock failed phase execution
        mock_result = Mock()
        mock_result.status = PhaseStatus.FAILED
        mock_result.message = "Phase failed"

        with patch.object(workflow_manager, "_execute_phase", return_value=mock_result):
            # Execute
            success = workflow_manager.transition_to_phase(PhaseType.SPECIFICATION)

            # Verify
            assert success is False
            assert workflow_manager.current_project_state.current_phase == PhaseType.INDEXING  # Should remain unchanged

    def test_invalid_phase_transition(self, workflow_manager, temp_project_dir, mock_cli_interface):
        """Test invalid phase transition."""
        # Setup
        workflow_manager.start_new_project(temp_project_dir)

        # Try to jump directly to implementation from indexing
        success = workflow_manager.transition_to_phase(PhaseType.IMPLEMENTATION)

        # Verify
        assert success is False
        mock_cli_interface.display_message.assert_called()

    def test_execute_complete_workflow(self, workflow_manager, temp_project_dir, mock_cli_interface):
        """Test executing the complete workflow."""
        # Setup
        workflow_manager.start_new_project(temp_project_dir)

        # Mock successful results for all phases
        successful_result = Mock()
        successful_result.status = PhaseStatus.COMPLETED
        successful_result.message = "Phase completed"

        with patch.object(workflow_manager, "_execute_phase", return_value=successful_result):
            # Execute
            success = workflow_manager.execute_complete_workflow()

            # Verify
            assert success is True
            assert workflow_manager.current_project_state.current_phase == PhaseType.IMPLEMENTATION


class TestPhaseManager:
    """Test cases for PhaseManager."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory with sample Python files."""
        temp_dir = tempfile.mkdtemp()

        # Create sample Python files
        (Path(temp_dir) / "main.py").write_text("""
def main():
    print("Hello, world!")

if __name__ == "__main__":
    main()
""")

        (Path(temp_dir) / "utils.py").write_text("""
class Calculator:
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b
""")

        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_cli_interface(self):
        """Create a mock CLI interface."""
        cli = Mock()
        cli.display_message = Mock()
        cli.display_progress = Mock()
        cli.request_approval = Mock(return_value=True)
        cli.get_user_input = Mock(return_value="test input")
        return cli

    @pytest.fixture
    def state_manager(self, temp_project_dir):
        """Create a StateManager instance."""
        return StateManager(temp_project_dir)

    @pytest.fixture
    def phase_manager(self, mock_cli_interface, state_manager):
        """Create a PhaseManager instance."""
        return PhaseManager(mock_cli_interface, state_manager)

    @pytest.fixture
    def project_context(self, temp_project_dir, state_manager):
        """Create a project context."""
        # Create initial project state
        session_data = SessionData(
            session_id="test-session",
            started_at=datetime.now(),
            last_activity=datetime.now(),
            user_approvals={},
            pending_approvals=[]
        )

        project_state = ProjectState(
            project_path=temp_project_dir,
            current_phase=PhaseType.INDEXING,
            indexing_complete=False,
            specification=None,
            design=None,
            tasks=None,
            implementation_progress={},
            index_metadata=None,
            session_data=session_data,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        return ProjectContext(
            project_state=project_state,
            ast_index=None,
            codebase_patterns=None,
            user_preferences={}
        )

    @patch("dev_agent.workflow.phase_manager.IndexingEngine")
    def test_execute_indexing_phase_success(self, mock_indexing_engine_class, phase_manager, temp_project_dir, mock_cli_interface):
        """Test successful indexing phase execution."""
        # Mock indexing engine
        mock_indexing_engine = Mock()
        mock_indexing_engine_class.return_value = mock_indexing_engine

        # Mock successful indexing
        mock_indexing_engine.is_index_stale.return_value = True
        mock_index_result = Mock()
        mock_index_result.success = True
        mock_index_result.metadata = {
            "total_files": 2,
            "total_lines": 20,
            "index_size_mb": 0.1,
            "languages_detected": ["python"],
            "indexing_time_seconds": 1.0
        }
        mock_index_result.errors = []
        mock_indexing_engine.build_index.return_value = mock_index_result

        # Execute
        result = phase_manager.execute_indexing_phase(temp_project_dir)

        # Verify
        assert result.status == PhaseStatus.COMPLETED
        assert result.files_indexed == 2
        assert result.total_lines == 20
        assert "python" in result.languages_detected

        # Verify CLI messages
        mock_cli_interface.display_message.assert_called()

    @patch("dev_agent.workflow.phase_manager.IndexingEngine")
    def test_execute_indexing_phase_existing_index(self, mock_indexing_engine_class, phase_manager, temp_project_dir, mock_cli_interface):
        """Test indexing phase with existing up-to-date index."""
        # Mock indexing engine
        mock_indexing_engine = Mock()
        mock_indexing_engine_class.return_value = mock_indexing_engine

        # Mock existing index
        mock_indexing_engine.is_index_stale.return_value = False
        mock_metadata = Mock()
        mock_metadata.total_files = 2
        mock_metadata.total_lines = 20
        mock_metadata.index_size_mb = 0.1
        mock_metadata.languages_detected = ["python"]
        mock_indexing_engine.get_index_metadata.return_value = mock_metadata

        # Execute
        result = phase_manager.execute_indexing_phase(temp_project_dir)

        # Verify
        assert result.status == PhaseStatus.COMPLETED
        assert "existing cache" in result.message.lower()
        assert result.files_indexed == 2

        # Verify build_index was not called
        mock_indexing_engine.build_index.assert_not_called()

    @patch("dev_agent.workflow.phase_manager.IndexingEngine")
    def test_execute_indexing_phase_failure(self, mock_indexing_engine_class, phase_manager, temp_project_dir, mock_cli_interface):
        """Test failed indexing phase execution."""
        # Mock indexing engine
        mock_indexing_engine = Mock()
        mock_indexing_engine_class.return_value = mock_indexing_engine

        # Mock failed indexing
        mock_indexing_engine.is_index_stale.return_value = True
        mock_index_result = Mock()
        mock_index_result.success = False
        mock_index_result.errors = ["Failed to parse files", "Memory error"]
        mock_indexing_engine.build_index.return_value = mock_index_result

        # Execute
        result = phase_manager.execute_indexing_phase(temp_project_dir)

        # Verify
        assert result.status == PhaseStatus.FAILED
        assert "Failed to parse files" in result.message
        assert len(result.errors) == 2

    @patch("dev_agent.workflow.phase_manager.SpecificationWorkflow")
    @patch("dev_agent.workflow.phase_manager.CodebaseAnalyzer")
    @patch("dev_agent.workflow.phase_manager.IndexingEngine")
    def test_execute_specification_phase_success(self, mock_indexing_engine_class, mock_analyzer_class,
                                               mock_workflow_class, phase_manager, project_context, mock_cli_interface):
        """Test successful specification phase execution."""
        # Mock components
        mock_workflow = Mock()
        mock_workflow_class.return_value = mock_workflow

        # Mock successful specification generation
        from dev_agent.models.documents import Requirement
        from dev_agent.models.enums import Priority, SpecificationSource

        mock_requirements = [
            Requirement(id="req1", user_story="As a user...", acceptance_criteria=["When..."], priority=Priority.HIGH, source_analysis=None),
            Requirement(id="req2", user_story="As a user...", acceptance_criteria=["When..."], priority=Priority.MEDIUM, source_analysis=None)
        ]

        mock_spec = SpecificationDocument(
            introduction="Test spec",
            key_features=["Feature 1", "Feature 2"],
            functional_requirements=mock_requirements,
            source=SpecificationSource.EXISTING_CODE,
            version="1.0",
            approved=True,
            approval_timestamp=None
        )
        mock_workflow.execute_specification_phase.return_value = mock_spec

        # Mock state manager to return project state with specification
        with patch.object(phase_manager.state_manager, "load_project_state") as mock_load_state:
            mock_project_state = Mock()
            mock_project_state.specification = mock_spec
            mock_load_state.return_value = mock_project_state

            # Execute
            result = phase_manager.execute_specification_phase(project_context)

            # Verify
            assert result.status == PhaseStatus.COMPLETED
            assert result.requirements_count == 2
            mock_cli_interface.display_message.assert_called()

    @patch("dev_agent.workflow.phase_manager.SpecificationWorkflow")
    @patch("dev_agent.workflow.phase_manager.CodebaseAnalyzer")
    @patch("dev_agent.workflow.phase_manager.IndexingEngine")
    def test_execute_specification_phase_not_approved(self, mock_indexing_engine_class, mock_analyzer_class,
                                                    mock_workflow_class, phase_manager, project_context, mock_cli_interface):
        """Test specification phase when not approved."""
        # Mock components
        mock_workflow = Mock()
        mock_workflow_class.return_value = mock_workflow

        # Mock specification not approved
        from dev_agent.models.enums import SpecificationSource

        mock_spec = SpecificationDocument(
            introduction="Test spec",
            key_features=["Feature 1"],
            functional_requirements=[],
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=False,
            approval_timestamp=None
        )
        mock_workflow.execute_specification_phase.return_value = mock_spec

        # Execute
        result = phase_manager.execute_specification_phase(project_context)

        # Verify
        assert result.status == PhaseStatus.FAILED
        assert "not approved" in result.message.lower()

    def test_validate_phase_completion_indexing_success(self, phase_manager):
        """Test validation of successful indexing completion."""
        result = IndexingResult(
            status=PhaseStatus.COMPLETED,
            files_indexed=10,
            total_lines=1000,
            index_size_mb=5.0,
            languages_detected=["python", "javascript"]
        )

        assert phase_manager.validate_phase_completion(PhaseType.INDEXING, result) is True

    def test_validate_phase_completion_indexing_failure(self, phase_manager, mock_cli_interface):
        """Test validation of failed indexing completion."""
        result = IndexingResult(
            status=PhaseStatus.COMPLETED,
            files_indexed=0,  # No files indexed
            total_lines=0,
            index_size_mb=0.0,
            languages_detected=[]
        )

        assert phase_manager.validate_phase_completion(PhaseType.INDEXING, result) is False
        mock_cli_interface.display_message.assert_called()

    def test_retry_phase_execution_success_on_retry(self, phase_manager, project_context, mock_cli_interface):
        """Test successful phase execution on retry."""
        # Mock phase execution to fail first, then succeed
        with patch.object(phase_manager, "execute_indexing_phase") as mock_execute:
            # First call fails, second succeeds
            failed_result = IndexingResult(status=PhaseStatus.FAILED, message="First attempt failed")
            success_result = IndexingResult(status=PhaseStatus.COMPLETED, message="Second attempt succeeded")
            mock_execute.side_effect = [failed_result, success_result]

            # Execute
            result = phase_manager.retry_phase_execution(PhaseType.INDEXING, project_context, max_attempts=2)

            # Verify
            assert result.status == PhaseStatus.COMPLETED
            assert mock_execute.call_count == 2
            mock_cli_interface.display_message.assert_called()

    def test_retry_phase_execution_all_attempts_fail(self, phase_manager, project_context, mock_cli_interface):
        """Test phase execution when all retry attempts fail."""
        # Mock phase execution to always fail
        with patch.object(phase_manager, "execute_indexing_phase") as mock_execute:
            failed_result = IndexingResult(status=PhaseStatus.FAILED, message="Always fails")
            mock_execute.return_value = failed_result

            # Execute
            result = phase_manager.retry_phase_execution(PhaseType.INDEXING, project_context, max_attempts=3)

            # Verify
            assert result.status == PhaseStatus.FAILED
            assert mock_execute.call_count == 3
            mock_cli_interface.display_message.assert_called()


class TestWorkflowIntegration:
    """Integration tests for complete workflow scenarios."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory with sample files."""
        temp_dir = tempfile.mkdtemp()

        # Create a realistic Python project structure
        (Path(temp_dir) / "src").mkdir()
        (Path(temp_dir) / "tests").mkdir()

        # Main application file
        (Path(temp_dir) / "src" / "app.py").write_text("""
from flask import Flask, jsonify
from .models import User
from .database import db

app = Flask(__name__)

@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@app.route('/users', methods=['POST'])
def create_user():
    # Implementation here
    pass

if __name__ == '__main__':
    app.run(debug=True)
""")

        # Models file
        (Path(temp_dir) / "src" / "models.py").write_text("""
from sqlalchemy import Column, Integer, String, DateTime
from .database import db

class User(db.Model):
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }
""")

        # Database file
        (Path(temp_dir) / "src" / "database.py").write_text("""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
""")

        # Test file
        (Path(temp_dir) / "tests" / "test_app.py").write_text("""
import pytest
from src.app import app
from src.models import User

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_get_users(client):
    response = client.get('/users')
    assert response.status_code == 200
""")

        # Requirements file
        (Path(temp_dir) / "requirements.txt").write_text("""
Flask==2.0.1
SQLAlchemy==1.4.22
Flask-SQLAlchemy==2.5.1
pytest==6.2.4
""")

        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_cli_interface(self):
        """Create a mock CLI interface that approves everything."""
        cli = Mock()
        cli.display_message = Mock()
        cli.display_progress = Mock()
        cli.request_approval = Mock(return_value=True)  # Always approve
        cli.get_user_input = Mock(return_value="Looks good!")
        return cli

    def test_complete_workflow_integration(self, temp_project_dir, mock_cli_interface):
        """Test complete workflow integration with mocked phase execution."""
        # Create workflow manager
        workflow_manager = WorkflowManager(mock_cli_interface)
        workflow_manager.start_new_project(temp_project_dir)

        # Mock successful results for all phases
        successful_result = Mock()
        successful_result.status = PhaseStatus.COMPLETED
        successful_result.message = "Phase completed"

        with patch.object(workflow_manager, "_execute_phase", return_value=successful_result):
            # Execute complete workflow
            success = workflow_manager.execute_complete_workflow()

            # Verify workflow completed successfully
            assert success is True
            assert workflow_manager.current_project_state.current_phase == PhaseType.IMPLEMENTATION

            # Verify CLI interactions
            assert mock_cli_interface.display_message.call_count > 5  # Many status messages

    def test_workflow_failure_recovery(self, temp_project_dir, mock_cli_interface):
        """Test workflow behavior when phases fail and recovery mechanisms."""
        # Create workflow manager
        workflow_manager = WorkflowManager(mock_cli_interface)
        workflow_manager.start_new_project(temp_project_dir)

        # Mock a phase to fail
        with patch.object(workflow_manager, "_execute_phase") as mock_execute:
            failed_result = Mock()
            failed_result.status = PhaseStatus.FAILED
            failed_result.message = "Simulated failure"
            mock_execute.return_value = failed_result

            # Try to transition to specification phase
            success = workflow_manager.transition_to_phase(PhaseType.SPECIFICATION)

            # Verify failure was handled gracefully
            assert success is False
            assert workflow_manager.current_project_state.current_phase == PhaseType.INDEXING  # Should remain unchanged

            # Verify error messages were displayed
            mock_cli_interface.display_message.assert_called()

    def test_workflow_state_persistence(self, temp_project_dir, mock_cli_interface):
        """Test that workflow state is properly persisted and can be resumed."""
        # Create and initialize workflow
        workflow_manager1 = WorkflowManager(mock_cli_interface)
        initial_state = workflow_manager1.start_new_project(temp_project_dir)

        # Modify state
        initial_state.indexing_complete = True
        initial_state.current_phase = PhaseType.SPECIFICATION
        workflow_manager1.state_manager.save_project_state(initial_state)

        # Create new workflow manager and resume
        workflow_manager2 = WorkflowManager(mock_cli_interface)
        resumed_state = workflow_manager2.resume_project(temp_project_dir)

        # Verify state was properly restored
        assert resumed_state.indexing_complete is True
        assert resumed_state.current_phase == PhaseType.SPECIFICATION
        assert resumed_state.project_path == temp_project_dir
        assert resumed_state.session_data.session_id == initial_state.session_data.session_id

    def test_workflow_validation_checks(self, temp_project_dir, mock_cli_interface):
        """Test workflow validation and error checking."""
        workflow_manager = WorkflowManager(mock_cli_interface)

        # Test operations without initialized project
        assert workflow_manager.transition_to_phase(PhaseType.SPECIFICATION) is False
        assert workflow_manager.execute_complete_workflow() is False

        # Initialize project
        workflow_manager.start_new_project(temp_project_dir)

        # Test invalid phase transitions
        assert workflow_manager.transition_to_phase(PhaseType.IMPLEMENTATION) is False  # Skip phases

        # Test valid transitions
        # Note: These would normally require proper mocking of phase execution
        # For now, we just test the validation logic
        assert workflow_manager._validate_phase_transition(PhaseType.INDEXING, PhaseType.SPECIFICATION) is True
        assert workflow_manager._validate_phase_transition(PhaseType.SPECIFICATION, PhaseType.DESIGN) is True
        assert workflow_manager._validate_phase_transition(PhaseType.DESIGN, PhaseType.IMPLEMENTATION) is True

        # Test backward transitions (allowed for refinement)
        assert workflow_manager._validate_phase_transition(PhaseType.SPECIFICATION, PhaseType.INDEXING) is True
        assert workflow_manager._validate_phase_transition(PhaseType.DESIGN, PhaseType.SPECIFICATION) is True
        assert workflow_manager._validate_phase_transition(PhaseType.IMPLEMENTATION, PhaseType.DESIGN) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
