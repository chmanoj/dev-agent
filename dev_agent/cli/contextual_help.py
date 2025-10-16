"""Contextual CLI help system that provides phase-aware command suggestions."""

from __future__ import annotations

import difflib
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..models.enums import PhaseType

if TYPE_CHECKING:
    from ..models.project_state import ProjectState

console = Console()


class ContextualHelp:
    """Provides phase-aware help system with command suggestions."""

    def __init__(self):
        """Initialize the contextual help system."""
        self.phase_commands = self._build_phase_command_mappings()
        self.command_help = self._build_command_help_text()
        self.phase_descriptions = self._build_phase_descriptions()

    def _build_phase_command_mappings(self) -> dict[PhaseType | str, list[str]]:
        """Build command mappings for each workflow phase.
        
        Returns:
            Dictionary mapping phases to available commands
        """
        return {
            # General setup commands when no project is initialized
            "no_project": [
                "init",
                "setup", 
                "validate",
                "help",
                "examples",
                "cost-report"
            ],
            PhaseType.INDEXING: [
                "index",
                "status", 
                "analyze",
                "validate",
                "cost-report",
                "help"
            ],
            PhaseType.SPECIFICATION: [
                "spec",
                "requirements", 
                "validate",
                "status",
                "cost-report",
                "help"
            ],
            PhaseType.DESIGN: [
                "design",
                "architecture",
                "review",
                "validate", 
                "status",
                "cost-report",
                "help"
            ],
            PhaseType.IMPLEMENTATION: [
                "tasks",
                "generate",
                "test",
                "review",
                "complete",
                "status",
                "cost-report",
                "validate",
                "help"
            ]
        }

    def _build_command_help_text(self) -> dict[str, dict[str, str]]:
        """Build help text and usage examples for each command.
        
        Returns:
            Dictionary with command help information
        """
        return {
            # Setup commands (when no project is initialized)
            "init": {
                "description": "Initialize a new dev-agent project",
                "usage": "init [PROJECT_PATH] [--provider PROVIDER]",
                "example": "init --provider azure",
                "phase": "setup"
            },
            "setup": {
                "description": "Run interactive setup wizard or display setup status",
                "usage": "setup [--status] [--verbose]",
                "example": "setup --status",
                "phase": "setup"
            },
            "examples": {
                "description": "Display common workflow examples and usage patterns",
                "usage": "examples [WORKFLOW]",
                "example": "examples new_project",
                "phase": "setup"
            },
            
            # Indexing phase commands
            "index": {
                "description": "Index the codebase for analysis and pattern detection",
                "usage": "index [--force] [--verbose]",
                "example": "index --verbose",
                "phase": "indexing"
            },
            "analyze": {
                "description": "Analyze codebase structure and patterns",
                "usage": "analyze [--detailed] [--export FILE]",
                "example": "analyze --detailed",
                "phase": "indexing"
            },
            
            # Specification phase commands
            "spec": {
                "description": "Generate or edit project specifications",
                "usage": "spec [create|edit|view] [FEATURE_NAME]",
                "example": "spec create user-authentication",
                "phase": "specification"
            },
            "requirements": {
                "description": "Manage project requirements",
                "usage": "requirements [add|edit|list] [REQUIREMENT]",
                "example": "requirements add \"User login functionality\"",
                "phase": "specification"
            },
            
            # Design phase commands
            "design": {
                "description": "Generate or edit technical design documents",
                "usage": "design [create|edit|view] [COMPONENT]",
                "example": "design create authentication-service",
                "phase": "design"
            },
            "architecture": {
                "description": "View or modify system architecture",
                "usage": "architecture [view|edit] [--diagram]",
                "example": "architecture view --diagram",
                "phase": "design"
            },
            "review": {
                "description": "Review and approve design documents",
                "usage": "review [approve|reject|comment] [DOCUMENT]",
                "example": "review approve design.md",
                "phase": "design"
            },
            
            # Implementation phase commands
            "tasks": {
                "description": "Display and manage implementation tasks",
                "usage": "tasks [list|start|complete] [TASK_ID]",
                "example": "tasks list",
                "phase": "implementation"
            },
            "generate": {
                "description": "Generate code for current task",
                "usage": "generate [--task TASK_ID] [--file FILE]",
                "example": "generate --task 1.1",
                "phase": "implementation"
            },
            "test": {
                "description": "Run tests for current implementation",
                "usage": "test [--task TASK_ID] [--coverage]",
                "example": "test --coverage",
                "phase": "implementation"
            },
            "complete": {
                "description": "Mark task or phase as complete",
                "usage": "complete [task|phase] [ID]",
                "example": "complete task 1.1",
                "phase": "implementation"
            },
            
            # Common commands (available in all phases)
            "status": {
                "description": "Display current project status and progress",
                "usage": "status [--detailed] [--phase PHASE]",
                "example": "status --detailed",
                "phase": "all"
            },
            "cost-report": {
                "description": "Display cost and token usage report",
                "usage": "cost-report [--phase PHASE] [--export FILE]",
                "example": "cost-report --phase indexing",
                "phase": "all"
            },
            "validate": {
                "description": "Validate environment and configuration",
                "usage": "validate [--fix] [--verbose]",
                "example": "validate --fix",
                "phase": "all"
            },
            "help": {
                "description": "Show contextual help for current phase",
                "usage": "help [COMMAND]",
                "example": "help tasks",
                "phase": "all"
            }
        }

    def _build_phase_descriptions(self) -> dict[PhaseType | str, dict[str, str]]:
        """Build descriptions and guidance for each phase.
        
        Returns:
            Dictionary with phase descriptions and next actions
        """
        return {
            "no_project": {
                "title": "Project Setup",
                "description": "Initialize and configure dev-agent for your project",
                "purpose": "Set up dev-agent to work with your codebase and AI providers",
                "next_actions": [
                    "Run 'setup' to configure AI providers (Azure OpenAI or Gemini)",
                    "Use 'init' to initialize a project in current or specified directory",
                    "Check 'validate' to ensure configuration is correct",
                    "View 'examples' for common workflow patterns"
                ],
                "common_issues": [
                    "Ensure AI provider credentials are properly configured",
                    "Check network connectivity to AI services",
                    "Verify project directory permissions"
                ]
            },
            PhaseType.INDEXING: {
                "title": "Indexing Phase",
                "description": "Analyze codebase structure, patterns, dependencies, and detect language/framework",
                "purpose": "Understanding existing code and project setup to generate consistent specifications and designs",
                "next_actions": [
                    "Run 'index' to analyze your codebase",
                    "Use 'analyze' to see detected patterns and languages",
                    "Check 'status' to see indexing progress",
                    "Proceed to specification phase when complete"
                ],
                "common_issues": [
                    "Large codebases may take time to index",
                    "Ensure Azure OpenAI is configured properly",
                    "Check file permissions if indexing fails",
                    "Language detection requires configuration files (pyproject.toml, package.json, etc.)"
                ]
            },
            PhaseType.SPECIFICATION: {
                "title": "Specification Phase", 
                "description": "Create detailed specifications for new features or changes",
                "purpose": "Define what needs to be built with clear requirements and acceptance criteria",
                "next_actions": [
                    "Use 'spec create' to generate specifications",
                    "Add requirements with 'requirements add'",
                    "Review and validate specifications",
                    "Proceed to design phase when approved"
                ],
                "common_issues": [
                    "Be specific about feature requirements",
                    "Include acceptance criteria for clarity",
                    "Consider edge cases and error handling"
                ]
            },
            PhaseType.DESIGN: {
                "title": "Design Phase",
                "description": "Create technical design documents and architecture plans", 
                "purpose": "Plan the technical implementation before writing code",
                "next_actions": [
                    "Use 'design create' to generate technical designs",
                    "Review architecture with 'architecture view'",
                    "Approve designs with 'review approve'",
                    "Proceed to implementation phase when ready"
                ],
                "common_issues": [
                    "Ensure designs match existing architecture",
                    "Consider scalability and maintainability",
                    "Review security and performance implications"
                ]
            },
            PhaseType.IMPLEMENTATION: {
                "title": "Implementation Phase",
                "description": "Execute implementation tasks and generate code",
                "purpose": "Build the features according to specifications and designs",
                "next_actions": [
                    "View tasks with 'tasks list'",
                    "Generate code with 'generate'", 
                    "Run tests with 'test'",
                    "Mark tasks complete as you finish them"
                ],
                "common_issues": [
                    "Follow the task order for dependencies",
                    "Test each component as you build it",
                    "Keep generated code consistent with existing patterns"
                ]
            }
        }

    def get_phase_commands(self, phase: PhaseType | str) -> list[str]:
        """Get available commands for a specific phase.
        
        Args:
            phase: The workflow phase or "no_project" for setup commands
            
        Returns:
            List of available command names
        """
        return self.phase_commands.get(phase, [])

    def get_command_help(self, command: str, phase: PhaseType | None = None) -> str:
        """Get help text for a specific command.
        
        Args:
            command: Command name
            phase: Current phase for context
            
        Returns:
            Formatted help text for the command
        """
        if command not in self.command_help:
            return f"Unknown command: {command}"
            
        cmd_info = self.command_help[command]
        
        help_text = f"[bold cyan]{command}[/bold cyan] - {cmd_info['description']}\n\n"
        help_text += f"[bold]Usage:[/bold] {cmd_info['usage']}\n"
        help_text += f"[bold]Example:[/bold] {cmd_info['example']}\n"
        
        # Add phase-specific context if available
        if phase and cmd_info.get('phase') != 'all':
            phase_info = self.phase_descriptions.get(phase)
            if phase_info:
                help_text += f"\n[dim]Available in {phase_info['title']}[/dim]"
        
        return help_text

    def suggest_next_actions(self, phase: PhaseType | str, project_state: ProjectState | None = None) -> list[str]:
        """Suggest next actions based on current phase and project state.
        
        Args:
            phase: Current workflow phase or "no_project" for setup
            project_state: Current project state
            
        Returns:
            List of suggested action descriptions
        """
        phase_info = self.phase_descriptions.get(phase)
        if not phase_info:
            return ["Use 'help' to see available commands"]
            
        suggestions = phase_info["next_actions"].copy()
        
        # Add project-state specific suggestions
        if project_state and isinstance(phase, PhaseType):
            if phase == PhaseType.INDEXING and not project_state.indexing_complete:
                suggestions.insert(0, "Complete indexing first with 'index' command")
            elif phase == PhaseType.SPECIFICATION and not project_state.specification_approved:
                suggestions.insert(0, "Create and approve specification before proceeding")
            elif phase == PhaseType.DESIGN and not project_state.design_approved:
                suggestions.insert(0, "Create and approve design before implementation")
                
        return suggestions

    def suggest_similar_commands(self, invalid_command: str, phase: PhaseType | str) -> list[str]:
        """Suggest similar commands when user enters an unrecognized command.
        
        Args:
            invalid_command: The command that wasn't recognized
            phase: Current workflow phase or "no_project" for setup
            
        Returns:
            List of similar command suggestions
        """
        available_commands = self.get_phase_commands(phase)
        
        # Use difflib to find similar commands
        suggestions = difflib.get_close_matches(
            invalid_command, 
            available_commands, 
            n=3, 
            cutoff=0.6
        )
        
        # If no close matches, suggest most common commands for the phase
        if not suggestions:
            if phase == "no_project":
                suggestions = ["init", "setup", "help"]
            elif phase == PhaseType.INDEXING:
                suggestions = ["index", "status", "help"]
            elif phase == PhaseType.SPECIFICATION:
                suggestions = ["spec", "requirements", "help"]
            elif phase == PhaseType.DESIGN:
                suggestions = ["design", "review", "help"]
            elif phase == PhaseType.IMPLEMENTATION:
                suggestions = ["tasks", "generate", "help"]
                
        return suggestions

    def show_phase_help(self, phase: PhaseType | str, project_state: ProjectState | None = None) -> None:
        """Display contextual help for the current phase.
        
        Args:
            phase: Current workflow phase or "no_project" for setup
            project_state: Current project state for context
        """
        phase_info = self.phase_descriptions.get(phase)
        if not phase_info:
            console.print("[red]Unknown phase[/red]")
            return
            
        # Display phase header
        console.print(
            Panel.fit(
                f"[bold cyan]{phase_info['title']}[/bold cyan]\n{phase_info['description']}",
                border_style="cyan"
            )
        )
        console.print()
        
        # Display purpose
        console.print(f"[bold]Purpose:[/bold] {phase_info['purpose']}")
        console.print()
        
        # Display available commands
        console.print("[bold]Available Commands:[/bold]")
        commands_table = Table(show_header=False, box=None, padding=(0, 2))
        commands_table.add_column("Command", style="green", width=15)
        commands_table.add_column("Description", width=50)
        
        available_commands = self.get_phase_commands(phase)
        for cmd in available_commands:
            if cmd in self.command_help:
                cmd_info = self.command_help[cmd]
                commands_table.add_row(cmd, cmd_info["description"])
                
        console.print(commands_table)
        console.print()
        
        # Display next actions
        console.print("[bold]Suggested Next Actions:[/bold]")
        next_actions = self.suggest_next_actions(phase, project_state)
        for i, action in enumerate(next_actions, 1):
            console.print(f"  {i}. {action}")
        console.print()
        
        # Display common issues
        if phase_info.get("common_issues"):
            console.print("[bold]Common Issues:[/bold]")
            for issue in phase_info["common_issues"]:
                console.print(f"  • {issue}")
            console.print()

    def handle_unrecognized_command(self, command: str, phase: PhaseType | str) -> None:
        """Handle unrecognized commands with helpful suggestions.
        
        Args:
            command: The unrecognized command
            phase: Current workflow phase or "no_project" for setup
        """
        phase_name = phase.value if isinstance(phase, PhaseType) else phase.replace("_", " ")
        console.print(f"[red]Command '{command}' not recognized in {phase_name} phase[/red]")
        console.print()
        
        # Suggest similar commands
        suggestions = self.suggest_similar_commands(command, phase)
        if suggestions:
            console.print("[yellow]Did you mean:[/yellow]")
            for suggestion in suggestions:
                console.print(f"  • [cyan]{suggestion}[/cyan]")
            console.print()
        
        # Show available commands for current phase
        console.print(f"[bold]Available commands in {phase_name} phase:[/bold]")
        available_commands = self.get_phase_commands(phase)
        for cmd in available_commands:
            console.print(f"  • [green]{cmd}[/green]")
        console.print()
        
        console.print("Use [cyan]help[/cyan] to see detailed information about available commands.")

    def validate_command_availability(self, command: str, phase: PhaseType | str) -> bool:
        """Validate if a command is available in the current phase.
        
        Args:
            command: Command to validate
            phase: Current workflow phase or "no_project" for setup
            
        Returns:
            True if command is available in the phase
        """
        available_commands = self.get_phase_commands(phase)
        return command in available_commands

    def get_command_usage_example(self, command: str) -> str | None:
        """Get usage example for a specific command.
        
        Args:
            command: Command name
            
        Returns:
            Usage example string or None if command not found
        """
        if command in self.command_help:
            return self.command_help[command]["example"]
        return None

    def get_current_phase_or_setup(self, project_state: ProjectState | None = None) -> PhaseType | str:
        """Determine current phase or return 'no_project' if not initialized.
        
        Args:
            project_state: Current project state, None if no project
            
        Returns:
            Current phase or "no_project" for setup commands
        """
        if project_state is None:
            return "no_project"
        return project_state.current_phase

    def show_contextual_help(self, project_state: ProjectState | None = None, command: str | None = None) -> None:
        """Show contextual help based on current project state.
        
        Args:
            project_state: Current project state, None if no project
            command: Specific command to show help for, None for phase help
        """
        current_phase = self.get_current_phase_or_setup(project_state)
        
        if command:
            # Show help for specific command
            help_text = self.get_command_help(command, current_phase if isinstance(current_phase, PhaseType) else None)
            console.print(help_text)
        else:
            # Show phase-specific help
            self.show_phase_help(current_phase, project_state)

    def get_phase_progress_suggestions(self, project_state: ProjectState | None = None) -> list[str]:
        """Get suggestions for progressing through workflow phases.
        
        Args:
            project_state: Current project state
            
        Returns:
            List of progression suggestions
        """
        if project_state is None:
            return [
                "Initialize a project with 'init' command",
                "Configure AI providers with 'setup' command",
                "Check configuration with 'validate' command"
            ]
        
        suggestions = []
        current_phase = project_state.current_phase
        
        if current_phase == PhaseType.INDEXING:
            if not project_state.indexing_complete:
                suggestions.append("Complete indexing with 'index' command")
            else:
                suggestions.append("Move to specification phase")
                
        elif current_phase == PhaseType.SPECIFICATION:
            if not project_state.specification_approved:
                suggestions.append("Create and approve specifications")
            else:
                suggestions.append("Move to design phase")
                
        elif current_phase == PhaseType.DESIGN:
            if not project_state.design_approved:
                suggestions.append("Create and approve design documents")
            else:
                suggestions.append("Move to implementation phase")
                
        elif current_phase == PhaseType.IMPLEMENTATION:
            suggestions.append("Execute implementation tasks")
            suggestions.append("Generate code for current tasks")
            
        return suggestions