# LLM Integration Development Guide

This guide is for developers working on the LLM integration layer in dev-agent.

## Architecture Overview

The LLM integration follows a clean architecture pattern with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Application Layer                             │
│         (Workflow Manager, Generators, CLI)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    LLM Abstraction Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ ILLMClient   │  │IEmbedding    │  │ Token        │          │
│  │ Interface    │  │Client        │  │ Counter      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│              Azure OpenAI Implementation                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Azure        │  │ Azure        │  │ Cost         │          │
│  │ LLM Client   │  │ Embedding    │  │ Tracker      │          │
│  │              │  │ Client       │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## Design Principles

### 1. Provider Agnostic

The abstraction layer is designed to support multiple LLM providers:

```python
# Abstract interface
class ILLMClient(ABC):
    @abstractmethod
    async def generate_completion(self, prompt: str, **kwargs) -> str:
        pass

# Azure OpenAI implementation
class AzureOpenAIClient(ILLMClient):
    async def generate_completion(self, prompt: str, **kwargs) -> str:
        # Azure-specific implementation
        pass

# Future: AWS Bedrock implementation
class BedrockClient(ILLMClient):
    async def generate_completion(self, prompt: str, **kwargs) -> str:
        # Bedrock-specific implementation
        pass
```

### 2. Async First

All I/O operations use async/await for non-blocking execution:

```python
# ✅ CORRECT - Async pattern
async def generate_spec(self, context: str) -> str:
    response = await self.llm_client.generate_completion(context)
    return response

# ❌ WRONG - Blocking call
def generate_spec(self, context: str) -> str:
    response = self.llm_client.generate_completion(context)  # Blocks!
    return response
```

### 3. Dependency Injection

Components receive dependencies through constructor injection:

```python
class SpecificationGenerator:
    def __init__(
        self,
        llm_client: ILLMClient,
        vector_db: VectorDatabase,
        cost_tracker: CostTracker,
    ):
        self.llm_client = llm_client
        self.vector_db = vector_db
        self.cost_tracker = cost_tracker
```

### 4. Error Handling

Use specific exception types with proper error context:

```python
try:
    response = await self.client.chat.completions.create(...)
except AuthenticationError as e:
    raise LLMAuthenticationError("Invalid Azure OpenAI credentials") from e
except RateLimitError as e:
    raise LLMRateLimitError("Azure OpenAI rate limit exceeded") from e
```

## Adding a New LLM Provider

To add support for a new LLM provider (e.g., AWS Bedrock):

### Step 1: Implement ILLMClient

```python
# dev_agent/llm/bedrock_client.py
from dev_agent.llm.base import ILLMClient
from dev_agent.models.llm_config import BedrockConfig

class BedrockClient(ILLMClient):
    """AWS Bedrock LLM client implementation."""
    
    def __init__(self, config: BedrockConfig):
        self.config = config
        # Initialize Bedrock client
    
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> str:
        """Generate completion using AWS Bedrock."""
        # Implementation
        pass
    
    async def generate_streaming(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream completion tokens."""
        # Implementation
        pass
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        # Implementation
        pass
    
    def estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """Estimate cost for token usage."""
        # Implementation
        pass
```

### Step 2: Create Configuration Model

```python
# dev_agent/models/llm_config.py
from pydantic import BaseModel, Field, SecretStr

class BedrockConfig(BaseModel):
    """AWS Bedrock configuration."""
    
    region: str = Field(..., description="AWS region")
    access_key_id: SecretStr = Field(..., description="AWS access key")
    secret_access_key: SecretStr = Field(..., description="AWS secret key")
    model_id: str = Field(..., description="Model ID (e.g., anthropic.claude-3)")
    max_tokens: int = Field(default=4000, ge=1, le=200000)
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
```

### Step 3: Add Provider Enum

```python
# dev_agent/models/enums.py
class LLMProvider(Enum):
    """Supported LLM providers."""
    
    AZURE_OPENAI = "azure_openai"
    AWS_BEDROCK = "aws_bedrock"  # New provider
```

### Step 4: Create Factory

```python
# dev_agent/llm/__init__.py
from dev_agent.llm.base import ILLMClient
from dev_agent.llm.azure_client import AzureOpenAIClient
from dev_agent.llm.bedrock_client import BedrockClient
from dev_agent.models.enums import LLMProvider

def create_llm_client(provider: LLMProvider, config) -> ILLMClient:
    """Factory function to create LLM client."""
    
    if provider == LLMProvider.AZURE_OPENAI:
        return AzureOpenAIClient(config)
    elif provider == LLMProvider.AWS_BEDROCK:
        return BedrockClient(config)
    else:
        raise ValueError(f"Unsupported provider: {provider}")
```

### Step 5: Add Tests

```python
# tests/test_bedrock_client.py
import pytest
from unittest.mock import AsyncMock
from dev_agent.llm.bedrock_client import BedrockClient

@pytest.fixture
def mock_bedrock_client():
    """Mock Bedrock client."""
    # Implementation
    pass

@pytest.mark.asyncio
async def test_bedrock_completion(mock_bedrock_client):
    """Test Bedrock completion."""
    # Test implementation
    pass
```

## Token Counting

### Implementing Token Counting

Token counting is provider-specific. For Azure OpenAI, we use tiktoken:

```python
import tiktoken

def count_tokens(self, text: str, model: str = "gpt-4") -> int:
    """Count tokens using tiktoken."""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception as e:
        logger.warning(f"Token counting failed: {e}")
        # Fallback: rough estimate
        return len(text.split()) * 1.3
```

For other providers, implement appropriate token counting:

```python
# AWS Bedrock (Claude models)
def count_tokens(self, text: str) -> int:
    """Count tokens for Claude models."""
    # Claude uses different tokenization
    # Implement using Anthropic's tokenizer
    pass
```

## Cost Estimation

### Implementing Cost Calculation

Cost calculation is provider and model-specific:

```python
class AzureOpenAIClient:
    # Azure OpenAI pricing (example)
    PRICING = {
        "gpt-4": {
            "prompt": 0.03 / 1000,  # $0.03 per 1K tokens
            "completion": 0.06 / 1000,  # $0.06 per 1K tokens
        },
        "gpt-4-turbo": {
            "prompt": 0.01 / 1000,
            "completion": 0.03 / 1000,
        },
    }
    
    def estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """Estimate cost based on token usage."""
        model = self.config.deployment_name
        pricing = self.PRICING.get(model, self.PRICING["gpt-4"])
        
        prompt_cost = prompt_tokens * pricing["prompt"]
        completion_cost = completion_tokens * pricing["completion"]
        
        return prompt_cost + completion_cost
```

## Retry Logic

### Implementing Retry with Tenacity

Use tenacity for resilient API calls:

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((RateLimitError, APITimeoutError)),
    before_sleep=lambda retry_state: logger.warning(
        f"Retry attempt {retry_state.attempt_number} after {retry_state.outcome.exception()}"
    ),
)
async def _call_with_retry(self, **kwargs):
    """Call API with automatic retry."""
    return await self.client.chat.completions.create(**kwargs)
```

### Retry Configuration

Make retry behavior configurable:

```python
class AzureOpenAIConfig(BaseModel):
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_min_wait: int = Field(default=4, ge=1, le=60)
    retry_max_wait: int = Field(default=60, ge=1, le=300)
```

## Streaming Implementation

### Implementing Streaming Responses

Streaming provides real-time feedback:

```python
async def generate_streaming(
    self,
    prompt: str,
    system_prompt: str | None = None,
) -> AsyncIterator[str]:
    """Stream completion tokens."""
    
    response = await self.client.chat.completions.create(
        model=self.config.deployment_name,
        messages=[
            {"role": "system", "content": system_prompt or ""},
            {"role": "user", "content": prompt},
        ],
        stream=True,
        temperature=self.config.temperature,
        max_tokens=self.config.max_tokens,
    )
    
    async for chunk in response:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

### Using Streaming in CLI

```python
async def generate_with_streaming(prompt: str):
    """Generate with streaming output."""
    
    print("Generating response...")
    async for chunk in client.generate_streaming(prompt):
        print(chunk, end="", flush=True)
    print("\n")
```

## Embedding Cache

### Cache Implementation

The embedding cache uses SHA-256 hashing:

```python
import hashlib
import json
from pathlib import Path

class EmbeddingCache:
    def _get_cache_key(self, text: str, model: str) -> str:
        """Generate cache key from text and model."""
        content = f"{model}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get(self, text: str, model: str) -> list[float] | None:
        """Get cached embedding."""
        key = self._get_cache_key(text, model)
        cache_file = self.cache_dir / f"{key}.json"
        
        if cache_file.exists():
            data = json.loads(cache_file.read_text())
            return data["embedding"]
        return None
    
    def set(self, text: str, model: str, embedding: list[float]) -> None:
        """Cache embedding."""
        key = self._get_cache_key(text, model)
        cache_file = self.cache_dir / f"{key}.json"
        
        data = {
            "text_hash": key,
            "model": model,
            "embedding": embedding,
            "timestamp": datetime.now().isoformat(),
        }
        
        cache_file.write_text(json.dumps(data))
```

### Cache Invalidation

Invalidate cache when model changes:

```python
def invalidate_model_cache(self, old_model: str, new_model: str) -> None:
    """Invalidate cache entries for old model."""
    
    for cache_file in self.cache_dir.glob("*.json"):
        data = json.loads(cache_file.read_text())
        if data["model"] == old_model:
            cache_file.unlink()
```

## Testing Guidelines

### Unit Testing

Mock all external API calls:

```python
@pytest.fixture
def mock_azure_client():
    """Mock Azure OpenAI client."""
    client = AsyncMock()
    
    client.chat.completions.create = AsyncMock(
        return_value=MagicMock(
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
    )
    
    return client

@pytest.mark.asyncio
async def test_generate_completion(mock_azure_client):
    """Test completion generation."""
    config = AzureOpenAIConfig(...)
    client = AzureOpenAIClient(config, client=mock_azure_client)
    
    response = await client.generate_completion("test prompt")
    
    assert response == "Generated content"
    mock_azure_client.chat.completions.create.assert_called_once()
```

### Integration Testing

Gate integration tests with environment variable:

```python
@pytest.mark.skipif(
    os.getenv("AZURE_OPENAI_INTEGRATION_TESTS") != "true",
    reason="Integration tests disabled",
)
@pytest.mark.asyncio
async def test_real_azure_completion():
    """Integration test with real API."""
    config = AzureOpenAIConfig(
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=SecretStr(os.getenv("AZURE_OPENAI_API_KEY")),
        # ... other config
    )
    
    client = AzureOpenAIClient(config)
    response = await client.generate_completion("Say hello")
    
    assert len(response) > 0
    assert isinstance(response, str)
```

### Testing Error Handling

Test all error scenarios:

```python
@pytest.mark.asyncio
async def test_authentication_error(mock_azure_client):
    """Test authentication error handling."""
    mock_azure_client.chat.completions.create.side_effect = AuthenticationError("Invalid key")
    
    client = AzureOpenAIClient(config, client=mock_azure_client)
    
    with pytest.raises(LLMAuthenticationError):
        await client.generate_completion("test")

@pytest.mark.asyncio
async def test_rate_limit_retry(mock_azure_client):
    """Test rate limit retry logic."""
    # First call fails, second succeeds
    mock_azure_client.chat.completions.create.side_effect = [
        RateLimitError("Rate limit"),
        MagicMock(choices=[MagicMock(message=MagicMock(content="success"))]),
    ]
    
    client = AzureOpenAIClient(config, client=mock_azure_client)
    response = await client.generate_completion("test")
    
    assert response == "success"
    assert mock_azure_client.chat.completions.create.call_count == 2
```

## Performance Optimization

### Batch Processing

Optimize embedding generation with batching:

```python
async def embed_batch(
    self,
    texts: list[str],
    batch_size: int = 16,
) -> list[list[float]]:
    """Generate embeddings in batches."""
    
    embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        # Check cache first
        cached_embeddings = []
        uncached_texts = []
        
        for text in batch:
            cached = self.cache.get(text, self.model)
            if cached:
                cached_embeddings.append(cached)
            else:
                uncached_texts.append(text)
        
        # Generate embeddings for uncached texts
        if uncached_texts:
            response = await self.client.embeddings.create(
                model=self.model,
                input=uncached_texts,
            )
            
            new_embeddings = [item.embedding for item in response.data]
            
            # Cache new embeddings
            for text, embedding in zip(uncached_texts, new_embeddings):
                self.cache.set(text, self.model, embedding)
            
            embeddings.extend(new_embeddings)
        
        embeddings.extend(cached_embeddings)
    
    return embeddings
```

### Concurrent Requests

Use asyncio for concurrent API calls:

```python
async def generate_multiple(
    self,
    prompts: list[str],
    max_concurrent: int = 3,
) -> list[str]:
    """Generate completions concurrently."""
    
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def generate_with_semaphore(prompt: str) -> str:
        async with semaphore:
            return await self.generate_completion(prompt)
    
    tasks = [generate_with_semaphore(p) for p in prompts]
    return await asyncio.gather(*tasks)
```

## Security Considerations

### API Key Management

Never log or expose API keys:

```python
from pydantic import BaseModel, SecretStr

class AzureOpenAIConfig(BaseModel):
    api_key: SecretStr  # Automatically redacted
    
    class Config:
        json_encoders = {
            SecretStr: lambda v: "***REDACTED***"
        }

# Usage
config = AzureOpenAIConfig(api_key=SecretStr("secret-key"))
print(config)  # api_key=SecretStr('***REDACTED***')
```

### Input Validation

Validate all inputs:

```python
def validate_prompt(prompt: str) -> str:
    """Validate and sanitize prompt."""
    
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty")
    
    if len(prompt) > 100000:  # Reasonable limit
        raise ValueError("Prompt too long")
    
    return prompt.strip()
```

## Monitoring and Logging

### Structured Logging

Use structured logging for better observability:

```python
import logging
import structlog

logger = structlog.get_logger(__name__)

async def generate_completion(self, prompt: str) -> str:
    """Generate completion with logging."""
    
    logger.info(
        "generating_completion",
        prompt_length=len(prompt),
        model=self.config.deployment_name,
    )
    
    try:
        response = await self._call_api(prompt)
        
        logger.info(
            "completion_generated",
            response_length=len(response),
            tokens=self.count_tokens(response),
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "completion_failed",
            error=str(e),
            error_type=type(e).__name__,
        )
        raise
```

### Metrics Collection

Track key metrics:

```python
from prometheus_client import Counter, Histogram

# Define metrics
api_calls_total = Counter(
    "llm_api_calls_total",
    "Total LLM API calls",
    ["provider", "operation", "status"],
)

api_latency = Histogram(
    "llm_api_latency_seconds",
    "LLM API call latency",
    ["provider", "operation"],
)

# Use metrics
async def generate_completion(self, prompt: str) -> str:
    """Generate completion with metrics."""
    
    start_time = time.time()
    
    try:
        response = await self._call_api(prompt)
        
        api_calls_total.labels(
            provider="azure_openai",
            operation="completion",
            status="success",
        ).inc()
        
        return response
        
    except Exception as e:
        api_calls_total.labels(
            provider="azure_openai",
            operation="completion",
            status="error",
        ).inc()
        raise
        
    finally:
        duration = time.time() - start_time
        api_latency.labels(
            provider="azure_openai",
            operation="completion",
        ).observe(duration)
```

## Additional Resources

- [Azure OpenAI Setup Guide](../configuration/azure-openai.md)
- [API Documentation](../api/llm.md)
- [Testing Guidelines](testing.md)
- [Architecture Overview](architecture.md)
