#!/usr/bin/env python3
"""
Direct End-to-End Test: Create Login Page in test-app

This test directly invokes the workflow manager to create a login page,
bypassing the interactive CLI to ensure proper testing.

Goal: Create a page with an input form that takes email and password
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()


class DirectLoginPageTest:
    """Direct test for creating a login page."""
    
    def __init__(self):
        self.test_app_path = Path("test-app").absolute()
        self.results = []
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result."""
        status = "✅" if success else "❌"
        self.results.append((test_name, success, details))
        console.print(f"{status} {test_name}")
        if details:
            if success:
                console.print(f"   [dim]{details}[/dim]")
            else:
                console.print(f"   [red]{details}[/red]")
    
    def verify_environment(self) -> bool:
        """Verify required environment variables are set."""
        console.print("\n[bold cyan]🔍 Verifying Environment Configuration[/bold cyan]")
        console.print("=" * 60)
        
        required_vars = [
            "GEMINI_API_KEY",
            "GEMINI_MODEL_NAME", 
            "GEMINI_EMBEDDING_MODEL",
            "PREFERRED_LLM_PROVIDER"
        ]
        
        missing_vars = []
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                missing_vars.append(var)
                self.log_result(f"Environment: {var}", False, "Not set")
            else:
                display_value = value if var != "GEMINI_API_KEY" else f"{value[:10]}...{value[-4:]}"
                self.log_result(f"Environment: {var}", True, f"Set to: {display_value}")
        
        if missing_vars:
            console.print(f"\n[red]❌ Missing required environment variables: {', '.join(missing_vars)}[/red]")
            return False
        
        provider = os.getenv("PREFERRED_LLM_PROVIDER", "").lower()
        if provider != "gemini":
            self.log_result("Provider Check", False, f"Expected 'gemini', got '{provider}'")
            return False
        
        self.log_result("Provider Check", True, "Using Gemini")
        return True
    
    async def run_workflow(self) -> bool:
        """Run the complete workflow to create a login page."""
        console.print("\n[bold cyan]🚀 Running Complete Workflow[/bold cyan]")
        console.print("=" * 60)
        
        try:
            # Import required modules
            from dev_agent.config import ConfigManager
            from dev_agent.workflow.workflow_manager import WorkflowManager
            from dev_agent.cli.enhanced_cli import EnhancedCLI
            from dev_agent.llm import create_embedding_client
            from dev_agent.models.enums import PhaseType
            
            self.log_result("Import modules", True)
            
            # Initialize configuration
            config_manager = ConfigManager()
            config = config_manager.get_config()
            
            # Create embedding client
            provider = config_manager.get_llm_provider()
            cache_dir = self.test_app_path / ".dev_agent" / "embedding_cache"
            embedding_client = create_embedding_client(provider=provider, cache_dir=cache_dir)
            
            self.log_result("Initialize embedding client", True, f"Using {provider.value}")
            
            # Create CLI and workflow manager
            cli = EnhancedCLI()
            workflow_manager = WorkflowManager(cli, embedding_client=embedding_client)
            
            self.log_result("Initialize workflow manager", True)
            
            # Load or create project
            state_file = self.test_app_path / ".dev_agent" / "state.json"
            if state_file.exists():
                console.print("[yellow]Loading existing project state...[/yellow]")
                workflow_manager.resume_project(str(self.test_app_path))
                self.log_result("Load project", True)
            else:
                console.print("[yellow]Creating new project...[/yellow]")
                workflow_manager.start_new_project(str(self.test_app_path))
                self.log_result("Create project", True)
            
            # Feature description
            feature_description = """Create a login page for the Streamlit app with the following requirements:

1. Create a new page called 'Login' (3_Login.py in the pages directory)
2. The page should have:
   - A title "Login" with a lock emoji 🔒
   - An email input field (st.text_input with label "Email")
   - A password input field (st.text_input with type='password' and label "Password")
   - A "Login" button (st.button)
   - Basic validation to check if both fields are filled
   - Success message when login button is clicked with valid inputs
   - Error message if fields are empty
3. Use Streamlit's session state to track login status
4. Follow the same style and structure as existing pages (1_About.py and 2_Contact.py)
5. Add appropriate emojis and styling consistent with the app
6. Include a simple authentication check (for demo purposes, accept any non-empty email/password)

The page should be simple, clean, and follow Streamlit best practices."""
            
            console.print("\n[cyan]📝 Feature Description:[/cyan]")
            console.print(Panel(feature_description[:300] + "...", border_style="cyan"))
            
            # Store feature description in project state
            if workflow_manager.current_project_state:
                workflow_manager.current_project_state.feature_description = feature_description
                workflow_manager.state_manager.save_project_state(workflow_manager.current_project_state)
                self.log_result("Store feature description", True)
            
            # Phase 1: Skip indexing (for speed)
            console.print("\n[bold cyan]Phase 1: Indexing[/bold cyan]")
            console.print("[yellow]Skipping indexing for faster testing...[/yellow]")
            
            if workflow_manager.current_project_state:
                workflow_manager.current_project_state.indexing_complete = True
                workflow_manager.current_project_state.current_phase = PhaseType.SPECIFICATION
                workflow_manager.state_manager.save_project_state(workflow_manager.current_project_state)
                self.log_result("Skip indexing", True, "Marked as complete")
            
            # Phase 2: Generate specification
            console.print("\n[bold cyan]Phase 2: Specification[/bold cyan]")
            console.print("[yellow]Generating specification...[/yellow]")
            
            try:
                success = await workflow_manager.transition_to_phase(PhaseType.SPECIFICATION)
                if success:
                    self.log_result("Generate specification", True)
                    
                    # Display specification preview
                    if workflow_manager.current_project_state and workflow_manager.current_project_state.specification:
                        spec_preview = workflow_manager.current_project_state.specification[:200]
                        console.print(f"\n[dim]Specification preview: {spec_preview}...[/dim]\n")
                else:
                    self.log_result("Generate specification", False, "Transition failed")
                    return False
            except Exception as e:
                self.log_result("Generate specification", False, str(e))
                console.print(f"[red]Error: {e}[/red]")
                return False
            
            # Auto-approve specification
            console.print("[yellow]Auto-approving specification...[/yellow]")
            if workflow_manager.current_project_state:
                workflow_manager.current_project_state.specification_approved = True
                workflow_manager.state_manager.save_project_state(workflow_manager.current_project_state)
                self.log_result("Approve specification", True)
            
            # Phase 3: Generate design
            console.print("\n[bold cyan]Phase 3: Design[/bold cyan]")
            console.print("[yellow]Generating design...[/yellow]")
            
            try:
                success = await workflow_manager.transition_to_phase(PhaseType.DESIGN)
                if success:
                    self.log_result("Generate design", True)
                    
                    # Display design preview
                    if workflow_manager.current_project_state and workflow_manager.current_project_state.design:
                        design_preview = workflow_manager.current_project_state.design[:200]
                        console.print(f"\n[dim]Design preview: {design_preview}...[/dim]\n")
                else:
                    self.log_result("Generate design", False, "Transition failed")
                    return False
            except Exception as e:
                self.log_result("Generate design", False, str(e))
                console.print(f"[red]Error: {e}[/red]")
                return False
            
            # Auto-approve design
            console.print("[yellow]Auto-approving design...[/yellow]")
            if workflow_manager.current_project_state:
                workflow_manager.current_project_state.design_approved = True
                workflow_manager.state_manager.save_project_state(workflow_manager.current_project_state)
                self.log_result("Approve design", True)
            
            # Phase 4: Generate implementation tasks
            console.print("\n[bold cyan]Phase 4: Implementation[/bold cyan]")
            console.print("[yellow]Generating implementation tasks...[/yellow]")
            
            try:
                success = await workflow_manager.transition_to_phase(PhaseType.IMPLEMENTATION)
                if success:
                    self.log_result("Generate tasks", True)
                    
                    # Display tasks preview
                    if workflow_manager.current_project_state and workflow_manager.current_project_state.tasks:
                        tasks_preview = str(workflow_manager.current_project_state.tasks)[:200]
                        console.print(f"\n[dim]Tasks preview: {tasks_preview}...[/dim]\n")
                else:
                    self.log_result("Generate tasks", False, "Transition failed")
                    return False
            except Exception as e:
                self.log_result("Generate tasks", False, str(e))
                console.print(f"[red]Error: {e}[/red]")
                return False
            
            # Display cost summary
            if workflow_manager.cost_tracker:
                console.print("\n[bold cyan]💰 Cost Summary[/bold cyan]")
                report = workflow_manager.cost_tracker.get_report()
                console.print(f"Total operations: {report.operations_count}")
                console.print(f"Total tokens: {report.total_prompt_tokens + report.total_completion_tokens + report.total_embedding_tokens:,}")
                console.print(f"Total cost: ${report.total_cost:.4f}")
                self.log_result("Cost tracking", True, f"${report.total_cost:.4f}")
            
            return True
            
        except Exception as e:
            self.log_result("Workflow execution", False, str(e))
            console.print(f"[red]Error: {e}[/red]")
            import traceback
            traceback.print_exc()
            return False
    
    def verify_generated_files(self) -> bool:
        """Verify that the expected files were generated."""
        console.print("\n[bold cyan]📋 Verifying Generated Files[/bold cyan]")
        console.print("=" * 60)
        
        # Check for state file
        state_file = self.test_app_path / ".dev_agent" / "state.json"
        if not state_file.exists():
            self.log_result("State file", False, "state.json not found")
            return False
        
        self.log_result("State file", True, "state.json exists")
        
        # Read and validate state file
        try:
            with open(state_file) as f:
                state_data = json.load(f)
            
            self.log_result("State JSON valid", True)
            
            # Check current phase
            current_phase = state_data.get("current_phase", "unknown")
            console.print(f"   [dim]Current phase: {current_phase}[/dim]")
            
            # Check for specification
            if state_data.get("specification"):
                self.log_result("Specification generated", True, f"{len(state_data['specification'])} chars")
            else:
                self.log_result("Specification generated", False)
            
            # Check for design
            if state_data.get("design"):
                self.log_result("Design generated", True, f"{len(state_data['design'])} chars")
            else:
                self.log_result("Design generated", False)
            
            # Check for tasks
            if state_data.get("tasks"):
                self.log_result("Tasks generated", True, f"{len(str(state_data['tasks']))} chars")
            else:
                self.log_result("Tasks generated", False)
            
        except Exception as e:
            self.log_result("State JSON valid", False, f"JSON error: {e}")
            return False
        
        # Check for documents directory
        docs_dir = self.test_app_path / ".dev_agent" / "documents"
        if docs_dir.exists():
            self.log_result("Documents directory", True)
            
            # List generated documents
            for doc_file in docs_dir.glob("*.md"):
                size = doc_file.stat().st_size
                self.log_result(f"Document: {doc_file.name}", True, f"{size} bytes")
        else:
            self.log_result("Documents directory", False)
        
        return True
    
    def display_summary(self) -> bool:
        """Display test summary."""
        console.print("\n" + "=" * 60)
        console.print("[bold cyan]📊 Test Results Summary[/bold cyan]")
        console.print("=" * 60)
        
        passed = sum(1 for _, success, _ in self.results if success)
        total = len(self.results)
        
        for test_name, success, details in self.results:
            status = "✅" if success else "❌"
            console.print(f"{status} {test_name}")
            if details and not success:
                console.print(f"   [red]{details}[/red]")
        
        console.print()
        console.print(f"[bold]Results: {passed}/{total} checks passed[/bold]")
        
        if passed == total:
            console.print("\n[bold green]🎉 SUCCESS! All checks passed![/bold green]")
            console.print("[green]The login page workflow completed successfully.[/green]")
            console.print()
            console.print("[cyan]Generated artifacts:[/cyan]")
            console.print("  • Specification document")
            console.print("  • Design document")
            console.print("  • Implementation tasks")
            console.print()
            console.print("[cyan]Next steps:[/cyan]")
            console.print("  1. Review documents in test-app/.dev_agent/documents/")
            console.print("  2. Implement the tasks to create 3_Login.py")
            console.print("  3. Test the login page: [cyan]streamlit run test-app/main.py[/cyan]")
            return True
        else:
            console.print(f"\n[bold yellow]⚠️  {total - passed} checks failed[/bold yellow]")
            return False
    
    async def run_async(self) -> bool:
        """Run the complete test asynchronously."""
        console.print("[bold blue]" + "=" * 60 + "[/bold blue]")
        console.print("[bold blue]🧪 Direct E2E Test: Create Login Page[/bold blue]")
        console.print("[bold blue]" + "=" * 60 + "[/bold blue]")
        console.print()
        console.print("[yellow]Goal: Create a page with an input form that takes email and password[/yellow]")
        console.print("[yellow]Provider: Google Gemini[/yellow]")
        console.print()
        
        # Step 1: Verify environment
        if not self.verify_environment():
            console.print("\n[red]❌ Environment verification failed.[/red]")
            return False
        
        # Step 2: Run workflow
        if not await self.run_workflow():
            console.print("\n[red]❌ Workflow execution failed.[/red]")
        
        # Step 3: Verify generated files
        self.verify_generated_files()
        
        # Step 4: Display summary
        return self.display_summary()
    
    def run(self) -> bool:
        """Run the complete test."""
        return asyncio.run(self.run_async())


def main():
    """Main entry point."""
    tester = DirectLoginPageTest()
    success = tester.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
