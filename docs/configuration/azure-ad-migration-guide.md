# Azure AD Authentication Migration Guide

This guide helps you migrate from API key authentication to Azure AD authentication for Azure OpenAI integration in dev-agent.

## Overview

dev-agent supports two authentication methods for Azure OpenAI:

1. **API Key Authentication** (default): Simple authentication using a static API key
2. **Azure AD Authentication**: Enterprise authentication using bearer tokens with automatic rotation

Azure AD authentication is recommended for enterprise environments that require:
- Enhanced security with short-lived tokens
- Centralized access control through Azure AD policies
- Detailed auditing and compliance tracking
- Managed identity support for Azure infrastructure

## Migration Steps

### Step 1: Understand Current Configuration

First, identify your current API key configuration. Check your environment variables:

```bash
# Current API key configuration
echo $AZURE_OPENAI_ENDPOINT
echo $AZURE_OPENAI_API_KEY
echo $AZURE_OPENAI_DEPLOYMENT_NAME
echo $AZURE_OPENAI_EMBEDDING_DEPLOYMENT
```

### Step 2: Obtain Azure AD Bearer Token

You have several options for obtaining a bearer token:

#### Option A: Using Azure CLI (Recommended for Development)

```bash
# Login to Azure
az login

# Get bearer token for Azure OpenAI
az account get-access-token --resource https://cognitiveservices.azure.com/.default --query accessToken -o tsv
```

#### Option B: Using Managed Identity (Recommended for Production)

If running on Azure infrastructure (VM, App Service, Functions), use managed identity:

```python
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
token = credential.get_token("https://cognitiveservices.azure.com/.default")
bearer_token = token.token
```

#### Option C: Using Service Principal

```bash
# Set service principal credentials
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_TENANT_ID="your-tenant-id"

# Get token using Azure CLI
az login --service-principal -u $AZURE_CLIENT_ID -p $AZURE_CLIENT_SECRET --tenant $AZURE_TENANT_ID
az account get-access-token --resource https://cognitiveservices.azure.com/.default --query accessToken -o tsv
```

### Step 3: Update Environment Variables

Replace your API key configuration with Azure AD configuration:

**Before (API Key):**
```bash
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_KEY="sk-..."
export AZURE_OPENAI_API_VERSION="2024-02-15-preview"
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-ada-002"
```

**After (Azure AD):**
```bash
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."
export AZURE_OPENAI_API_VERSION="2024-02-15-preview"
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-ada-002"

# Optional: Add auditing headers
export AZURE_OPENAI_USER_SID="A123456"
export AZURE_OPENAI_CUSTOM_HEADERS='{"department": "engineering", "project": "dev-agent"}'
```

### Step 4: Test the Configuration

Verify your Azure AD authentication works:

```bash
# Test with dev-agent CLI
uv run dev-agent --help

# Or test with a simple Python script
python -c "
import os
from dev_agent.config.config_manager import ConfigManager

config_manager = ConfigManager()
azure_config = config_manager.get_azure_config()
print(f'Authentication method: {\"Azure AD\" if azure_config.bearer_token else \"API Key\"}')
print(f'Endpoint: {azure_config.endpoint}')
print(f'Deployment: {azure_config.deployment_name}')
"
```

### Step 5: Remove API Key (Optional)

Once Azure AD authentication is working, you can remove the API key:

```bash
# Unset the API key environment variable
unset AZURE_OPENAI_API_KEY

# Or remove it from your .env file
```

**Note:** You can keep both configured. Bearer token takes precedence when both are present.

## Side-by-Side Configuration Examples

### Example 1: Basic Migration

**API Key Configuration:**
```bash
# .env file
AZURE_OPENAI_ENDPOINT=https://my-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=sk-abc123def456ghi789jkl012mno345pqr678stu901vwx234yz
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

**Azure AD Configuration:**
```bash
# .env file
AZURE_OPENAI_ENDPOINT=https://my-resource.openai.azure.com/
AZURE_OPENAI_TOKEN=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6Ik1yNS1BVWliZkJpaTdOZDFqQmViYXhib1hXMCIsImtpZCI6Ik1yNS1BVWliZkJpaTdOZDFqQmViYXhib1hXMCJ9...
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

### Example 2: With Custom Headers for Auditing

**API Key Configuration:**
```bash
AZURE_OPENAI_ENDPOINT=https://my-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=sk-abc123def456ghi789jkl012mno345pqr678stu901vwx234yz
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

**Azure AD Configuration with Auditing:**
```bash
AZURE_OPENAI_ENDPOINT=https://my-resource.openai.azure.com/
AZURE_OPENAI_TOKEN=eyJ0eXAiOiJKV1QiLCJhbGc...
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Auditing headers
AZURE_OPENAI_USER_SID=A123456
AZURE_OPENAI_CUSTOM_HEADERS={"department": "engineering", "cost_center": "CC-1234", "environment": "production"}
```

### Example 3: Using Deployment Name Alias

**API Key Configuration:**
```bash
AZURE_OPENAI_ENDPOINT=https://my-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=sk-abc123def456ghi789jkl012mno345pqr678stu901vwx234yz
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

**Azure AD Configuration with Alias:**
```bash
AZURE_OPENAI_ENDPOINT=https://my-resource.openai.azure.com/
AZURE_OPENAI_TOKEN=eyJ0eXAiOiJKV1QiLCJhbGc...
AZURE_CHAT_DEPLOYMENT_NAME=gpt-4  # Alternative to AZURE_OPENAI_DEPLOYMENT_NAME
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

## Environment Variable Precedence Rules

Understanding precedence is important when both authentication methods are configured:

### Authentication Method Precedence

1. **Bearer Token** (highest priority)
   - If `AZURE_OPENAI_TOKEN` is set, it will be used
   - API key is ignored even if present
   - `openai_api_type` is automatically set to "azure_ad"

2. **API Key** (fallback)
   - Used only if `AZURE_OPENAI_TOKEN` is not set
   - `openai_api_type` remains "azure"

### Deployment Name Precedence

1. **AZURE_CHAT_DEPLOYMENT_NAME** (highest priority)
   - New alias for deployment name
   - Takes precedence over `AZURE_OPENAI_DEPLOYMENT_NAME`

2. **AZURE_OPENAI_DEPLOYMENT_NAME** (fallback)
   - Standard deployment name variable
   - Used if `AZURE_CHAT_DEPLOYMENT_NAME` is not set

### Custom Headers Precedence

1. **AZURE_OPENAI_CUSTOM_HEADERS** (JSON object)
   - Parsed as JSON dictionary
   - Merged with other headers

2. **AZURE_OPENAI_USER_SID** (individual header)
   - Added to custom headers dictionary
   - Overrides `user_sid` in `AZURE_OPENAI_CUSTOM_HEADERS` if both are set

### Complete Precedence Example

```bash
# All variables set - shows precedence
export AZURE_OPENAI_TOKEN="token-123"              # Used (bearer token takes precedence)
export AZURE_OPENAI_API_KEY="key-456"              # Ignored (token present)
export AZURE_CHAT_DEPLOYMENT_NAME="gpt-4-turbo"    # Used (alias takes precedence)
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"        # Ignored (alias present)
export AZURE_OPENAI_USER_SID="A123456"             # Added to headers
export AZURE_OPENAI_CUSTOM_HEADERS='{"user_sid": "B999999", "dept": "eng"}'  # user_sid overridden by AZURE_OPENAI_USER_SID

# Result:
# - Authentication: Azure AD with token-123
# - Deployment: gpt-4-turbo
# - Headers: {"user_sid": "A123456", "dept": "eng"}
```

## Frequently Asked Questions (FAQ)

### General Questions

**Q: Do I need to change my code when migrating to Azure AD?**

A: No code changes are required. Simply update your environment variables. dev-agent automatically detects and uses the appropriate authentication method.

**Q: Can I use both API key and Azure AD authentication?**

A: Yes, you can configure both. Bearer token takes precedence when both are present. This allows for gradual migration and fallback scenarios.

**Q: Will my existing API key stop working after migration?**

A: No, API keys continue to work. You can keep the API key as a fallback or remove it entirely after confirming Azure AD works.

**Q: How do I know which authentication method is being used?**

A: Check the logs when dev-agent initializes. You'll see messages like:
```
INFO: Initialized Azure OpenAI client for deployment: gpt-4 using Azure AD authentication
```

### Token Management

**Q: How long do Azure AD bearer tokens last?**

A: Bearer tokens typically expire after 1 hour. You need to implement token refresh for long-running processes.

**Q: How do I refresh expired tokens?**

A: Use Azure SDK's `DefaultAzureCredential` for automatic token refresh:

```python
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
token = credential.get_token("https://cognitiveservices.azure.com/.default")
os.environ["AZURE_OPENAI_TOKEN"] = token.token
```

**Q: What happens if my token expires during execution?**

A: You'll receive an authentication error. Implement token refresh before starting long-running operations, or use managed identity for automatic refresh.

**Q: Can I use the same token for multiple Azure OpenAI resources?**

A: Yes, if the token has access to multiple resources. The token is scoped to the Azure Cognitive Services resource, not a specific OpenAI instance.

### Security Questions

**Q: Is Azure AD authentication more secure than API keys?**

A: Yes, Azure AD provides:
- Short-lived tokens (1 hour expiration)
- Centralized access control
- Audit logging through Azure AD
- Support for conditional access policies
- No long-lived credentials to manage

**Q: Where should I store bearer tokens?**

A: For production:
- Use Azure Key Vault for token storage
- Use managed identities when running on Azure infrastructure
- Never commit tokens to version control
- Use environment variables for local development

**Q: How do I rotate credentials with Azure AD?**

A: With Azure AD, you don't rotate tokens manually. Tokens expire automatically after 1 hour. For service principals, rotate the client secret in Azure AD.

**Q: Can I use Azure AD authentication with managed identities?**

A: Yes, this is the recommended approach for production. Managed identities automatically handle token acquisition and refresh:

```python
from azure.identity import ManagedIdentityCredential

credential = ManagedIdentityCredential()
token = credential.get_token("https://cognitiveservices.azure.com/.default")
```

### Custom Headers

**Q: What are custom headers used for?**

A: Custom headers enable:
- User tracking and auditing (`user_sid`)
- Cost allocation by department or project
- Environment identification (dev/staging/prod)
- Compliance and regulatory tracking

**Q: Are custom headers required for Azure AD authentication?**

A: No, custom headers are optional. They're useful for auditing but not required for authentication.

**Q: What format should custom headers use?**

A: Use JSON format for `AZURE_OPENAI_CUSTOM_HEADERS`:
```bash
export AZURE_OPENAI_CUSTOM_HEADERS='{"key1": "value1", "key2": "value2"}'
```

**Q: Can I use custom headers with API key authentication?**

A: Yes, custom headers work with both authentication methods.

### Troubleshooting

**Q: I get "authentication failed" errors after migration. What should I check?**

A: Verify:
1. Token is not expired (tokens last 1 hour)
2. Token has correct scope: `https://cognitiveservices.azure.com/.default`
3. Azure AD user/service principal has access to the Azure OpenAI resource
4. Endpoint URL is correct
5. No typos in environment variable names

**Q: How do I test if my Azure AD configuration is correct?**

A: Run this test script:

```python
import os
from dev_agent.config.config_manager import ConfigManager

try:
    config_manager = ConfigManager()
    azure_config = config_manager.get_azure_config()
    
    print("✓ Configuration loaded successfully")
    print(f"  Authentication: {'Azure AD' if azure_config.bearer_token else 'API Key'}")
    print(f"  Endpoint: {azure_config.endpoint}")
    print(f"  Deployment: {azure_config.deployment_name}")
    
    if azure_config.custom_headers:
        print(f"  Custom headers: {list(azure_config.custom_headers.keys())}")
    
except Exception as e:
    print(f"✗ Configuration error: {e}")
```

**Q: My custom headers JSON is not parsing. What's wrong?**

A: Common issues:
- Use single quotes around the JSON string in bash: `'{"key": "value"}'`
- Ensure valid JSON format (double quotes for keys and string values)
- Escape special characters if needed
- Check logs for parsing errors

**Q: Can I use Azure AD authentication in CI/CD pipelines?**

A: Yes, use service principal authentication:

```bash
# In your CI/CD pipeline
az login --service-principal -u $AZURE_CLIENT_ID -p $AZURE_CLIENT_SECRET --tenant $AZURE_TENANT_ID
export AZURE_OPENAI_TOKEN=$(az account get-access-token --resource https://cognitiveservices.azure.com/.default --query accessToken -o tsv)
```

### Migration Issues

**Q: I migrated but dev-agent still uses API key. Why?**

A: Check:
1. `AZURE_OPENAI_TOKEN` environment variable is set
2. Token is not empty or malformed
3. Environment variables are loaded in your shell session
4. No typos in variable name (it's `AZURE_OPENAI_TOKEN`, not `AZURE_OPENAI_BEARER_TOKEN`)

**Q: Can I migrate gradually (some environments use API key, others use Azure AD)?**

A: Yes, configure different environment variables per environment:
- Development: API key for simplicity
- Staging: Azure AD for testing
- Production: Azure AD with managed identity

**Q: Do I need to update my code after migration?**

A: No, dev-agent handles both authentication methods transparently. Only environment variables need to change.

## Security Best Practices

### Token Storage

**DO:**
- ✅ Use Azure Key Vault for production token storage
- ✅ Use managed identities when running on Azure infrastructure
- ✅ Store tokens in environment variables for local development
- ✅ Use `.env` files (added to `.gitignore`) for local development
- ✅ Implement automatic token refresh for long-running processes
- ✅ Use short-lived tokens (default 1-hour expiration)

**DON'T:**
- ❌ Commit tokens to version control
- ❌ Hardcode tokens in source code
- ❌ Share tokens between users
- ❌ Log tokens in application logs
- ❌ Store tokens in plain text files
- ❌ Use long-lived tokens without rotation

### Access Control

**DO:**
- ✅ Use Azure RBAC to control access to Azure OpenAI resources
- ✅ Grant minimum required permissions (Cognitive Services User role)
- ✅ Use separate service principals for different environments
- ✅ Enable Azure AD conditional access policies
- ✅ Monitor and audit token usage through Azure AD logs
- ✅ Implement token refresh before expiration

**DON'T:**
- ❌ Use the same credentials across all environments
- ❌ Grant excessive permissions (like Contributor or Owner)
- ❌ Share service principal credentials
- ❌ Disable audit logging
- ❌ Use personal accounts for production services

### Auditing and Compliance

**DO:**
- ✅ Use `user_sid` header to track individual users
- ✅ Add custom headers for cost allocation and compliance
- ✅ Enable Azure OpenAI logging and monitoring
- ✅ Review access logs regularly
- ✅ Implement alerting for unusual usage patterns
- ✅ Document your authentication configuration

**DON'T:**
- ❌ Include sensitive data in custom headers
- ❌ Disable logging for compliance-critical operations
- ❌ Ignore authentication failures
- ❌ Use generic or shared user identifiers

### Token Refresh Implementation

For long-running processes, implement automatic token refresh:

```python
import time
from azure.identity import DefaultAzureCredential
from datetime import datetime, timedelta

class TokenManager:
    """Manage Azure AD token refresh."""
    
    def __init__(self):
        self.credential = DefaultAzureCredential()
        self.current_token = None
        self.token_expiry = None
    
    def get_token(self) -> str:
        """Get current token or refresh if expired."""
        current_time = datetime.now()
        
        # Refresh if token expires in less than 5 minutes
        if not self.current_token or current_time >= (self.token_expiry - timedelta(minutes=5)):
            token_obj = self.credential.get_token(
                "https://cognitiveservices.azure.com/.default"
            )
            self.current_token = token_obj.token
            self.token_expiry = datetime.fromtimestamp(token_obj.expires_on)
            
            print(f"Token refreshed. Expires at: {self.token_expiry}")
        
        return self.current_token

# Usage
token_manager = TokenManager()

# Update environment variable before each operation
import os
os.environ["AZURE_OPENAI_TOKEN"] = token_manager.get_token()
```

### Managed Identity Configuration

For production deployments on Azure infrastructure:

```python
# app.py - Production configuration with managed identity
from azure.identity import ManagedIdentityCredential
import os

def configure_azure_openai():
    """Configure Azure OpenAI with managed identity."""
    
    # Use managed identity for authentication
    credential = ManagedIdentityCredential()
    token = credential.get_token("https://cognitiveservices.azure.com/.default")
    
    # Set environment variables
    os.environ["AZURE_OPENAI_TOKEN"] = token.token
    os.environ["AZURE_OPENAI_ENDPOINT"] = "https://your-resource.openai.azure.com/"
    os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"] = "gpt-4"
    os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"] = "text-embedding-ada-002"
    
    # Add auditing headers
    os.environ["AZURE_OPENAI_CUSTOM_HEADERS"] = json.dumps({
        "environment": "production",
        "application": "dev-agent",
        "version": "1.0.0"
    })

# Call during application startup
configure_azure_openai()
```

## Rollback Procedure

If you need to rollback to API key authentication:

### Step 1: Restore API Key Configuration

```bash
# Set API key
export AZURE_OPENAI_API_KEY="your-api-key"

# Remove bearer token
unset AZURE_OPENAI_TOKEN

# Or comment out in .env file
# AZURE_OPENAI_TOKEN=...
```

### Step 2: Verify Rollback

```bash
# Test configuration
python -c "
from dev_agent.config.config_manager import ConfigManager
config = ConfigManager().get_azure_config()
print(f'Auth method: {\"Azure AD\" if config.bearer_token else \"API Key\"}')
"
```

### Step 3: Remove Custom Headers (Optional)

```bash
# Remove custom headers if no longer needed
unset AZURE_OPENAI_USER_SID
unset AZURE_OPENAI_CUSTOM_HEADERS
```

## Additional Resources

### Documentation
- [Azure OpenAI Configuration Guide](./azure-openai.md)
- [Azure AD Authentication Setup](../examples/azure-setup.md)
- [Security Best Practices](./security.md)

### Azure Documentation
- [Azure OpenAI Service Documentation](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/)
- [Azure AD Authentication](https://learn.microsoft.com/en-us/azure/active-directory/develop/)
- [Managed Identities](https://learn.microsoft.com/en-us/azure/active-directory/managed-identities-azure-resources/)
- [Azure Key Vault](https://learn.microsoft.com/en-us/azure/key-vault/)

### Support
- GitHub Issues: [Report issues or ask questions](https://github.com/your-org/dev-agent/issues)
- Documentation: [Full documentation](https://your-docs-site.com)

## Summary

Migrating from API key to Azure AD authentication provides:
- ✅ Enhanced security with short-lived tokens
- ✅ Centralized access control
- ✅ Better auditing and compliance
- ✅ Support for managed identities
- ✅ No code changes required

The migration process is straightforward:
1. Obtain Azure AD bearer token
2. Update environment variables
3. Test configuration
4. Remove API key (optional)

Both authentication methods can coexist, allowing for gradual migration and fallback scenarios.
