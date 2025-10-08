"""Interactive CLI implementation for dev-agent."""

import os
import signal
import sys
from typing import AsyncIterator

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..interfaces.cli_interface import ICLIInterface
from ..interfaces.workflow_interface import IWorkflowManager
from ..models.enums import PhaseType

console = Console()


class InteractiveCLI(ICLIInterface):
    """Interactive command-line interface with chat-based interaction."""

    def __init__(self, workflow_manager: IWorkflowManager | None = None):
        """Initialize the interactive CLI.

        Args:
            workflow_manager: Optional workflow manager for handling project operations
        """
        self.workflow_manager = workflow_manager
        self.session_active = False
        self._setup_signal_handlers()

        # Initialize workflow manager if not provided
        if not self.workflow_manager:
            from ..config import ConfigManager
            from ..llm.embeddings import AzureEmbeddingClient
            from ..workflow.workflow_manager import WorkflowManager

            # Initialize embedding client for workflow
            config_manager = ConfigManager()
            config = config_manager.get_config()
            
            embedding_client = None
            if config.azure_openai:
                try:
                    embedding_client = AzureEmbeddingClient(config.azure_openai)
                except Exception as e:
                    console.print(
                        f"[yellow]Warning: Could not initialize embedding client: {e}[/yellow]"
                    )
                    console.print(
                        "[yellow]Some features may be limited.[/yellow]"
                    )

            self.workflow_manager = WorkflowManager(self, embedding_client=embedding_client)

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
        console.print(
            "[bold blue]Welcome to dev-agent![/bold blue] Type 'help' for available commands or 'exit' to quit."
        )

        while self.session_active:
            try:
                user_input = self.get_user_input("dev-agent> ")
                if user_input.lower().strip() in ["exit", "quit", "q"]:
                    self._graceful_exit()
                elif user_input.lower().strip() == "help":
                    self._display_help()
                else:
                    response = self.handle_user_input(user_input)
                    if response:
                        console.print(response)
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
        if input_text.startswith("init"):
            parts = input_text.split()
            if len(parts) > 1:
                project_path = parts[1]
            else:
                project_path = os.getcwd()

            try:
                self.init_command(project_path)
                return f"[green]Project initialized at: {project_path}[/green]"
            except Exception as e:
                return f"[red]Error initializing project: {e!s}[/red]"

        # Handle status command
        elif input_text == "status":
            if self.workflow_manager:
                current_phase = self.workflow_manager.get_current_phase()
                return f"[cyan]Current phase: {current_phase.value}[/cyan]"
            else:
                return "[yellow]No active project. Use 'init [path]' to start.[/yellow]"

        # Handle cost report command
        elif input_text.startswith("cost"):
            if self.workflow_manager:
                try:
                    self._display_cost_report()
                    return ""
                except Exception as e:
                    return f"[red]Error generating cost report: {e!s}[/red]"
            else:
                return "[yellow]No active project. Use 'init [path]' to start.[/yellow]"

        # Handle workflow commands
        elif input_text == "run" or input_text == "start":
            if self.workflow_manager:
                try:
                    success = self.workflow_manager.execute_complete_workflow()
                    if success:
                        # Display cost summary after workflow
                        self._display_cost_summary()
                        return "[green]Workflow completed successfully![/green]"
                    else:
                        return "[red]Workflow execution failed. Check the logs for details.[/red]"
                except Exception as e:
                    return f"[red]Error running workflow: {e!s}[/red]"
            else:
                return "[yellow]No active project. Use 'init [path]' to start.[/yellow]"

        elif input_text.startswith("phase "):
            phase_name = input_text[6:].strip().upper()
            if self.workflow_manager:
                try:
                    from ..models.enums import PhaseType

                    # Convert uppercase input to lowercase for enum matching
                    phase = PhaseType(phase_name.lower())
                    success = self.workflow_manager.transition_to_phase(phase)
                    if success:
                        # Display cost summary after phase transition
                        self._display_cost_summary()
                        return f"[green]Successfully transitioned to {phase_name} phase[/green]"
                    else:
                        return f"[red]Failed to transition to {phase_name} phase[/red]"
                except ValueError:
                    return f"[red]Invalid phase: {phase_name}. Valid phases: INDEXING, SPECIFICATION, DESIGN, IMPLEMENTATION[/red]"
                except Exception as e:
                    return f"[red]Error transitioning to phase: {e!s}[/red]"
            else:
                return "[yellow]No active project. Use 'init [path]' to start.[/yellow]"

        # Default response for unrecognized commands
        else:
            return (
                f"[yellow]Unknown command: '{input_text}'. Type 'help' for available commands.[/yellow]"
            )

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
            response = (
                self.get_user_input(f"Do you approve this {document_type}? (y/n): ")
                .lower()
                .strip()
            )

            if response in ["y", "yes"]:
                return True
            elif response in ["n", "no"]:
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
        bar = "█" * filled_length + "-" * (bar_length - filled_length)

        console.print(
            f"\r{phase.value.title()}: |{bar}| {progress_percent}%", end=""
        )

        if progress >= 1.0:
            console.print()  # New line when complete

    def display_streaming_progress(self, phase: PhaseType, message: str = "Processing") -> None:
        """Display streaming progress indicator for LLM operations.

        Args:
            phase: The current phase
            message: Progress message to display
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(f"[cyan]{phase.value.title()}: {message}...", total=None)
            # This will be updated by the caller
            return progress, task

    def display_cost_summary(self, phase: PhaseType | None = None) -> None:
        """Display cost summary after phase completion.

        Args:
            phase: Optional phase to show summary for (None = all phases)
        """
        if not self.workflow_manager:
            return

        try:
            if phase:
                report = self.workflow_manager.cost_tracker.get_phase_report(phase)
                title = f"Cost Summary - {phase.value} Phase"
            else:
                report = self.workflow_manager.cost_tracker.get_report()
                title = "Total Cost Summary"

            # Create a table for cost display
            table = Table(title=title, show_header=True, header_style="bold cyan")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", justify="right", style="green")

            table.add_row("Operations", str(report.operations_count))
            table.add_row(
                "Total Tokens",
                f"{report.total_prompt_tokens + report.total_completion_tokens + report.total_embedding_tokens:,}"
            )
            table.add_row("  Prompt Tokens", f"{report.total_prompt_tokens:,}")
            table.add_row("  Completion Tokens", f"{report.total_completion_tokens:,}")
            table.add_row("  Embedding Tokens", f"{report.total_embedding_tokens:,}")
            table.add_row("Total Cost", f"${report.total_cost:.4f}", style="bold green")

            console.print(table)

            # Check budget warnings
            if self.workflow_manager.cost_tracker.check_budget_threshold():
                current_cost = self.workflow_manager.cost_tracker.get_current_cost()
                if self.workflow_manager.cost_tracker.budget_limit:
                    remaining = self.workflow_manager.cost_tracker.budget_limit - current_cost
                    console.print(
                        f"[yellow]⚠ Budget Warning: ${current_cost:.2f} spent, ${remaining:.2f} remaining[/yellow]"
                    )
                else:
                    console.print(
                        f"[yellow]⚠ Budget threshold exceeded: ${current_cost:.2f} spent[/yellow]"
                    )

        except Exception as e:
            console.print(f"[red]Error displaying cost summary: {e}[/red]")

    def _display_cost_summary(self) -> None:
        """Internal method to display cost summary."""
        self.display_cost_summary()

    def _display_cost_report(self) -> None:
        """Display detailed cost report."""
        if not self.workflow_manager:
            console.print("[yellow]No active project[/yellow]")
            return

        report = self.workflow_manager.cost_tracker.get_report()

        # Create main summary table
        summary_table = Table(title="Complete Cost Report", show_header=True, header_style="bold blue")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", justify="right", style="green")

        summary_table.add_row("Total Operations", str(report.operations_count))
        summary_table.add_row(
            "Total Tokens",
            f"{report.total_prompt_tokens + report.total_completion_tokens + report.total_embedding_tokens:,}"
        )
        summary_table.add_row("  Prompt Tokens", f"{report.total_prompt_tokens:,}")
        summary_table.add_row("  Completion Tokens", f"{report.total_completion_tokens:,}")
        summary_table.add_row("  Embedding Tokens", f"{report.total_embedding_tokens:,}")
        summary_table.add_row("Total Cost", f"${report.total_cost:.4f}", style="bold green")

        console.print(summary_table)

        # Display by phase
        if report.by_phase:
            phase_table = Table(title="Cost by Phase", show_header=True, header_style="bold blue")
            phase_table.add_column("Phase", style="cyan")
            phase_table.add_column("Cost", justify="right", style="green")

            for phase_type, cost in report.by_phase.items():
                phase_table.add_row(phase_type.value, f"${cost:.4f}")

            console.print(phase_table)

        # Display by operation type
        if report.by_operation:
            op_table = Table(title="Operations by Type", show_header=True, header_style="bold blue")
            op_table.add_column("Operation Type", style="cyan")
            op_table.add_column("Count", justify="right", style="green")

            for op_type, count in report.by_operation.items():
                op_table.add_row(op_type, str(count))

            console.print(op_table)

        # Display time range
        console.print(
            f"\n[dim]Period: {report.start_time.strftime('%Y-%m-%d %H:%M:%S')} to "
            f"{report.end_time.strftime('%Y-%m-%d %H:%M:%S')}[/dim]"
        )

    def init_command(self, project_path: str) -> None:
        """Initialize a new project or resume an existing one.

        Args:
            project_path: Path to the project directory
        """
        if not os.path.exists(project_path):
            raise ValueError(f"Project path does not exist: {project_path}")

        dev_agent_dir = os.path.join(project_path, ".dev_agent")
        documents_dir = os.path.join(dev_agent_dir, "documents")
        index_dir = os.path.join(dev_agent_dir, "index")

        # Check if this is an existing project by looking for actual project structure
        if os.path.exists(documents_dir) and os.path.exists(index_dir):
            self.display_message("Found existing dev-agent project. Resuming...")
            if self.workflow_manager:
                self.workflow_manager.resume_project(project_path)
        else:
            self.display_message("Initializing new dev-agent project...")
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
        console.print(message)

    def get_user_input(self, prompt: str) -> str:
        """Get input from the user with a prompt.

        Args:
            prompt: The prompt to display

        Returns:
            The user's input as a string
        """
        return input(prompt)

    async def display_streaming_response(self, stream: AsyncIterator[str]) -> str:
        """Display streaming LLM response in real-time.

        Args:
            stream: Async iterator of response tokens

        Returns:
            Complete response text
        """
        response_text = ""
        
        with Live(console=console, refresh_per_second=10) as live:
            async for token in stream:
                response_text += token
                live.update(Panel(response_text, title="[cyan]Generating Response[/cyan]", border_style="cyan"))
        
        return response_text

    def _display_help(self) -> None:
        """Display help information."""
        help_text = """
[bold blue]Available commands:[/bold blue]
  [cyan]init [path][/cyan]       - Initialize a new project or resume existing (default: current directory)
  [cyan]status[/cyan]            - Show current project status and phase
  [cyan]cost[/cyan]              - Display cost report for Azure OpenAI usage
  [cyan]run/start[/cyan]         - Execute the complete four-phase workflow
  [cyan]phase <PHASE>[/cyan]     - Transition to a specific phase (INDEXING, SPECIFICATION, DESIGN, IMPLEMENTATION)
  [cyan]help[/cyan]              - Show this help message
  [cyan]exit/quit/q[/cyan]       - Exit the application

[bold blue]Workflow Phases:[/bold blue]
  1. [green]INDEXING[/green]       - Analyze and index the codebase
  2. [green]SPECIFICATION[/green]  - Generate requirements specification
  3. [green]DESIGN[/green]         - Create technical design document
  4. [green]IMPLEMENTATION[/green] - Generate implementation tasks

[bold blue]Cost Tracking:[/bold blue]
  Token usage and costs are tracked automatically for all Azure OpenAI operations.
  Use the [cyan]cost[/cyan] command to view detailed usage reports.

During workflow phases, you'll be prompted for approval of generated documents.
Use Ctrl+C or Ctrl+D to exit at any time.

[bold blue]Examples:[/bold blue]
  [dim]init[/dim]              - Initialize project in current directory
  [dim]init /path[/dim]        - Initialize project at specific path
  [dim]status[/dim]            - Check current workflow phase
  [dim]cost[/dim]              - View cost report
  [dim]run[/dim]               - Execute complete workflow
  [dim]phase INDEXING[/dim]    - Run indexing phase
        """
        console.print(help_text.strip())
