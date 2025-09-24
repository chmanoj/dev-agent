"""Plugin loader for dynamically loading and managing plugins."""

from __future__ import annotations

import importlib.util
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

from dev_agent.plugins.models import PluginConfig, PluginStatus
from dev_agent.plugins.registry import PluginRegistry
from dev_agent.plugins.security import PluginSecurityManager

logger = logging.getLogger(__name__)


class Plugin:
    """Represents a loaded plugin."""
    
    def __init__(
        self,
        plugin_id: str,
        config: PluginConfig,
        module: Any,
        instance: Any,
    ) -> None:
        """Initialize a plugin.
        
        Args:
            plugin_id: Unique plugin identifier
            config: Plugin configuration
            module: Loaded Python module
            instance: Plugin instance
        """
        self.plugin_id = plugin_id
        self.config = config
        self.module = module
        self.instance = instance
        self.is_active = False
    
    def activate(self) -> bool:
        """Activate the plugin.
        
        Returns:
            True if activation successful
        """
        try:
            if hasattr(self.instance, "activate"):
                self.instance.activate()
            self.is_active = True
            logger.info(f"Activated plugin: {self.plugin_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to activate plugin {self.plugin_id}: {e}")
            return False
    
    def deactivate(self) -> bool:
        """Deactivate the plugin.
        
        Returns:
            True if deactivation successful
        """
        try:
            if hasattr(self.instance, "deactivate"):
                self.instance.deactivate()
            self.is_active = False
            logger.info(f"Deactivated plugin: {self.plugin_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to deactivate plugin {self.plugin_id}: {e}")
            return False


class PluginLoader:
    """Loads and manages plugin lifecycle."""
    
    def __init__(
        self,
        registry: PluginRegistry,
        security_manager: PluginSecurityManager,
    ) -> None:
        """Initialize the plugin loader.
        
        Args:
            registry: Plugin registry
            security_manager: Security manager
        """
        self.registry = registry
        self.security_manager = security_manager
        self.loaded_plugins: Dict[str, Plugin] = {}
    
    def load_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """Load a plugin by ID.
        
        Args:
            plugin_id: ID of the plugin to load
            
        Returns:
            Loaded plugin instance or None if failed
        """
        if plugin_id in self.loaded_plugins:
            return self.loaded_plugins[plugin_id]
        
        metadata = self.registry.get_plugin(plugin_id)
        if not metadata:
            logger.error(f"Plugin not found in registry: {plugin_id}")
            return None
        
        # Update status to loading
        self.registry.update_plugin_status(plugin_id, PluginStatus.LOADING)
        
        try:
            start_time = time.time()
            
            # Validate security
            validation = self.security_manager.validate_plugin(
                metadata.path,
                metadata.config,
            )
            
            if not validation.is_valid:
                logger.error(f"Plugin security validation failed: {plugin_id}")
                logger.error(f"Violations: {validation.violations}")
                self.registry.update_plugin_status(plugin_id, PluginStatus.ERROR)
                return None
            
            # Load the plugin module
            plugin_file = metadata.path / "main.py"
            if not plugin_file.exists():
                logger.error(f"Plugin main.py not found: {plugin_file}")
                self.registry.update_plugin_status(plugin_id, PluginStatus.ERROR)
                return None
            
            spec = importlib.util.spec_from_file_location(
                f"plugin_{plugin_id.replace(':', '_')}",
                plugin_file,
            )
            
            if not spec or not spec.loader:
                logger.error(f"Failed to create module spec for plugin: {plugin_id}")
                self.registry.update_plugin_status(plugin_id, PluginStatus.ERROR)
                return None
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            
            # Create plugin instance
            if not hasattr(module, "create_plugin"):
                logger.error(f"Plugin missing create_plugin function: {plugin_id}")
                self.registry.update_plugin_status(plugin_id, PluginStatus.ERROR)
                return None
            
            instance = module.create_plugin(metadata.config)
            
            # Create plugin wrapper
            plugin = Plugin(plugin_id, metadata.config, module, instance)
            self.loaded_plugins[plugin_id] = plugin
            
            # Update metadata
            load_time = time.time() - start_time
            metadata.load_time = load_time
            self.registry.update_plugin_status(plugin_id, PluginStatus.LOADED)
            
            logger.info(f"Loaded plugin: {plugin_id} in {load_time:.2f}s")
            return plugin
            
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_id}: {e}")
            self.registry.update_plugin_status(plugin_id, PluginStatus.ERROR)
            return None
    
    def unload_plugin(self, plugin_id: str) -> bool:
        """Unload a plugin.
        
        Args:
            plugin_id: ID of the plugin to unload
            
        Returns:
            True if unload successful
        """
        if plugin_id not in self.loaded_plugins:
            return True
        
        try:
            plugin = self.loaded_plugins[plugin_id]
            
            # Deactivate if active
            if plugin.is_active:
                plugin.deactivate()
            
            # Clean up module
            module_name = f"plugin_{plugin_id.replace(':', '_')}"
            if module_name in sys.modules:
                del sys.modules[module_name]
            
            # Remove from loaded plugins
            del self.loaded_plugins[plugin_id]
            
            # Update status
            self.registry.update_plugin_status(plugin_id, PluginStatus.UNLOADED)
            
            logger.info(f"Unloaded plugin: {plugin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_id}: {e}")
            return False
    
    def get_loaded_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """Get a loaded plugin by ID.
        
        Args:
            plugin_id: ID of the plugin
            
        Returns:
            Plugin instance if loaded
        """
        return self.loaded_plugins.get(plugin_id)
    
    def list_loaded_plugins(self) -> Dict[str, Plugin]:
        """List all loaded plugins.
        
        Returns:
            Dictionary of loaded plugins
        """
        return self.loaded_plugins.copy()
    
    def reload_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """Reload a plugin.
        
        Args:
            plugin_id: ID of the plugin to reload
            
        Returns:
            Reloaded plugin instance or None if failed
        """
        # Unload first
        self.unload_plugin(plugin_id)
        
        # Load again
        return self.load_plugin(plugin_id)