# Design Document: Azure OpenAI Integration

## Overview

This design document outlines the technical architecture for completing the Azure OpenAI integration in dev-agent. The system will establish a clean LLM abstraction layer, integrate Azure OpenAI across all workflow phases, implement token management and cost tracking, and provide robust error handling with caching strategies.

### Goals

1. Create a provider-agnostic LLM abstraction layer for future extensibility
2. Integrate Azure OpenAI as the exclusive AI provider for all operations
3. Implement comprehensive token tracking and cost management
4. Provide efficient embedding generation with intelligent caching
5. Ensure robust error handling with automatic retry and recovery
6. Maintain high test coverage with comprehensive mocking
7. Remove local model dependencies from core requirements

### Non-Goals

1. Support for multiple LLM providers simultaneously (future enhancement)
2. Fine-tuning custom models (future enhancement)
3. Local model fallback (removed to simplify architecture)
4. Real-time streaming UI updates (CLI streaming only)

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                           │
│                    (CLI / Interactive Mode)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      Workflow Manager                            │
│              (Orchestrates 4-Phase Workflow)                     │
└─┬──────────────┬──────────────┬──────────────┬─────────────────┘
  │              │              │              │
  │ Indexing     │ Specification│ Design       │ Implementation
  │ Phase        │ Phase        │ Phase        │ Phase
  │              │              │              │
  └──────────────┴──────────────┴──────────────┴─────────────────┘
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
│              Azure OpenAI Client Implementation                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Azure        │  │ Azure        │  │ Cost         │          │
│  │ LLM Client   │  │ Embedding    │  │ Tracker      │          │
│  │              │  │ Client       │  │              │          │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘          │
│         │                 │                                      │
│         │  ┌──────────────▼────────────┐                        │
│         │  │  Embedding Cache          │                        │
│         │  │  (Disk-based, SHA-256)    │                        │
│         │  └───────────────────────────┘                        │
└─────────┼─────────────────┼────────────────────────────────────┘
          │                 │
          │  Retry Logic    │  Batch Processing
          │  (tenacity)     │  (16 texts/batch)
          │                 │
┌─────────▼─────────────────▼────────────────────────────────────┐
│                    Azure OpenAI API                              │
│         (GPT-4 + text-embedding-ada-002)                        │
└─────────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

**Specification Generation Flow:**
```
User Request → Workflow Manager → Specification Generator
                                        ↓
                                  Retrieve Context
                                  (Vector Search)
                                        ↓
                                  Build Prompt
                                  (Template + Context)
                                        ↓
                                  Azure LLM Client
                                        ↓
                                  Token Counter
                                  (Pre-flight check)
                                        ↓
                                  Azure OpenAI API
                                  (GPT-4 Completion)
                                        ↓
                                  Cost Tracker
                                  (Record usage)
                                        ↓
                                  Save Document
                                        ↓
                                  Return to User
```

**Embedding Generation Flow:**
```
Code Chunks → Indexing Engine → Azure Embedding Client
                                        ↓
                                  Check Cache
                                  (SHA-256 hash)
                                        ↓
                                  Cache Hit? → Return Cached
                                        ↓ No
                                  Batch Texts
                                  (16 per batch)
                                        ↓
                                  Azure OpenAI API
                                  (text-embedding-ada-002)
                                        ↓
                                  Store in Cache
                                        ↓
                                  Store in FAISS
                                        ↓
                                  Return Embeddings
```

## Components and Interfaces

### 1. LLM Abstraction Layer (`dev_agent/llm/`)

#### 1.1 Base Interfaces (`dev_agent/llm/base.py`)

**ILLMClient Interface:**
```python
from abc import ABC, abstractmethod
from typing import AsyncIterator

class ILLMClient(ABC):
    """Abstract interface for LLM providers."""
    
    @abstractmethod
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> str:
        """Generate text completion."""
        
    @abstractmethod
    async def generate_streaming(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream completion tokens."""
        
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        
    @abstractmethod
    def estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """Estimate cost for token usage."""
```

**IEmbeddingClient Interface:**
```python
class IEmbeddingClient(ABC):
    """Abstract interface for embedding providers."""
    
    @abstractmethod
    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for single text."""
        
    @abstractmethod
    async def embed_batch(
        self,
        texts: list[str],
        batch_size: int = 16,
    ) -> list[list[float]]:
        """Generate embeddings for batch of texts."""
        
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding dimension size."""
```

#### 1.2 Azure OpenAI Client (`dev_agent/llm/azure_client.py`)

**Purpose:** Implements ILLMClient for Azure OpenAI with retry logic and error handling.

**Key Features:**
- Async API calls using `AsyncAzureOpenAI`
- Exponential backoff retry with tenacity
- Streaming support for real-time feedback
- Token counting with tiktoken
- Cost estimation based on Azure pricing
- Comprehensive error handling

**Dependencies:**
- `openai` (AsyncAzureOpenAI)
- `tiktoken` (token counting)
- `tenacity` (retry logic)
- `dev_agent.models.llm_config` (AzureOpenAIConfig)

**Error Handling:**
- `AuthenticationError` → `LLMAuthenticationError`
- `RateLimitError` → Automatic retry with backoff
- `APITimeoutError` → Retry with increased timeout
- `BadRequestError` → `LLMBadRequestError`
- `APIError` → `LLMAPIError`

#### 1.3 Azure Embedding Client (`dev_agent/llm/embeddings.py`)

**Purpose:** Implements IEmbeddingClient with caching and batch processing.

**Key Features:**
- Batch embedding generation (16 texts per API call)
- Disk-based caching with SHA-256 content hashing
- Cache invalidation on model changes
- Async batch processing
- Progress tracking for large batches

**Cache Structure:**
```
.dev_agent/embedding_cache/
├── {sha256_hash}.json  # Individual embedding cache files
└── cache_metadata.json # Cache statistics and model info
```

**Cache Entry Format:**
```json
{
  "text_hash": "sha256_hash",
  "model": "text-embedding-ada-002",
  "dimension": 1536,
  "embedding": [0.1, 0.2, ...],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### 1.4 Token Counter (`dev_agent/llm/token_counter.py`)

**Purpose:** Accurate token counting and cost estimation.

**Key Features:**
- Uses tiktoken for GPT-4 token counting
- Validates context window limits
- Estimates costs before API calls
- Tracks cumulative usage per session

**Token Limits:**
- GPT-4: 8,192 tokens (standard)
- GPT-4-32k: 32,768 tokens
- GPT-4-turbo: 128,000 tokens

**Cost Calculation (Example Azure Pricing):**
- GPT-4 Prompt: $0.03 per 1K tokens
- GPT-4 Completion: $0.06 per 1K tokens
- text-embedding-ada-002: $0.0001 per 1K tokens

#### 1.5 Cost Tracker (`dev_agent/llm/cost_tracker.py`)

**Purpose:** Track and report API usage and costs.

**Key Features:**
- Per-operation token tracking
- Per-phase cost aggregation
- Session-level cost reporting
- Budget threshold warnings

**Tracked Metrics:**
- Prompt tokens
- Completion tokens
- Embedding tokens
- Total cost (USD)
- Operations count
- Average tokens per operation

#### 1.6 Prompt Templates (`dev_agent/llm/prompt_templates.py`)

**Purpose:** Structured prompts for each workflow phase.

**Template Structure:**
```python
@dataclass
class PromptTemplate:
    """Structured prompt template."""
    
    system_prompt: str
    user_prompt_template: str
    required_context: list[str]
    max_context_tokens: int
    temperature: float
    max_tokens: int
```

**Templates:**
1. **Specification Generation Template**
   - System: "You are a technical specification writer..."
   - Context: Codebase summary, relevant examples, patterns
   - Output: Structured specification with requirements

2. **Design Generation Template**
   - System: "You are a software architect..."
   - Context: Specification, existing architecture, patterns
   - Output: Technical design document

3. **Code Generation Template**
   - System: "You are a Python developer..."
   - Context: Design, similar code, style guide
   - Output: Python code with type hints and docstrings

4. **Task Generation Template**
   - System: "You are a technical project manager..."
   - Context: Design, requirements, complexity
   - Output: Incremental task breakdown

### 2. Data Models (`dev_agent/models/`)

#### 2.1 LLM Configuration Models (`dev_agent/models/llm_config.py`)

**AzureOpenAIConfig (Enhanced):**
```python
from pydantic import BaseModel, Field, SecretStr, field_validator

class AzureOpenAIConfig(BaseModel):
    """Azure OpenAI configuration with validation."""
    
    endpoint: str = Field(..., description="Azure OpenAI endpoint URL")
    api_key: SecretStr = Field(..., description="Azure OpenAI API key")
    api_version: str = Field(default="2024-02-15-preview")
    deployment_name: str = Field(..., description="GPT-4 deployment")
    embedding_deployment: str = Field(..., description="Embedding deployment")
    max_tokens: int = Field(default=4000, ge=1, le=128000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_retries: int = Field(default=3, ge=0, le=10)
    timeout: int = Field(default=60, ge=1, le=300)
    batch_size: int = Field(default=16, ge=1, le=100)
    
    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(cls, v: str) -> str:
        """Validate endpoint URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("Endpoint must start with http:// or https://")
        return v
    
    class Config:
        json_encoders = {SecretStr: lambda v: "***REDACTED***"}
```

#### 2.2 LLM Response Models (`dev_agent/models/llm_responses.py`)

**CompletionResponse:**
```python
@dataclass
class CompletionResponse:
    """Response from LLM completion."""
    
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    finish_reason: str
    estimated_cost: float
```

**EmbeddingResponse:**
```python
@dataclass
class EmbeddingResponse:
    """Response from embedding generation."""
    
    embeddings: list[list[float]]
    model: str
    total_tokens: int
    dimension: int
    estimated_cost: float
    cache_hits: int
    cache_misses: int
```

#### 2.3 Cost Tracking Models (`dev_agent/models/cost_tracking.py`)

**TokenUsage:**
```python
@dataclass
class TokenUsage:
    """Token usage for an operation."""
    
    operation_type: str  # "completion", "embedding", "streaming"
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float
    timestamp: datetime
    phase: PhaseType
```

**CostReport:**
```python
@dataclass
class CostReport:
    """Cost report for a session or phase."""
    
    total_prompt_tokens: int
    total_completion_tokens: int
    total_embedding_tokens: int
    total_cost: float
    operations_count: int
    by_phase: dict[PhaseType, float]
    by_operation: dict[str, int]
    start_time: datetime
    end_time: datetime
```

#### 2.4 Enhanced Enums (`dev_agent/models/enums.py`)

**Add LLMProvider Enum:**
```python
class LLMProvider(Enum):
    """Supported LLM providers."""
    
    AZURE_OPENAI = "azure_openai"
    # Future: AWS_BEDROCK = "aws_bedrock"
```

**Add LLMOperationType Enum:**
```python
class LLMOperationType(Enum):
    """Types of LLM operations."""
    
    COMPLETION = "completion"
    STREAMING = "streaming"
    EMBEDDING = "embedding"
    TOKEN_COUNT = "token_count"
```

### 3. Error Handling (`dev_agent/errors/`)

#### 3.1 LLM Exceptions (`dev_agent/errors/llm_exceptions.py`)

**Exception Hierarchy:**
```python
class LLMError(Exception):
    """Base exception for LLM operations."""
    pass

class LLMAuthenticationError(LLMError):
    """Authentication failed with LLM provider."""
    pass

class LLMRateLimitError(LLMError):
    """Rate limit exceeded."""
    pass

class LLMTimeoutError(LLMError):
    """Request timed out."""
    pass

class LLMBadRequestError(LLMError):
    """Invalid request parameters."""
    pass

class LLMAPIError(LLMError):
    """General API error."""
    pass

class LLMTokenLimitError(LLMError):
    """Token limit exceeded."""
    pass

class LLMCostLimitError(LLMError):
    """Cost limit exceeded."""
    pass
```

### 4. Integration with Existing Components

#### 4.1 Workflow Manager Integration

**Changes to `dev_agent/workflow/workflow_manager.py`:**
- Inject `ILLMClient` and `IEmbeddingClient` via dependency injection
- Track token usage per phase
- Display cost summaries after each phase
- Save token usage to project state

#### 4.2 Generation Components Integration

**Changes to `dev_agent/generation/` modules:**
- Replace direct Azure OpenAI service calls with `ILLMClient`
- Use prompt templates from `llm/prompt_templates.py`
- Implement context injection from vector search
- Add token validation before generation

**Affected Files:**
- `specification_generator.py`
- `design_generator.py`
- `task_generator.py`
- `python_code_generator.py`

#### 4.3 Indexing Engine Integration

**Changes to `dev_agent/indexing/indexing_engine.py`:**
- Use `IEmbeddingClient` instead of direct service calls
- Implement batch processing with progress tracking
- Use embedding cache for efficiency
- Track embedding tokens and costs

#### 4.4 Vector Database Integration

**Changes to `dev_agent/indexing/vector_database.py`:**
- Accept `IEmbeddingClient` in constructor
- Remove local model fallback logic
- Simplify to Azure OpenAI only
- Improve error handling

## Data Flow

### Specification Generation Data Flow

```
1. User Request
   ↓
2. Workflow Manager (Specification Phase)
   ↓
3. Specification Generator
   ├─→ Vector DB: Query similar code (top 5)
   ├─→ Pattern Analyzer: Detect patterns
   └─→ Build Context
   ↓
4. Prompt Template
   ├─→ Inject codebase summary
   ├─→ Inject relevant examples
   └─→ Inject detected patterns
   ↓
5. Token Counter
   ├─→ Count prompt tokens
   ├─→ Validate < 8K limit
   └─→ Estimate cost
   ↓
6. Azure LLM Client
   ├─→ Retry logic (tenacity)
   └─→ API call (GPT-4)
   ↓
7. Azure OpenAI API
   ↓
8. Response Processing
   ├─→ Extract content
   ├─→ Record token usage
   └─→ Calculate actual cost
   ↓
9. Cost Tracker
   ├─→ Update session totals
   └─→ Check budget thresholds
   ↓
10. Save Document
    ├─→ .dev_agent/documents/specification.md
    └─→ Update project state
    ↓
11. Display to User
    ├─→ Show specification
    ├─→ Show token usage
    └─→ Show estimated cost
```

### Embedding Generation Data Flow

```
1. Code Chunks (from Tree-sitter)
   ↓
2. Indexing Engine
   ├─→ Extract text content
   └─→ Batch into groups of 16
   ↓
3. Azure Embedding Client
   ↓
4. For each text:
   ├─→ Generate SHA-256 hash
   ├─→ Check cache
   │   ├─→ Cache hit: Return cached embedding
   │   └─→ Cache miss: Continue
   ↓
5. Batch uncached texts
   ↓
6. Azure OpenAI API
   ├─→ text-embedding-ada-002
   └─→ Return 1536-dim vectors
   ↓
7. Cache new embeddings
   ├─→ Save to disk (JSON)
   └─→ Update cache metadata
   ↓
8. Store in FAISS
   ├─→ Add vectors to index
   └─→ Store chunk metadata
   ↓
9. Cost Tracker
   ├─→ Record embedding tokens
   └─→ Calculate cost
   ↓
10. Return to Indexing Engine
```

## Error Handling Strategy

### Retry Logic

**Transient Errors (Automatic Retry):**
- Rate limit errors (429)
- Timeout errors
- Connection errors
- Server errors (5xx)

**Retry Configuration:**
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((RateLimitError, APITimeoutError)),
    before_sleep=log_retry_attempt,
)
```

**Permanent Errors (No Retry):**
- Authentication errors (401)
- Bad request errors (400)
- Not found errors (404)
- Token limit exceeded

### Error Recovery

**State Preservation:**
- Save project state before each API call
- Store partial responses on streaming errors
- Allow resume from last successful operation

**User Guidance:**
- Clear error messages with resolution steps
- Link to documentation for common errors
- Suggest checking Azure OpenAI service status

## Testing Strategy

### Unit Tests

**Mock Strategy:**
```python
@pytest.fixture
def mock_azure_client():
    """Mock Azure OpenAI client."""
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        return_value=MagicMock(
            choices=[MagicMock(
                message=MagicMock(content="Generated content"),
                finish_reason="stop",
            )],
            usage=MagicMock(
                prompt_tokens=100,
                completion_tokens=200,
                total_tokens=300,
            ),
        )
    )
    return client
```

**Test Coverage:**
- LLM client methods (completion, streaming, token counting)
- Embedding client methods (single, batch, caching)
- Error handling (all exception types)
- Retry logic (exponential backoff)
- Token counting accuracy
- Cost calculation accuracy
- Cache hit/miss scenarios

### Integration Tests

**Gated by Environment Variable:**
```python
@pytest.mark.skipif(
    os.getenv("AZURE_OPENAI_INTEGRATION_TESTS") != "true",
    reason="Integration tests disabled",
)
@pytest.mark.asyncio
async def test_real_azure_completion():
    """Test with real Azure OpenAI API."""
    # Real API call
```

**Integration Test Scenarios:**
- End-to-end specification generation
- End-to-end code generation
- Embedding generation and vector search
- Cost tracking across workflow phases
- Error recovery and retry

### Performance Tests

**Benchmarks:**
- Embedding generation: <5s per 100 chunks
- Completion generation: <10s for 1000 token response
- Vector search: <100ms for 100K chunk database
- Cache lookup: <10ms per embedding

## Security Considerations

### API Key Management

**Storage:**
- Environment variables (preferred)
- Config files with restricted permissions (0600)
- Never in version control (.gitignore)

**Usage:**
- Pydantic SecretStr for in-memory handling
- Never logged or displayed
- Redacted in error messages

### Data Privacy

**Code Privacy:**
- Code sent only to user's Azure tenant
- No third-party services
- Complies with Azure compliance requirements

**Audit Logging:**
- Log all API calls (without sensitive data)
- Track token usage per user/session
- Monitor for unusual patterns

## Performance Optimization

### Embedding Cache

**Cache Strategy:**
- Content-based hashing (SHA-256)
- Disk-based storage (JSON files)
- LRU eviction for large caches
- Model-specific cache keys

**Cache Performance:**
- Hit rate target: >80% for repeated indexing
- Lookup time: <10ms per embedding
- Storage: ~6KB per cached embedding (1536 dims)

### Batch Processing

**Embedding Batches:**
- Batch size: 16 texts per API call
- Parallel batches: Up to 3 concurrent
- Progress tracking: Every 100 chunks

**API Call Optimization:**
- Reuse HTTP connections
- Async concurrent requests
- Connection pooling

### Token Management

**Context Window Optimization:**
- Intelligent truncation of context
- Prioritize recent and relevant code
- Summarize large contexts

## Migration Plan

### Phase 1: Core Infrastructure
1. Create LLM abstraction layer
2. Implement Azure OpenAI client
3. Add token counter and cost tracker
4. Create prompt templates

### Phase 2: Integration
1. Update workflow manager
2. Update generation components
3. Update indexing engine
4. Update vector database

### Phase 3: Testing & Documentation
1. Add comprehensive unit tests
2. Add integration tests
3. Update documentation
4. Create examples

### Phase 4: Cleanup
1. Remove local model dependencies
2. Update pyproject.toml
3. Update steering docs
4. Final testing

## Deployment Considerations

### Configuration

**Environment Variables:**
```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

**Config File Location:**
- Global: `~/.dev_agent/dev_agent_config.json`
- Project: `.dev_agent/config.json`

### Monitoring

**Metrics to Track:**
- API call success/failure rates
- Average response times
- Token usage trends
- Cost per operation
- Cache hit rates

### Troubleshooting

**Common Issues:**
1. Authentication failures → Check API key and endpoint
2. Rate limits → Reduce concurrent requests
3. Timeout errors → Increase timeout setting
4. Token limit exceeded → Reduce context size
5. High costs → Review token usage patterns

## Future Enhancements

### AWS Bedrock Integration
- Implement BedrockClient following ILLMClient interface
- Support Claude 3 models
- Add provider selection in configuration
- Implement fallback between providers

### Cost Optimization
- Automatic model selection based on task complexity
- Use GPT-3.5 Turbo for simple tasks
- Implement budget limits and warnings
- Cost prediction before operations

### Advanced Features
- Fine-tuned models for code generation
- Custom embeddings for domain-specific code
- Multi-region deployment support
- Caching layer for common queries
- Prompt optimization based on feedback

## Appendix

### A. File Structure

```
dev_agent/
├── llm/                          # NEW
│   ├── __init__.py
│   ├── base.py                   # Abstract interfaces
│   ├── azure_client.py           # Azure OpenAI client
│   ├── embeddings.py             # Embedding client
│   ├── token_counter.py          # Token counting
│   ├── cost_tracker.py           # Cost tracking
│   └── prompt_templates.py       # Prompt templates
├── models/
│   ├── llm_config.py             # NEW: LLM config models
│   ├── llm_responses.py          # NEW: Response models
│   ├── cost_tracking.py          # NEW: Cost models
│   └── enums.py                  # UPDATED: Add LLM enums
├── errors/
│   └── llm_exceptions.py         # NEW: LLM exceptions
├── services/
│   └── azure_openai_service.py   # UPDATED: Use new client
├── generation/
│   ├── specification_generator.py # UPDATED
│   ├── design_generator.py        # UPDATED
│   ├── task_generator.py          # UPDATED
│   └── python_code_generator.py   # UPDATED
├── indexing/
│   ├── indexing_engine.py         # UPDATED
│   └── vector_database.py         # UPDATED
└── workflow/
    └── workflow_manager.py        # UPDATED
```

### B. Dependencies

**New Dependencies:**
```toml
[project]
dependencies = [
    "openai>=1.50.0",      # Azure OpenAI SDK
    "tiktoken>=0.6.0",     # Token counting
    "tenacity>=8.2.0",     # Retry logic
    # ... existing dependencies
]
```

**Removed from Core:**
```toml
[project.optional-dependencies]
local-embeddings = [
    "sentence-transformers>=3.3.0",  # Optional only
]
```

### C. Configuration Schema

**Complete Configuration:**
```json
{
  "azure_openai": {
    "endpoint": "https://your-resource.openai.azure.com/",
    "api_key": "***",
    "api_version": "2024-02-15-preview",
    "deployment_name": "gpt-4",
    "embedding_deployment": "text-embedding-ada-002",
    "max_tokens": 4000,
    "temperature": 0.7,
    "max_retries": 3,
    "timeout": 60,
    "batch_size": 16
  },
  "indexing": {
    "use_azure_embeddings": true,
    "chunk_size": 1000,
    "overlap_size": 200,
    "max_files_per_batch": 100
  },
  "cost_tracking": {
    "enabled": true,
    "budget_warning_threshold": 10.0,
    "budget_limit": 50.0
  }
}
```
