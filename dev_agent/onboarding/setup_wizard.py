"""Interactive setup wizard for first-time users."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from pydantic import SecretStr, ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from dev_agent.config.config_manager import ConfigManager
from dev_agent.llm.azure_client import AzureOpenAIClient
from dev_agent.llm.embeddings import AzureEmbeddingClient
from dev_agent.models.llm_config import AzureOpenAIConfig
from dev_agent.onboarding.models import (
    OnboardingStep,
    SetupResult,
    UserPreferences,
)

logger = logging.getLogger(__name__)


class SetupWizard:
    """Interactive setup wizard for first-time users.

    Guides users through initial configuration including Azure OpenAI setup,
    workflow explanation, and preference configuration.

    Attributes:
        console: Rich console for formatted output
        config_path: Path to user configuration file
        preferences: User preferences being configured
        steps: List of onboarding steps to execute
    """

    def __init__(
        self,
        config_path: Path | None = None,
        console: Console | None = None,
    ) -> None:
        """Initialize setup wizard.

        Args:
            config_path: Path to configuration file (defaults to ~/.dev_agent_config)
            console: Rich console instance (creates new if None)
        """
        self.console = console or Console()
        self.config_path = config_path or Path.home() / ".dev_agent_config"
        self.preferences = UserPreferences()
        self.steps: list[OnboardingStep] = []

    def run(self) -> SetupResult:
        """Run the complete setup wizard.

        Executes all onboarding steps in sequence, handling user input
        and errors gracefully.

        Returns:
            SetupResult with configuration status and any errors
        """
        result = SetupResult()

        try:
            # Display welcome message
            self._show_welcome()

            # Check if this is first run
            if self._is_first_run():
                self.console.print(
                    "\n[cyan]This appears to be your first time using dev-agent![/cyan]"
                )
                self.console.print(
                    "Let's get you set up with a quick configuration wizard.\n"
                )
            else:
                self.console.print("\n[yellow]Reconfiguring dev-agent...[/yellow]\n")

            # Build onboarding steps
            self._build_onboarding_steps()

            # Execute each step
            for step in self.steps:
                if not self._execute_step(step, result) and not step.skippable:
                    # Step failed and is not skippable
                    result.ready_to_use = False
                    return result

            # Save preferences
            if self._save_preferences():
                result.preferences_saved = True
                self.console.print(
                    "\n[green]✓[/green] Configuration saved successfully!"
                )
            else:
                result.errors.append("Failed to save preferences")
                result.ready_to_use = False
                return result

            # Determine if system is ready to use
            result.ready_to_use = result.azure_configured

            # Show completion message
            self._show_completion(result)

        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]Setup cancelled by user.[/yellow]")
            result.ready_to_use = False
        except Exception as e:
            logger.exception("Setup wizard failed")
            result.errors.append(f"Unexpected error: {e}")
            result.ready_to_use = False
            self.console.print(f"\n[red]Setup failed: {e}[/red]")

        return result

    def _show_welcome(self) -> None:
        """Display welcome message and introduction."""
        welcome_text = """
[bold cyan]Welcome to dev-agent![/bold cyan]

dev-agent is an AI-powered development workflow assistant that helps you:
  • Analyze and understand large codebases
  • Generate specifications and design documents
  • Create implementation plans and code
  • Maintain consistency with existing patterns

This wizard will help you configure dev-agent for first use.
        """

        self.console.print(Panel(welcome_text.strip(), border_style="cyan"))

    def _is_first_run(self) -> bool:
        """Check if this is the first run.

        Returns:
            True if configuration file doesn't exist
        """
        return not self.config_path.exists()

    def configure_azure_openai(self) -> bool:  # noqa: PLR0911
        """Configure Azure OpenAI with interactive prompts.

        Prompts user for Azure OpenAI credentials and configuration,
        validates inputs, and saves to configuration.

        Returns:
            True if configuration was successful, False otherwise
        """
        try:
            self.console.print("\n[bold cyan]Azure OpenAI Configuration[/bold cyan]")
            self.console.print(
                "Configure your Azure OpenAI credentials to enable AI-powered features.\n"
            )

            # Display security notice
            self.console.print(
                Panel(
                    "[yellow]Security Notice:[/yellow]\n"
                    "• API keys will be stored securely in your configuration\n"
                    "• Never commit API keys to version control\n"
                    "• Consider using environment variables for production\n"
                    "• Use Azure Key Vault for sensitive deployments",
                    title="🔒 Security",
                    border_style="yellow",
                )
            )
            self.console.print()

            # Load existing config if available
            config_manager = ConfigManager()
            current_config = config_manager.get_config()
            current_azure = current_config.azure_openai

            # Prompt for endpoint
            endpoint = Prompt.ask(
                "[cyan]Azure OpenAI Endpoint URL[/cyan]",
                default=current_azure.endpoint if current_azure else "",
            ).strip()

            if not endpoint:
                self.console.print("[red]Endpoint is required[/red]")
                return False

            # Validate endpoint format
            if not endpoint.startswith("https://"):
                self.console.print(
                    "[yellow]Warning: Endpoint should start with https://[/yellow]"
                )
                if not Confirm.ask("Continue anyway?", default=False):
                    return False

            # Prompt for API key
            api_key = Prompt.ask(
                "[cyan]Azure OpenAI API Key[/cyan]",
                password=True,
            ).strip()

            if not api_key:
                self.console.print("[red]API key is required[/red]")
                return False

            # Prompt for API version
            api_version = Prompt.ask(
                "[cyan]API Version[/cyan]",
                default=current_azure.api_version
                if current_azure
                else "2024-02-15-preview",
            ).strip()

            # Prompt for deployment name
            deployment_name = Prompt.ask(
                "[cyan]GPT-4 Deployment Name[/cyan]",
                default=current_azure.deployment_name if current_azure else "",
            ).strip()

            if not deployment_name:
                self.console.print("[red]Deployment name is required[/red]")
                return False

            # Prompt for embedding deployment
            embedding_deployment = Prompt.ask(
                "[cyan]Embedding Deployment Name[/cyan]",
                default=current_azure.embedding_deployment if current_azure else "",
            ).strip()

            if not embedding_deployment:
                self.console.print("[red]Embedding deployment name is required[/red]")
                return False

            # Create and validate configuration
            try:
                azure_config = AzureOpenAIConfig(
                    api_key=SecretStr(api_key),
                    endpoint=endpoint,
                    api_version=api_version,
                    deployment_name=deployment_name,
                    embedding_deployment=embedding_deployment,
                    max_tokens=current_azure.max_tokens if current_azure else 4000,
                    temperature=current_azure.temperature if current_azure else 0.7,
                    timeout=current_azure.timeout if current_azure else 60,
                    max_retries=current_azure.max_retries if current_azure else 3,
                    batch_size=current_azure.batch_size if current_azure else 16,
                )
            except ValidationError as e:
                self.console.print(f"[red]Configuration validation failed: {e}[/red]")
                return False

            # Update and save configuration
            current_config.azure_openai = azure_config
            current_config.indexing.use_azure_embeddings = True

            try:
                config_manager.save_config(current_config)
                self.console.print("[green]✓ Azure OpenAI configuration saved[/green]")
                self.preferences.azure_configured = True
                return True
            except Exception as e:
                self.console.print(f"[red]Failed to save configuration: {e}[/red]")
                return False

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Configuration cancelled[/yellow]")
            return False
        except Exception as e:
            logger.exception("Azure OpenAI configuration failed")
            self.console.print(f"[red]Configuration failed: {e}[/red]")
            return False

    def test_azure_connection(self) -> bool:
        """Test Azure OpenAI connection.

        Makes test API calls to both completion and embedding endpoints
        to verify configuration is working correctly.

        Returns:
            True if both tests pass, False otherwise
        """
        try:
            self.console.print(
                "\n[bold cyan]Testing Azure OpenAI Connection[/bold cyan]"
            )
            self.console.print("Verifying completion and embedding endpoints...\n")

            config_manager = ConfigManager()
            config = config_manager.get_config()
            azure_config = config.azure_openai

            # Check if configuration exists
            if (
                not azure_config
                or not azure_config.api_key
                or not azure_config.endpoint
            ):
                self.console.print(
                    "[red]Azure OpenAI is not configured. Please configure it first.[/red]"
                )
                return False

            test_results = {"completion": False, "embedding": False}

            # Test 1: Chat Completion
            self.console.print("[bold]1. Testing Chat Completion...[/bold]")
            try:
                llm_client = AzureOpenAIClient(azure_config)

                # Run async test
                async def test_completion() -> str:
                    return await llm_client.generate_completion(
                        prompt="Say 'test successful' if you can read this.",
                        system_prompt="You are a helpful assistant.",
                        max_tokens=10,
                    )

                response = asyncio.run(test_completion())

                if response and len(response) > 0:
                    self.console.print("[green]✓ Chat completion test passed[/green]")
                    test_results["completion"] = True
                else:
                    self.console.print(
                        "[red]✗ Chat completion returned empty response[/red]"
                    )

            except Exception as e:
                self.console.print(f"[red]✗ Chat completion test failed: {e}[/red]")
                logger.exception("Chat completion test failed")

            # Test 2: Embeddings
            self.console.print("\n[bold]2. Testing Embeddings...[/bold]")
            try:
                embedding_client = AzureEmbeddingClient(azure_config)

                # Run async test
                async def test_embeddings() -> list[list[float]]:
                    return await embedding_client.embed_batch(texts=["test embedding"])

                embeddings = asyncio.run(test_embeddings())

                if embeddings and len(embeddings) > 0 and len(embeddings[0]) > 0:
                    dimension = len(embeddings[0])
                    self.console.print("[green]✓ Embeddings test passed[/green]")
                    self.console.print(f"  Dimension: {dimension}")
                    test_results["embedding"] = True
                else:
                    self.console.print("[red]✗ Embeddings test failed[/red]")

            except Exception as e:
                self.console.print(f"[red]✗ Embeddings test failed: {e}[/red]")
                logger.exception("Embeddings test failed")

            # Summary
            self.console.print()
            if all(test_results.values()):
                self.console.print(
                    Panel(
                        "[green]All tests passed![/green]\n\n"
                        "Your Azure OpenAI configuration is working correctly.",
                        title="✅ Success",
                        border_style="green",
                    )
                )
                return True
            else:
                self.console.print(
                    Panel(
                        "[yellow]Some tests failed.[/yellow]\n\n"
                        "Please verify your configuration and try again.",
                        title="⚠️  Partial Failure",
                        border_style="yellow",
                    )
                )
                return False

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Testing cancelled[/yellow]")
            return False
        except Exception as e:
            logger.exception("Connection testing failed")
            self.console.print(f"[red]Testing failed: {e}[/red]")
            return False

    def explain_workflow(self) -> bool:
        """Explain the four-phase workflow.

        Describes the dev-agent workflow phases, estimated times,
        and cost implications to help users understand what to expect.

        Returns:
            True (always succeeds as it's informational)
        """
        try:
            self.console.print("\n[bold cyan]dev-agent Workflow Overview[/bold cyan]")
            self.console.print(
                "dev-agent uses a structured four-phase workflow to help you develop features:\n"
            )

            workflow_text = """
[bold]Phase 1: Indexing[/bold]
• Analyzes your codebase using Tree-sitter
• Generates semantic embeddings with Azure OpenAI
• Stores code patterns in vector database
• [dim]Estimated time: 1-5 minutes for typical projects[/dim]
• [dim]Cost: ~$0.01-0.10 depending on codebase size[/dim]

[bold]Phase 2: Specification[/bold]
• Generates detailed feature specifications
• Uses GPT-4 with context from your codebase
• Creates structured requirements documents
• [dim]Estimated time: 2-5 minutes[/dim]
• [dim]Cost: ~$0.05-0.20 per specification[/dim]

[bold]Phase 3: Design[/bold]
• Creates technical design documents
• Ensures consistency with existing architecture
• References patterns from your codebase
• [dim]Estimated time: 2-5 minutes[/dim]
• [dim]Cost: ~$0.05-0.20 per design[/dim]

[bold]Phase 4: Implementation[/bold]
• Generates implementation tasks
• Creates code matching your style
• Maintains consistency with existing patterns
• [dim]Estimated time: 5-15 minutes[/dim]
• [dim]Cost: ~$0.10-0.50 per implementation[/dim]

[bold cyan]Total Estimated Cost:[/bold cyan]
• Small feature: $0.20-0.50
• Medium feature: $0.50-1.50
• Large feature: $1.50-5.00

[yellow]Note:[/yellow] Costs are estimates based on Azure OpenAI pricing.
Actual costs depend on codebase size and feature complexity.
            """

            self.console.print(Panel(workflow_text.strip(), border_style="cyan"))

            self.console.print("\n[bold]Key Benefits:[/bold]")
            self.console.print("  • Context-aware code generation")
            self.console.print("  • Maintains consistency with your codebase")
            self.console.print("  • Structured development process")
            self.console.print("  • Human-in-the-loop approval at each phase")

            self.console.print("\n[dim]Press Enter to continue...[/dim]")
            input()

            return True

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Skipped[/yellow]")
            return True
        except Exception as e:
            logger.exception("Workflow explanation failed")
            self.console.print(f"[red]Error: {e}[/red]")
            return True  # Don't fail setup for informational step

    def offer_sample_project(self) -> bool:
        """Offer sample project or guide user to next steps.

        Provides options for what to do next: create new project,
        analyze existing codebase, or skip for now.

        Returns:
            True (always succeeds as it's informational)
        """
        try:
            self.console.print(
                "\n[bold cyan]What would you like to do next?[/bold cyan]"
            )
            self.console.print()

            options_text = """
[bold]1. Start with a new project[/bold]
   Create a new project from scratch and use dev-agent to build it.
   [dim]Run: dev-agent init /path/to/new/project[/dim]

[bold]2. Analyze an existing codebase[/bold]
   Point dev-agent at an existing project to analyze and document it.
   [dim]Run: dev-agent init /path/to/existing/project[/dim]

[bold]3. Skip for now[/bold]
   Complete setup and explore dev-agent later.
   [dim]Run: dev-agent --help to see all commands[/dim]
            """

            self.console.print(Panel(options_text.strip(), border_style="cyan"))

            choice = Prompt.ask(
                "\n[cyan]Choose an option[/cyan]",
                choices=["1", "2", "3"],
                default="3",
            )

            if choice == "1":
                self.console.print("\n[green]Great! To start a new project:[/green]")
                self.console.print("  1. Create a new directory for your project")
                self.console.print(
                    "  2. Run: [cyan]dev-agent init /path/to/project[/cyan]"
                )
                self.console.print("  3. Follow the prompts to scaffold your project")
                self.console.print(
                    "\n[dim]You can also use templates with: dev-agent scaffold list[/dim]"
                )

            elif choice == "2":
                self.console.print(
                    "\n[green]Great! To analyze an existing codebase:[/green]"
                )
                self.console.print("  1. Navigate to your project directory")
                self.console.print("  2. Run: [cyan]dev-agent init .[/cyan]")
                self.console.print(
                    "  3. dev-agent will index your code and detect patterns"
                )
                self.console.print(
                    "  4. Then you can generate specs, designs, and tasks"
                )
                self.console.print(
                    "\n[dim]The indexing phase may take a few minutes for large codebases[/dim]"
                )

            else:
                self.console.print(
                    "\n[green]No problem! You can start using dev-agent anytime.[/green]"
                )
                self.console.print("\n[bold]Quick reference:[/bold]")
                self.console.print(
                    "  • [cyan]dev-agent --help[/cyan] - Show all commands"
                )
                self.console.print(
                    "  • [cyan]dev-agent init[/cyan] - Initialize a project"
                )
                self.console.print(
                    "  • [cyan]dev-agent[/cyan] - Start interactive mode"
                )
                self.console.print(
                    "  • [cyan]dev-agent azure test[/cyan] - Test your Azure OpenAI connection"
                )

            return True

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Skipped[/yellow]")
            return True
        except Exception as e:
            logger.exception("Project type selection failed")
            self.console.print(f"[red]Error: {e}[/red]")
            return True  # Don't fail setup for informational step

    def _build_onboarding_steps(self) -> None:
        """Build the list of onboarding steps.

        Creates OnboardingStep instances for each configuration step
        in the wizard flow.
        """
        # Build steps for the wizard
        self.steps = [
            OnboardingStep(
                title="Azure OpenAI Configuration",
                description="Configure your Azure OpenAI credentials",
                action=self.configure_azure_openai,
                help_text="You'll need your Azure OpenAI endpoint, API key, and deployment names",
                estimated_time="2-3 minutes",
                skippable=False,
            ),
            OnboardingStep(
                title="Connection Test",
                description="Test your Azure OpenAI connection",
                action=self.test_azure_connection,
                help_text="Verify that your configuration is working correctly",
                estimated_time="30 seconds",
                skippable=True,
            ),
            OnboardingStep(
                title="Workflow Overview",
                description="Learn about the dev-agent workflow",
                action=self.explain_workflow,
                help_text="Understand the four-phase development process",
                estimated_time="2 minutes",
                skippable=True,
            ),
            OnboardingStep(
                title="Next Steps",
                description="Choose what to do next",
                action=self.offer_sample_project,
                help_text="Decide how you want to start using dev-agent",
                estimated_time="1 minute",
                skippable=True,
            ),
        ]

    def _execute_step(
        self,
        step: OnboardingStep,
        result: SetupResult,
    ) -> bool:
        """Execute a single onboarding step.

        Args:
            step: OnboardingStep to execute
            result: SetupResult to update with step outcomes

        Returns:
            True if step succeeded or was skipped, False if failed
        """
        try:
            # Show step header
            self.console.print(f"\n[bold]{step.title}[/bold]")
            self.console.print(f"[dim]{step.description}[/dim]")

            if step.estimated_time:
                self.console.print(f"[dim]Estimated time: {step.estimated_time}[/dim]")

            # Offer to skip if skippable
            if step.skippable and not Confirm.ask(
                "\nWould you like to complete this step?", default=True
            ):
                result.skipped_steps.append(step.title)
                self.console.print("[yellow]Skipped[/yellow]")
                return True

            # Execute step action
            success = step.action()

            if success:
                step.completed = True
                self.console.print("[green]✓ Completed[/green]")
                return True
            else:
                error_msg = f"Step failed: {step.title}"
                result.errors.append(error_msg)
                self.console.print("[red]✗ Failed[/red]")

                if step.skippable and Confirm.ask(
                    "Would you like to skip this step?", default=False
                ):
                    result.skipped_steps.append(step.title)
                    return True

                return False

        except Exception as e:
            logger.exception(f"Error executing step: {step.title}")
            error_msg = f"Error in {step.title}: {e}"
            result.errors.append(error_msg)
            self.console.print(f"[red]✗ Error: {e}[/red]")

            if step.skippable and Confirm.ask(
                "Would you like to skip this step?", default=False
            ):
                result.skipped_steps.append(step.title)
                return True

            return False

    def save_user_preferences(self) -> bool:
        """Save user preferences to ~/.dev_agent_config.

        Saves user preferences including Azure configuration status,
        editor preferences, and other settings. API keys are NOT stored
        here - they are stored in the main config file managed by ConfigManager.

        Returns:
            True if preferences were saved successfully
        """
        return self._save_preferences()

    def _save_preferences(self) -> bool:
        """Save user preferences to configuration file.

        Returns:
            True if preferences were saved successfully
        """
        try:
            # Create parent directory if needed
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert preferences to dict
            prefs_dict = {
                "azure_configured": self.preferences.azure_configured,
                "preferred_editor": self.preferences.preferred_editor,
                "cost_warnings_enabled": self.preferences.cost_warnings_enabled,
                "budget_threshold": self.preferences.budget_threshold,
                "auto_approve_phases": self.preferences.auto_approve_phases,
                "verbose_output": self.preferences.verbose_output,
                "first_run_completed": True,  # Mark first run as complete
            }

            # Save to file
            self.config_path.write_text(json.dumps(prefs_dict, indent=2))

            # Set appropriate permissions (user read/write only)
            self.config_path.chmod(0o600)

            logger.info(f"Saved preferences to {self.config_path}")
            return True

        except Exception as e:
            logger.exception("Failed to save preferences")
            self.console.print(f"[red]Failed to save preferences: {e}[/red]")
            return False

    def _show_completion(self, result: SetupResult) -> None:
        """Show setup completion message.

        Args:
            result: SetupResult with configuration outcomes
        """
        if result.ready_to_use:
            completion_text = """
[bold green]Setup Complete![/bold green]

dev-agent is now configured and ready to use.

[bold]Next Steps:[/bold]
  1. Initialize a project: [cyan]dev-agent init[/cyan]
  2. Or start interactive mode: [cyan]dev-agent[/cyan]
  3. Get help anytime: [cyan]dev-agent --help[/cyan]

For more information, visit the documentation or run [cyan]dev-agent help[/cyan]
            """
        else:
            completion_text = """
[bold yellow]Setup Incomplete[/bold yellow]

Some configuration steps were not completed.
You can run the setup wizard again with: [cyan]dev-agent setup[/cyan]

Or configure manually by setting environment variables.
See documentation for details.
            """

        self.console.print(
            Panel(
                completion_text.strip(),
                border_style="green" if result.ready_to_use else "yellow",
            )
        )

        # Show any errors
        if result.errors:
            self.console.print("\n[bold red]Errors encountered:[/bold red]")
            for error in result.errors:
                self.console.print(f"  • {error}")

        # Show skipped steps
        if result.skipped_steps:
            self.console.print("\n[bold yellow]Skipped steps:[/bold yellow]")
            for step in result.skipped_steps:
                self.console.print(f"  • {step}")

    def load_existing_preferences(self) -> UserPreferences | None:
        """Load existing user preferences from config file.

        Returns:
            UserPreferences if file exists and is valid, None otherwise
        """
        try:
            if not self.config_path.exists():
                return None

            prefs_dict = json.loads(self.config_path.read_text())

            return UserPreferences(
                azure_configured=prefs_dict.get("azure_configured", False),
                preferred_editor=prefs_dict.get("preferred_editor"),
                cost_warnings_enabled=prefs_dict.get("cost_warnings_enabled", True),
                budget_threshold=prefs_dict.get("budget_threshold"),
                auto_approve_phases=prefs_dict.get("auto_approve_phases", False),
                verbose_output=prefs_dict.get("verbose_output", False),
            )

        except Exception as e:
            logger.warning(f"Failed to load existing preferences: {e}")
            return None
