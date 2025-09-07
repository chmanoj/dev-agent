# CLI Usage Guide

Complete reference for the dev-agent command-line interface.

## Overview

dev-agent provides a modern CLI built with Typer and Rich, offering both command-based and interactive modes.

## Global Options

Available for all commands:

```bash
--verbose, -v     Enable verbose output
--debug          Enable debug logging  
--config-path    Path to custom configuration file
--help          Show help message
```

## Commands

### `init` - Initialize New Project

Initialize a new dev-agent project in a directory.

```bash
# Initialize in current directory
uv run dev-agent init

# Initialize in specific directory  
uv run dev-agent init /path/to/project

# With verbose output
uv run dev-agent init --verbose /path/to/project
```

**What it does:**
- Creates `.dev_agent/` directory structure
- Starts indexing phase for existing code
- Begins interactive session

**Example output:**
```
✅ Initialized new dev-agent project at /home/user/my-project
🔍 Starting indexing phase...
📊 Analyzed 156 files, 12,847 lines of code
📋 Found 23 functions, 8 classes, 4 modules
✅ Indexing complete (2.3s)

💬 Interactive mode started. Type 'help' for available commands.
dev-agent> 
```

### `resume` - Resume Existing Project

Resume work on an existing dev-agent project.

```bash
# Resume in current directory
uv run dev-agent resume

# Resume specific project
uv run dev-agent resume /path/to/project

# With debug logging
uv run dev-agent resume --debug /path/to/project
```

**What it does:**
- Loads existing project state
- Resumes from last completed phase
- Continues interactive session

**Example output:**
```
✅ Resumed project at /home/user/my-project
📊 Current phase: Design
📋 Last activity: 2 hours ago
🎯 Progress: Specification (✅) → Design (🔄) → Implementation (⏳)

💬 Interactive mode started. Type 'help' for available commands.
dev-agent> 
```

### Interactive Mode (Default)

Start interactive mode directly:

```bash
# Interactive mode in current directory
uv run dev-agent

# Interactive mode in specific directory
uv run dev-agent /path/to/project

# With custom configuration
uv run dev-agent --config-path ~/.dev_agent/custom.toml
```

## Interactive Commands

Once in interactive mode, use these commands:

### Navigation Commands

```bash
help                    # Show available commands
status                  # Show current project status
phase                   # Show current phase information
history                 # Show session history
```

### Phase Commands

```bash
next                    # Proceed to next phase
approve                 # Approve current phase output
reject                  # Reject and request changes
retry                   # Retry current phase
skip                    # Skip current phase (with confirmation)
```

### Information Commands

```bash
show spec              # Display current specification
show design            # Display current design
show tasks             # Display implementation tasks
show progress          # Show detailed progress
```

### Configuration Commands

```bash
config show            # Show current configuration
config set <key> <val> # Set configuration value
config reset           # Reset to defaults
```

### Utility Commands

```bash
export                 # Export project artifacts
save                   # Save current session
load <session>         # Load previous session
clear                  # Clear screen
exit, quit, q          # Exit interactive mode
```

## Configuration Management

### Show Configuration

```bash
uv run dev-agent config show
```

Output:
```yaml
Current dev-agent configuration:
========================================
{
  "logging": {
    "level": "INFO",
    "file": "~/.dev_agent/logs/dev-agent.log"
  },
  "indexing": {
    "max_file_size_mb": 10,
    "exclude_patterns": ["*.pyc", "__pycache__"],
    "include_tests": true
  },
  "generation": {
    "max_context_length": 8192,
    "temperature": 0.1
  }
}
========================================
Config file: ~/.dev_agent/config.toml
```

### Set Configuration Values

```bash
# Set logging level
uv run dev-agent config set logging.level DEBUG

# Set indexing options
uv run dev-agent config set indexing.include_tests false

# Set generation parameters
uv run dev-agent config set generation.temperature 0.2
```

### Reset Configuration

```bash
uv run dev-agent config reset
```

## Examples

### Complete Workflow Example

```bash
# 1. Initialize new project
$ uv run dev-agent init my-web-app
✅ Initialized new dev-agent project
🔍 Starting indexing phase...
📊 Analyzed 45 files, 3,421 lines of code
✅ Indexing complete

# 2. Interactive session starts
dev-agent> status
📊 Project Status:
   Path: /home/user/my-web-app
   Phase: Specification (ready)
   Progress: Indexing (✅) → Specification (⏳) → Design (⏳) → Implementation (⏳)

# 3. Proceed to specification
dev-agent> next
📝 Starting specification generation...
📋 Generated specification with 8 functional requirements
📄 Would you like to review the specification? (y/n): y

[Specification document displayed]

dev-agent> approve
✅ Specification approved and saved

# 4. Continue to design phase
dev-agent> next
🏗️ Starting design phase...
📐 Created technical design with 5 components
📄 Would you like to review the design? (y/n): y

[Design document displayed]

dev-agent> approve
✅ Design approved and saved

# 5. Implementation phase
dev-agent> next
⚡ Starting implementation phase...
🔨 Generated 3 Python modules with tests
📄 Would you like to review the implementation? (y/n): y

[Implementation files displayed]

dev-agent> approve
✅ Implementation complete!
🎉 All phases completed successfully!

dev-agent> exit
```

### Resume Existing Project

```bash
$ uv run dev-agent resume ~/projects/api-service
✅ Resumed project at /home/user/projects/api-service
📊 Current phase: Implementation
📋 Last activity: 1 day ago

dev-agent> status
📊 Project Status:
   Phase: Implementation (in progress)
   Tasks: 3 completed, 2 remaining
   Progress: 60%

dev-agent> show tasks
📋 Implementation Tasks:
   ✅ Create user authentication module
   ✅ Implement JWT token handling  
   ✅ Add password hashing utilities
   🔄 Create user profile endpoints
   ⏳ Add admin dashboard views

dev-agent> next
🔨 Continuing implementation...
```

### Configuration Examples

```bash
# Enable debug logging
uv run dev-agent config set logging.level DEBUG

# Exclude additional file patterns
uv run dev-agent config set indexing.exclude_patterns '["*.pyc", "*.log", "node_modules"]'

# Adjust generation settings
uv run dev-agent config set generation.max_context_length 16384
uv run dev-agent config set generation.temperature 0.05

# Show updated configuration
uv run dev-agent config show
```

## Tips and Best Practices

### Efficient Workflow

1. **Use verbose mode** for debugging: `--verbose`
2. **Review each phase** before approving
3. **Save sessions** regularly in long workflows
4. **Use specific paths** to avoid confusion

### Keyboard Shortcuts

In interactive mode:
- `Ctrl+C`: Cancel current operation
- `Ctrl+D`: Exit interactive mode
- `Tab`: Auto-complete commands (where supported)
- `↑/↓`: Command history navigation

### Error Handling

If commands fail:
1. Check with `--debug` flag for detailed logs
2. Verify project structure with `status`
3. Use `retry` to attempt operation again
4. Use `config show` to check settings

## Next Steps

- [Workflow Guide](workflow.md) - Understand the four-phase process
- [Configuration](configuration.md) - Customize dev-agent behavior  
- [API Reference](../api/cli.md) - Developer documentation
- [Examples](../examples/basic-usage.md) - More practical examples