"""Configuration management for dev-agent."""

from .config_manager import ConfigManager, DevAgentConfig
from .config_validator import ConfigValidator, ConfigValidationRule, ConsistencyCheck
from .customization_manager import (
    ArchitecturalPreferences,
    CodingStandards,
    CustomizationManager,
    CustomizationProfile,
    QualityThresholds,
    ToolConfig,
    ValidationResult,
)
from .integration_manager import (
    BaseIntegration,
    CustomIntegration,
    DockerIntegration,
    GitIntegration,
    IntegrationManager,
    IntegrationResult,
    PythonToolIntegration,
)
from .logging_config import get_logger, log_config_info, log_system_info, setup_logging
from .template_manager import CustomTemplate, TemplateManager, TemplateMetadata

__all__ = [
    # Core config
    "ConfigManager",
    "DevAgentConfig",
    # Customization
    "CustomizationManager",
    "CustomizationProfile",
    "CodingStandards",
    "ArchitecturalPreferences",
    "QualityThresholds",
    "ToolConfig",
    "ValidationResult",
    # Template management
    "TemplateManager",
    "CustomTemplate",
    "TemplateMetadata",
    # Validation
    "ConfigValidator",
    "ConfigValidationRule",
    "ConsistencyCheck",
    # Integration
    "IntegrationManager",
    "BaseIntegration",
    "GitIntegration",
    "DockerIntegration",
    "PythonToolIntegration",
    "CustomIntegration",
    "IntegrationResult",
    # Logging
    "get_logger",
    "log_config_info",
    "log_system_info",
    "setup_logging",
]
