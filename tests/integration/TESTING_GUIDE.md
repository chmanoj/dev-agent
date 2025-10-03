# Integration Testing Guide

## Overview

This guide explains how to run and maintain the Azure OpenAI integration tests.

## Test Structure

The integration test suite (`test_azure_openai_integration.py`) contains 15 comprehensive tests covering:

### 1. Basic LLM Operations (Tests 1-4)
- `test_real_completion_generation`: Basic completion with real API
- `test_real_streaming_generation`: Streaming responses
- `test_real_token_counting`: Token counting accuracy
- `test_real_cost_estimation`: Cost estimation validation

### 2. Embedding Operations (Tests 5-7)
- `test_real_embedding_generation`: Single text embedding
- `test_real_batch_embedding`: Batch embedding processing
- `test_real_embedding_cache`: Cache functionality

### 3. Error Handling (Tests 8, 15)
- `test_real_error_recovery`: Retry logic and error recovery
- `test_real_error_handling`: Authentication and error scenarios

### 4. End-to-End Workflows (Tests 9-11)
- `test_real_specification_generation`: Full spec generation workflow
- `test_real_code_generation`: Full code generation workflow
- `test_real_vector_search`: Vector search with real embeddings

### 5. Cost Tracking (Tests 12-13)
- `test_real_cost_tracking_workflow`: Multi-phase cost tracking
- `test_real_streaming_with_cost_tracking`: Streaming with cost tracking

### 6. Performance (Test 14)
- `test_real_performance_benchmarks`: Performance validation

## Running Tests

### Prerequisites

1. Install dependencies:
```bash
uv sync --dev
```

2. Configure Azure OpenAI:
```bash
export AZURE_OPENAI_INTEGRATION_TESTS=true
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
export AZURE_OPENAI_API_KEY=your-api-key-here
export AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

### Run All Tests

```bash
uv run pytest tests/integration/ -v
```

### Run Specific Test Category

```bash
# Basic operations only
uv run pytest tests/integration/ -v -k "completion or streaming or token or cost_estimation"

# Embedding operations only
uv run pytest tests/integration/ -v -k "embedding"

# End-to-end workflows only
uv run pytest tests/integration/ -v -k "specification or code_generation or vector_search"

# Cost tracking only
uv run pytest tests/integration/ -v -k "cost_tracking"
```

### Run Single Test

```bash
uv run pytest tests/integration/test_azure_openai_integration.py::test_real_completion_generation -v -s
```

## Test Requirements Coverage

The integration tests verify the following requirements:

### Requirement 9.6: Gated Integration Tests
- All tests are gated by `AZURE_OPENAI_INTEGRATION_TESTS=true`
- Tests are skipped if environment variable is not set
- Clear skip messages guide users on how to enable tests

### Requirement 9.7: Real API Verification
- All tests use real Azure OpenAI API calls
- Tests verify end-to-end functionality
- Tests validate actual token usage and costs
- Tests verify streaming, embeddings, and completions

### Requirement 9.8: Code Coverage
- Tests cover all major LLM modules
- Tests verify integration between components
- Tests validate error handling and recovery
- Tests ensure >90% coverage for LLM-related code

## Cost Management

### Estimated Costs

Per test run (approximate):
- Basic operations (4 tests): $0.05 - $0.15
- Embedding operations (3 tests): $0.01 - $0.03
- End-to-end workflows (3 tests): $0.10 - $0.30
- Cost tracking (2 tests): $0.05 - $0.10
- Performance (1 test): $0.02 - $0.05
- **Total per run: $0.23 - $0.63**

### Cost Optimization Tips

1. **Use GPT-3.5-turbo for testing**:
```bash
export AZURE_OPENAI_DEPLOYMENT_NAME=gpt-35-turbo
```

2. **Run selective tests**:
```bash
# Only run cheap tests
uv run pytest tests/integration/ -v -k "token or cache"
```

3. **Set lower token limits**:
   - Tests already use `max_tokens=1000` or less
   - Modify test fixtures if needed

4. **Use test markers**:
```python
@pytest.mark.expensive  # Mark expensive tests
@pytest.mark.cheap      # Mark cheap tests
```

## Troubleshooting

### Tests Skipped

**Problem**: All tests show "Integration tests disabled"

**Solution**:
```bash
# Ensure environment variable is set
export AZURE_OPENAI_INTEGRATION_TESTS=true

# Verify it's set
echo $AZURE_OPENAI_INTEGRATION_TESTS

# Run tests
uv run pytest tests/integration/ -v
```

### Authentication Errors

**Problem**: `LLMAuthenticationError` or 401 errors

**Solutions**:
1. Verify API key is correct
2. Check endpoint URL format (must end with `.openai.azure.com/`)
3. Ensure Azure OpenAI resource is active
4. Verify deployment names match your Azure configuration

### Rate Limiting

**Problem**: 429 Too Many Requests errors

**Solutions**:
1. Wait 60 seconds before retrying
2. Check Azure OpenAI quota in Azure Portal
3. Run fewer tests concurrently
4. Increase retry delays in test configuration

### Timeout Errors

**Problem**: Tests timeout after 60 seconds

**Solutions**:
1. Check network connectivity
2. Verify Azure OpenAI service status
3. Increase timeout in test fixtures:
```python
azure_config.timeout = 120  # Increase to 120 seconds
```

### Import Errors

**Problem**: `ModuleNotFoundError` for dev_agent modules

**Solutions**:
1. Ensure you're in the project root directory
2. Install in development mode:
```bash
uv sync --dev
```
3. Verify PYTHONPATH includes project root

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  workflow_dispatch:  # Manual trigger

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install uv
        run: pip install uv
      
      - name: Install dependencies
        run: uv sync --dev
      
      - name: Run integration tests
        env:
          AZURE_OPENAI_INTEGRATION_TESTS: true
          AZURE_OPENAI_ENDPOINT: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
          AZURE_OPENAI_API_KEY: ${{ secrets.AZURE_OPENAI_API_KEY }}
          AZURE_OPENAI_DEPLOYMENT_NAME: ${{ secrets.AZURE_OPENAI_DEPLOYMENT_NAME }}
          AZURE_OPENAI_EMBEDDING_DEPLOYMENT: ${{ secrets.AZURE_OPENAI_EMBEDDING_DEPLOYMENT }}
        run: |
          uv run pytest tests/integration/ -v --cov=dev_agent.llm --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
```

### Best Practices for CI/CD

1. **Run on Schedule**: Run integration tests weekly, not on every commit
2. **Use Secrets**: Store Azure credentials in GitHub Secrets
3. **Monitor Costs**: Track API usage in Azure Portal
4. **Fail Fast**: Use `-x` flag to stop on first failure
5. **Parallel Execution**: Use `pytest-xdist` for parallel test execution

## Maintenance

### Adding New Tests

1. Follow the existing test structure
2. Use descriptive test names: `test_real_<feature>_<scenario>`
3. Add docstrings with requirements references
4. Keep tests focused and independent
5. Mock external dependencies except Azure OpenAI

### Updating Tests

1. Update tests when API changes
2. Verify cost estimates are current
3. Update documentation when adding features
4. Maintain backward compatibility

### Monitoring

1. Track test execution times
2. Monitor API costs per test run
3. Review test failures and patterns
4. Update performance benchmarks

## Support

For issues or questions:
- Review main documentation: `docs/configuration/azure-openai.md`
- Check troubleshooting guide: `docs/configuration/troubleshooting.md`
- Open an issue on GitHub with test logs
- Include environment details and error messages
