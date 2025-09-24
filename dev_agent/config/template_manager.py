"""Template management and customization system."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from jinja2 import Environment, FileSystemLoader, Template, TemplateSyntaxError
from pydantic import BaseModel, Field, ValidationError

from ..models.enums import FrameworkType, LanguageType, ProjectType
from ..models.templates import (
    CustomizationPoint,
    FileTemplate,
    ProjectTemplate,
    TemplateContext,
    TemplateValidationResult,
)
from .customization_manager import CustomizationProfile, TemplateOverride


class TemplateVersion(BaseModel):
    """Version information for templates."""

    version: str = Field(..., description="Version string (semver)")
    created_at: str = Field(..., description="Creation timestamp")
    created_by: str = Field(..., description="Creator")
    changelog: str = Field(default="", description="Version changelog")
    is_stable: bool = Field(default=False, description="Whether version is stable")


class TemplateMetadata(BaseModel):
    """Extended metadata for templates."""

    template_id: str = Field(..., description="Template identifier")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    
    # Version management
    current_version: str = Field(..., description="Current version")
    versions: List[TemplateVersion] = Field(default_factory=list, description="Version history")
    
    # Categorization
    category: str = Field(default="general", description="Template category")
    tags: List[str] = Field(default_factory=list, description="Template tags")
    
    # Compatibility
    supported_languages: List[LanguageType] = Field(default_factory=list)
    supported_frameworks: List[FrameworkType] = Field(default_factory=list)
    project_types: List[ProjectType] = Field(default_factory=list)
    
    # Usage statistics
    usage_count: int = Field(default=0, description="Number of times used")
    rating: float = Field(default=0.0, description="Average user rating")
    
    # Sharing and collaboration
    is_public: bool = Field(default=False, description="Whether template is public")
    team_id: Optional[str] = Field(default=None, description="Associated team")
    created_by: str = Field(..., description="Template creator")
    contributors: List[str] = Field(default_factory=list, description="Contributors")


class CustomTemplate(BaseModel):
    """Custom template with extended functionality."""

    metadata: TemplateMetadata = Field(..., description="Template metadata")
    template: ProjectTemplate = Field(..., description="Template definition")
    
    # Customization
    customization_points: List[CustomizationPoint] = Field(
        default_factory=list,
        description="Available customization points"
    )
    
    # Dependencies
    dependencies: List[str] = Field(
        default_factory=list,
        description="Template dependencies"
    )
    
    # Validation rules
    validation_rules: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom validation rules"
    )


class TemplateManager:
    """Manages custom templates and template operations."""

    def __init__(self, templates_dir: Optional[Path] = None):
        """Initialize template manager.
        
        Args:
            templates_dir: Directory for storing templates
        """
        if templates_dir:
            self.templates_dir = Path(templates_dir)
        else:
            self.templates_dir = Path.home() / ".dev_agent" / "templates"
        
        self.custom_templates_dir = self.templates_dir / "custom"
        self.shared_templates_dir = self.templates_dir / "shared"
        self.builtin_templates_dir = self.templates_dir / "builtin"
        
        self._ensure_directories()
        self._template_cache: Dict[str, CustomTemplate] = {}
        self._jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        for directory in [
            self.templates_dir,
            self.custom_templates_dir,
            self.shared_templates_dir,
            self.builtin_templates_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    def create_template(
        self,
        template_id: str,
        name: str,
        description: str,
        created_by: str,
        project_template: ProjectTemplate,
        category: str = "general",
        tags: Optional[List[str]] = None,
    ) -> CustomTemplate:
        """Create a new custom template.
        
        Args:
            template_id: Unique template identifier
            name: Template name
            description: Template description
            created_by: Creator of the template
            project_template: Base project template
            category: Template category
            tags: Optional tags
            
        Returns:
            Created custom template
            
        Raises:
            ValueError: If template ID already exists
        """
        if self.template_exists(template_id):
            raise ValueError(f"Template with ID '{template_id}' already exists")
        
        from datetime import datetime
        
        # Create metadata
        metadata = TemplateMetadata(
            template_id=template_id,
            name=name,
            description=description,
            current_version="1.0.0",
            category=category,
            tags=tags or [],
            created_by=created_by,
        )
        
        # Add initial version
        initial_version = TemplateVersion(
            version="1.0.0",
            created_at=datetime.now().isoformat(),
            created_by=created_by,
            changelog="Initial version",
            is_stable=True,
        )
        metadata.versions.append(initial_version)
        
        # Create custom template
        custom_template = CustomTemplate(
            metadata=metadata,
            template=project_template,
        )
        
        self.save_template(custom_template)
        return custom_template

    def load_template(self, template_id: str) -> Optional[CustomTemplate]:
        """Load a custom template.
        
        Args:
            template_id: ID of template to load
            
        Returns:
            Loaded template or None if not found
        """
        if template_id in self._template_cache:
            return self._template_cache[template_id]
        
        # Try custom templates first
        template_path = self.custom_templates_dir / f"{template_id}.json"
        if not template_path.exists():
            # Try shared templates
            template_path = self.shared_templates_dir / f"{template_id}.json"
        
        if not template_path.exists():
            # Try builtin templates
            template_path = self.builtin_templates_dir / f"{template_id}.json"
        
        if not template_path.exists():
            return None
        
        try:
            with open(template_path, encoding="utf-8") as f:
                data = json.load(f)
            
            template = CustomTemplate(**data)
            self._template_cache[template_id] = template
            return template
            
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"Error loading template {template_id}: {e}")
            return None

    def save_template(self, template: CustomTemplate, is_shared: bool = False) -> bool:
        """Save a custom template.
        
        Args:
            template: Template to save
            is_shared: Whether to save as shared template
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            if is_shared:
                template_path = self.shared_templates_dir / f"{template.metadata.template_id}.json"
            else:
                template_path = self.custom_templates_dir / f"{template.metadata.template_id}.json"
            
            with open(template_path, "w", encoding="utf-8") as f:
                json.dump(template.model_dump(mode='json'), f, indent=2)
            
            self._template_cache[template.metadata.template_id] = template
            return True
            
        except Exception as e:
            print(f"Error saving template {template.metadata.template_id}: {e}")
            return False

    def delete_template(self, template_id: str) -> bool:
        """Delete a custom template.
        
        Args:
            template_id: ID of template to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Try to delete from all possible locations
            for templates_dir in [self.custom_templates_dir, self.shared_templates_dir]:
                template_path = templates_dir / f"{template_id}.json"
                if template_path.exists():
                    template_path.unlink()
            
            if template_id in self._template_cache:
                del self._template_cache[template_id]
            
            return True
            
        except Exception as e:
            print(f"Error deleting template {template_id}: {e}")
            return False

    def list_templates(
        self,
        category: Optional[str] = None,
        language: Optional[LanguageType] = None,
        framework: Optional[FrameworkType] = None,
        project_type: Optional[ProjectType] = None,
        include_shared: bool = True,
        include_builtin: bool = True,
    ) -> List[CustomTemplate]:
        """List available templates with filtering.
        
        Args:
            category: Filter by category
            language: Filter by supported language
            framework: Filter by supported framework
            project_type: Filter by project type
            include_shared: Include shared templates
            include_builtin: Include builtin templates
            
        Returns:
            List of matching templates
        """
        templates = []
        
        # Collect template files
        template_dirs = [self.custom_templates_dir]
        if include_shared:
            template_dirs.append(self.shared_templates_dir)
        if include_builtin:
            template_dirs.append(self.builtin_templates_dir)
        
        for templates_dir in template_dirs:
            for template_file in templates_dir.glob("*.json"):
                template_id = template_file.stem
                template = self.load_template(template_id)
                
                if template and self._matches_filters(
                    template, category, language, framework, project_type
                ):
                    templates.append(template)
        
        return templates

    def _matches_filters(
        self,
        template: CustomTemplate,
        category: Optional[str],
        language: Optional[LanguageType],
        framework: Optional[FrameworkType],
        project_type: Optional[ProjectType],
    ) -> bool:
        """Check if template matches filters."""
        if category and template.metadata.category != category:
            return False
        
        # Check both metadata and template supported languages
        supported_languages = template.metadata.supported_languages or template.template.supported_languages
        if language and language not in supported_languages:
            return False
        
        # Check both metadata and template supported frameworks
        supported_frameworks = template.metadata.supported_frameworks or template.template.supported_frameworks
        if framework and framework not in supported_frameworks:
            return False
        
        # Check both metadata and template project types
        project_types = template.metadata.project_types or template.template.project_types
        if project_type and project_type not in project_types:
            return False
        
        return True

    def template_exists(self, template_id: str) -> bool:
        """Check if a template exists.
        
        Args:
            template_id: ID to check
            
        Returns:
            True if template exists, False otherwise
        """
        for templates_dir in [
            self.custom_templates_dir,
            self.shared_templates_dir,
            self.builtin_templates_dir,
        ]:
            template_path = templates_dir / f"{template_id}.json"
            if template_path.exists():
                return True
        return False

    def validate_template(self, template: CustomTemplate) -> TemplateValidationResult:
        """Validate a custom template.
        
        Args:
            template: Template to validate
            
        Returns:
            Validation result
        """
        errors = []
        warnings = []
        
        # Validate metadata
        if not template.metadata.template_id:
            errors.append("Template ID cannot be empty")
        
        if not template.metadata.name:
            errors.append("Template name cannot be empty")
        
        if not template.metadata.created_by:
            errors.append("Template creator cannot be empty")
        
        # Validate template structure
        try:
            # Check if template files have valid Jinja2 syntax
            for file_template in self._get_all_file_templates(template.template):
                try:
                    self._jinja_env.from_string(file_template.content)
                except TemplateSyntaxError as e:
                    errors.append(f"Invalid Jinja2 syntax in {file_template.path}: {e}")
        except Exception as e:
            errors.append(f"Error validating template structure: {e}")
        
        # Validate customization points
        for point in template.customization_points:
            if not point.name:
                errors.append("Customization point name cannot be empty")
            
            if point.type not in ["string", "boolean", "choice", "number"]:
                warnings.append(f"Unknown customization point type: {point.type}")
        
        # Validate dependencies
        for dependency in template.dependencies:
            if not self.template_exists(dependency):
                warnings.append(f"Dependency template '{dependency}' not found")
        
        return TemplateValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _get_all_file_templates(self, project_template: ProjectTemplate) -> List[FileTemplate]:
        """Get all file templates from a project template."""
        file_templates = []
        
        # Add files from root directory
        self._collect_file_templates(project_template.root_directory, file_templates)
        
        # Add configuration files
        file_templates.extend(project_template.build_configs.values())
        file_templates.extend(project_template.ci_cd_configs.values())
        file_templates.extend(project_template.linting_configs.values())
        file_templates.extend(project_template.testing_configs.values())
        
        # Add documentation files
        if project_template.readme_template:
            file_templates.append(project_template.readme_template)
        if project_template.contributing_template:
            file_templates.append(project_template.contributing_template)
        if project_template.changelog_template:
            file_templates.append(project_template.changelog_template)
        
        return file_templates

    def _collect_file_templates(self, directory, file_templates: List[FileTemplate]) -> None:
        """Recursively collect file templates from directory structure."""
        file_templates.extend(directory.files)
        for subdir in directory.subdirectories:
            self._collect_file_templates(subdir, file_templates)

    def apply_customization(
        self,
        template: CustomTemplate,
        customization_profile: CustomizationProfile,
    ) -> CustomTemplate:
        """Apply customization profile to template.
        
        Args:
            template: Base template
            customization_profile: Customization to apply
            
        Returns:
            Customized template
        """
        # Create a copy of the template
        customized_data = template.model_dump()
        
        # Apply template overrides from profile
        template_id = template.metadata.template_id
        if template_id in customization_profile.template_overrides:
            override = customization_profile.template_overrides[template_id]
            self._apply_template_override(customized_data, override)
        
        # Apply coding standards
        self._apply_coding_standards(customized_data, customization_profile.coding_standards)
        
        # Apply architectural preferences
        self._apply_architectural_preferences(
            customized_data, customization_profile.architectural_preferences
        )
        
        return CustomTemplate(**customized_data)

    def _apply_template_override(self, template_data: Dict[str, Any], override: TemplateOverride) -> None:
        """Apply template override to template data."""
        if override.override_type == "replace":
            # Replace entire sections
            for key, value in override.file_overrides.items():
                if "template" in template_data and "root_directory" in template_data["template"]:
                    # Find and replace file content
                    self._replace_file_content(template_data["template"]["root_directory"], key, value)
        
        elif override.override_type == "merge":
            # Merge variable overrides
            if "template" in template_data:
                template_vars = template_data["template"].get("template_variables", {})
                template_vars.update(override.variable_overrides)
                template_data["template"]["template_variables"] = template_vars

    def _replace_file_content(self, directory_data: Dict[str, Any], file_path: str, new_content: str) -> None:
        """Replace file content in directory structure."""
        # Check files in current directory
        for file_data in directory_data.get("files", []):
            if file_data.get("path") == file_path:
                file_data["content"] = new_content
                return
        
        # Check subdirectories
        for subdir_data in directory_data.get("subdirectories", []):
            self._replace_file_content(subdir_data, file_path, new_content)

    def _apply_coding_standards(self, template_data: Dict[str, Any], coding_standards) -> None:
        """Apply coding standards to template."""
        # Update template variables with coding standards
        template_vars = template_data.get("template", {}).get("template_variables", {})
        
        template_vars.update({
            "line_length": coding_standards.line_length,
            "indent_size": coding_standards.indent_size,
            "indentation": coding_standards.indentation,
            "naming_conventions": coding_standards.naming_conventions,
            "documentation_style": coding_standards.documentation_style,
            "type_hints_required": coding_standards.type_hints_required,
        })
        
        if "template" not in template_data:
            template_data["template"] = {}
        template_data["template"]["template_variables"] = template_vars

    def _apply_architectural_preferences(self, template_data: Dict[str, Any], arch_prefs) -> None:
        """Apply architectural preferences to template."""
        template_vars = template_data.get("template", {}).get("template_variables", {})
        
        template_vars.update({
            "preferred_patterns": arch_prefs.preferred_patterns,
            "layered_architecture": arch_prefs.layered_architecture,
            "dependency_injection": arch_prefs.dependency_injection,
            "error_handling_strategy": arch_prefs.error_handling_strategy,
            "logging_strategy": arch_prefs.logging_strategy,
            "testing_strategy": arch_prefs.testing_strategy,
        })
        
        if "template" not in template_data:
            template_data["template"] = {}
        template_data["template"]["template_variables"] = template_vars

    def render_template(
        self,
        template: CustomTemplate,
        context: TemplateContext,
    ) -> Dict[str, str]:
        """Render template with given context.
        
        Args:
            template: Template to render
            context: Rendering context
            
        Returns:
            Dictionary mapping file paths to rendered content
        """
        rendered_files = {}
        
        # Prepare Jinja2 context
        jinja_context = {
            **template.template.template_variables,
            **context.template_variables,
            "project_spec": context.project_spec.model_dump(),
        }
        
        # Render all file templates
        for file_template in self._get_all_file_templates(template.template):
            try:
                jinja_template = self._jinja_env.from_string(file_template.content)
                rendered_content = jinja_template.render(**jinja_context)
                rendered_files[file_template.path] = rendered_content
            except Exception as e:
                print(f"Error rendering template {file_template.path}: {e}")
        
        return rendered_files

    def create_version(
        self,
        template_id: str,
        new_version: str,
        changelog: str,
        created_by: str,
        is_stable: bool = False,
    ) -> bool:
        """Create a new version of a template.
        
        Args:
            template_id: ID of template to version
            new_version: New version string
            changelog: Version changelog
            created_by: Version creator
            is_stable: Whether version is stable
            
        Returns:
            True if version created successfully, False otherwise
        """
        template = self.load_template(template_id)
        if not template:
            return False
        
        from datetime import datetime
        
        # Create new version
        version = TemplateVersion(
            version=new_version,
            created_at=datetime.now().isoformat(),
            created_by=created_by,
            changelog=changelog,
            is_stable=is_stable,
        )
        
        # Add to template
        template.metadata.versions.append(version)
        template.metadata.current_version = new_version
        
        return self.save_template(template)

    def export_template(self, template_id: str, export_path: Path) -> bool:
        """Export a template to a file.
        
        Args:
            template_id: ID of template to export
            export_path: Path to export file
            
        Returns:
            True if exported successfully, False otherwise
        """
        template = self.load_template(template_id)
        if not template:
            return False
        
        try:
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(template.model_dump(mode='json'), f, indent=2)
            return True
            
        except Exception as e:
            print(f"Error exporting template: {e}")
            return False

    def import_template(self, import_path: Path, new_template_id: Optional[str] = None) -> Optional[str]:
        """Import a template from a file.
        
        Args:
            import_path: Path to import file
            new_template_id: Optional new ID for imported template
            
        Returns:
            ID of imported template or None if failed
        """
        try:
            with open(import_path, encoding="utf-8") as f:
                data = json.load(f)
            
            template = CustomTemplate(**data)
            
            if new_template_id:
                template.metadata.template_id = new_template_id
            
            # Check if template already exists
            if self.template_exists(template.metadata.template_id):
                # Generate unique ID
                counter = 1
                base_id = template.metadata.template_id
                while self.template_exists(f"{base_id}_{counter}"):
                    counter += 1
                template.metadata.template_id = f"{base_id}_{counter}"
            
            if self.save_template(template):
                return template.metadata.template_id
            
            return None
            
        except Exception as e:
            print(f"Error importing template: {e}")
            return None

    def share_template(self, template_id: str) -> bool:
        """Share a template (move to shared directory).
        
        Args:
            template_id: ID of template to share
            
        Returns:
            True if shared successfully, False otherwise
        """
        template = self.load_template(template_id)
        if not template:
            return False
        
        # Mark as public and save to shared directory
        template.metadata.is_public = True
        return self.save_template(template, is_shared=True)