"""Main CLI entry point for dev-agent."""

import json
import logging
import os
from typing import Annotated

import typer
from rich.console import Console

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
    help="AI-powered development workflow assistant",
    rich_markup_mode="rich",
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


@app.callback()
def main(
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose output")
    ] = False,
    debug: Annotated[
        bool, typer.Option("--debug", help="Enable debug logging")
    ] = False,
    config_path: Annotated[
        str | None, typer.Option("--config-path", help="Path to configuration file")
    ] = None,
) -> None:
    """AI-powered development workflow assistant."""
    if config_path:
        # TODO: Handle custom config path
        pass


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
    """Initialize a new dev-agent project."""
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

        # Load project-specific configuration if available
        config_manager.load_project_config(project_path)

        # Check configuration and provide helpful messages
        config = config_manager.get_config()
        _check_configuration_and_warn(config)

        # Initialize CLI and session manager
        session_manager = SessionManager(project_path)

        # Initialize workflow manager
        from ..workflow.workflow_manager import WorkflowManager

        cli = EnhancedCLI()
        workflow_manager = WorkflowManager(cli)
        cli.workflow_manager = workflow_manager

        if logger:
            logger.info(f"Initializing project at: {project_path}")

        # Initialize project through workflow manager
        project_state = workflow_manager.start_new_project(project_path)

        success_msg = f"Started new project: {project_state.project_path}"
        if logger:
            logger.info(success_msg)
        console.print(f"[green]{success_msg}[/green]")

        # Start interactive mode after initialization
        _start_interactive_mode(project_path, session_manager, cli)

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
    """Resume an existing dev-agent project."""
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
        str | None, typer.Option("--phase", "-p", help="Filter by phase (INDEXING, SPECIFICATION, DESIGN, IMPLEMENTATION)")
    ] = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose output")
    ] = False,
) -> None:
    """Display cost report for Azure OpenAI usage."""
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
            raise typer.Exit(1)

        # Initialize workflow manager to access cost tracker
        from ..workflow.workflow_manager import WorkflowManager

        cli = EnhancedCLI()
        workflow_manager = WorkflowManager(cli)

        try:
            workflow_manager.resume_project(project_path)
        except Exception:
            console.print("[yellow]Could not load project state, showing empty report[/yellow]")

        # Get cost report
        if phase:
            try:
                from ..models.enums import PhaseType
                phase_enum = PhaseType(phase.upper())
                report = workflow_manager.cost_tracker.get_phase_report(phase_enum)
                console.print(f"[bold blue]Cost Report for {phase_enum.value} Phase[/bold blue]")
            except ValueError:
                console.print(f"[red]Invalid phase: {phase}[/red]")
                console.print("Valid phases: INDEXING, SPECIFICATION, DESIGN, IMPLEMENTATION")
                raise typer.Exit(1)
        else:
            report = workflow_manager.cost_tracker.get_report()
            console.print("[bold blue]Complete Cost Report[/bold blue]")

        console.print("=" * 60)

        # Display summary
        console.print(f"[cyan]Total Operations:[/cyan] {report.operations_count}")
        console.print(f"[cyan]Total Tokens:[/cyan] {report.total_prompt_tokens + report.total_completion_tokens + report.total_embedding_tokens:,}")
        console.print(f"  - Prompt Tokens: {report.total_prompt_tokens:,}")
        console.print(f"  - Completion Tokens: {report.total_completion_tokens:,}")
        console.print(f"  - Embedding Tokens: {report.total_embedding_tokens:,}")
        console.print(f"[green]Total Cost:[/green] ${report.total_cost:.4f}")

        # Display by phase
        if not phase and report.by_phase:
            console.print("\n[bold]Cost by Phase:[/bold]")
            for phase_type, cost in report.by_phase.items():
                console.print(f"  {phase_type.value}: ${cost:.4f}")

        # Display by operation type
        if report.by_operation:
            console.print("\n[bold]Operations by Type:[/bold]")
            for op_type, count in report.by_operation.items():
                console.print(f"  {op_type}: {count}")

        # Display time range
        console.print(f"\n[dim]Period: {report.start_time.strftime('%Y-%m-%d %H:%M:%S')} to {report.end_time.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
        console.print("=" * 60)

    except Exception as e:
        error_msg = f"Failed to generate cost report: {e}"
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
    """Check configuration and provide helpful warnings."""
    # Check if Azure OpenAI is configured
    if not config.azure_openai.api_key or not config.azure_openai.endpoint:
        console.print("[yellow]⚠ Azure OpenAI not configured[/yellow]")
        console.print("  Configure with: [cyan]dev-agent azure configure[/cyan]")
        console.print("  [dim]Note: Azure OpenAI is required for all AI operations[/dim]")
        console.print()


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
