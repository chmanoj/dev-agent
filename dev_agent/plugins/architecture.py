"""Main plugin architecture class that orchestrates the plugin system."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

from dev_agent.plugins.bridge import CommandBridge, IDECommunicator
from dev_agent.plugins.loader import Plugin, PluginLoader
from dev_agent.plugins.models import (
    CodeContext,
    Command,
    FileEvent,
    IDEType,
    PluginAPI,
    PluginConfig,
    Suggestion,
)
from dev_agent.plugins.registry import PluginRegistry
from dev_agent.plugins.security import PluginSecurityManager

logger = logging.getLogger(__name__)


class PluginArchitecture:
    """Main plugin architecture class with plugin loading and lifecycle management."""
    
    def __init__(self, config_dir: Path) -> None:
        """Initialize the plugin architecture.
        
        Args:
            config_dir: Directory for plugin configuration and registry
        """
        self.config_dir = config_dir
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        registry_path = config_dir / "plugin_registry.json"
        self.plugin_registry = PluginRegistry(registry_path)
        self.security_manager = PluginSecurityManager()
        self.plugin_loader = PluginLoader(self.plugin_registry, self.security_manager)
        
        # Communication bridge
        self.command_bridge = CommandBridge()
        self.ide_communicator = IDECommunicator(self.command_bridge)
        
        # Plugin API
        self.plugin_api = PluginAPI()
        
        # Setup command handlers
        self._setup_command_handlers()
    
    def start(self) -> bool:
        """Start the plugin architecture.
        
        Returns:
            True if started successfully
        """
        try:
            # Start command bridge
            if not self.command_bridge.start():
                return False
            
            # Auto-load enabled plugins
            self._auto_load_plugins()
            
            logger.info("Plugin architecture started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start plugin architecture: {e}")
            return False
    
    def stop(self) -> None:
        """Stop the plugin architecture."""
        try:
            # Unload all plugins
            for plugin_id in list(self.plugin_loader.loaded_plugins.keys()):
                self.unload_plugin(plugin_id)
            
            # Stop command bridge
            self.command_bridge.stop()
            
            logger.info("Plugin architecture stopped")
            
        except Exception as e:
            logger.error(f"Error stopping plugin architecture: {e}")
    
    def install_plugin(self, plugin_path: Path) -> bool:
        """Install a new plugin.
        
        Args:
            plugin_path: Path to the plugin directory
            
        Returns:
            True if installation successful
        """
        try:
            # Load plugin configuration
            config_file = plugin_path / "plugin.json"
            if not config_file.exists():
                logger.error(f"Plugin configuration not found: {config_file}")
                return False
            
            import json
            with open(config_file) as f:
                config_data = json.load(f)
            
            config = PluginConfig(**config_data)
            
            # Validate security
            validation = self.security_manager.validate_plugin(plugin_path, config)
            if not validation.is_valid:
                logger.error(f"Plugin security validation failed: {validation.violations}")
                return False
            
            # Register plugin
            if not self.plugin_registry.register_plugin(plugin_path, config):
                return False
            
            logger.info(f"Installed plugin: {config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to install plugin: {e}")
            return False
    
    def uninstall_plugin(self, plugin_id: str) -> bool:
        """Uninstall a plugin.
        
        Args:
            plugin_id: ID of the plugin to uninstall
            
        Returns:
            True if uninstallation successful
        """
        try:
            # Unload if loaded
            self.unload_plugin(plugin_id)
            
            # Unregister
            if not self.plugin_registry.unregister_plugin(plugin_id):
                return False
            
            logger.info(f"Uninstalled plugin: {plugin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to uninstall plugin: {e}")
            return False
    
    def load_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """Load a plugin by ID.
        
        Args:
            plugin_id: ID of the plugin to load
            
        Returns:
            Loaded plugin instance or None if failed
        """
        plugin = self.plugin_loader.load_plugin(plugin_id)
        if plugin:
            # Register plugin commands
            self._register_plugin_commands(plugin)
        
        return plugin
    
    def unload_plugin(self, plugin_id: str) -> bool:
        """Unload a plugin.
        
        Args:
            plugin_id: ID of the plugin to unload
            
        Returns:
            True if unload successful
        """
        # Unregister commands first
        self._unregister_plugin_commands(plugin_id)
        
        return self.plugin_loader.unload_plugin(plugin_id)
    
    def activate_plugin(self, plugin_id: str) -> bool:
        """Activate a loaded plugin.
        
        Args:
            plugin_id: ID of the plugin to activate
            
        Returns:
            True if activation successful
        """
        plugin = self.plugin_loader.get_loaded_plugin(plugin_id)
        if not plugin:
            # Try to load first
            plugin = self.load_plugin(plugin_id)
        
        if plugin:
            return plugin.activate()
        
        return False
    
    def deactivate_plugin(self, plugin_id: str) -> bool:
        """Deactivate a plugin.
        
        Args:
            plugin_id: ID of the plugin to deactivate
            
        Returns:
            True if deactivation successful
        """
        plugin = self.plugin_loader.get_loaded_plugin(plugin_id)
        if plugin:
            return plugin.deactivate()
        
        return False
    
    def get_plugin_suggestions(self, context: CodeContext) -> List[Suggestion]:
        """Get code suggestions from active plugins.
        
        Args:
            context: Code context for suggestions
            
        Returns:
            List of suggestions from plugins
        """
        suggestions = []
        
        for plugin in self.plugin_loader.loaded_plugins.values():
            if not plugin.is_active:
                continue
            
            try:
                if hasattr(plugin.instance, "get_suggestions"):
                    plugin_suggestions = plugin.instance.get_suggestions(context)
                    if plugin_suggestions:
                        suggestions.extend(plugin_suggestions)
            except Exception as e:
                logger.error(f"Error getting suggestions from plugin {plugin.plugin_id}: {e}")
        
        # Sort by confidence and priority
        suggestions.sort(key=lambda s: (s.confidence, s.priority), reverse=True)
        return suggestions
    
    def handle_file_event(self, event: FileEvent) -> None:
        """Handle file events from IDE.
        
        Args:
            event: File event to handle
        """
        for plugin in self.plugin_loader.loaded_plugins.values():
            if not plugin.is_active:
                continue
            
            try:
                if hasattr(plugin.instance, "handle_file_event"):
                    plugin.instance.handle_file_event(event)
            except Exception as e:
                logger.error(f"Error handling file event in plugin {plugin.plugin_id}: {e}")
    
    def list_plugins(self, ide_type: Optional[IDEType] = None) -> List[Dict]:
        """List available plugins.
        
        Args:
            ide_type: Filter by IDE type
            
        Returns:
            List of plugin information
        """
        plugins = self.plugin_registry.list_plugins(ide_type=ide_type)
        
        result = []
        for metadata in plugins:
            plugin_info = {
                "id": f"{metadata.config.ide_type.value}:{metadata.config.name}",
                "name": metadata.config.name,
                "version": metadata.config.version,
                "description": metadata.config.description,
                "author": metadata.config.author,
                "ide_type": metadata.config.ide_type.value,
                "status": metadata.status.value,
                "enabled": metadata.config.enabled,
            }
            
            # Add runtime info if loaded
            plugin_id = plugin_info["id"]
            loaded_plugin = self.plugin_loader.get_loaded_plugin(plugin_id)
            if loaded_plugin:
                plugin_info["is_active"] = loaded_plugin.is_active
            
            result.append(plugin_info)
        
        return result
    
    def provide_plugin_api(self, plugin: Plugin) -> PluginAPI:
        """Provide API interface to a plugin.
        
        Args:
            plugin: Plugin instance
            
        Returns:
            Plugin API interface
        """
        # Customize API based on plugin permissions
        api = PluginAPI()
        
        validation = self.security_manager.validate_plugin(
            plugin.config.path if hasattr(plugin.config, 'path') else Path(),
            plugin.config,
        )
        
        api.permissions = validation.permissions_granted
        
        return api
    
    def _setup_command_handlers(self) -> None:
        """Setup command handlers for the bridge."""
        self.command_bridge.register_command_handler(
            "get_suggestions",
            self._handle_get_suggestions,
        )
        
        self.command_bridge.register_event_handler(
            "file_event",
            self._handle_file_event_bridge,
        )
    
    def _handle_get_suggestions(self, **kwargs) -> List[Dict]:
        """Handle get suggestions command from IDE.
        
        Returns:
            List of suggestion dictionaries
        """
        try:
            context = CodeContext(**kwargs)
            suggestions = self.get_plugin_suggestions(context)
            return [s.model_dump() for s in suggestions]
        except Exception as e:
            logger.error(f"Error handling get_suggestions: {e}")
            return []
    
    def _handle_file_event_bridge(self, event_data: Dict) -> None:
        """Handle file event from bridge.
        
        Args:
            event_data: Event data from bridge
        """
        try:
            event = FileEvent(**event_data)
            self.handle_file_event(event)
        except Exception as e:
            logger.error(f"Error handling file event: {e}")
    
    def _auto_load_plugins(self) -> None:
        """Auto-load enabled plugins."""
        plugins = self.plugin_registry.list_plugins()
        
        for metadata in plugins:
            if metadata.config.enabled:
                plugin_id = f"{metadata.config.ide_type.value}:{metadata.config.name}"
                self.load_plugin(plugin_id)
    
    def _register_plugin_commands(self, plugin: Plugin) -> None:
        """Register commands from a plugin.
        
        Args:
            plugin: Plugin instance
        """
        try:
            if hasattr(plugin.instance, "get_commands"):
                commands = plugin.instance.get_commands()
                for command in commands:
                    handler_name = f"plugin_{plugin.plugin_id}_{command.id}"
                    
                    def create_handler(cmd_id: str, plugin_inst: Plugin):
                        def handler(**kwargs):
                            return plugin_inst.instance.handle_command(cmd_id, **kwargs)
                        return handler
                    
                    self.command_bridge.register_command_handler(
                        handler_name,
                        create_handler(command.id, plugin),
                    )
        except Exception as e:
            logger.error(f"Error registering commands for plugin {plugin.plugin_id}: {e}")
    
    def _unregister_plugin_commands(self, plugin_id: str) -> None:
        """Unregister commands from a plugin.
        
        Args:
            plugin_id: ID of the plugin
        """
        # Remove command handlers (simplified - in real implementation,
        # we'd need to track which handlers belong to which plugin)
        pass