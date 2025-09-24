"""Visualization engine for generating Mermaid diagrams from codebase analysis."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..models.analysis import (
    ArchitectureInfo,
    ComponentAnalysis,
    DesignAnalysis,
    LanguageInfo,
)
from ..models.visualization import (
    ArchitectureVisualization,
    ComponentVisualization,
    DataFlowVisualization,
    DependencyVisualization,
    DiagramExportOptions,
    DiagramMetadata,
    DiagramTemplate,
    DiagramType,
    DiagramValidationResult,
    ExportFormat,
    FilterCriteria,
    InteractiveDiagram,
    MultiLanguageVisualization,
    VisualizationConfig,
)


class VisualizationEngine:
    """Generates Mermaid diagrams from codebase analysis data."""

    def __init__(self, config: VisualizationConfig | None = None) -> None:
        """Initialize the visualization engine.
        
        Args:
            config: Configuration for visualization behavior
        """
        self.config = config or VisualizationConfig()
        self.diagram_types = {
            "architecture": self._generate_architecture_diagram,
            "component": self._generate_component_diagram,
            "dependency": self._generate_dependency_diagram,
            "data_flow": self._generate_data_flow_diagram,
            "class": self._generate_class_diagram,
            "sequence": self._generate_sequence_diagram,
        }
        self.templates: dict[str, DiagramTemplate] = {}
        self._load_default_templates()

    def _load_default_templates(self) -> None:
        """Load default diagram templates."""
        # Architecture template
        self.templates["default_architecture"] = DiagramTemplate(
            template_id="default_architecture",
            name="Default Architecture",
            description="Standard architecture diagram template",
            diagram_type=DiagramType.ARCHITECTURE,
            layout=self.config.default_layout,
        )
        
        # Component template
        self.templates["default_component"] = DiagramTemplate(
            template_id="default_component",
            name="Default Component",
            description="Standard component diagram template",
            diagram_type=DiagramType.COMPONENT,
            layout=self.config.default_layout,
        )

    def validate_diagram(self, diagram: str) -> DiagramValidationResult:
        """Validate a Mermaid diagram for correctness and readability.
        
        Args:
            diagram: Mermaid diagram string to validate
            
        Returns:
            Validation result with errors, warnings, and suggestions
        """
        errors = []
        warnings = []
        suggestions = []
        
        lines = diagram.split('\n')
        node_count = 0
        edge_count = 0
        
        # Basic syntax validation
        if not lines or not any(line.strip() for line in lines):
            errors.append("Diagram is empty")
            return DiagramValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions
            )
        
        # Check for diagram type declaration
        first_line = lines[0].strip()
        valid_types = ["graph", "flowchart", "classDiagram", "sequenceDiagram"]
        if not any(first_line.startswith(t) for t in valid_types):
            errors.append("Missing or invalid diagram type declaration")
        
        # Count nodes and edges
        for line in lines:
            line = line.strip()
            if '[' in line and ']' in line:
                node_count += 1
            if '-->' in line or '->' in line:
                edge_count += 1
        
        # Check complexity
        if node_count > self.config.max_nodes_per_diagram:
            warnings.append(f"Diagram has {node_count} nodes, consider splitting for better readability")
        elif node_count > 15:  # Warning threshold lower than max
            warnings.append(f"Diagram has {node_count} nodes, consider grouping related components")
        
        if node_count == 0:
            errors.append("No nodes found in diagram")
        
        # Calculate scores
        complexity_score = min(10.0, (node_count + edge_count) / 10.0)
        readability_score = max(0.0, 10.0 - complexity_score)
        
        # Suggestions
        if edge_count > node_count * 2:
            suggestions.append("Consider reducing connections for better clarity")
        
        if node_count > 20:
            suggestions.append("Consider using subgraphs to group related components")
        
        return DiagramValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            complexity_score=complexity_score,
            readability_score=readability_score
        )

    def create_interactive_diagram(
        self, 
        base_diagram: str,
        metadata: DiagramMetadata,
        filter_options: list[FilterCriteria] | None = None
    ) -> InteractiveDiagram:
        """Create an interactive diagram with filtering capabilities.
        
        Args:
            base_diagram: Base Mermaid diagram
            metadata: Diagram metadata
            filter_options: Available filter options
            
        Returns:
            Interactive diagram with filtering capabilities
        """
        return InteractiveDiagram(
            base_diagram=base_diagram,
            metadata=metadata,
            available_filters=filter_options or [],
            zoom_levels={},
            drill_down_paths={}
        )

    def apply_template(
        self, 
        template_id: str, 
        data: Any,
        title: str = ""
    ) -> str:
        """Apply a diagram template to data.
        
        Args:
            template_id: ID of the template to apply
            data: Data to visualize
            title: Title for the diagram
            
        Returns:
            Generated diagram string
        """
        if template_id not in self.templates:
            msg = f"Template '{template_id}' not found"
            raise ValueError(msg)
        
        template = self.templates[template_id]
        
        # Apply template-specific generation logic
        if template.diagram_type == DiagramType.ARCHITECTURE:
            return self._generate_architecture_diagram(data, title or template.name)
        elif template.diagram_type == DiagramType.COMPONENT:
            return self._generate_component_diagram(data, title or template.name)
        else:
            msg = f"Template type {template.diagram_type} not supported"
            raise ValueError(msg)

    def generate_architecture_diagram(
        self, 
        architecture_info: ArchitectureInfo,
        title: str = "System Architecture"
    ) -> str:
        """Generate a Mermaid architecture diagram from architecture analysis.
        
        Args:
            architecture_info: Architecture analysis results
            title: Title for the diagram
            
        Returns:
            Mermaid diagram as string
        """
        return self._generate_architecture_diagram(architecture_info, title)

    def generate_component_diagram(
        self, 
        components: list[ComponentAnalysis],
        title: str = "Component Structure"
    ) -> str:
        """Generate a Mermaid component diagram.
        
        Args:
            components: List of component analyses
            title: Title for the diagram
            
        Returns:
            Mermaid diagram as string
        """
        return self._generate_component_diagram(components, title)

    def generate_dependency_diagram(
        self, 
        dependencies: dict[str, list[str]],
        title: str = "Dependency Graph"
    ) -> str:
        """Generate a Mermaid dependency diagram.
        
        Args:
            dependencies: Dictionary mapping components to their dependencies
            title: Title for the diagram
            
        Returns:
            Mermaid diagram as string
        """
        return self._generate_dependency_diagram(dependencies, title)

    def generate_data_flow_diagram(
        self, 
        data_flow: dict[str, Any],
        title: str = "Data Flow"
    ) -> str:
        """Generate a Mermaid data flow diagram.
        
        Args:
            data_flow: Data flow information
            title: Title for the diagram
            
        Returns:
            Mermaid diagram as string
        """
        return self._generate_data_flow_diagram(data_flow, title)

    def generate_project_overview_diagram(
        self, 
        design_analysis: DesignAnalysis,
        title: str = "Project Overview"
    ) -> str:
        """Generate a comprehensive project overview diagram.
        
        Args:
            design_analysis: Complete design analysis
            title: Title for the diagram
            
        Returns:
            Mermaid diagram as string
        """
        lines = [
            "graph TB",
            f"    %% {title}",
            "",
        ]

        # Add components
        for i, component in enumerate(design_analysis.components):
            component_id = self._sanitize_id(component.name)
            lines.append(f"    {component_id}[{component.name}]")
            
            # Add styling based on complexity
            if component.complexity_score > 5:
                lines.append(f"    {component_id} --> |high complexity| {component_id}")

        # Add relationships between components
        for component in design_analysis.components:
            component_id = self._sanitize_id(component.name)
            for dep in component.dependencies:
                dep_id = self._sanitize_id(dep)
                lines.append(f"    {component_id} --> {dep_id}")

        # Add styling
        lines.extend([
            "",
            "    %% Styling",
            "    classDef default fill:#f9f9f9,stroke:#333,stroke-width:2px",
            "    classDef highComplexity fill:#ffcccc,stroke:#ff0000,stroke-width:2px",
        ])

        return "\n".join(lines)

    def generate_multi_language_diagram(
        self, 
        languages: list[LanguageInfo],
        title: str = "Multi-Language Architecture"
    ) -> str:
        """Generate a diagram showing multi-language project structure.
        
        Args:
            languages: List of language information
            title: Title for the diagram
            
        Returns:
            Mermaid diagram as string
        """
        lines = [
            "graph LR",
            f"    %% {title}",
            "",
        ]

        # Add language nodes
        for lang in languages:
            lang_id = self._sanitize_id(lang.language)
            lines.append(f"    {lang_id}[{lang.language}<br/>{lang.file_count} files]")
            
            # Add framework connections
            for framework in lang.frameworks:
                fw_id = self._sanitize_id(framework)
                lines.append(f"    {fw_id}[{framework}]")
                lines.append(f"    {lang_id} --> {fw_id}")

        # Add styling based on language
        lines.extend([
            "",
            "    %% Styling",
            "    classDef python fill:#3776ab,color:#fff",
            "    classDef javascript fill:#f7df1e,color:#000",
            "    classDef typescript fill:#3178c6,color:#fff",
            "    classDef java fill:#ed8b00,color:#fff",
            "    classDef framework fill:#e1f5fe,stroke:#0277bd",
        ])

        # Apply styling to language nodes
        for lang in languages:
            lang_id = self._sanitize_id(lang.language)
            lang_lower = lang.language.lower()
            if lang_lower in ["python"]:
                lines.append(f"    class {lang_id} python")
            elif lang_lower in ["javascript", "js"]:
                lines.append(f"    class {lang_id} javascript")
            elif lang_lower in ["typescript", "ts"]:
                lines.append(f"    class {lang_id} typescript")
            elif lang_lower in ["java"]:
                lines.append(f"    class {lang_id} java")

        return "\n".join(lines)

    def export_diagram(
        self, 
        diagram: str, 
        output_path: str | Path,
        options: DiagramExportOptions | None = None
    ) -> None:
        """Export diagram to file with advanced options.
        
        Args:
            diagram: Mermaid diagram string
            output_path: Path to save the diagram
            options: Export options including format and metadata
        """
        if options is None:
            options = DiagramExportOptions()
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate filename if template provided and no specific filename given
        if (options.filename_template and "{" in options.filename_template and 
            options.output_path):  # Only use template if output_path is set in options
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = options.filename_template.format(
                title="diagram",
                timestamp=timestamp
            )
            output_path = output_path.parent / f"{filename}.{options.format.value}"
        
        # Ensure the output path has the correct extension
        if not output_path.suffix:
            output_path = output_path.with_suffix(f".{options.format.value}")

        if options.format == ExportFormat.MERMAID:
            content = diagram
            if options.include_metadata:
                metadata_comment = f"<!-- Generated by dev-agent-visualization-engine at {datetime.now().isoformat()} -->\n"
                content = metadata_comment + content
            output_path.write_text(content, encoding="utf-8")
            
        elif options.format == ExportFormat.HTML:
            html_content = self._wrap_in_html(diagram, options.include_styling)
            output_path.write_text(html_content, encoding="utf-8")
            
        elif options.format == ExportFormat.JSON:
            diagram_data = {
                "type": "mermaid",
                "content": diagram,
                "export_options": {
                    "format": options.format.value,
                    "include_metadata": options.include_metadata,
                    "include_styling": options.include_styling,
                }
            }
            if options.include_metadata:
                diagram_data["metadata"] = {
                    "generated_by": "dev-agent-visualization-engine",
                    "timestamp": datetime.now().isoformat(),
                    "format": "mermaid"
                }
            output_path.write_text(json.dumps(diagram_data, indent=2), encoding="utf-8")
        else:
            msg = f"Unsupported format: {options.format}"
            raise ValueError(msg)

    def export_multiple_formats(
        self,
        diagram: str,
        base_path: str | Path,
        formats: list[ExportFormat],
        metadata: DiagramMetadata | None = None
    ) -> dict[ExportFormat, Path]:
        """Export diagram in multiple formats.
        
        Args:
            diagram: Mermaid diagram string
            base_path: Base path for exports (without extension)
            formats: List of formats to export
            metadata: Optional metadata to include
            
        Returns:
            Dictionary mapping formats to their output paths
        """
        base_path = Path(base_path)
        exported_files = {}
        
        for format_type in formats:
            options = DiagramExportOptions(
                format=format_type,
                include_metadata=metadata is not None
            )
            
            output_path = base_path.with_suffix(f".{format_type.value}")
            self.export_diagram(diagram, output_path, options)
            exported_files[format_type] = output_path
        
        return exported_files

    def create_filtered_diagram(
        self, 
        components: list[ComponentAnalysis],
        filter_criteria: FilterCriteria
    ) -> str:
        """Create a filtered diagram based on criteria.
        
        Args:
            components: List of components to visualize
            filter_criteria: Criteria for filtering components
            
        Returns:
            Filtered Mermaid diagram
        """
        filtered_components = []
        
        for component in components:
            include = True
            
            # Apply complexity filter
            if (filter_criteria.max_complexity is not None and 
                component.complexity_score > filter_criteria.max_complexity):
                include = False
            
            # Apply dependency count filters
            if (filter_criteria.max_dependencies is not None and 
                len(component.dependencies) > filter_criteria.max_dependencies):
                include = False
                
            if (filter_criteria.min_dependencies is not None and 
                len(component.dependencies) < filter_criteria.min_dependencies):
                include = False
            
            # Apply name pattern filter
            if filter_criteria.name_pattern:
                pattern = filter_criteria.name_pattern.lower()
                if pattern not in component.name.lower():
                    include = False
            
            # Apply exclude patterns
            for exclude_pattern in filter_criteria.exclude_patterns:
                if exclude_pattern.lower() in component.name.lower():
                    include = False
                    break
            
            # Apply component type filter
            if filter_criteria.component_types:
                # Infer component type from name or purpose
                component_type = self._infer_component_type(component)
                if component_type not in filter_criteria.component_types:
                    include = False
            
            if include:
                filtered_components.append(component)
        
        return self.generate_component_diagram(
            filtered_components, 
            f"Filtered Components ({len(filtered_components)} of {len(components)})"
        )

    def _infer_component_type(self, component: ComponentAnalysis) -> str:
        """Infer component type from its characteristics."""
        name_lower = component.name.lower()
        purpose_lower = component.purpose.lower()
        
        if any(keyword in name_lower for keyword in ["service", "api", "handler"]):
            return "service"
        elif any(keyword in name_lower for keyword in ["model", "entity", "data"]):
            return "model"
        elif any(keyword in name_lower for keyword in ["controller", "view", "ui"]):
            return "controller"
        elif any(keyword in name_lower for keyword in ["util", "helper", "tool"]):
            return "utility"
        elif any(keyword in purpose_lower for keyword in ["test", "testing"]):
            return "test"
        else:
            return "component"

    def _generate_architecture_diagram(
        self, 
        architecture_info: ArchitectureInfo, 
        title: str
    ) -> str:
        """Generate architecture diagram from architecture info."""
        lines = [
            "graph TB",
            f"    %% {title}",
            "",
        ]

        # Add layers
        if architecture_info.layers:
            lines.append("    %% Architectural Layers")
            for i, layer in enumerate(architecture_info.layers):
                layer_id = self._sanitize_id(layer)
                lines.append(f"    {layer_id}[{layer}]")
                if i > 0:
                    prev_layer_id = self._sanitize_id(architecture_info.layers[i-1])
                    lines.append(f"    {prev_layer_id} --> {layer_id}")
            lines.append("")

        # Add components
        if architecture_info.components:
            lines.append("    %% Components")
            for component in architecture_info.components:
                component_id = self._sanitize_id(component)
                lines.append(f"    {component_id}[{component}]")
            lines.append("")

        # Add dependencies
        if architecture_info.dependencies:
            lines.append("    %% Dependencies")
            for component, deps in architecture_info.dependencies.items():
                component_id = self._sanitize_id(component)
                for dep in deps:
                    dep_id = self._sanitize_id(dep)
                    lines.append(f"    {component_id} --> {dep_id}")
            lines.append("")

        # Add entry points
        if architecture_info.entry_points:
            lines.append("    %% Entry Points")
            for entry_point in architecture_info.entry_points:
                entry_id = self._sanitize_id(entry_point)
                lines.append(f"    {entry_id}{{Entry: {entry_point}}}")
            lines.append("")

        # Add styling
        lines.extend([
            "    %% Styling",
            "    classDef layer fill:#e3f2fd,stroke:#1976d2,stroke-width:2px",
            "    classDef component fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px", 
            "    classDef entry fill:#e8f5e8,stroke:#388e3c,stroke-width:2px",
        ])

        return "\n".join(lines)

    def _generate_component_diagram(
        self, 
        components: list[ComponentAnalysis], 
        title: str
    ) -> str:
        """Generate component diagram from component analyses."""
        lines = [
            "graph TD",
            f"    %% {title}",
            "",
        ]

        # Add components
        for component in components:
            component_id = self._sanitize_id(component.name)
            complexity_indicator = "🔴" if component.complexity_score > 5 else "🟢"
            lines.append(f"    {component_id}[{complexity_indicator} {component.name}]")

        lines.append("")

        # Add relationships
        for component in components:
            component_id = self._sanitize_id(component.name)
            for dep in component.dependencies:
                dep_id = self._sanitize_id(dep)
                # Only add relationship if dependency is in our component list
                if any(c.name == dep for c in components):
                    lines.append(f"    {component_id} --> {dep_id}")

        # Add styling
        lines.extend([
            "",
            "    %% Styling",
            "    classDef default fill:#f9f9f9,stroke:#333,stroke-width:2px",
            "    classDef highComplexity fill:#ffebee,stroke:#d32f2f,stroke-width:3px",
            "    classDef lowComplexity fill:#e8f5e8,stroke:#388e3c,stroke-width:2px",
        ])

        # Apply complexity-based styling
        for component in components:
            component_id = self._sanitize_id(component.name)
            if component.complexity_score > 5:
                lines.append(f"    class {component_id} highComplexity")
            else:
                lines.append(f"    class {component_id} lowComplexity")

        return "\n".join(lines)

    def _generate_dependency_diagram(
        self, 
        dependencies: dict[str, list[str]], 
        title: str
    ) -> str:
        """Generate dependency diagram."""
        lines = [
            "graph LR",
            f"    %% {title}",
            "",
        ]

        # Add all nodes first
        all_nodes = set(dependencies.keys())
        for deps in dependencies.values():
            all_nodes.update(deps)

        for node in sorted(all_nodes):
            node_id = self._sanitize_id(node)
            lines.append(f"    {node_id}[{node}]")

        lines.append("")

        # Add dependencies
        for component, deps in dependencies.items():
            component_id = self._sanitize_id(component)
            for dep in deps:
                dep_id = self._sanitize_id(dep)
                lines.append(f"    {component_id} --> {dep_id}")

        # Add styling
        lines.extend([
            "",
            "    %% Styling", 
            "    classDef default fill:#f0f8ff,stroke:#4682b4,stroke-width:2px",
        ])

        return "\n".join(lines)

    def _generate_data_flow_diagram(
        self, 
        data_flow: dict[str, Any], 
        title: str
    ) -> str:
        """Generate data flow diagram."""
        lines = [
            "flowchart TD",
            f"    %% {title}",
            "",
        ]

        # Extract flow information
        if "flows" in data_flow:
            for flow in data_flow["flows"]:
                source_id = self._sanitize_id(flow.get("source", "unknown"))
                target_id = self._sanitize_id(flow.get("target", "unknown"))
                data_type = flow.get("data_type", "data")
                
                lines.append(f"    {source_id}[{flow.get('source', 'Unknown')}]")
                lines.append(f"    {target_id}[{flow.get('target', 'Unknown')}]")
                lines.append(f"    {source_id} -->|{data_type}| {target_id}")

        # Add styling
        lines.extend([
            "",
            "    %% Styling",
            "    classDef default fill:#fff2cc,stroke:#d6b656,stroke-width:2px",
        ])

        return "\n".join(lines)

    def _generate_class_diagram(
        self, 
        classes: list[dict[str, Any]], 
        title: str
    ) -> str:
        """Generate class diagram."""
        lines = [
            "classDiagram",
            f"    %% {title}",
            "",
        ]

        for class_info in classes:
            class_name = class_info.get("name", "Unknown")
            methods = class_info.get("methods", [])
            attributes = class_info.get("attributes", [])

            lines.append(f"    class {class_name} {{")
            
            # Add attributes
            for attr in attributes[:5]:  # Limit to first 5 attributes
                lines.append(f"        +{attr}")
            
            # Add methods
            for method in methods[:5]:  # Limit to first 5 methods
                lines.append(f"        +{method}()")
            
            lines.append("    }")
            lines.append("")

        return "\n".join(lines)

    def _generate_sequence_diagram(
        self, 
        interactions: list[dict[str, Any]], 
        title: str
    ) -> str:
        """Generate sequence diagram."""
        lines = [
            "sequenceDiagram",
            f"    %% {title}",
            "",
        ]

        participants = set()
        for interaction in interactions:
            participants.add(interaction.get("from", "Unknown"))
            participants.add(interaction.get("to", "Unknown"))

        # Add participants
        for participant in sorted(participants):
            lines.append(f"    participant {participant}")

        lines.append("")

        # Add interactions
        for interaction in interactions:
            from_actor = interaction.get("from", "Unknown")
            to_actor = interaction.get("to", "Unknown")
            message = interaction.get("message", "interaction")
            lines.append(f"    {from_actor}->>+{to_actor}: {message}")

        return "\n".join(lines)

    def _sanitize_id(self, name: str) -> str:
        """Sanitize a name to be used as a Mermaid node ID."""
        # Replace spaces and special characters with underscores
        sanitized = "".join(c if c.isalnum() else "_" for c in name)
        # Remove consecutive underscores
        while "__" in sanitized:
            sanitized = sanitized.replace("__", "_")
        # Remove leading/trailing underscores
        sanitized = sanitized.strip("_")
        # Ensure it starts with a letter
        if sanitized and not sanitized[0].isalpha():
            sanitized = f"node_{sanitized}"
        return sanitized or "unknown"

    def _wrap_in_html(self, diagram: str, include_styling: bool = True) -> str:
        """Wrap Mermaid diagram in HTML for standalone viewing.
        
        Args:
            diagram: Mermaid diagram string
            include_styling: Whether to include enhanced styling
            
        Returns:
            Complete HTML document with embedded diagram
        """
        styling = ""
        if include_styling:
            styling = """
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .mermaid {
            background-color: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin: 20px 0;
        }
        .diagram-header {
            text-align: center;
            margin-bottom: 20px;
        }
        .diagram-controls {
            text-align: center;
            margin: 10px 0;
        }
        .control-button {
            background-color: #007acc;
            color: white;
            border: none;
            padding: 8px 16px;
            margin: 0 5px;
            border-radius: 4px;
            cursor: pointer;
        }
        .control-button:hover {
            background-color: #005a9e;
        }
    </style>"""

        interactive_controls = ""
        if include_styling:
            interactive_controls = """
    <div class="diagram-header">
        <h1>Architecture Diagram</h1>
        <p>Generated by dev-agent visualization engine</p>
    </div>
    <div class="diagram-controls">
        <button class="control-button" onclick="zoomIn()">Zoom In</button>
        <button class="control-button" onclick="zoomOut()">Zoom Out</button>
        <button class="control-button" onclick="resetZoom()">Reset</button>
        <button class="control-button" onclick="exportSVG()">Export SVG</button>
    </div>"""

        interactive_script = ""
        if include_styling:
            interactive_script = """
    <script>
        let currentZoom = 1.0;
        
        function zoomIn() {
            currentZoom *= 1.2;
            applyZoom();
        }
        
        function zoomOut() {
            currentZoom /= 1.2;
            applyZoom();
        }
        
        function resetZoom() {
            currentZoom = 1.0;
            applyZoom();
        }
        
        function applyZoom() {
            const diagram = document.querySelector('.mermaid');
            diagram.style.transform = `scale(${currentZoom})`;
            diagram.style.transformOrigin = 'top left';
        }
        
        function exportSVG() {
            const svg = document.querySelector('.mermaid svg');
            if (svg) {
                const serializer = new XMLSerializer();
                const svgString = serializer.serializeToString(svg);
                const blob = new Blob([svgString], {type: 'image/svg+xml'});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'diagram.svg';
                a.click();
                URL.revokeObjectURL(url);
            }
        }
    </script>"""

        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Architecture Diagram</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true
            }}
        }});
    </script>{styling}
</head>
<body>
    {interactive_controls}
    <div class="mermaid">
{diagram}
    </div>
    {interactive_script}
</body>
</html>"""