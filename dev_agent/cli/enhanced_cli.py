"""Enhanced CLI with Rich UI components for improved user experience."""

from __future__ import annotations

import difflib
import re
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.prompt import Confirm, Prompt
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from dev_agent.interfaces.cli_interface import ICLIInterface
from dev_agent.models.enums import PhaseType

if TYPE_CHECKING:
    from dev_agent.interfaces.workflow_interface import IWorkflowManager


class ProgressManager:
    """Manages interactive progress tracking with time estimates."""

    def __init__(self, console: Console):
        """Initialize the progress manager.

        Args:
            console: Rich console instance for output
        """
        self.console = console
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
            expand=True,
        )
        self.current_task: TaskID | None = None
        self.phase_start_times: dict[PhaseType, datetime] = {}
        self.phase_estimates: dict[PhaseType, float] = {
            PhaseType.INDEXING: 30.0,  # 30 seconds
            PhaseType.SPECIFICATION: 45.0,  # 45 seconds
            PhaseType.DESIGN: 60.0,  # 1 minute
            PhaseType.IMPLEMENTATION: 120.0,  # 2 minutes
        }

    def start_phase_progress(self, phase: PhaseType, total_steps: int = 100) -> TaskID:
        """Start progress tracking for a phase.

        Args:
            phase: The phase being tracked
            total_steps: Total number of steps (default 100 for percentage)

        Returns:
            Task ID for the progress task
        """
        self.phase_start_times[phase] = datetime.now()
        description = f"[bold blue]{phase.value.title()}[/bold blue]"

        if self.current_task is not None:
            self.progress.remove_task(self.current_task)

        self.current_task = self.progress.add_task(
            description, total=total_steps, start=True
        )
        return self.current_task

    def update_progress(self, completed: int, status_message: str = "") -> None:
        """Update the current progress.

        Args:
            completed: Number of completed steps
            status_message: Optional status message to display
        """
        if self.current_task is not None:
            # Get current task description safely
            description = None
            try:
                # Rich Progress stores tasks differently - try to get the task
                for task in self.progress.tasks:
                    if task.id == self.current_task:
                        description = task.description
                        break

                if description and status_message:
                    description = f"{description.split(' - ')[0]} - {status_message}"
                elif status_message:
                    description = f"Progress - {status_message}"

            except (KeyError, IndexError, AttributeError):
                description = (
                    f"Progress - {status_message}" if status_message else "Progress"
                )

            if description:
                self.progress.update(
                    self.current_task, completed=completed, description=description
                )
            else:
                self.progress.update(self.current_task, completed=completed)

    def complete_phase(self, phase: PhaseType) -> None:
        """Complete the current phase progress.

        Args:
            phase: The phase that was completed
        """
        if self.current_task is not None:
            self.progress.update(self.current_task, completed=100)

            # Calculate actual time taken
            if phase in self.phase_start_times:
                elapsed = datetime.now() - self.phase_start_times[phase]
                elapsed_seconds = elapsed.total_seconds()

                # Update estimate for future runs
                self.phase_estimates[phase] = (
                    self.phase_estimates[phase] * 0.7 + elapsed_seconds * 0.3
                )

    def show_phase_summary(self, completed_phases: list[PhaseType]) -> None:
        """Show a summary of completed phases.

        Args:
            completed_phases: List of completed phases
        """
        table = Table(
            title="Phase Summary", show_header=True, header_style="bold magenta"
        )
        table.add_column("Phase", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")
        table.add_column("Duration", style="yellow")

        for phase in PhaseType:
            if phase in completed_phases:
                status = "✅ Complete"
                duration = "N/A"
                if phase in self.phase_start_times:
                    # This would need to be tracked properly in a real implementation
                    duration = f"{int(self.phase_estimates[phase])}s"
            else:
                status = "⏳ Pending"
                duration = f"~{int(self.phase_estimates[phase])}s"

            table.add_row(phase.value.title(), status, duration)

        self.console.print(table)


class DocumentPreviewer:
    """Handles syntax-highlighted document previews and diff views."""

    def __init__(self, console: Console):
        """Initialize the document previewer.

        Args:
            console: Rich console instance for output
        """
        self.console = console
        self.language_map = {
            "specification": "markdown",
            "design": "markdown",
            "tasks": "markdown",
            "python": "python",
            "javascript": "javascript",
            "typescript": "typescript",
            "json": "json",
            "yaml": "yaml",
            "toml": "toml",
        }

    def show_document_preview(
        self,
        content: str,
        document_type: str,
        title: str | None = None,
        line_numbers: bool = True,
    ) -> None:
        """Show a syntax-highlighted preview of a document.

        Args:
            content: Document content to preview
            document_type: Type of document (affects syntax highlighting)
            title: Optional title for the preview
            line_numbers: Whether to show line numbers
        """
        language = self.language_map.get(document_type.lower(), "text")

        if not title:
            title = f"{document_type.title()} Preview"

        # Create syntax-highlighted content
        syntax = Syntax(
            content,
            language,
            theme="monokai",
            line_numbers=line_numbers,
            word_wrap=True,
            background_color="default",
        )

        # Create panel with the content
        panel = Panel(
            syntax,
            title=f"[bold cyan]{title}[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )

        self.console.print(panel)

    def show_diff_view(
        self,
        old_content: str,
        new_content: str,
        title: str = "Changes",
        context_lines: int = 3,
    ) -> None:
        """Show a diff view between two versions of content.

        Args:
            old_content: Original content
            new_content: Modified content
            title: Title for the diff view
            context_lines: Number of context lines to show around changes
        """
        # Split content into lines
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)

        # Generate unified diff
        diff_lines = list(
            difflib.unified_diff(
                old_lines,
                new_lines,
                fromfile="Original",
                tofile="Modified",
                n=context_lines,
            )
        )

        if not diff_lines:
            self.console.print(f"[green]✅ No changes detected in {title}[/green]")
            return

        # Create colored diff output
        diff_content = Text()

        for diff_line in diff_lines:
            line = diff_line.rstrip("\n")
            if line.startswith("+++") or line.startswith("---"):
                diff_content.append(line + "\n", style="bold white")
            elif line.startswith("@@"):
                diff_content.append(line + "\n", style="bold cyan")
            elif line.startswith("+"):
                diff_content.append(line + "\n", style="bold green")
            elif line.startswith("-"):
                diff_content.append(line + "\n", style="bold red")
            else:
                diff_content.append(line + "\n", style="dim white")

        # Create panel with diff
        panel = Panel(
            diff_content,
            title=f"[bold yellow]📋 {title}[/bold yellow]",
            border_style="yellow",
            padding=(1, 2),
        )

        self.console.print(panel)

    def show_file_tree(self, project_path: str, max_depth: int = 3) -> None:
        """Show a tree view of the project structure.

        Args:
            project_path: Path to the project root
            max_depth: Maximum depth to traverse
        """

        def add_directory_to_tree(
            tree: Tree, path: Path, current_depth: int = 0
        ) -> None:
            """Recursively add directory contents to tree."""
            if current_depth >= max_depth:
                return

            try:
                items = sorted(
                    path.iterdir(), key=lambda x: (x.is_file(), x.name.lower())
                )
                for item in items:
                    if item.name.startswith(".") and item.name not in [
                        ".gitignore",
                        ".env.example",
                    ]:
                        continue

                    if item.is_dir():
                        branch = tree.add(f"📁 [bold blue]{item.name}[/bold blue]")
                        add_directory_to_tree(branch, item, current_depth + 1)
                    else:
                        # Add file with appropriate icon
                        icon = self._get_file_icon(item.suffix)
                        tree.add(f"{icon} {item.name}")
            except PermissionError:
                tree.add("[red]❌ Permission denied[/red]")

        project_path_obj = Path(project_path)
        tree = Tree(f"📁 [bold green]{project_path_obj.name}[/bold green]")

        add_directory_to_tree(tree, project_path_obj)

        panel = Panel(
            tree,
            title="[bold cyan]📂 Project Structure[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )

        self.console.print(panel)

    def _get_file_icon(self, extension: str) -> str:
        """Get an appropriate icon for a file extension.

        Args:
            extension: File extension (including dot)

        Returns:
            Unicode icon for the file type
        """
        icon_map = {
            ".py": "🐍",
            ".js": "📜",
            ".ts": "📘",
            ".html": "🌐",
            ".css": "🎨",
            ".json": "📋",
            ".yaml": "⚙️",
            ".yml": "⚙️",
            ".toml": "⚙️",
            ".md": "📝",
            ".txt": "📄",
            ".log": "📊",
            ".env": "🔐",
            ".gitignore": "🚫",
            ".dockerfile": "🐳",
            ".sql": "🗃️",
        }
        return icon_map.get(extension.lower(), "📄")


class CLIVisualizationEngine:
    """CLI wrapper for the visualization engine with console output."""

    def __init__(self, console: Console):
        """Initialize the CLI visualization engine.

        Args:
            console: Rich console instance for output
        """
        self.console = console
        # Import here to avoid circular imports
        from dev_agent.analysis.visualization_engine import VisualizationEngine
        from dev_agent.models.visualization import VisualizationConfig

        config = VisualizationConfig(enable_interactive_features=True)
        self.engine = VisualizationEngine(config)

    def generate_architecture_diagram_from_analysis(
        self, project_analysis: dict[str, Any]
    ) -> str:
        """Generate a Mermaid architecture diagram from project analysis.

        Args:
            project_analysis: Dictionary containing project structure and dependencies

        Returns:
            Mermaid diagram syntax as string
        """
        # Convert analysis dict to ArchitectureInfo if needed
        from dev_agent.models.analysis import ArchitectureInfo

        if isinstance(project_analysis, dict):
            architecture_info = ArchitectureInfo(
                patterns=[],
                layers=project_analysis.get("layers", []),
                components=project_analysis.get("components", []),
                dependencies=project_analysis.get("dependencies", {}),
                entry_points=project_analysis.get("entry_points", []),
                data_flow=project_analysis.get("data_flow", {}),
                technology_stack=project_analysis.get("technology_stack", []),
            )
        else:
            architecture_info = project_analysis

        return self.engine.generate_architecture_diagram(
            architecture_info, "Project Architecture"
        )

    def generate_workflow_diagram(self, phases: list[PhaseType]) -> str:
        """Generate a Mermaid workflow diagram for dev-agent phases.

        Args:
            phases: List of workflow phases

        Returns:
            Mermaid diagram syntax as string
        """
        mermaid_lines = ["flowchart LR"]

        phase_nodes = []
        for i, phase in enumerate(phases):
            node_id = f"P{i}"
            phase_name = phase.value.title()
            phase_nodes.append(node_id)

            # Add phase node with appropriate styling
            if phase == PhaseType.INDEXING:
                mermaid_lines.append(f'    {node_id}["🔍 {phase_name}"]')
            elif phase == PhaseType.SPECIFICATION:
                mermaid_lines.append(f'    {node_id}["📋 {phase_name}"]')
            elif phase == PhaseType.DESIGN:
                mermaid_lines.append(f'    {node_id}["🏗️ {phase_name}"]')
            elif phase == PhaseType.IMPLEMENTATION:
                mermaid_lines.append(f'    {node_id}["⚡ {phase_name}"]')

        # Connect phases in sequence
        mermaid_lines.extend(
            [
                f"    {phase_nodes[i]} --> {phase_nodes[i + 1]}"
                for i in range(len(phase_nodes) - 1)
            ]
        )

        # Add styling
        mermaid_lines.extend(
            [
                "",
                "    classDef indexing fill:#fff3e0,stroke:#e65100,stroke-width:2px",
                "    classDef specification fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px",
                "    classDef design fill:#e3f2fd,stroke:#1565c0,stroke-width:2px",
                "    classDef implementation fill:#fce4ec,stroke:#c2185b,stroke-width:2px",
            ]
        )

        return "\n".join(mermaid_lines)

    def show_architecture_diagram(self, project_analysis: dict[str, Any]) -> None:
        """Display architecture diagram in the console.

        Args:
            project_analysis: Project analysis data
        """
        diagram = self.generate_architecture_diagram_from_analysis(project_analysis)

        # Create syntax-highlighted Mermaid code
        syntax = Syntax(
            diagram,
            "mermaid",
            theme="monokai",
            line_numbers=True,
            word_wrap=True,
        )

        panel = Panel(
            syntax,
            title="[bold cyan]🏗️ Architecture Diagram (Mermaid)[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )

        self.console.print(panel)

        # Validate the diagram and show results
        validation_result = self.engine.validate_diagram(diagram)

        if validation_result.warnings or validation_result.suggestions:
            validation_text = Text()

            if validation_result.warnings:
                validation_text.append("⚠️ Warnings:\n", style="bold yellow")
                for warning in validation_result.warnings:
                    validation_text.append(f"  • {warning}\n", style="yellow")
                validation_text.append("\n")

            if validation_result.suggestions:
                validation_text.append("💡 Suggestions:\n", style="bold blue")
                for suggestion in validation_result.suggestions:
                    validation_text.append(f"  • {suggestion}\n", style="blue")

            validation_panel = Panel(
                validation_text,
                title="[bold yellow]📊 Diagram Analysis[/bold yellow]",
                border_style="yellow",
                padding=(1, 2),
            )
            self.console.print(validation_panel)

        # Show instructions for rendering and exporting
        instructions = Text()
        instructions.append("💡 To render this diagram:\n", style="bold yellow")
        instructions.append("1. Copy the Mermaid code above\n", style="white")
        instructions.append("2. Paste it into https://mermaid.live/\n", style="white")
        instructions.append(
            "3. Or use a Mermaid-enabled markdown viewer\n", style="white"
        )
        instructions.append(
            "4. Use 'export diagram' command to save to file\n", style="white"
        )

        info_panel = Panel(
            instructions,
            title="[bold green]📖 How to Render[/bold green]",
            border_style="green",
            padding=(1, 2),
        )

        self.console.print(info_panel)

    def export_diagram_to_file(
        self, diagram: str, output_path: str, format_type: str = "mermaid"
    ) -> None:
        """Export diagram to file with user feedback.

        Args:
            diagram: Mermaid diagram string
            output_path: Path to save the diagram
            format_type: Export format (mermaid, html, json)
        """
        try:
            from dev_agent.models.visualization import (
                DiagramExportOptions,
                ExportFormat,
            )

            format_map = {
                "mermaid": ExportFormat.MERMAID,
                "html": ExportFormat.HTML,
                "json": ExportFormat.JSON,
            }

            if format_type not in format_map:
                self.console.print(f"[red]❌ Unsupported format: {format_type}[/red]")
                return

            options = DiagramExportOptions(
                format=format_map[format_type],
                include_metadata=True,
                include_styling=True,
            )

            self.engine.export_diagram(diagram, output_path, options)

            self.console.print(f"[green]✅ Diagram exported to: {output_path}[/green]")

            # Show file info
            file_path = Path(output_path)
            if file_path.exists():
                file_size = file_path.stat().st_size
                self.console.print(f"[dim]File size: {file_size} bytes[/dim]")

        except Exception as e:
            self.console.print(f"[red]❌ Export failed: {e}[/red]")

    def show_workflow_diagram(self, phases: list[PhaseType]) -> None:
        """Display workflow diagram in the console.

        Args:
            phases: List of workflow phases
        """
        diagram = self.generate_workflow_diagram(phases)

        syntax = Syntax(
            diagram,
            "mermaid",
            theme="monokai",
            line_numbers=True,
            word_wrap=True,
        )

        panel = Panel(
            syntax,
            title="[bold magenta]🔄 Workflow Diagram (Mermaid)[/bold magenta]",
            border_style="magenta",
            padding=(1, 2),
        )

        self.console.print(panel)


class SearchAndFilterEngine:
    """Provides search and filtering capabilities for documents and project data."""

    def __init__(self, console: Console):
        """Initialize the search and filter engine.

        Args:
            console: Rich console instance for output
        """
        self.console = console

    def search_in_document(
        self, content: str, query: str, context_lines: int = 2
    ) -> list[dict[str, Any]]:
        """Search for a query within document content.

        Args:
            content: Document content to search
            query: Search query
            context_lines: Number of context lines to include around matches

        Returns:
            List of search results with line numbers and context
        """
        lines = content.split("\n")
        results = []

        for line_num, line in enumerate(lines, 1):
            if query.lower() in line.lower():
                # Get context lines
                start_line = max(0, line_num - 1 - context_lines)
                end_line = min(len(lines), line_num + context_lines)

                context = [
                    {
                        "line_number": i + 1,
                        "content": lines[i],
                        "is_match": i == line_num - 1,
                    }
                    for i in range(start_line, end_line)
                ]

                results.append(
                    {
                        "line_number": line_num,
                        "line_content": line,
                        "context": context,
                    }
                )

        return results

    def filter_project_files(
        self, project_path: str, filters: dict[str, Any]
    ) -> list[Path]:
        """Filter project files based on criteria.

        Args:
            project_path: Path to project root
            filters: Dictionary of filter criteria

        Returns:
            List of filtered file paths
        """
        project_path_obj = Path(project_path)
        all_files = []

        # Collect all files
        all_files = [
            file_path
            for file_path in project_path_obj.rglob("*")
            if file_path.is_file()
        ]

        filtered_files = all_files

        # Apply extension filter
        if "extensions" in filters:
            extensions = filters["extensions"]
            filtered_files = [
                f for f in filtered_files if f.suffix.lower() in extensions
            ]

        # Apply size filter
        if "max_size" in filters:
            max_size = filters["max_size"]
            filtered_files = [f for f in filtered_files if f.stat().st_size <= max_size]

        # Apply name pattern filter
        if "name_pattern" in filters:
            pattern = re.compile(filters["name_pattern"], re.IGNORECASE)
            filtered_files = [f for f in filtered_files if pattern.search(f.name)]

        # Exclude hidden files by default
        if filters.get("include_hidden", False) is False:
            filtered_files = [f for f in filtered_files if not f.name.startswith(".")]

        return filtered_files

    def show_search_results(
        self, results: list[dict[str, Any]], query: str, document_type: str
    ) -> None:
        """Display search results in a formatted table.

        Args:
            results: List of search results
            query: Original search query
            document_type: Type of document searched
        """
        if not results:
            self.console.print(
                f"[yellow]No matches found for '{query}' in {document_type}[/yellow]"
            )
            return

        # Create results table
        table = Table(
            title=f"Search Results for '{query}' in {document_type}",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Line", style="dim", width=6)
        table.add_column("Content", style="white")
        table.add_column("Context", style="dim")

        for result in results[:10]:  # Limit to first 10 results
            line_num = str(result["line_number"])
            content = result["line_content"].strip()

            # Highlight the query in the content
            highlighted_content = content.replace(
                query, f"[bold yellow]{query}[/bold yellow]"
            )

            # Create context preview
            context_lines = []
            for ctx in result["context"]:
                if ctx["is_match"]:
                    continue  # Skip the match line itself
                context_lines.append(f"L{ctx['line_number']}: {ctx['content'][:50]}...")

            context_preview = "\n".join(context_lines[:3])  # Show max 3 context lines

            table.add_row(line_num, highlighted_content, context_preview)

        self.console.print(table)

        if len(results) > 10:
            self.console.print(f"[dim]... and {len(results) - 10} more results[/dim]")

    def show_filtered_files(
        self, files: list[Path], filters: dict[str, Any], project_path: str
    ) -> None:
        """Display filtered files in a tree structure.

        Args:
            files: List of filtered file paths
            filters: Applied filters
            project_path: Project root path
        """
        if not files:
            self.console.print("[yellow]No files match the specified filters[/yellow]")
            return

        # Create filter summary
        filter_text = Text()
        filter_text.append("Applied Filters:\n", style="bold cyan")

        for key, value in filters.items():
            filter_text.append(f"  {key}: {value}\n", style="white")

        filter_panel = Panel(
            filter_text,
            title="[bold blue]🔍 Filters[/bold blue]",
            border_style="blue",
            padding=(1, 2),
        )

        self.console.print(filter_panel)

        # Group files by directory
        project_root = Path(project_path)
        file_tree: dict[str, Any] = {}

        for file_path in files:
            # Check if file is within project root before processing
            if not str(file_path).startswith(str(project_root)):
                continue

            try:
                relative_path = file_path.relative_to(project_root)
                parts = relative_path.parts

                current_level = file_tree
                for part in parts[:-1]:  # All parts except filename
                    if part not in current_level:
                        current_level[part] = {}
                    current_level = current_level[part]

                # Add the file
                filename = parts[-1]
                current_level[filename] = None  # None indicates it's a file

            except ValueError:
                # File is outside project root, skip
                continue

        # Create tree visualization
        tree = Tree(
            f"📁 [bold green]{project_root.name}[/bold green] ({len(files)} files)"
        )
        self._add_tree_nodes(tree, file_tree)

        tree_panel = Panel(
            tree,
            title="[bold green]📂 Filtered Files[/bold green]",
            border_style="green",
            padding=(1, 2),
        )

        self.console.print(tree_panel)

    def _add_tree_nodes(self, parent_tree: Tree, file_dict: dict[str, Any]) -> None:
        """Recursively add nodes to the tree structure.

        Args:
            parent_tree: Parent tree node
            file_dict: Dictionary representing file structure
        """
        for name, content in sorted(file_dict.items()):
            if content is None:  # It's a file
                # Get file icon based on extension
                icon = self._get_file_icon(Path(name).suffix)
                parent_tree.add(f"{icon} {name}")
            else:  # It's a directory
                branch = parent_tree.add(f"📁 [bold blue]{name}[/bold blue]")
                self._add_tree_nodes(branch, content)

    def _get_file_icon(self, extension: str) -> str:
        """Get an appropriate icon for a file extension.

        Args:
            extension: File extension (including dot)

        Returns:
            Unicode icon for the file type
        """
        icon_map = {
            ".py": "🐍",
            ".js": "📜",
            ".ts": "📘",
            ".html": "🌐",
            ".css": "🎨",
            ".json": "📋",
            ".yaml": "⚙️",
            ".yml": "⚙️",
            ".toml": "⚙️",
            ".md": "📝",
            ".txt": "📄",
            ".log": "📊",
            ".env": "🔐",
            ".gitignore": "🚫",
            ".dockerfile": "🐳",
            ".sql": "🗃️",
        }
        return icon_map.get(extension.lower(), "📄")


class ContextualHelpSystem:
    """Provides contextual help and command suggestions based on workflow state."""

    def __init__(self, console: Console):
        """Initialize the contextual help system.

        Args:
            console: Rich console instance for output
        """
        self.console = console
        self.help_shown_count = 0
        self.last_help_time = datetime.now()

        # Define help content for different contexts
        self.phase_help = {
            PhaseType.INDEXING: {
                "description": "Analyzing and indexing your codebase",
                "commands": [
                    ("status", "Check indexing progress"),
                    ("skip", "Skip to next phase (not recommended)"),
                    ("cancel", "Cancel current operation"),
                ],
                "tips": [
                    "Indexing may take longer for large codebases",
                    "The system is analyzing code patterns and dependencies",
                    "You can continue working while indexing runs in background",
                ],
            },
            PhaseType.SPECIFICATION: {
                "description": "Generating project specification document",
                "commands": [
                    ("approve", "Approve the generated specification"),
                    ("reject", "Reject and regenerate specification"),
                    ("edit", "Make manual edits to specification"),
                    ("preview", "Show specification preview"),
                ],
                "tips": [
                    "Review the specification carefully before approving",
                    "You can request changes or additions",
                    "The specification guides all subsequent phases",
                ],
            },
            PhaseType.DESIGN: {
                "description": "Creating technical design document",
                "commands": [
                    ("approve", "Approve the generated design"),
                    ("reject", "Reject and regenerate design"),
                    ("diff", "Show changes from previous version"),
                    ("architecture", "View architecture diagram"),
                ],
                "tips": [
                    "The design builds upon your approved specification",
                    "Check that all requirements are addressed",
                    "Consider scalability and maintainability aspects",
                ],
            },
            PhaseType.IMPLEMENTATION: {
                "description": "Generating implementation tasks and code",
                "commands": [
                    ("tasks", "View implementation task list"),
                    ("generate", "Generate code for specific task"),
                    ("test", "Run generated tests"),
                    ("review", "Review generated code"),
                ],
                "tips": [
                    "Tasks are ordered by dependency and complexity",
                    "Review generated code before integration",
                    "Tests are generated alongside implementation code",
                ],
            },
        }

        self.general_commands = [
            ("help", "Show this help message"),
            ("status", "Show current project status"),
            ("history", "Show command history"),
            ("architecture", "Show project architecture diagram"),
            ("workflow", "Show workflow phase diagram"),
            ("search <query> <doc>", "Search within documents"),
            ("filter [options]", "Filter project files"),
            ("preview <doc>", "Preview document with syntax highlighting"),
            ("diff <old> <new>", "Show differences between documents"),
            ("tree [path]", "Show project file tree"),
            ("clear", "Clear the screen"),
            ("undo", "Undo last operation"),
            ("redo", "Redo last undone operation"),
            ("save", "Save current progress"),
            ("exit", "Exit dev-agent"),
        ]

    def should_show_help(self, context: dict[str, Any]) -> bool:
        """Determine if contextual help should be shown automatically.

        Args:
            context: Current workflow context

        Returns:
            True if help should be shown
        """
        # Show help less frequently as user becomes more familiar
        time_since_last = datetime.now() - self.last_help_time

        # Show help on first run or if user seems stuck
        return (
            self.help_shown_count == 0
            or time_since_last.total_seconds() > 300  # 5 minutes
            or context.get("errors_count", 0) > 2  # Multiple errors
        )

    def show_contextual_help(self, context: dict[str, Any]) -> None:
        """Show contextual help based on current workflow state.

        Args:
            context: Current workflow context including phase, errors, etc.
        """
        current_phase = context.get("current_phase")

        if current_phase and current_phase in self.phase_help:
            self._show_phase_help(current_phase)
        else:
            self._show_general_help()

        self.help_shown_count += 1
        self.last_help_time = datetime.now()

    def _show_phase_help(self, phase: PhaseType) -> None:
        """Show help specific to a workflow phase.

        Args:
            phase: Current workflow phase
        """
        help_info = self.phase_help[phase]

        # Create help content
        help_content = Text()
        help_content.append("📍 Current Phase: ", style="bold white")
        help_content.append(f"{phase.value.title()}\n", style="bold cyan")
        help_content.append(f"{help_info['description']}\n\n", style="dim white")

        # Add available commands
        help_content.append("Available Commands:\n", style="bold yellow")
        for cmd, desc in help_info["commands"]:
            help_content.append(f"  {cmd:<12} - {desc}\n", style="white")

        help_content.append("\n")

        # Add tips
        help_content.append("💡 Tips:\n", style="bold green")
        for tip in help_info["tips"]:
            help_content.append(f"  • {tip}\n", style="dim green")

        # Create panel
        panel = Panel(
            help_content,
            title=f"[bold blue]🤖 Contextual Help - {phase.value.title()}[/bold blue]",
            border_style="blue",
            padding=(1, 2),
        )

        self.console.print(panel)

    def _show_general_help(self) -> None:
        """Show general help information."""
        # Show a quick start guide instead of just general commands
        help_content = Panel(
            """👋 Getting Started

To begin using dev-agent, initialize a project:
• init - Initialize in current directory
• init /path - Initialize at specific path

Once initialized, you can run the complete workflow or execute individual phases.""",
            title="[bold cyan]Quick Start[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )

        self.console.print(help_content)

    def display_full_help(self, context: dict[str, Any]) -> None:  # noqa: ARG002
        """Display comprehensive help information.

        Args:
            context: Current workflow context
        """
        # Create general commands table
        commands_table = Table(
            title="General Commands", show_header=True, header_style="bold yellow"
        )
        commands_table.add_column("Command", style="cyan", no_wrap=True)
        commands_table.add_column("Description", style="white")

        for cmd, desc in self.general_commands:
            commands_table.add_row(cmd, desc)

        # Create phases table
        phases_table = Table(
            title="Workflow Phases", show_header=True, header_style="bold green"
        )
        phases_table.add_column("Phase", style="cyan", no_wrap=True)
        phases_table.add_column("Description", style="white")

        for phase in PhaseType:
            phase_info = self.phase_help.get(phase, {})
            desc_value = phase_info.get("description", "No description available")
            desc = (
                desc_value
                if isinstance(desc_value, str)
                else "No description available"
            )
            phases_table.add_row(phase.value.title(), desc)

        # Print both tables
        self.console.print(commands_table)
        self.console.print()
        self.console.print(phases_table)

    def show_command_suggestions(
        self, invalid_command: str, context: dict[str, Any]
    ) -> None:
        """Show command suggestions for invalid commands.

        Args:
            invalid_command: The invalid command entered
            context: Current workflow context
        """
        current_phase = context.get("current_phase")

        # Get available commands for current phase
        available_commands = []
        if current_phase and current_phase in self.phase_help:
            available_commands.extend(
                [cmd for cmd, _ in self.phase_help[current_phase]["commands"]]
            )

        available_commands.extend([cmd for cmd, _ in self.general_commands])

        # Find similar commands using simple string matching
        suggestions = [
            cmd
            for cmd in available_commands
            if (
                invalid_command.lower() in cmd.lower()
                or cmd.lower() in invalid_command.lower()
            )
        ]

        # If no similar commands, suggest most relevant for current phase
        if not suggestions and current_phase:
            suggestions = [
                cmd for cmd, _ in self.phase_help[current_phase]["commands"][:3]
            ]

        if suggestions:
            suggestion_text = Text()
            suggestion_text.append(
                f"❓ Unknown command: '{invalid_command}'\n\n", style="bold red"
            )
            suggestion_text.append("Did you mean:\n", style="bold yellow")

            for suggestion in suggestions[:5]:  # Limit to 5 suggestions
                suggestion_text.append(f"  • {suggestion}\n", style="cyan")

            suggestion_text.append(
                "\nType 'help' for all available commands", style="dim white"
            )

            panel = Panel(
                suggestion_text,
                title="[bold red]🤔 Command Suggestions[/bold red]",
                border_style="red",
                padding=(1, 2),
            )

            self.console.print(panel)


class EnhancedCLI(ICLIInterface):
    """Enhanced interactive CLI with Rich UI components and advanced features."""

    def __init__(self, workflow_manager: IWorkflowManager | None = None):
        """Initialize the enhanced CLI.

        Args:
            workflow_manager: Optional workflow manager for handling project operations
        """
        self.workflow_manager = workflow_manager
        self.session_active = False
        self.console = Console()
        self.progress_manager = ProgressManager(self.console)
        self.document_previewer = DocumentPreviewer(self.console)
        self.help_system = ContextualHelpSystem(self.console)
        self.visualization_engine = CLIVisualizationEngine(self.console)
        self.search_engine = SearchAndFilterEngine(self.console)
        self.command_history: list[str] = []
        self.current_project_path: str | None = None
        self._setup_signal_handlers()

        # Initialize workflow manager if not provided
        if not self.workflow_manager:
            from dev_agent.workflow.workflow_manager import (  # noqa: PLC0415
                WorkflowManager,
            )

            self.workflow_manager = WorkflowManager(self)

    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful exit."""
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)

    def _handle_interrupt(self, signum: int, frame: Any) -> None:  # noqa: ARG002
        """Handle interrupt signals for graceful shutdown."""
        self.console.print(
            "\n[yellow]Received interrupt signal. Shutting down gracefully...[/yellow]"
        )
        self._graceful_exit()

    def _graceful_exit(self) -> None:
        """Perform graceful exit operations."""
        if self.session_active:
            self.console.print("[blue]Saving session state...[/blue]")
            self.session_active = False
        self.console.print("[green]Goodbye![/green]")
        sys.exit(0)

    def start_chat_session(self) -> None:
        """Start an interactive chat session with enhanced UI."""
        self.session_active = True

        # Display welcome banner
        self._display_welcome_banner()

        while self.session_active:
            try:
                # Get current context for help system
                current_context = self._get_current_context()

                # Show contextual help if needed
                if self.help_system.should_show_help(current_context):
                    self.help_system.show_contextual_help(current_context)

                user_input = Prompt.ask(
                    "[bold cyan]dev-agent[/bold cyan]", default="help"
                )

                if user_input.lower().strip() in ["exit", "quit", "q"]:
                    self._graceful_exit()
                elif user_input.lower().strip() == "help":
                    self.help_system.display_full_help(current_context)
                else:
                    response = self.handle_user_input(user_input)
                    if response:
                        self.display_message(response)

            except (EOFError, KeyboardInterrupt):  # noqa: PERF203
                self._graceful_exit()

    def _display_welcome_banner(self) -> None:
        """Display an enhanced welcome banner."""
        banner_text = """
[bold blue]🤖 dev-agent[/bold blue] - AI-powered development workflow assistant

[dim]Enhanced Features:[/dim]
• [green]Interactive progress tracking[/green] with time estimates
• [blue]Syntax-highlighted document previews[/blue] with diff views
• [yellow]Contextual help system[/yellow] based on workflow state
• [magenta]Visual architecture diagrams[/magenta] using Mermaid
• [cyan]Advanced search and filtering[/cyan] capabilities
• [red]Rich UI components[/red] for enhanced experience

Type [bold]help[/bold] for commands or [bold]exit[/bold] to quit.
        """

        panel = Panel(
            banner_text.strip(),
            title="[bold]Welcome[/bold]",
            border_style="blue",
            padding=(1, 2),
        )
        self.console.print(panel)

    def _get_current_context(self) -> dict[str, Any]:
        """Get current workflow context for help system.

        Returns:
            Dictionary containing current context information
        """
        context: dict[str, Any] = {
            "session_active": self.session_active,
            "command_history_count": len(self.command_history),
            "project_path": self.current_project_path,
        }

        if self.workflow_manager:
            try:
                current_phase = self.workflow_manager.get_current_phase()
                context["current_phase"] = current_phase

                # Get project state if available
                project_state = getattr(self.workflow_manager, "project_state", None)
                if project_state:
                    context["indexing_complete"] = project_state.indexing_complete
                    context["has_specification"] = (
                        project_state.specification is not None
                    )
                    context["has_design"] = project_state.design is not None
                    context["has_tasks"] = project_state.tasks is not None

            except Exception:  # noqa: S110
                # If we can't get workflow info, continue with basic context
                # This is intentional - we want to gracefully degrade
                pass

        return context

    def handle_user_input(self, input_text: str) -> str:  # noqa: PLR0911
        """Process user input and return response.

        Args:
            input_text: The user's input text

        Returns:
            Response message for the user
        """
        input_text = input_text.strip()

        if not input_text:
            return ""

        # Add to command history
        self.command_history.append(input_text)

        # Parse command and arguments
        parts = input_text.split()
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        try:
            # Handle enhanced CLI commands
            if command == "help":
                context = self._get_current_context()
                self.help_system.display_full_help(context)
                return ""
            elif command == "preview" and args:
                return self._handle_preview_command(args)
            elif command == "diff" and len(args) >= 2:
                return self._handle_diff_command(args)
            elif command == "tree":
                return self._handle_tree_command(args)
            elif command == "progress":
                return self._handle_progress_command()
            elif command == "history":
                return self._handle_history_command()
            elif command == "clear":
                self.console.clear()
                return "Screen cleared."
            elif command == "architecture":
                return self._handle_architecture_command()
            elif command == "workflow":
                return self._handle_workflow_diagram_command()
            elif command == "search" and args:
                return self._handle_search_command(args)
            elif command == "filter":
                return self._handle_filter_command(args)

            # Handle standard CLI commands
            elif command == "init":
                project_path = args[0] if args else str(Path.cwd())
                try:
                    self.init_command(project_path)
                    return f"Project initialized at: {project_path}"
                except Exception as e:
                    return f"Error initializing project: {e!s}"

            elif command == "status":
                return self._handle_status_command()

            elif command in ["run", "start"]:
                return self._handle_run_command()

            elif command == "phase" and args:
                return self._handle_phase_command(args[0])

            elif command == "approve":
                return "Approval functionality would be handled by workflow manager"

            elif command == "reject":
                return "Rejection functionality would be handled by workflow manager"

            elif command == "skip":
                return self._handle_skip_command()

            elif command == "cancel":
                return self._handle_cancel_command()

            else:
                # Show command suggestions for unknown commands
                context = self._get_current_context()
                self.help_system.show_command_suggestions(command, context)
                return ""

        except Exception as e:
            return f"Error executing command '{command}': {e!s}"

    def _handle_preview_command(self, args: list[str]) -> str:
        """Handle document preview command.

        Args:
            args: Command arguments

        Returns:
            Response message
        """
        doc_type = args[0].lower()

        if not self.workflow_manager:
            return "No active project. Use 'init [path]' to start."

        try:
            project_state = getattr(self.workflow_manager, "project_state", None)
            if not project_state:
                return "No project state available."

            content = None
            if doc_type == "specification" and project_state.specification:
                content = project_state.specification.content
            elif doc_type == "design" and project_state.design:
                content = project_state.design.content
            elif doc_type == "tasks" and project_state.tasks:
                content = str(project_state.tasks)  # Convert to string representation

            if content:
                self.document_previewer.show_document_preview(content, doc_type)
                return ""
            else:
                return f"No {doc_type} document available yet."

        except Exception as e:
            return f"Error showing preview: {e!s}"

    def _handle_diff_command(self, args: list[str]) -> str:  # noqa: ARG002
        """Handle diff command.

        Args:
            args: Command arguments

        Returns:
            Response message
        """
        # This would need to be implemented with actual document versioning
        return "Diff functionality requires document versioning (not yet implemented)"

    def _handle_tree_command(self, args: list[str]) -> str:
        """Handle tree command to show project structure.

        Args:
            args: Command arguments

        Returns:
            Response message
        """
        project_path = args[0] if args else self.current_project_path

        if not project_path:
            project_path = str(Path.cwd())

        if not Path(project_path).exists():
            return f"Path does not exist: {project_path}"

        self.document_previewer.show_file_tree(project_path)
        return ""

    def _handle_progress_command(self) -> str:
        """Handle progress command to show phase summary.

        Returns:
            Response message
        """
        if not self.workflow_manager:
            return "No active project."

        try:
            current_phase = self.workflow_manager.get_current_phase()
            completed_phases = []  # This would need to be tracked properly

            # For now, assume phases before current are completed
            completed_phases = [
                phase for phase in PhaseType if phase.value < current_phase.value
            ]

            self.progress_manager.show_phase_summary(completed_phases)
            return ""

        except Exception as e:
            return f"Error showing progress: {e!s}"

    def _handle_history_command(self) -> str:
        """Handle history command to show command history.

        Returns:
            Response message
        """
        if not self.command_history:
            return "No command history available."

        table = Table(
            title="Command History", show_header=True, header_style="bold cyan"
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Command", style="white")
        table.add_column("Time", style="dim")

        # Show last 10 commands
        recent_commands = self.command_history[-10:]
        for i, cmd in enumerate(recent_commands, 1):
            table.add_row(str(i), cmd, "Recent")  # Time tracking would need to be added

        self.console.print(table)
        return ""

    def _handle_status_command(self) -> str:
        """Handle status command.

        Returns:
            Status message
        """
        if not self.workflow_manager:
            return "No active project. Use 'init [path]' to start."

        try:
            current_phase = self.workflow_manager.get_current_phase()

            # Create status table
            table = Table(
                title="Project Status", show_header=True, header_style="bold magenta"
            )
            table.add_column("Property", style="cyan", no_wrap=True)
            table.add_column("Value", style="green")

            table.add_row("Current Phase", current_phase.value.title())
            table.add_row("Status", "Active")
            table.add_row("Last Updated", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            # Print table directly instead of capturing
            self.console.print(table)
            return ""  # Return empty string since we already printed

        except Exception as e:
            return f"Error getting status: {e!s}"

    def _handle_run_command(self) -> str:
        """Handle run/start command.

        Returns:
            Response message
        """
        if not self.workflow_manager:
            return "No active project. Use 'init [path]' to start."

        try:
            with self.progress_manager.progress:
                success = self.workflow_manager.execute_complete_workflow()

            if success:
                return "✅ Workflow completed successfully!"
            else:
                return "❌ Workflow execution failed. Check the logs for details."

        except Exception as e:
            return f"Error running workflow: {e!s}"

    def _handle_phase_command(self, phase_name: str) -> str:
        """Handle phase transition command.

        Args:
            phase_name: Name of the phase to transition to

        Returns:
            Response message
        """
        if not self.workflow_manager:
            return "No active project. Use 'init [path]' to start."

        try:
            # Try to match phase name case-insensitively
            phase_name_upper = phase_name.upper()
            phase = None
            for p in PhaseType:
                if p.value.upper() == phase_name_upper:
                    phase = p
                    break

            if phase is None:
                valid_phases = [phase.value for phase in PhaseType]
                return f"Invalid phase: {phase_name}. Valid phases: {', '.join(valid_phases)}"

            success = self.workflow_manager.transition_to_phase(phase)

            if success:
                return f"✅ Successfully transitioned to {phase_name.title()} phase"
            else:
                return f"❌ Failed to transition to {phase_name.title()} phase"

        except Exception as e:
            return f"Error transitioning to phase: {e!s}"

    def _handle_skip_command(self) -> str:
        """Handle skip command to skip current phase.

        Returns:
            Response message
        """
        if not self.workflow_manager:
            return "No active project. Use 'init [path]' to start."

        try:
            current_phase = self.workflow_manager.get_current_phase()

            # Warn user about skipping
            self.console.print(
                f"[yellow]⚠️  Warning: Skipping {current_phase.value} phase[/yellow]"
            )
            self.console.print(
                "[dim]Skipping phases may result in incomplete context "
                "for later phases.[/dim]"
            )

            from rich.prompt import Confirm

            if not Confirm.ask(
                "Are you sure you want to skip this phase?", default=False
            ):
                return "Skip cancelled."

            # Determine next phase
            phase_order = list(PhaseType)
            current_index = phase_order.index(current_phase)

            if current_index >= len(phase_order) - 1:
                return "Already at the last phase. Cannot skip."

            next_phase = phase_order[current_index + 1]

            # Mark current phase as skipped in state
            if (
                hasattr(self.workflow_manager, "current_project_state")
                and self.workflow_manager.current_project_state
            ):
                # Update phase status to indicate it was skipped
                self.console.print(
                    f"[yellow]Skipping to {next_phase.value} phase...[/yellow]"
                )

            # Transition to next phase
            success = self.workflow_manager.transition_to_phase(next_phase)

            if success:
                return f"✅ Skipped to {next_phase.value.title()} phase"
            return f"❌ Failed to skip to {next_phase.value.title()} phase"

        except Exception as e:
            return f"Error skipping phase: {e!s}"

    def _handle_cancel_command(self) -> str:
        """Handle cancel command to cancel current operation.

        Returns:
            Response message
        """
        if not self.workflow_manager:
            return "No active project. Use 'init [path]' to start."

        try:
            current_phase = self.workflow_manager.get_current_phase()

            self.console.print(
                f"[yellow]⚠️  Cancelling current operation in "
                f"{current_phase.value} phase[/yellow]"
            )

            from rich.prompt import Confirm

            if not Confirm.ask("Are you sure you want to cancel?", default=False):
                return "Cancel aborted."

            # Save current state
            if hasattr(self.workflow_manager, "state_manager") and hasattr(
                self.workflow_manager, "current_project_state"
            ):
                if self.workflow_manager.current_project_state:
                    self.workflow_manager.state_manager.save_project_state(
                        self.workflow_manager.current_project_state
                    )
                    self.console.print("[green]✓ Project state saved[/green]")

            return (
                "✅ Operation cancelled. You can resume with 'dev-agent resume' "
                "or continue with other commands."
            )

        except Exception as e:
            return f"Error cancelling operation: {e!s}"

    def _handle_architecture_command(self) -> str:
        """Handle architecture diagram command.

        Returns:
            Response message
        """
        if not self.workflow_manager:
            return "No active project. Use 'init [path]' to start."

        try:
            # Get project analysis data (this would come from the workflow manager)
            # For now, create a sample analysis
            project_analysis = {
                "components": [
                    {"name": "CLI", "type": "interface"},
                    {"name": "WorkflowManager", "type": "service"},
                    {"name": "IndexingEngine", "type": "service"},
                    {"name": "CodeGenerator", "type": "service"},
                    {"name": "ProjectState", "type": "model"},
                    {"name": "Document", "type": "model"},
                ],
                "dependencies": {
                    "CLI": ["WorkflowManager"],
                    "WorkflowManager": [
                        "IndexingEngine",
                        "CodeGenerator",
                        "ProjectState",
                    ],
                    "IndexingEngine": ["ProjectState"],
                    "CodeGenerator": ["Document"],
                },
            }

            self.visualization_engine.show_architecture_diagram(project_analysis)
            return ""

        except Exception as e:
            return f"Error generating architecture diagram: {e!s}"

    def _handle_workflow_diagram_command(self) -> str:
        """Handle workflow diagram command.

        Returns:
            Response message
        """
        try:
            phases = list(PhaseType)
            self.visualization_engine.show_workflow_diagram(phases)
            return ""

        except Exception as e:
            return f"Error generating workflow diagram: {e!s}"

    def _handle_search_command(self, args: list[str]) -> str:
        """Handle search command.

        Args:
            args: Command arguments [query, document_type]

        Returns:
            Response message
        """
        if len(args) < 2:
            return "Usage: search <query> <document_type>"

        query = args[0]
        document_type = args[1].lower()

        if not self.workflow_manager:
            return "No active project. Use 'init [path]' to start."

        try:
            project_state = getattr(self.workflow_manager, "project_state", None)
            if not project_state:
                return "No project state available."

            content = None
            if document_type == "specification" and project_state.specification:
                content = project_state.specification.content
            elif document_type == "design" and project_state.design:
                content = project_state.design.content
            elif document_type == "tasks" and project_state.tasks:
                content = str(project_state.tasks)

            if content:
                results = self.search_engine.search_in_document(content, query)
                self.search_engine.show_search_results(results, query, document_type)
                return ""
            else:
                return f"No {document_type} document available to search."

        except Exception as e:
            return f"Error searching document: {e!s}"

    def _handle_filter_command(self, args: list[str]) -> str:
        """Handle filter command for project files.

        Args:
            args: Command arguments

        Returns:
            Response message
        """
        if not self.current_project_path:
            return "No active project. Use 'init [path]' to start."

        try:
            # Parse filter arguments
            filters: dict[str, Any] = {}

            i = 0
            while i < len(args):
                if args[i] == "--ext" and i + 1 < len(args):
                    # Extensions filter: --ext .py,.js,.ts
                    extensions = args[i + 1].split(",")
                    filters["extensions"] = extensions
                    i += 2
                elif args[i] == "--size" and i + 1 < len(args):
                    # Size filter: --size 1MB
                    size_str = args[i + 1]
                    try:
                        if size_str.endswith("KB"):
                            max_size = int(size_str[:-2]) * 1024
                        elif size_str.endswith("MB"):
                            max_size = int(size_str[:-2]) * 1024 * 1024
                        else:
                            max_size = int(size_str)
                        filters["max_size"] = max_size
                    except ValueError:
                        return f"Invalid size format: {size_str}"
                    i += 2
                elif args[i] == "--name" and i + 1 < len(args):
                    # Name pattern filter: --name "test.*"
                    filters["name_pattern"] = args[i + 1]
                    i += 2
                elif args[i] == "--hidden":
                    # Include hidden files
                    filters["include_hidden"] = True
                    i += 1
                else:
                    return f"Unknown filter option: {args[i]}"

            if not filters:
                return "Usage: filter [--ext .py,.js] [--size 1MB] [--name pattern] [--hidden]"

            filtered_files = self.search_engine.filter_project_files(
                self.current_project_path, filters
            )
            self.search_engine.show_filtered_files(
                filtered_files, filters, self.current_project_path
            )
            return ""

        except Exception as e:
            return f"Error filtering files: {e!s}"

    def request_approval(self, document: str, document_type: str) -> bool:
        """Request user approval for a generated document.

        Args:
            document: The document content to approve
            document_type: Type of document (specification, design, tasks)

        Returns:
            True if approved, False if rejected
        """
        # Show document preview with syntax highlighting
        self.document_previewer.show_document_preview(
            document, document_type, title=f"Generated {document_type.title()}"
        )

        # Create approval prompt with enhanced styling
        self.console.print()
        self.console.print(
            Rule(f"[bold yellow]📋 {document_type.title()} Review[/bold yellow]")
        )

        return Confirm.ask(
            f"[bold cyan]Do you approve this {document_type}?[/bold cyan]",
            default=False,
        )

    def display_progress(self, phase: PhaseType, progress: float) -> None:
        """Display progress information for the current phase.

        Args:
            phase: The current phase
            progress: Progress as a float between 0.0 and 1.0
        """
        # Start phase progress if not already started
        if self.progress_manager.current_task is None:
            self.progress_manager.start_phase_progress(phase)

        # Update progress
        completed_steps = int(progress * 100)
        self.progress_manager.update_progress(completed_steps)

        # Complete phase if at 100%
        if progress >= 1.0:
            self.progress_manager.complete_phase(phase)

    def init_command(self, project_path: str) -> None:
        """Initialize a new project or resume an existing one.

        Args:
            project_path: Path to the project directory
        """
        if not Path(project_path).exists():
            raise ValueError(f"Project path does not exist: {project_path}")

        self.current_project_path = project_path

        # Show project structure
        self.document_previewer.show_file_tree(project_path)

        project_path_obj = Path(project_path)
        dev_agent_dir = project_path_obj / ".dev_agent"
        documents_dir = dev_agent_dir / "documents"
        index_dir = dev_agent_dir / "index"

        # Check if this is an existing project
        if documents_dir.exists() and index_dir.exists():
            self.display_message(
                "[green]📁 Found existing dev-agent project. Resuming...[/green]"
            )
            if self.workflow_manager:
                self.workflow_manager.resume_project(project_path)
        else:
            self.display_message(
                "[blue]🚀 Initializing new dev-agent project...[/blue]"
            )
            # Create .dev_agent directory structure
            dev_agent_dir.mkdir(parents=True, exist_ok=True)
            documents_dir.mkdir(parents=True, exist_ok=True)
            index_dir.mkdir(parents=True, exist_ok=True)

            if self.workflow_manager:
                self.workflow_manager.start_new_project(project_path)

    def display_message(self, message: str) -> None:
        """Display a message to the user.

        Args:
            message: The message to display
        """
        self.console.print(message)

    def get_user_input(self, prompt: str) -> str:
        """Get input from the user with a prompt.

        Args:
            prompt: The prompt to display

        Returns:
            The user's input as a string
        """
        return Prompt.ask(prompt)

    # Enhanced CLI methods (implementing optional interface methods)
    def show_document_preview(self, content: str, document_type: str) -> None:
        """Show document preview with syntax highlighting.

        Args:
            content: Document content to preview
            document_type: Type of document for syntax highlighting
        """
        self.document_previewer.show_document_preview(content, document_type)

    def show_diff_view(
        self, old_content: str, new_content: str, title: str = "Changes"
    ) -> None:
        """Show diff between two versions of content.

        Args:
            old_content: Original content
            new_content: Modified content
            title: Title for the diff view
        """
        self.document_previewer.show_diff_view(old_content, new_content, title)

    def get_contextual_help(self, context: dict[str, Any] | None = None) -> None:
        """Show contextual help based on current state.

        Args:
            context: Optional context dictionary
        """
        if context is None:
            context = self._get_current_context()
        self.help_system.show_contextual_help(context)
