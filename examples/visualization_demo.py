#!/usr/bin/env python3
"""Demonstration of the visualization engine capabilities."""

from pathlib import Path
from tempfile import TemporaryDirectory

from dev_agent.analysis.visualization_engine import VisualizationEngine
from dev_agent.models.analysis import (
    ArchitectureInfo,
    ArchitecturePattern,
    ComponentAnalysis,
    LanguageInfo,
)
from dev_agent.models.visualization import (
    ExportFormat,
    FilterCriteria,
    VisualizationConfig,
)


def create_sample_architecture() -> ArchitectureInfo:
    """Create sample architecture data for demonstration."""
    return ArchitectureInfo(
        patterns=[
            ArchitecturePattern(
                name="Layered Architecture",
                description="Clear separation of presentation, business, and data layers",
                confidence=0.9,
                evidence=[
                    "Controllers found in presentation layer",
                    "Services found in business layer",
                    "Repositories found in data layer"
                ],
                files_involved=["controllers/", "services/", "repositories/"]
            )
        ],
        layers=["Presentation", "Business Logic", "Data Access", "Database"],
        components=[
            "UserController", "UserService", "UserRepository",
            "OrderController", "OrderService", "OrderRepository",
            "PaymentService", "NotificationService"
        ],
        dependencies={
            "UserController": ["UserService"],
            "UserService": ["UserRepository", "NotificationService"],
            "OrderController": ["OrderService"],
            "OrderService": ["OrderRepository", "PaymentService", "NotificationService"],
            "PaymentService": ["UserRepository"],
            "NotificationService": [],
            "UserRepository": [],
            "OrderRepository": []
        },
        entry_points=["main.py", "app.py", "wsgi.py"],
        data_flow={
            "flows": [
                {
                    "source": "UserController",
                    "target": "UserService",
                    "data_type": "UserRequest"
                }
            ]
        },
        technology_stack=["Python", "FastAPI", "SQLAlchemy", "PostgreSQL", "Redis"]
    )


def demonstrate_visualization_features():
    """Demonstrate visualization engine features."""
    print("🎨 Dev-Agent Visualization Engine Demo")
    print("=" * 50)
    
    # Initialize visualization engine
    config = VisualizationConfig(
        max_nodes_per_diagram=25,
        enable_interactive_features=True
    )
    engine = VisualizationEngine(config)
    
    # Create sample data
    architecture = create_sample_architecture()
    
    print("\n1. 🏗️ Architecture Diagram Generation")
    print("-" * 40)
    
    # Generate architecture diagram
    arch_diagram = engine.generate_architecture_diagram(
        architecture, 
        "E-Commerce Platform Architecture"
    )
    
    print("Generated architecture diagram with:")
    print(f"  • {len(architecture.layers)} layers")
    print(f"  • {len(architecture.components)} components")
    print(f"  • {len(architecture.patterns)} architectural patterns")
    
    # Show sample diagram content
    print(f"\n📋 Sample Architecture Diagram (first 10 lines):")
    print("-" * 50)
    arch_lines = arch_diagram.split('\n')[:10]
    for i, line in enumerate(arch_lines, 1):
        print(f"{i:2d}: {line}")
    
    print(f"\n🎉 Demo completed successfully!")


if __name__ == "__main__":
    demonstrate_visualization_features()