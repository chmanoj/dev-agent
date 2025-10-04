"""Tests for journey manager."""

# ruff: noqa: S108, ARG002, PT019

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dev_agent.models.enums import PhaseType
from dev_agent.onboarding.journey_manager import JourneyManager, ProjectContext


@pytest.fixture
def journey_manager(tmp_path: Path) -> JourneyManager:
    """Create journey manager with temporary config path."""
    config_path = tmp_path / "config.json"
    return JourneyManager(config_path=config_path)


@pytest.fixture
def empty_project_dir(tmp_path: Path) -> Path:
    """Create an empty project directory."""
    project_dir = tmp_path / "empty_project"
    project_dir.mkdir()
    return project_dir


@pytest.fixture
def python_project_dir(tmp_path: Path) -> Path:
    """Create a small Python project directory."""
    project_dir = tmp_path / "python_project"
    project_dir.mkdir()

    # Create some Python files
    (project_dir / "main.py").write_text("print('hello')")
    (project_dir / "utils.py").write_text("def helper(): pass")
    (project_dir / "tests").mkdir()
    (project_dir / "tests" / "test_main.py").write_text("def test_main(): pass")

    return project_dir


@pytest.fixture
def large_project_dir(tmp_path: Path) -> Path:
    """Create a large multi-language project directory."""
    project_dir = tmp_path / "large_project"
    project_dir.mkdir()

    # Create many files
    for i in range(100):
        (project_dir / f"file_{i}.py").write_text(f"# File {i}")

    # Add some JavaScript files
    js_dir = project_dir / "frontend"
    js_dir.mkdir()
    for i in range(50):
        (js_dir / f"component_{i}.js").write_text(f"// Component {i}")

    return project_dir


class TestDetectProjectType:
    """Tests for detect_project_type method."""

    def test_detect_nonexistent_directory(self, journey_manager: JourneyManager, tmp_path: Path):
        """Test detection of non-existent directory."""
        nonexistent = tmp_path / "does_not_exist"
        context = journey_manager.detect_project_type(nonexistent)

        assert context.project_type == "new"
        assert not context.has_code
        assert context.file_count == 0
        assert context.estimated_size == "small"
        assert context.complexity == "simple"

    def test_detect_empty_directory(self, journey_manager: JourneyManager, empty_project_dir: Path):
        """Test detection of empty directory."""
        context = journey_manager.detect_project_type(empty_project_dir)

        assert context.project_type == "new"
        assert not context.has_code
        assert context.file_count == 0
        assert context.estimated_size == "small"
        assert context.complexity == "simple"

    def test_detect_small_python_project(self, journey_manager: JourneyManager, python_project_dir: Path):
        """Test detection of small Python project."""
        context = journey_manager.detect_project_type(python_project_dir)

        assert context.project_type == "existing"
        assert context.has_code
        assert "Python" in context.languages_detected
        assert context.file_count > 0
        assert context.estimated_size == "small"
        assert context.complexity == "simple"

    def test_detect_large_multi_language_project(
        self,
        journey_manager: JourneyManager,
        large_project_dir: Path,
    ):
        """Test detection of large multi-language project."""
        context = journey_manager.detect_project_type(large_project_dir)

        assert context.project_type == "existing"
        assert context.has_code
        assert "Python" in context.languages_detected
        assert "JavaScript" in context.languages_detected
        assert context.file_count > 100
        assert context.estimated_size in ["medium", "large"]
        assert context.complexity in ["moderate", "complex"]

    def test_ignores_common_directories(self, journey_manager: JourneyManager, tmp_path: Path):
        """Test that common directories are ignored."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Create files in ignored directories
        (project_dir / ".git").mkdir()
        (project_dir / ".git" / "config").write_text("git config")

        (project_dir / "node_modules").mkdir()
        (project_dir / "node_modules" / "package.js").write_text("// package")

        (project_dir / "__pycache__").mkdir()
        (project_dir / "__pycache__" / "cache.pyc").write_text("cache")

        # Create actual code file
        (project_dir / "main.py").write_text("print('hello')")

        context = journey_manager.detect_project_type(project_dir)

        # Should only count the main.py file
        assert context.has_code
        assert context.file_count == 1


class TestIsFirstRun:
    """Tests for is_first_run method."""

    def test_first_run_when_config_missing(self, journey_manager: JourneyManager):
        """Test first run detection when config doesn't exist."""
        assert journey_manager.is_first_run()

    def test_not_first_run_when_config_exists(self, journey_manager: JourneyManager):
        """Test first run detection when config exists."""
        # Create config file
        journey_manager.config_path.parent.mkdir(parents=True, exist_ok=True)
        journey_manager.config_path.write_text("{}")

        assert not journey_manager.is_first_run()


class TestGetOnboardingFlow:
    """Tests for get_onboarding_flow method."""

    def test_new_project_flow(self, journey_manager: JourneyManager):
        """Test onboarding flow for new project."""
        context = ProjectContext(
            path=Path("/tmp/new_project"),
            project_type="new",
            has_code=False,
        )

        flow = journey_manager.get_onboarding_flow(context)

        assert len(flow.steps) > 0
        assert len(flow.tips) > 0
        assert any("new project" in step.description.lower() for step in flow.steps)
        assert any("template" in step.title.lower() for step in flow.steps)

    def test_existing_codebase_flow(self, journey_manager: JourneyManager):
        """Test onboarding flow for existing codebase."""
        context = ProjectContext(
            path=Path("/tmp/existing_project"),
            project_type="existing",
            has_code=True,
            languages_detected=["Python", "JavaScript"],
            file_count=150,
            estimated_size="medium",
            complexity="moderate",
        )

        flow = journey_manager.get_onboarding_flow(context)

        assert len(flow.steps) > 0
        assert len(flow.tips) > 0
        assert len(flow.warnings) > 0
        assert any("index" in step.title.lower() for step in flow.steps)
        assert any("150 files" in step.description for step in flow.steps)

    def test_flow_includes_azure_config_step(self, journey_manager: JourneyManager):
        """Test that all flows include Azure OpenAI configuration."""
        new_context = ProjectContext(
            path=Path("/tmp/new"),
            project_type="new",
            has_code=False,
        )

        existing_context = ProjectContext(
            path=Path("/tmp/existing"),
            project_type="existing",
            has_code=True,
        )

        new_flow = journey_manager.get_onboarding_flow(new_context)
        existing_flow = journey_manager.get_onboarding_flow(existing_context)

        assert any("azure" in step.title.lower() for step in new_flow.steps)
        assert any("azure" in step.title.lower() for step in existing_flow.steps)


class TestGuideUserThroughPhase:
    """Tests for guide_user_through_phase method."""

    @patch("dev_agent.onboarding.journey_manager.Console")
    def test_indexing_phase_new_project(self, _mock_console: MagicMock, journey_manager: JourneyManager):
        """Test guidance for indexing phase in new project."""
        context = ProjectContext(
            path=Path("/tmp/new"),
            project_type="new",
            has_code=False,
        )

        # Should not raise any errors
        journey_manager.guide_user_through_phase(PhaseType.INDEXING, context)

    @patch("dev_agent.onboarding.journey_manager.Console")
    def test_indexing_phase_existing_project(
        self,
        mock_console: MagicMock,
        journey_manager: JourneyManager,
    ):
        """Test guidance for indexing phase in existing project."""
        context = ProjectContext(
            path=Path("/tmp/existing"),
            project_type="existing",
            has_code=True,
            file_count=200,
            estimated_size="medium",
        )

        # Should not raise any errors
        journey_manager.guide_user_through_phase(PhaseType.INDEXING, context)

    @patch("dev_agent.onboarding.journey_manager.Console")
    def test_specification_phase(self, mock_console: MagicMock, journey_manager: JourneyManager):
        """Test guidance for specification phase."""
        context = ProjectContext(
            path=Path("/tmp/project"),
            project_type="new",
            has_code=False,
        )

        # Should not raise any errors
        journey_manager.guide_user_through_phase(PhaseType.SPECIFICATION, context)

    @patch("dev_agent.onboarding.journey_manager.Console")
    def test_design_phase(self, mock_console: MagicMock, journey_manager: JourneyManager):
        """Test guidance for design phase."""
        context = ProjectContext(
            path=Path("/tmp/project"),
            project_type="existing",
            has_code=True,
        )

        # Should not raise any errors
        journey_manager.guide_user_through_phase(PhaseType.DESIGN, context)

    @patch("dev_agent.onboarding.journey_manager.Console")
    def test_implementation_phase(self, mock_console: MagicMock, journey_manager: JourneyManager):
        """Test guidance for implementation phase."""
        context = ProjectContext(
            path=Path("/tmp/project"),
            project_type="existing",
            has_code=True,
        )

        # Should not raise any errors
        journey_manager.guide_user_through_phase(PhaseType.IMPLEMENTATION, context)


class TestEstimateIndexingTime:
    """Tests for _estimate_indexing_time method."""

    def test_small_project_time(self, journey_manager: JourneyManager):
        """Test time estimate for small project."""
        context = ProjectContext(
            path=Path("/tmp/small"),
            project_type="existing",
            has_code=True,
            file_count=30,
        )

        time_estimate = journey_manager._estimate_indexing_time(context)
        assert "1-2 minutes" in time_estimate

    def test_medium_project_time(self, journey_manager: JourneyManager):
        """Test time estimate for medium project."""
        context = ProjectContext(
            path=Path("/tmp/medium"),
            project_type="existing",
            has_code=True,
            file_count=150,
        )

        time_estimate = journey_manager._estimate_indexing_time(context)
        assert "3-5 minutes" in time_estimate

    def test_large_project_time(self, journey_manager: JourneyManager):
        """Test time estimate for large project."""
        context = ProjectContext(
            path=Path("/tmp/large"),
            project_type="existing",
            has_code=True,
            file_count=600,
        )

        time_estimate = journey_manager._estimate_indexing_time(context)
        assert "10-20 minutes" in time_estimate


class TestEstimateIndexingCost:
    """Tests for _estimate_indexing_cost method."""

    def test_small_project_cost(self, journey_manager: JourneyManager):
        """Test cost estimate for small project."""
        context = ProjectContext(
            path=Path("/tmp/small"),
            project_type="existing",
            has_code=True,
            file_count=10,
        )

        cost_estimate = journey_manager._estimate_indexing_cost(context)
        assert "$" in cost_estimate
        assert "0.01" in cost_estimate or "<" in cost_estimate

    def test_large_project_cost(self, journey_manager: JourneyManager):
        """Test cost estimate for large project."""
        context = ProjectContext(
            path=Path("/tmp/large"),
            project_type="existing",
            has_code=True,
            file_count=1000,
        )

        cost_estimate = journey_manager._estimate_indexing_cost(context)
        assert "$" in cost_estimate


class TestDisplayProjectSummary:
    """Tests for display_project_summary method."""

    @patch("dev_agent.onboarding.journey_manager.Console")
    def test_display_new_project_summary(self, mock_console: MagicMock, journey_manager: JourneyManager):
        """Test displaying summary for new project."""
        context = ProjectContext(
            path=Path("/tmp/new"),
            project_type="new",
            has_code=False,
            file_count=0,
            estimated_size="small",
            complexity="simple",
        )

        # Should not raise any errors
        journey_manager.display_project_summary(context)

    @patch("dev_agent.onboarding.journey_manager.Console")
    def test_display_existing_project_summary(
        self,
        mock_console: MagicMock,
        journey_manager: JourneyManager,
    ):
        """Test displaying summary for existing project."""
        context = ProjectContext(
            path=Path("/tmp/existing"),
            project_type="existing",
            has_code=True,
            languages_detected=["Python", "JavaScript", "TypeScript"],
            file_count=250,
            estimated_size="medium",
            complexity="moderate",
        )

        # Should not raise any errors
        journey_manager.display_project_summary(context)


class TestProjectContext:
    """Tests for ProjectContext dataclass."""

    def test_project_context_creation(self):
        """Test creating ProjectContext."""
        context = ProjectContext(
            path=Path("/tmp/project"),
            project_type="existing",
            has_code=True,
            languages_detected=["Python"],
            estimated_size="small",
            complexity="simple",
            file_count=50,
        )

        assert context.path == Path("/tmp/project")
        assert context.project_type == "existing"
        assert context.has_code
        assert "Python" in context.languages_detected
        assert context.file_count == 50

    def test_project_context_defaults(self):
        """Test ProjectContext with default values."""
        context = ProjectContext(
            path=Path("/tmp/project"),
            project_type="new",
            has_code=False,
        )

        assert context.languages_detected == []
        assert context.estimated_size == "unknown"
        assert context.complexity == "unknown"
        assert context.file_count == 0
