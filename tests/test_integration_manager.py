"""Tests for integration manager."""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from dev_agent.config.customization_manager import ToolConfig
from dev_agent.config.integration_manager import (
    BaseIntegration,
    CustomIntegration,
    DockerIntegration,
    GitIntegration,
    IntegrationManager,
    IntegrationResult,
    PythonToolIntegration,
)


class TestIntegrationResult:
    """Test integration result."""

    def test_successful_result(self):
        """Test successful integration result."""
        result = IntegrationResult(
            success=True,
            output="Command executed successfully",
            exit_code=0,
        )
        
        assert result.success is True
        assert result.output == "Command executed successfully"
        assert result.error == ""
        assert result.exit_code == 0

    def test_failed_result(self):
        """Test failed integration result."""
        result = IntegrationResult(
            success=False,
            error="Command failed",
            exit_code=1,
        )
        
        assert result.success is False
        assert result.error == "Command failed"
        assert result.exit_code == 1


class TestGitIntegration:
    """Test Git integration."""

    @pytest.fixture
    def git_config(self):
        """Create Git tool config."""
        return ToolConfig(
            tool_name="git",
            enabled=True,
        )

    @pytest.fixture
    def git_integration(self, git_config):
        """Create Git integration."""
        return GitIntegration("git", git_config)

    @patch('subprocess.run')
    def test_git_initialization_success(self, mock_run, git_integration):
        """Test successful Git initialization."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="git version 2.34.1",
            stderr="",
        )
        
        success = git_integration.initialize()
        
        assert success is True
        assert git_integration.is_initialized is True
        mock_run.assert_called_once_with(
            ["git", "--version"],
            capture_output=True,
            text=True,
            cwd=None,
            timeout=30,
            check=False,
        )

    @patch('subprocess.run')
    def test_git_initialization_failure(self, mock_run, git_integration):
        """Test failed Git initialization."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="git: command not found",
        )
        
        success = git_integration.initialize()
        
        assert success is False
        assert git_integration.is_initialized is False

    @patch('subprocess.run')
    def test_git_execute_command(self, mock_run, git_integration):
        """Test Git command execution."""
        # Initialize first
        mock_run.return_value = Mock(returncode=0, stdout="git version 2.34.1", stderr="")
        git_integration.initialize()
        
        # Execute command
        mock_run.return_value = Mock(
            returncode=0,
            stdout="On branch main\nnothing to commit, working tree clean",
            stderr="",
        )
        
        result = git_integration.execute_command("status")
        
        assert result.success is True
        assert "main" in result.output
        assert result.exit_code == 0

    @patch('subprocess.run')
    def test_git_get_status(self, mock_run, git_integration):
        """Test Git status retrieval."""
        # Initialize
        mock_run.return_value = Mock(returncode=0, stdout="git version 2.34.1", stderr="")
        git_integration.initialize()
        
        # Mock status and branch commands
        def mock_run_side_effect(cmd, **kwargs):
            if "status" in cmd:
                return Mock(returncode=0, stdout=" M file.py\n", stderr="")
            elif "branch" in cmd:
                return Mock(returncode=0, stdout="main\n", stderr="")
            return Mock(returncode=0, stdout="", stderr="")
        
        mock_run.side_effect = mock_run_side_effect
        
        status = git_integration.get_status()
        
        assert status["initialized"] is True
        assert status["has_changes"] is True
        assert status["current_branch"] == "main"

    @patch('subprocess.run')
    def test_git_create_commit(self, mock_run, git_integration):
        """Test Git commit creation."""
        # Initialize
        mock_run.return_value = Mock(returncode=0, stdout="git version 2.34.1", stderr="")
        git_integration.initialize()
        
        # Mock add and commit commands
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        result = git_integration.create_commit("Test commit", ["file.py"])
        
        assert result.success is True
        assert mock_run.call_count >= 2  # At least add and commit calls


class TestDockerIntegration:
    """Test Docker integration."""

    @pytest.fixture
    def docker_config(self):
        """Create Docker tool config."""
        return ToolConfig(
            tool_name="docker",
            enabled=True,
        )

    @pytest.fixture
    def docker_integration(self, docker_config):
        """Create Docker integration."""
        return DockerIntegration("docker", docker_config)

    @patch('subprocess.run')
    def test_docker_initialization_success(self, mock_run, docker_integration):
        """Test successful Docker initialization."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Docker version 20.10.17",
            stderr="",
        )
        
        success = docker_integration.initialize()
        
        assert success is True
        assert docker_integration.is_initialized is True

    @patch('subprocess.run')
    def test_docker_build_image(self, mock_run, docker_integration):
        """Test Docker image building."""
        # Initialize
        mock_run.return_value = Mock(returncode=0, stdout="Docker version 20.10.17", stderr="")
        docker_integration.initialize()
        
        # Mock build command
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Successfully built abc123\nSuccessfully tagged myapp:latest",
            stderr="",
        )
        
        dockerfile_path = Path("/tmp/Dockerfile")
        result = docker_integration.build_image(dockerfile_path, "myapp:latest")
        
        assert result.success is True
        assert "Successfully built" in result.output


class TestPythonToolIntegration:
    """Test Python tool integration."""

    @pytest.fixture
    def pytest_config(self):
        """Create pytest tool config."""
        return ToolConfig(
            tool_name="pytest",
            enabled=True,
        )

    @pytest.fixture
    def pytest_integration(self, pytest_config):
        """Create pytest integration."""
        return PythonToolIntegration("pytest", pytest_config)

    @patch('subprocess.run')
    def test_pytest_initialization_success(self, mock_run, pytest_integration):
        """Test successful pytest initialization."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="pytest 7.2.0",
            stderr="",
        )
        
        success = pytest_integration.initialize()
        
        assert success is True
        assert pytest_integration.is_initialized is True

    @patch('subprocess.run')
    def test_pytest_run_tests(self, mock_run, pytest_integration):
        """Test running tests with pytest."""
        # Initialize
        mock_run.return_value = Mock(returncode=0, stdout="pytest 7.2.0", stderr="")
        pytest_integration.initialize()
        
        # Mock test run
        mock_run.return_value = Mock(
            returncode=0,
            stdout="===== 5 passed in 2.34s =====",
            stderr="",
        )
        
        result = pytest_integration.run_tests("tests/")
        
        assert result.success is True
        assert "5 passed" in result.output

    @patch('subprocess.run')
    def test_ruff_format_code(self, mock_run):
        """Test code formatting with ruff."""
        ruff_config = ToolConfig(tool_name="ruff", enabled=True)
        ruff_integration = PythonToolIntegration("ruff", ruff_config)
        
        # Initialize
        mock_run.return_value = Mock(returncode=0, stdout="ruff 0.1.0", stderr="")
        ruff_integration.initialize()
        
        # Mock format command
        mock_run.return_value = Mock(returncode=0, stdout="2 files reformatted", stderr="")
        
        result = ruff_integration.format_code(["file1.py", "file2.py"])
        
        assert result.success is True
        assert "reformatted" in result.output

    @patch('subprocess.run')
    def test_mypy_check_types(self, mock_run):
        """Test type checking with mypy."""
        mypy_config = ToolConfig(tool_name="mypy", enabled=True)
        mypy_integration = PythonToolIntegration("mypy", mypy_config)
        
        # Initialize
        mock_run.return_value = Mock(returncode=0, stdout="mypy 1.0.0", stderr="")
        mypy_integration.initialize()
        
        # Mock type check
        mock_run.return_value = Mock(returncode=0, stdout="Success: no issues found", stderr="")
        
        result = mypy_integration.check_types(["src/"])
        
        assert result.success is True
        assert "Success" in result.output


class TestCustomIntegration:
    """Test custom integration."""

    @pytest.fixture
    def custom_config(self):
        """Create custom tool config."""
        return ToolConfig(
            tool_name="custom_tool",
            enabled=True,
            configuration={
                "executable": "custom_tool",
                "version_command": ["--version"],
            },
            custom_commands={
                "analyze": "analyze --verbose",
                "report": "report --format json",
            },
        )

    @pytest.fixture
    def custom_integration(self, custom_config):
        """Create custom integration."""
        return CustomIntegration("custom_tool", custom_config)

    @patch('subprocess.run')
    def test_custom_initialization_success(self, mock_run, custom_integration):
        """Test successful custom tool initialization."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="custom_tool version 1.0.0",
            stderr="",
        )
        
        success = custom_integration.initialize()
        
        assert success is True
        assert custom_integration.is_initialized is True

    @patch('subprocess.run')
    def test_custom_execute_command(self, mock_run, custom_integration):
        """Test custom command execution."""
        # Initialize
        mock_run.return_value = Mock(returncode=0, stdout="custom_tool version 1.0.0", stderr="")
        custom_integration.initialize()
        
        # Execute custom command
        mock_run.return_value = Mock(returncode=0, stdout="Analysis complete", stderr="")
        
        result = custom_integration.execute_command("analyze", ["--input", "file.py"])
        
        assert result.success is True
        assert "Analysis complete" in result.output

    @patch('subprocess.run')
    def test_custom_command_mapping(self, mock_run, custom_integration):
        """Test custom command mapping."""
        # Initialize
        mock_run.return_value = Mock(returncode=0, stdout="custom_tool version 1.0.0", stderr="")
        custom_integration.initialize()
        
        # Execute mapped command
        mock_run.return_value = Mock(returncode=0, stdout="Report generated", stderr="")
        
        result = custom_integration.execute_command("report", ["output.json"])
        
        assert result.success is True
        # Should use the mapped command from custom_commands


class TestIntegrationManager:
    """Test integration manager."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def manager(self, temp_config_dir):
        """Create integration manager with temp directory."""
        return IntegrationManager(temp_config_dir)

    def test_manager_initialization(self, manager):
        """Test manager initialization."""
        assert manager.config_dir.exists()
        assert isinstance(manager.registry.integration_types, dict)
        assert "git" in manager.registry.integration_types
        assert "docker" in manager.registry.integration_types

    @patch('subprocess.run')
    def test_add_integration_success(self, mock_run, manager):
        """Test successful integration addition."""
        mock_run.return_value = Mock(returncode=0, stdout="git version 2.34.1", stderr="")
        
        git_config = ToolConfig(tool_name="git", enabled=True)
        success = manager.add_integration("git", "git", git_config)
        
        assert success is True
        assert "git" in manager.list_integrations()

    def test_add_duplicate_integration(self, manager):
        """Test adding duplicate integration."""
        git_config = ToolConfig(tool_name="git", enabled=True)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="git version 2.34.1", stderr="")
            manager.add_integration("git", "git", git_config)
        
        # Try to add again
        success = manager.add_integration("git", "git", git_config)
        assert success is False

    @patch('subprocess.run')
    def test_remove_integration(self, mock_run, manager):
        """Test integration removal."""
        mock_run.return_value = Mock(returncode=0, stdout="git version 2.34.1", stderr="")
        
        git_config = ToolConfig(tool_name="git", enabled=True)
        manager.add_integration("git", "git", git_config)
        
        assert "git" in manager.list_integrations()
        
        success = manager.remove_integration("git")
        assert success is True
        assert "git" not in manager.list_integrations()

    @patch('subprocess.run')
    def test_execute_integration_command(self, mock_run, manager):
        """Test executing integration command."""
        # Add integration
        mock_run.return_value = Mock(returncode=0, stdout="git version 2.34.1", stderr="")
        git_config = ToolConfig(tool_name="git", enabled=True)
        manager.add_integration("git", "git", git_config)
        
        # Execute command
        mock_run.return_value = Mock(returncode=0, stdout="On branch main", stderr="")
        result = manager.execute_integration_command("git", "status")
        
        assert result.success is True
        assert "main" in result.output

    def test_execute_nonexistent_integration_command(self, manager):
        """Test executing command on nonexistent integration."""
        result = manager.execute_integration_command("nonexistent", "status")
        
        assert result.success is False
        assert "not found" in result.error

    @patch('subprocess.run')
    def test_get_all_status(self, mock_run, manager):
        """Test getting status of all integrations."""
        # Add multiple integrations
        mock_run.return_value = Mock(returncode=0, stdout="version info", stderr="")
        
        git_config = ToolConfig(tool_name="git", enabled=True)
        docker_config = ToolConfig(tool_name="docker", enabled=True)
        
        manager.add_integration("git", "git", git_config)
        manager.add_integration("docker", "docker", docker_config)
        
        status = manager.get_all_status()
        
        assert "git" in status
        assert "docker" in status
        assert status["git"]["initialized"] is True
        assert status["docker"]["initialized"] is True

    @patch('subprocess.run')
    def test_test_integration(self, mock_run, manager):
        """Test integration testing."""
        mock_run.return_value = Mock(returncode=0, stdout="git version 2.34.1", stderr="")
        
        git_config = ToolConfig(tool_name="git", enabled=True)
        manager.add_integration("git", "git", git_config)
        
        is_working = manager.test_integration("git")
        assert is_working is True
        
        is_working = manager.test_integration("nonexistent")
        assert is_working is False

    @patch('subprocess.run')
    def test_setup_common_integrations(self, mock_run, manager):
        """Test setting up common integrations."""
        # Mock successful initialization for all tools
        mock_run.return_value = Mock(returncode=0, stdout="version info", stderr="")
        
        results = manager.setup_common_integrations()
        
        assert isinstance(results, dict)
        assert "git" in results
        assert "docker" in results
        assert "pytest" in results

    def test_cleanup_all(self, manager):
        """Test cleaning up all integrations."""
        # Add some integrations first
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="version info", stderr="")
            git_config = ToolConfig(tool_name="git", enabled=True)
            manager.add_integration("git", "git", git_config)
        
        assert len(manager.list_integrations()) > 0
        
        manager.cleanup_all()
        
        assert len(manager.list_integrations()) == 0

    @patch('subprocess.run')
    def test_integration_persistence(self, mock_run, temp_config_dir):
        """Test integration configuration persistence."""
        mock_run.return_value = Mock(returncode=0, stdout="git version 2.34.1", stderr="")
        
        # Create manager and add integration
        manager1 = IntegrationManager(temp_config_dir)
        git_config = ToolConfig(tool_name="git", enabled=True)
        manager1.add_integration("git", "git", git_config)
        
        # Create new manager instance (should load saved integrations)
        manager2 = IntegrationManager(temp_config_dir)
        
        # Check that integration was loaded
        assert "git" in manager2.list_integrations()

    def test_subprocess_timeout_handling(self):
        """Test subprocess timeout handling."""
        git_config = ToolConfig(tool_name="git", enabled=True)
        integration = GitIntegration("git", git_config)
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("git", 30)
            
            result = integration._run_subprocess(["git", "--version"], timeout=1)
            
            assert result.success is False
            assert "timed out" in result.error.lower()
            assert result.exit_code == -1

    def test_subprocess_exception_handling(self):
        """Test subprocess exception handling."""
        git_config = ToolConfig(tool_name="git", enabled=True)
        integration = GitIntegration("git", git_config)
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception("Unexpected error")
            
            result = integration._run_subprocess(["git", "--version"])
            
            assert result.success is False
            assert "Unexpected error" in result.error
            assert result.exit_code == -1