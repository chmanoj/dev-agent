"""Enhanced help system for dev-agent CLI."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


class HelpSystem:
    """Provides contextual help and examples for dev-agent commands."""

    def __init__(self):
        """Initialize the help system."""
        self.commands = self._build_command_reference()
        self.workflows = self._build_workflow_examples()

    def _build_command_reference(self) -> dict:
        """Build comprehensive command reference."""
        return {
            "init": {
                "description": "Initialize a new dev-agent project",
                "usage": "dev-agent init [PROJECT_PATH]",
                "options": [
                    ("-v, --verbose", "Enable verbose output"),
                    ("--debug", "Enable debug logging"),
                ],
                "examples": [
                    ("dev-agent init", "Initialize in current directory"),
                    ("dev-agent init /path/to/project", "Initialize specific directory"),
                    ("dev-agent init --verbose", "Initialize with verbose output"),
                ],
                "notes": [
                    "Detects if project is new or existing",
                    "Runs setup wizard if not configured",
                    "Automatically indexes existing codebases",
                    "Offers template selection for new projects",
                ],
            },
            "resume": {
                "description": "Resume an existing dev-agent project",
                "usage": "dev-agent resume [PROJECT_PATH]",
                "options": [
                    ("-v, --verbose", "Enable verbose output"),
                    ("--debug", "Enable debug logging"),
                ],
                "examples": [
                    ("dev-agent resume", "Resume project in current directory"),
                    ("dev-agent resume /path/to/project", "Resume specific project"),
                ],
                "notes": [
                    "Loads previous project state",
                    "Continues from last phase",
                    "Starts interactive mode automatically",
                ],
            },
            "setup": {
                "description": "Run interactive setup wizard or display setup status",
                "usage": "dev-agent setup [OPTIONS]",
                "options": [
                    ("--status", "Display current setup status"),
                    ("-v, --verbose", "Enable verbose output"),
                ],
                "examples": [
                    ("dev-agent setup", "Run setup wizard"),
                    ("dev-agent setup --status", "Check configuration status"),
                ],
                "notes": [
                    "Guides through Azure OpenAI configuration",
                    "Tests API connectivity",
                    "Explains workflow and costs",
                    "Can be re-run to reconfigure",
                ],
            },
            "status": {
                "description": "Display current project status and progress",
                "usage": "dev-agent status [OPTIONS]",
                "options": [
                    ("--detailed", "Show detailed status information"),
                    ("-v, --verbose", "Enable verbose output"),
                ],
                "examples": [
                    ("dev-agent status", "Show current status"),
                    ("dev-agent status --detailed", "Show detailed status"),
                ],
                "notes": [
                    "Shows current phase and progress",
                    "Displays completed phases",
                    "Shows cost information",
                    "Displays last activity timestamp",
                ],
            },
            "cost-report": {
                "description": "Display detailed cost and token usage report",
                "usage": "dev-agent cost-report [OPTIONS]",
                "options": [
                    ("--phase PHASE", "Filter by specific phase"),
                    ("--export FILE", "Export report as JSON"),
                    ("-v, --verbose", "Enable verbose output"),
                ],
                "examples": [
                    ("dev-agent cost-report", "Show complete cost report"),
                    ("dev-agent cost-report --phase indexing", "Show indexing costs"),
                    ("dev-agent cost-report --export costs.json", "Export to JSON"),
                ],
                "notes": [
                    "Shows token usage by operation type",
                    "Calculates costs based on Azure pricing",
                    "Warns if budget thresholds exceeded",
                    "Supports JSON export for analysis",
                ],
            },
            "validate": {
                "description": "Validate environment and configuration",
                "usage": "dev-agent validate [OPTIONS]",
                "options": [
                    ("-v, --verbose", "Enable verbose output"),
                ],
                "examples": [
                    ("dev-agent validate", "Run validation checks"),
                ],
                "notes": [
                    "Checks Azure OpenAI configuration",
                    "Tests API connectivity",
                    "Verifies required dependencies",
                    "Checks file system permissions",
                ],
            },
            "audit": {
                "description": "Run comprehensive audit of dev-agent functionality",
                "usage": "dev-agent audit [OPTIONS]",
                "options": [
                    ("-v, --verbose", "Enable verbose output"),
                ],
                "examples": [
                    ("dev-agent audit", "Run full audit"),
                ],
                "notes": [
                    "Tests all workflow phases",
                    "Verifies Azure OpenAI integration",
                    "Checks state management",
                    "Generates audit report",
                ],
            },
            "cleanup": {
                "description": "Scan and clean up repository files",
                "usage": "dev-agent cleanup [OPTIONS]",
                "options": [
                    ("--scan", "Scan for cleanup candidates"),
                    ("--dry-run", "Simulate cleanup without removing"),
                    ("--execute", "Execute cleanup (requires confirmation)"),
                    ("--category CAT", "Clean specific category only"),
                    ("--safety LEVEL", "Set safety level (safe/moderate/aggressive)"),
                ],
                "examples": [
                    ("dev-agent cleanup --scan", "Show what would be cleaned"),
                    ("dev-agent cleanup --dry-run", "Simulate cleanup"),
                    ("dev-agent cleanup --execute", "Execute cleanup"),
                    ("dev-agent cleanup --category temp", "Clean only temp files"),
                ],
                "notes": [
                    "Identifies temporary and generated files",
                    "Finds obsolete examples and artifacts",
                    "Detects unused dependencies",
                    "Creates backups before removal",
                ],
            },
            "azure": {
                "description": "Azure OpenAI configuration commands",
                "usage": "dev-agent azure <subcommand> [OPTIONS]",
                "subcommands": {
                    "configure": "Configure Azure OpenAI credentials",
                    "test": "Test Azure OpenAI connection",
                    "models": "List available models",
                },
                "examples": [
                    ("dev-agent azure configure", "Configure Azure OpenAI"),
                    ("dev-agent azure test", "Test connection"),
                    ("dev-agent azure models", "List available models"),
                ],
                "notes": [
                    "Stores credentials securely",
                    "Tests both completion and embedding endpoints",
                    "Validates deployment names",
                ],
            },
            "interactive": {
                "description": "Start interactive mode (default command)",
                "usage": "dev-agent [interactive] [PROJECT_PATH]",
                "options": [
                    ("-v, --verbose", "Enable verbose output"),
                    ("--debug", "Enable debug logging"),
                ],
                "examples": [
                    ("dev-agent", "Start interactive mode"),
                    ("dev-agent interactive", "Explicitly start interactive mode"),
                ],
                "notes": [
                    "Chat-based interface for workflow",
                    "Provides contextual help",
                    "Supports all workflow operations",
                ],
            },
        }

    def _build_workflow_examples(self) -> dict:
        """Build workflow examples."""
        return {
            "new_project": {
                "title": "New Project Workflow",
                "description": "Starting a new project from scratch",
                "steps": [
                    ("1. Run setup wizard", "dev-agent setup"),
                    ("2. Initialize project", "dev-agent init /path/to/new/project"),
                    ("3. Optional: Use template", "dev-agent scaffold list\ndev-agent scaffold create <template>"),
                    ("4. Start interactive mode", "dev-agent"),
                    ("5. Create specification", "Type your feature description in interactive mode"),
                    ("6. Review and approve", "Approve the generated specification"),
                    ("7. Generate design", "Continue to design phase"),
                    ("8. Generate tasks", "Continue to implementation phase"),
                    ("9. Implement features", "Follow the generated task list"),
                ],
                "estimated_time": "30-60 minutes for initial setup and specification",
                "estimated_cost": "$0.50-$2.00 depending on project complexity",
            },
            "existing_codebase": {
                "title": "Existing Codebase Workflow",
                "description": "Analyzing and extending an existing project",
                "steps": [
                    ("1. Run setup wizard", "dev-agent setup"),
                    ("2. Initialize in project", "cd /path/to/existing/project\ndev-agent init"),
                    ("3. Wait for indexing", "Automatic indexing of codebase"),
                    ("4. Review index summary", "Check detected patterns and languages"),
                    ("5. Start interactive mode", "dev-agent"),
                    ("6. Generate specification", "Describe new feature to add"),
                    ("7. Review design", "Design will match existing patterns"),
                    ("8. Generate tasks", "Tasks will match existing code style"),
                    ("9. Implement features", "Code generation uses indexed patterns"),
                ],
                "estimated_time": "15-30 minutes for indexing + 30-60 minutes for workflow",
                "estimated_cost": "$1.00-$5.00 depending on codebase size",
            },
            "quick_start": {
                "title": "Quick Start (5 Minutes)",
                "description": "Get started with dev-agent quickly",
                "steps": [
                    ("1. Install dev-agent", "pip install dev-agent"),
                    ("2. Run setup", "dev-agent setup"),
                    ("3. Configure Azure OpenAI", "Enter endpoint, API key, deployments"),
                    ("4. Test connection", "Wizard tests connection automatically"),
                    ("5. Initialize project", "dev-agent init"),
                    ("6. Start building", "Follow the interactive prompts"),
                ],
                "estimated_time": "5 minutes",
                "estimated_cost": "Free (no API calls during setup)",
            },
            "cost_management": {
                "title": "Managing Costs",
                "description": "Monitor and control Azure OpenAI costs",
                "steps": [
                    ("1. Check current costs", "dev-agent cost-report"),
                    ("2. View phase breakdown", "dev-agent cost-report --phase indexing"),
                    ("3. Export for analysis", "dev-agent cost-report --export costs.json"),
                    ("4. Monitor during workflow", "Cost shown after each phase"),
                    ("5. Set budget alerts", "Configure in Azure portal"),
                ],
                "estimated_time": "Ongoing monitoring",
                "estimated_cost": "Varies by usage",
            },
            "troubleshooting": {
                "title": "Troubleshooting Common Issues",
                "description": "Resolve common problems",
                "steps": [
                    ("1. Validate environment", "dev-agent validate"),
                    ("2. Check setup status", "dev-agent setup --status"),
                    ("3. Test Azure connection", "dev-agent azure test"),
                    ("4. Run audit", "dev-agent audit"),
                    ("5. Check logs", "Look in .dev_agent/logs/"),
                    ("6. Reconfigure if needed", "dev-agent setup"),
                ],
                "estimated_time": "5-15 minutes",
                "estimated_cost": "Minimal (only connection tests)",
            },
        }

    def show_command_help(self, command: str) -> None:
        """Display detailed help for a specific command.

        Args:
            command: Command name to show help for
        """
        if command not in self.commands:
            console.print(f"[red]Unknown command: {command}[/red]")
            console.print("\nAvailable commands:")
            for cmd in sorted(self.commands.keys()):
                console.print(f"  • {cmd}")
            console.print("\nUse [cyan]dev-agent help <command>[/cyan] for details")
            return

        cmd_info = self.commands[command]

        # Display command header
        console.print(
            Panel.fit(
                f"[bold cyan]{command}[/bold cyan] - {cmd_info['description']}",
                border_style="cyan",
            )
        )
        console.print()

        # Usage
        console.print("[bold]Usage:[/bold]")
        console.print(f"  {cmd_info['usage']}")
        console.print()

        # Options
        if cmd_info.get("options"):
            console.print("[bold]Options:[/bold]")
            options_table = Table(show_header=False, box=None, padding=(0, 2))
            options_table.add_column("Option", style="cyan")
            options_table.add_column("Description")

            for option, desc in cmd_info["options"]:
                options_table.add_row(option, desc)

            console.print(options_table)
            console.print()

        # Subcommands
        if "subcommands" in cmd_info:
            console.print("[bold]Subcommands:[/bold]")
            sub_table = Table(show_header=False, box=None, padding=(0, 2))
            sub_table.add_column("Subcommand", style="cyan")
            sub_table.add_column("Description")

            for subcmd, desc in cmd_info["subcommands"].items():
                sub_table.add_row(subcmd, desc)

            console.print(sub_table)
            console.print()

        # Examples
        if cmd_info.get("examples"):
            console.print("[bold]Examples:[/bold]")
            for example, desc in cmd_info["examples"]:  # Command first, then description
                console.print(f"  [dim]{desc}:[/dim]")
                console.print(f"  [green]$ {example}[/green]")
                console.print()

        # Notes
        if cmd_info.get("notes"):
            console.print("[bold]Notes:[/bold]")
            for note in cmd_info["notes"]:
                console.print(f"  • {note}")
            console.print()

    def show_all_commands(self) -> None:
        """Display overview of all commands."""
        console.print(
            Panel.fit(
                "[bold cyan]dev-agent Command Reference[/bold cyan]\n"
                "AI-powered development workflow assistant",
                border_style="cyan",
            )
        )
        console.print()

        # Group commands by category
        categories = {
            "Project Management": ["init", "resume", "setup"],
            "Monitoring": ["status", "cost-report", "validate", "audit"],
            "Maintenance": ["cleanup"],
            "Configuration": ["azure"],
            "Interactive": ["interactive"],
        }

        for category, commands in categories.items():
            console.print(f"[bold cyan]{category}:[/bold cyan]")

            cmd_table = Table(show_header=False, box=None, padding=(0, 2))
            cmd_table.add_column("Command", style="green", width=20)
            cmd_table.add_column("Description", width=60)

            for cmd in commands:
                if cmd in self.commands:
                    cmd_table.add_row(cmd, self.commands[cmd]["description"])

            console.print(cmd_table)
            console.print()

        # Footer
        console.print("[dim]Use [cyan]dev-agent help <command>[/cyan] for detailed help on a specific command[/dim]")
        console.print("[dim]Use [cyan]dev-agent examples[/cyan] to see common workflow examples[/dim]")
        console.print()

    def show_examples(self, workflow: str | None = None) -> None:
        """Display workflow examples.

        Args:
            workflow: Specific workflow to show, or None for all
        """
        if workflow and workflow not in self.workflows:
            console.print(f"[red]Unknown workflow: {workflow}[/red]")
            console.print("\nAvailable workflows:")
            for wf in sorted(self.workflows.keys()):
                console.print(f"  • {wf}")
            console.print("\nUse [cyan]dev-agent examples <workflow>[/cyan] for details")
            return

        if workflow:
            # Show specific workflow
            wf_info = self.workflows[workflow]
            console.print(
                Panel.fit(
                    f"[bold cyan]{wf_info['title']}[/bold cyan]\n{wf_info['description']}",
                    border_style="cyan",
                )
            )
            console.print()

            console.print("[bold]Steps:[/bold]")
            for step_desc, step_cmd in wf_info["steps"]:
                console.print(f"\n[cyan]{step_desc}[/cyan]")
                for line in step_cmd.split("\n"):
                    console.print(f"  [green]$ {line}[/green]")

            console.print()
            console.print(f"[bold]Estimated Time:[/bold] {wf_info['estimated_time']}")
            console.print(f"[bold]Estimated Cost:[/bold] {wf_info['estimated_cost']}")
            console.print()

        else:
            # Show all workflows overview
            console.print(
                Panel.fit(
                    "[bold cyan]dev-agent Workflow Examples[/bold cyan]\n"
                    "Common workflows and usage patterns",
                    border_style="cyan",
                )
            )
            console.print()

            for wf_name, wf_info in self.workflows.items():
                console.print(f"[bold green]{wf_info['title']}[/bold green]")
                console.print(f"  {wf_info['description']}")
                console.print(f"  [dim]Time: {wf_info['estimated_time']} | Cost: {wf_info['estimated_cost']}[/dim]")
                console.print(f"  [cyan]View details: dev-agent examples {wf_name}[/cyan]")
                console.print()

            console.print("[dim]Use [cyan]dev-agent examples <workflow>[/cyan] for detailed steps[/dim]")
            console.print()

    def show_quick_reference(self) -> None:
        """Display quick reference card."""
        console.print(
            Panel.fit(
                "[bold cyan]dev-agent Quick Reference[/bold cyan]",
                border_style="cyan",
            )
        )
        console.print()

        # Most common commands
        console.print("[bold]Most Common Commands:[/bold]")
        common = [
            ("dev-agent setup", "First-time configuration"),
            ("dev-agent init", "Initialize project"),
            ("dev-agent", "Start interactive mode"),
            ("dev-agent status", "Check project status"),
            ("dev-agent cost-report", "View costs"),
            ("dev-agent validate", "Troubleshoot issues"),
        ]

        for cmd, desc in common:
            console.print(f"  [green]{cmd:30}[/green] {desc}")

        console.print()

        # Quick tips
        console.print("[bold]Quick Tips:[/bold]")
        tips = [
            "Run [cyan]dev-agent setup[/cyan] before first use",
            "Use [cyan]--verbose[/cyan] flag for detailed output",
            "Check [cyan]dev-agent setup --status[/cyan] if having issues",
            "Interactive mode is the easiest way to use dev-agent",
            "Costs are shown after each phase completion",
        ]

        for tip in tips:
            console.print(f"  • {tip}")

        console.print()

        # Get more help
        console.print("[bold]Get More Help:[/bold]")
        console.print("  • [cyan]dev-agent help <command>[/cyan] - Detailed command help")
        console.print("  • [cyan]dev-agent examples[/cyan] - Workflow examples")
        console.print("  • [cyan]dev-agent --help[/cyan] - Built-in help")
        console.print()


# Global help system instance
help_system = HelpSystem()
