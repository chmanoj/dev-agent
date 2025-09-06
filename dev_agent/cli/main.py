"""Main CLI entry point for dev-agent."""

import argparse
import os
import sys
from typing import Optional
from .interactive_cli import InteractiveCLI
from .session_manager import SessionManager
from ..models.enums import PhaseType


class CLIApplication:
    """Main CLI application coordinator."""
    
    def __init__(self):
        """Initialize the CLI application."""
        self.cli: Optional[InteractiveCLI] = None
        self.session_manager: Optional[SessionManager] = None
        self.project_path: Optional[str] = None
    
    def run(self, args: Optional[list] = None) -> int:
        """Run the CLI application.
        
        Args:
            args: Command line arguments (defaults to sys.argv)
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            parsed_args = self._parse_arguments(args)
            
            if parsed_args.command == 'init':
                return self._handle_init_command(parsed_args)
            elif parsed_args.command == 'resume':
                return self._handle_resume_command(parsed_args)
            else:
                # Default to interactive mode
                return self._start_interactive_mode(parsed_args.project_path)
                
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            return 1
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _parse_arguments(self, args: Optional[list] = None) -> argparse.Namespace:
        """Parse command line arguments.
        
        Args:
            args: Arguments to parse (defaults to sys.argv)
            
        Returns:
            Parsed arguments namespace
        """
        parser = argparse.ArgumentParser(
            description='dev-agent: AI-powered development workflow assistant',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  dev-agent                    # Start interactive mode in current directory
  dev-agent init               # Initialize project in current directory
  dev-agent init /path/to/proj # Initialize project at specific path
  dev-agent resume             # Resume existing project in current directory
            """
        )
        
        parser.add_argument(
            'command',
            nargs='?',
            choices=['init', 'resume'],
            help='Command to execute (default: interactive mode)'
        )
        
        parser.add_argument(
            'project_path',
            nargs='?',
            default=os.getcwd(),
            help='Path to project directory (default: current directory)'
        )
        
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose output'
        )
        
        return parser.parse_args(args)
    
    def _handle_init_command(self, args: argparse.Namespace) -> int:
        """Handle the init command.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Exit code
        """
        project_path = os.path.abspath(args.project_path)
        
        if not os.path.exists(project_path):
            print(f"Error: Project path does not exist: {project_path}")
            return 1
        
        # Initialize CLI and session manager
        self.project_path = project_path
        self.session_manager = SessionManager(project_path)
        self.cli = InteractiveCLI()
        
        try:
            self.cli.init_command(project_path)
            
            # Start a new session
            session = self.session_manager.start_session(PhaseType.INDEXING)
            print(f"Started new session: {session.session_id}")
            
            # Start interactive mode after initialization
            return self._start_interactive_mode(project_path)
            
        except Exception as e:
            print(f"Failed to initialize project: {e}")
            return 1
    
    def _handle_resume_command(self, args: argparse.Namespace) -> int:
        """Handle the resume command.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Exit code
        """
        project_path = os.path.abspath(args.project_path)
        
        if not os.path.exists(project_path):
            print(f"Error: Project path does not exist: {project_path}")
            return 1
        
        dev_agent_dir = os.path.join(project_path, '.dev_agent')
        if not os.path.exists(dev_agent_dir):
            print(f"Error: No dev-agent project found at {project_path}")
            print("Use 'dev-agent init' to initialize a new project.")
            return 1
        
        # Initialize session manager and try to resume
        self.project_path = project_path
        self.session_manager = SessionManager(project_path)
        
        session = self.session_manager.resume_session()
        if session:
            print(f"Resumed session: {session.session_id}")
            print(f"Current phase: {session.current_phase.value}")
        else:
            print("No previous session found, starting new session...")
            session = self.session_manager.start_session(PhaseType.INDEXING)
        
        # Start interactive mode
        return self._start_interactive_mode(project_path)
    
    def _start_interactive_mode(self, project_path: str) -> int:
        """Start interactive CLI mode.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Exit code
        """
        if not self.session_manager:
            self.session_manager = SessionManager(project_path)
        
        if not self.cli:
            self.cli = InteractiveCLI()
        
        try:
            print(f"Starting interactive mode for project: {project_path}")
            self.cli.start_chat_session()
            return 0
            
        except Exception as e:
            print(f"Error in interactive mode: {e}")
            return 1
        finally:
            if self.session_manager:
                self.session_manager.end_session()


def main() -> int:
    """Main entry point for the CLI application."""
    app = CLIApplication()
    return app.run()


if __name__ == '__main__':
    sys.exit(main())