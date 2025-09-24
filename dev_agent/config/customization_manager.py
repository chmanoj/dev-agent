"""Advanced configuration and customization management for dev-agent."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from pydantic import BaseModel, Field, ValidationError

from ..models.enums import FrameworkType, LanguageType, ProjectType
from ..models.templates import ProjectTemplate, TemplateValidationResult
from .config_manager import DevAgentConfig


class CodingStandards(BaseModel):
    """Coding standards and conventions configuration."""

    naming_conventions: Dict[str, str] = Field(
        default_factory=lambda: {
            "class": "PascalCase",
            "function": "snake_case",
            "variable": "snake_case",
            "constant": "UPPER_CASE",
            "module": "snake_case",
            "package": "snake_case",
        },
        description="Naming convention rules"
    )
    
    line_length: int = Field(default=88, description="Maximum line length")
    indentation: str = Field(default="spaces", description="Indentation type (spaces/tabs)")
    indent_size: int = Field(default=4, description="Number of spaces/tabs for indentation")
    
    import_style: Dict[str, Any] = Field(
        default_factory=lambda: {
            "sort_imports": True,
            "group_imports": True,
            "separate_local": True,
            "force_single_line": False,
        },
        description="Import organization rules"
    )
    
    documentation_style: str = Field(default="google", description="Docstring style (google/numpy/sphinx)")
    type_hints_required: bool = Field(default=True, description="Whether type hints are required")
    
    quality_thresholds: Dict[str, float] = Field(
        default_factory=lambda: {
            "complexity": 10.0,
            "coverage": 90.0,
            "maintainability": 80.0,
            "duplication": 5.0,
        },
        description="Code quality thresholds"
    )


class ArchitecturalPreferences(BaseModel):
    """Architectural patterns and preferences."""

    preferred_patterns: List[str] = Field(
        default_factory=lambda: ["MVC", "Repository", "Factory", "Observer"],
        description="Preferred design patterns"
    )
    
    layered_architecture: bool = Field(default=True, description="Use layered architecture")
    dependency_injection: bool = Field(default=True, description="Use dependency injection")
    
    error_handling_strategy: str = Field(
        default="exception_based", 
        description="Error handling approach (exception_based/result_based/hybrid)"
    )
    
    logging_strategy: Dict[str, Any] = Field(
        default_factory=lambda: {
            "structured_logging": True,
            "log_levels": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            "include_context": True,
            "async_logging": False,
        },
        description="Logging configuration"
    )
    
    testing_strategy: Dict[str, Any] = Field(
        default_factory=lambda: {
            "test_driven": True,
            "unit_test_coverage": 90.0,
            "integration_tests": True,
            "e2e_tests": False,
            "property_based_testing": False,
        },
        description="Testing approach"
    )


class ToolConfig(BaseModel):
    """Configuration for external tools and integrations."""

    tool_name: str = Field(..., description="Name of the tool")
    enabled: bool = Field(default=True, description="Whether tool is enabled")
    version: Optional[str] = Field(default=None, description="Required tool version")
    
    configuration: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Tool-specific configuration"
    )
    
    integration_points: List[str] = Field(
        default_factory=list,
        description="Points where tool integrates with workflow"
    )
    
    custom_commands: Dict[str, str] = Field(
        default_factory=dict,
        description="Custom commands for the tool"
    )


class TemplateOverride(BaseModel):
    """Override configuration for templates."""

    template_id: str = Field(..., description="ID of template to override")
    override_type: str = Field(..., description="Type of override (replace/merge/extend)")
    
    file_overrides: Dict[str, str] = Field(
        default_factory=dict,
        description="File content overrides"
    )
    
    variable_overrides: Dict[str, Any] = Field(
        default_factory=dict,
        description="Template variable overrides"
    )
    
    structure_modifications: Dict[str, Any] = Field(
        default_factory=dict,
        description="Directory structure modifications"
    )


class QualityThresholds(BaseModel):
    """Quality thresholds and metrics configuration."""

    code_coverage: float = Field(default=90.0, description="Minimum code coverage percentage")
    cyclomatic_complexity: float = Field(default=10.0, description="Maximum cyclomatic complexity")
    maintainability_index: float = Field(default=80.0, description="Minimum maintainability index")
    
    security_score: float = Field(default=95.0, description="Minimum security score")
    performance_score: float = Field(default=85.0, description="Minimum performance score")
    
    technical_debt_ratio: float = Field(default=5.0, description="Maximum technical debt ratio")
    duplication_percentage: float = Field(default=3.0, description="Maximum code duplication")
    
    custom_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Custom quality metrics and thresholds"
    )


class CustomizationProfile(BaseModel):
    """Complete customization profile for a team or individual."""

    id: str = Field(..., description="Unique profile identifier")
    name: str = Field(..., description="Profile display name")
    description: str = Field(default="", description="Profile description")
    version: str = Field(default="1.0.0", description="Profile version")
    
    # Team information
    team_id: Optional[str] = Field(default=None, description="Associated team ID")
    created_by: str = Field(..., description="Profile creator")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    
    # Configuration sections
    coding_standards: CodingStandards = Field(
        default_factory=CodingStandards,
        description="Coding standards and conventions"
    )
    
    architectural_preferences: ArchitecturalPreferences = Field(
        default_factory=ArchitecturalPreferences,
        description="Architectural patterns and preferences"
    )
    
    tool_configurations: Dict[str, ToolConfig] = Field(
        default_factory=dict,
        description="External tool configurations"
    )
    
    template_overrides: Dict[str, TemplateOverride] = Field(
        default_factory=dict,
        description="Template customizations"
    )
    
    quality_thresholds: QualityThresholds = Field(
        default_factory=QualityThresholds,
        description="Quality metrics and thresholds"
    )
    
    # Language and framework preferences
    preferred_languages: List[LanguageType] = Field(
        default_factory=list,
        description="Preferred programming languages"
    )
    
    preferred_frameworks: List[FrameworkType] = Field(
        default_factory=list,
        description="Preferred frameworks and libraries"
    )
    
    # Custom generation rules
    custom_generation_rules: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom code generation rules"
    )
    
    # Analysis rules
    custom_analysis_rules: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom code analysis rules"
    )


@dataclass
class ValidationResult:
    """Result of configuration validation."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


class CustomizationManager:
    """Manages customization profiles and advanced configuration."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize customization manager.
        
        Args:
            config_dir: Directory for storing customization profiles
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / ".dev_agent" / "customization"
        
        self.profiles_dir = self.config_dir / "profiles"
        self.templates_dir = self.config_dir / "templates"
        self.shared_dir = self.config_dir / "shared"
        
        self._ensure_directories()
        self._loaded_profiles: Dict[str, CustomizationProfile] = {}
        self._template_cache: Dict[str, ProjectTemplate] = {}

    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        for directory in [self.config_dir, self.profiles_dir, self.templates_dir, self.shared_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def create_profile(
        self,
        profile_id: str,
        name: str,
        created_by: str,
        description: str = "",
        team_id: Optional[str] = None,
    ) -> CustomizationProfile:
        """Create a new customization profile.
        
        Args:
            profile_id: Unique identifier for the profile
            name: Display name for the profile
            created_by: Creator of the profile
            description: Optional description
            team_id: Optional team association
            
        Returns:
            Created customization profile
            
        Raises:
            ValueError: If profile ID already exists
        """
        if self.profile_exists(profile_id):
            raise ValueError(f"Profile with ID '{profile_id}' already exists")
        
        from datetime import datetime
        
        profile = CustomizationProfile(
            id=profile_id,
            name=name,
            description=description,
            team_id=team_id,
            created_by=created_by,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        
        self.save_profile(profile)
        return profile

    def load_profile(self, profile_id: str) -> Optional[CustomizationProfile]:
        """Load a customization profile.
        
        Args:
            profile_id: ID of the profile to load
            
        Returns:
            Loaded profile or None if not found
        """
        if profile_id in self._loaded_profiles:
            return self._loaded_profiles[profile_id]
        
        profile_path = self.profiles_dir / f"{profile_id}.json"
        if not profile_path.exists():
            return None
        
        try:
            with open(profile_path, encoding="utf-8") as f:
                data = json.load(f)
            
            profile = CustomizationProfile(**data)
            self._loaded_profiles[profile_id] = profile
            return profile
            
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"Error loading profile {profile_id}: {e}")
            return None

    def save_profile(self, profile: CustomizationProfile) -> bool:
        """Save a customization profile.
        
        Args:
            profile: Profile to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            from datetime import datetime
            
            # Update timestamp
            profile.updated_at = datetime.now().isoformat()
            
            profile_path = self.profiles_dir / f"{profile.id}.json"
            with open(profile_path, "w", encoding="utf-8") as f:
                # Use model_dump with mode='json' to handle enum serialization
                json.dump(profile.model_dump(mode='json'), f, indent=2)
            
            self._loaded_profiles[profile.id] = profile
            return True
            
        except Exception as e:
            print(f"Error saving profile {profile.id}: {e}")
            return False

    def delete_profile(self, profile_id: str) -> bool:
        """Delete a customization profile.
        
        Args:
            profile_id: ID of the profile to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            profile_path = self.profiles_dir / f"{profile_id}.json"
            if profile_path.exists():
                profile_path.unlink()
            
            if profile_id in self._loaded_profiles:
                del self._loaded_profiles[profile_id]
            
            return True
            
        except Exception as e:
            print(f"Error deleting profile {profile_id}: {e}")
            return False

    def list_profiles(self, team_id: Optional[str] = None) -> List[CustomizationProfile]:
        """List available customization profiles.
        
        Args:
            team_id: Optional team filter
            
        Returns:
            List of available profiles
        """
        profiles = []
        
        for profile_file in self.profiles_dir.glob("*.json"):
            profile_id = profile_file.stem
            profile = self.load_profile(profile_id)
            
            if profile and (team_id is None or profile.team_id == team_id):
                profiles.append(profile)
        
        return profiles

    def profile_exists(self, profile_id: str) -> bool:
        """Check if a profile exists.
        
        Args:
            profile_id: ID to check
            
        Returns:
            True if profile exists, False otherwise
        """
        profile_path = self.profiles_dir / f"{profile_id}.json"
        return profile_path.exists()

    def validate_profile(self, profile: CustomizationProfile) -> ValidationResult:
        """Validate a customization profile.
        
        Args:
            profile: Profile to validate
            
        Returns:
            Validation result with errors and warnings
        """
        result = ValidationResult(is_valid=True)
        
        # Validate basic fields
        if not profile.id or not profile.id.strip():
            result.errors.append("Profile ID cannot be empty")
            result.is_valid = False
        
        if not profile.name or not profile.name.strip():
            result.errors.append("Profile name cannot be empty")
            result.is_valid = False
        
        if not profile.created_by or not profile.created_by.strip():
            result.errors.append("Profile creator cannot be empty")
            result.is_valid = False
        
        # Validate coding standards
        standards = profile.coding_standards
        if standards.line_length < 50 or standards.line_length > 200:
            result.warnings.append(f"Line length {standards.line_length} is outside recommended range (50-200)")
        
        if standards.indent_size < 2 or standards.indent_size > 8:
            result.warnings.append(f"Indent size {standards.indent_size} is outside recommended range (2-8)")
        
        # Validate quality thresholds
        thresholds = profile.quality_thresholds
        if thresholds.code_coverage < 0 or thresholds.code_coverage > 100:
            result.errors.append("Code coverage must be between 0 and 100")
            result.is_valid = False
        
        if thresholds.cyclomatic_complexity < 1:
            result.errors.append("Cyclomatic complexity threshold must be positive")
            result.is_valid = False
        
        # Validate tool configurations
        for tool_name, tool_config in profile.tool_configurations.items():
            if not tool_config.tool_name:
                result.errors.append(f"Tool configuration for '{tool_name}' missing tool name")
                result.is_valid = False
        
        # Add suggestions
        if not profile.preferred_languages:
            result.suggestions.append("Consider specifying preferred programming languages")
        
        if not profile.preferred_frameworks:
            result.suggestions.append("Consider specifying preferred frameworks")
        
        return result

    def merge_profiles(
        self,
        base_profile: CustomizationProfile,
        override_profile: CustomizationProfile,
    ) -> CustomizationProfile:
        """Merge two customization profiles.
        
        Args:
            base_profile: Base profile
            override_profile: Profile with overrides
            
        Returns:
            Merged profile
        """
        # Create a copy of the base profile
        merged_data = base_profile.model_dump()
        override_data = override_profile.model_dump()
        
        # Merge configurations
        self._deep_merge(merged_data, override_data)
        
        # Create new profile with merged data
        merged_profile = CustomizationProfile(**merged_data)
        
        # Update metadata
        merged_profile.id = f"{base_profile.id}_merged_{override_profile.id}"
        merged_profile.name = f"{base_profile.name} + {override_profile.name}"
        merged_profile.description = f"Merged profile: {base_profile.description} with {override_profile.description}"
        
        return merged_profile

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Deep merge two dictionaries.
        
        Args:
            base: Base dictionary (modified in place)
            override: Override dictionary
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def apply_profile_to_config(
        self,
        profile: CustomizationProfile,
        base_config: DevAgentConfig,
    ) -> DevAgentConfig:
        """Apply customization profile to base configuration.
        
        Args:
            profile: Customization profile to apply
            base_config: Base configuration
            
        Returns:
            Modified configuration
        """
        # Create a copy of the base config
        config_dict = base_config.to_dict()
        
        # Apply coding standards to CLI config
        config_dict["cli"]["color_output"] = True  # Enable colors for better UX
        
        # Apply quality thresholds to indexing config
        if hasattr(base_config.indexing, "quality_thresholds"):
            config_dict["indexing"]["quality_thresholds"] = profile.quality_thresholds.model_dump()
        
        # Apply tool configurations
        if "tools" not in config_dict:
            config_dict["tools"] = {}
        
        for tool_name, tool_config in profile.tool_configurations.items():
            config_dict["tools"][tool_name] = tool_config.model_dump()
        
        return DevAgentConfig.from_dict(config_dict)

    def export_profile(self, profile_id: str, export_path: Path) -> bool:
        """Export a profile to a file.
        
        Args:
            profile_id: ID of profile to export
            export_path: Path to export file
            
        Returns:
            True if exported successfully, False otherwise
        """
        profile = self.load_profile(profile_id)
        if not profile:
            return False
        
        try:
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(profile.model_dump(mode='json'), f, indent=2)
            return True
            
        except Exception as e:
            print(f"Error exporting profile: {e}")
            return False

    def import_profile(self, import_path: Path, new_profile_id: Optional[str] = None) -> Optional[str]:
        """Import a profile from a file.
        
        Args:
            import_path: Path to import file
            new_profile_id: Optional new ID for imported profile
            
        Returns:
            ID of imported profile or None if failed
        """
        try:
            with open(import_path, encoding="utf-8") as f:
                data = json.load(f)
            
            profile = CustomizationProfile(**data)
            
            if new_profile_id:
                profile.id = new_profile_id
            
            # Check if profile already exists
            if self.profile_exists(profile.id):
                # Generate unique ID
                counter = 1
                base_id = profile.id
                while self.profile_exists(f"{base_id}_{counter}"):
                    counter += 1
                profile.id = f"{base_id}_{counter}"
            
            if self.save_profile(profile):
                return profile.id
            
            return None
            
        except Exception as e:
            print(f"Error importing profile: {e}")
            return None

    def share_profile(self, profile_id: str, team_id: str) -> bool:
        """Share a profile with a team.
        
        Args:
            profile_id: ID of profile to share
            team_id: ID of team to share with
            
        Returns:
            True if shared successfully, False otherwise
        """
        profile = self.load_profile(profile_id)
        if not profile:
            return False
        
        try:
            # Copy profile to shared directory
            shared_path = self.shared_dir / team_id
            shared_path.mkdir(exist_ok=True)
            
            shared_profile_path = shared_path / f"{profile_id}.json"
            with open(shared_profile_path, "w", encoding="utf-8") as f:
                json.dump(profile.model_dump(mode='json'), f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error sharing profile: {e}")
            return False

    def get_shared_profiles(self, team_id: str) -> List[CustomizationProfile]:
        """Get profiles shared with a team.
        
        Args:
            team_id: Team ID
            
        Returns:
            List of shared profiles
        """
        profiles = []
        shared_path = self.shared_dir / team_id
        
        if not shared_path.exists():
            return profiles
        
        for profile_file in shared_path.glob("*.json"):
            try:
                with open(profile_file, encoding="utf-8") as f:
                    data = json.load(f)
                
                profile = CustomizationProfile(**data)
                profiles.append(profile)
                
            except Exception as e:
                print(f"Error loading shared profile {profile_file}: {e}")
        
        return profiles