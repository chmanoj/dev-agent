# Installation Guide

This guide covers installing dev-agent and its dependencies on different platforms.

## Prerequisites

dev-agent requires Python 3.10 or higher and uses modern Python tooling.

### Python Version Check

```bash
python --version
# Should show Python 3.10.0 or higher
```

If you need to install or upgrade Python:

=== "macOS"
    ```bash
    # Using Homebrew
    brew install python@3.11
    
    # Using pyenv
    pyenv install 3.11.7
    pyenv global 3.11.7
    ```

=== "Ubuntu/Debian"
    ```bash
    # Ubuntu 22.04+ has Python 3.10+
    sudo apt update
    sudo apt install python3.11 python3.11-venv python3.11-dev
    
    # For older versions, use deadsnakes PPA
    sudo add-apt-repository ppa:deadsnakes/ppa
    sudo apt update
    sudo apt install python3.11 python3.11-venv python3.11-dev
    ```

=== "Windows"
    ```powershell
    # Download from python.org or use winget
    winget install Python.Python.3.11
    
    # Or use Chocolatey
    choco install python311
    ```

## Install uv (Recommended)

dev-agent uses [uv](https://docs.astral.sh/uv/) for fast dependency management:

=== "macOS/Linux"
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

=== "Windows"
    ```powershell
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

=== "Alternative (pip)"
    ```bash
    pip install uv
    ```

Verify installation:
```bash
uv --version
# Should show uv 0.5.0 or higher
```

## Install dev-agent

### From Source (Recommended for Development)

```bash
# Clone the repository
git clone https://github.com/dev-agent/dev-agent.git
cd dev-agent

# Install with development dependencies
uv sync --dev

# Verify installation
uv run dev-agent --help
```

### From PyPI (Coming Soon)

```bash
# Install from PyPI (when available)
uv add dev-agent

# Or with pip
pip install dev-agent
```

### Development Installation

For contributing to dev-agent:

```bash
# Clone and install in development mode
git clone https://github.com/dev-agent/dev-agent.git
cd dev-agent

# Install all dependencies including docs and testing
uv sync --all-extras --dev

# Install pre-commit hooks
uv run pre-commit install

# Run tests to verify installation
uv run pytest

# Start documentation server
uv run mkdocs serve
```

## Verify Installation

Test that everything is working:

```bash
# Check version
uv run dev-agent --version

# Run help command
uv run dev-agent --help

# Test with a sample project
mkdir test-project
cd test-project
uv run dev-agent init
```

Expected output:
```
✅ Initialized new dev-agent project
🔍 Starting indexing phase...
📊 No existing code found, ready for specification phase
💬 Interactive mode started. Type 'help' for commands.
```

## Configuration

### Environment Variables

dev-agent respects these environment variables:

```bash
# Logging level (DEBUG, INFO, WARNING, ERROR)
export DEV_AGENT_LOG_LEVEL=INFO

# Custom configuration file
export DEV_AGENT_CONFIG_PATH=/path/to/config.toml

# Disable color output
export NO_COLOR=1
```

### Configuration File

Create a configuration file at `~/.dev_agent/config.toml`:

```toml
[logging]
level = "INFO"
file = "~/.dev_agent/logs/dev-agent.log"

[indexing]
max_file_size_mb = 10
exclude_patterns = ["*.pyc", "__pycache__", ".git"]
include_tests = true

[generation]
max_context_length = 8192
temperature = 0.1
```

## Troubleshooting

### Common Issues

#### Python Version Too Old
```
Error: dev-agent requires Python 3.10 or higher
```
**Solution**: Install Python 3.10+ using the methods above.

#### uv Not Found
```
Command 'uv' not found
```
**Solution**: Install uv using the installation script or add it to your PATH.

#### Permission Errors
```
Permission denied: /usr/local/bin/dev-agent
```
**Solution**: Use virtual environments or install with `--user` flag.

#### Import Errors
```
ModuleNotFoundError: No module named 'dev_agent'
```
**Solution**: Ensure you're running from the correct environment:
```bash
uv run dev-agent  # Use uv run
# or activate the virtual environment first
source .venv/bin/activate
dev-agent
```

### Getting Help

If you encounter issues:

1. **Check the logs**: `~/.dev_agent/logs/dev-agent.log`
2. **Run with debug**: `DEV_AGENT_LOG_LEVEL=DEBUG uv run dev-agent`
3. **Check dependencies**: `uv run pip list`
4. **File an issue**: [GitHub Issues](https://github.com/dev-agent/dev-agent/issues)

### System Requirements

- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 1GB free space for dependencies and cache
- **Network**: Internet connection for initial setup and updates

## Next Steps

- [CLI Usage Guide](usage/cli.md) - Learn the command-line interface
- [Workflow Guide](usage/workflow.md) - Understand the four-phase process
- [Configuration](usage/configuration.md) - Customize dev-agent behavior
- [Examples](examples/basic-usage.md) - See practical usage examples