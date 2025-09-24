"""Tests for IDE plugin implementations."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

from dev_agent.plugins.ide_plugin import VSCodePlugin
from dev_agent.plugins.models import (
    CodeContext,
    CommandType,
    EventType,
    FileEvent,
    IDEType,
    PluginConfig,
    SecurityLevel,
)


class TestVSCodePlugin:
    """Test cases for VSCodePlugin class."""
    
    @pytest.fixture
    def plugin_config(self):
        """Create a plugin configuration for VS Code."""
        return PluginConfig(
            name="vscode-dev-agent",
            version="1.0.0",
            description="Dev-Agent VS Code plugin",
            author="Dev-Agent Team",
            ide_type=IDEType.VSCODE,
            security_level=SecurityLevel.TRUSTED,
            permissions=["ide_integration", "workspace_access"],
        )
    
    @pytest.fixture
    def vscode_plugin(self, plugin_config):
        """Create a VSCodePlugin instance."""
        return VSCodePlugin(plugin_config)
    
    def test_initialization(self, vscode_plugin, plugin_config):
        """Test VS Code plugin initialization."""
        assert vscode_plugin.ide_type == IDEType.VSCODE
        assert vscode_plugin.plugin_config == plugin_config
        assert vscode_plugin.is_active is False
        assert vscode_plugin.workspace_path is None
        assert vscode_plugin.active_file is None
    
    def test_register_commands(self, vscode_plugin):
        """Test command registration."""
        commands = vscode_plugin.register_commands()
        
        assert len(commands) > 0
        
        # Check for expected commands
        command_ids = [cmd.id for cmd in commands]
        assert "analyze_project" in command_ids
        assert "generate_specification" in command_ids
        assert "generate_design" in command_ids
        assert "generate_tasks" in command_ids
        assert "suggest_improvements" in command_ids
        assert "open_dev_agent_panel" in command_ids
        
        # Check command properties
        analyze_cmd = next(cmd for cmd in commands if cmd.id == "analyze_project")
        assert analyze_cmd.title == "Analyze Project with Dev-Agent"
        assert analyze_cmd.command_type == CommandType.ANALYSIS
        assert analyze_cmd.keybinding == "Ctrl+Shift+A"
    
    def test_activation_deactivation(self, vscode_plugin):
        """Test plugin activation and deactivation."""
        # Initially inactive
        assert vscode_plugin.is_active is False
        
        # Activate
        vscode_plugin.activate()
        assert vscode_plugin.is_active is True
        
        # Deactivate
        vscode_plugin.deactivate()
        assert vscode_plugin.is_active is False
    
    def test_handle_file_opened_event(self, vscode_plugin):
        """Test handling file opened event."""
        vscode_plugin.activate()
        
        event = FileEvent(
            event_type=EventType.FILE_OPENED,
            file_path=Path("test.py"),
            content="def test(): pass",
            timestamp=1234567890.0,
        )
        
        # Should not raise an exception
        vscode_plugin.handle_file_events(event)
        
        # Active file should be updated
        assert vscode_plugin.active_file == Path("test.py")
    
    def test_handle_file_saved_event(self, vscode_plugin):
        """Test handling file saved event."""
        vscode_plugin.activate()
        
        event = FileEvent(
            event_type=EventType.FILE_SAVED,
            file_path=Path("test.py"),
            content="def test(): pass",
            timestamp=1234567890.0,
        )
        
        # Should not raise an exception
        vscode_plugin.handle_file_events(event)
    
    def test_handle_file_events_inactive(self, vscode_plugin):
        """Test that file events are ignored when plugin is inactive."""
        # Plugin is inactive by default
        assert vscode_plugin.is_active is False
        
        event = FileEvent(
            event_type=EventType.FILE_OPENED,
            file_path=Path("test.py"),
            content="def test(): pass",
            timestamp=1234567890.0,
        )
        
        # Should not update active file when inactive
        vscode_plugin.handle_file_events(event)
        assert vscode_plugin.active_file is None
    
    def test_provide_inline_suggestions_python(self, vscode_plugin):
        """Test providing inline suggestions for Python code."""
        context = CodeContext(
            file_path=Path("test.py"),
            language="python",
            content="def test_function():\n    pass",
            cursor_position={"line": 0, "character": 0},
        )
        
        suggestions = vscode_plugin.provide_inline_suggestions(context)
        
        assert isinstance(suggestions, list)
        # Should provide suggestions for Python code
        assert len(suggestions) > 0
    
    def test_provide_inline_suggestions_non_python(self, vscode_plugin):
        """Test providing inline suggestions for non-Python code."""
        context = CodeContext(
            file_path=Path("test.js"),
            language="javascript",
            content="function test() { return 42; }",
            cursor_position={"line": 0, "character": 0},
        )
        
        suggestions = vscode_plugin.provide_inline_suggestions(context)
        
        assert isinstance(suggestions, list)
        # May or may not provide suggestions for non-Python code
    
    def test_handle_analyze_project_command(self, vscode_plugin):
        """Test handling analyze project command."""
        result = vscode_plugin.handle_command("analyze_project")
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "message" in result
        assert result["success"] is True
    
    def test_handle_generate_specification_command(self, vscode_plugin):
        """Test handling generate specification command."""
        result = vscode_plugin.handle_command("generate_specification")
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "message" in result
        assert result["success"] is True
    
    def test_handle_generate_design_command(self, vscode_plugin):
        """Test handling generate design command."""
        result = vscode_plugin.handle_command("generate_design")
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "message" in result
        assert result["success"] is True
    
    def test_handle_generate_tasks_command(self, vscode_plugin):
        """Test handling generate tasks command."""
        result = vscode_plugin.handle_command("generate_tasks")
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "message" in result
        assert result["success"] is True
    
    def test_handle_suggest_improvements_command(self, vscode_plugin):
        """Test handling suggest improvements command."""
        context_data = {
            "file_path": "test.py",
            "language": "python",
            "content": "def test(): pass",
            "cursor_position": {"line": 0, "character": 0},
        }
        
        result = vscode_plugin.handle_command("suggest_improvements", **context_data)
        
        assert isinstance(result, dict)
        assert "success" in result
        assert result["success"] is True
        if "suggestions" in result:
            assert isinstance(result["suggestions"], list)
    
    def test_handle_open_panel_command(self, vscode_plugin):
        """Test handling open panel command."""
        result = vscode_plugin.handle_command("open_panel")
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "message" in result
        assert result["success"] is True
    
    def test_handle_unknown_command(self, vscode_plugin):
        """Test handling unknown command."""
        result = vscode_plugin.handle_command("unknown_command")
        
        assert result is None
    
    def test_should_suggest_improvements(self, vscode_plugin):
        """Test logic for when to suggest improvements."""
        # Python code with sufficient length
        context = CodeContext(
            file_path=Path("test.py"),
            language="python",
            content="def test_function():\n    return 42\n\n# This is a longer piece of code",
            cursor_position={"line": 0, "character": 0},
        )
        
        should_suggest = vscode_plugin._should_suggest_improvements(context)
        assert should_suggest is True
        
        # Short code
        short_context = CodeContext(
            file_path=Path("test.py"),
            language="python",
            content="x = 1",
            cursor_position={"line": 0, "character": 0},
        )
        
        should_suggest = vscode_plugin._should_suggest_improvements(short_context)
        assert should_suggest is False
        
        # Non-Python code
        js_context = CodeContext(
            file_path=Path("test.js"),
            language="javascript",
            content="function test() { return 42; }",
            cursor_position={"line": 0, "character": 0},
        )
        
        should_suggest = vscode_plugin._should_suggest_improvements(js_context)
        assert should_suggest is False
    
    def test_should_suggest_patterns(self, vscode_plugin):
        """Test logic for when to suggest patterns."""
        # Code with class definition
        class_context = CodeContext(
            file_path=Path("test.py"),
            language="python",
            content="class TestClass:\n    def __init__(self):\n        pass",
            cursor_position={"line": 0, "character": 0},
        )
        
        should_suggest = vscode_plugin._should_suggest_patterns(class_context)
        assert should_suggest is True
        
        # Code with function definition
        func_context = CodeContext(
            file_path=Path("test.py"),
            language="python",
            content="def test_function():\n    return 42",
            cursor_position={"line": 0, "character": 0},
        )
        
        should_suggest = vscode_plugin._should_suggest_patterns(func_context)
        assert should_suggest is True
        
        # Code without class or function
        simple_context = CodeContext(
            file_path=Path("test.py"),
            language="python",
            content="x = 42\ny = x + 1",
            cursor_position={"line": 0, "character": 0},
        )
        
        should_suggest = vscode_plugin._should_suggest_patterns(simple_context)
        assert should_suggest is False
    
    def test_should_suggest_tests(self, vscode_plugin):
        """Test logic for when to suggest tests."""
        # Python function in non-test file
        func_context = CodeContext(
            file_path=Path("module.py"),
            language="python",
            content="def calculate_sum(a, b):\n    return a + b",
            cursor_position={"line": 0, "character": 0},
        )
        
        should_suggest = vscode_plugin._should_suggest_tests(func_context)
        assert should_suggest is True
        
        # Test file (should not suggest tests for tests)
        test_context = CodeContext(
            file_path=Path("test_module.py"),
            language="python",
            content="def test_calculate_sum():\n    assert calculate_sum(1, 2) == 3",
            cursor_position={"line": 0, "character": 0},
        )
        
        should_suggest = vscode_plugin._should_suggest_tests(test_context)
        assert should_suggest is False
        
        # Non-Python file
        js_context = CodeContext(
            file_path=Path("script.js"),
            language="javascript",
            content="function test() { return 42; }",
            cursor_position={"line": 0, "character": 0},
        )
        
        should_suggest = vscode_plugin._should_suggest_tests(js_context)
        assert should_suggest is False
    
    def test_is_python_file(self, vscode_plugin):
        """Test Python file detection."""
        assert vscode_plugin._is_python_file(Path("test.py")) is True
        assert vscode_plugin._is_python_file(Path("module.py")) is True
        assert vscode_plugin._is_python_file(Path("script.js")) is False
        assert vscode_plugin._is_python_file(Path("README.md")) is False
        assert vscode_plugin._is_python_file(Path("config.json")) is False