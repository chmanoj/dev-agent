"""Plugin system for dev-agent IDE integrations and extensions."""

from __future__ import annotations

from dev_agent.plugins.architecture import PluginArchitecture
from dev_agent.plugins.bridge import CommandBridge, IDECommunicator
from dev_agent.plugins.ide_plugin import BaseIDEPlugin, VSCodePlugin
from dev_agent.plugins.loader import Plugin, PluginLoader
from dev_agent.plugins.registry import PluginRegistry
from dev_agent.plugins.security import PluginSecurityManager

__all__ = [
    "PluginArchitecture",
    "BaseIDEPlugin",
    "VSCodePlugin",
    "CommandBridge",
    "IDECommunicator",
    "Plugin",
    "PluginLoader",
    "PluginRegistry",
    "PluginSecurityManager",
]