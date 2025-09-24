"""Tests for template manager."""

import json
import tempfile
from pathlib import Path

import pytest

from dev_agent.config.template_manager import (
    CustomTemplate,
    TemplateManager,
    TemplateMetadata,
    TemplateVersion,
)
from dev_agent.models.enums import FrameworkType, LanguageType, ProjectType
from dev_agent.models.templates import (
    DirectoryTemplate,
    FileTemplate,
    ProjectTemplate,
    TemplateContext,
    ProjectSpec,
)


class TestTemplateMetadata:
    """Test template metadata."""

    def test_metadata_creation(self):
        """Test metadata creation."""
        metadata = TemplateMetadata(
            template_id="test_template",
            name="Test Template",
            description="A test template",
            current_version="1.0.0",
            created_by="test_user",
        )
        
        assert metadata.template_id == "test_template"
        assert metadata.name == "Test Template"
        assert metadata.current_version == "1.0.0"
        assert metadata.usage_count == 0
        assert metadata.rating == 0.0
        assert metadata.is_public is False

    def test_metadata_with_versions(self):
        """Test metadata with version history."""
        version1 = TemplateVersion(
            version="1.0.0",
            created_at="2023-01-01T00:00:00",
            created_by="user1",
            changelog="Initial version",
            is_stable=True,
        )
        
        version2 = TemplateVersion(
            version="1.1.0",
            created_at="2023-02-01T00:00:00",
            created_by="user1",
            changelog="Added new features",
            is_stable=False,
        )
        
        metadata = TemplateMetadata(
            template_id="test_template",
            name="Test Template",
            description="A test template",
            current_version="1.1.0",
            created_by="test_user",
            versions=[version1, version2],
        )
        
        assert len(metadata.versions) == 2
        assert metadata.versions[0].version == "1.0.0"
        assert metadata.versions[1].version == "1.1.0"


class TestCustomTemplate:
    """Test custom template."""

    def test_template_creation(self):
        """Test custom template creation."""
        # Create a simple project template
        file_template = FileTemplate(
            path="main.py",
            content="print('Hello, {{ project_name }}!')",
        )
        
        root_dir = DirectoryTemplate(
            path=".",
            files=[file_template],
        )
        
        project_template = ProjectTemplate(
            id="python_basic",
            name="Basic Python Project",
            description="A basic Python project template",
            supported_languages=[LanguageType.PYTHON],
            project_types=[ProjectType.CLI_TOOL],
            root_directory=root_dir,
        )
        
        metadata = TemplateMetadata(
            template_id="python_basic",
            name="Basic Python Project",
            description="A basic Python project template",
            current_version="1.0.0",
            created_by="test_user",
        )
        
        custom_template = CustomTemplate(
            metadata=metadata,
            template=project_template,
        )
        
        assert custom_template.metadata.template_id == "python_basic"
        assert custom_template.template.name == "Basic Python Project"
        assert LanguageType.PYTHON in custom_template.template.supported_languages


class TestTemplateManager:
    """Test template manager."""

    @pytest.fixture
    def temp_templates_dir(self):
        """Create temporary templates directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def manager(self, temp_templates_dir):
        """Create template manager with temp directory."""
        return TemplateManager(temp_templates_dir)

    @pytest.fixture
    def sample_project_template(self):
        """Create a sample project template."""
        file_template = FileTemplate(
            path="main.py",
            content="#!/usr/bin/env python3\n\ndef main():\n    print('Hello, {{ project_name }}!')\n\nif __name__ == '__main__':\n    main()",
        )
        
        root_dir = DirectoryTemplate(
            path=".",
            files=[file_template],
        )
        
        return ProjectTemplate(
            id="python_cli",
            name="Python CLI Tool",
            description="A Python CLI tool template",
            supported_languages=[LanguageType.PYTHON],
            project_types=[ProjectType.CLI_TOOL],
            root_directory=root_dir,
            template_variables={"project_name": "MyProject"},
        )

    def test_manager_initialization(self, manager):
        """Test manager initialization."""
        assert manager.templates_dir.exists()
        assert manager.custom_templates_dir.exists()
        assert manager.shared_templates_dir.exists()
        assert manager.builtin_templates_dir.exists()

    def test_create_template(self, manager, sample_project_template):
        """Test template creation."""
        template = manager.create_template(
            template_id="python_cli",
            name="Python CLI Tool",
            description="A Python CLI tool template",
            created_by="test_user",
            project_template=sample_project_template,
            category="python",
            tags=["python", "cli", "tool"],
        )
        
        assert template.metadata.template_id == "python_cli"
        assert template.metadata.name == "Python CLI Tool"
        assert template.metadata.category == "python"
        assert "python" in template.metadata.tags
        assert len(template.metadata.versions) == 1
        assert template.metadata.versions[0].version == "1.0.0"

    def test_create_duplicate_template(self, manager, sample_project_template):
        """Test creating duplicate template raises error."""
        manager.create_template(
            template_id="python_cli",
            name="Python CLI Tool",
            description="A Python CLI tool template",
            created_by="test_user",
            project_template=sample_project_template,
        )
        
        with pytest.raises(ValueError, match="already exists"):
            manager.create_template(
                template_id="python_cli",
                name="Another CLI Tool",
                description="Another template",
                created_by="test_user",
                project_template=sample_project_template,
            )

    def test_load_template(self, manager, sample_project_template):
        """Test template loading."""
        # Create template
        original_template = manager.create_template(
            template_id="python_cli",
            name="Python CLI Tool",
            description="A Python CLI tool template",
            created_by="test_user",
            project_template=sample_project_template,
        )
        
        # Clear cache
        manager._template_cache.clear()
        
        # Load template
        loaded_template = manager.load_template("python_cli")
        
        assert loaded_template is not None
        assert loaded_template.metadata.template_id == original_template.metadata.template_id
        assert loaded_template.metadata.name == original_template.metadata.name

    def test_load_nonexistent_template(self, manager):
        """Test loading nonexistent template returns None."""
        template = manager.load_template("nonexistent")
        assert template is None

    def test_save_template(self, manager, sample_project_template):
        """Test template saving."""
        metadata = TemplateMetadata(
            template_id="test_template",
            name="Test Template",
            description="A test template",
            current_version="1.0.0",
            created_by="test_user",
        )
        
        custom_template = CustomTemplate(
            metadata=metadata,
            template=sample_project_template,
        )
        
        success = manager.save_template(custom_template)
        assert success is True
        
        # Verify file exists
        template_file = manager.custom_templates_dir / "test_template.json"
        assert template_file.exists()

    def test_delete_template(self, manager, sample_project_template):
        """Test template deletion."""
        # Create template
        manager.create_template(
            template_id="test_template",
            name="Test Template",
            description="A test template",
            created_by="test_user",
            project_template=sample_project_template,
        )
        
        assert manager.template_exists("test_template")
        
        # Delete template
        success = manager.delete_template("test_template")
        assert success is True
        assert not manager.template_exists("test_template")

    def test_list_templates(self, manager, sample_project_template):
        """Test listing templates."""
        # Create multiple templates
        manager.create_template(
            "python_cli", "Python CLI", "CLI tool", "user1",
            sample_project_template, category="python", tags=["python", "cli"]
        )
        
        web_template = ProjectTemplate(
            id="web_app",
            name="Web Application",
            description="A web app template",
            supported_languages=[LanguageType.JAVASCRIPT],
            project_types=[ProjectType.WEB_APPLICATION],
            root_directory=DirectoryTemplate(path=".", files=[]),
        )
        
        manager.create_template(
            "web_app", "Web App", "Web application", "user2",
            web_template, category="web", tags=["javascript", "web"]
        )
        
        # List all templates
        all_templates = manager.list_templates()
        assert len(all_templates) == 2
        
        # List templates by category
        python_templates = manager.list_templates(category="python")
        assert len(python_templates) == 1
        assert python_templates[0].metadata.template_id == "python_cli"
        
        # List templates by language
        js_templates = manager.list_templates(language=LanguageType.JAVASCRIPT)
        assert len(js_templates) == 1
        assert js_templates[0].metadata.template_id == "web_app"

    def test_validate_template(self, manager, sample_project_template):
        """Test template validation."""
        # Valid template
        metadata = TemplateMetadata(
            template_id="valid_template",
            name="Valid Template",
            description="A valid template",
            current_version="1.0.0",
            created_by="test_user",
        )
        
        valid_template = CustomTemplate(
            metadata=metadata,
            template=sample_project_template,
        )
        
        result = manager.validate_template(valid_template)
        assert result.is_valid is True
        assert len(result.errors) == 0
        
        # Invalid template
        invalid_metadata = TemplateMetadata(
            template_id="",  # Empty ID
            name="",  # Empty name
            description="Invalid template",
            current_version="1.0.0",
            created_by="",  # Empty creator
        )
        
        invalid_template = CustomTemplate(
            metadata=invalid_metadata,
            template=sample_project_template,
        )
        
        result = manager.validate_template(invalid_template)
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_render_template(self, manager, sample_project_template):
        """Test template rendering."""
        # Create template
        template = manager.create_template(
            template_id="python_cli",
            name="Python CLI Tool",
            description="A Python CLI tool template",
            created_by="test_user",
            project_template=sample_project_template,
        )
        
        # Create context
        project_spec = ProjectSpec(
            name="MyAwesomeProject",
            description="An awesome project",
            project_type=ProjectType.CLI_TOOL,
            primary_language=LanguageType.PYTHON,
        )
        
        context = TemplateContext(
            project_spec=project_spec,
            template_variables={"project_name": "MyAwesomeProject"},
            output_path=Path("/tmp/test"),
        )
        
        # Render template
        rendered_files = manager.render_template(template, context)
        
        assert "main.py" in rendered_files
        assert "MyAwesomeProject" in rendered_files["main.py"]

    def test_create_version(self, manager, sample_project_template):
        """Test creating template version."""
        # Create template
        manager.create_template(
            template_id="test_template",
            name="Test Template",
            description="A test template",
            created_by="test_user",
            project_template=sample_project_template,
        )
        
        # Create new version
        success = manager.create_version(
            template_id="test_template",
            new_version="1.1.0",
            changelog="Added new features",
            created_by="test_user",
            is_stable=True,
        )
        
        assert success is True
        
        # Verify version was added
        template = manager.load_template("test_template")
        assert template is not None
        assert template.metadata.current_version == "1.1.0"
        assert len(template.metadata.versions) == 2

    def test_export_import_template(self, manager, sample_project_template, temp_templates_dir):
        """Test template export and import."""
        # Create template
        original_template = manager.create_template(
            template_id="test_template",
            name="Test Template",
            description="A test template",
            created_by="test_user",
            project_template=sample_project_template,
        )
        
        # Export template
        export_path = temp_templates_dir / "exported_template.json"
        success = manager.export_template("test_template", export_path)
        assert success is True
        assert export_path.exists()
        
        # Import template with new ID
        imported_id = manager.import_template(export_path, "imported_template")
        assert imported_id == "imported_template"
        
        # Verify imported template
        imported_template = manager.load_template("imported_template")
        assert imported_template is not None
        assert imported_template.metadata.name == original_template.metadata.name

    def test_share_template(self, manager, sample_project_template):
        """Test template sharing."""
        # Create template
        manager.create_template(
            template_id="test_template",
            name="Test Template",
            description="A test template",
            created_by="test_user",
            project_template=sample_project_template,
        )
        
        # Share template
        success = manager.share_template("test_template")
        assert success is True
        
        # Verify shared template exists
        shared_file = manager.shared_templates_dir / "test_template.json"
        assert shared_file.exists()
        
        # Verify template is marked as public
        template = manager.load_template("test_template")
        assert template.metadata.is_public is True

    def test_template_with_invalid_jinja_syntax(self, manager):
        """Test template validation with invalid Jinja2 syntax."""
        # Create template with invalid Jinja2 syntax
        invalid_file = FileTemplate(
            path="invalid.py",
            content="print('{{ unclosed_variable')",  # Missing closing }}
        )
        
        root_dir = DirectoryTemplate(
            path=".",
            files=[invalid_file],
        )
        
        invalid_project_template = ProjectTemplate(
            id="invalid_template",
            name="Invalid Template",
            description="Template with invalid syntax",
            supported_languages=[LanguageType.PYTHON],
            project_types=[ProjectType.CLI_TOOL],
            root_directory=root_dir,
        )
        
        metadata = TemplateMetadata(
            template_id="invalid_template",
            name="Invalid Template",
            description="Template with invalid syntax",
            current_version="1.0.0",
            created_by="test_user",
        )
        
        invalid_template = CustomTemplate(
            metadata=metadata,
            template=invalid_project_template,
        )
        
        result = manager.validate_template(invalid_template)
        assert result.is_valid is False
        assert any("syntax" in error.lower() for error in result.errors)

    def test_template_serialization(self, manager, sample_project_template):
        """Test template serialization and deserialization."""
        template = manager.create_template(
            template_id="test_template",
            name="Test Template",
            description="A test template",
            created_by="test_user",
            project_template=sample_project_template,
            category="test",
            tags=["test", "sample"],
        )
        
        # Save and reload
        manager.save_template(template)
        loaded_template = manager.load_template("test_template")
        
        assert loaded_template is not None
        assert loaded_template.metadata.category == "test"
        assert "test" in loaded_template.metadata.tags
        assert loaded_template.template.name == "Python CLI Tool"