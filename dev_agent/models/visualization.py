"""Data models for visualization and diagram generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DiagramType(Enum):
    """Types of diagrams that can be generated."""
    
    ARCHITECTURE = "architecture"
    COMPONENT = "component"
    DEPENDENCY = "dependency"
    DATA_FLOW = "data_flow"
    CLASS = "class"
    SEQUENCE = "sequence"
    MULTI_LANGUAGE = "multi_language"
    PROJECT_OVERVIEW = "project_overview"


class ExportFormat(Enum):
    """Export formats for diagrams."""
    
    MERMAID = "mermaid"
    HTML = "html"
    JSON = "json"
    SVG = "svg"
    PNG = "png"


@dataclass
class DiagramNode:
    """Represents a node in a diagram."""
    
    id: str
    label: str
    node_type: str
    properties: dict[str, Any] = field(default_factory=dict)
    styling: dict[str, str] = field(default_factory=dict)


@dataclass
class DiagramEdge:
    """Represents an edge/connection in a diagram."""
    
    source: str
    target: str
    label: str = ""
    edge_type: str = "default"
    properties: dict[str, Any] = field(default_factory=dict)
    styling: dict[str, str] = field(default_factory=dict)


@dataclass
class DiagramLayout:
    """Layout configuration for a diagram."""
    
    direction: str = "TB"  # Top-Bottom, Left-Right, etc.
    spacing: dict[str, int] = field(default_factory=dict)
    grouping: dict[str, list[str]] = field(default_factory=dict)
    styling: dict[str, dict[str, str]] = field(default_factory=dict)


@dataclass
class FilterCriteria:
    """Criteria for filtering diagram elements."""
    
    max_complexity: float | None = None
    max_dependencies: int | None = None
    min_dependencies: int | None = None
    name_pattern: str | None = None
    component_types: list[str] = field(default_factory=list)
    exclude_patterns: list[str] = field(default_factory=list)
    include_test_coverage: bool = True
    complexity_threshold: float = 5.0


@dataclass
class DiagramMetadata:
    """Metadata for generated diagrams."""
    
    title: str
    description: str = ""
    generated_by: str = "dev-agent-visualization-engine"
    diagram_type: DiagramType = DiagramType.ARCHITECTURE
    creation_timestamp: str = ""
    source_data: dict[str, Any] = field(default_factory=dict)
    filter_applied: FilterCriteria | None = None
    node_count: int = 0
    edge_count: int = 0


@dataclass
class InteractiveDiagram:
    """Interactive diagram with filtering and navigation capabilities."""
    
    base_diagram: str
    metadata: DiagramMetadata
    available_filters: list[FilterCriteria] = field(default_factory=list)
    zoom_levels: dict[str, str] = field(default_factory=dict)
    drill_down_paths: dict[str, str] = field(default_factory=dict)


@dataclass
class DiagramExportOptions:
    """Options for exporting diagrams."""
    
    format: ExportFormat = ExportFormat.MERMAID
    include_metadata: bool = True
    include_styling: bool = True
    output_path: str = ""
    filename_template: str = "{title}_{timestamp}"
    compression: bool = False


@dataclass
class VisualizationConfig:
    """Configuration for the visualization engine."""
    
    default_layout: DiagramLayout = field(default_factory=DiagramLayout)
    color_scheme: dict[str, str] = field(default_factory=dict)
    node_size_mapping: dict[str, dict[str, Any]] = field(default_factory=dict)
    edge_style_mapping: dict[str, dict[str, str]] = field(default_factory=dict)
    complexity_thresholds: dict[str, float] = field(default_factory=dict)
    max_nodes_per_diagram: int = 50
    enable_interactive_features: bool = True


@dataclass
class ComponentVisualization:
    """Visualization data for a component."""
    
    component_id: str
    display_name: str
    component_type: str
    complexity_score: float
    dependency_count: int
    test_coverage: float | None = None
    file_count: int = 0
    line_count: int = 0
    interfaces: list[str] = field(default_factory=list)
    position: dict[str, float] = field(default_factory=dict)


@dataclass
class DependencyVisualization:
    """Visualization data for dependencies."""
    
    source_component: str
    target_component: str
    dependency_type: str
    strength: float = 1.0
    is_circular: bool = False
    path_length: int = 1
    coupling_score: float = 0.0


@dataclass
class ArchitectureVisualization:
    """Complete architecture visualization data."""
    
    components: list[ComponentVisualization]
    dependencies: list[DependencyVisualization]
    layers: list[str] = field(default_factory=list)
    patterns: list[str] = field(default_factory=list)
    entry_points: list[str] = field(default_factory=list)
    technology_stack: list[str] = field(default_factory=list)
    quality_metrics: dict[str, float] = field(default_factory=dict)


@dataclass
class DataFlowVisualization:
    """Visualization data for data flow."""
    
    flow_id: str
    source: str
    target: str
    data_type: str
    flow_direction: str = "unidirectional"
    volume: str = "unknown"  # low, medium, high
    frequency: str = "unknown"  # real-time, batch, on-demand
    transformation: str = ""
    validation_rules: list[str] = field(default_factory=list)


@dataclass
class MultiLanguageVisualization:
    """Visualization data for multi-language projects."""
    
    languages: list[dict[str, Any]]
    cross_language_interactions: list[dict[str, Any]]
    shared_resources: list[dict[str, Any]]
    build_dependencies: list[dict[str, Any]]
    api_boundaries: list[dict[str, Any]]
    configuration_files: list[str] = field(default_factory=list)


@dataclass
class DiagramValidationResult:
    """Result of diagram validation."""
    
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    complexity_score: float = 0.0
    readability_score: float = 0.0


@dataclass
class DiagramTemplate:
    """Template for generating consistent diagrams."""
    
    template_id: str
    name: str
    description: str
    diagram_type: DiagramType
    layout: DiagramLayout
    styling: dict[str, Any] = field(default_factory=dict)
    default_filters: FilterCriteria | None = None
    node_templates: dict[str, dict[str, Any]] = field(default_factory=dict)
    edge_templates: dict[str, dict[str, Any]] = field(default_factory=dict)