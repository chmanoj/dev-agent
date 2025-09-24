"""Plugin registry for managing installed plugins."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from dev_agent.plugins.models import (
    IDEType,
    PluginConfig,
    PluginMetadata,
    PluginStatus,
)

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Registry for managing plugin metadata and discovery."""
    
    def __init__(self, registry_path: Path) -> None:
        """Initialize the plugin registry.
        
        Args:
            registry_path: Path to the registry file
        """
        self.registry_path = registry_path
        self.plugins: Dict[str, PluginMetadata] = {}
        self._load_registry()
    
    def register_plugin(self, plugin_path: Path, config: PluginConfig) -> bool:
        """Register a new plugin.
        
        Args:
            plugin_path: Path to the plugin directory
            config: Plugin configuration
            
        Returns:
            True if registration successful
        """
        try:
            plugin_id = f"{config.ide_type.value}:{config.name}"
            
            metadata = PluginMetadata(
                config=config,
                path=plugin_path,
                status=PluginStatus.UNLOADED,
            )
            
            self.plugins[plugin_id] = metadata
            self._save_registry()
            
            logger.info(f"Registered plugin: {plugin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register plugin {config.name}: {e}")
            return False
    
    def unregister_plugin(self, plugin_id: str) -> bool:
        """Unregister a plugin.
        
        Args:
            plugin_id: ID of the plugin to unregister
            
        Returns:
            True if unregistration successful
        """
        if plugin_id in self.plugins:
            del self.plugins[plugin_id]
            self._save_registry()
            logger.info(f"Unregistered plugin: {plugin_id}")
            return True
        return False
    
    def get_plugin(self, plugin_id: str) -> Optional[PluginMetadata]:
        """Get plugin metadata by ID.
        
        Args:
            plugin_id: ID of the plugin
            
        Returns:
            Plugin metadata if found
        """
        return self.plugins.get(plugin_id)
    
    def list_plugins(
        self,
        ide_type: Optional[IDEType] = None,
        status: Optional[PluginStatus] = None,
    ) -> List[PluginMetadata]:
        """List plugins with optional filtering.
        
        Args:
            ide_type: Filter by IDE type
            status: Filter by status
            
        Returns:
            List of matching plugin metadata
        """
        plugins = list(self.plugins.values())
        
        if ide_type:
            plugins = [p for p in plugins if p.config.ide_type == ide_type]
        
        if status:
            plugins = [p for p in plugins if p.status == status]
        
        return plugins
    
    def update_plugin_status(self, plugin_id: str, status: PluginStatus) -> None:
        """Update plugin status.
        
        Args:
            plugin_id: ID of the plugin
            status: New status
        """
        if plugin_id in self.plugins:
            self.plugins[plugin_id].status = status
            self._save_registry()
    
    def discover_plugins(self, search_paths: List[Path]) -> List[PluginConfig]:
        """Discover plugins in the given paths.
        
        Args:
            search_paths: Paths to search for plugins
            
        Returns:
            List of discovered plugin configurations
        """
        discovered = []
        
        for search_path in search_paths:
            if not search_path.exists():
                continue
                
            for plugin_dir in search_path.iterdir():
                if not plugin_dir.is_dir():
                    continue
                
                config_file = plugin_dir / "plugin.json"
                if config_file.exists():
                    try:
                        with open(config_file) as f:
                            config_data = json.load(f)
                        
                        config = PluginConfig(**config_data)
                        discovered.append(config)
                        
                    except Exception as e:
                        logger.warning(f"Failed to load plugin config from {config_file}: {e}")
        
        return discovered
    
    def _load_registry(self) -> None:
        """Load registry from file."""
        if not self.registry_path.exists():
            return
        
        try:
            with open(self.registry_path) as f:
                data = json.load(f)
            
            for plugin_id, plugin_data in data.items():
                config = PluginConfig(**plugin_data["config"])
                metadata = PluginMetadata(
                    config=config,
                    path=Path(plugin_data["path"]),
                    status=PluginStatus(plugin_data["status"]),
                    load_time=plugin_data.get("load_time"),
                    error_message=plugin_data.get("error_message"),
                    api_version=plugin_data.get("api_version", "1.0.0"),
                )
                self.plugins[plugin_id] = metadata
                
        except Exception as e:
            logger.error(f"Failed to load plugin registry: {e}")
    
    def _save_registry(self) -> None:
        """Save registry to file."""
        try:
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {}
            for plugin_id, metadata in self.plugins.items():
                data[plugin_id] = {
                    "config": metadata.config.model_dump(),
                    "path": str(metadata.path),
                    "status": metadata.status.value,
                    "load_time": metadata.load_time,
                    "error_message": metadata.error_message,
                    "api_version": metadata.api_version,
                }
            
            with open(self.registry_path, "w") as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save plugin registry: {e}")