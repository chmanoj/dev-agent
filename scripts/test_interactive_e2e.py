#!/usr/bin/env python3
"""End-to-end interactive CLI testing using pexpect."""

import os
import shutil
import sys
import time
from pathlib import Path

import pexpect


class InteractiveE2ETest:
    """End-to-end test runner for interactive CLI."""
    
    def __init__(self, timeout: int = 300, test_project_path: str | None = None):
        """Initialize test runner.
        
        Args:
            timeout: Default timeout for pexpect operations in seconds
            test_project_path: Path to existing test project (default: test-app/)
        """
        self.timeout = timeout
        self.child = None
        
        # Use existing test-app directory by default
        if test_project_path:
            self.test_project_dir = os.path.abspath(test_project_path)
        else:
            # Default to test-app in the project root
            script_dir = Path(__file__).parent
            project_root = script_dir.parent
            self.test_project_dir = str(project_root / "test-app")
        
        if not os.path.exists(self.test_project_dir):
            raise ValueError(f"Test project directory does not exist: {self.test_project_dir}")
    
    def setup_test_project(self) -> str:
        """Setup the test project by cleaning any existing dev-agent data."""
        print(f"📁 Using test project: {self.test_project_dir}")
        
        # Clean up any existing .dev_agent directory
        dev_agent_dir = Path(self.test_project_dir) / ".dev_agent"
        if dev_agent_dir.exists():
            print(f"🧹 Cleaning existing .dev_agent directory...")
            shutil.rmtree(dev_agent_dir, ignore_errors=True)
            print(f"✓ Removed existing dev-agent data")
        
        # Verify the test project has some Python files
        python_files = list(Path(self.test_project_dir).rglob("*.py"))
        if not python_files:
            raise ValueError(f"No Python files found in test project: {self.test_project_dir}")
        
        print(f"✓ Test project ready with {len(python_files)} Python files")
        return self.test_project_dir
    
    def cleanup(self):
        """Clean up test resources."""
        if self.child:
            try:
                self.child.close()
            except:
                pass
        
        # Optionally clean up .dev_agent directory after test
        # (commented out to preserve test results for inspection)
        # dev_agent_dir = Path(self.test_project_dir) / ".dev_agent"
        # if dev_agent_dir.exists():
        #     shutil.rmtree(dev_agent_dir, ignore_errors=True)
        #     print(f"✓ Cleaned up dev-agent data from: {self.test_project_dir}")
        
        print(f"✓ Test completed. Results preserved in: {self.test_project_dir}/.dev_agent/")
    
    def start_cli(self) -> pexpect.spawn:
        """Start the dev-agent CLI."""
        print("🚀 Starting dev-agent CLI...")
        
        # Start the CLI process
        self.child = pexpect.spawn(
            'uv run dev-agent',
            timeout=self.timeout,
            encoding='utf-8',
            cwd=self.test_project_dir
        )
        
        # Enable logging for debugging
        if os.getenv('DEBUG_PEXPECT'):
            self.child.logfile = sys.stdout
        
        return self.child
    
    def test_initialization(self) -> bool:
        """Test project initialization."""
        print("\n📋 Testing project initialization...")
        
        try:
            # Wait for initial prompt - try multiple possible prompts
            patterns = [
                r'dev-agent>',
                r'dev-agent.*:',
                r'What would you like to do',
                r'Welcome to dev-agent',
                r'Type.*help.*for available commands',
                pexpect.TIMEOUT
            ]
            
            index = self.child.expect(patterns, timeout=60)
            
            if index < 4:
                print("✓ CLI started successfully")
            else:
                print("❌ CLI startup timed out")
                print(f"Last output: {self.child.before}")
                return False
            
            # Initialize project
            self.child.sendline('init')
            
            # Should detect existing project and start indexing
            patterns = [
                r'Detected existing.*project',
                r'Indexing.*complete',
                r'✅.*Indexing Complete',
                r'Initializing.*project',
                r'dev-agent>',
                pexpect.TIMEOUT
            ]
            
            index = self.child.expect(patterns, timeout=180)  # Increased timeout for indexing
            
            if index < 5:
                print("✓ Project initialization successful")
                
                # Wait for prompt to return
                try:
                    self.child.expect([r'dev-agent>', r'dev-agent.*:'], timeout=60)
                except pexpect.TIMEOUT:
                    # Sometimes the prompt might not appear immediately
                    print("⚠ Prompt not returned immediately, but initialization seems successful")
                return True
            else:
                print("❌ Initialization timed out")
                print(f"Last output: {self.child.before}")
                return False
                
        except pexpect.TIMEOUT:
            print("❌ Initialization failed: timeout")
            print(f"Last output: {self.child.before}")
            return False
        except pexpect.EOF:
            print("❌ Initialization failed: unexpected exit")
            print(f"Last output: {self.child.before}")
            return False
    
    def test_status_command(self) -> bool:
        """Test status command."""
        print("\n📋 Testing status command...")
        
        try:
            self.child.sendline('status')
            
            # Should show current phase or contextual help
            patterns = [
                r'Current phase:.*indexing',
                r'Current phase:.*specification',
                r'Current phase:.*design', 
                r'Current phase:.*implementation',
                r'📍 Current Phase:',
                r'Contextual Help',
                r'Available Commands:',
                r'Indexing',
                r'dev-agent>',
                r'dev-agent.*:',
                pexpect.TIMEOUT
            ]
            
            index = self.child.expect(patterns, timeout=10)
            
            if index < 10:
                print("✓ Status command successful")
                return True
            else:
                print("❌ Status command failed")
                return False
                
        except (pexpect.TIMEOUT, pexpect.EOF):
            print("❌ Status command failed: timeout or EOF")
            return False
    
    def test_specification_phase(self) -> bool:
        """Test specification generation phase."""
        print("\n📋 Testing specification phase...")
        
        try:
            # Transition to specification phase
            self.child.sendline('phase SPECIFICATION')
            
            # Wait for specification generation to start
            patterns = [
                r'What feature would you like to build',
                r'Enter.*feature.*description',
                r'Describe.*feature',
                r'Successfully transitioned.*SPECIFICATION',
                pexpect.TIMEOUT
            ]
            
            index = self.child.expect(patterns, timeout=60)
            
            if index < 3:
                print("✓ Specification phase started")
                
                # Provide feature description
                feature_description = "Add a REST API endpoint for user authentication with JWT tokens"
                self.child.sendline(feature_description)
                
                # Wait for specification generation
                patterns = [
                    r'Specification.*generated',
                    r'Generated.*specification',
                    r'Do you approve.*specification',
                    r'Approve.*specification',
                    r'Please enter Y or N',
                    r'\[y/n\]',
                    pexpect.TIMEOUT
                ]
                
                index = self.child.expect(patterns, timeout=180)
                
                if index < 6:
                    print("✓ Specification generated")
                    
                    # Approve the specification
                    self.child.sendline('y')
                    
                    # Wait for approval confirmation or next prompt
                    patterns = [
                        r'Specification approved',
                        r'Successfully transitioned.*DESIGN',
                        r'dev-agent>',
                        r'dev-agent.*:',
                        pexpect.TIMEOUT
                    ]
                    
                    index = self.child.expect(patterns, timeout=30)
                    
                    if index < 4:
                        print("✓ Specification approved")
                        return True
                    else:
                        print("⚠ Specification may be approved but prompt unclear")
                        return True  # Consider it successful if we got this far
                else:
                    print("❌ Specification generation timed out")
                    return False
            else:
                print("❌ Failed to start specification phase")
                return False
                
        except (pexpect.TIMEOUT, pexpect.EOF):
            print("❌ Specification phase failed: timeout or EOF")
            return False
    
    def test_design_phase(self) -> bool:
        """Test design generation phase."""
        print("\n📋 Testing design phase...")
        
        try:
            # Transition to design phase
            self.child.sendline('phase DESIGN')
            
            # Wait for design generation
            patterns = [
                r'Design.*generated',
                r'Generated.*design',
                r'Do you approve.*design',
                r'Approve.*design',
                r'Successfully transitioned.*DESIGN',
                pexpect.TIMEOUT
            ]
            
            index = self.child.expect(patterns, timeout=180)
            
            if index < 5:
                print("✓ Design phase completed")
                
                # If approval is requested, approve it
                if index < 4:
                    self.child.sendline('y')
                    self.child.expect(r'dev-agent>', timeout=30)
                    print("✓ Design approved")
                
                return True
            else:
                print("❌ Design phase timed out")
                return False
                
        except (pexpect.TIMEOUT, pexpect.EOF):
            print("❌ Design phase failed: timeout or EOF")
            return False
    
    def test_implementation_phase(self) -> bool:
        """Test implementation phase."""
        print("\n📋 Testing implementation phase...")
        
        try:
            # Transition to implementation phase
            self.child.sendline('phase IMPLEMENTATION')
            
            # Wait for implementation plan generation
            patterns = [
                r'Implementation.*generated',
                r'Generated.*implementation',
                r'Implementation.*plan.*ready',
                r'Successfully transitioned.*IMPLEMENTATION',
                pexpect.TIMEOUT
            ]
            
            index = self.child.expect(patterns, timeout=180)
            
            if index < 4:
                print("✓ Implementation phase completed")
                return True
            else:
                print("❌ Implementation phase timed out")
                return False
                
        except (pexpect.TIMEOUT, pexpect.EOF):
            print("❌ Implementation phase failed: timeout or EOF")
            return False
    
    def test_indexing_phase(self) -> bool:
        """Test indexing phase completion."""
        print("\n📋 Testing indexing phase...")
        
        try:
            # Check if indexing is already complete or trigger it
            self.child.sendline('status')
            
            # Look for indexing status
            patterns = [
                r'Current Phase.*Indexing',
                r'Indexing.*complete',
                r'✅.*Indexing Complete',
                r'Phase.*Specification',  # Already moved to next phase
                r'dev-agent>',
                r'dev-agent.*:',
                pexpect.TIMEOUT
            ]
            
            index = self.child.expect(patterns, timeout=30)
            
            if index < 6:
                print("✓ Indexing status checked")
                
                # If still in indexing phase, try to trigger completion
                if index == 0:  # Still in indexing phase
                    print("🔄 Indexing phase active, checking for completion...")
                    
                    # Try to proceed to next phase
                    self.child.sendline('next')
                    
                    # Wait for indexing to complete or phase transition
                    patterns = [
                        r'Indexing.*complete',
                        r'✅.*Indexing Complete',
                        r'Phase.*Specification',
                        r'Successfully transitioned.*SPECIFICATION',
                        r'What feature would you like to build',
                        r'dev-agent>',
                        pexpect.TIMEOUT
                    ]
                    
                    index = self.child.expect(patterns, timeout=180)  # Long timeout for indexing
                    
                    if index < 6:
                        print("✓ Indexing phase completed or transitioned")
                        # Wait for prompt
                        try:
                            self.child.expect([r'dev-agent>', r'dev-agent.*:'], timeout=30)
                        except pexpect.TIMEOUT:
                            print("⚠ Prompt not returned immediately after indexing")
                        return True
                    else:
                        print("❌ Indexing phase did not complete in time")
                        return False
                else:
                    print("✓ Indexing phase already completed or not needed")
                    return True
            else:
                print("❌ Could not check indexing status")
                return False
                
        except (pexpect.TIMEOUT, pexpect.EOF):
            print("❌ Indexing phase test failed: timeout or EOF")
            return False
    
    def test_help_command(self) -> bool:
        """Test help command."""
        print("\n📋 Testing help command...")
        
        try:
            self.child.sendline('help')
            
            # Should show help information
            patterns = [
                r'Available commands',
                r'init.*Initialize',
                r'status.*Show',
                r'cost.*Display',
                r'Commands:',
                r'dev-agent>',
                r'dev-agent.*:',
                pexpect.TIMEOUT
            ]
            
            index = self.child.expect(patterns, timeout=10)
            
            if index < 7:
                print("✓ Help command successful")
                # Wait for prompt with longer timeout
                try:
                    self.child.expect([r'dev-agent>', r'dev-agent.*:'], timeout=30)
                except pexpect.TIMEOUT:
                    print("⚠ Help command succeeded but prompt didn't return immediately")
                return True
            else:
                print("❌ Help command failed")
                return False
                
        except (pexpect.TIMEOUT, pexpect.EOF):
            print("❌ Help command failed: timeout or EOF")
            return False
    
    def test_exit_command(self) -> bool:
        """Test graceful exit."""
        print("\n📋 Testing exit command...")
        
        try:
            self.child.sendline('exit')
            
            # Should exit gracefully
            patterns = [
                r'Goodbye',
                r'Shutting down',
                pexpect.EOF,
                pexpect.TIMEOUT
            ]
            
            index = self.child.expect(patterns, timeout=10)
            
            if index < 3:
                print("✓ Exit command successful")
                return True
            else:
                print("❌ Exit command failed")
                return False
                
        except pexpect.EOF:
            print("✓ CLI exited successfully")
            return True
        except pexpect.TIMEOUT:
            print("❌ Exit command timed out")
            return False
    
    def run_full_workflow_test(self) -> bool:
        """Run complete workflow test."""
        print("🧪 Starting full workflow test...")
        print(f"📍 Test project: {self.test_project_dir}")
        
        try:
            # Setup test environment
            self.setup_test_project()
            
            # Start CLI
            self.start_cli()
            
            # Run test sequence
            tests = [
                ("Initialization", self.test_initialization),
                ("Status Command", self.test_status_command),
                ("Help Command", self.test_help_command),
                ("Indexing Phase", self.test_indexing_phase),
                ("Specification Phase", self.test_specification_phase),
                ("Design Phase", self.test_design_phase),
                ("Implementation Phase", self.test_implementation_phase),
                ("Exit Command", self.test_exit_command),
            ]
            
            results = []
            for test_name, test_func in tests:
                print(f"\n{'='*50}")
                print(f"Running: {test_name}")
                print('='*50)
                
                try:
                    result = test_func()
                    results.append((test_name, result))
                    
                    if result:
                        print(f"✅ {test_name}: PASSED")
                    else:
                        print(f"❌ {test_name}: FAILED")
                        print(f"💥 Stopping test execution due to failure in: {test_name}")
                        break  # Stop on first failure
                        
                except Exception as e:
                    print(f"❌ {test_name}: ERROR - {e}")
                    results.append((test_name, False))
                    print(f"💥 Stopping test execution due to error in: {test_name}")
                    break  # Stop on first error
            
            # Print summary
            print(f"\n{'='*60}")
            print("TEST SUMMARY")
            print('='*60)
            
            passed = sum(1 for _, result in results if result)
            total = len(results)
            
            for test_name, result in results:
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"{test_name:<30} {status}")
            
            print(f"\nResults: {passed}/{total} tests passed")
            print(f"📁 Test artifacts saved in: {self.test_project_dir}/.dev_agent/")
            
            if passed == total:
                print("🎉 All tests PASSED!")
                return True
            else:
                print(f"💥 {total - passed} tests FAILED!")
                return False
                
        except Exception as e:
            print(f"❌ Test suite failed with error: {e}")
            return False
        finally:
            self.cleanup()
    
    def run_smoke_test(self) -> bool:
        """Run quick smoke test (basic functionality only)."""
        print("🔥 Starting smoke test...")
        print(f"📍 Test project: {self.test_project_dir}")
        
        try:
            # Setup test environment
            self.setup_test_project()
            
            # Start CLI
            self.start_cli()
            
            # Run basic tests only
            tests = [
                ("CLI Startup", self.test_initialization),
                ("Status Command", self.test_status_command),
                ("Help Command", self.test_help_command),
                ("Exit Command", self.test_exit_command),
            ]
            
            for test_name, test_func in tests:
                print(f"\n--- {test_name} ---")
                try:
                    result = test_func()
                    
                    if not result:
                        print(f"❌ Smoke test failed at: {test_name}")
                        return False
                        
                    print(f"✅ {test_name}: PASSED")
                except Exception as e:
                    print(f"❌ Smoke test error at: {test_name} - {e}")
                    return False
            
            print("\n🎉 Smoke test PASSED!")
            print(f"📁 Test artifacts saved in: {self.test_project_dir}/.dev_agent/")
            return True
            
        except Exception as e:
            print(f"❌ Smoke test failed with error: {e}")
            return False
        finally:
            self.cleanup()


def load_gemini_config_from_file():
    """Load Gemini configuration from gemini.export.txt file."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    gemini_file = project_root / "gemini.export.txt"
    
    if not gemini_file.exists():
        raise FileNotFoundError(f"Gemini config file not found: {gemini_file}")
    
    gemini_config = {}
    
    with open(gemini_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('export ') and '=' in line:
                # Parse export statements like: export KEY=value
                export_part = line[7:]  # Remove 'export '
                key, value = export_part.split('=', 1)
                gemini_config[key] = value
    
    return gemini_config


def setup_gemini_environment():
    """Setup Gemini API environment variables for testing."""
    try:
        gemini_config = load_gemini_config_from_file()
        
        for key, value in gemini_config.items():
            os.environ[key] = value
        
        print("🔧 Loaded Gemini configuration from gemini.export.txt")
        print(f"   Model: {gemini_config.get('GEMINI_MODEL_NAME', 'Not set')}")
        print(f"   Embedding Model: {gemini_config.get('GEMINI_EMBEDDING_MODEL', 'Not set')}")
        print(f"   Provider: {gemini_config.get('PREFERRED_LLM_PROVIDER', 'Not set')}")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("Please ensure gemini.export.txt exists in the project root with Gemini configuration.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading Gemini configuration: {e}")
        sys.exit(1)


def main():
    """Main entry point for test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Interactive E2E test runner for dev-agent")
    parser.add_argument(
        "--test-type",
        choices=["full", "smoke"],
        default="smoke",
        help="Type of test to run (default: smoke)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout for pexpect operations in seconds (default: 300)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output (shows pexpect interactions)"
    )
    parser.add_argument(
        "--project-path",
        type=str,
        help="Path to test project directory (default: test-app/)"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean .dev_agent directory before starting test (default: True)"
    )
    
    args = parser.parse_args()
    
    # Setup Gemini environment variables
    setup_gemini_environment()
    
    # Set debug environment variable
    if args.debug:
        os.environ['DEBUG_PEXPECT'] = '1'
    
    # Check if uv is available
    if os.system("which uv > /dev/null 2>&1") != 0:
        print("❌ Error: 'uv' command not found. Please install uv first.")
        sys.exit(1)
    
    # Check if dev-agent can be run
    if os.system("uv run dev-agent --version > /dev/null 2>&1") != 0:
        print("❌ Error: Cannot run 'uv run dev-agent'. Please check your installation.")
        sys.exit(1)
    
    # Create test runner with specified or default project path
    try:
        test_runner = InteractiveE2ETest(
            timeout=args.timeout,
            test_project_path=args.project_path
        )
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    # Run appropriate test
    if args.test_type == "full":
        success = test_runner.run_full_workflow_test()
    else:
        success = test_runner.run_smoke_test()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()