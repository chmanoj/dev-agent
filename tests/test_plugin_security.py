"""Tests for plugin security validation."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from dev_agent.plugins.models import PluginConfig, SecurityLevel, IDEType
from dev_agent.plugins.security import PluginSecurityManager


class TestPluginSecurityManager:
    """Test cases for PluginSecurityManager class."""
    
    @pytest.fixture
    def security_manager(self):
        """Create a PluginSecurityManager instance."""
        return PluginSecurityManager()
    
    @pytest.fixture
    def safe_plugin_config(self):
        """Create a safe plugin configuration."""
        return PluginConfig(
            name="safe-plugin",
            version="1.0.0",
            description="Safe test plugin",
            author="Test Author",
            ide_type=IDEType.VSCODE,
            security_level=SecurityLevel.SANDBOXED,
            permissions=["ide_integration"],
        )
    
    @pytest.fixture
    def unsafe_plugin_config(self):
        """Create an unsafe plugin configuration."""
        return PluginConfig(
            name="unsafe-plugin",
            version="1.0.0",
            description="Unsafe test plugin",
            author="Test Author",
            ide_type=IDEType.VSCODE,
            security_level=SecurityLevel.TRUSTED,
            permissions=["system_commands", "network_access"],
        )
    
    @pytest.fixture
    def safe_plugin_dir(self, safe_plugin_config):
        """Create a safe plugin directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_dir = Path(temp_dir)
            
            # Create safe Python file
            safe_file = plugin_dir / "safe.py"
            safe_file.write_text("""
def safe_function():
    return "Hello, World!"

class SafeClass:
    def __init__(self):
        self.value = 42
    
    def get_value(self):
        return self.value
""")
            
            yield plugin_dir
    
    @pytest.fixture
    def unsafe_plugin_dir(self, unsafe_plugin_config):
        """Create an unsafe plugin directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_dir = Path(temp_dir)
            
            # Create unsafe Python file
            unsafe_file = plugin_dir / "unsafe.py"
            unsafe_file.write_text("""
import os
import subprocess
import sys

def dangerous_function():
    # This is dangerous - executing system commands
    os.system("rm -rf /")
    subprocess.call(["malicious", "command"])
    
    # This is also dangerous - dynamic code execution
    eval("print('dangerous')")
    exec("import sys; sys.exit()")
    
    # Accessing restricted modules
    __import__("os")
    
def another_dangerous_function():
    # File system access
    with open("/etc/passwd", "r") as f:
        return f.read()
""")
            
            yield plugin_dir
    
    def test_validate_safe_plugin(self, security_manager, safe_plugin_dir, safe_plugin_config):
        """Test validation of a safe plugin."""
        validation = security_manager.validate_plugin(safe_plugin_dir, safe_plugin_config)
        
        assert validation.is_valid is True
        assert validation.security_level == SecurityLevel.SANDBOXED
        assert len(validation.violations) == 0
        assert "ide_integration" in validation.permissions_granted
    
    def test_validate_unsafe_plugin(self, security_manager, unsafe_plugin_dir, unsafe_plugin_config):
        """Test validation of an unsafe plugin."""
        validation = security_manager.validate_plugin(unsafe_plugin_dir, unsafe_plugin_config)
        
        assert validation.is_valid is False
        assert validation.security_level == SecurityLevel.RESTRICTED
        assert len(validation.violations) > 0
        
        # Check for specific violations
        violation_text = " ".join(validation.violations)
        assert "os" in violation_text or "subprocess" in violation_text
        assert "eval" in violation_text or "exec" in violation_text
    
    def test_invalid_permissions(self, security_manager, safe_plugin_dir):
        """Test plugin with invalid permissions."""
        config = PluginConfig(
            name="invalid-perms-plugin",
            version="1.0.0",
            description="Plugin with invalid permissions",
            author="Test Author",
            ide_type=IDEType.VSCODE,
            permissions=["invalid_permission", "another_invalid"],
        )
        
        validation = security_manager.validate_plugin(safe_plugin_dir, config)
        
        assert validation.is_valid is False
        assert len(validation.violations) > 0
        assert "Invalid permissions" in validation.violations[0]
    
    def test_trusted_plugin_management(self, security_manager):
        """Test trusted plugin management."""
        plugin_id = "test:trusted-plugin"
        
        # Initially not trusted
        assert security_manager.is_trusted_plugin(plugin_id) is False
        
        # Add to trusted list
        security_manager.add_trusted_plugin(plugin_id)
        assert security_manager.is_trusted_plugin(plugin_id) is True
        
        # Remove from trusted list
        security_manager.remove_trusted_plugin(plugin_id)
        assert security_manager.is_trusted_plugin(plugin_id) is False
    
    def test_permission_granting_trusted(self, security_manager):
        """Test permission granting for trusted plugins."""
        requested_permissions = ["file_read", "file_write", "network_access"]
        
        granted = security_manager._determine_permissions(
            requested_permissions,
            SecurityLevel.TRUSTED,
        )
        
        assert granted == requested_permissions
    
    def test_permission_granting_sandboxed(self, security_manager):
        """Test permission granting for sandboxed plugins."""
        requested_permissions = ["ide_integration", "workspace_access", "system_commands"]
        
        granted = security_manager._determine_permissions(
            requested_permissions,
            SecurityLevel.SANDBOXED,
        )
        
        # Only safe permissions should be granted
        assert "ide_integration" in granted
        assert "workspace_access" in granted
        assert "system_commands" not in granted
    
    def test_permission_granting_restricted(self, security_manager):
        """Test permission granting for restricted plugins."""
        requested_permissions = ["ide_integration", "workspace_access"]
        
        granted = security_manager._determine_permissions(
            requested_permissions,
            SecurityLevel.RESTRICTED,
        )
        
        # No permissions should be granted
        assert len(granted) == 0
    
    def test_analyze_python_file_safe(self, security_manager, safe_plugin_dir):
        """Test analysis of safe Python file."""
        safe_file = safe_plugin_dir / "safe.py"
        
        violations, warnings = security_manager._analyze_python_file(safe_file)
        
        assert len(violations) == 0
        # May have warnings for suspicious patterns, but no violations
    
    def test_analyze_python_file_unsafe(self, security_manager, unsafe_plugin_dir):
        """Test analysis of unsafe Python file."""
        unsafe_file = unsafe_plugin_dir / "unsafe.py"
        
        violations, warnings = security_manager._analyze_python_file(unsafe_file)
        
        assert len(violations) > 0
        
        # Check for specific violations
        violation_text = " ".join(violations)
        assert "os" in violation_text or "subprocess" in violation_text
        assert "eval" in violation_text or "exec" in violation_text
    
    def test_analyze_nonexistent_file(self, security_manager):
        """Test analysis of non-existent file."""
        nonexistent_file = Path("/nonexistent/file.py")
        
        violations, warnings = security_manager._analyze_python_file(nonexistent_file)
        
        # Should have warnings about failed analysis
        assert len(warnings) > 0
        assert "Failed to analyze" in warnings[0]
    
    def test_restricted_imports_detection(self, security_manager):
        """Test detection of restricted imports."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_dir = Path(temp_dir)
            
            # Create file with restricted imports
            restricted_file = plugin_dir / "restricted.py"
            restricted_file.write_text("""
import os
import subprocess
from sys import exit
import __builtin__
""")
            
            violations, warnings = security_manager._analyze_python_file(restricted_file)
            
            assert len(violations) > 0
            violation_text = " ".join(violations)
            assert "os" in violation_text
            assert "subprocess" in violation_text
            assert "sys" in violation_text
    
    def test_restricted_functions_detection(self, security_manager):
        """Test detection of restricted function calls."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_dir = Path(temp_dir)
            
            # Create file with restricted function calls
            restricted_file = plugin_dir / "restricted.py"
            restricted_file.write_text("""
def dangerous():
    eval("print('hello')")
    exec("x = 1")
    compile("code", "string", "exec")
    __import__("os")
    getattr(obj, "attr")
""")
            
            violations, warnings = security_manager._analyze_python_file(restricted_file)
            
            assert len(violations) > 0
            violation_text = " ".join(violations)
            assert "eval" in violation_text
            assert "exec" in violation_text