"""Tests for customization manager."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from dev_agent.config.customization_manager import (
    ArchitecturalPreferences,
    CodingStandards,
    CustomizationManager,
    CustomizationProfile,
    QualityThresholds,
    ToolConfig,
    ValidationResult,
)
from dev_agent.models.enums import FrameworkType, LanguageType


class TestCodingStandards:
    """Test coding standards configuration."""

    def test_default_coding_standards(self):
        """Test default coding standards."""
        standards = CodingStandards()
        
        assert standards.line_length == 88
        assert standards.indentation == "spaces"
        assert standards.indent_size == 4
        assert standards.documentation_style == "google"
        assert standards.type_hints_required is True
        
        # Check naming conventions
        assert standards.naming_conventions["class"] == "PascalCase"
        assert standards.naming_conventions["function"] == "snake_case"
        assert standards.naming_conventions["variable"] == "snake_case"

    def test_custom_coding_standards(self):
        """Test custom coding standards."""
        standards = CodingStandards(
            line_length=120,
            indentation="tabs",
            indent_size=2,
            documentation_style="numpy",
            type_hints_required=False,
        )
        
        assert standards.line_length == 120
        assert standards.indentation == "tabs"
        assert standards.indent_size == 2
        assert standards.documentation_style == "numpy"
        assert standards.type_hints_required is False


class TestArchitecturalPreferences:
    """Test architectural preferences configuration."""

    def test_default_architectural_preferences(self):
        """Test default architectural preferences."""
        prefs = ArchitecturalPreferences()
        
        assert prefs.layered_architecture is True
        assert prefs.dependency_injection is True
        assert prefs.error_handling_strategy == "exception_based"
        
        # Check preferred patterns
        assert "MVC" in prefs.preferred_patterns
        assert "Repository" in prefs.preferred_patterns

    def test_custom_architectural_preferences(self):
        """Test custom architectural preferences."""
        prefs = ArchitecturalPreferences(
            preferred_patterns=["Factory", "Observer"],
            layered_architecture=False,
            dependency_injection=False,
            error_handling_strategy="result_based",
        )
        
        assert prefs.preferred_patterns == ["Factory", "Observer"]
        assert prefs.layered_architecture is False
        assert prefs.dependency_injection is False
        assert prefs.error_handling_strategy == "result_based"


class TestQualityThresholds:
    """Test quality thresholds configuration."""

    def test_default_quality_thresholds(self):
        """Test default quality thresholds."""
        thresholds = QualityThresholds()
        
        assert thresholds.code_coverage == 90.0
        assert thresholds.cyclomatic_complexity == 10.0
        assert thresholds.maintainability_index == 80.0
        assert thresholds.security_score == 95.0

    def test_custom_quality_thresholds(self):
        """Test custom quality thresholds."""
        thresholds = QualityThresholds(
            code_coverage=85.0,
            cyclomatic_complexity=15.0,
            maintainability_index=75.0,
            security_score=90.0,
        )
        
        assert thresholds.code_coverage == 85.0
        assert thresholds.cyclomatic_complexity == 15.0
        assert thresholds.maintainability_index == 75.0
        assert thresholds.security_score == 90.0


class TestToolConfig:
    """Test tool configuration."""

    def test_tool_config_creation(self):
        """Test tool configuration creation."""
        config = ToolConfig(
            tool_name="pytest",
            enabled=True,
            version="7.0.0",
            configuration={"verbose": True, "coverage": True},
            integration_points=["testing", "ci_cd"],
            custom_commands={"test": "pytest -v", "coverage": "pytest --cov"},
        )
        
        assert config.tool_name == "pytest"
        assert config.enabled is True
        assert config.version == "7.0.0"
        assert config.configuration["verbose"] is True
        assert "testing" in config.integration_points
        assert config.custom_commands["test"] == "pytest -v"


class TestCustomizationProfile:
    """Test customization profile."""

    def test_profile_creation(self):
        """Test profile creation with defaults."""
        profile = CustomizationProfile(
            id="test_profile",
            name="Test Profile",
            created_by="test_user",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        
        assert profile.id == "test_profile"
        assert profile.name == "Test Profile"
        assert profile.created_by == "test_user"
        assert isinstance(profile.coding_standards, CodingStandards)
        assert isinstance(profile.architectural_preferences, ArchitecturalPreferences)
        assert isinstance(profile.quality_thresholds, QualityThresholds)

    def test_profile_with_custom_settings(self):
        """Test profile with custom settings."""
        custom_standards = CodingStandards(line_length=120)
        custom_thresholds = QualityThresholds(code_coverage=85.0)
        
        profile = CustomizationProfile(
            id="custom_profile",
            name="Custom Profile",
            created_by="test_user",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            coding_standards=custom_standards,
            quality_thresholds=custom_thresholds,
            preferred_languages=[LanguageType.PYTHON, LanguageType.JAVASCRIPT],
            preferred_frameworks=[FrameworkType.FASTAPI, FrameworkType.REACT],
        )
        
        assert profile.coding_standards.line_length == 120
        assert profile.quality_thresholds.code_coverage == 85.0
        assert LanguageType.PYTHON in profile.preferred_languages
        assert FrameworkType.FASTAPI in profile.preferred_frameworks


class TestCustomizationManager:
    """Test customization manager."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def manager(self, temp_config_dir):
        """Create customization manager with temp directory."""
        return CustomizationManager(temp_config_dir)

    def test_manager_initialization(self, manager):
        """Test manager initialization."""
        assert manager.config_dir.exists()
        assert manager.profiles_dir.exists()
        assert manager.templates_dir.exists()
        assert manager.shared_dir.exists()

    def test_create_profile(self, manager):
        """Test profile creation."""
        profile = manager.create_profile(
            profile_id="test_profile",
            name="Test Profile",
            created_by="test_user",
            description="Test description",
        )
        
        assert profile.id == "test_profile"
        assert profile.name == "Test Profile"
        assert profile.created_by == "test_user"
        assert profile.description == "Test description"
        
        # Check that profile was saved
        assert manager.profile_exists("test_profile")

    def test_create_duplicate_profile(self, manager):
        """Test creating duplicate profile raises error."""
        manager.create_profile(
            profile_id="test_profile",
            name="Test Profile",
            created_by="test_user",
        )
        
        with pytest.raises(ValueError, match="already exists"):
            manager.create_profile(
                profile_id="test_profile",
                name="Another Profile",
                created_by="test_user",
            )

    def test_load_profile(self, manager):
        """Test profile loading."""
        # Create profile
        original_profile = manager.create_profile(
            profile_id="test_profile",
            name="Test Profile",
            created_by="test_user",
        )
        
        # Clear cache
        manager._loaded_profiles.clear()
        
        # Load profile
        loaded_profile = manager.load_profile("test_profile")
        
        assert loaded_profile is not None
        assert loaded_profile.id == original_profile.id
        assert loaded_profile.name == original_profile.name

    def test_load_nonexistent_profile(self, manager):
        """Test loading nonexistent profile returns None."""
        profile = manager.load_profile("nonexistent")
        assert profile is None

    def test_save_profile(self, manager):
        """Test profile saving."""
        profile = CustomizationProfile(
            id="test_profile",
            name="Test Profile",
            created_by="test_user",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        
        success = manager.save_profile(profile)
        assert success is True
        
        # Verify file exists
        profile_file = manager.profiles_dir / "test_profile.json"
        assert profile_file.exists()

    def test_delete_profile(self, manager):
        """Test profile deletion."""
        # Create profile
        manager.create_profile(
            profile_id="test_profile",
            name="Test Profile",
            created_by="test_user",
        )
        
        assert manager.profile_exists("test_profile")
        
        # Delete profile
        success = manager.delete_profile("test_profile")
        assert success is True
        assert not manager.profile_exists("test_profile")

    def test_list_profiles(self, manager):
        """Test listing profiles."""
        # Create multiple profiles
        manager.create_profile("profile1", "Profile 1", "user1")
        manager.create_profile("profile2", "Profile 2", "user2", team_id="team1")
        manager.create_profile("profile3", "Profile 3", "user3", team_id="team1")
        
        # List all profiles
        all_profiles = manager.list_profiles()
        assert len(all_profiles) == 3
        
        # List profiles for specific team
        team_profiles = manager.list_profiles(team_id="team1")
        assert len(team_profiles) == 2

    def test_validate_profile(self, manager):
        """Test profile validation."""
        # Valid profile
        valid_profile = CustomizationProfile(
            id="valid_profile",
            name="Valid Profile",
            created_by="test_user",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        
        result = manager.validate_profile(valid_profile)
        assert result.is_valid is True
        assert len(result.errors) == 0
        
        # Invalid profile
        invalid_profile = CustomizationProfile(
            id="",  # Empty ID
            name="",  # Empty name
            created_by="",  # Empty creator
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        
        result = manager.validate_profile(invalid_profile)
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_merge_profiles(self, manager):
        """Test profile merging."""
        base_profile = CustomizationProfile(
            id="base_profile",
            name="Base Profile",
            created_by="test_user",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            coding_standards=CodingStandards(line_length=88),
        )
        
        override_profile = CustomizationProfile(
            id="override_profile",
            name="Override Profile",
            created_by="test_user",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            coding_standards=CodingStandards(line_length=120),
        )
        
        merged_profile = manager.merge_profiles(base_profile, override_profile)
        
        assert merged_profile.coding_standards.line_length == 120
        assert "base_profile_merged_override_profile" in merged_profile.id

    def test_export_import_profile(self, manager, temp_config_dir):
        """Test profile export and import."""
        # Create profile
        original_profile = manager.create_profile(
            profile_id="test_profile",
            name="Test Profile",
            created_by="test_user",
        )
        
        # Export profile
        export_path = temp_config_dir / "exported_profile.json"
        success = manager.export_profile("test_profile", export_path)
        assert success is True
        assert export_path.exists()
        
        # Import profile with new ID
        imported_id = manager.import_profile(export_path, "imported_profile")
        assert imported_id == "imported_profile"
        
        # Verify imported profile
        imported_profile = manager.load_profile("imported_profile")
        assert imported_profile is not None
        assert imported_profile.name == original_profile.name

    def test_share_profile(self, manager):
        """Test profile sharing."""
        # Create profile
        manager.create_profile(
            profile_id="test_profile",
            name="Test Profile",
            created_by="test_user",
        )
        
        # Share profile
        success = manager.share_profile("test_profile", "team1")
        assert success is True
        
        # Verify shared profile exists
        shared_file = manager.shared_dir / "team1" / "test_profile.json"
        assert shared_file.exists()

    def test_get_shared_profiles(self, manager):
        """Test getting shared profiles."""
        # Create and share profile
        manager.create_profile(
            profile_id="test_profile",
            name="Test Profile",
            created_by="test_user",
        )
        manager.share_profile("test_profile", "team1")
        
        # Get shared profiles
        shared_profiles = manager.get_shared_profiles("team1")
        assert len(shared_profiles) == 1
        assert shared_profiles[0].id == "test_profile"

    def test_profile_validation_with_invalid_data(self, manager):
        """Test profile validation with various invalid data."""
        # Profile with invalid quality thresholds
        invalid_profile = CustomizationProfile(
            id="invalid_profile",
            name="Invalid Profile",
            created_by="test_user",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            quality_thresholds=QualityThresholds(code_coverage=150.0),  # Invalid coverage
        )
        
        result = manager.validate_profile(invalid_profile)
        assert result.is_valid is False
        assert any("coverage" in error.lower() for error in result.errors)

    def test_profile_serialization(self, manager):
        """Test profile serialization and deserialization."""
        profile = CustomizationProfile(
            id="test_profile",
            name="Test Profile",
            created_by="test_user",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            preferred_languages=[LanguageType.PYTHON],
            preferred_frameworks=[FrameworkType.FASTAPI],
        )
        
        # Save and reload
        manager.save_profile(profile)
        loaded_profile = manager.load_profile("test_profile")
        
        assert loaded_profile is not None
        assert loaded_profile.preferred_languages == [LanguageType.PYTHON]
        assert loaded_profile.preferred_frameworks == [FrameworkType.FASTAPI]