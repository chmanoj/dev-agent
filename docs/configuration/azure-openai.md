# Azure OpenAI Setup Guide

This guide walks you through setting up Azure OpenAI integration for dev-agent, from creating Azure resources to configuring your local environment.

## Prerequisites

- An active Azure subscription
- Azure CLI installed (optional, but recommended)
- Python 3.10 or higher
- dev-agent installed (`uv sync --dev`)

## Step 1: Create Azure OpenAI Resource

### Using Azure Portal

1. **Navigate to Azure Portal**
   - Go to [portal.azure.com](https://portal.azure.com)
   - Sign in with your Azure account

2. **Create a new Azure OpenAI resource**
   - Click "Create a resource"
   - Search for "Azure OpenAI"
   - Click "Create"

3. **Configure the resource**
   - **Subscription**: Select your Azure subscription
   - **Resource Group**: Create new or select existing
   - **Region**: Choose a region that supports GPT-4 (e.g., East US, West Europe)
   - **Name**: Choose a unique name (e.g., `my-dev-agent-openai`)
   - **Pricing Tier**: Select Standard S0

4. **Review and Create**
   - Review your configuration
   - Click "Create"
   - Wait for deployment to complete (usually 1-2 minutes)

### Using Azure CLI

```bash
# Login to Azure
az login

# Create resource group (if needed)
az group create --name dev-agent-rg --location eastus

# Create Azure OpenAI resource
az cognitiveservices account create \
  --name my-dev-agent-openai \
  --resource-group dev-agent-rg \
  --kind OpenAI \
  --sku S0 \
  --location eastus
```

## Step 2: Deploy Models

Azure OpenAI requires you to deploy models before using them. dev-agent needs two deployments:

1. **GPT-4** - For code generation, specifications, and designs
2. **text-embedding-ada-002** - For code embeddings and vector search

### Using Azure Portal

1. **Navigate to your Azure OpenAI resource**
   - Go to your resource in the Azure Portal
   - Click "Model deployments" in the left menu
   - Click "Manage Deployments" (opens Azure OpenAI Studio)

2. **Deploy GPT-4**
   - Click "Create new deployment"
   - **Model**: Select `gpt-4` (or `gpt-4-turbo` for better performance)
   - **Deployment name**: `gpt-4` (recommended) or your custom name
   - **Model version**: Select the latest available
   - **Deployment type**: Standard
   - **Tokens per minute rate limit**: 10K (adjust based on your needs)
   - Click "Create"

3. **Deploy text-embedding-ada-002**
   - Click "Create new deployment" again
   - **Model**: Select `text-embedding-ada-002`
   - **Deployment name**: `text-embedding-ada-002` (recommended)
   - **Model version**: Select the latest available
   - **Deployment type**: Standard
   - **Tokens per minute rate limit**: 120K (embeddings are cheaper)
   - Click "Create"

### Using Azure CLI

```bash
# Deploy GPT-4
az cognitiveservices account deployment create \
  --name my-dev-agent-openai \
  --resource-group dev-agent-rg \
  --deployment-name gpt-4 \
  --model-name gpt-4 \
  --model-version "0613" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name "Standard"

# Deploy text-embedding-ada-002
az cognitiveservices account deployment create \
  --name my-dev-agent-openai \
  --resource-group dev-agent-rg \
  --deployment-name text-embedding-ada-002 \
  --model-name text-embedding-ada-002 \
  --model-version "2" \
  --model-format OpenAI \
  --sku-capacity 120 \
  --sku-name "Standard"
```

## Step 3: Get API Credentials

### Using Azure Portal

1. **Get the endpoint URL**
   - Navigate to your Azure OpenAI resource
   - Click "Keys and Endpoint" in the left menu
   - Copy the "Endpoint" value (e.g., `https://my-dev-agent-openai.openai.azure.com/`)

2. **Get the API key**
   - On the same "Keys and Endpoint" page
   - Copy either "KEY 1" or "KEY 2"
   - **Important**: Keep this key secure and never commit it to version control

### Using Azure CLI

```bash
# Get endpoint
az cognitiveservices account show \
  --name my-dev-agent-openai \
  --resource-group dev-agent-rg \
  --query "properties.endpoint" \
  --output tsv

# Get API key
az cognitiveservices account keys list \
  --name my-dev-agent-openai \
  --resource-group dev-agent-rg \
  --query "key1" \
  --output tsv
```

## Step 4: Configure Environment Variables

The recommended way to configure dev-agent is using environment variables. This keeps your credentials secure and out of version control.

### Linux/macOS

Create or edit `~/.bashrc`, `~/.zshrc`, or `~/.profile`:

```bash
# Azure OpenAI Configuration
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_KEY="your-api-key-here"
export AZURE_OPENAI_API_VERSION="2024-02-15-preview"
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-ada-002"

# Optional: Model Configuration
export AZURE_OPENAI_MAX_TOKENS="4000"
export AZURE_OPENAI_TEMPERATURE="0.7"
export AZURE_OPENAI_MAX_RETRIES="3"
export AZURE_OPENAI_TIMEOUT="60"
```

Then reload your shell:

```bash
source ~/.bashrc  # or ~/.zshrc, ~/.profile
```

### Windows (PowerShell)

Add to your PowerShell profile (`$PROFILE`):

```powershell
# Azure OpenAI Configuration
$env:AZURE_OPENAI_ENDPOINT = "https://your-resource.openai.azure.com/"
$env:AZURE_OPENAI_API_KEY = "your-api-key-here"
$env:AZURE_OPENAI_API_VERSION = "2024-02-15-preview"
$env:AZURE_OPENAI_DEPLOYMENT_NAME = "gpt-4"
$env:AZURE_OPENAI_EMBEDDING_DEPLOYMENT = "text-embedding-ada-002"
```

### Using .env File (Local Development)

For local development, you can create a `.env` file in your project root:

```bash
# .env file (add to .gitignore!)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

**Important**: Add `.env` to your `.gitignore` file to prevent committing credentials:

```bash
echo ".env" >> .gitignore
```

## Step 5: Configure Using Interactive CLI

dev-agent provides an interactive configuration wizard:

```bash
# Run the configuration wizard
uv run dev-agent azure configure

# Follow the prompts to enter:
# - Azure OpenAI endpoint
# - API key
# - Deployment names
# - Optional settings
```

The wizard will:
- Validate your endpoint URL format
- Test the connection to Azure OpenAI
- Verify your deployments exist
- Save configuration to `~/.dev_agent/dev_agent_config.json`

## Step 6: Test Your Configuration

### Using CLI Test Command

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

### Manual Test

Create a test script `test_azure.py`:

```python
import asyncio
import os
from dev_agent.llm.azure_client import AzureOpenAIClient
from dev_agent.models.llm_config import AzureOpenAIConfig
from pydantic import SecretStr

async def test_azure_openai():
    """Test Azure OpenAI connection."""
    config = AzureOpenAIConfig(
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=SecretStr(os.getenv("AZURE_OPENAI_API_KEY")),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4"),
        embedding_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002"),
    )
    
    client = AzureOpenAIClient(config)
    
    # Test completion
    print("Testing GPT-4 completion...")
    response = await client.generate_completion(
        prompt="Say 'Hello from Azure OpenAI!'",
        max_tokens=50,
    )
    print(f"Response: {response}")
    
    # Test token counting
    token_count = client.count_tokens("This is a test message")
    print(f"Token count: {token_count}")
    
    print("\n✓ All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_azure_openai())
```

Run the test:

```bash
uv run python test_azure.py
```

## Configuration Options Reference

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AZURE_OPENAI_ENDPOINT` | Your Azure OpenAI endpoint URL | `https://my-resource.openai.azure.com/` |
| `AZURE_OPENAI_API_KEY` | Your Azure OpenAI API key | `abc123...` |
| `AZURE_OPENAI_API_VERSION` | Azure OpenAI API version | `2024-02-15-preview` |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | GPT-4 deployment name | `gpt-4` |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Embedding deployment name | `text-embedding-ada-002` |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AZURE_OPENAI_MAX_TOKENS` | Maximum tokens for generation | `4000` |
| `AZURE_OPENAI_TEMPERATURE` | Sampling temperature (0.0-2.0) | `0.7` |
| `AZURE_OPENAI_MAX_RETRIES` | Maximum retry attempts | `3` |
| `AZURE_OPENAI_TIMEOUT` | Request timeout in seconds | `60` |
| `AZURE_OPENAI_BATCH_SIZE` | Embedding batch size | `16` |

## Troubleshooting

### Common Issues

#### "Authentication failed" Error

**Problem**: Invalid API key or endpoint

**Solution**:
1. Verify your API key is correct (check Azure Portal)
2. Ensure endpoint URL ends with `/`
3. Check that the endpoint matches your resource name
4. Try regenerating the API key in Azure Portal

#### "Deployment not found" Error

**Problem**: Deployment name doesn't match

**Solution**:
1. Check deployment names in Azure OpenAI Studio
2. Ensure deployment names match exactly (case-sensitive)
3. Verify deployments are in "Succeeded" state
4. Wait a few minutes if deployments were just created

#### "Rate limit exceeded" Error

**Problem**: Too many requests to Azure OpenAI

**Solution**:
1. Increase rate limits in Azure OpenAI Studio
2. Reduce concurrent requests in your code
3. Implement exponential backoff (dev-agent does this automatically)
4. Consider upgrading to higher tier

#### "Timeout" Error

**Problem**: Request took too long

**Solution**:
1. Increase `AZURE_OPENAI_TIMEOUT` value
2. Check your network connection
3. Verify Azure OpenAI service status
4. Try a different Azure region

For more troubleshooting help, see the [Troubleshooting Guide](troubleshooting.md).

## Security Best Practices

### API Key Management

1. **Never commit API keys to version control**
   - Add `.env` to `.gitignore`
   - Use environment variables or Azure Key Vault
   - Rotate keys regularly (every 90 days)

2. **Use Azure Key Vault for production**
   ```bash
   # Store key in Azure Key Vault
   az keyvault secret set \
     --vault-name my-keyvault \
     --name azure-openai-key \
     --value "your-api-key"
   ```

3. **Use Managed Identities when possible**
   - For Azure VMs, App Service, Functions
   - Eliminates need for API keys
   - Automatic credential rotation

### Network Security

1. **Restrict network access**
   - Configure Azure OpenAI firewall rules
   - Use private endpoints for production
   - Limit access to specific IP ranges

2. **Enable diagnostic logging**
   - Monitor API usage and access patterns
   - Set up alerts for unusual activity
   - Review logs regularly

### Compliance

1. **Data residency**
   - Choose Azure region based on compliance requirements
   - Understand data processing locations
   - Review Azure compliance certifications

2. **Audit logging**
   - Enable Azure Monitor logs
   - Track all API calls
   - Implement retention policies

## Next Steps

- [Cost Management Guide](../usage/cost-management.md) - Learn how to track and optimize costs
- [Usage Examples](../examples/azure-setup.md) - See practical examples
- [API Documentation](../api/llm.md) - Explore the LLM integration API
- [Troubleshooting Guide](troubleshooting.md) - Solve common issues

## Additional Resources

- [Azure OpenAI Documentation](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/)
- [Azure OpenAI Pricing](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/)
- [Azure OpenAI Service Limits](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/quotas-limits)
- [Azure OpenAI Best Practices](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/how-to/best-practices)
