# Design Document

## Overview

This design document outlines the implementation approach for adding Azure AD authentication support with custom headers to dev-agent's Azure OpenAI integration. The solution will extend the existing `AzureOpenAIClient` and `AzureEmbeddingClient` classes to support bearer token authentication and custom headers while maintaining backward compatibility with API key authentication.

The design follows the existing architecture patterns in dev-agent, using Pydantic models for configuration validation, async/await for API calls, and maintaining the clean separation between configuration, client initialization, and API operations.

## Architecture

### High-Level Architecture

```
Environment Variables
    ↓
ConfigManager (loads and validates)
    ↓
AzureOpenAIConfig (Pydantic model with new fields)
    ↓
AzureOpenAIClient / AzureEmbeddingClient
    ↓
AsyncAzureOpenAI (with custom headers and auth)
    ↓
Azure OpenAI API
```

### Authentication Flow

```
1. Load Configuration
   ├─ Check for AZURE_OPENAI_TOKEN (bearer token)
   ├─ Check for AZURE_OPENAI_API_KEY (API key)
   └─ Validate at least one is present

2. Determine Authentication Method
   ├─ If bearer token present → Azure AD auth
   └─ Else → API key auth

3. Build Custom Headers
   ├─ Add Authorization header (if bearer token)
   ├─ Add user_sid header (if configured)
   └─ Add any additional custom headers

4. Initialize AsyncAzureOpenAI Client
   ├─ Pass api_key (token or key)
   ├─ Pass default_headers
   └─ Set appropriate configuration
```

## Components and Interfaces

### 1. Enhanced AzureOpenAIConfig Model

**Location:** `dev_agent/models/llm_config.py`

**Changes:**
- Add optional `bearer_token: SecretStr | None` field
- Add optional `custom_headers: dict[str, str]` field  
- Add optional `user_sid: str | None` field
- Add `openai_api_type: str` field (default: "azure", can be "azure_ad")
- Update validation to ensure either `api_key` or `bearer_token` is provided
- Add method `get_auth_headers()` to build headers dict
- Add method `get_api_key_value()` to return appropriate credential

**New Fields:**
```python
bearer_token: SecretStr | None = Field(
    default=None,
    description="Azure AD bearer token for authentication"
)
custom_headers: dict[str, str] = Field(
    default_factory=dict,
    description="Custom headers to include in all API requests"
)
user_sid: str | None = Field(
    default=None,
    description="User session ID for auditing and tracking"
)
openai_api_type: str = Field(
    default="azure",
    description="OpenAI API type: 'azure' for API key, 'azure_ad' for bearer token"
)
```

**Validation Logic:**
```python
@model_validator(mode='after')
def validate_authentication(self) -> 'AzureOpenAIConfig':
    """Ensure at least one authentication method is configured."""
    if not self.api_key and not self.bearer_token:
        raise ValueError(
            "Either api_key or bearer_token must be provided"
        )
    
    # Set api_type based on authentication method
    if self.bearer_token:
        self.openai_api_type = "azure_ad"
    
    return self
```

### 2. ConfigManager Enhancements

**Location:** `dev_agent/config/config_manager.py`

**Changes to `_load_azure_config_from_env()`:**

Add support for new environment variables:
- `AZURE_OPENAI_TOKEN` → `bearer_token`
- `AZURE_CHAT_DEPLOYMENT_NAME` → `deployment_name` (alias)
- `AZURE_OPENAI_USER_SID` → `user_sid`
- `AZURE_OPENAI_CUSTOM_HEADERS` → `custom_headers` (JSON string)

**Environment Variable Precedence:**
1. `AZURE_OPENAI_TOKEN` (if present, use Azure AD auth)
2. `AZURE_OPENAI_API_KEY` (fallback to API key auth)
3. `AZURE_CHAT_DEPLOYMENT_NAME` (alias for `AZURE_OPENAI_DEPLOYMENT_NAME`)

**Custom Headers Parsing:**
```python
# Parse custom headers from JSON string
custom_headers = {}
if headers_json := os.getenv("AZURE_OPENAI_CUSTOM_HEADERS"):
    try:
        custom_headers = json.loads(headers_json)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse AZURE_OPENAI_CUSTOM_HEADERS: {e}")

# Add user_sid if provided
if user_sid := os.getenv("AZURE_OPENAI_USER_SID"):
    custom_headers["user_sid"] = user_sid
```

### 3. AzureOpenAIClient Modifications

**Location:** `dev_agent/llm/azure_client.py`

**Changes to `__init__()` method:**

```python
def __init__(
    self,
    config: AzureOpenAIConfig,
    client: AsyncAzureOpenAI | None = None,
) -> None:
    """Initialize Azure OpenAI client with auth and custom headers."""
    self.config = config
    
    if client is None:
        # Build default headers
        default_headers = self._build_default_headers()
        
        # Get API key or bearer token
        api_key_value = self._get_api_key_value()
        
        # Initialize client with custom headers
        self.client = AsyncAzureOpenAI(
            api_key=api_key_value,
            api_version=config.api_version,
            azure_endpoint=config.endpoint,
            timeout=config.timeout,
            max_retries=0,
            default_headers=default_headers,
        )
    else:
        self.client = client
    
    self.token_counter = TokenCounter(model=config.deployment_name)
    
    auth_method = "Azure AD" if config.bearer_token else "API Key"
    logger.info(
        f"Initialized Azure OpenAI client for deployment: {config.deployment_name} "
        f"using {auth_method} authentication"
    )
```

**New Helper Methods:**

```python
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
```

### 4. AzureEmbeddingClient Modifications

**Location:** `dev_agent/llm/embeddings.py`

**Changes to `__init__()` method:**

Apply the same pattern as `AzureOpenAIClient`:
- Build default headers using the same logic
- Pass headers to `AsyncAzureOpenAI` initialization
- Use bearer token if configured, otherwise API key
- Log authentication method used

```python
def __init__(
    self,
    config: AzureOpenAIConfig,
    cache_dir: Path | str | None = None,
    client: AsyncAzureOpenAI | None = None,
) -> None:
    """Initialize Azure embedding client with auth and custom headers."""
    self.config = config
    self.model = config.embedding_deployment
    
    # Initialize cache
    if cache_dir is None:
        cache_dir = ".dev_agent/embedding_cache"
    self.cache = EmbeddingCache(cache_dir)
    
    # Initialize Azure OpenAI client
    if client is None:
        # Build default headers (same logic as AzureOpenAIClient)
        default_headers = self._build_default_headers()
        api_key_value = self._get_api_key_value()
        
        self.client = AsyncAzureOpenAI(
            api_key=api_key_value,
            api_version=config.api_version,
            azure_endpoint=config.endpoint,
            timeout=config.timeout,
            max_retries=config.max_retries,
            default_headers=default_headers,
        )
    else:
        self.client = client
    
    auth_method = "Azure AD" if config.bearer_token else "API Key"
    logger.info(
        f"Initialized Azure embedding client with model: {self.model} "
        f"using {auth_method} authentication"
    )
```

## Data Models

### Enhanced AzureOpenAIConfig

```python
class AzureOpenAIConfig(BaseModel):
    """Enhanced Azure OpenAI configuration with Azure AD support."""
    
    # Existing fields
    endpoint: str
    api_key: SecretStr | None = None  # Made optional
    api_version: str = "2024-02-15-preview"
    deployment_name: str
    embedding_deployment: str
    max_tokens: int = 4000
    temperature: float = 0.7
    max_retries: int = 3
    timeout: int = 60
    batch_size: int = 16
    
    # New fields for Azure AD authentication
    bearer_token: SecretStr | None = None
    openai_api_type: str = "azure"
    
    # New fields for custom headers
    custom_headers: dict[str, str] = Field(default_factory=dict)
    user_sid: str | None = None
    
    @model_validator(mode='after')
    def validate_authentication(self) -> 'AzureOpenAIConfig':
        """Validate authentication configuration."""
        if not self.api_key and not self.bearer_token:
            raise ValueError(
                "Either api_key or bearer_token must be provided for authentication"
            )
        
        # Auto-set api_type based on authentication method
        if self.bearer_token:
            self.openai_api_type = "azure_ad"
        
        return self
    
    def get_auth_headers(self) -> dict[str, str]:
        """Build authentication and custom headers."""
        headers = {}
        
        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token.get_secret_value()}"
        
        headers.update(self.custom_headers)
        
        if self.user_sid:
            headers["user_sid"] = self.user_sid
        
        return headers
    
    def get_api_key_value(self) -> str:
        """Get the appropriate credential value."""
        if self.bearer_token:
            return self.bearer_token.get_secret_value()
        return self.api_key.get_secret_value()
```

### Environment Variable Mapping

| Environment Variable | Config Field | Type | Required | Default |
|---------------------|--------------|------|----------|---------|
| AZURE_OPENAI_ENDPOINT | endpoint | str | Yes | - |
| AZURE_OPENAI_API_KEY | api_key | SecretStr | Conditional* | - |
| AZURE_OPENAI_TOKEN | bearer_token | SecretStr | Conditional* | - |
| AZURE_OPENAI_API_VERSION | api_version | str | No | 2024-02-15-preview |
| AZURE_OPENAI_DEPLOYMENT_NAME | deployment_name | str | Yes | - |
| AZURE_CHAT_DEPLOYMENT_NAME | deployment_name | str | Yes (alias) | - |
| AZURE_OPENAI_EMBEDDING_DEPLOYMENT | embedding_deployment | str | Yes | - |
| AZURE_OPENAI_USER_SID | user_sid | str | No | None |
| AZURE_OPENAI_CUSTOM_HEADERS | custom_headers | dict | No | {} |

*Either `api_key` or `bearer_token` must be provided

## Error Handling

### Authentication Errors

**Scenario 1: Missing Credentials**
```python
if not config.api_key and not config.bearer_token:
    raise ValueError(
        "Azure OpenAI authentication not configured.\n"
        "Please set one of:\n"
        "  - AZURE_OPENAI_API_KEY (for API key authentication)\n"
        "  - AZURE_OPENAI_TOKEN (for Azure AD authentication)"
    )
```

**Scenario 2: Bearer Token Expired**
```python
except AuthenticationError as e:
    auth_method = "Azure AD bearer token" if config.bearer_token else "API key"
    logger.error(f"Azure OpenAI authentication failed using {auth_method}: {e}")
    raise LLMAuthenticationError(
        f"Failed to authenticate with Azure OpenAI using {auth_method}",
        "Check that your credentials are valid and not expired"
    ) from e
```

**Scenario 3: Invalid Custom Headers**
```python
try:
    custom_headers = json.loads(os.getenv("AZURE_OPENAI_CUSTOM_HEADERS", "{}"))
    if not isinstance(custom_headers, dict):
        raise ValueError("Custom headers must be a JSON object")
except (json.JSONDecodeError, ValueError) as e:
    logger.warning(
        f"Failed to parse AZURE_OPENAI_CUSTOM_HEADERS: {e}. "
        "Using empty custom headers."
    )
    custom_headers = {}
```

### Error Messages

All error messages should:
1. Clearly indicate which authentication method was attempted
2. Provide actionable guidance on how to fix the issue
3. Reference relevant environment variables
4. Log the authentication method used for debugging

## Testing Strategy

### Unit Tests

**Test File:** `tests/test_azure_ad_authentication.py`

**Test Cases:**

1. **Configuration Validation**
   - Test API key authentication configuration
   - Test bearer token authentication configuration
   - Test missing credentials raises ValueError
   - Test both credentials provided (bearer token takes precedence)
   - Test custom headers parsing from JSON
   - Test user_sid configuration

2. **Client Initialization**
   - Test AzureOpenAIClient with API key
   - Test AzureOpenAIClient with bearer token
   - Test AzureEmbeddingClient with API key
   - Test AzureEmbeddingClient with bearer token
   - Test custom headers are included in client initialization
   - Test default_headers are built correctly

3. **Header Building**
   - Test `_build_default_headers()` with API key (no Authorization header)
   - Test `_build_default_headers()` with bearer token (includes Authorization)
   - Test custom headers are merged correctly
   - Test user_sid is added when configured
   - Test empty custom headers when not configured

4. **Authentication Method Detection**
   - Test `_get_api_key_value()` returns API key when no bearer token
   - Test `_get_api_key_value()` returns bearer token when configured
   - Test `openai_api_type` is set to "azure_ad" with bearer token
   - Test `openai_api_type` is "azure" with API key

5. **Backward Compatibility**
   - Test existing API key configuration still works
   - Test existing environment variables work unchanged
   - Test config file with old format loads correctly
   - Test migration from API key to bearer token

### Integration Tests

**Test File:** `tests/integration/test_azure_ad_integration.py`

**Test Cases:**

1. **Real API Calls with Bearer Token** (optional, gated by env var)
   - Test completion generation with Azure AD auth
   - Test embedding generation with Azure AD auth
   - Test custom headers are sent in requests
   - Test user_sid appears in request headers

2. **Mock API Calls**
   - Mock AsyncAzureOpenAI to verify headers are passed
   - Verify Authorization header format
   - Verify custom headers are included
   - Verify api_key parameter receives correct value

### Test Fixtures

```python
@pytest.fixture
def azure_ad_config():
    """Azure OpenAI config with bearer token."""
    return AzureOpenAIConfig(
        endpoint="https://test.openai.azure.com/",
        bearer_token=SecretStr("test-bearer-token"),
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
        user_sid="A123456",
        custom_headers={"custom-header": "custom-value"},
    )

@pytest.fixture
def api_key_config():
    """Azure OpenAI config with API key."""
    return AzureOpenAIConfig(
        endpoint="https://test.openai.azure.com/",
        api_key=SecretStr("test-api-key"),
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
    )
```

## Migration Guide

### For Existing Users

**No Changes Required:**
- Existing API key authentication continues to work
- No configuration file changes needed
- All existing environment variables work as before

**To Enable Azure AD Authentication:**

1. Set new environment variables:
```bash
export AZURE_OPENAI_TOKEN="your-bearer-token"
export AZURE_OPENAI_USER_SID="A123456"  # Optional
```

2. Optionally add custom headers:
```bash
export AZURE_OPENAI_CUSTOM_HEADERS='{"custom-header": "value"}'
```

3. Remove or keep `AZURE_OPENAI_API_KEY` (bearer token takes precedence)

### Configuration Examples

**API Key Authentication (Existing):**
```bash
export AZURE_OPENAI_ENDPOINT="https://my-resource.openai.azure.com/"
export AZURE_OPENAI_API_KEY="sk-..."
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-ada-002"
```

**Azure AD Authentication (New):**
```bash
export AZURE_OPENAI_ENDPOINT="https://my-resource.openai.azure.com/"
export AZURE_OPENAI_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-ada-002"
export AZURE_OPENAI_USER_SID="A123456"
```

**With Custom Headers:**
```bash
export AZURE_OPENAI_CUSTOM_HEADERS='{"user_sid": "A123456", "department": "engineering"}'
```

**Using Alias (AZURE_CHAT_DEPLOYMENT_NAME):**
```bash
export AZURE_CHAT_DEPLOYMENT_NAME="gpt-4"  # Alternative to AZURE_OPENAI_DEPLOYMENT_NAME
```

## Security Considerations

1. **Token Storage:**
   - Bearer tokens stored as `SecretStr` (never logged)
   - Tokens redacted in config serialization
   - Tokens not included in error messages

2. **Token Expiration:**
   - Users responsible for token refresh
   - Clear error messages when tokens expire
   - Recommend using short-lived tokens

3. **Custom Headers:**
   - Validated before use
   - Logged at debug level only (not in production logs)
   - No sensitive data in header names

4. **Backward Compatibility:**
   - API key authentication remains secure
   - No breaking changes to existing security model
   - Both auth methods use same error handling

## Performance Considerations

1. **Header Building:**
   - Headers built once during client initialization
   - No per-request overhead
   - Minimal memory footprint

2. **Configuration Loading:**
   - Environment variables parsed once at startup
   - Cached in ConfigManager
   - No performance impact on API calls

3. **Authentication:**
   - No additional API calls for authentication
   - Bearer token passed directly to Azure OpenAI
   - Same performance as API key authentication

## Documentation Updates

### Files to Update

1. **`docs/configuration/azure-openai.md`**
   - Add Azure AD authentication section
   - Document new environment variables
   - Provide configuration examples
   - Add troubleshooting guide

2. **`docs/examples/azure-setup.md`**
   - Add Azure AD setup example
   - Show custom headers configuration
   - Demonstrate user_sid usage

3. **`README.md`**
   - Update environment variables section
   - Add Azure AD authentication mention
   - Link to detailed documentation

4. **Steering Rules (`azure-openai.md`)**
   - Update configuration standards
   - Add Azure AD authentication patterns
   - Document custom headers usage

### Example Documentation Snippet

```markdown
## Azure AD Authentication

dev-agent supports Azure AD authentication for enterprise environments:

### Configuration

```bash
# Azure AD Authentication
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_TOKEN="your-bearer-token"
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-ada-002"

# Optional: Add custom headers for auditing
export AZURE_OPENAI_USER_SID="A123456"
export AZURE_OPENAI_CUSTOM_HEADERS='{"department": "engineering"}'
```

### Authentication Methods

1. **API Key** (default): Simple authentication using API key
2. **Azure AD**: Enterprise authentication using bearer tokens

Bearer token authentication takes precedence when both are configured.
```

## Implementation Notes

1. **OpenAI SDK Version:**
   - Requires openai>=1.50.0 for `default_headers` support
   - Already specified in project dependencies

2. **AsyncAzureOpenAI Client:**
   - Supports `default_headers` parameter natively
   - Headers applied to all requests automatically
   - No need for request-level header injection

3. **Testing Approach:**
   - Mock AsyncAzureOpenAI for unit tests
   - Optional integration tests with real API (gated by env var)
   - Verify headers using mock assertions

4. **Code Reuse:**
   - Extract header building logic to shared methods
   - Use same pattern in both AzureOpenAIClient and AzureEmbeddingClient
   - Maintain DRY principle

5. **Logging:**
   - Log authentication method at INFO level
   - Log custom headers at DEBUG level only
   - Never log bearer tokens or API keys
