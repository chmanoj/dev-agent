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
# from .enhanced_cli import EnhancedCLI
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

        # Initialize CLI and session manager
        session_manager = SessionManager(project_path)

        # Initialize workflow manager
        from ..workflow.workflow_manager import WorkflowManager

        cli = InteractiveCLI()
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
        config_manager.load_project_config(project_path)

        # Initialize session manager and try to resume
        session_manager = SessionManager(project_path)

        # Initialize workflow manager
        from ..workflow.workflow_manager import WorkflowManager

        cli = InteractiveCLI()
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
        cli = InteractiveCLI()

        _start_interactive_mode(project_path, session_manager, cli)

    except Exception as e:
        error_msg = f"Error in interactive mode: {e}"
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


if __name__ == "__main__":
    app()
