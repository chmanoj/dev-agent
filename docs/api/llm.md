# LLM Integration API

This document provides comprehensive API documentation for the LLM integration layer in dev-agent.

## Overview

The LLM integration layer provides a clean abstraction for interacting with Azure OpenAI services. It includes:

- **LLM Client**: Generate completions and stream responses
- **Embedding Client**: Generate and cache embeddings
- **Token Counter**: Count tokens and estimate costs
- **Cost Tracker**: Track usage and costs
- **Prompt Templates**: Structured prompts for each workflow phase

## Module Structure

```
dev_agent/llm/
├── base.py              # Abstract interfaces
├── azure_client.py      # Azure OpenAI LLM client
├── embeddings.py        # Embedding client
├── token_counter.py     # Token counting
├── cost_tracker.py      # Cost tracking
├── prompt_templates.py  # Prompt templates
└── embedding_cache.py   # Embedding cache
```

## Base Interfaces

::: dev_agent.llm.base.ILLMClient
    options:
      show_source: true
      heading_level: 3

::: dev_agent.llm.base.IEmbeddingClient
    options:
      show_source: true
      heading_level: 3

## Azure OpenAI Client

::: dev_agent.llm.azure_client.AzureOpenAIClient
    options:
      show_source: true
      heading_level: 3
      members:
        - __init__
        - generate_completion
        - generate_streaming
        - count_tokens
        - estimate_cost

### Usage Example

```python
import asyncio
import os
from dev_agent.llm.azure_client import AzureOpenAIClient
from dev_agent.models.llm_config import AzureOpenAIConfig
from pydantic import SecretStr

async def main():
    config = AzureOpenAIConfig(
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=SecretStr(os.getenv("AZURE_OPENAI_API_KEY")),
        api_version="2024-02-15-preview",
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
    )
    
    client = AzureOpenAIClient(config)
    
    # Generate completion
    response = await client.generate_completion(
        prompt="Write a Python function to calculate fibonacci",
        system_prompt="You are a Python expert.",
        temperature=0.7,
        max_tokens=500,
    )
    
    print(response)

asyncio.run(main())
```

## Embedding Client

::: dev_agent.llm.embeddings.AzureEmbeddingClient
    options:
      show_source: true
      heading_level: 3
      members:
        - __init__
        - embed_text
        - embed_batch
        - dimension

### Usage Example

```python
import asyncio
import os
from dev_agent.llm.embeddings import AzureEmbeddingClient
from dev_agent.models.llm_config import AzureOpenAIConfig
from pydantic import SecretStr

async def main():
    config = AzureOpenAIConfig(
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=SecretStr(os.getenv("AZURE_OPENAI_API_KEY")),
        api_version="2024-02-15-preview",
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
    )
    
    client = AzureEmbeddingClient(config)
    
    # Single embedding
    embedding = await client.embed_text("def hello(): print('Hello')")
    print(f"Embedding dimension: {len(embedding)}")
    
    # Batch embeddings
    texts = ["code1", "code2", "code3"]
    embeddings = await client.embed_batch(texts, batch_size=16)
    print(f"Generated {len(embeddings)} embeddings")

asyncio.run(main())
```

## Token Counter

::: dev_agent.llm.token_counter.TokenCounter
    options:
      show_source: true
      heading_level: 3
      members:
        - __init__
        - count_tokens
        - estimate_cost
        - validate_context_window

### Usage Example

```python
from dev_agent.llm.token_counter import TokenCounter

counter = TokenCounter()

# Count tokens
text = "This is a sample text for token counting"
token_count = counter.count_tokens(text)
print(f"Token count: {token_count}")

# Estimate cost
cost = counter.estimate_cost(
    prompt_tokens=1000,
    completion_tokens=500,
)
print(f"Estimated cost: ${cost:.4f}")

# Validate context window
is_valid = counter.validate_context_window(
    text=text,
    model="gpt-4",
    max_tokens=8192,
)
print(f"Within context window: {is_valid}")
```

## Cost Tracker

::: dev_agent.llm.cost_tracker.CostTracker
    options:
      show_source: true
      heading_level: 3
      members:
        - __init__
        - add_completion
        - add_embedding_tokens
        - calculate_cost
        - get_report
        - check_budget_threshold

### Usage Example

```python
from dev_agent.llm.cost_tracker import CostTracker

tracker = CostTracker()

# Track completion
tracker.add_completion(
    prompt_tokens=1000,
    completion_tokens=500,
)

# Track embeddings
tracker.add_embedding_tokens(50000)

# Get report
report = tracker.get_report()
print(f"Total tokens: {report['total_tokens']:,}")
print(f"Total cost: ${report['estimated_cost']:.2f}")

# Check budget
tracker.check_budget_threshold(budget_limit=10.0)
```

## Embedding Cache

::: dev_agent.llm.embedding_cache.EmbeddingCache
    options:
      show_source: true
      heading_level: 3
      members:
        - __init__
        - get
        - set
        - clear
        - get_stats

### Usage Example

```python
from pathlib import Path
from dev_agent.llm.embedding_cache import EmbeddingCache

cache = EmbeddingCache(Path(".dev_agent/embedding_cache"))

# Store embedding
embedding = [0.1, 0.2, 0.3, ...]  # 1536-dimensional vector
cache.set(
    text="def hello(): pass",
    model="text-embedding-ada-002",
    embedding=embedding,
)

# Retrieve embedding
cached = cache.get(
    text="def hello(): pass",
    model="text-embedding-ada-002",
)

if cached:
    print("Cache hit!")
else:
    print("Cache miss")

# Get cache statistics
stats = cache.get_stats()
print(f"Cache entries: {stats['total_entries']}")
print(f"Cache size: {stats['total_size_mb']:.2f} MB")
```

## Prompt Templates

::: dev_agent.llm.prompt_templates
    options:
      show_source: true
      heading_level: 3

### Available Templates

#### Specification Generation Template

```python
from dev_agent.llm.prompt_templates import SPECIFICATION_TEMPLATE

prompt = SPECIFICATION_TEMPLATE.format(
    codebase_summary="Python web application with FastAPI",
    relevant_code_chunks="...",
    detected_patterns="...",
    feature_description="Add user authentication",
)
```

#### Design Generation Template

```python
from dev_agent.llm.prompt_templates import DESIGN_TEMPLATE

prompt = DESIGN_TEMPLATE.format(
    specification="...",
    existing_architecture="...",
    patterns="...",
)
```

#### Code Generation Template

```python
from dev_agent.llm.prompt_templates import CODE_GENERATION_TEMPLATE

prompt = CODE_GENERATION_TEMPLATE.format(
    code_patterns="...",
    similar_code="...",
    specification="...",
)
```

#### Task Generation Template

```python
from dev_agent.llm.prompt_templates import TASK_GENERATION_TEMPLATE

prompt = TASK_GENERATION_TEMPLATE.format(
    design="...",
    requirements="...",
    complexity="medium",
)
```

## Configuration Models

::: dev_agent.models.llm_config.AzureOpenAIConfig
    options:
      show_source: true
      heading_level: 3

### Configuration Example

```python
from dev_agent.models.llm_config import AzureOpenAIConfig
from pydantic import SecretStr

config = AzureOpenAIConfig(
    endpoint="https://my-resource.openai.azure.com/",
    api_key=SecretStr("your-api-key-here"),
    api_version="2024-02-15-preview",
    deployment_name="gpt-4",
    embedding_deployment="text-embedding-ada-002",
    max_tokens=4000,
    temperature=0.7,
    max_retries=3,
    timeout=60,
    batch_size=16,
)

# API key is automatically redacted
print(config)  # Shows: api_key=SecretStr('***REDACTED***')
```

## Response Models

::: dev_agent.models.llm_responses.CompletionResponse
    options:
      show_source: true
      heading_level: 3

::: dev_agent.models.llm_responses.EmbeddingResponse
    options:
      show_source: true
      heading_level: 3

### Response Example

```python
from dev_agent.models.llm_responses import CompletionResponse

response = CompletionResponse(
    content="def fibonacci(n): ...",
    model="gpt-4",
    prompt_tokens=50,
    completion_tokens=100,
    total_tokens=150,
    finish_reason="stop",
    estimated_cost=0.0045,
)

print(f"Generated: {response.content}")
print(f"Cost: ${response.estimated_cost:.4f}")
```

## Cost Tracking Models

::: dev_agent.models.cost_tracking.TokenUsage
    options:
      show_source: true
      heading_level: 3

::: dev_agent.models.cost_tracking.CostReport
    options:
      show_source: true
      heading_level: 3

### Cost Report Example

```python
from dev_agent.models.cost_tracking import CostReport
from datetime import datetime

report = CostReport(
    total_prompt_tokens=10000,
    total_completion_tokens=5000,
    total_embedding_tokens=100000,
    total_cost=1.25,
    operations_count=50,
    by_phase={"indexing": 0.10, "specification": 0.25, "design": 0.40, "implementation": 0.50},
    by_operation={"completion": 30, "embedding": 20},
    start_time=datetime.now(),
    end_time=datetime.now(),
)

print(f"Total cost: ${report.total_cost:.2f}")
print(f"Operations: {report.operations_count}")
```

## Exception Classes

::: dev_agent.errors.llm_exceptions
    options:
      show_source: true
      heading_level: 3

### Exception Hierarchy

```
LLMError (base)
├── LLMAuthenticationError
├── LLMRateLimitError
├── LLMTimeoutError
├── LLMBadRequestError
├── LLMAPIError
├── LLMTokenLimitError
└── LLMCostLimitError
```

### Exception Handling Example

```python
from dev_agent.errors.llm_exceptions import (
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
)

try:
    response = await client.generate_completion(prompt)
except LLMAuthenticationError as e:
    print(f"Authentication failed: {e}")
    # Check API key and endpoint
except LLMRateLimitError as e:
    print(f"Rate limit exceeded: {e}")
    # Automatic retry with backoff
except LLMTimeoutError as e:
    print(f"Request timed out: {e}")
    # Increase timeout or reduce request size
```

## Enums

::: dev_agent.models.enums.LLMProvider
    options:
      show_source: true
      heading_level: 3

::: dev_agent.models.enums.LLMOperationType
    options:
      show_source: true
      heading_level: 3

### Enum Usage Example

```python
from dev_agent.models.enums import LLMProvider, LLMOperationType

# LLM Provider
provider = LLMProvider.AZURE_OPENAI
print(f"Using provider: {provider.value}")

# Operation Type
operation = LLMOperationType.COMPLETION
print(f"Operation type: {operation.value}")
```

## Best Practices

### 1. Always Use Async/Await

```python
# ✅ CORRECT
async def generate_code():
    response = await client.generate_completion(prompt)
    return response

# ❌ WRONG
def generate_code():
    response = client.generate_completion(prompt)  # Blocks!
    return response
```

### 2. Handle Errors Gracefully

```python
# ✅ CORRECT
try:
    response = await client.generate_completion(prompt)
except LLMError as e:
    logger.error(f"LLM error: {e}")
    # Handle error appropriately
    raise

# ❌ WRONG
response = await client.generate_completion(prompt)  # No error handling
```

### 3. Count Tokens Before API Calls

```python
# ✅ CORRECT
token_count = client.count_tokens(prompt)
if token_count > 8000:
    raise ValueError("Prompt too long")
response = await client.generate_completion(prompt)

# ❌ WRONG
response = await client.generate_completion(prompt)  # May exceed limits
```

### 4. Use Caching for Embeddings

```python
# ✅ CORRECT
cache = EmbeddingCache(cache_dir)
client = AzureEmbeddingClient(config, cache=cache)
embeddings = await client.embed_batch(texts)  # Uses cache

# ❌ WRONG
client = AzureEmbeddingClient(config)  # No cache
embeddings = await client.embed_batch(texts)  # Regenerates every time
```

### 5. Track Costs

```python
# ✅ CORRECT
tracker = CostTracker()
response = await client.generate_completion(prompt)
tracker.add_completion(prompt_tokens, completion_tokens)
report = tracker.get_report()

# ❌ WRONG
response = await client.generate_completion(prompt)  # No cost tracking
```

### 6. Use SecretStr for API Keys

```python
# ✅ CORRECT
from pydantic import SecretStr
api_key = SecretStr(os.getenv("AZURE_OPENAI_API_KEY"))
config = AzureOpenAIConfig(api_key=api_key, ...)

# ❌ WRONG
api_key = os.getenv("AZURE_OPENAI_API_KEY")  # Plain string
config = AzureOpenAIConfig(api_key=api_key, ...)  # May be logged
```

## Performance Considerations

### Batch Processing

```python
# ✅ EFFICIENT - Batch embeddings
embeddings = await client.embed_batch(texts, batch_size=16)

# ❌ INEFFICIENT - Individual embeddings
embeddings = []
for text in texts:
    embedding = await client.embed_text(text)
    embeddings.append(embedding)
```

### Concurrent Requests

```python
# ✅ EFFICIENT - Concurrent requests
import asyncio
tasks = [client.generate_completion(p) for p in prompts]
responses = await asyncio.gather(*tasks)

# ❌ INEFFICIENT - Sequential requests
responses = []
for prompt in prompts:
    response = await client.generate_completion(prompt)
    responses.append(response)
```

### Streaming for Long Responses

```python
# ✅ EFFICIENT - Stream for immediate feedback
async for chunk in client.generate_streaming(prompt):
    print(chunk, end="", flush=True)

# ❌ INEFFICIENT - Wait for complete response
response = await client.generate_completion(prompt, max_tokens=4000)
print(response)  # User waits for entire response
```

## Testing

### Mocking Azure OpenAI

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_azure_client():
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        return_value=MagicMock(
            choices=[MagicMock(message=MagicMock(content="test"))],
            usage=MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30),
        )
    )
    return client

@pytest.mark.asyncio
async def test_completion(mock_azure_client):
    llm_client = AzureOpenAIClient(config, client=mock_azure_client)
    response = await llm_client.generate_completion("test")
    assert response == "test"
```

## Additional Resources

- [Azure OpenAI Setup Guide](../configuration/azure-openai.md)
- [Cost Management Guide](../usage/cost-management.md)
- [Usage Examples](../examples/azure-setup.md)
- [Troubleshooting Guide](../configuration/troubleshooting.md)

## API Reference Summary

| Component | Purpose | Key Methods |
|-----------|---------|-------------|
| `AzureOpenAIClient` | Generate completions | `generate_completion()`, `generate_streaming()` |
| `AzureEmbeddingClient` | Generate embeddings | `embed_text()`, `embed_batch()` |
| `TokenCounter` | Count tokens | `count_tokens()`, `estimate_cost()` |
| `CostTracker` | Track costs | `add_completion()`, `get_report()` |
| `EmbeddingCache` | Cache embeddings | `get()`, `set()` |

## Version Information

- **API Version**: 2024-02-15-preview
- **Supported Models**: GPT-4, GPT-4 Turbo, GPT-4o, text-embedding-ada-002
- **Python Version**: 3.10+
- **Dependencies**: openai>=1.50.0, tiktoken>=0.6.0, tenacity>=8.2.0
