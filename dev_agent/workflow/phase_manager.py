"""Phase management system that handles individual workflow phases."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from ..analysis.codebase_analyzer import CodebaseAnalyzer
from ..generation.python_code_generator import PythonCodeGenerator
from ..generation.task_generator import TaskGenerator
from ..indexing.indexing_engine import IndexingEngine
from ..interfaces.analysis_interface import ICodebaseAnalyzer
from ..interfaces.cli_interface import ICLIInterface
from ..interfaces.indexing_interface import IIndexingEngine
from ..interfaces.workflow_interface import IPhaseManager
from ..models.context import ProjectContext
from ..models.enums import PhaseStatus, PhaseType
from ..models.project_state import IndexMetadata
from ..models.results import (
    DesignResult,
    ImplementationResult,
    IndexingResult,
    PhaseResult,
    SpecificationResult,
)
from ..state.state_manager import StateManager
from ..workflow.design_workflow import DesignWorkflow
from ..workflow.specification_workflow import SpecificationWorkflow

if TYPE_CHECKING:
    from ..indexing.vector_database import VectorDatabase
    from ..llm.base import IEmbeddingClient, ILLMClient
    from ..llm.cost_tracker import CostTracker
    from ..llm.token_counter import TokenCounter


class PhaseManager(IPhaseManager):
    """Manages execution of individual workflow phases with validation and recovery.
    
    This class orchestrates the execution of the four workflow phases (indexing,
    specification, design, and implementation) with proper LLM client integration,
    validation, and error recovery.
    """

    def __init__(
        self,
        cli_interface: ICLIInterface,
        state_manager: StateManager,
        embedding_client: IEmbeddingClient | None = None,
        cost_tracker: CostTracker | None = None,
        llm_client: ILLMClient | None = None,
        token_counter: TokenCounter | None = None,
        vector_db: VectorDatabase | None = None,
    ):
        """Initialize the phase manager with all required components.

        Args:
            cli_interface: CLI interface for user interaction
            state_manager: State manager for persistence
            embedding_client: Optional embedding client for indexing (required for specification phase)
            cost_tracker: Optional cost tracker for monitoring API usage
            llm_client: Optional LLM client for AI-powered generation (required for specification phase)
            token_counter: Optional token counter for cost estimation and validation
            vector_db: Optional vector database for semantic code search
        """
        self.cli_interface = cli_interface
        self.state_manager = state_manager
        self.embedding_client = embedding_client
        self.cost_tracker = cost_tracker
        self.llm_client = llm_client
        self.token_counter = token_counter
        self.vector_db = vector_db

        # Component instances (initialized lazily)
        self.indexing_engine: IIndexingEngine | None = None
        self.codebase_analyzer: ICodebaseAnalyzer | None = None
        self.specification_workflow: SpecificationWorkflow | None = None
        self.design_workflow: DesignWorkflow | None = None
        self.task_generator: TaskGenerator | None = None
        self.code_generator: PythonCodeGenerator | None = None

        # Phase execution settings
        self.max_retry_attempts = 3
        self.phase_timeout_seconds = 3600  # 1 hour default timeout

        # Progress tracking
        self.current_phase_progress = 0.0

    def execute_indexing_phase(self, project_path: str) -> IndexingResult:
        """Execute the indexing phase.

        Args:
            project_path: Path to the project directory

        Returns:
            IndexingResult with execution details
        """
        self.cli_interface.display_message("🔍 Starting indexing phase...")

        start_time = time.time()
        result = IndexingResult()

        try:
            # Initialize indexing engine
            if not self.indexing_engine:
                self.indexing_engine = IndexingEngine(project_path)

                # Set up progress callback
                def progress_callback(current: int, total: int, message: str):
                    self.current_phase_progress = current / total if total > 0 else 0.0
                    self.cli_interface.display_progress(
                        PhaseType.INDEXING, self.current_phase_progress
                    )
                    if message:
                        self.cli_interface.display_message(f"  {message}")

                self.indexing_engine.set_progress_callback(progress_callback)

            # Check if index already exists and is up to date
            if not self.indexing_engine.is_index_stale():
                self.cli_interface.display_message(
                    "✅ Existing index is up to date, skipping rebuild"
                )

                # Load existing index metadata
                metadata = self.indexing_engine.get_index_metadata()
                if metadata:
                    result.files_indexed = metadata.total_files
                    result.total_lines = metadata.total_lines
                    result.index_size_mb = metadata.index_size_mb
                    result.languages_detected = metadata.languages_detected

                result.status = PhaseStatus.COMPLETED
                result.message = "Index loaded from existing cache"

                # Automatically transition to specification phase (same as new index)
                project_state = self.state_manager.load_project_state()
                if project_state:
                    project_state.current_phase = PhaseType.SPECIFICATION
                    self.state_manager.save_project_state(project_state)

                self.cli_interface.display_message(
                    "✅ Indexing complete! Moving to specification phase..."
                )

            else:
                # Build new index
                self.cli_interface.display_message("Building codebase index...")

                index_result = self.indexing_engine.build_index()

                if index_result.success:
                    result.status = PhaseStatus.COMPLETED
                    result.message = "Indexing completed successfully"
                    result.files_indexed = index_result.metadata.get("total_files", 0)
                    result.total_lines = index_result.metadata.get("total_lines", 0)
                    result.index_size_mb = index_result.metadata.get(
                        "index_size_mb", 0.0
                    )
                    result.languages_detected = index_result.metadata.get(
                        "languages_detected", []
                    )

                    # Update project state
                    project_state = self.state_manager.load_project_state()
                    if project_state:
                        project_state.indexing_complete = True

                        # Create index metadata
                        project_state.index_metadata = IndexMetadata(
                            total_files=result.files_indexed,
                            total_lines=result.total_lines,
                            languages_detected=result.languages_detected,
                            index_size_mb=result.index_size_mb,
                            last_indexed=time.time(),
                            index_version="1.0",
                        )

                        # Automatically transition to specification phase
                        project_state.current_phase = PhaseType.SPECIFICATION

                        self.state_manager.save_project_state(project_state)

                    self.cli_interface.display_message(
                        f"✅ Indexed {result.files_indexed} files "
                        f"({result.total_lines:,} lines) in {time.time() - start_time:.1f}s"
                    )
                    self.cli_interface.display_message(
                        "✅ Indexing complete! Moving to specification phase..."
                    )

                else:
                    result.status = PhaseStatus.FAILED
                    result.message = (
                        f"Indexing failed: {'; '.join(index_result.errors)}"
                    )
                    result.errors = index_result.errors

                    self.cli_interface.display_message(
                        f"❌ Indexing failed: {result.message}"
                    )

            # Validate phase completion only if it was successful
            if result.status == PhaseStatus.COMPLETED:
                if not self.validate_phase_completion(PhaseType.INDEXING, result):
                    result.status = PhaseStatus.FAILED
                    result.message = "Indexing validation failed"

            return result

        except Exception as e:
            result.status = PhaseStatus.FAILED
            result.message = f"Indexing phase error: {e}"
            result.errors = [str(e)]

            self.cli_interface.display_message(f"❌ Indexing phase failed: {e}")
            return result

    async def execute_specification_phase(
        self, context: ProjectContext
    ) -> SpecificationResult:
        """Execute the specification phase.

        Args:
            context: Project context with state and analysis data

        Returns:
            SpecificationResult with execution details
        """
        self.cli_interface.display_message("📋 Starting specification phase...")

        result = SpecificationResult()

        try:
            # Initialize components
            if not self.codebase_analyzer:
                if not self.indexing_engine:
                    # Initialize indexing engine with embedding client for vector search
                    self.indexing_engine = IndexingEngine(
                        project_path=context.project_state.project_path,
                        embedding_client=self.embedding_client,
                        cost_tracker=self.cost_tracker,
                    )
                self.codebase_analyzer = CodebaseAnalyzer(self.indexing_engine)

            if not self.specification_workflow:
                self.specification_workflow = SpecificationWorkflow(
                    cli_interface=self.cli_interface,
                    codebase_analyzer=self.codebase_analyzer,
                    state_manager=self.state_manager,
                    llm_client=self.llm_client,
                    cost_tracker=self.cost_tracker,
                    token_counter=self.token_counter,
                    vector_db=self.vector_db,
                )

            # Execute specification generation (async)
            specification = await self.specification_workflow.execute_specification_phase(
                context.project_state.project_path
            )

            if specification and specification.approved:
                result.status = PhaseStatus.COMPLETED
                result.message = "Specification generated and approved"
                result.requirements_count = len(specification.functional_requirements)
                result.source_type = specification.source.value
                result.confidence_score = 0.9  # Could be calculated from analysis

                # Update project state
                project_state = self.state_manager.load_project_state()
                if project_state:
                    project_state.specification = specification
                    self.state_manager.save_project_state(project_state)

                self.cli_interface.display_message(
                    f"✅ Specification completed with {result.requirements_count} requirements"
                )

            else:
                result.status = PhaseStatus.FAILED
                result.message = "Specification was not approved or generation failed"
                self.cli_interface.display_message("❌ Specification phase failed")

            # Validate phase completion only if it was successful
            if result.status == PhaseStatus.COMPLETED:
                if not self.validate_phase_completion(PhaseType.SPECIFICATION, result):
                    result.status = PhaseStatus.FAILED
                    result.message = "Specification validation failed"

            return result

        except Exception as e:
            result.status = PhaseStatus.FAILED
            result.message = f"Specification phase error: {e}"
            result.errors = [str(e)]

            self.cli_interface.display_message(f"❌ Specification phase failed: {e}")
            return result

    def execute_design_phase(self, context: ProjectContext) -> DesignResult:
        """Execute the design phase.

        Args:
            context: Project context with state and analysis data

        Returns:
            DesignResult with execution details
        """
        self.cli_interface.display_message("🏗️ Starting design phase...")

        result = DesignResult()

        try:
            # Ensure we have a specification
            project_state = self.state_manager.load_project_state()
            if not project_state or not project_state.specification:
                result.status = PhaseStatus.FAILED
                result.message = "No approved specification found. Complete specification phase first."
                return result

            # Initialize components
            if not self.codebase_analyzer:
                if not self.indexing_engine:
                    # Initialize indexing engine with embedding client for vector search
                    self.indexing_engine = IndexingEngine(
                        project_path=context.project_state.project_path,
                        embedding_client=self.embedding_client,
                        cost_tracker=self.cost_tracker,
                    )
                self.codebase_analyzer = CodebaseAnalyzer(self.indexing_engine)

            if not self.design_workflow:
                self.design_workflow = DesignWorkflow(
                    cli_interface=self.cli_interface,
                    codebase_analyzer=self.codebase_analyzer,
                    state_manager=self.state_manager,
                )

            # Execute design generation
            design = self.design_workflow.execute_design_phase(
                project_state.specification
            )

            if design and design.approved:
                result.status = PhaseStatus.COMPLETED
                result.message = "Design generated and approved"
                result.components_count = len(design.components)
                result.interfaces_count = len(design.interfaces)
                result.data_models_count = len(design.data_models)

                # Update project state
                project_state.design = design
                self.state_manager.save_project_state(project_state)

                self.cli_interface.display_message(
                    f"✅ Design completed with {result.components_count} components, "
                    f"{result.interfaces_count} interfaces, {result.data_models_count} data models"
                )

            else:
                result.status = PhaseStatus.FAILED
                result.message = "Design was not approved or generation failed"
                self.cli_interface.display_message("❌ Design phase failed")

            # Validate phase completion only if it was successful
            if result.status == PhaseStatus.COMPLETED:
                if not self.validate_phase_completion(PhaseType.DESIGN, result):
                    result.status = PhaseStatus.FAILED
                    result.message = "Design validation failed"

            return result

        except Exception as e:
            result.status = PhaseStatus.FAILED
            result.message = f"Design phase error: {e}"
            result.errors = [str(e)]

            self.cli_interface.display_message(f"❌ Design phase failed: {e}")
            return result

    def execute_implementation_phase(
        self, context: ProjectContext
    ) -> ImplementationResult:
        """Execute the implementation phase.

        Args:
            context: Project context with state and analysis data

        Returns:
            ImplementationResult with execution details
        """
        self.cli_interface.display_message("⚙️ Starting implementation phase...")

        result = ImplementationResult()

        try:
            # Ensure we have a design
            project_state = self.state_manager.load_project_state()
            if not project_state or not project_state.design:
                result.status = PhaseStatus.FAILED
                result.message = (
                    "No approved design found. Complete design phase first."
                )
                return result

            # Initialize components
            if not self.codebase_analyzer:
                if not self.indexing_engine:
                    # Initialize indexing engine with embedding client for vector search
                    self.indexing_engine = IndexingEngine(
                        project_path=context.project_state.project_path,
                        embedding_client=self.embedding_client,
                        cost_tracker=self.cost_tracker,
                    )
                self.codebase_analyzer = CodebaseAnalyzer(self.indexing_engine)

            if not self.task_generator:
                self.task_generator = TaskGenerator(self.cli_interface)

            if not self.code_generator:
                self.code_generator = PythonCodeGenerator(self.codebase_analyzer)

            # Step 1: Generate task list
            self.cli_interface.display_message("Generating implementation tasks...")

            task_list = self.task_generator.generate_from_design(project_state.design)

            if not task_list:
                result.status = PhaseStatus.FAILED
                result.message = "Failed to generate task list from design"
                return result

            # Request approval for task list
            task_content = self.task_generator.format_task_list(task_list)
            approved = self.cli_interface.request_approval(task_content, "tasks")

            if not approved:
                result.status = PhaseStatus.FAILED
                result.message = "Task list was not approved"
                return result

            # Save task list
            task_list.approved = True
            project_state.tasks = task_list
            self.state_manager.save_project_state(project_state)
            self.state_manager.save_document(task_content, "tasks")

            # Step 2: Initialize implementation tracking
            implementation_progress = {}
            for task in task_list.tasks:
                implementation_progress[task.id] = "not_started"

            project_state.implementation_progress = implementation_progress
            self.state_manager.save_project_state(project_state)

            result.status = PhaseStatus.COMPLETED
            result.message = "Implementation phase setup completed"
            result.tasks_completed = 0  # No tasks executed yet, just prepared
            result.files_generated = 0
            result.tests_generated = 0

            self.cli_interface.display_message(
                f"✅ Implementation phase ready with {len(task_list.tasks)} tasks"
            )
            self.cli_interface.display_message(
                "Tasks are ready for execution. Use the task execution workflow to implement them."
            )

            # Validate phase completion only if it was successful
            if result.status == PhaseStatus.COMPLETED:
                if not self.validate_phase_completion(PhaseType.IMPLEMENTATION, result):
                    result.status = PhaseStatus.FAILED
                    result.message = "Implementation validation failed"

            return result

        except Exception as e:
            result.status = PhaseStatus.FAILED
            result.message = f"Implementation phase error: {e}"
            result.errors = [str(e)]

            self.cli_interface.display_message(f"❌ Implementation phase failed: {e}")
            return result

    def validate_phase_completion(self, phase: PhaseType, result: PhaseResult) -> bool:
        """Validate that a phase has been completed successfully.

        Args:
            phase: Phase to validate
            result: Phase execution result

        Returns:
            True if phase completed successfully
        """
        try:
            # Basic validation - check if phase completed without errors
            if result.status != PhaseStatus.COMPLETED:
                return False

            if result.errors:
                self.cli_interface.display_message(
                    f"⚠️ Phase completed with warnings: {'; '.join(result.errors)}"
                )

            # Phase-specific validation
            if phase == PhaseType.INDEXING:
                return self._validate_indexing_completion(result)
            elif phase == PhaseType.SPECIFICATION:
                return self._validate_specification_completion(result)
            elif phase == PhaseType.DESIGN:
                return self._validate_design_completion(result)
            elif phase == PhaseType.IMPLEMENTATION:
                return self._validate_implementation_completion(result)

            return True

        except Exception as e:
            self.cli_interface.display_message(f"❌ Phase validation error: {e}")
            return False

    def _validate_indexing_completion(self, result: IndexingResult) -> bool:
        """Validate indexing phase completion.

        Args:
            result: Indexing result to validate

        Returns:
            True if indexing completed successfully
        """
        # Check if any files were indexed
        if result.files_indexed == 0:
            self.cli_interface.display_message("⚠️ Warning: No files were indexed")
            return False

        # Check if index has reasonable size
        if result.index_size_mb == 0:
            self.cli_interface.display_message("⚠️ Warning: Index size is zero")
            return False

        # Check if languages were detected
        if not result.languages_detected:
            self.cli_interface.display_message(
                "⚠️ Warning: No programming languages detected"
            )
            return False

        return True

    def _validate_specification_completion(self, result: SpecificationResult) -> bool:
        """Validate specification phase completion.

        Args:
            result: Specification result to validate

        Returns:
            True if specification completed successfully
        """
        # Check if requirements were generated
        if result.requirements_count == 0:
            self.cli_interface.display_message(
                "⚠️ Warning: No requirements were generated"
            )
            return False

        # Check confidence score
        if result.confidence_score < 0.5:
            self.cli_interface.display_message(
                "⚠️ Warning: Low confidence in specification generation"
            )

        # Verify specification was saved
        project_state = self.state_manager.load_project_state()
        if not project_state or not project_state.specification:
            self.cli_interface.display_message(
                "❌ Error: Specification not saved to project state"
            )
            return False

        return True

    def _validate_design_completion(self, result: DesignResult) -> bool:
        """Validate design phase completion.

        Args:
            result: Design result to validate

        Returns:
            True if design completed successfully
        """
        # Check if components were generated
        if result.components_count == 0:
            self.cli_interface.display_message(
                "⚠️ Warning: No components were generated"
            )
            return False

        # Verify design was saved
        project_state = self.state_manager.load_project_state()
        if not project_state or not project_state.design:
            self.cli_interface.display_message(
                "❌ Error: Design not saved to project state"
            )
            return False

        return True

    def _validate_implementation_completion(self, result: ImplementationResult) -> bool:
        """Validate implementation phase completion.

        Args:
            result: Implementation result to validate

        Returns:
            True if implementation completed successfully
        """
        # Verify task list was generated and saved
        project_state = self.state_manager.load_project_state()
        if not project_state or not project_state.tasks:
            self.cli_interface.display_message(
                "❌ Error: Task list not saved to project state"
            )
            return False

        # Check if implementation progress tracking was initialized
        if not project_state.implementation_progress:
            self.cli_interface.display_message(
                "❌ Error: Implementation progress tracking not initialized"
            )
            return False

        return True

    async def retry_phase_execution(
        self, phase: PhaseType, context: ProjectContext, max_attempts: int = 3
    ) -> PhaseResult:
        """Retry phase execution with error recovery.

        Args:
            phase: Phase to retry
            context: Project context
            max_attempts: Maximum retry attempts

        Returns:
            Final phase result after retries
        """
        last_result = None

        for attempt in range(1, max_attempts + 1):
            self.cli_interface.display_message(
                f"🔄 Attempt {attempt}/{max_attempts} for {phase.value} phase"
            )

            try:
                # Execute phase based on type
                if phase == PhaseType.INDEXING:
                    result = self.execute_indexing_phase(
                        context.project_state.project_path
                    )
                elif phase == PhaseType.SPECIFICATION:
                    result = await self.execute_specification_phase(context)
                elif phase == PhaseType.DESIGN:
                    result = self.execute_design_phase(context)
                elif phase == PhaseType.IMPLEMENTATION:
                    result = self.execute_implementation_phase(context)
                else:
                    raise ValueError(f"Unknown phase: {phase}")

                # Check if successful
                if result.status == PhaseStatus.COMPLETED:
                    if attempt > 1:
                        self.cli_interface.display_message(
                            f"✅ {phase.value} phase succeeded on attempt {attempt}"
                        )
                    return result

                last_result = result

                if attempt < max_attempts:
                    self.cli_interface.display_message(
                        f"⚠️ Attempt {attempt} failed: {result.message}"
                    )
                    self.cli_interface.display_message("Retrying in 2 seconds...")
                    time.sleep(2)

            except Exception as e:
                error_result = PhaseResult(
                    phase=phase,
                    status=PhaseStatus.FAILED,
                    message=f"Attempt {attempt} failed with exception: {e}",
                    errors=[str(e)],
                )

                last_result = error_result

                if attempt < max_attempts:
                    self.cli_interface.display_message(
                        f"❌ Attempt {attempt} failed with error: {e}"
                    )
                    self.cli_interface.display_message("Retrying in 2 seconds...")
                    time.sleep(2)

        # All attempts failed
        self.cli_interface.display_message(
            f"❌ All {max_attempts} attempts failed for {phase.value} phase"
        )
        return last_result or PhaseResult(
            phase=phase,
            status=PhaseStatus.FAILED,
            message=f"All {max_attempts} retry attempts failed",
            errors=["Maximum retry attempts exceeded"],
        )

    def get_phase_progress(self, phase: PhaseType) -> float:
        """Get current progress for a phase.

        Args:
            phase: Phase to get progress for

        Returns:
            Progress as float between 0.0 and 1.0
        """
        if phase == self._get_current_executing_phase():
            return self.current_phase_progress
        else:
            # Check if phase is completed
            project_state = self.state_manager.load_project_state()
            if project_state:
                if (
                    (phase == PhaseType.INDEXING and project_state.indexing_complete)
                    or (
                        phase == PhaseType.SPECIFICATION and project_state.specification
                    )
                    or (phase == PhaseType.DESIGN and project_state.design)
                    or (phase == PhaseType.IMPLEMENTATION and project_state.tasks)
                ):
                    return 1.0

            return 0.0

    def _get_current_executing_phase(self) -> PhaseType | None:
        """Get the currently executing phase.

        Returns:
            Currently executing phase or None
        """
        # This would be tracked during phase execution
        # For now, return None as we don't have active tracking
        return None
