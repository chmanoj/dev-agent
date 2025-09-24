"""Integration manager for custom tools and external services."""

from __future__ import annotations

import json
import subprocess
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Union

from pydantic import BaseModel, Field

from .customization_manager import ToolConfig


class IntegrationProtocol(Protocol):
    """Protocol for tool integrations."""

    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the integration with configuration."""
        ...

    def execute_command(self, command: str, args: List[str]) -> Dict[str, Any]:
        """Execute a command with the integrated tool."""
        ...

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the integration."""
        ...

    def cleanup(self) -> None:
        """Clean up resources used by the integration."""
        ...


class IntegrationResult(BaseModel):
    """Result of an integration operation."""

    success: bool = Field(..., description="Whether operation was successful")
    output: str = Field(default="", description="Command output")
    error: str = Field(default="", description="Error message if any")
    exit_code: int = Field(default=0, description="Exit code")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class BaseIntegration(ABC):
    """Base class for tool integrations."""

    def __init__(self, name: str, config: ToolConfig):
        """Initialize integration.
        
        Args:
            name: Integration name
            config: Tool configuration
        """
        self.name = name
        self.config = config
        self._initialized = False

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the integration.
        
        Returns:
            True if initialization successful, False otherwise
        """
        pass

    @abstractmethod
    def execute_command(self, command: str, args: Optional[List[str]] = None) -> IntegrationResult:
        """Execute a command with the integrated tool.
        
        Args:
            command: Command to execute
            args: Optional command arguments
            
        Returns:
            Integration result
        """
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the integration.
        
        Returns:
            Status information
        """
        pass

    def cleanup(self) -> None:
        """Clean up resources used by the integration."""
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if integration is initialized."""
        return self._initialized

    def _run_subprocess(
        self,
        command: List[str],
        cwd: Optional[Path] = None,
        timeout: Optional[int] = None,
    ) -> IntegrationResult:
        """Run a subprocess command.
        
        Args:
            command: Command and arguments
            cwd: Working directory
            timeout: Command timeout in seconds
            
        Returns:
            Integration result
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=timeout or 30,
                check=False,
            )
            
            return IntegrationResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr,
                exit_code=result.returncode,
            )
            
        except subprocess.TimeoutExpired:
            return IntegrationResult(
                success=False,
                error=f"Command timed out after {timeout} seconds",
                exit_code=-1,
            )
        except Exception as e:
            return IntegrationResult(
                success=False,
                error=str(e),
                exit_code=-1,
            )


class GitIntegration(BaseIntegration):
    """Git version control integration."""

    def initialize(self) -> bool:
        """Initialize Git integration."""
        try:
            result = self._run_subprocess(["git", "--version"])
            self._initialized = result.success
            return self._initialized
        except Exception:
            return False

    def execute_command(self, command: str, args: Optional[List[str]] = None) -> IntegrationResult:
        """Execute a Git command."""
        if not self._initialized:
            return IntegrationResult(
                success=False,
                error="Git integration not initialized"
            )
        
        git_command = ["git", command]
        if args:
            git_command.extend(args)
        
        return self._run_subprocess(git_command)

    def get_status(self) -> Dict[str, Any]:
        """Get Git repository status."""
        if not self._initialized:
            return {"error": "Not initialized"}
        
        status_result = self.execute_command("status", ["--porcelain"])
        branch_result = self.execute_command("branch", ["--show-current"])
        
        return {
            "initialized": self._initialized,
            "has_changes": bool(status_result.output.strip()),
            "current_branch": branch_result.output.strip(),
            "status_output": status_result.output,
        }

    def create_commit(self, message: str, files: Optional[List[str]] = None) -> IntegrationResult:
        """Create a Git commit."""
        if files:
            # Add specific files
            for file in files:
                add_result = self.execute_command("add", [file])
                if not add_result.success:
                    return add_result
        else:
            # Add all changes
            add_result = self.execute_command("add", ["."])
            if not add_result.success:
                return add_result
        
        return self.execute_command("commit", ["-m", message])


class DockerIntegration(BaseIntegration):
    """Docker containerization integration."""

    def initialize(self) -> bool:
        """Initialize Docker integration."""
        try:
            result = self._run_subprocess(["docker", "--version"])
            self._initialized = result.success
            return self._initialized
        except Exception:
            return False

    def execute_command(self, command: str, args: Optional[List[str]] = None) -> IntegrationResult:
        """Execute a Docker command."""
        if not self._initialized:
            return IntegrationResult(
                success=False,
                error="Docker integration not initialized"
            )
        
        docker_command = ["docker", command]
        if args:
            docker_command.extend(args)
        
        return self._run_subprocess(docker_command)

    def get_status(self) -> Dict[str, Any]:
        """Get Docker status."""
        if not self._initialized:
            return {"error": "Not initialized"}
        
        info_result = self.execute_command("info", ["--format", "json"])
        
        return {
            "initialized": self._initialized,
            "daemon_running": info_result.success,
            "info": info_result.output if info_result.success else None,
        }

    def build_image(self, dockerfile_path: Path, tag: str, context_path: Optional[Path] = None) -> IntegrationResult:
        """Build a Docker image."""
        context = str(context_path or dockerfile_path.parent)
        return self.execute_command("build", ["-t", tag, "-f", str(dockerfile_path), context])


class PythonToolIntegration(BaseIntegration):
    """Integration for Python tools (pytest, ruff, mypy, etc.)."""

    def initialize(self) -> bool:
        """Initialize Python tool integration."""
        tool_name = self.config.tool_name.lower()
        
        try:
            # Check if tool is available
            if tool_name in ["pytest", "ruff", "mypy", "black", "isort"]:
                result = self._run_subprocess([sys.executable, "-m", tool_name, "--version"])
            else:
                result = self._run_subprocess([tool_name, "--version"])
            
            self._initialized = result.success
            return self._initialized
        except Exception:
            return False

    def execute_command(self, command: str, args: Optional[List[str]] = None) -> IntegrationResult:
        """Execute a Python tool command."""
        if not self._initialized:
            return IntegrationResult(
                success=False,
                error=f"{self.config.tool_name} integration not initialized"
            )
        
        tool_name = self.config.tool_name.lower()
        
        if tool_name in ["pytest", "ruff", "mypy", "black", "isort"]:
            tool_command = [sys.executable, "-m", tool_name]
        else:
            tool_command = [tool_name]
        
        if command != "run":  # For non-run commands, add the command
            tool_command.append(command)
        
        if args:
            tool_command.extend(args)
        
        return self._run_subprocess(tool_command)

    def get_status(self) -> Dict[str, Any]:
        """Get Python tool status."""
        if not self._initialized:
            return {"error": "Not initialized"}
        
        return {
            "initialized": self._initialized,
            "tool_name": self.config.tool_name,
            "version": self.config.version,
        }

    def run_tests(self, test_path: Optional[str] = None) -> IntegrationResult:
        """Run tests using pytest."""
        if self.config.tool_name.lower() != "pytest":
            return IntegrationResult(
                success=False,
                error="This method is only for pytest integration"
            )
        
        args = []
        if test_path:
            args.append(test_path)
        
        # Add common pytest options
        args.extend(["-v", "--tb=short"])
        
        return self.execute_command("run", args)

    def format_code(self, file_paths: List[str]) -> IntegrationResult:
        """Format code using ruff or black."""
        tool_name = self.config.tool_name.lower()
        
        if tool_name == "ruff":
            return self.execute_command("format", file_paths)
        elif tool_name == "black":
            return self.execute_command("run", file_paths)
        else:
            return IntegrationResult(
                success=False,
                error=f"Code formatting not supported for {tool_name}"
            )

    def check_types(self, file_paths: Optional[List[str]] = None) -> IntegrationResult:
        """Check types using mypy."""
        if self.config.tool_name.lower() != "mypy":
            return IntegrationResult(
                success=False,
                error="This method is only for mypy integration"
            )
        
        args = file_paths or ["."]
        return self.execute_command("run", args)


class CustomIntegration(BaseIntegration):
    """Custom integration for proprietary or specialized tools."""

    def initialize(self) -> bool:
        """Initialize custom integration."""
        # Check if custom executable exists
        executable = self.config.configuration.get("executable")
        if not executable:
            return False
        
        try:
            # Try to run the tool with a version or help command
            version_cmd = self.config.configuration.get("version_command", ["--version"])
            if isinstance(version_cmd, str):
                version_cmd = [version_cmd]
            
            result = self._run_subprocess([executable] + version_cmd)
            self._initialized = result.success
            return self._initialized
        except Exception:
            return False

    def execute_command(self, command: str, args: Optional[List[str]] = None) -> IntegrationResult:
        """Execute a custom tool command."""
        if not self._initialized:
            return IntegrationResult(
                success=False,
                error=f"{self.config.tool_name} integration not initialized"
            )
        
        executable = self.config.configuration.get("executable")
        if not executable:
            return IntegrationResult(
                success=False,
                error="No executable configured for custom integration"
            )
        
        # Build command
        tool_command = [executable]
        
        # Add command if not the default run command
        if command != "run":
            tool_command.append(command)
        
        if args:
            tool_command.extend(args)
        
        # Apply any custom command mappings
        if command in self.config.custom_commands:
            custom_cmd = self.config.custom_commands[command]
            tool_command = [executable] + custom_cmd.split()
            if args:
                tool_command.extend(args)
        
        return self._run_subprocess(tool_command)

    def get_status(self) -> Dict[str, Any]:
        """Get custom tool status."""
        return {
            "initialized": self._initialized,
            "tool_name": self.config.tool_name,
            "executable": self.config.configuration.get("executable"),
            "configuration": self.config.configuration,
        }


@dataclass
class IntegrationRegistry:
    """Registry of available integrations."""

    integrations: Dict[str, BaseIntegration] = field(default_factory=dict)
    integration_types: Dict[str, type] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize default integration types."""
        self.integration_types.update({
            "git": GitIntegration,
            "docker": DockerIntegration,
            "python_tool": PythonToolIntegration,
            "custom": CustomIntegration,
        })

    def register_integration_type(self, name: str, integration_class: type) -> None:
        """Register a new integration type.
        
        Args:
            name: Integration type name
            integration_class: Integration class
        """
        self.integration_types[name] = integration_class

    def create_integration(self, name: str, integration_type: str, config: ToolConfig) -> Optional[BaseIntegration]:
        """Create a new integration instance.
        
        Args:
            name: Integration name
            integration_type: Type of integration
            config: Tool configuration
            
        Returns:
            Created integration or None if type not found
        """
        if integration_type not in self.integration_types:
            return None
        
        integration_class = self.integration_types[integration_type]
        integration = integration_class(name, config)
        
        if integration.initialize():
            self.integrations[name] = integration
            return integration
        
        return None

    def get_integration(self, name: str) -> Optional[BaseIntegration]:
        """Get an integration by name.
        
        Args:
            name: Integration name
            
        Returns:
            Integration instance or None if not found
        """
        return self.integrations.get(name)

    def remove_integration(self, name: str) -> bool:
        """Remove an integration.
        
        Args:
            name: Integration name
            
        Returns:
            True if removed, False if not found
        """
        if name in self.integrations:
            self.integrations[name].cleanup()
            del self.integrations[name]
            return True
        return False

    def list_integrations(self) -> List[str]:
        """List all registered integration names.
        
        Returns:
            List of integration names
        """
        return list(self.integrations.keys())

    def get_integration_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all integrations.
        
        Returns:
            Dictionary mapping integration names to their status
        """
        return {
            name: integration.get_status()
            for name, integration in self.integrations.items()
        }


class IntegrationManager:
    """Manages tool integrations and external service connections."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize integration manager.
        
        Args:
            config_dir: Directory for storing integration configurations
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / ".dev_agent" / "integrations"
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.registry = IntegrationRegistry()
        self._load_saved_integrations()

    def _load_saved_integrations(self) -> None:
        """Load saved integration configurations."""
        config_file = self.config_dir / "integrations.json"
        if not config_file.exists():
            return
        
        try:
            with open(config_file, encoding="utf-8") as f:
                data = json.load(f)
            
            for integration_data in data.get("integrations", []):
                name = integration_data["name"]
                integration_type = integration_data["type"]
                config_data = integration_data["config"]
                
                config = ToolConfig(**config_data)
                self.registry.create_integration(name, integration_type, config)
                
        except Exception as e:
            print(f"Error loading saved integrations: {e}")

    def _save_integrations(self) -> None:
        """Save integration configurations."""
        config_file = self.config_dir / "integrations.json"
        
        integrations_data = []
        for name, integration in self.registry.integrations.items():
            # Determine integration type
            integration_type = "custom"
            for type_name, type_class in self.registry.integration_types.items():
                if isinstance(integration, type_class):
                    integration_type = type_name
                    break
            
            integrations_data.append({
                "name": name,
                "type": integration_type,
                "config": integration.config.model_dump(mode='json'),
            })
        
        try:
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump({"integrations": integrations_data}, f, indent=2)
        except Exception as e:
            print(f"Error saving integrations: {e}")

    def add_integration(
        self,
        name: str,
        integration_type: str,
        tool_config: ToolConfig,
    ) -> bool:
        """Add a new integration.
        
        Args:
            name: Integration name
            integration_type: Type of integration
            tool_config: Tool configuration
            
        Returns:
            True if added successfully, False otherwise
        """
        if name in self.registry.integrations:
            return False
        
        integration = self.registry.create_integration(name, integration_type, tool_config)
        if integration:
            self._save_integrations()
            return True
        
        return False

    def remove_integration(self, name: str) -> bool:
        """Remove an integration.
        
        Args:
            name: Integration name
            
        Returns:
            True if removed successfully, False otherwise
        """
        if self.registry.remove_integration(name):
            self._save_integrations()
            return True
        return False

    def get_integration(self, name: str) -> Optional[BaseIntegration]:
        """Get an integration by name.
        
        Args:
            name: Integration name
            
        Returns:
            Integration instance or None if not found
        """
        return self.registry.get_integration(name)

    def list_integrations(self) -> List[str]:
        """List all integration names.
        
        Returns:
            List of integration names
        """
        return self.registry.list_integrations()

    def execute_integration_command(
        self,
        integration_name: str,
        command: str,
        args: Optional[List[str]] = None,
    ) -> IntegrationResult:
        """Execute a command using an integration.
        
        Args:
            integration_name: Name of integration to use
            command: Command to execute
            args: Optional command arguments
            
        Returns:
            Integration result
        """
        integration = self.get_integration(integration_name)
        if not integration:
            return IntegrationResult(
                success=False,
                error=f"Integration '{integration_name}' not found"
            )
        
        return integration.execute_command(command, args)

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all integrations.
        
        Returns:
            Dictionary mapping integration names to their status
        """
        return self.registry.get_integration_status()

    def test_integration(self, name: str) -> bool:
        """Test if an integration is working.
        
        Args:
            name: Integration name
            
        Returns:
            True if integration is working, False otherwise
        """
        integration = self.get_integration(name)
        if not integration:
            return False
        
        status = integration.get_status()
        return status.get("initialized", False)

    def setup_common_integrations(self) -> Dict[str, bool]:
        """Setup common development tool integrations.
        
        Returns:
            Dictionary mapping tool names to setup success status
        """
        results = {}
        
        # Common tools to set up
        common_tools = [
            ("git", "git", {}),
            ("docker", "docker", {}),
            ("pytest", "python_tool", {"executable": "pytest"}),
            ("ruff", "python_tool", {"executable": "ruff"}),
            ("mypy", "python_tool", {"executable": "mypy"}),
        ]
        
        for name, integration_type, config_data in common_tools:
            config = ToolConfig(
                tool_name=name,
                configuration=config_data,
            )
            
            results[name] = self.add_integration(name, integration_type, config)
        
        return results

    def cleanup_all(self) -> None:
        """Clean up all integrations."""
        for integration in self.registry.integrations.values():
            integration.cleanup()
        
        self.registry.integrations.clear()