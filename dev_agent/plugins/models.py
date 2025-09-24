"""Data models for the plugin system."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class IDEType(str, Enum):
    """Supported IDE types."""
    
    VSCODE = "vscode"
    INTELLIJ = "intellij"
    VIM = "vim"
    EMACS = "emacs"
    SUBLIME = "sublime"


class PluginStatus(str, Enum):
    """Plugin lifecycle status."""
    
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"


class CommandType(str, Enum):
    """Types of commands that can be registered."""
    
    WORKFLOW = "workflow"
    ANALYSIS = "analysis"
    GENERATION = "generation"
    NAVIGATION = "navigation"
    UTILITY = "utility"


class EventType(str, Enum):
    """Types of file/IDE events."""
    
    FILE_OPENED = "file_opened"
    FILE_SAVED = "file_saved"
    FILE_CHANGED = "file_changed"
    FILE_CLOSED = "file_closed"
    SELECTION_CHANGED = "selection_changed"
    CURSOR_MOVED = "cursor_moved"


class SecurityLevel(str, Enum):
    """Security levels for plugins."""
    
    TRUSTED = "trusted"
    SANDBOXED = "sandboxed"
    RESTRICTED = "restricted"


class PluginConfig(BaseModel):
    """Configuration for a plugin."""
    
    name: str
    version: str
    description: str
    author: str
    ide_type: IDEType
    security_level: SecurityLevel = SecurityLevel.SANDBOXED
    permissions: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    settings: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class Command(BaseModel):
    """A command that can be executed in the IDE."""
    
    id: str
    title: str
    description: str
    command_type: CommandType
    keybinding: Optional[str] = None
    context: Optional[str] = None
    handler: str  # Function name to call


class FileEvent(BaseModel):
    """File event from the IDE."""
    
    event_type: EventType
    file_path: Path
    content: Optional[str] = None
    selection: Optional[Dict[str, Any]] = None
    cursor_position: Optional[Dict[str, int]] = None
    timestamp: float


class CodeContext(BaseModel):
    """Context information for code suggestions."""
    
    file_path: Path
    language: str
    content: str
    cursor_position: Dict[str, int]
    selection: Optional[Dict[str, Any]] = None
    surrounding_code: Optional[str] = None
    project_context: Optional[Dict[str, Any]] = None


class Suggestion(BaseModel):
    """Code suggestion from dev-agent."""
    
    id: str
    title: str
    description: str
    code: str
    range: Dict[str, int]
    confidence: float
    category: str
    priority: int = 0


@dataclass
class SecurityValidation:
    """Result of plugin security validation."""
    
    is_valid: bool
    security_level: SecurityLevel
    violations: List[str]
    warnings: List[str]
    permissions_granted: List[str]


@dataclass
class PluginMetadata:
    """Metadata about a plugin."""
    
    config: PluginConfig
    path: Path
    status: PluginStatus
    load_time: Optional[float] = None
    error_message: Optional[str] = None
    api_version: str = "1.0.0"


class PluginAPI(BaseModel):
    """API interface provided to plugins."""
    
    version: str = "1.0.0"
    available_commands: List[str] = Field(default_factory=list)
    available_events: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)