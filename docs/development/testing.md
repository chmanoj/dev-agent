# Testing Guide

## Overview

dev-agent maintains high code quality through comprehensive testing with a target of 90%+ test coverage.

## Testing Stack

- **Framework**: pytest >=8.3.0
- **Coverage**: pytest-cov
- **Async Testing**: pytest-asyncio
- **Mocking**: unittest.mock
- **Fixtures**: pytest fixtures and conftest.py

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── sample_files/                  # Test data
│   ├── simple_module.py
│   └── complex_module.py
├── test_*.py                      # Unit tests
└── integration/                   # Integration tests
    ├── test_azure_openai_integration.py
    └── test_discovery.py
```

## Running Tests

### Basic Test Execution
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=dev_agent --cov-report=html

# Run specific test file
uv run pytest tests/test_llm_client.py

# Run specific test
uv run pytest tests/test_llm_client.py::test_generate_completion

# Run with verbose output
uv run pytest -v

# Fail fast (stop on first failure)
uv run pytest -x
```

### Integration Tests
```bash
# Run integration tests (requires Azure OpenAI credentials)
AZURE_OPENAI_INTEGRATION_TESTS=true uv run pytest tests/integration/

# Skip integration tests (default)
uv run pytest
```

### Coverage Reports
```bash
# Generate HTML coverage report
uv run pytest --cov=dev_agent --cov-report=html

# View report
open htmlcov/index.html

# Generate terminal report
uv run pytest --cov=dev_agent --cov-report=term-missing
```

## Test Categories

### Unit Tests
Test individual components in isolation with mocked dependencies.

**Example: Testing LLM Client**
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from dev_agent.llm.azure_client import AzureOpenAIClient

@pytest.fixture
def mock_azure_client():
    """Mock Azure OpenAI client."""
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        return_value=MagicMock(
            choices=[MagicMock(message=MagicMock(content="Generated text"))],
            usage=MagicMock(prompt_tokens=100, completion_tokens=200),
        )
    )
    return client

@pytest.mark.asyncio
async def test_generate_completion(mock_azure_client):
    """Test completion generation."""
    llm_client = AzureOpenAIClient(config, client=mock_azure_client)
    result = await llm_client.generate_completion("Test prompt")
    
    assert result == "Generated text"
    mock_azure_client.chat.completions.create.assert_called_once()
```

### Integration Tests
Test component interactions and real API calls (optional, gated by environment variable).

**Example: Azure OpenAI Integration**
```python
import os
import pytest

@pytest.mark.skipif(
    os.getenv("AZURE_OPENAI_INTEGRATION_TESTS") != "true",
    reason="Integration tests disabled",
)
@pytest.mark.asyncio
async def test_real_azure_openai():
    """Test with real Azure OpenAI API."""
    config = AzureOpenAIConfig(
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    )
    
    client = AzureOpenAIClient(config)
    result = await client.generate_completion("Say hello")
    
    assert len(result) > 0
    assert isinstance(result, str)
```

### End-to-End Tests
Test complete workflows from CLI to output.

**Example: Workflow Test**
```python
def test_complete_workflow(tmp_path):
    """Test complete four-phase workflow."""
    # Initialize project
    result = runner.invoke(app, ["init", str(tmp_path)])
    assert result.exit_code == 0
    
    # Run indexing
    result = runner.invoke(app, ["phase", "indexing"])
    assert result.exit_code == 0
    
    # Verify state
    state_file = tmp_path / ".dev_agent" / "state.json"
    assert state_file.exists()
```

## Writing Tests

### Test Naming Conventions
- Test files: `test_<module_name>.py`
- Test functions: `test_<functionality>`
- Test classes: `Test<ComponentName>`

### Test Structure (AAA Pattern)
```python
def test_example():
    # Arrange - Set up test data and mocks
    config = create_test_config()
    client = AzureOpenAIClient(config)
    
    # Act - Execute the functionality
    result = client.count_tokens("test text")
    
    # Assert - Verify the results
    assert result > 0
    assert isinstance(result, int)
```

### Fixtures
Use pytest fixtures for reusable test setup:

```python
@pytest.fixture
def test_config():
    """Provide test configuration."""
    return AzureOpenAIConfig(
        endpoint="https://test.openai.azure.com/",
        api_key="test-key",
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
    )

@pytest.fixture
def temp_project(tmp_path):
    """Create temporary project structure."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("print('hello')")
    return project_dir
```

### Parametrized Tests
Test multiple scenarios with one test function:

```python
@pytest.mark.parametrize("input_text,expected_tokens", [
    ("hello", 1),
    ("hello world", 2),
    ("", 0),
])
def test_token_counting(input_text, expected_tokens):
    """Test token counting with various inputs."""
    counter = TokenCounter()
    result = counter.count_tokens(input_text)
    assert result == expected_tokens
```

## Mocking Guidelines

### Mock Azure OpenAI Calls
**ALWAYS mock Azure OpenAI in unit tests** to avoid API costs:

```python
@pytest.fixture
def mock_openai_response():
    """Mock Azure OpenAI response."""
    return MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(content="Generated content"),
                finish_reason="stop",
            )
        ],
        usage=MagicMock(
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300,
        ),
    )
```

### Mock File System
Use `tmp_path` fixture for file operations:

```python
def test_state_persistence(tmp_path):
    """Test state save and load."""
    state_file = tmp_path / "state.json"
    state = ProjectState(phase=PhaseType.INDEXING)
    
    # Save state
    state_manager.save_state(state, state_file)
    
    # Load state
    loaded_state = state_manager.load_state(state_file)
    assert loaded_state.phase == PhaseType.INDEXING
```

## Coverage Requirements

### Minimum Coverage
- **Overall**: 90%+
- **Critical paths**: 100%
- **Public APIs**: 100%
- **Error handling**: 100%

### Checking Coverage
```bash
# Generate coverage report
uv run pytest --cov=dev_agent --cov-report=term-missing

# View uncovered lines
uv run pytest --cov=dev_agent --cov-report=html
open htmlcov/index.html
```

### Coverage Exclusions
Mark code that shouldn't be covered:

```python
def debug_function():  # pragma: no cover
    """Debug function not used in production."""
    print("Debug info")

if TYPE_CHECKING:  # pragma: no cover
    from typing import Protocol
```

## Continuous Integration

### GitHub Actions
Tests run automatically on:
- Pull requests
- Pushes to main/develop
- Multiple Python versions (3.10, 3.11, 3.12, 3.13)

### Pre-commit Hooks
Tests run locally before commit:
```bash
# Install hooks
uv run pre-commit install

# Run manually
uv run pre-commit run --all-files
```

## Best Practices

### Do's
✅ Mock all external dependencies (especially Azure OpenAI)  
✅ Use descriptive test names  
✅ Test edge cases and error conditions  
✅ Keep tests fast and deterministic  
✅ Use fixtures for common setup  
✅ Test one thing per test function  
✅ Use parametrize for multiple scenarios  

### Don'ts
❌ Don't call real Azure OpenAI API in unit tests  
❌ Don't use sleep() or time-based tests  
❌ Don't test implementation details  
❌ Don't share state between tests  
❌ Don't skip tests without good reason  
❌ Don't commit failing tests  

## Debugging Tests

### Run with Debug Output
```bash
# Show print statements
uv run pytest -s

# Show local variables on failure
uv run pytest -l

# Drop into debugger on failure
uv run pytest --pdb

# Show full diff on assertion failures
uv run pytest -vv
```

### Using pytest-watch
```bash
# Auto-run tests on file changes
uv run pytest-watch
```

## Performance Testing

### Benchmark Tests
```python
import time

def test_indexing_performance(large_codebase):
    """Test indexing performance."""
    start = time.time()
    
    indexer.index_codebase(large_codebase)
    
    duration = time.time() - start
    assert duration < 10.0  # Should complete in under 10 seconds
```

### Memory Testing
```python
import tracemalloc

def test_memory_usage():
    """Test memory usage stays within limits."""
    tracemalloc.start()
    
    # Run operation
    result = process_large_file()
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    assert peak < 100 * 1024 * 1024  # Less than 100MB
```

## Related Documentation

- [Contributing](contributing.md) - Development workflow
- [Architecture](architecture.md) - System design
