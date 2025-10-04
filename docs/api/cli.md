# CLI Module API Reference

The CLI module provides the command-line interface for dev-agent, including interactive mode, progress display, feedback system, help system, and enhanced CLI features.

## Overview

The CLI system provides:

- **Command-line Interface**: Typer-based CLI with Rich formatting
- **Interactive Mode**: Chat-based interface for conversational interaction
- **Progress Display**: Real-time progress indicators and status updates
- **Feedback System**: User-friendly messages and guidance
- **Help System**: Contextual help and examples
- **Session Management**: Persistent state across CLI invocations
- **Azure Configuration**: Interactive Azure OpenAI setup

## Main CLI Application

The main CLI application provides all dev-agent commands including workflow operations, utility commands, and configuration management.

::: dev_agent.cli.main
    options:
      show_root_heading: true
      show_source: true
      members_order: source

## Interactive CLI

The interactive CLI provides a chat-based interface for conversational interaction with dev-agent.

::: dev_agent.cli.interactive_cli
    options:
      show_root_heading: true
      show_source: true
      members_order: source

## Session Manager

The session manager handles persistent state across CLI invocations, allowing users to resume work seamlessly.

::: dev_agent.cli.session_manager
    options:
      show_root_heading: true
      show_source: true
      members_order: source

## Progress Display

The progress display system provides real-time feedback during long-running operations with Rich progress bars and spinners.

::: dev_agent.cli.progress_display
    options:
      show_root_heading: true
      show_source: true
      members_order: source

## Feedback System

The feedback system provides user-friendly messages, warnings, errors, and success notifications with actionable guidance.

::: dev_agent.cli.feedback_system
    options:
      show_root_heading: true
      show_source: true
      members_order: source

## Help System

The help system provides contextual help, command examples, and usage guidance throughout the CLI experience.

::: dev_agent.cli.help_system
    options:
      show_root_heading: true
      show_source: true
      members_order: source

## Enhanced CLI

The enhanced CLI module provides improved command implementations with better user experience and error handling.

::: dev_agent.cli.enhanced_cli
    options:
      show_root_heading: true
      show_source: true
      members_order: source

## Azure Configuration

The Azure configuration module provides interactive setup and validation for Azure OpenAI credentials.

::: dev_agent.cli.azure_config
    options:
      show_root_heading: true
      show_source: true
      members_order: source

## Undo/Redo CLI

The undo/redo CLI module provides commands for reverting and reapplying workflow operations.

::: dev_agent.cli.undo_redo_cli
    options:
      show_root_heading: true
      show_source: true
      members_order: source

## Usage Examples

### Basic CLI Usage

```bash
# Initialize a new project
dev-agent init /path/to/project

# Resume an existing project
dev-agent resume /path/to/project

# Run the complete workflow
dev-agent run

# Check project status
dev-agent status

# View cost report
dev-agent cost-report
```

### Interactive Mode

```bash
# Start interactive mode
dev-agent

# In interactive mode:
> help
> status
> run
> exit
```

### Setup and Configuration

```bash
# Run setup wizard
dev-agent setup

# Configure Azure OpenAI
dev-agent azure configure

# Validate configuration
dev-agent validate
```

### Utility Commands

```bash
# Run audit
dev-agent audit

# Scan for cleanup candidates
dev-agent cleanup --scan

# Execute cleanup
dev-agent cleanup --execute

# View help
dev-agent --help
dev-agent <command> --help
```

## CLI Architecture

The CLI is built with:

- **Typer**: Modern CLI framework with type hints
- **Rich**: Beautiful terminal formatting and progress indicators
- **Async Support**: Non-blocking operations for API calls
- **Error Handling**: User-friendly error messages with recovery suggestions
- **State Management**: Persistent session state across invocations

## Best Practices

1. **Use interactive mode** for exploratory work
2. **Check status regularly** to track progress and costs
3. **Review help** for unfamiliar commands
4. **Enable verbose output** when troubleshooting
5. **Use dry-run mode** for destructive operations
6. **Validate configuration** before starting workflows