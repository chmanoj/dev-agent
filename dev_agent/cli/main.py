"""Main CLI entry point for dev-agent."""

import json
import logging
import os
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from ..config import (
    ConfigManager,
    get_logger,
    log_config_info,
    log_system_info,
    setup_logging,
)
from .enhanced_cli import EnhancedCLI
from .interactive_cli import InteractiveCLI
from .session_manager import SessionManager

console = Console()
app = typer.Typer(
    name="dev-agent",
    help="""[bold cyan]dev-agent[/bold cyan] - AI-powered development workflow assistant

[bold]Four-Phase Workflow:[/bold]
  1. [cyan]Indexing[/cyan] - Analyze codebase structure and patterns
  2. [cyan]Specification[/cyan] - Generate detailed specifications
  3. [cyan]Design[/cyan] - Create technical design documents
  4. [cyan]Implementation[/cyan] - Generate actionable tasks

[bold]Quick Start:[/bold]
  [green]dev-agent setup[/green]        Configure Azure OpenAI
  [green]dev-agent init[/green]         Initialize project
  [green]dev-agent[/green]              Start interactive mode

[bold]Get Help:[/bold]
  [green]dev-agent help[/green]         Show all commands
  [green]dev-agent help <command>[/green]  Command-specific help
  [green]dev-agent examples[/green]    Common workflow examples

[dim]Use --help with any command for detailed information[/dim]
""",
    rich_markup_mode="rich",
    epilog="[dim]For more information, visit: https://github.com/yourusername/dev-agent[/dim]",
)


# Global state for CLI
config_manager = ConfigManager()
logger: logging.Logger | None = None


def setup_cli_logging(
    verbose: bool = False, debug: bool = False, project_path: str | None = None
) -> None:
    """Setup logging for CLI operations."""
    global logger
    config = config_manager.load_config()
    setup_logging(config.logging, project_path=project_path, verbose=verbose)
    logger = get_logger(__name__)

    if verbose or debug:
        log_system_info()
        log_config_info(config)

    logger.info(f"Starting dev-agent v{config.version}")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose output")
    ] = False,
    debug: Annotated[
        bool, typer.Option("--debug", help="Enable debug logging")
    ] = False,
    config_path: Annotated[
        str | None, typer.Option("--config-path", help="Path to configuration file")
    ] = None,
    version: Annotated[
        bool, typer.Option("--version", help="Show version and exit")
    ] = False,
    insecure: Annotated[
        bool, typer.Option("--insecure", help="Disable SSL certificate verification (INSECURE - for testing only)")
    ] = False,
) -> None:
    """AI-powered development workflow assistant.
    
    When invoked without a command, starts interactive mode in the current directory.
    Use 'dev-agent help' for a list of all commands and 'dev-agent examples' for
    common workflow examples.
    """
    if version:
        from ..config import ConfigManager
        config = ConfigManager().get_config()
        console.print(f"[bold cyan]dev-agent[/bold cyan] version {config.version}")
        raise typer.Exit(0)
    
    # Store insecure flag in context for subcommands to access
    if insecure:
        console.print(Panel(
            "[yellow]⚠️  SSL CERTIFICATE VERIFICATION DISABLED[/yellow]\n\n"
            "Running in insecure mode. SSL certificates will NOT be verified.\n"
            "This should ONLY be used for testing/development.\n"
            "NEVER use this in production environments.",
            title="⚠️  Security Warning",
            border_style="yellow"
        ))
        console.print()
        # Set environment variable so all Azure OpenAI clients use it
        import os
        os.environ["AZURE_OPENAI_VERIFY_SSL"] = "false"
    
    if config_path:
        # TODO: Handle custom config path
        pass
    
    # If no subcommand was provided, start interactive mode
    if ctx.invoked_subcommand is None:
        # Start interactive mode in current directory
        try:
            interactive(project_path=None, verbose=verbose, debug=debug)
        except Exception:
            # If interactive mode fails, show help
            from dev_agent.cli.help_system import help_system
            help_system.show_quick_reference()


def _run_indexing_with_progress(
    workflow_manager, project_path: str, project_context, console: Console
) -> None:
    """Run indexing phase with progress display for existing codebases.

    Args:
        workflow_manager: WorkflowManager instance
        project_path: Path to the project
        project_context: ProjectContext with detected information
        console: Rich console for output
    """
    from pathlib import Path

    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        Progress,
        SpinnerColumn,
        TaskProgressColumn,
        TextColumn,
        TimeElapsedColumn,
    )
    from rich.table import Table

    from dev_agent.indexing.indexing_engine import IndexingEngine

    try:
        # Display codebase detection summary
        console.print("[bold cyan]📊 Codebase Detection Summary[/bold cyan]")
        console.print()

        summary_table = Table(show_header=False, box=None, padding=(0, 2))
        summary_table.add_column("Property", style="cyan")
        summary_table.add_column("Value", style="green")

        summary_table.add_row("Languages", ", ".join(project_context.languages_detected) if project_context.languages_detected else "Unknown")
        summary_table.add_row("File Count", str(project_context.file_count))
        summary_table.add_row("Project Size", project_context.estimated_size.title())
        summary_table.add_row("Complexity", project_context.complexity.title())

        console.print(summary_table)
        console.print()

        # Initialize indexing engine with embedding client from config
        embedding_client = None
        try:
            from dev_agent.llm.embeddings import AzureEmbeddingClient
            from dev_agent.errors.exceptions import IndexingError
            
            config = config_manager.get_config()
            
            # Check if Azure OpenAI is configured
            if not config.azure_openai:
                console.print()
                console.print(Panel(
                    "[red]Azure OpenAI is not configured.[/red]\n\n"
                    "dev-agent requires Azure OpenAI for embeddings generation.\n\n"
                    "Please configure Azure OpenAI first:\n"
                    "  [cyan]dev-agent azure configure[/cyan]\n\n"
                    "Or set environment variables:\n"
                    "  [cyan]AZURE_OPENAI_ENDPOINT[/cyan]\n"
                    "  [cyan]AZURE_OPENAI_API_KEY[/cyan]\n"
                    "  [cyan]AZURE_OPENAI_DEPLOYMENT_NAME[/cyan]\n"
                    "  [cyan]AZURE_OPENAI_EMBEDDING_DEPLOYMENT[/cyan]",
                    title="❌ Configuration Required",
                    border_style="red"
                ))
                raise typer.Exit(1)
            
            embedding_client = AzureEmbeddingClient(config.azure_openai)
            
        except typer.Exit:
            raise
        except Exception as e:
            console.print()
            console.print(Panel(
                f"[red]Failed to initialize Azure OpenAI embedding client:[/red]\n\n"
                f"{e}\n\n"
                "Please verify your Azure OpenAI configuration:\n"
                "  [cyan]dev-agent azure status[/cyan]\n\n"
                "Test your connection:\n"
                "  [cyan]dev-agent azure test[/cyan]\n\n"
                "Reconfigure if needed:\n"
                "  [cyan]dev-agent azure configure[/cyan]",
                title="❌ Initialization Failed",
                border_style="red"
            ))
            if logger:
                logger.error(f"Could not initialize embedding client: {e}", exc_info=True)
            raise typer.Exit(1)

        indexing_engine = IndexingEngine(
            project_path=project_path,
            embedding_client=embedding_client,
            cost_tracker=workflow_manager.cost_tracker,
        )

        # Create progress display
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:

            # Add progress task
            indexing_task = progress.add_task(
                "[cyan]Indexing codebase...",
                total=100
            )

            # Set up progress callback
            def update_progress(current: int, total: int, message: str = ""):
                if total > 0:
                    percentage = int((current / total) * 100)
                    progress.update(
                        indexing_task,
                        completed=percentage,
                        description=f"[cyan]{message or 'Indexing codebase...'}",
                    )

            indexing_engine.set_progress_callback(update_progress)

            # Run indexing
            result = indexing_engine.build_index()

            # Complete progress
            progress.update(indexing_task, completed=100, description="[green]✓ Indexing complete!")

        console.print()

        # Display indexing summary
        if result.success:
            console.print("[bold green]✅ Indexing Complete![/bold green]")
            console.print()

            # Create summary table
            summary = Table(title="Indexing Summary", show_header=True, header_style="bold cyan")
            summary.add_column("Metric", style="cyan", width=30)
            summary.add_column("Value", justify="right", style="green", width=20)

            metadata = result.metadata
            summary.add_row("Files Indexed", str(metadata.get("total_files", 0)))
            summary.add_row("Lines of Code", f"{metadata.get('total_lines', 0):,}")
            summary.add_row("Code Chunks", str(metadata.get('total_chunks', 0)))
            summary.add_row("Embeddings Generated", str(result.embeddings_count))
            summary.add_row("Functions Found", str(metadata.get('functions_count', 0)))
            summary.add_row("Classes Found", str(metadata.get('classes_count', 0)))
            summary.add_row("Imports Found", str(metadata.get('imports_count', 0)))

            languages = metadata.get('languages_detected', [])
            if languages:
                summary.add_row("Languages Detected", ", ".join(languages))

            indexing_time = metadata.get('indexing_time_seconds', 0)
            summary.add_row("Indexing Time", f"{indexing_time:.2f}s")

            console.print(summary)
            console.print()

            # Display patterns found
            if result.ast_index:
                console.print("[bold cyan]🔍 Patterns Detected:[/bold cyan]")
                console.print(f"  • {len(result.ast_index.functions)} function definitions")
                console.print(f"  • {len(result.ast_index.classes)} class definitions")
                console.print(f"  • {len(result.ast_index.imports)} import statements")
                console.print(f"  • {len(result.ast_index.symbols)} symbols")
                console.print()

            # Display cost information if available
            if workflow_manager.cost_tracker:
                cost = workflow_manager.cost_tracker.get_current_cost()
                console.print(f"[dim]💰 Indexing cost: ${cost:.4f}[/dim]")
                console.print()

            # Update project state with indexing results
            if workflow_manager.current_project_state:
                workflow_manager.current_project_state.indexing_complete = True
                workflow_manager.current_project_state.index_metadata = indexing_engine.get_index_metadata()
                workflow_manager.state_manager.save_project_state(workflow_manager.current_project_state)

        else:
            console.print("[bold red]❌ Indexing Failed[/bold red]")
            if result.errors:
                console.print("\n[yellow]Errors encountered:[/yellow]")
                for error in result.errors[:5]:  # Show first 5 errors
                    console.print(f"  • {error}")
                if len(result.errors) > 5:
                    console.print(f"  ... and {len(result.errors) - 5} more errors")
            console.print()

    except Exception as e:
        console.print(f"[red]Error during indexing: {e}[/red]")
        if logger:
            logger.error(f"Indexing error: {e}", exc_info=True)


@app.command()
def init(
    project_path: Annotated[
        str | None, typer.Argument(help="Project directory path")
    ] = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose output")
    ] = False,
    debug: Annotated[
        bool, typer.Option("--debug", help="Enable debug logging")
    ] = False,
) -> None:
    """Initialize a new dev-agent project.
    
    This command initializes dev-agent for a project directory. It will:
    - Detect if this is a new or existing project
    - Guide you through setup if not configured
    - Offer template selection for new projects
    - Index existing code for existing projects
    - Create the .dev_agent/ directory structure
    
    For new projects, you'll be guided through template selection and initial
    specification creation. For existing codebases, the tool will automatically
    index your code to understand patterns and conventions.
    
    Examples:
        # Initialize in current directory
        dev-agent init
        
        # Initialize specific directory
        dev-agent init /path/to/project
        
        # Initialize with verbose output
        dev-agent init --verbose
        
        # Initialize and see detailed logging
        dev-agent init --debug
    
    After initialization, use 'dev-agent' to start interactive mode or
    'dev-agent resume' to continue an existing project.
    """
    from pathlib import Path

    from rich.panel import Panel
    from rich.prompt import Confirm

    from dev_agent.onboarding.journey_manager import JourneyManager

    if project_path is None:
        project_path = os.getcwd()

    project_path = os.path.abspath(project_path)

    try:
        setup_cli_logging(verbose, debug, project_path)

        if not os.path.exists(project_path):
            console.print(
                f"[red]Error: Project path does not exist: {project_path}[/red]"
            )
            raise typer.Exit(1)

        # Initialize journey manager to detect project type
        journey_manager = JourneyManager()
        project_context = journey_manager.detect_project_type(Path(project_path))

        # Display project detection results
        console.print(
            Panel.fit(
                "[bold cyan]Initializing dev-agent Project[/bold cyan]",
                border_style="cyan",
            )
        )
        console.print()

        # Show project analysis
        journey_manager.display_project_summary(project_context)

        # Check if this is a new project (empty directory)
        is_new_project = project_context.project_type == "new"

        if is_new_project:
            console.print(
                "[cyan]This appears to be a new project (empty directory).[/cyan]"
            )
            console.print(
                "dev-agent will help you set up and scaffold your project.\n"
            )
        else:
            console.print(
                f"[cyan]Detected existing {project_context.project_type} project with "
                f"{project_context.file_count} files.[/cyan]"
            )
            if project_context.languages_detected:
                console.print(
                    f"[cyan]Languages: {', '.join(project_context.languages_detected)}[/cyan]\n"
                )

        # Load project-specific configuration if available
        config_manager.load_project_config(project_path)

        # Check configuration and offer setup wizard if needed
        config = config_manager.get_config()
        setup_completed = _check_configuration_and_offer_setup(config, is_new_project)

        if not setup_completed:
            console.print(
                "\n[yellow]Setup was not completed. Please run [cyan]dev-agent setup[/cyan] "
                "to configure Azure OpenAI before continuing.[/yellow]"
            )
            raise typer.Exit(1)

        # For new projects, offer template selection
        if is_new_project:
            if Confirm.ask(
                "\n[cyan]Would you like to use a project template?[/cyan]",
                default=False,
            ):
                console.print(
                    "\n[green]Great! You can browse templates with:[/green]"
                )
                console.print("  [cyan]dev-agent scaffold list[/cyan]")
                console.print("\n[green]Then create from a template with:[/green]")
                console.print("  [cyan]dev-agent scaffold create <template-name>[/cyan]")
                console.print(
                    "\n[yellow]After scaffolding, run [cyan]dev-agent init[/cyan] again to continue.[/yellow]"
                )
                raise typer.Exit(0)

            # Explain what happens next for new projects
            console.print()
            console.print(
                Panel(
                    "[bold]New Project Workflow[/bold]\n\n"
                    "Since this is a new project, dev-agent will:\n"
                    "  1. Create the .dev_agent/ directory structure\n"
                    "  2. Skip indexing (no code to analyze yet)\n"
                    "  3. Guide you through creating an initial specification\n"
                    "  4. Help you design your project architecture\n"
                    "  5. Generate implementation tasks\n\n"
                    "[dim]You can start by describing what you want to build.[/dim]",
                    border_style="cyan",
                )
            )
            console.print()

            if not Confirm.ask("Ready to continue?", default=True):
                console.print("[yellow]Initialization cancelled.[/yellow]")
                raise typer.Exit(0)

        # Initialize CLI and session manager
        session_manager = SessionManager(project_path)

        # Initialize workflow manager
        from ..workflow.workflow_manager import WorkflowManager

        cli = EnhancedCLI()
        workflow_manager = WorkflowManager(cli)
        cli.workflow_manager = workflow_manager

        if logger:
            logger.info(f"Initializing project at: {project_path}")

        # Provide contextual guidance based on project type
        if is_new_project:
            console.print(
                "[bold green]✓[/bold green] Initializing new project structure..."
            )
        else:
            console.print(
                "[bold green]✓[/bold green] Initializing dev-agent for existing codebase..."
            )

        # Initialize project through workflow manager
        project_state = workflow_manager.start_new_project(project_path)

        success_msg = f"Started new project: {project_state.project_path}"
        if logger:
            logger.info(success_msg)
        console.print(f"[green]{success_msg}[/green]")

        # For existing codebases, automatically start indexing
        if not is_new_project:
            console.print()
            console.print(
                Panel(
                    "[bold]Existing Codebase Detected[/bold]\n\n"
                    "dev-agent will now index your codebase to understand its structure,\n"
                    "patterns, and conventions. This enables context-aware code generation.\n\n"
                    "[dim]This may take a few minutes depending on codebase size...[/dim]",
                    border_style="cyan",
                )
            )
            console.print()

            # Start indexing with progress display
            _run_indexing_with_progress(
                workflow_manager, project_path, project_context, console
            )

        # Provide next steps guidance
        if is_new_project:
            console.print()
            console.print("[bold cyan]Next Steps:[/bold cyan]")
            console.print(
                "  1. Enter interactive mode to start creating your specification"
            )
            console.print("  2. Describe what you want to build")
            console.print("  3. Review and approve the generated specification")
            console.print("  4. Continue through design and implementation phases")
            console.print()
        else:
            console.print()
            console.print("[bold cyan]Next Steps:[/bold cyan]")
            console.print(
                "  1. Generate specifications for new features using the indexed code"
            )
            console.print("  2. Create designs that match your existing architecture")
            console.print("  3. Generate implementation tasks consistent with your code style")
            console.print("  4. Use [cyan]dev-agent resume[/cyan] to continue your workflow")
            console.print()

        # Start interactive mode after initialization
        _start_interactive_mode(project_path, session_manager, cli)

    except typer.Exit:
        raise
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Initialization cancelled by user.[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        error_msg = f"Failed to initialize project: {e}"
        if logger:
            logger.error(error_msg, exc_info=True)
        console.print(f"[red]Error: {error_msg}[/red]")
        raise typer.Exit(1) from e


@app.command()
def resume(
    project_path: Annotated[
        str | None, typer.Argument(help="Project directory path")
    ] = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose output")
    ] = False,
    debug: Annotated[
        bool, typer.Option("--debug", help="Enable debug logging")
    ] = False,
) -> None:
    """Resume an existing dev-agent project.
    
    Load a previously initialized dev-agent project and continue from where
    you left off. The project state is automatically restored, including the
    current phase, generated documents, and workflow progress.
    
    This command will:
    - Load the project state from .dev_agent/
    - Display current phase and progress
    - Start interactive mode to continue workflow
    - Restore all previous context and documents
    
    Examples:
        # Resume project in current directory
        dev-agent resume
        
        # Resume specific project
        dev-agent resume /path/to/project
        
        # Resume with verbose output
        dev-agent resume --verbose
    
    If the project hasn't been initialized yet, you'll see an error message
    suggesting to use 'dev-agent init' first.
    """
    if project_path is None:
        project_path = os.getcwd()

    project_path = os.path.abspath(project_path)

    try:
        setup_cli_logging(verbose, debug, project_path)

        if not os.path.exists(project_path):
            console.print(
                f"[red]Error: Project path does not exist: {project_path}[/red]"
            )
            raise typer.Exit(1)

        dev_agent_dir = os.path.join(project_path, ".dev_agent")
        if not os.path.exists(dev_agent_dir):
            console.print(
                f"[red]Error: No dev-agent project found at {project_path}[/red]"
            )
            console.print(
                "Use '[cyan]dev-agent init[/cyan]' to initialize a new project."
            )
            raise typer.Exit(1)

        # Load project-specific configuration
        config = config_manager.load_project_config(project_path)
        _check_configuration_and_warn(config)

        # Initialize session manager and try to resume
        session_manager = SessionManager(project_path)

        # Initialize workflow manager
        from ..workflow.workflow_manager import WorkflowManager

        cli = EnhancedCLI()
        workflow_manager = WorkflowManager(cli)
        cli.workflow_manager = workflow_manager

        if logger:
            logger.info(f"Resuming project at: {project_path}")

        # Resume project through workflow manager
        try:
            project_state = workflow_manager.resume_project(project_path)
            resume_msg = f"Resumed project: {project_state.project_path}"
            phase_msg = f"Current phase: {project_state.current_phase.value}"
            if logger:
                logger.info(f"{resume_msg}, {phase_msg}")
            console.print(f"[green]{resume_msg}[/green]")
            console.print(f"[blue]{phase_msg}[/blue]")
        except Exception as e:
            if logger:
                logger.info(f"Could not resume project: {e}, starting new project")
            console.print(
                "[yellow]Could not resume project, starting new project...[/yellow]"
            )
            project_state = workflow_manager.start_new_project(project_path)

        # Start interactive mode
        _start_interactive_mode(project_path, session_manager, cli)

    except Exception as e:
        error_msg = f"Failed to resume project: {e}"
        if logger:
            logger.error(error_msg, exc_info=True)
        console.print(f"[red]Error: {error_msg}[/red]")
        raise typer.Exit(1) from e


@app.command()
def interactive(
    project_path: Annotated[
        str | None, typer.Argument(help="Project directory path")
    ] = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose output")
    ] = False,
    debug: Annotated[
        bool, typer.Option("--debug", help="Enable debug logging")
    ] = False,
) -> None:
    """Start interactive mode (default command)."""
    if project_path is None:
        project_path = os.getcwd()

    project_path = os.path.abspath(project_path)

    try:
        setup_cli_logging(verbose, debug, project_path)

        session_manager = SessionManager(project_path)
        cli = EnhancedCLI()

        _start_interactive_mode(project_path, session_manager, cli)

    except Exception as e:
        error_msg = f"Error in interactive mode: {e}"
        if logger:
            logger.error(error_msg, exc_info=True)
        console.print(f"[red]Error: {error_msg}[/red]")
        raise typer.Exit(1)


@app.command()
def setup(
    status: Annotated[
        bool, typer.Option("--status", help="Display current setup status")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose output")
    ] = False,
) -> None:
    """Run interactive setup wizard or display setup status.

    The setup wizard guides you through initial configuration including:
    - Azure OpenAI credentials and deployment names
    - Connection testing to verify configuration
    - Workflow overview and cost estimates
    - Next steps guidance

    Use --status to check if dev-agent is properly configured.
    """
    from pathlib import Path

    from rich.panel import Panel
    from rich.table import Table

    from dev_agent.onboarding.setup_wizard import SetupWizard

    try:
        setup_cli_logging(verbose, False)

        # Check if we're showing status or running wizard
        if status:
            # Display setup status
            console.print(
                Panel.fit(
                    "[bold blue]dev-agent Setup Status[/bold blue]",
                    border_style="blue",
                )
            )
            console.print()

            # Load configuration
            config = config_manager.get_config()
            wizard = SetupWizard()
            prefs = wizard.load_existing_preferences()

            # Create status table
            status_table = Table(
                title="Configuration Status",
                show_header=True,
                header_style="bold cyan",
            )
            status_table.add_column("Component", style="cyan", width=30)
            status_table.add_column("Status", justify="center", width=15)
            status_table.add_column("Details", width=40)

            # Check Azure OpenAI configuration
            azure_configured = bool(
                config.azure_openai
                and config.azure_openai.api_key
                and config.azure_openai.endpoint
                and config.azure_openai.deployment_name
                and config.azure_openai.embedding_deployment
            )

            status_table.add_row(
                "Azure OpenAI",
                "[green]✓ Configured[/green]"
                if azure_configured
                else "[red]✗ Not Configured[/red]",
                f"Endpoint: {config.azure_openai.endpoint[:50]}..."
                if azure_configured
                else "Run: dev-agent setup",
            )

            # Check user preferences
            prefs_exist = prefs is not None
            status_table.add_row(
                "User Preferences",
                "[green]✓ Saved[/green]"
                if prefs_exist
                else "[yellow]⚠ Not Set[/yellow]",
                f"Config: {Path.home() / '.dev_agent_config'}"
                if prefs_exist
                else "Will be created on first setup",
            )

            # Check first run status
            first_run_complete = prefs and prefs.azure_configured if prefs else False
            status_table.add_row(
                "First Run",
                "[green]✓ Complete[/green]"
                if first_run_complete
                else "[yellow]⚠ Pending[/yellow]",
                "Setup wizard completed"
                if first_run_complete
                else "Run: dev-agent setup",
            )

            console.print(status_table)
            console.print()

            # Overall status
            if azure_configured and first_run_complete:
                console.print(
                    Panel(
                        "[bold green]✅ dev-agent is fully configured and ready to use![/bold green]\n\n"
                        "You can now:\n"
                        "  • Initialize projects: [cyan]dev-agent init[/cyan]\n"
                        "  • Start interactive mode: [cyan]dev-agent[/cyan]\n"
                        "  • Test Azure connection: [cyan]dev-agent azure test[/cyan]",
                        title="Status: Ready",
                        border_style="green",
                    )
                )
            elif azure_configured:
                console.print(
                    Panel(
                        "[bold yellow]⚠️  Azure OpenAI is configured but setup is incomplete[/bold yellow]\n\n"
                        "Run [cyan]dev-agent setup[/cyan] to complete the setup wizard.",
                        title="Status: Partial",
                        border_style="yellow",
                    )
                )
            else:
                console.print(
                    Panel(
                        "[bold red]❌ dev-agent is not configured[/bold red]\n\n"
                        "Run [cyan]dev-agent setup[/cyan] to configure Azure OpenAI and complete setup.",
                        title="Status: Not Configured",
                        border_style="red",
                    )
                )

            raise typer.Exit(0)

        # Run setup wizard
        console.print(
            Panel.fit(
                "[bold cyan]dev-agent Setup Wizard[/bold cyan]\n"
                "Configure dev-agent for first use",
                border_style="cyan",
            )
        )
        console.print()

        # Check if already configured
        config = config_manager.get_config()
        wizard = SetupWizard()
        prefs = wizard.load_existing_preferences()

        if (
            config.azure_openai
            and config.azure_openai.api_key
            and config.azure_openai.endpoint
            and prefs
            and prefs.azure_configured
        ):
            console.print(
                "[yellow]dev-agent appears to be already configured.[/yellow]"
            )
            console.print()

            from rich.prompt import Confirm

            if not Confirm.ask(
                "Would you like to reconfigure?",
                default=False,
            ):
                console.print("[green]Setup cancelled. Configuration unchanged.[/green]")
                raise typer.Exit(0)

            console.print()

        # Run the wizard
        result = wizard.run()

        # Exit with appropriate code
        if result.ready_to_use:
            raise typer.Exit(0)
        else:
            console.print(
                "\n[yellow]Setup incomplete. Run [cyan]dev-agent setup[/cyan] again to retry.[/yellow]"
            )
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Setup cancelled by user.[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        error_msg = f"Setup failed: {e}"
        if logger:
            logger.error(error_msg, exc_info=True)
        console.print(f"[red]Error: {error_msg}[/red]")
        raise typer.Exit(1) from e


@app.command()
def validate(
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose output")
    ] = False,
) -> None:
    """Validate dev-agent environment and configuration.

    This command performs quick validation checks including:
    - Azure OpenAI configuration (credentials, endpoints, deployments)
    - API connectivity (test connection to Azure OpenAI)
    - Required dependencies (Python packages)
    - File system permissions (read/write access)

    Use this command to troubleshoot configuration issues before running workflows.
    """
    import asyncio
    import importlib.util
    import sys
    from pathlib import Path

    from rich.panel import Panel
    from rich.table import Table

    try:
        setup_cli_logging(verbose, False)

        console.print(
            Panel.fit(
                "[bold blue]dev-agent Environment Validation[/bold blue]\n"
                "Checking configuration and dependencies...",
                border_style="blue",
            )
        )
        console.print()

        # Track validation results
        all_passed = True
        issues = []
        suggestions = []

        # Create results table
        results_table = Table(
            title="Validation Results",
            show_header=True,
            header_style="bold cyan",
        )
        results_table.add_column("Check", style="cyan", width=35)
        results_table.add_column("Status", justify="center", width=15)
        results_table.add_column("Details", width=50)

        # 1. Check Azure OpenAI Configuration
        console.print("[cyan]Checking Azure OpenAI configuration...[/cyan]")
        config = config_manager.get_config()

        if (
            config.azure_openai
            and config.azure_openai.api_key
            and config.azure_openai.endpoint
            and config.azure_openai.deployment_name
            and config.azure_openai.embedding_deployment
        ):
            results_table.add_row(
                "Azure OpenAI Config",
                "[green]✓ Pass[/green]",
                f"Endpoint: {config.azure_openai.endpoint[:40]}...",
            )
        else:
            all_passed = False
            missing = []
            if not config.azure_openai or not config.azure_openai.endpoint:
                missing.append("endpoint")
            if not config.azure_openai or not config.azure_openai.api_key:
                missing.append("API key")
            if not config.azure_openai or not config.azure_openai.deployment_name:
                missing.append("deployment name")
            if not config.azure_openai or not config.azure_openai.embedding_deployment:
                missing.append("embedding deployment")

            results_table.add_row(
                "Azure OpenAI Config",
                "[red]✗ Fail[/red]",
                f"Missing: {', '.join(missing)}",
            )
            issues.append("Azure OpenAI is not properly configured")
            suggestions.append("Run: dev-agent setup")

        # 2. Test API Connectivity
        console.print("[cyan]Testing Azure OpenAI connectivity...[/cyan]")
        if config.azure_openai and config.azure_openai.api_key and config.azure_openai.endpoint:
            try:
                from dev_agent.llm.azure_client import AzureOpenAIClient

                async def test_connection():
                    try:
                        client = AzureOpenAIClient(config.azure_openai)
                        # Try a simple completion
                        response = await client.generate_completion(
                            prompt="Say 'OK'",
                            system_prompt="Respond with exactly 'OK'",
                            max_tokens=10,
                            temperature=0.0,
                        )
                        return True, "Connection successful"
                    except Exception as e:
                        return False, str(e)

                success, message = asyncio.run(test_connection())

                if success:
                    results_table.add_row(
                        "API Connectivity",
                        "[green]✓ Pass[/green]",
                        "Successfully connected to Azure OpenAI",
                    )
                else:
                    all_passed = False
                    results_table.add_row(
                        "API Connectivity",
                        "[red]✗ Fail[/red]",
                        f"Error: {message[:45]}...",
                    )
                    issues.append(f"Cannot connect to Azure OpenAI: {message}")
                    suggestions.append("Check your API key and endpoint")
                    suggestions.append("Verify network connectivity")

            except Exception as e:
                all_passed = False
                results_table.add_row(
                    "API Connectivity",
                    "[red]✗ Fail[/red]",
                    f"Error: {str(e)[:45]}...",
                )
                issues.append(f"Failed to test connectivity: {e}")
                suggestions.append("Check Azure OpenAI configuration")
        else:
            results_table.add_row(
                "API Connectivity",
                "[yellow]⚠ Skip[/yellow]",
                "Skipped (configuration missing)",
            )

        # 3. Check Required Dependencies
        console.print("[cyan]Checking required dependencies...[/cyan]")
        required_packages = [
            ("openai", "Azure OpenAI SDK"),
            ("tiktoken", "Token counting"),
            ("tenacity", "Retry logic"),
            ("faiss", "Vector database"),
            ("tree_sitter", "Code parsing"),
            ("typer", "CLI framework"),
            ("rich", "Terminal output"),
            ("pydantic", "Data validation"),
            ("httpx", "HTTP client"),
        ]

        missing_packages = []
        for package_name, description in required_packages:
            # Handle special cases
            check_name = "faiss-cpu" if package_name == "faiss" else package_name
            spec = importlib.util.find_spec(check_name)
            if spec is None:
                missing_packages.append(f"{package_name} ({description})")

        if not missing_packages:
            results_table.add_row(
                "Required Dependencies",
                "[green]✓ Pass[/green]",
                f"All {len(required_packages)} packages installed",
            )
        else:
            all_passed = False
            results_table.add_row(
                "Required Dependencies",
                "[red]✗ Fail[/red]",
                f"Missing: {', '.join(missing_packages[:2])}...",
            )
            issues.append(f"Missing {len(missing_packages)} required package(s)")
            suggestions.append("Run: uv sync --dev")

        # 4. Check Python Version
        console.print("[cyan]Checking Python version...[/cyan]")
        python_version = sys.version_info
        if python_version >= (3, 10):
            results_table.add_row(
                "Python Version",
                "[green]✓ Pass[/green]",
                f"Python {python_version.major}.{python_version.minor}.{python_version.micro}",
            )
        else:
            all_passed = False
            results_table.add_row(
                "Python Version",
                "[red]✗ Fail[/red]",
                f"Python {python_version.major}.{python_version.minor} (requires 3.10+)",
            )
            issues.append("Python version is too old")
            suggestions.append("Upgrade to Python 3.10 or newer")

        # 5. Check File System Permissions
        console.print("[cyan]Checking file system permissions...[/cyan]")
        try:
            # Test write permissions in current directory
            test_file = Path(".dev_agent_test_write")
            test_file.write_text("test")
            test_file.unlink()

            # Test read permissions
            current_dir = Path.cwd()
            list(current_dir.iterdir())

            results_table.add_row(
                "File System Permissions",
                "[green]✓ Pass[/green]",
                "Read/write access verified",
            )
        except PermissionError as e:
            all_passed = False
            results_table.add_row(
                "File System Permissions",
                "[red]✗ Fail[/red]",
                f"Permission denied: {str(e)[:30]}...",
            )
            issues.append("Insufficient file system permissions")
            suggestions.append("Check directory permissions")
        except Exception as e:
            all_passed = False
            results_table.add_row(
                "File System Permissions",
                "[red]✗ Fail[/red]",
                f"Error: {str(e)[:40]}...",
            )
            issues.append(f"File system check failed: {e}")

        # Display results
        console.print()
        console.print(results_table)
        console.print()

        # Display overall status
        if all_passed:
            console.print(
                Panel(
                    "[bold green]✅ All validation checks passed![/bold green]\n\n"
                    "dev-agent is properly configured and ready to use.\n\n"
                    "Next steps:\n"
                    "  • Initialize a project: [cyan]dev-agent init[/cyan]\n"
                    "  • Start interactive mode: [cyan]dev-agent[/cyan]\n"
                    "  • View status: [cyan]dev-agent setup --status[/cyan]",
                    title="Validation: Success",
                    border_style="green",
                )
            )
            raise typer.Exit(0)
        else:
            # Display issues and suggestions
            console.print(
                Panel(
                    f"[bold red]❌ Validation failed with {len(issues)} issue(s)[/bold red]",
                    title="Validation: Failed",
                    border_style="red",
                )
            )
            console.print()

            if issues:
                console.print("[bold yellow]Issues Found:[/bold yellow]")
                for i, issue in enumerate(issues, 1):
                    console.print(f"  {i}. {issue}")
                console.print()

            if suggestions:
                console.print("[bold cyan]Suggested Solutions:[/bold cyan]")
                for i, suggestion in enumerate(suggestions, 1):
                    console.print(f"  {i}. {suggestion}")
                console.print()

            console.print(
                "[dim]For more help, visit: https://github.com/your-repo/dev-agent/docs[/dim]"
            )
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Validation cancelled by user.[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        error_msg = f"Validation failed: {e}"
        if logger:
            logger.error(error_msg, exc_info=True)
        console.print(f"[red]Error: {error_msg}[/red]")
        raise typer.Exit(1) from e


@app.command()
def help(
    command: Annotated[
        str | None, typer.Argument(help="Command to get help for")
    ] = None,
) -> None:
    """Display detailed help for commands.

    Show comprehensive help information including usage, options, examples,
    and notes for specific commands or an overview of all commands.

    Examples:
        dev-agent help              # Show all commands
        dev-agent help init         # Help for init command
        dev-agent help azure        # Help for azure commands
    """
    from dev_agent.cli.help_system import help_system

    try:
        if command:
            help_system.show_command_help(command)
        else:
            help_system.show_all_commands()

    except KeyboardInterrupt:
        console.print("\n")
        raise typer.Exit(0)
    except Exception as e:
        console.print(f"[red]Error displaying help: {e}[/red]")
        raise typer.Exit(1) from e


@app.command()
def examples(
    workflow: Annotated[
        str | None, typer.Argument(help="Specific workflow to show examples for")
    ] = None,
) -> None:
    """Display common workflow examples and usage patterns.

    Show step-by-step examples for common workflows including new projects,
    existing codebases, quick start, cost management, and troubleshooting.

    Available workflows:
        - new_project: Starting a new project from scratch
        - existing_codebase: Analyzing an existing codebase
        - quick_start: Get started in 5 minutes
        - cost_management: Monitor and control costs
        - troubleshooting: Resolve common issues

    Examples:
        dev-agent examples                    # Show all workflows
        dev-agent examples new_project        # New project workflow
        dev-agent examples existing_codebase  # Existing codebase workflow
        dev-agent examples quick_start        # Quick start guide
    """
    from dev_agent.cli.help_system import help_system

    try:
        help_system.show_examples(workflow)

    except KeyboardInterrupt:
        console.print("\n")
        raise typer.Exit(0)
    except Exception as e:
        console.print(f"[red]Error displaying examples: {e}[/red]")
        raise typer.Exit(1) from e


@app.command()
def audit(
    skip_azure: Annotated[
        bool, typer.Option("--skip-azure", help="Skip Azure OpenAI integration tests")
    ] = False,
    save_report: Annotated[
        bool, typer.Option("--save-report/--no-save-report", help="Save detailed report to file")
    ] = True,
    report_path: Annotated[
        str | None, typer.Option("--report-path", help="Path to save audit report")
    ] = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose output")
    ] = False,
) -> None:
    """Run comprehensive audit of dev-agent functionality.

    This command performs systematic checks of all core features including:
    - Indexing phase (Tree-sitter, FAISS, embeddings)
    - Specification phase (GPT-4 generation, document structure)
    - Design phase (design generation, formatting)
    - Implementation phase (task generation)
    - State management (persistence, recovery)
    - Azure OpenAI integration (API connectivity, cost tracking)
    - Error handling (graceful degradation, recovery)
    """
    import asyncio

    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        Progress,
        SpinnerColumn,
        TaskProgressColumn,
        TextColumn,
    )
    from rich.table import Table

    try:
        setup_cli_logging(verbose, False)

        console.print(Panel.fit(
            "[bold blue]Dev-Agent Comprehensive Audit[/bold blue]\n"
            "Verifying all core functionality...",
            border_style="blue"
        ))
        console.print()

        # Import audit engine
        from dev_agent.audit.audit_engine import AuditEngine
        from dev_agent.audit.models import AuditConfig

        # Configure audit
        audit_config = AuditConfig(
            skip_azure_tests=skip_azure,
            verbose=verbose,
            save_report=save_report,
            report_path=report_path or ".dev_agent/audit_report.md",
        )

        if skip_azure:
            console.print("[yellow]⚠ Skipping Azure OpenAI integration tests[/yellow]")
            console.print()

        # Create audit engine
        engine = AuditEngine(audit_config)

        # Run audit with progress display
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:

            # Create progress task
            audit_task = progress.add_task(
                "[cyan]Running audit checks...",
                total=7 if not skip_azure else 6
            )

            # Run the audit (this will take some time)
            async def run_with_progress():
                # We'll update progress as we go
                report = await engine.run_audit()
                return report

            # Run async audit
            report = asyncio.run(run_with_progress())
            progress.update(audit_task, completed=7 if not skip_azure else 6)

        console.print()

        # Display results summary
        status_color = {
            "pass": "green",
            "warning": "yellow",
            "fail": "red",
        }[report.overall_status]

        status_emoji = {
            "pass": "✅",
            "warning": "⚠️",
            "fail": "❌",
        }[report.overall_status]

        console.print(Panel.fit(
            f"[bold {status_color}]{status_emoji} Overall Status: {report.overall_status.upper()}[/bold {status_color}]",
            border_style=status_color
        ))
        console.print()

        # Display statistics
        stats_table = Table(title="Audit Statistics", show_header=True, header_style="bold cyan")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Count", justify="right", style="white")

        stats_table.add_row("Total Checks", str(report.total_checks))
        stats_table.add_row("Passed", f"[green]{report.passed_checks}[/green]")
        stats_table.add_row("Failed", f"[red]{report.failed_checks}[/red]")
        stats_table.add_row("Warnings", f"[yellow]{report.warnings}[/yellow]")

        console.print(stats_table)
        console.print()

        # Display detailed results
        results_table = Table(title="Detailed Results", show_header=True, header_style="bold cyan")
        results_table.add_column("Component", style="cyan", width=30)
        results_table.add_column("Status", justify="center", width=10)
        results_table.add_column("Message", width=60)

        for result in report.results:
            status_display = {
                "pass": "[green]✅ PASS[/green]",
                "warning": "[yellow]⚠️  WARN[/yellow]",
                "fail": "[red]❌ FAIL[/red]",
            }[result.status]

            results_table.add_row(
                result.component,
                status_display,
                result.message
            )

        console.print(results_table)
        console.print()

        # Display recommendations if any
        all_recommendations = []
        for result in report.results:
            if result.recommendations:
                all_recommendations.extend([
                    f"[{result.component}] {rec}"
                    for rec in result.recommendations
                ])

        if all_recommendations:
            console.print("[bold yellow]Recommendations:[/bold yellow]")
            for i, rec in enumerate(all_recommendations, 1):
                console.print(f"  {i}. {rec}")
            console.print()

        # Display report save location
        if save_report:
            console.print(f"[dim]📄 Detailed report saved to: {audit_config.report_path}[/dim]")
            console.print()

        # Exit with appropriate code
        if report.overall_status == "fail":
            console.print("[red]Audit failed. Please address the issues above.[/red]")
            raise typer.Exit(1)
        elif report.overall_status == "warning":
            console.print("[yellow]Audit completed with warnings. Review recommendations above.[/yellow]")
            raise typer.Exit(0)
        else:
            console.print("[green]✅ All checks passed! Dev-agent is fully functional.[/green]")
            raise typer.Exit(0)

    except Exception as e:
        error_msg = f"Failed to run audit: {e}"
        if logger:
            logger.error(error_msg, exc_info=True)
        console.print(f"[red]Error: {error_msg}[/red]")
        raise typer.Exit(1) from e


@app.command()
def cost_report(
    project_path: Annotated[
        str | None, typer.Argument(help="Project directory path")
    ] = None,
    phase: Annotated[
        str | None, typer.Option("--phase", "-p", help="Filter by phase (indexing, specification, design, implementation)")
    ] = None,
    export: Annotated[
        str | None, typer.Option("--export", "-e", help="Export report to JSON file")
    ] = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose output")
    ] = False,
) -> None:
    """Display detailed cost report for Azure OpenAI usage.
    
    This command provides comprehensive cost tracking and analysis including:
    - Token usage statistics (prompt, completion, embedding)
    - Cost breakdown by workflow phase
    - Cost breakdown by operation type (completion, streaming, embedding)
    - Budget threshold warnings
    - Time period analysis
    - JSON export for further analysis
    
    Examples:
        # Show complete cost report
        dev-agent cost-report
        
        # Show costs for specific phase
        dev-agent cost-report --phase specification
        
        # Export report to JSON
        dev-agent cost-report --export cost_report.json
        
        # Phase-specific export
        dev-agent cost-report --phase indexing --export indexing_costs.json
    """
    from pathlib import Path

    from rich.panel import Panel
    from rich.table import Table

    if project_path is None:
        project_path = os.getcwd()

    project_path = os.path.abspath(project_path)

    try:
        setup_cli_logging(verbose, False, project_path)

        dev_agent_dir = os.path.join(project_path, ".dev_agent")
        if not os.path.exists(dev_agent_dir):
            console.print(
                f"[red]Error: No dev-agent project found at {project_path}[/red]"
            )
            console.print("Use '[cyan]dev-agent init[/cyan]' to initialize a project.")
            raise typer.Exit(1)

        # Initialize workflow manager to access cost tracker
        from ..workflow.workflow_manager import WorkflowManager

        cli = EnhancedCLI()
        workflow_manager = WorkflowManager(cli)

        try:
            workflow_manager.resume_project(project_path)
        except Exception:
            console.print("[yellow]Could not load project state, showing empty report[/yellow]")
            console.print()

        # Get cost report
        phase_enum = None
        if phase:
            try:
                from ..models.enums import PhaseType
                phase_enum = PhaseType(phase.lower())
                report = workflow_manager.cost_tracker.get_phase_report(phase_enum)
                title = f"Cost Report: {phase_enum.value.title()} Phase"
            except ValueError:
                console.print(f"[red]Invalid phase: {phase}[/red]")
                console.print("[yellow]Valid phases: indexing, specification, design, implementation[/yellow]")
                raise typer.Exit(1)
        else:
            report = workflow_manager.cost_tracker.get_report()
            title = "Complete Cost Report"

        # Display header
        console.print(Panel.fit(
            f"[bold blue]{title}[/bold blue]",
            border_style="blue"
        ))
        console.print()

        # Check if there's any data
        if report.operations_count == 0:
            console.print("[yellow]No operations recorded yet.[/yellow]")
            console.print()
            console.print("[dim]Operations will be tracked as you use dev-agent features like:[/dim]")
            console.print("  • Indexing codebases")
            console.print("  • Generating specifications")
            console.print("  • Creating designs")
            console.print("  • Generating implementation tasks")
            raise typer.Exit(0)

        # Summary statistics table
        summary_table = Table(
            title="Summary Statistics",
            show_header=True,
            header_style="bold cyan",
            border_style="cyan",
        )
        summary_table.add_column("Metric", style="cyan", width=30)
        summary_table.add_column("Value", justify="right", style="green", width=20)

        summary_table.add_row("Total Operations", str(report.operations_count))
        summary_table.add_row("Total Tokens", f"{report.total_tokens:,}")
        summary_table.add_row("Total Cost", f"${report.total_cost:.4f}")
        
        if report.operations_count > 0:
            summary_table.add_row("Avg Cost/Operation", f"${report.average_cost_per_operation:.4f}")
            summary_table.add_row("Avg Tokens/Operation", f"{report.average_tokens_per_operation:.1f}")
        
        duration_hours = report.duration_seconds / 3600
        if duration_hours < 1:
            duration_str = f"{report.duration_seconds / 60:.1f} minutes"
        else:
            duration_str = f"{duration_hours:.1f} hours"
        summary_table.add_row("Duration", duration_str)

        console.print(summary_table)
        console.print()

        # Token usage breakdown table
        token_table = Table(
            title="Token Usage Statistics",
            show_header=True,
            header_style="bold cyan",
            border_style="cyan",
        )
        token_table.add_column("Token Type", style="cyan", width=25)
        token_table.add_column("Count", justify="right", style="yellow", width=15)
        token_table.add_column("Percentage", justify="right", style="blue", width=15)

        total_tokens = report.total_tokens
        if total_tokens > 0:
            prompt_pct = (report.total_prompt_tokens / total_tokens) * 100
            completion_pct = (report.total_completion_tokens / total_tokens) * 100
            embedding_pct = (report.total_embedding_tokens / total_tokens) * 100
            
            token_table.add_row("Prompt Tokens", f"{report.total_prompt_tokens:,}", f"{prompt_pct:.1f}%")
            token_table.add_row("Completion Tokens", f"{report.total_completion_tokens:,}", f"{completion_pct:.1f}%")
            token_table.add_row("Embedding Tokens", f"{report.total_embedding_tokens:,}", f"{embedding_pct:.1f}%")
            token_table.add_row("[bold]Total[/bold]", f"[bold]{total_tokens:,}[/bold]", "[bold]100.0%[/bold]")

        console.print(token_table)
        console.print()

        # Cost breakdown by operation type
        if report.by_operation:
            op_table = Table(
                title="Cost Breakdown by Operation Type",
                show_header=True,
                header_style="bold cyan",
                border_style="cyan",
            )
            op_table.add_column("Operation Type", style="cyan", width=25)
            op_table.add_column("Token Count", justify="right", style="yellow", width=15)
            op_table.add_column("Percentage", justify="right", style="blue", width=15)

            for op_type, token_count in sorted(report.by_operation.items(), key=lambda x: x[1], reverse=True):
                pct = (token_count / total_tokens) * 100 if total_tokens > 0 else 0
                op_table.add_row(op_type.title(), f"{token_count:,}", f"{pct:.1f}%")

            console.print(op_table)
            console.print()

        # Cost breakdown by phase (only if showing complete report)
        if not phase and report.by_phase:
            phase_table = Table(
                title="Cost Breakdown by Workflow Phase",
                show_header=True,
                header_style="bold cyan",
                border_style="cyan",
            )
            phase_table.add_column("Phase", style="cyan", width=25)
            phase_table.add_column("Cost", justify="right", style="green", width=15)
            phase_table.add_column("Percentage", justify="right", style="blue", width=15)

            for phase_type, cost in sorted(report.by_phase.items(), key=lambda x: x[1], reverse=True):
                pct = (cost / report.total_cost) * 100 if report.total_cost > 0 else 0
                phase_table.add_row(phase_type.value.title(), f"${cost:.4f}", f"{pct:.1f}%")

            console.print(phase_table)
            console.print()

        # Budget warnings
        budget_threshold = workflow_manager.cost_tracker.budget_threshold
        budget_limit = workflow_manager.cost_tracker.budget_limit
        
        if budget_threshold is not None or budget_limit is not None:
            console.print("[bold cyan]Budget Status:[/bold cyan]")
            
            if budget_threshold is not None:
                threshold_pct = (report.total_cost / budget_threshold) * 100
                if report.total_cost >= budget_threshold:
                    console.print(f"  [red]⚠ Budget threshold exceeded: ${report.total_cost:.2f} / ${budget_threshold:.2f} ({threshold_pct:.1f}%)[/red]")
                else:
                    remaining = budget_threshold - report.total_cost
                    console.print(f"  [green]✓ Within threshold: ${report.total_cost:.2f} / ${budget_threshold:.2f} ({threshold_pct:.1f}%)[/green]")
                    console.print(f"    [dim]Remaining: ${remaining:.2f}[/dim]")
            
            if budget_limit is not None:
                limit_pct = (report.total_cost / budget_limit) * 100
                if report.total_cost >= budget_limit:
                    console.print(f"  [bold red]❌ BUDGET LIMIT EXCEEDED: ${report.total_cost:.2f} / ${budget_limit:.2f} ({limit_pct:.1f}%)[/bold red]")
                else:
                    remaining = budget_limit - report.total_cost
                    console.print(f"  [green]✓ Within limit: ${report.total_cost:.2f} / ${budget_limit:.2f} ({limit_pct:.1f}%)[/green]")
                    console.print(f"    [dim]Remaining: ${remaining:.2f}[/dim]")
            
            console.print()

        # Time period
        console.print(f"[dim]Period: {report.start_time.strftime('%Y-%m-%d %H:%M:%S')} to {report.end_time.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
        console.print()

        # Export to JSON if requested
        if export:
            export_path = Path(export)
            
            # Build export data
            export_data = {
                "title": title,
                "generated_at": datetime.now().isoformat(),
                "project_path": project_path,
                "phase_filter": phase_enum.value if phase_enum else None,
                "summary": {
                    "total_operations": report.operations_count,
                    "total_tokens": report.total_tokens,
                    "total_prompt_tokens": report.total_prompt_tokens,
                    "total_completion_tokens": report.total_completion_tokens,
                    "total_embedding_tokens": report.total_embedding_tokens,
                    "total_cost": report.total_cost,
                    "average_cost_per_operation": report.average_cost_per_operation,
                    "average_tokens_per_operation": report.average_tokens_per_operation,
                    "duration_seconds": report.duration_seconds,
                },
                "period": {
                    "start_time": report.start_time.isoformat(),
                    "end_time": report.end_time.isoformat(),
                },
                "breakdown_by_operation": report.by_operation,
                "breakdown_by_phase": {
                    phase_type.value: cost
                    for phase_type, cost in report.by_phase.items()
                },
                "budget_status": {},
                "operations": [
                    {
                        "operation_type": op.operation_type.value,
                        "prompt_tokens": op.prompt_tokens,
                        "completion_tokens": op.completion_tokens,
                        "total_tokens": op.total_tokens,
                        "estimated_cost": op.estimated_cost,
                        "timestamp": op.timestamp.isoformat(),
                        "phase": op.phase.value,
                        "model": op.model,
                    }
                    for op in report.operations
                ],
            }
            
            # Add budget status if configured
            if budget_threshold is not None:
                export_data["budget_status"]["threshold"] = budget_threshold
                export_data["budget_status"]["threshold_exceeded"] = report.total_cost >= budget_threshold
                export_data["budget_status"]["threshold_percentage"] = (report.total_cost / budget_threshold) * 100
            
            if budget_limit is not None:
                export_data["budget_status"]["limit"] = budget_limit
                export_data["budget_status"]["limit_exceeded"] = report.total_cost >= budget_limit
                export_data["budget_status"]["limit_percentage"] = (report.total_cost / budget_limit) * 100
            
            # Write JSON file
            try:
                export_path.parent.mkdir(parents=True, exist_ok=True)
                export_path.write_text(json.dumps(export_data, indent=2))
                console.print(f"[green]✓ Report exported to: {export_path}[/green]")
                console.print()
            except Exception as e:
                console.print(f"[red]Failed to export report: {e}[/red]")
                if logger:
                    logger.error(f"Export failed: {e}", exc_info=True)

    except typer.Exit:
        raise
    except Exception as e:
        error_msg = f"Failed to generate cost report: {e}"
        if logger:
            logger.error(error_msg, exc_info=True)
        console.print(f"[red]Error: {error_msg}[/red]")
        raise typer.Exit(1) from e


@app.command()
def status(
    project_path: Annotated[
        str | None, typer.Argument(help="Project directory path")
    ] = None,
    detailed: Annotated[
        bool, typer.Option("--detailed", "-d", help="Show detailed status information")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose output")
    ] = False,
) -> None:
    """Display current project status with phase progress and cost information.
    
    Shows:
    - Current workflow phase with progress percentage
    - Completed phases with checkmarks
    - Cost information (current and by phase)
    - Last activity timestamp
    - Next steps guidance
    
    Use --detailed for verbose output including:
    - Detailed phase information
    - Token usage breakdown
    - Index metadata
    - Session information
    """
    from pathlib import Path

    from rich.panel import Panel
    from rich.table import Table

    if project_path is None:
        project_path = os.getcwd()

    project_path = os.path.abspath(project_path)

    try:
        setup_cli_logging(verbose, False, project_path)

        dev_agent_dir = os.path.join(project_path, ".dev_agent")
        if not os.path.exists(dev_agent_dir):
            console.print(
                f"[red]Error: No dev-agent project found at {project_path}[/red]"
            )
            console.print(
                "Use '[cyan]dev-agent init[/cyan]' to initialize a new project."
            )
            raise typer.Exit(1)

        # Initialize workflow manager to access project state
        from ..workflow.workflow_manager import WorkflowManager

        cli = EnhancedCLI()
        workflow_manager = WorkflowManager(cli)

        try:
            project_state = workflow_manager.resume_project(project_path)
        except Exception as e:
            console.print(f"[red]Error: Could not load project state: {e}[/red]")
            raise typer.Exit(1)

        # Display header
        console.print()
        console.print(
            Panel.fit(
                f"[bold cyan]Project Status[/bold cyan]\n"
                f"[dim]{project_path}[/dim]",
                border_style="cyan",
            )
        )
        console.print()

        # Create phase status table
        phase_table = Table(
            title="Workflow Progress",
            show_header=True,
            header_style="bold cyan",
        )
        phase_table.add_column("Phase", style="cyan", width=20)
        phase_table.add_column("Status", justify="center", width=15)
        phase_table.add_column("Progress", justify="center", width=15)

        # Define all phases in order
        from ..models.enums import PhaseType

        all_phases = [
            PhaseType.INDEXING,
            PhaseType.SPECIFICATION,
            PhaseType.DESIGN,
            PhaseType.IMPLEMENTATION,
        ]

        current_phase_index = all_phases.index(project_state.current_phase)

        # Add rows for each phase
        for i, phase in enumerate(all_phases):
            phase_name = phase.value.title()

            if i < current_phase_index:
                # Completed phase
                status = "[green]✓ Complete[/green]"
                progress = "[green]100%[/green]"
            elif i == current_phase_index:
                # Current phase
                status = "[yellow]⚡ In Progress[/yellow]"

                # Calculate progress based on phase
                if phase == PhaseType.INDEXING:
                    progress_pct = 100 if project_state.indexing_complete else 50
                elif phase == PhaseType.SPECIFICATION:
                    progress_pct = 100 if project_state.specification else 50
                elif phase == PhaseType.DESIGN:
                    progress_pct = 100 if project_state.design else 50
                elif phase == PhaseType.IMPLEMENTATION:
                    if project_state.tasks and project_state.implementation_progress:
                        total_tasks = len(project_state.implementation_progress)
                        completed_tasks = sum(
                            1
                            for status in project_state.implementation_progress.values()
                            if status.value == "completed"
                        )
                        progress_pct = (
                            int((completed_tasks / total_tasks) * 100)
                            if total_tasks > 0
                            else 0
                        )
                    else:
                        progress_pct = 0
                else:
                    progress_pct = 0

                progress = f"[yellow]{progress_pct}%[/yellow]"
            else:
                # Not started
                status = "[dim]○ Not Started[/dim]"
                progress = "[dim]0%[/dim]"

            phase_table.add_row(phase_name, status, progress)

        console.print(phase_table)
        console.print()

        # Display cost information
        cost_report = workflow_manager.cost_tracker.get_report()

        cost_table = Table(
            title="Cost Summary",
            show_header=True,
            header_style="bold cyan",
        )
        cost_table.add_column("Metric", style="cyan", width=30)
        cost_table.add_column("Value", justify="right", style="green", width=20)

        cost_table.add_row("Total Operations", str(cost_report.operations_count))
        cost_table.add_row(
            "Total Tokens",
            f"{cost_report.total_prompt_tokens + cost_report.total_completion_tokens + cost_report.total_embedding_tokens:,}",
        )
        cost_table.add_row("Total Cost", f"${cost_report.total_cost:.4f}")

        # Add cost by phase if available
        if cost_report.by_phase:
            cost_table.add_row("", "")  # Separator
            for phase_type, cost in cost_report.by_phase.items():
                cost_table.add_row(
                    f"  {phase_type.value.title()} Phase", f"${cost:.4f}"
                )

        console.print(cost_table)
        console.print()

        # Display last activity
        last_activity = project_state.session_data.last_activity
        console.print(
            f"[cyan]Last Activity:[/cyan] {last_activity.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        console.print()

        # Display detailed information if requested
        if detailed:
            console.print("[bold cyan]Detailed Information[/bold cyan]")
            console.print()

            # Index metadata
            if project_state.index_metadata:
                index_table = Table(
                    title="Index Metadata",
                    show_header=False,
                    box=None,
                    padding=(0, 2),
                )
                index_table.add_column("Property", style="cyan")
                index_table.add_column("Value", style="white")

                index_table.add_row("Total Files", str(project_state.index_metadata.total_files))
                index_table.add_row(
                    "Total Lines", f"{project_state.index_metadata.total_lines:,}"
                )
                index_table.add_row(
                    "Languages",
                    ", ".join(project_state.index_metadata.languages_detected),
                )
                index_table.add_row(
                    "Index Size", f"{project_state.index_metadata.index_size_mb:.2f} MB"
                )
                index_table.add_row(
                    "Last Indexed",
                    project_state.index_metadata.last_indexed.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                )

                console.print(index_table)
                console.print()

            # Session information
            session_table = Table(
                title="Session Information",
                show_header=False,
                box=None,
                padding=(0, 2),
            )
            session_table.add_column("Property", style="cyan")
            session_table.add_column("Value", style="white")

            session_table.add_row("Session ID", project_state.session_data.session_id)
            session_table.add_row(
                "Started At",
                project_state.session_data.started_at.strftime("%Y-%m-%d %H:%M:%S"),
            )

            # User approvals
            if project_state.session_data.user_approvals:
                approvals_str = ", ".join(
                    f"{phase}: {'✓' if approved else '✗'}"
                    for phase, approved in project_state.session_data.user_approvals.items()
                )
                session_table.add_row("Approvals", approvals_str)

            # Pending approvals
            if project_state.session_data.pending_approvals:
                session_table.add_row(
                    "Pending Approvals",
                    ", ".join(project_state.session_data.pending_approvals),
                )

            console.print(session_table)
            console.print()

            # Token usage breakdown
            console.print("[bold cyan]Token Usage Breakdown[/bold cyan]")
            token_table = Table(show_header=True, header_style="bold cyan")
            token_table.add_column("Type", style="cyan", width=20)
            token_table.add_column("Count", justify="right", style="white", width=15)

            token_table.add_row("Prompt Tokens", f"{cost_report.total_prompt_tokens:,}")
            token_table.add_row(
                "Completion Tokens", f"{cost_report.total_completion_tokens:,}"
            )
            token_table.add_row(
                "Embedding Tokens", f"{cost_report.total_embedding_tokens:,}"
            )

            console.print(token_table)
            console.print()

        # Display next steps based on current phase
        console.print("[bold cyan]Next Steps:[/bold cyan]")

        if project_state.current_phase == PhaseType.INDEXING:
            if not project_state.indexing_complete:
                console.print("  • Complete indexing of your codebase")
                console.print("  • Run [cyan]dev-agent resume[/cyan] to continue")
            else:
                console.print("  • Generate specification for your feature")
                console.print("  • Run [cyan]dev-agent resume[/cyan] to continue")
        elif project_state.current_phase == PhaseType.SPECIFICATION:
            if not project_state.specification:
                console.print("  • Create or review specification document")
                console.print("  • Run [cyan]dev-agent resume[/cyan] to continue")
            else:
                console.print("  • Review and approve specification")
                console.print("  • Proceed to design phase")
        elif project_state.current_phase == PhaseType.DESIGN:
            if not project_state.design:
                console.print("  • Create or review design document")
                console.print("  • Run [cyan]dev-agent resume[/cyan] to continue")
            else:
                console.print("  • Review and approve design")
                console.print("  • Proceed to implementation phase")
        elif project_state.current_phase == PhaseType.IMPLEMENTATION:
            if project_state.tasks:
                if project_state.implementation_progress:
                    total_tasks = len(project_state.implementation_progress)
                    completed_tasks = sum(
                        1
                        for status in project_state.implementation_progress.values()
                        if status.value == "completed"
                    )
                    console.print(
                        f"  • Continue implementation ({completed_tasks}/{total_tasks} tasks complete)"
                    )
                else:
                    console.print("  • Start implementing tasks")
                console.print("  • Run [cyan]dev-agent resume[/cyan] to continue")
            else:
                console.print("  • Generate implementation tasks")
                console.print("  • Run [cyan]dev-agent resume[/cyan] to continue")

        console.print()

    except typer.Exit:
        raise
    except Exception as e:
        error_msg = f"Failed to get project status: {e}"
        if logger:
            logger.error(error_msg, exc_info=True)
        console.print(f"[red]Error: {error_msg}[/red]")
        raise typer.Exit(1)


def _start_interactive_mode(
    project_path: str, session_manager: SessionManager, cli: InteractiveCLI
) -> None:
    """Start interactive CLI mode."""
    try:
        start_msg = f"Starting interactive mode for project: {project_path}"
        if logger:
            logger.info(start_msg)
        console.print(f"[blue]{start_msg}[/blue]")

        cli.start_chat_session()

    except Exception as e:
        error_msg = f"Error in interactive mode: {e}"
        if logger:
            logger.error(error_msg, exc_info=True)
        console.print(f"[red]Error: {error_msg}[/red]")
        raise typer.Exit(1)
    finally:
        if session_manager:
            if logger:
                logger.info("Ending session")
            session_manager.end_session()


# Config command group
config_app = typer.Typer(name="config", help="Configuration management")
app.add_typer(config_app, name="config")

# Azure command group
from .azure_config import app as azure_app

app.add_typer(azure_app, name="azure")

# Scaffold command group
scaffold_app = typer.Typer(name="scaffold", help="Project scaffolding and templates")
app.add_typer(scaffold_app, name="scaffold")

# Cleanup command group
cleanup_app = typer.Typer(name="cleanup", help="Repository cleanup and maintenance")
app.add_typer(cleanup_app, name="cleanup")


@config_app.command("show")
def config_show() -> None:
    """Show current configuration."""
    try:
        config = config_manager.get_config()

        console.print("[bold blue]Current dev-agent configuration:[/bold blue]")
        console.print("=" * 40)

        # Display configuration in a readable format
        config_dict = config.to_dict()
        console.print_json(json.dumps(config_dict, indent=2))

        console.print("=" * 40)
        console.print(f"[dim]Config file: {config_manager.config_path}[/dim]")

    except Exception as e:
        console.print(f"[red]Error showing configuration: {e}[/red]")
        raise typer.Exit(1)


@config_app.command("set")
def config_set(
    key: Annotated[str, typer.Argument(help="Configuration key (e.g., logging.level)")],
    value: Annotated[str, typer.Argument(help="Configuration value")],
) -> None:
    """Set configuration value."""
    try:
        # Parse nested keys
        keys = key.split(".")
        if len(keys) != 2:
            console.print(
                "[red]Error: Configuration key must be in format 'section.key' (e.g., 'logging.level')[/red]"
            )
            raise typer.Exit(1)

        section, config_key = keys

        # Convert value to appropriate type
        converted_value = _convert_config_value(value)

        # Update configuration
        update_dict = {section: {config_key: converted_value}}
        config_manager.update_config(**update_dict)

        console.print(
            f"[green]Configuration updated: {key} = {converted_value}[/green]"
        )
        if logger:
            logger.info(f"Configuration updated: {key} = {converted_value}")

    except Exception as e:
        console.print(f"[red]Error setting configuration: {e}[/red]")
        raise typer.Exit(1)


@config_app.command("reset")
def config_reset() -> None:
    """Reset configuration to defaults."""
    try:
        config_manager.reset_to_default()
        console.print("[green]Configuration reset to defaults.[/green]")
        if logger:
            logger.info("Configuration reset to defaults")
    except Exception as e:
        console.print(f"[red]Error resetting configuration: {e}[/red]")
        raise typer.Exit(1)


def _convert_config_value(value: str):
    """Convert string value to appropriate type."""
    # Try boolean
    if value.lower() in ("true", "false"):
        return value.lower() == "true"

    # Try integer
    try:
        return int(value)
    except ValueError:
        pass

    # Try float
    try:
        return float(value)
    except ValueError:
        pass

    # Return as string
    return value


def _check_configuration_and_warn(config) -> None:
    """Check configuration and provide helpful warnings.
    
    Offers to run setup wizard on first invocation if not configured.
    """
    from rich.prompt import Confirm

    from dev_agent.onboarding.setup_wizard import SetupWizard

    # Check if Azure OpenAI is configured
    if not config.azure_openai.api_key or not config.azure_openai.endpoint:
        console.print("[yellow]⚠ Azure OpenAI not configured[/yellow]")
        
        # Check if this is first run
        wizard = SetupWizard()
        prefs = wizard.load_existing_preferences()
        is_first_run = prefs is None or not prefs.azure_configured
        
        if is_first_run:
            console.print("\n[cyan]It looks like this is your first time using dev-agent.[/cyan]")
            console.print("Would you like to run the setup wizard to configure Azure OpenAI?")
            console.print()
            
            if Confirm.ask("Run setup wizard now?", default=True):
                console.print()
                result = wizard.run()
                
                if result.ready_to_use:
                    console.print("\n[green]✓ Setup complete! Continuing with initialization...[/green]")
                    # Reload config after setup
                    global config_manager
                    config_manager = ConfigManager()
                else:
                    console.print("\n[red]Setup incomplete. Please run [cyan]dev-agent setup[/cyan] to configure.[/red]")
                    raise typer.Exit(1)
            else:
                console.print("\n[yellow]You can run setup later with: [cyan]dev-agent setup[/cyan][/yellow]")
                console.print("[yellow]Azure OpenAI configuration is required to use dev-agent.[/yellow]")
                raise typer.Exit(1)
        else:
            console.print("\n[yellow]Please configure Azure OpenAI with: [cyan]dev-agent setup[/cyan][/yellow]")
            raise typer.Exit(1)


def _check_configuration_and_offer_setup(config, is_new_project: bool = False) -> bool:
    """Check configuration and offer setup wizard if needed.
    
    Args:
        config: Current configuration
        is_new_project: Whether this is a new project (empty directory)
        
    Returns:
        True if configuration is complete, False otherwise
    """
    from rich.prompt import Confirm

    from dev_agent.onboarding.setup_wizard import SetupWizard

    # Check if Azure OpenAI is configured
    if not config.azure_openai.api_key or not config.azure_openai.endpoint:
        console.print("[yellow]⚠ Azure OpenAI not configured[/yellow]")
        
        # Check if this is first run
        wizard = SetupWizard()
        prefs = wizard.load_existing_preferences()
        is_first_run = prefs is None or not prefs.azure_configured
        
        if is_first_run:
            console.print("\n[cyan]It looks like this is your first time using dev-agent.[/cyan]")
            
            if is_new_project:
                console.print(
                    "Before starting your new project, let's configure Azure OpenAI.\n"
                )
            else:
                console.print(
                    "Before analyzing your codebase, let's configure Azure OpenAI.\n"
                )
            
            if Confirm.ask("Run setup wizard now?", default=True):
                console.print()
                result = wizard.run()
                
                if result.ready_to_use:
                    console.print(
                        "\n[green]✓ Setup complete! Continuing with initialization...[/green]\n"
                    )
                    # Reload config after setup
                    global config_manager
                    config_manager = ConfigManager()
                    return True
                else:
                    console.print(
                        "\n[red]Setup incomplete. Please run [cyan]dev-agent setup[/cyan] to configure.[/red]"
                    )
                    return False
            else:
                console.print(
                    "\n[yellow]You can run setup later with: [cyan]dev-agent setup[/cyan][/yellow]"
                )
                console.print(
                    "[yellow]Azure OpenAI configuration is required to use dev-agent.[/yellow]"
                )
                return False
        else:
            console.print(
                "\n[yellow]Please configure Azure OpenAI with: [cyan]dev-agent setup[/cyan][/yellow]"
            )
            return False
    
    # Configuration is complete
    return True


@scaffold_app.command("list")
def scaffold_list(
    language: Annotated[
        str | None, typer.Option("--language", "-l", help="Filter by programming language")
    ] = None,
    project_type: Annotated[
        str | None, typer.Option("--type", "-t", help="Filter by project type")
    ] = None,
    framework: Annotated[
        str | None, typer.Option("--framework", "-f", help="Filter by framework")
    ] = None,
) -> None:
    """List available project templates."""
    try:
        from ..generation.template_system import TemplateSystem
        from ..models.enums import FrameworkType, LanguageType, ProjectType

        template_system = TemplateSystem()

        # Convert string filters to enums if provided
        language_filter = None
        if language:
            try:
                language_filter = LanguageType(language.lower())
            except ValueError:
                console.print(f"[red]Invalid language: {language}[/red]")
                console.print(f"Available languages: {', '.join([l.value for l in LanguageType])}")
                raise typer.Exit(1)

        project_type_filter = None
        if project_type:
            try:
                project_type_filter = ProjectType(project_type.lower().replace("-", "_"))
            except ValueError:
                console.print(f"[red]Invalid project type: {project_type}[/red]")
                console.print(f"Available types: {', '.join([t.value for t in ProjectType])}")
                raise typer.Exit(1)

        framework_filter = None
        if framework:
            try:
                framework_filter = FrameworkType(framework.lower())
            except ValueError:
                console.print(f"[red]Invalid framework: {framework}[/red]")
                console.print(f"Available frameworks: {', '.join([f.value for f in FrameworkType])}")
                raise typer.Exit(1)

        # Get filtered templates
        templates = template_system.list_available_templates(
            language=language_filter,
            project_type=project_type_filter,
            framework=framework_filter,
        )

        if not templates:
            console.print("[yellow]No templates found matching the specified criteria.[/yellow]")
            return

        console.print(f"[bold blue]Available Templates ({len(templates)} found):[/bold blue]")
        console.print("=" * 60)

        for template in templates:
            console.print(f"[bold green]{template.name}[/bold green] ({template.id})")
            console.print(f"  Description: {template.description}")
            console.print(f"  Languages: {', '.join([l.value for l in template.supported_languages])}")
            console.print(f"  Project Types: {', '.join([t.value for t in template.project_types])}")
            if template.supported_frameworks:
                console.print(f"  Frameworks: {', '.join([f.value for f in template.supported_frameworks])}")
            console.print()

    except Exception as e:
        console.print(f"[red]Error listing templates: {e}[/red]")
        raise typer.Exit(1)


@scaffold_app.command("create")
def scaffold_create(
    name: Annotated[str, typer.Argument(help="Project name")],
    template_id: Annotated[
        str | None, typer.Option("--template", "-t", help="Template ID to use")
    ] = None,
    output_path: Annotated[
        str | None, typer.Option("--output", "-o", help="Output directory path")
    ] = None,
    description: Annotated[
        str | None, typer.Option("--description", "-d", help="Project description")
    ] = None,
    language: Annotated[
        str | None, typer.Option("--language", "-l", help="Primary programming language")
    ] = None,
    project_type: Annotated[
        str | None, typer.Option("--type", help="Project type")
    ] = None,
    author_name: Annotated[
        str | None, typer.Option("--author", help="Author name")
    ] = None,
    author_email: Annotated[
        str | None, typer.Option("--email", help="Author email")
    ] = None,
    include_ci_cd: Annotated[
        bool, typer.Option("--ci-cd/--no-ci-cd", help="Include CI/CD configuration")
    ] = True,
    include_docker: Annotated[
        bool, typer.Option("--docker/--no-docker", help="Include Docker configuration")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose output")
    ] = False,
) -> None:
    """Create a new project from a template."""
    try:
        from pathlib import Path

        from ..generation.template_system import TemplateSystem
        from ..models.enums import CICDPlatform, LanguageType, ProjectType
        from ..models.templates import ProjectSpec

        setup_cli_logging(verbose, False)

        template_system = TemplateSystem()

        # Set default output path
        if output_path is None:
            output_path = os.path.join(os.getcwd(), name)

        output_path = Path(output_path).resolve()

        # Interactive template selection if not provided
        if template_id is None:
            templates = template_system.list_available_templates()
            if not templates:
                console.print("[red]No templates available.[/red]")
                raise typer.Exit(1)

            console.print("[bold blue]Available Templates:[/bold blue]")
            for i, template in enumerate(templates, 1):
                console.print(f"  {i}. {template.name} ({template.id})")
                console.print(f"     {template.description}")

            while True:
                try:
                    choice = typer.prompt("Select template number")
                    template_index = int(choice) - 1
                    if 0 <= template_index < len(templates):
                        template_id = templates[template_index].id
                        break
                    else:
                        console.print("[red]Invalid selection. Please try again.[/red]")
                except ValueError:
                    console.print("[red]Please enter a valid number.[/red]")

        # Get the selected template
        template = template_system.get_template_by_id(template_id)
        if not template:
            console.print(f"[red]Template not found: {template_id}[/red]")
            raise typer.Exit(1)

        # Interactive project configuration
        if description is None:
            description = typer.prompt("Project description", default=f"A {template.name} project")

        if language is None and len(template.supported_languages) > 1:
            console.print("Available languages:")
            for i, lang in enumerate(template.supported_languages, 1):
                console.print(f"  {i}. {lang.value}")

            while True:
                try:
                    choice = typer.prompt("Select language number", default="1")
                    lang_index = int(choice) - 1
                    if 0 <= lang_index < len(template.supported_languages):
                        language = template.supported_languages[lang_index].value
                        break
                    else:
                        console.print("[red]Invalid selection. Please try again.[/red]")
                except ValueError:
                    console.print("[red]Please enter a valid number.[/red]")
        elif language is None:
            language = template.supported_languages[0].value

        if project_type is None and len(template.project_types) > 1:
            console.print("Available project types:")
            for i, ptype in enumerate(template.project_types, 1):
                console.print(f"  {i}. {ptype.value}")

            while True:
                try:
                    choice = typer.prompt("Select project type number", default="1")
                    type_index = int(choice) - 1
                    if 0 <= type_index < len(template.project_types):
                        project_type = template.project_types[type_index].value
                        break
                    else:
                        console.print("[red]Invalid selection. Please try again.[/red]")
                except ValueError:
                    console.print("[red]Please enter a valid number.[/red]")
        elif project_type is None:
            project_type = template.project_types[0].value

        # Create project specification
        project_spec = ProjectSpec(
            name=name,
            description=description,
            project_type=ProjectType(project_type.replace("-", "_")),
            primary_language=LanguageType(language),
            frameworks=template.supported_frameworks[:3],  # Use first 3 frameworks
            include_ci_cd=include_ci_cd,
            ci_cd_platform=CICDPlatform.GITHUB_ACTIONS if include_ci_cd else None,
            include_docker=include_docker,
            author_name=author_name,
            author_email=author_email,
        )

        # Create the project
        console.print(f"[blue]Creating project '{name}' using template '{template.name}'...[/blue]")

        result = template_system.create_project_scaffold(project_spec, output_path)

        if result.success:
            console.print(f"[green]✓ Project created successfully at: {result.project_path}[/green]")
            console.print(f"[green]✓ Created {len(result.created_files)} files[/green]")
            console.print(f"[green]✓ Created {len(result.created_directories)} directories[/green]")

            if result.warnings:
                console.print("[yellow]Warnings:[/yellow]")
                for warning in result.warnings:
                    console.print(f"  [yellow]⚠ {warning}[/yellow]")

            if result.next_steps:
                console.print("\n[bold blue]Next Steps:[/bold blue]")
                for i, step in enumerate(result.next_steps, 1):
                    console.print(f"  {i}. {step}")

        else:
            console.print("[red]✗ Project creation failed[/red]")
            for error in result.errors:
                console.print(f"  [red]✗ {error}[/red]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error creating project: {e}[/red]")
        if verbose and logger:
            logger.error("Project creation failed", exc_info=True)
        raise typer.Exit(1)


@scaffold_app.command("microservices")
def scaffold_microservices(
    name: Annotated[str, typer.Argument(help="Architecture name")],
    output_path: Annotated[
        str | None, typer.Option("--output", "-o", help="Output directory path")
    ] = None,
    services: Annotated[
        str | None, typer.Option("--services", help="Comma-separated list of service names")
    ] = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose output")
    ] = False,
) -> None:
    """Create a microservices architecture."""
    try:
        from pathlib import Path

        from ..generation.microservices_scaffolder import (
            MicroservicesArchitecture,
            MicroserviceSpec,
            MicroservicesScaffolder,
        )
        from ..generation.template_system import TemplateSystem
        from ..models.enums import FrameworkType, LanguageType

        setup_cli_logging(verbose, False)

        # Set default output path
        if output_path is None:
            output_path = os.path.join(os.getcwd(), name)

        output_path = Path(output_path).resolve()

        # Parse services or use interactive mode
        service_specs = []
        if services:
            service_names = [s.strip() for s in services.split(",")]
            for i, service_name in enumerate(service_names):
                service_specs.append(
                    MicroserviceSpec(
                        name=service_name,
                        description=f"{service_name.replace('-', ' ').title()} service",
                        port=8000 + i,
                        language=LanguageType.PYTHON,
                        framework=FrameworkType.FASTAPI,
                    )
                )
        else:
            # Interactive service configuration
            console.print("[bold blue]Configure Microservices:[/bold blue]")

            while True:
                service_name = typer.prompt("Service name (or 'done' to finish)")
                if service_name.lower() == "done":
                    break

                service_description = typer.prompt(
                    "Service description",
                    default=f"{service_name.replace('-', ' ').title()} service"
                )

                port = typer.prompt("Service port", default=str(8000 + len(service_specs)))

                service_specs.append(
                    MicroserviceSpec(
                        name=service_name,
                        description=service_description,
                        port=int(port),
                        language=LanguageType.PYTHON,
                        framework=FrameworkType.FASTAPI,
                    )
                )

        if not service_specs:
            console.print("[red]At least one service is required.[/red]")
            raise typer.Exit(1)

        # Create microservices architecture
        architecture = MicroservicesArchitecture(
            name=name,
            description=f"{name.replace('-', ' ').title()} microservices platform",
            services=service_specs,
            api_gateway=True,
            service_discovery="consul",
            monitoring=True,
            logging=True,
        )

        # Create the scaffolder and generate the architecture
        template_system = TemplateSystem()
        scaffolder = MicroservicesScaffolder(template_system)

        console.print(f"[blue]Creating microservices architecture '{name}'...[/blue]")

        result = scaffolder.scaffold_microservices_architecture(architecture, output_path)

        if result.success:
            console.print(f"[green]✓ Microservices architecture created successfully at: {result.project_path}[/green]")
            console.print(f"[green]✓ Created {len(result.created_files)} files[/green]")
            console.print(f"[green]✓ Created {len(result.created_directories)} directories[/green]")
            console.print(f"[green]✓ Configured {len(service_specs)} services[/green]")

            if result.warnings:
                console.print("[yellow]Warnings:[/yellow]")
                for warning in result.warnings:
                    console.print(f"  [yellow]⚠ {warning}[/yellow]")

            if result.next_steps:
                console.print("\n[bold blue]Next Steps:[/bold blue]")
                for i, step in enumerate(result.next_steps, 1):
                    console.print(f"  {i}. {step}")

        else:
            console.print("[red]✗ Architecture creation failed[/red]")
            for error in result.errors:
                console.print(f"  [red]✗ {error}[/red]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error creating microservices architecture: {e}[/red]")
        if verbose and logger:
            logger.error("Microservices architecture creation failed", exc_info=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()


@cleanup_app.command("scan")
def cleanup_scan(
    project_path: Annotated[
        str | None, typer.Argument(help="Project directory path")
    ] = None,
    safety_level: Annotated[
        str,
        typer.Option(
            "--safety-level",
            "-s",
            help="Safety level: safe, moderate, or aggressive",
        ),
    ] = "safe",
    category: Annotated[
        str | None,
        typer.Option(
            "--category",
            "-c",
            help="Specific category to scan: temp, generated, artifacts, examples, deps",
        ),
    ] = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose output")
    ] = False,
) -> None:
    """Scan for cleanup candidates and show cleanup plan.

    This command scans the project directory for files and directories
    that can be cleaned up, including temporary files, generated files,
    development artifacts, obsolete examples, and unused dependencies.

    Safety levels:
    - safe: Only temporary and generated files
    - moderate: Also includes development artifacts
    - aggressive: Also includes obsolete examples and unused dependencies
    """
    from pathlib import Path

    from rich.panel import Panel
    from rich.table import Table

    try:
        setup_cli_logging(verbose, False, project_path)

        if project_path is None:
            project_path = os.getcwd()

        project_path = os.path.abspath(project_path)

        if not os.path.exists(project_path):
            console.print(
                f"[red]Error: Project path does not exist: {project_path}[/red]"
            )
            raise typer.Exit(1)

        # Validate safety level
        if safety_level not in ["safe", "moderate", "aggressive"]:
            console.print(
                f"[red]Invalid safety level: {safety_level}[/red]\n"
                "Valid options: safe, moderate, aggressive"
            )
            raise typer.Exit(1)

        # Validate category if provided
        valid_categories = ["temp", "generated", "artifacts", "examples", "deps"]
        if category and category not in valid_categories:
            console.print(
                f"[red]Invalid category: {category}[/red]\n"
                f"Valid options: {', '.join(valid_categories)}"
            )
            raise typer.Exit(1)

        console.print(
            Panel.fit(
                f"[bold blue]Scanning for Cleanup Candidates[/bold blue]\n"
                f"Project: {project_path}\n"
                f"Safety Level: {safety_level}",
                border_style="blue",
            )
        )
        console.print()

        # Import cleanup manager
        from dev_agent.cleanup.cleanup_manager import CleanupManager

        # Create cleanup manager
        manager = CleanupManager(Path(project_path), safety_level=safety_level)

        # Scan for cleanup candidates
        with console.status("[cyan]Scanning project...", spinner="dots"):
            if category:
                # Scan specific category only
                plan = manager.scan_for_cleanup_candidates()
                # Filter plan based on category
                if category == "temp":
                    plan.directories_to_remove = [
                        d
                        for d in plan.directories_to_remove
                        if any(
                            p in str(d)
                            for p in [
                                "__pycache__",
                                ".pytest_cache",
                                ".mypy_cache",
                                ".ruff_cache",
                            ]
                        )
                    ]
                    plan.files_to_move = {}
                    plan.dependencies_to_remove = []
                elif category == "generated":
                    plan.files_to_remove = [
                        f for f in plan.files_to_remove if "TASK_" in str(f)
                    ]
                    plan.directories_to_remove = [
                        d for d in plan.directories_to_remove if "site" in str(d)
                    ]
                    plan.files_to_move = {}
                    plan.dependencies_to_remove = []
                elif category == "artifacts":
                    plan.files_to_remove = []
                    plan.directories_to_remove = []
                    plan.dependencies_to_remove = []
                elif category == "examples":
                    plan.files_to_remove = [
                        f for f in plan.files_to_remove if "examples" in str(f)
                    ]
                    plan.directories_to_remove = []
                    plan.files_to_move = {}
                    plan.dependencies_to_remove = []
                elif category == "deps":
                    plan.files_to_remove = []
                    plan.directories_to_remove = []
                    plan.files_to_move = {}
            else:
                plan = manager.scan_for_cleanup_candidates()

        # Display summary
        summary = plan.get_summary()

        console.print("[bold green]Scan Complete![/bold green]")
        console.print()

        # Create summary table
        summary_table = Table(
            title="Cleanup Plan Summary", show_header=True, header_style="bold cyan"
        )
        summary_table.add_column("Category", style="cyan")
        summary_table.add_column("Count", justify="right", style="white")

        summary_table.add_row("Files to Remove", str(summary["files_to_remove"]))
        summary_table.add_row(
            "Directories to Remove", str(summary["directories_to_remove"])
        )
        summary_table.add_row("Files to Move", str(summary["files_to_move"]))
        summary_table.add_row(
            "Dependencies to Remove", str(summary["dependencies_to_remove"])
        )
        summary_table.add_row("", "")
        summary_table.add_row(
            "[bold]Total Items[/bold]", f"[bold]{summary['total_items']}[/bold]"
        )
        summary_table.add_row(
            "[bold]Size Reduction[/bold]",
            f"[bold]{summary['size_reduction_mb']} MB[/bold]",
        )
        summary_table.add_row(
            "[bold]Estimated Time[/bold]", f"[bold]{summary['estimated_time']}[/bold]"
        )

        console.print(summary_table)
        console.print()

        # Show sample files
        if plan.files_to_remove:
            console.print("[bold yellow]Sample Files to Remove:[/bold yellow]")
            for file_path in list(plan.files_to_remove)[:10]:
                try:
                    rel_path = file_path.relative_to(Path(project_path))
                    console.print(f"  - {rel_path}")
                except ValueError:
                    console.print(f"  - {file_path}")
            if len(plan.files_to_remove) > 10:
                console.print(
                    f"  [dim]... and {len(plan.files_to_remove) - 10} more files[/dim]"
                )
            console.print()

        if plan.directories_to_remove:
            console.print("[bold yellow]Directories to Remove:[/bold yellow]")
            for dir_path in list(plan.directories_to_remove)[:10]:
                try:
                    rel_path = dir_path.relative_to(Path(project_path))
                    console.print(f"  - {rel_path}/")
                except ValueError:
                    console.print(f"  - {dir_path}/")
            if len(plan.directories_to_remove) > 10:
                console.print(
                    f"  [dim]... and {len(plan.directories_to_remove) - 10} more directories[/dim]"
                )
            console.print()

        if plan.files_to_move:
            console.print("[bold yellow]Files to Move:[/bold yellow]")
            for src, dst in list(plan.files_to_move.items())[:5]:
                try:
                    src_rel = src.relative_to(Path(project_path))
                    dst_rel = dst.relative_to(Path(project_path))
                    console.print(f"  - {src_rel} → {dst_rel}")
                except ValueError:
                    console.print(f"  - {src} → {dst}")
            if len(plan.files_to_move) > 5:
                console.print(
                    f"  [dim]... and {len(plan.files_to_move) - 5} more files[/dim]"
                )
            console.print()

        if plan.dependencies_to_remove:
            console.print("[bold yellow]Dependencies to Remove:[/bold yellow]")
            for dep in plan.dependencies_to_remove:
                console.print(f"  - {dep}")
            console.print()

        # Show next steps
        console.print("[bold blue]Next Steps:[/bold blue]")
        console.print("  1. Review the cleanup plan above")
        console.print(
            "  2. Run [cyan]dev-agent cleanup --dry-run[/cyan] to simulate cleanup"
        )
        console.print(
            "  3. Run [cyan]dev-agent cleanup --execute[/cyan] to perform cleanup"
        )
        console.print()

    except Exception as e:
        error_msg = f"Failed to scan for cleanup candidates: {e}"
        if logger:
            logger.error(error_msg, exc_info=True)
        console.print(f"[red]Error: {error_msg}[/red]")
        raise typer.Exit(1) from e


@cleanup_app.command("dry-run")
def cleanup_dry_run(
    project_path: Annotated[
        str | None, typer.Argument(help="Project directory path")
    ] = None,
    safety_level: Annotated[
        str,
        typer.Option(
            "--safety-level",
            "-s",
            help="Safety level: safe, moderate, or aggressive",
        ),
    ] = "safe",
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose output")
    ] = False,
) -> None:
    """Simulate cleanup without making any changes.

    This command performs a dry-run of the cleanup operation, showing
    exactly what would be removed or moved without actually making any
    changes to the filesystem.
    """
    from pathlib import Path

    from rich.panel import Panel

    try:
        setup_cli_logging(verbose, False, project_path)

        if project_path is None:
            project_path = os.getcwd()

        project_path = os.path.abspath(project_path)

        if not os.path.exists(project_path):
            console.print(
                f"[red]Error: Project path does not exist: {project_path}[/red]"
            )
            raise typer.Exit(1)

        # Validate safety level
        if safety_level not in ["safe", "moderate", "aggressive"]:
            console.print(
                f"[red]Invalid safety level: {safety_level}[/red]\n"
                "Valid options: safe, moderate, aggressive"
            )
            raise typer.Exit(1)

        console.print(
            Panel.fit(
                "[bold yellow]Cleanup Dry-Run Mode[/bold yellow]\n"
                "[dim]No changes will be made to the filesystem[/dim]",
                border_style="yellow",
            )
        )
        console.print()

        # Import cleanup manager
        from dev_agent.cleanup.cleanup_manager import CleanupManager

        # Create cleanup manager
        manager = CleanupManager(Path(project_path), safety_level=safety_level)

        # Scan for cleanup candidates
        with console.status("[cyan]Scanning project...", spinner="dots"):
            plan = manager.scan_for_cleanup_candidates()

        # Execute dry-run
        console.print("[bold blue]Executing dry-run...[/bold blue]")
        console.print()

        # Execute cleanup in dry-run mode (result not used, just for logging)
        _ = manager.execute_cleanup(plan, dry_run=True)

        console.print()
        console.print(
            Panel.fit(
                "[bold green]Dry-run Complete[/bold green]\n"
                "[dim]No changes were made[/dim]",
                border_style="green",
            )
        )
        console.print()

        # Show what would happen
        console.print("[bold blue]Summary of Changes:[/bold blue]")
        console.print(f"  - Would remove {len(plan.files_to_remove)} files")
        console.print(f"  - Would remove {len(plan.directories_to_remove)} directories")
        console.print(f"  - Would move {len(plan.files_to_move)} files")
        console.print(
            f"  - Would remove {len(plan.dependencies_to_remove)} dependencies"
        )
        console.print(f"  - Size reduction: {plan.size_reduction_mb:.2f} MB")
        console.print()

        console.print("[bold blue]To execute cleanup:[/bold blue]")
        console.print("  Run [cyan]dev-agent cleanup --execute[/cyan]")
        console.print()

    except Exception as e:
        error_msg = f"Failed to perform dry-run: {e}"
        if logger:
            logger.error(error_msg, exc_info=True)
        console.print(f"[red]Error: {error_msg}[/red]")
        raise typer.Exit(1) from e


@cleanup_app.command("execute")
def cleanup_execute(
    project_path: Annotated[
        str | None, typer.Argument(help="Project directory path")
    ] = None,
    safety_level: Annotated[
        str,
        typer.Option(
            "--safety-level",
            "-s",
            help="Safety level: safe, moderate, or aggressive",
        ),
    ] = "safe",
    yes: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            help="Skip confirmation prompts",
        ),
    ] = False,
    save_report: Annotated[
        bool,
        typer.Option(
            "--save-report/--no-save-report",
            help="Save cleanup report to file",
        ),
    ] = True,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose output")
    ] = False,
) -> None:
    """Execute cleanup operations with confirmation prompts.

    This command performs the actual cleanup operation, removing or moving
    files as specified in the cleanup plan. A backup is created before
    any changes are made.

    WARNING: This operation will modify your filesystem. Always review
    the cleanup plan with --scan or --dry-run first.
    """
    from pathlib import Path

    from rich.panel import Panel
    from rich.prompt import Confirm

    try:
        setup_cli_logging(verbose, False, project_path)

        if project_path is None:
            project_path = os.getcwd()

        project_path = os.path.abspath(project_path)

        if not os.path.exists(project_path):
            console.print(
                f"[red]Error: Project path does not exist: {project_path}[/red]"
            )
            raise typer.Exit(1)

        # Validate safety level
        if safety_level not in ["safe", "moderate", "aggressive"]:
            console.print(
                f"[red]Invalid safety level: {safety_level}[/red]\n"
                "Valid options: safe, moderate, aggressive"
            )
            raise typer.Exit(1)

        console.print(
            Panel.fit(
                "[bold red]⚠️  Cleanup Execution Mode[/bold red]\n"
                "[yellow]This will modify your filesystem![/yellow]",
                border_style="red",
            )
        )
        console.print()

        # Import cleanup manager
        from dev_agent.cleanup.cleanup_manager import CleanupManager

        # Create cleanup manager
        manager = CleanupManager(Path(project_path), safety_level=safety_level)

        # Scan for cleanup candidates
        with console.status("[cyan]Scanning project...", spinner="dots"):
            plan = manager.scan_for_cleanup_candidates()

        # Show summary
        summary = plan.get_summary()
        console.print("[bold blue]Cleanup Plan Summary:[/bold blue]")
        console.print(f"  - Files to remove: {summary['files_to_remove']}")
        console.print(f"  - Directories to remove: {summary['directories_to_remove']}")
        console.print(f"  - Files to move: {summary['files_to_move']}")
        console.print(
            f"  - Dependencies to remove: {summary['dependencies_to_remove']}"
        )
        console.print(f"  - Total items: {summary['total_items']}")
        console.print(f"  - Size reduction: {summary['size_reduction_mb']} MB")
        console.print(f"  - Safety level: {summary['safety_level']}")
        console.print()

        # Confirmation prompt
        if not yes:
            console.print(
                "[yellow]⚠️  A backup will be created before cleanup[/yellow]"
            )
            console.print()

            if not Confirm.ask(
                "[bold]Do you want to proceed with cleanup?[/bold]", default=False
            ):
                console.print("[yellow]Cleanup cancelled by user[/yellow]")
                raise typer.Exit(0)

        # Execute cleanup
        console.print()
        console.print("[bold blue]Executing cleanup...[/bold blue]")
        console.print()

        with console.status("[cyan]Cleaning up...", spinner="dots"):
            result = manager.execute_cleanup(plan, dry_run=False)

        console.print()

        # Display results
        if result.error_count == 0:
            console.print(
                Panel.fit(
                    "[bold green]✅ Cleanup Complete![/bold green]\n"
                    f"Successfully processed {result.success_count} items",
                    border_style="green",
                )
            )
        else:
            console.print(
                Panel.fit(
                    "[bold yellow]⚠️  Cleanup Complete with Errors[/bold yellow]\n"
                    f"Successful: {result.success_count}, Errors: {result.error_count}",
                    border_style="yellow",
                )
            )

        console.print()

        # Show summary
        result_summary = result.get_summary()
        console.print("[bold blue]Cleanup Results:[/bold blue]")
        console.print(f"  - Removed files: {result_summary['removed_files']}")
        console.print(
            f"  - Removed directories: {result_summary['removed_directories']}"
        )
        console.print(f"  - Moved files: {result_summary['moved_files']}")
        console.print(
            f"  - Removed dependencies: {result_summary['removed_dependencies']}"
        )
        console.print(f"  - Size reduction: {result_summary['size_reduction_mb']} MB")
        console.print(f"  - Execution time: {result_summary['execution_time']} seconds")
        console.print(f"  - Success rate: {result_summary['success_rate']}%")
        console.print()

        # Show errors if any
        if result.errors:
            console.print("[bold red]Errors:[/bold red]")
            for error in result.errors[:10]:
                console.print(f"  [red]✗ {error}[/red]")
            if len(result.errors) > 10:
                console.print(f"  [dim]... and {len(result.errors) - 10} more errors[/dim]")
            console.print()

        # Generate and save report
        if save_report:
            report_path = Path(project_path) / "CLEANUP_REPORT.md"
            report_content = manager.generate_cleanup_report(result)

            with report_path.open("w", encoding="utf-8") as f:
                f.write(report_content)

            console.print(f"[dim]📄 Cleanup report saved to: {report_path}[/dim]")
            console.print()

        # Exit with appropriate code
        if result.error_count > 0:
            raise typer.Exit(1)
        else:
            raise typer.Exit(0)

    except Exception as e:
        error_msg = f"Failed to execute cleanup: {e}"
        if logger:
            logger.error(error_msg, exc_info=True)
        console.print(f"[red]Error: {error_msg}[/red]")
        raise typer.Exit(1) from e


@cleanup_app.callback()
def cleanup_callback() -> None:
    """Repository cleanup and maintenance commands.

    These commands help maintain a clean repository by identifying and
    removing temporary files, generated files, development artifacts,
    obsolete examples, and unused dependencies.

    Use --scan to see what would be cleaned, --dry-run to simulate,
    and --execute to perform the actual cleanup.
    """
