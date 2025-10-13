"""Workflow integration for design generation phase."""

from ..generation.design_generator import DesignGenerator
from ..interfaces.analysis_interface import ICodebaseAnalyzer
from ..interfaces.cli_interface import ICLIInterface
from ..models.analysis import DesignAnalysis
from ..models.documents import DesignDocument, SpecificationDocument
from ..models.enums import DocumentType
from ..state.state_manager import StateManager


class DesignWorkflow:
    """Manages the design generation workflow phase."""

    def __init__(
        self,
        cli_interface: ICLIInterface,
        codebase_analyzer: ICodebaseAnalyzer,
        state_manager: StateManager | None = None,
    ):
        """Initialize the design workflow.

        Args:
            cli_interface: CLI interface for user interaction
            codebase_analyzer: Codebase analyzer for architecture analysis
            state_manager: Optional state manager for persistence
        """
        self.cli_interface = cli_interface
        self.codebase_analyzer = codebase_analyzer
        self.state_manager = state_manager
        self.generator = DesignGenerator(codebase_analyzer, cli_interface)

    async def execute_design_phase(
        self, specification: SpecificationDocument
    ) -> DesignDocument:
        """Execute the design generation phase.

        Args:
            specification: Approved specification document

        Returns:
            Approved design document
        """
        self.cli_interface.display_message("Starting design generation phase...")

        # Perform design analysis
        design_analysis = self._perform_design_analysis()

        # Generate design document
        design = self._generate_design_document(specification, design_analysis)

        # Request approval and handle refinements
        design = await self._approval_workflow(design)

        # Save the design
        if self.state_manager:
            await self._save_design(design)

        self.cli_interface.display_message("Design phase completed successfully!")
        return design

    def _perform_design_analysis(self) -> DesignAnalysis:
        """Perform design analysis using the codebase analyzer.

        Returns:
            Design analysis results
        """
        self.cli_interface.display_message(
            "Analyzing codebase architecture and design patterns..."
        )

        try:
            analysis = self.codebase_analyzer.analyze_for_design()

            self.cli_interface.display_message(
                f"Design analysis complete. Found {len(analysis.components)} components, "
                f"{len(analysis.design_patterns)} design patterns, and "
                f"{len(analysis.data_models)} data models."
            )

            if analysis.recommendations:
                self.cli_interface.display_message(
                    f"Analysis includes {len(analysis.recommendations)} recommendations for improvement."
                )

            return analysis

        except Exception as e:
            self.cli_interface.display_message(f"Warning: Design analysis failed: {e}")
            # Return empty analysis to allow design generation to continue
            return DesignAnalysis(
                architecture_overview="Unable to analyze existing architecture",
                components=[],
                data_models=[],
                api_interfaces=[],
                design_patterns=[],
                quality_metrics={},
                technical_debt=[],
                recommendations=[],
            )

    def _generate_design_document(
        self, specification: SpecificationDocument, analysis: DesignAnalysis
    ) -> DesignDocument:
        """Generate design document from specification and analysis.

        Args:
            specification: Specification document
            analysis: Design analysis results

        Returns:
            Generated design document
        """
        self.cli_interface.display_message("Generating design document...")

        design = self.generator.generate_from_specification(specification, analysis)

        self.cli_interface.display_message(
            f"Design document generated with {len(design.components)} components, "
            f"{len(design.data_models)} data models, and "
            f"{len(design.interfaces)} interfaces."
        )

        return design

    async def _approval_workflow(self, design: DesignDocument) -> DesignDocument:
        """Handle the approval workflow with potential refinements.

        Args:
            design: Initial design document

        Returns:
            Final approved design document
        """
        current_design = design
        max_iterations = 3
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Display design summary
            self._display_design_summary(current_design)

            # Request user approval
            approved = self.generator.request_user_approval(current_design)

            if approved:
                self.cli_interface.display_message("Design approved!")
                return current_design

            # Get feedback for refinement
            if iteration < max_iterations:
                feedback = self.cli_interface.get_user_input(
                    "Please provide feedback for improving the design: "
                )

                if feedback.strip():
                    self.cli_interface.display_message(
                        "Refining design based on your feedback..."
                    )
                    current_design = await self.generator.refine_design(
                        current_design, feedback
                    )
                    self.cli_interface.display_message(
                        f"Design refined to version {current_design.version}"
                    )
                else:
                    self.cli_interface.display_message(
                        "No feedback provided. Using current design."
                    )
                    current_design.approved = True
                    return current_design
            else:
                self.cli_interface.display_message(
                    "Maximum refinement iterations reached. Using current design."
                )
                current_design.approved = True
                return current_design

        return current_design

    def _display_design_summary(self, design: DesignDocument) -> None:
        """Display a summary of the design document.

        Args:
            design: Design document to summarize
        """
        self.cli_interface.display_message("\n=== Design Summary ===")
        self.cli_interface.display_message(f"Version: {design.version}")
        self.cli_interface.display_message(f"Components: {len(design.components)}")
        self.cli_interface.display_message(f"Data Models: {len(design.data_models)}")
        self.cli_interface.display_message(f"Interfaces: {len(design.interfaces)}")

        if design.architecture.patterns:
            patterns = ", ".join(design.architecture.patterns[:3])
            self.cli_interface.display_message(f"Design Patterns: {patterns}")

        if design.components:
            component_names = [c.name for c in design.components[:3]]
            self.cli_interface.display_message(
                f"Main Components: {', '.join(component_names)}"
            )

        self.cli_interface.display_message("=====================\n")

    async def _save_design(self, design: DesignDocument) -> None:
        """Save the design document.

        Args:
            design: Design document to save
        """
        try:
            # Format the design as markdown
            formatted_design = self.generator.format_design_document(design)

            # Save using state manager
            state = self.state_manager.load_project_state()
            if state:
                state.design_document = design
                await self.state_manager.save_project_state(state)

            await self.state_manager.save_document(formatted_design, DocumentType.DESIGN)

            self.cli_interface.display_message("Design saved to DESIGN.md")

        except Exception as e:
            self.cli_interface.display_message(f"Warning: Could not save design: {e}")

    def validate_specification_input(
        self, specification: SpecificationDocument
    ) -> bool:
        """Validate that the specification is suitable for design generation.

        Args:
            specification: Specification document to validate

        Returns:
            True if specification is valid, False otherwise
        """
        if not specification:
            self.cli_interface.display_message("Error: No specification provided")
            return False

        if not specification.approved:
            self.cli_interface.display_message(
                "Error: Specification must be approved before design generation"
            )
            return False

        if not specification.functional_requirements:
            self.cli_interface.display_message(
                "Error: Specification must contain functional requirements"
            )
            return False

        return True

    def get_design_metrics(self, design: DesignDocument) -> dict:
        """Get metrics about the generated design.

        Args:
            design: Design document to analyze

        Returns:
            Dictionary of design metrics
        """
        return {
            "version": design.version,
            "component_count": len(design.components),
            "data_model_count": len(design.data_models),
            "interface_count": len(design.interfaces),
            "pattern_count": len(design.architecture.patterns),
            "error_category_count": len(design.error_handling.error_categories),
            "test_coverage_target": design.testing_strategy.test_coverage_target,
            "approved": design.approved,
        }


class DesignWorkflowResult:
    """Result of design workflow execution."""

    def __init__(
        self,
        design: DesignDocument,
        success: bool,
        message: str = "",
        metrics: dict | None = None,
    ):
        """Initialize the result.

        Args:
            design: Generated design document
            success: Whether the workflow completed successfully
            message: Optional message about the result
            metrics: Optional metrics about the design
        """
        self.design = design
        self.success = success
        self.message = message
        self.metrics = metrics or {}
