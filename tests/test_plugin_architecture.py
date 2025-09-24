"""Tests for the plugin architecture system."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from dev_agent.plugins.architecture import PluginArchitecture
from dev_agent.plugins.models import (
    CodeContext,
    IDEType,
    PluginConfig,
    SecurityLevel,
)


class TestPluginArchitecture:
    """Test cases for PluginArchitecture class."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def plugin_architecture(self, temp_config_dir):
        """Create a PluginArchitecture instance."""
        return PluginArchitecture(temp_config_dir)
    
    @pytest.fixture
    def sample_plugin_config(self):
        """Create a sample plugin configuration."""
        return PluginConfig(
            name="test-plugin",
            version="1.0.0",
            description="Test plugin for unit tests",
            author="Test Author",
            ide_type=IDEType.VSCODE,
            security_level=SecurityLevel.SANDBOXED,
            permissions=["ide_integration"],
            enabled=True,
        )
    
    @pytest.fixture
    def sample_plugin_dir(self, temp_config_dir, sample_plugin_config):
        """Create a sample plugin directory."""
        plugin_dir = temp_config_dir / "test_plugin"
        plugin_dir.mkdir()
        
        # Create plugin.json
        config_file = plugin_dir / "plugin.json"
        with open(config_file, "w") as f:
            json.dump(sample_plugin_config.model_dump(), f)
        
        # Create main.py
        main_file = plugin_dir / "main.py"
        main_file.write_text("""
def create_plugin(config):
    return TestPlugin(config)

class TestPlugin:
    def __init__(self, config):
        self.config = config
        self.is_active = False
    
    def activate(self):
        self.is_active = True
    
    def deactivate(self):
        self.is_active = False
    
    def get_suggestions(self, context):
        return []
    
    def handle_file_event(self, event):
        pass
""")
        
        return plugin_dir
    
    def test_initialization(self, temp_config_dir):
        """Test plugin architecture initialization."""
        arch = PluginArchitecture(temp_config_dir)
        
        assert arch.config_dir == temp_config_dir
        assert arch.plugin_registry is not None
        assert arch.security_manager is not None
        assert arch.plugin_loader is not None
        assert arch.command_bridge is not None
    
    @patch('dev_agent.plugins.architecture.CommandBridge.start')
    def test_start_success(self, mock_bridge_start, plugin_architecture):
        """Test successful plugin architecture start."""
        mock_bridge_start.return_value = True
        
        result = plugin_architecture.start()
        
        assert result is True
        mock_bridge_start.assert_called_once()
    
    @patch('dev_agent.plugins.architecture.CommandBridge.start')
    def test_start_failure(self, mock_bridge_start, plugin_architecture):
        """Test plugin architecture start failure."""
        mock_bridge_start.return_value = False
        
        result = plugin_architecture.start()
        
        assert result is False
    
    def test_install_plugin_success(self, plugin_architecture, sample_plugin_dir):
        """Test successful plugin installation."""
        result = plugin_architecture.install_plugin(sample_plugin_dir)
        
        assert result is True
        
        # Check if plugin is registered
        plugins = plugin_architecture.list_plugins()
        assert len(plugins) == 1
        assert plugins[0]["name"] == "test-plugin"
    
    def test_install_plugin_no_config(self, plugin_architecture, temp_config_dir):
        """Test plugin installation without config file."""
        plugin_dir = temp_config_dir / "invalid_plugin"
        plugin_dir.mkdir()
        
        result = plugin_architecture.install_plugin(plugin_dir)
        
        assert result is False
    
    def test_install_plugin_invalid_config(self, plugin_architecture, temp_config_dir):
        """Test plugin installation with invalid config."""
        plugin_dir = temp_config_dir / "invalid_plugin"
        plugin_dir.mkdir()
        
        config_file = plugin_dir / "plugin.json"
        config_file.write_text("invalid json")
        
        result = plugin_architecture.install_plugin(plugin_dir)
        
        assert result is False
    
    def test_uninstall_plugin(self, plugin_architecture, sample_plugin_dir):
        """Test plugin uninstallation."""
        # Install first
        plugin_architecture.install_plugin(sample_plugin_dir)
        plugin_id = "vscode:test-plugin"
        
        # Uninstall
        result = plugin_architecture.uninstall_plugin(plugin_id)
        
        assert result is True
        
        # Check if plugin is removed
        plugins = plugin_architecture.list_plugins()
        assert len(plugins) == 0
    
    def test_load_plugin(self, plugin_architecture, sample_plugin_dir):
        """Test plugin loading."""
        # Install first
        plugin_architecture.install_plugin(sample_plugin_dir)
        plugin_id = "vscode:test-plugin"
        
        # Load plugin
        plugin = plugin_architecture.load_plugin(plugin_id)
        
        assert plugin is not None
        assert plugin.plugin_id == plugin_id
        assert plugin.config.name == "test-plugin"
    
    def test_unload_plugin(self, plugin_architecture, sample_plugin_dir):
        """Test plugin unloading."""
        # Install and load first
        plugin_architecture.install_plugin(sample_plugin_dir)
        plugin_id = "vscode:test-plugin"
        plugin_architecture.load_plugin(plugin_id)
        
        # Unload plugin
        result = plugin_architecture.unload_plugin(plugin_id)
        
        assert result is True
    
    def test_activate_plugin(self, plugin_architecture, sample_plugin_dir):
        """Test plugin activation."""
        # Install first
        plugin_architecture.install_plugin(sample_plugin_dir)
        plugin_id = "vscode:test-plugin"
        
        # Activate plugin
        result = plugin_architecture.activate_plugin(plugin_id)
        
        assert result is True
        
        # Check if plugin is active
        plugin = plugin_architecture.plugin_loader.get_loaded_plugin(plugin_id)
        assert plugin is not None
        assert plugin.is_active is True
    
    def test_deactivate_plugin(self, plugin_architecture, sample_plugin_dir):
        """Test plugin deactivation."""
        # Install and activate first
        plugin_architecture.install_plugin(sample_plugin_dir)
        plugin_id = "vscode:test-plugin"
        plugin_architecture.activate_plugin(plugin_id)
        
        # Deactivate plugin
        result = plugin_architecture.deactivate_plugin(plugin_id)
        
        assert result is True
        
        # Check if plugin is inactive
        plugin = plugin_architecture.plugin_loader.get_loaded_plugin(plugin_id)
        assert plugin is not None
        assert plugin.is_active is False
    
    def test_get_plugin_suggestions(self, plugin_architecture, sample_plugin_dir):
        """Test getting suggestions from plugins."""
        # Install and activate plugin
        plugin_architecture.install_plugin(sample_plugin_dir)
        plugin_id = "vscode:test-plugin"
        plugin_architecture.activate_plugin(plugin_id)
        
        # Create code context
        context = CodeContext(
            file_path=Path("test.py"),
            language="python",
            content="def test(): pass",
            cursor_position={"line": 0, "character": 0},
        )
        
        # Get suggestions
        suggestions = plugin_architecture.get_plugin_suggestions(context)
        
        assert isinstance(suggestions, list)
    
    def test_list_plugins(self, plugin_architecture, sample_plugin_dir):
        """Test listing plugins."""
        # Install plugin
        plugin_architecture.install_plugin(sample_plugin_dir)
        
        # List all plugins
        plugins = plugin_architecture.list_plugins()
        
        assert len(plugins) == 1
        assert plugins[0]["name"] == "test-plugin"
        assert plugins[0]["ide_type"] == "vscode"
    
    def test_list_plugins_filtered(self, plugin_architecture, sample_plugin_dir):
        """Test listing plugins with filter."""
        # Install plugin
        plugin_architecture.install_plugin(sample_plugin_dir)
        
        # List VS Code plugins
        vscode_plugins = plugin_architecture.list_plugins(ide_type=IDEType.VSCODE)
        assert len(vscode_plugins) == 1
        
        # List IntelliJ plugins (should be empty)
        intellij_plugins = plugin_architecture.list_plugins(ide_type=IDEType.INTELLIJ)
        assert len(intellij_plugins) == 0
    
    def test_stop(self, plugin_architecture, sample_plugin_dir):
        """Test stopping plugin architecture."""
        # Install and load plugin
        plugin_architecture.install_plugin(sample_plugin_dir)
        plugin_id = "vscode:test-plugin"
        plugin_architecture.load_plugin(plugin_id)
        
        # Stop architecture
        plugin_architecture.stop()
        
        # Check if plugins are unloaded
        loaded_plugins = plugin_architecture.plugin_loader.list_loaded_plugins()
        assert len(loaded_plugins) == 0