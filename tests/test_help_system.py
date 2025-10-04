"""Tests for the enhanced help system."""

import pytest
from rich.console import Console

from dev_agent.cli.help_system import HelpSystem, help_system


class TestHelpSystem:
    """Test the help system functionality."""

    def test_help_system_initialization(self):
        """Test that help system initializes correctly."""
        hs = HelpSystem()
        assert hs.commands is not None
        assert hs.workflows is not None
        assert len(hs.commands) > 0
        assert len(hs.workflows) > 0

    def test_command_reference_structure(self):
        """Test that command reference has correct structure."""
        hs = HelpSystem()
        
        # Check that key commands exist
        assert "init" in hs.commands
        assert "resume" in hs.commands
        assert "setup" in hs.commands
        assert "status" in hs.commands
        assert "validate" in hs.commands
        
        # Check command structure
        for cmd_name, cmd_info in hs.commands.items():
            assert "description" in cmd_info
            assert "usage" in cmd_info
            assert isinstance(cmd_info["description"], str)
            assert isinstance(cmd_info["usage"], str)
            
            # Check optional fields
            if "options" in cmd_info:
                assert isinstance(cmd_info["options"], list)
            if "examples" in cmd_info:
                assert isinstance(cmd_info["examples"], list)
            if "notes" in cmd_info:
                assert isinstance(cmd_info["notes"], list)

    def test_workflow_examples_structure(self):
        """Test that workflow examples have correct structure."""
        hs = HelpSystem()
        
        # Check that key workflows exist
        assert "new_project" in hs.workflows
        assert "existing_codebase" in hs.workflows
        assert "quick_start" in hs.workflows
        
        # Check workflow structure
        for wf_name, wf_info in hs.workflows.items():
            assert "title" in wf_info
            assert "description" in wf_info
            assert "steps" in wf_info
            assert "estimated_time" in wf_info
            assert "estimated_cost" in wf_info
            
            assert isinstance(wf_info["steps"], list)
            assert len(wf_info["steps"]) > 0
            
            # Check step structure
            for step in wf_info["steps"]:
                assert isinstance(step, tuple)
                assert len(step) == 2
                assert isinstance(step[0], str)  # description
                assert isinstance(step[1], str)  # command

    def test_show_command_help_valid(self, capsys):
        """Test showing help for a valid command."""
        hs = HelpSystem()
        
        # Should not raise exception
        hs.show_command_help("init")
        
        # Capture output would show help content
        # (Rich output is complex to test, so we just verify no exception)

    def test_show_command_help_invalid(self, capsys):
        """Test showing help for an invalid command."""
        hs = HelpSystem()
        
        # Should not raise exception, but show error
        hs.show_command_help("nonexistent_command")
        
        # Should suggest available commands

    def test_show_all_commands(self):
        """Test showing all commands overview."""
        hs = HelpSystem()
        
        # Should not raise exception
        hs.show_all_commands()

    def test_show_examples_all(self):
        """Test showing all workflow examples."""
        hs = HelpSystem()
        
        # Should not raise exception
        hs.show_examples(None)

    def test_show_examples_specific(self):
        """Test showing specific workflow example."""
        hs = HelpSystem()
        
        # Should not raise exception
        hs.show_examples("new_project")
        hs.show_examples("existing_codebase")
        hs.show_examples("quick_start")

    def test_show_examples_invalid(self):
        """Test showing invalid workflow example."""
        hs = HelpSystem()
        
        # Should not raise exception, but show error
        hs.show_examples("nonexistent_workflow")

    def test_show_quick_reference(self):
        """Test showing quick reference card."""
        hs = HelpSystem()
        
        # Should not raise exception
        hs.show_quick_reference()

    def test_global_help_system_instance(self):
        """Test that global help_system instance exists."""
        assert help_system is not None
        assert isinstance(help_system, HelpSystem)

    def test_command_examples_format(self):
        """Test that command examples are properly formatted."""
        hs = HelpSystem()
        
        for cmd_name, cmd_info in hs.commands.items():
            if "examples" in cmd_info:
                for example in cmd_info["examples"]:
                    assert isinstance(example, tuple)
                    assert len(example) == 2
                    cmd, desc = example  # Command first, then description
                    assert isinstance(desc, str)
                    assert isinstance(cmd, str)
                    # Command should start with dev-agent
                    assert "dev-agent" in cmd.lower() or cmd.startswith("$")

    def test_workflow_cost_estimates(self):
        """Test that workflows include cost estimates."""
        hs = HelpSystem()
        
        for wf_name, wf_info in hs.workflows.items():
            assert "estimated_cost" in wf_info
            cost = wf_info["estimated_cost"]
            assert isinstance(cost, str)
            # Should mention cost or be "Free" or similar
            assert len(cost) > 0

    def test_workflow_time_estimates(self):
        """Test that workflows include time estimates."""
        hs = HelpSystem()
        
        for wf_name, wf_info in hs.workflows.items():
            assert "estimated_time" in wf_info
            time = wf_info["estimated_time"]
            assert isinstance(time, str)
            assert len(time) > 0

    def test_command_usage_patterns(self):
        """Test that command usage follows consistent patterns."""
        hs = HelpSystem()
        
        for cmd_name, cmd_info in hs.commands.items():
            usage = cmd_info["usage"]
            # Usage should start with dev-agent
            assert usage.startswith("dev-agent")
            # Usage should include the command name
            assert cmd_name in usage or "<" in usage  # <command> for groups

    def test_command_options_format(self):
        """Test that command options are properly formatted."""
        hs = HelpSystem()
        
        for cmd_name, cmd_info in hs.commands.items():
            if "options" in cmd_info:
                for option in cmd_info["options"]:
                    assert isinstance(option, tuple)
                    assert len(option) == 2
                    opt_name, opt_desc = option
                    assert isinstance(opt_name, str)
                    assert isinstance(opt_desc, str)
                    # Option should start with - or --
                    assert "-" in opt_name

    def test_command_notes_content(self):
        """Test that command notes provide useful information."""
        hs = HelpSystem()
        
        for cmd_name, cmd_info in hs.commands.items():
            if "notes" in cmd_info:
                notes = cmd_info["notes"]
                assert len(notes) > 0
                for note in notes:
                    assert isinstance(note, str)
                    assert len(note) > 10  # Should be meaningful

    def test_workflow_steps_completeness(self):
        """Test that workflow steps are complete and actionable."""
        hs = HelpSystem()
        
        for wf_name, wf_info in hs.workflows.items():
            steps = wf_info["steps"]
            assert len(steps) >= 3  # Should have multiple steps
            
            # First step should be numbered
            first_step_desc = steps[0][0]
            assert "1" in first_step_desc or first_step_desc.startswith("1")

    def test_help_system_coverage(self):
        """Test that help system covers all major commands."""
        hs = HelpSystem()
        
        # Essential commands that should have help
        essential_commands = [
            "init",
            "resume",
            "setup",
            "status",
            "validate",
            "azure",
        ]
        
        for cmd in essential_commands:
            assert cmd in hs.commands, f"Missing help for essential command: {cmd}"

    def test_workflow_coverage(self):
        """Test that help system covers essential workflows."""
        hs = HelpSystem()
        
        # Essential workflows that should be documented
        essential_workflows = [
            "new_project",
            "existing_codebase",
            "quick_start",
        ]
        
        for wf in essential_workflows:
            assert wf in hs.workflows, f"Missing workflow: {wf}"

    def test_command_descriptions_quality(self):
        """Test that command descriptions are informative."""
        hs = HelpSystem()
        
        for cmd_name, cmd_info in hs.commands.items():
            desc = cmd_info["description"]
            # Description should be meaningful (not too short)
            assert len(desc) > 20
            # Should not end with period (convention)
            assert not desc.endswith(".")

    def test_no_duplicate_commands(self):
        """Test that there are no duplicate command entries."""
        hs = HelpSystem()
        
        command_names = list(hs.commands.keys())
        assert len(command_names) == len(set(command_names))

    def test_no_duplicate_workflows(self):
        """Test that there are no duplicate workflow entries."""
        hs = HelpSystem()
        
        workflow_names = list(hs.workflows.keys())
        assert len(workflow_names) == len(set(workflow_names))


class TestHelpSystemIntegration:
    """Integration tests for help system with CLI."""

    def test_help_system_import(self):
        """Test that help system can be imported."""
        from dev_agent.cli.help_system import help_system
        assert help_system is not None

    def test_help_system_console_output(self):
        """Test that help system produces console output."""
        hs = HelpSystem()
        
        # These should not raise exceptions
        try:
            hs.show_all_commands()
            hs.show_command_help("init")
            hs.show_examples()
            hs.show_quick_reference()
        except Exception as e:
            pytest.fail(f"Help system raised unexpected exception: {e}")
