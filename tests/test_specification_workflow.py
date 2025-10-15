"""Tests for specification workflow integration."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from dev_agent.interfaces.analysis_interface import ICodebaseAnalyzer
from dev_agent.interfaces.cli_interface import ICLIInterface
from dev_agent.models.analysis import RequirementEvidence, SpecificationAnalysis
from dev_agent.models.documents import Requirement, SpecificationDocument
from dev_agent.models.enums import DocumentType, Priority, SpecificationSource
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
    def mock_llm_client(self):
        """Create a mock LLM client."""
        llm_client = Mock()
        llm_client.generate_completion = AsyncMock(return_value="Generated text")
        return llm_client

    @pytest.fixture
    def workflow(self, mock_cli, mock_analyzer, mock_state_manager, mock_llm_client):
        """Create a specification workflow with mocks."""
        return SpecificationWorkflow(
            cli_interface=mock_cli,
            codebase_analyzer=mock_analyzer,
            state_manager=mock_state_manager,
            llm_client=mock_llm_client,
        )

    @pytest.fixture
    def workflow_no_analyzer(self, mock_cli, mock_state_manager, mock_llm_client):
        """Create a specification workflow without analyzer."""
        return SpecificationWorkflow(
            cli_interface=mock_cli,
            codebase_analyzer=None,
            state_manager=mock_state_manager,
            llm_client=mock_llm_client,
        )

    @pytest.mark.asyncio
    async def test_execute_specification_phase_existing_code(
        self, workflow, mock_cli, mock_analyzer
    ):
        """Test executing specification phase with existing code."""
        project_path = "/test/project"

        with patch.object(workflow, "_has_existing_code", return_value=True):
            with patch.object(workflow, "_get_feature_description", return_value="Test feature"):
                spec = await workflow.execute_specification_phase(project_path)

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

    @pytest.mark.asyncio
    async def test_execute_specification_phase_new_project(
        self, workflow_no_analyzer, mock_cli
    ):
        """Test executing specification phase for new project."""
        project_path = "/test/project"

        with patch.object(
            workflow_no_analyzer, "_has_existing_code", return_value=False
        ):
            with patch.object(workflow_no_analyzer, "_get_feature_description", return_value="Test feature"):
                spec = await workflow_no_analyzer.execute_specification_phase(project_path)

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

    @pytest.mark.asyncio
    async def test_approval_workflow_immediate_approval(self, workflow, mock_cli):
        """Test approval workflow with immediate approval."""
        # Create a sample specification
        spec = SpecificationDocument(
            introduction="Test spec",
            key_features=["Feature 1"],
            functional_requirements=[Mock(user_story="Test user story")],
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=False,
        )

        # Mock immediate approval with side effect to update spec
        def mock_approval(spec_doc):
            spec_doc.approved = True
            return True

        workflow.generator.request_user_approval = Mock(side_effect=mock_approval)

        result_spec = await workflow._approval_workflow_ai(spec, "Test feature")

        assert result_spec.approved is True
        mock_cli.display_message.assert_any_call("✅ Specification approved!")

    @pytest.mark.asyncio
    async def test_approval_workflow_with_refinement(self, workflow, mock_cli):
        """Test approval workflow with one refinement iteration."""
        # Create a sample specification
        spec = SpecificationDocument(
            introduction="Test spec",
            key_features=["Feature 1"],
            functional_requirements=[Mock(user_story="Test user story")],
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
        workflow.generator.refine_specification_ai = AsyncMock(return_value=spec)

        result_spec = await workflow._approval_workflow_ai(spec, "Test feature")

        # Verify refinement was requested
        mock_cli.get_user_input.assert_called_once_with(
            "\nYour feedback (or press Enter to approve): "
        )
        mock_cli.display_message.assert_any_call(
            "🤖 Refining specification using AI based on your feedback... This may take a moment."
        )
        mock_cli.display_message.assert_any_call("✅ Specification refined successfully!")

        assert result_spec.approved is True

    @pytest.mark.asyncio
    async def test_approval_workflow_max_iterations(self, workflow, mock_cli):
        """Test approval workflow reaching maximum iterations."""
        # Create a sample specification
        spec = SpecificationDocument(
            introduction="Test spec",
            key_features=["Feature 1"],
            functional_requirements=[Mock(user_story="Test user story")],
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=False,
        )

        # Mock always rejecting approval
        workflow.generator.request_user_approval = Mock(return_value=False)
        mock_cli.get_user_input.return_value = "Keep improving"
        workflow.generator.refine_specification_ai = AsyncMock(return_value=spec)

        result_spec = await workflow._approval_workflow_ai(spec, "Test feature")

        # Should reach max iterations and auto-approve
        assert workflow.generator.request_user_approval.call_count == 3
        mock_cli.display_message.assert_any_call(
            "Maximum refinement iterations reached. Using current specification."
        )
        assert result_spec.approved is True

    @pytest.mark.asyncio
    async def test_approval_workflow_empty_feedback(self, workflow, mock_cli):
        """Test approval workflow with empty feedback."""
        # Create a sample specification
        spec = SpecificationDocument(
            introduction="Test spec",
            key_features=["Feature 1"],
            functional_requirements=[Mock(user_story="Test user story")],
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=False,
        )

        # Mock rejection then empty feedback
        workflow.generator.request_user_approval = Mock(return_value=False)
        mock_cli.get_user_input.return_value = ""  # Empty feedback

        result_spec = await workflow._approval_workflow_ai(spec, "Test feature")

        mock_cli.display_message.assert_any_call(
            "✅ No feedback provided. Approving current specification."
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

    @pytest.mark.asyncio
    async def test_save_specification_success(self, workflow, mock_state_manager, mock_cli):
        """Test successful specification saving."""
        requirement = Requirement(
            id="REQ-1",
            user_story="As a user, I want to do something.",
            acceptance_criteria=["It should do the thing.", "It should not fail."],
            priority=Priority.HIGH,
            source_analysis=None
        )
        spec = SpecificationDocument(
            introduction="Test spec",
            key_features=["Feature 1"],
            functional_requirements=[requirement],
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=True,
        )
        mock_state_manager.save_document = AsyncMock()

        with patch.object(Path, "cwd", return_value=Path("/test")):
            mock_state_manager.documents_dir = Path("/test/docs")
            await workflow._save_specification(spec)

        # Verify state manager was called
        mock_state_manager.save_document.assert_awaited_once_with(
            workflow.generator.format_specification_document(spec),
            DocumentType.SPECIFICATION,
        )
        mock_cli.display_message.assert_any_call(
            "Specification saved to docs/SPECIFICATION.md"
        )

    @pytest.mark.asyncio
    async def test_save_specification_error(self, workflow, mock_state_manager, mock_cli):
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
        mock_state_manager.save_document = AsyncMock(side_effect=Exception("Save failed"))

        await workflow._save_specification(spec)

        mock_cli.display_message.assert_any_call(
            "Warning: Could not save specification: Save failed"
        )

    @pytest.mark.asyncio
    async def test_generate_from_existing_code(self, workflow, mock_cli, mock_analyzer):
        """Test generating specification from existing code."""
        workflow.generator.generate_from_existing_code_ai = AsyncMock(
            return_value=SpecificationDocument(
                introduction="Test spec",
                key_features=["Feature 1"],
                functional_requirements=[Mock(user_story="Test user story", acceptance_criteria=["Test criteria"])],
                source=SpecificationSource.EXISTING_CODE,
                version="1.0",
                approved=False,
            )
        )
        with patch.object(workflow.generator, "_validate_specification", return_value=(True, [])):
            spec = await workflow._generate_from_existing_code("Test feature")

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

    @pytest.mark.asyncio
    async def test_generate_from_user_input(self, workflow, mock_cli):
        """Test generating specification from user input."""
        requirement = Requirement(
            id="REQ-1",
            user_story="As a user, I want to do something.",
            acceptance_criteria=["It should do the thing.", "It should not fail."],
            priority=Priority.HIGH,
            source_analysis=None
        )
        workflow.generator.generate_from_user_input_ai = AsyncMock(
            return_value=SpecificationDocument(
                introduction="Test spec",
                key_features=["Feature 1"],
                functional_requirements=[requirement],
                source=SpecificationSource.USER_INPUT,
                version="1.0",
                approved=False,
            )
        )
        spec = await workflow._generate_from_user_input("Test feature")

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

    @pytest.mark.asyncio
    async def test_full_workflow_new_project(self, real_workflow, mock_llm_client):
        """Test complete workflow for new project."""
        real_workflow.llm_client = mock_llm_client
        # Mock user providing requirements
        real_workflow.cli_interface.get_user_input.side_effect = [
            "Users can create accounts",
            "Users can login securely",
            "Users can manage profiles",
            "",  # Empty to stop
        ]
        requirement = Requirement(
            id="REQ-1",
            user_story="As a user, I want to do something.",
            acceptance_criteria=["It should do the thing.", "It should not fail."],
            priority=Priority.HIGH,
            source_analysis=None
        )
        real_workflow.generator.generate_from_user_input_ai = AsyncMock(
            return_value=SpecificationDocument(
                introduction="Test spec",
                key_features=["Feature 1"],
                functional_requirements=[requirement],
                source=SpecificationSource.USER_INPUT,
                version="1.0",
                approved=False,
            )
        )

        with patch.object(real_workflow, "_has_existing_code", return_value=False):
            with patch.object(real_workflow, "_get_feature_description", return_value="Test feature"):
                spec = await real_workflow.execute_specification_phase("/test/project")

        # Verify complete workflow
        assert isinstance(spec, SpecificationDocument)
        assert spec.source == SpecificationSource.USER_INPUT
        assert spec.approved is True
        assert len(spec.functional_requirements) > 0

    @pytest.mark.asyncio
    async def test_workflow_with_refinement_cycle(self, real_workflow, mock_llm_client):
        """Test workflow with approval and refinement cycle."""
        real_workflow.llm_client = mock_llm_client
        # Mock user providing requirements
        real_workflow.cli_interface.get_user_input.side_effect = [
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
        real_workflow.generator.refine_specification_ai = AsyncMock(return_value=SpecificationDocument(
            introduction="Refined spec",
            key_features=["Feature 1"],
            functional_requirements=[Mock(user_story="Test user story", acceptance_criteria=["Test criteria"])],
            source=SpecificationSource.USER_INPUT,
            version="1.1",
            approved=False,
        ))
        real_workflow.generator.generate_from_user_input_ai = AsyncMock(
            return_value=SpecificationDocument(
                introduction="Test spec",
                key_features=["Feature 1"],
                functional_requirements=[Mock(user_story="Test user story", acceptance_criteria=["Test criteria"])],
                source=SpecificationSource.USER_INPUT,
                version="1.0",
                approved=False,
            )
        )

        with patch.object(real_workflow, "_has_existing_code", return_value=False):
            with patch.object(real_workflow, "_get_feature_description", return_value="Test feature"):
                spec = await real_workflow.execute_specification_phase("/test/project")

        # Verify refinement occurred
        assert real_workflow.generator.request_user_approval.call_count == 2
        assert spec.approved is True
        assert spec.version != "1.0"  # Should be incremented due to refinement
