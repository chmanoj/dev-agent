"""Tests for design workflow."""

from unittest.mock import Mock, patch, AsyncMock

import pytest

from dev_agent.interfaces.analysis_interface import ICodebaseAnalyzer
from dev_agent.interfaces.cli_interface import ICLIInterface
from dev_agent.models.analysis import ComponentAnalysis, DesignAnalysis
from dev_agent.models.documents import (
    ArchitectureDescription,
    DesignDocument,
    ErrorHandlingStrategy,
    Requirement,
    SpecificationDocument,
    TestingStrategy,
)
from dev_agent.models.enums import Priority, SpecificationSource
from dev_agent.state.state_manager import StateManager
from dev_agent.workflow.design_workflow import DesignWorkflow, DesignWorkflowResult


class TestDesignWorkflow:
    """Test cases for DesignWorkflow."""

    @pytest.fixture
    def mock_cli(self):
        """Create a mock CLI interface."""
        cli = Mock(spec=ICLIInterface)
        cli.display_message = Mock()
        cli.get_user_input = Mock(return_value="Looks good!")
        return cli

    @pytest.fixture
    def mock_analyzer(self):
        """Create a mock codebase analyzer."""
        analyzer = Mock(spec=ICodebaseAnalyzer)

        # Mock design analysis
        component_analysis = ComponentAnalysis(
            name="TestComponent",
            purpose="Test component for testing",
            interfaces=["ITestInterface"],
            dependencies=["TestDependency"],
            internal_structure={"files": 2, "functions": 10, "classes": 1},
            complexity_score=2.0,
        )

        design_analysis = DesignAnalysis(
            architecture_overview="Test architecture overview",
            components=[component_analysis],
            data_models=[{"name": "TestModel", "attributes": ["id", "name"]}],
            api_interfaces=[
                {"name": "test_api", "parameters": ["param1"], "return_type": "str"}
            ],
            design_patterns=["Repository Pattern"],
            quality_metrics={"documentation_coverage": 0.8},
            technical_debt=["Some technical debt"],
            recommendations=["Add more tests"],
        )

        analyzer.analyze_for_design.return_value = design_analysis
        return analyzer

    @pytest.fixture
    def mock_state_manager(self):
        """Create a mock state manager."""
        state_manager = Mock(spec=StateManager)
        state_manager.save_document = AsyncMock()
        state_manager.save_project_state = AsyncMock()
        state_manager.load_project_state = Mock(return_value=Mock())
        return state_manager

    @pytest.fixture
    def workflow(self, mock_cli, mock_analyzer, mock_state_manager):
        """Create a design workflow with mocks."""
        return DesignWorkflow(
            cli_interface=mock_cli,
            codebase_analyzer=mock_analyzer,
            state_manager=mock_state_manager,
        )

    @pytest.fixture
    def workflow_no_state(self, mock_cli, mock_analyzer):
        """Create a design workflow without state manager."""
        return DesignWorkflow(cli_interface=mock_cli, codebase_analyzer=mock_analyzer)

    @pytest.fixture
    def sample_specification(self):
        """Create a sample approved specification."""
        requirements = [
            Requirement(
                id="FR-1",
                user_story="As a user, I want to manage data, so that I can store information",
                acceptance_criteria=["WHEN I save data THEN it SHALL be stored"],
                priority=Priority.HIGH,
            )
        ]

        return SpecificationDocument(
            introduction="Test specification",
            key_features=["Data Management"],
            functional_requirements=requirements,
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=True,
        )

    @pytest.mark.asyncio
    async def test_execute_design_phase_success(
        self, workflow, sample_specification, mock_cli, mock_analyzer
    ):
        """Test successful execution of design phase."""

        # Mock the generator's request_user_approval to return True and set approved flag
        def mock_approval(design):
            design.approved = True
            return True

        with patch.object(
            workflow.generator, "request_user_approval", side_effect=mock_approval
        ):
            result = await workflow.execute_design_phase(sample_specification)

        assert isinstance(result, DesignDocument)
        assert result.approved
        mock_cli.display_message.assert_called()
        mock_analyzer.analyze_for_design.assert_called_once()
        workflow.state_manager.save_document.assert_awaited_once()
        workflow.state_manager.save_project_state.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_design_persistence(self, tmp_path, sample_specification):
        """Test that the design is correctly saved to and loaded from state."""
        # 1. Setup a real StateManager
        state_manager = StateManager(project_path=str(tmp_path))
        await state_manager.save_project_state(state_manager.create_initial_state(str(tmp_path), "test_session"))


        # 2. Setup workflow with the real StateManager
        cli = Mock(spec=ICLIInterface)
        analyzer = Mock(spec=ICodebaseAnalyzer)
        analyzer.analyze_for_design.return_value = DesignAnalysis(
            architecture_overview="Test architecture",
            components=[],
            data_models=[],
            api_interfaces=[],
            design_patterns=[],
            quality_metrics={},
            technical_debt=[],
            recommendations=[],
        )
        workflow = DesignWorkflow(
            cli_interface=cli,
            codebase_analyzer=analyzer,
            state_manager=state_manager,
        )

        # 3. Execute design phase
        def mock_approval(design):
            design.approved = True
            return True

        with patch.object(
            workflow.generator, "request_user_approval", side_effect=mock_approval
        ):
            design_doc = await workflow.execute_design_phase(sample_specification)

        # 4. The workflow should have saved the state, so we can load it into a new manager
        new_state_manager = StateManager(project_path=str(tmp_path))
        new_state = new_state_manager.load_project_state()

        # 5. Assert that the loaded design document is correct
        loaded_design_doc = new_state.design
        assert loaded_design_doc is not None
        assert isinstance(loaded_design_doc, DesignDocument)
        assert loaded_design_doc.overview == design_doc.overview
        assert loaded_design_doc.version == design_doc.version
        assert loaded_design_doc.approved is True

    @pytest.mark.asyncio
    async def test_execute_design_phase_without_state_manager(
        self, workflow_no_state, sample_specification
    ):
        """Test design phase execution without state manager."""

        def mock_approval(design):
            design.approved = True
            return True

        with patch.object(
            workflow_no_state.generator,
            "request_user_approval",
            side_effect=mock_approval,
        ):
            result = await workflow_no_state.execute_design_phase(sample_specification)

        assert isinstance(result, DesignDocument)
        assert result.approved

    def test_perform_design_analysis_success(self, workflow, mock_analyzer):
        """Test successful design analysis."""
        analysis = workflow._perform_design_analysis()

        assert isinstance(analysis, DesignAnalysis)
        assert analysis.architecture_overview == "Test architecture overview"
        assert len(analysis.components) == 1
        assert analysis.components[0].name == "TestComponent"
        mock_analyzer.analyze_for_design.assert_called_once()

    def test_perform_design_analysis_failure(self, workflow, mock_analyzer, mock_cli):
        """Test design analysis failure handling."""
        mock_analyzer.analyze_for_design.side_effect = Exception("Analysis failed")

        analysis = workflow._perform_design_analysis()

        assert isinstance(analysis, DesignAnalysis)
        assert (
            analysis.architecture_overview == "Unable to analyze existing architecture"
        )
        assert len(analysis.components) == 0
        mock_cli.display_message.assert_any_call(
            "Warning: Design analysis failed: Analysis failed"
        )

    def test_generate_design(self, workflow, sample_specification, mock_cli):
        """Test design generation."""
        analysis = workflow._perform_design_analysis()
        design = workflow._generate_design(sample_specification, analysis)

        assert isinstance(design, DesignDocument)
        assert design.overview is not None
        assert design.architecture is not None
        mock_cli.display_message.assert_called()

    @pytest.mark.asyncio
    async def test_approval_workflow_immediate_approval(self, workflow, sample_specification):
        """Test approval workflow with immediate approval."""
        analysis = workflow._perform_design_analysis()
        design = workflow._generate_design(sample_specification, analysis)

        def mock_approval(design):
            design.approved = True
            return True

        with patch.object(
            workflow.generator, "request_user_approval", side_effect=mock_approval
        ):
            approved_design = await workflow._approval_workflow(design)

        assert approved_design.approved
        assert approved_design.version == design.version

    @pytest.mark.asyncio
    async def test_approval_workflow_with_refinement(
        self, workflow, sample_specification, mock_cli
    ):
        """Test approval workflow with one refinement iteration."""
        analysis = workflow._perform_design_analysis()
        design = workflow._generate_design(sample_specification, analysis)

        # Mock approval sequence: reject first, approve second
        def mock_approval_sequence(design):
            if not hasattr(mock_approval_sequence, "call_count"):
                mock_approval_sequence.call_count = 0
            mock_approval_sequence.call_count += 1

            if mock_approval_sequence.call_count == 1:
                return False
            else:
                design.approved = True
                return True

        mock_cli.get_user_input.return_value = "Add more components"

        with patch.object(
            workflow.generator,
            "request_user_approval",
            side_effect=mock_approval_sequence,
        ):
            with patch.object(workflow.generator, "refine_design", new_callable=AsyncMock) as mock_refine:
                # Mock refine_design to return a modified design
                refined_design = DesignDocument(
                    overview="Refined overview",
                    architecture=design.architecture,
                    components=design.components,
                    data_models=design.data_models,
                    interfaces=design.interfaces,
                    error_handling=design.error_handling,
                    testing_strategy=design.testing_strategy,
                    version="1.1",
                    approved=False,
                )
                mock_refine.return_value = refined_design

                approved_design = await workflow._approval_workflow(design)

        assert approved_design.approved
        mock_refine.assert_called_once_with(design, "Add more components")
        mock_cli.get_user_input.assert_called()

    @pytest.mark.asyncio
    async def test_approval_workflow_max_iterations(
        self, workflow, sample_specification, mock_cli
    ):
        """Test approval workflow reaching maximum iterations."""
        analysis = workflow._perform_design_analysis()
        design = workflow._generate_design(sample_specification, analysis)

        # Mock approval to always return False
        mock_cli.get_user_input.return_value = "Keep refining"

        with patch.object(
            workflow.generator, "request_user_approval", return_value=False
        ):
            with patch.object(workflow.generator, "refine_design", new_callable=AsyncMock, return_value=design):
                approved_design = await workflow._approval_workflow(design)

        assert approved_design.approved  # Should be force-approved after max iterations
        mock_cli.display_message.assert_any_call(
            "Maximum refinement iterations reached. Using current design."
        )

    @pytest.mark.asyncio
    async def test_approval_workflow_no_feedback(
        self, workflow, sample_specification, mock_cli
    ):
        """Test approval workflow with no feedback provided."""
        analysis = workflow._perform_design_analysis()
        design = workflow._generate_design(sample_specification, analysis)

        # Mock approval sequence: reject first, then no feedback
        approval_calls = [False]
        mock_cli.get_user_input.return_value = ""  # Empty feedback

        with patch.object(
            workflow.generator, "request_user_approval", side_effect=approval_calls
        ):
            approved_design = await workflow._approval_workflow(design)

        assert approved_design.approved
        mock_cli.display_message.assert_any_call(
            "No feedback provided. Using current design."
        )

    def test_display_design_summary(self, workflow, sample_specification, mock_cli):
        """Test design summary display."""
        analysis = workflow._perform_design_analysis()
        design = workflow._generate_design(sample_specification, analysis)

        workflow._display_design_summary(design)

        # Check that summary information was displayed
        mock_cli.display_message.assert_any_call("\n=== Design Summary ===")
        mock_cli.display_message.assert_any_call(f"Version: {design.version}")
        mock_cli.display_message.assert_any_call("=====================\n")

    @pytest.mark.asyncio
    async def test_save_design_success(self, workflow, sample_specification):
        """Test successful design saving."""
        analysis = workflow._perform_design_analysis()
        design = workflow._generate_design(sample_specification, analysis)

        await workflow._save_design(design)
        workflow.state_manager.save_document.assert_awaited_once()
        workflow.state_manager.save_project_state.assert_awaited_once()
        workflow.cli_interface.display_message.assert_any_call(
            "Design saved to DESIGN.md"
        )

    @pytest.mark.asyncio
    async def test_save_design_failure(self, workflow, sample_specification, mock_cli):
        """Test design saving failure handling."""
        analysis = workflow._perform_design_analysis()
        design = workflow._generate_design(sample_specification, analysis)

        workflow.state_manager.save_project_state.side_effect = Exception("Save failed")

        await workflow._save_design(design)

        mock_cli.display_message.assert_any_call(
            "Warning: Could not save design: Save failed"
        )

    def test_validate_specification_input_valid(self, workflow, sample_specification):
        """Test specification validation with valid input."""
        result = workflow.validate_specification_input(sample_specification)
        assert result is True

    def test_validate_specification_input_none(self, workflow, mock_cli):
        """Test specification validation with None input."""
        result = workflow.validate_specification_input(None)
        assert result is False
        mock_cli.display_message.assert_called_with("Error: No specification provided")

    def test_validate_specification_input_not_approved(self, workflow, mock_cli):
        """Test specification validation with unapproved specification."""
        spec = SpecificationDocument(
            introduction="Test",
            key_features=[],
            functional_requirements=[],
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=False,
        )

        result = workflow.validate_specification_input(spec)
        assert result is False
        mock_cli.display_message.assert_called_with(
            "Error: Specification must be approved before design generation"
        )

    def test_validate_specification_input_no_requirements(self, workflow, mock_cli):
        """Test specification validation with no requirements."""
        spec = SpecificationDocument(
            introduction="Test",
            key_features=[],
            functional_requirements=[],
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=True,
        )

        result = workflow.validate_specification_input(spec)
        assert result is False
        mock_cli.display_message.assert_called_with(
            "Error: Specification must contain functional requirements"
        )

    def test_get_design_metrics(self, workflow, sample_specification):
        """Test design metrics extraction."""
        analysis = workflow._perform_design_analysis()
        design = workflow._generate_design(sample_specification, analysis)

        metrics = workflow.get_design_metrics(design)

        assert isinstance(metrics, dict)
        assert "version" in metrics
        assert "component_count" in metrics
        assert "data_model_count" in metrics
        assert "interface_count" in metrics
        assert "pattern_count" in metrics
        assert "error_category_count" in metrics
        assert "test_coverage_target" in metrics
        assert "approved" in metrics

        assert metrics["version"] == design.version
        assert metrics["component_count"] == len(design.components)
        assert metrics["approved"] == design.approved


class TestDesignWorkflowResult:
    """Test cases for DesignWorkflowResult."""

    def test_design_workflow_result_creation(self):
        """Test creating a design workflow result."""
        design = DesignDocument(
            overview="Test overview",
            architecture=ArchitectureDescription(
                overview="Test arch", patterns=[], components=[]
            ),
            components=[],
            data_models=[],
            interfaces=[],
            error_handling=ErrorHandlingStrategy(
                error_categories=[], recovery_mechanisms=[], logging_strategy="Test"
            ),
            testing_strategy=TestingStrategy(
                unit_testing="Test",
                integration_testing="Test",
                performance_testing="Test",
                test_coverage_target=0.8,
            ),
            version="1.0",
            approved=True,
        )

        result = DesignWorkflowResult(
            design=design,
            success=True,
            message="Design generated successfully",
            metrics={"component_count": 0},
        )

        assert result.design == design
        assert result.success is True
        assert result.message == "Design generated successfully"
        assert result.metrics["component_count"] == 0

    def test_design_workflow_result_default_metrics(self):
        """Test creating a design workflow result with default metrics."""
        design = DesignDocument(
            overview="Test overview",
            architecture=ArchitectureDescription(
                overview="Test arch", patterns=[], components=[]
            ),
            components=[],
            data_models=[],
            interfaces=[],
            error_handling=ErrorHandlingStrategy(
                error_categories=[], recovery_mechanisms=[], logging_strategy="Test"
            ),
            testing_strategy=TestingStrategy(
                unit_testing="Test",
                integration_testing="Test",
                performance_testing="Test",
                test_coverage_target=0.8,
            ),
            version="1.0",
            approved=True,
        )

        result = DesignWorkflowResult(design=design, success=True)

        assert result.metrics == {}


class TestDesignWorkflowIntegration:
    """Integration tests for design workflow."""

    @pytest.fixture
    def integration_workflow(self):
        """Create a workflow for integration testing."""
        cli = Mock(spec=ICLIInterface)
        cli.display_message = Mock()
        cli.get_user_input = Mock(return_value="")

        analyzer = Mock(spec=ICodebaseAnalyzer)
        analyzer.analyze_for_design.return_value = DesignAnalysis(
            architecture_overview="Integration test architecture",
            components=[],
            data_models=[],
            api_interfaces=[],
            design_patterns=[],
            quality_metrics={},
            technical_debt=[],
            recommendations=[],
        )

        state_manager = Mock(spec=StateManager)
        state_manager.save_document = AsyncMock()
        state_manager.save_project_state = AsyncMock()
        state_manager.load_project_state = Mock(return_value=Mock())
        return DesignWorkflow(cli, analyzer, state_manager)

    @pytest.mark.asyncio
    async def test_end_to_end_design_workflow(self, integration_workflow):
        """Test complete end-to-end design workflow."""
        # Create a comprehensive specification
        requirements = [
            Requirement(
                id="FR-1",
                user_story="As a user, I want data management, so that I can store information",
                acceptance_criteria=["WHEN I save data THEN it SHALL be stored"],
                priority=Priority.HIGH,
            ),
            Requirement(
                id="FR-2",
                user_story="As a user, I want authentication, so that my data is secure",
                acceptance_criteria=[
                    "WHEN I login THEN my credentials SHALL be verified"
                ],
                priority=Priority.HIGH,
            ),
        ]

        spec = SpecificationDocument(
            introduction="Comprehensive test application",
            key_features=["Data Management", "Authentication", "API Access"],
            functional_requirements=requirements,
            source=SpecificationSource.USER_INPUT,
            version="1.0",
            approved=True,
        )

        # Mock approval to return True immediately
        def mock_approval(design):
            design.approved = True
            return True

        with patch.object(
            integration_workflow.generator,
            "request_user_approval",
            side_effect=mock_approval,
        ):
            design = await integration_workflow.execute_design_phase(spec)

        # Verify the design was generated properly
        assert isinstance(design, DesignDocument)
        assert design.approved
        assert design.overview is not None
        assert design.architecture is not None
        assert design.error_handling is not None
        assert design.testing_strategy is not None

        # Verify workflow interactions
        integration_workflow.codebase_analyzer.analyze_for_design.assert_called_once()
        integration_workflow.state_manager.save_document.assert_awaited_once()
        integration_workflow.state_manager.save_project_state.assert_awaited_once()

        # Verify metrics
        metrics = integration_workflow.get_design_metrics(design)
        assert metrics["approved"] is True
        assert "component_count" in metrics
        assert "test_coverage_target" in metrics
