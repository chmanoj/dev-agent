"""Azure OpenAI configuration CLI commands."""

from __future__ import annotations

import os

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from dev_agent.config.config_manager import AzureOpenAIConfig, ConfigManager
from dev_agent.errors.exceptions import ConfigurationError
from dev_agent.services.azure_openai_service import AzureOpenAIService

console = Console()
app = typer.Typer(name="azure", help="Azure OpenAI configuration commands")


@app.command("configure")
def configure_azure_openai(
    api_key: str | None = typer.Option(None, "--api-key", help="Azure OpenAI API key"),
    endpoint: str | None = typer.Option(
        None, "--endpoint", help="Azure OpenAI endpoint URL"
    ),
    api_version: str | None = typer.Option(
        None, "--api-version", help="Azure OpenAI API version"
    ),
    chat_model: str | None = typer.Option(
        None, "--chat-model", help="Chat model deployment name"
    ),
    embedding_model: str | None = typer.Option(
        None, "--embedding-model", help="Embedding model deployment name"
    ),
    interactive: bool = typer.Option(
        True, "--interactive/--no-interactive", help="Interactive configuration"
    ),
) -> None:
    """Configure Azure OpenAI settings."""
    console.print("\n[bold blue]Azure OpenAI Configuration[/bold blue]")
    console.print("Configure your Azure OpenAI settings for dev-agent.\n")

    config_manager = ConfigManager()
    current_config = config_manager.get_config()

    # Interactive configuration
    if interactive:
        console.print("[yellow]Current configuration:[/yellow]")
        _display_current_config(current_config.azure_openai)
        console.print()

        if not Confirm.ask("Do you want to update the Azure OpenAI configuration?"):
            console.print("Configuration unchanged.")
            return

        # Get configuration values interactively
        api_key = api_key or _prompt_for_api_key(current_config.azure_openai.api_key)
        endpoint = endpoint or _prompt_for_endpoint(
            current_config.azure_openai.endpoint
        )
        api_version = api_version or _prompt_for_api_version(
            current_config.azure_openai.api_version
        )
        chat_model = chat_model or _prompt_for_chat_model(
            current_config.azure_openai.chat_model
        )
        embedding_model = embedding_model or _prompt_for_embedding_model(
            current_config.azure_openai.embedding_model
        )

    # Validate required fields
    if not api_key:
        console.print("[red]Error: API key is required[/red]")
        raise typer.Exit(1)

    if not endpoint:
        console.print("[red]Error: Endpoint URL is required[/red]")
        raise typer.Exit(1)

    # Create new Azure OpenAI configuration
    azure_config = AzureOpenAIConfig(
        api_key=api_key,
        endpoint=endpoint,
        api_version=api_version or current_config.azure_openai.api_version,
        chat_model=chat_model or current_config.azure_openai.chat_model,
        embedding_model=embedding_model or current_config.azure_openai.embedding_model,
        max_tokens=current_config.azure_openai.max_tokens,
        temperature=current_config.azure_openai.temperature,
        timeout=current_config.azure_openai.timeout,
        max_retries=current_config.azure_openai.max_retries,
    )

    # Update configuration
    current_config.azure_openai = azure_config

    # Enable Azure embeddings by default when Azure OpenAI is configured
    current_config.indexing.use_azure_embeddings = True

    try:
        config_manager.save_config(current_config)
        console.print(
            "\n[green]✓ Azure OpenAI configuration saved successfully![/green]"
        )

        # Test the configuration
        if interactive and Confirm.ask("Do you want to test the connection?"):
            test_azure_connection()

    except Exception as e:
        console.print(f"[red]Error saving configuration: {e}[/red]")
        raise typer.Exit(1)


@app.command("test")
def test_azure_connection() -> None:
    """Test Azure OpenAI connection."""
    console.print("\n[bold blue]Testing Azure OpenAI Connection[/bold blue]")

    config_manager = ConfigManager()
    config = config_manager.get_config()

    if not config.azure_openai.api_key or not config.azure_openai.endpoint:
        console.print(
            "[red]Error: Azure OpenAI not configured. Run 'dev-agent azure configure' first.[/red]"
        )
        raise typer.Exit(1)

    try:
        with console.status("[bold green]Testing connection..."):
            service = AzureOpenAIService(config.azure_openai)

            # Test chat completion
            console.print("Testing chat completion...")
            success = service.test_connection()

            if success:
                console.print("[green]✓ Chat completion test successful[/green]")
            else:
                console.print("[red]✗ Chat completion test failed[/red]")
                return

            # Test embeddings
            console.print("Testing embeddings...")
            try:
                response = service.generate_embeddings(["test embedding"])
                if response.embeddings:
                    console.print(
                        f"[green]✓ Embeddings test successful (dimension: {len(response.embeddings[0])})[/green]"
                    )
                else:
                    console.print(
                        "[red]✗ Embeddings test failed - no embeddings returned[/red]"
                    )
            except Exception as e:
                console.print(f"[red]✗ Embeddings test failed: {e}[/red]")

        console.print("\n[green]Azure OpenAI connection test completed![/green]")

    except ConfigurationError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Connection test failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("status")
def show_azure_status() -> None:
    """Show Azure OpenAI configuration status."""
    console.print("\n[bold blue]Azure OpenAI Status[/bold blue]")

    config_manager = ConfigManager()
    config = config_manager.get_config()

    # Create status table
    table = Table(title="Azure OpenAI Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Status", style="yellow")

    # Check configuration status
    api_key_status = "✓ Configured" if config.azure_openai.api_key else "✗ Not set"
    endpoint_status = "✓ Configured" if config.azure_openai.endpoint else "✗ Not set"

    table.add_row(
        "API Key", "***" if config.azure_openai.api_key else "Not set", api_key_status
    )
    table.add_row(
        "Endpoint", config.azure_openai.endpoint or "Not set", endpoint_status
    )
    table.add_row("API Version", config.azure_openai.api_version, "✓ Set")
    table.add_row("Chat Model", config.azure_openai.chat_model, "✓ Set")
    table.add_row("Embedding Model", config.azure_openai.embedding_model, "✓ Set")
    table.add_row(
        "Use Azure Embeddings",
        str(config.indexing.use_azure_embeddings),
        "✓ Enabled" if config.indexing.use_azure_embeddings else "✗ Disabled",
    )

    console.print(table)

    # Overall status
    if config.azure_openai.api_key and config.azure_openai.endpoint:
        console.print("\n[green]✓ Azure OpenAI is configured and ready to use[/green]")
    else:
        console.print("\n[red]✗ Azure OpenAI is not fully configured[/red]")
        console.print(
            "Run [cyan]dev-agent azure configure[/cyan] to set up Azure OpenAI"
        )


@app.command("models")
def list_available_models() -> None:
    """List available Azure OpenAI models."""
    console.print("\n[bold blue]Azure OpenAI Models[/bold blue]")

    # Common Azure OpenAI models
    chat_models = [
        ("gpt-4", "Most capable GPT-4 model"),
        ("gpt-4-32k", "GPT-4 with 32k context window"),
        ("gpt-4-turbo", "Latest GPT-4 Turbo model"),
        ("gpt-35-turbo", "GPT-3.5 Turbo model"),
        ("gpt-35-turbo-16k", "GPT-3.5 Turbo with 16k context"),
    ]

    embedding_models = [
        ("text-embedding-ada-002", "Most capable embedding model"),
        ("text-embedding-3-small", "Smaller, faster embedding model"),
        ("text-embedding-3-large", "Larger, more capable embedding model"),
    ]

    # Chat models table
    chat_table = Table(title="Chat Models")
    chat_table.add_column("Model Name", style="cyan")
    chat_table.add_column("Description", style="white")

    for model, description in chat_models:
        chat_table.add_row(model, description)

    console.print(chat_table)

    # Embedding models table
    embedding_table = Table(title="Embedding Models")
    embedding_table.add_column("Model Name", style="cyan")
    embedding_table.add_column("Description", style="white")

    for model, description in embedding_models:
        embedding_table.add_row(model, description)

    console.print(embedding_table)

    console.print(
        "\n[yellow]Note:[/yellow] Model availability depends on your Azure OpenAI deployment."
    )
    console.print(
        "Use the deployment names from your Azure OpenAI resource, not the base model names."
    )


@app.command("env")
def show_env_variables() -> None:
    """Show required environment variables."""
    console.print("\n[bold blue]Azure OpenAI Environment Variables[/bold blue]")

    env_vars = [
        (
            "AZURE_OPENAI_API_KEY",
            "Your Azure OpenAI API key",
            os.getenv("AZURE_OPENAI_API_KEY"),
        ),
        (
            "AZURE_OPENAI_ENDPOINT",
            "Your Azure OpenAI endpoint URL",
            os.getenv("AZURE_OPENAI_ENDPOINT"),
        ),
        (
            "AZURE_OPENAI_API_VERSION",
            "API version (optional)",
            os.getenv("AZURE_OPENAI_API_VERSION"),
        ),
        (
            "AZURE_OPENAI_CHAT_MODEL",
            "Chat model deployment name (optional)",
            os.getenv("AZURE_OPENAI_CHAT_MODEL"),
        ),
        (
            "AZURE_OPENAI_EMBEDDING_MODEL",
            "Embedding model deployment name (optional)",
            os.getenv("AZURE_OPENAI_EMBEDDING_MODEL"),
        ),
    ]

    table = Table(title="Environment Variables")
    table.add_column("Variable", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Current Value", style="green")
    table.add_column("Status", style="yellow")

    for var_name, description, current_value in env_vars:
        if current_value:
            if "key" in var_name.lower():
                display_value = "***"
            else:
                display_value = current_value
            status = "✓ Set"
        else:
            display_value = "Not set"
            status = "✗ Not set" if "optional" not in description else "○ Optional"

        table.add_row(var_name, description, display_value, status)

    console.print(table)

    console.print(
        "\n[yellow]You can set these environment variables or use the interactive configuration.[/yellow]"
    )


def _display_current_config(config: AzureOpenAIConfig) -> None:
    """Display current Azure OpenAI configuration."""
    table = Table()
    table.add_column("Setting", style="cyan")
    table.add_column("Current Value", style="white")

    table.add_row("API Key", "***" if config.api_key else "Not set")
    table.add_row("Endpoint", config.endpoint or "Not set")
    table.add_row("API Version", config.api_version)
    table.add_row("Chat Model", config.chat_model)
    table.add_row("Embedding Model", config.embedding_model)

    console.print(table)


def _prompt_for_api_key(current: str | None) -> str:
    """Prompt for API key."""
    if current:
        if Confirm.ask("Keep current API key (***)?"):
            return current

    while True:
        api_key = Prompt.ask("Enter your Azure OpenAI API key", password=True)
        if api_key.strip():
            return api_key.strip()
        console.print("[red]API key cannot be empty[/red]")


def _prompt_for_endpoint(current: str | None) -> str:
    """Prompt for endpoint URL."""
    default = current or "https://your-resource.openai.azure.com/"

    while True:
        endpoint = Prompt.ask("Enter your Azure OpenAI endpoint URL", default=default)
        if endpoint.strip():
            endpoint = endpoint.strip()
            if not endpoint.startswith(("http://", "https://")):
                console.print("[red]Endpoint must start with http:// or https://[/red]")
                continue
            return endpoint
        console.print("[red]Endpoint cannot be empty[/red]")


def _prompt_for_api_version(current: str) -> str:
    """Prompt for API version."""
    return Prompt.ask("Enter API version", default=current)


def _prompt_for_chat_model(current: str) -> str:
    """Prompt for chat model."""
    return Prompt.ask("Enter chat model deployment name", default=current)


def _prompt_for_embedding_model(current: str) -> str:
    """Prompt for embedding model."""
    return Prompt.ask("Enter embedding model deployment name", default=current)
