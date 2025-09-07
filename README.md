# dev-agent

AI-powered development workflow assistant that implements a four-phase development process: Indexing, Specification, Design, and Implementation.

## Features

- **Interactive CLI**: Chat-based command-line interface with user approval workflows built with Typer and Rich
- **High-Performance Indexing**: Analyzes large codebases using Tree-sitter and vector embeddings
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

### Setup

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

- **Build System**: `uv` for dependency management, `hatchling` for building
- **CLI Framework**: Typer with Rich for enhanced terminal output
- **Data Models**: Pydantic v2 for data validation and settings
- **Code Quality**: Ruff with comprehensive rule set (formatting, linting, security, performance)
- **Type Checking**: mypy with strict configuration
- **Web Framework**: FastAPI with uvicorn (for future API features)
- **Code Quality**: Ruff (replaces black, isort, flake8), mypy for type checking
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