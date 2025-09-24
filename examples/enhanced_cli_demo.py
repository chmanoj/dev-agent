#!/usr/bin/env python3
"""Demo script showcasing the enhanced CLI features."""

from __future__ import annotations

import tempfile
from pathlib import Path

from dev_agent.cli.enhanced_cli import EnhancedCLI
from dev_agent.models.enums import PhaseType


def demo_enhanced_cli_features():
    """Demonstrate the enhanced CLI features."""
    print("🚀 Enhanced CLI Demo")
    print("=" * 50)

    # Create a temporary project for demonstration
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create some sample files
        (temp_path / "main.py").write_text("""
def hello_world():
    '''A simple hello world function.'''
    print("Hello, World!")

if __name__ == "__main__":
    hello_world()
""")
        
        (temp_path / "README.md").write_text("""
# Sample Project

This is a sample project for demonstrating the enhanced CLI features.

## Features

- Rich UI components
- Interactive progress tracking
- Syntax-highlighted document previews
- Visual architecture diagrams
- Advanced search and filtering
""")
        
        (temp_path / "config.json").write_text('{"name": "sample", "version": "1.0.0"}')
        
        # Create subdirectory
        src_dir = temp_path / "src"
        src_dir.mkdir()
        (src_dir / "utils.py").write_text("def utility_function(): pass")

        # Initialize enhanced CLI
        cli = EnhancedCLI()
        
        print("\n1. 📁 Project File Tree")
        print("-" * 30)
        cli.document_previewer.show_file_tree(str(temp_path))
        
        print("\n2. 🏗️ Architecture Diagram Generation")
        print("-" * 40)
        sample_analysis = {
            "components": [
                {"name": "Main", "type": "interface"},
                {"name": "Utils", "type": "service"},
                {"name": "Config", "type": "model"},
            ],
            "dependencies": {
                "Main": ["Utils", "Config"],
                "Utils": ["Config"],
            }
        }
        cli.visualization_engine.show_architecture_diagram(sample_analysis)
        
        print("\n3. 🔄 Workflow Diagram")
        print("-" * 25)
        phases = list(PhaseType)
        cli.visualization_engine.show_workflow_diagram(phases)
        
        print("\n4. 🔍 Document Search")
        print("-" * 22)
        readme_content = (temp_path / "README.md").read_text()
        search_results = cli.search_engine.search_in_document(readme_content, "features")
        cli.search_engine.show_search_results(search_results, "features", "README")
        
        print("\n5. 📂 File Filtering")
        print("-" * 20)
        filters = {"extensions": [".py"]}
        filtered_files = cli.search_engine.filter_project_files(str(temp_path), filters)
        cli.search_engine.show_filtered_files(filtered_files, filters, str(temp_path))
        
        print("\n6. 📋 Document Preview")
        print("-" * 24)
        cli.document_previewer.show_document_preview(
            readme_content, "markdown", "README.md Preview"
        )
        
        print("\n7. 📊 Progress Tracking")
        print("-" * 25)
        with cli.progress_manager.progress:
            task_id = cli.progress_manager.start_phase_progress(PhaseType.INDEXING)
            for i in range(0, 101, 25):
                cli.progress_manager.update_progress(i, f"Processing step {i//25 + 1}")
            cli.progress_manager.complete_phase(PhaseType.INDEXING)
        
        print("\n8. 📈 Phase Summary")
        print("-" * 20)
        completed_phases = [PhaseType.INDEXING, PhaseType.SPECIFICATION]
        cli.progress_manager.show_phase_summary(completed_phases)
        
        print("\n✅ Enhanced CLI Demo Complete!")
        print("=" * 50)


if __name__ == "__main__":
    demo_enhanced_cli_features()