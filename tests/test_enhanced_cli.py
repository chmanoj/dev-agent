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

        assert "Current Phase" in result

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
            patch("rich.prompt.Confirm.ask", return_value=True) as mock_confirm,
            patch.object(enhanced_cli.document_previewer, "show_document_preview") as mock_show,
        ):
            result = enhanced_cli.request_approval(document_content, "specification")

            mock_show.assert_called_once()
            mock_confirm.assert_called_once()
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

    def test_handle_architecture_command(self, enhanced_cli):
        """Test handling of architecture command."""
        result = enhanced_cli.handle_user_input("architecture")

        # Should return empty string (output goes to console)
        assert result == ""

    def test_handle_workflow_command(self, enhanced_cli):
        """Test handling of workflow diagram command."""
        result = enhanced_cli.handle_user_input("workflow")

        # Should return empty string (output goes to console)
        assert result == ""

    def test_handle_search_command_valid(self, enhanced_cli):
        """Test handling of search command with valid arguments."""
        # Mock project state with specification
        mock_spec = Mock()
        mock_spec.content = "This is a test specification with hello world"
        
        mock_project_state = Mock()
        mock_project_state.specification = mock_spec
        mock_project_state.design = None
        mock_project_state.tasks = None
        
        enhanced_cli.workflow_manager.project_state = mock_project_state

        result = enhanced_cli.handle_user_input("search hello specification")

        # Should return empty string (output goes to console)
        assert result == ""

    def test_handle_search_command_invalid_args(self, enhanced_cli):
        """Test handling of search command with invalid arguments."""
        result = enhanced_cli.handle_user_input("search hello")

        assert "Usage: search" in result

    def test_handle_filter_command_valid(self, enhanced_cli, temp_project_dir):
        """Test handling of filter command with valid arguments."""
        enhanced_cli.current_project_path = temp_project_dir

        result = enhanced_cli.handle_user_input("filter --ext .py")

        # Should return empty string (output goes to console)
        assert result == ""

    def test_handle_filter_command_no_project(self, enhanced_cli):
        """Test handling of filter command with no active project."""
        result = enhanced_cli.handle_user_input("filter --ext .py")

        assert "No active project" in result

    def test_handle_filter_command_invalid_args(self, enhanced_cli, temp_project_dir):
        """Test handling of filter command with invalid arguments."""
        enhanced_cli.current_project_path = temp_project_dir

        result = enhanced_cli.handle_user_input("filter")

        assert "Usage: filter" in result


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
        from datetime import datetime
        
        phase = PhaseType.INDEXING
        progress_manager.current_task = "task_id"
        progress_manager.phase_start_times[phase] = datetime.now()
        
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

            # Should print two tables and a newline
            assert mock_print.call_count >= 2

    def test_show_command_suggestions(self, help_system):
        """Test showing command suggestions."""
        context = {"current_phase": PhaseType.INDEXING}

        with patch.object(help_system.console, "print") as mock_print:
            help_system.show_command_suggestions("unknow", context)

            mock_print.assert_called_once()


class TestVisualizationEngine:
    """Test cases for the VisualizationEngine class."""

    @pytest.fixture
    def console(self):
        """Create a Rich console instance."""
        return Console()

    @pytest.fixture
    def visualization_engine(self, console):
        """Create a VisualizationEngine instance."""
        from dev_agent.cli.enhanced_cli import VisualizationEngine
        return VisualizationEngine(console)

    def test_initialization(self, visualization_engine, console):
        """Test VisualizationEngine initialization."""
        assert visualization_engine.console == console

    def test_generate_architecture_diagram(self, visualization_engine):
        """Test architecture diagram generation."""
        project_analysis = {
            "components": [
                {"name": "CLI", "type": "interface"},
                {"name": "Service", "type": "service"},
            ],
            "dependencies": {"CLI": ["Service"]},
        }

        diagram = visualization_engine.generate_architecture_diagram(project_analysis)

        assert "graph TD" in diagram
        assert "CLI" in diagram
        assert "Service" in diagram

    def test_generate_workflow_diagram(self, visualization_engine):
        """Test workflow diagram generation."""
        phases = [PhaseType.INDEXING, PhaseType.SPECIFICATION]

        diagram = visualization_engine.generate_workflow_diagram(phases)

        assert "flowchart LR" in diagram
        assert "Indexing" in diagram
        assert "Specification" in diagram

    def test_show_architecture_diagram(self, visualization_engine):
        """Test showing architecture diagram."""
        project_analysis = {
            "components": [{"name": "Test", "type": "service"}],
            "dependencies": {},
        }

        with patch.object(visualization_engine.console, "print") as mock_print:
            visualization_engine.show_architecture_diagram(project_analysis)
            assert mock_print.call_count >= 2  # Diagram + instructions

    def test_show_workflow_diagram(self, visualization_engine):
        """Test showing workflow diagram."""
        phases = [PhaseType.INDEXING]

        with patch.object(visualization_engine.console, "print") as mock_print:
            visualization_engine.show_workflow_diagram(phases)
            mock_print.assert_called_once()


class TestSearchAndFilterEngine:
    """Test cases for the SearchAndFilterEngine class."""

    @pytest.fixture
    def console(self):
        """Create a Rich console instance."""
        return Console()

    @pytest.fixture
    def search_engine(self, console):
        """Create a SearchAndFilterEngine instance."""
        from dev_agent.cli.enhanced_cli import SearchAndFilterEngine
        return SearchAndFilterEngine(console)

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory with test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            (temp_path / "test.py").write_text("def hello():\n    print('Hello, World!')")
            (temp_path / "test.js").write_text("console.log('Hello, World!');")
            (temp_path / "README.md").write_text("# Test Project\n\nThis is a test.")
            
            # Create subdirectory
            sub_dir = temp_path / "src"
            sub_dir.mkdir()
            (sub_dir / "main.py").write_text("import os\nprint('Main')")
            
            yield temp_dir

    def test_initialization(self, search_engine, console):
        """Test SearchAndFilterEngine initialization."""
        assert search_engine.console == console

    def test_search_in_document(self, search_engine):
        """Test searching within document content."""
        content = "Line 1\nHello World\nLine 3\nAnother Hello\nLine 5"
        query = "Hello"

        results = search_engine.search_in_document(content, query)

        assert len(results) == 2
        assert results[0]["line_number"] == 2
        assert results[1]["line_number"] == 4
        assert "Hello" in results[0]["line_content"]

    def test_search_in_document_no_matches(self, search_engine):
        """Test searching with no matches."""
        content = "Line 1\nLine 2\nLine 3"
        query = "NotFound"

        results = search_engine.search_in_document(content, query)

        assert len(results) == 0

    def test_filter_project_files_by_extension(self, search_engine, temp_project_dir):
        """Test filtering files by extension."""
        filters = {"extensions": [".py"]}

        filtered_files = search_engine.filter_project_files(temp_project_dir, filters)

        py_files = [f for f in filtered_files if f.suffix == ".py"]
        assert len(py_files) == 2  # test.py and src/main.py
        assert all(f.suffix == ".py" for f in py_files)

    def test_filter_project_files_by_name_pattern(self, search_engine, temp_project_dir):
        """Test filtering files by name pattern."""
        filters = {"name_pattern": "test.*"}

        filtered_files = search_engine.filter_project_files(temp_project_dir, filters)

        test_files = [f for f in filtered_files if "test" in f.name.lower()]
        assert len(test_files) >= 1

    def test_show_search_results(self, search_engine):
        """Test displaying search results."""
        results = [
            {
                "line_number": 1,
                "line_content": "Hello World",
                "context": [{"line_number": 1, "content": "Hello World", "is_match": True}],
            }
        ]

        with patch.object(search_engine.console, "print") as mock_print:
            search_engine.show_search_results(results, "Hello", "test")
            mock_print.assert_called()

    def test_show_search_results_no_matches(self, search_engine):
        """Test displaying no search results."""
        results = []

        with patch.object(search_engine.console, "print") as mock_print:
            search_engine.show_search_results(results, "NotFound", "test")
            mock_print.assert_called_once()

    def test_show_filtered_files(self, search_engine, temp_project_dir):
        """Test displaying filtered files."""
        files = [Path(temp_project_dir) / "test.py"]
        filters = {"extensions": [".py"]}

        with patch.object(search_engine.console, "print") as mock_print:
            search_engine.show_filtered_files(files, filters, temp_project_dir)
            assert mock_print.call_count >= 2  # Filter panel + tree panel


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
        assert "Current Phase" in status_result

        # Test run command
        with patch.object(enhanced_cli.progress_manager, "progress") as mock_progress:
            mock_progress.__enter__ = Mock(return_value=mock_progress)
            mock_progress.__exit__ = Mock(return_value=None)
            run_result = enhanced_cli.handle_user_input("run")
            assert "completed successfully" in run_result

    def test_document_approval_workflow(self, enhanced_cli):
        """Test document approval workflow."""
        document_content = "# Test Specification\n\nThis is a test specification document."

        with patch("rich.prompt.Confirm.ask", return_value=True):
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
