"""Template and scaffolding data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .enums import (
    CICDPlatform,
    FrameworkType,
    LanguageType,
    ProjectType,
    TeamSize,
    TemplateType,
)


class ProjectSpec(BaseModel):
    """Specification for a new project to be scaffolded."""

    name: str = Field(..., description="Project name")
    description: str = Field(..., description="Project description")
    project_type: ProjectType = Field(..., description="Type of project")
    primary_language: LanguageType = Field(..., description="Primary programming language")
    frameworks: List[FrameworkType] = Field(default_factory=list, description="Frameworks to include")
    team_size: TeamSize = Field(default=TeamSize.SOLO, description="Team size")
    include_ci_cd: bool = Field(default=True, description="Include CI/CD configuration")
    ci_cd_platform: Optional[CICDPlatform] = Field(default=None, description="CI/CD platform")
    include_docker: bool = Field(default=False, description="Include Docker configuration")
    include_testing: bool = Field(default=True, description="Include testing framework")
    include_linting: bool = Field(default=True, description="Include linting configuration")
    include_docs: bool = Field(default=True, description="Include documentation templates")
    python_version: str = Field(default="3.11", description="Python version for Python projects")
    license_type: Optional[str] = Field(default="MIT", description="License type")
    author_name: Optional[str] = Field(default=None, description="Author name")
    author_email: Optional[str] = Field(default=None, description="Author email")
    repository_url: Optional[str] = Field(default=None, description="Repository URL")
    custom_requirements: Dict[str, Any] = Field(default_factory=dict, description="Custom requirements")


class FileTemplate(BaseModel):
    """Template for generating a single file."""

    path: str = Field(..., description="Relative path where file should be created")
    content: str = Field(..., description="Template content with placeholders")
    is_executable: bool = Field(default=False, description="Whether file should be executable")
    encoding: str = Field(default="utf-8", description="File encoding")
    template_variables: Dict[str, Any] = Field(default_factory=dict, description="Template variables")


class DirectoryTemplate(BaseModel):
    """Template for creating a directory structure."""

    path: str = Field(..., description="Relative path for directory")
    files: List[FileTemplate] = Field(default_factory=list, description="Files in this directory")
    subdirectories: List[DirectoryTemplate] = Field(default_factory=list, description="Subdirectories")


class ProjectTemplate(BaseModel):
    """Complete project template definition."""

    id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Human-readable template name")
    description: str = Field(..., description="Template description")
    version: str = Field(default="1.0.0", description="Template version")
    supported_languages: List[LanguageType] = Field(..., description="Supported languages")
    supported_frameworks: List[FrameworkType] = Field(default_factory=list, description="Supported frameworks")
    project_types: List[ProjectType] = Field(..., description="Applicable project types")
    team_sizes: List[TeamSize] = Field(default_factory=list, description="Applicable team sizes")
    
    # Template structure
    root_directory: DirectoryTemplate = Field(..., description="Root directory template")
    
    # Configuration templates
    build_configs: Dict[str, FileTemplate] = Field(default_factory=dict, description="Build configuration files")
    ci_cd_configs: Dict[CICDPlatform, FileTemplate] = Field(default_factory=dict, description="CI/CD configurations")
    linting_configs: Dict[str, FileTemplate] = Field(default_factory=dict, description="Linting configurations")
    testing_configs: Dict[str, FileTemplate] = Field(default_factory=dict, description="Testing configurations")
    
    # Documentation templates
    readme_template: Optional[FileTemplate] = Field(default=None, description="README template")
    contributing_template: Optional[FileTemplate] = Field(default=None, description="Contributing guidelines template")
    changelog_template: Optional[FileTemplate] = Field(default=None, description="Changelog template")
    
    # Prerequisites and dependencies
    prerequisites: List[str] = Field(default_factory=list, description="Required tools/dependencies")
    dependencies: Dict[str, List[str]] = Field(default_factory=dict, description="Language-specific dependencies")
    
    # Customization points
    customization_points: List[str] = Field(default_factory=list, description="Customizable aspects")
    template_variables: Dict[str, Any] = Field(default_factory=dict, description="Default template variables")


class TemplateContext(BaseModel):
    """Context for template rendering."""

    project_spec: ProjectSpec = Field(..., description="Project specification")
    template_variables: Dict[str, Any] = Field(default_factory=dict, description="Template variables")
    output_path: Path = Field(..., description="Output directory path")
    overwrite_existing: bool = Field(default=False, description="Whether to overwrite existing files")


class ScaffoldingResult(BaseModel):
    """Result of project scaffolding operation."""

    success: bool = Field(..., description="Whether scaffolding was successful")
    project_path: Path = Field(..., description="Path to created project")
    created_files: List[Path] = Field(default_factory=list, description="List of created files")
    created_directories: List[Path] = Field(default_factory=list, description="List of created directories")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")
    warnings: List[str] = Field(default_factory=list, description="Any warnings")
    next_steps: List[str] = Field(default_factory=list, description="Recommended next steps")


@dataclass
class TemplateRegistry:
    """Registry of available project templates."""

    templates: Dict[str, ProjectTemplate] = field(default_factory=dict)
    template_paths: Dict[str, Path] = field(default_factory=dict)

    def register_template(self, template: ProjectTemplate, template_path: Optional[Path] = None) -> None:
        """Register a new template."""
        self.templates[template.id] = template
        if template_path:
            self.template_paths[template.id] = template_path

    def get_template(self, template_id: str) -> Optional[ProjectTemplate]:
        """Get a template by ID."""
        return self.templates.get(template_id)

    def list_templates(
        self,
        language: Optional[LanguageType] = None,
        project_type: Optional[ProjectType] = None,
        framework: Optional[FrameworkType] = None,
    ) -> List[ProjectTemplate]:
        """List templates matching criteria."""
        templates = list(self.templates.values())
        
        if language:
            templates = [t for t in templates if language in t.supported_languages]
        
        if project_type:
            templates = [t for t in templates if project_type in t.project_types]
        
        if framework:
            templates = [t for t in templates if framework in t.supported_frameworks]
        
        return templates


class CustomizationPoint(BaseModel):
    """Defines a customizable aspect of a template."""

    name: str = Field(..., description="Customization point name")
    description: str = Field(..., description="Description of what can be customized")
    type: str = Field(..., description="Type of customization (string, boolean, choice, etc.)")
    default_value: Any = Field(default=None, description="Default value")
    choices: Optional[List[str]] = Field(default=None, description="Available choices for choice type")
    required: bool = Field(default=False, description="Whether customization is required")


class TemplateValidationResult(BaseModel):
    """Result of template validation."""

    is_valid: bool = Field(..., description="Whether template is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")