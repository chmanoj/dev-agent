"""CLI interface for undo/redo functionality."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt
from rich.table import Table
from rich.text import Text

from ..models.enums import PhaseType
from ..models.undo_redo import ActionType, CommandHistoryEntry, SnapshotType, StateSnapshot, UndoRedoAction
from ..state.undo_redo_manager import UndoRedoManager


class UndoRedoCLI:
    """CLI interface for undo/redo operations."""

    def __init__(self, undo_redo_manager: UndoRedoManager):
        """Initialize the undo/redo CLI.

        Args:
            undo_redo_manager: UndoRedoManager instance
        """
        self.undo_redo_manager = undo_redo_manager
        self.console = Console()

    def show_snapshots_browser(self) -> str | None:
        """Show interactive browser for available snapshots.

        Returns:
            Selected snapshot ID, or None if cancelled
        """
        snapshots = self.undo_redo_manager.get_available_snapshots()
        
        if not snapshots:
            self.console.print("[yellow]No snapshots available.[/yellow]")
            return None

        self.console.print("\n[bold blue]Available State Snapshots[/bold blue]")
        self.console.print("=" * 60)

        # Create table for snapshots
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=3)
        table.add_column("Timestamp", style="cyan", width=20)
        table.add_column("Type", style="green", width=12)
        table.add_column("Description", style="white", width=40)
        table.add_column("Phase", style="yellow", width=15)

        for i, snapshot in enumerate(snapshots, 1):
            # Get phase from metadata if available
            phase = snapshot.metadata.get("phase", "Unknown")
            if isinstance(phase, PhaseType):
                phase = phase.value.title()
            
            # Format timestamp
            timestamp_str = snapshot.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            # Format snapshot type
            type_str = snapshot.snapshot_type.value.replace("_", " ").title()
            
            table.add_row(
                str(i),
                timestamp_str,
                type_str,
                snapshot.description[:37] + "..." if len(snapshot.description) > 40 else snapshot.description,
                str(phase),
            )

        self.console.print(table)

        # Get user selection
        try:
            selection = IntPrompt.ask(
                "\nSelect snapshot number (0 to cancel)",
                default=0,
                show_default=True,
            )
            
            if selection == 0 or selection > len(snapshots):
                return None
                
            selected_snapshot = snapshots[selection - 1]
            
            # Show detailed snapshot info
            self._show_snapshot_details(selected_snapshot)
            
            # Confirm restoration
            if Confirm.ask(f"\nRestore to this snapshot?"):
                return selected_snapshot.id
                
        except (KeyboardInterrupt, EOFError):
            self.console.print("\n[yellow]Operation cancelled.[/yellow]")
            
        return None

    def show_undo_actions(self) -> str | None:
        """Show available undo actions.

        Returns:
            Selected action ID, or None if cancelled
        """
        actions = self.undo_redo_manager.get_undo_actions()
        
        if not actions:
            self.console.print("[yellow]No actions available to undo.[/yellow]")
            return None

        self.console.print("\n[bold red]Available Undo Actions[/bold red]")
        self.console.print("=" * 60)

        # Create table for actions
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=3)
        table.add_column("Timestamp", style="cyan", width=20)
        table.add_column("Type", style="green", width=18)
        table.add_column("Description", style="white", width=35)

        for i, action in enumerate(actions, 1):
            timestamp_str = action.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            type_str = action.action_type.value.replace("_", " ").title()
            
            table.add_row(
                str(i),
                timestamp_str,
                type_str,
                action.description[:32] + "..." if len(action.description) > 35 else action.description,
            )

        self.console.print(table)

        # Get user selection
        try:
            selection = IntPrompt.ask(
                "\nSelect action to undo (0 to cancel)",
                default=0,
                show_default=True,
            )
            
            if selection == 0 or selection > len(actions):
                return None
                
            selected_action = actions[selection - 1]
            
            # Show detailed action info
            self._show_action_details(selected_action)
            
            # Confirm undo
            if Confirm.ask(f"\nUndo this action?"):
                return selected_action.id
                
        except (KeyboardInterrupt, EOFError):
            self.console.print("\n[yellow]Operation cancelled.[/yellow]")
            
        return None

    def show_redo_actions(self) -> str | None:
        """Show available redo actions.

        Returns:
            Selected action ID, or None if cancelled
        """
        actions = self.undo_redo_manager.get_redo_actions()
        
        if not actions:
            self.console.print("[yellow]No actions available to redo.[/yellow]")
            return None

        self.console.print("\n[bold green]Available Redo Actions[/bold green]")
        self.console.print("=" * 60)

        # Create table for actions
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=3)
        table.add_column("Timestamp", style="cyan", width=20)
        table.add_column("Type", style="green", width=18)
        table.add_column("Description", style="white", width=35)

        for i, action in enumerate(actions, 1):
            timestamp_str = action.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            type_str = action.action_type.value.replace("_", " ").title()
            
            table.add_row(
                str(i),
                timestamp_str,
                type_str,
                action.description[:32] + "..." if len(action.description) > 35 else action.description,
            )

        self.console.print(table)

        # Get user selection
        try:
            selection = IntPrompt.ask(
                "\nSelect action to redo (0 to cancel)",
                default=0,
                show_default=True,
            )
            
            if selection == 0 or selection > len(actions):
                return None
                
            selected_action = actions[selection - 1]
            
            # Show detailed action info
            self._show_action_details(selected_action)
            
            # Confirm redo
            if Confirm.ask(f"\nRedo this action?"):
                return selected_action.id
                
        except (KeyboardInterrupt, EOFError):
            self.console.print("\n[yellow]Operation cancelled.[/yellow]")
            
        return None

    def show_command_history(self) -> str | None:
        """Show command history for rollback.

        Returns:
            Selected history entry ID, or None if cancelled
        """
        history = self.undo_redo_manager.get_command_history()
        
        if not history:
            self.console.print("[yellow]No command history available.[/yellow]")
            return None

        self.console.print("\n[bold blue]Command History[/bold blue]")
        self.console.print("=" * 70)

        # Create table for command history
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=3)
        table.add_column("Timestamp", style="cyan", width=20)
        table.add_column("Phase", style="yellow", width=12)
        table.add_column("Command", style="white", width=25)
        table.add_column("Status", style="green", width=8)

        for i, entry in enumerate(history, 1):
            timestamp_str = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            phase_str = entry.phase.value.title()
            command_str = entry.command[:22] + "..." if len(entry.command) > 25 else entry.command
            status_str = "[green]✓[/green]" if entry.success else "[red]✗[/red]"
            
            table.add_row(
                str(i),
                timestamp_str,
                phase_str,
                command_str,
                status_str,
            )

        self.console.print(table)

        # Get user selection
        try:
            selection = IntPrompt.ask(
                "\nSelect command to rollback to (0 to cancel)",
                default=0,
                show_default=True,
            )
            
            if selection == 0 or selection > len(history):
                return None
                
            selected_entry = history[selection - 1]
            
            # Show detailed entry info
            self._show_history_entry_details(selected_entry)
            
            # Confirm rollback
            if Confirm.ask(f"\nRollback to this command?"):
                return selected_entry.id
                
        except (KeyboardInterrupt, EOFError):
            self.console.print("\n[yellow]Operation cancelled.[/yellow]")
            
        return None

    def show_phase_transitions(self) -> None:
        """Show all phase transitions for review."""
        transitions = self.undo_redo_manager.get_phase_transitions()
        
        if not transitions:
            self.console.print("[yellow]No phase transitions found.[/yellow]")
            return

        self.console.print("\n[bold blue]Phase Transition History[/bold blue]")
        self.console.print("=" * 60)

        # Create table for phase transitions
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Timestamp", style="cyan", width=20)
        table.add_column("Description", style="white", width=40)

        for transition in sorted(transitions, key=lambda t: t.timestamp):
            timestamp_str = transition.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            table.add_row(
                timestamp_str,
                transition.description,
            )

        self.console.print(table)

    def _show_snapshot_details(self, snapshot: StateSnapshot) -> None:
        """Show detailed information about a snapshot.

        Args:
            snapshot: Snapshot to show details for
        """
        details = []
        details.append(f"[bold]ID:[/bold] {snapshot.id}")
        details.append(f"[bold]Timestamp:[/bold] {snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        details.append(f"[bold]Type:[/bold] {snapshot.snapshot_type.value.replace('_', ' ').title()}")
        details.append(f"[bold]Description:[/bold] {snapshot.description}")
        
        # Show metadata if available
        if snapshot.metadata:
            details.append(f"[bold]Metadata:[/bold]")
            for key, value in snapshot.metadata.items():
                if isinstance(value, PhaseType):
                    value = value.value.title()
                details.append(f"  • {key}: {value}")

        panel = Panel(
            "\n".join(details),
            title="[bold blue]Snapshot Details[/bold blue]",
            border_style="blue",
        )
        self.console.print(panel)

    def _show_action_details(self, action: UndoRedoAction) -> None:
        """Show detailed information about an action.

        Args:
            action: Action to show details for
        """
        details = []
        details.append(f"[bold]ID:[/bold] {action.id}")
        details.append(f"[bold]Timestamp:[/bold] {action.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        details.append(f"[bold]Type:[/bold] {action.action_type.value.replace('_', ' ').title()}")
        details.append(f"[bold]Description:[/bold] {action.description}")
        details.append(f"[bold]Before Snapshot:[/bold] {action.before_snapshot_id}")
        details.append(f"[bold]After Snapshot:[/bold] {action.after_snapshot_id}")
        
        # Show metadata if available
        if action.metadata:
            details.append(f"[bold]Metadata:[/bold]")
            for key, value in action.metadata.items():
                if isinstance(value, (PhaseType, ActionType)):
                    value = value.value.title()
                details.append(f"  • {key}: {value}")

        panel = Panel(
            "\n".join(details),
            title="[bold blue]Action Details[/bold blue]",
            border_style="blue",
        )
        self.console.print(panel)

    def _show_history_entry_details(self, entry: CommandHistoryEntry) -> None:
        """Show detailed information about a command history entry.

        Args:
            entry: History entry to show details for
        """
        details = []
        details.append(f"[bold]ID:[/bold] {entry.id}")
        details.append(f"[bold]Timestamp:[/bold] {entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        details.append(f"[bold]Command:[/bold] {entry.command}")
        details.append(f"[bold]Phase:[/bold] {entry.phase.value.title()}")
        details.append(f"[bold]Success:[/bold] {'Yes' if entry.success else 'No'}")
        details.append(f"[bold]Snapshot ID:[/bold] {entry.snapshot_id}")
        
        if entry.error_message:
            details.append(f"[bold]Error:[/bold] {entry.error_message}")
        
        # Show metadata if available
        if entry.metadata:
            details.append(f"[bold]Metadata:[/bold]")
            for key, value in entry.metadata.items():
                if isinstance(value, PhaseType):
                    value = value.value.title()
                details.append(f"  • {key}: {value}")

        panel = Panel(
            "\n".join(details),
            title="[bold blue]Command History Entry Details[/bold blue]",
            border_style="blue",
        )
        self.console.print(panel)

    def display_operation_result(self, operation: str, success: bool, message: str = "") -> None:
        """Display the result of an undo/redo operation.

        Args:
            operation: Name of the operation (undo, redo, restore, etc.)
            success: Whether the operation succeeded
            message: Additional message to display
        """
        if success:
            self.console.print(f"[green]✓ {operation.title()} operation completed successfully![/green]")
            if message:
                self.console.print(f"[dim]{message}[/dim]")
        else:
            self.console.print(f"[red]✗ {operation.title()} operation failed.[/red]")
            if message:
                self.console.print(f"[red]{message}[/red]")

    def display_current_state_info(self, current_snapshot_id: str | None) -> None:
        """Display information about the current state.

        Args:
            current_snapshot_id: ID of the current snapshot
        """
        if not current_snapshot_id:
            self.console.print("[yellow]No current snapshot available.[/yellow]")
            return

        snapshot = self.undo_redo_manager.get_snapshot_by_id(current_snapshot_id)
        if not snapshot:
            self.console.print(f"[red]Current snapshot {current_snapshot_id} not found.[/red]")
            return

        self.console.print(f"\n[bold blue]Current State[/bold blue]")
        self.console.print(f"Snapshot: {snapshot.description}")
        self.console.print(f"Created: {snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if snapshot.project_state:
            self.console.print(f"Phase: {snapshot.project_state.current_phase.value.title()}")
            self.console.print(f"Indexing Complete: {'Yes' if snapshot.project_state.indexing_complete else 'No'}")