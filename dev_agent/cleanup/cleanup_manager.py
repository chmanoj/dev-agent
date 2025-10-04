"""Cleanup manager for repository maintenance operations."""

from __future__ import annotations

import ast
import json
import logging
import shutil
import subprocess
import time
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Literal

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[import-not-found,no-redef]
    except ImportError:
        tomllib = None  # type: ignore[assignment,unused-ignore]

from dev_agent.cleanup.models import CleanupPlan, CleanupResult

logger = logging.getLogger(__name__)


class CleanupManager:
    """Manages repository cleanup operations.

    This class provides functionality to scan for cleanup candidates,
    generate cleanup plans, and execute cleanup operations with safety
    mechanisms like dry-run mode and backup creation.

    Attributes:
        project_root: Root directory of the project to clean
        safety_level: Safety level for cleanup operations
    """

    def __init__(
        self,
        project_root: Path | str,
        safety_level: Literal["safe", "moderate", "aggressive"] = "safe",
    ) -> None:
        """Initialize the cleanup manager.

        Args:
            project_root: Root directory of the project
            safety_level: Safety level for cleanup operations
        """
        self.project_root = Path(project_root).resolve()
        self.safety_level = safety_level

        if not self.project_root.exists():
            msg = f"Project root does not exist: {self.project_root}"
            raise ValueError(msg)

        if not self.project_root.is_dir():
            msg = f"Project root is not a directory: {self.project_root}"
            raise ValueError(msg)

        logger.info(
            f"Initialized CleanupManager for {self.project_root} "
            f"with safety level: {self.safety_level}"
        )

    def scan_for_cleanup_candidates(self) -> CleanupPlan:
        """Scan the project for cleanup candidates.

        This method identifies files and directories that can be cleaned up,
        including temporary files, generated files, development artifacts,
        obsolete examples, and unused dependencies.

        Returns:
            CleanupPlan containing all identified cleanup candidates
        """
        logger.info(
            f"Scanning for cleanup candidates (safety level: {self.safety_level})..."
        )

        plan = CleanupPlan(safety_level=self.safety_level)

        # Safe level: Only temporary and generated files
        if self.safety_level in ["safe", "moderate", "aggressive"]:
            plan.files_to_remove.extend(self.identify_temporary_files())
            plan.files_to_remove.extend(self.identify_generated_files())
            plan.directories_to_remove.extend(self._identify_temporary_directories())
            plan.directories_to_remove.extend(self._identify_generated_directories())

        # Moderate level: Also include development artifacts
        if self.safety_level in ["moderate", "aggressive"]:
            artifacts = self.identify_development_artifacts()
            plan.files_to_move.update(artifacts)

        # Aggressive level: Also include obsolete examples and unused dependencies
        if self.safety_level == "aggressive":
            plan.files_to_remove.extend(self.identify_obsolete_examples())
            plan.dependencies_to_remove.extend(self.identify_unused_dependencies())

        # Remove duplicates from files_to_remove
        plan.files_to_remove = list(set(plan.files_to_remove))
        plan.directories_to_remove = list(set(plan.directories_to_remove))

        # Calculate total size reduction
        plan.total_size_reduction = self._calculate_size_reduction(plan)

        # Estimate time
        plan.estimated_time = self._estimate_cleanup_time(plan)

        logger.info(
            f"Scan complete: {plan.total_items} items identified, "
            f"{plan.size_reduction_mb:.2f} MB reduction, "
            f"safety level: {plan.safety_level}"
        )

        return plan

    def identify_temporary_files(self) -> list[Path]:
        """Identify temporary files for removal.

        Identifies files like .coverage, *.pyc, __pycache__/ directories,
        and other cache directories.

        Returns:
            List of temporary file paths
        """
        logger.debug("Identifying temporary files...")
        temporary_files: list[Path] = []

        # Patterns for temporary files based on .gitignore
        temp_patterns = [
            # Python bytecode
            "**/*.pyc",
            "**/*.pyo",
            "**/*.pyd",
            "**/*$py.class",
            # Cache directories
            "**/__pycache__",
            "**/.pytest_cache",
            "**/.mypy_cache",
            "**/.ruff_cache",
            "**/.hypothesis",
            # Coverage files
            ".coverage",
            ".coverage.*",
            "htmlcov",
            "coverage.xml",
            "**/*.cover",
            "**/*.py.cover",
            # Build artifacts
            "build",
            "dist",
            "*.egg-info",
            ".eggs",
            # Other cache
            ".cache",
            ".tox",
            ".nox",
            # OS-specific
            ".DS_Store",
            "Thumbs.db",
            "**/*.tmp",
            "**/*.temp",
        ]

        for pattern in temp_patterns:
            try:
                for match in self.project_root.glob(pattern):
                    if match.exists():
                        # Add directories to directories_to_remove instead
                        if match.is_dir():
                            continue
                        temporary_files.append(match)
            except (OSError, PermissionError) as e:
                logger.warning(f"Error scanning pattern {pattern}: {e}")

        # Also identify cache directories separately
        cache_dirs = [
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            ".hypothesis",
            "htmlcov",
            ".cache",
            ".tox",
            ".nox",
            "build",
            "dist",
            ".eggs",
        ]

        for cache_dir in cache_dirs:
            try:
                for match in self.project_root.glob(f"**/{cache_dir}"):
                    if match.exists() and match.is_dir():
                        # These will be added to directories_to_remove in scan method
                        pass
            except (OSError, PermissionError) as e:
                logger.warning(f"Error scanning for {cache_dir}: {e}")

        logger.debug(f"Found {len(temporary_files)} temporary files")
        return temporary_files

    def identify_generated_files(self) -> list[Path]:
        """Identify generated files for removal.

        Identifies files like site/, TASK_*.md, build artifacts,
        documentation build outputs, and test coverage reports.

        Returns:
            List of generated file paths
        """
        logger.debug("Identifying generated files...")
        generated_files: list[Path] = []

        # Patterns for generated files
        generated_patterns = [
            # Task completion summaries
            "TASK_*_COMPLETION_SUMMARY.md",
            "TASK_*.md",
            # Documentation build outputs (site/ is a directory, handled separately)
            "docs/_build/**/*",
            # Coverage reports
            ".coverage",
            ".coverage.*",
            "coverage.xml",
            # Build artifacts
            "*.egg-info/**/*",
            "dist/**/*",
            "build/**/*",
            # Temporary markdown files
            "MODERNIZATION_SUMMARY.md",
            "MANIFEST.in",
        ]

        for pattern in generated_patterns:
            try:
                for match in self.project_root.glob(pattern):
                    if match.exists() and match.is_file():
                        generated_files.append(match)
            except (OSError, PermissionError) as e:
                logger.warning(f"Error scanning pattern {pattern}: {e}")

        # Check for specific generated files at root
        specific_files = [
            "MODERNIZATION_SUMMARY.md",
            "MANIFEST.in",
        ]

        for filename in specific_files:
            file_path = self.project_root / filename
            if (
                file_path.exists()
                and file_path.is_file()
                and file_path not in generated_files
            ):
                generated_files.append(file_path)

        # Identify generated directories (will be added separately)
        generated_dirs = ["site", "docs/_build"]
        for dir_name in generated_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                # These will be added to directories_to_remove in scan method
                pass

        logger.debug(f"Found {len(generated_files)} generated files")
        return generated_files

    def identify_development_artifacts(self) -> dict[Path, Path]:
        """Identify development artifacts for moving or removal.

        Identifies files in .development/ and categorizes them as
        movable or removable, suggesting appropriate destinations.

        Returns:
            Dictionary mapping source paths to destination paths
        """
        logger.debug("Identifying development artifacts...")
        artifacts: dict[Path, Path] = {}

        dev_dir = self.project_root / ".development"
        if not dev_dir.exists() or not dev_dir.is_dir():
            logger.debug("No .development directory found")
            return artifacts

        # Scan .development directory
        try:
            for item in dev_dir.rglob("*"):
                if not item.is_file():
                    continue

                # Determine destination based on file type and content
                destination = self._suggest_artifact_destination(item, dev_dir)

                if destination:
                    artifacts[item] = destination
                else:
                    # If no destination suggested, it should be removed
                    # (will be handled separately)
                    pass

        except (OSError, PermissionError) as e:
            logger.warning(f"Error scanning .development directory: {e}")

        logger.debug(f"Found {len(artifacts)} development artifacts to move")
        return artifacts

    def _suggest_artifact_destination(
        self,
        source: Path,
        dev_dir: Path,
    ) -> Path | None:
        """Suggest destination for a development artifact.

        Args:
            source: Source file path
            dev_dir: .development directory path

        Returns:
            Suggested destination path, or None if file should be removed
        """
        # Get relative path within .development
        try:
            rel_path = source.relative_to(dev_dir)
        except ValueError:
            return None

        # Migration summaries should go to docs/development/
        if "migration-summaries" in source.parts:
            docs_dev = self.project_root / "docs" / "development"
            return docs_dev / rel_path.name

        # README files might be useful in docs
        if source.name == "README.md":
            docs_dev = self.project_root / "docs" / "development"
            return docs_dev / f"development-{rel_path.name}"

        # Other markdown files could go to docs/development/
        if source.suffix == ".md":
            docs_dev = self.project_root / "docs" / "development"
            return docs_dev / rel_path.name

        # For other files, suggest removal (return None)
        return None

    def identify_obsolete_examples(self) -> list[Path]:
        """Identify obsolete examples for removal.

        Scans examples/ directory and identifies examples that are
        non-functional (imports don't work, syntax errors) or don't
        match the current API.

        Returns:
            List of obsolete example file paths
        """
        logger.debug("Identifying obsolete examples...")
        obsolete_examples: list[Path] = []

        examples_dir = self.project_root / "examples"
        if not examples_dir.exists() or not examples_dir.is_dir():
            logger.debug("No examples directory found")
            return obsolete_examples

        # Scan all Python files in examples directory
        try:
            for example_file in examples_dir.glob("**/*.py"):
                if not example_file.is_file():
                    continue

                # Check if example is functional
                if not self._is_example_functional(example_file):
                    obsolete_examples.append(example_file)

        except (OSError, PermissionError) as e:
            logger.warning(f"Error scanning examples directory: {e}")

        logger.debug(f"Found {len(obsolete_examples)} obsolete examples")
        return obsolete_examples

    def _is_example_functional(self, example_file: Path) -> bool:
        """Check if an example file is functional.

        Args:
            example_file: Path to example file

        Returns:
            True if example appears functional, False otherwise
        """

        try:
            # Read the file
            content = example_file.read_text(encoding="utf-8")

            # Check for syntax errors
            try:
                ast.parse(content)
            except SyntaxError:
                logger.debug(f"Syntax error in {example_file.name}")
                return False

            # Check for basic import issues (simple heuristic)
            # Look for imports from dev_agent
            has_dev_agent_import = (
                "from dev_agent" in content or "import dev_agent" in content
            )

            # If it's a dev_agent example, it should import from dev_agent
            if not has_dev_agent_import:
                # Might be a utility script, consider it functional
                return True

            # For now, consider examples with valid syntax as functional
            # More sophisticated API compatibility checking would require
            # actually importing and running the code, which is risky
            return True

        except (OSError, UnicodeDecodeError) as e:
            logger.warning(f"Error reading {example_file.name}: {e}")
            return False

    def identify_unused_dependencies(self) -> list[str]:
        """Identify unused dependencies in pyproject.toml.

        Analyzes pyproject.toml and uses static analysis to find
        dependencies that are not imported in the codebase.

        Returns:
            List of unused dependency names
        """
        logger.debug("Identifying unused dependencies...")
        unused_deps: list[str] = []

        # Read pyproject.toml
        pyproject_path = self.project_root / "pyproject.toml"
        if not pyproject_path.exists():
            logger.debug("No pyproject.toml found")
            return unused_deps

        if tomllib is None:
            logger.warning("tomllib/tomli not available, skipping dependency analysis")
            return unused_deps

        try:
            with pyproject_path.open("rb") as f:
                pyproject_data = tomllib.load(f)

            # Get dependencies
            dependencies = self._extract_dependencies(pyproject_data)

            # Get all imports from codebase
            imports = self._collect_imports()

            # Find unused dependencies
            for dep_name in dependencies:
                # Normalize dependency name for import checking
                import_name = self._normalize_import_name(dep_name)

                # Check if this dependency is imported anywhere
                if not self._is_dependency_used(import_name, imports):
                    unused_deps.append(dep_name)

        except Exception as e:
            logger.warning(f"Error analyzing dependencies: {e}")

        logger.debug(f"Found {len(unused_deps)} potentially unused dependencies")
        return unused_deps

    def _extract_dependencies(self, pyproject_data: dict[str, object]) -> list[str]:
        """Extract dependency names from pyproject.toml data.

        Args:
            pyproject_data: Parsed pyproject.toml data

        Returns:
            List of dependency names
        """
        dependencies = []

        # Get main dependencies
        if "project" in pyproject_data:
            project = pyproject_data["project"]
            if isinstance(project, dict) and "dependencies" in project:
                deps = project["dependencies"]
                if isinstance(deps, list):
                    for dep in deps:
                        if isinstance(dep, str):
                            # Extract package name (before any version specifier)
                            dep_name = (
                                dep.split("[")[0]
                                .split(">=")[0]
                                .split("==")[0]
                                .split("<")[0]
                                .split(">")[0]
                                .strip()
                            )
                            dependencies.append(dep_name)

        return dependencies

    def _collect_imports(self) -> set[str]:
        """Collect all import statements from Python files in the codebase.

        Returns:
            Set of imported module names
        """

        imports: set[str] = set()

        # Scan main package directory
        package_dir = self.project_root / "dev_agent"
        if package_dir.exists():
            for py_file in package_dir.rglob("*.py"):
                try:
                    content = py_file.read_text(encoding="utf-8")
                    tree = ast.parse(content)

                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                imports.add(alias.name.split(".")[0])
                        elif isinstance(node, ast.ImportFrom) and node.module:
                            imports.add(node.module.split(".")[0])

                except (OSError, UnicodeDecodeError, SyntaxError):
                    # Skip files that can't be parsed
                    pass

        return imports

    def _normalize_import_name(self, dep_name: str) -> str:
        """Normalize dependency name to import name.

        Args:
            dep_name: Dependency name from pyproject.toml

        Returns:
            Normalized import name
        """
        # Common mappings from package name to import name
        name_mappings = {
            "python-dotenv": "dotenv",
            "pillow": "PIL",
            "pyyaml": "yaml",
            "beautifulsoup4": "bs4",
            "scikit-learn": "sklearn",
            "opencv-python": "cv2",
        }

        normalized = dep_name.lower().replace("-", "_")
        return name_mappings.get(dep_name.lower(), normalized)

    def _is_dependency_used(self, import_name: str, imports: set[str]) -> bool:
        """Check if a dependency is used in the codebase.

        Args:
            import_name: Normalized import name
            imports: Set of all imports found in codebase

        Returns:
            True if dependency is used, False otherwise
        """
        # Check exact match
        if import_name in imports:
            return True

        # Check if any import starts with this name (for submodules)
        return any(imp.startswith(f"{import_name}.") for imp in imports)

    def execute_cleanup(
        self,
        plan: CleanupPlan,
        dry_run: bool = True,
    ) -> CleanupResult:
        """Execute the cleanup plan.

        Args:
            plan: CleanupPlan to execute
            dry_run: If True, only simulate cleanup without making changes

        Returns:
            CleanupResult containing execution results
        """
        start_time = time.time()
        logger.info(f"Executing cleanup plan ({'dry-run' if dry_run else 'actual'})...")

        result = CleanupResult()

        if dry_run:
            # Dry-run mode: Display what would be removed without actually removing
            logger.info("=== DRY RUN MODE - No changes will be made ===")

            # Show files that would be removed
            if plan.files_to_remove:
                logger.info(f"\nWould remove {len(plan.files_to_remove)} files:")
                for file_path in plan.files_to_remove[:10]:  # Show first 10
                    size = 0
                    if file_path.exists():
                        with suppress(OSError):
                            size = file_path.stat().st_size
                    logger.info(f"  - {file_path} ({size / 1024:.2f} KB)")
                if len(plan.files_to_remove) > 10:
                    logger.info(
                        f"  ... and {len(plan.files_to_remove) - 10} more files"
                    )

            # Show directories that would be removed
            if plan.directories_to_remove:
                logger.info(
                    f"\nWould remove {len(plan.directories_to_remove)} directories:"
                )
                for dir_path in plan.directories_to_remove[:10]:  # Show first 10
                    size = 0
                    if dir_path.exists():
                        with suppress(OSError):
                            size = sum(
                                f.stat().st_size
                                for f in dir_path.rglob("*")
                                if f.is_file()
                            )
                    logger.info(f"  - {dir_path} ({size / (1024 * 1024):.2f} MB)")
                if len(plan.directories_to_remove) > 10:
                    logger.info(
                        f"  ... and {len(plan.directories_to_remove) - 10} more directories"
                    )

            # Show files that would be moved
            if plan.files_to_move:
                logger.info(f"\nWould move {len(plan.files_to_move)} files:")
                for src, dst in list(plan.files_to_move.items())[:10]:  # Show first 10
                    logger.info(f"  - {src} -> {dst}")
                if len(plan.files_to_move) > 10:
                    logger.info(f"  ... and {len(plan.files_to_move) - 10} more files")

            # Show dependencies that would be removed
            if plan.dependencies_to_remove:
                logger.info(
                    f"\nWould remove {len(plan.dependencies_to_remove)} dependencies:"
                )
                for dep in plan.dependencies_to_remove:
                    logger.info(f"  - {dep}")

            # Show size reduction estimate
            logger.info(f"\nEstimated size reduction: {plan.size_reduction_mb:.2f} MB")
            logger.info(f"Estimated time: {plan.estimated_time}")
            logger.info(f"Safety level: {plan.safety_level}")

            logger.info("\n=== Dry-run complete - no changes made ===")
        else:
            # Actual cleanup execution
            logger.info("=== EXECUTING CLEANUP ===")

            # Create backup before cleanup
            backup_dir = self._create_backup(plan)
            if backup_dir:
                logger.info(f"Backup created at: {backup_dir}")

            # Execute file removal
            self._remove_files(plan, result)

            # Execute directory removal
            self._remove_directories(plan, result)

            # Execute file moving
            self._move_files(plan, result)

            # Execute dependency removal
            self._remove_dependencies(plan, result)

            # Calculate actual size reduction
            result.size_reduction = self._calculate_actual_size_reduction(result)

            logger.info(
                f"\nCleanup complete: {result.success_count} operations succeeded, "
                f"{result.error_count} errors"
            )
            logger.info(f"Size reduction: {result.size_reduction_mb:.2f} MB")

        result.execution_time = time.time() - start_time
        return result

    def generate_cleanup_report(self, result: CleanupResult) -> str:
        """Generate a markdown cleanup report.

        Args:
            result: CleanupResult to generate report from

        Returns:
            Markdown-formatted cleanup report
        """
        logger.debug("Generating cleanup report...")

        # Build the report
        lines = [
            "# Cleanup Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Project:** {self.project_root}",
            "",
            "## Summary",
            "",
            f"- **Total Operations:** {result.success_count + result.error_count}",
            f"- **Successful:** {result.success_count}",
            f"- **Errors:** {result.error_count}",
            f"- **Success Rate:** {result.success_rate:.1f}%",
            f"- **Size Reduction:** {result.size_reduction_mb:.2f} MB",
            f"- **Execution Time:** {result.execution_time:.2f} seconds",
            "",
        ]

        # Removed files section
        if result.removed_files:
            lines.extend(
                [
                    "## Removed Files",
                    "",
                    f"Total: {len(result.removed_files)} files",
                    "",
                ]
            )

            # Group files by category for better organization
            temp_files = []
            generated_files = []
            other_files = []

            for file_path in result.removed_files:
                try:
                    # Resolve paths to handle symlinks
                    resolved_file = file_path.resolve()
                    resolved_root = self.project_root.resolve()
                    file_str = str(resolved_file.relative_to(resolved_root))
                except ValueError:
                    # If relative path fails, use absolute path
                    file_str = str(file_path)

                # Categorize files
                if any(
                    pattern in file_str
                    for pattern in [
                        ".pyc",
                        "__pycache__",
                        ".coverage",
                        ".cache",
                        ".pytest_cache",
                    ]
                ):
                    temp_files.append(file_str)
                elif any(
                    pattern in file_str
                    for pattern in ["TASK_", "COMPLETION_SUMMARY", "site/"]
                ):
                    generated_files.append(file_str)
                else:
                    other_files.append(file_str)

            if temp_files:
                lines.extend(
                    [
                        "### Temporary Files",
                        "",
                    ]
                )
                lines.extend(f"- `{file_str}`" for file_str in sorted(temp_files)[:50])
                if len(temp_files) > 50:
                    lines.append(f"- ... and {len(temp_files) - 50} more")
                lines.append("")

            if generated_files:
                lines.extend(
                    [
                        "### Generated Files",
                        "",
                    ]
                )
                lines.extend(
                    f"- `{file_str}`" for file_str in sorted(generated_files)[:50]
                )
                if len(generated_files) > 50:
                    lines.append(f"- ... and {len(generated_files) - 50} more")
                lines.append("")

            if other_files:
                lines.extend(
                    [
                        "### Other Files",
                        "",
                    ]
                )
                lines.extend(f"- `{file_str}`" for file_str in sorted(other_files)[:50])
                if len(other_files) > 50:
                    lines.append(f"- ... and {len(other_files) - 50} more")
                lines.append("")

        # Removed directories section
        if result.removed_directories:
            lines.extend(
                [
                    "## Removed Directories",
                    "",
                    f"Total: {len(result.removed_directories)} directories",
                    "",
                ]
            )

            for dir_path in sorted(result.removed_directories):
                try:
                    # Resolve paths to handle symlinks
                    resolved_dir = dir_path.resolve()
                    resolved_root = self.project_root.resolve()
                    dir_str = str(resolved_dir.relative_to(resolved_root))
                except ValueError:
                    # If relative path fails, use absolute path
                    dir_str = str(dir_path)
                lines.append(f"- `{dir_str}/`")

            lines.append("")

        # Moved files section
        if result.moved_files:
            lines.extend(
                [
                    "## Moved Files",
                    "",
                    f"Total: {len(result.moved_files)} files",
                    "",
                ]
            )

            for src_path, dst_path in sorted(result.moved_files.items()):
                try:
                    # Resolve paths to handle symlinks
                    resolved_src = src_path.resolve()
                    resolved_dst = dst_path.resolve()
                    resolved_root = self.project_root.resolve()
                    src_str = str(resolved_src.relative_to(resolved_root))
                    dst_str = str(resolved_dst.relative_to(resolved_root))
                except ValueError:
                    # If relative path fails, use absolute paths
                    src_str = str(src_path)
                    dst_str = str(dst_path)
                lines.append(f"- `{src_str}` → `{dst_str}`")

            lines.append("")

        # Removed dependencies section
        if result.removed_dependencies:
            lines.extend(
                [
                    "## Removed Dependencies",
                    "",
                    f"Total: {len(result.removed_dependencies)} dependencies",
                    "",
                ]
            )

            lines.extend(f"- `{dep}`" for dep in sorted(result.removed_dependencies))

            lines.append("")

        # Errors section
        if result.errors:
            lines.extend(
                [
                    "## Errors",
                    "",
                    f"Total: {len(result.errors)} errors encountered",
                    "",
                ]
            )

            lines.extend(f"- {error}" for error in result.errors)

            lines.append("")

        # Recommendations section
        lines.extend(
            [
                "## Recommendations",
                "",
            ]
        )

        if result.error_count > 0:
            lines.append(
                "- Review errors above and address any permission or access issues"
            )

        if result.removed_dependencies:
            lines.extend(
                [
                    "- Run tests to verify project still works after dependency removal",
                    "- Run `uv sync` to ensure environment is up to date",
                ]
            )

        if result.moved_files:
            lines.append(
                "- Review moved files to ensure they are in the correct locations"
            )

        lines.extend(
            [
                "- Commit changes to version control",
                "- Consider running the cleanup audit again to verify results",
                "",
            ]
        )

        # Footer
        lines.extend(
            [
                "---",
                "",
                "*This report was generated by dev-agent cleanup system*",
            ]
        )

        report = "\n".join(lines)

        # Save report to file
        report_path = self.project_root / "CLEANUP_REPORT.md"
        try:
            report_path.write_text(report, encoding="utf-8")
            logger.info(f"Cleanup report saved to {report_path}")
        except OSError as e:
            logger.error(f"Failed to save cleanup report: {e}")

        return report

    def _identify_temporary_directories(self) -> list[Path]:
        """Identify temporary directories for removal.

        Returns:
            List of temporary directory paths
        """
        temp_dirs: list[Path] = []

        cache_dir_names = [
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            ".hypothesis",
            "htmlcov",
            ".cache",
            ".tox",
            ".nox",
            "build",
            "dist",
            ".eggs",
        ]

        for cache_dir in cache_dir_names:
            try:
                for match in self.project_root.glob(f"**/{cache_dir}"):
                    if match.exists() and match.is_dir():
                        temp_dirs.append(match)
            except (OSError, PermissionError) as e:
                logger.warning(f"Error scanning for {cache_dir}: {e}")

        logger.debug(f"Found {len(temp_dirs)} temporary directories")
        return temp_dirs

    def _identify_generated_directories(self) -> list[Path]:
        """Identify generated directories for removal.

        Returns:
            List of generated directory paths
        """
        generated_dirs: list[Path] = []

        # Documentation build output
        site_dir = self.project_root / "site"
        if site_dir.exists() and site_dir.is_dir():
            generated_dirs.append(site_dir)

        docs_build_dir = self.project_root / "docs" / "_build"
        if docs_build_dir.exists() and docs_build_dir.is_dir():
            generated_dirs.append(docs_build_dir)

        # Demo project directory
        demo_dir = self.project_root / "demo_project"
        if demo_dir.exists() and demo_dir.is_dir():
            generated_dirs.append(demo_dir)

        logger.debug(f"Found {len(generated_dirs)} generated directories")
        return generated_dirs

    def _calculate_size_reduction(self, plan: CleanupPlan) -> int:
        """Calculate total size reduction from cleanup plan.

        Args:
            plan: CleanupPlan to calculate size for

        Returns:
            Total size reduction in bytes
        """
        total_size = 0

        # Calculate size of files to remove
        for file_path in plan.files_to_remove:
            if file_path.exists() and file_path.is_file():
                try:
                    total_size += file_path.stat().st_size
                except OSError as e:
                    logger.warning(f"Could not get size of {file_path}: {e}")

        # Calculate size of directories to remove
        for dir_path in plan.directories_to_remove:
            if dir_path.exists() and dir_path.is_dir():
                try:
                    total_size += sum(
                        f.stat().st_size for f in dir_path.rglob("*") if f.is_file()
                    )
                except OSError as e:
                    logger.warning(f"Could not get size of {dir_path}: {e}")

        return total_size

    def _estimate_cleanup_time(self, plan: CleanupPlan) -> str:
        """Estimate time required for cleanup.

        Args:
            plan: CleanupPlan to estimate time for

        Returns:
            Human-readable time estimate
        """
        total_items = plan.total_items

        if total_items == 0:
            return "< 1 second"
        if total_items < 10:
            return "< 5 seconds"
        if total_items < 50:
            return "< 30 seconds"
        if total_items < 200:
            return "1-2 minutes"
        return "2-5 minutes"

    def _create_backup(self, plan: CleanupPlan) -> Path | None:
        """Create backup directory before cleanup.

        Creates a timestamped backup directory and copies files that will
        be removed or moved to the backup location. Also stores metadata
        about the backup.

        Args:
            plan: CleanupPlan containing files to backup

        Returns:
            Path to backup directory, or None if backup creation failed
        """
        try:
            # Create backup directory with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.project_root / ".cleanup_backups" / f"backup_{timestamp}"
            backup_dir.mkdir(parents=True, exist_ok=True)

            logger.info(f"Creating backup at {backup_dir}...")

            # Backup files to be removed
            files_backed_up = 0
            for file_path in plan.files_to_remove:
                if not file_path.exists():
                    continue

                try:
                    # Calculate relative path from project root
                    # Resolve both paths to handle symlinks (e.g., /var -> /private/var on macOS)
                    resolved_file = file_path.resolve()
                    resolved_root = self.project_root.resolve()
                    rel_path = resolved_file.relative_to(resolved_root)
                    backup_path = backup_dir / "removed" / rel_path

                    # Create parent directories
                    backup_path.parent.mkdir(parents=True, exist_ok=True)

                    # Copy file to backup
                    shutil.copy2(file_path, backup_path)
                    files_backed_up += 1

                except (OSError, ValueError) as e:
                    logger.warning(f"Could not backup {file_path}: {e}")

            # Backup directories to be removed
            dirs_backed_up = 0
            for dir_path in plan.directories_to_remove:
                if not dir_path.exists():
                    continue

                try:
                    # Calculate relative path from project root
                    # Resolve both paths to handle symlinks
                    resolved_dir = dir_path.resolve()
                    resolved_root = self.project_root.resolve()
                    rel_path = resolved_dir.relative_to(resolved_root)
                    backup_path = backup_dir / "removed" / rel_path

                    # Copy entire directory tree to backup
                    shutil.copytree(dir_path, backup_path, dirs_exist_ok=True)
                    dirs_backed_up += 1

                except (OSError, ValueError) as e:
                    logger.warning(f"Could not backup {dir_path}: {e}")

            # Backup files to be moved
            moved_backed_up = 0
            for src_path in plan.files_to_move:
                if not src_path.exists():
                    continue

                try:
                    # Calculate relative path from project root
                    # Resolve both paths to handle symlinks
                    resolved_src = src_path.resolve()
                    resolved_root = self.project_root.resolve()
                    rel_path = resolved_src.relative_to(resolved_root)
                    backup_path = backup_dir / "moved" / rel_path

                    # Create parent directories
                    backup_path.parent.mkdir(parents=True, exist_ok=True)

                    # Copy file to backup
                    shutil.copy2(src_path, backup_path)
                    moved_backed_up += 1

                except (OSError, ValueError) as e:
                    logger.warning(f"Could not backup {src_path}: {e}")

            # Store backup metadata
            metadata = {
                "timestamp": timestamp,
                "project_root": str(self.project_root),
                "safety_level": plan.safety_level,
                "files_backed_up": files_backed_up,
                "directories_backed_up": dirs_backed_up,
                "moved_files_backed_up": moved_backed_up,
                "total_items": files_backed_up + dirs_backed_up + moved_backed_up,
                "files_to_remove": [str(f) for f in plan.files_to_remove],
                "directories_to_remove": [str(d) for d in plan.directories_to_remove],
                "files_to_move": {
                    str(k): str(v) for k, v in plan.files_to_move.items()
                },
                "dependencies_to_remove": plan.dependencies_to_remove,
            }

            metadata_path = backup_dir / "backup_metadata.json"
            with metadata_path.open("w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

            logger.info(
                f"Backup complete: {files_backed_up} files, "
                f"{dirs_backed_up} directories, {moved_backed_up} moved files"
            )

            return backup_dir

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None

    def _remove_files(self, plan: CleanupPlan, result: CleanupResult) -> None:
        """Remove files from the cleanup plan.

        Args:
            plan: CleanupPlan containing files to remove
            result: CleanupResult to update with removal results
        """
        logger.info(f"Removing {len(plan.files_to_remove)} files...")

        for file_path in plan.files_to_remove:
            try:
                if not file_path.exists():
                    logger.debug(f"File already removed or doesn't exist: {file_path}")
                    continue

                if not file_path.is_file():
                    logger.warning(f"Not a file, skipping: {file_path}")
                    continue

                # Get file size before removal
                try:
                    file_size = file_path.stat().st_size
                except OSError:
                    file_size = 0

                # Remove the file
                file_path.unlink()
                result.removed_files.append(file_path)
                result.size_reduction += file_size

                logger.debug(f"Removed file: {file_path}")

            except PermissionError as e:
                error_msg = f"Permission denied removing {file_path}: {e}"
                logger.error(error_msg)
                result.errors.append(error_msg)

            except OSError as e:
                error_msg = f"Error removing {file_path}: {e}"
                logger.error(error_msg)
                result.errors.append(error_msg)

        logger.info(f"Removed {len(result.removed_files)} files successfully")

    def _remove_directories(self, plan: CleanupPlan, result: CleanupResult) -> None:
        """Remove directories from the cleanup plan.

        Args:
            plan: CleanupPlan containing directories to remove
            result: CleanupResult to update with removal results
        """
        logger.info(f"Removing {len(plan.directories_to_remove)} directories...")

        for dir_path in plan.directories_to_remove:
            try:
                if not dir_path.exists():
                    logger.debug(
                        f"Directory already removed or doesn't exist: {dir_path}"
                    )
                    continue

                if not dir_path.is_dir():
                    logger.warning(f"Not a directory, skipping: {dir_path}")
                    continue

                # Calculate directory size before removal
                dir_size = 0
                with suppress(OSError):
                    dir_size = sum(
                        f.stat().st_size for f in dir_path.rglob("*") if f.is_file()
                    )

                # Remove the directory and all its contents
                shutil.rmtree(dir_path)
                result.removed_directories.append(dir_path)
                result.size_reduction += dir_size

                logger.debug(f"Removed directory: {dir_path}")

            except PermissionError as e:
                error_msg = f"Permission denied removing {dir_path}: {e}"
                logger.error(error_msg)
                result.errors.append(error_msg)

            except OSError as e:
                error_msg = f"Error removing {dir_path}: {e}"
                logger.error(error_msg)
                result.errors.append(error_msg)

        logger.info(
            f"Removed {len(result.removed_directories)} directories successfully"
        )

    def _move_files(self, plan: CleanupPlan, result: CleanupResult) -> None:
        """Move files according to the cleanup plan.

        Args:
            plan: CleanupPlan containing files to move
            result: CleanupResult to update with move results
        """
        logger.info(f"Moving {len(plan.files_to_move)} files...")

        for src_path, dst_path in plan.files_to_move.items():
            try:
                if not src_path.exists():
                    logger.debug(f"Source file doesn't exist: {src_path}")
                    continue

                if not src_path.is_file():
                    logger.warning(f"Source is not a file, skipping: {src_path}")
                    continue

                # Create destination directory if needed
                dst_path.parent.mkdir(parents=True, exist_ok=True)

                # Handle conflicts (existing files at destination)
                if dst_path.exists():
                    if dst_path.is_file():
                        # Create backup of existing file
                        backup_path = dst_path.with_suffix(dst_path.suffix + ".backup")
                        counter = 1
                        while backup_path.exists():
                            backup_path = dst_path.with_suffix(
                                f"{dst_path.suffix}.backup{counter}"
                            )
                            counter += 1

                        logger.warning(
                            f"Destination exists, backing up to {backup_path.name}"
                        )
                        shutil.move(str(dst_path), str(backup_path))
                    else:
                        error_msg = f"Destination exists and is not a file: {dst_path}"
                        logger.error(error_msg)
                        result.errors.append(error_msg)
                        continue

                # Move the file
                shutil.move(str(src_path), str(dst_path))
                result.moved_files[src_path] = dst_path

                logger.debug(f"Moved file: {src_path} -> {dst_path}")

            except PermissionError as e:
                error_msg = f"Permission denied moving {src_path} to {dst_path}: {e}"
                logger.error(error_msg)
                result.errors.append(error_msg)

            except OSError as e:
                error_msg = f"Error moving {src_path} to {dst_path}: {e}"
                logger.error(error_msg)
                result.errors.append(error_msg)

        logger.info(f"Moved {len(result.moved_files)} files successfully")

    def _remove_dependencies(self, plan: CleanupPlan, result: CleanupResult) -> None:
        """Remove unused dependencies from pyproject.toml.

        Args:
            plan: CleanupPlan containing dependencies to remove
            result: CleanupResult to update with removal results
        """
        if not plan.dependencies_to_remove:
            logger.debug("No dependencies to remove")
            return

        logger.info(f"Removing {len(plan.dependencies_to_remove)} dependencies...")

        pyproject_path = self.project_root / "pyproject.toml"
        if not pyproject_path.exists():
            error_msg = "pyproject.toml not found, cannot remove dependencies"
            logger.error(error_msg)
            result.errors.append(error_msg)
            return

        if tomllib is None:
            error_msg = "tomllib/tomli not available, cannot remove dependencies"
            logger.error(error_msg)
            result.errors.append(error_msg)
            return

        try:
            # Read current pyproject.toml
            with pyproject_path.open("rb") as f:
                pyproject_data = tomllib.load(f)

            # Create backup of pyproject.toml
            backup_path = pyproject_path.with_suffix(".toml.backup")
            shutil.copy2(pyproject_path, backup_path)
            logger.info(f"Created backup: {backup_path}")

            # Remove dependencies from the data structure
            modified = False
            if (
                "project" in pyproject_data
                and "dependencies" in pyproject_data["project"]
            ):
                original_deps = pyproject_data["project"]["dependencies"]
                if isinstance(original_deps, list):
                    # Filter out dependencies to remove
                    new_deps = []
                    for dep in original_deps:
                        if isinstance(dep, str):
                            # Extract package name
                            dep_name = (
                                dep.split("[")[0]
                                .split(">=")[0]
                                .split("==")[0]
                                .split("<")[0]
                                .split(">")[0]
                                .strip()
                            )

                            if dep_name in plan.dependencies_to_remove:
                                logger.info(f"Removing dependency: {dep_name}")
                                result.removed_dependencies.append(dep_name)
                                modified = True
                            else:
                                new_deps.append(dep)
                        else:
                            new_deps.append(dep)

                    pyproject_data["project"]["dependencies"] = new_deps

            if not modified:
                logger.warning(
                    "No dependencies were actually removed from pyproject.toml"
                )
                return

            # Write updated pyproject.toml
            # Note: We need to use toml library for writing, not tomllib
            try:
                import toml  # type: ignore[import-not-found]  # noqa: PLC0415

                with pyproject_path.open("w", encoding="utf-8") as f:
                    toml.dump(pyproject_data, f)

                logger.info("Updated pyproject.toml")

            except ImportError:
                # If toml library not available, write manually (basic approach)
                logger.warning("toml library not available, using basic TOML writing")
                # For now, just log that we can't write
                error_msg = (
                    "Cannot write pyproject.toml without toml library. "
                    "Dependencies identified but not removed."
                )
                logger.error(error_msg)
                result.errors.append(error_msg)
                # Restore backup
                shutil.copy2(backup_path, pyproject_path)
                return

            # Run uv lock to update lock file
            logger.info("Updating lock file with uv lock...")
            try:
                subprocess.run(
                    ["uv", "lock"],
                    cwd=self.project_root,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                logger.info("Lock file updated successfully")

            except subprocess.CalledProcessError as e:
                error_msg = f"Failed to update lock file: {e.stderr}"
                logger.error(error_msg)
                result.errors.append(error_msg)
                # Restore backup
                shutil.copy2(backup_path, pyproject_path)
                result.removed_dependencies.clear()

            except subprocess.TimeoutExpired:
                error_msg = "Lock file update timed out"
                logger.error(error_msg)
                result.errors.append(error_msg)
                # Restore backup
                shutil.copy2(backup_path, pyproject_path)
                result.removed_dependencies.clear()

            except FileNotFoundError:
                error_msg = "uv command not found, cannot update lock file"
                logger.error(error_msg)
                result.errors.append(error_msg)
                # Keep the changes but warn user
                logger.warning(
                    "Dependencies removed from pyproject.toml but lock file not updated"
                )

        except Exception as e:
            error_msg = f"Error removing dependencies: {e}"
            logger.error(error_msg)
            result.errors.append(error_msg)

        logger.info(
            f"Removed {len(result.removed_dependencies)} dependencies successfully"
        )

    def _calculate_actual_size_reduction(self, result: CleanupResult) -> int:
        """Calculate actual size reduction from cleanup result.

        Args:
            result: CleanupResult containing removed items

        Returns:
            Total size reduction in bytes
        """
        # Size reduction is already tracked in result.size_reduction
        # during file and directory removal
        return result.size_reduction
