# dev-agent

AI-powered development workflow assistant that implements a four-phase development process: Indexing, Specification, Design, and Implementation.

## Features

- **Azure OpenAI Integration**: Enterprise-grade AI powered by GPT-4 and text-embedding-ada-002 using your Azure OpenAI deployments
- **Interactive CLI**: Chat-based command-line interface with user approval workflows built with Typer and Rich
- **High-Performance Indexing**: Analyzes large codebases using Tree-sitter and Azure OpenAI embeddings
- **AI-Powered Generation**: Intelligent specification, design, and task generation using GPT-4
- **Semantic Code Search**: Advanced code similarity search with Azure OpenAI embeddings
- **Context-Aware Code Generation**: Generates Python code consistent with existing patterns
- **Session Management**: Persistent state across CLI sessions
- **Modern Python Stack**: Built with Pydantic v2, FastAPI, and modern tooling
- **Python-First**: Focused on Python development with plans for multi-language support

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

## Usage

### Initialize a new project
```bash
uv run dev-agent init [path]
```

### Resume an existing project
```bash
uv run dev-agent resume [path]
```

### Interactive mode (default)
```bash
uv run dev-agent [path]
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
```bash
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_CHAT_MODEL="gpt-4"
export AZURE_OPENAI_EMBEDDING_MODEL="text-embedding-ada-002"
```

**Required Azure OpenAI deployments:**
- GPT-4 (or GPT-4 Turbo) for code generation and specifications
- text-embedding-ada-002 for code embeddings and similarity search

For detailed setup instructions, see the [Azure OpenAI documentation](docs/azure-openai-integration.md).

### Configuration management
```bash
uv run dev-agent config show
uv run dev-agent config set logging.level DEBUG
uv run dev-agent config reset
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