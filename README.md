# dev-agent

AI-powered development workflow assistant that implements a four-phase development process: Indexing, Specification, Design, and Implementation.

## Features

### Core Capabilities
- **Azure OpenAI Integration**: Enterprise-grade AI powered by GPT-4 and text-embedding-ada-002 using your Azure OpenAI deployments
- **Flexible Authentication**: Support for both API key and Azure AD authentication with custom headers for auditing
- **Interactive CLI**: Chat-based command-line interface with user approval workflows built with Typer and Rich
- **High-Performance Indexing**: Analyzes large codebases using Tree-sitter and Azure OpenAI embeddings
- **AI-Powered Generation**: Intelligent specification, design, and task generation using GPT-4
- **Semantic Code Search**: Advanced code similarity search with Azure OpenAI embeddings
- **Context-Aware Code Generation**: Generates Python code consistent with existing patterns
- **Session Management**: Persistent state across CLI sessions
- **Modern Python Stack**: Built with Pydantic v2, FastAPI, and modern tooling
- **Python-First**: Focused on Python development with plans for multi-language support

### Enhanced User Experience
- **Setup Wizard**: Guided first-time setup with Azure OpenAI configuration and connection testing
- **User Journey Optimization**: Tailored workflows for new projects and existing codebases
- **Progress Display**: Real-time progress indicators with Rich terminal output
- **Streaming Responses**: Live display of AI-generated content as it's created
- **Cost Tracking**: Monitor token usage and API costs per operation and phase
- **Enhanced Error Handling**: User-friendly error messages with actionable solutions
- **Contextual Help**: Comprehensive help system with examples and command-specific guidance

### Maintenance & Quality
- **Audit System**: Comprehensive functionality verification across all workflow phases
- **Cleanup Tools**: Identify and remove temporary files, obsolete code, and unused dependencies
- **Validation Commands**: Verify configuration, connectivity, and environment setup
- **Performance Optimizations**: Efficient indexing, batch processing, and caching strategies

## Installation

This project uses modern Python tooling with [uv](https://docs.astral.sh/uv/) for dependency management.

### Prerequisites

Install uv:
```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv
```

### Basic Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd dev-agent
```

2. Install dependencies:
```bash
uv sync --dev
```

3. Verify installation:
```bash
uv run dev-agent --help
```

### Installation Options

**Default installation:**
```bash
pip install dev-agent
```

**Development installation:**
```bash
pip install -e '.[dev]'
```

> **Note:** Azure OpenAI configuration is required for all AI-powered features. See the Azure OpenAI Configuration section below for setup instructions.

### Troubleshooting Installation

**Issue: `uv` command not found**
```bash
# Install uv using pip
pip install uv

# Or use the official installer
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

**Issue: Python version mismatch**
```bash
# Check your Python version (must be 3.10+)
python --version

# Install Python 3.10+ if needed
# On macOS with Homebrew:
brew install python@3.11

# On Ubuntu/Debian:
sudo apt-get install python3.11
```

**Issue: Azure OpenAI connection fails**
```bash
# Verify your configuration
uv run dev-agent azure status

# Test connection
uv run dev-agent azure test

# Reconfigure if needed
uv run dev-agent azure configure
```

**Issue: Permission errors during installation**
```bash
# Use virtual environment (recommended)
uv sync --dev

# Or install with user flag
pip install --user dev-agent
```

**Issue: Tree-sitter compilation errors**
```bash
# Install build tools
# On macOS:
xcode-select --install

# On Ubuntu/Debian:
sudo apt-get install build-essential

# On Windows:
# Install Visual Studio Build Tools
```

For more troubleshooting help, see the [documentation](docs/getting-started/troubleshooting.md) or open an issue on GitHub.

## Usage

### First-Time Setup

When you run dev-agent for the first time, you'll be guided through an interactive setup wizard:

```bash
# Run the setup wizard
uv run dev-agent setup

# The wizard will guide you through:
# 1. Azure OpenAI configuration (endpoint, API key, deployments)
# 2. Connection testing
# 3. Workflow explanation
# 4. Project type selection (new project or existing codebase)
```

You can also run the setup wizard later to reconfigure:
```bash
# Check setup status
uv run dev-agent setup --status

# Re-run setup wizard
uv run dev-agent setup
```

### Quick Start Commands

**Initialize a new project:**
```bash
uv run dev-agent init [path]
```

**Resume an existing project:**
```bash
uv run dev-agent resume [path]
```

**Interactive mode (default):**
```bash
uv run dev-agent [path]
```

**Check project status:**
```bash
uv run dev-agent status
uv run dev-agent status --detailed  # verbose output
```

**Validate environment:**
```bash
uv run dev-agent validate
```

### New Project Workflow

Starting a new project from scratch with dev-agent:

```bash
# 1. Create project directory
mkdir my-new-project
cd my-new-project

# 2. Initialize dev-agent (runs setup wizard if first time)
uv run dev-agent init

# 3. The system will:
#    - Create .dev_agent/ directory structure
#    - Guide you through Azure OpenAI configuration
#    - Explain the four-phase workflow
#    - Offer template selection (optional)

# 4. Create initial specification
uv run dev-agent phase specification
# Describe your project when prompted
# Review and approve the generated specification

# 5. Generate design document
uv run dev-agent phase design
# Review and approve the generated design

# 6. Generate implementation tasks
uv run dev-agent phase implementation
# Review the task breakdown

# 7. Start implementing
# Follow the generated tasks in .dev_agent/documents/tasks.md
```

**Example: Creating a REST API project**
```bash
mkdir my-api-project
cd my-api-project
uv run dev-agent init

# When prompted, describe your project:
# "Create a REST API for managing user accounts with authentication,
#  CRUD operations, and PostgreSQL database integration"

# Follow the workflow phases to generate specifications,
# design documents, and implementation tasks
```

### Existing Codebase Workflow

Analyzing and documenting an existing codebase:

```bash
# 1. Navigate to your existing project
cd /path/to/existing/project

# 2. Initialize dev-agent
uv run dev-agent init

# 3. The system will:
#    - Detect existing code automatically
#    - Display codebase summary (languages, file count)
#    - Start indexing with progress display
#    - Show indexing summary (patterns found, languages detected)

# 4. Generate specification from existing code
uv run dev-agent phase specification
# The AI will analyze your codebase and generate documentation

# 5. Generate design documentation
uv run dev-agent phase design
# Creates technical design docs based on existing architecture

# 6. Generate enhancement tasks
uv run dev-agent phase implementation
# Suggests improvements and generates implementation tasks
```

**Example: Documenting a legacy project**
```bash
cd /path/to/legacy-project
uv run dev-agent init

# Watch as dev-agent:
# - Indexes 1,247 Python files
# - Detects patterns: Flask app, SQLAlchemy models, pytest tests
# - Identifies architecture: MVC pattern with service layer
# - Generates comprehensive specification document

# Review generated documentation in .dev_agent/documents/
```

### Azure OpenAI Configuration (Required)

dev-agent requires Azure OpenAI for all AI-powered features including code analysis, specification generation, design creation, and code generation.

**Interactive configuration:**
```bash
# Configure Azure OpenAI credentials
uv run dev-agent azure configure

# Test your connection
uv run dev-agent azure test

# Check configuration status
uv run dev-agent azure status
```

**Environment variables (recommended for production):**

*Option A: API Key Authentication (Default)*
```bash
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_OPENAI_API_VERSION="2024-02-15-preview"
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-ada-002"
```

*Option B: Azure AD Authentication (Enterprise)*
```bash
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_TOKEN="your-bearer-token"
export AZURE_OPENAI_API_VERSION="2024-02-15-preview"
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-ada-002"

# Optional: Custom headers for auditing
export AZURE_OPENAI_USER_SID="A123456"
export AZURE_OPENAI_CUSTOM_HEADERS='{"department": "engineering"}'
```

**Authentication Methods:**
- **API Key**: Simple authentication using Azure OpenAI API key (default)
- **Azure AD**: Enterprise authentication using bearer tokens with support for custom headers and auditing

**Required Azure OpenAI deployments:**
- GPT-4 (or GPT-4 Turbo) for code generation and specifications
- text-embedding-ada-002 for code embeddings and similarity search

**Documentation:**
- [Azure OpenAI Configuration Guide](docs/configuration/azure-openai.md) - Complete setup instructions
- [Azure AD Migration Guide](docs/configuration/azure-ad-migration-guide.md) - Migrate from API key to Azure AD authentication

### CLI Commands Reference

#### Workflow Commands
```bash
# Run complete workflow
uv run dev-agent run

# Execute specific phase
uv run dev-agent phase indexing
uv run dev-agent phase specification
uv run dev-agent phase design
uv run dev-agent phase implementation

# Retry failed phase
uv run dev-agent retry
```

#### Status and Monitoring
```bash
# Show project status
uv run dev-agent status
uv run dev-agent status --detailed

# Show cost report
uv run dev-agent cost
uv run dev-agent cost --phase indexing
uv run dev-agent cost --export report.json
```

#### Maintenance Commands
```bash
# Run comprehensive audit
uv run dev-agent audit

# Cleanup operations
uv run dev-agent cleanup --scan           # Show cleanup plan
uv run dev-agent cleanup --dry-run        # Simulate cleanup
uv run dev-agent cleanup --execute        # Execute cleanup
uv run dev-agent cleanup --category temp  # Clean specific category
```

#### Configuration Management
```bash
# General configuration
uv run dev-agent config show
uv run dev-agent config set logging.level DEBUG
uv run dev-agent config reset

# Azure OpenAI configuration
uv run dev-agent azure configure
uv run dev-agent azure test
uv run dev-agent azure status
```

#### Help and Documentation
```bash
# General help
uv run dev-agent help
uv run dev-agent --help

# Command-specific help
uv run dev-agent help <command>
uv run dev-agent <command> --help

# Show usage examples
uv run dev-agent examples
```

#### Validation
```bash
# Validate environment and configuration
uv run dev-agent validate
```

## Development

This project uses modern Python development tools:

### Quick Start
```bash
# Install all dependencies
make install-dev

# Run all quality checks
make check-all

# Fix formatting and linting issues
make fix-all

# Run tests with coverage
make test-cov
```

### Individual Commands
```bash
# Run tests
uv run pytest
uv run pytest tests/test_specific.py  # specific test
uv run pytest --cov=dev_agent        # with coverage

# Code quality
uv run ruff format dev_agent tests    # format code
uv run ruff check dev_agent tests     # lint code
uv run ruff check --fix dev_agent tests  # auto-fix issues
uv run mypy dev_agent                 # type checking

# Run the application
uv run dev-agent --help
```

### Pre-commit Hooks
```bash
# Install pre-commit hooks
make pre-commit-install

# Run on all files
make pre-commit-run
```

## Technology Stack

- **AI Provider**: Azure OpenAI (GPT-4 + text-embedding-ada-002) - required for all AI operations
- **Build System**: `uv` for dependency management, `hatchling` for building
- **CLI Framework**: Typer with Rich for enhanced terminal output
- **Data Models**: Pydantic v2 for data validation and settings
- **Code Analysis**: Tree-sitter for AST parsing, FAISS for vector storage
- **Code Quality**: Ruff with comprehensive rule set (formatting, linting, security, performance)
- **Type Checking**: mypy with strict configuration
- **Web Framework**: FastAPI with uvicorn (for future API features)
- **Testing**: pytest with coverage, mock, and asyncio support
- **Python**: 3.10+ (supports 3.10, 3.11, 3.12, 3.13)

## Project Structure

```
dev-agent/
├── dev_agent/           # Main package
│   ├── cli/            # Typer-based command-line interface
│   ├── interfaces/     # Abstract interfaces and protocols
│   ├── models/         # Pydantic data models and enums
│   ├── indexing/       # Tree-sitter code indexing engine
│   ├── generation/     # Content generation (specs, designs, code)
│   ├── analysis/       # Codebase analysis tools
│   ├── workflow/       # Workflow orchestration
│   ├── state/          # State management
│   ├── config/         # Configuration management
│   └── errors/         # Error handling and recovery
├── tests/              # Comprehensive test suite
├── scripts/            # Development and utility scripts
├── examples/           # Usage examples and demos
├── pyproject.toml      # Modern project configuration
├── Makefile           # Development workflow commands
└── .pre-commit-config.yaml  # Code quality automation
```

## Architecture

The system implements a four-phase workflow with modern Python patterns:

1. **Indexing Phase**: Analyzes existing codebase using Tree-sitter and vector embeddings
2. **Specification Phase**: Generates or refines project requirements
3. **Design Phase**: Creates technical design documents
4. **Implementation Phase**: Generates Python code and tests

Key architectural features:
- **Interface-based design** with dependency injection
- **Pydantic models** for type-safe data handling
- **Enum-driven state management** for workflow phases
- **Session persistence** across CLI interactions
- **User approval workflows** between phases

## Contributing

1. Install development dependencies: `make install-dev`
2. Run quality checks: `make check-all`
3. Run tests: `make test-cov`
4. Install pre-commit hooks: `make pre-commit-install`
5. Submit pull request

## License

MIT License - see LICENSE file for details.