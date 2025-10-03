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

## Configure Azure OpenAI (Required)

dev-agent requires Azure OpenAI for all AI-powered features. You must configure your Azure OpenAI credentials before using the tool.

### Prerequisites

1. An Azure subscription
2. An Azure OpenAI resource with deployed models:
   - GPT-4 (or GPT-4 Turbo) deployment for code generation
   - text-embedding-ada-002 deployment for embeddings

### Interactive Configuration

The easiest way to configure Azure OpenAI:

```bash
# Run the interactive configuration wizard
uv run dev-agent azure configure

# Test your connection
uv run dev-agent azure test

# Check configuration status
uv run dev-agent azure status
```

### Environment Variables (Recommended)

For production or CI/CD environments, use environment variables:

```bash
# Required settings
export AZURE_OPENAI_API_KEY="your-api-key-here"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_CHAT_MODEL="gpt-4"
export AZURE_OPENAI_EMBEDDING_MODEL="text-embedding-ada-002"

# Optional settings
export AZURE_OPENAI_API_VERSION="2024-02-15-preview"
export AZURE_OPENAI_MAX_TOKENS="4000"
export AZURE_OPENAI_TEMPERATURE="0.7"
```

Add these to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.) or use a `.env` file.

### Configuration File

Alternatively, create a configuration file at `~/.dev_agent/config.json`:

```json
{
  "azure_openai": {
    "api_key": "your-api-key-here",
    "endpoint": "https://your-resource.openai.azure.com/",
    "chat_model": "gpt-4",
    "embedding_model": "text-embedding-ada-002",
    "api_version": "2024-02-15-preview"
  }
}
```

**Security Note**: Never commit API keys to version control. Use environment variables or secure key management systems in production.

## Verify Installation

Test that everything is working:

```bash
# Check version
uv run dev-agent --version

# Verify Azure OpenAI configuration
uv run dev-agent azure status

# Test Azure OpenAI connection
uv run dev-agent azure test

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
📊 Analyzing codebase with Azure OpenAI embeddings...
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

#### Azure OpenAI Not Configured
```
Error: Azure OpenAI embeddings are required
```
**Solution**: Configure Azure OpenAI using the interactive wizard:
```bash
uv run dev-agent azure configure
```

#### Azure OpenAI Authentication Failed
```
Error: Failed to initialize Azure OpenAI service
```
**Solution**: 
1. Verify your API key is correct
2. Check that your endpoint URL is correct
3. Ensure your Azure OpenAI resource is active
4. Test the connection: `uv run dev-agent azure test`

#### Model Deployment Not Found
```
Error: The API deployment for this resource does not exist
```
**Solution**: 
1. Verify your model deployment names in Azure Portal
2. Ensure you've deployed both GPT-4 and text-embedding-ada-002
3. Update your configuration with the correct deployment names

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

- [Azure OpenAI Setup](azure-openai-integration.md) - Detailed Azure OpenAI configuration guide
- [CLI Usage Guide](usage/cli.md) - Learn the command-line interface
- [Workflow Guide](usage/workflow.md) - Understand the four-phase process
- [Configuration](usage/configuration.md) - Customize dev-agent behavior
- [Examples](examples/basic-usage.md) - See practical usage examples