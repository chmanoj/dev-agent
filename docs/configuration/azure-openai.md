# Azure OpenAI Setup Guide

This guide walks you through setting up Azure OpenAI integration for dev-agent, from creating Azure resources to configuring your local environment.

> **Note on Screenshots**: This guide includes references to screenshots that illustrate key steps in the Azure Portal. To add actual screenshots:
> 1. Create a `docs/images/` directory
> 2. Take screenshots while following the setup steps
> 3. Save them with the filenames referenced in this guide (e.g., `azure-portal-home.png`)
> 4. The screenshots will automatically appear in the documentation

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

   > **Note**: Navigate to the Azure Portal home page at portal.azure.com

2. **Create a new Azure OpenAI resource**
   - Click "Create a resource" in the top-left corner
   - Search for "Azure OpenAI" in the search bar
   - Select "Azure OpenAI" from the results
   - Click "Create"

   > **Note**: Use the "Create a resource" button and search for "Azure OpenAI"

3. **Configure the resource**
   - **Subscription**: Select your Azure subscription
   - **Resource Group**: Create new or select existing (e.g., `dev-agent-rg`)
   - **Region**: Choose a region that supports GPT-4 (e.g., East US, West Europe, Sweden Central)
     - **Important**: Not all regions support GPT-4. Check [region availability](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/concepts/models#model-summary-table-and-region-availability)
   - **Name**: Choose a unique name (e.g., `my-dev-agent-openai`)
     - Must be globally unique across Azure
     - Use lowercase letters, numbers, and hyphens only
   - **Pricing Tier**: Select Standard S0
     - This is the only tier available for Azure OpenAI

   > **Note**: Fill in the resource configuration form with your subscription, resource group, region, and name

4. **Review and Create**
   - Review your configuration
   - Click "Create"
   - Wait for deployment to complete (usually 1-2 minutes)
   - Click "Go to resource" when deployment is complete

   > **Note**: Wait for the deployment to complete, then click "Go to resource"

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

   > **Note**: Click "Manage Deployments" to open Azure OpenAI Studio

2. **Deploy GPT-4**
   - Click "Create new deployment" or "Deployments" → "Create new deployment"
   - **Model**: Select `gpt-4` (or `gpt-4-turbo` for better performance and lower cost)
     - **gpt-4**: Original GPT-4 model (8K context)
     - **gpt-4-32k**: Extended context window (32K tokens)
     - **gpt-4-turbo**: Faster and cheaper (128K context)
   - **Deployment name**: `gpt-4` (recommended) or your custom name
     - Use a simple, memorable name
     - This name will be used in your environment variables
   - **Model version**: Select the latest available (e.g., `0613`, `1106-Preview`)
   - **Deployment type**: Standard
   - **Tokens per minute rate limit**: 10K (adjust based on your needs)
     - Start with 10K for development
     - Increase for production workloads
     - Maximum depends on your quota
   - Click "Create"

   > **Note**: Select GPT-4 model and configure deployment settings

3. **Deploy text-embedding-ada-002**
   - Click "Create new deployment" again
   - **Model**: Select `text-embedding-ada-002`
   - **Deployment name**: `text-embedding-ada-002` (recommended)
   - **Model version**: Select the latest available (usually `2`)
   - **Deployment type**: Standard
   - **Tokens per minute rate limit**: 120K (embeddings are cheaper and faster)
     - Embeddings use fewer tokens
     - Higher limits allow batch processing
   - Click "Create"

   > **Note**: Select text-embedding-ada-002 model and configure deployment settings

4. **Verify Deployments**
   - Wait for both deployments to show "Succeeded" status
   - Note down your deployment names (you'll need them for configuration)
   - Test deployments using the "Playground" feature

   > **Note**: Verify both deployments appear in the deployments list

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
   - Navigate to your Azure OpenAI resource in the Azure Portal
   - Click "Keys and Endpoint" in the left menu under "Resource Management"
   - Copy the "Endpoint" value (e.g., `https://my-dev-agent-openai.openai.azure.com/`)
   - **Important**: The endpoint URL must end with a trailing slash (`/`)

   > **Note**: Find the endpoint URL and API keys in the "Keys and Endpoint" section

2. **Get the API key**
   - On the same "Keys and Endpoint" page
   - Copy either "KEY 1" or "KEY 2" (both work identically)
   - Click the "Show Keys" button if keys are hidden
   - Use the copy icon to copy the key to clipboard
   - **Important**: Keep this key secure and never commit it to version control
   - **Best Practice**: Use KEY 1 for production and KEY 2 for development, or rotate between them

   > **Note**: Use the copy button next to KEY 1 to copy your API key

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

## Azure AD Authentication

dev-agent supports Azure Active Directory (Azure AD) authentication for enterprise environments that require bearer token authentication instead of simple API keys. This is particularly useful for organizations with strict security policies, compliance requirements, or those using managed identities.

### Authentication Methods

dev-agent supports two authentication methods:

1. **API Key Authentication** (default): Simple authentication using an API key
2. **Azure AD Authentication**: Enterprise authentication using bearer tokens

When both are configured, bearer token authentication takes precedence.

### Why Use Azure AD Authentication?

- **Enhanced Security**: Bearer tokens can be short-lived and automatically rotated
- **Compliance**: Meet organizational security policies requiring Azure AD
- **Auditing**: Better tracking of API usage by user with custom headers
- **Managed Identities**: Use Azure managed identities when running on Azure infrastructure
- **Centralized Access Control**: Manage access through Azure AD policies

### Setting Up Azure AD Authentication

#### Step 1: Obtain a Bearer Token

There are several ways to obtain an Azure AD bearer token:

**Option A: Using Azure CLI**

```bash
# Login to Azure
az login

# Get access token for Azure OpenAI
az account get-access-token --resource https://cognitiveservices.azure.com --query accessToken -o tsv
```

**Option B: Using Azure PowerShell**

```powershell
# Connect to Azure
Connect-AzAccount

# Get access token
(Get-AzAccessToken -ResourceUrl "https://cognitiveservices.azure.com").Token
```

**Option C: Using Managed Identity (for Azure resources)**

```python
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
token = credential.get_token("https://cognitiveservices.azure.com/.default")
bearer_token = token.token
```

**Option D: Using Service Principal**

```bash
# Login with service principal
az login --service-principal \
  --username <app-id> \
  --password <password-or-cert> \
  --tenant <tenant-id>

# Get token
az account get-access-token --resource https://cognitiveservices.azure.com --query accessToken -o tsv
```

#### Step 2: Configure Environment Variables

Replace or add to your existing Azure OpenAI configuration:

**Linux/macOS**:

```bash
# Azure AD Authentication
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."  # Your bearer token
export AZURE_OPENAI_API_VERSION="2024-02-15-preview"
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-ada-002"

# Optional: User session ID for auditing
export AZURE_OPENAI_USER_SID="A123456"

# Optional: Custom headers (JSON format)
export AZURE_OPENAI_CUSTOM_HEADERS='{"department": "engineering", "project": "dev-agent"}'
```

**Windows (PowerShell)**:

```powershell
# Azure AD Authentication
$env:AZURE_OPENAI_ENDPOINT = "https://your-resource.openai.azure.com/"
$env:AZURE_OPENAI_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGc..."
$env:AZURE_OPENAI_API_VERSION = "2024-02-15-preview"
$env:AZURE_OPENAI_DEPLOYMENT_NAME = "gpt-4"
$env:AZURE_OPENAI_EMBEDDING_DEPLOYMENT = "text-embedding-ada-002"
$env:AZURE_OPENAI_USER_SID = "A123456"
```

**Using .env file**:

```bash
# .env file (add to .gitignore!)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_TOKEN=eyJ0eXAiOiJKV1QiLCJhbGc...
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
AZURE_OPENAI_USER_SID=A123456
AZURE_OPENAI_CUSTOM_HEADERS={"department": "engineering"}
```

### Custom Headers for Auditing

Custom headers allow you to track API usage by user, department, or project for compliance and auditing purposes.

#### User Session ID (user_sid)

The `user_sid` header is commonly used for tracking individual user sessions:

```bash
export AZURE_OPENAI_USER_SID="A123456"
```

This automatically adds a `user_sid` header to all Azure OpenAI API requests.

#### Additional Custom Headers

You can add any custom headers as a JSON object:

```bash
export AZURE_OPENAI_CUSTOM_HEADERS='{
  "user_sid": "A123456",
  "department": "engineering",
  "project": "dev-agent",
  "cost_center": "CC-1234",
  "environment": "production"
}'
```

**Note**: Custom headers must be valid JSON. If parsing fails, dev-agent will log a warning and continue without custom headers.

### Configuration Examples

#### Example 1: API Key Authentication (Default)

```bash
# Traditional API key authentication
export AZURE_OPENAI_ENDPOINT="https://my-resource.openai.azure.com/"
export AZURE_OPENAI_API_KEY="abc123def456..."
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-ada-002"
```

#### Example 2: Azure AD Authentication

```bash
# Azure AD bearer token authentication
export AZURE_OPENAI_ENDPOINT="https://my-resource.openai.azure.com/"
export AZURE_OPENAI_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-ada-002"
```

#### Example 3: Azure AD with Custom Headers

```bash
# Azure AD with auditing headers
export AZURE_OPENAI_ENDPOINT="https://my-resource.openai.azure.com/"
export AZURE_OPENAI_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-ada-002"
export AZURE_OPENAI_USER_SID="A123456"
export AZURE_OPENAI_CUSTOM_HEADERS='{"department": "engineering", "project": "dev-agent"}'
```

#### Example 4: Using Deployment Name Alias

```bash
# Using AZURE_CHAT_DEPLOYMENT_NAME as an alias
export AZURE_OPENAI_ENDPOINT="https://my-resource.openai.azure.com/"
export AZURE_OPENAI_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."
export AZURE_CHAT_DEPLOYMENT_NAME="gpt-4"  # Alternative to AZURE_OPENAI_DEPLOYMENT_NAME
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-ada-002"
```

### Token Management

#### Token Expiration

Azure AD bearer tokens typically expire after 1 hour. You'll need to refresh tokens periodically:

**Manual Refresh**:
```bash
# Get new token
NEW_TOKEN=$(az account get-access-token --resource https://cognitiveservices.azure.com --query accessToken -o tsv)

# Update environment variable
export AZURE_OPENAI_TOKEN="$NEW_TOKEN"
```

**Automated Refresh Script** (`refresh_token.sh`):
```bash
#!/bin/bash
# refresh_token.sh - Automatically refresh Azure AD token

while true; do
    # Get new token
    TOKEN=$(az account get-access-token --resource https://cognitiveservices.azure.com --query accessToken -o tsv)
    
    # Update environment variable
    export AZURE_OPENAI_TOKEN="$TOKEN"
    
    echo "Token refreshed at $(date)"
    
    # Wait 50 minutes before refreshing (tokens expire in 60 minutes)
    sleep 3000
done
```

**Using Managed Identity** (recommended for Azure resources):
```python
# automatic_token_refresh.py
from azure.identity import DefaultAzureCredential
import os
import time

def refresh_token():
    """Automatically refresh token using managed identity."""
    credential = DefaultAzureCredential()
    
    while True:
        try:
            token = credential.get_token("https://cognitiveservices.azure.com/.default")
            os.environ["AZURE_OPENAI_TOKEN"] = token.token
            print(f"Token refreshed at {time.ctime()}")
            
            # Refresh 5 minutes before expiration
            sleep_time = token.expires_on - time.time() - 300
            time.sleep(max(sleep_time, 0))
        except Exception as e:
            print(f"Error refreshing token: {e}")
            time.sleep(60)  # Retry after 1 minute

if __name__ == "__main__":
    refresh_token()
```

#### Token Security Best Practices

1. **Never commit tokens to version control**
   - Add `.env` to `.gitignore`
   - Use environment variables or Azure Key Vault
   - Tokens are even more sensitive than API keys due to shorter lifespan

2. **Use short-lived tokens**
   - Default 1-hour expiration is recommended
   - Implement automatic refresh
   - Don't extend token lifetime unnecessarily

3. **Rotate tokens regularly**
   - Implement automatic token refresh
   - Use managed identities when possible
   - Monitor token usage and expiration

4. **Secure token storage**
   - Use Azure Key Vault for production
   - Encrypt tokens at rest
   - Use secure environment variable management

### Troubleshooting Azure AD Authentication

#### "401 Unauthorized" with Bearer Token

**Problem**: Bearer token is invalid or expired

**Solutions**:

1. **Check token expiration**:
   ```bash
   # Decode JWT token to check expiration (requires jq)
   echo "$AZURE_OPENAI_TOKEN" | cut -d'.' -f2 | base64 -d | jq '.exp'
   
   # Compare with current time
   date +%s
   ```

2. **Refresh the token**:
   ```bash
   # Get new token
   export AZURE_OPENAI_TOKEN=$(az account get-access-token --resource https://cognitiveservices.azure.com --query accessToken -o tsv)
   ```

3. **Verify token audience**:
   - Token must be for `https://cognitiveservices.azure.com`
   - Check token claims using JWT decoder

4. **Check Azure AD permissions**:
   - Ensure service principal has "Cognitive Services User" role
   - Verify RBAC permissions on the Azure OpenAI resource

#### "403 Forbidden" with Bearer Token

**Problem**: Token is valid but lacks required permissions

**Solutions**:

1. **Assign required role**:
   ```bash
   # Assign Cognitive Services User role
   az role assignment create \
     --assignee <user-or-service-principal-id> \
     --role "Cognitive Services User" \
     --scope /subscriptions/<subscription-id>/resourceGroups/<resource-group>/providers/Microsoft.CognitiveServices/accounts/<resource-name>
   ```

2. **Check resource access**:
   - Verify the resource exists and is accessible
   - Check network restrictions on the resource
   - Ensure no conditional access policies are blocking

3. **Verify tenant**:
   - Ensure you're authenticated to the correct Azure AD tenant
   - Check tenant ID in token matches resource tenant

#### Custom Headers Not Working

**Problem**: Custom headers are not being sent with requests

**Solutions**:

1. **Validate JSON format**:
   ```bash
   # Test JSON parsing
   echo '{"user_sid": "A123456"}' | python -m json.tool
   ```

2. **Check environment variable**:
   ```bash
   echo $AZURE_OPENAI_CUSTOM_HEADERS
   ```

3. **Review logs**:
   ```bash
   # Enable debug logging
   export DEV_AGENT_LOG_LEVEL=DEBUG
   uv run dev-agent --verbose init
   ```

4. **Verify header names**:
   - Use lowercase header names
   - Avoid special characters
   - Check Azure OpenAI header restrictions

#### Token Refresh Failures

**Problem**: Automatic token refresh is failing

**Solutions**:

1. **Check Azure CLI authentication**:
   ```bash
   az account show
   ```

2. **Re-authenticate**:
   ```bash
   az login
   ```

3. **Verify managed identity** (for Azure resources):
   ```bash
   # Test managed identity
   curl 'http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://cognitiveservices.azure.com' -H Metadata:true
   ```

4. **Check service principal credentials**:
   ```bash
   # Verify service principal
   az ad sp show --id <app-id>
   ```

### Migration from API Key to Azure AD

If you're currently using API key authentication and want to migrate to Azure AD:

#### Step 1: Test Azure AD Authentication

Keep your existing API key configuration and add Azure AD:

```bash
# Keep existing API key
export AZURE_OPENAI_API_KEY="your-existing-key"

# Add bearer token (takes precedence)
export AZURE_OPENAI_TOKEN="your-bearer-token"
```

Test that Azure AD authentication works:
```bash
uv run dev-agent azure test
```

#### Step 2: Update Configuration

Once verified, you can remove the API key:

```bash
# Remove API key from environment
unset AZURE_OPENAI_API_KEY

# Keep only bearer token
export AZURE_OPENAI_TOKEN="your-bearer-token"
```

#### Step 3: Update Documentation

Update your team's documentation and deployment scripts to use Azure AD authentication.

#### Step 4: Implement Token Refresh

Set up automatic token refresh to avoid authentication failures:

```bash
# Add to your startup script
./refresh_token.sh &
```

### Best Practices

1. **Use Managed Identities**: When running on Azure infrastructure (VMs, App Service, Functions), use managed identities instead of service principals

2. **Implement Token Refresh**: Always implement automatic token refresh to avoid authentication failures

3. **Monitor Token Usage**: Track token expiration and refresh patterns in your logs

4. **Use Custom Headers**: Leverage custom headers for auditing and compliance tracking

5. **Secure Token Storage**: Never log or expose bearer tokens in error messages or logs

6. **Test Thoroughly**: Test Azure AD authentication in development before deploying to production

7. **Document Configuration**: Maintain clear documentation of your Azure AD setup for your team

8. **Plan for Failures**: Implement fallback mechanisms and clear error messages for authentication failures

## Configuration Options Reference

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AZURE_OPENAI_ENDPOINT` | Your Azure OpenAI endpoint URL | `https://my-resource.openai.azure.com/` |
| `AZURE_OPENAI_API_KEY` | Your Azure OpenAI API key (if using API key auth) | `abc123...` |
| `AZURE_OPENAI_TOKEN` | Azure AD bearer token (if using Azure AD auth) | `eyJ0eXAiOiJKV1Qi...` |
| `AZURE_OPENAI_API_VERSION` | Azure OpenAI API version | `2024-02-15-preview` |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | GPT-4 deployment name | `gpt-4` |
| `AZURE_CHAT_DEPLOYMENT_NAME` | Alternative name for GPT-4 deployment (alias) | `gpt-4` |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Embedding deployment name | `text-embedding-ada-002` |

**Note**: Either `AZURE_OPENAI_API_KEY` or `AZURE_OPENAI_TOKEN` must be provided. If both are present, `AZURE_OPENAI_TOKEN` takes precedence.

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AZURE_OPENAI_MAX_TOKENS` | Maximum tokens for generation | `4000` |
| `AZURE_OPENAI_TEMPERATURE` | Sampling temperature (0.0-2.0) | `0.7` |
| `AZURE_OPENAI_MAX_RETRIES` | Maximum retry attempts | `3` |
| `AZURE_OPENAI_TIMEOUT` | Request timeout in seconds | `60` |
| `AZURE_OPENAI_BATCH_SIZE` | Embedding batch size | `16` |
| `AZURE_OPENAI_USER_SID` | User session ID for auditing | None |
| `AZURE_OPENAI_CUSTOM_HEADERS` | Custom headers as JSON string | `{}` |

## Troubleshooting

### Common API Errors

#### Authentication Errors

##### "401 Unauthorized" or "Authentication failed"

**Problem**: Invalid API key or endpoint configuration

**Symptoms**:
```
Error: Authentication failed
Status Code: 401
Message: Access denied due to invalid subscription key
```

**Solutions**:
1. **Verify API key**:
   - Check Azure Portal → Your Resource → Keys and Endpoint
   - Ensure you copied the entire key (no extra spaces)
   - Try using the other key (KEY 2 instead of KEY 1)
   
2. **Check endpoint URL**:
   - Must end with trailing slash: `https://your-resource.openai.azure.com/`
   - Must match your resource name exactly
   - Should use HTTPS, not HTTP

3. **Regenerate API key**:
   ```bash
   az cognitiveservices account keys regenerate \
     --name my-dev-agent-openai \
     --resource-group dev-agent-rg \
     --key-name key1
   ```

4. **Verify environment variables**:
   ```bash
   echo $AZURE_OPENAI_ENDPOINT
   echo $AZURE_OPENAI_API_KEY
   ```

##### "403 Forbidden"

**Problem**: API key is valid but lacks permissions

**Solutions**:
1. Check Azure RBAC permissions on the resource
2. Ensure your subscription is active
3. Verify the resource is not in a restricted region
4. Check if network restrictions are blocking your IP

#### Deployment Errors

##### "404 Not Found" or "Deployment not found"

**Problem**: Deployment name doesn't match or doesn't exist

**Symptoms**:
```
Error: The API deployment for this resource does not exist
Status Code: 404
Deployment: gpt-4
```

**Solutions**:
1. **Verify deployment names**:
   - Go to Azure OpenAI Studio → Deployments
   - Copy the exact deployment name (case-sensitive)
   - Update your environment variables to match

2. **Check deployment status**:
   - Ensure deployment shows "Succeeded" status
   - Wait 2-3 minutes if just created
   - Try redeploying if status is "Failed"

3. **Verify API version**:
   - Some deployments require specific API versions
   - Try `2024-02-15-preview` or later
   - Check [API version compatibility](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/api-version-deprecation)

4. **Test with Azure CLI**:
   ```bash
   az cognitiveservices account deployment list \
     --name my-dev-agent-openai \
     --resource-group dev-agent-rg
   ```

##### "Model not available in region"

**Problem**: Selected model not supported in your Azure region

**Solutions**:
1. Check [model availability by region](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/concepts/models#model-summary-table-and-region-availability)
2. Create a new resource in a supported region (e.g., East US, Sweden Central)
3. Use an alternative model (e.g., `gpt-35-turbo` instead of `gpt-4`)

#### Rate Limiting Errors

##### "429 Too Many Requests" or "Rate limit exceeded"

**Problem**: Exceeded tokens-per-minute (TPM) or requests-per-minute (RPM) quota

**Symptoms**:
```
Error: Rate limit is exceeded
Status Code: 429
Retry-After: 20 seconds
```

**Solutions**:
1. **Wait and retry** (dev-agent does this automatically):
   - Check `Retry-After` header for wait time
   - Implement exponential backoff
   - dev-agent uses tenacity for automatic retries

2. **Increase rate limits**:
   - Go to Azure OpenAI Studio → Deployments
   - Edit deployment → Increase TPM limit
   - Maximum depends on your quota

3. **Request quota increase**:
   - Azure Portal → Your Resource → Quotas
   - Click "Request quota increase"
   - Provide justification and expected usage

4. **Optimize token usage**:
   - Reduce `max_tokens` parameter
   - Use shorter prompts
   - Implement caching for repeated queries
   - Batch embedding requests

5. **Monitor usage**:
   ```bash
   # Check current usage
   uv run dev-agent cost --phase indexing
   ```

#### Timeout Errors

##### "408 Request Timeout" or "Connection timeout"

**Problem**: Request took too long to complete

**Symptoms**:
```
Error: Request timed out
Status Code: 408
Timeout: 60 seconds
```

**Solutions**:
1. **Increase timeout**:
   ```bash
   export AZURE_OPENAI_TIMEOUT=120  # 2 minutes
   ```

2. **Check network connectivity**:
   ```bash
   # Test endpoint reachability
   curl -I https://your-resource.openai.azure.com/
   ```

3. **Reduce request complexity**:
   - Lower `max_tokens` value
   - Simplify prompts
   - Break large requests into smaller chunks

4. **Check Azure service status**:
   - Visit [Azure Status](https://status.azure.com/)
   - Check for outages in your region

5. **Try different region**:
   - Create resource in alternative region
   - Use geo-redundant setup for production

#### Content Filtering Errors

##### "400 Bad Request" with content filter message

**Problem**: Request or response triggered Azure content filters

**Symptoms**:
```
Error: The response was filtered due to the prompt triggering Azure OpenAI's content management policy
Status Code: 400
```

**Solutions**:
1. **Review content policies**:
   - Check [Azure OpenAI content filtering](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/concepts/content-filter)
   - Understand what triggers filters (hate, violence, sexual, self-harm)

2. **Modify prompts**:
   - Rephrase to avoid triggering filters
   - Remove potentially sensitive content
   - Use more neutral language

3. **Configure content filters** (if available):
   - Azure Portal → Your Resource → Content filters
   - Adjust filter severity levels
   - Note: Some filters cannot be disabled

4. **Request filter exemption**:
   - For legitimate use cases
   - Contact Azure support
   - Provide detailed justification

#### Token Limit Errors

##### "400 Bad Request" - "Maximum context length exceeded"

**Problem**: Total tokens (prompt + completion) exceed model limit

**Symptoms**:
```
Error: This model's maximum context length is 8192 tokens
Status Code: 400
Requested: 9500 tokens
```

**Solutions**:
1. **Check token counts**:
   ```python
   from dev_agent.llm.token_counter import TokenCounter
   
   counter = TokenCounter()
   token_count = counter.count_tokens(your_prompt)
   print(f"Prompt tokens: {token_count}")
   ```

2. **Reduce prompt size**:
   - Shorten context
   - Remove unnecessary examples
   - Summarize long code snippets

3. **Reduce max_tokens**:
   ```bash
   export AZURE_OPENAI_MAX_TOKENS=2000
   ```

4. **Use model with larger context**:
   - `gpt-4-32k`: 32,768 tokens
   - `gpt-4-turbo`: 128,000 tokens
   - `gpt-4o`: 128,000 tokens

5. **Implement chunking**:
   - Split large documents
   - Process in multiple requests
   - Combine results

#### Invalid Request Errors

##### "400 Bad Request" - "Invalid parameter"

**Problem**: Request contains invalid parameters

**Common causes**:
- Invalid `temperature` value (must be 0.0-2.0)
- Invalid `max_tokens` (must be positive integer)
- Invalid `top_p` value (must be 0.0-1.0)
- Unsupported parameter for model

**Solutions**:
1. **Validate parameters**:
   ```python
   # Valid ranges
   temperature: 0.0 - 2.0
   max_tokens: 1 - model_max
   top_p: 0.0 - 1.0
   frequency_penalty: -2.0 - 2.0
   presence_penalty: -2.0 - 2.0
   ```

2. **Check API version compatibility**:
   - Some parameters require specific API versions
   - Update `AZURE_OPENAI_API_VERSION` if needed

3. **Review model capabilities**:
   - Not all models support all parameters
   - Check model documentation

### Network and Connectivity Issues

#### "Connection refused" or "Name resolution failed"

**Problem**: Cannot reach Azure OpenAI endpoint

**Solutions**:
1. **Check DNS resolution**:
   ```bash
   nslookup your-resource.openai.azure.com
   ```

2. **Check firewall rules**:
   - Corporate firewall may block Azure OpenAI
   - Check proxy settings
   - Verify outbound HTTPS (443) is allowed

3. **Test connectivity**:
   ```bash
   curl -v https://your-resource.openai.azure.com/
   ```

4. **Check VPN/proxy**:
   - Disable VPN temporarily to test
   - Configure proxy settings if required

#### "SSL certificate verification failed"

**Problem**: SSL/TLS certificate issues

**Solutions**:
1. **Update CA certificates**:
   ```bash
   # Ubuntu/Debian
   sudo apt-get update && sudo apt-get install ca-certificates
   
   # macOS
   brew install ca-certificates
   ```

2. **Check system time**:
   - Ensure system clock is accurate
   - SSL certificates are time-sensitive

3. **Verify endpoint URL**:
   - Must use HTTPS
   - Check for typos in domain name

### Debugging Tips

#### Enable Debug Logging

```bash
# Set log level to DEBUG
export DEV_AGENT_LOG_LEVEL=DEBUG

# Run with verbose output
uv run dev-agent --verbose init
```

#### Check Configuration

```bash
# Validate configuration
uv run dev-agent validate

# Test Azure connection
uv run dev-agent azure test

# Show current configuration
uv run dev-agent config show
```

#### Monitor API Calls

```bash
# View cost report
uv run dev-agent cost

# View detailed usage
uv run dev-agent cost --detailed

# Export usage data
uv run dev-agent cost --export usage.json
```

#### Test with Minimal Example

Create `test_minimal.py`:
```python
import asyncio
import os
from openai import AsyncAzureOpenAI

async def test():
    client = AsyncAzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    )
    
    response = await client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=10,
    )
    
    print(response.choices[0].message.content)

asyncio.run(test())
```

Run:
```bash
uv run python test_minimal.py
```

### Getting Help

If you're still experiencing issues:

1. **Check Azure Service Health**:
   - [Azure Status Dashboard](https://status.azure.com/)
   - [Azure OpenAI Service Updates](https://azure.microsoft.com/en-us/updates/?product=cognitive-services)

2. **Review Documentation**:
   - [Azure OpenAI Documentation](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/)
   - [API Reference](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/reference)

3. **Contact Support**:
   - [Azure Support](https://azure.microsoft.com/en-us/support/options/)
   - [GitHub Issues](https://github.com/your-repo/dev-agent/issues)

4. **Community Resources**:
   - [Azure OpenAI Community](https://techcommunity.microsoft.com/t5/azure-ai-services/ct-p/AzureAIServices)
   - [Stack Overflow](https://stackoverflow.com/questions/tagged/azure-openai)

For more general troubleshooting, see the [Troubleshooting Guide](../getting-started/troubleshooting.md).

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

## Cost Estimation and Budgeting

Understanding and managing Azure OpenAI costs is crucial for sustainable usage. This section helps you estimate, track, and optimize your spending.

### Azure OpenAI Pricing Overview

Azure OpenAI charges based on token usage. Tokens are pieces of words used for processing text.

#### Current Pricing (as of 2024)

**GPT-4 Models**:
| Model | Input (per 1K tokens) | Output (per 1K tokens) | Context Window |
|-------|----------------------|------------------------|----------------|
| GPT-4 (8K) | $0.03 | $0.06 | 8,192 tokens |
| GPT-4-32K | $0.06 | $0.12 | 32,768 tokens |
| GPT-4 Turbo | $0.01 | $0.03 | 128,000 tokens |
| GPT-4o | $0.005 | $0.015 | 128,000 tokens |

**GPT-3.5 Models**:
| Model | Input (per 1K tokens) | Output (per 1K tokens) | Context Window |
|-------|----------------------|------------------------|----------------|
| GPT-3.5 Turbo | $0.0005 | $0.0015 | 16,385 tokens |
| GPT-3.5 Turbo 16K | $0.001 | $0.002 | 16,385 tokens |

**Embeddings**:
| Model | Price (per 1K tokens) | Dimensions |
|-------|----------------------|------------|
| text-embedding-ada-002 | $0.0001 | 1,536 |
| text-embedding-3-small | $0.00002 | 1,536 |
| text-embedding-3-large | $0.00013 | 3,072 |

**Note**: Prices may vary by region and are subject to change. Check [Azure OpenAI Pricing](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/) for current rates.

### Understanding Token Usage

#### What are Tokens?

Tokens are pieces of words. As a rough rule of thumb:
- 1 token ≈ 4 characters in English
- 1 token ≈ ¾ of a word
- 100 tokens ≈ 75 words
- 1,000 tokens ≈ 750 words

#### Token Counting Examples

```python
# Use dev-agent's token counter
from dev_agent.llm.token_counter import TokenCounter

counter = TokenCounter()

# Example texts
short_text = "Hello, world!"
print(counter.count_tokens(short_text))  # ~4 tokens

code_snippet = """
def hello_world():
    print("Hello, world!")
    return True
"""
print(counter.count_tokens(code_snippet))  # ~20 tokens

long_document = "..." # 1000 words
print(counter.count_tokens(long_document))  # ~1,333 tokens
```

#### Token Usage by Operation

**Indexing Phase** (per file):
- Small file (100 lines): ~500 tokens for embedding
- Medium file (500 lines): ~2,500 tokens for embedding
- Large file (2000 lines): ~10,000 tokens for embedding

**Specification Phase**:
- Context retrieval: ~2,000 tokens (input)
- Specification generation: ~3,000 tokens (output)
- Total per specification: ~5,000 tokens

**Design Phase**:
- Context + specification: ~5,000 tokens (input)
- Design document: ~4,000 tokens (output)
- Total per design: ~9,000 tokens

**Implementation Phase**:
- Context + design: ~6,000 tokens (input)
- Code generation: ~2,000 tokens (output)
- Total per implementation: ~8,000 tokens

### Cost Estimation for Common Scenarios

#### Small Project (10 files, ~1,000 lines total)

**Indexing**:
- Embeddings: 10,000 tokens × $0.0001/1K = $0.001

**Specification**:
- GPT-4 Turbo: (2K input + 3K output) × 1 spec = 5K tokens
- Cost: (2K × $0.01/1K) + (3K × $0.03/1K) = $0.11

**Design**:
- GPT-4 Turbo: (5K input + 4K output) × 1 design = 9K tokens
- Cost: (5K × $0.01/1K) + (4K × $0.03/1K) = $0.17

**Implementation**:
- GPT-4 Turbo: (6K input + 2K output) × 5 tasks = 40K tokens
- Cost: (30K × $0.01/1K) + (10K × $0.03/1K) = $0.60

**Total Estimated Cost**: ~$0.88

#### Medium Project (100 files, ~10,000 lines total)

**Indexing**:
- Embeddings: 100,000 tokens × $0.0001/1K = $0.01

**Specification**:
- GPT-4 Turbo: 5K tokens × 3 specs = 15K tokens
- Cost: $0.33

**Design**:
- GPT-4 Turbo: 9K tokens × 3 designs = 27K tokens
- Cost: $0.51

**Implementation**:
- GPT-4 Turbo: 8K tokens × 20 tasks = 160K tokens
- Cost: $2.40

**Total Estimated Cost**: ~$3.25

#### Large Project (1,000 files, ~100,000 lines total)

**Indexing**:
- Embeddings: 1,000,000 tokens × $0.0001/1K = $0.10

**Specification**:
- GPT-4 Turbo: 5K tokens × 10 specs = 50K tokens
- Cost: $1.10

**Design**:
- GPT-4 Turbo: 9K tokens × 10 designs = 90K tokens
- Cost: $1.70

**Implementation**:
- GPT-4 Turbo: 8K tokens × 50 tasks = 400K tokens
- Cost: $6.00

**Total Estimated Cost**: ~$8.90

### Cost Tracking with dev-agent

dev-agent automatically tracks all token usage and costs.

#### View Current Costs

```bash
# Show overall cost summary
uv run dev-agent cost

# Output:
# Cost Summary
# ════════════════════════════════════════
# Total Tokens: 125,430
# Total Cost: $2.45
# 
# By Phase:
# - Indexing: $0.01 (1,000 tokens)
# - Specification: $0.33 (15,000 tokens)
# - Design: $0.51 (27,000 tokens)
# - Implementation: $1.60 (82,430 tokens)
```

#### View Phase-Specific Costs

```bash
# Cost for specific phase
uv run dev-agent cost --phase indexing
uv run dev-agent cost --phase specification
uv run dev-agent cost --phase design
uv run dev-agent cost --phase implementation
```

#### Export Cost Data

```bash
# Export to JSON for analysis
uv run dev-agent cost --export costs.json

# Export to CSV
uv run dev-agent cost --export costs.csv --format csv
```

#### Cost Report Structure

```json
{
  "total_cost": 2.45,
  "total_tokens": 125430,
  "by_phase": {
    "indexing": {
      "tokens": 1000,
      "cost": 0.01,
      "operations": 10
    },
    "specification": {
      "prompt_tokens": 6000,
      "completion_tokens": 9000,
      "cost": 0.33,
      "operations": 3
    }
  },
  "by_model": {
    "gpt-4-turbo": {
      "tokens": 124430,
      "cost": 2.44
    },
    "text-embedding-ada-002": {
      "tokens": 1000,
      "cost": 0.01
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Setting Up Budget Alerts

#### Environment Variable Budget

```bash
# Set budget threshold (in USD)
export AZURE_OPENAI_BUDGET_THRESHOLD=10.00

# Enable budget warnings
export AZURE_OPENAI_BUDGET_WARNINGS=true
```

When costs approach or exceed the threshold:
```
⚠️  Warning: Budget threshold approaching
Current cost: $9.50 / $10.00 (95%)
Remaining: $0.50
```

#### Azure Cost Management

Set up cost alerts in Azure Portal:

1. **Navigate to Cost Management**:
   - Azure Portal → Cost Management + Billing
   - Select your subscription
   - Click "Cost alerts"

2. **Create Budget**:
   - Click "Add" → "Budget"
   - Name: "Azure OpenAI Monthly Budget"
   - Amount: $50 (adjust as needed)
   - Reset period: Monthly
   - Start date: First day of month

3. **Configure Alerts**:
   - Alert condition: Actual cost
   - Alert threshold: 80% of budget ($40)
   - Action group: Email notification
   - Add additional thresholds: 90%, 100%

4. **Monitor Usage**:
   - View cost analysis dashboard
   - Download usage reports
   - Set up automated reports

### Cost Optimization Strategies

#### 1. Use Appropriate Models

**For Simple Tasks** (use GPT-3.5 Turbo):
- Simple code formatting
- Basic documentation
- Straightforward refactoring
- Cost: ~10x cheaper than GPT-4

**For Complex Tasks** (use GPT-4 Turbo):
- Architecture design
- Complex code generation
- Specification writing
- Cost: Best balance of quality and price

**For Maximum Quality** (use GPT-4):
- Critical production code
- Security-sensitive implementations
- Complex algorithms
- Cost: Highest, but best quality

#### 2. Optimize Token Usage

**Reduce Prompt Size**:
```python
# ❌ Inefficient - includes unnecessary context
prompt = f"""
Here is the entire codebase:
{entire_codebase}  # 50,000 tokens!

Generate a function to add two numbers.
"""

# ✅ Efficient - only relevant context
prompt = f"""
Relevant examples:
{relevant_snippets}  # 500 tokens

Generate a function to add two numbers.
"""
```

**Use Caching**:
- dev-agent caches embeddings automatically
- Avoid re-indexing unchanged files
- Reuse generated specifications

**Batch Operations**:
```python
# ✅ Efficient - batch embeddings
embeddings = await client.embed_batch(texts, batch_size=16)

# ❌ Inefficient - individual requests
embeddings = [await client.embed_text(text) for text in texts]
```

#### 3. Set Token Limits

```bash
# Limit maximum tokens per request
export AZURE_OPENAI_MAX_TOKENS=2000

# Reduce temperature for more focused output
export AZURE_OPENAI_TEMPERATURE=0.3
```

#### 4. Use Incremental Development

```bash
# Generate one task at a time
uv run dev-agent phase implementation --task 1

# Review before generating next task
uv run dev-agent phase implementation --task 2
```

#### 5. Monitor and Analyze

```bash
# Regular cost reviews
uv run dev-agent cost --detailed

# Identify expensive operations
uv run dev-agent cost --by-operation

# Compare costs across projects
uv run dev-agent cost --export project1.json
uv run dev-agent cost --export project2.json
```

### Cost Comparison: Azure OpenAI vs Alternatives

| Provider | GPT-4 Equivalent | Cost (per 1M tokens) | Notes |
|----------|------------------|---------------------|-------|
| Azure OpenAI | GPT-4 Turbo | $10-30 | Enterprise features, SLA |
| OpenAI Direct | GPT-4 Turbo | $10-30 | No enterprise features |
| AWS Bedrock | Claude 3 Opus | $15-75 | Different pricing model |
| Local Models | Llama 3 70B | $0 (compute only) | Requires GPU infrastructure |

**Azure OpenAI Advantages**:
- Enterprise SLA and support
- Data residency and compliance
- Integration with Azure services
- Managed infrastructure
- No GPU costs

### Sample Monthly Budgets

#### Individual Developer
- **Light usage**: $10-25/month
  - Small projects
  - Occasional code generation
  - Learning and experimentation

- **Regular usage**: $25-100/month
  - Multiple projects
  - Daily code generation
  - Full workflow usage

#### Small Team (3-5 developers)
- **Budget**: $100-500/month
  - Shared Azure OpenAI resource
  - Multiple concurrent projects
  - Regular specification and design generation

#### Enterprise Team (10+ developers)
- **Budget**: $500-2,000+/month
  - High-volume usage
  - Large codebases
  - Continuous integration
  - Production workloads

### Cost Monitoring Best Practices

1. **Set up alerts early**:
   - Configure Azure cost alerts
   - Set dev-agent budget thresholds
   - Review weekly

2. **Track by project**:
   - Use separate Azure resources per project
   - Tag resources appropriately
   - Generate per-project cost reports

3. **Regular audits**:
   - Monthly cost review meetings
   - Identify optimization opportunities
   - Adjust budgets as needed

4. **Educate team members**:
   - Share cost awareness
   - Provide optimization guidelines
   - Celebrate cost savings

5. **Plan for growth**:
   - Start with conservative budgets
   - Scale based on actual usage
   - Negotiate enterprise agreements for high volume

### Cost Estimation Tools

#### Built-in Estimator

```bash
# Estimate cost before running
uv run dev-agent estimate --files 100 --lines 10000

# Output:
# Cost Estimation
# ════════════════════════════════════════
# Project Size: 100 files, ~10,000 lines
# 
# Estimated Costs:
# - Indexing: $0.01
# - Specification (3 specs): $0.33
# - Design (3 designs): $0.51
# - Implementation (20 tasks): $2.40
# 
# Total Estimated: $3.25
# 
# Proceed? [y/N]:
```

#### Custom Cost Calculator

Create `calculate_cost.py`:
```python
from dev_agent.llm.cost_tracker import CostCalculator

calculator = CostCalculator()

# Estimate for your project
estimate = calculator.estimate_project_cost(
    num_files=100,
    avg_lines_per_file=100,
    num_specifications=3,
    num_designs=3,
    num_tasks=20,
    model="gpt-4-turbo"
)

print(f"Estimated cost: ${estimate.total_cost:.2f}")
print(f"Breakdown: {estimate.breakdown}")
```

## Next Steps

- [Azure AD Migration Guide](./azure-ad-migration-guide.md) - Migrate from API key to Azure AD authentication
- [Cost Management Guide](../usage/cost-management.md) - Learn how to track and optimize costs
- [Usage Examples](../examples/azure-setup.md) - See practical examples
- [API Documentation](../api/llm.md) - Explore the LLM integration API
- [Troubleshooting Guide](../getting-started/troubleshooting.md) - Solve common issues

## Additional Resources

- [Azure OpenAI Documentation](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/)
- [Azure OpenAI Pricing](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/)
- [Azure OpenAI Service Limits](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/quotas-limits)
- [Azure OpenAI Best Practices](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/how-to/best-practices)
