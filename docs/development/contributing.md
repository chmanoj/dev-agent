# Contributing Guide

Thank you for your interest in contributing to dev-agent! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- uv package manager
- Git

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/dev-agent/dev-agent.git
cd dev-agent

# Install all dependencies including development tools
uv sync --all-extras --dev

# Install pre-commit hooks
uv run pre-commit install

# Verify setup
uv run pytest
uv run ruff check dev_agent tests
uv run mypy dev_agent
```

## Development Workflow

### Code Quality Standards

All code must pass these checks:

```bash
# Format code
uv run ruff format dev_agent tests

# Lint code  
uv run ruff check dev_agent tests

# Type checking
uv run mypy dev_agent

# Run tests
uv run pytest --cov=dev_agent

# All quality checks
make quality
```

### Pre-commit Hooks

Pre-commit hooks automatically run on every commit:

- Ruff formatting and linting
- mypy type checking
- YAML/JSON validation
- Trailing whitespace removal
- Large file detection

### Testing

#### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=dev_agent --cov-report=html

# Run specific test file
uv run pytest tests/test_cli.py

# Run tests matching pattern
uv run pytest -k "test_init"

# Run with verbose output
uv run pytest -v
```

#### Writing Tests

- Use pytest fixtures for setup/teardown
- Mock external dependencies
- Test both success and failure cases
- Maintain >90% test coverage

Example test:
```python
import pytest
from unittest.mock import Mock, patch
from dev_agent.cli.main import CLIApplication

def test_init_command_success(tmp_path):
    """Test successful project initialization."""
    app = CLIApplication()
    
    with patch('dev_agent.cli.main.SessionManager') as mock_session:
        mock_session.return_value.start_session.return_value = Mock(session_id="test-123")
        
        result = app._handle_init_command(Mock(project_path=str(tmp_path)))
        
        assert result == 0
        mock_session.assert_called_once_with(str(tmp_path))
```

### Documentation

#### Writing Documentation

- Update documentation WITH code changes
- Use Google-style docstrings
- Include examples in docstrings
- Test all code examples

Example docstring:
```python
def analyze_codebase(project_path: str, config: Config) -> AnalysisResult:
    """Analyze a Python codebase and extract patterns.
    
    This function performs comprehensive analysis including AST parsing,
    dependency analysis, and pattern detection.
    
    Args:
        project_path: Absolute path to the project directory
        config: Configuration object with analysis settings
        
    Returns:
        AnalysisResult containing all analysis data and metrics
        
    Raises:
        ProjectNotFoundError: If project_path doesn't exist
        AnalysisError: If analysis fails due to code issues
        
    Example:
        ```python
        config = Config(include_tests=True)
        result = analyze_codebase("/path/to/project", config)
        print(f"Found {len(result.functions)} functions")
        ```
    """
```

#### Building Documentation

```bash
# Install documentation dependencies
uv sync --group docs

# Serve documentation locally
uv run mkdocs serve

# Build documentation
uv run mkdocs build

# Test documentation examples
python scripts/test_docs_examples.py
```

## Contribution Process

### 1. Create an Issue

Before starting work:
- Check existing issues and PRs
- Create an issue describing the change
- Discuss approach with maintainers

### 2. Fork and Branch

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/dev-agent.git
cd dev-agent

# Create feature branch
git checkout -b feature/your-feature-name
```

### 3. Make Changes

- Follow code quality standards
- Write tests for new functionality
- Update documentation
- Keep commits focused and atomic

### 4. Test Your Changes

```bash
# Run full test suite
make ci

# Test specific functionality
uv run pytest tests/test_your_feature.py

# Test documentation
uv run mkdocs serve
```

### 5. Submit Pull Request

- Push your branch to your fork
- Create pull request with clear description
- Link to related issues
- Ensure CI passes

## Code Style Guidelines

### Python Code

- Follow PEP 8 (enforced by Ruff)
- Use type hints for all functions
- Prefer composition over inheritance
- Use descriptive variable names
- Keep functions focused and small

### Imports

```python
# Standard library imports first
import os
import sys
from pathlib import Path

# Third-party imports second
import typer
from rich.console import Console
from pydantic import BaseModel

# Local imports last
from dev_agent.models.enums import PhaseType
from dev_agent.interfaces.cli_interface import ICLIInterface
```

### Error Handling

```python
# Use specific exceptions
try:
    result = process_file(file_path)
except FileNotFoundError as e:
    logger.error(f"File not found: {file_path}")
    raise ProcessingError(f"Cannot process missing file: {file_path}") from e
except PermissionError as e:
    logger.error(f"Permission denied: {file_path}")
    raise ProcessingError(f"Cannot access file: {file_path}") from e
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

def process_data(data: list[str]) -> dict[str, int]:
    """Process data and return results."""
    logger.info(f"Processing {len(data)} items")
    
    try:
        result = expensive_operation(data)
        logger.debug(f"Operation completed with {len(result)} results")
        return result
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        raise
```

## Architecture Guidelines

### Module Organization

- Keep modules focused on single responsibility
- Use interfaces for dependency injection
- Separate business logic from CLI/UI code
- Use Pydantic models for data structures

### Design Patterns

- **Strategy Pattern**: For different analysis approaches
- **Observer Pattern**: For progress reporting
- **Factory Pattern**: For creating components
- **Command Pattern**: For CLI operations

### Testing Strategy

- **Unit Tests**: Test individual functions/classes
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete workflows
- **Property Tests**: Test with generated data

## Release Process

### Version Management

- Use semantic versioning (MAJOR.MINOR.PATCH)
- Update version in `pyproject.toml`
- Create git tags for releases
- Maintain CHANGELOG.md

### Release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] Version bumped
- [ ] CHANGELOG updated
- [ ] Git tag created
- [ ] PyPI package published
- [ ] GitHub release created

## Getting Help

- **Questions**: Use GitHub Discussions
- **Bugs**: Create GitHub Issues
- **Security**: Email security@dev-agent.dev
- **Chat**: Join our Discord server

## Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- Release notes
- Documentation credits
- Annual contributor highlights

Thank you for contributing to dev-agent! 🎉