#!/usr/bin/env python3
"""
End-to-End Test: Create Login Page in test-app

This test mimics a real user creating a login page with email and password
inputs in the test-app Streamlit application using the Gemini provider.

Goal: Create a page with an input form that takes email and password

Test Flow:
1. Initialize/resume test-app project
2. Provide feature description for login page
3. Skip indexing (or run it if needed)
4. Approve specification
5. Approve design
6. Approve implementation tasks
7. Verify generated files

Environment Variables Required:
- GEMINI_API_KEY
- GEMINI_MODEL_NAME
- GEMINI_EMBEDDING_MODEL
- PREFERRED_LLM_PROVIDER=gemini
"""

import os
import sys
import json
from pathlib import Path
from typer.testing import CliRunner
from rich.console import Console

console = Console()


class LoginPageE2ETest:
    """End-to-end test for creating a login page in test-app."""
    
    def __init__(self):
        self.runner = CliRunner()
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
                # Mask API key for security
                display_value = value if var != "GEMINI_API_KEY" else f"{value[:10]}...{value[-4:]}"
                self.log_result(f"Environment: {var}", True, f"Set to: {display_value}")
        
        if missing_vars:
            console.print(f"\n[red]❌ Missing required environment variables: {', '.join(missing_vars)}[/red]")
            console.print("\n[yellow]Please set them using:[/yellow]")
            console.print("[cyan]export GEMINI_API_KEY=your-api-key[/cyan]")
            console.print("[cyan]export GEMINI_MODEL_NAME=gemini-2.5-flash[/cyan]")
            console.print("[cyan]export GEMINI_EMBEDDING_MODEL=gemini-embedding-001[/cyan]")
            console.print("[cyan]export PREFERRED_LLM_PROVIDER=gemini[/cyan]")
            return False
        
        # Verify provider is set to gemini
        provider = os.getenv("PREFERRED_LLM_PROVIDER", "").lower()
        if provider != "gemini":
            self.log_result("Provider Check", False, f"Expected 'gemini', got '{provider}'")
            return False
        
        self.log_result("Provider Check", True, "Using Gemini")
        return True
    
    def verify_test_app_exists(self) -> bool:
        """Verify test-app directory exists."""
        console.print("\n[bold cyan]📁 Verifying test-app Directory[/bold cyan]")
        console.print("=" * 60)
        
        if not self.test_app_path.exists():
            self.log_result("test-app exists", False, f"Path not found: {self.test_app_path}")
            return False
        
        self.log_result("test-app exists", True, str(self.test_app_path))
        
        # Check for main.py
        main_py = self.test_app_path / "main.py"
        if not main_py.exists():
            self.log_result("main.py exists", False, "Main Streamlit file not found")
            return False
        
        self.log_result("main.py exists", True)
        
        # Check for .dev_agent directory
        dev_agent_dir = self.test_app_path / ".dev_agent"
        if dev_agent_dir.exists():
            self.log_result(".dev_agent exists", True, "Project already initialized")
        else:
            self.log_result(".dev_agent exists", False, "Project not initialized yet")
        
        return True
    
    def test_complete_workflow(self) -> bool:
        """Test the complete workflow to create a login page."""
        console.print("\n[bold cyan]🚀 Starting Complete Workflow Test[/bold cyan]")
        console.print("=" * 60)
        console.print("[yellow]Goal: Create a login page with email and password inputs[/yellow]")
        console.print()
        
        try:
            from dev_agent.cli.main import app
        except ImportError as e:
            self.log_result("Import CLI", False, f"Cannot import CLI: {e}")
            return False
        
        self.log_result("Import CLI", True)
        
        # Feature description for login page
        feature_description = """Create a login page for the Streamlit app with the following requirements:

1. Create a new page called 'Login' (3_Login.py in the pages directory)
2. The page should have:
   - A title "Login"
   - An email input field (text_input with type='default')
   - A password input field (text_input with type='password')
   - A "Login" button
   - Basic validation to check if both fields are filled
   - Success message when login button is clicked with valid inputs
   - Error message if fields are empty
3. Use Streamlit's session state to track login status
4. Follow the same style and structure as existing pages in the app
5. Add appropriate emojis and styling consistent with the app

The page should be simple, clean, and follow Streamlit best practices."""
        
        # Prepare input sequence for the interactive CLI
        # This simulates a user going through the entire workflow
        workflow_input = "\n".join([
            feature_description,  # Feature description when prompted
            "skip",              # Skip indexing (faster for testing, or use "y" to run indexing)
            "y",                 # Approve specification
            "next",              # Move to design phase
            "y",                 # Approve design
            "next",              # Move to implementation phase
            "y",                 # Approve implementation tasks
            "exit"               # Exit CLI
        ])
        
        console.print("[cyan]📝 Feature Description:[/cyan]")
        console.print(f"[dim]{feature_description[:200]}...[/dim]")
        console.print()
        
        console.print("[cyan]🎬 Simulating User Interactions:[/cyan]")
        console.print("  1. Provide feature description")
        console.print("  2. Skip indexing (for speed)")
        console.print("  3. Approve specification")
        console.print("  4. Move to design phase")
        console.print("  5. Approve design")
        console.print("  6. Move to implementation phase")
        console.print("  7. Approve implementation tasks")
        console.print("  8. Exit")
        console.print()
        
        # Check if project is already initialized
        dev_agent_dir = self.test_app_path / ".dev_agent"
        if dev_agent_dir.exists():
            console.print("[yellow]Project already initialized, using 'resume' command[/yellow]")
            command = ['resume', str(self.test_app_path)]
        else:
            console.print("[yellow]Project not initialized, using 'init' command[/yellow]")
            command = ['init', str(self.test_app_path)]
        
        console.print(f"[cyan]Running: dev-agent {' '.join(command)}[/cyan]")
        console.print()
        
        # Run the CLI command with simulated user input
        result = self.runner.invoke(
            app,
            command,
            input=workflow_input,
            catch_exceptions=False  # Let exceptions bubble up for debugging
        )
        
        # Check exit code
        if result.exit_code != 0:
            self.log_result("CLI Execution", False, f"Exit code: {result.exit_code}")
            console.print("\n[red]CLI Output:[/red]")
            console.print(result.stdout)
            if result.stderr:
                console.print("\n[red]CLI Errors:[/red]")
                console.print(result.stderr)
            return False
        
        self.log_result("CLI Execution", True, "Exit code: 0")
        
        # Display CLI output for debugging
        console.print("\n[dim]--- CLI Output (last 1000 chars) ---[/dim]")
        console.print(result.stdout[-1000:] if len(result.stdout) > 1000 else result.stdout)
        console.print("[dim]--- End CLI Output ---[/dim]\n")
        
        return True
    
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
            
        except Exception as e:
            self.log_result("State JSON valid", False, f"JSON error: {e}")
            return False
        
        # Check for documents directory
        docs_dir = self.test_app_path / ".dev_agent" / "documents"
        if not docs_dir.exists():
            self.log_result("Documents directory", False, "documents/ not found")
            return False
        
        self.log_result("Documents directory", True)
        
        # Check for generated documents
        expected_docs = [
            "specification.md",
            "design.md",
            "tasks.md"
        ]
        
        for doc in expected_docs:
            doc_path = docs_dir / doc
            if doc_path.exists():
                size = doc_path.stat().st_size
                self.log_result(f"Document: {doc}", True, f"{size} bytes")
                
                # Display first few lines of each document
                try:
                    with open(doc_path) as f:
                        lines = f.readlines()[:5]
                    console.print(f"   [dim]Preview: {lines[0].strip()[:60]}...[/dim]")
                except Exception:
                    pass
            else:
                self.log_result(f"Document: {doc}", False, "Not found")
        
        # Check for login page file (this might not be generated yet in the workflow)
        login_page = self.test_app_path / "pages" / "3_Login.py"
        if login_page.exists():
            self.log_result("Login page file", True, "3_Login.py created")
            
            # Display preview of login page
            try:
                with open(login_page) as f:
                    content = f.read()
                console.print(f"   [dim]File size: {len(content)} bytes[/dim]")
                
                # Check for key components
                has_email = "email" in content.lower()
                has_password = "password" in content.lower()
                has_streamlit = "import streamlit" in content
                
                if has_email and has_password and has_streamlit:
                    self.log_result("Login page content", True, "Contains email, password, and Streamlit imports")
                else:
                    missing = []
                    if not has_email:
                        missing.append("email")
                    if not has_password:
                        missing.append("password")
                    if not has_streamlit:
                        missing.append("streamlit import")
                    self.log_result("Login page content", False, f"Missing: {', '.join(missing)}")
                
            except Exception as e:
                self.log_result("Login page content", False, f"Error reading file: {e}")
        else:
            self.log_result("Login page file", False, "3_Login.py not created yet (may require implementation phase completion)")
        
        return True
    
    def verify_workflow_state(self) -> bool:
        """Verify the workflow state is correct."""
        console.print("\n[bold cyan]🔄 Verifying Workflow State[/bold cyan]")
        console.print("=" * 60)
        
        state_file = self.test_app_path / ".dev_agent" / "state.json"
        if not state_file.exists():
            self.log_result("State file check", False, "state.json not found")
            return False
        
        try:
            with open(state_file) as f:
                state_data = json.load(f)
            
            # Check key state fields
            project_path = state_data.get("project_path")
            current_phase = state_data.get("current_phase")
            indexing_complete = state_data.get("indexing_complete", False)
            
            self.log_result("Project path", True, project_path)
            self.log_result("Current phase", True, current_phase)
            self.log_result("Indexing complete", indexing_complete, "Skipped" if not indexing_complete else "Completed")
            
            # Check phase history
            phase_history = state_data.get("phase_history", [])
            if phase_history:
                console.print(f"   [dim]Phase history: {' → '.join(phase_history)}[/dim]")
                self.log_result("Phase history", True, f"{len(phase_history)} phases")
            
            # Check for feature description
            feature_desc = state_data.get("feature_description", "")
            if feature_desc:
                preview = feature_desc[:100] + "..." if len(feature_desc) > 100 else feature_desc
                self.log_result("Feature description", True, preview)
            
            return True
            
        except Exception as e:
            self.log_result("State verification", False, f"Error: {e}")
            return False
    
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
            console.print("[cyan]Next steps:[/cyan]")
            console.print("  1. Check the generated documents in test-app/.dev_agent/documents/")
            console.print("  2. Review the specification, design, and tasks")
            console.print("  3. If implementation is complete, check test-app/pages/3_Login.py")
            console.print("  4. Run the Streamlit app: [cyan]streamlit run test-app/main.py[/cyan]")
            return True
        else:
            console.print(f"\n[bold yellow]⚠️  {total - passed} checks failed[/bold yellow]")
            console.print("[yellow]Review the failures above and check the CLI output.[/yellow]")
            return False
    
    def run(self) -> bool:
        """Run the complete end-to-end test."""
        console.print("[bold blue]" + "=" * 60 + "[/bold blue]")
        console.print("[bold blue]🧪 End-to-End Test: Create Login Page in test-app[/bold blue]")
        console.print("[bold blue]" + "=" * 60 + "[/bold blue]")
        console.print()
        console.print("[yellow]Goal: Create a page with an input form that takes email and password[/yellow]")
        console.print("[yellow]Provider: Google Gemini[/yellow]")
        console.print()
        
        # Step 1: Verify environment
        if not self.verify_environment():
            console.print("\n[red]❌ Environment verification failed. Cannot proceed.[/red]")
            return False
        
        # Step 2: Verify test-app exists
        if not self.verify_test_app_exists():
            console.print("\n[red]❌ test-app verification failed. Cannot proceed.[/red]")
            return False
        
        # Step 3: Run complete workflow
        if not self.test_complete_workflow():
            console.print("\n[red]❌ Workflow execution failed.[/red]")
            # Continue to verification to see what was generated
        
        # Step 4: Verify generated files
        self.verify_generated_files()
        
        # Step 5: Verify workflow state
        self.verify_workflow_state()
        
        # Step 6: Display summary
        return self.display_summary()


def main():
    """Main entry point for the test."""
    tester = LoginPageE2ETest()
    success = tester.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
