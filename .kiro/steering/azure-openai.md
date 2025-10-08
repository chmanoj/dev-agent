# Azure OpenAI Integration Standards

## CRITICAL: Azure OpenAI is the ONLY AI Provider

dev-agent uses **Azure OpenAI exclusively** for all AI operations. No local models, no other providers in the current implementation.

## Architecture Overview

### LLM Integration Layer
All Azure OpenAI interactions go through a clean abstraction layer:

```
User Request → Workflow Manager → LLM Client → Azure OpenAI API
                                      ↓
                                 Retry Logic
                                      ↓
                                Token Counting
                                      ↓
                                Cost Tracking
```

### Core Components

#### 1. LLM Client (`dev_agent/llm/azure_client.py`)
- **Purpose**: Async wrapper around Azure OpenAI SDK
- **Responsibilities**:
  - Manage API connections and credentials
  - Implement retry logic with exponential backoff
  - Handle streaming responses
  - Track token usage and costs
  - Provide error handling and recovery

#### 2. Embedding Client (`dev_agent/llm/embeddings.py`)
- **Purpose**: Generate and cache embeddings
- **Responsibilities**:
  - Batch embedding generation for efficiency
  - Cache embeddings to avoid re-computation
  - Handle text-embedding-ada-002 API calls
  - Manage 1536-dimensional vectors

#### 3. Token Counter (`dev_agent/llm/token_counter.py`)
- **Purpose**: Accurate token counting before API calls
- **Responsibilities**:
  - Use tiktoken for GPT-4 token counting
  - Estimate costs before API calls
  - Validate context window limits
  - Track cumulative token usage

#### 4. Prompt Templates (`dev_agent/llm/prompt_templates.py`)
- **Purpose**: Structured prompts for each workflow phase
- **Responsibilities**:
  - Specification generation prompts
  - Design document prompts
  - Code generation prompts
  - Context injection patterns

#### 5. Cost Tracker (`dev_agent/llm/cost_tracker.py`)
- **Purpose**: Monitor API usage and costs
- **Responsibilities**:
  - Track tokens per operation
  - Calculate costs based on Azure pricing
  - Generate usage reports
  - Warn on budget thresholds

## Configuration (MANDATORY)

### Authentication Methods

dev-agent supports two authentication methods for Azure OpenAI:

1. **API Key Authentication** (default): Simple authentication using API key
2. **Azure AD Authentication**: Enterprise authentication using bearer tokens

When both are configured, bearer token authentication takes precedence.

### Environment Variables (REQUIRED)

**Option A: API Key Authentication (Default)**
```bash
# Azure OpenAI Endpoint (REQUIRED)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# API Key (REQUIRED - NEVER commit to git)
AZURE_OPENAI_API_KEY=your-api-key-here

# API Version (REQUIRED)
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Model Deployments (REQUIRED)
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Optional Configuration
AZURE_OPENAI_MAX_TOKENS=4000
AZURE_OPENAI_TEMPERATURE=0.7
AZURE_OPENAI_MAX_RETRIES=3
AZURE_OPENAI_TIMEOUT=60
AZURE_OPENAI_BATCH_SIZE=16  # For embedding batches
```

**Option B: Azure AD Authentication (Enterprise)**
```bash
# Azure OpenAI Endpoint (REQUIRED)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# Bearer Token (REQUIRED for Azure AD - NEVER commit to git)
AZURE_OPENAI_TOKEN=eyJ0eXAiOiJKV1QiLCJhbGc...

# API Version (REQUIRED)
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Model Deployments (REQUIRED)
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_CHAT_DEPLOYMENT_NAME=gpt-4  # Alternative alias
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Optional: Custom Headers for Auditing
AZURE_OPENAI_USER_SID=A123456
AZURE_OPENAI_CUSTOM_HEADERS={"department": "engineering", "project": "dev-agent"}

# Optional Configuration
AZURE_OPENAI_MAX_TOKENS=4000
AZURE_OPENAI_TEMPERATURE=0.7
AZURE_OPENAI_MAX_RETRIES=3
AZURE_OPENAI_TIMEOUT=60
AZURE_OPENAI_BATCH_SIZE=16
```

### Pydantic Configuration Model
```python
from pydantic import BaseModel, Field, SecretStr, model_validator

class AzureOpenAIConfig(BaseModel):
    """Azure OpenAI configuration with validation and Azure AD support."""
    
    # Endpoint and API version
    endpoint: str = Field(..., description="Azure OpenAI endpoint URL")
    api_version: str = Field(default="2024-02-15-preview")
    
    # Authentication (either api_key or bearer_token required)
    api_key: SecretStr | None = Field(default=None, description="Azure OpenAI API key")
    bearer_token: SecretStr | None = Field(default=None, description="Azure AD bearer token")
    openai_api_type: str = Field(default="azure", description="API type: 'azure' or 'azure_ad'")
    
    # Model deployments
    deployment_name: str = Field(..., description="GPT-4 deployment name")
    embedding_deployment: str = Field(..., description="Embedding deployment name")
    
    # Generation parameters
    max_tokens: int = Field(default=4000, ge=1, le=128000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_retries: int = Field(default=3, ge=0, le=10)
    timeout: int = Field(default=60, ge=1, le=300)
    batch_size: int = Field(default=16, ge=1, le=100)
    
    # Custom headers for auditing
    user_sid: str | None = Field(default=None, description="User session ID for auditing")
    custom_headers: dict[str, str] = Field(default_factory=dict, description="Custom request headers")
    
    @model_validator(mode='after')
    def validate_authentication(self) -> 'AzureOpenAIConfig':
        """Ensure at least one authentication method is configured."""
        if not self.api_key and not self.bearer_token:
            raise ValueError(
                "Either api_key or bearer_token must be provided for authentication"
            )
        
        # Set api_type based on authentication method
        if self.bearer_token:
            self.openai_api_type = "azure_ad"
        
        return self
    
    def get_auth_headers(self) -> dict[str, str]:
        """Build authentication and custom headers."""
        headers = {}
        
        # Add Authorization header for Azure AD
        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token.get_secret_value()}"
        
        # Add custom headers
        headers.update(self.custom_headers)
        
        # Add user_sid if configured
        if self.user_sid:
            headers["user_sid"] = self.user_sid
        
        return headers
    
    def get_api_key_value(self) -> str:
        """Get the appropriate credential value."""
        if self.bearer_token:
            return self.bearer_token.get_secret_value()
        return self.api_key.get_secret_value()
    
    class Config:
        # Prevent sensitive data from being logged or serialized
        json_encoders = {SecretStr: lambda v: "***REDACTED***"}
```

## Implementation Standards

### Async/Await Pattern (MANDATORY)
ALL Azure OpenAI calls MUST be async:

```python
# ✅ CORRECT - Async pattern
async def generate_specification(self, context: str) -> str:
    """Generate specification using Azure OpenAI."""
    response = await self.llm_client.generate_completion(
        prompt=self._build_prompt(context),
        system_prompt="You are a technical specification writer.",
        temperature=0.7,
        max_tokens=4000,
    )
    return response

# ❌ WRONG - Synchronous call
def generate_specification(self, context: str) -> str:
    response = self.llm_client.generate_completion(...)  # Blocks!
    return response
```

### Retry Logic (REQUIRED)
Use tenacity for resilient API calls:

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from openai import RateLimitError, APITimeoutError

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((RateLimitError, APITimeoutError)),
)
async def _call_azure_openai(self, **kwargs) -> str:
    """Call Azure OpenAI with retry logic."""
    response = await self.client.chat.completions.create(**kwargs)
    return response.choices[0].message.content
```

### Token Counting (MANDATORY)
Count tokens BEFORE making API calls:

```python
import tiktoken

def count_tokens(self, text: str, model: str = "gpt-4") -> int:
    """Count tokens in text using tiktoken."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

async def generate_with_validation(self, prompt: str) -> str:
    """Generate with token validation."""
    token_count = self.count_tokens(prompt)
    
    if token_count > 8000:  # GPT-4 context limit
        raise ValueError(f"Prompt too long: {token_count} tokens")
    
    # Estimate cost before calling
    estimated_cost = self.estimate_cost(token_count, max_tokens=4000)
    logger.info(f"Estimated cost: ${estimated_cost:.4f}")
    
    return await self._call_azure_openai(prompt=prompt)
```

### Streaming Support (REQUIRED)
Support streaming for interactive CLI:

```python
async def generate_streaming(
    self,
    prompt: str,
    system_prompt: str | None = None,
) -> AsyncIterator[str]:
    """Stream completion tokens from Azure OpenAI."""
    response = await self.client.chat.completions.create(
        model=self.deployment_name,
        messages=[
            {"role": "system", "content": system_prompt or ""},
            {"role": "user", "content": prompt},
        ],
        stream=True,
    )
    
    async for chunk in response:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

### Error Handling (MANDATORY)
Handle all Azure OpenAI error types:

```python
from openai import (
    APIError,
    RateLimitError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
)

async def safe_generate(self, prompt: str) -> str:
    """Generate with comprehensive error handling."""
    try:
        return await self.generate_completion(prompt)
    
    except AuthenticationError as e:
        logger.error("Azure OpenAI authentication failed - check API key")
        raise LLMAuthenticationError("Invalid Azure OpenAI credentials") from e
    
    except RateLimitError as e:
        logger.warning("Rate limit hit - retrying with backoff")
        raise LLMRateLimitError("Azure OpenAI rate limit exceeded") from e
    
    except APITimeoutError as e:
        logger.error("Azure OpenAI request timed out")
        raise LLMTimeoutError("Request to Azure OpenAI timed out") from e
    
    except BadRequestError as e:
        logger.error(f"Invalid request to Azure OpenAI: {e}")
        raise LLMBadRequestError("Invalid request parameters") from e
    
    except APIError as e:
        logger.error(f"Azure OpenAI API error: {e}")
        raise LLMAPIError("Azure OpenAI service error") from e
```

## Embedding Strategy

### Batch Processing (REQUIRED)
Always batch embeddings for efficiency:

```python
async def embed_code_chunks(
    self,
    chunks: list[str],
    batch_size: int = 16,
) -> list[list[float]]:
    """Generate embeddings in batches."""
    embeddings = []
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        
        response = await self.client.embeddings.create(
            model=self.embedding_deployment,
            input=batch,
        )
        
        batch_embeddings = [item.embedding for item in response.data]
        embeddings.extend(batch_embeddings)
        
        # Track usage
        self.cost_tracker.add_embedding_tokens(response.usage.total_tokens)
    
    return embeddings
```

### Embedding Cache (REQUIRED)
Cache embeddings to avoid re-computation:

```python
import hashlib
import json
from pathlib import Path

class EmbeddingCache:
    """Cache embeddings to disk."""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, text: str, model: str) -> str:
        """Generate cache key from text and model."""
        content = f"{model}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get(self, text: str, model: str) -> list[float] | None:
        """Get cached embedding if exists."""
        key = self._get_cache_key(text, model)
        cache_file = self.cache_dir / f"{key}.json"
        
        if cache_file.exists():
            return json.loads(cache_file.read_text())
        return None
    
    def set(self, text: str, model: str, embedding: list[float]) -> None:
        """Cache embedding to disk."""
        key = self._get_cache_key(text, model)
        cache_file = self.cache_dir / f"{key}.json"
        cache_file.write_text(json.dumps(embedding))
```

## Prompt Engineering

### Template Structure (REQUIRED)
Use structured templates with clear sections:

```python
SPECIFICATION_PROMPT = """
You are a technical specification writer analyzing a Python codebase.

## Codebase Context
{codebase_summary}

## Relevant Code Examples
{relevant_code_chunks}

## Existing Patterns
{detected_patterns}

## Task
Generate a detailed specification for: {feature_description}

## Requirements
1. Follow existing architectural patterns shown in the code examples
2. Use the same naming conventions and code style
3. Maintain consistency with current dependencies
4. Include acceptance criteria
5. Specify error handling requirements

## Output Format
Provide a structured specification with:
- Overview
- Functional Requirements
- Technical Requirements
- Acceptance Criteria
- Dependencies
"""

CODE_GENERATION_PROMPT = """
You are generating Python code for an existing codebase.

## Existing Code Patterns
{code_patterns}

## Similar Implementations
{similar_code}

## Specification
{specification}

## Requirements
1. Match the existing code style EXACTLY
2. Use the same type annotation patterns
3. Follow the same error handling approach
4. Use the same logging patterns
5. Include docstrings in the same format
6. Add type hints to ALL functions

## Output
Generate ONLY the Python code, no explanations.
"""
```

### Context Injection (REQUIRED)
Always inject relevant context from vector search:

```python
async def generate_code(
    self,
    specification: str,
    project_path: Path,
) -> str:
    """Generate code with context from codebase."""
    # Get relevant code examples via vector search
    relevant_chunks = await self.vector_db.search(
        query=specification,
        top_k=5,
    )
    
    # Extract patterns from codebase
    patterns = self.pattern_detector.detect_patterns(project_path)
    
    # Build prompt with context
    prompt = CODE_GENERATION_PROMPT.format(
        code_patterns=self._format_patterns(patterns),
        similar_code=self._format_chunks(relevant_chunks),
        specification=specification,
    )
    
    # Generate with context
    return await self.llm_client.generate_completion(prompt)
```

## Cost Management

### Token Tracking (MANDATORY)
Track all token usage:

```python
class CostTracker:
    """Track Azure OpenAI usage and costs."""
    
    def __init__(self):
        self.completion_tokens = 0
        self.prompt_tokens = 0
        self.embedding_tokens = 0
    
    def add_completion(self, prompt_tokens: int, completion_tokens: int) -> None:
        """Add completion usage."""
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
    
    def add_embedding_tokens(self, tokens: int) -> None:
        """Add embedding usage."""
        self.embedding_tokens += tokens
    
    def calculate_cost(self) -> float:
        """Calculate total cost based on Azure pricing."""
        # GPT-4 pricing (example - update with actual pricing)
        prompt_cost = (self.prompt_tokens / 1000) * 0.03
        completion_cost = (self.completion_tokens / 1000) * 0.06
        embedding_cost = (self.embedding_tokens / 1000) * 0.0001
        
        return prompt_cost + completion_cost + embedding_cost
    
    def get_report(self) -> dict:
        """Generate usage report."""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "embedding_tokens": self.embedding_tokens,
            "total_tokens": self.prompt_tokens + self.completion_tokens + self.embedding_tokens,
            "estimated_cost": self.calculate_cost(),
        }
```

## Testing Standards

### Mock Azure OpenAI (MANDATORY)
NEVER call real Azure OpenAI in unit tests:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_azure_client():
    """Mock Azure OpenAI client."""
    client = AsyncMock()
    
    # Mock completion
    client.chat.completions.create = AsyncMock(
        return_value=MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(content="Generated code here"),
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
    
    # Mock embeddings
    client.embeddings.create = AsyncMock(
        return_value=MagicMock(
            data=[MagicMock(embedding=[0.1] * 1536)],
            usage=MagicMock(total_tokens=50),
        )
    )
    
    return client

@pytest.mark.asyncio
async def test_generate_code(mock_azure_client):
    """Test code generation with mocked Azure OpenAI."""
    llm_client = AzureOpenAIClient(config, client=mock_azure_client)
    
    result = await llm_client.generate_completion("Generate a function")
    
    assert result == "Generated code here"
    mock_azure_client.chat.completions.create.assert_called_once()
```

### Integration Tests (OPTIONAL)
Optional integration tests with real API (gated by env var):

```python
import os
import pytest

@pytest.mark.skipif(
    os.getenv("AZURE_OPENAI_INTEGRATION_TESTS") != "true",
    reason="Integration tests disabled - set AZURE_OPENAI_INTEGRATION_TESTS=true",
)
@pytest.mark.asyncio
async def test_real_azure_openai():
    """Integration test with real Azure OpenAI API."""
    config = AzureOpenAIConfig(
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        # ... other config
    )
    
    client = AzureOpenAIClient(config)
    result = await client.generate_completion("Say hello")
    
    assert len(result) > 0
    assert isinstance(result, str)
```

## Azure AD Authentication Standards

### When to Use Azure AD Authentication

Use Azure AD authentication when:
- **Enterprise Security**: Organization requires Azure AD for all services
- **Compliance**: Need to meet specific compliance requirements
- **Auditing**: Require detailed tracking of API usage by user
- **Managed Identities**: Running on Azure infrastructure (VMs, App Service, Functions)
- **Short-Lived Credentials**: Need automatic token rotation
- **Centralized Access Control**: Manage access through Azure AD policies

### Bearer Token Management (REQUIRED)

```python
# ✅ CORRECT - Automatic token refresh with managed identity
from azure.identity import DefaultAzureCredential

class TokenManager:
    """Manage Azure AD token refresh."""
    
    def __init__(self):
        self.credential = DefaultAzureCredential()
        self.current_token = None
        self.token_expiry = 0
    
    def get_token(self) -> str:
        """Get current token or refresh if expired."""
        import time
        current_time = time.time()
        
        # Refresh if token expires in less than 5 minutes
        if current_time >= (self.token_expiry - 300):
            token_obj = self.credential.get_token(
                "https://cognitiveservices.azure.com/.default"
            )
            self.current_token = token_obj.token
            self.token_expiry = token_obj.expires_on
        
        return self.current_token

# ❌ WRONG - Hardcoded token without refresh
bearer_token = "eyJ0eXAiOiJKV1Qi..."  # Will expire!
```

### Custom Headers for Auditing (RECOMMENDED)

```python
# ✅ CORRECT - Comprehensive auditing headers
config = AzureOpenAIConfig(
    endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    bearer_token=SecretStr(token_manager.get_token()),
    api_version="2024-02-15-preview",
    deployment_name="gpt-4",
    embedding_deployment="text-embedding-ada-002",
    user_sid="A123456",  # User identifier
    custom_headers={
        "department": "engineering",
        "project": "dev-agent",
        "cost_center": "CC-1234",
        "environment": "production",
    },
)

# ❌ WRONG - No auditing headers
config = AzureOpenAIConfig(
    endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    bearer_token=SecretStr(token),
    # Missing user_sid and custom_headers
)
```

### Client Initialization with Azure AD

```python
# ✅ CORRECT - Azure AD authentication with custom headers
def _build_default_headers(self) -> dict[str, str]:
    """Build default headers including auth and custom headers."""
    headers = {}
    
    # Add bearer token authorization if using Azure AD
    if self.config.bearer_token:
        token_value = self.config.bearer_token.get_secret_value()
        headers["Authorization"] = f"Bearer {token_value}"
    
    # Add custom headers
    headers.update(self.config.custom_headers)
    
    # Add user_sid if configured
    if self.config.user_sid:
        headers["user_sid"] = self.config.user_sid
    
    return headers

def _get_api_key_value(self) -> str:
    """Get the API key or bearer token value for client initialization."""
    if self.config.bearer_token:
        # When using Azure AD, pass the bearer token as api_key
        return self.config.bearer_token.get_secret_value()
    else:
        # Standard API key authentication
        return self.config.api_key.get_secret_value()

# Initialize client with headers
self.client = AsyncAzureOpenAI(
    api_key=self._get_api_key_value(),
    api_version=config.api_version,
    azure_endpoint=config.endpoint,
    timeout=config.timeout,
    max_retries=0,
    default_headers=self._build_default_headers(),
)
```

### Error Handling for Azure AD

```python
# ✅ CORRECT - Specific error messages for authentication method
async def safe_generate(self, prompt: str) -> str:
    """Generate with authentication-aware error handling."""
    try:
        return await self.generate_completion(prompt)
    
    except AuthenticationError as e:
        auth_method = "Azure AD bearer token" if self.config.bearer_token else "API key"
        logger.error(f"Azure OpenAI authentication failed using {auth_method}")
        
        if self.config.bearer_token:
            raise LLMAuthenticationError(
                f"Failed to authenticate with Azure OpenAI using {auth_method}. "
                "Check that your bearer token is valid and not expired. "
                "Tokens typically expire after 1 hour."
            ) from e
        else:
            raise LLMAuthenticationError(
                f"Failed to authenticate with Azure OpenAI using {auth_method}. "
                "Check that your API key is correct."
            ) from e
```

### Configuration Loading with Azure AD

```python
# ✅ CORRECT - Load Azure AD configuration from environment
def _load_azure_config_from_env(self) -> AzureOpenAIConfig:
    """Load Azure OpenAI configuration from environment variables."""
    
    # Get bearer token (takes precedence over API key)
    bearer_token = os.getenv("AZURE_OPENAI_TOKEN")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    
    # Parse custom headers from JSON
    custom_headers = {}
    if headers_json := os.getenv("AZURE_OPENAI_CUSTOM_HEADERS"):
        try:
            custom_headers = json.loads(headers_json)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AZURE_OPENAI_CUSTOM_HEADERS: {e}")
    
    # Add user_sid to custom headers if provided
    if user_sid := os.getenv("AZURE_OPENAI_USER_SID"):
        custom_headers["user_sid"] = user_sid
    
    # Support deployment name alias
    deployment_name = (
        os.getenv("AZURE_CHAT_DEPLOYMENT_NAME") or
        os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    )
    
    return AzureOpenAIConfig(
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=SecretStr(api_key) if api_key else None,
        bearer_token=SecretStr(bearer_token) if bearer_token else None,
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        deployment_name=deployment_name,
        embedding_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
        custom_headers=custom_headers,
    )
```

## Security Requirements (ENFORCED)

### API Key Management
- **NEVER commit API keys** to version control
- **Use .env files** for local development (add to .gitignore)
- **Use Azure Key Vault** for production deployments
- **Rotate keys regularly** (every 90 days minimum)
- **Use managed identities** when running on Azure infrastructure

### Bearer Token Management (Azure AD)
- **NEVER commit bearer tokens** to version control
- **Implement automatic token refresh** (tokens expire after 1 hour)
- **Use managed identities** when possible (automatic token management)
- **Use short-lived tokens** (default 1-hour expiration is recommended)
- **Monitor token expiration** and refresh proactively
- **Secure token storage** using Azure Key Vault or secure environment variables

### Logging Security
- **NEVER log API keys or bearer tokens** in any form
- **Use SecretStr** for all sensitive data (API keys and bearer tokens)
- **Redact credentials** in error messages
- **Audit log API calls** without sensitive data
- **Log authentication method used** (API key vs Azure AD) for debugging

### Custom Headers Security
- **Validate custom headers** before use
- **Avoid sensitive data** in header names or values
- **Log custom headers** at debug level only
- **Document header usage** for compliance audits
- **Use standard header names** when possible

### Data Privacy
- **Code stays in Azure** - never sent to third parties
- **Comply with Azure compliance** requirements
- **Document data flow** for security reviews
- **Implement data retention** policies
- **Track API usage by user** using custom headers for auditing

## Future Enhancements (Backlog)

### AWS Bedrock Integration
- Support Claude 3 models via AWS Bedrock
- Implement BedrockClient following same interface
- Add provider selection in configuration
- Support fallback between providers

### Cost Optimization
- Automatic model selection based on task complexity
- Use GPT-3.5 Turbo for simple tasks
- Use GPT-4o-mini when available
- Implement budget limits and warnings

### Advanced Features
- Fine-tuned models for code generation
- Custom embeddings for domain-specific code
- Multi-region deployment support
- Caching layer for common queries

Remember: Azure OpenAI integration is CRITICAL infrastructure - treat it with the same rigor as database or authentication systems.
