"""Interfaces for workflow management components."""

from abc import ABC, abstractmethod

from ..models.enums import PhaseType
from ..models.project_state import ProjectState


class IWorkflowManager(ABC):
    """Interface for workflow management."""

    @abstractmethod
    def start_new_project(self, project_path: str) -> ProjectState:
        """Start a new project workflow."""
        pass

    @abstractmethod
    def resume_project(self, project_path: str) -> ProjectState:
        """Resume an existing project workflow."""
        pass

    @abstractmethod
    def transition_to_phase(self, phase: PhaseType) -> bool:
        """Transition to the specified phase."""
        pass

    @abstractmethod
    def require_user_approval(self, content: str, phase: PhaseType) -> bool:
        """Require user approval for phase completion."""
        pass

    @abstractmethod
    def get_current_phase(self) -> PhaseType:
        """Get the current workflow phase."""
        pass

    @abstractmethod
    def execute_complete_workflow(self) -> bool:
        """Execute the complete four-phase workflow."""
        pass


class IPhaseManager(ABC):
    """Interface for managing individual workflow phases."""

    @abstractmethod
    def execute_indexing_phase(self, project_path: str) -> "IndexingResult":
        """Execute the indexing phase."""
        pass

    @abstractmethod
    def execute_specification_phase(
        self, context: "ProjectContext"
    ) -> "SpecificationResult":
        """Execute the specification phase."""
        pass

    @abstractmethod
    def execute_design_phase(self, context: "ProjectContext") -> "DesignResult":
        """Execute the design phase."""
        pass

    @abstractmethod
    def execute_implementation_phase(
        self, context: "ProjectContext"
    ) -> "ImplementationResult":
        """Execute the implementation phase."""
        pass

    @abstractmethod
    def validate_phase_completion(
        self, phase: PhaseType, result: "PhaseResult"
    ) -> bool:
        """Validate that a phase has been completed successfully."""
        pass
