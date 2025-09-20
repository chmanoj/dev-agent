"""Tests for the enhanced CLI with Rich UI components."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from rich.console import Console

from dev_agent.cli.enhanced_cli import (
    ContextualHelpSystem,
    DocumentPreviewer,
    EnhancedCLI,
    ProgressManager,
)
from dev_agent.models.enums import PhaseType


class TestEnhancedCLI:
    """Test cases for the EnhancedCLI class."""

    @pytest.fixture
    def mock_workflow_manager(self):
        """Create a mock workflow manager."""
        mock_manager = Mock()
        mock_manager.get_current_phase.return_value = PhaseType.INDEXING
        mock_manager.execute_complete_workflow.return_value = True
        mock_manager.transition_to_phase.return_value = True
        return mock_manager

    @pytest.fixture
    def enhanced_cli(self, mock_workflow_manager):
        """Create an EnhancedCLI instance with mocked dependencies."""
        cli = EnhancedCLI(workflow_manager=mock_workflow_manager)
        return cli

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    def test_initialization(self, enhanced_cli):
        """Test EnhancedCLI initialization."""
        assert enhanced_cli.workflow_manager is not None
        assert enhanced_cli.session_active is False
        assert enhanced_cli.console is not None
        assert enhanced_cli.progress_manager is not None
        assert enhanced_cli.document_previewer is not None
        assert enhanced_cli.help_system is not None

    def test_handle_user_input_init_command(self, enhanced_cli, temp_project_dir):
        """Test handling of init command."""
        with patch.object(enhanced_cli, "init_command") as mock_init:
            result = enhanced_cli.handle_user_input(f"init {temp_project_dir}")

            mock_init.assert_called_once_with(temp_project_dir)
            assert "Project initialized" in result
            assert temp_project_dir in result

    def test_handle_user_input_status_command(self, enhanced_cli):
        """Test handling of status command."""
        result = enhanced_cli.handle_user_input("status")

        assert "Current phase" in result

    def test_handle_user_input_run_command(self, enhanced_cli):
        """Test handling of run command."""
        with patch.object(enhanced_cli.progress_manager, "progress") as mock_progress:
            mock_progress.__enter__ = Mock(return_value=mock_progress)
            mock_progress.__exit__ = Mock(return_value=None)

            result = enhanced_cli.handle_user_input("run")

            assert "completed successfully" in result

    def test_handle_user_input_phase_command(self, enhanced_cli):
        """Test handling of phase transition command."""
        result = enhanced_cli.handle_user_input("phase indexing")

        assert "Successfully transitioned" in result

    def test_handle_user_input_invalid_phase(self, enhanced_cli):
        """Test handling of invalid phase command."""
        result = enhanced_cli.handle_user_input("phase INVALID")

        assert "Invalid phase" in result
        assert "Valid phases" in result

    def test_handle_user_input_unknown_command(self, enhanced_cli):
        """Test handling of unknown command."""
        with patch.object(enhanced_cli.help_system, "show_command_suggestions") as mock_suggestions:
            result = enhanced_cli.handle_user_input("unknown_command")

            mock_suggestions.assert_called_once()
            assert result == ""

    def test_request_approval(self, enhanced_cli):
        """Test document approval request."""
        document_content = "# Test Document\nThis is a test document."

        with (
            patch("rich.prompt.Prompt.ask", return_value="y") as mock_prompt,
            patch.object(enhanced_cli.document_previewer, "show_document_preview") as mock_show,
        ):
            result = enhanced_cli.request_approval(document_content, "specification")

            mock_show.assert_called_once()
            mock_prompt.assert_called()
            assert result is True

    def test_display_progress(self, enhanced_cli):
        """Test progress display."""
        phase = PhaseType.INDEXING
        progress = 0.5

        with patch.object(enhanced_cli.progress_manager, "update_progress") as mock_update:
            enhanced_cli.display_progress(phase, progress)

            mock_update.assert_called_once_with(50)

    def test_init_command_new_project(self, enhanced_cli, temp_project_dir):
        """Test initializing a new project."""
        enhanced_cli.init_command(temp_project_dir)

        # Check that directories were created
        temp_path = Path(temp_project_dir)
        dev_agent_dir = temp_path / ".dev_agent"
        assert dev_agent_dir.exists()
        assert (dev_agent_dir / "documents").exists()
        assert (dev_agent_dir / "index").exists()

    def test_init_command_existing_project(self, enhanced_cli, temp_project_dir):
        """Test resuming an existing project."""
        # Create existing project structure
        temp_path = Path(temp_project_dir)
        dev_agent_dir = temp_path / ".dev_agent"
        (dev_agent_dir / "documents").mkdir(parents=True)
        (dev_agent_dir / "index").mkdir(parents=True)

        with patch.object(enhanced_cli, "display_message") as mock_display:
            enhanced_cli.init_command(temp_project_dir)

            # Should show resuming message
            mock_display.assert_called()
            call_args = [call[0][0] for call in mock_display.call_args_list]
            assert any("resuming" in arg.lower() for arg in call_args)

    def test_init_command_invalid_path(self, enhanced_cli):
        """Test initializing with invalid path."""
        invalid_path = "/nonexistent/path"

        with pytest.raises(ValueError, match="Project path does not exist"):
            enhanced_cli.init_command(invalid_path)

    def test_display_message(self, enhanced_cli):
        """Test message display."""
        message = "Test message"

        with patch.object(enhanced_cli.console, "print") as mock_print:
            enhanced_cli.display_message(message)

            mock_print.assert_called_once_with(message)

    def test_get_user_input(self, enhanced_cli):
        """Test user input retrieval."""
        prompt = "Enter something: "
        expected_input = "user input"

        with patch("rich.prompt.Prompt.ask", return_value=expected_input) as mock_prompt:
            result = enhanced_cli.get_user_input(prompt)

            mock_prompt.assert_called_once_with(prompt)
            assert result == expected_input

    def test_get_current_context_no_project(self, enhanced_cli):
        """Test getting context when no project is active."""
        enhanced_cli.workflow_manager = None

        context = enhanced_cli._get_current_context()

        assert context["session_active"] is False
        assert context["command_history_count"] == 0

    def test_get_current_context_with_project(self, enhanced_cli):
        """Test getting context when project is active."""
        context = enhanced_cli._get_current_context()

        assert context["session_active"] is False
        assert context["current_phase"] == PhaseType.INDEXING


class TestProgressManager:
    """Test cases for the ProgressManager class."""

    @pytest.fixture
    def console(self):
        """Create a Rich console instance."""
        return Console()

    @pytest.fixture
    def progress_manager(self, console):
        """Create a ProgressManager instance."""
        return ProgressManager(console)

    def test_initialization(self, progress_manager, console):
        """Test ProgressManager initialization."""
        assert progress_manager.console == console
        assert progress_manager.current_task is None
        assert progress_manager.phase_start_times == {}
        assert progress_manager.phase_estimates is not None

    def test_start_phase_progress(self, progress_manager):
        """Test starting phase progress."""
        phase = PhaseType.INDEXING
        
        with patch.object(progress_manager.progress, "add_task", return_value="task_id") as mock_add:
            task_id = progress_manager.start_phase_progress(phase)
            
            assert task_id == "task_id"
            mock_add.assert_called_once()

    def test_update_progress(self, progress_manager):
        """Test updating progress."""
        progress_manager.current_task = "task_id"
        
        with patch.object(progress_manager.progress, "update") as mock_update:
            progress_manager.update_progress(50, "Test status")
            
            mock_update.assert_called_once()

    def test_complete_phase(self, progress_manager):
        """Test completing a phase."""
        phase = PhaseType.INDEXING
        progress_manager.current_task = "task_id"
        progress_manager.phase_start_times[phase] = progress_manager.phase_start_times.get(phase, progress_manager.phase_start_times.setdefault(phase, Mock()))
        
        with patch.object(progress_manager.progress, "update") as mock_update:
            progress_manager.complete_phase(phase)
            
            mock_update.assert_called_once_with("task_id", completed=100)

    def test_show_phase_summary(self, progress_manager):
        """Test showing phase summary."""
        completed_phases = [PhaseType.INDEXING]
        
        with patch.object(progress_manager.console, "print") as mock_print:
            progress_manager.show_phase_summary(completed_phases)
            
            mock_print.assert_called_once()





class TestDocumentPreviewer:
    """Test cases for the DocumentPreviewer class."""

    @pytest.fixture
    def console(self):
        """Create a Rich console instance."""
        return Console()

    @pytest.fixture
    def document_previewer(self, console):
        """Create a DocumentPreviewer instance."""
        return DocumentPreviewer(console)

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    def test_initialization(self, document_previewer, console):
        """Test DocumentPreviewer initialization."""
        assert document_previewer.console == console

    def test_show_document_preview(self, document_previewer):
        """Test showing a document with syntax highlighting."""
        content = "# Test Document\nThis is a test."
        document_type = "specification"

        with patch.object(document_previewer.console, "print") as mock_print:
            document_previewer.show_document_preview(content, document_type)

            mock_print.assert_called_once()

    def test_show_diff_view_with_changes(self, document_previewer):
        """Test showing diff with actual changes."""
        old_content = "line 1\nline 2\nline 3"
        new_content = "line 1\nmodified line 2\nline 3"

        with patch.object(document_previewer.console, "print") as mock_print:
            document_previewer.show_diff_view(old_content, new_content, "Test Changes")

            mock_print.assert_called_once()

    def test_show_diff_view_no_changes(self, document_previewer):
        """Test showing diff with no changes."""
        content = "line 1\nline 2\nline 3"

        with patch.object(document_previewer.console, "print") as mock_print:
            document_previewer.show_diff_view(content, content)

            mock_print.assert_called_once()

    def test_show_file_tree(self, document_previewer, temp_project_dir):
        """Test showing project file tree."""
        with patch.object(document_previewer.console, "print") as mock_print:
            document_previewer.show_file_tree(temp_project_dir)

            mock_print.assert_called_once()

    def test_get_file_icon(self, document_previewer):
        """Test file icon selection for different extensions."""
        assert document_previewer._get_file_icon(".py") == "🐍"
        assert document_previewer._get_file_icon(".js") == "📜"
        assert document_previewer._get_file_icon(".md") == "📝"
        assert document_previewer._get_file_icon(".unknown") == "📄"


class TestContextualHelpSystem:
    """Test cases for the ContextualHelpSystem class."""

    @pytest.fixture
    def console(self):
        """Create a Rich console instance."""
        return Console()

    @pytest.fixture
    def help_system(self, console):
        """Create a ContextualHelpSystem instance."""
        return ContextualHelpSystem(console)

    def test_initialization(self, help_system, console):
        """Test ContextualHelpSystem initialization."""
        assert help_system.console == console
        assert help_system.help_shown_count == 0

    def test_should_show_help_first_time(self, help_system):
        """Test help should be shown on first interaction."""
        context = {"session_active": False}

        result = help_system.should_show_help(context)

        assert result is True

    def test_should_show_help_after_first_time(self, help_system):
        """Test help should not be shown after first time."""
        help_system.help_shown_count = 1
        context = {"session_active": True}

        result = help_system.should_show_help(context)

        assert result is False

    def test_show_contextual_help_with_phase(self, help_system):
        """Test showing contextual help for specific phase."""
        context = {"current_phase": PhaseType.INDEXING}

        with patch.object(help_system, "_show_phase_help") as mock_help:
            help_system.show_contextual_help(context)

            mock_help.assert_called_once_with(PhaseType.INDEXING)

    def test_show_contextual_help_general(self, help_system):
        """Test showing general contextual help."""
        context = {}

        with patch.object(help_system, "_show_general_help") as mock_help:
            help_system.show_contextual_help(context)

            mock_help.assert_called_once()

    def test_display_full_help(self, help_system):
        """Test displaying full help information."""
        context = {"session_active": True}

        with patch.object(help_system.console, "print") as mock_print:
            help_system.display_full_help(context)

            mock_print.assert_called_once()

    def test_show_command_suggestions(self, help_system):
        """Test showing command suggestions."""
        context = {"current_phase": PhaseType.INDEXING}

        with patch.object(help_system.console, "print") as mock_print:
            help_system.show_command_suggestions("unknow", context)

            mock_print.assert_called_once()


class TestEnhancedCLIIntegration:
    """Integration tests for EnhancedCLI components."""

    @pytest.fixture
    def enhanced_cli(self):
        """Create an EnhancedCLI instance for integration testing."""
        return EnhancedCLI()

    def test_full_workflow_simulation(self, enhanced_cli, temp_project_dir):
        """Test a complete workflow simulation."""
        # Mock the workflow manager
        mock_manager = Mock()
        mock_manager.get_current_phase.return_value = PhaseType.INDEXING
        mock_manager.execute_complete_workflow.return_value = True
        enhanced_cli.workflow_manager = mock_manager

        # Test init command
        enhanced_cli.init_command(temp_project_dir)

        # Test status command
        status_result = enhanced_cli.handle_user_input("status")
        assert "Current phase" in status_result

        # Test run command
        with patch.object(enhanced_cli.progress_manager, "progress") as mock_progress:
            mock_progress.__enter__ = Mock(return_value=mock_progress)
            mock_progress.__exit__ = Mock(return_value=None)
            run_result = enhanced_cli.handle_user_input("run")
            assert "completed successfully" in run_result

    def test_document_approval_workflow(self, enhanced_cli):
        """Test document approval workflow."""
        document_content = "# Test Specification\n\nThis is a test specification document."

        with patch("rich.prompt.Prompt.ask", return_value="y"):
            result = enhanced_cli.request_approval(document_content, "specification")
            assert result is True

    def test_progress_tracking_workflow(self, enhanced_cli):
        """Test progress tracking workflow."""
        # Mock the workflow manager
        mock_manager = Mock()
        mock_manager.transition_to_phase.return_value = True
        enhanced_cli.workflow_manager = mock_manager

        # Test phase progress update
        enhanced_cli.display_progress(PhaseType.INDEXING, 0.5)

        # Test phase transition
        result = enhanced_cli.handle_user_input("phase indexing")
        assert "Successfully transitioned" in result

    def test_help_system_workflow(self, enhanced_cli):
        """Test help system workflow."""
        # Test contextual help
        context = enhanced_cli._get_current_context()
        enhanced_cli.help_system.display_full_help(context)

        # Test getting started help
        if enhanced_cli.help_system.should_show_help(context):
            enhanced_cli.help_system.show_contextual_help(context)

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
