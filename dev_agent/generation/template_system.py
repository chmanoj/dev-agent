"""Project template and scaffolding system."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, Template

from ..errors.exceptions import TemplateError, ValidationError
from ..models.enums import CICDPlatform, FrameworkType, LanguageType, ProjectType, TeamSize
from ..models.templates import (
    CustomizationPoint,
    FileTemplate,
    ProjectSpec,
    ProjectTemplate,
    ScaffoldingResult,
    TemplateContext,
    TemplateRegistry,
    TemplateValidationResult,
)


class TemplateSystem:
    """Main template system for intelligent project scaffolding."""

    def __init__(self, template_directory: Optional[Path] = None):
        """Initialize the template system.
        
        Args:
            template_directory: Directory containing template definitions
        """
        self.template_directory = template_directory or Path(__file__).parent / "templates"
        self.registry = TemplateRegistry()
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_directory)),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self._load_builtin_templates()

    def _load_builtin_templates(self) -> None:
        """Load built-in project templates."""
        # Load templates from the template directory
        if self.template_directory.exists():
            for template_file in self.template_directory.glob("*.json"):
                try:
                    template_data = json.loads(template_file.read_text())
                    template = ProjectTemplate(**template_data)
                    self.registry.register_template(template, template_file)
                except Exception as e:
                    # Log error but continue loading other templates
                    print(f"Warning: Failed to load template {template_file}: {e}")

    def create_project_scaffold(self, project_spec: ProjectSpec, output_path: Path) -> ScaffoldingResult:
        """Create a complete project scaffold based on specification.
        
        Args:
            project_spec: Project specification
            output_path: Directory where project should be created
            
        Returns:
            ScaffoldingResult with details of the scaffolding operation
        """
        try:
            # Find appropriate template
            template = self._select_template(project_spec)
            if not template:
                return ScaffoldingResult(
                    success=False,
                    project_path=output_path,
                    errors=["No suitable template found for project specification"]
                )

            # Create template context
            context = TemplateContext(
                project_spec=project_spec,
                template_variables=self._build_template_variables(project_spec),
                output_path=output_path,
                overwrite_existing=False
            )

            # Validate template
            validation_result = self.validate_template(template)
            if not validation_result.is_valid:
                return ScaffoldingResult(
                    success=False,
                    project_path=output_path,
                    errors=validation_result.errors,
                    warnings=validation_result.warnings
                )

            # Create project structure
            result = self._create_project_structure(template, context)
            
            # Generate configuration files
            self._generate_build_configs(template, context, result)
            self._generate_ci_cd_configs(template, context, result)
            self._generate_linting_configs(template, context, result)
            self._generate_testing_configs(template, context, result)
            
            # Generate documentation
            self._generate_documentation(template, context, result)
            
            # Add next steps
            result.next_steps = self._generate_next_steps(project_spec, template)
            
            return result

        except Exception as e:
            return ScaffoldingResult(
                success=False,
                project_path=output_path,
                errors=[f"Scaffolding failed: {str(e)}"]
            )

    def _select_template(self, project_spec: ProjectSpec) -> Optional[ProjectTemplate]:
        """Select the most appropriate template for the project specification."""
        templates = self.registry.list_templates(
            language=project_spec.primary_language,
            project_type=project_spec.project_type
        )
        
        if not templates:
            # Try to find a generic template
            templates = self.registry.list_templates(project_type=project_spec.project_type)
        
        if not templates:
            return None
        
        # Score templates based on framework compatibility
        scored_templates = []
        for template in templates:
            score = 0
            
            # Score based on framework support
            for framework in project_spec.frameworks:
                if framework in template.supported_frameworks:
                    score += 10
            
            # Score based on team size support
            if project_spec.team_size in template.team_sizes:
                score += 5
            
            scored_templates.append((score, template))
        
        # Return the highest scoring template
        scored_templates.sort(key=lambda x: x[0], reverse=True)
        return scored_templates[0][1] if scored_templates else templates[0]

    def _build_template_variables(self, project_spec: ProjectSpec) -> Dict[str, Any]:
        """Build template variables from project specification."""
        return {
            "project_name": project_spec.name,
            "project_description": project_spec.description,
            "project_type": project_spec.project_type.value,
            "primary_language": project_spec.primary_language.value,
            "frameworks": [f.value for f in project_spec.frameworks],
            "team_size": project_spec.team_size.value,
            "python_version": project_spec.python_version,
            "license_type": project_spec.license_type,
            "author_name": project_spec.author_name or "Your Name",
            "author_email": project_spec.author_email or "your.email@example.com",
            "repository_url": project_spec.repository_url or "",
            "include_ci_cd": project_spec.include_ci_cd,
            "ci_cd_platform": project_spec.ci_cd_platform.value if project_spec.ci_cd_platform else None,
            "include_docker": project_spec.include_docker,
            "include_testing": project_spec.include_testing,
            "include_linting": project_spec.include_linting,
            "include_docs": project_spec.include_docs,
            **project_spec.custom_requirements,
        }

    def _create_project_structure(self, template: ProjectTemplate, context: TemplateContext) -> ScaffoldingResult:
        """Create the basic project directory structure."""
        result = ScaffoldingResult(
            success=True,
            project_path=context.output_path,
            created_files=[],
            created_directories=[],
            errors=[],
            warnings=[]
        )

        try:
            # Create root directory
            context.output_path.mkdir(parents=True, exist_ok=True)
            result.created_directories.append(context.output_path)

            # Create directory structure from template
            self._create_directory_from_template(
                template.root_directory,
                context.output_path,
                context.template_variables,
                result
            )

        except Exception as e:
            result.success = False
            result.errors.append(f"Failed to create project structure: {str(e)}")

        return result

    def _create_directory_from_template(
        self,
        dir_template: Any,  # DirectoryTemplate from models
        base_path: Path,
        variables: Dict[str, Any],
        result: ScaffoldingResult
    ) -> None:
        """Recursively create directory structure from template."""
        # Create the directory
        dir_path = base_path / self._render_template_string(dir_template.path, variables)
        dir_path.mkdir(parents=True, exist_ok=True)
        result.created_directories.append(dir_path)

        # Create files in this directory
        for file_template in dir_template.files:
            file_path = dir_path / self._render_template_string(file_template.path, variables)
            content = self._render_template_string(file_template.content, variables)
            
            file_path.write_text(content, encoding=file_template.encoding)
            result.created_files.append(file_path)
            
            if file_template.is_executable:
                file_path.chmod(0o755)

        # Create subdirectories
        for subdir_template in dir_template.subdirectories:
            self._create_directory_from_template(subdir_template, dir_path, variables, result)

    def _render_template_string(self, template_string: str, variables: Dict[str, Any]) -> str:
        """Render a template string with variables."""
        template = Template(template_string)
        return template.render(**variables)

    def _generate_build_configs(
        self,
        template: ProjectTemplate,
        context: TemplateContext,
        result: ScaffoldingResult
    ) -> None:
        """Generate build configuration files."""
        for config_name, file_template in template.build_configs.items():
            try:
                file_path = context.output_path / self._render_template_string(
                    file_template.path, context.template_variables
                )
                content = self._render_template_string(file_template.content, context.template_variables)
                
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content, encoding=file_template.encoding)
                result.created_files.append(file_path)
                
            except Exception as e:
                result.warnings.append(f"Failed to generate build config {config_name}: {str(e)}")

    def _generate_ci_cd_configs(
        self,
        template: ProjectTemplate,
        context: TemplateContext,
        result: ScaffoldingResult
    ) -> None:
        """Generate CI/CD configuration files."""
        if not context.project_spec.include_ci_cd or not context.project_spec.ci_cd_platform:
            return

        platform = context.project_spec.ci_cd_platform
        if platform in template.ci_cd_configs:
            try:
                file_template = template.ci_cd_configs[platform]
                file_path = context.output_path / self._render_template_string(
                    file_template.path, context.template_variables
                )
                content = self._render_template_string(file_template.content, context.template_variables)
                
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content, encoding=file_template.encoding)
                result.created_files.append(file_path)
                
            except Exception as e:
                result.warnings.append(f"Failed to generate CI/CD config for {platform.value}: {str(e)}")

    def _generate_linting_configs(
        self,
        template: ProjectTemplate,
        context: TemplateContext,
        result: ScaffoldingResult
    ) -> None:
        """Generate linting configuration files."""
        if not context.project_spec.include_linting:
            return

        for config_name, file_template in template.linting_configs.items():
            try:
                file_path = context.output_path / self._render_template_string(
                    file_template.path, context.template_variables
                )
                content = self._render_template_string(file_template.content, context.template_variables)
                
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content, encoding=file_template.encoding)
                result.created_files.append(file_path)
                
            except Exception as e:
                result.warnings.append(f"Failed to generate linting config {config_name}: {str(e)}")

    def _generate_testing_configs(
        self,
        template: ProjectTemplate,
        context: TemplateContext,
        result: ScaffoldingResult
    ) -> None:
        """Generate testing framework configuration files."""
        if not context.project_spec.include_testing:
            return

        for config_name, file_template in template.testing_configs.items():
            try:
                file_path = context.output_path / self._render_template_string(
                    file_template.path, context.template_variables
                )
                content = self._render_template_string(file_template.content, context.template_variables)
                
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content, encoding=file_template.encoding)
                result.created_files.append(file_path)
                
            except Exception as e:
                result.warnings.append(f"Failed to generate testing config {config_name}: {str(e)}")

    def _generate_documentation(
        self,
        template: ProjectTemplate,
        context: TemplateContext,
        result: ScaffoldingResult
    ) -> None:
        """Generate documentation templates."""
        if not context.project_spec.include_docs:
            return

        # Generate README
        if template.readme_template:
            try:
                file_path = context.output_path / self._render_template_string(
                    template.readme_template.path, context.template_variables
                )
                content = self._render_template_string(
                    template.readme_template.content, context.template_variables
                )
                
                file_path.write_text(content, encoding=template.readme_template.encoding)
                result.created_files.append(file_path)
                
            except Exception as e:
                result.warnings.append(f"Failed to generate README: {str(e)}")

        # Generate contributing guidelines
        if template.contributing_template:
            try:
                file_path = context.output_path / self._render_template_string(
                    template.contributing_template.path, context.template_variables
                )
                content = self._render_template_string(
                    template.contributing_template.content, context.template_variables
                )
                
                file_path.write_text(content, encoding=template.contributing_template.encoding)
                result.created_files.append(file_path)
                
            except Exception as e:
                result.warnings.append(f"Failed to generate CONTRIBUTING: {str(e)}")

        # Generate changelog
        if template.changelog_template:
            try:
                file_path = context.output_path / self._render_template_string(
                    template.changelog_template.path, context.template_variables
                )
                content = self._render_template_string(
                    template.changelog_template.content, context.template_variables
                )
                
                file_path.write_text(content, encoding=template.changelog_template.encoding)
                result.created_files.append(file_path)
                
            except Exception as e:
                result.warnings.append(f"Failed to generate CHANGELOG: {str(e)}")

    def _generate_next_steps(self, project_spec: ProjectSpec, template: ProjectTemplate) -> List[str]:
        """Generate recommended next steps for the user."""
        steps = []
        
        # Basic setup steps
        steps.append(f"cd {project_spec.name}")
        
        if project_spec.primary_language == LanguageType.PYTHON:
            steps.append("uv sync --dev  # Install dependencies")
            if project_spec.include_linting:
                steps.append("uv run pre-commit install  # Setup pre-commit hooks")
        
        if project_spec.include_testing:
            if project_spec.primary_language == LanguageType.PYTHON:
                steps.append("uv run pytest  # Run tests")
            elif project_spec.primary_language in [LanguageType.JAVASCRIPT, LanguageType.TYPESCRIPT]:
                steps.append("npm test  # Run tests")
        
        if project_spec.include_ci_cd:
            steps.append("git init && git add . && git commit -m 'Initial commit'")
            steps.append("# Push to your repository to trigger CI/CD")
        
        # Framework-specific steps
        for framework in project_spec.frameworks:
            if framework == FrameworkType.FASTAPI:
                steps.append("uv run uvicorn main:app --reload  # Start development server")
            elif framework == FrameworkType.DJANGO:
                steps.append("python manage.py migrate  # Run database migrations")
                steps.append("python manage.py runserver  # Start development server")
            elif framework == FrameworkType.REACT:
                steps.append("npm start  # Start development server")
        
        return steps

    def validate_template(self, template: ProjectTemplate) -> TemplateValidationResult:
        """Validate a project template for correctness."""
        errors = []
        warnings = []

        # Validate basic template structure
        if not template.id:
            errors.append("Template ID is required")
        
        if not template.name:
            errors.append("Template name is required")
        
        if not template.supported_languages:
            errors.append("Template must support at least one language")
        
        if not template.project_types:
            errors.append("Template must support at least one project type")

        # Validate file templates
        for config_name, file_template in template.build_configs.items():
            if not file_template.path:
                errors.append(f"Build config '{config_name}' missing path")
            if not file_template.content:
                warnings.append(f"Build config '{config_name}' has empty content")

        # Validate CI/CD configs
        for platform, file_template in template.ci_cd_configs.items():
            if not file_template.path:
                errors.append(f"CI/CD config for '{platform.value}' missing path")

        return TemplateValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def list_available_templates(
        self,
        language: Optional[LanguageType] = None,
        project_type: Optional[ProjectType] = None,
        framework: Optional[FrameworkType] = None,
    ) -> List[ProjectTemplate]:
        """List available templates matching criteria."""
        return self.registry.list_templates(language, project_type, framework)

    def get_template_by_id(self, template_id: str) -> Optional[ProjectTemplate]:
        """Get a specific template by ID."""
        return self.registry.get_template(template_id)

    def register_custom_template(self, template: ProjectTemplate) -> None:
        """Register a custom template."""
        self.registry.register_template(template)

    def customize_template(
        self,
        template_id: str,
        customizations: Dict[str, Any]
    ) -> Optional[ProjectTemplate]:
        """Create a customized version of a template."""
        base_template = self.registry.get_template(template_id)
        if not base_template:
            return None

        # Create a copy of the template with customizations applied
        customized_template = base_template.model_copy(deep=True)
        
        # Apply customizations to template variables
        customized_template.template_variables.update(customizations)
        
        # Update template ID to indicate it's customized
        customized_template.id = f"{template_id}_customized"
        
        return customized_template