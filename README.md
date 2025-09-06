# dev-agent

AI-powered development workflow assistant that implements a four-phase development process: Indexing, Specification, Design, and Implementation.

## Features

- **Interactive CLI**: Chat-based command-line interface with user approval workflows
- **High-Performance Indexing**: Analyzes large codebases using Tree-sitter and vector embeddings
- **Context-Aware Code Generation**: Generates Python code consistent with existing patterns
- **Session Management**: Persistent state across CLI sessions
- **Python-First**: Focused on Python development with plans for multi-language support

## Installation

This project uses [uv](https://docs.astral.sh/uv/) for dependency management and virtual environment handling.

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

### Interactive mode
```bash
uv run dev-agent
```

## Development

### Running tests
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_interactive_cli.py

# Run with coverage
uv run pytest --cov=dev_agent
```

### Code formatting
```bash
# Format code
uv run black dev_agent tests

# Sort imports
uv run isort dev_agent tests

# Type checking
uv run mypy dev_agent
```

### Manual testing
```bash
python3 scripts/test_cli_manual.py
```

## Project Structure

```
dev-agent/
├── dev_agent/           # Main package
│   ├── cli/            # Command-line interface
│   ├── interfaces/     # Abstract interfaces
│   ├── models/         # Data models and enums
│   ├── indexing/       # Code indexing engine
│   ├── state/          # State management
│   └── workflow/       # Workflow orchestration
├── tests/              # Test suite
├── scripts/            # Utility scripts
└── pyproject.toml      # Project configuration
```

## Architecture

The system implements a four-phase workflow:

1. **Indexing Phase**: Analyzes existing codebase using Tree-sitter and vector embeddings
2. **Specification Phase**: Generates or refines project requirements
3. **Design Phase**: Creates technical design documents
4. **Implementation Phase**: Generates Python code and tests

Each phase requires explicit user approval before proceeding to the next.

## Contributing

1. Install development dependencies: `uv sync --dev`
2. Run tests: `uv run pytest`
3. Format code: `uv run black dev_agent tests`
4. Submit pull request

## License

MIT License - see LICENSE file for details.