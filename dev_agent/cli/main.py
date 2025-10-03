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
                project_type_filter = ProjectType(project_type.lower().replace('-', '_'))
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
            project_type=ProjectType(project_type.replace('-', '_')),
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
            console.print(f"[red]✗ Project creation failed[/red]")
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
            MicroserviceSpec,
            MicroservicesArchitecture,
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
            console.print(f"[red]✗ Architecture creation failed[/red]")
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
