"""Interface for CLI components."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..models.enums import PhaseType


class ICLIInterface(ABC):
    """Interface for interactive command-line interface."""

    @abstractmethod
    def start_chat_session(self) -> None:
        """Start an interactive chat session with the user."""
        pass

    @abstractmethod
    def handle_user_input(self, input_text: str) -> str:
        """Process user input and return response."""
        pass

    @abstractmethod
    def request_approval(self, document: str, document_type: str) -> bool:
        """Request user approval for a generated document."""
        pass

    @abstractmethod
    def display_progress(self, phase: PhaseType, progress: float) -> None:
        """Display progress information for the current phase."""
        pass

    @abstractmethod
    def init_command(self, project_path: str) -> None:
        """Initialize a new project or resume an existing one."""
        pass

    @abstractmethod
    def display_message(self, message: str) -> None:
        """Display a message to the user."""
        pass

    @abstractmethod
    def get_user_input(self, prompt: str) -> str:
        """Get input from the user with a prompt."""
        pass

    # Enhanced CLI methods (optional for backward compatibility)
    def show_document_preview(self, content: str, document_type: str) -> None:
        """Show document preview with syntax highlighting (optional enhancement)."""
        pass

    def show_diff_view(self, old_content: str, new_content: str, title: str = "Changes") -> None:
        """Show diff between two versions of content (optional enhancement)."""
        pass

    def get_contextual_help(self, context: Optional[Dict[str, Any]] = None) -> None:
        """Show contextual help based on current state (optional enhancement)."""
        pass
