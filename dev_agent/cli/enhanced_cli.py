"""Enhanced CLI with Rich UI components for improved user experience."""

from __future__ import annotations

import difflib
import os
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
from dev_agent.models.enums import PhaseType, TaskStatus

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
                    ("next", "Proceed to next phase (when current is complete)"),
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
            from dev_agent.config import ConfigManager
            from dev_agent.llm.embeddings import AzureEmbeddingClient
            from dev_agent.workflow.workflow_manager import (
                WorkflowManager,
            )

            # Initialize workflow manager (it will create its own embedding client)
            self.workflow_manager = WorkflowManager(self)
            
            # Auto-resume project if .dev_agent directory exists
            self._auto_resume_project()

    def _auto_resume_project(self) -> None:
        """Automatically resume project if .dev_agent directory exists."""
        try:
            from pathlib import Path
            import asyncio
            
            current_dir = Path.cwd()
            dev_agent_dir = current_dir / ".dev_agent"
            state_file = dev_agent_dir / "state.json"
            
            if dev_agent_dir.exists() and state_file.exists():
                self.console.print("[blue]Found existing dev-agent project. Resuming...[/blue]")
                
                # Resume the project using asyncio.run()
                try:
                    project_state = asyncio.run(self.workflow_manager.resume_project(str(current_dir)))
                    self.current_project_path = str(current_dir)
                    self.console.print(f"[green]✓ Resumed project in {project_state.current_phase.value} phase[/green]")
                except Exception as e:
                    self.console.print(f"[yellow]Warning: Could not resume project: {e}[/yellow]")
                    self.console.print("[dim]You can use 'init' to start a new project or check the project state.[/dim]")
        except Exception:
            # Silently fail - this is just a convenience feature
            pass

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
        # Get active provider information
        try:
            from ..config import ConfigManager

            config_manager = ConfigManager()
            active_provider = config_manager.get_llm_provider()
            provider_display = active_provider.value.replace("_", " ").title()
            provider_info = f"[dim]Active AI Provider: {provider_display}[/dim]"
        except Exception:
            provider_info = "[dim]Active AI Provider: Not Configured[/dim]"

        banner_text = f"""
[bold blue]🤖 dev-agent[/bold blue] - AI-powered development workflow assistant

{provider_info}

[dim]Enhanced Features:[/dim]
• [green]Interactive progress tracking[/green] with time estimates
• [blue]Syntax-highlighted document previews[/blue] with diff views
• [yellow]Contextual help system[/yellow] based on workflow state
• [magenta]Visual architecture diagrams[/magenta] using Mermaid
• [cyan]Advanced search and filtering[/cyan] capabilities
• [red]Rich UI components[/red] for enhanced experience

[dim]Supported Providers:[/dim] Azure OpenAI, Google Gemini

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
                project_state = getattr(self.workflow_manager, "current_project_state", None)
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
                return self._handle_approve_command()

            elif command == "reject":
                return self._handle_reject_command()

            elif command == "skip":
                return self._handle_skip_command()

            elif command in ("next", "proceed", "continue"):
                return self._handle_next_command()

            elif command == "cancel":
                return self._handle_cancel_command()

            elif command == "generate":
                return self._handle_generate_command(args)

            elif command == "tasks":
                return self._handle_tasks_command(args)

            elif command == "setup":
                return self._handle_setup_command(args)

            elif command == "validate":
                return self._handle_validate_command(args)

            elif command == "examples":
                return self._handle_examples_command()

            elif command == "cost-report":
                return self._handle_cost_report_command()

            elif command == "index":
                return self._handle_index_command(args)

            elif command == "analyze":
                return self._handle_analyze_command(args)

            elif command == "spec":
                return self._handle_spec_command(args)

            elif command == "requirements":
                return self._handle_requirements_command(args)

            elif command == "design":
                return self._handle_design_command(args)

            elif command == "test":
                return self._handle_test_command(args)

            elif command == "review":
                return self._handle_review_command(args)

            elif command == "complete":
                return self._handle_complete_command(args)

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
            project_state = getattr(self.workflow_manager, "current_project_state", None)
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

            # Get project state to determine actual status
            project_state = None
            if hasattr(self.workflow_manager, "current_project_state"):
                project_state = self.workflow_manager.current_project_state
            elif hasattr(self.workflow_manager, "state_manager"):
                project_state = self.workflow_manager.state_manager.load_project_state()

            # Determine phase status
            phase_status = "Active"
            if project_state:
                if current_phase == PhaseType.INDEXING:
                    phase_status = (
                        "Completed" if project_state.indexing_complete else "Active"
                    )
                elif current_phase == PhaseType.SPECIFICATION:
                    phase_status = (
                        "Completed"
                        if (
                            project_state.specification
                            and project_state.specification.approved
                        )
                        else "Active"
                    )
                elif current_phase == PhaseType.DESIGN:
                    phase_status = (
                        "Completed"
                        if (project_state.design and project_state.design.approved)
                        else "Active"
                    )
                elif current_phase == PhaseType.IMPLEMENTATION:
                    # Check if all tasks are completed
                    if project_state.implementation_progress:
                        completed_tasks = sum(
                            1
                            for status in project_state.implementation_progress.values()
                            if status == TaskStatus.COMPLETED
                        )
                        total_tasks = len(project_state.implementation_progress)
                        if completed_tasks == total_tasks and total_tasks > 0:
                            phase_status = "Completed"
                        else:
                            phase_status = (
                                f"Active ({completed_tasks}/{total_tasks} tasks)"
                            )
                    else:
                        phase_status = "Active"

            # Create status table
            table = Table(
                title="Project Status", show_header=True, header_style="bold magenta"
            )
            table.add_column("Property", style="cyan", no_wrap=True)
            table.add_column("Value", style="green")

            table.add_row("Current Phase", current_phase.value.title())

            # Color code the status
            if phase_status == "Completed":
                status_display = f"[green]{phase_status}[/green]"
            elif "Active" in phase_status:
                status_display = f"[yellow]{phase_status}[/yellow]"
            else:
                status_display = phase_status

            table.add_row("Status", status_display)
            table.add_row("Last Updated", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            # Print table directly instead of capturing
            self.console.print(table)
            return ""  # Return empty string since we already printed

        except Exception as e:
            return f"Error getting status: {e!s}"

    def _handle_run_command(self) -> str:
        """Handle run/start command.

        Note: This method uses asyncio.run() to execute the async workflow.
        This is safe because enhanced_cli methods are called synchronously
        from the main CLI loop.

        Returns:
            Response message
        """
        if not self.workflow_manager:
            return "No active project. Use 'init [path]' to start."

        try:
            import asyncio

            with self.progress_manager.progress:
                # Execute async workflow using asyncio.run()
                # This creates a new event loop for the async operation
                success = asyncio.run(self.workflow_manager.execute_complete_workflow())

            if success:
                return "✅ Workflow completed successfully!"
            else:
                return "❌ Workflow execution failed. Check the logs for details."

        except Exception as e:
            return f"Error running workflow: {e!s}"

    def _handle_phase_command(self, phase_name: str) -> str:
        """Handle phase transition command.

        Note: This method uses asyncio.run() to execute the async phase transition.
        This is safe because enhanced_cli methods are called synchronously
        from the main CLI loop.

        Args:
            phase_name: Name of the phase to transition to

        Returns:
            Response message
        """
        if not self.workflow_manager:
            return "No active project. Use 'init [path]' to start."

        try:
            import asyncio

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

            # Execute async phase transition using asyncio.run()
            # This creates a new event loop for the async operation
            success = asyncio.run(self.workflow_manager.transition_to_phase(phase))

            if success:
                return f"✅ Successfully transitioned to {phase_name.title()} phase"
            else:
                return f"❌ Failed to transition to {phase_name.title()} phase"

        except Exception as e:
            return f"Error transitioning to phase: {e!s}"

    def _handle_next_command(self) -> str:
        """Handle next/proceed command to move to next phase when current is complete.

        Returns:
            Response message
        """
        if not self.workflow_manager:
            return "No active project. Use 'init [path]' to start."

        try:
            current_phase = self.workflow_manager.get_current_phase()

            # Get project state to check if current phase is complete
            project_state = None
            if hasattr(self.workflow_manager, "current_project_state"):
                project_state = self.workflow_manager.current_project_state
            elif hasattr(self.workflow_manager, "state_manager"):
                project_state = self.workflow_manager.state_manager.load_project_state()

            if not project_state:
                return "❌ No project state available"

            # Import enums at the top
            from dev_agent.models.enums import PhaseType

            # Check if current phase is complete
            phase_complete = False
            if current_phase == PhaseType.INDEXING:
                phase_complete = project_state.indexing_complete
            elif current_phase == PhaseType.SPECIFICATION:
                phase_complete = (
                    project_state.specification and project_state.specification.approved
                )
            elif current_phase == PhaseType.DESIGN:
                phase_complete = project_state.design and project_state.design.approved
            elif current_phase == PhaseType.IMPLEMENTATION:
                if project_state.implementation_progress:
                    total_tasks = len(project_state.implementation_progress)
                    completed_tasks = sum(
                        1
                        for status in project_state.implementation_progress.values()
                        if status == TaskStatus.COMPLETED
                    )
                    phase_complete = completed_tasks == total_tasks and total_tasks > 0

            if not phase_complete:
                return f"❌ Cannot proceed: {current_phase.value.title()} phase is not yet complete"

            # Determine next phase

            phase_order = list(PhaseType)
            current_index = phase_order.index(current_phase)

            if current_index >= len(phase_order) - 1:
                return "✅ Already at the last phase. Workflow complete!"

            next_phase = phase_order[current_index + 1]

            self.console.print(
                f"[green]Proceeding to {next_phase.value} phase...[/green]"
            )

            # Transition to next phase using asyncio.run()
            import asyncio

            success = asyncio.run(self.workflow_manager.transition_to_phase(next_phase))

            if success:
                return f"✅ Successfully moved to {next_phase.value.title()} phase"
            return f"❌ Failed to move to {next_phase.value.title()} phase"

        except Exception as e:
            return f"Error proceeding to next phase: {e!s}"

    def _handle_approve_command(self) -> str:
        """Handle approve command for current phase documents.

        Returns:
            Response message
        """
        if not self.workflow_manager:
            return "No active project. Use 'init [path]' to start."

        try:
            current_phase = self.workflow_manager.get_current_phase()
            
            if current_phase == PhaseType.SPECIFICATION:
                return "✅ Specification approval is handled during the specification generation process.\nUse 'next' to proceed once approved."
            elif current_phase == PhaseType.DESIGN:
                return "✅ Design approval is handled during the design generation process.\nUse 'next' to proceed once approved."
            else:
                return f"❌ Approval not applicable for {current_phase.value.title()} phase"
                
        except Exception as e:
            return f"Error handling approval: {e!s}"

    def _handle_reject_command(self) -> str:
        """Handle reject command for current phase documents.

        Returns:
            Response message
        """
        if not self.workflow_manager:
            return "No active project. Use 'init [path]' to start."

        try:
            current_phase = self.workflow_manager.get_current_phase()
            
            if current_phase == PhaseType.SPECIFICATION:
                return "❌ To regenerate specification, you'll need to restart the specification phase.\nUse 'skip' to move to next phase or restart the workflow."
            elif current_phase == PhaseType.DESIGN:
                return "❌ To regenerate design, you'll need to restart the design phase.\nUse 'skip' to move to next phase or restart the workflow."
            else:
                return f"❌ Rejection not applicable for {current_phase.value.title()} phase"
                
        except Exception as e:
            return f"Error handling rejection: {e!s}"

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

            # Transition to next phase using asyncio.run()
            import asyncio

            success = asyncio.run(self.workflow_manager.transition_to_phase(next_phase))

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
            project_state = getattr(self.workflow_manager, "current_project_state", None)
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

    def _handle_generate_command(self, args: list[str]) -> str:
        """Handle generate command for code generation.

        Args:
            args: Command arguments

        Returns:
            Response message
        """
        if not self.workflow_manager:
            return "No active project. Use 'init [path]' to start."

        try:
            # Check if we're in implementation phase
            current_phase = self.workflow_manager.get_current_phase()
            if current_phase != PhaseType.IMPLEMENTATION:
                return f"Generate command is only available in implementation phase. Current phase: {current_phase.value}"

            project_state = getattr(self.workflow_manager, "current_project_state", None)
            if not project_state or not project_state.tasks:
                return "No tasks available. Generate tasks from design first."

            # Parse arguments
            task_id = None
            file_path = None
            force = False
            
            i = 0
            while i < len(args):
                if args[i] == "--task-id" and i + 1 < len(args):
                    task_id = args[i + 1]
                    i += 2
                elif args[i] == "--file" and i + 1 < len(args):
                    file_path = args[i + 1]
                    i += 2
                elif args[i] == "--force":
                    force = True
                    i += 1
                else:
                    i += 1

            # Import required modules
            import asyncio
            from ..generation.python_code_generator import PythonCodeGenerator
            from ..models.context import CodeContext
            from ..models.enums import TaskStatus

            if task_id:
                # Find the specific task
                target_task = None
                for task in project_state.tasks.tasks:
                    if task.id == task_id:
                        target_task = task
                        break
                
                if not target_task:
                    return f"Task '{task_id}' not found. Use 'tasks' to see available tasks."
                
                if target_task.status == TaskStatus.COMPLETED and not force:
                    return f"Task '{task_id}' is already completed. Use --force to regenerate."

                self.console.print(f"[cyan]Generating code for task: {task_id}[/cyan]")
                
                # Generate code for specific task
                result = asyncio.run(self._generate_code_for_task(target_task, project_state))
                return result

            elif file_path:
                self.console.print(f"[cyan]Generating file: {file_path}[/cyan]")
                
                # Find tasks that would generate this file
                matching_tasks = []
                for task in project_state.tasks.tasks:
                    if file_path in task.description.lower() or any(file_path in pattern for pattern in getattr(task, 'file_patterns', [])):
                        matching_tasks.append(task)
                
                if not matching_tasks:
                    return f"No tasks found that would generate '{file_path}'. Use 'tasks' to see available tasks."
                
                # Generate code for all matching tasks
                results = []
                for task in matching_tasks:
                    if task.status != TaskStatus.COMPLETED or force:
                        result = asyncio.run(self._generate_code_for_task(task, project_state))
                        results.append(f"Task {task.id}: {result}")
                
                return "\n".join(results) if results else f"All tasks for '{file_path}' are already completed."

            else:
                # Generate code for next available task
                next_task = None
                for task in project_state.tasks.tasks:
                    if task.status == TaskStatus.NOT_STARTED:
                        next_task = task
                        break
                
                if not next_task:
                    return "No pending tasks found. All tasks are completed or in progress."
                
                self.console.print(f"[cyan]Generating code for next task: {next_task.id} - {next_task.title}[/cyan]")
                
                result = asyncio.run(self._generate_code_for_task(next_task, project_state))
                return result

        except Exception as e:
            return f"Error generating code: {e!s}"

    async def _generate_code_for_task(self, task, project_state):
        """Generate code for a specific task.
        
        Args:
            task: The task to generate code for
            project_state: Current project state
            
        Returns:
            Result message
        """
        try:
            from ..generation.python_code_generator import PythonCodeGenerator
            from ..models.analysis import CodeContext
            from ..models.enums import TaskStatus
            from ..indexing.indexing_engine import IndexingEngine
            from ..analysis.codebase_analyzer import CodebaseAnalyzer
            from pathlib import Path

            # Initialize indexing engine and codebase analyzer
            indexing_engine = IndexingEngine(
                embedding_client=self.workflow_manager.embedding_client,
                project_path=Path(project_state.project_path)
            )
            codebase_analyzer = CodebaseAnalyzer(indexing_engine)

            # Create code context using the analyzer
            context = codebase_analyzer.get_context_for_task(task)

            # Initialize code generator with analyzer
            generator = PythonCodeGenerator(
                codebase_analyzer=codebase_analyzer,
                llm_client=self.workflow_manager.llm_client,
                cost_tracker=self.workflow_manager.cost_tracker
            )
            
            # Generate code
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                gen_task = progress.add_task(f"Generating code for {task.title}...", total=None)
                
                generated_code = generator.generate_code_from_task(task, context)
                
                progress.update(gen_task, description="[green]✓ Code generated successfully")

            # Display generated code
            if generated_code and generated_code.code:
                self.console.print("\n[bold green]Generated Code:[/bold green]")
                
                # Show syntax highlighted code
                from rich.syntax import Syntax
                syntax = Syntax(
                    generated_code.code, 
                    "python", 
                    theme="monokai", 
                    line_numbers=True,
                    word_wrap=True
                )
                self.console.print(syntax)
                
                # Ask for approval to save
                from rich.prompt import Confirm
                if Confirm.ask(f"\nSave generated code to {generated_code.file_path}?", default=True):
                    # Save the file
                    file_path = Path(project_state.project_path) / generated_code.file_path
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(generated_code.code)
                    
                    # Update task status
                    task.status = TaskStatus.COMPLETED
                    
                    # Save project state
                    if hasattr(self.workflow_manager, 'state_manager'):
                        await self.workflow_manager.state_manager.save_project_state(project_state)
                    
                    return f"✓ Code generated and saved to {generated_code.file_path}"
                else:
                    return "Code generation completed but not saved."
            else:
                return "Code generation failed - no code produced."

        except Exception as e:
            return f"Error generating code for task: {e!s}"

    def _handle_tasks_command(self, args: list[str]) -> str:
        """Handle tasks command to list and manage implementation tasks.

        Args:
            args: Command arguments

        Returns:
            Response message
        """
        if not self.workflow_manager:
            return "No active project. Use 'init [path]' to start."

        try:
            project_state = getattr(self.workflow_manager, "current_project_state", None)
            if not project_state:
                return "No project state available."

            if not project_state.tasks:
                return "No tasks available. Generate tasks from design first."

            # Parse command arguments
            show_details = "--details" in args
            filter_status = None
            task_id = None
            
            i = 0
            while i < len(args):
                if args[i] == "--status" and i + 1 < len(args):
                    filter_status = args[i + 1].lower()
                    i += 2
                elif args[i] == "--id" and i + 1 < len(args):
                    task_id = args[i + 1]
                    i += 2
                elif args[i] == "--details":
                    show_details = True
                    i += 1
                else:
                    i += 1

            # If specific task ID requested, show task details
            if task_id:
                target_task = None
                for task in project_state.tasks.tasks:
                    if task.id == task_id:
                        target_task = task
                        break
                
                if not target_task:
                    return f"Task '{task_id}' not found."
                
                # Display detailed task information
                task_panel = Panel(
                    f"[bold]Title:[/bold] {target_task.title}\n"
                    f"[bold]Description:[/bold] {target_task.description}\n"
                    f"[bold]Status:[/bold] {target_task.status.value}\n"
                    f"[bold]Language:[/bold] {getattr(target_task, 'target_language', 'python')}\n"
                    f"[bold]Requirements:[/bold] {', '.join(target_task.requirements_refs) if target_task.requirements_refs else 'None'}\n"
                    f"[bold]Subtasks:[/bold] {len(target_task.subtasks)} subtasks" +
                    (f"\n[bold]Implementation Notes:[/bold] {target_task.implementation_notes}" if getattr(target_task, 'implementation_notes') else ""),
                    title=f"[bold cyan]Task {task_id} Details[/bold cyan]",
                    border_style="cyan"
                )
                self.console.print(task_panel)
                return ""

            # Filter tasks by status if specified
            tasks_to_show = project_state.tasks.tasks
            if filter_status:
                from ..models.enums import TaskStatus
                try:
                    status_enum = TaskStatus(filter_status)
                    tasks_to_show = [task for task in tasks_to_show if task.status == status_enum]
                except ValueError:
                    return f"Invalid status '{filter_status}'. Valid statuses: not_started, in_progress, completed, failed, blocked"

            if not tasks_to_show:
                status_msg = f" with status '{filter_status}'" if filter_status else ""
                return f"No tasks found{status_msg}."

            # Display tasks summary
            self.console.print(f"\n[bold cyan]📋 Implementation Tasks ({len(tasks_to_show)} tasks)[/bold cyan]")
            
            # Count tasks by status
            from collections import Counter
            status_counts = Counter(task.status.value for task in project_state.tasks.tasks)
            
            summary_table = Table(show_header=False, box=None, padding=(0, 2))
            summary_table.add_column("Status", style="cyan")
            summary_table.add_column("Count", style="white")
            
            for status, count in status_counts.items():
                status_style = {
                    "completed": "green",
                    "in_progress": "yellow", 
                    "not_started": "blue",
                    "failed": "red",
                    "blocked": "magenta"
                }.get(status, "white")
                
                summary_table.add_row(
                    f"[{status_style}]{status.replace('_', ' ').title()}[/{status_style}]",
                    str(count)
                )
            
            self.console.print(summary_table)
            self.console.print()

            # Display main tasks table
            tasks_table = Table(
                show_header=True, 
                header_style="bold cyan",
                title="Task List" if not filter_status else f"Tasks - {filter_status.replace('_', ' ').title()}"
            )
            tasks_table.add_column("ID", style="cyan", width=10)
            tasks_table.add_column("Title", style="white", width=35)
            tasks_table.add_column("Status", style="white", width=12)
            tasks_table.add_column("Language", style="dim", width=10)
            
            if show_details:
                tasks_table.add_column("Description", style="dim", width=40)

            for task in tasks_to_show:
                status_style = {
                    "completed": "green",
                    "in_progress": "yellow",
                    "not_started": "blue", 
                    "failed": "red",
                    "blocked": "magenta"
                }.get(task.status.value, "white")
                
                status_display = f"[{status_style}]{task.status.value.replace('_', ' ').title()}[/{status_style}]"
                
                row_data = [
                    task.id,
                    task.title[:32] + "..." if len(task.title) > 35 else task.title,
                    status_display,
                    getattr(task, 'target_language', 'python')
                ]
                
                if show_details:
                    desc = task.description[:37] + "..." if len(task.description) > 40 else task.description
                    row_data.append(desc)
                
                tasks_table.add_row(*row_data)

            self.console.print(tasks_table)
            
            # Show helpful commands
            self.console.print("\n[dim]Commands:[/dim]")
            self.console.print("  [cyan]tasks --id <task_id>[/cyan]     Show task details")
            self.console.print("  [cyan]tasks --status completed[/cyan] Filter by status")
            self.console.print("  [cyan]tasks --details[/cyan]          Show descriptions")
            self.console.print("  [cyan]generate --task-id <id>[/cyan]  Generate code for task")
            
            return ""

        except Exception as e:
            return f"Error displaying tasks: {e!s}"

    def _handle_setup_command(self, args: list[str]) -> str:
        """Handle setup command for configuration.

        Args:
            args: Command arguments

        Returns:
            Response message
        """
        try:
            # Check for --status flag
            if "--status" in args:
                from ..config import ConfigManager
                config_manager = ConfigManager()
                config = config_manager.get_config()
                
                # Display configuration status
                status_table = Table(
                    title="Configuration Status",
                    show_header=True,
                    header_style="bold cyan"
                )
                status_table.add_column("Component", style="cyan", width=20)
                status_table.add_column("Status", style="white", width=15)
                status_table.add_column("Details", style="dim", width=40)

                # Check Azure OpenAI
                if config.azure_openai:
                    status_table.add_row(
                        "Azure OpenAI",
                        "[green]✓ Configured[/green]",
                        f"Endpoint: {config.azure_openai.endpoint}"
                    )
                else:
                    status_table.add_row(
                        "Azure OpenAI",
                        "[red]✗ Not configured[/red]",
                        "Run 'dev-agent azure configure'"
                    )

                # Check Gemini
                gemini_key = os.getenv("GEMINI_API_KEY")
                if gemini_key:
                    status_table.add_row(
                        "Google Gemini",
                        "[green]✓ Configured[/green]",
                        "API key found in environment"
                    )
                else:
                    status_table.add_row(
                        "Google Gemini",
                        "[red]✗ Not configured[/red]",
                        "Set GEMINI_API_KEY environment variable"
                    )

                self.console.print(status_table)
                return ""
            else:
                return "Interactive setup wizard not yet implemented. Use 'setup --status' to check configuration."

        except Exception as e:
            return f"Error in setup: {e!s}"

    def _handle_validate_command(self, args: list[str]) -> str:
        """Handle validate command for project validation.

        Args:
            args: Command arguments

        Returns:
            Response message
        """
        if not self.workflow_manager:
            return "No active project. Use 'init [path]' to start."

        try:
            # Validate current project state
            project_state = getattr(self.workflow_manager, "current_project_state", None)
            if not project_state:
                return "No project state to validate."

            validation_results = []
            
            # Validate based on current phase
            current_phase = self.workflow_manager.get_current_phase()
            
            if current_phase == PhaseType.INDEXING:
                if project_state.indexing_complete:
                    validation_results.append(("Indexing", "✓", "Complete"))
                else:
                    validation_results.append(("Indexing", "✗", "Not complete"))
            
            elif current_phase == PhaseType.SPECIFICATION:
                if project_state.specification:
                    validation_results.append(("Specification", "✓", "Generated"))
                else:
                    validation_results.append(("Specification", "✗", "Missing"))
            
            elif current_phase == PhaseType.DESIGN:
                if project_state.design:
                    validation_results.append(("Design", "✓", "Generated"))
                else:
                    validation_results.append(("Design", "✗", "Missing"))
            
            elif current_phase == PhaseType.IMPLEMENTATION:
                if project_state.tasks:
                    validation_results.append(("Tasks", "✓", f"{len(project_state.tasks.tasks)} tasks"))
                else:
                    validation_results.append(("Tasks", "✗", "No tasks generated"))

            # Display validation results
            validation_table = Table(
                title="Project Validation",
                show_header=True,
                header_style="bold cyan"
            )
            validation_table.add_column("Component", style="cyan", width=20)
            validation_table.add_column("Status", style="white", width=10)
            validation_table.add_column("Details", style="dim", width=30)

            for component, status, details in validation_results:
                status_style = "green" if status == "✓" else "red"
                validation_table.add_row(
                    component,
                    f"[{status_style}]{status}[/{status_style}]",
                    details
                )

            self.console.print(validation_table)
            return ""

        except Exception as e:
            return f"Error validating project: {e!s}"

    def _handle_examples_command(self) -> str:
        """Handle examples command to show usage examples.

        Returns:
            Response message
        """
        examples_text = """
[bold cyan]dev-agent Usage Examples[/bold cyan]

[bold]1. Initialize a new project:[/bold]
  dev-agent init
  dev-agent init /path/to/project --provider azure

[bold]2. Resume existing project:[/bold]
  dev-agent resume
  dev-agent resume /path/to/project

[bold]3. Interactive workflow:[/bold]
  dev-agent                    # Start interactive mode
  help                         # Show available commands
  status                       # Check project status
  next                         # Proceed to next phase

[bold]4. Implementation phase:[/bold]
  tasks                        # List implementation tasks
  generate                     # Generate code for current task
  generate --task-id 1.1       # Generate specific task
  test                         # Run tests
  review                       # Review implementation

[bold]5. Document management:[/bold]
  preview specification        # Preview specification document
  preview design              # Preview design document
  search "auth" specification # Search in documents

[bold]6. Configuration:[/bold]
  setup --status              # Check configuration
  validate                    # Validate project state
  cost-report                 # Show API usage costs
        """
        
        panel = Panel(
            examples_text.strip(),
            title="[bold]Usage Examples[/bold]",
            border_style="cyan",
            padding=(1, 2),
        )
        self.console.print(panel)
        return ""

    def _handle_cost_report_command(self) -> str:
        """Handle cost-report command to show API usage costs.

        Returns:
            Response message
        """
        if not self.workflow_manager:
            return "No active project. Use 'init [path]' to start."

        try:
            cost_tracker = getattr(self.workflow_manager, "cost_tracker", None)
            if not cost_tracker:
                return "No cost tracking available."

            # Get cost report
            report = cost_tracker.get_report()
            
            # Display cost information
            cost_table = Table(
                title="API Usage & Cost Report",
                show_header=True,
                header_style="bold cyan"
            )
            cost_table.add_column("Metric", style="cyan", width=25)
            cost_table.add_column("Value", style="white", width=15)
            cost_table.add_column("Cost", style="green", width=15)

            cost_table.add_row(
                "Prompt Tokens",
                f"{report.get('prompt_tokens', 0):,}",
                f"${report.get('prompt_cost', 0):.4f}"
            )
            cost_table.add_row(
                "Completion Tokens", 
                f"{report.get('completion_tokens', 0):,}",
                f"${report.get('completion_cost', 0):.4f}"
            )
            cost_table.add_row(
                "Embedding Tokens",
                f"{report.get('embedding_tokens', 0):,}",
                f"${report.get('embedding_cost', 0):.4f}"
            )
            cost_table.add_row(
                "[bold]Total",
                f"[bold]{report.get('total_tokens', 0):,}",
                f"[bold green]${report.get('total_cost', 0):.4f}"
            )

            self.console.print(cost_table)
            return ""

        except Exception as e:
            return f"Error generating cost report: {e!s}"

    def _handle_index_command(self, args: list[str]) -> str:
        """Handle index command for codebase indexing.

        Args:
            args: Command arguments

        Returns:
            Response message
        """
        if not self.workflow_manager:
            return "No active project. Use 'init [path]' to start."

        try:
            # Check if already indexed
            project_state = getattr(self.workflow_manager, "current_project_state", None)
            if project_state and project_state.indexing_complete:
                if "--force" not in args:
                    return "Codebase already indexed. Use 'index --force' to re-index."

            self.console.print("[cyan]Starting codebase indexing...[/cyan]")
            # TODO: Implement indexing trigger
            return "Indexing functionality needs to be implemented"

        except Exception as e:
            return f"Error indexing codebase: {e!s}"

    def _handle_analyze_command(self, args: list[str]) -> str:
        """Handle analyze command for codebase analysis.

        Args:
            args: Command arguments

        Returns:
            Response message
        """
        if not self.workflow_manager:
            return "No active project. Use 'init [path]' to start."

        try:
            # TODO: Implement codebase analysis
            return "Codebase analysis functionality needs to be implemented"

        except Exception as e:
            return f"Error analyzing codebase: {e!s}"

    def _handle_spec_command(self, args: list[str]) -> str:
        """Handle spec command for specification generation.

        Args:
            args: Command arguments

        Returns:
            Response message
        """
        if not self.workflow_manager:
            return "No active project. Use 'init [path]' to start."

        try:
            current_phase = self.workflow_manager.get_current_phase()
            if current_phase != PhaseType.SPECIFICATION:
                return f"Specification generation is only available in specification phase. Current phase: {current_phase.value}"

            # TODO: Implement specification generation
            return "Specification generation functionality needs to be implemented"

        except Exception as e:
            return f"Error generating specification: {e!s}"

    def _handle_requirements_command(self, args: list[str]) -> str:
        """Handle requirements command (alias for spec).

        Args:
            args: Command arguments

        Returns:
            Response message
        """
        return self._handle_spec_command(args)

    def _handle_design_command(self, args: list[str]) -> str:
        """Handle design command for design generation.

        Args:
            args: Command arguments

        Returns:
            Response message
        """
        if not self.workflow_manager:
            return "No active project. Use 'init [path]' to start."

        try:
            current_phase = self.workflow_manager.get_current_phase()
            if current_phase != PhaseType.DESIGN:
                return f"Design generation is only available in design phase. Current phase: {current_phase.value}"

            # TODO: Implement design generation
            return "Design generation functionality needs to be implemented"

        except Exception as e:
            return f"Error generating design: {e!s}"

    def _handle_test_command(self, args: list[str]) -> str:
        """Handle test command for running tests.

        Args:
            args: Command arguments

        Returns:
            Response message
        """
        if not self.workflow_manager:
            return "No active project. Use 'init [path]' to start."

        try:
            # Parse test arguments
            coverage = "--coverage" in args
            pattern = None
            
            for i, arg in enumerate(args):
                if arg == "--pattern" and i + 1 < len(args):
                    pattern = args[i + 1]
                    break

            self.console.print("[cyan]Running tests...[/cyan]")
            
            if coverage:
                self.console.print("[dim]Generating coverage report...[/dim]")
            
            if pattern:
                self.console.print(f"[dim]Using pattern: {pattern}[/dim]")

            # TODO: Implement test execution
            return "Test execution functionality needs to be implemented"

        except Exception as e:
            return f"Error running tests: {e!s}"

    def _handle_review_command(self, args: list[str]) -> str:
        """Handle review command for code review.

        Args:
            args: Command arguments

        Returns:
            Response message
        """
        if not self.workflow_manager:
            return "No active project. Use 'init [path]' to start."

        try:
            project_state = getattr(self.workflow_manager, "current_project_state", None)
            if not project_state:
                return "No project state available."

            # Parse arguments
            show_files = "--files" in args
            show_progress = "--progress" in args
            task_id = None
            
            i = 0
            while i < len(args):
                if args[i] == "--task-id" and i + 1 < len(args):
                    task_id = args[i + 1]
                    i += 2
                elif args[i] in ["--files", "--progress"]:
                    i += 1
                else:
                    i += 1

            # If no specific arguments, show overall review
            if not any([show_files, show_progress, task_id]):
                return self._show_implementation_review(project_state)
            
            # Show specific reviews based on arguments
            if task_id:
                return self._review_specific_task(project_state, task_id)
            elif show_files:
                return self._review_generated_files(project_state)
            elif show_progress:
                return self._review_progress(project_state)
            
            return ""

        except Exception as e:
            return f"Error reviewing code: {e!s}"

    def _show_implementation_review(self, project_state) -> str:
        """Show overall implementation review.
        
        Args:
            project_state: Current project state
            
        Returns:
            Review summary
        """
        if not project_state.tasks:
            return "No tasks available to review."

        # Calculate progress statistics
        from ..models.enums import TaskStatus
        total_tasks = len(project_state.tasks.tasks)
        completed_tasks = sum(1 for task in project_state.tasks.tasks if task.status == TaskStatus.COMPLETED)
        in_progress_tasks = sum(1 for task in project_state.tasks.tasks if task.status == TaskStatus.IN_PROGRESS)
        failed_tasks = sum(1 for task in project_state.tasks.tasks if task.status == TaskStatus.FAILED)
        
        progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Create review summary
        review_content = f"""
[bold]Implementation Progress Review[/bold]

[bold cyan]📊 Progress Overview[/bold cyan]
• Total Tasks: {total_tasks}
• Completed: [green]{completed_tasks}[/green] ({progress_percentage:.1f}%)
• In Progress: [yellow]{in_progress_tasks}[/yellow]
• Failed: [red]{failed_tasks}[/red]
• Remaining: [blue]{total_tasks - completed_tasks - in_progress_tasks - failed_tasks}[/blue]

[bold cyan]🎯 Status Summary[/bold cyan]
"""

        if progress_percentage >= 100:
            review_content += "✅ [bold green]All tasks completed![/bold green] Ready for final testing.\n"
        elif progress_percentage >= 75:
            review_content += "🚀 [bold yellow]Nearly complete![/bold yellow] Most tasks are done.\n"
        elif progress_percentage >= 50:
            review_content += "⚡ [bold blue]Good progress![/bold blue] Halfway through implementation.\n"
        elif progress_percentage >= 25:
            review_content += "🔄 [bold cyan]Getting started![/bold cyan] Some tasks completed.\n"
        else:
            review_content += "🏁 [bold white]Just beginning![/bold white] Most tasks still pending.\n"

        # Show recent activity
        completed_tasks_list = [task for task in project_state.tasks.tasks if task.status == TaskStatus.COMPLETED]
        if completed_tasks_list:
            review_content += f"\n[bold cyan]✅ Recently Completed[/bold cyan]\n"
            for task in completed_tasks_list[-3:]:  # Show last 3 completed
                review_content += f"• {task.id}: {task.title}\n"

        # Show next tasks
        pending_tasks = [task for task in project_state.tasks.tasks if task.status == TaskStatus.NOT_STARTED]
        if pending_tasks:
            review_content += f"\n[bold cyan]📋 Next Up[/bold cyan]\n"
            for task in pending_tasks[:3]:  # Show next 3 tasks
                review_content += f"• {task.id}: {task.title}\n"

        # Show any failed tasks
        failed_tasks_list = [task for task in project_state.tasks.tasks if task.status == TaskStatus.FAILED]
        if failed_tasks_list:
            review_content += f"\n[bold red]❌ Failed Tasks (Need Attention)[/bold red]\n"
            for task in failed_tasks_list:
                review_content += f"• {task.id}: {task.title}\n"

        review_content += f"""
[bold cyan]🔧 Available Commands[/bold cyan]
• [cyan]review --progress[/cyan]     Detailed progress breakdown
• [cyan]review --files[/cyan]        Review generated files
• [cyan]review --task-id <id>[/cyan] Review specific task
• [cyan]generate[/cyan]              Generate code for next task
• [cyan]tasks[/cyan]                 View all tasks
        """

        panel = Panel(
            review_content.strip(),
            title="[bold]Implementation Review[/bold]",
            border_style="cyan",
            padding=(1, 2)
        )
        self.console.print(panel)
        return ""

    def _review_specific_task(self, project_state, task_id: str) -> str:
        """Review a specific task.
        
        Args:
            project_state: Current project state
            task_id: ID of task to review
            
        Returns:
            Task review
        """
        target_task = None
        for task in project_state.tasks.tasks:
            if task.id == task_id:
                target_task = task
                break
        
        if not target_task:
            return f"Task '{task_id}' not found."

        # Check if task has generated files
        generated_files = getattr(target_task, 'generated_files', [])
        
        review_content = f"""
[bold]Task Review: {target_task.id}[/bold]

[bold cyan]📋 Task Details[/bold cyan]
• Title: {target_task.title}
• Status: {target_task.status.value}
• Language: {getattr(target_task, 'target_language', 'python')}
• Description: {target_task.description}

[bold cyan]📁 Generated Files[/bold cyan]
"""
        
        if generated_files:
            from pathlib import Path
            for file_info in generated_files:
                file_path = Path(project_state.project_path) / file_info.get('path', '')
                exists = file_path.exists()
                status_icon = "✅" if exists else "❌"
                review_content += f"• {status_icon} {file_info.get('path', 'Unknown')}\n"
        else:
            review_content += "• No files generated yet\n"

        # Show implementation notes if available
        if hasattr(target_task, 'implementation_notes') and target_task.implementation_notes:
            review_content += f"\n[bold cyan]📝 Implementation Notes[/bold cyan]\n{target_task.implementation_notes}\n"

        # Show next steps
        from ..models.enums import TaskStatus
        if target_task.status == TaskStatus.NOT_STARTED:
            review_content += f"\n[bold cyan]🚀 Next Steps[/bold cyan]\n• Run: [cyan]generate --task-id {task_id}[/cyan]\n"
        elif target_task.status == TaskStatus.COMPLETED:
            review_content += f"\n[bold green]✅ Task Completed[/bold green]\n• Files generated and saved\n"
        elif target_task.status == TaskStatus.FAILED:
            review_content += f"\n[bold red]❌ Task Failed[/bold red]\n• Review errors and retry generation\n"

        panel = Panel(
            review_content.strip(),
            title=f"[bold]Task {task_id} Review[/bold]",
            border_style="cyan",
            padding=(1, 2)
        )
        self.console.print(panel)
        return ""

    def _review_generated_files(self, project_state) -> str:
        """Review all generated files.
        
        Args:
            project_state: Current project state
            
        Returns:
            Files review
        """
        from pathlib import Path
        from ..models.enums import TaskStatus
        
        # Collect all generated files from completed tasks
        all_files = []
        for task in project_state.tasks.tasks:
            if task.status == TaskStatus.COMPLETED and hasattr(task, 'generated_files'):
                for file_info in task.generated_files:
                    all_files.append({
                        'task_id': task.id,
                        'task_title': task.title,
                        'file_path': file_info.get('path', ''),
                        'file_type': file_info.get('type', 'unknown')
                    })

        if not all_files:
            return "No files have been generated yet."

        # Create files table
        files_table = Table(
            title="Generated Files Review",
            show_header=True,
            header_style="bold cyan"
        )
        files_table.add_column("Task", style="cyan", width=10)
        files_table.add_column("File Path", style="white", width=40)
        files_table.add_column("Type", style="yellow", width=12)
        files_table.add_column("Status", style="green", width=10)

        project_path = Path(project_state.project_path)
        
        for file_info in all_files:
            file_path = project_path / file_info['file_path']
            exists = file_path.exists()
            status = "✅ Exists" if exists else "❌ Missing"
            status_style = "green" if exists else "red"
            
            files_table.add_row(
                file_info['task_id'],
                file_info['file_path'],
                file_info['file_type'],
                f"[{status_style}]{status}[/{status_style}]"
            )

        self.console.print(files_table)
        
        # Show summary
        existing_files = sum(1 for f in all_files if (project_path / f['file_path']).exists())
        self.console.print(f"\n[bold]Summary:[/bold] {existing_files}/{len(all_files)} files exist on disk")
        
        return ""

    def _review_progress(self, project_state) -> str:
        """Show detailed progress review.
        
        Args:
            project_state: Current project state
            
        Returns:
            Progress review
        """
        if not project_state.tasks:
            return "No tasks available for progress review."

        # Create progress breakdown by status
        from ..models.enums import TaskStatus
        from collections import defaultdict
        
        status_groups = defaultdict(list)
        for task in project_state.tasks.tasks:
            status_groups[task.status].append(task)

        # Display progress for each status
        for status in [TaskStatus.COMPLETED, TaskStatus.IN_PROGRESS, TaskStatus.NOT_STARTED, TaskStatus.FAILED, TaskStatus.BLOCKED]:
            tasks_in_status = status_groups.get(status, [])
            if not tasks_in_status:
                continue
                
            status_name = status.value.replace('_', ' ').title()
            status_style = {
                TaskStatus.COMPLETED: "green",
                TaskStatus.IN_PROGRESS: "yellow",
                TaskStatus.NOT_STARTED: "blue",
                TaskStatus.FAILED: "red",
                TaskStatus.BLOCKED: "magenta"
            }.get(status, "white")
            
            self.console.print(f"\n[bold {status_style}]{status_name} Tasks ({len(tasks_in_status)})[/bold {status_style}]")
            
            for task in tasks_in_status:
                self.console.print(f"  • {task.id}: {task.title}")

        # Show overall progress bar
        total_tasks = len(project_state.tasks.tasks)
        completed_tasks = len(status_groups.get(TaskStatus.COMPLETED, []))
        
        if total_tasks > 0:
            progress_bar = "█" * int(completed_tasks / total_tasks * 20)
            remaining_bar = "░" * (20 - int(completed_tasks / total_tasks * 20))
            percentage = completed_tasks / total_tasks * 100
            
            self.console.print(f"\n[bold]Overall Progress:[/bold]")
            self.console.print(f"[green]{progress_bar}[/green][dim]{remaining_bar}[/dim] {percentage:.1f}% ({completed_tasks}/{total_tasks})")

        return ""

    def _handle_complete_command(self, args: list[str]) -> str:
        """Handle complete command to mark tasks as complete.

        Args:
            args: Command arguments

        Returns:
            Response message
        """
        if not self.workflow_manager:
            return "No active project. Use 'init [path]' to start."

        try:
            current_phase = self.workflow_manager.get_current_phase()
            if current_phase != PhaseType.IMPLEMENTATION:
                return f"Complete command is only available in implementation phase. Current phase: {current_phase.value}"

            # Parse task ID if provided
            task_id = None
            if args and not args[0].startswith("--"):
                task_id = args[0]

            if task_id:
                self.console.print(f"[cyan]Marking task {task_id} as complete...[/cyan]")
                # TODO: Implement task completion
                return f"Task completion functionality needs to be implemented for task: {task_id}"
            else:
                # TODO: Show completion options
                return "Task completion functionality needs to be implemented"

        except Exception as e:
            return f"Error completing task: {e!s}"

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
            
        Note: This method uses asyncio.run() to execute async workflow operations.
        This is safe because enhanced_cli methods are called synchronously
        from the main CLI loop.
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
                # Execute async resume using asyncio.run()
                # This creates a new event loop for the async operation
                import asyncio
                asyncio.run(self.workflow_manager.resume_project(project_path))
        else:
            self.display_message(
                "[blue]🚀 Initializing new dev-agent project...[/blue]"
            )
            # Create .dev_agent directory structure
            dev_agent_dir.mkdir(parents=True, exist_ok=True)
            documents_dir.mkdir(parents=True, exist_ok=True)
            index_dir.mkdir(parents=True, exist_ok=True)

            if self.workflow_manager:
                # Execute async initialization using asyncio.run()
                # This creates a new event loop for the async operation
                import asyncio
                asyncio.run(self.workflow_manager.start_new_project(project_path))

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
