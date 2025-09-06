"""Interface for state management components."""

from abc import ABC, abstractmethod
from typing import Optional
from ..models.enums import PhaseType, PhaseStatus, DocumentType
from ..models.project_state import ProjectState


class IStateManager(ABC):
    """Interface for project state management."""
    
    @abstractmethod
    def save_project_state(self, state: ProjectState) -> bool:
        """Save the current project state to persistent storage."""
        pass
    
    @abstractmethod
    def load_project_state(self) -> Optional[ProjectState]:
        """Load project state from persistent storage."""
        pass
    
    @abstractmethod
    def update_phase_status(self, phase: PhaseType, status: PhaseStatus) -> bool:
        """Update the status of a specific phase."""
        pass
    
    @abstractmethod
    def save_document(self, document: str, doc_type: DocumentType) -> bool:
        """Save a generated document to storage."""
        pass
    
    @abstractmethod
    def load_document(self, doc_type: DocumentType) -> Optional[str]:
        """Load a document from storage."""
        pass
    
    @abstractmethod
    def track_task_progress(self, task_id: str, progress: 'TaskProgress') -> bool:
        """Track progress of an implementation task."""
        pass
    
    @abstractmethod
    def initialize_project_directory(self, project_path: str) -> bool:
        """Initialize the .dev_agent directory structure."""
        pass