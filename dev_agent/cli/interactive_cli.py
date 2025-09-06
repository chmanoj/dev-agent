"""Interactive CLI implementation for dev-agent."""

import os
import sys
import signal
from typing import Optional
from ..interfaces.cli_interface import ICLIInterface
from ..interfaces.workflow_interface import IWorkflowManager
from ..models.enums import PhaseType


class InteractiveCLI(ICLIInterface):
    """Interactive command-line interface with chat-based interaction."""
    
    def __init__(self, workflow_manager: Optional[IWorkflowManager] = None):
        """Initialize the interactive CLI.
        
        Args:
            workflow_manager: Optional workflow manager for handling project operations
        """
        self.workflow_manager = workflow_manager
        self.session_active = False
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful exit."""
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)
    
    def _handle_interrupt(self, signum: int, frame) -> None:
        """Handle interrupt signals for graceful shutdown."""
        print("\n\nReceived interrupt signal. Shutting down gracefully...")
        self._graceful_exit()
    
    def _graceful_exit(self) -> None:
        """Perform graceful exit operations."""
        if self.session_active:
            print("Saving session state...")
            # Session state will be saved by workflow manager
            self.session_active = False
        print("Goodbye!")
        sys.exit(0)
    
    def start_chat_session(self) -> None:
        """Start an interactive chat session with the user."""
        self.session_active = True
        self.display_message("Welcome to dev-agent! Type 'help' for available commands or 'exit' to quit.")
        
        while self.session_active:
            try:
                user_input = self.get_user_input("dev-agent> ")
                if user_input.lower().strip() in ['exit', 'quit', 'q']:
                    self._graceful_exit()
                elif user_input.lower().strip() == 'help':
                    self._display_help()
                else:
                    response = self.handle_user_input(user_input)
                    if response:
                        self.display_message(response)
            except EOFError:
                # Handle Ctrl+D
                self._graceful_exit()
            except KeyboardInterrupt:
                # Handle Ctrl+C
                self._graceful_exit()
    
    def handle_user_input(self, input_text: str) -> str:
        """Process user input and return response.
        
        Args:
            input_text: The user's input text
            
        Returns:
            Response message for the user
        """
        input_text = input_text.strip()
        
        if not input_text:
            return ""
        
        # Handle init command
        if input_text.startswith('init'):
            parts = input_text.split()
            if len(parts) > 1:
                project_path = parts[1]
            else:
                project_path = os.getcwd()
            
            try:
                self.init_command(project_path)
                return f"Project initialized at: {project_path}"
            except Exception as e:
                return f"Error initializing project: {str(e)}"
        
        # Handle status command
        elif input_text == 'status':
            if self.workflow_manager:
                current_phase = self.workflow_manager.get_current_phase()
                return f"Current phase: {current_phase.value}"
            else:
                return "No active project. Use 'init [path]' to start."
        
        # Default response for unrecognized commands
        else:
            return f"Unknown command: '{input_text}'. Type 'help' for available commands."
    
    def request_approval(self, document: str, document_type: str) -> bool:
        """Request user approval for a generated document.
        
        Args:
            document: The document content to approve
            document_type: Type of document (specification, design, tasks)
            
        Returns:
            True if approved, False if rejected
        """
        self.display_message(f"\n--- Generated {document_type.title()} ---")
        self.display_message(document)
        self.display_message(f"--- End of {document_type.title()} ---\n")
        
        while True:
            response = self.get_user_input(f"Do you approve this {document_type}? (y/n): ").lower().strip()
            
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                self.display_message("Please enter 'y' for yes or 'n' for no.")
    
    def display_progress(self, phase: PhaseType, progress: float) -> None:
        """Display progress information for the current phase.
        
        Args:
            phase: The current phase
            progress: Progress as a float between 0.0 and 1.0
        """
        progress_percent = int(progress * 100)
        bar_length = 30
        filled_length = int(bar_length * progress)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        
        print(f"\r{phase.value.title()}: |{bar}| {progress_percent}%", end='', flush=True)
        
        if progress >= 1.0:
            print()  # New line when complete
    
    def init_command(self, project_path: str) -> None:
        """Initialize a new project or resume an existing one.
        
        Args:
            project_path: Path to the project directory
        """
        if not os.path.exists(project_path):
            raise ValueError(f"Project path does not exist: {project_path}")
        
        dev_agent_dir = os.path.join(project_path, '.dev_agent')
        
        # Check if this is an existing project
        if os.path.exists(dev_agent_dir):
            self.display_message("Found existing dev-agent project. Resuming...")
            if self.workflow_manager:
                self.workflow_manager.resume_project(project_path)
        else:
            self.display_message("Initializing new dev-agent project...")
            # Create .dev_agent directory structure
            os.makedirs(dev_agent_dir, exist_ok=True)
            os.makedirs(os.path.join(dev_agent_dir, 'documents'), exist_ok=True)
            os.makedirs(os.path.join(dev_agent_dir, 'index'), exist_ok=True)
            
            if self.workflow_manager:
                self.workflow_manager.start_new_project(project_path)
    
    def display_message(self, message: str) -> None:
        """Display a message to the user.
        
        Args:
            message: The message to display
        """
        print(message)
    
    def get_user_input(self, prompt: str) -> str:
        """Get input from the user with a prompt.
        
        Args:
            prompt: The prompt to display
            
        Returns:
            The user's input as a string
        """
        return input(prompt)
    
    def _display_help(self) -> None:
        """Display help information."""
        help_text = """
Available commands:
  init [path]    - Initialize a new project or resume existing (default: current directory)
  status         - Show current project status and phase
  help           - Show this help message
  exit/quit/q    - Exit the application

During workflow phases, you'll be prompted for approval of generated documents.
Use Ctrl+C or Ctrl+D to exit at any time.

Examples:
  init           - Initialize project in current directory
  init /path     - Initialize project at specific path
  status         - Check current workflow phase
        """
        self.display_message(help_text.strip())