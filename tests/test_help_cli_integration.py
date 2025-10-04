"""Integration tests for help system with CLI."""

import pytest
from typer.testing import CliRunner

from dev_agent.cli.main import app

runner = CliRunner()


class TestHelpCLIIntegration:
    """Test help system integration with CLI commands."""

    def test_help_command_no_args(self):
        """Test help command without arguments shows all commands."""
        result = runner.invoke(app, ["help"])
        assert result.exit_code == 0
        assert "dev-agent Command Reference" in result.stdout
        assert "Project Management" in result.stdout
        assert "init" in result.stdout
        assert "resume" in result.stdout
        assert "setup" in result.stdout

    def test_help_command_with_init(self):
        """Test help command for init."""
        result = runner.invoke(app, ["help", "init"])
        assert result.exit_code == 0
        assert "Initialize a new dev-agent project" in result.stdout
        assert "Usage:" in result.stdout
        assert "Examples:" in result.stdout
        assert "Notes:" in result.stdout

    def test_help_command_with_resume(self):
        """Test help command for resume."""
        result = runner.invoke(app, ["help", "resume"])
        assert result.exit_code == 0
        assert "Resume an existing dev-agent project" in result.stdout
        assert "Usage:" in result.stdout

    def test_help_command_with_setup(self):
        """Test help command for setup."""
        result = runner.invoke(app, ["help", "setup"])
        assert result.exit_code == 0
        assert "setup" in result.stdout.lower()
        assert "Usage:" in result.stdout

    def test_help_command_with_status(self):
        """Test help command for status."""
        result = runner.invoke(app, ["help", "status"])
        assert result.exit_code == 0
        assert "status" in result.stdout.lower()
        assert "Usage:" in result.stdout

    def test_help_command_with_validate(self):
        """Test help command for validate."""
        result = runner.invoke(app, ["help", "validate"])
        assert result.exit_code == 0
        assert "validate" in result.stdout.lower()
        assert "Usage:" in result.stdout

    def test_help_command_with_azure(self):
        """Test help command for azure."""
        result = runner.invoke(app, ["help", "azure"])
        assert result.exit_code == 0
        assert "Azure OpenAI" in result.stdout
        assert "Subcommands:" in result.stdout
        assert "configure" in result.stdout
        assert "test" in result.stdout

    def test_help_command_with_invalid(self):
        """Test help command with invalid command name."""
        result = runner.invoke(app, ["help", "nonexistent"])
        assert result.exit_code == 0
        assert "Unknown command" in result.stdout
        assert "Available commands:" in result.stdout

    def test_examples_command_no_args(self):
        """Test examples command without arguments shows all workflows."""
        result = runner.invoke(app, ["examples"])
        assert result.exit_code == 0
        assert "dev-agent Workflow Examples" in result.stdout
        assert "New Project Workflow" in result.stdout
        assert "Existing Codebase Workflow" in result.stdout
        assert "Quick Start" in result.stdout

    def test_examples_command_new_project(self):
        """Test examples command for new_project workflow."""
        result = runner.invoke(app, ["examples", "new_project"])
        assert result.exit_code == 0
        assert "New Project Workflow" in result.stdout
        assert "Steps:" in result.stdout
        assert "dev-agent setup" in result.stdout
        assert "Estimated Time:" in result.stdout
        assert "Estimated Cost:" in result.stdout

    def test_examples_command_existing_codebase(self):
        """Test examples command for existing_codebase workflow."""
        result = runner.invoke(app, ["examples", "existing_codebase"])
        assert result.exit_code == 0
        assert "Existing Codebase Workflow" in result.stdout
        assert "Steps:" in result.stdout
        assert "dev-agent init" in result.stdout

    def test_examples_command_quick_start(self):
        """Test examples command for quick_start workflow."""
        result = runner.invoke(app, ["examples", "quick_start"])
        assert result.exit_code == 0
        assert "Quick Start" in result.stdout
        assert "5 minutes" in result.stdout
        assert "Free" in result.stdout

    def test_examples_command_cost_management(self):
        """Test examples command for cost_management workflow."""
        result = runner.invoke(app, ["examples", "cost_management"])
        assert result.exit_code == 0
        assert "Managing Costs" in result.stdout or "Cost" in result.stdout
        assert "dev-agent cost-report" in result.stdout

    def test_examples_command_troubleshooting(self):
        """Test examples command for troubleshooting workflow."""
        result = runner.invoke(app, ["examples", "troubleshooting"])
        assert result.exit_code == 0
        assert "Troubleshooting" in result.stdout
        assert "dev-agent validate" in result.stdout

    def test_examples_command_invalid(self):
        """Test examples command with invalid workflow name."""
        result = runner.invoke(app, ["examples", "nonexistent"])
        assert result.exit_code == 0
        assert "Unknown workflow" in result.stdout
        assert "Available workflows:" in result.stdout

    def test_main_help_flag(self):
        """Test main --help flag shows enhanced help."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "dev-agent" in result.stdout
        assert "Four-Phase Workflow" in result.stdout
        assert "Quick Start" in result.stdout
        assert "Get Help" in result.stdout
        assert "dev-agent help" in result.stdout
        assert "dev-agent examples" in result.stdout

    def test_version_flag(self):
        """Test --version flag shows version."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "dev-agent" in result.stdout
        assert "version" in result.stdout

    def test_help_command_help_flag(self):
        """Test help command with --help flag."""
        result = runner.invoke(app, ["help", "--help"])
        assert result.exit_code == 0
        assert "Display detailed help for commands" in result.stdout
        assert "Examples:" in result.stdout

    def test_examples_command_help_flag(self):
        """Test examples command with --help flag."""
        result = runner.invoke(app, ["examples", "--help"])
        assert result.exit_code == 0
        assert "Display common workflow examples" in result.stdout
        assert "Available workflows:" in result.stdout

    def test_init_command_enhanced_help(self):
        """Test init command has enhanced help text."""
        result = runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0
        assert "Initialize a new dev-agent project" in result.stdout
        assert "Examples:" in result.stdout
        assert "dev-agent init" in result.stdout

    def test_resume_command_enhanced_help(self):
        """Test resume command has enhanced help text."""
        result = runner.invoke(app, ["resume", "--help"])
        assert result.exit_code == 0
        assert "Resume an existing dev-agent project" in result.stdout
        assert "Examples:" in result.stdout
        assert "dev-agent resume" in result.stdout

    def test_help_system_consistency(self):
        """Test that help system is consistent across commands."""
        # Get help for multiple commands
        commands = ["init", "resume", "setup", "status", "validate"]
        
        for cmd in commands:
            result = runner.invoke(app, ["help", cmd])
            assert result.exit_code == 0
            assert "Usage:" in result.stdout
            # Most commands should have examples
            if cmd not in ["interactive"]:
                assert "Examples:" in result.stdout or "Subcommands:" in result.stdout

    def test_examples_all_workflows_accessible(self):
        """Test that all workflows are accessible via examples command."""
        workflows = [
            "new_project",
            "existing_codebase",
            "quick_start",
            "cost_management",
            "troubleshooting",
        ]
        
        for workflow in workflows:
            result = runner.invoke(app, ["examples", workflow])
            assert result.exit_code == 0
            assert "Steps:" in result.stdout
            assert "Estimated Time:" in result.stdout
            assert "Estimated Cost:" in result.stdout

    def test_help_command_shows_categories(self):
        """Test that help command shows command categories."""
        result = runner.invoke(app, ["help"])
        assert result.exit_code == 0
        assert "Project Management:" in result.stdout
        assert "Monitoring:" in result.stdout
        assert "Configuration:" in result.stdout

    def test_examples_command_shows_all_workflows(self):
        """Test that examples command lists all workflows."""
        result = runner.invoke(app, ["examples"])
        assert result.exit_code == 0
        assert "new_project" in result.stdout
        assert "existing_codebase" in result.stdout
        assert "quick_start" in result.stdout
        assert "cost_management" in result.stdout
        assert "troubleshooting" in result.stdout
