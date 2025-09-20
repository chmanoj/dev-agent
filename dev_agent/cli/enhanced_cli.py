"""Enhanced CLI with Rich UI components for improved user experience."""

from __future__ import annotations

import difflib
import os
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

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
        """Initialize the progress manager."""
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
        self.current_task: Optional[TaskID] = None
        self.phase_start_times: dict[PhaseType, datetime] = {}
        self.phase_estimates: dict[PhaseType, float] = {
            PhaseType.INDEXING: 30.0,
            PhaseType.SPECIFICATION: 45.0,
            PhaseType.DESIGN: 60.0,
            PhaseType.IMPLEMENTATION: 120.0,
        }

    def start_phase_progress(self, phase: PhaseType, total_steps: int = 100) -> TaskID:
        """Start progress tracking for a phase."""
        self.phase_start_times[phase] = datetime.now()
        description = f"[bold blue]{phase.value.title()}[/bold blue]"
        
        if self.current_task is not None:
            self.progress.remove_task(self.current_task)
            
        self.current_task = self.progress.add_task(
            description, 
            total=total_steps,
            start=True
        )
        return self.current_task

    def update_progress(self, completed: int, status_message: str = "") -> None:
        """Update the current progress."""
        if self.current_task is not None:
            description = self.progress.tasks[self.current_task].description
            if status_message:
                description = f"{description.split(' - ')[0]} - {status_message}"
            
            self.progress.update(
                self.current_task,
                completed=completed,
                description=description
            )

    def complete_phase(self, phase: PhaseType) -> None:
        """Complete the current phase progress."""
        if self.current_task is not None:
            self.progress.update(self.current_task, completed=100)
            
            if phase in self.phase_start_times:
                elapsed = datetime.now() - self.phase_start_times[phase]
                elapsed_seconds = elapsed.total_seconds()
                
                self.phase_estimates[phase] = (
                    self.phase_estimates[phase] * 0.7 + elapsed_seconds * 0.3
                )

    def show_phase_summary(self, completed_phases: list[PhaseType]) -> None:
        """Show a summary of completed phases."""
        table = Table(title="Phase Summary", show_header=True, header_style="bold magenta")
        table.add_column("Phase", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")
        table.add_column("Duration", style="yellow")
        
        for phase in PhaseType:
            if phase in completed_phases:
                status = "✅ Complete"
                duration = f"{int(self.phase_estimates[phase])}s"
            else:
                status = "⏳ Pending"
                duration = f"~{int(self.phase_estimates[phase])}s"
                
            table.add_row(phase.value.title(), status, duration)
            
        self.console.print(table)
