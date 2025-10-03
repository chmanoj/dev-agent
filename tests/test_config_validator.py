"""Tests for configuration validator."""

from datetime import datetime

import pytest

from dev_agent.config.config_manager import DevAgentConfig, IndexingConfig, LoggingConfig, CLIConfig
from dev_agent.config.config_validator import ConfigValidator, ConfigValidationRule, ConsistencyCheck
from dev_agent.config.customization_manager import (
    ArchitecturalPreferences,
    CodingStandards,
    CustomizationProfile,
    QualityThresholds,
    ToolConfig,
)
from dev_agent.models.enums import FrameworkType, LanguageType


class TestConfigValidator:
    """Test configuration validator."""

    @pytest.fixture
    def validator(self):
        """Create config validator."""
        return ConfigValidator()

    @pytest.fixture
    def valid_config(self):
        """Create valid dev agent config."""
        return DevAgentConfig(
            indexing=IndexingConfig(
                max_file_size_mb=10,
                chunk_size=1000,
                overlap_size=200,
            ),
            logging=LoggingConfig(
                level="INFO",
                max_file_size_mb=10,
            ),
            cli=CLIConfig(),
            azure_openai=None,
        )

    @pytest.fixture
    def valid_profile(self):
        """Create valid customization profile."""
        return CustomizationProfile(
            id="test_profile",
            name="Test Profile",
            created_by="test_user",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            coding_standards=CodingStandards(
                line_length=88,
                indent_size=4,
            ),
            quality_thresholds=QualityThresholds(
                code_coverage=90.0,
                cyclomatic_complexity=10.0,
            ),
        )

    def test_validate_valid_config(self, validator, valid_config):
        """Test validation of valid config."""
        result = validator.validate_config(valid_config)
        
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_invalid_config(self, validator):
        """Test validation of invalid config."""
        invalid_config = DevAgentConfig(
            indexing=IndexingConfig(
                max_file_size_mb=-1,  # Invalid negative value
                chunk_size=0,  # Invalid zero value
                overlap_size=-5,  # Invalid negative value
            ),
            logging=LoggingConfig(
                level="INVALID_LEVEL",  # Invalid log level
                max_file_size_mb=0,  # Invalid zero value
            ),
            cli=CLIConfig(),
            azure_openai=None,
        )
        
        result = validator.validate_config(invalid_config)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("positive" in error.lower() for error in result.errors)
        assert any("invalid log level" in error.lower() for error in result.errors)

    def test_validate_config_with_warnings(self, validator):
        """Test validation with warnings."""
        config_with_warnings = DevAgentConfig(
            indexing=IndexingConfig(
                max_file_size_mb=10,
                chunk_size=1000,
                overlap_size=900,  # Overlap size close to chunk size
            ),
            logging=LoggingConfig(
                level="INFO",
                max_file_size_mb=10,
            ),
            cli=CLIConfig(),
            azure_openai=None,
        )
        
        result = validator.validate_config(config_with_warnings)
        
        assert result.is_valid is True
        assert len(result.warnings) > 0
        assert any("overlap" in warning.lower() for warning in result.warnings)

    def test_validate_valid_profile(self, validator, valid_profile):
        """Test validation of valid profile."""
        result = validator.validate_profile(valid_profile)
        
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_invalid_profile(self, validator):
        """Test validation of invalid profile."""
        invalid_profile = CustomizationProfile(
            id="",  # Empty ID
            name="",  # Empty name
            created_by="",  # Empty creator
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            coding_standards=CodingStandards(
                line_length=30,  # Too short
                indent_size=10,  # Too large
                naming_conventions={"class": "invalid_case"},  # Invalid case type
            ),
            quality_thresholds=QualityThresholds(
                code_coverage=150.0,  # Invalid coverage > 100
                cyclomatic_complexity=-5.0,  # Invalid negative complexity
            ),
            tool_configurations={
                "invalid_tool": ToolConfig(
                    tool_name="",  # Empty tool name
                    version="invalid.version",  # Invalid version format
                )
            },
        )
        
        result = validator.validate_profile(invalid_profile)
        
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_validate_profile_with_warnings(self, validator):
        """Test profile validation with warnings."""
        profile_with_warnings = CustomizationProfile(
            id="test_profile",
            name="Test Profile",
            created_by="test_user",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            coding_standards=CodingStandards(
                line_length=40,  # Short but not invalid
                indent_size=8,  # Large but not invalid
            ),
        )
        
        result = validator.validate_profile(profile_with_warnings)
        
        assert result.is_valid is True
        assert len(result.warnings) > 0

    def test_check_profile_consistency(self, validator):
        """Test profile consistency checking."""
        profile1 = CustomizationProfile(
            id="profile1",
            name="Profile 1",
            created_by="user1",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            coding_standards=CodingStandards(line_length=88),
            quality_thresholds=QualityThresholds(code_coverage=90.0),
        )
        
        profile2 = CustomizationProfile(
            id="profile2",
            name="Profile 2",
            created_by="user2",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            coding_standards=CodingStandards(line_length=120),  # Different line length
            quality_thresholds=QualityThresholds(code_coverage=70.0),  # Different coverage
        )
        
        issues = validator.check_profile_consistency(profile1, profile2)
        
        assert len(issues) > 0
        assert any("line length" in issue.lower() for issue in issues)
        assert any("coverage" in issue.lower() for issue in issues)

    def test_suggest_improvements(self, validator):
        """Test improvement suggestions."""
        minimal_profile = CustomizationProfile(
            id="minimal_profile",
            name="Minimal Profile",
            created_by="test_user",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            # Minimal configuration with low quality thresholds
            quality_thresholds=QualityThresholds(
                code_coverage=60.0,  # Low coverage
                cyclomatic_complexity=20.0,  # High complexity
            ),
            coding_standards=CodingStandards(
                line_length=150,  # Long lines
                type_hints_required=False,  # No type hints
            ),
        )
        
        suggestions = validator.suggest_improvements(minimal_profile)
        
        assert len(suggestions) > 0
        assert any("language" in suggestion.lower() for suggestion in suggestions)
        assert any("coverage" in suggestion.lower() for suggestion in suggestions)

    def test_language_framework_consistency(self, validator):
        """Test language and framework consistency checking."""
        # Profile with inconsistent language/framework combination
        inconsistent_profile = CustomizationProfile(
            id="inconsistent_profile",
            name="Inconsistent Profile",
            created_by="test_user",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            preferred_languages=[LanguageType.PYTHON],  # Only Python
            preferred_frameworks=[FrameworkType.REACT],  # But React framework (JS/TS)
        )
        
        result = validator.validate_profile(inconsistent_profile)
        
        # Should have warnings about framework/language mismatch
        assert len(result.warnings) > 0

    def test_testing_coverage_consistency(self, validator):
        """Test testing strategy and coverage consistency."""
        # Profile with test-driven development but low coverage
        inconsistent_profile = CustomizationProfile(
            id="test_profile",
            name="Test Profile",
            created_by="test_user",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            architectural_preferences=ArchitecturalPreferences(
                testing_strategy={"test_driven": True, "unit_test_coverage": 95.0}
            ),
            quality_thresholds=QualityThresholds(code_coverage=60.0),  # Low coverage
        )
        
        result = validator.validate_profile(inconsistent_profile)
        
        # Should have warnings about inconsistent testing configuration
        assert len(result.warnings) > 0

    def test_add_custom_validation_rule(self, validator):
        """Test adding custom validation rule."""
        def custom_validator(profile):
            if profile.name.startswith("Test"):
                return ["Profile name should not start with 'Test'"]
            return []
        
        custom_rule = ConfigValidationRule(
            name="no_test_prefix",
            description="Profile names should not start with 'Test'",
            severity="warning",
            validator_func=custom_validator,
        )
        
        validator.add_validation_rule(custom_rule)
        
        test_profile = CustomizationProfile(
            id="test_profile",
            name="Test Profile",  # Starts with "Test"
            created_by="test_user",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        
        result = validator.validate_profile(test_profile)
        
        # Should have warning from custom rule
        assert any("Test" in warning for warning in result.warnings)

    def test_add_custom_consistency_check(self, validator):
        """Test adding custom consistency check."""
        def custom_check(profile):
            if (profile.coding_standards.line_length > 100 and 
                profile.quality_thresholds.maintainability_index > 90):
                return ["Long lines with high maintainability requirements may conflict"]
            return []
        
        custom_check_obj = ConsistencyCheck(
            name="line_length_maintainability",
            description="Check line length vs maintainability requirements",
            check_func=custom_check,
        )
        
        validator.add_consistency_check(custom_check_obj)
        
        conflicting_profile = CustomizationProfile(
            id="conflicting_profile",
            name="Conflicting Profile",
            created_by="test_user",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            coding_standards=CodingStandards(line_length=120),  # Long lines
            quality_thresholds=QualityThresholds(maintainability_index=95.0),  # High maintainability
        )
        
        result = validator.validate_profile(conflicting_profile)
        
        # Should have warning from custom consistency check
        assert len(result.warnings) > 0

    def test_remove_validation_rule(self, validator):
        """Test removing validation rule."""
        initial_rule_count = len(validator.get_validation_rules())
        
        # Remove a default rule
        success = validator.remove_validation_rule("valid_line_length")
        assert success is True
        
        # Check rule count decreased
        assert len(validator.get_validation_rules()) == initial_rule_count - 1
        
        # Try to remove non-existent rule
        success = validator.remove_validation_rule("non_existent_rule")
        assert success is False

    def test_get_validation_rules(self, validator):
        """Test getting validation rules."""
        rules = validator.get_validation_rules()
        
        assert len(rules) > 0
        assert all(isinstance(rule, ConfigValidationRule) for rule in rules)
        
        # Check that default rules are present
        rule_names = [rule.name for rule in rules]
        assert "valid_line_length" in rule_names
        assert "valid_coverage_threshold" in rule_names

    def test_get_consistency_checks(self, validator):
        """Test getting consistency checks."""
        checks = validator.get_consistency_checks()
        
        assert len(checks) > 0
        assert all(isinstance(check, ConsistencyCheck) for check in checks)
        
        # Check that default checks are present
        check_names = [check.name for check in checks]
        assert "language_framework_consistency" in check_names