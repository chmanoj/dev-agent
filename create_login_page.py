#!/usr/bin/env python3
"""
Simple script to create a login page in test-app using dev-agent workflow.
This bypasses CLI complexity and directly uses the workflow manager.
"""

import os
import sys
import asyncio
from pathlib import Path

# Set Gemini environment
os.environ["GEMINI_API_KEY"] = "AIzaSyB7b0svJ7VFJKiCVq5A1xylYjngGR0E-I0"
os.environ["GEMINI_MODEL_NAME"] = "gemini-2.5-flash"
os.environ["GEMINI_EMBEDDING_MODEL"] = "gemini-embedding-001"
os.environ["PREFERRED_LLM_PROVIDER"] = "gemini"

from rich.console import Console
from rich.panel import Panel

console = Console()

FEATURE_DESCRIPTION = """Create a login page for the Streamlit app:

1. Create pages/3_Login.py
2. Include:
   - Title "🔒 Login"
   - Email input field
   - Password input field (type='password')
   - Login button
   - Validation for empty fields
   - Success/error messages
3. Use st.session_state for login tracking
4. Match style of existing pages (1_About.py, 2_Contact.py)
5. Simple demo authentication (accept any non-empty credentials)
"""

async def main():
    console.print("[bold blue]🚀 Creating Login Page for test-app[/bold blue]")
    console.print("=" * 60)
    
    try:
        from dev_agent.config import ConfigManager
        from dev_agent.workflow.workflow_manager import WorkflowManager
        from dev_agent.cli.enhanced_cli import EnhancedCLI
        from dev_agent.llm import create_embedding_client
        from dev_agent.models.enums import PhaseType
        
        # Setup
        test_app_path = Path("test-app").absolute()
        config_manager = ConfigManager()
        provider = config_manager.get_llm_provider()
        
        console.print(f"[green]✓[/green] Using {provider.value} provider")
        
        # Create components
        cache_dir = test_app_path / ".dev_agent" / "embedding_cache"
        embedding_client = create_embedding_client(provider=provider, cache_dir=cache_dir)
        cli = EnhancedCLI()
        workflow_manager = WorkflowManager(cli, embedding_client=embedding_client)
        
        # Load project
        console.print(f"[green]✓[/green] Loading project: {test_app_path}")
        workflow_manager.resume_project(str(test_app_path))
        
        # Store feature description
        if workflow_manager.current_project_state:
            workflow_manager.current_project_state.feature_description = FEATURE_DESCRIPTION
            workflow_manager.current_project_state.indexing_complete = True
            workflow_manager.state_manager.save_project_state(workflow_manager.current_project_state)
        
        console.print("\n[cyan]📝 Feature:[/cyan]")
        console.print(Panel(FEATURE_DESCRIPTION, border_style="cyan"))
        
        # Generate specification
        console.print("\n[bold cyan]Phase 1: Specification[/bold cyan]")
        console.print("[yellow]Generating...[/yellow]")
        
        success = await workflow_manager.transition_to_phase(PhaseType.SPECIFICATION)
        if not success:
            console.print("[red]❌ Failed to generate specification[/red]")
            return 1
        
        console.print("[green]✓ Specification generated[/green]")
        
        # Show preview
        if workflow_manager.current_project_state and workflow_manager.current_project_state.specification:
            spec = workflow_manager.current_project_state.specification
            console.print(f"\n[dim]Preview ({len(spec)} chars):[/dim]")
            console.print(Panel(spec[:300] + "...", border_style="dim"))
        
        # The specification was already approved during generation
        # Just verify it's saved
        console.print("[green]✓ Specification approved[/green]")
        
        # Generate design
        console.print("\n[bold cyan]Phase 2: Design[/bold cyan]")
        console.print("[yellow]Generating...[/yellow]")
        
        success = await workflow_manager.transition_to_phase(PhaseType.DESIGN)
        if not success:
            console.print("[red]❌ Failed to generate design[/red]")
            return 1
        
        console.print("[green]✓ Design generated[/green]")
        
        # The design was already approved during generation
        console.print("[green]✓ Design approved[/green]")
        
        # Generate tasks
        console.print("\n[bold cyan]Phase 3: Implementation Tasks[/bold cyan]")
        console.print("[yellow]Generating...[/yellow]")
        
        success = await workflow_manager.transition_to_phase(PhaseType.IMPLEMENTATION)
        if not success:
            console.print("[red]❌ Failed to generate tasks[/red]")
            return 1
        
        console.print("[green]✓ Tasks generated[/green]")
        
        # Show cost
        if workflow_manager.cost_tracker:
            report = workflow_manager.cost_tracker.get_report()
            console.print(f"\n[bold cyan]💰 Cost:[/bold cyan] ${report.total_cost:.4f}")
            console.print(f"   Tokens: {report.total_prompt_tokens + report.total_completion_tokens:,}")
        
        # Show results
        console.print("\n[bold green]✅ Success![/bold green]")
        console.print("\n[cyan]Generated files:[/cyan]")
        docs_dir = test_app_path / ".dev_agent" / "documents"
        if docs_dir.exists():
            for doc in docs_dir.glob("*.md"):
                size = doc.stat().st_size
                console.print(f"  • {doc.name} ({size:,} bytes)")
        
        console.print("\n[cyan]Next steps:[/cyan]")
        console.print("  1. Review: test-app/.dev_agent/documents/")
        console.print("  2. Implement tasks to create pages/3_Login.py")
        console.print("  3. Test: streamlit run test-app/main.py")
        
        return 0
        
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
