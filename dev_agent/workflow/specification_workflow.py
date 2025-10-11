"""Workflow integration for specification generation phase."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from rich.panel import Panel

from ..generation.specification_generator import SpecificationGenerator
from ..interfaces.analysis_interface import ICodebaseAnalyzer
from ..interfaces.cli_interface import ICLIInterface
from ..llm import create_llm_client, get_preferred_provider
from ..models.documents import SpecificationDocument
from ..models.enums import DocumentType, LLMProvider
from ..state.state_manager import StateManager

if TYPE_CHECKING:
    from ..indexing.vector_database import VectorDatabase
    from ..llm.base import ILLMClient
    from ..llm.cost_tracker import CostTracker
    from ..llm.token_counter import TokenCounter

logger = logging.getLogger(__name__)


class SpecificationWorkflow:
    """Manages the specification generation workflow phase.

    This workflow orchestrates the specification generation process, integrating
    with Azure OpenAI for AI-powered specification generation and refinement.
    """

    def __init__(
        self,
        cli_interface: ICLIInterface,
        codebase_analyzer: ICodebaseAnalyzer | None = None,
        state_manager: StateManager | None = None,
        llm_client: ILLMClient | None = None,
        cost_tracker: CostTracker | None = None,
        token_counter: TokenCounter | None = None,
        vector_db: VectorDatabase | None = None,
        provider: LLMProvider | str | None = None,
    ):
        """Initialize the specification workflow.

        Args:
            cli_interface: CLI interface for user interaction
            codebase_analyzer: Optional codebase analyzer for existing projects
            state_manager: Optional state manager for persistence
            llm_client: LLM client for AI-powered generation (optional for backward compatibility)
            cost_tracker: Cost tracker for monitoring API usage
            token_counter: Token counter for validation
            vector_db: Vector database for context retrieval
            provider: LLM provider to use (optional, defaults to preferred provider)
        """
        self.cli_interface = cli_interface
        self.codebase_analyzer = codebase_analyzer
        self.state_manager = state_manager
        self.cost_tracker = cost_tracker
        self.token_counter = token_counter
        self.vector_db = vector_db

        # Initialize LLM client using factory pattern
        if llm_client is not None:
            # Use provided client for backward compatibility
            self.llm_client = llm_client
            logger.info("SpecificationWorkflow initialized with provided LLM client")
        else:
            # Create client using factory pattern
            try:
                self.llm_client = create_llm_client(provider=provider)
                current_provider = get_preferred_provider()
                logger.info(f"SpecificationWorkflow initialized with {current_provider.value} LLM client")
            except (ValueError, ImportError) as e:
                logger.warning(f"Failed to create LLM client: {e}")
                self.llm_client = None
                logger.warning("SpecificationWorkflow initialized without LLM client")

        # Initialize generator with all components
        self.generator = SpecificationGenerator(
            cli_interface=cli_interface,
            llm_client=self.llm_client,
            cost_tracker=cost_tracker,
            token_counter=token_counter,
            vector_db=vector_db,
            provider=provider,
        )

    async def execute_specification_phase(
        self, project_path: str
    ) -> SpecificationDocument:
        """Execute the specification generation phase.

        Args:
            project_path: Path to the project directory

        Returns:
            Approved specification document

        Raises:
            ValueError: If LLM client is not configured
        """
        # Check LLM client availability
        if not self.llm_client:
            self.cli_interface.display_message(
                Panel(
                    "[red]Azure OpenAI is not configured.[/red]\n\n"
                    "The specification phase requires Azure OpenAI for AI-powered generation.\n\n"
                    "[yellow]To configure Azure OpenAI:[/yellow]\n"
                    "  1. Run: [cyan]dev-agent azure configure[/cyan]\n"
                    "  2. Or set environment variables:\n"
                    "     [cyan]AZURE_OPENAI_ENDPOINT[/cyan]\n"
                    "     [cyan]AZURE_OPENAI_API_KEY[/cyan]\n"
                    "     [cyan]AZURE_OPENAI_DEPLOYMENT_NAME[/cyan]\n"
                    "     [cyan]AZURE_OPENAI_EMBEDDING_DEPLOYMENT[/cyan]\n\n"
                    "[dim]See documentation: docs/configuration/azure-openai.md[/dim]",
                    title="❌ Configuration Required",
                    border_style="red",
                )
            )
            raise ValueError("LLM client required for specification generation")

        self.cli_interface.display_message("Starting specification generation phase...")

        # Prompt user for feature description
        feature_description = self._get_feature_description()

        # Determine if this is an existing codebase or new project
        if self.codebase_analyzer and self._has_existing_code(project_path):
            spec = await self._generate_from_existing_code(feature_description)
        else:
            spec = await self._generate_from_user_input(feature_description)

        # Request approval and handle refinements
        spec = await self._approval_workflow_ai(spec, feature_description)

        # Save the specification
        if self.state_manager:
            await self._save_specification(spec)

        self.cli_interface.display_message(
            "Specification phase completed successfully!"
        )
        return spec

    def _get_feature_description(self) -> str:
        """Prompt user for feature description with validation.

        Returns:
            Feature description provided by user

        Raises:
            ValueError: If user provides empty description after multiple attempts
        """
        max_attempts = 3
        attempt = 0

        # Display helpful instructions
        self.cli_interface.display_message(
            Panel(
                "[cyan]Please describe the feature you want to build.[/cyan]\n\n"
                "[yellow]Tips for a good description:[/yellow]\n"
                "  • Be specific about what the feature should do\n"
                "  • Include key requirements and constraints\n"
                "  • Mention any integration points or dependencies\n"
                "  • Describe the expected user experience\n\n"
                "[dim]Example: 'Add user authentication with JWT tokens, "
                "including login, logout, and password reset functionality. "
                "Should integrate with existing user database.'[/dim]",
                title="📝 Feature Description",
                border_style="cyan",
            )
        )

        while attempt < max_attempts:
            attempt += 1

            feature_description = self.cli_interface.get_user_input(
                "\nDescribe your feature: "
            )

            # Validate not empty
            if not feature_description.strip():
                if attempt < max_attempts:
                    remaining = max_attempts - attempt
                    self.cli_interface.display_message(
                        f"❌ Feature description cannot be empty. "
                        f"Please provide a description. ({remaining} attempts remaining)"
                    )
                else:
                    self.cli_interface.display_message(
                        "❌ Feature description is required. Cannot proceed without it."
                    )
                    raise ValueError("Feature description cannot be empty")
                continue

            # Validate minimum length (at least 10 characters)
            if len(feature_description.strip()) < 10:
                if attempt < max_attempts:
                    remaining = max_attempts - attempt
                    self.cli_interface.display_message(
                        f"❌ Feature description is too short. "
                        f"Please provide more details. ({remaining} attempts remaining)"
                    )
                else:
                    self.cli_interface.display_message(
                        "❌ Feature description must be at least 10 characters. Cannot proceed."
                    )
                    raise ValueError("Feature description is too short")
                continue

            # Valid description
            return feature_description.strip()

        raise ValueError("Feature description validation failed")

    async def _generate_from_existing_code(
        self, feature_description: str
    ) -> SpecificationDocument:
        """Generate specification from existing codebase analysis using AI.

        Args:
            feature_description: Description of the feature to build

        Returns:
            Generated specification document
        """
        self.cli_interface.display_message("Analyzing existing codebase...")

        # Perform codebase analysis
        analysis = self.codebase_analyzer.analyze_for_specification()

        self.cli_interface.display_message(
            f"Analysis complete with {analysis.confidence_score:.0%} confidence. "
            f"Found {len(analysis.main_features)} main features and "
            f"{len(analysis.requirement_evidence)} requirement areas."
        )

        # Generate specification from analysis using AI
        self.cli_interface.display_message(
            "🤖 Generating specification using AI... This may take a moment."
        )
        spec = await self.generator.generate_from_existing_code_ai(
            analysis=analysis,
            feature_description=feature_description,
        )

        # Display cost information if available
        if self.cost_tracker:
            report = self.cost_tracker.get_report()
            self.cli_interface.display_message(
                f"💰 Generation complete! API Usage: {report.total_tokens} tokens "
                f"(~${report.total_cost:.4f})"
            )
        else:
            self.cli_interface.display_message("✅ Specification generated successfully!")

        # Validate the generated specification
        is_valid, validation_issues = self.generator._validate_specification(spec)
        req_count = len(spec.functional_requirements)
        
        if req_count > 0:
            self.cli_interface.display_message(
                f"📋 Generated {req_count} requirement{'s' if req_count != 1 else ''}"
            )
        else:
            self.cli_interface.display_message(
                "⚠️ Warning: No requirements were generated. The specification may be incomplete."
            )
        
        # Display validation warnings if specification has issues
        if not is_valid and req_count < 3:
            self.cli_interface.display_message(
                Panel(
                    f"[yellow]Warning: Only {req_count} requirement(s) generated.[/yellow]\n\n"
                    "A complete specification typically has 3-5 requirements.\n"
                    "You may want to regenerate or provide more detailed feedback.",
                    title="⚠️ Incomplete Specification",
                    border_style="yellow",
                )
            )
        elif not is_valid:
            # Show other validation issues
            issues_text = "\n".join(f"• {issue}" for issue in validation_issues[:3])
            if len(validation_issues) > 3:
                issues_text += f"\n• ... and {len(validation_issues) - 3} more issues"
            
            self.cli_interface.display_message(
                Panel(
                    f"[yellow]Specification validation found some issues:[/yellow]\n\n{issues_text}\n\n"
                    "You can still proceed, but consider regenerating for better quality.",
                    title="⚠️ Specification Quality Issues",
                    border_style="yellow",
                )
            )

        return spec

    async def _generate_from_user_input(
        self, feature_description: str
    ) -> SpecificationDocument:
        """Generate specification from user input using AI.

        Args:
            feature_description: Description of the feature to build

        Returns:
            Generated specification document
        """
        self.cli_interface.display_message(
            "No existing codebase detected. "
            "Let's create a specification from your requirements."
        )

        # Generate specification from user input using AI
        self.cli_interface.display_message(
            "🤖 Generating specification using AI... This may take a moment."
        )
        spec = await self.generator.generate_from_user_input_ai(
            feature_description=feature_description,
        )

        # Display cost information if available
        if self.cost_tracker:
            report = self.cost_tracker.get_report()
            self.cli_interface.display_message(
                f"💰 Generation complete! API Usage: {report.total_tokens} tokens "
                f"(~${report.total_cost:.4f})"
            )
        else:
            self.cli_interface.display_message("✅ Specification generated successfully!")

        # Validate the generated specification
        is_valid, validation_issues = self.generator._validate_specification(spec)
        req_count = len(spec.functional_requirements)
        
        if req_count > 0:
            self.cli_interface.display_message(
                f"📋 Generated {req_count} requirement{'s' if req_count != 1 else ''}"
            )
        else:
            self.cli_interface.display_message(
                "⚠️ Warning: No requirements were generated. The specification may be incomplete."
            )
        
        # Display validation warnings if specification has issues
        if not is_valid and req_count < 3:
            self.cli_interface.display_message(
                Panel(
                    f"[yellow]Warning: Only {req_count} requirement(s) generated.[/yellow]\n\n"
                    "A complete specification typically has 3-5 requirements.\n"
                    "You may want to regenerate or provide more detailed feedback.",
                    title="⚠️ Incomplete Specification",
                    border_style="yellow",
                )
            )
        elif not is_valid:
            # Show other validation issues
            issues_text = "\n".join(f"• {issue}" for issue in validation_issues[:3])
            if len(validation_issues) > 3:
                issues_text += f"\n• ... and {len(validation_issues) - 3} more issues"
            
            self.cli_interface.display_message(
                Panel(
                    f"[yellow]Specification validation found some issues:[/yellow]\n\n{issues_text}\n\n"
                    "You can still proceed, but consider regenerating for better quality.",
                    title="⚠️ Specification Quality Issues",
                    border_style="yellow",
                )
            )

        return spec

    async def _approval_workflow_ai(
        self,
        spec: SpecificationDocument,
        feature_description: str,
    ) -> SpecificationDocument:
        """Handle the approval workflow with AI-powered refinements.

        Args:
            spec: Initial specification document
            feature_description: Original feature description from user

        Returns:
            Final approved specification document
        """
        current_spec = spec
        max_iterations = 3
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Request user approval
            approved = self.generator.request_user_approval(current_spec)

            if approved:
                self.cli_interface.display_message("✅ Specification approved!")
                return current_spec

            # Get feedback for refinement
            if iteration < max_iterations:
                # Display helpful instructions for feedback
                self.cli_interface.display_message(
                    Panel(
                        "[cyan]Please provide specific feedback to improve the specification.[/cyan]\n\n"
                        "[yellow]Good feedback examples:[/yellow]\n"
                        "  • 'Add error handling requirements'\n"
                        "  • 'Include performance criteria'\n"
                        "  • 'Clarify the authentication flow'\n"
                        "  • 'Add more details about data validation'\n\n"
                        "[dim]Press Enter without typing to approve the current specification.[/dim]",
                        title="💬 Feedback",
                        border_style="cyan",
                    )
                )

                feedback = self.cli_interface.get_user_input(
                    "\nYour feedback (or press Enter to approve): "
                )

                # Validate feedback
                if feedback.strip():
                    # Check minimum length for meaningful feedback
                    if len(feedback.strip()) < 5:
                        self.cli_interface.display_message(
                            "⚠️ Feedback is too short. Please provide more specific feedback "
                            "or press Enter to approve the current specification."
                        )
                        continue

                    self.cli_interface.display_message(
                        "🤖 Refining specification using AI based on your feedback... This may take a moment."
                    )

                    # Use AI to refine specification
                    current_spec = await self.generator.refine_specification_ai(
                        spec=current_spec,
                        feedback=feedback,
                        feature_description=feature_description,
                    )

                    # Display cost information if available
                    if self.cost_tracker:
                        report = self.cost_tracker.get_report()
                        self.cli_interface.display_message(
                            f"💰 Refinement complete! Total API Usage: {report.total_tokens} tokens "
                            f"(~${report.total_cost:.4f})"
                        )
                    else:
                        self.cli_interface.display_message("✅ Specification refined successfully!")
                else:
                    self.cli_interface.display_message(
                        "✅ No feedback provided. Approving current specification."
                    )
                    current_spec.approved = True
                    return current_spec
            else:
                self.cli_interface.display_message(
                    "Maximum refinement iterations reached. "
                    "Using current specification."
                )
                current_spec.approved = True
                return current_spec

        return current_spec

    def _approval_workflow(self, spec: SpecificationDocument) -> SpecificationDocument:
        """Handle the approval workflow with potential refinements.

        Args:
            spec: Initial specification document

        Returns:
            Final approved specification document
        """
        current_spec = spec
        max_iterations = 3
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Request user approval
            approved = self.generator.request_user_approval(current_spec)

            if approved:
                self.cli_interface.display_message("Specification approved!")
                return current_spec

            # Get feedback for refinement
            if iteration < max_iterations:
                feedback = self.cli_interface.get_user_input(
                    "Please provide feedback for improving the specification: "
                )

                if feedback.strip():
                    self.cli_interface.display_message(
                        "Refining specification based on your feedback..."
                    )
                    current_spec = self.generator.refine_specification(
                        current_spec, feedback
                    )
                else:
                    self.cli_interface.display_message(
                        "No feedback provided. Using current specification."
                    )
                    current_spec.approved = True
                    return current_spec
            else:
                self.cli_interface.display_message(
                    "Maximum refinement iterations reached. "
                    "Using current specification."
                )
                current_spec.approved = True
                return current_spec

        return current_spec

    def _has_existing_code(self, project_path: str) -> bool:
        """Check if the project has existing code to analyze.

        Args:
            project_path: Path to the project directory

        Returns:
            True if existing code is found, False otherwise
        """

        project_dir = Path(project_path)

        # Look for common code file extensions
        code_extensions = {
            ".py",
            ".js",
            ".ts",
            ".java",
            ".cpp",
            ".c",
            ".cs",
            ".rb",
            ".go",
            ".rs",
        }

        for file_path in project_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in code_extensions:
                # Skip common non-source directories
                if any(
                    part.startswith(".")
                    or part in ["node_modules", "__pycache__", "build", "dist"]
                    for part in file_path.parts
                ):
                    continue
                return True

        return False

    async def _save_specification(self, spec: SpecificationDocument) -> None:
        """Save the specification document.

        Args:
            spec: Specification document to save
        """
        try:
            # Format the specification as markdown
            formatted_spec = self.generator.format_specification_document(spec)

            # Save using state manager
            await self.state_manager.save_document(
                formatted_spec, DocumentType.SPECIFICATION
            )

            # Update project state with approved specification
            project_state = self.state_manager.load_project_state()
            if project_state:
                project_state.specification = spec
                await self.state_manager.save_project_state(project_state)

            # Get the full path for display
            spec_path = self.state_manager.documents_dir / "SPECIFICATION.md"
            relative_path = (
                spec_path.relative_to(Path.cwd())
                if spec_path.is_relative_to(Path.cwd())
                else spec_path
            )

            self.cli_interface.display_message(
                f"Specification saved to {relative_path}"
            )

        except Exception as e:
            self.cli_interface.display_message(
                f"Warning: Could not save specification: {e}"
            )


class SpecificationWorkflowResult:
    """Result of specification workflow execution."""

    def __init__(
        self, specification: SpecificationDocument, success: bool, message: str = ""
    ):
        """Initialize the result.

        Args:
            specification: Generated specification document
            success: Whether the workflow completed successfully
            message: Optional message about the result
        """
        self.specification = specification
        self.success = success
        self.message = message
