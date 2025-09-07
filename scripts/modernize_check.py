#!/usr/bin/env python3
"""
Script to check if the modernization is working correctly.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"🔍 {description}...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ {description} - OK")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(f"Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"❌ {description} - Command not found: {cmd[0]}")
        return False


def main():
    """Run modernization checks."""
    print("🚀 Checking dev-agent modernization...")
    print("=" * 50)
    
    checks = [
        (["uv", "--version"], "UV installation"),
        (["uv", "sync", "--dry-run"], "UV dependency resolution"),
        (["uv", "run", "ruff", "--version"], "Ruff installation"),
        (["uv", "run", "mypy", "--version"], "MyPy installation"),
        (["uv", "run", "pytest", "--version"], "Pytest installation"),
        (["uv", "run", "dev-agent", "--help"], "CLI application"),
    ]
    
    passed = 0
    total = len(checks)
    
    for cmd, description in checks:
        if run_command(cmd, description):
            passed += 1
    
    print("=" * 50)
    print(f"📊 Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All checks passed! Modernization successful.")
        print("\nNext steps:")
        print("1. Run 'make install-dev' to install all dependencies")
        print("2. Run 'make test' to run the test suite")
        print("3. Run 'make check-all' to run code quality checks")
        print("4. Run 'uv run dev-agent --help' to test the CLI")
        return 0
    else:
        print("⚠️  Some checks failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())