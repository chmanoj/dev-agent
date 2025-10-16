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
                    "Automatically detects programming language and frameworks",
                    "Runs setup wizard if not configured",
                    "Automatically indexes existing codebases",
                    "Offers template selection for new projects",
                    "Applies language-specific naming conventions",
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
            "tasks": {
                "description": "Display and manage implementation tasks",
                "usage": "dev-agent tasks [OPTIONS]",
                "options": [
                    ("--action ACTION", "Action to perform (list, start, complete)"),
                    ("--task-id ID", "Specific task ID to operate on"),
                    ("-v, --verbose", "Enable verbose output"),
                ],
                "examples": [
                    ("dev-agent tasks", "List all tasks"),
                    ("dev-agent tasks --action start --task-id 1.1", "Start task 1.1"),
                    ("dev-agent tasks --action complete --task-id 1.1", "Complete task 1.1"),
                ],
                "notes": [
                    "Shows task status and progress",
                    "Tracks task dependencies",
                    "Updates project state automatically",
                    "Available in implementation phase",
                ],
            },
            "generate": {
                "description": "Generate code for current implementation task",
                "usage": "dev-agent generate [OPTIONS]",
                "options": [
                    ("--task-id ID", "Generate code for specific task"),
                    ("--file FILE", "Generate specific file"),
                    ("--provider PROVIDER", "Use specific LLM provider"),
                    ("-v, --verbose", "Enable verbose output"),
                ],
                "examples": [
                    ("dev-agent generate", "Generate code for current context"),
                    ("dev-agent generate --task-id 1.1", "Generate code for task 1.1"),
                    ("dev-agent generate --file src/auth.py", "Generate specific file"),
                    ("dev-agent generate --provider gemini", "Use Gemini provider"),
                ],
                "notes": [
                    "Uses indexed codebase patterns",
                    "Maintains consistency with existing code",
                    "Supports multiple LLM providers",
                    "Available in implementation phase",
                ],
            },
            "test": {
                "description": "Run tests for current implementation",
                "usage": "dev-agent test [OPTIONS]",
                "options": [
                    ("--task-id ID", "Run tests for specific task"),
                    ("--coverage", "Generate coverage report"),
                    ("--pattern PATTERN", "Test file pattern to run"),
                    ("-v, --verbose", "Enable verbose output"),
                ],
                "examples": [
                    ("dev-agent test", "Run all tests"),
                    ("dev-agent test --coverage", "Run tests with coverage"),
                    ("dev-agent test --task-id 1.1", "Run tests for task 1.1"),
                    ("dev-agent test --pattern '*auth*'", "Run auth-related tests"),
                ],
                "notes": [
                    "Integrates with pytest",
                    "Supports coverage reporting",
                    "Can filter by task or pattern",
                    "Shows test results in CLI",
                ],
            },
            "review": {
                "description": "Review implementation progress and code quality",
                "usage": "dev-agent review [OPTIONS]",
                "options": [
                    ("--action ACTION", "Review action (view, approve, reject, comment)"),
                    ("--task-id ID", "Review specific task"),
                    ("--file FILE", "Review specific file"),
                    ("--comment TEXT", "Add review comment"),
                    ("-v, --verbose", "Enable verbose output"),
                ],
                "examples": [
                    ("dev-agent review", "View implementation status"),
                    ("dev-agent review --action approve --task-id 1.1", "Approve task 1.1"),
                    ("dev-agent review --action comment --file src/auth.py --comment 'Add error handling'", "Add comment"),
                ],
                "notes": [
                    "Tracks implementation progress",
                    "Supports approval workflow",
                    "Allows commenting on tasks/files",
                    "Available in implementation phase",
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
                "description": "Analyzing and extending an existing project with automatic language detection",
                "steps": [
                    ("1. Run setup wizard", "dev-agent setup"),
                    ("2. Initialize in project", "cd /path/to/existing/project\ndev-agent init"),
                    ("3. Language detection", "Automatic detection of Python/TypeScript/JavaScript/Java"),
                    ("4. Framework detection", "Detects FastAPI, React, Django, Express, etc."),
                    ("5. Wait for indexing", "Automatic indexing of codebase"),
                    ("6. Review index summary", "Check detected patterns and languages"),
                    ("7. Start interactive mode", "dev-agent"),
                    ("8. Generate specification", "Describe new feature to add"),
                    ("9. Review design", "Design will match existing patterns"),
                    ("10. Generate tasks", "Tasks use language-specific naming conventions"),
                    ("11. Implement features", "Code generation follows detected patterns"),
                ],
                "estimated_time": "15-30 minutes for indexing + 30-60 minutes for workflow",
                "estimated_cost": "$1.00-$5.00 depending on codebase size",
            },
            "language_detection": {
                "title": "Language Detection Features",
                "description": "Understanding how dev-agent detects and applies language patterns",
                "steps": [
                    ("1. Configuration analysis", "Scans pyproject.toml, package.json, pom.xml"),
                    ("2. File extension analysis", "Counts .py, .ts, .js, .java files"),
                    ("3. Framework detection", "Analyzes dependencies and file patterns"),
                    ("4. Pattern application", "Applies snake_case for Python, camelCase for JS/TS"),
                    ("5. Task generation", "Creates tasks with correct naming conventions"),
                    ("6. Code generation", "Generates code following detected patterns"),
                ],
                "estimated_time": "Automatic (< 1 minute)",
                "estimated_cost": "Free (no API calls for detection)",
                "supported_languages": [
                    "Python (snake_case methods, PascalCase classes)",
                    "TypeScript (camelCase methods, PascalCase classes)",
                    "JavaScript (camelCase methods, PascalCase classes)",
                    "Java (camelCase methods, PascalCase classes)",
                ],
                "supported_frameworks": [
                    "Python: FastAPI, Django, Flask, Streamlit",
                    "TypeScript/JavaScript: React, Angular, Express, NestJS",
                ],
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
            "implementation": {
                "title": "Implementation Phase Workflow",
                "description": "Execute implementation tasks and generate code",
                "steps": [
                    ("1. View task list", "dev-agent tasks"),
                    ("2. Start a task", "dev-agent tasks --action start --task-id 1.1"),
                    ("3. Generate code", "dev-agent generate --task-id 1.1"),
                    ("4. Run tests", "dev-agent test --coverage"),
                    ("5. Review progress", "dev-agent review"),
                    ("6. Complete task", "dev-agent tasks --action complete --task-id 1.1"),
                    ("7. Repeat for next task", "Continue with remaining tasks"),
                    ("8. Final review", "dev-agent review --action approve"),
                ],
                "estimated_time": "Varies by task complexity (30 minutes - 2 hours per task)",
                "estimated_cost": "$0.10-$1.00 per task depending on code complexity",
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

    def show_language_detection_help(self) -> None:
        """Display help about language and framework detection."""
        console.print(Panel.fit(
            "[bold cyan]Language and Framework Detection[/bold cyan]\n\n"
            "[bold]Automatic Detection:[/bold]\n"
            "• Analyzes project files and configuration\n"
            "• Detects primary programming language\n"
            "• Identifies frameworks and libraries\n"
            "• Applies appropriate naming conventions\n\n"
            "[bold]Supported Languages:[/bold]\n"
            "• Python (snake_case, PascalCase classes)\n"
            "• TypeScript/JavaScript (camelCase, PascalCase classes)\n"
            "• Java (camelCase, PascalCase classes)\n\n"
            "[bold]Supported Frameworks:[/bold]\n"
            "• Python: FastAPI, Django, Flask, Streamlit\n"
            "• TypeScript: React, Angular, Express, NestJS\n"
            "• JavaScript: React, Vue, Express\n\n"
            "[bold]Detection Sources:[/bold]\n"
            "• Configuration files (pyproject.toml, package.json, etc.)\n"
            "• File extensions and naming patterns\n"
            "• Dependencies and imports\n"
            "• Directory structure analysis\n\n"
            "[bold]Pattern Application:[/bold]\n"
            "• Task generation uses detected patterns\n"
            "• Code generation follows conventions\n"
            "• File naming matches project style\n"
            "• Import statements use correct format\n\n"
            "[bold]Troubleshooting:[/bold]\n"
            "• Ensure config files exist (pyproject.toml, package.json)\n"
            "• Check file permissions for project analysis\n"
            "• Language defaults to Python if detection fails\n"
            "• Use 'dev-agent analyze' to see detected patterns",
            title="Language Detection",
            border_style="cyan"
        ))

    def show_troubleshooting_guide(self) -> None:
        """Display troubleshooting guide for common issues."""
        console.print(Panel.fit(
            "[bold red]Common Issues and Solutions[/bold red]\n\n"
            "[bold]Language Detection Issues:[/bold]\n"
            "• Problem: Wrong language detected\n"
            "  Solution: Ensure config files exist (pyproject.toml, package.json)\n"
            "• Problem: No frameworks detected\n"
            "  Solution: Check dependencies in requirements.txt or package.json\n"
            "• Problem: Tasks use wrong naming conventions\n"
            "  Solution: Verify language detection with 'dev-agent analyze'\n\n"
            "[bold]Task Generation Issues:[/bold]\n"
            "• Problem: Tasks don't match project style\n"
            "  Solution: Re-run 'dev-agent init' to re-detect patterns\n"
            "• Problem: Generated code uses wrong patterns\n"
            "  Solution: Check that framework is correctly detected\n\n"
            "[bold]General Issues:[/bold]\n"
            "• Problem: Indexing fails\n"
            "  Solution: Check file permissions and Azure OpenAI config\n"
            "• Problem: API errors during generation\n"
            "  Solution: Verify Azure OpenAI credentials and quotas",
            title="Troubleshooting Guide",
            border_style="red"
        ))

    def show_command_help(self, command: str) -> None:
        """Display detailed help for a specific command.

        Args:
            command: Command name to show help for
        """
        # Handle special help topics
        if command == "language-detection":
            self.show_language_detection_help()
            return
        elif command == "troubleshooting":
            self.show_troubleshooting_guide()
            return
        
        if command not in self.commands:
            console.print(f"[red]Unknown command: {command}[/red]")
            console.print("\nAvailable commands:")
            for cmd in sorted(self.commands.keys()):
                console.print(f"  • {cmd}")
            console.print("\nSpecial help topics:")
            console.print("  • language-detection")
            console.print("  • troubleshooting")
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
