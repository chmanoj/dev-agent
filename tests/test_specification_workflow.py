"""Tests for specification workflow integration."""

from unittest.mock import Mock, patch

import pytest

from dev_agent.interfaces.analysis_interface import ICodebaseAnalyzer
from dev_agent.interfaces.cli_interface import ICLIInterface
from dev_agent.models.analysis import RequirementEvidence, SpecificationAnalysis
from dev_agent.models.documents import SpecificationDocument
from dev_agent.models.enums import Priority, SpecificationSource
from dev_agent.state.state_manager import StateManager
from dev_agent.workflow.specification_workflow import (
    SpecificationWorkflow,
    SpecificationWorkflowResult,
)


class TestSpecificationWorkflow:
    """Test cases for SpecificationWorkflow."""

    @pytest.fixture
    def mock_cli(self):
        """Create a mock CLI interface."""
        cli = Mock(spec=ICLIInterface)
        cli.display_message = Mock()
        cli.get_user_input = Mock()
        cli.request_approval = Mock(return_value=True)
        return cli

    @pytest.fixture
    def mock_analyzer(self):
        """Create a mock codebase analyzer."""
        analyzer = Mock(spec=ICodebaseAnalyzer)

        # Create sample analysis result
        evidence = RequirementEvidence(
            requirement_type="User Management",
            description="System manages user accounts",
            supporting_files=["models/user.py"],
            supporting_functions=["create_user", "update_user"],
            confidence=0.8,
            code_examples=[],
        )

        analysis = SpecificationAnalysis(
            project_purpose="Web application for user management",
            main_features=["User Registration", "Authentication"],
            user_roles=["User", "Admin"],
            functional_areas=["Authentication", "User Management"],
            requirement_evidence=[evidence],
            technology_constraints=["Python 3.x"],
            external_dependencies=["flask"],
            confidence_score=0.8,
        )

        analyzer.analyze_for_specification.return_value = analysis
        return analyzer

    @pytest.fixture
    def mock_state_manager(self):
        """Create a mock state manager."""
        state_manager = Mock(spec=StateManager)
        state_manager.save_document = Mock()
        return state_manager

    @pytest.fixture
    def workflow(self, mock_cli, mock_analyzer, mock_state_manager):
        """Create a specification workflow with mocks."""
        return SpecificationWorkflow(
            cli_interface=mock_cli,
            codebase_analyzer=mock_analyzer,
            state_manager=mock_state_manager,
        )

    @pytest.fixture
    def workflow_no_analyzer(self, mock_cli, mock_state_manager):
        """Create a specification workflow without analyzer."""
        return SpecificationWorkflow(
            cli_interface=mock_cli,
            codebase_analyzer=None,
            state_manager=mock_state_manager,
        )

    def test_execute_specification_phase_existing_code(
        self, workflow, mock_cli, mock_analyzer
    ):
        """Test executing specification phase with existing code."""
        project_path = "/test/project"

        with patch.object(workflow, "_has_existing_code", return_value=True):
            spec = workflow.execute_specification_phase(project_path)

        # Verify analyzer was called
        mock_analyzer.analyze_for_specification.assert_called_once()

        # Verify CLI messages
        mock_cli.display_message.assert_any_call(
            "Starting specification generation phase..."
        )
        mock_cli.display_message.assert_any_call("Analyzing existing codebase...")
        mock_cli.display_message.assert_any_call(
            "Specification phase completed successfully!"
        )

        # Verify specification properties
        assert isinstance(spec, SpecificationDocument)
        assert spec.source == SpecificationSource.EXISTING_CODE
        assert spec.approved is True

    def test_execute_specification_phase_new_project(
        self, workflow_no_analyzer, mock_cli
    ):
        """Test executing specification phase for new project."""
        project_path = "/test/project"

        # Mock user input for requirements
        mock_cli.get_user_input.side_effect = [
            "Create user accounts",
            "Manage user profiles",
            "",  # Empty to stop
        ]

        with patch.object(
            workflow_no_analyzer, "_has_existing_code", return_value=False
        ):
            spec = workflow_no_analyzer.execute_specification_phase(project_path)

        # Verify CLI messages
        mock_cli.display_message.assert_any_call(
            "Starting specification generation phase..."
        )
        mock_cli.display_message.assert_any_call(
            "No existing codebase detected. Let's create a specification from your requirements."
        )
        mock_cli.display_message.assert_any_call(
            "Specification phase completed successfully!"
        )

        # Verify specification properties
        assert isinstance(spec, SpecificationDocument)
        assert spec.source == SpecificationSource.USER_INPUT
        assert spec.approved is True

    def test_approval_workflow_immediate_approval(self, workflow, mock_cli):
        """Test approval workflow with immediate approval."""
        # Create a sample specification
        spec = SpecificationDocument(
            introduction="Test spec",
            key_features=["Feature 1"],
            functional_requirements=[],
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=False,
        )

        # Mock immediate approval with side effect to update spec
        def mock_approval(spec_doc):
            spec_doc.approved = True
            return True

        workflow.generator.request_user_approval = Mock(side_effect=mock_approval)

        result_spec = workflow._approval_workflow(spec)

        assert result_spec.approved is True
        mock_cli.display_message.assert_any_call("Specification approved!")

    def test_approval_workflow_with_refinement(self, workflow, mock_cli):
        """Test approval workflow with one refinement iteration."""
        # Create a sample specification
        spec = SpecificationDocument(
            introduction="Test spec",
            key_features=["Feature 1"],
            functional_requirements=[],
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=False,
        )

        # Mock approval sequence: reject first, approve second
        def mock_approval_sequence(spec_doc):
            if not hasattr(mock_approval_sequence, "call_count"):
                mock_approval_sequence.call_count = 0
            mock_approval_sequence.call_count += 1

            if mock_approval_sequence.call_count == 1:
                return False  # First call rejects
            else:
                spec_doc.approved = True  # Second call approves
                return True

        workflow.generator.request_user_approval = Mock(
            side_effect=mock_approval_sequence
        )
        mock_cli.get_user_input.return_value = "Add more security features"

        result_spec = workflow._approval_workflow(spec)

        # Verify refinement was requested
        mock_cli.get_user_input.assert_called_once_with(
            "Please provide feedback for improving the specification: "
        )
        mock_cli.display_message.assert_any_call(
            "Refining specification based on your feedback..."
        )
        mock_cli.display_message.assert_any_call("Specification approved!")

        assert result_spec.approved is True
        assert result_spec.version != spec.version  # Version should be incremented

    def test_approval_workflow_max_iterations(self, workflow, mock_cli):
        """Test approval workflow reaching maximum iterations."""
        # Create a sample specification
        spec = SpecificationDocument(
            introduction="Test spec",
            key_features=["Feature 1"],
            functional_requirements=[],
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=False,
        )

        # Mock always rejecting approval
        workflow.generator.request_user_approval = Mock(return_value=False)
        mock_cli.get_user_input.return_value = "Keep improving"

        result_spec = workflow._approval_workflow(spec)

        # Should reach max iterations and auto-approve
        assert workflow.generator.request_user_approval.call_count == 3
        mock_cli.display_message.assert_any_call(
            "Maximum refinement iterations reached. Using current specification."
        )
        assert result_spec.approved is True

    def test_approval_workflow_empty_feedback(self, workflow, mock_cli):
        """Test approval workflow with empty feedback."""
        # Create a sample specification
        spec = SpecificationDocument(
            introduction="Test spec",
            key_features=["Feature 1"],
            functional_requirements=[],
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=False,
        )

        # Mock rejection then empty feedback
        workflow.generator.request_user_approval = Mock(return_value=False)
        mock_cli.get_user_input.return_value = ""  # Empty feedback

        result_spec = workflow._approval_workflow(spec)

        mock_cli.display_message.assert_any_call(
            "No feedback provided. Using current specification."
        )
        assert result_spec.approved is True

    def test_has_existing_code_with_python_files(self, workflow):
        """Test detecting existing code with Python files."""
        with patch("pathlib.Path.rglob") as mock_rglob:
            # Mock finding Python files
            mock_file = Mock()
            mock_file.is_file.return_value = True
            mock_file.suffix = ".py"
            mock_file.parts = ("project", "src", "main.py")

            mock_rglob.return_value = [mock_file]

            result = workflow._has_existing_code("/test/project")
            assert result is True

    def test_has_existing_code_no_files(self, workflow):
        """Test detecting no existing code."""
        with patch("pathlib.Path.rglob") as mock_rglob:
            mock_rglob.return_value = []

            result = workflow._has_existing_code("/test/project")
            assert result is False

    def test_has_existing_code_ignores_hidden_files(self, workflow):
        """Test that hidden files and directories are ignored."""
        with patch("pathlib.Path.rglob") as mock_rglob:
            # Mock finding files in hidden directories
            mock_file = Mock()
            mock_file.is_file.return_value = True
            mock_file.suffix = ".py"
            mock_file.parts = ("project", ".git", "hooks", "pre-commit")

            mock_rglob.return_value = [mock_file]

            result = workflow._has_existing_code("/test/project")
            assert result is False

    def test_save_specification_success(self, workflow, mock_state_manager, mock_cli):
        """Test successful specification saving."""
        spec = SpecificationDocument(
            introduction="Test spec",
            key_features=["Feature 1"],
            functional_requirements=[],
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=True,
        )

        workflow._save_specification(spec)

        # Verify state manager was called
        mock_state_manager.save_document.assert_called_once()
        mock_cli.display_message.assert_any_call(
            "Specification saved to SPECIFICATION.md"
        )

    def test_save_specification_error(self, workflow, mock_state_manager, mock_cli):
        """Test specification saving with error."""
        spec = SpecificationDocument(
            introduction="Test spec",
            key_features=["Feature 1"],
            functional_requirements=[],
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=True,
        )

        # Mock save error
        mock_state_manager.save_document.side_effect = Exception("Save failed")

        workflow._save_specification(spec)

        mock_cli.display_message.assert_any_call(
            "Warning: Could not save specification: Save failed"
        )

    def test_generate_from_existing_code(self, workflow, mock_cli, mock_analyzer):
        """Test generating specification from existing code."""
        spec = workflow._generate_from_existing_code()

        # Verify analyzer was called
        mock_analyzer.analyze_for_specification.assert_called_once()

        # Verify CLI messages
        mock_cli.display_message.assert_any_call("Analyzing existing codebase...")
        mock_cli.display_message.assert_any_call(
            "Analysis complete with 80% confidence. Found 2 main features and 1 requirement areas."
        )

        # Verify specification
        assert isinstance(spec, SpecificationDocument)
        assert spec.source == SpecificationSource.EXISTING_CODE

    def test_generate_from_user_input(self, workflow, mock_cli):
        """Test generating specification from user input."""
        # Mock user input
        mock_cli.get_user_input.side_effect = [
            "Create user system",
            "",  # Empty to stop
        ]

        spec = workflow._generate_from_user_input()

        # Verify CLI message
        mock_cli.display_message.assert_any_call(
            "No existing codebase detected. Let's create a specification from your requirements."
        )

        # Verify specification
        assert isinstance(spec, SpecificationDocument)
        assert spec.source == SpecificationSource.USER_INPUT


class TestSpecificationWorkflowResult:
    """Test cases for SpecificationWorkflowResult."""

    def test_workflow_result_creation(self):
        """Test creating workflow result."""
        spec = SpecificationDocument(
            introduction="Test",
            key_features=[],
            functional_requirements=[],
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=True,
        )

        result = SpecificationWorkflowResult(
            specification=spec, success=True, message="Completed successfully"
        )

        assert result.specification == spec
        assert result.success is True
        assert result.message == "Completed successfully"


class TestSpecificationWorkflowIntegration:
    """Integration tests for specification workflow."""

    @pytest.fixture
    def real_workflow(self):
        """Create a real workflow for integration testing."""
        cli = Mock(spec=ICLIInterface)
        cli.display_message = Mock()
        cli.get_user_input = Mock()
        cli.request_approval = Mock(return_value=True)

        return SpecificationWorkflow(cli_interface=cli)

    def test_full_workflow_new_project(self, real_workflow):
        """Test complete workflow for new project."""
        # Mock user providing requirements
        real_workflow.cli_interface.get_user_input.side_effect = [
            "Users can create accounts",
            "Users can login securely",
            "Users can manage profiles",
            "",  # Empty to stop
        ]

        with patch.object(real_workflow, "_has_existing_code", return_value=False):
            spec = real_workflow.execute_specification_phase("/test/project")

        # Verify complete workflow
        assert isinstance(spec, SpecificationDocument)
        assert spec.source == SpecificationSource.USER_INPUT
        assert spec.approved is True
        assert len(spec.functional_requirements) == 3

        # Verify all requirements have proper structure
        for req in spec.functional_requirements:
            assert req.user_story.startswith("As a")
            assert len(req.acceptance_criteria) >= 2
            assert req.priority == Priority.MEDIUM

    def test_workflow_with_refinement_cycle(self, real_workflow):
        """Test workflow with approval and refinement cycle."""
        # Mock user providing requirements
        real_workflow.cli_interface.get_user_input.side_effect = [
            "Create user management system",
            "",  # Empty to stop requirements
            "Add more security features",  # Refinement feedback
        ]

        # Mock approval sequence: reject first, approve second
        def mock_approval_sequence(spec_doc):
            if not hasattr(mock_approval_sequence, "call_count"):
                mock_approval_sequence.call_count = 0
            mock_approval_sequence.call_count += 1

            if mock_approval_sequence.call_count == 1:
                return False  # First call rejects
            else:
                spec_doc.approved = True  # Second call approves
                return True

        real_workflow.generator.request_user_approval = Mock(
            side_effect=mock_approval_sequence
        )

        with patch.object(real_workflow, "_has_existing_code", return_value=False):
            spec = real_workflow.execute_specification_phase("/test/project")

        # Verify refinement occurred
        assert real_workflow.generator.request_user_approval.call_count == 2
        assert spec.approved is True
        assert spec.version != "1.0"  # Should be incremented due to refinement
