# Design Document

## Overview

This design document outlines the implementation of Google Gemini API support for dev-agent. The implementation follows the existing Azure OpenAI integration architecture, using the same abstract interfaces (ILLMClient and IEmbeddingClient) to ensure seamless provider switching and maintain code consistency across the application.

The Gemini integration will support:
- **Code Generation**: Using Gemini Pro, Gemini Pro Vision, and Gemini Ultra models
- **Embeddings**: Using Gemini's embedding models (embedding-001, text-embedding-004)
- **Provider Selection**: Runtime selection between Azure OpenAI and Gemini
- **Cost Tracking**: Token usage and cost monitoring for Gemini API calls
- **Error Handling**: Comprehensive error handling with Gemini-specific guidance

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  (Workflow, Generation, Analysis, CLI)                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  LLM Factory Layer                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  create_llm_client(config) -> ILLMClient             │  │
│  │  create_embedding_client(config) -> IEmbeddingClient │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
┌──────────────────┐      ┌──────────────────┐
│ Azure OpenAI     │      │ Gemini API       │
│ Implementation   │      │ Implementation   │
├──────────────────┤      ├──────────────────┤
│ AzureOpenAIClient│      │ GeminiClient     │
│ AzureEmbedding   │      │ GeminiEmbedding  │
│ Client           │      │ Client           │
└──────────────────┘      └──────────────────┘
        │                         │
        ▼                         ▼
┌──────────────────┐      ┌──────────────────┐
│ Azure OpenAI API │      │ Google Gemini API│
└──────────────────┘      └──────────────────┘
```

### Provider Selection Flow

```
Configuration Loading
        │
        ▼
┌─────────────────────────────────────┐
│ Check PREFERRED_LLM_PROVIDER env    │
│ - "azure" → Azure OpenAI            │
│ - "gemini" → Google Gemini          │
│ - Not set → Azure OpenAI (default)  │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│ Validate Provider Credentials       │
│ - Azure: AZURE_OPENAI_API_KEY       │
│ - Gemini: GEMINI_API_KEY            │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│ Create Provider-Specific Clients    │
│ via Factory Pattern                 │
└─────────────────────────────────────┘
```

## Components and Interfaces

### 1. Configuration Models

#### GeminiConfig (Pydantic Model)

```python
class GeminiConfig(BaseModel):
    """Google Gemini API configuration.
    
    Attributes:
        api_key: Gemini API key (SecretStr for security)
        model_name: Model for code generation (gemini-pro, gemini-ultra)
        embedding_model: Model for embeddings (embedding-001, text-embedding-004)
        api_endpoint: Gemini API endpoint (default: generativelanguage.googleapis.com)
        max_output_tokens: Maximum tokens for generation (1-8192)
        temperature: Sampling temperature (0.0-2.0)
        top_p: Nucleus sampling parameter (0.0-1.0)
        top_k: Top-k sampling parameter (1-100)
        max_retries: Maximum retry attempts (0-10)
        timeout: Request timeout in seconds (1-300)
        batch_size: Batch size for embeddings (1-100)
        safety_settings: Content filtering levels
    """
    
    api_key: SecretStr
    model_name: str = "gemini-pro"
    embedding_model: str = "embedding-001"
    api_endpoint: str = "generativelanguage.googleapis.com"
    max_output_tokens: int = Field(default=2048, ge=1, le=8192)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.95, ge=0.0, le=1.0)
    top_k: int = Field(default=40, ge=1, le=100)
    max_retries: int = Field(default=3, ge=0, le=10)
    timeout: int = Field(default=60, ge=1, le=300)
    batch_size: int = Field(default=16, ge=1, le=100)
    safety_settings: dict[str, str] = Field(default_factory=dict)
```

#### LLMProvider Enum

```python
class LLMProvider(str, Enum):
    """Supported LLM providers."""
    
    AZURE_OPENAI = "azure"
    GEMINI = "gemini"
```

### 2. Gemini LLM Client

#### GeminiClient (implements ILLMClient)

**File**: `dev_agent/llm/gemini_client.py`

**Key Methods**:
- `__init__(config: GeminiConfig)`: Initialize Gemini client with configuration
- `async generate_completion(...)`: Generate text completion using Gemini API
- `async generate_streaming(...)`: Stream completion tokens in real-time
- `count_tokens(text: str)`: Count tokens using Gemini's token counting API
- `estimate_cost(...)`: Calculate cost based on Gemini pricing

**Implementation Details**:
- Uses `google-generativeai` SDK for API calls
- Implements retry logic with tenacity (exponential backoff)
- Handles Gemini-specific errors (quota exceeded, safety filters, etc.)
- Supports safety settings for content filtering
- Tracks token usage for cost estimation

**Error Handling**:
- `google.api_core.exceptions.PermissionDenied` → LLMAuthenticationError
- `google.api_core.exceptions.ResourceExhausted` → LLMRateLimitError
- `google.api_core.exceptions.DeadlineExceeded` → LLMTimeoutError
- `google.api_core.exceptions.InvalidArgument` → LLMBadRequestError
- `google.api_core.exceptions.GoogleAPIError` → LLMAPIError

### 3. Gemini Embedding Client

#### GeminiEmbeddingClient (implements IEmbeddingClient)

**File**: `dev_agent/llm/gemini_embeddings.py`

**Key Methods**:
- `__init__(config: GeminiConfig, cache_dir: Path)`: Initialize with caching
- `async embed_text(text: str)`: Generate single embedding
- `async embed_batch(texts: list[str])`: Generate batch embeddings
- `@property dimension`: Return embedding dimension (768 for embedding-001)

**Implementation Details**:
- Uses `google-generativeai` SDK for embedding generation
- Implements disk-based caching (same as Azure implementation)
- Batch processing with configurable batch size
- Progress tracking for large batches
- Compatible with existing FAISS vector database

**Embedding Models**:
- `embedding-001`: 768 dimensions, optimized for text similarity
- `text-embedding-004`: 768 dimensions, latest model with improved performance

### 4. LLM Factory

#### Factory Functions

**File**: `dev_agent/llm/__init__.py`

```python
def create_llm_client(
    provider: LLMProvider | str | None = None,
    config: AzureOpenAIConfig | GeminiConfig | None = None,
) -> ILLMClient:
    """Create LLM client based on provider.
    
    Args:
        provider: LLM provider (azure, gemini, or None for auto-detect)
        config: Provider-specific configuration
        
    Returns:
        ILLMClient implementation for the specified provider
        
    Raises:
        ValueError: If provider is unsupported or config is invalid
    """

def create_embedding_client(
    provider: LLMProvider | str | None = None,
    config: AzureOpenAIConfig | GeminiConfig | None = None,
    cache_dir: Path | None = None,
) -> IEmbeddingClient:
    """Create embedding client based on provider.
    
    Args:
        provider: LLM provider (azure, gemini, or None for auto-detect)
        config: Provider-specific configuration
        cache_dir: Directory for embedding cache
        
    Returns:
        IEmbeddingClient implementation for the specified provider
        
    Raises:
        ValueError: If provider is unsupported or config is invalid
    """
```

**Provider Detection Logic**:
1. If `provider` is explicitly specified, use that provider
2. If `provider` is None, check `PREFERRED_LLM_PROVIDER` environment variable
3. If environment variable is not set, default to Azure OpenAI
4. Validate that required credentials are available for the selected provider

### 5. Configuration Manager Updates

#### ConfigManager Enhancements

**File**: `dev_agent/config/config_manager.py`

**New Methods**:
- `load_gemini_config()`: Load Gemini configuration from environment
- `get_llm_provider()`: Determine which provider to use
- `validate_provider_config()`: Validate provider-specific configuration

**Environment Variables**:
```bash
# Provider Selection
PREFERRED_LLM_PROVIDER=gemini  # or "azure" (default)

# Gemini Configuration
GEMINI_API_KEY=your-api-key-here
GEMINI_MODEL_NAME=gemini-pro
GEMINI_EMBEDDING_MODEL=embedding-001
GEMINI_API_ENDPOINT=generativelanguage.googleapis.com
GEMINI_MAX_OUTPUT_TOKENS=2048
GEMINI_TEMPERATURE=0.7
GEMINI_TOP_P=0.95
GEMINI_TOP_K=40
GEMINI_MAX_RETRIES=3
GEMINI_TIMEOUT=60
GEMINI_BATCH_SIZE=16
```

## Data Models

### Token Usage Tracking

```python
@dataclass
class TokenUsage:
    """Token usage for a single API call."""
    
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    provider: LLMProvider
    timestamp: datetime
    cost: float
```

### Cost Tracking

```python
class CostTracker:
    """Track API usage and costs across providers."""
    
    def record_completion(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str,
        provider: LLMProvider,
    ) -> None:
        """Record completion usage."""
    
    def record_embedding(
        self,
        tokens: int,
        model: str,
        provider: LLMProvider,
    ) -> None:
        """Record embedding usage."""
    
    def get_report(self) -> dict[str, Any]:
        """Generate usage report by provider."""
    
    def get_total_cost(self) -> float:
        """Get total cost across all providers."""
```

## Error Handling

### Gemini-Specific Exceptions

All Gemini errors are mapped to existing LLM exception types:

```python
# Gemini Error → dev-agent Exception
google.api_core.exceptions.PermissionDenied → LLMAuthenticationError
google.api_core.exceptions.ResourceExhausted → LLMRateLimitError
google.api_core.exceptions.DeadlineExceeded → LLMTimeoutError
google.api_core.exceptions.InvalidArgument → LLMBadRequestError
google.api_core.exceptions.GoogleAPIError → LLMAPIError
```

### Error Messages

Error messages include provider-specific guidance:

```python
# Azure OpenAI
"Failed to authenticate with Azure OpenAI using API key. "
"Check that AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT are set correctly."

# Gemini
"Failed to authenticate with Google Gemini API. "
"Check that GEMINI_API_KEY is set correctly. "
"Get your API key at: https://makersuite.google.com/app/apikey"
```

### Retry Strategy

Both providers use the same retry strategy:
- **Transient Errors**: Rate limits, timeouts → Retry with exponential backoff
- **Permanent Errors**: Authentication, bad request → Fail immediately
- **Max Retries**: 3 attempts (configurable)
- **Backoff**: 4s, 16s, 64s (exponential with multiplier=1, min=4, max=60)

## Testing Strategy

### Unit Tests

**Test Files**:
- `tests/test_gemini_client.py`: Test GeminiClient implementation
- `tests/test_gemini_embeddings.py`: Test GeminiEmbeddingClient implementation
- `tests/test_llm_factory.py`: Test factory functions and provider selection
- `tests/test_gemini_config.py`: Test GeminiConfig validation

**Test Coverage**:
- Mock all Gemini API calls (never call real API in unit tests)
- Test error handling for all Gemini exception types
- Test retry logic with simulated failures
- Test token counting and cost estimation
- Test provider selection logic
- Test configuration validation

**Mock Strategy**:
```python
@pytest.fixture
def mock_gemini_client():
    """Mock Gemini client for testing."""
    with patch('google.generativeai.GenerativeModel') as mock:
        mock_model = MagicMock()
        mock_model.generate_content.return_value = MagicMock(
            text="Generated code here",
            usage_metadata=MagicMock(
                prompt_token_count=100,
                candidates_token_count=200,
                total_token_count=300,
            ),
        )
        mock.return_value = mock_model
        yield mock
```

### Integration Tests

**Test Files**:
- `tests/integration/test_gemini_integration.py`: Real Gemini API tests

**Gating**:
```python
@pytest.mark.skipif(
    os.getenv("GEMINI_INTEGRATION_TESTS") != "true",
    reason="Integration tests disabled - set GEMINI_INTEGRATION_TESTS=true",
)
@pytest.mark.asyncio
async def test_real_gemini_api():
    """Integration test with real Gemini API."""
    config = GeminiConfig(
        api_key=SecretStr(os.getenv("GEMINI_API_KEY")),
        model_name="gemini-pro",
    )
    
    client = GeminiClient(config)
    result = await client.generate_completion("Say hello")
    
    assert len(result) > 0
    assert isinstance(result, str)
```

### Provider Switching Tests

**Test Scenarios**:
- Switch from Azure OpenAI to Gemini at runtime
- Use both providers in the same session
- Verify embeddings from both providers work with FAISS
- Verify cost tracking separates providers correctly

## Dependencies

### New Dependencies

Add to `pyproject.toml`:

```toml
[project.dependencies]
# Existing dependencies...
google-generativeai = ">=0.3.0"  # Google Gemini API SDK
google-api-core = ">=2.15.0"     # Google API core utilities
```

### Version Constraints

- `google-generativeai`: >=0.3.0 (latest stable version)
- `google-api-core`: >=2.15.0 (for error handling)
- Python: >=3.10 (same as existing requirement)

## Migration Path

### Backward Compatibility

- **Default Provider**: Azure OpenAI remains the default provider
- **Existing Code**: No changes required to existing code
- **Configuration**: Existing Azure OpenAI configuration continues to work
- **Gradual Adoption**: Users can opt-in to Gemini by setting environment variables

### Migration Steps

1. **Install Dependencies**: `uv sync --dev` to install new dependencies
2. **Set Environment Variables**: Configure Gemini API key and preferences
3. **Test Configuration**: Run `dev-agent status` to verify provider setup
4. **Switch Provider**: Set `PREFERRED_LLM_PROVIDER=gemini` to use Gemini
5. **Monitor Costs**: Use cost tracking to compare provider costs

## Security Considerations

### API Key Management

- **SecretStr**: All API keys stored as Pydantic SecretStr
- **Never Logged**: API keys never appear in logs or error messages
- **Environment Variables**: Credentials only via environment variables
- **No Hardcoding**: No API keys in code or configuration files
- **Redaction**: JSON serialization automatically redacts credentials

### Data Privacy

- **Azure OpenAI**: Data stays within Azure tenant
- **Gemini**: Data sent to Google Cloud (review Google's data policies)
- **Compliance**: Document data flow for security reviews
- **Audit Logging**: Log API calls without sensitive data

### Rate Limiting

- **Respect Limits**: Implement exponential backoff for rate limits
- **Batch Optimization**: Use batch processing to reduce API calls
- **Caching**: Cache embeddings to avoid redundant API calls
- **Cost Alerts**: Warn users when approaching budget thresholds

## Performance Considerations

### Latency

- **Azure OpenAI**: Typically 1-3 seconds for completions
- **Gemini**: Typically 1-2 seconds for completions (may vary)
- **Embeddings**: Batch processing reduces latency overhead
- **Caching**: Embedding cache eliminates redundant API calls

### Throughput

- **Concurrent Requests**: Support up to 5 concurrent batches
- **Batch Size**: Optimize batch size per provider (16 for both)
- **Connection Pooling**: Reuse HTTP connections for efficiency

### Cost Optimization

- **Model Selection**: Use appropriate model for task complexity
- **Token Limits**: Validate token counts before API calls
- **Caching**: Aggressive caching for embeddings
- **Monitoring**: Track costs per provider for optimization

## Documentation Updates

### New Documentation Files

1. **docs/configuration/gemini-setup.md**: Gemini API setup guide
2. **docs/usage/provider-selection.md**: How to choose and switch providers
3. **docs/examples/gemini-usage.md**: Gemini-specific examples
4. **docs/api/gemini.md**: Gemini client API reference

### Updated Documentation Files

1. **docs/installation.md**: Add Gemini dependencies
2. **docs/configuration/environment.md**: Add Gemini environment variables
3. **docs/usage/cost-management.md**: Add Gemini pricing information
4. **README.md**: Mention Gemini support in features list

### Example Code

```python
# Example: Using Gemini for code generation
from dev_agent.llm import create_llm_client
from dev_agent.models.llm_config import GeminiConfig
from pydantic import SecretStr

config = GeminiConfig(
    api_key=SecretStr("your-api-key-here"),
    model_name="gemini-pro",
    temperature=0.7,
)

client = create_llm_client(provider="gemini", config=config)

# Generate code
code = await client.generate_completion(
    prompt="Write a Python function to calculate fibonacci numbers",
    system_prompt="You are a Python expert",
)

print(code)
```

## Future Enhancements

### Phase 2 Features

1. **Multi-Provider Fallback**: Automatically fallback to secondary provider on failure
2. **Cost-Based Selection**: Automatically select cheapest provider for task
3. **Performance Comparison**: A/B testing between providers
4. **Provider-Specific Optimizations**: Leverage unique features of each provider

### Additional Providers

1. **AWS Bedrock**: Support Claude 3 models
2. **Anthropic Direct**: Direct Claude API integration
3. **Local Models**: Support for local LLMs (Ollama, LM Studio)

## Implementation Checklist

- [ ] Create GeminiConfig Pydantic model
- [ ] Implement GeminiClient (ILLMClient)
- [ ] Implement GeminiEmbeddingClient (IEmbeddingClient)
- [ ] Create LLM factory functions
- [ ] Update ConfigManager for Gemini support
- [ ] Add LLMProvider enum
- [ ] Update CostTracker for multi-provider support
- [ ] Write unit tests for Gemini client
- [ ] Write unit tests for Gemini embeddings
- [ ] Write integration tests (gated)
- [ ] Update documentation
- [ ] Add example code
- [ ] Test provider switching
- [ ] Verify FAISS compatibility
- [ ] Update CLI to show active provider
- [ ] Add provider selection to `dev-agent init`
