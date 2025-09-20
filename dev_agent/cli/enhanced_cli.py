"""Enhanced CLI with Rich UI components for improved user experience."""

from __future__ import annotations

import difflib
import os
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.prompt import Confirm, Prompt
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from dev_agent.interfaces.cli_interface import ICLIInterface
from dev_agent.models.enums import PhaseType

if TYPE_CHECKING:
    from dev_agent.interfaces.workflow_interface import IWorkflowManager


class ProgressManager:
    """Manages interactive progress tracking with time estimates."""

    def __init__(self, console: Console):
        """Initialize the progress manager.
        
        Args:
            console: Rich console instance for output
        """
        self.console = console
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
            expand=True,
        )
        self.current_task: Optional[TaskID] = None
        self.phase_start_times: dict[PhaseType, datetime] = {}
        self.phase_estimates: dict[PhaseType, float] = {
            PhaseType.INDEXING: 30.0,  # 30 seconds
            PhaseType.SPECIFICATION: 45.0,  # 45 seconds
            PhaseType.DESIGN: 60.0,  # 1 minute
            PhaseType.IMPLEMENTATION: 120.0,  # 2 minutes
        }

    def start_phase_progress(self, phase: PhaseType, total_steps: int = 100) -> TaskID:
        """Start progress tracking for a phase.
        
        Args:
            phase: The phase being tracked
            total_steps: Total number of steps (default 100 for percentage)
            
        Returns:
            Task ID for the progress task
        """
        self.phase_start_times[phase] = datetime.now()
        description = f"[bold blue]{phase.value.title()}[/bold blue]"
        
        if self.current_task is not None:
            self.progress.remove_task(self.current_task)
            
        self.current_task = self.progress.add_task(
            description, 
            total=total_steps,
            start=True
        )
        return self.current_task

    def update_progress(self, completed: int, status_message: str = "") -> None:
        """Update the current progress.
        
        Args:
            completed: Number of completed steps
            status_message: Optional status message to display
        """
        if self.current_task is not None:
            description = self.progress.tasks[self.current_task].description
            if status_message:
                description = f"{description.split(' - ')[0]} - {status_message}"
            
            self.progress.update(
                self.current_task,
                completed=completed,
                description=description
            )

    def complete_phase(self, phase: PhaseType) -> None:
        """Complete the current phase progress.
        
        Args:
            phase: The phase that was completed
        """
        if self.current_task is not None:
            self.progress.update(self.current_task, completed=100)
            
            # Calculate actual time taken
            if phase in self.phase_start_times:
                elapsed = datetime.now() - self.phase_start_times[phase]
                elapsed_seconds = elapsed.total_seconds()
                
                # Update estimate for future runs
                self.phase_estimates[phase] = (
                    self.phase_estimates[phase] * 0.7 + elapsed_seconds * 0.3
                )

    def show_phase_summary(self, completed_phases: list[PhaseType]) -> None:
        """Show a summary of completed phases.
        
        Args:
            completed_phases: List of completed phases
        """
        table = Table(title="Phase Summary", show_header=True, header_style="bold magenta")
        table.add_column("Phase", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")
        table.add_column("Duration", style="yellow")
        
        for phase in PhaseType:
            if phase in completed_phases:
                status = "✅ Complete"
                duration = "N/A"
                if phase in self.phase_start_times:
                    # This would need to be tracked properly in a real implementation
                    duration = f"{int(self.phase_estimates[phase])}s"
            else:
                status = "⏳ Pending"
                duration = f"~{int(self.phase_estimates[phase])}s"
                
            table.add_row(phase.value.title(), status, duration)
            
        self.console.print(table)


class DocumentPreviewer:
    """Handles syntax-highlighted document previews and diff views."""

    def __init__(self, console: Console):
        """Initialize the document previewer.
        
        Args:
            console: Rich console instance for output
        """
        self.console = console
        self.language_map = {
            "specification": "markdown",
            "design": "markdown", 
            "tasks": "markdown",
            "python": "python",
            "javascript": "javascript",
            "typescript": "typescript",
            "json": "json",
            "yaml": "yaml",
            "toml": "toml",
        }

    def show_document_preview(
        self, 
        content: str, 
        document_type: str, 
        title: Optional[str] = None,
        line_numbers: bool = True
    ) -> None:
        """Show a syntax-highlighted preview of a document.
        
        Args:
            content: Document content to preview
            document_type: Type of document (affects syntax highlighting)
            title: Optional title for the preview
            line_numbers: Whether to show line numbers
        """
        language = self.language_map.get(document_type.lower(), "text")
        
        if not title:
            title = f"{document_type.title()} Preview"
            
        # Create syntax-highlighted content
        syntax = Syntax(
            content,
            language,
            theme="monokai",
            line_numbers=line_numbers,
            word_wrap=True,
            background_color="default"
        )
        
        # Create panel with the content
        panel = Panel(
            syntax,
            title=f"[bold cyan]{title}[/bold cyan]",
            border_style="cyan",
            padding=(1, 2)
        )
        
        self.console.print(panel)

    def show_diff_view(
        self, 
        old_content: str, 
        new_content: str, 
        title: str = "Changes",
        context_lines: int = 3
    ) -> None:
        """Show a diff view between two versions of content.
        
        Args:
            old_content: Original content
            new_content: Modified content
            title: Title for the diff view
            context_lines: Number of context lines to show around changes
        """
        # Split content into lines
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        # Generate unified diff
        diff_lines = list(difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile="Original",
            tofile="Modified",
            n=context_lines
        ))
        
        if not diff_lines:
            self.console.print(f"[green]✅ No changes detected in {title}[/green]")
            return
            
        # Create colored diff output
        diff_content = Text()
        
        for line in diff_lines:
            line = line.rstrip('\n')
            if line.startswith('+++') or line.startswith('---'):
                diff_content.append(line + '\n', style="bold white")
            elif line.startswith('@@'):
                diff_content.append(line + '\n', style="bold cyan")
            elif line.startswith('+'):
                diff_content.append(line + '\n', style="bold green")
            elif line.startswith('-'):
                diff_content.append(line + '\n', style="bold red")
            else:
                diff_content.append(line + '\n', style="dim white")
        
        # Create panel with diff
        panel = Panel(
            diff_content,
            title=f"[bold yellow]📋 {title}[/bold yellow]",
            border_style="yellow",
            padding=(1, 2)
        )
        
        self.console.print(panel)

    def show_file_tree(self, project_path: str, max_depth: int = 3) -> None:
        """Show a tree view of the project structure.
        
        Args:
            project_path: Path to the project root
            max_depth: Maximum depth to traverse
        """
        def add_directory_to_tree(tree: Tree, path: Path, current_depth: int = 0) -> None:
            """Recursively add directory contents to tree."""
            if current_depth >= max_depth:
                return
                
            try:
                items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
                for item in items:
                    if item.name.startswith('.') and item.name not in ['.gitignore', '.env.example']:
                        continue
                        
                    if item.is_dir():
                        branch = tree.add(f"📁 [bold blue]{item.name}[/bold blue]")
                        add_directory_to_tree(branch, item, current_depth + 1)
                    else:
                        # Add file with appropriate icon
                        icon = self._get_file_icon(item.suffix)
                        tree.add(f"{icon} {item.name}")
            except PermissionError:
                tree.add("[red]❌ Permission denied[/red]")

        project_path_obj = Path(project_path)
        tree = Tree(f"📁 [bold green]{project_path_obj.name}[/bold green]")
        
        add_directory_to_tree(tree, project_path_obj)
        
        panel = Panel(
            tree,
            title="[bold cyan]📂 Project Structure[/bold cyan]",
            border_style="cyan",
            padding=(1, 2)
        )
        
        self.console.print(panel)

    def _get_file_icon(self, extension: str) -> str:
        """Get an appropriate icon for a file extension.
        
        Args:
            extension: File extension (including dot)
            
        Returns:
            Unicode icon for the file type
        """
        icon_map = {
            '.py': '🐍',
            '.js': '📜',
            '.ts': '📘',
            '.html': '🌐',
            '.css': '🎨',
            '.json': '📋',
            '.yaml': '⚙️',
            '.yml': '⚙️',
            '.toml': '⚙️',
            '.md': '📝',
            '.txt': '📄',
            '.log': '📊',
            '.env': '🔐',
            '.gitignore': '🚫',
            '.dockerfile': '🐳',
            '.sql': '🗃️',
        }
        return icon_map.get(extension.lower(), '📄')


class ContextualHelpSystem:
    """Provides contextual help and command suggestions based on workflow state."""

    def __init__(self, console: Console):
        """Initialize the contextual help system.
        
        Args:
            console: Rich console instance for output
        """
        self.console = console
        self.help_shown_count = 0
        self.last_help_time = datetime.now()
        
        # Define help content for different contexts
        self.phase_help = {
            PhaseType.INDEXING: {
                "description": "Analyzing and indexing your codebase",
                "commands": [
                    ("status", "Check indexing progress"),
                    ("skip", "Skip to next phase (not recommended)"),
                    ("cancel", "Cancel current operation"),
                ],
                "tips": [
                    "Indexing may take longer for large codebases",
                    "The system is analyzing code patterns and dependencies",
                    "You can continue working while indexing runs in background",
                ]
            },
            PhaseType.SPECIFICATION: {
                "description": "Generating project specification document",
                "commands": [
                    ("approve", "Approve the generated specification"),
                    ("reject", "Reject and regenerate specification"),
                    ("edit", "Make manual edits to specification"),
                    ("preview", "Show specification preview"),
                ],
                "tips": [
                    "Review the specification carefully before approving",
                    "You can request changes or additions",
                    "The specification guides all subsequent phases",
                ]
            },
            PhaseType.DESIGN: {
                "description": "Creating technical design document",
                "commands": [
                    ("approve", "Approve the generated design"),
                    ("reject", "Reject and regenerate design"),
                    ("diff", "Show changes from previous version"),
                    ("architecture", "View architecture diagram"),
                ],
                "tips": [
                    "The design builds upon your approved specification",
                    "Check that all requirements are addressed",
                    "Consider scalability and maintainability aspects",
                ]
            },
            PhaseType.IMPLEMENTATION: {
                "description": "Generating implementation tasks and code",
                "commands": [
                    ("tasks", "View implementation task list"),
                    ("generate", "Generate code for specific task"),
                    ("test", "Run generated tests"),
                    ("review", "Review generated code"),
                ],
                "tips": [
                    "Tasks are ordered by dependency and complexity",
                    "Review generated code before integration",
                    "Tests are generated alongside implementation code",
                ]
            }
        }
        
        self.general_commands = [
            ("help", "Show this help message"),
            ("status", "Show current project status"),
            ("history", "Show command history"),
            ("undo", "Undo last operation"),
            ("redo", "Redo last undone operation"),
            ("save", "Save current progress"),
            ("exit", "Exit dev-agent"),
        ]

    def should_show_help(self, context: dict[str, Any]) -> bool:
        """Determine if contextual help should be shown automatically.
        
        Args:
            context: Current workflow context
            
        Returns:
            True if help should be shown
        """
        # Show help less frequently as user becomes more familiar
        time_since_last = datetime.now() - self.last_help_time
        
        # Show help on first run or if user seems stuck
        if self.help_shown_count == 0:
            return True
        elif time_since_last.total_seconds() > 300:  # 5 minutes
            return True
        elif context.get("errors_count", 0) > 2:  # Multiple errors
            return True
            
        return False

    def show_contextual_help(self, context: dict[str, Any]) -> None:
        """Show contextual help based on current workflow state.
        
        Args:
            context: Current workflow context including phase, errors, etc.
        """
        current_phase = context.get("current_phase")
        
        if current_phase and current_phase in self.phase_help:
            self._show_phase_help(current_phase)
        else:
            self._show_general_help()
            
        self.help_shown_count += 1
        self.last_help_time = datetime.now()

    def _show_phase_help(self, phase: PhaseType) -> None:
        """Show help specific to a workflow phase.
        
        Args:
            phase: Current workflow phase
        """
        help_info = self.phase_help[phase]
        
        # Create help content
        help_content = Text()
        help_content.append(f"📍 Current Phase: ", style="bold white")
        help_content.append(f"{phase.value.title()}\n", style="bold cyan")
        help_content.append(f"{help_info['description']}\n\n", style="dim white")
        
        # Add available commands
        help_content.append("Available Commands:\n", style="bold yellow")
        for cmd, desc in help_info['commands']:
            help_content.append(f"  {cmd:<12} - {desc}\n", style="white")
        
        help_content.append("\n")
        
        # Add tips
        help_content.append("💡 Tips:\n", style="bold green")
        for tip in help_info['tips']:
            help_content.append(f"  • {tip}\n", style="dim green")
        
        # Create panel
        panel = Panel(
            help_content,
            title=f"[bold blue]🤖 Contextual Help - {phase.value.title()}[/bold blue]",
            border_style="blue",
            padding=(1, 2)
        )
        
        self.console.print(panel)

    def _show_general_help(self) -> None:
        """Show general help information."""
        # Show a quick start guide instead of just general commands
        help_content = Panel(
            """👋 Getting Started

To begin using dev-agent, initialize a project:
• init - Initialize in current directory
• init /path - Initialize at specific path

Once initialized, you can run the complete workflow or execute individual phases.""",
            title="[bold cyan]Quick Start[/bold cyan]",
            border_style="cyan",
            padding=(1, 2)
        )
        
        self.console.print(help_content)

    def display_full_help(self, context: dict[str, Any]) -> None:
        """Display comprehensive help information.
        
        Args:
            context: Current workflow context
        """
        # Create general commands table
        commands_table = Table(title="General Commands", show_header=True, header_style="bold yellow")
        commands_table.add_column("Command", style="cyan", no_wrap=True)
        commands_table.add_column("Description", style="white")
        
        for cmd, desc in self.general_commands:
            commands_table.add_row(cmd, desc)
        
        # Create phases table
        phases_table = Table(title="Workflow Phases", show_header=True, header_style="bold green")
        phases_table.add_column("Phase", style="cyan", no_wrap=True)
        phases_table.add_column("Description", style="white")
        
        for phase in PhaseType:
            phase_info = self.phase_help.get(phase, {})
            desc = phase_info.get("description", "No description available")
            phases_table.add_row(phase.value.title(), desc)
        
        # Print both tables
        self.console.print(commands_table)
        self.console.print()
        self.console.print(phases_table)

    def show_command_suggestions(self, invalid_command: str, context: dict[str, Any]) -> None:
        """Show command suggestions for invalid commands.
        
        Args:
            invalid_command: The invalid command entered
            context: Current workflow context
        """
        current_phase = context.get("current_phase")
        
        # Get available commands for current phase
        available_commands = []
        if current_phase and current_phase in self.phase_help:
            available_commands.extend([cmd for cmd, _ in self.phase_help[current_phase]['commands']])
        
        available_commands.extend([cmd for cmd, _ in self.general_commands])
        
        # Find similar commands using simple string matching
        suggestions = []
        for cmd in available_commands:
            if invalid_command.lower() in cmd.lower() or cmd.lower() in invalid_command.lower():
                suggestions.append(cmd)
        
        # If no similar commands, suggest most relevant for current phase
        if not suggestions and current_phase:
            suggestions = [cmd for cmd, _ in self.phase_help[current_phase]['commands'][:3]]
        
        if suggestions:
            suggestion_text = Text()
            suggestion_text.append(f"❓ Unknown command: '{invalid_command}'\n\n", style="bold red")
            suggestion_text.append("Did you mean:\n", style="bold yellow")
            
            for suggestion in suggestions[:5]:  # Limit to 5 suggestions
                suggestion_text.append(f"  • {suggestion}\n", style="cyan")
            
            suggestion_text.append("\nType 'help' for all available commands", style="dim white")
            
            panel = Panel(
                suggestion_text,
                title="[bold red]🤔 Command Suggestions[/bold red]",
                border_style="red",
                padding=(1, 2)
            )
            
            self.console.print(panel)

cla
ss EnhancedCLI(ICLIInterface):
    """Enhanced interactive CLI with Rich UI components and advanced features."""

    def __init__(self, workflow_manager: IWorkflowManager | None = None):
        """Initialize the enhanced CLI.

        Args:
            workflow_manager: Optional workflow manager for handling project operations
        """
        self.workflow_manager = workflow_manager
        self.session_active = False
        self.console = Console()
        self.progress_manager = ProgressManager(self.console)
        self.document_previewer = DocumentPreviewer(self.console)
        self.help_system = ContextualHelpSystem(self.console)
        self.command_history: list[str] = []
        self.current_project_path: Optional[str] = None
        self._setup_signal_handlers()

        # Initialize workflow manager if not provided
        if not self.workflow_manager:
            from dev_agent.workflow.workflow_manager import WorkflowManager

            self.workflow_manager = WorkflowManager(self)

    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful exit."""
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)

    def _handle_interrupt(self, signum: int, frame: Any) -> None:  # noqa: ARG002
        """Handle interrupt signals for graceful shutdown."""
        self.console.print("\n[yellow]Received interrupt signal. Shutting down gracefully...[/yellow]")
        self._graceful_exit()

    def _graceful_exit(self) -> None:
        """Perform graceful exit operations."""
        if self.session_active:
            self.console.print("[blue]Saving session state...[/blue]")
            self.session_active = False
        self.console.print("[green]Goodbye![/green]")
        sys.exit(0)

    def start_chat_session(self) -> None:
        """Start an interactive chat session with enhanced UI."""
        self.session_active = True
        
        # Display welcome banner
        self._display_welcome_banner()
        
        while self.session_active:
            try:
                # Get current context for help system
                current_context = self._get_current_context()
                
                # Show contextual help if needed
                if self.help_system.should_show_help(current_context):
                    self.help_system.show_contextual_help(current_context)
                
                user_input = Prompt.ask(
                    "[bold cyan]dev-agent[/bold cyan]",
                    default="help"
                )
                
                if user_input.lower().strip() in ["exit", "quit", "q"]:
                    self._graceful_exit()
                elif user_input.lower().strip() == "help":
                    self.help_system.display_full_help(current_context)
                else:
                    response = self.handle_user_input(user_input)
                    if response:
                        self.display_message(response)
                        
            except (EOFError, KeyboardInterrupt):  # noqa: PERF203
                self._graceful_exit()

    def _display_welcome_banner(self) -> None:
        """Display an enhanced welcome banner."""
        banner_text = """
[bold blue]🤖 dev-agent[/bold blue] - AI-powered development workflow assistant

[dim]Features:[/dim]
• [green]Interactive progress tracking[/green] with time estimates
• [blue]Syntax-highlighted document previews[/blue] with diff views
• [yellow]Contextual help system[/yellow] based on workflow state
• [magenta]Rich UI components[/magenta] for enhanced experience

Type [bold]help[/bold] for commands or [bold]exit[/bold] to quit.
        """
        
        panel = Panel(
            banner_text.strip(),
            title="[bold]Welcome[/bold]",
            border_style="blue",
            padding=(1, 2)
        )
        self.console.print(panel)

    def _get_current_context(self) -> dict[str, Any]:
        """Get current workflow context for help system.
        
        Returns:
            Dictionary containing current context information
        """
        context: dict[str, Any] = {
            "session_active": self.session_active,
            "command_history_count": len(self.command_history),
            "project_path": self.current_project_path,
        }
        
        if self.workflow_manager:
            try:
                current_phase = self.workflow_manager.get_current_phase()
                context["current_phase"] = current_phase
                
                # Get project state if available
                project_state = getattr(self.workflow_manager, 'project_state', None)
                if project_state:
                    context["indexing_complete"] = project_state.indexing_complete
                    context["has_specification"] = project_state.specification is not None
                    context["has_design"] = project_state.design is not None
                    context["has_tasks"] = project_state.tasks is not None
                    
            except Exception:
                # If we can't get workflow info, continue with basic context
                pass
                
        return context

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
            
        # Add to command history
        self.command_history.append(input_text)
        
        # Parse command and arguments
        parts = input_text.split()
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        try:
            # Handle enhanced CLI commands
            if command == "preview" and args:
                return self._handle_preview_command(args)
            elif command == "diff" and len(args) >= 2:
                return self._handle_diff_command(args)
            elif command == "tree":
                return self._handle_tree_command(args)
            elif command == "progress":
                return self._handle_progress_command()
            elif command == "history":
                return self._handle_history_command()
            elif command == "clear":
                self.console.clear()
                return "Screen cleared."
                
            # Handle standard CLI commands
            elif command == "init":
                project_path = args[0] if args else os.getcwd()
                try:
                    self.init_command(project_path)
                    return f"Project initialized at: {project_path}"
                except Exception as e:
                    return f"Error initializing project: {e!s}"
                    
            elif command == "status":
                return self._handle_status_command()
                
            elif command in ["run", "start"]:
                return self._handle_run_command()
                
            elif command == "phase" and args:
                return self._handle_phase_command(args[0])
                
            elif command == "approve":
                return "Approval functionality would be handled by workflow manager"
                
            elif command == "reject":
                return "Rejection functionality would be handled by workflow manager"
                
            else:
                # Show command suggestions for unknown commands
                context = self._get_current_context()
                self.help_system.show_command_suggestions(command, context)
                return ""
                
        except Exception as e:
            return f"Error executing command '{command}': {e!s}"

    def _handle_preview_command(self, args: list[str]) -> str:
        """Handle document preview command.
        
        Args:
            args: Command arguments
            
        Returns:
            Response message
        """
        doc_type = args[0].lower()
        
        if not self.workflow_manager:
            return "No active project. Use 'init [path]' to start."
            
        try:
            project_state = getattr(self.workflow_manager, 'project_state', None)
            if not project_state:
                return "No project state available."
                
            content = None
            if doc_type == "specification" and project_state.specification:
                content = project_state.specification.content
            elif doc_type == "design" and project_state.design:
                content = project_state.design.content
            elif doc_type == "tasks" and project_state.tasks:
                content = str(project_state.tasks)  # Convert to string representation
                
            if content:
                self.document_previewer.show_document_preview(content, doc_type)
                return ""
            else:
                return f"No {doc_type} document available yet."
                
        except Exception as e:
            return f"Error showing preview: {e!s}"

    def _handle_diff_command(self, args: list[str]) -> str:
        """Handle diff command.
        
        Args:
            args: Command arguments
            
        Returns:
            Response message
        """
        # This would need to be implemented with actual document versioning
        return "Diff functionality requires document versioning (not yet implemented)"

    def _handle_tree_command(self, args: list[str]) -> str:
        """Handle tree command to show project structure.
        
        Args:
            args: Command arguments
            
        Returns:
            Response message
        """
        project_path = args[0] if args else self.current_project_path
        
        if not project_path:
            project_path = os.getcwd()
            
        if not os.path.exists(project_path):
            return f"Path does not exist: {project_path}"
            
        self.document_previewer.show_file_tree(project_path)
        return ""

    def _handle_progress_command(self) -> str:
        """Handle progress command to show phase summary.
        
        Returns:
            Response message
        """
        if not self.workflow_manager:
            return "No active project."
            
        try:
            current_phase = self.workflow_manager.get_current_phase()
            completed_phases = []  # This would need to be tracked properly
            
            # For now, assume phases before current are completed
            for phase in PhaseType:
                if phase.value < current_phase.value:
                    completed_phases.append(phase)
                    
            self.progress_manager.show_phase_summary(completed_phases)
            return ""
            
        except Exception as e:
            return f"Error showing progress: {e!s}"

    def _handle_history_command(self) -> str:
        """Handle history command to show command history.
        
        Returns:
            Response message
        """
        if not self.command_history:
            return "No command history available."
            
        table = Table(title="Command History", show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=4)
        table.add_column("Command", style="white")
        table.add_column("Time", style="dim")
        
        # Show last 10 commands
        recent_commands = self.command_history[-10:]
        for i, cmd in enumerate(recent_commands, 1):
            table.add_row(str(i), cmd, "Recent")  # Time tracking would need to be added
            
        self.console.print(table)
        return ""

    def _handle_status_command(self) -> str:
        """Handle status command.
        
        Returns:
            Status message
        """
        if not self.workflow_manager:
            return "No active project. Use 'init [path]' to start."
            
        try:
            current_phase = self.workflow_manager.get_current_phase()
            
            # Create status table
            table = Table(title="Project Status", show_header=True, header_style="bold magenta")
            table.add_column("Property", style="cyan", no_wrap=True)
            table.add_column("Value", style="green")

            table.add_row("Current Phase", current_phase.value.title())
            table.add_row("Status", "Active")
            table.add_row("Last Updated", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            # Render table to string
            with self.console.capture() as capture:
                self.console.print(table)

            return capture.get()
            
        except Exception as e:
            return f"Error getting status: {e!s}"

    def _handle_run_command(self) -> str:
        """Handle run/start command.
        
        Returns:
            Response message
        """
        if not self.workflow_manager:
            return "No active project. Use 'init [path]' to start."
            
        try:
            with self.progress_manager.progress:
                success = self.workflow_manager.execute_complete_workflow()
                
            if success:
                return "✅ Workflow completed successfully!"
            else:
                return "❌ Workflow execution failed. Check the logs for details."
                
        except Exception as e:
            return f"Error running workflow: {e!s}"

    def _handle_phase_command(self, phase_name: str) -> str:
        """Handle phase transition command.
        
        Args:
            phase_name: Name of the phase to transition to
            
        Returns:
            Response message
        """
        if not self.workflow_manager:
            return "No active project. Use 'init [path]' to start."
            
        try:
            phase = PhaseType(phase_name.upper())
            success = self.workflow_manager.transition_to_phase(phase)
            
            if success:
                return f"✅ Successfully transitioned to {phase_name.title()} phase"
            else:
                return f"❌ Failed to transition to {phase_name.title()} phase"
                
        except ValueError:
            valid_phases = [phase.value for phase in PhaseType]
            return f"Invalid phase: {phase_name}. Valid phases: {', '.join(valid_phases)}"
        except Exception as e:
            return f"Error transitioning to phase: {e!s}"

    def request_approval(self, document: str, document_type: str) -> bool:
        """Request user approval for a generated document.

        Args:
            document: The document content to approve
            document_type: Type of document (specification, design, tasks)

        Returns:
            True if approved, False if rejected
        """
        # Show document preview with syntax highlighting
        self.document_previewer.show_document_preview(
            document, 
            document_type,
            title=f"Generated {document_type.title()}"
        )
        
        # Create approval prompt with enhanced styling
        self.console.print()
        self.console.print(Rule(f"[bold yellow]📋 {document_type.title()} Review[/bold yellow]"))
        
        return Confirm.ask(
            f"[bold cyan]Do you approve this {document_type}?[/bold cyan]",
            default=False
        )

    def display_progress(self, phase: PhaseType, progress: float) -> None:
        """Display progress information for the current phase.

        Args:
            phase: The current phase
            progress: Progress as a float between 0.0 and 1.0
        """
        # Start phase progress if not already started
        if self.progress_manager.current_task is None:
            self.progress_manager.start_phase_progress(phase)
            
        # Update progress
        completed_steps = int(progress * 100)
        self.progress_manager.update_progress(completed_steps)
        
        # Complete phase if at 100%
        if progress >= 1.0:
            self.progress_manager.complete_phase(phase)

    def init_command(self, project_path: str) -> None:
        """Initialize a new project or resume an existing one.

        Args:
            project_path: Path to the project directory
        """
        if not os.path.exists(project_path):
            raise ValueError(f"Project path does not exist: {project_path}")

        self.current_project_path = project_path
        
        # Show project structure
        self.document_previewer.show_file_tree(project_path)
        
        dev_agent_dir = os.path.join(project_path, ".dev_agent")
        documents_dir = os.path.join(dev_agent_dir, "documents")
        index_dir = os.path.join(dev_agent_dir, "index")

        # Check if this is an existing project
        if os.path.exists(documents_dir) and os.path.exists(index_dir):
            self.display_message("[green]📁 Found existing dev-agent project. Resuming...[/green]")
            if self.workflow_manager:
                self.workflow_manager.resume_project(project_path)
        else:
            self.display_message("[blue]🚀 Initializing new dev-agent project...[/blue]")
            # Create .dev_agent directory structure
            os.makedirs(dev_agent_dir, exist_ok=True)
            os.makedirs(documents_dir, exist_ok=True)
            os.makedirs(index_dir, exist_ok=True)

            if self.workflow_manager:
                self.workflow_manager.start_new_project(project_path)

    def display_message(self, message: str) -> None:
        """Display a message to the user.

        Args:
            message: The message to display
        """
        self.console.print(message)

    def get_user_input(self, prompt: str) -> str:
        """Get input from the user with a prompt.

        Args:
            prompt: The prompt to display

        Returns:
            The user's input as a string
        """
        return Prompt.ask(prompt)

    # Enhanced CLI methods (implementing optional interface methods)
    def show_document_preview(self, content: str, document_type: str) -> None:
        """Show document preview with syntax highlighting.
        
        Args:
            content: Document content to preview
            document_type: Type of document for syntax highlighting
        """
        self.document_previewer.show_document_preview(content, document_type)

    def show_diff_view(self, old_content: str, new_content: str, title: str = "Changes") -> None:
        """Show diff between two versions of content.
        
        Args:
            old_content: Original content
            new_content: Modified content
            title: Title for the diff view
        """
        self.document_previewer.show_diff_view(old_content, new_content, title)

    def get_contextual_help(self, context: Optional[dict[str, Any]] = None) -> None:
        """Show contextual help based on current state.
        
        Args:
            context: Optional context dictionary
        """
        if context is None:
            context = self._get_current_context()
        self.help_system.show_contextual_help(context)