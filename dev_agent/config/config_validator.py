"""Configuration validation and consistency checking."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from pydantic import ValidationError

from ..models.enums import FrameworkType, LanguageType, ProjectType
from .config_manager import DevAgentConfig
from .customization_manager import CustomizationProfile, ValidationResult
from .template_manager import CustomTemplate


@dataclass
class ConfigValidationRule:
    """Defines a configuration validation rule."""

    name: str
    description: str
    severity: str  # "error", "warning", "info"
    validator_func: callable
    applies_to: List[str] = field(default_factory=list)  # Config sections this applies to


@dataclass
class ConsistencyCheck:
    """Defines a consistency check between configuration elements."""

    name: str
    description: str
    check_func: callable
    dependencies: List[str] = field(default_factory=list)  # Required config sections


class ConfigValidator:
    """Validates configuration consistency and correctness."""

    def __init__(self):
        """Initialize configuration validator."""
        self._validation_rules: List[ConfigValidationRule] = []
        self._consistency_checks: List[ConsistencyCheck] = []
        self._setup_default_rules()

    def _setup_default_rules(self) -> None:
        """Setup default validation rules."""
        # Basic configuration validation rules
        self._validation_rules.extend([
            ConfigValidationRule(
                name="valid_line_length",
                description="Line length should be between 50 and 200 characters",
                severity="warning",
                validator_func=self._validate_line_length,
                applies_to=["coding_standards"]
            ),
            ConfigValidationRule(
                name="valid_indent_size",
                description="Indent size should be between 2 and 8",
                severity="warning",
                validator_func=self._validate_indent_size,
                applies_to=["coding_standards"]
            ),
            ConfigValidationRule(
                name="valid_coverage_threshold",
                description="Coverage threshold should be between 0 and 100",
                severity="error",
                validator_func=self._validate_coverage_threshold,
                applies_to=["quality_thresholds"]
            ),
            ConfigValidationRule(
                name="valid_complexity_threshold",
                description="Complexity threshold should be positive",
                severity="error",
                validator_func=self._validate_complexity_threshold,
                applies_to=["quality_thresholds"]
            ),
            ConfigValidationRule(
                name="valid_naming_conventions",
                description="Naming conventions should use valid case types",
                severity="error",
                validator_func=self._validate_naming_conventions,
                applies_to=["coding_standards"]
            ),
            ConfigValidationRule(
                name="valid_tool_configurations",
                description="Tool configurations should have required fields",
                severity="error",
                validator_func=self._validate_tool_configurations,
                applies_to=["tool_configurations"]
            ),
        ])

        # Consistency checks
        self._consistency_checks.extend([
            ConsistencyCheck(
                name="language_framework_consistency",
                description="Frameworks should be compatible with selected languages",
                check_func=self._check_language_framework_consistency,
                dependencies=["preferred_languages", "preferred_frameworks"]
            ),
            ConsistencyCheck(
                name="testing_coverage_consistency",
                description="Testing strategy should align with coverage requirements",
                check_func=self._check_testing_coverage_consistency,
                dependencies=["architectural_preferences", "quality_thresholds"]
            ),
            ConsistencyCheck(
                name="tool_integration_consistency",
                description="Tool configurations should be consistent with preferences",
                check_func=self._check_tool_integration_consistency,
                dependencies=["tool_configurations", "architectural_preferences"]
            ),
        ])

    def validate_config(self, config: DevAgentConfig) -> ValidationResult:
        """Validate a base configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            Validation result
        """
        result = ValidationResult(is_valid=True)
        
        # Basic config validation
        if not hasattr(config, 'indexing') or config.indexing is None:
            result.errors.append("Indexing configuration is required")
            result.is_valid = False
        
        if not hasattr(config, 'logging') or config.logging is None:
            result.errors.append("Logging configuration is required")
            result.is_valid = False
        
        if not hasattr(config, 'cli') or config.cli is None:
            result.errors.append("CLI configuration is required")
            result.is_valid = False
        
        # Validate indexing config
        if hasattr(config, 'indexing') and config.indexing:
            if config.indexing.max_file_size_mb <= 0:
                result.errors.append("Max file size must be positive")
                result.is_valid = False
            
            if config.indexing.chunk_size <= 0:
                result.errors.append("Chunk size must be positive")
                result.is_valid = False
            
            if config.indexing.overlap_size < 0:
                result.errors.append("Overlap size cannot be negative")
                result.is_valid = False
            
            if config.indexing.overlap_size >= config.indexing.chunk_size:
                result.warnings.append("Overlap size should be smaller than chunk size")
            elif config.indexing.overlap_size > config.indexing.chunk_size * 0.8:
                result.warnings.append("Overlap size is very close to chunk size, consider reducing it")
        
        # Validate logging config
        if hasattr(config, 'logging') and config.logging:
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if config.logging.level not in valid_levels:
                result.errors.append(f"Invalid log level: {config.logging.level}")
                result.is_valid = False
            
            if config.logging.max_file_size_mb <= 0:
                result.errors.append("Max log file size must be positive")
                result.is_valid = False
        
        return result

    def validate_profile(self, profile: CustomizationProfile) -> ValidationResult:
        """Validate a customization profile.
        
        Args:
            profile: Profile to validate
            
        Returns:
            Validation result
        """
        result = ValidationResult(is_valid=True)
        
        # Apply validation rules
        for rule in self._validation_rules:
            try:
                rule_result = rule.validator_func(profile)
                if rule_result:
                    if rule.severity == "error":
                        result.errors.extend(rule_result)
                        result.is_valid = False
                    elif rule.severity == "warning":
                        result.warnings.extend(rule_result)
                    else:  # info
                        result.suggestions.extend(rule_result)
            except Exception as e:
                result.warnings.append(f"Error running validation rule {rule.name}: {e}")
        
        # Apply consistency checks
        for check in self._consistency_checks:
            try:
                check_result = check.check_func(profile)
                if check_result:
                    result.warnings.extend(check_result)
            except Exception as e:
                result.warnings.append(f"Error running consistency check {check.name}: {e}")
        
        return result

    def validate_template(self, template: CustomTemplate) -> ValidationResult:
        """Validate a custom template.
        
        Args:
            template: Template to validate
            
        Returns:
            Validation result
        """
        result = ValidationResult(is_valid=True)
        
        # Validate metadata
        if not template.metadata.template_id:
            result.errors.append("Template ID is required")
            result.is_valid = False
        
        if not template.metadata.name:
            result.errors.append("Template name is required")
            result.is_valid = False
        
        if not template.metadata.created_by:
            result.errors.append("Template creator is required")
            result.is_valid = False
        
        # Validate template ID format
        if template.metadata.template_id and not re.match(r'^[a-zA-Z0-9_-]+$', template.metadata.template_id):
            result.errors.append("Template ID can only contain letters, numbers, underscores, and hyphens")
            result.is_valid = False
        
        # Validate version format (semver)
        if template.metadata.current_version and not re.match(r'^\d+\.\d+\.\d+', template.metadata.current_version):
            result.warnings.append("Template version should follow semantic versioning (x.y.z)")
        
        # Validate supported languages and frameworks consistency
        if template.metadata.supported_languages and template.metadata.supported_frameworks:
            inconsistent_frameworks = self._check_framework_language_compatibility(
                template.metadata.supported_languages,
                template.metadata.supported_frameworks
            )
            if inconsistent_frameworks:
                result.warnings.append(
                    f"Some frameworks may not be compatible with supported languages: {inconsistent_frameworks}"
                )
        
        # Validate customization points
        for point in template.customization_points:
            if not point.name:
                result.errors.append("Customization point name is required")
                result.is_valid = False
            
            if point.type == "choice" and not point.choices:
                result.errors.append(f"Customization point '{point.name}' of type 'choice' must have choices")
                result.is_valid = False
        
        return result

    def check_profile_consistency(
        self,
        profile1: CustomizationProfile,
        profile2: CustomizationProfile,
    ) -> List[str]:
        """Check consistency between two profiles.
        
        Args:
            profile1: First profile
            profile2: Second profile
            
        Returns:
            List of consistency issues
        """
        issues = []
        
        # Check coding standards consistency
        if profile1.coding_standards.line_length != profile2.coding_standards.line_length:
            issues.append(f"Line length differs: {profile1.coding_standards.line_length} vs {profile2.coding_standards.line_length}")
        
        if profile1.coding_standards.indentation != profile2.coding_standards.indentation:
            issues.append(f"Indentation type differs: {profile1.coding_standards.indentation} vs {profile2.coding_standards.indentation}")
        
        # Check quality thresholds consistency
        if abs(profile1.quality_thresholds.code_coverage - profile2.quality_thresholds.code_coverage) > 10:
            issues.append(f"Code coverage thresholds differ significantly: {profile1.quality_thresholds.code_coverage}% vs {profile2.quality_thresholds.code_coverage}%")
        
        # Check architectural preferences
        if profile1.architectural_preferences.dependency_injection != profile2.architectural_preferences.dependency_injection:
            issues.append("Dependency injection preferences differ")
        
        return issues

    def suggest_improvements(self, profile: CustomizationProfile) -> List[str]:
        """Suggest improvements for a customization profile.
        
        Args:
            profile: Profile to analyze
            
        Returns:
            List of improvement suggestions
        """
        suggestions = []
        
        # Check if profile has basic configurations
        if not profile.preferred_languages:
            suggestions.append("Consider specifying preferred programming languages")
        
        if not profile.preferred_frameworks:
            suggestions.append("Consider specifying preferred frameworks")
        
        if not profile.tool_configurations:
            suggestions.append("Consider configuring external tools for better integration")
        
        # Check quality thresholds
        if profile.quality_thresholds.code_coverage < 80:
            suggestions.append("Consider increasing code coverage threshold to at least 80%")
        
        if profile.quality_thresholds.cyclomatic_complexity > 15:
            suggestions.append("Consider lowering cyclomatic complexity threshold for better maintainability")
        
        # Check coding standards
        if profile.coding_standards.line_length > 120:
            suggestions.append("Consider using a shorter line length for better readability")
        
        if not profile.coding_standards.type_hints_required:
            suggestions.append("Consider requiring type hints for better code documentation")
        
        # Check architectural preferences
        if not profile.architectural_preferences.dependency_injection:
            suggestions.append("Consider enabling dependency injection for better testability")
        
        if not profile.architectural_preferences.testing_strategy.get("unit_test_coverage", 0):
            suggestions.append("Consider defining unit test coverage requirements")
        
        return suggestions

    # Validation rule implementations
    def _validate_line_length(self, profile: CustomizationProfile) -> List[str]:
        """Validate line length setting."""
        issues = []
        line_length = profile.coding_standards.line_length
        
        if line_length < 50:
            issues.append(f"Line length {line_length} is too short (minimum recommended: 50)")
        elif line_length > 200:
            issues.append(f"Line length {line_length} is too long (maximum recommended: 200)")
        
        return issues

    def _validate_indent_size(self, profile: CustomizationProfile) -> List[str]:
        """Validate indent size setting."""
        issues = []
        indent_size = profile.coding_standards.indent_size
        
        if indent_size < 2:
            issues.append(f"Indent size {indent_size} is too small (minimum recommended: 2)")
        elif indent_size > 8:
            issues.append(f"Indent size {indent_size} is too large (maximum recommended: 8)")
        
        return issues

    def _validate_coverage_threshold(self, profile: CustomizationProfile) -> List[str]:
        """Validate coverage threshold setting."""
        issues = []
        coverage = profile.quality_thresholds.code_coverage
        
        if coverage < 0 or coverage > 100:
            issues.append(f"Coverage threshold {coverage}% must be between 0 and 100")
        
        return issues

    def _validate_complexity_threshold(self, profile: CustomizationProfile) -> List[str]:
        """Validate complexity threshold setting."""
        issues = []
        complexity = profile.quality_thresholds.cyclomatic_complexity
        
        if complexity <= 0:
            issues.append(f"Complexity threshold {complexity} must be positive")
        
        return issues

    def _validate_naming_conventions(self, profile: CustomizationProfile) -> List[str]:
        """Validate naming conventions."""
        issues = []
        valid_cases = ["PascalCase", "camelCase", "snake_case", "UPPER_CASE", "kebab-case"]
        
        for element, case_type in profile.coding_standards.naming_conventions.items():
            if case_type not in valid_cases:
                issues.append(f"Invalid case type '{case_type}' for {element}. Valid types: {valid_cases}")
        
        return issues

    def _validate_tool_configurations(self, profile: CustomizationProfile) -> List[str]:
        """Validate tool configurations."""
        issues = []
        
        for tool_name, tool_config in profile.tool_configurations.items():
            if not tool_config.tool_name:
                issues.append(f"Tool configuration '{tool_name}' missing tool name")
            
            if tool_config.version and not re.match(r'^\d+\.\d+', tool_config.version):
                issues.append(f"Tool '{tool_name}' has invalid version format: {tool_config.version}")
        
        return issues

    # Consistency check implementations
    def _check_language_framework_consistency(self, profile: CustomizationProfile) -> List[str]:
        """Check language and framework consistency."""
        issues = []
        
        if not profile.preferred_languages or not profile.preferred_frameworks:
            return issues
        
        # Define framework-language mappings
        framework_languages = {
            FrameworkType.DJANGO: [LanguageType.PYTHON],
            FrameworkType.FLASK: [LanguageType.PYTHON],
            FrameworkType.FASTAPI: [LanguageType.PYTHON],
            FrameworkType.REACT: [LanguageType.JAVASCRIPT, LanguageType.TYPESCRIPT],
            FrameworkType.VUE: [LanguageType.JAVASCRIPT, LanguageType.TYPESCRIPT],
            FrameworkType.ANGULAR: [LanguageType.TYPESCRIPT],
            FrameworkType.EXPRESS: [LanguageType.JAVASCRIPT, LanguageType.TYPESCRIPT],
            FrameworkType.SPRING_BOOT: [LanguageType.JAVA],
            FrameworkType.SPRING: [LanguageType.JAVA],
        }
        
        for framework in profile.preferred_frameworks:
            if framework in framework_languages:
                required_languages = framework_languages[framework]
                if not any(lang in profile.preferred_languages for lang in required_languages):
                    issues.append(f"Framework {framework.value} requires one of {[lang.value for lang in required_languages]} but none are in preferred languages")
        
        return issues

    def _check_testing_coverage_consistency(self, profile: CustomizationProfile) -> List[str]:
        """Check testing strategy and coverage consistency."""
        issues = []
        
        testing_strategy = profile.architectural_preferences.testing_strategy
        coverage_threshold = profile.quality_thresholds.code_coverage
        
        if testing_strategy.get("test_driven", False) and coverage_threshold < 80:
            issues.append("Test-driven development typically requires higher coverage threshold (80%+)")
        
        strategy_coverage = testing_strategy.get("unit_test_coverage", 0)
        if strategy_coverage > 0 and abs(strategy_coverage - coverage_threshold) > 10:
            issues.append(f"Unit test coverage in strategy ({strategy_coverage}%) differs from quality threshold ({coverage_threshold}%)")
        
        return issues

    def _check_tool_integration_consistency(self, profile: CustomizationProfile) -> List[str]:
        """Check tool configuration consistency."""
        issues = []
        
        # Check if testing tools are configured when testing is emphasized
        if profile.architectural_preferences.testing_strategy.get("test_driven", False):
            testing_tools = ["pytest", "jest", "junit"]
            configured_tools = list(profile.tool_configurations.keys())
            
            if not any(tool in configured_tools for tool in testing_tools):
                issues.append("Test-driven development enabled but no testing tools configured")
        
        # Check if linting tools are configured for quality requirements
        if profile.quality_thresholds.code_coverage > 90:
            linting_tools = ["ruff", "eslint", "checkstyle"]
            configured_tools = list(profile.tool_configurations.keys())
            
            if not any(tool in configured_tools for tool in linting_tools):
                issues.append("High quality thresholds set but no linting tools configured")
        
        return issues

    def _check_framework_language_compatibility(
        self,
        languages: List[LanguageType],
        frameworks: List[FrameworkType],
    ) -> List[str]:
        """Check framework and language compatibility."""
        incompatible = []
        
        # Define framework-language mappings
        framework_languages = {
            FrameworkType.DJANGO: [LanguageType.PYTHON],
            FrameworkType.FLASK: [LanguageType.PYTHON],
            FrameworkType.FASTAPI: [LanguageType.PYTHON],
            FrameworkType.REACT: [LanguageType.JAVASCRIPT, LanguageType.TYPESCRIPT],
            FrameworkType.VUE: [LanguageType.JAVASCRIPT, LanguageType.TYPESCRIPT],
            FrameworkType.ANGULAR: [LanguageType.TYPESCRIPT],
            FrameworkType.EXPRESS: [LanguageType.JAVASCRIPT, LanguageType.TYPESCRIPT],
            FrameworkType.SPRING_BOOT: [LanguageType.JAVA],
            FrameworkType.SPRING: [LanguageType.JAVA],
        }
        
        for framework in frameworks:
            if framework in framework_languages:
                required_languages = framework_languages[framework]
                if not any(lang in languages for lang in required_languages):
                    incompatible.append(framework.value)
        
        return incompatible

    def add_validation_rule(self, rule: ConfigValidationRule) -> None:
        """Add a custom validation rule.
        
        Args:
            rule: Validation rule to add
        """
        self._validation_rules.append(rule)

    def add_consistency_check(self, check: ConsistencyCheck) -> None:
        """Add a custom consistency check.
        
        Args:
            check: Consistency check to add
        """
        self._consistency_checks.append(check)

    def remove_validation_rule(self, rule_name: str) -> bool:
        """Remove a validation rule by name.
        
        Args:
            rule_name: Name of rule to remove
            
        Returns:
            True if rule was removed, False if not found
        """
        for i, rule in enumerate(self._validation_rules):
            if rule.name == rule_name:
                del self._validation_rules[i]
                return True
        return False

    def get_validation_rules(self) -> List[ConfigValidationRule]:
        """Get all validation rules.
        
        Returns:
            List of validation rules
        """
        return self._validation_rules.copy()

    def get_consistency_checks(self) -> List[ConsistencyCheck]:
        """Get all consistency checks.
        
        Returns:
            List of consistency checks
        """
        return self._consistency_checks.copy()