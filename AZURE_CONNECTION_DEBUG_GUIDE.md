# Azure OpenAI Connection Error Debugging Guide

## Error: "Azure OpenAI service error: connection error"

When you run `uv run dev-agent azure test` and get a connection error, follow this systematic debugging approach.

## Quick Diagnosis Steps

### 1. Check Environment Variables

First, verify all required environment variables are set:

```bash
# Check if variables are set
echo "Endpoint: $AZURE_OPENAI_ENDPOINT"
echo "API Key: ${AZURE_OPENAI_API_KEY:0:10}..."  # Shows first 10 chars only
echo "Deployment: $AZURE_OPENAI_DEPLOYMENT_NAME"
echo "Embedding: $AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
echo "API Version: $AZURE_OPENAI_API_VERSION"
```

**Required variables:**
- `AZURE_OPENAI_ENDPOINT` - Your Azure OpenAI endpoint URL
- `AZURE_OPENAI_API_KEY` or `AZURE_OPENAI_TOKEN` - Authentication credential
- `AZURE_OPENAI_DEPLOYMENT_NAME` - Your GPT-4 deployment name
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` - Your embedding deployment name

**Optional but recommended:**
- `AZURE_OPENAI_API_VERSION` - Defaults to "2024-02-15-preview"

### 2. Verify Endpoint Format

The endpoint must be in the correct format:

```bash
# ✅ CORRECT
https://your-resource.openai.azure.com/

# ❌ WRONG - Missing trailing slash
https://your-resource.openai.azure.com

# ❌ WRONG - Has extra path
https://your-resource.openai.azure.com/openai/

# ❌ WRONG - Wrong domain
https://your-resource.azure.com/
```

### 3. Test Network Connectivity

Test if you can reach the Azure OpenAI endpoint:

```bash
# Test basic connectivity
curl -I "$AZURE_OPENAI_ENDPOINT"

# Should return HTTP 401 (Unauthorized) - this is GOOD, means endpoint is reachable
# If you get connection refused, timeout, or DNS errors - network issue
```

### 4. Validate API Key

Check if your API key is valid:

```bash
# Test with curl (replace variables with actual values)
curl -X POST "$AZURE_OPENAI_ENDPOINT/openai/deployments/$AZURE_OPENAI_DEPLOYMENT_NAME/chat/completions?api-version=2024-02-15-preview" \
  -H "Content-Type: application/json" \
  -H "api-key: $AZURE_OPENAI_API_KEY" \
  -d '{
    "messages": [{"role": "user", "content": "test"}],
    "max_tokens": 10
  }'
```

**Expected responses:**
- ✅ Success: JSON response with completion
- ❌ 401: Invalid API key
- ❌ 404: Wrong deployment name or endpoint
- ❌ Connection error: Network/firewall issue

## Common Issues and Solutions

### Issue 1: Connection Timeout

**Symptoms:**
```
Azure OpenAI service error: connection error
```

**Possible Causes:**
1. **Firewall blocking outbound HTTPS** - Corporate firewall blocking Azure OpenAI
2. **VPN required** - Your organization requires VPN to access Azure resources
3. **Proxy configuration** - Need to configure HTTP proxy
4. **DNS resolution failure** - Can't resolve *.openai.azure.com

**Solutions:**

```bash
# Check if you can resolve the hostname
nslookup your-resource.openai.azure.com

# Check if port 443 is accessible
nc -zv your-resource.openai.azure.com 443

# If behind a proxy, set proxy environment variables
export HTTPS_PROXY=http://proxy.company.com:8080
export HTTP_PROXY=http://proxy.company.com:8080

# Then test again
uv run dev-agent azure test
```

### Issue 2: SSL/TLS Certificate Errors

**Symptoms:**
```
SSL: CERTIFICATE_VERIFY_FAILED
```

**Solutions:**

```bash
# Update CA certificates (macOS)
brew install ca-certificates

# Update CA certificates (Linux)
sudo apt-get update && sudo apt-get install ca-certificates

# If using corporate proxy with SSL inspection, you may need to:
# 1. Get your company's root CA certificate
# 2. Set SSL_CERT_FILE environment variable
export SSL_CERT_FILE=/path/to/company-ca-cert.pem
```

### Issue 3: Wrong Endpoint Format

**Symptoms:**
```
404 Not Found
Invalid URL
```

**Solution:**

```bash
# Verify endpoint format
echo $AZURE_OPENAI_ENDPOINT

# Should be: https://YOUR-RESOURCE-NAME.openai.azure.com/
# NOT: https://YOUR-RESOURCE-NAME.azure.com/

# Fix if needed
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
```

### Issue 4: Invalid Deployment Names

**Symptoms:**
```
DeploymentNotFound
The API deployment for this resource does not exist
```

**Solution:**

1. Go to Azure OpenAI Studio: https://oai.azure.com
2. Navigate to "Deployments" section
3. Copy the exact deployment name (case-sensitive!)
4. Update environment variables:

```bash
# Use the DEPLOYMENT NAME, not the model name
# ✅ CORRECT - deployment name
export AZURE_OPENAI_DEPLOYMENT_NAME="my-gpt4-deployment"

# ❌ WRONG - model name
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"
```

### Issue 5: API Key Expired or Rotated

**Symptoms:**
```
401 Unauthorized
Authentication failed
```

**Solution:**

1. Go to Azure Portal: https://portal.azure.com
2. Navigate to your Azure OpenAI resource
3. Go to "Keys and Endpoint" section
4. Regenerate key if needed
5. Update environment variable:

```bash
export AZURE_OPENAI_API_KEY="your-new-key-here"
```

### Issue 6: Regional Availability

**Symptoms:**
```
Resource not found
Deployment not available
```

**Possible Cause:**
Your Azure OpenAI resource might be in a region that doesn't support certain models.

**Solution:**

1. Check model availability by region: https://learn.microsoft.com/azure/ai-services/openai/concepts/models
2. Ensure your deployment uses a supported model in your region
3. Consider creating a new deployment in a supported region

## Detailed Debugging Commands

### Check Current Configuration

```bash
# Show current Azure OpenAI status
uv run dev-agent azure status

# Show environment variables
uv run dev-agent azure env

# Export configuration (without secrets)
uv run dev-agent azure export --output debug-config.json
cat debug-config.json
```

### Enable Debug Logging

```bash
# Run with debug logging
uv run dev-agent azure test --verbose

# Or set log level
export DEV_AGENT_LOG_LEVEL=DEBUG
uv run dev-agent azure test
```

### Test Individual Components

```python
# Create a test script: test_azure_connection.py
import asyncio
import os
from dev_agent.models.llm_config import AzureOpenAIConfig
from dev_agent.llm.azure_client import AzureOpenAIClient

async def test_connection():
    config = AzureOpenAIConfig(
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        embedding_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
    )
    
    print(f"Testing endpoint: {config.endpoint}")
    print(f"Testing deployment: {config.deployment_name}")
    
    client = AzureOpenAIClient(config)
    
    try:
        response = await client.generate_completion(
            prompt="Say hello",
            max_tokens=10
        )
        print(f"✅ Success: {response}")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_connection())
```

Run it:
```bash
uv run python test_azure_connection.py
```

## Azure AD Authentication (Bearer Token)

If using Azure AD authentication instead of API key:

### Required Environment Variables

```bash
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."  # Bearer token
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-ada-002"

# Optional: Custom headers for auditing
export AZURE_OPENAI_USER_SID="A123456"
export AZURE_OPENAI_CUSTOM_HEADERS='{"department": "engineering"}'
```

### Common Azure AD Issues

1. **Token Expired** - Bearer tokens expire after 1 hour
   ```bash
   # Get a new token using Azure CLI
   az account get-access-token --resource https://cognitiveservices.azure.com
   ```

2. **Wrong Scope** - Token must be for Cognitive Services
   ```bash
   # Correct scope
   az account get-access-token --resource https://cognitiveservices.azure.com
   
   # NOT this
   az account get-access-token --resource https://management.azure.com
   ```

## Network Diagnostics

### Check DNS Resolution

```bash
# Resolve Azure OpenAI endpoint
dig your-resource.openai.azure.com

# Or using nslookup
nslookup your-resource.openai.azure.com
```

### Check Firewall Rules

```bash
# Test HTTPS connectivity
curl -v https://your-resource.openai.azure.com/

# Test with timeout
curl --max-time 10 https://your-resource.openai.azure.com/

# Test through proxy
curl -x http://proxy:8080 https://your-resource.openai.azure.com/
```

### Check for Proxy Issues

```bash
# Check current proxy settings
env | grep -i proxy

# Unset proxy temporarily to test
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy

# Test again
uv run dev-agent azure test
```

## Configuration File Issues

### Check Config File Location

```bash
# Global config
cat ~/.dev_agent/dev_agent_config.json

# Project config (if in a project)
cat .dev_agent/config.json
```

### Reset Configuration

```bash
# Backup current config
cp ~/.dev_agent/dev_agent_config.json ~/.dev_agent/dev_agent_config.json.backup

# Remove config to force reconfiguration
rm ~/.dev_agent/dev_agent_config.json

# Reconfigure
uv run dev-agent azure configure
```

## Still Having Issues?

### Collect Diagnostic Information

```bash
# Create a diagnostic report
cat > azure_diagnostics.txt << EOF
=== Environment Variables ===
AZURE_OPENAI_ENDPOINT: $AZURE_OPENAI_ENDPOINT
AZURE_OPENAI_API_KEY: ${AZURE_OPENAI_API_KEY:0:10}... (truncated)
AZURE_OPENAI_DEPLOYMENT_NAME: $AZURE_OPENAI_DEPLOYMENT_NAME
AZURE_OPENAI_EMBEDDING_DEPLOYMENT: $AZURE_OPENAI_EMBEDDING_DEPLOYMENT
AZURE_OPENAI_API_VERSION: $AZURE_OPENAI_API_VERSION

=== Network Test ===
$(curl -I $AZURE_OPENAI_ENDPOINT 2>&1)

=== DNS Resolution ===
$(nslookup $(echo $AZURE_OPENAI_ENDPOINT | sed 's|https://||' | sed 's|/||') 2>&1)

=== Configuration Status ===
$(uv run dev-agent azure status 2>&1)

=== Python Version ===
$(python --version)

=== UV Version ===
$(uv --version)

=== Operating System ===
$(uname -a)
EOF

cat azure_diagnostics.txt
```

### Get Help

1. **Check Azure Service Health**: https://status.azure.com
2. **Review Azure OpenAI Documentation**: https://learn.microsoft.com/azure/ai-services/openai/
3. **Check dev-agent logs**: `.dev_agent/logs/dev_agent.log`
4. **Open GitHub Issue**: Include the diagnostic report (remove sensitive data!)

## Quick Fix Checklist

- [ ] Environment variables are set correctly
- [ ] Endpoint has trailing slash: `https://resource.openai.azure.com/`
- [ ] API key is valid and not expired
- [ ] Deployment names match exactly (case-sensitive)
- [ ] Network connectivity to Azure OpenAI endpoint works
- [ ] No firewall blocking outbound HTTPS
- [ ] Proxy settings configured if needed
- [ ] SSL certificates are up to date
- [ ] Using correct API version (2024-02-15-preview or later)
- [ ] Azure OpenAI resource is in a supported region

## Example: Complete Working Configuration

```bash
# Set all required environment variables
export AZURE_OPENAI_ENDPOINT="https://my-openai-resource.openai.azure.com/"
export AZURE_OPENAI_API_KEY="abc123def456..."
export AZURE_OPENAI_API_VERSION="2024-02-15-preview"
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4-deployment"
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-ada-002"

# Test the connection
uv run dev-agent azure test

# If successful, you should see:
# ✓ Chat completion test successful
# ✓ Embeddings test successful
# ✅ All tests passed successfully!
```
