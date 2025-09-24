"""Tests for the visualization engine."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from dev_agent.analysis.visualization_engine import VisualizationEngine
from dev_agent.models.analysis import (
    ArchitectureInfo,
    ArchitecturePattern,
    ComponentAnalysis,
    DesignAnalysis,
    LanguageInfo,
)
from dev_agent.models.visualization import (
    DiagramExportOptions,
    DiagramMetadata,
    DiagramType,
    ExportFormat,
    FilterCriteria,
    VisualizationConfig,
)


class TestVisualizationEngine:
    """Test cases for the VisualizationEngine class."""

    @pytest.fixture
    def engine(self) -> VisualizationEngine:
        """Create a visualization engine for testing."""
        config = VisualizationConfig(
            max_nodes_per_diagram=20,
            enable_interactive_features=True
        )
        return VisualizationEngine(config)

    @pytest.fixture
    def sample_architecture_info(self) -> ArchitectureInfo:
        """Create sample architecture info for testing."""
        return ArchitectureInfo(
            patterns=[
                ArchitecturePattern(
                    name="MVC",
                    description="Model-View-Controller pattern",
                    confidence=0.8,
                    evidence=["Controller classes found", "Model directory exists"],
                    files_involved=["controller.py", "models.py"]
                )
            ],
            layers=["Presentation", "Business", "Data"],
            components=["UserController", "UserService", "UserRepository"],
            dependencies={
                "UserController": ["UserService"],
                "UserService": ["UserRepository"],
                "UserRepository": []
            },
            entry_points=["main.py", "app.py"],
            data_flow={
                "flows": [
                    {
                        "source": "UserController",
                        "target": "UserService",
                        "data_type": "UserRequest"
                    }
                ]
            },
            technology_stack=["Python", "FastAPI", "SQLAlchemy"]
        )

    @pytest.fixture
    def sample_components(self) -> list[ComponentAnalysis]:
        """Create sample components for testing."""
        return [
            ComponentAnalysis(
                name="UserService",
                purpose="Handles user operations",
                interfaces=["IUserService"],
                dependencies=["UserRepository", "EmailService"],
                internal_structure={"classes": 3, "functions": 15},
                complexity_score=4.2
            ),
            ComponentAnalysis(
                name="OrderService",
                purpose="Handles order processing",
                interfaces=["IOrderService"],
                dependencies=["OrderRepository", "PaymentService"],
                internal_structure={"classes": 5, "functions": 25},
                complexity_score=7.8
            ),
            ComponentAnalysis(
                name="EmailService",
                purpose="Sends email notifications",
                interfaces=["IEmailService"],
                dependencies=["SMTPClient"],
                internal_structure={"classes": 2, "functions": 8},
                complexity_score=2.1
            )
        ]

    @pytest.fixture
    def sample_languages(self) -> list[LanguageInfo]:
        """Create sample language info for testing."""
        return [
            LanguageInfo(
                language="Python",
                version="3.11",
                file_count=45,
                line_count=5000,
                frameworks=["FastAPI", "SQLAlchemy"],
                conventions={"naming": "snake_case"},
                quality_score=8.5
            ),
            LanguageInfo(
                language="TypeScript",
                version="4.9",
                file_count=32,
                line_count=3200,
                frameworks=["React", "Express"],
                conventions={"naming": "camelCase"},
                quality_score=7.8
            )
        ]

    def test_initialization(self, engine: VisualizationEngine) -> None:
        """Test engine initialization."""
        assert engine.config is not None
        assert engine.config.max_nodes_per_diagram == 20
        assert engine.config.enable_interactive_features is True
        assert len(engine.templates) > 0
        assert "default_architecture" in engine.templates
        assert "default_component" in engine.templates

    def test_generate_architecture_diagram(
        self, 
        engine: VisualizationEngine,
        sample_architecture_info: ArchitectureInfo
    ) -> None:
        """Test architecture diagram generation."""
        diagram = engine.generate_architecture_diagram(
            sample_architecture_info,
            "Test Architecture"
        )
        
        assert isinstance(diagram, str)
        assert "graph TB" in diagram
        assert "Test Architecture" in diagram
        assert "UserController" in diagram
        assert "UserService" in diagram
        assert "UserRepository" in diagram
        assert "-->" in diagram  # Should have connections

    def test_generate_component_diagram(
        self, 
        engine: VisualizationEngine,
        sample_components: list[ComponentAnalysis]
    ) -> None:
        """Test component diagram generation."""
        diagram = engine.generate_component_diagram(
            sample_components,
            "Test Components"
        )
        
        assert isinstance(diagram, str)
        assert "graph TD" in diagram
        assert "Test Components" in diagram
        assert "UserService" in diagram
        assert "OrderService" in diagram
        assert "EmailService" in diagram
        
        # Check for complexity indicators
        assert "🔴" in diagram or "🟢" in diagram

    def test_generate_dependency_diagram(self, engine: VisualizationEngine) -> None:
        """Test dependency diagram generation."""
        dependencies = {
            "ServiceA": ["ServiceB", "ServiceC"],
            "ServiceB": ["ServiceC"],
            "ServiceC": []
        }
        
        diagram = engine.generate_dependency_diagram(dependencies, "Dependencies")
        
        assert isinstance(diagram, str)
        assert "graph LR" in diagram
        assert "Dependencies" in diagram
        assert "ServiceA" in diagram
        assert "ServiceB" in diagram
        assert "ServiceC" in diagram
        assert "-->" in diagram

    def test_generate_data_flow_diagram(self, engine: VisualizationEngine) -> None:
        """Test data flow diagram generation."""
        data_flow = {
            "flows": [
                {
                    "source": "Frontend",
                    "target": "API",
                    "data_type": "HTTP Request"
                },
                {
                    "source": "API",
                    "target": "Database",
                    "data_type": "SQL Query"
                }
            ]
        }
        
        diagram = engine.generate_data_flow_diagram(data_flow, "Data Flow")
        
        assert isinstance(diagram, str)
        assert "flowchart TD" in diagram
        assert "Data Flow" in diagram
        assert "Frontend" in diagram
        assert "API" in diagram
        assert "Database" in diagram

    def test_generate_multi_language_diagram(
        self, 
        engine: VisualizationEngine,
        sample_languages: list[LanguageInfo]
    ) -> None:
        """Test multi-language diagram generation."""
        diagram = engine.generate_multi_language_diagram(
            sample_languages,
            "Multi-Language Project"
        )
        
        assert isinstance(diagram, str)
        assert "graph LR" in diagram
        assert "Multi-Language Project" in diagram
        assert "Python" in diagram
        assert "TypeScript" in diagram
        assert "FastAPI" in diagram
        assert "React" in diagram

    def test_create_filtered_diagram(
        self, 
        engine: VisualizationEngine,
        sample_components: list[ComponentAnalysis]
    ) -> None:
        """Test filtered diagram creation."""
        filter_criteria = FilterCriteria(
            max_complexity=5.0,
            name_pattern="Service"
        )
        
        diagram = engine.create_filtered_diagram(sample_components, filter_criteria)
        
        assert isinstance(diagram, str)
        assert "UserService" in diagram
        assert "EmailService" in diagram
        # OrderService should be filtered out due to high complexity (7.8 > 5.0)
        assert "OrderService" not in diagram

    def test_validate_diagram_valid(self, engine: VisualizationEngine) -> None:
        """Test diagram validation with valid diagram."""
        valid_diagram = """graph TD
    A[Node A]
    B[Node B]
    A --> B"""
        
        result = engine.validate_diagram(valid_diagram)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.complexity_score > 0
        assert result.readability_score > 0

    def test_validate_diagram_invalid(self, engine: VisualizationEngine) -> None:
        """Test diagram validation with invalid diagram."""
        invalid_diagram = ""
        
        result = engine.validate_diagram(invalid_diagram)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert "empty" in result.errors[0].lower()

    def test_validate_diagram_complex(self, engine: VisualizationEngine) -> None:
        """Test diagram validation with overly complex diagram."""
        # Create a diagram with many nodes
        nodes = [f"    Node{i}[Node {i}]" for i in range(25)]
        complex_diagram = "graph TD\n" + "\n".join(nodes)
        
        result = engine.validate_diagram(complex_diagram)
        
        assert result.is_valid is True  # Still valid, just complex
        assert len(result.warnings) > 0
        assert any("nodes" in warning for warning in result.warnings)

    def test_export_diagram_mermaid(self, engine: VisualizationEngine) -> None:
        """Test exporting diagram in Mermaid format."""
        diagram = "graph TD\n    A[Test]\n    B[Node]\n    A --> B"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.mmd"
            options = DiagramExportOptions(format=ExportFormat.MERMAID)
            
            engine.export_diagram(diagram, output_path, options)
            
            assert output_path.exists()
            content = output_path.read_text()
            assert "graph TD" in content
            assert "A[Test]" in content

    def test_export_diagram_html(self, engine: VisualizationEngine) -> None:
        """Test exporting diagram in HTML format."""
        diagram = "graph TD\n    A[Test]\n    B[Node]\n    A --> B"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.html"
            options = DiagramExportOptions(
                format=ExportFormat.HTML,
                include_styling=True
            )
            
            engine.export_diagram(diagram, output_path, options)
            
            assert output_path.exists()
            content = output_path.read_text()
            assert "<!DOCTYPE html>" in content
            assert "mermaid" in content
            assert "graph TD" in content

    def test_export_diagram_json(self, engine: VisualizationEngine) -> None:
        """Test exporting diagram in JSON format."""
        diagram = "graph TD\n    A[Test]\n    B[Node]\n    A --> B"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.json"
            options = DiagramExportOptions(
                format=ExportFormat.JSON,
                include_metadata=True
            )
            
            engine.export_diagram(diagram, output_path, options)
            
            assert output_path.exists()
            content = json.loads(output_path.read_text())
            assert content["type"] == "mermaid"
            assert "graph TD" in content["content"]
            assert "metadata" in content

    def test_export_multiple_formats(self, engine: VisualizationEngine) -> None:
        """Test exporting diagram in multiple formats."""
        diagram = "graph TD\n    A[Test]\n    B[Node]\n    A --> B"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir) / "test"
            formats = [ExportFormat.MERMAID, ExportFormat.HTML, ExportFormat.JSON]
            
            exported_files = engine.export_multiple_formats(
                diagram, base_path, formats
            )
            
            assert len(exported_files) == 3
            assert ExportFormat.MERMAID in exported_files
            assert ExportFormat.HTML in exported_files
            assert ExportFormat.JSON in exported_files
            
            for file_path in exported_files.values():
                assert file_path.exists()

    def test_apply_template(
        self, 
        engine: VisualizationEngine,
        sample_architecture_info: ArchitectureInfo
    ) -> None:
        """Test applying diagram template."""
        diagram = engine.apply_template(
            "default_architecture",
            sample_architecture_info,
            "Template Test"
        )
        
        assert isinstance(diagram, str)
        assert "Template Test" in diagram
        assert "UserController" in diagram

    def test_apply_template_invalid(self, engine: VisualizationEngine) -> None:
        """Test applying invalid template."""
        with pytest.raises(ValueError, match="Template 'invalid' not found"):
            engine.apply_template("invalid", {}, "Test")

    def test_create_interactive_diagram(self, engine: VisualizationEngine) -> None:
        """Test creating interactive diagram."""
        diagram = "graph TD\n    A[Test]\n    B[Node]\n    A --> B"
        metadata = DiagramMetadata(
            title="Test Diagram",
            diagram_type=DiagramType.ARCHITECTURE
        )
        
        interactive = engine.create_interactive_diagram(diagram, metadata)
        
        assert interactive.base_diagram == diagram
        assert interactive.metadata.title == "Test Diagram"
        assert interactive.metadata.diagram_type == DiagramType.ARCHITECTURE

    def test_infer_component_type(self, engine: VisualizationEngine) -> None:
        """Test component type inference."""
        service_component = ComponentAnalysis(
            name="UserService",
            purpose="Handles user operations",
            interfaces=[],
            dependencies=[],
            internal_structure={},
            complexity_score=1.0
        )
        
        model_component = ComponentAnalysis(
            name="UserModel",
            purpose="User data model",
            interfaces=[],
            dependencies=[],
            internal_structure={},
            complexity_score=1.0
        )
        
        assert engine._infer_component_type(service_component) == "service"
        assert engine._infer_component_type(model_component) == "model"

    def test_sanitize_id(self, engine: VisualizationEngine) -> None:
        """Test ID sanitization for Mermaid compatibility."""
        assert engine._sanitize_id("User Service") == "User_Service"
        assert engine._sanitize_id("user-service") == "user_service"
        assert engine._sanitize_id("123service") == "node_123service"
        assert engine._sanitize_id("") == "unknown"
        assert engine._sanitize_id("valid_name") == "valid_name"

    def test_project_overview_diagram(
        self, 
        engine: VisualizationEngine,
        sample_components: list[ComponentAnalysis]
    ) -> None:
        """Test project overview diagram generation."""
        design_analysis = DesignAnalysis(
            architecture_overview="Test overview",
            components=sample_components,
            data_models=[],
            api_interfaces=[],
            design_patterns=[],
            quality_metrics={},
            technical_debt=[],
            recommendations=[]
        )
        
        diagram = engine.generate_project_overview_diagram(
            design_analysis,
            "Project Overview"
        )
        
        assert isinstance(diagram, str)
        assert "graph TB" in diagram
        assert "Project Overview" in diagram
        assert "UserService" in diagram
        assert "OrderService" in diagram
        assert "EmailService" in diagram

    def test_filter_criteria_all_filters(
        self, 
        engine: VisualizationEngine,
        sample_components: list[ComponentAnalysis]
    ) -> None:
        """Test all filter criteria options."""
        filter_criteria = FilterCriteria(
            max_complexity=10.0,
            min_dependencies=1,
            max_dependencies=3,
            name_pattern="Service",
            component_types=["service"],
            exclude_patterns=["Email"]
        )
        
        diagram = engine.create_filtered_diagram(sample_components, filter_criteria)
        
        # Should include UserService and OrderService, but exclude EmailService
        assert "UserService" in diagram
        assert "OrderService" in diagram
        assert "EmailService" not in diagram  # Excluded by pattern