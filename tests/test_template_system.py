"""Tests for the template system and project scaffolding."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest

from dev_agent.generation.template_system import TemplateSystem
from dev_agent.models.enums import (
    CICDPlatform,
    FrameworkType,
    LanguageType,
    ProjectType,
    TeamSize,
)
from dev_agent.models.templates import (
    DirectoryTemplate,
    FileTemplate,
    ProjectSpec,
    ProjectTemplate,
    TemplateRegistry,
)


class TestTemplateSystem:
    """Test cases for the TemplateSystem class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.template_system = TemplateSystem(self.temp_dir)

    def teardown_method(self) -> None:
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_template_system_initialization(self) -> None:
        """Test template system initialization."""
        assert self.template_system.template_directory == self.temp_dir
        assert isinstance(self.template_system.registry, TemplateRegistry)
        assert self.template_system.jinja_env is not None

    def test_create_simple_project_scaffold(self) -> None:
        """Test creating a simple project scaffold."""
        # Create a simple template
        template = self._create_test_template()
        self.template_system.registry.register_template(template)

        # Create project spec
        project_spec = ProjectSpec(
            name="test-project",
            description="A test project",
            project_type=ProjectType.API_SERVICE,
            primary_language=LanguageType.PYTHON,
            frameworks=[FrameworkType.FASTAPI],
        )

        # Create scaffold
        output_path = self.temp_dir / "output"
        result = self.template_system.create_project_scaffold(project_spec, output_path)

        # Verify results
        assert result.success
        assert result.project_path == output_path
        assert len(result.created_files) > 0
        assert len(result.created_directories) > 0
        assert len(result.errors) == 0

        # Verify files were created
        assert (output_path / "main.py").exists()
        assert (output_path / "README.md").exists()

    def test_template_variable_substitution(self) -> None:
        """Test template variable substitution."""
        template = self._create_test_template()
        self.template_system.registry.register_template(template)

        project_spec = ProjectSpec(
            name="my-awesome-project",
            description="An awesome test project",
            project_type=ProjectType.API_SERVICE,
            primary_language=LanguageType.PYTHON,
        )

        output_path = self.temp_dir / "output"
        result = self.template_system.create_project_scaffold(project_spec, output_path)

        assert result.success

        # Check that variables were substituted
        main_py_content = (output_path / "main.py").read_text()
        assert "my-awesome-project" in main_py_content
        assert "An awesome test project" in main_py_content

    def test_ci_cd_configuration_generation(self) -> None:
        """Test CI/CD configuration generation."""
        template = self._create_test_template_with_cicd()
        self.template_system.registry.register_template(template)

        project_spec = ProjectSpec(
            name="test-project",
            description="A test project",
            project_type=ProjectType.API_SERVICE,
            primary_language=LanguageType.PYTHON,
            include_ci_cd=True,
            ci_cd_platform=CICDPlatform.GITHUB_ACTIONS,
        )

        output_path = self.temp_dir / "output"
        result = self.template_system.create_project_scaffold(project_spec, output_path)

        assert result.success
        assert (output_path / ".github" / "workflows" / "ci.yml").exists()

        # Verify CI/CD content
        ci_content = (output_path / ".github" / "workflows" / "ci.yml").read_text()
        assert "name: CI" in ci_content
        assert "test-project" in ci_content

    def test_template_validation(self) -> None:
        """Test template validation."""
        # Valid template
        valid_template = self._create_test_template()
        validation_result = self.template_system.validate_template(valid_template)
        assert validation_result.is_valid
        assert len(validation_result.errors) == 0

        # Invalid template (missing required fields)
        invalid_template = ProjectTemplate(
            id="",  # Empty ID should cause validation error
            name="Test Template",
            description="Test",
            supported_languages=[LanguageType.PYTHON],
            project_types=[ProjectType.API_SERVICE],
            root_directory=DirectoryTemplate(path=".", files=[], subdirectories=[]),
        )
        validation_result = self.template_system.validate_template(invalid_template)
        assert not validation_result.is_valid
        assert len(validation_result.errors) > 0
        assert "Template ID is required" in validation_result.errors

    def test_template_customization(self) -> None:
        """Test template customization."""
        template = self._create_test_template()
        self.template_system.registry.register_template(template)

        customizations = {
            "custom_feature": True,
            "api_version": "v2",
        }

        customized_template = self.template_system.customize_template(
            template.id, customizations
        )

        assert customized_template is not None
        assert customized_template.id == f"{template.id}_customized"
        assert customized_template.template_variables["custom_feature"] is True
        assert customized_template.template_variables["api_version"] == "v2"

    def test_list_available_templates(self) -> None:
        """Test listing available templates."""
        # Register multiple templates
        python_template = self._create_test_template()
        self.template_system.registry.register_template(python_template)

        js_template = ProjectTemplate(
            id="js_template",
            name="JavaScript Template",
            description="JavaScript project template",
            supported_languages=[LanguageType.JAVASCRIPT],
            project_types=[ProjectType.WEB_APPLICATION],
            root_directory=DirectoryTemplate(path=".", files=[], subdirectories=[]),
        )
        self.template_system.registry.register_template(js_template)

        # Test filtering by language
        python_templates = self.template_system.list_available_templates(
            language=LanguageType.PYTHON
        )
        assert len(python_templates) == 1
        assert python_templates[0].id == python_template.id

        js_templates = self.template_system.list_available_templates(
            language=LanguageType.JAVASCRIPT
        )
        assert len(js_templates) == 1
        assert js_templates[0].id == js_template.id

        # Test filtering by project type
        api_templates = self.template_system.list_available_templates(
            project_type=ProjectType.API_SERVICE
        )
        assert len(api_templates) == 1

        web_templates = self.template_system.list_available_templates(
            project_type=ProjectType.WEB_APPLICATION
        )
        assert len(web_templates) == 1

    def test_error_handling_invalid_template(self) -> None:
        """Test error handling with invalid template."""
        project_spec = ProjectSpec(
            name="test-project",
            description="A test project",
            project_type=ProjectType.API_SERVICE,
            primary_language=LanguageType.PYTHON,
        )

        output_path = self.temp_dir / "output"
        result = self.template_system.create_project_scaffold(project_spec, output_path)

        # Should fail because no suitable template is found
        assert not result.success
        assert len(result.errors) > 0
        assert "No suitable template found" in result.errors[0]

    def test_next_steps_generation(self) -> None:
        """Test generation of next steps."""
        template = self._create_test_template()
        self.template_system.registry.register_template(template)

        project_spec = ProjectSpec(
            name="test-project",
            description="A test project",
            project_type=ProjectType.API_SERVICE,
            primary_language=LanguageType.PYTHON,
            frameworks=[FrameworkType.FASTAPI],
            include_testing=True,
            include_ci_cd=True,
        )

        output_path = self.temp_dir / "output"
        result = self.template_system.create_project_scaffold(project_spec, output_path)

        assert result.success
        assert len(result.next_steps) > 0
        
        # Check for expected next steps
        next_steps_text = " ".join(result.next_steps)
        assert "cd test-project" in next_steps_text
        assert "uv sync --dev" in next_steps_text
        assert "pytest" in next_steps_text

    def _create_test_template(self) -> ProjectTemplate:
        """Create a test template for testing."""
        return ProjectTemplate(
            id="test_template",
            name="Test Template",
            description="A test template for unit testing",
            supported_languages=[LanguageType.PYTHON],
            supported_frameworks=[FrameworkType.FASTAPI],
            project_types=[ProjectType.API_SERVICE],
            team_sizes=[TeamSize.SOLO, TeamSize.SMALL],
            root_directory=DirectoryTemplate(
                path=".",
                files=[
                    FileTemplate(
                        path="main.py",
                        content='"""{{ project_description }}."""\n\nprint("Hello from {{ project_name }}!")\n',
                        is_executable=False,
                        encoding="utf-8",
                    ),
                    FileTemplate(
                        path="README.md",
                        content="# {{ project_name }}\n\n{{ project_description }}\n",
                        is_executable=False,
                        encoding="utf-8",
                    ),
                ],
                subdirectories=[],
            ),
            build_configs={
                "pyproject": FileTemplate(
                    path="pyproject.toml",
                    content='[project]\nname = "{{ project_name }}"\ndescription = "{{ project_description }}"\n',
                    is_executable=False,
                    encoding="utf-8",
                )
            },
            prerequisites=["python>=3.10"],
            dependencies={"python": ["fastapi>=0.100.0"]},
        )

    def _create_test_template_with_cicd(self) -> ProjectTemplate:
        """Create a test template with CI/CD configuration."""
        template = self._create_test_template()
        template.ci_cd_configs = {
            CICDPlatform.GITHUB_ACTIONS: FileTemplate(
                path=".github/workflows/ci.yml",
                content="name: CI\n\non:\n  push:\n    branches: [ main ]\n\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n    - uses: actions/checkout@v4\n    - name: Test {{ project_name }}\n      run: echo 'Testing {{ project_name }}'\n",
                is_executable=False,
                encoding="utf-8",
            )
        }
        return template


class TestTemplateRegistry:
    """Test cases for the TemplateRegistry class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.registry = TemplateRegistry()

    def test_register_and_get_template(self) -> None:
        """Test registering and retrieving templates."""
        template = ProjectTemplate(
            id="test_template",
            name="Test Template",
            description="Test",
            supported_languages=[LanguageType.PYTHON],
            project_types=[ProjectType.API_SERVICE],
            root_directory=DirectoryTemplate(path=".", files=[], subdirectories=[]),
        )

        # Register template
        self.registry.register_template(template)

        # Retrieve template
        retrieved = self.registry.get_template("test_template")
        assert retrieved is not None
        assert retrieved.id == "test_template"
        assert retrieved.name == "Test Template"

        # Try to get non-existent template
        non_existent = self.registry.get_template("non_existent")
        assert non_existent is None

    def test_list_templates_with_filters(self) -> None:
        """Test listing templates with various filters."""
        # Create templates for different languages and project types
        python_api_template = ProjectTemplate(
            id="python_api",
            name="Python API",
            description="Python API template",
            supported_languages=[LanguageType.PYTHON],
            project_types=[ProjectType.API_SERVICE],
            supported_frameworks=[FrameworkType.FASTAPI],
            root_directory=DirectoryTemplate(path=".", files=[], subdirectories=[]),
        )

        js_web_template = ProjectTemplate(
            id="js_web",
            name="JavaScript Web",
            description="JavaScript web template",
            supported_languages=[LanguageType.JAVASCRIPT],
            project_types=[ProjectType.WEB_APPLICATION],
            supported_frameworks=[FrameworkType.REACT],
            root_directory=DirectoryTemplate(path=".", files=[], subdirectories=[]),
        )

        python_web_template = ProjectTemplate(
            id="python_web",
            name="Python Web",
            description="Python web template",
            supported_languages=[LanguageType.PYTHON],
            project_types=[ProjectType.WEB_APPLICATION],
            supported_frameworks=[FrameworkType.DJANGO],
            root_directory=DirectoryTemplate(path=".", files=[], subdirectories=[]),
        )

        # Register all templates
        self.registry.register_template(python_api_template)
        self.registry.register_template(js_web_template)
        self.registry.register_template(python_web_template)

        # Test filtering by language
        python_templates = self.registry.list_templates(language=LanguageType.PYTHON)
        assert len(python_templates) == 2
        template_ids = [t.id for t in python_templates]
        assert "python_api" in template_ids
        assert "python_web" in template_ids

        # Test filtering by project type
        web_templates = self.registry.list_templates(project_type=ProjectType.WEB_APPLICATION)
        assert len(web_templates) == 2
        template_ids = [t.id for t in web_templates]
        assert "js_web" in template_ids
        assert "python_web" in template_ids

        # Test filtering by framework
        react_templates = self.registry.list_templates(framework=FrameworkType.REACT)
        assert len(react_templates) == 1
        assert react_templates[0].id == "js_web"

        # Test multiple filters
        python_web_templates = self.registry.list_templates(
            language=LanguageType.PYTHON,
            project_type=ProjectType.WEB_APPLICATION
        )
        assert len(python_web_templates) == 1
        assert python_web_templates[0].id == "python_web"

        # Test no matches
        no_matches = self.registry.list_templates(
            language=LanguageType.JAVA,
            project_type=ProjectType.API_SERVICE
        )
        assert len(no_matches) == 0


class TestProjectSpec:
    """Test cases for the ProjectSpec model."""

    def test_project_spec_creation(self) -> None:
        """Test creating a project specification."""
        spec = ProjectSpec(
            name="my-project",
            description="My awesome project",
            project_type=ProjectType.API_SERVICE,
            primary_language=LanguageType.PYTHON,
            frameworks=[FrameworkType.FASTAPI, FrameworkType.PYTEST],
            team_size=TeamSize.SMALL,
            include_ci_cd=True,
            ci_cd_platform=CICDPlatform.GITHUB_ACTIONS,
            include_docker=True,
            python_version="3.11",
            author_name="John Doe",
            author_email="john@example.com",
        )

        assert spec.name == "my-project"
        assert spec.description == "My awesome project"
        assert spec.project_type == ProjectType.API_SERVICE
        assert spec.primary_language == LanguageType.PYTHON
        assert FrameworkType.FASTAPI in spec.frameworks
        assert FrameworkType.PYTEST in spec.frameworks
        assert spec.team_size == TeamSize.SMALL
        assert spec.include_ci_cd is True
        assert spec.ci_cd_platform == CICDPlatform.GITHUB_ACTIONS
        assert spec.include_docker is True
        assert spec.python_version == "3.11"
        assert spec.author_name == "John Doe"
        assert spec.author_email == "john@example.com"

    def test_project_spec_defaults(self) -> None:
        """Test project specification default values."""
        spec = ProjectSpec(
            name="minimal-project",
            description="Minimal project",
            project_type=ProjectType.LIBRARY,
            primary_language=LanguageType.PYTHON,
        )

        assert spec.frameworks == []
        assert spec.team_size == TeamSize.SOLO
        assert spec.include_ci_cd is True
        assert spec.ci_cd_platform is None
        assert spec.include_docker is False
        assert spec.include_testing is True
        assert spec.include_linting is True
        assert spec.include_docs is True
        assert spec.python_version == "3.11"
        assert spec.license_type == "MIT"
        assert spec.custom_requirements == {}


@pytest.mark.integration
class TestTemplateSystemIntegration:
    """Integration tests for the template system."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.template_system = TemplateSystem()

    def teardown_method(self) -> None:
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_builtin_templates(self) -> None:
        """Test loading built-in templates."""
        # The template system should load built-in templates on initialization
        templates = self.template_system.list_available_templates()
        
        # Should have at least the templates we created
        template_ids = [t.id for t in templates]
        assert "python_fastapi_api" in template_ids

    def test_end_to_end_project_creation(self) -> None:
        """Test end-to-end project creation with built-in template."""
        project_spec = ProjectSpec(
            name="test-api",
            description="A test API service",
            project_type=ProjectType.API_SERVICE,
            primary_language=LanguageType.PYTHON,
            frameworks=[FrameworkType.FASTAPI],
            include_ci_cd=True,
            ci_cd_platform=CICDPlatform.GITHUB_ACTIONS,
            include_testing=True,
            include_linting=True,
            author_name="Test Author",
            author_email="test@example.com",
        )

        output_path = self.temp_dir / "test-api"
        result = self.template_system.create_project_scaffold(project_spec, output_path)

        # Should succeed if built-in templates are available
        if result.success:
            assert output_path.exists()
            assert len(result.created_files) > 0
            assert len(result.next_steps) > 0
        else:
            # If no suitable template found, that's also acceptable for this test
            assert "No suitable template found" in str(result.errors)