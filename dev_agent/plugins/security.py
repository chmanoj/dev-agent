"""Security validation and management for plugins."""

from __future__ import annotations

import ast
import logging
import re
from pathlib import Path
from typing import List, Set

from dev_agent.plugins.models import (
    PluginConfig,
    SecurityLevel,
    SecurityValidation,
)

logger = logging.getLogger(__name__)


class PluginSecurityManager:
    """Manages plugin security validation and sandboxing."""
    
    # Dangerous imports and functions that are restricted
    RESTRICTED_IMPORTS = {
        "os",
        "subprocess",
        "sys",
        "importlib",
        "__import__",
        "eval",
        "exec",
        "compile",
        "open",
        "file",
        "input",
        "raw_input",
    }
    
    RESTRICTED_FUNCTIONS = {
        "eval",
        "exec",
        "compile",
        "__import__",
        "getattr",
        "setattr",
        "delattr",
        "hasattr",
        "globals",
        "locals",
        "vars",
        "dir",
    }
    
    ALLOWED_PERMISSIONS = {
        "file_read",
        "file_write",
        "network_access",
        "system_commands",
        "ide_integration",
        "workspace_access",
        "ai_services",
    }
    
    def __init__(self) -> None:
        """Initialize the security manager."""
        self.trusted_plugins: Set[str] = set()
    
    def validate_plugin(self, plugin_path: Path, config: PluginConfig) -> SecurityValidation:
        """Validate plugin security.
        
        Args:
            plugin_path: Path to the plugin directory
            config: Plugin configuration
            
        Returns:
            Security validation result
        """
        violations = []
        warnings = []
        
        # Check permissions
        invalid_permissions = set(config.permissions) - self.ALLOWED_PERMISSIONS
        if invalid_permissions:
            violations.append(f"Invalid permissions: {invalid_permissions}")
        
        # Analyze plugin code
        python_files = list(plugin_path.glob("**/*.py"))
        for py_file in python_files:
            file_violations, file_warnings = self._analyze_python_file(py_file)
            violations.extend(file_violations)
            warnings.extend(file_warnings)
        
        # Determine security level
        if violations:
            security_level = SecurityLevel.RESTRICTED
        elif warnings or config.security_level == SecurityLevel.SANDBOXED:
            security_level = SecurityLevel.SANDBOXED
        else:
            security_level = SecurityLevel.TRUSTED
        
        # Grant permissions based on security level
        permissions_granted = self._determine_permissions(config.permissions, security_level)
        
        return SecurityValidation(
            is_valid=len(violations) == 0,
            security_level=security_level,
            violations=violations,
            warnings=warnings,
            permissions_granted=permissions_granted,
        )
    
    def add_trusted_plugin(self, plugin_id: str) -> None:
        """Add a plugin to the trusted list.
        
        Args:
            plugin_id: ID of the plugin to trust
        """
        self.trusted_plugins.add(plugin_id)
        logger.info(f"Added trusted plugin: {plugin_id}")
    
    def remove_trusted_plugin(self, plugin_id: str) -> None:
        """Remove a plugin from the trusted list.
        
        Args:
            plugin_id: ID of the plugin to untrust
        """
        self.trusted_plugins.discard(plugin_id)
        logger.info(f"Removed trusted plugin: {plugin_id}")
    
    def is_trusted_plugin(self, plugin_id: str) -> bool:
        """Check if a plugin is trusted.
        
        Args:
            plugin_id: ID of the plugin
            
        Returns:
            True if the plugin is trusted
        """
        return plugin_id in self.trusted_plugins
    
    def _analyze_python_file(self, file_path: Path) -> tuple[List[str], List[str]]:
        """Analyze a Python file for security issues.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            Tuple of (violations, warnings)
        """
        violations = []
        warnings = []
        
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content)
            
            # Check for dangerous imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in self.RESTRICTED_IMPORTS:
                            violations.append(f"Restricted import: {alias.name} in {file_path}")
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module in self.RESTRICTED_IMPORTS:
                        violations.append(f"Restricted import: {node.module} in {file_path}")
                
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in self.RESTRICTED_FUNCTIONS:
                            violations.append(f"Restricted function call: {node.func.id} in {file_path}")
            
            # Check for suspicious patterns
            suspicious_patterns = [
                r"__.*__",  # Dunder methods
                r"eval\s*\(",  # eval calls
                r"exec\s*\(",  # exec calls
                r"subprocess\.",  # subprocess usage
                r"os\.",  # os module usage
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, content):
                    warnings.append(f"Suspicious pattern '{pattern}' found in {file_path}")
        
        except Exception as e:
            warnings.append(f"Failed to analyze {file_path}: {e}")
        
        return violations, warnings
    
    def _determine_permissions(
        self,
        requested_permissions: List[str],
        security_level: SecurityLevel,
    ) -> List[str]:
        """Determine which permissions to grant based on security level.
        
        Args:
            requested_permissions: Permissions requested by the plugin
            security_level: Security level of the plugin
            
        Returns:
            List of granted permissions
        """
        if security_level == SecurityLevel.TRUSTED:
            return requested_permissions
        
        elif security_level == SecurityLevel.SANDBOXED:
            # Allow safe permissions only
            safe_permissions = {"ide_integration", "workspace_access"}
            return [p for p in requested_permissions if p in safe_permissions]
        
        else:  # RESTRICTED
            # No permissions granted
            return []