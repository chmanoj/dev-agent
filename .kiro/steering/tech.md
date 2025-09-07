# Technology Stack & Modern Python Standards

## Build System & Package Management
- **Primary**: `uv` for dependency management and virtual environments (REQUIRED)
- **Fallback**: `pip` with `requirements.txt` for compatibility only
- **Build**: `hatchling` build backend with `pyproject.toml` (modern standard)
- **Lock File**: `uv.lock` for reproducible builds

## Core Dependencies (Latest Versions Required)
- **CLI Framework**: Typer >=0.15.0 with Rich >=13.9.0 for enhanced terminal output
- **Data Models**: Pydantic >=2.10.0 for data validation and settings (v2 required)
- **Vector Database**: FAISS-CPU >=1.9.0 for embeddings storage
- **Code Analysis**: Tree-sitter for parsing, sentence-transformers >=3.3.0 for embeddings
- **Web Framework**: FastAPI >=0.115.0 with uvicorn >=0.32.0 (for future API features)
- **HTTP Client**: httpx >=0.28.0 for async requests
- **Numerical**: NumPy >=2.0.0 (latest major version)

## Development Tools (Modern Standards)
- **Testing**: pytest >=8.3.0 with coverage, mock, and asyncio support
- **Code Quality**: Ruff >=0.8.0 (replaces black, isort, flake8, bandit, and more)
  - MUST include comprehensive rule set: security, performance, complexity, imports
  - MUST use strict formatting and linting rules
- **Type Checking**: mypy >=1.13.0 with strict configuration
  - MUST enable strict mode and enhanced error codes
- **Pre-commit**: Automated hooks for code quality, formatting, and type checking
- **CI/CD**: GitHub Actions with multi-Python version testing

## Python Version Requirements
- **Minimum**: Python 3.10 (REQUIRED - no older versions)
- **Supported**: 3.10, 3.11, 3.12, 3.13
- **Target**: Python 3.11+ for optimal performance

## Python Requirements
- **Minimum**: Python 3.10
- **Supported**: 3.10, 3.11, 3.12, 3.13

## Common Commands

### Environment Setup
```bash
# Install dependencies
uv sync --dev

# Activate virtual environment (if needed)
source .venv/bin/activate
```

### Development (Modern Workflow)
```bash
# Environment setup (ALWAYS use uv)
uv sync --dev  # Install all dependencies
uv run pre-commit install  # Setup automated hooks

# Testing (comprehensive)
uv run pytest  # Run all tests
uv run pytest --cov=dev_agent --cov-report=html  # with coverage
uv run pytest tests/test_specific.py  # specific test
uv run pytest -x  # fail fast

# Code quality (MUST pass all checks)
uv run ruff format dev_agent tests  # format code (replaces black)
uv run ruff check dev_agent tests   # comprehensive linting (replaces flake8, isort, bandit)
uv run ruff check --fix dev_agent tests  # auto-fix issues

# Type checking (STRICT mode required)
uv run mypy dev_agent  # strict type checking

# Documentation (MANDATORY)
uv sync --group docs  # install documentation dependencies
uv run mkdocs serve   # serve docs locally with live reload
uv run mkdocs build   # build documentation
make docs-serve       # shortcut for local documentation

# Pre-commit hooks (automated quality)
uv run pre-commit run --all-files  # run all checks
uv run pre-commit install  # install hooks

# Development shortcuts (use Makefile)
make dev      # setup development environment
make quality  # run all quality checks
make test     # run tests with coverage
make ci       # run all CI checks locally
```

### Application Usage
```bash
# Run the CLI
uv run dev-agent --help
uv run dev-agent init [path]
uv run dev-agent resume [path]
uv run dev-agent  # interactive mode
```

### Manual Testing
```bash
python3 scripts/test_cli_manual.py
```

## Configuration Files (Modern Standards)
- `pyproject.toml`: PRIMARY configuration (dependencies, tools, build settings)
- `uv.lock`: Locked dependency versions (managed by uv, NEVER edit manually)
- `requirements.txt`: Legacy compatibility ONLY (keep in sync with pyproject.toml)
- `.pre-commit-config.yaml`: Automated code quality hooks
- `Makefile`: Development workflow commands
- `.github/workflows/ci.yml`: CI/CD pipeline
- `.gitignore`: Comprehensive ignore patterns for modern Python development
- **NO setup.py, MANIFEST.in, or other legacy files**

## Code Quality Standards (ENFORCED)
- **Ruff Rules**: MUST include security (S), performance (PERF), complexity (C901), imports (I)
- **mypy**: MUST use strict mode with enhanced error codes
- **Coverage**: MUST maintain >90% test coverage
- **Pre-commit**: MUST pass all hooks before commit
- **CI/CD**: MUST test on Python 3.10, 3.11, 3.12, 3.13

## Dependency Management Rules
- **Primary**: Always use `uv sync --dev` for development
- **Updates**: Use `uv lock --upgrade` to update dependencies
- **Production**: Use `uv sync --no-dev` for production installs
- **Legacy**: Keep requirements.txt in sync for pip compatibility only