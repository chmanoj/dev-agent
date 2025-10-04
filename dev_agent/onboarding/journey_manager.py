"""Journey manager for guiding users through different project scenarios."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from dev_agent.models.enums import PhaseType
from dev_agent.onboarding.models import OnboardingFlow, OnboardingStep

console = Console()


@dataclass
class ProjectContext:
    """Context about the project being worked on.

    Attributes:
        path: Path to the project directory
        project_type: Type of project (new, existing, template)
        has_code: Whether the project has existing code
        languages_detected: List of programming languages detected
        estimated_size: Estimated project size (small, medium, large)
        complexity: Project complexity level
        file_count: Number of files in the project
    """

    path: Path
    project_type: str  # "new", "existing", "template"
    has_code: bool
    languages_detected: list[str] = field(default_factory=list)
    estimated_size: str = "unknown"  # "small", "medium", "large"
    complexity: str = "unknown"  # "simple", "moderate", "complex"
    file_count: int = 0


class JourneyManager:
    """Manages user journey based on project context.

    This class provides contextual guidance for users based on their
    project type (new vs existing) and current workflow phase.
    """

    def __init__(self, config_path: Path | None = None):
        """Initialize journey manager.

        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = config_path or Path.home() / ".dev_agent" / "dev_agent_config.json"
        self.console = Console()

    def detect_project_type(self, path: Path) -> ProjectContext:
        """Detect project type by analyzing the directory.

        Args:
            path: Path to the project directory

        Returns:
            ProjectContext with detected information
        """
        path = Path(path).resolve()

        # Check if directory exists
        if not path.exists():
            return ProjectContext(
                path=path,
                project_type="new",
                has_code=False,
                estimated_size="small",
                complexity="simple",
            )

        # Check if directory is empty
        if not any(path.iterdir()):
            return ProjectContext(
                path=path,
                project_type="new",
                has_code=False,
                estimated_size="small",
                complexity="simple",
            )

        # Analyze existing directory
        return self._analyze_existing_project(path)

    def _analyze_existing_project(self, path: Path) -> ProjectContext:
        """Analyze an existing project directory.

        Args:
            path: Path to the project directory

        Returns:
            ProjectContext with analysis results
        """
        # Count files and detect languages
        file_count = 0
        languages = set()
        code_extensions = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".java": "Java",
            ".go": "Go",
            ".rs": "Rust",
            ".cpp": "C++",
            ".c": "C",
            ".cs": "C#",
            ".rb": "Ruby",
            ".php": "PHP",
            ".swift": "Swift",
            ".kt": "Kotlin",
        }

        # Walk through directory (excluding common ignore patterns)
        ignore_dirs = {
            ".git",
            ".venv",
            "venv",
            "node_modules",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            "dist",
            "build",
            ".dev_agent",
        }

        for item in path.rglob("*"):
            # Skip ignored directories
            if any(ignored in item.parts for ignored in ignore_dirs):
                continue

            if item.is_file():
                file_count += 1
                suffix = item.suffix.lower()
                if suffix in code_extensions:
                    languages.add(code_extensions[suffix])

        # Determine if it has code
        has_code = len(languages) > 0

        # Estimate size
        if file_count < 50:
            estimated_size = "small"
        elif file_count < 500:
            estimated_size = "medium"
        else:
            estimated_size = "large"

        # Estimate complexity
        if len(languages) <= 1 and file_count < 50:
            complexity = "simple"
        elif len(languages) <= 2 and file_count < 200:
            complexity = "moderate"
        else:
            complexity = "complex"

        return ProjectContext(
            path=path,
            project_type="existing" if has_code else "new",
            has_code=has_code,
            languages_detected=sorted(languages),
            estimated_size=estimated_size,
            complexity=complexity,
            file_count=file_count,
        )

    def is_first_run(self) -> bool:
        """Check if this is the first time dev-agent is being run.

        Returns:
            True if config file doesn't exist, False otherwise
        """
        return not self.config_path.exists()

    def get_onboarding_flow(self, project_context: ProjectContext) -> OnboardingFlow:
        """Get appropriate onboarding flow based on project context.

        Args:
            project_context: Context about the project

        Returns:
            OnboardingFlow with steps and guidance
        """
        if project_context.project_type == "new":
            return self._get_new_project_flow(project_context)
        else:
            return self._get_existing_codebase_flow(project_context)

    def _get_new_project_flow(self, _context: ProjectContext) -> OnboardingFlow:
        """Get onboarding flow for new projects.

        Args:
            _context: Project context (unused but kept for consistency)

        Returns:
            OnboardingFlow for new projects
        """
        steps = [
            OnboardingStep(
                title="Welcome to dev-agent",
                description="Let's set up your new project with AI-powered development workflow",
                action=lambda: True,
                help_text="dev-agent will guide you through creating a new project from scratch",
                estimated_time="1 minute",
                skippable=False,
            ),
            OnboardingStep(
                title="Configure Azure OpenAI",
                description="Set up your Azure OpenAI credentials for AI-powered features",
                action=lambda: True,
                help_text="You'll need an Azure OpenAI endpoint and API key",
                estimated_time="3 minutes",
                skippable=False,
            ),
            OnboardingStep(
                title="Choose Project Template",
                description="Select a template to scaffold your project structure",
                action=lambda: True,
                help_text="Templates provide best-practice project structures",
                estimated_time="2 minutes",
                skippable=True,
            ),
            OnboardingStep(
                title="Create Initial Specification",
                description="Define what you want to build",
                action=lambda: True,
                help_text="Describe your project goals and requirements",
                estimated_time="5 minutes",
                skippable=False,
            ),
        ]

        tips = [
            "Start with a clear project goal in mind",
            "Templates can save you setup time",
            "You can always modify the generated structure",
            "Azure OpenAI costs are tracked automatically",
        ]

        warnings = [
            "Make sure you have Azure OpenAI access before starting",
            "Keep your API keys secure and never commit them to git",
        ]

        return OnboardingFlow(steps=steps, tips=tips, warnings=warnings)

    def _get_existing_codebase_flow(self, context: ProjectContext) -> OnboardingFlow:
        """Get onboarding flow for existing codebases.

        Args:
            context: Project context

        Returns:
            OnboardingFlow for existing codebases
        """
        steps = [
            OnboardingStep(
                title="Welcome to dev-agent",
                description=f"Let's analyze your existing {', '.join(context.languages_detected)} codebase",
                action=lambda: True,
                help_text="dev-agent will index and understand your code",
                estimated_time="1 minute",
                skippable=False,
            ),
            OnboardingStep(
                title="Configure Azure OpenAI",
                description="Set up your Azure OpenAI credentials for AI-powered analysis",
                action=lambda: True,
                help_text="You'll need an Azure OpenAI endpoint and API key",
                estimated_time="3 minutes",
                skippable=False,
            ),
            OnboardingStep(
                title="Index Codebase",
                description=f"Analyze {context.file_count} files and generate embeddings",
                action=lambda: True,
                help_text="This creates a searchable index of your code",
                estimated_time=self._estimate_indexing_time(context),
                skippable=False,
            ),
            OnboardingStep(
                title="Review Analysis",
                description="See detected patterns and architecture",
                action=lambda: True,
                help_text="Understand what dev-agent learned about your codebase",
                estimated_time="2 minutes",
                skippable=False,
            ),
        ]

        tips = [
            f"Your {context.estimated_size} codebase will be analyzed locally",
            "Indexing creates embeddings for semantic code search",
            "Detected patterns help generate consistent code",
            "You can re-run indexing anytime to update the analysis",
        ]

        warnings = [
            "Indexing large codebases may take several minutes",
            f"Estimated {context.file_count} files to process",
            "Azure OpenAI API calls will incur costs",
        ]

        return OnboardingFlow(steps=steps, tips=tips, warnings=warnings)

    def _estimate_indexing_time(self, context: ProjectContext) -> str:
        """Estimate indexing time based on project size.

        Args:
            context: Project context

        Returns:
            Estimated time string
        """
        if context.file_count < 50:
            return "1-2 minutes"
        elif context.file_count < 200:
            return "3-5 minutes"
        elif context.file_count < 500:
            return "5-10 minutes"
        else:
            return "10-20 minutes"

    def guide_user_through_phase(
        self,
        phase: PhaseType,
        project_context: ProjectContext,
    ) -> None:
        """Provide contextual guidance for a workflow phase.

        Args:
            phase: Current workflow phase
            project_context: Context about the project
        """
        guidance = self._get_phase_guidance(phase, project_context)

        # Display guidance panel
        description = guidance.get("description", "")
        if isinstance(description, list):
            description = "\n".join(description)

        panel = Panel(
            description,
            title=f"[bold cyan]{guidance.get('title', 'Phase Guidance')}[/bold cyan]",
            border_style="cyan",
        )
        self.console.print(panel)

        # Display tips if available
        if guidance.get("tips"):
            self.console.print("\n[bold yellow]💡 Tips:[/bold yellow]")
            for tip in guidance["tips"]:
                self.console.print(f"  • {tip}")

        # Display what to expect
        if guidance.get("what_to_expect"):
            self.console.print("\n[bold green]📋 What to Expect:[/bold green]")
            for item in guidance["what_to_expect"]:
                self.console.print(f"  • {item}")

        # Display estimated time and cost
        if guidance.get("estimated_time"):
            self.console.print(f"\n[dim]⏱️  Estimated time: {guidance['estimated_time']}[/dim]")

        if guidance.get("estimated_cost"):
            self.console.print(f"[dim]💰 Estimated cost: {guidance['estimated_cost']}[/dim]")

        self.console.print()

    def _get_phase_guidance(
        self,
        phase: PhaseType,
        context: ProjectContext,
    ) -> dict[str, str | list[str]]:
        """Get guidance information for a specific phase.

        Args:
            phase: Workflow phase
            context: Project context

        Returns:
            Dictionary with guidance information
        """
        if phase == PhaseType.INDEXING:
            return self._get_indexing_guidance(context)
        elif phase == PhaseType.SPECIFICATION:
            return self._get_specification_guidance(context)
        elif phase == PhaseType.DESIGN:
            return self._get_design_guidance(context)
        else:  # PhaseType.IMPLEMENTATION
            return self._get_implementation_guidance(context)

    def _get_indexing_guidance(self, context: ProjectContext) -> dict[str, str | list[str]]:
        """Get guidance for indexing phase."""
        if context.project_type == "new":
            return {
                "title": "Indexing Phase - New Project",
                "description": (
                    "Since this is a new project, there's no existing code to index yet. "
                    "You can skip this phase and move directly to specification."
                ),
                "tips": [
                    "You'll return to indexing after generating initial code",
                    "Indexing helps dev-agent understand your code patterns",
                ],
                "what_to_expect": [
                    "Quick validation that directory is ready",
                    "Setup of project structure",
                ],
                "estimated_time": "< 1 minute",
                "estimated_cost": "$0.00",
            }
        else:
            return {
                "title": "Indexing Phase - Existing Codebase",
                "description": (
                    f"dev-agent will analyze your {context.estimated_size} codebase "
                    f"({context.file_count} files) to understand its structure, patterns, and conventions."
                ),
                "tips": [
                    "Indexing creates embeddings for semantic code search",
                    "Detected patterns help generate consistent code",
                    "This only needs to be done once (or when code changes significantly)",
                    "You can exclude files using .gitignore patterns",
                ],
                "what_to_expect": [
                    "Parse code files using Tree-sitter",
                    "Generate embeddings via Azure OpenAI",
                    "Store vectors in FAISS database",
                    "Detect coding patterns and conventions",
                    f"Process {context.file_count} files",
                ],
                "estimated_time": self._estimate_indexing_time(context),
                "estimated_cost": self._estimate_indexing_cost(context),
            }

    def _get_specification_guidance(self, context: ProjectContext) -> dict[str, str | list[str]]:
        """Get guidance for specification phase."""
        if context.project_type == "new":
            return {
                "title": "Specification Phase - New Project",
                "description": (
                    "Define what you want to build. dev-agent will help you create "
                    "a detailed specification document using GPT-4."
                ),
                "tips": [
                    "Be specific about your requirements",
                    "Include user stories and acceptance criteria",
                    "Think about edge cases and error handling",
                    "You can iterate on the specification",
                ],
                "what_to_expect": [
                    "Interactive prompts about your project",
                    "GPT-4 generates structured specification",
                    "Review and approval step",
                    "Saved to .dev_agent/documents/specification.md",
                ],
                "estimated_time": "5-10 minutes",
                "estimated_cost": "$0.10 - $0.30",
            }
        else:
            return {
                "title": "Specification Phase - Existing Codebase",
                "description": (
                    "Generate specifications based on your existing code. "
                    "dev-agent will analyze patterns and create documentation."
                ),
                "tips": [
                    "Specifications will reference your existing code",
                    "Useful for documenting undocumented features",
                    "Can help plan new features that fit existing patterns",
                    "Review carefully to ensure accuracy",
                ],
                "what_to_expect": [
                    "Retrieve relevant code via vector search",
                    "GPT-4 analyzes code and generates specs",
                    "Specifications match your coding style",
                    "Review and approval step",
                ],
                "estimated_time": "3-7 minutes",
                "estimated_cost": "$0.15 - $0.40",
            }

    def _get_design_guidance(self, context: ProjectContext) -> dict[str, str | list[str]]:
        """Get guidance for design phase."""
        return {
            "title": "Design Phase",
            "description": (
                "Create a technical design document based on your specification. "
                "This includes architecture, components, and implementation details."
            ),
            "tips": [
                "Design will reference your specification",
                "Includes component diagrams and data models",
                "Considers existing architectural patterns" if context.has_code else "Follows best practices",
                "You can iterate on the design",
            ],
            "what_to_expect": [
                "GPT-4 generates technical design",
                "Architecture and component breakdown",
                "Data models and interfaces",
                "Error handling strategy",
                "Testing approach",
                "Review and approval step",
            ],
            "estimated_time": "5-10 minutes",
            "estimated_cost": "$0.20 - $0.50",
        }

    def _get_implementation_guidance(self, _context: ProjectContext) -> dict[str, str | list[str]]:
        """Get guidance for implementation phase.

        Args:
            _context: Project context (unused but kept for consistency)
        """
        return {
            "title": "Implementation Phase",
            "description": (
                "Break down the design into actionable implementation tasks. "
                "Each task will be a discrete coding step."
            ),
            "tips": [
                "Tasks are ordered for incremental development",
                "Each task references specific requirements",
                "Test-driven development is encouraged",
                "You can execute tasks one at a time",
            ],
            "what_to_expect": [
                "GPT-4 generates task breakdown",
                "Numbered checklist of coding tasks",
                "Each task has clear objectives",
                "Tasks build on each other",
                "Saved to .dev_agent/documents/tasks.md",
            ],
            "estimated_time": "3-5 minutes",
            "estimated_cost": "$0.10 - $0.25",
        }

    def _estimate_indexing_cost(self, context: ProjectContext) -> str:
        """Estimate indexing cost based on project size.

        Args:
            context: Project context

        Returns:
            Estimated cost string
        """
        # Rough estimate: $0.0001 per 1000 tokens for embeddings
        # Average file ~500 tokens
        estimated_tokens = context.file_count * 500
        estimated_cost = (estimated_tokens / 1000) * 0.0001

        if estimated_cost < 0.01:
            return "< $0.01"
        elif estimated_cost < 0.10:
            return f"~${estimated_cost:.2f}"
        else:
            return f"~${estimated_cost:.2f}"

    def display_project_summary(self, context: ProjectContext) -> None:
        """Display a summary of the detected project.

        Args:
            context: Project context to display
        """
        table = Table(title="Project Analysis", show_header=False, box=None)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Project Type", context.project_type.title())
        table.add_row("Has Code", "Yes" if context.has_code else "No")

        if context.languages_detected:
            table.add_row("Languages", ", ".join(context.languages_detected))

        table.add_row("File Count", str(context.file_count))
        table.add_row("Estimated Size", context.estimated_size.title())
        table.add_row("Complexity", context.complexity.title())

        self.console.print(table)
        self.console.print()
