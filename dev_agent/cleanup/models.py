"""Data models for cleanup operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass
class CleanupPlan:
    """Plan for cleanup operations.

    Attributes:
        files_to_remove: List of file paths to remove
        directories_to_remove: List of directory paths to remove
        dependencies_to_remove: List of dependency names to remove from pyproject.toml
        files_to_move: Dictionary mapping source paths to destination paths
        total_size_reduction: Estimated size reduction in bytes
        estimated_time: Human-readable estimated time for cleanup
        safety_level: Safety level of the cleanup operation
    """

    files_to_remove: list[Path] = field(default_factory=list)
    directories_to_remove: list[Path] = field(default_factory=list)
    dependencies_to_remove: list[str] = field(default_factory=list)
    files_to_move: dict[Path, Path] = field(default_factory=dict)
    total_size_reduction: int = 0
    estimated_time: str = "Unknown"
    safety_level: Literal["safe", "moderate", "aggressive"] = "safe"

    def __post_init__(self) -> None:
        """Validate the cleanup plan after initialization."""
        # Ensure all paths are Path objects
        self.files_to_remove = [
            Path(p) if not isinstance(p, Path) else p  # type: ignore[redundant-expr]
            for p in self.files_to_remove
        ]
        self.directories_to_remove = [
            Path(p) if not isinstance(p, Path) else p  # type: ignore[redundant-expr]
            for p in self.directories_to_remove
        ]
        self.files_to_move = {
            (Path(k) if not isinstance(k, Path) else k): (  # type: ignore[redundant-expr]
                Path(v) if not isinstance(v, Path) else v  # type: ignore[redundant-expr]
            )
            for k, v in self.files_to_move.items()
        }

    @property
    def total_items(self) -> int:
        """Get total number of items to process."""
        return (
            len(self.files_to_remove)
            + len(self.directories_to_remove)
            + len(self.dependencies_to_remove)
            + len(self.files_to_move)
        )

    @property
    def size_reduction_mb(self) -> float:
        """Get size reduction in megabytes."""
        return self.total_size_reduction / (1024 * 1024)

    def get_summary(self) -> dict[str, int | float | str]:
        """Get a summary of the cleanup plan.

        Returns:
            Dictionary containing plan summary statistics
        """
        return {
            "files_to_remove": len(self.files_to_remove),
            "directories_to_remove": len(self.directories_to_remove),
            "dependencies_to_remove": len(self.dependencies_to_remove),
            "files_to_move": len(self.files_to_move),
            "total_items": self.total_items,
            "size_reduction_mb": round(self.size_reduction_mb, 2),
            "estimated_time": self.estimated_time,
            "safety_level": self.safety_level,
        }


@dataclass
class CleanupResult:
    """Result of cleanup execution.

    Attributes:
        removed_files: List of successfully removed file paths
        removed_directories: List of successfully removed directory paths
        moved_files: Dictionary of successfully moved files (source -> destination)
        removed_dependencies: List of successfully removed dependency names
        errors: List of error messages encountered during cleanup
        size_reduction: Actual size reduction achieved in bytes
        execution_time: Time taken to execute cleanup in seconds
    """

    removed_files: list[Path] = field(default_factory=list)
    removed_directories: list[Path] = field(default_factory=list)
    moved_files: dict[Path, Path] = field(default_factory=dict)
    removed_dependencies: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    size_reduction: int = 0
    execution_time: float = 0.0

    def __post_init__(self) -> None:
        """Validate the cleanup result after initialization."""
        # Ensure all paths are Path objects
        self.removed_files = [
            Path(p) if not isinstance(p, Path) else p  # type: ignore[redundant-expr]
            for p in self.removed_files
        ]
        self.removed_directories = [
            Path(p) if not isinstance(p, Path) else p  # type: ignore[redundant-expr]
            for p in self.removed_directories
        ]
        self.moved_files = {
            (Path(k) if not isinstance(k, Path) else k): (  # type: ignore[redundant-expr]
                Path(v) if not isinstance(v, Path) else v  # type: ignore[redundant-expr]
            )
            for k, v in self.moved_files.items()
        }

    @property
    def success_count(self) -> int:
        """Get total number of successful operations."""
        return (
            len(self.removed_files)
            + len(self.removed_directories)
            + len(self.removed_dependencies)
            + len(self.moved_files)
        )

    @property
    def error_count(self) -> int:
        """Get total number of errors."""
        return len(self.errors)

    @property
    def size_reduction_mb(self) -> float:
        """Get size reduction in megabytes."""
        return self.size_reduction / (1024 * 1024)

    @property
    def success_rate(self) -> float:
        """Calculate success rate as a percentage.

        Returns:
            Success rate between 0.0 and 100.0
        """
        total = self.success_count + self.error_count
        if total == 0:
            return 100.0
        return (self.success_count / total) * 100.0

    def get_summary(self) -> dict[str, int | float | str]:
        """Get a summary of the cleanup result.

        Returns:
            Dictionary containing result summary statistics
        """
        return {
            "removed_files": len(self.removed_files),
            "removed_directories": len(self.removed_directories),
            "moved_files": len(self.moved_files),
            "removed_dependencies": len(self.removed_dependencies),
            "success_count": self.success_count,
            "errors": self.error_count,
            "size_reduction_mb": round(self.size_reduction_mb, 2),
            "execution_time": round(self.execution_time, 2),
            "success_rate": round(self.success_rate, 2),
        }
