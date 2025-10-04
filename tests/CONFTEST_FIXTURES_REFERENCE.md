# Conftest.py Fixtures Reference

## Overview

This document provides a comprehensive reference for all fixtures available in `tests/conftest.py`. These fixtures are automatically available to all test files in the project.

## Quick Start

```python
# In any test file, simply use the fixture as a parameter
def test_my_feature(mock_llm_client, mock_cost_tracker):
    # Fixtures are automatically injected by pytest
    result = my_function(mock_llm_client)
    assert result is not None
```

## Available Fixtures

### Configuration Fixtures

#### `azure_config`
Returns a test Azure OpenAI configuration.

**Type:** `AzureOpenAIConfig`

**Usage:**
```python
def test_with_config(azure_config):
    assert azure_config.endpoint == "https://test-resource.openai.azure.com/"
    assert azure_config.deployment_name == "gpt-4"
```

**Configuration:**
- Endpoint: `https://test-resource.openai.azure.com/`
- API Key: `test-api-key` (SecretStr)
- API Version: `2024-02-15-preview`
- Deployment: `gpt-4`
- Embedding Deployment: `text-embedding-ada-002`
- Max Tokens: 4000
- Temperature: 0.7
- Max Retries: 3
- Timeout: 60s
- Batch Size: 16

#### `temp_cache_dir`
Returns a temporary cache directory for testing.

**Type:** `Path`

**Usage:**
```python
def test_with_cache(temp_cache_dir):
    cache_file = temp_cache_dir / "test.json"
    cache_file.write_text('{"test": "data"}')
    assert cache_file.exists()
```

---

### Azure OpenAI Client Mocks

#### `mock_azure_openai_client`
Returns a fully mocked `AsyncAzureOpenAI` client.

**Type:** `AsyncMock`

**Default Behavior:**
- Completion responses return "Generated completion text"
- Token usage: 100 prompt + 200 completion = 300 total
- Embedding responses return 1536-dimensional vectors
- Embedding token usage: 10 tokens

**Usage:**
```python
def test_with_azure_client(mock_azure_openai_client):
    # Use default behavior
    response = await mock_azure_openai_client.chat.completions.create(...)
    
    # Or customize for specific test
    mock_azure_openai_client.chat.completions.create.return_value = custom_response
```

#### `mock_streaming_response`
Returns a mock streaming response generator.

**Type:** `AsyncMock`

**Default Behavior:**
Yields three chunks: "Hello", " world", "!"

**Usage:**
```python
@pytest.mark.asyncio
async def test_streaming(mock_streaming_response):
    chunks = []
    async for chunk in mock_streaming_response:
        chunks.append(chunk.choices[0].delta.content)
    assert chunks == ["Hello", " world", "!"]
```

---

### LLM Client Fixtures

#### `mock_llm_client`
Returns a fully configured `AzureOpenAIClient` with mocked API calls.

**Type:** `AzureOpenAIClient`

**Usage:**
```python
@pytest.mark.asyncio
async def test_generation(mock_llm_client):
    result = await mock_llm_client.generate_completion(
        prompt="Write a function",
        temperature=0.7,
    )
    assert result == "Generated completion text"
```

**Features:**
- Mocked Azure OpenAI API calls
- Token counting enabled
- Cost estimation enabled
- No actual API calls made

#### `mock_embedding_client`
Returns a fully configured `AzureEmbeddingClient` with mocked API calls.

**Type:** `AzureEmbeddingClient`

**Usage:**
```python
@pytest.mark.asyncio
async def test_embeddings(mock_embedding_client):
    embedding = await mock_embedding_client.embed_text("test code")
    assert len(embedding) == 1536
```

**Features:**
- Mocked embedding API calls
- Temporary cache directory
- Batch embedding support
- 1536-dimensional vectors

---

### Cost Tracking Fixtures

#### `mock_cost_tracker`
Returns a `CostTracker` with budget limits configured.

**Type:** `CostTracker`

**Configuration:**
- Current Phase: `PhaseType.INDEXING`
- Budget Threshold: $10.00
- Budget Limit: $50.00

**Usage:**
```python
def test_cost_tracking(mock_cost_tracker):
    cost = mock_cost_tracker.record_completion(100, 200, "gpt-4")
    assert cost > 0
    assert mock_cost_tracker.get_current_cost() == cost
```

#### `cost_tracker_no_budget`
Returns a `CostTracker` without budget constraints.

**Type:** `CostTracker`

**Configuration:**
- Current Phase: `PhaseType.INDEXING`
- No budget threshold
- No budget limit

**Usage:**
```python
def test_unlimited_tracking(cost_tracker_no_budget):
    # Track costs without budget warnings
    cost_tracker_no_budget.record_completion(10000, 20000)
    assert not cost_tracker_no_budget.check_budget_threshold()
```

---

### Token Counter Fixtures

#### `mock_token_counter`
Returns a `TokenCounter` configured for GPT-4.

**Type:** `TokenCounter`

**Configuration:**
- Model: GPT-4
- Context Limit: 8,192 tokens
- Pricing: $0.03/1K prompt, $0.06/1K completion

**Usage:**
```python
def test_token_counting(mock_token_counter):
    count = mock_token_counter.count_tokens("Hello, world!")
    assert count > 0
    
    cost = mock_token_counter.estimate_cost(100, 200)
    assert cost == 0.015  # (100/1000)*0.03 + (200/1000)*0.06
```

#### `token_counter_gpt4_turbo`
Returns a `TokenCounter` configured for GPT-4 Turbo.

**Type:** `TokenCounter`

**Configuration:**
- Model: GPT-4 Turbo
- Context Limit: 128,000 tokens
- Pricing: $0.01/1K prompt, $0.03/1K completion

**Usage:**
```python
def test_large_context(token_counter_gpt4_turbo):
    # Can handle much larger contexts
    is_valid, msg = token_counter_gpt4_turbo.validate_context_window(
        prompt_tokens=100000,
        max_completion_tokens=20000,
    )
    assert is_valid
```

#### `token_counter_gpt35`
Returns a `TokenCounter` configured for GPT-3.5 Turbo.

**Type:** `TokenCounter`

**Configuration:**
- Model: GPT-3.5 Turbo
- Context Limit: 4,096 tokens
- Pricing: $0.0015/1K prompt, $0.002/1K completion

**Usage:**
```python
def test_cost_comparison(token_counter_gpt35, mock_token_counter):
    # GPT-3.5 is cheaper than GPT-4
    cost_gpt35 = token_counter_gpt35.estimate_cost(1000, 1000)
    cost_gpt4 = mock_token_counter.estimate_cost(1000, 1000)
    assert cost_gpt35 < cost_gpt4
```

---

### Helper Fixtures

#### `sample_code_text`
Returns sample Python code for testing.

**Type:** `str`

**Content:**
- `hello_world()` function
- `Calculator` class with `add()` and `subtract()` methods

**Usage:**
```python
def test_code_parsing(sample_code_text):
    assert "def hello_world():" in sample_code_text
    assert "class Calculator:" in sample_code_text
```

#### `sample_code_chunks`
Returns a list of code chunks for testing.

**Type:** `list[str]`

**Content:**
- 5 code chunks (functions, classes, imports)

**Usage:**
```python
def test_batch_processing(sample_code_chunks):
    assert len(sample_code_chunks) == 5
    assert "def function_one():" in sample_code_chunks[0]
```

#### `sample_embeddings`
Returns sample embedding vectors for testing.

**Type:** `list[list[float]]`

**Content:**
- 3 embedding vectors
- Each vector is 1536-dimensional

**Usage:**
```python
def test_embedding_storage(sample_embeddings):
    assert len(sample_embeddings) == 3
    assert all(len(emb) == 1536 for emb in sample_embeddings)
```

---

### Mock Response Builders

These are helper functions (not fixtures) that create mock responses.

#### `create_mock_completion_response()`
Creates a mock completion response.

**Parameters:**
- `content` (str): Response content (default: "Generated text")
- `prompt_tokens` (int): Prompt token count (default: 100)
- `completion_tokens` (int): Completion token count (default: 200)
- `model` (str): Model name (default: "gpt-4")

**Returns:** `MagicMock`

**Usage:**
```python
def test_custom_response(mock_azure_openai_client):
    custom_response = create_mock_completion_response(
        content="Custom output",
        prompt_tokens=50,
        completion_tokens=100,
    )
    mock_azure_openai_client.chat.completions.create.return_value = custom_response
```

#### `create_mock_embedding_response()`
Creates a mock embedding response.

**Parameters:**
- `count` (int): Number of embeddings (default: 1)
- `dimension` (int): Embedding dimension (default: 1536)
- `tokens` (int): Total tokens used (default: 10)
- `model` (str): Model name (default: "text-embedding-ada-002")

**Returns:** `MagicMock`

**Usage:**
```python
def test_batch_embeddings(mock_azure_openai_client):
    batch_response = create_mock_embedding_response(count=5, tokens=50)
    mock_azure_openai_client.embeddings.create.return_value = batch_response
```

#### `create_mock_streaming_chunks()`
Creates mock streaming chunks.

**Parameters:**
- `texts` (list[str]): List of text chunks to stream

**Returns:** `list[MagicMock]`

**Usage:**
```python
def test_custom_streaming(mock_azure_openai_client):
    chunks = create_mock_streaming_chunks(["First", "Second", "Third"])
    
    async def mock_stream():
        for chunk in chunks:
            yield chunk
    
    mock_azure_openai_client.chat.completions.create.return_value = mock_stream()
```

---

## Advanced Usage

### Customizing Fixtures Per Test

```python
def test_with_custom_behavior(mock_llm_client):
    # Override default behavior for this specific test
    mock_llm_client.generate_completion.return_value = "Custom response"
    
    result = await mock_llm_client.generate_completion("test")
    assert result == "Custom response"
```

### Using Multiple Fixtures

```python
@pytest.mark.asyncio
async def test_full_workflow(
    mock_llm_client,
    mock_embedding_client,
    mock_cost_tracker,
    mock_token_counter,
):
    # Use multiple fixtures together
    mock_cost_tracker.set_phase(PhaseType.SPECIFICATION)
    
    # Generate completion
    result = await mock_llm_client.generate_completion("test")
    
    # Generate embeddings
    embedding = await mock_embedding_client.embed_text("test")
    
    # Verify costs were tracked
    assert mock_cost_tracker.get_current_cost() > 0
```

### Testing Error Scenarios

```python
@pytest.mark.asyncio
async def test_api_error(mock_llm_client, mock_azure_openai_client):
    from openai import APIError
    
    # Make the mock raise an error
    mock_azure_openai_client.chat.completions.create.side_effect = APIError(
        "API error",
        request=MagicMock(),
        body=None,
    )
    
    # Test error handling
    with pytest.raises(LLMAPIError):
        await mock_llm_client.generate_completion("test")
```

### Testing Retry Logic

```python
@pytest.mark.asyncio
async def test_retry_success(mock_llm_client, mock_azure_openai_client):
    from openai import RateLimitError
    
    call_count = 0
    
    async def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RateLimitError("Rate limit", response=MagicMock(), body=None)
        return create_mock_completion_response()
    
    mock_azure_openai_client.chat.completions.create.side_effect = side_effect
    
    result = await mock_llm_client.generate_completion("test")
    assert call_count == 2  # Should have retried once
```

---

## Pytest Configuration

### Custom Markers

The conftest.py defines these custom markers:

- **`@pytest.mark.integration`** - Tests requiring real Azure OpenAI API
- **`@pytest.mark.slow`** - Slow-running tests
- **`@pytest.mark.asyncio`** - Async tests

**Usage:**
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_api():
    # This test calls the real Azure OpenAI API
    # Only runs when AZURE_OPENAI_INTEGRATION_TESTS=true
    pass
```

### Event Loop

An event loop fixture is provided for async tests:

```python
@pytest.mark.asyncio
async def test_async_operation(event_loop):
    # event_loop is automatically available
    result = await some_async_function()
    assert result is not None
```

---

## Best Practices

### 1. Use Fixtures Instead of Creating Mocks
❌ **Don't:**
```python
def test_something():
    mock_client = AsyncMock()
    mock_client.generate_completion.return_value = "test"
    # ...
```

✅ **Do:**
```python
def test_something(mock_llm_client):
    mock_llm_client.generate_completion.return_value = "test"
    # ...
```

### 2. Customize Only When Needed
❌ **Don't:**
```python
def test_something(mock_llm_client):
    # Reconfiguring everything
    mock_llm_client.config = AzureOpenAIConfig(...)
    mock_llm_client.client = AsyncMock()
    # ...
```

✅ **Do:**
```python
def test_something(mock_llm_client):
    # Only override what's needed
    mock_llm_client.generate_completion.return_value = "custom"
    # ...
```

### 3. Keep Test-Specific Fixtures Local
If a fixture is truly unique to one test file, keep it in that file:

```python
# In test_my_feature.py
@pytest.fixture
def special_test_data():
    # This is unique to this test file
    return {"special": "data"}
```

### 4. Use Type Hints
```python
from dev_agent.llm.azure_client import AzureOpenAIClient

def test_something(mock_llm_client: AzureOpenAIClient):
    # Type hints help with IDE autocomplete
    result = await mock_llm_client.generate_completion("test")
```

---

## Troubleshooting

### Fixture Not Found
If pytest can't find a fixture:
1. Ensure `conftest.py` is in the `tests/` directory
2. Check that the fixture name matches exactly
3. Verify pytest is discovering the conftest.py file

### Mock Not Behaving as Expected
If a mock isn't working:
1. Check if you're using `await` for async methods
2. Verify you're using `return_value` for sync methods and `AsyncMock` for async
3. Use `side_effect` for more complex behavior

### Import Errors
If you get import errors:
1. Ensure all dependencies are installed
2. Check that the module paths are correct
3. Verify the project structure matches expectations

---

## Summary

The `conftest.py` file provides 19 fixtures and 3 helper functions that cover all common testing scenarios for Azure OpenAI integration:

- ✅ Configuration fixtures for test setup
- ✅ Mocked Azure OpenAI clients (no real API calls)
- ✅ LLM and embedding client fixtures
- ✅ Cost tracking and token counting fixtures
- ✅ Sample data for testing
- ✅ Helper functions for custom responses
- ✅ Pytest configuration and markers

All fixtures are well-documented, type-safe, and ready to use in any test file.
