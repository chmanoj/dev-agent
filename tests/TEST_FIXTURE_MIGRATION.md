# Test Fixture Migration Guide

## Overview

This document tracks the migration of test fixtures from individual test files to the centralized `conftest.py` file.

## Centralized Fixtures Available in `conftest.py`

### Configuration Fixtures
- `azure_config` - Azure OpenAI configuration for testing
- `temp_cache_dir` - Temporary cache directory

### Azure OpenAI Client Mocks
- `mock_azure_openai_client` - Mock AsyncAzureOpenAI client
- `mock_streaming_response` - Mock streaming response

### LLM Client Fixtures
- `mock_llm_client` - Mock ILLMClient implementation
- `mock_embedding_client` - Mock IEmbeddingClient implementation

### Cost Tracking Fixtures
- `mock_cost_tracker` - CostTracker with budget limits
- `cost_tracker_no_budget` - CostTracker without budget limits

### Token Counter Fixtures
- `mock_token_counter` - TokenCounter for GPT-4
- `token_counter_gpt4_turbo` - TokenCounter for GPT-4 Turbo
- `token_counter_gpt35` - TokenCounter for GPT-3.5 Turbo

### Helper Fixtures
- `sample_code_text` - Sample Python code
- `sample_code_chunks` - List of code chunks
- `sample_embeddings` - Sample embedding vectors

### Mock Response Builders
- `create_mock_completion_response()` - Build completion responses
- `create_mock_embedding_response()` - Build embedding responses
- `create_mock_streaming_chunks()` - Build streaming chunks

## Files That Need Migration

### High Priority (Core LLM Integration)
- [x] `tests/test_azure_llm_client.py` - Already uses fixtures correctly
- [x] `tests/test_azure_embedding_client.py` - Already uses fixtures correctly
- [x] `tests/test_cost_tracker.py` - Already uses fixtures correctly
- [x] `tests/test_token_counter.py` - Already uses fixtures correctly

### Medium Priority (Generation Components)
- [ ] `tests/test_specification_generator.py` - Remove local mock_llm_client, mock_cost_tracker, mock_token_counter
- [ ] `tests/test_design_generator.py` - Remove local mock_llm_client, mock_cost_tracker, mock_token_counter
- [ ] `tests/test_task_generator.py` - Remove local mock_llm_client, mock_cost_tracker, mock_token_counter
- [ ] `tests/test_python_code_generator.py` - Remove local mocks

### Medium Priority (Indexing Components)
- [ ] `tests/test_indexing_engine.py` - Remove local mock_cost_tracker, use mock_embedding_client
- [ ] `tests/test_vector_database.py` - Use mock_embedding_client

### Low Priority (Workflow Components)
- [ ] `tests/test_workflow_orchestration.py` - Remove local mock_cost_tracker
- [ ] `tests/test_workflow_manager.py` - Use centralized fixtures

### Low Priority (Other Components)
- [ ] `tests/test_azure_openai_service.py` - Use centralized fixtures
- [ ] Other test files as needed

## Migration Steps for Each File

1. **Remove local fixture definitions** that duplicate conftest.py fixtures
2. **Update fixture parameters** in test methods to use conftest.py fixtures
3. **Remove unnecessary imports** (AsyncMock, MagicMock if only used for fixtures)
4. **Update fixture names** if they differ from conftest.py conventions
5. **Test the changes** to ensure all tests still pass

## Example Migration

### Before (Local Fixture)
```python
@pytest.fixture
def mock_llm_client(self):
    \"\"\"Create a mock LLM client.\"\"\"
    client = AsyncMock(spec=ILLMClient)
    client.generate_completion = AsyncMock(return_value="Generated text")
    return client

def test_something(self, mock_llm_client):
    # Test code
    pass
```

### After (Using Centralized Fixture)
```python
# No local fixture needed - use conftest.py fixture

def test_something(self, mock_llm_client):
    # Configure mock for specific test if needed
    mock_llm_client.generate_completion.return_value = "Generated text"
    # Test code
    pass
```

## Benefits of Centralized Fixtures

1. **Consistency** - All tests use the same mock configurations
2. **Maintainability** - Update mocks in one place
3. **Reusability** - Fixtures available to all test files
4. **Reduced Duplication** - Less code to maintain
5. **Easier Testing** - Standard fixtures make tests easier to write

## Notes

- Some test files may need custom fixtures for specific test scenarios
- Keep custom fixtures in test files when they're truly unique to that file
- The centralized fixtures provide sensible defaults that work for most tests
- Tests can still customize mock behavior using `mock.return_value` or `mock.side_effect`

## Status

- **Created**: conftest.py with comprehensive fixtures
- **Next Steps**: Migrate test files systematically, starting with high-priority files
- **Testing**: Run full test suite after each migration to ensure no regressions
