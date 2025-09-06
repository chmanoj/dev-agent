#!/usr/bin/env python3
"""Manual test script for CLI functionality."""

import os
import tempfile
import subprocess
import sys


def test_cli_help():
    """Test CLI help command."""
    print("Testing CLI help...")
    result = subprocess.run(['uv', 'run', 'dev-agent', '--help'], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ CLI help works")
        print(f"Help output preview: {result.stdout[:100]}...")
    else:
        print("✗ CLI help failed")
        print(f"Error: {result.stderr}")
        return False
    
    return True


def test_cli_init():
    """Test CLI init command."""
    print("\nTesting CLI init...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test init command with timeout to avoid hanging
        result = subprocess.run(['timeout', '5', 'uv', 'run', 'dev-agent', 'init', temp_dir], 
                              capture_output=True, text=True, input='exit\n')
        
        # Check if .dev_agent directory was created
        dev_agent_dir = os.path.join(temp_dir, '.dev_agent')
        if os.path.exists(dev_agent_dir):
            print("✓ CLI init creates project structure")
            
            # Check subdirectories
            if (os.path.exists(os.path.join(dev_agent_dir, 'documents')) and
                os.path.exists(os.path.join(dev_agent_dir, 'index')) and
                os.path.exists(os.path.join(dev_agent_dir, 'session.json'))):
                print("✓ All required directories and files created")
                return True
            else:
                print("✗ Missing required directories or files")
                return False
        else:
            print("✗ CLI init failed to create .dev_agent directory")
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
            return False


def test_package_installation():
    """Test that the package is properly installed."""
    print("Testing package installation...")
    
    # Test import using uv run
    result = subprocess.run(['uv', 'run', 'python', '-c', 
                           'import dev_agent; from dev_agent.cli.main import main; print("Import successful")'], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ dev_agent package can be imported")
        print("✓ CLI main function can be imported")
        return True
    else:
        print(f"✗ Import failed: {result.stderr}")
        return False


def main():
    """Run all manual tests."""
    print("Running manual CLI tests...\n")
    
    tests = [
        test_package_installation,
        test_cli_help,
        test_cli_init,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            print(f"Test {test.__name__} failed!")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All manual tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())