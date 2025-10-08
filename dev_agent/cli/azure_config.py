"""Azure OpenAI configuration CLI commands."""

from __future__ import annotations

import json
import os
from pathlib import Path

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from dev_agent.config.config_manager import ConfigManager
from dev_agent.errors.exceptions import ConfigurationError
from dev_agent.errors.llm_exceptions import (
    LLMAPIError,
    LLMAuthenticationError,
    LLMBadRequestError,
)
from dev_agent.llm.azure_client import AzureOpenAIClient
from dev_agent.llm.embeddings import AzureEmbeddingClient
from dev_agent.models.llm_config import AzureOpenAIConfig

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
    deployment_name: str | None = typer.Option(
        None, "--deployment-name", help="GPT-4 deployment name"
    ),
    embedding_deployment: str | None = typer.Option(
        None, "--embedding-deployment", help="Embedding model deployment name"
    ),
    interactive: bool = typer.Option(
        True, "--interactive/--no-interactive", help="Interactive configuration"
    ),
) -> None:
    """Configure Azure OpenAI settings with enhanced validation.
    
    This command provides an interactive wizard to configure Azure OpenAI
    credentials and settings. It validates all inputs and can optionally
    test the connection after configuration.
    
    Examples:
        # Interactive configuration (recommended)
        dev-agent azure configure
        
        # Non-interactive configuration
        dev-agent azure configure --no-interactive \\
            --api-key "your-key" \\
            --endpoint "https://your-resource.openai.azure.com/" \\
            --deployment-name "gpt-4" \\
            --embedding-deployment "text-embedding-ada-002"
    """
    console.print("\n[bold blue]Azure OpenAI Configuration Wizard[/bold blue]")
    console.print("Configure your Azure OpenAI settings for dev-agent.\n")
    
    # Display security warning
    console.print(Panel(
        "[yellow]Security Notice:[/yellow]\n"
        "• API keys will be stored in your configuration file\n"
        "• Consider using environment variables for production\n"
        "• Never commit API keys to version control\n"
        "• Use Azure Key Vault for sensitive deployments",
        title="⚠️  Security",
        border_style="yellow"
    ))
    console.print()

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

        # Get configuration values interactively with validation
        api_key = api_key or _prompt_for_api_key(current_config.azure_openai.api_key)
        endpoint = endpoint or _prompt_for_endpoint(
            current_config.azure_openai.endpoint
        )
        api_version = api_version or _prompt_for_api_version(
            current_config.azure_openai.api_version
        )
        deployment_name = deployment_name or _prompt_for_deployment_name(
            current_config.azure_openai.deployment_name
        )
        embedding_deployment = embedding_deployment or _prompt_for_embedding_deployment(
            current_config.azure_openai.embedding_deployment
        )

    # Validate required fields
    if not api_key:
        console.print(Panel(
            "[red]Error: API key is required[/red]\n\n"
            "To get an API key:\n"
            "1. Go to Azure Portal (portal.azure.com)\n"
            "2. Navigate to your Azure OpenAI resource\n"
            "3. Go to 'Keys and Endpoint' section\n"
            "4. Copy one of the keys\n\n"
            "Or set the AZURE_OPENAI_API_KEY environment variable.",
            title="❌ Missing API Key",
            border_style="red"
        ))
        raise typer.Exit(1)

    if not endpoint:
        console.print(Panel(
            "[red]Error: Endpoint URL is required[/red]\n\n"
            "To get your endpoint:\n"
            "1. Go to Azure Portal (portal.azure.com)\n"
            "2. Navigate to your Azure OpenAI resource\n"
            "3. Go to 'Keys and Endpoint' section\n"
            "4. Copy the endpoint URL\n\n"
            "Format: https://your-resource.openai.azure.com/\n"
            "Or set the AZURE_OPENAI_ENDPOINT environment variable.",
            title="❌ Missing Endpoint",
            border_style="red"
        ))
        raise typer.Exit(1)

    # Validate deployment names
    if not deployment_name:
        console.print(Panel(
            "[red]Error: Deployment name is required[/red]\n\n"
            "To get your deployment name:\n"
            "1. Go to Azure OpenAI Studio (oai.azure.com)\n"
            "2. Navigate to 'Deployments' section\n"
            "3. Copy the deployment name (not the model name)\n\n"
            "Example: 'gpt-4' or 'my-gpt4-deployment'",
            title="❌ Missing Deployment Name",
            border_style="red"
        ))
        raise typer.Exit(1)

    if not embedding_deployment:
        console.print(Panel(
            "[red]Error: Embedding deployment name is required[/red]\n\n"
            "To get your embedding deployment name:\n"
            "1. Go to Azure OpenAI Studio (oai.azure.com)\n"
            "2. Navigate to 'Deployments' section\n"
            "3. Find your text-embedding-ada-002 deployment\n"
            "4. Copy the deployment name\n\n"
            "Example: 'text-embedding-ada-002' or 'my-embedding-deployment'",
            title="❌ Missing Embedding Deployment",
            border_style="red"
        ))
        raise typer.Exit(1)

    # Create new Azure OpenAI configuration with validation
    try:
        azure_config = AzureOpenAIConfig(
            api_key=api_key,
            endpoint=endpoint,
            api_version=api_version or current_config.azure_openai.api_version,
            deployment_name=deployment_name,
            embedding_deployment=embedding_deployment,
            max_tokens=current_config.azure_openai.max_tokens,
            temperature=current_config.azure_openai.temperature,
            timeout=current_config.azure_openai.timeout,
            max_retries=current_config.azure_openai.max_retries,
            batch_size=current_config.azure_openai.batch_size,
        )
    except ValidationError as e:
        console.print(Panel(
            f"[red]Configuration validation failed:[/red]\n\n{e}",
            title="❌ Validation Error",
            border_style="red"
        ))
        raise typer.Exit(1)

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
        if interactive and Confirm.ask("Do you want to test the connection now?"):
            test_azure_connection()
        else:
            console.print("\n[yellow]Run 'dev-agent azure test' to verify your configuration.[/yellow]")

    except Exception as e:
        console.print(Panel(
            f"[red]Error saving configuration:[/red]\n\n{e}\n\n"
            "Please check file permissions and try again.",
            title="❌ Save Failed",
            border_style="red"
        ))
        raise typer.Exit(1)


def _run_async_test(coro):
    """Helper to run async code in CLI context."""
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No event loop running
        return asyncio.run(coro)
    else:
        # Event loop is running (e.g., in tests)
        import nest_asyncio
        nest_asyncio.apply()
        return asyncio.run(coro)


@app.command("test")
def test_azure_connection(
    insecure: bool = typer.Option(
        False,
        "--insecure",
        help="Disable SSL certificate verification (INSECURE - for testing only)"
    ),
) -> None:
    """Test Azure OpenAI connection with comprehensive validation.
    
    This command tests both completion and embedding endpoints to ensure
    your Azure OpenAI configuration is working correctly. It validates:
    - API authentication
    - Deployment accessibility
    - Model availability
    - Network connectivity
    
    Examples:
        dev-agent azure test
        dev-agent azure test --insecure  # Disable SSL verification (not recommended)
    """
    console.print("\n[bold blue]Testing Azure OpenAI Connection[/bold blue]")
    console.print("This will test both completion and embedding endpoints.\n")
    
    # Show warning if SSL verification is disabled
    if insecure:
        console.print(Panel(
            "[yellow]⚠️  SSL CERTIFICATE VERIFICATION DISABLED[/yellow]\n\n"
            "You are running in insecure mode. This means:\n"
            "• SSL certificates will NOT be verified\n"
            "• Your connection is vulnerable to man-in-the-middle attacks\n"
            "• This should ONLY be used for testing/development\n"
            "• NEVER use this in production\n\n"
            "To fix SSL certificate issues properly, see:\n"
            "  [cyan]FIX_SSL_CERTIFICATE_ERROR.md[/cyan]",
            title="⚠️  Security Warning",
            border_style="yellow"
        ))
        console.print()

    config_manager = ConfigManager()
    config = config_manager.get_config()
    
    # Override SSL verification if --insecure flag is used
    if insecure and config.azure_openai:
        config.azure_openai.verify_ssl = False

    # Validate configuration exists
    if not config.azure_openai.api_key or not config.azure_openai.endpoint:
        console.print(Panel(
            "[red]Azure OpenAI is not configured.[/red]\n\n"
            "Please run the configuration wizard first:\n"
            "  [cyan]dev-agent azure configure[/cyan]\n\n"
            "Or set environment variables:\n"
            "  [cyan]AZURE_OPENAI_API_KEY[/cyan]\n"
            "  [cyan]AZURE_OPENAI_ENDPOINT[/cyan]\n"
            "  [cyan]AZURE_OPENAI_DEPLOYMENT_NAME[/cyan]\n"
            "  [cyan]AZURE_OPENAI_EMBEDDING_DEPLOYMENT[/cyan]",
            title="❌ Configuration Missing",
            border_style="red"
        ))
        raise typer.Exit(1)

    # Display configuration being tested
    console.print("[yellow]Testing configuration:[/yellow]")
    table = Table(show_header=False)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Endpoint", config.azure_openai.endpoint)
    table.add_row("API Version", config.azure_openai.api_version)
    table.add_row("Deployment", config.azure_openai.deployment_name)
    table.add_row("Embedding Deployment", config.azure_openai.embedding_deployment)
    console.print(table)
    console.print()

    test_results = {
        "completion": False,
        "embedding": False,
        "deployment_valid": False,
        "embedding_deployment_valid": False,
    }

    try:
        # Test 1: Chat Completion
        console.print("[bold]1. Testing Chat Completion[/bold]")
        with console.status("[bold green]Calling completion API..."):
            try:
                llm_client = AzureOpenAIClient(config.azure_openai)
                
                # Use helper to run async test
                response = _run_async_test(llm_client.generate_completion(
                    prompt="Say 'test successful' if you can read this.",
                    system_prompt="You are a helpful assistant.",
                    max_tokens=10,
                ))
                
                if response and len(response) > 0:
                    console.print("[green]✓ Chat completion test successful[/green]")
                    console.print(f"  Response: {response[:50]}...")
                    test_results["completion"] = True
                    test_results["deployment_valid"] = True
                else:
                    console.print("[red]✗ Chat completion returned empty response[/red]")
                    
            except LLMAuthenticationError as e:
                console.print(Panel(
                    "[red]Authentication failed[/red]\n\n"
                    "Possible causes:\n"
                    "• Invalid API key\n"
                    "• API key has been rotated or revoked\n"
                    "• Incorrect endpoint URL\n\n"
                    "Resolution:\n"
                    "1. Verify your API key in Azure Portal\n"
                    "2. Check 'Keys and Endpoint' section\n"
                    "3. Run: [cyan]dev-agent azure configure[/cyan]",
                    title="❌ Authentication Error",
                    border_style="red"
                ))
            except LLMBadRequestError as e:
                console.print(Panel(
                    "[red]Invalid deployment configuration[/red]\n\n"
                    "Possible causes:\n"
                    "• Deployment name doesn't exist\n"
                    "• Deployment is not ready\n"
                    "• Model not deployed in your region\n\n"
                    "Resolution:\n"
                    "1. Go to Azure OpenAI Studio (oai.azure.com)\n"
                    "2. Check 'Deployments' section\n"
                    "3. Verify deployment name matches exactly\n"
                    "4. Ensure deployment status is 'Succeeded'\n"
                    f"5. Current deployment: [cyan]{config.azure_openai.deployment_name}[/cyan]",
                    title="❌ Deployment Error",
                    border_style="red"
                ))
            except LLMAPIError as e:
                console.print(Panel(
                    f"[red]API error occurred[/red]\n\n"
                    f"Error: {e}\n\n"
                    "Possible causes:\n"
                    "• Azure OpenAI service is down\n"
                    "• Network connectivity issues\n"
                    "• Rate limiting\n\n"
                    "Resolution:\n"
                    "1. Check Azure Service Health\n"
                    "2. Verify network connectivity\n"
                    "3. Wait a moment and try again",
                    title="❌ API Error",
                    border_style="red"
                ))
            except Exception as e:
                console.print(f"[red]✗ Chat completion test failed: {e}[/red]")

        console.print()

        # Test 2: Embeddings
        console.print("[bold]2. Testing Embeddings[/bold]")
        with console.status("[bold green]Calling embeddings API..."):
            try:
                embedding_client = AzureEmbeddingClient(config.azure_openai)
                
                # Use helper to run async test
                embeddings = _run_async_test(embedding_client.embed_batch(
                    texts=["test embedding"],
                ))
                
                if embeddings and len(embeddings) > 0 and len(embeddings[0]) > 0:
                    dimension = len(embeddings[0])
                    console.print(f"[green]✓ Embeddings test successful[/green]")
                    console.print(f"  Dimension: {dimension}")
                    console.print(f"  Expected: 1536 (text-embedding-ada-002)")
                    
                    if dimension == 1536:
                        console.print("  [green]✓ Dimension matches expected value[/green]")
                    else:
                        console.print(f"  [yellow]⚠ Unexpected dimension (got {dimension}, expected 1536)[/yellow]")
                    
                    test_results["embedding"] = True
                    test_results["embedding_deployment_valid"] = True
                else:
                    console.print("[red]✗ Embeddings test failed - no embeddings returned[/red]")
                    
            except LLMAuthenticationError as e:
                console.print(Panel(
                    "[red]Authentication failed[/red]\n\n"
                    "Same authentication issue as completion test.\n"
                    "Please fix the API key configuration.",
                    title="❌ Authentication Error",
                    border_style="red"
                ))
            except LLMBadRequestError as e:
                console.print(Panel(
                    "[red]Invalid embedding deployment configuration[/red]\n\n"
                    "Possible causes:\n"
                    "• Embedding deployment name doesn't exist\n"
                    "• Embedding deployment is not ready\n"
                    "• Wrong model type deployed\n\n"
                    "Resolution:\n"
                    "1. Go to Azure OpenAI Studio (oai.azure.com)\n"
                    "2. Check 'Deployments' section\n"
                    "3. Verify embedding deployment exists\n"
                    "4. Ensure it's text-embedding-ada-002 or compatible\n"
                    f"5. Current deployment: [cyan]{config.azure_openai.embedding_deployment}[/cyan]",
                    title="❌ Embedding Deployment Error",
                    border_style="red"
                ))
            except Exception as e:
                console.print(f"[red]✗ Embeddings test failed: {e}[/red]")

        console.print()

        # Summary
        console.print("[bold]Test Summary[/bold]")
        summary_table = Table()
        summary_table.add_column("Test", style="cyan")
        summary_table.add_column("Status", style="white")
        
        summary_table.add_row(
            "Chat Completion",
            "[green]✓ Passed[/green]" if test_results["completion"] else "[red]✗ Failed[/red]"
        )
        summary_table.add_row(
            "Embeddings",
            "[green]✓ Passed[/green]" if test_results["embedding"] else "[red]✗ Failed[/red]"
        )
        summary_table.add_row(
            "Deployment Valid",
            "[green]✓ Yes[/green]" if test_results["deployment_valid"] else "[red]✗ No[/red]"
        )
        summary_table.add_row(
            "Embedding Deployment Valid",
            "[green]✓ Yes[/green]" if test_results["embedding_deployment_valid"] else "[red]✗ No[/red]"
        )
        
        console.print(summary_table)
        console.print()

        # Overall result
        if all(test_results.values()):
            console.print(Panel(
                "[green]All tests passed successfully![/green]\n\n"
                "Your Azure OpenAI configuration is working correctly.\n"
                "You can now use dev-agent with Azure OpenAI.",
                title="✅ Success",
                border_style="green"
            ))
        else:
            console.print(Panel(
                "[yellow]Some tests failed.[/yellow]\n\n"
                "Please review the error messages above and:\n"
                "1. Verify your configuration in Azure Portal\n"
                "2. Check deployment names and status\n"
                "3. Run: [cyan]dev-agent azure configure[/cyan] to update settings\n"
                "4. Check: [cyan]dev-agent azure status[/cyan] for current config",
                title="⚠️  Partial Failure",
                border_style="yellow"
            ))
            raise typer.Exit(1)

    except ConfigurationError as e:
        console.print(Panel(
            f"[red]Configuration error:[/red]\n\n{e}",
            title="❌ Configuration Error",
            border_style="red"
        ))
        raise typer.Exit(1)
    except Exception as e:
        console.print(Panel(
            f"[red]Unexpected error:[/red]\n\n{e}\n\n"
            "Please check your network connection and Azure service status.",
            title="❌ Error",
            border_style="red"
        ))
        raise typer.Exit(1)


@app.command("status")
def show_azure_status() -> None:
    """Show Azure OpenAI configuration status with validation."""
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
    deployment_status = "✓ Set" if config.azure_openai.deployment_name else "✗ Not set"
    embedding_status = "✓ Set" if config.azure_openai.embedding_deployment else "✗ Not set"

    table.add_row(
        "API Key", "***" if config.azure_openai.api_key else "Not set", api_key_status
    )
    table.add_row(
        "Endpoint", config.azure_openai.endpoint or "Not set", endpoint_status
    )
    table.add_row("API Version", config.azure_openai.api_version, "✓ Set")
    table.add_row("Deployment Name", config.azure_openai.deployment_name or "Not set", deployment_status)
    table.add_row("Embedding Deployment", config.azure_openai.embedding_deployment or "Not set", embedding_status)
    table.add_row("Max Tokens", str(config.azure_openai.max_tokens), "✓ Set")
    table.add_row("Temperature", str(config.azure_openai.temperature), "✓ Set")
    table.add_row("Max Retries", str(config.azure_openai.max_retries), "✓ Set")
    table.add_row("Timeout", f"{config.azure_openai.timeout}s", "✓ Set")
    table.add_row("Batch Size", str(config.azure_openai.batch_size), "✓ Set")
    table.add_row(
        "Use Azure Embeddings",
        str(config.indexing.use_azure_embeddings),
        "✓ Enabled" if config.indexing.use_azure_embeddings else "✗ Disabled",
    )

    console.print(table)

    # Overall status
    all_configured = (
        config.azure_openai.api_key 
        and config.azure_openai.endpoint
        and config.azure_openai.deployment_name
        and config.azure_openai.embedding_deployment
    )
    
    if all_configured:
        console.print(Panel(
            "[green]Azure OpenAI is fully configured and ready to use![/green]\n\n"
            "Next steps:\n"
            "• Run [cyan]dev-agent azure test[/cyan] to verify connection\n"
            "• Run [cyan]dev-agent init[/cyan] to start a new project\n"
            "• Run [cyan]dev-agent resume[/cyan] to continue existing project",
            title="✅ Ready",
            border_style="green"
        ))
    else:
        missing = []
        if not config.azure_openai.api_key:
            missing.append("API Key")
        if not config.azure_openai.endpoint:
            missing.append("Endpoint")
        if not config.azure_openai.deployment_name:
            missing.append("Deployment Name")
        if not config.azure_openai.embedding_deployment:
            missing.append("Embedding Deployment")
        
        console.print(Panel(
            f"[yellow]Azure OpenAI is not fully configured[/yellow]\n\n"
            f"Missing: {', '.join(missing)}\n\n"
            "Run [cyan]dev-agent azure configure[/cyan] to complete setup",
            title="⚠️  Incomplete Configuration",
            border_style="yellow"
        ))


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
            "AZURE_OPENAI_DEPLOYMENT_NAME",
            "GPT-4 deployment name (optional)",
            os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        ),
        (
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
            "Embedding deployment name (optional)",
            os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
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


@app.command("export")
def export_config(
    output_file: Path = typer.Option(
        Path("azure_openai_config.json"),
        "--output",
        "-o",
        help="Output file path",
    ),
    include_secrets: bool = typer.Option(
        False,
        "--include-secrets",
        help="Include API key in export (NOT RECOMMENDED)",
    ),
) -> None:
    """Export Azure OpenAI configuration to a file.
    
    This command exports your Azure OpenAI configuration to a JSON file.
    By default, API keys are NOT included for security reasons.
    
    Examples:
        # Export without API key (recommended)
        dev-agent azure export
        
        # Export to specific file
        dev-agent azure export --output my-config.json
        
        # Export with API key (use with caution)
        dev-agent azure export --include-secrets
    """
    console.print("\n[bold blue]Export Azure OpenAI Configuration[/bold blue]")
    
    config_manager = ConfigManager()
    config = config_manager.get_config()
    
    # Prepare export data
    export_data = {
        "endpoint": config.azure_openai.endpoint,
        "api_version": config.azure_openai.api_version,
        "deployment_name": config.azure_openai.deployment_name,
        "embedding_deployment": config.azure_openai.embedding_deployment,
        "max_tokens": config.azure_openai.max_tokens,
        "temperature": config.azure_openai.temperature,
        "max_retries": config.azure_openai.max_retries,
        "timeout": config.azure_openai.timeout,
        "batch_size": config.azure_openai.batch_size,
    }
    
    if include_secrets:
        console.print(Panel(
            "[yellow]⚠️  WARNING: Including API key in export[/yellow]\n\n"
            "This file will contain your API key in plain text.\n"
            "• Do NOT commit this file to version control\n"
            "• Do NOT share this file publicly\n"
            "• Store it securely\n"
            "• Delete it after use",
            title="Security Warning",
            border_style="yellow"
        ))
        export_data["api_key"] = config.azure_openai.api_key.get_secret_value()
    else:
        export_data["api_key"] = "*** REDACTED - Set via environment variable or configure command ***"
    
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(json.dumps(export_data, indent=2))
        
        console.print(f"\n[green]✓ Configuration exported to: {output_file}[/green]")
        
        if not include_secrets:
            console.print("\n[yellow]Note: API key was not included in the export.[/yellow]")
            console.print("Set it via environment variable or use --include-secrets flag.")
            
    except Exception as e:
        console.print(Panel(
            f"[red]Export failed:[/red]\n\n{e}",
            title="❌ Error",
            border_style="red"
        ))
        raise typer.Exit(1)


@app.command("import")
def import_config(
    input_file: Path = typer.Argument(
        ...,
        help="Input file path",
    ),
    merge: bool = typer.Option(
        False,
        "--merge",
        help="Merge with existing configuration",
    ),
) -> None:
    """Import Azure OpenAI configuration from a file.
    
    This command imports Azure OpenAI configuration from a JSON file.
    You can either replace the entire configuration or merge with existing settings.
    
    Examples:
        # Import and replace configuration
        dev-agent azure import azure_openai_config.json
        
        # Import and merge with existing
        dev-agent azure import azure_openai_config.json --merge
    """
    console.print("\n[bold blue]Import Azure OpenAI Configuration[/bold blue]")
    
    if not input_file.exists():
        console.print(Panel(
            f"[red]File not found:[/red] {input_file}\n\n"
            "Please check the file path and try again.",
            title="❌ File Not Found",
            border_style="red"
        ))
        raise typer.Exit(1)
    
    try:
        # Load import data
        import_data = json.loads(input_file.read_text())
        
        # Display what will be imported
        console.print("\n[yellow]Configuration to import:[/yellow]")
        table = Table(show_header=False)
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="white")
        
        for key, value in import_data.items():
            if key == "api_key" and "REDACTED" not in str(value):
                display_value = "***"
            else:
                display_value = str(value)
            table.add_row(key, display_value)
        
        console.print(table)
        console.print()
        
        if not Confirm.ask("Do you want to import this configuration?"):
            console.print("Import cancelled.")
            return
        
        config_manager = ConfigManager()
        current_config = config_manager.get_config()
        
        # Prepare configuration data
        if merge:
            # Merge with existing
            config_data = {
                "endpoint": import_data.get("endpoint", current_config.azure_openai.endpoint),
                "api_version": import_data.get("api_version", current_config.azure_openai.api_version),
                "deployment_name": import_data.get("deployment_name", current_config.azure_openai.deployment_name),
                "embedding_deployment": import_data.get("embedding_deployment", current_config.azure_openai.embedding_deployment),
                "max_tokens": import_data.get("max_tokens", current_config.azure_openai.max_tokens),
                "temperature": import_data.get("temperature", current_config.azure_openai.temperature),
                "max_retries": import_data.get("max_retries", current_config.azure_openai.max_retries),
                "timeout": import_data.get("timeout", current_config.azure_openai.timeout),
                "batch_size": import_data.get("batch_size", current_config.azure_openai.batch_size),
            }
        else:
            # Replace entirely
            config_data = import_data.copy()
        
        # Handle API key
        api_key = config_data.get("api_key", "")
        if not api_key or "REDACTED" in api_key:
            # API key not in file, keep existing or prompt
            if current_config.azure_openai.api_key:
                api_key = current_config.azure_openai.api_key.get_secret_value()
            else:
                console.print("\n[yellow]API key not found in import file.[/yellow]")
                api_key = _prompt_for_api_key(None)
        
        config_data["api_key"] = api_key
        
        # Validate and create configuration
        try:
            azure_config = AzureOpenAIConfig(**config_data)
        except ValidationError as e:
            console.print(Panel(
                f"[red]Configuration validation failed:[/red]\n\n{e}",
                title="❌ Validation Error",
                border_style="red"
            ))
            raise typer.Exit(1)
        
        # Update and save
        current_config.azure_openai = azure_config
        current_config.indexing.use_azure_embeddings = True
        
        config_manager.save_config(current_config)
        
        console.print(Panel(
            "[green]Configuration imported successfully![/green]\n\n"
            "Run [cyan]dev-agent azure test[/cyan] to verify the configuration.",
            title="✅ Success",
            border_style="green"
        ))
        
    except json.JSONDecodeError as e:
        console.print(Panel(
            f"[red]Invalid JSON file:[/red]\n\n{e}\n\n"
            "Please check the file format and try again.",
            title="❌ Parse Error",
            border_style="red"
        ))
        raise typer.Exit(1)
    except Exception as e:
        console.print(Panel(
            f"[red]Import failed:[/red]\n\n{e}",
            title="❌ Error",
            border_style="red"
        ))
        raise typer.Exit(1)


def _display_current_config(config: AzureOpenAIConfig) -> None:
    """Display current Azure OpenAI configuration."""
    table = Table()
    table.add_column("Setting", style="cyan")
    table.add_column("Current Value", style="white")

    table.add_row("API Key", "***" if config.api_key else "Not set")
    table.add_row("Endpoint", config.endpoint or "Not set")
    table.add_row("API Version", config.api_version)
    table.add_row("Deployment Name", config.deployment_name)
    table.add_row("Embedding Deployment", config.embedding_deployment)
    table.add_row("Max Tokens", str(config.max_tokens))
    table.add_row("Temperature", str(config.temperature))

    console.print(table)


def _prompt_for_api_key(current: str | None) -> str:
    """Prompt for API key with validation."""
    if current:
        if Confirm.ask("Keep current API key (***)?"):
            return current

    console.print("\n[yellow]Enter your Azure OpenAI API key:[/yellow]")
    console.print("Find it in: Azure Portal → Your Resource → Keys and Endpoint")
    
    while True:
        api_key = Prompt.ask("API Key", password=True)
        if api_key.strip():
            # Basic validation - Azure OpenAI keys are typically 32 characters
            if len(api_key.strip()) < 20:
                console.print("[red]API key seems too short. Please verify and try again.[/red]")
                if not Confirm.ask("Use this key anyway?"):
                    continue
            return api_key.strip()
        console.print("[red]API key cannot be empty[/red]")


def _prompt_for_endpoint(current: str | None) -> str:
    """Prompt for endpoint URL with validation."""
    default = current or "https://your-resource.openai.azure.com/"
    
    console.print("\n[yellow]Enter your Azure OpenAI endpoint URL:[/yellow]")
    console.print("Find it in: Azure Portal → Your Resource → Keys and Endpoint")
    console.print("Format: https://your-resource.openai.azure.com/")

    while True:
        endpoint = Prompt.ask("Endpoint URL", default=default)
        if endpoint.strip():
            endpoint = endpoint.strip()
            if not endpoint.startswith(("http://", "https://")):
                console.print("[red]Endpoint must start with http:// or https://[/red]")
                continue
            if not endpoint.endswith(".openai.azure.com/") and not endpoint.endswith(".openai.azure.com"):
                console.print("[yellow]Warning: Endpoint doesn't look like a standard Azure OpenAI URL[/yellow]")
                if not Confirm.ask("Use this endpoint anyway?"):
                    continue
            return endpoint
        console.print("[red]Endpoint cannot be empty[/red]")


def _prompt_for_api_version(current: str) -> str:
    """Prompt for API version."""
    console.print("\n[yellow]Enter API version:[/yellow]")
    console.print("Recommended: 2024-02-15-preview (default)")
    return Prompt.ask("API Version", default=current)


def _prompt_for_deployment_name(current: str) -> str:
    """Prompt for GPT-4 deployment name with validation."""
    console.print("\n[yellow]Enter your GPT-4 deployment name:[/yellow]")
    console.print("Find it in: Azure OpenAI Studio → Deployments")
    console.print("Note: Use the deployment name, not the model name")
    console.print("Example: 'gpt-4' or 'my-gpt4-deployment'")
    
    while True:
        deployment = Prompt.ask("Deployment Name", default=current)
        if deployment.strip():
            return deployment.strip()
        console.print("[red]Deployment name cannot be empty[/red]")


def _prompt_for_embedding_deployment(current: str) -> str:
    """Prompt for embedding deployment name with validation."""
    console.print("\n[yellow]Enter your embedding deployment name:[/yellow]")
    console.print("Find it in: Azure OpenAI Studio → Deployments")
    console.print("Note: Should be text-embedding-ada-002 or compatible")
    console.print("Example: 'text-embedding-ada-002' or 'my-embedding-deployment'")
    
    while True:
        deployment = Prompt.ask("Embedding Deployment", default=current)
        if deployment.strip():
            return deployment.strip()
        console.print("[red]Embedding deployment name cannot be empty[/red]")
