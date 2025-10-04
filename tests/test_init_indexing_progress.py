"""Tests for init command indexing progress display for existing codebases."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from rich.console import Console

from dev_agent.cli.main import _run_indexing_with_progress
from dev_agent.models.indexing import ASTIndex
from dev_agent.models.results import IndexResult
from dev_agent.onboarding.journey_manager import ProjectContext


@pytest.fixture
def mock_workflow_manager():
    """Create a mock workflow manager."""
    manager = Mock()
    manager.cost_tracker = Mock()
    manager.cost_tracker.get_current_cost.return_value = 0.0123
    manager.current_project_state = Mock()
    manager.state_manager = Mock()
    manager.phase_manager = None
    return manager


@pytest.fixture
def mock_project_context():
    """Create a mock project context."""
    return ProjectContext(
        path=Path("/test/project"),
        project_type="existing",
        has_code=True,
        languages_detected=["Python", "JavaScript"],
        estimated_size="medium",
        complexity="moderate",
        file_count=150,
    )


@pytest.fixture
def mock_console():
    """Create a mock console."""
    return Mock(spec=Console)


@pytest.fixture
def mock_config_manager():
    """Create a mock config manager."""
    config = Mock()
    config.azure_openai = Mock()
    config.azure_openai.endpoint = "https://test.openai.azure.com/"
    config.azure_openai.api_key = "test-key"
    config.azure_openai.deployment_name = "gpt-4"
    config.azure_openai.embedding_deployment = "text-embedding-ada-002"
    return config


class TestRunIndexingWithProgress:
    """Test the _run_indexing_with_progress helper function."""

    def test_function_exists(self):
        """Test that the _run_indexing_with_progress function exists and is callable."""
        assert callable(_run_indexing_with_progress)
