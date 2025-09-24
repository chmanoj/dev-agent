"""Integration tests for visualization engine with codebase analysis."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from dev_agent.analysis.codebase_analyzer import CodebaseAnalyzer
from dev_agent.analysis.visualization_engine import VisualizationEngine
from dev_agent.models.analysis import (
    ArchitectureInfo,
    ArchitecturePattern,
    ComponentAnalysis,
    DesignAnalysis,
)
from dev_agent.models.visualization import (
    DiagramType,
    ExportFormat,
    FilterCriteria,
)


class TestVisualizationIntegration:
    """Integration tests for visualization engine with analysis components."""

    @pytest.fixture
    def mock_indexing_engine(self) -> Mock:
        """Create a mock indexing engine."""
        mock_engine = Mock()
        mock_engine.get_symbol_map.return_value = {"test": "data"}
        mock_engine.ast_index = Mock()
        mock_engine.ast_index.functions = {}
        mock_engine.ast_index.classes = {}
        mock_engine.ast_index.file_metadata = {}
        mock_engine.ast_index.imports = []
        return mock_engine

    @pytest.fixture
    def codebase_analyzer(self, mock_indexing_engine: Mock) -> CodebaseAnalyzer:
        """Create a codebase analyzer with mock data."""
        return CodebaseAnalyzer(mock_indexing_engine)

    @pytest.fixture
    def visualization_engine(self) -> VisualizationEngine:
        """Create a visualization engine."""
        return VisualizationEngine()

    def test_end_to_end_architecture_visualization(
        self,
        codebase_analyzer: CodebaseAnalyzer,
        visualization_engine: VisualizationEngine
    ) -> None:
        """Test end-to-end architecture visualization workflow."""
        # Mock architecture extraction
        mock_architecture = ArchitectureInfo(
            patterns=[
                ArchitecturePattern(
                    name="Layered Architecture",
                    description="Clear separation of layers",
                    confidence=0.9,
                    evidence=["Service layer found", "Repository pattern detected"],
                    files_involved=["service.py", "repository.py"]
                )
            ],
            layers=["Presentation", "Business", "Data"],
            components=["WebController", "BusinessService", "DataRepository"],
            dependencies={
                "WebController": ["BusinessService"],
                "BusinessService": ["DataRepository"],
                "DataRepository": []
            },
            entry_points=["main.py"],
            data_flow={
                "flows": [
                    {
                        "source": "WebController",
                        "target": "BusinessService",
                        "data_type": "Request"
                    }
                ]
            },
            technology_stack=["Python", "FastAPI"]
        )

        with patch.object(
            codebase_analyzer, 
            'extract_architecture_patterns', 
            return_value=mock_architecture
        ):
            # Extract architecture
            architecture = codebase_analyzer.extract_architecture_patterns()
            
            # Generate visualization
            diagram = visualization_engine.generate_architecture_diagram(
                architecture,
                "Integration Test Architecture"
            )
            
            # Verify diagram content
            assert isinstance(diagram, str)
            assert "Integration Test Architecture" in diagram
            assert "WebController" in diagram
            assert "BusinessService" in diagram
            assert "DataRepository" in diagram
            assert "Presentation" in diagram
            assert "Business" in diagram
            assert "Data" in diagram

    def test_design_analysis_to_component_diagram(
        self,
        codebase_analyzer: CodebaseAnalyzer,
        visualization_engine: VisualizationEngine
    ) -> None:
        """Test converting design analysis to component diagram."""
        # Mock design analysis
        mock_design = DesignAnalysis(
            architecture_overview="Microservices architecture with clear boundaries",
            components=[
                ComponentAnalysis(
                    name="UserManagement",
                    purpose="Handles user registration and authentication",
                    interfaces=["IUserService", "IAuthService"],
                    dependencies=["DatabaseService", "EmailService"],
                    internal_structure={"classes": 5, "functions": 20},
                    complexity_score=6.2
                ),
                ComponentAnalysis(
                    name="OrderProcessing",
                    purpose="Manages order lifecycle",
                    interfaces=["IOrderService"],
                    dependencies=["PaymentService", "InventoryService"],
                    internal_structure={"classes": 8, "functions": 35},
                    complexity_score=8.7
                )
            ],
            data_models=[],
            api_interfaces=[],
            design_patterns=["Repository", "Service Layer"],
            quality_metrics={"maintainability": 7.5, "complexity": 6.8},
            technical_debt=["Large classes in OrderProcessing"],
            recommendations=["Split OrderProcessing into smaller components"]
        )

        with patch.object(
            codebase_analyzer,
            'analyze_for_design',
            return_value=mock_design
        ):
            # Get design analysis
            design = codebase_analyzer.analyze_for_design()
            
            # Generate component diagram
            diagram = visualization_engine.generate_component_diagram(
                design.components,
                "System Components"
            )
            
            # Verify diagram
            assert "System Components" in diagram
            assert "UserManagement" in diagram
            assert "OrderProcessing" in diagram
            
            # Check for complexity indicators
            assert "🔴" in diagram or "🟢" in diagram

    def test_filtered_visualization_workflow(
        self,
        visualization_engine: VisualizationEngine
    ) -> None:
        """Test filtered visualization workflow."""
        # Create sample components with varying complexity
        components = [
            ComponentAnalysis(
                name="SimpleUtility",
                purpose="Basic utility functions",
                interfaces=[],
                dependencies=[],
                internal_structure={"functions": 5},
                complexity_score=1.5
            ),
            ComponentAnalysis(
                name="CoreService",
                purpose="Main business logic",
                interfaces=["ICoreService"],
                dependencies=["DatabaseService", "CacheService"],
                internal_structure={"classes": 10, "functions": 50},
                complexity_score=8.2
            ),
            ComponentAnalysis(
                name="HelperService",
                purpose="Supporting functionality",
                interfaces=["IHelper"],
                dependencies=["LoggingService"],
                internal_structure={"classes": 3, "functions": 15},
                complexity_score=3.8
            )
        ]

        # Apply complexity filter
        filter_criteria = FilterCriteria(
            max_complexity=5.0,
            min_dependencies=0
        )

        filtered_diagram = visualization_engine.create_filtered_diagram(
            components, filter_criteria
        )

        # Should include SimpleUtility and HelperService, exclude CoreService
        assert "SimpleUtility" in filtered_diagram
        assert "HelperService" in filtered_diagram
        assert "CoreService" not in filtered_diagram

    def test_multi_format_export_workflow(
        self,
        visualization_engine: VisualizationEngine
    ) -> None:
        """Test exporting diagrams in multiple formats."""
        # Create a simple diagram
        components = [
            ComponentAnalysis(
                name="TestComponent",
                purpose="Test component",
                interfaces=[],
                dependencies=[],
                internal_structure={},
                complexity_score=2.0
            )
        ]

        diagram = visualization_engine.generate_component_diagram(
            components,
            "Export Test"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir) / "test_diagram"
            formats = [ExportFormat.MERMAID, ExportFormat.HTML, ExportFormat.JSON]

            # Export in multiple formats
            exported_files = visualization_engine.export_multiple_formats(
                diagram, base_path, formats
            )

            # Verify all formats were exported
            assert len(exported_files) == 3
            for format_type, file_path in exported_files.items():
                assert file_path.exists()
                assert file_path.suffix == f".{format_type.value}"

                # Verify content based on format
                content = file_path.read_text()
                if format_type == ExportFormat.MERMAID:
                    assert "graph TD" in content
                elif format_type == ExportFormat.HTML:
                    assert "<!DOCTYPE html>" in content
                    assert "mermaid" in content
                elif format_type == ExportFormat.JSON:
                    import json
                    data = json.loads(content)
                    assert data["type"] == "mermaid"

    def test_diagram_validation_workflow(
        self,
        visualization_engine: VisualizationEngine
    ) -> None:
        """Test diagram validation in the workflow."""
        # Generate a diagram
        components = [
            ComponentAnalysis(
                name=f"Component{i}",
                purpose=f"Component {i} purpose",
                interfaces=[],
                dependencies=[f"Component{i-1}"] if i > 0 else [],
                internal_structure={},
                complexity_score=float(i)
            )
            for i in range(25)  # Create many components to test complexity
        ]

        diagram = visualization_engine.generate_component_diagram(
            components,
            "Validation Test"
        )

        # Validate the diagram
        validation_result = visualization_engine.validate_diagram(diagram)

        # Should be valid but have warnings about complexity
        assert validation_result.is_valid is True
        assert len(validation_result.warnings) > 0
        assert any("nodes" in warning for warning in validation_result.warnings)
        assert validation_result.complexity_score > 0
        assert validation_result.readability_score >= 0

    def test_interactive_diagram_creation(
        self,
        visualization_engine: VisualizationEngine
    ) -> None:
        """Test creating interactive diagrams."""
        from dev_agent.models.visualization import DiagramMetadata

        # Create base diagram
        components = [
            ComponentAnalysis(
                name="InteractiveComponent",
                purpose="Test interactive features",
                interfaces=[],
                dependencies=[],
                internal_structure={},
                complexity_score=3.0
            )
        ]

        base_diagram = visualization_engine.generate_component_diagram(
            components,
            "Interactive Test"
        )

        # Create metadata
        metadata = DiagramMetadata(
            title="Interactive Test Diagram",
            description="Test diagram for interactive features",
            diagram_type=DiagramType.COMPONENT
        )

        # Create interactive diagram
        interactive = visualization_engine.create_interactive_diagram(
            base_diagram,
            metadata
        )

        assert interactive.base_diagram == base_diagram
        assert interactive.metadata.title == "Interactive Test Diagram"
        assert interactive.metadata.diagram_type == DiagramType.COMPONENT

    def test_template_application_workflow(
        self,
        visualization_engine: VisualizationEngine
    ) -> None:
        """Test applying templates in the workflow."""
        # Create architecture data
        architecture = ArchitectureInfo(
            patterns=[],
            layers=["UI", "Service", "Data"],
            components=["UIComponent", "ServiceComponent", "DataComponent"],
            dependencies={
                "UIComponent": ["ServiceComponent"],
                "ServiceComponent": ["DataComponent"],
                "DataComponent": []
            },
            entry_points=["app.py"],
            data_flow={},
            technology_stack=["Python"]
        )

        # Apply template
        diagram = visualization_engine.apply_template(
            "default_architecture",
            architecture,
            "Template Application Test"
        )

        assert "Template Application Test" in diagram
        assert "UIComponent" in diagram
        assert "ServiceComponent" in diagram
        assert "DataComponent" in diagram

    def test_error_handling_in_visualization(
        self,
        visualization_engine: VisualizationEngine
    ) -> None:
        """Test error handling in visualization workflows."""
        # Test with invalid template
        with pytest.raises(ValueError, match="Template 'nonexistent' not found"):
            visualization_engine.apply_template("nonexistent", {}, "Test")

        # Test with invalid export format
        from dev_agent.models.visualization import DiagramExportOptions
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.txt"
            
            # This should work with supported formats
            options = DiagramExportOptions(format=ExportFormat.MERMAID)
            visualization_engine.export_diagram(
                "graph TD\nA[Test]", 
                output_path, 
                options
            )
            assert output_path.exists()

    def test_performance_with_large_dataset(
        self,
        visualization_engine: VisualizationEngine
    ) -> None:
        """Test visualization performance with large datasets."""
        # Create a large number of components
        large_component_set = [
            ComponentAnalysis(
                name=f"Component_{i:03d}",
                purpose=f"Component {i} handles specific functionality",
                interfaces=[f"IComponent{i}"],
                dependencies=[f"Component_{j:03d}" for j in range(max(0, i-3), i)],
                internal_structure={"classes": i % 10, "functions": i % 50},
                complexity_score=float(i % 10)
            )
            for i in range(100)
        ]

        # This should complete without errors, even with many components
        diagram = visualization_engine.generate_component_diagram(
            large_component_set[:20],  # Limit to reasonable size
            "Performance Test"
        )

        assert isinstance(diagram, str)
        assert len(diagram) > 0
        assert "Performance Test" in diagram

        # Test filtering on large dataset
        filter_criteria = FilterCriteria(max_complexity=5.0)
        filtered_diagram = visualization_engine.create_filtered_diagram(
            large_component_set, filter_criteria
        )

        assert isinstance(filtered_diagram, str)
        assert len(filtered_diagram) > 0