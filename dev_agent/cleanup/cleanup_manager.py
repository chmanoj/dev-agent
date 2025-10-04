"""Cleanup manager for repository maintenance operations."""

from __future__ import annotations

import ast
import logging
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
        plan: CleanupPlan,  # noqa: ARG002
        dry_run: bool = True,
    ) -> CleanupResult:
        """Execute the cleanup plan.

        Args:
            plan: CleanupPlan to execute
            dry_run: If True, only simulate cleanup without making changes

        Returns:
            CleanupResult containing execution results
        """
        logger.info(f"Executing cleanup plan ({'dry-run' if dry_run else 'actual'})...")

        result = CleanupResult()

        # TODO: Implement cleanup execution
        # This is a stub that will be implemented in task 6

        if dry_run:
            logger.info("Dry-run complete - no changes made")
        else:
            logger.info(
                f"Cleanup complete: {result.success_count} operations succeeded, "
                f"{result.error_count} errors"
            )

        return result

    def generate_cleanup_report(self, result: CleanupResult) -> str:  # noqa: ARG002
        """Generate a markdown cleanup report.

        Args:
            result: CleanupResult to generate report from

        Returns:
            Markdown-formatted cleanup report
        """
        logger.debug("Generating cleanup report...")

        # TODO: Implement cleanup report generation
        # This is a stub that will be implemented in task 6.6

        report = "# Cleanup Report\n\nReport generation not yet implemented.\n"

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
