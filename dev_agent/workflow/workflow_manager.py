"""Workflow orchestration system that coordinates all four phases."""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from ..analysis.framework_detector import FrameworkDetector
from ..analysis.language_detector import LanguageDetector
from ..config.config_manager import ConfigManager
from ..errors.exceptions import DocumentSaveError, ErrorContext
from ..interfaces.cli_interface import ICLIInterface
from ..interfaces.workflow_interface import IWorkflowManager
from ..llm.cost_tracker import CostTracker
from ..models.context import ProjectContext
from ..models.enums import PhaseStatus, PhaseType
from ..models.project_state import ProjectState
from ..models.results import PhaseResult
from ..models.undo_redo import ActionType, SnapshotType
from ..state.state_manager import StateManager
from ..state.undo_redo_manager import UndoRedoManager
from .phase_manager import PhaseManager

logger = logging.getLogger(__name__)


class WorkflowManager(IWorkflowManager):
    """Orchestrates the complete four-phase development workflow."""

    def __init__(
        self,
        cli_interface: ICLIInterface,
        cost_tracker: CostTracker | None = None,
        budget_threshold: float | None = None,
        budget_limit: float | None = None,
        embedding_client: Any | None = None,
    ):
        """Initialize the workflow manager.

        Args:
            cli_interface: CLI interface for user interaction
            cost_tracker: Optional cost tracker instance (created if not provided)
            budget_threshold: Budget threshold for warnings in USD
            budget_limit: Hard budget limit in USD
            embedding_client: Optional embedding client for indexing and vector search
        """
        self.cli_interface = cli_interface
        self.state_manager: StateManager | None = None
        self.phase_manager: PhaseManager | None = None
        self.undo_redo_manager: UndoRedoManager | None = None
        self.current_project_state: ProjectState | None = None
        self.error_handler = WorkflowErrorHandler(cli_interface)
        self.embedding_client = embedding_client

        # Initialize cost tracker
        self.cost_tracker = cost_tracker or CostTracker(
            current_phase=PhaseType.INDEXING,
            budget_threshold=budget_threshold,
            budget_limit=budget_limit,
        )

        # Initialize LLM components
        self.llm_client: Any | None = None
        self.token_counter: Any | None = None
        self.vector_db: Any | None = None

        # Initialize language and framework detection
        self.language_detector = LanguageDetector()
        self.framework_detector = FrameworkDetector()

        self._initialize_llm_components()

        # Workflow configuration
        self.max_retry_attempts = 3
        self.require_explicit_approval = True

    def _initialize_llm_components(self) -> None:
        """Initialize LLM client, token counter, and vector database.

        This method detects the configured LLM provider and initializes
        the necessary components for AI-powered specification generation.
        Supports both Azure OpenAI and Google Gemini providers.
        """
        try:
            # Load configuration and detect provider
            config_manager = ConfigManager()

            # Get the preferred LLM provider
            try:
                provider = config_manager.get_llm_provider()
                logger.info(f"Detected LLM provider: {provider.value}")
            except ValueError as e:
                logger.info(f"No valid LLM provider configured: {e}")
                self.llm_client = None
                self.token_counter = None
                self.vector_db = None
                return

            # Import LLM factory functions (lazy import to avoid circular dependencies)
            from ..llm import create_llm_client
            from ..llm.token_counter import TokenCounter

            # Initialize LLM client using factory function
            self.llm_client = create_llm_client(provider=provider)
            logger.info(f"Initialized {provider.value} LLM client")

            # Initialize token counter with appropriate model
            if provider.value == "azure_openai":
                config = config_manager.get_config()
                model_name = config.azure_openai.deployment_name
            elif provider.value == "gemini":
                config = config_manager.get_config()
                model_name = config.gemini.model_name if config.gemini else "gemini-pro"
            else:
                model_name = "default"

            self.token_counter = TokenCounter(model=model_name)
            logger.info(f"Initialized token counter for model: {model_name}")

            # Vector database will be initialized when state_manager is available
            # (needs project path for index storage)
            self.vector_db = None

        except Exception as e:
            logger.warning(f"Failed to initialize LLM components: {e}")
            self.llm_client = None
            self.token_counter = None
            self.vector_db = None

    def _initialize_vector_database(self, project_path: str) -> None:
        """Initialize vector database for semantic code search.

        This method initializes the VectorDatabase with the project-specific
        index path. It creates an embedding client based on the configured provider.

        Args:
            project_path: Path to the project directory
        """
        try:
            # Create embedding client if not provided
            if self.embedding_client is None:
                try:
                    # Load configuration and detect provider
                    config_manager = ConfigManager()
                    provider = config_manager.get_llm_provider()

                    # Import embedding factory function
                    from ..llm import create_embedding_client

                    # Create embedding client with cache in index directory
                    cache_dir = Path(project_path) / ".dev_agent" / "index" / "embedding_cache"
                    self.embedding_client = create_embedding_client(
                        provider=provider, cache_dir=cache_dir
                    )
                    logger.info(f"Created {provider.value} embedding client")

                except Exception as e:
                    logger.warning(f"Failed to create embedding client: {e}")
                    self.vector_db = None
                    return

            # Import VectorDatabase (lazy import)
            from ..indexing.vector_database import VectorDatabase

            # Create index path
            index_path = Path(project_path) / ".dev_agent" / "index"

            # Initialize vector database
            self.vector_db = VectorDatabase(
                index_path=str(index_path),
                embedding_client=self.embedding_client,
            )
            logger.info(f"Initialized vector database at {index_path}")

        except Exception as e:
            logger.warning(f"Failed to initialize vector database: {e}")
            self.vector_db = None

    async def _detect_and_store_project_context(self, project_state: ProjectState, project_path: Path) -> None:
        """Detect and store language and framework context in project state.
        
        Args:
            project_state: Project state to update
            project_path: Path to the project directory
        """
        try:
            self.cli_interface.display_message("Analyzing project language and frameworks...")
            
            # Detect primary language
            primary_language = self.language_detector.detect_primary_language(project_path)
            logger.info(f"Detected primary language: {primary_language.value}")
            
            # Detect frameworks
            detected_frameworks = self.framework_detector.detect_frameworks(project_path, primary_language)
            logger.info(f"Detected frameworks: {[f.value for f in detected_frameworks]}")
            
            # Get comprehensive project context
            language_context = self.language_detector.analyze_project_context(project_path)
            language_context.detected_frameworks = detected_frameworks
            
            # Get framework patterns for detected frameworks
            framework_patterns = []
            for framework in detected_frameworks:
                try:
                    patterns = self.framework_detector.get_framework_patterns(framework)
                    framework_patterns.append(patterns)
                except ValueError:
                    logger.warning(f"No patterns available for framework: {framework.value}")
            
            language_context.framework_patterns = framework_patterns
            
            # Store in project state
            project_state.language_context = language_context
            project_state.primary_language = primary_language
            project_state.detected_frameworks = detected_frameworks
            
            # Display results to user
            self.cli_interface.display_message(f"✓ Primary language: {primary_language.value}")
            if detected_frameworks:
                frameworks_str = ", ".join([f.value for f in detected_frameworks])
                self.cli_interface.display_message(f"✓ Detected frameworks: {frameworks_str}")
            else:
                self.cli_interface.display_message("✓ No specific frameworks detected")
            
            if language_context.package_manager:
                self.cli_interface.display_message(f"✓ Package manager: {language_context.package_manager}")
            
        except Exception as e:
            logger.error(f"Failed to detect project context: {e}")
            # Continue without language context - don't fail project initialization
            self.cli_interface.display_message(f"Warning: Could not analyze project context: {e}")

    async def start_new_project(self, project_path: str) -> ProjectState:
        """Start a new project workflow.

        Args:
            project_path: Path to the project directory

        Returns:
            Initial project state
        """
        try:
            self.cli_interface.display_message(
                f"Initializing new project at: {project_path}"
            )

            # Initialize state manager
            self.state_manager = StateManager(project_path)

            # Initialize undo/redo manager
            self.undo_redo_manager = UndoRedoManager(project_path)

            # Create initial project state
            session_id = str(uuid.uuid4())
            project_state = self.state_manager.create_initial_state(
                project_path, session_id
            )

            # Perform language and framework detection
            await self._detect_and_store_project_context(project_state, Path(project_path))

            # Save initial state first
            if not await self.state_manager.save_project_state(project_state):
                raise Exception("Failed to save initial project state")

            self.current_project_state = project_state

            # Create initial snapshot
            self.undo_redo_manager.create_snapshot(
                project_state,
                SnapshotType.AUTOMATIC,
                "Initial project state",
                {
                    "phase": project_state.current_phase,
                    "action": "project_initialization",
                },
            )

            # Initialize vector database now that we have project path
            self._initialize_vector_database(project_path)

            # Initialize phase manager after state is set
            self.phase_manager = PhaseManager(
                cli_interface=self.cli_interface,
                state_manager=self.state_manager,
                embedding_client=self.embedding_client,
                cost_tracker=self.cost_tracker,
                llm_client=self.llm_client,
                token_counter=self.token_counter,
                vector_db=self.vector_db,
            )

            self.cli_interface.display_message("Project initialized successfully!")
            self.cli_interface.display_message(
                f"Starting with {project_state.current_phase.value} phase"
            )

            # Check if there are code files to index and automatically run indexing
            logger.info("Checking for code files to automatically index...")
            
            try:
                from ..onboarding.journey_manager import JourneyManager
                from pathlib import Path
                
                journey_manager = JourneyManager()
                project_context = journey_manager.detect_project_type(Path(project_path))
                
                logger.info(f"Project context: has_code={project_context.has_code}, file_count={project_context.file_count}")
                
                # If there are code files, automatically run indexing
                if project_context.has_code and project_context.file_count > 0:
                    logger.info(f"Detected {project_context.file_count} code files, starting automatic indexing...")
                    
                    try:
                        # Run indexing phase
                        indexing_result = await self.phase_manager.execute_indexing_phase(project_path)
                        
                        if indexing_result.status == PhaseStatus.COMPLETED:
                            logger.info("Automatic indexing completed successfully")
                            # Update project state to specification phase
                            project_state.current_phase = PhaseType.SPECIFICATION
                            project_state.last_updated = datetime.now()
                            await self.state_manager.save_project_state(project_state)
                        else:
                            logger.warning(f"Indexing completed with status {indexing_result.status}: {indexing_result.message}")
                            
                    except Exception as e:
                        logger.error(f"Automatic indexing failed: {e}")
                        # Continue with project initialization even if indexing fails
                else:
                    logger.info("No code files detected, skipping automatic indexing")
                    
            except Exception as e:
                logger.error(f"Failed to check for code files: {e}")
                logger.info("Continuing with project initialization without automatic indexing")

            return project_state

        except Exception as e:
            error_msg = f"Failed to start new project: {e}"
            self.cli_interface.display_message(f"Error: {error_msg}")
            raise WorkflowException(error_msg) from e

    async def resume_project(self, project_path: str) -> ProjectState:
        """Resume an existing project workflow.

        Args:
            project_path: Path to the project directory

        Returns:
            Loaded project state
        """
        try:
            self.cli_interface.display_message(f"Resuming project at: {project_path}")

            # Initialize state manager
            self.state_manager = StateManager(project_path)

            # Initialize undo/redo manager
            self.undo_redo_manager = UndoRedoManager(project_path)

            # Load existing project state
            project_state = self.state_manager.load_project_state()
            if not project_state:
                raise Exception(
                    "No existing project state found. Use start_new_project instead."
                )

            # Update session data
            project_state.session_data.last_activity = datetime.now()
            
            # Detect language context if not already present
            if not project_state.language_context:
                await self._detect_and_store_project_context(project_state, Path(project_path))
            
            await self.state_manager.save_project_state(project_state)

            self.current_project_state = project_state

            # Create resume snapshot
            self.undo_redo_manager.create_snapshot(
                project_state,
                SnapshotType.AUTOMATIC,
                f"Project resumed in {project_state.current_phase.value} phase",
                {"phase": project_state.current_phase, "action": "project_resume"},
            )

            # Initialize vector database now that we have project path
            self._initialize_vector_database(project_path)

            # Initialize phase manager after state is set
            self.phase_manager = PhaseManager(
                cli_interface=self.cli_interface,
                state_manager=self.state_manager,
                embedding_client=self.embedding_client,
                cost_tracker=self.cost_tracker,
                llm_client=self.llm_client,
                token_counter=self.token_counter,
                vector_db=self.vector_db,
            )

            self.cli_interface.display_message("Project resumed successfully!")
            self.cli_interface.display_message(
                f"Current phase: {project_state.current_phase.value}"
            )

            # Display progress summary
            self._display_progress_summary(project_state)

            return project_state

        except Exception as e:
            error_msg = f"Failed to resume project: {e}"
            self.cli_interface.display_message(f"Error: {error_msg}")
            raise WorkflowException(error_msg) from e

    async def transition_to_phase(self, phase: PhaseType) -> bool:
        """Transition to the specified phase.

        Args:
            phase: Target phase to transition to

        Returns:
            True if transition successful
        """
        if not self.current_project_state:
            self.cli_interface.display_message(
                "Error: No active project. Start or resume a project first."
            )
            return False

        # Ensure phase manager is initialized
        if not self.phase_manager:
            self.phase_manager = PhaseManager(
                cli_interface=self.cli_interface,
                state_manager=self.state_manager,
                embedding_client=self.embedding_client,
                cost_tracker=self.cost_tracker,
                llm_client=self.llm_client,
                token_counter=self.token_counter,
                vector_db=self.vector_db,
            )

        try:
            current_phase = self.current_project_state.current_phase

            # Validate phase transition
            if not self._validate_phase_transition(current_phase, phase):
                return False

            # Create before snapshot
            before_snapshot_id = None
            if self.undo_redo_manager:
                before_snapshot_id = self.undo_redo_manager.create_snapshot(
                    self.current_project_state,
                    SnapshotType.AUTOMATIC,
                    f"Before transition from {current_phase.value} to {phase.value}",
                    {
                        "phase": current_phase,
                        "action": "phase_transition_before",
                        "target_phase": phase,
                    },
                )

            self.cli_interface.display_message(
                f"Transitioning from {current_phase.value} to {phase.value} phase..."
            )

            # Execute the target phase (async)
            result = await self._execute_phase(phase)

            if result.status == PhaseStatus.COMPLETED:
                # Update project state
                self.current_project_state.current_phase = phase
                await self.state_manager.save_project_state(self.current_project_state)

                # Create after snapshot and action
                if self.undo_redo_manager and before_snapshot_id:
                    after_snapshot_id = self.undo_redo_manager.create_snapshot(
                        self.current_project_state,
                        SnapshotType.AUTOMATIC,
                        f"After transition to {phase.value}",
                        {
                            "phase": phase,
                            "action": "phase_transition_after",
                            "source_phase": current_phase,
                        },
                    )

                    # Create undo/redo action
                    self.undo_redo_manager.create_action(
                        ActionType.PHASE_TRANSITION,
                        f"Transition from {current_phase.value} to {phase.value}",
                        before_snapshot_id,
                        after_snapshot_id,
                        {"source_phase": current_phase, "target_phase": phase},
                    )

                    # Add command history entry
                    self.undo_redo_manager.add_command_history_entry(
                        f"transition_to_phase({phase.value})",
                        phase,
                        True,
                        after_snapshot_id,
                        metadata={"source_phase": current_phase, "target_phase": phase},
                    )

                self.cli_interface.display_message(
                    f"Successfully transitioned to {phase.value} phase!"
                )
                return True
            else:
                # Add failed command history entry
                if self.undo_redo_manager and before_snapshot_id:
                    self.undo_redo_manager.add_command_history_entry(
                        f"transition_to_phase({phase.value})",
                        current_phase,
                        False,
                        before_snapshot_id,
                        error_message=result.message,
                        metadata={"source_phase": current_phase, "target_phase": phase},
                    )

                self.cli_interface.display_message(
                    f"Phase transition failed: {result.message}"
                )
                return False

        except Exception as e:
            error_msg = f"Error during phase transition: {e}"
            self.cli_interface.display_message(f"Error: {error_msg}")
            self.error_handler.handle_phase_transition_error(current_phase, phase, e)
            return False

    async def require_user_approval(self, content: str, phase: PhaseType) -> bool:
        """Require user approval for phase completion.

        Args:
            content: Content to show user for approval
            phase: Phase requesting approval

        Returns:
            True if user approves
        """
        if not self.require_explicit_approval:
            return True

        try:
            self.cli_interface.display_message(
                f"\n=== {phase.value.title()} Phase Approval Required ==="
            )
            self.cli_interface.display_message(content)
            self.cli_interface.display_message("=" * 50)

            # Request approval through CLI
            approved = self.cli_interface.request_approval(content, phase.value)

            # Track approval in session data
            if self.current_project_state:
                self.current_project_state.session_data.user_approvals[phase.value] = (
                    approved
                )
                await self.state_manager.save_project_state(self.current_project_state)

                # Create approval point snapshot
                if self.undo_redo_manager:
                    approval_description = f"{phase.value.title()} phase {'approved' if approved else 'rejected'}"
                    self.undo_redo_manager.create_snapshot(
                        self.current_project_state,
                        SnapshotType.APPROVAL_POINT,
                        approval_description,
                        {
                            "phase": phase,
                            "action": "user_approval",
                            "approved": approved,
                        },
                    )

            if approved:
                self.cli_interface.display_message(
                    f"{phase.value.title()} phase approved!"
                )
            else:
                self.cli_interface.display_message(
                    f"{phase.value.title()} phase not approved."
                )

            return approved

        except Exception as e:
            self.cli_interface.display_message(f"Error during approval process: {e}")
            return False

    def get_current_phase(self) -> PhaseType:
        """Get the current workflow phase.

        Returns:
            Current phase type
        """
        if self.current_project_state:
            return self.current_project_state.current_phase
        else:
            return PhaseType.INDEXING  # Default phase

    async def execute_complete_workflow(self) -> bool:
        """Execute the complete four-phase workflow.

        Returns:
            True if entire workflow completed successfully
        """
        if not self.current_project_state:
            self.cli_interface.display_message(
                "Error: No active project. Start or resume a project first."
            )
            return False

        # Ensure phase manager is initialized
        if not self.phase_manager:
            self.phase_manager = PhaseManager(
                cli_interface=self.cli_interface,
                state_manager=self.state_manager,
                embedding_client=self.embedding_client,
                cost_tracker=self.cost_tracker,
                llm_client=self.llm_client,
                token_counter=self.token_counter,
                vector_db=self.vector_db,
            )

        phases = [
            PhaseType.INDEXING,
            PhaseType.SPECIFICATION,
            PhaseType.DESIGN,
            PhaseType.IMPLEMENTATION,
        ]
        current_phase_index = phases.index(self.current_project_state.current_phase)

        self.cli_interface.display_message("Starting complete workflow execution...")

        # Execute remaining phases
        for phase in phases[current_phase_index:]:
            self.cli_interface.display_message(f"\n{'=' * 60}")
            self.cli_interface.display_message(f"EXECUTING {phase.value.upper()} PHASE")
            self.cli_interface.display_message(f"{'=' * 60}")

            if not await self.transition_to_phase(phase):
                self.cli_interface.display_message(
                    f"Workflow stopped at {phase.value} phase due to failure."
                )
                return False

        self.cli_interface.display_message(
            "\n🎉 Complete workflow executed successfully!"
        )
        self._display_final_summary()
        return True

    def _validate_phase_transition(
        self, current_phase: PhaseType, target_phase: PhaseType
    ) -> bool:
        """Validate that phase transition is allowed.

        Args:
            current_phase: Current phase
            target_phase: Target phase

        Returns:
            True if transition is valid
        """
        # Define valid phase transitions
        valid_transitions = {
            PhaseType.INDEXING: [PhaseType.SPECIFICATION],
            PhaseType.SPECIFICATION: [
                PhaseType.DESIGN,
                PhaseType.INDEXING,
            ],  # Allow going back
            PhaseType.DESIGN: [
                PhaseType.IMPLEMENTATION,
                PhaseType.SPECIFICATION,
            ],  # Allow going back
            PhaseType.IMPLEMENTATION: [PhaseType.DESIGN],  # Allow going back to refine
        }

        if target_phase in valid_transitions.get(current_phase, []):
            return True

        # Allow staying in the same phase (for re-execution)
        if current_phase == target_phase:
            return True

        self.cli_interface.display_message(
            f"Error: Invalid phase transition from {current_phase.value} to {target_phase.value}"
        )
        return False

    async def _execute_phase(self, phase: PhaseType) -> PhaseResult:
        """Execute a specific phase.

        Args:
            phase: Phase to execute

        Returns:
            Phase execution result
        """
        if not self.phase_manager:
            raise Exception("Phase manager not initialized")

        # Update cost tracker phase
        self.cost_tracker.set_phase(phase)

        # Get cost before phase execution
        cost_before = self.cost_tracker.get_current_cost()

        # Create project context
        context = self._create_project_context()

        # Execute phase based on type
        if phase == PhaseType.INDEXING:
            result = await self.phase_manager.execute_indexing_phase(
                self.current_project_state.project_path
            )
        elif phase == PhaseType.SPECIFICATION:
            result = await self.phase_manager.execute_specification_phase(context)
        elif phase == PhaseType.DESIGN:
            result = await self.phase_manager.execute_design_phase(context)
        elif phase == PhaseType.IMPLEMENTATION:
            result = await self.phase_manager.execute_implementation_phase(context)
        else:
            raise Exception(f"Unknown phase: {phase}")

        # Display cost summary for this phase
        cost_after = self.cost_tracker.get_current_cost()
        phase_cost = cost_after - cost_before
        self._display_phase_cost_summary(phase, phase_cost)

        # Check budget warnings
        if self.cost_tracker.check_budget_threshold():
            self._display_budget_warning()

        # Save token usage to project state
        await self._save_token_usage_to_state()

        return result

    def _create_project_context(self) -> ProjectContext:
        """Create project context for phase execution.

        Returns:
            ProjectContext object
        """
        return ProjectContext(
            project_state=self.current_project_state,
            ast_index=None,  # Will be loaded by phase manager if needed
            codebase_patterns=None,  # Will be analyzed by phase manager if needed
            user_preferences={},  # Could be loaded from config in future
            language_context=self.current_project_state.language_context if self.current_project_state else None,
        )

    def _display_progress_summary(self, project_state: ProjectState) -> None:
        """Display a summary of project progress.

        Args:
            project_state: Current project state
        """
        self.cli_interface.display_message("\n=== Project Progress Summary ===")
        self.cli_interface.display_message(
            f"Project Path: {project_state.project_path}"
        )
        self.cli_interface.display_message(
            f"Current Phase: {project_state.current_phase.value}"
        )
        self.cli_interface.display_message(
            f"Indexing Complete: {'Yes' if project_state.indexing_complete else 'No'}"
        )
        self.cli_interface.display_message(
            f"Has Specification: {'Yes' if project_state.specification else 'No'}"
        )
        self.cli_interface.display_message(
            f"Has Design: {'Yes' if project_state.design else 'No'}"
        )
        self.cli_interface.display_message(
            f"Has Tasks: {'Yes' if project_state.tasks else 'No'}"
        )

        if project_state.implementation_progress:
            completed_tasks = sum(
                1
                for status in project_state.implementation_progress.values()
                if status.value == "completed"
            )
            total_tasks = len(project_state.implementation_progress)
            self.cli_interface.display_message(
                f"Implementation Progress: {completed_tasks}/{total_tasks} tasks completed"
            )

        self.cli_interface.display_message(
            f"Last Updated: {project_state.updated_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        self.cli_interface.display_message("=" * 35)

    def _display_final_summary(self) -> None:
        """Display final workflow completion summary."""
        if not self.current_project_state:
            return

        self.cli_interface.display_message("\n🎯 Workflow Completion Summary")
        self.cli_interface.display_message("=" * 40)

        # Index summary
        if self.current_project_state.index_metadata:
            meta = self.current_project_state.index_metadata
            self.cli_interface.display_message(
                f"📊 Indexed: {meta.total_files} files, {meta.total_lines} lines"
            )
            self.cli_interface.display_message(
                f"🔍 Languages: {', '.join(meta.languages_detected)}"
            )

        # Specification summary
        if self.current_project_state.specification:
            spec = self.current_project_state.specification
            self.cli_interface.display_message(
                f"📋 Specification: {len(spec.functional_requirements)} requirements"
            )

        # Design summary
        if self.current_project_state.design:
            design = self.current_project_state.design
            self.cli_interface.display_message(
                f"🏗️  Design: {len(design.components)} components, {len(design.data_models)} models"
            )

        # Implementation summary
        if self.current_project_state.tasks:
            tasks = self.current_project_state.tasks
            self.cli_interface.display_message(
                f"✅ Tasks: {len(tasks.tasks)} implementation tasks ready"
            )

        # Display complete cost report
        self._display_complete_cost_report()

        self.cli_interface.display_message(
            "\n🚀 Your project is ready for development!"
        )
        self.cli_interface.display_message(
            "Check the .dev_agent/documents/ folder for generated documents."
        )

    def _display_phase_cost_summary(self, phase: PhaseType, phase_cost: float) -> None:
        """Display cost summary for a completed phase.

        Args:
            phase: Phase that was completed
            phase_cost: Cost incurred during this phase
        """
        phase_report = self.cost_tracker.get_phase_report(phase)

        self.cli_interface.display_message(
            f"\n💰 {phase.value.title()} Phase Cost Summary"
        )
        self.cli_interface.display_message("=" * 50)
        self.cli_interface.display_message(
            f"Operations: {phase_report.operations_count}"
        )
        self.cli_interface.display_message(
            f"Prompt Tokens: {phase_report.total_prompt_tokens:,}"
        )
        self.cli_interface.display_message(
            f"Completion Tokens: {phase_report.total_completion_tokens:,}"
        )
        self.cli_interface.display_message(
            f"Embedding Tokens: {phase_report.total_embedding_tokens:,}"
        )
        self.cli_interface.display_message(
            f"Total Tokens: {phase_report.total_prompt_tokens + phase_report.total_completion_tokens + phase_report.total_embedding_tokens:,}"
        )
        self.cli_interface.display_message(f"Phase Cost: ${phase_cost:.4f}")
        self.cli_interface.display_message(
            f"Total Cost So Far: ${self.cost_tracker.get_current_cost():.4f}"
        )
        self.cli_interface.display_message("=" * 50)

    def _display_budget_warning(self) -> None:
        """Display budget threshold warning."""
        current_cost = self.cost_tracker.get_current_cost()

        if self.cost_tracker.budget_limit is not None:
            if current_cost >= self.cost_tracker.budget_limit:
                self.cli_interface.display_message(
                    f"\n⚠️  BUDGET LIMIT EXCEEDED: ${current_cost:.2f} >= ${self.cost_tracker.budget_limit:.2f}"
                )
                self.cli_interface.display_message(
                    "Consider stopping operations to avoid additional costs."
                )
            elif self.cost_tracker.budget_threshold is not None:
                remaining = self.cost_tracker.budget_limit - current_cost
                self.cli_interface.display_message(
                    f"\n⚠️  Budget threshold exceeded: ${current_cost:.2f} >= ${self.cost_tracker.budget_threshold:.2f}"
                )
                self.cli_interface.display_message(
                    f"Remaining budget: ${remaining:.2f}"
                )
        elif self.cost_tracker.budget_threshold is not None:
            self.cli_interface.display_message(
                f"\n⚠️  Budget threshold exceeded: ${current_cost:.2f} >= ${self.cost_tracker.budget_threshold:.2f}"
            )

    def _display_complete_cost_report(self) -> None:
        """Display complete cost report for entire workflow."""
        report = self.cost_tracker.get_report()

        self.cli_interface.display_message("\n💰 Complete Workflow Cost Report")
        self.cli_interface.display_message("=" * 50)
        self.cli_interface.display_message(
            f"Total Operations: {report.operations_count}"
        )
        self.cli_interface.display_message(
            f"Total Prompt Tokens: {report.total_prompt_tokens:,}"
        )
        self.cli_interface.display_message(
            f"Total Completion Tokens: {report.total_completion_tokens:,}"
        )
        self.cli_interface.display_message(
            f"Total Embedding Tokens: {report.total_embedding_tokens:,}"
        )
        self.cli_interface.display_message(
            f"Total Tokens: {report.total_prompt_tokens + report.total_completion_tokens + report.total_embedding_tokens:,}"
        )
        self.cli_interface.display_message(f"Total Cost: ${report.total_cost:.4f}")

        # Display breakdown by phase
        if report.by_phase:
            self.cli_interface.display_message("\nCost by Phase:")
            for phase_name, phase_cost in report.by_phase.items():
                self.cli_interface.display_message(f"  {phase_name}: ${phase_cost:.4f}")

        # Display breakdown by operation type
        if report.by_operation:
            self.cli_interface.display_message("\nOperations by Type:")
            for op_type, count in report.by_operation.items():
                self.cli_interface.display_message(f"  {op_type}: {count}")

        self.cli_interface.display_message("=" * 50)

    async def _save_token_usage_to_state(self) -> None:
        """Save token usage statistics to project state."""
        if not self.state_manager:
            return

        # Reload current state to avoid overwriting changes made by phase manager
        current_state = self.state_manager.load_project_state()
        if not current_state:
            return

        # Get current report
        report = self.cost_tracker.get_report()

        # Convert by_phase dict to use string keys for JSON serialization
        by_phase_str = {phase.value: cost for phase, cost in report.by_phase.items()}

        # Store token usage in session data
        token_usage_data = {
            "total_prompt_tokens": report.total_prompt_tokens,
            "total_completion_tokens": report.total_completion_tokens,
            "total_embedding_tokens": report.total_embedding_tokens,
            "total_cost": report.total_cost,
            "operations_count": report.operations_count,
            "by_phase": by_phase_str,
            "by_operation": report.by_operation,
            "last_updated": datetime.now().isoformat(),
        }

        current_state.session_data.token_usage = token_usage_data

        # Save updated state (preserving any changes made by phase manager)
        await self.state_manager.save_project_state(current_state)
        
        # Update our cached state
        self.current_project_state = current_state

    def _save_document_to_file(self, phase: PhaseType, content: str) -> None:
        """Save generated document to filesystem.

        Args:
            phase: Phase that generated the document
            content: Document content to save

        Raises:
            DocumentSaveError: If document cannot be saved
        """
        if not self.current_project_state:
            raise DocumentSaveError(
                "No active project state",
                phase=phase.value,
                context=ErrorContext(
                    operation="save_document_to_file",
                    phase=phase.value,
                ),
            )

        # Ensure documents directory exists
        project_path = Path(self.current_project_state.project_path)
        docs_dir = project_path / ".dev_agent" / "documents"
        
        try:
            docs_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured documents directory exists: {docs_dir}")
        except Exception as e:
            logger.error(f"Failed to create documents directory: {e}", exc_info=True)
            raise DocumentSaveError(
                f"Could not create documents directory: {e}",
                file_path=str(docs_dir),
                phase=phase.value,
                context=ErrorContext(
                    operation="create_documents_directory",
                    file_path=str(docs_dir),
                    phase=phase.value,
                ),
                original_error=e,
            ) from e

        # Map phase to filename
        filename_map = {
            PhaseType.SPECIFICATION: "specification.md",
            PhaseType.DESIGN: "design.md",
            PhaseType.IMPLEMENTATION: "tasks.md",
        }

        filename = filename_map.get(phase)
        if not filename:
            logger.warning(f"Unknown phase for document save: {phase}")
            raise DocumentSaveError(
                f"Unknown phase type: {phase.value}",
                phase=phase.value,
                context=ErrorContext(
                    operation="map_phase_to_filename",
                    phase=phase.value,
                    additional_info={"available_phases": list(filename_map.keys())},
                ),
            )

        filepath = docs_dir / filename

        try:
            # Create timestamped backup if file exists
            if filepath.exists():
                timestamp = int(datetime.now().timestamp())
                backup_path = filepath.with_suffix(f".md.backup.{timestamp}")
                filepath.rename(backup_path)
                logger.info(f"Backed up existing document to {backup_path}")

            # Write new content with UTF-8 encoding
            filepath.write_text(content, encoding="utf-8")
            logger.info(f"Saved {phase.value} document to {filepath}")

        except PermissionError as e:
            logger.error(f"Permission denied writing document: {e}", exc_info=True)
            raise DocumentSaveError(
                f"Permission denied writing to {filepath}",
                file_path=str(filepath),
                phase=phase.value,
                context=ErrorContext(
                    operation="write_document_file",
                    file_path=str(filepath),
                    phase=phase.value,
                ),
                original_error=e,
            ) from e
        except OSError as e:
            # Covers disk full, I/O errors, etc.
            logger.error(f"OS error writing document: {e}", exc_info=True)
            raise DocumentSaveError(
                f"Failed to write document to {filepath}: {e}",
                file_path=str(filepath),
                phase=phase.value,
                context=ErrorContext(
                    operation="write_document_file",
                    file_path=str(filepath),
                    phase=phase.value,
                ),
                original_error=e,
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error writing document: {e}", exc_info=True)
            raise DocumentSaveError(
                f"Unexpected error saving {phase.value} document: {e}",
                file_path=str(filepath),
                phase=phase.value,
                context=ErrorContext(
                    operation="write_document_file",
                    file_path=str(filepath),
                    phase=phase.value,
                ),
                original_error=e,
            ) from e

    def get_cost_tracker(self) -> CostTracker:
        """Get the cost tracker instance.

        Returns:
            CostTracker instance
        """
        return self.cost_tracker

    def generate_cost_report(self) -> dict:
        """Generate a cost report for the entire workflow.

        Returns:
            Dictionary containing cost report data
        """
        report = self.cost_tracker.get_report()

        return {
            "total_operations": report.operations_count,
            "total_prompt_tokens": report.total_prompt_tokens,
            "total_completion_tokens": report.total_completion_tokens,
            "total_embedding_tokens": report.total_embedding_tokens,
            "total_tokens": report.total_prompt_tokens
            + report.total_completion_tokens
            + report.total_embedding_tokens,
            "total_cost": report.total_cost,
            "by_phase": report.by_phase,
            "by_operation": report.by_operation,
            "start_time": report.start_time.isoformat(),
            "end_time": report.end_time.isoformat(),
        }

    def create_manual_snapshot(self, description: str) -> str | None:
        """Create a manual snapshot of the current state.

        Args:
            description: Description for the snapshot

        Returns:
            Snapshot ID if successful, None otherwise
        """
        if not self.current_project_state or not self.undo_redo_manager:
            self.cli_interface.display_message(
                "Error: No active project or undo/redo manager not initialized."
            )
            return None

        try:
            snapshot_id = self.undo_redo_manager.create_snapshot(
                self.current_project_state,
                SnapshotType.MANUAL,
                description,
                {
                    "phase": self.current_project_state.current_phase,
                    "action": "manual_snapshot",
                },
            )

            self.cli_interface.display_message(
                f"Manual snapshot created: {description}"
            )
            return snapshot_id

        except Exception as e:
            self.cli_interface.display_message(f"Error creating snapshot: {e}")
            return None

    async def restore_from_snapshot(self, snapshot_id: str) -> bool:
        """Restore project state from a specific snapshot.

        Args:
            snapshot_id: ID of the snapshot to restore

        Returns:
            True if successful
        """
        if not self.undo_redo_manager or not self.state_manager:
            self.cli_interface.display_message(
                "Error: Undo/redo manager or state manager not initialized."
            )
            return False

        try:
            # Restore project state
            restored_state = self.undo_redo_manager.restore_snapshot(snapshot_id)
            if not restored_state:
                self.cli_interface.display_message(
                    f"Error: Could not restore snapshot {snapshot_id}"
                )
                return False

            # Update current state
            self.current_project_state = restored_state

            # Save restored state
            if not await self.state_manager.save_project_state(restored_state):
                self.cli_interface.display_message(
                    "Error: Could not save restored state"
                )
                return False

            # Create restoration snapshot
            self.undo_redo_manager.create_snapshot(
                restored_state,
                SnapshotType.AUTOMATIC,
                f"Restored from snapshot {snapshot_id}",
                {
                    "phase": restored_state.current_phase,
                    "action": "snapshot_restore",
                    "source_snapshot": snapshot_id,
                },
            )

            self.cli_interface.display_message(
                f"Successfully restored to snapshot {snapshot_id}"
            )
            self.cli_interface.display_message(
                f"Current phase: {restored_state.current_phase.value}"
            )

            return True

        except Exception as e:
            self.cli_interface.display_message(f"Error restoring snapshot: {e}")
            return False

    async def undo_last_action(self) -> bool:
        """Undo the last action.

        Returns:
            True if successful
        """
        if not self.undo_redo_manager:
            self.cli_interface.display_message(
                "Error: Undo/redo manager not initialized."
            )
            return False

        try:
            undo_actions = self.undo_redo_manager.get_undo_actions(limit=1)
            if not undo_actions:
                self.cli_interface.display_message("No actions available to undo.")
                return False

            action = undo_actions[0]
            restored_state = self.undo_redo_manager.undo_action(action.id)

            if not restored_state:
                self.cli_interface.display_message("Error: Could not undo action")
                return False

            # Update current state
            self.current_project_state = restored_state

            # Save restored state
            if not await self.state_manager.save_project_state(restored_state):
                self.cli_interface.display_message("Error: Could not save undone state")
                return False

            self.cli_interface.display_message(
                f"Successfully undone: {action.description}"
            )

            return True

        except Exception as e:
            self.cli_interface.display_message(f"Error undoing action: {e}")
            return False

    async def redo_last_action(self) -> bool:
        """Redo the last undone action.

        Returns:
            True if successful
        """
        if not self.undo_redo_manager:
            self.cli_interface.display_message(
                "Error: Undo/redo manager not initialized."
            )
            return False

        try:
            redo_actions = self.undo_redo_manager.get_redo_actions(limit=1)
            if not redo_actions:
                self.cli_interface.display_message("No actions available to redo.")
                return False

            action = redo_actions[0]
            restored_state = self.undo_redo_manager.redo_action(action.id)

            if not restored_state:
                self.cli_interface.display_message("Error: Could not redo action")
                return False

            # Update current state
            self.current_project_state = restored_state

            # Save restored state
            if not await self.state_manager.save_project_state(restored_state):
                self.cli_interface.display_message("Error: Could not save redone state")
                return False

            self.cli_interface.display_message(
                f"Successfully redone: {action.description}"
            )

            return True

        except Exception as e:
            self.cli_interface.display_message(f"Error redoing action: {e}")
            return False

    def get_undo_redo_manager(self) -> UndoRedoManager | None:
        """Get the undo/redo manager instance.

        Returns:
            UndoRedoManager instance or None if not initialized
        """
        return self.undo_redo_manager


class WorkflowErrorHandler:
    """Handles errors and recovery mechanisms for workflow operations."""

    def __init__(self, cli_interface: ICLIInterface):
        """Initialize error handler.

        Args:
            cli_interface: CLI interface for user communication
        """
        self.cli_interface = cli_interface
        self.error_log = []

    def handle_phase_transition_error(
        self, current_phase: PhaseType, target_phase: PhaseType, error: Exception
    ) -> None:
        """Handle errors during phase transitions.

        Args:
            current_phase: Phase transitioning from
            target_phase: Phase transitioning to
            error: Exception that occurred
        """
        error_info = {
            "timestamp": datetime.now(),
            "current_phase": current_phase.value,
            "target_phase": target_phase.value,
            "error": str(error),
            "error_type": type(error).__name__,
        }

        self.error_log.append(error_info)

        self.cli_interface.display_message("\n⚠️  Phase Transition Error")
        self.cli_interface.display_message(
            f"From: {current_phase.value} → To: {target_phase.value}"
        )
        self.cli_interface.display_message(f"Error: {error}")

        # Suggest recovery actions
        recovery_suggestions = self._get_recovery_suggestions(
            current_phase, target_phase, error
        )
        if recovery_suggestions:
            self.cli_interface.display_message("\n💡 Suggested Recovery Actions:")
            for suggestion in recovery_suggestions:
                self.cli_interface.display_message(f"  • {suggestion}")

    def handle_phase_execution_error(self, phase: PhaseType, error: Exception) -> None:
        """Handle errors during phase execution.

        Args:
            phase: Phase that failed
            error: Exception that occurred
        """
        error_info = {
            "timestamp": datetime.now(),
            "phase": phase.value,
            "error": str(error),
            "error_type": type(error).__name__,
        }

        self.error_log.append(error_info)

        self.cli_interface.display_message(f"\n❌ {phase.value.title()} Phase Error")
        self.cli_interface.display_message(f"Error: {error}")

        # Suggest recovery actions
        recovery_suggestions = self._get_phase_recovery_suggestions(phase, error)
        if recovery_suggestions:
            self.cli_interface.display_message("\n💡 Suggested Recovery Actions:")
            for suggestion in recovery_suggestions:
                self.cli_interface.display_message(f"  • {suggestion}")

    def _get_recovery_suggestions(
        self, current_phase: PhaseType, target_phase: PhaseType, error: Exception
    ) -> list:
        """Get recovery suggestions for phase transition errors.

        Args:
            current_phase: Current phase
            target_phase: Target phase
            error: Error that occurred

        Returns:
            List of recovery suggestions
        """
        suggestions = []

        if "state" in str(error).lower():
            suggestions.append(
                "Check if project state file is corrupted and try resuming the project"
            )
            suggestions.append(
                "If state is corrupted, you may need to restart from the indexing phase"
            )

        if "permission" in str(error).lower():
            suggestions.append("Check file permissions in the project directory")
            suggestions.append(
                "Ensure you have write access to the .dev_agent directory"
            )

        if "memory" in str(error).lower() or "resource" in str(error).lower():
            suggestions.append("Try closing other applications to free up memory")
            suggestions.append("Consider processing the project in smaller chunks")

        # Phase-specific suggestions
        if target_phase == PhaseType.INDEXING:
            suggestions.append(
                "Check if the project directory contains valid source files"
            )
            suggestions.append("Ensure Tree-sitter parsers are properly installed")

        elif target_phase == PhaseType.SPECIFICATION:
            suggestions.append("Verify that indexing completed successfully")
            suggestions.append("Check if codebase analysis produced valid results")

        elif target_phase == PhaseType.DESIGN:
            suggestions.append("Ensure specification was approved and saved")
            suggestions.append("Check if specification contains valid requirements")

        elif target_phase == PhaseType.IMPLEMENTATION:
            suggestions.append("Verify that design document was approved")
            suggestions.append(
                "Check if design contains valid components and interfaces"
            )

        return suggestions

    def _get_phase_recovery_suggestions(
        self, phase: PhaseType, error: Exception
    ) -> list:
        """Get recovery suggestions for phase execution errors.

        Args:
            phase: Phase that failed
            error: Error that occurred

        Returns:
            List of recovery suggestions
        """
        suggestions = []
        error_str = str(error).lower()

        # Common suggestions
        if "timeout" in error_str:
            suggestions.append("Increase timeout settings for long-running operations")
            suggestions.append("Try processing smaller chunks of the codebase")

        if "network" in error_str or "connection" in error_str:
            suggestions.append("Check internet connection for external dependencies")
            suggestions.append("Retry the operation after network issues are resolved")

        # Phase-specific suggestions
        if phase == PhaseType.INDEXING:
            suggestions.extend(
                [
                    "Check if all source files are readable",
                    "Verify Tree-sitter language parsers are installed",
                    "Try excluding problematic files or directories",
                    "Ensure sufficient disk space for index storage",
                ]
            )

        elif phase == PhaseType.SPECIFICATION:
            suggestions.extend(
                [
                    "Verify codebase analysis completed successfully",
                    "Check if project contains recognizable code patterns",
                    "Try providing more explicit user input for specification",
                ]
            )

        elif phase == PhaseType.DESIGN:
            suggestions.extend(
                [
                    "Ensure specification document is valid and complete",
                    "Check if architecture analysis found valid patterns",
                    "Try simplifying the specification requirements",
                ]
            )

        elif phase == PhaseType.IMPLEMENTATION:
            suggestions.extend(
                [
                    "Verify design document contains actionable components",
                    "Check if task generation produced valid tasks",
                    "Ensure target directory has write permissions",
                ]
            )

        return suggestions


class WorkflowException(Exception):
    """Exception raised during workflow operations."""

    pass
