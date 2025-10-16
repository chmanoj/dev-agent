"""Language pattern models for code generation and analysis."""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from dev_agent.models.enums import FrameworkType, LanguageType


class LanguagePatterns(BaseModel):
    """Defines naming conventions and patterns for a programming language.
    
    This class encapsulates the various naming and structural conventions
    used by different programming languages to ensure generated code
    follows the appropriate patterns.
    """
    
    # File and extension patterns
    file_extension: str = Field(..., description="Primary file extension for the language")
    test_file_suffix: str = Field(..., description="Suffix for test files")
    config_files: List[str] = Field(default_factory=list, description="Common configuration file names")
    
    # Naming conventions
    class_naming: str = Field(..., description="Class naming convention (PascalCase, snake_case)")
    method_naming: str = Field(..., description="Method naming convention (camelCase, snake_case)")
    variable_naming: str = Field(..., description="Variable naming convention (camelCase, snake_case)")
    constant_naming: str = Field(..., description="Constant naming convention (UPPER_CASE, camelCase)")
    file_naming: str = Field(..., description="File naming convention (kebab-case, snake_case, PascalCase)")
    
    # Service and component patterns
    service_suffix: str = Field(default="", description="Suffix for service classes")
    interface_prefix: str = Field(default="", description="Prefix for interface classes")
    abstract_prefix: str = Field(default="", description="Prefix for abstract classes")
    
    # Directory structure patterns
    source_directory: str = Field(default="", description="Primary source code directory")
    test_directory: str = Field(default="tests", description="Test directory name")
    config_directory: str = Field(default="config", description="Configuration directory name")
    
    # Import and module patterns
    import_style: str = Field(default="explicit", description="Import style (explicit, wildcard, namespace)")
    module_separator: str = Field(default=".", description="Module path separator")
    
    def validate_class_name(self, name: str) -> bool:
        """Validate if a class name follows the language conventions.
        
        Args:
            name: The class name to validate
            
        Returns:
            True if the name follows conventions, False otherwise
        """
        if self.class_naming == "PascalCase":
            return name[0].isupper() and "_" not in name
        elif self.class_naming == "snake_case":
            return name.islower() and " " not in name
        return True
    
    def validate_method_name(self, name: str) -> bool:
        """Validate if a method name follows the language conventions.
        
        Args:
            name: The method name to validate
            
        Returns:
            True if the name follows conventions, False otherwise
        """
        if self.method_naming == "camelCase":
            return name[0].islower() and "_" not in name
        elif self.method_naming == "snake_case":
            return name.islower() and " " not in name
        return True
    
    def validate_file_name(self, name: str) -> bool:
        """Validate if a file name follows the language conventions.
        
        Args:
            name: The file name to validate (without extension)
            
        Returns:
            True if the name follows conventions, False otherwise
        """
        if self.file_naming == "kebab-case":
            return name.islower() and "_" not in name and " " not in name
        elif self.file_naming == "snake_case":
            return name.islower() and "-" not in name and " " not in name
        elif self.file_naming == "PascalCase":
            return name[0].isupper() and "_" not in name and "-" not in name
        return True
    
    def transform_to_class_name(self, name: str) -> str:
        """Transform a name to follow class naming conventions.
        
        Args:
            name: The name to transform
            
        Returns:
            The transformed name following class conventions
        """
        if self.class_naming == "PascalCase":
            # Convert snake_case or kebab-case to PascalCase
            parts = name.replace("-", "_").split("_")
            return "".join(word.capitalize() for word in parts)
        elif self.class_naming == "snake_case":
            # Convert PascalCase or kebab-case to snake_case
            import re
            # Handle PascalCase to snake_case
            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
            s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
            # Handle kebab-case to snake_case
            return s2.replace("-", "_")
        return name
    
    def transform_to_method_name(self, name: str) -> str:
        """Transform a name to follow method naming conventions.
        
        Args:
            name: The name to transform
            
        Returns:
            The transformed name following method conventions
        """
        if self.method_naming == "camelCase":
            # Convert snake_case or kebab-case to camelCase
            parts = name.replace("-", "_").split("_")
            if not parts:
                return name
            return parts[0].lower() + "".join(word.capitalize() for word in parts[1:])
        elif self.method_naming == "snake_case":
            # Convert PascalCase or kebab-case to snake_case
            import re
            # Handle PascalCase to snake_case
            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
            s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
            # Handle kebab-case to snake_case
            return s2.replace("-", "_")
        return name
    
    def transform_to_file_name(self, name: str) -> str:
        """Transform a name to follow file naming conventions.
        
        Args:
            name: The name to transform
            
        Returns:
            The transformed name following file conventions
        """
        if self.file_naming == "kebab-case":
            # Convert snake_case or PascalCase to kebab-case
            import re
            # Handle PascalCase to kebab-case
            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', name)
            s2 = re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()
            # Handle snake_case to kebab-case
            return s2.replace("_", "-")
        elif self.file_naming == "snake_case":
            # Convert PascalCase or kebab-case to snake_case
            import re
            # Handle PascalCase to snake_case
            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
            s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
            # Handle kebab-case to snake_case
            return s2.replace("-", "_")
        elif self.file_naming == "PascalCase":
            # Convert snake_case or kebab-case to PascalCase
            parts = name.replace("-", "_").split("_")
            return "".join(word.capitalize() for word in parts)
        return name


class FrameworkPatterns(BaseModel):
    """Framework-specific patterns and conventions.
    
    This model defines patterns specific to frameworks like FastAPI, React, etc.
    that extend beyond basic language patterns.
    """
    
    model_config = ConfigDict(use_enum_values=True)
    
    framework: FrameworkType = Field(..., description="The framework type")
    
    # Directory structure
    preferred_structure: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Preferred directory structure for the framework"
    )
    
    # File patterns
    entry_point_files: List[str] = Field(
        default_factory=list,
        description="Common entry point file names"
    )
    
    config_file_patterns: List[str] = Field(
        default_factory=list,
        description="Framework-specific configuration files"
    )
    
    # Naming patterns
    component_suffix: Optional[str] = Field(
        default=None,
        description="Suffix for framework components (e.g., 'Component' for React)"
    )
    
    service_patterns: List[str] = Field(
        default_factory=list,
        description="Patterns for service/business logic files"
    )
    
    # Dependencies and imports
    common_dependencies: List[str] = Field(
        default_factory=list,
        description="Common dependencies for this framework"
    )
    
    import_patterns: Dict[str, str] = Field(
        default_factory=dict,
        description="Common import patterns for the framework"
    )
    
    # Testing patterns
    test_file_patterns: List[str] = Field(
        default_factory=list,
        description="Test file naming patterns"
    )
    
    test_directory_structure: Optional[str] = Field(
        default=None,
        description="Preferred test directory structure"
    )
    
    def validate_component_name(self, name: str) -> bool:
        """Validate if a component name follows framework conventions.
        
        Args:
            name: The component name to validate
            
        Returns:
            True if the name follows conventions, False otherwise
        """
        if self.component_suffix:
            return name.endswith(self.component_suffix)
        return True
    
    def transform_to_component_name(self, name: str) -> str:
        """Transform a name to follow component naming conventions.
        
        Args:
            name: The name to transform
            
        Returns:
            The transformed name following component conventions
        """
        if self.component_suffix and not name.endswith(self.component_suffix):
            return f"{name}{self.component_suffix}"
        return name
    
    def get_recommended_dependencies(self) -> List[str]:
        """Get recommended dependencies for this framework.
        
        Returns:
            List of recommended dependency names
        """
        return self.common_dependencies.copy()
    
    def get_import_statement(self, import_key: str) -> Optional[str]:
        """Get import statement for a specific import key.
        
        Args:
            import_key: The key for the import pattern
            
        Returns:
            Import statement if found, None otherwise
        """
        return self.import_patterns.get(import_key)
    
    def matches_file_pattern(self, filename: str) -> bool:
        """Check if a filename matches framework file patterns.
        
        Args:
            filename: The filename to check
            
        Returns:
            True if filename matches any framework pattern
        """
        import fnmatch
        
        # Check entry point files
        if filename in self.entry_point_files:
            return True
        
        # Check config file patterns
        if filename in self.config_file_patterns:
            return True
        
        # Check service patterns
        for pattern in self.service_patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True
        
        # Check test file patterns
        for pattern in self.test_file_patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True
        
        return False


class LanguageProjectContext(BaseModel):
    """Context about a project's language and framework patterns.
    
    This model combines language and framework information to provide
    complete context for code generation and analysis.
    """
    
    model_config = ConfigDict(use_enum_values=True)
    
    primary_language: LanguageType = Field(..., description="Primary programming language")
    detected_frameworks: List[FrameworkType] = Field(
        default_factory=list,
        description="Detected frameworks in the project"
    )
    
    language_patterns: Optional[LanguagePatterns] = Field(
        default=None,
        description="Language-specific patterns"
    )
    
    framework_patterns: List[FrameworkPatterns] = Field(
        default_factory=list,
        description="Framework-specific patterns"
    )
    
    # Project structure analysis
    source_directories: List[str] = Field(
        default_factory=list,
        description="Detected source code directories"
    )
    
    test_directories: List[str] = Field(
        default_factory=list,
        description="Detected test directories"
    )
    
    config_files: List[str] = Field(
        default_factory=list,
        description="Detected configuration files"
    )
    
    # Package manager and build tools
    package_manager: Optional[str] = Field(
        default=None,
        description="Detected package manager (pip, npm, yarn, etc.)"
    )
    
    build_tools: List[str] = Field(
        default_factory=list,
        description="Detected build tools"
    )
    
    def get_effective_patterns(self) -> LanguagePatterns:
        """Get the effective language patterns, considering framework overrides.
        
        Returns:
            The language patterns with any framework-specific overrides applied
        """
        if not self.language_patterns:
            raise ValueError("No language patterns available")
        
        # Start with base language patterns
        effective_patterns = self.language_patterns
        
        # Apply framework-specific overrides if any
        # This could be extended to merge framework patterns with language patterns
        
        return effective_patterns
    
    def supports_framework(self, framework: FrameworkType) -> bool:
        """Check if the project supports a specific framework.
        
        Args:
            framework: The framework to check for
            
        Returns:
            True if the framework is detected in the project
        """
        return framework in self.detected_frameworks
    
    def get_framework_patterns(self, framework: FrameworkType) -> Optional[FrameworkPatterns]:
        """Get patterns for a specific framework.
        
        Args:
            framework: The framework to get patterns for
            
        Returns:
            Framework patterns if found, None otherwise
        """
        for patterns in self.framework_patterns:
            if patterns.framework == framework:
                return patterns
        return None