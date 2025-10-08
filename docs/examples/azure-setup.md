# Azure OpenAI Setup Examples

This guide provides practical examples for setting up and using Azure OpenAI with dev-agent.

## Basic Setup Example

### Step 1: Environment Variables Setup

Create a `.env` file in your project root (remember to add to `.gitignore`):

**Option A: API Key Authentication (Default)**

```bash
# .env file - DO NOT COMMIT TO VERSION CONTROL
AZURE_OPENAI_ENDPOINT=https://my-dev-agent.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

**Option B: Azure AD Authentication (Enterprise)**

```bash
# .env file - DO NOT COMMIT TO VERSION CONTROL
AZURE_OPENAI_ENDPOINT=https://my-dev-agent.openai.azure.com/
AZURE_OPENAI_TOKEN=eyJ0eXAiOiJKV1QiLCJhbGc...
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
AZURE_OPENAI_USER_SID=A123456
AZURE_OPENAI_CUSTOM_HEADERS={"department": "engineering"}
```

### Step 2: Load Environment Variables

```bash
# Load environment variables
source .env

# Or use a tool like direnv
echo "dotenv" >> .envrc
direnv allow
```

### Step 3: Test Configuration

```bash
# Test Azure OpenAI connection
uv run dev-agent azure test

# Expected output:
# ✓ Azure OpenAI endpoint is reachable
# ✓ API key is valid
# ✓ GPT-4 deployment is accessible
# ✓ Embedding deployment is accessible
# ✓ Configuration is valid
```

## Configuration Examples

### Example 1: Basic Configuration

```python
"""Basic Azure OpenAI configuration."""
import os
from dev_agent.models.llm_config import AzureOpenAIConfig
from pydantic import SecretStr

# Create configuration from environment variables
config = AzureOpenAIConfig(
    endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=SecretStr(os.getenv("AZURE_OPENAI_API_KEY")),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4"),
    embedding_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002"),
)

print(f"Endpoint: {config.endpoint}")
print(f"Deployment: {config.deployment_name}")
print(f"API Key: {config.api_key}")  # Automatically redacted
```

### Example 2: Custom Configuration

```python
"""Custom Azure OpenAI configuration with advanced settings."""
from dev_agent.models.llm_config import AzureOpenAIConfig
from pydantic import SecretStr

config = AzureOpenAIConfig(
    endpoint="https://my-dev-agent.openai.azure.com/",
    api_key=SecretStr("your-api-key-here"),
    api_version="2024-02-15-preview",
    deployment_name="gpt-4-turbo",  # Use GPT-4 Turbo for cost savings
    embedding_deployment="text-embedding-ada-002",
    max_tokens=2000,  # Reduce for faster responses
    temperature=0.5,  # Lower temperature for more deterministic output
    max_retries=5,  # More retries for reliability
    timeout=120,  # Longer timeout for complex requests
    batch_size=16,  # Optimal batch size for embeddings
)
```

### Example 3: Multiple Environments

```python
"""Configuration for different environments."""
import os
from dev_agent.models.llm_config import AzureOpenAIConfig
from pydantic import SecretStr

def get_config(environment: str = "development") -> AzureOpenAIConfig:
    """Get configuration for specific environment."""
    
    configs = {
        "development": {
            "endpoint": "https://dev-openai.openai.azure.com/",
            "deployment_name": "gpt-4",
            "max_tokens": 4000,
            "temperature": 0.7,
        },
        "staging": {
            "endpoint": "https://staging-openai.openai.azure.com/",
            "deployment_name": "gpt-4-turbo",
            "max_tokens": 2000,
            "temperature": 0.5,
        },
        "production": {
            "endpoint": "https://prod-openai.openai.azure.com/",
            "deployment_name": "gpt-4-turbo",
            "max_tokens": 2000,
            "temperature": 0.3,  # More deterministic for production
        },
    }
    
    env_config = configs[environment]
    
    return AzureOpenAIConfig(
        endpoint=env_config["endpoint"],
        api_key=SecretStr(os.getenv("AZURE_OPENAI_API_KEY")),
        api_version="2024-02-15-preview",
        deployment_name=env_config["deployment_name"],
        embedding_deployment="text-embedding-ada-002",
        max_tokens=env_config["max_tokens"],
        temperature=env_config["temperature"],
    )

# Usage
dev_config = get_config("development")
prod_config = get_config("production")
```

## LLM Client Examples

### Example 1: Basic Completion

```python
"""Generate a simple completion."""
import asyncio
import os
from dev_agent.llm.azure_client import AzureOpenAIClient
from dev_agent.models.llm_config import AzureOpenAIConfig
from pydantic import SecretStr

async def basic_completion():
    """Generate a basic completion."""
    
    # Create configuration
    config = AzureOpenAIConfig(
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=SecretStr(os.getenv("AZURE_OPENAI_API_KEY")),
        api_version="2024-02-15-preview",
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
    )
    
    # Create client
    client = AzureOpenAIClient(config)
    
    # Generate completion
    response = await client.generate_completion(
        prompt="Write a Python function to calculate factorial",
        system_prompt="You are a Python programming expert.",
        temperature=0.7,
        max_tokens=500,
    )
    
    print("Generated code:")
    print(response)

# Run
asyncio.run(basic_completion())
```

### Example 2: Streaming Completion

```python
"""Stream completion tokens in real-time."""
import asyncio
import os
from dev_agent.llm.azure_client import AzureOpenAIClient
from dev_agent.models.llm_config import AzureOpenAIConfig
from pydantic import SecretStr

async def streaming_completion():
    """Stream completion tokens."""
    
    config = AzureOpenAIConfig(
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=SecretStr(os.getenv("AZURE_OPENAI_API_KEY")),
        api_version="2024-02-15-preview",
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
    )
    
    client = AzureOpenAIClient(config)
    
    print("Streaming response:")
    async for chunk in client.generate_streaming(
        prompt="Explain how async/await works in Python",
        system_prompt="You are a Python expert.",
    ):
        print(chunk, end="", flush=True)
    
    print("\n\nStreaming complete!")

asyncio.run(streaming_completion())
```

### Example 3: Token Counting and Cost Estimation

```python
"""Count tokens and estimate costs before making API calls."""
import asyncio
import os
from dev_agent.llm.azure_client import AzureOpenAIClient
from dev_agent.models.llm_config import AzureOpenAIConfig
from pydantic import SecretStr

async def token_counting_example():
    """Demonstrate token counting and cost estimation."""
    
    config = AzureOpenAIConfig(
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=SecretStr(os.getenv("AZURE_OPENAI_API_KEY")),
        api_version="2024-02-15-preview",
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
    )
    
    client = AzureOpenAIClient(config)
    
    # Prepare prompt
    prompt = """
    Generate a Python class for user authentication with the following features:
    - Login with username and password
    - Password hashing with bcrypt
    - Session management
    - Token-based authentication
    """
    
    # Count tokens
    prompt_tokens = client.count_tokens(prompt)
    print(f"Prompt tokens: {prompt_tokens}")
    
    # Estimate cost (assuming 1000 completion tokens)
    estimated_cost = client.estimate_cost(
        prompt_tokens=prompt_tokens,
        completion_tokens=1000,
    )
    print(f"Estimated cost: ${estimated_cost:.4f}")
    
    # Ask user to confirm
    confirm = input("Proceed with generation? (y/n): ")
    if confirm.lower() == 'y':
        response = await client.generate_completion(
            prompt=prompt,
            max_tokens=1000,
        )
        print("\nGenerated code:")
        print(response)

asyncio.run(token_counting_example())
```

## Embedding Examples

### Example 1: Single Text Embedding

```python
"""Generate embedding for a single text."""
import asyncio
import os
from dev_agent.llm.embeddings import AzureEmbeddingClient
from dev_agent.models.llm_config import AzureOpenAIConfig
from pydantic import SecretStr

async def single_embedding():
    """Generate embedding for single text."""
    
    config = AzureOpenAIConfig(
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=SecretStr(os.getenv("AZURE_OPENAI_API_KEY")),
        api_version="2024-02-15-preview",
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
    )
    
    client = AzureEmbeddingClient(config)
    
    # Generate embedding
    text = "def calculate_factorial(n): return 1 if n <= 1 else n * calculate_factorial(n-1)"
    embedding = await client.embed_text(text)
    
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")

asyncio.run(single_embedding())
```

### Example 2: Batch Embeddings with Cache

```python
"""Generate embeddings for multiple texts with caching."""
import asyncio
import os
from pathlib import Path
from dev_agent.llm.embeddings import AzureEmbeddingClient
from dev_agent.llm.embedding_cache import EmbeddingCache
from dev_agent.models.llm_config import AzureOpenAIConfig
from pydantic import SecretStr

async def batch_embeddings_with_cache():
    """Generate batch embeddings with caching."""
    
    config = AzureOpenAIConfig(
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=SecretStr(os.getenv("AZURE_OPENAI_API_KEY")),
        api_version="2024-02-15-preview",
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
        batch_size=16,
    )
    
    # Create cache
    cache_dir = Path(".dev_agent/embedding_cache")
    cache = EmbeddingCache(cache_dir)
    
    # Create client with cache
    client = AzureEmbeddingClient(config, cache=cache)
    
    # Prepare texts
    code_chunks = [
        "def add(a, b): return a + b",
        "def subtract(a, b): return a - b",
        "def multiply(a, b): return a * b",
        "def divide(a, b): return a / b if b != 0 else None",
        # ... more chunks
    ]
    
    print(f"Generating embeddings for {len(code_chunks)} chunks...")
    
    # Generate embeddings (uses cache automatically)
    embeddings = await client.embed_batch(code_chunks)
    
    print(f"Generated {len(embeddings)} embeddings")
    print(f"Cache hits: {client.cache_hits}")
    print(f"Cache misses: {client.cache_misses}")
    print(f"Cache hit rate: {client.cache_hits / len(code_chunks) * 100:.1f}%")

asyncio.run(batch_embeddings_with_cache())
```

## Cost Tracking Examples

### Example 1: Basic Cost Tracking

```python
"""Track costs for Azure OpenAI operations."""
import asyncio
import os
from dev_agent.llm.azure_client import AzureOpenAIClient
from dev_agent.llm.cost_tracker import CostTracker
from dev_agent.models.llm_config import AzureOpenAIConfig
from pydantic import SecretStr

async def cost_tracking_example():
    """Track costs for operations."""
    
    config = AzureOpenAIConfig(
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=SecretStr(os.getenv("AZURE_OPENAI_API_KEY")),
        api_version="2024-02-15-preview",
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
    )
    
    client = AzureOpenAIClient(config)
    tracker = CostTracker()
    
    # Generate multiple completions
    prompts = [
        "Write a function to sort a list",
        "Write a function to find duplicates",
        "Write a function to merge dictionaries",
    ]
    
    for prompt in prompts:
        response = await client.generate_completion(prompt, max_tokens=200)
        
        # Track usage (in real implementation, this is automatic)
        tracker.add_completion(
            prompt_tokens=client.count_tokens(prompt),
            completion_tokens=client.count_tokens(response),
        )
    
    # Get cost report
    report = tracker.get_report()
    print("\nCost Report:")
    print(f"Total prompt tokens: {report['total_prompt_tokens']:,}")
    print(f"Total completion tokens: {report['total_completion_tokens']:,}")
    print(f"Total tokens: {report['total_tokens']:,}")
    print(f"Estimated cost: ${report['estimated_cost']:.4f}")

asyncio.run(cost_tracking_example())
```

### Example 2: Budget Management

```python
"""Manage budget and set alerts."""
from dev_agent.llm.cost_tracker import CostTracker

def budget_management_example():
    """Demonstrate budget management."""
    
    tracker = CostTracker()
    
    # Set monthly budget
    monthly_budget = 100.00  # $100 per month
    tracker.set_budget(monthly_limit=monthly_budget)
    
    # Set alert thresholds
    tracker.set_alert_thresholds([
        (50, "50% of budget used"),
        (75, "75% of budget used - consider optimization"),
        (90, "90% of budget used - approaching limit!"),
    ])
    
    # Simulate usage
    tracker.add_completion(prompt_tokens=10000, completion_tokens=5000)
    tracker.add_embedding_tokens(100000)
    
    # Check budget status
    status = tracker.get_budget_status()
    print(f"Budget: ${status['limit']:.2f}")
    print(f"Used: ${status['used']:.2f} ({status['percentage']:.1f}%)")
    print(f"Remaining: ${status['remaining']:.2f}")
    
    # Check if alerts triggered
    if status['alerts']:
        print("\nAlerts:")
        for alert in status['alerts']:
            print(f"  ⚠ {alert}")

budget_management_example()
```

## Complete Workflow Example

### Example: End-to-End Feature Development

```python
"""Complete workflow: indexing, specification, design, and implementation."""
import asyncio
import os
from pathlib import Path
from dev_agent.llm.azure_client import AzureOpenAIClient
from dev_agent.llm.embeddings import AzureEmbeddingClient
from dev_agent.llm.cost_tracker import CostTracker
from dev_agent.models.llm_config import AzureOpenAIConfig
from pydantic import SecretStr

async def complete_workflow():
    """Demonstrate complete workflow with cost tracking."""
    
    # Setup
    config = AzureOpenAIConfig(
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=SecretStr(os.getenv("AZURE_OPENAI_API_KEY")),
        api_version="2024-02-15-preview",
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
    )
    
    llm_client = AzureOpenAIClient(config)
    embedding_client = AzureEmbeddingClient(config)
    cost_tracker = CostTracker()
    
    print("=== Phase 1: Indexing ===")
    
    # Simulate indexing phase
    code_chunks = [
        "def user_login(username, password): ...",
        "def user_logout(session_id): ...",
        "class UserSession: ...",
        # ... more chunks
    ]
    
    embeddings = await embedding_client.embed_batch(code_chunks)
    cost_tracker.add_embedding_tokens(len(code_chunks) * 100)  # Approximate
    
    print(f"✓ Indexed {len(code_chunks)} code chunks")
    print(f"  Cost: ${cost_tracker.calculate_cost():.4f}")
    
    print("\n=== Phase 2: Specification ===")
    
    # Generate specification
    spec_prompt = """
    Based on the existing authentication code, generate a specification
    for adding two-factor authentication (2FA) support.
    """
    
    specification = await llm_client.generate_completion(
        prompt=spec_prompt,
        system_prompt="You are a technical specification writer.",
        max_tokens=2000,
    )
    
    cost_tracker.add_completion(
        prompt_tokens=llm_client.count_tokens(spec_prompt),
        completion_tokens=llm_client.count_tokens(specification),
    )
    
    print("✓ Generated specification")
    print(f"  Cost: ${cost_tracker.calculate_cost():.4f}")
    
    print("\n=== Phase 3: Design ===")
    
    # Generate design
    design_prompt = f"""
    Based on this specification:
    {specification[:500]}...
    
    Generate a technical design document.
    """
    
    design = await llm_client.generate_completion(
        prompt=design_prompt,
        system_prompt="You are a software architect.",
        max_tokens=3000,
    )
    
    cost_tracker.add_completion(
        prompt_tokens=llm_client.count_tokens(design_prompt),
        completion_tokens=llm_client.count_tokens(design),
    )
    
    print("✓ Generated design")
    print(f"  Cost: ${cost_tracker.calculate_cost():.4f}")
    
    print("\n=== Phase 4: Implementation ===")
    
    # Generate code
    code_prompt = f"""
    Based on this design:
    {design[:500]}...
    
    Generate Python code for 2FA implementation.
    """
    
    code = await llm_client.generate_completion(
        prompt=code_prompt,
        system_prompt="You are a Python developer.",
        max_tokens=2000,
    )
    
    cost_tracker.add_completion(
        prompt_tokens=llm_client.count_tokens(code_prompt),
        completion_tokens=llm_client.count_tokens(code),
    )
    
    print("✓ Generated implementation")
    print(f"  Cost: ${cost_tracker.calculate_cost():.4f}")
    
    # Final report
    print("\n=== Final Cost Report ===")
    report = cost_tracker.get_report()
    print(f"Total tokens: {report['total_tokens']:,}")
    print(f"Total cost: ${report['estimated_cost']:.2f}")
    print(f"\nBreakdown:")
    print(f"  Embeddings: {report['total_embedding_tokens']:,} tokens")
    print(f"  Completions: {report['total_completion_tokens']:,} tokens")

asyncio.run(complete_workflow())
```

## Error Handling Examples

### Example: Robust Error Handling

```python
"""Handle Azure OpenAI errors gracefully."""
import asyncio
import os
from dev_agent.llm.azure_client import AzureOpenAIClient
from dev_agent.models.llm_config import AzureOpenAIConfig
from dev_agent.errors.llm_exceptions import (
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMAPIError,
)
from pydantic import SecretStr

async def error_handling_example():
    """Demonstrate error handling."""
    
    config = AzureOpenAIConfig(
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=SecretStr(os.getenv("AZURE_OPENAI_API_KEY")),
        api_version="2024-02-15-preview",
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
    )
    
    client = AzureOpenAIClient(config)
    
    try:
        response = await client.generate_completion(
            prompt="Generate a complex algorithm",
            max_tokens=4000,
        )
        print("Success:", response[:100])
        
    except LLMAuthenticationError as e:
        print(f"Authentication failed: {e}")
        print("Please check your API key and endpoint")
        
    except LLMRateLimitError as e:
        print(f"Rate limit exceeded: {e}")
        print("Waiting and retrying automatically...")
        # Automatic retry with exponential backoff
        
    except LLMTimeoutError as e:
        print(f"Request timed out: {e}")
        print("Try reducing max_tokens or increasing timeout")
        
    except LLMAPIError as e:
        print(f"API error: {e}")
        print("Check Azure OpenAI service status")
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        print("Please report this issue")

asyncio.run(error_handling_example())
```

## Testing Examples

### Example: Mock Azure OpenAI for Testing

```python
"""Test code that uses Azure OpenAI without making real API calls."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from dev_agent.llm.azure_client import AzureOpenAIClient

@pytest.fixture
def mock_azure_client():
    """Mock Azure OpenAI client for testing."""
    client = AsyncMock()
    
    # Mock completion
    client.chat.completions.create = AsyncMock(
        return_value=MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(content="def test(): pass"),
                    finish_reason="stop",
                )
            ],
            usage=MagicMock(
                prompt_tokens=50,
                completion_tokens=100,
                total_tokens=150,
            ),
        )
    )
    
    return client

@pytest.mark.asyncio
async def test_code_generation(mock_azure_client):
    """Test code generation with mocked client."""
    # Your test code here
    # Uses mock instead of real API
    pass
```

## Azure AD Authentication Examples

### Example 1: Obtaining Bearer Token with Azure CLI

```bash
#!/bin/bash
# get_azure_token.sh - Get Azure AD bearer token

# Login to Azure (if not already logged in)
az login

# Get access token for Azure OpenAI
TOKEN=$(az account get-access-token \
  --resource https://cognitiveservices.azure.com \
  --query accessToken \
  --output tsv)

# Export token
export AZURE_OPENAI_TOKEN="$TOKEN"

echo "Bearer token obtained and exported"
echo "Token expires in 1 hour"
```

### Example 2: Azure AD Configuration with Python

```python
"""Azure AD authentication configuration example."""
import os
from dev_agent.models.llm_config import AzureOpenAIConfig
from pydantic import SecretStr

# Create configuration with bearer token
config = AzureOpenAIConfig(
    endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    bearer_token=SecretStr(os.getenv("AZURE_OPENAI_TOKEN")),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4"),
    embedding_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002"),
    user_sid="A123456",  # For auditing
    custom_headers={
        "department": "engineering",
        "project": "dev-agent",
    },
)

print(f"Authentication: Azure AD")
print(f"Endpoint: {config.endpoint}")
print(f"User SID: {config.user_sid}")
print(f"Custom headers: {config.custom_headers}")
```

### Example 3: Automatic Token Refresh with Managed Identity

```python
"""Automatic token refresh using Azure managed identity."""
import asyncio
import os
import time
from azure.identity import DefaultAzureCredential
from dev_agent.llm.azure_client import AzureOpenAIClient
from dev_agent.models.llm_config import AzureOpenAIConfig
from pydantic import SecretStr

class TokenRefreshManager:
    """Manage automatic token refresh for Azure AD."""
    
    def __init__(self):
        self.credential = DefaultAzureCredential()
        self.current_token = None
        self.token_expiry = 0
    
    def get_token(self) -> str:
        """Get current token or refresh if expired."""
        current_time = time.time()
        
        # Refresh if token expires in less than 5 minutes
        if current_time >= (self.token_expiry - 300):
            token_obj = self.credential.get_token(
                "https://cognitiveservices.azure.com/.default"
            )
            self.current_token = token_obj.token
            self.token_expiry = token_obj.expires_on
            print(f"Token refreshed, expires at {time.ctime(self.token_expiry)}")
        
        return self.current_token
    
    def get_config(self) -> AzureOpenAIConfig:
        """Get configuration with current token."""
        return AzureOpenAIConfig(
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            bearer_token=SecretStr(self.get_token()),
            api_version="2024-02-15-preview",
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )

async def main():
    """Example usage with automatic token refresh."""
    token_manager = TokenRefreshManager()
    
    # Get initial configuration
    config = token_manager.get_config()
    client = AzureOpenAIClient(config)
    
    # Use client for multiple operations
    for i in range(5):
        # Refresh token if needed
        config = token_manager.get_config()
        client.config = config
        
        # Make API call
        response = await client.generate_completion(
            prompt=f"Generate example {i+1}",
            max_tokens=100,
        )
        print(f"Response {i+1}: {response[:50]}...")
        
        # Wait between calls
        await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 4: Service Principal Authentication

```python
"""Authenticate using Azure service principal."""
import os
import subprocess
from dev_agent.models.llm_config import AzureOpenAIConfig
from pydantic import SecretStr

def get_service_principal_token(
    tenant_id: str,
    client_id: str,
    client_secret: str,
) -> str:
    """Get bearer token using service principal credentials."""
    
    # Login with service principal
    subprocess.run([
        "az", "login",
        "--service-principal",
        "--username", client_id,
        "--password", client_secret,
        "--tenant", tenant_id,
    ], check=True, capture_output=True)
    
    # Get access token
    result = subprocess.run([
        "az", "account", "get-access-token",
        "--resource", "https://cognitiveservices.azure.com",
        "--query", "accessToken",
        "--output", "tsv",
    ], check=True, capture_output=True, text=True)
    
    return result.stdout.strip()

# Usage
tenant_id = os.getenv("AZURE_TENANT_ID")
client_id = os.getenv("AZURE_CLIENT_ID")
client_secret = os.getenv("AZURE_CLIENT_SECRET")

token = get_service_principal_token(tenant_id, client_id, client_secret)

config = AzureOpenAIConfig(
    endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    bearer_token=SecretStr(token),
    api_version="2024-02-15-preview",
    deployment_name="gpt-4",
    embedding_deployment="text-embedding-ada-002",
)

print("Authenticated with service principal")
```

### Example 5: Custom Headers for Auditing

```python
"""Use custom headers for detailed auditing and tracking."""
import asyncio
import os
from dev_agent.llm.azure_client import AzureOpenAIClient
from dev_agent.models.llm_config import AzureOpenAIConfig
from pydantic import SecretStr

async def auditing_example():
    """Demonstrate custom headers for auditing."""
    
    # Configuration with comprehensive auditing headers
    config = AzureOpenAIConfig(
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        bearer_token=SecretStr(os.getenv("AZURE_OPENAI_TOKEN")),
        api_version="2024-02-15-preview",
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
        user_sid="A123456",  # User identifier
        custom_headers={
            "department": "engineering",
            "project": "dev-agent",
            "cost_center": "CC-1234",
            "environment": "production",
            "request_id": "req-001",
            "session_id": "sess-abc123",
        },
    )
    
    client = AzureOpenAIClient(config)
    
    # All API calls will include these headers
    response = await client.generate_completion(
        prompt="Generate a function",
        max_tokens=200,
    )
    
    print("Request completed with auditing headers:")
    print(f"  User SID: {config.user_sid}")
    print(f"  Department: {config.custom_headers['department']}")
    print(f"  Project: {config.custom_headers['project']}")
    print(f"  Cost Center: {config.custom_headers['cost_center']}")

asyncio.run(auditing_example())
```

### Example 6: Token Refresh Script for Long-Running Processes

```bash
#!/bin/bash
# refresh_token_daemon.sh - Background token refresh daemon

LOG_FILE="/var/log/azure_token_refresh.log"
TOKEN_FILE="/tmp/azure_openai_token"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

refresh_token() {
    # Get new token
    TOKEN=$(az account get-access-token \
        --resource https://cognitiveservices.azure.com \
        --query accessToken \
        --output tsv 2>&1)
    
    if [ $? -eq 0 ]; then
        # Save token to file
        echo "$TOKEN" > "$TOKEN_FILE"
        chmod 600 "$TOKEN_FILE"
        
        # Export to environment
        export AZURE_OPENAI_TOKEN="$TOKEN"
        
        log "Token refreshed successfully"
        return 0
    else
        log "ERROR: Failed to refresh token: $TOKEN"
        return 1
    fi
}

# Initial token fetch
log "Starting token refresh daemon"
refresh_token

# Refresh every 50 minutes (tokens expire in 60 minutes)
while true; do
    sleep 3000  # 50 minutes
    refresh_token
done
```

### Example 7: Environment-Specific Azure AD Configuration

```python
"""Configure Azure AD authentication for different environments."""
import os
from enum import Enum
from dev_agent.models.llm_config import AzureOpenAIConfig
from pydantic import SecretStr

class Environment(Enum):
    """Deployment environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

def get_azure_ad_config(env: Environment) -> AzureOpenAIConfig:
    """Get Azure AD configuration for specific environment."""
    
    # Environment-specific settings
    env_configs = {
        Environment.DEVELOPMENT: {
            "endpoint": "https://dev-openai.openai.azure.com/",
            "deployment_name": "gpt-4",
            "user_sid": "DEV-USER",
            "custom_headers": {
                "environment": "development",
                "cost_center": "CC-DEV",
            },
        },
        Environment.STAGING: {
            "endpoint": "https://staging-openai.openai.azure.com/",
            "deployment_name": "gpt-4-turbo",
            "user_sid": "STAGING-USER",
            "custom_headers": {
                "environment": "staging",
                "cost_center": "CC-STAGING",
            },
        },
        Environment.PRODUCTION: {
            "endpoint": "https://prod-openai.openai.azure.com/",
            "deployment_name": "gpt-4-turbo",
            "user_sid": os.getenv("PRODUCTION_USER_ID"),
            "custom_headers": {
                "environment": "production",
                "cost_center": "CC-PROD",
                "compliance": "required",
            },
        },
    }
    
    env_config = env_configs[env]
    
    # Get bearer token (same for all environments)
    bearer_token = os.getenv("AZURE_OPENAI_TOKEN")
    if not bearer_token:
        raise ValueError("AZURE_OPENAI_TOKEN environment variable not set")
    
    return AzureOpenAIConfig(
        endpoint=env_config["endpoint"],
        bearer_token=SecretStr(bearer_token),
        api_version="2024-02-15-preview",
        deployment_name=env_config["deployment_name"],
        embedding_deployment="text-embedding-ada-002",
        user_sid=env_config["user_sid"],
        custom_headers=env_config["custom_headers"],
    )

# Usage
current_env = Environment(os.getenv("DEPLOYMENT_ENV", "development"))
config = get_azure_ad_config(current_env)

print(f"Configured for: {current_env.value}")
print(f"Endpoint: {config.endpoint}")
print(f"User SID: {config.user_sid}")
```

### Example 8: Testing Azure AD Authentication

```python
"""Test Azure AD authentication configuration."""
import asyncio
import os
from dev_agent.llm.azure_client import AzureOpenAIClient
from dev_agent.models.llm_config import AzureOpenAIConfig
from pydantic import SecretStr

async def test_azure_ad_auth():
    """Test Azure AD authentication setup."""
    
    print("Testing Azure AD Authentication...")
    print("=" * 50)
    
    # Check environment variables
    print("\n1. Checking environment variables...")
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_TOKEN",
        "AZURE_OPENAI_DEPLOYMENT_NAME",
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    print("✓ All required environment variables present")
    
    # Create configuration
    print("\n2. Creating configuration...")
    try:
        config = AzureOpenAIConfig(
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            bearer_token=SecretStr(os.getenv("AZURE_OPENAI_TOKEN")),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            embedding_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002"),
            user_sid=os.getenv("AZURE_OPENAI_USER_SID"),
        )
        print("✓ Configuration created successfully")
        print(f"  Endpoint: {config.endpoint}")
        print(f"  Deployment: {config.deployment_name}")
        print(f"  User SID: {config.user_sid}")
        print(f"  Auth method: Azure AD (bearer token)")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    # Test API connection
    print("\n3. Testing API connection...")
    try:
        client = AzureOpenAIClient(config)
        response = await client.generate_completion(
            prompt="Say 'Hello from Azure AD authentication!'",
            max_tokens=20,
        )
        print("✓ API connection successful")
        print(f"  Response: {response}")
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False
    
    # Test custom headers
    print("\n4. Testing custom headers...")
    if config.custom_headers or config.user_sid:
        print("✓ Custom headers configured:")
        if config.user_sid:
            print(f"  user_sid: {config.user_sid}")
        for key, value in config.custom_headers.items():
            print(f"  {key}: {value}")
    else:
        print("ℹ No custom headers configured (optional)")
    
    print("\n" + "=" * 50)
    print("✓ All tests passed!")
    print("\nYour Azure AD authentication is configured correctly.")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_azure_ad_auth())
    exit(0 if success else 1)
```

### Example 9: Migration from API Key to Azure AD

```python
"""Migrate from API key to Azure AD authentication."""
import asyncio
import os
from dev_agent.llm.azure_client import AzureOpenAIClient
from dev_agent.models.llm_config import AzureOpenAIConfig
from pydantic import SecretStr

async def migration_example():
    """Demonstrate migration from API key to Azure AD."""
    
    print("Migration Example: API Key → Azure AD")
    print("=" * 50)
    
    # Step 1: Current API key configuration
    print("\n1. Current configuration (API Key):")
    api_key_config = AzureOpenAIConfig(
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=SecretStr(os.getenv("AZURE_OPENAI_API_KEY")),
        api_version="2024-02-15-preview",
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
    )
    print(f"  Auth method: API Key")
    print(f"  Endpoint: {api_key_config.endpoint}")
    
    # Test current configuration
    client = AzureOpenAIClient(api_key_config)
    response = await client.generate_completion(
        prompt="Test with API key",
        max_tokens=10,
    )
    print(f"  ✓ API key authentication working")
    
    # Step 2: New Azure AD configuration
    print("\n2. New configuration (Azure AD):")
    azure_ad_config = AzureOpenAIConfig(
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        bearer_token=SecretStr(os.getenv("AZURE_OPENAI_TOKEN")),
        api_version="2024-02-15-preview",
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
        user_sid="A123456",
        custom_headers={"migration": "api-key-to-azure-ad"},
    )
    print(f"  Auth method: Azure AD")
    print(f"  Endpoint: {azure_ad_config.endpoint}")
    print(f"  User SID: {azure_ad_config.user_sid}")
    
    # Test new configuration
    client = AzureOpenAIClient(azure_ad_config)
    response = await client.generate_completion(
        prompt="Test with Azure AD",
        max_tokens=10,
    )
    print(f"  ✓ Azure AD authentication working")
    
    # Step 3: Migration complete
    print("\n3. Migration steps:")
    print("  ✓ Obtained Azure AD bearer token")
    print("  ✓ Updated configuration to use bearer token")
    print("  ✓ Added custom headers for auditing")
    print("  ✓ Tested new authentication method")
    print("\n  Next steps:")
    print("  - Update environment variables in production")
    print("  - Implement automatic token refresh")
    print("  - Remove API key from configuration")
    print("  - Update documentation for team")

asyncio.run(migration_example())
```

## Security Best Practices

### Example: Secure Configuration Management

```python
"""Secure configuration management example."""
import os
from pathlib import Path
from dev_agent.models.llm_config import AzureOpenAIConfig
from pydantic import SecretStr

def load_secure_config() -> AzureOpenAIConfig:
    """Load configuration securely."""
    
    # Option 1: Environment variables (recommended)
    if all([
        os.getenv("AZURE_OPENAI_ENDPOINT"),
        os.getenv("AZURE_OPENAI_API_KEY"),
    ]):
        return AzureOpenAIConfig(
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=SecretStr(os.getenv("AZURE_OPENAI_API_KEY")),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4"),
            embedding_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002"),
        )
    
    # Option 2: Azure Key Vault (production)
    # from azure.keyvault.secrets import SecretClient
    # from azure.identity import DefaultAzureCredential
    # 
    # credential = DefaultAzureCredential()
    # client = SecretClient(vault_url="https://my-vault.vault.azure.net/", credential=credential)
    # api_key = client.get_secret("azure-openai-key").value
    
    # Option 3: Config file (development only, not recommended)
    config_file = Path.home() / ".dev_agent" / "dev_agent_config.json"
    if config_file.exists():
        import json
        config_data = json.loads(config_file.read_text())
        return AzureOpenAIConfig(**config_data["azure_openai"])
    
    raise ValueError("No Azure OpenAI configuration found")

# Usage
config = load_secure_config()
print(f"Loaded config for: {config.endpoint}")
print(f"API Key: {config.api_key}")  # Automatically redacted
```

## Additional Resources

- [Azure OpenAI Setup Guide](../configuration/azure-openai.md)
- [Cost Management Guide](../usage/cost-management.md)
- [Troubleshooting Guide](../configuration/troubleshooting.md)
- [API Documentation](../api/llm.md)

## Important Reminders

1. **Never commit API keys** to version control
2. **Always use environment variables** or Azure Key Vault for credentials
3. **Test with small examples** before running on large codebases
4. **Monitor costs** regularly to avoid surprises
5. **Use caching** to optimize performance and reduce costs
6. **Handle errors gracefully** with proper exception handling
7. **Validate configuration** before starting workflows
8. **Keep dependencies updated** for security and performance
