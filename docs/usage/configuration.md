# Configuration Guide

Customize dev-agent behavior through configuration files and environment variables.

## Configuration Files

### Global Configuration

Create `~/.dev_agent/config.toml` for user-wide settings:

```toml
[logging]
level = "INFO"
file = "~/.dev_agent/logs/dev-agent.log"
format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

[indexing]
max_file_size_mb = 10
exclude_patterns = ["*.pyc", "__pycache__", ".git", "node_modules"]
include_tests = true
max_files = 10000

[generation]
max_context_length = 8192
temperature = 0.1
model = "gpt-4"

[ui]
theme = "dark"
show_progress = true
auto_approve = false
```

### Project Configuration

Create `.dev_agent/config.toml` in your project for project-specific settings:

```toml
[project]
name = "my-project"
description = "Project description"
language = "python"
framework = "fastapi"

[indexing]
# Override global settings for this project
include_patterns = ["*.py", "*.md"]
exclude_patterns = ["tests/fixtures/*", "migrations/*"]

[generation]
# Project-specific generation settings
style_guide = "google"
max_line_length = 88
use_type_hints = true
```

## Environment Variables

Override configuration with environment variables:

```bash
# Logging
export DEV_AGENT_LOG_LEVEL=DEBUG
export DEV_AGENT_LOG_FILE=/tmp/dev-agent.log

# Indexing
export DEV_AGENT_MAX_FILE_SIZE=20
export DEV_AGENT_INCLUDE_TESTS=false

# Generation
export DEV_AGENT_TEMPERATURE=0.05
export DEV_AGENT_MAX_CONTEXT=16384

# UI
export DEV_AGENT_THEME=light
export NO_COLOR=1  # Disable colored output
```

## Configuration Options

### Logging Section

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `level` | string | "INFO" | Log level (DEBUG, INFO, WARNING, ERROR) |
| `file` | string | "~/.dev_agent/logs/dev-agent.log" | Log file path |
| `format` | string | Standard format | Log message format |
| `max_size_mb` | int | 10 | Max log file size before rotation |
| `backup_count` | int | 5 | Number of backup log files |

### Indexing Section

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `max_file_size_mb` | int | 10 | Skip files larger than this |
| `exclude_patterns` | list | ["*.pyc", "__pycache__"] | Patterns to exclude |
| `include_patterns` | list | ["*.py"] | Patterns to include |
| `include_tests` | bool | true | Include test files in analysis |
| `max_files` | int | 10000 | Maximum files to process |
| `follow_symlinks` | bool | false | Follow symbolic links |

### Generation Section

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `max_context_length` | int | 8192 | Maximum context for generation |
| `temperature` | float | 0.1 | Generation randomness (0.0-1.0) |
| `model` | string | "gpt-4" | AI model to use |
| `style_guide` | string | "pep8" | Code style guide |
| `max_line_length` | int | 88 | Maximum line length |
| `use_type_hints` | bool | true | Generate type hints |

### UI Section

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `theme` | string | "auto" | UI theme (light, dark, auto) |
| `show_progress` | bool | true | Show progress bars |
| `auto_approve` | bool | false | Auto-approve phases (dangerous) |
| `editor` | string | "$EDITOR" | Editor for reviewing documents |

## Command-Line Configuration

### View Configuration

```bash
# Show all configuration
uv run dev-agent config show

# Show specific section
uv run dev-agent config show logging
uv run dev-agent config show indexing
```

### Set Configuration

```bash
# Set logging level
uv run dev-agent config set logging.level DEBUG

# Set indexing options
uv run dev-agent config set indexing.max_file_size_mb 20
uv run dev-agent config set indexing.include_tests false

# Set generation parameters
uv run dev-agent config set generation.temperature 0.05
uv run dev-agent config set generation.max_context_length 16384
```

### Reset Configuration

```bash
# Reset all to defaults
uv run dev-agent config reset

# Reset specific section
uv run dev-agent config reset logging
uv run dev-agent config reset indexing
```

## Advanced Configuration

### Custom Exclude Patterns

```toml
[indexing]
exclude_patterns = [
    "*.pyc",
    "__pycache__",
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "*.egg-info",
    "build",
    "dist",
    "*.log",
    "*.tmp",
    "migrations/*.py",
    "tests/fixtures/*",
    "docs/_build/*"
]
```

### Framework-Specific Settings

```toml
# Django project
[project]
framework = "django"

[indexing]
exclude_patterns = ["migrations/*.py", "static/*", "media/*"]
include_patterns = ["*.py", "*.html", "*.md"]

[generation]
style_guide = "django"
use_class_based_views = true

# FastAPI project  
[project]
framework = "fastapi"

[generation]
use_async = true
include_openapi = true
use_pydantic_v2 = true
```

### Team Configuration

Share configuration across team members:

```toml
# .dev_agent/team.toml
[team]
style_guide = "company-standard"
max_line_length = 100
use_type_hints = true
test_framework = "pytest"

[indexing]
exclude_patterns = [
    "*.pyc", "__pycache__", ".git",
    "legacy/*",  # Skip legacy code
    "vendor/*",  # Skip vendor code
    "generated/*"  # Skip generated code
]

[generation]
# Consistent generation settings
temperature = 0.1
max_context_length = 8192
include_docstrings = true
docstring_style = "google"
```

## Configuration Validation

dev-agent validates configuration on startup:

```bash
$ uv run dev-agent config validate
✅ Configuration is valid
📊 Using settings:
   - Log level: INFO
   - Max file size: 10MB
   - Include tests: true
   - Temperature: 0.1
```

If configuration is invalid:

```bash
$ uv run dev-agent config validate
❌ Configuration errors found:
   - logging.level: Invalid value 'TRACE' (must be DEBUG, INFO, WARNING, ERROR)
   - indexing.max_file_size_mb: Must be positive integer
   - generation.temperature: Must be between 0.0 and 1.0
```

## Troubleshooting

### Common Issues

#### Configuration Not Loading
```
Warning: Using default configuration
```
**Solution**: Check file path and permissions:
```bash
ls -la ~/.dev_agent/config.toml
chmod 644 ~/.dev_agent/config.toml
```

#### Invalid Configuration Values
```
Error: Invalid configuration value for 'logging.level'
```
**Solution**: Check valid values in documentation or use:
```bash
uv run dev-agent config validate
```

#### Environment Variables Not Working
```
Warning: Environment variable DEV_AGENT_LOG_LEVEL ignored
```
**Solution**: Ensure correct variable names and restart shell.

### Configuration Priority

Configuration is loaded in this order (later overrides earlier):

1. Default values
2. Global config file (`~/.dev_agent/config.toml`)
3. Project config file (`.dev_agent/config.toml`)
4. Environment variables
5. Command-line arguments

## Next Steps

- [CLI Usage](cli.md) - Command-line interface
- [Workflow Guide](workflow.md) - Understanding the process
- [Examples](../examples/basic-usage.md) - Practical examples