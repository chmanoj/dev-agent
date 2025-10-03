# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with Azure OpenAI integration in dev-agent.

## Quick Diagnostics

Run the built-in diagnostic tool to check your configuration:

```bash
# Test Azure OpenAI connection
uv run dev-agent azure test

# Run with verbose output
uv run dev-agent azure test --verbose
```

## Authentication Issues

### Error: "Authentication failed" or "Invalid API key"

**Symptoms**:
```
Error: LLMAuthenticationError: Invalid Azure OpenAI credentials
Failed to authenticate with Azure OpenAI API
```

**Causes**:
- Incorrect API key
- API key expired or regenerated
- Wrong endpoint URL
- API key not set in environment

**Solutions**:

1. **Verify API key**:
   ```bash
   # Check if API key is set
   echo $AZURE_OPENAI_API_KEY
   
   # Should output your key (not empty)
   ```

2. **Get fresh API key from Azure Portal**:
   - Navigate to your Azure OpenAI resource
   - Click "Keys and Endpoint"
   - Copy KEY 1 or KEY 2
   - Update your environment variable

3. **Check endpoint URL**:
   ```bash
   # Verify endpoint format
   echo $AZURE_OPENAI_ENDPOINT
   
   # Should be: https://your-resource.openai.azure.com/
   # Must end with /
   ```

4. **Reconfigure using CLI**:
   ```bash
   uv run dev-agent azure configure
   ```

5. **Test connection**:
   ```bash
   uv run dev-agent azure test
   ```

### Error: "Unauthorized" or "Access denied"

**Symptoms**:
```
Error: 401 Unauthorized
Access to Azure OpenAI resource denied
```

**Causes**:
- API key doesn't have permissions
- Resource access restrictions
- Firewall blocking requests

**Solutions**:

1. **Check resource permissions**:
   - Verify you have "Cognitive Services OpenAI User" role
   - Check Azure RBAC settings

2. **Review firewall rules**:
   - Check if your IP is allowed
   - Add your IP to allowed list in Azure Portal

3. **Try different API key**:
   - Use KEY 2 if KEY 1 fails
   - Regenerate keys if needed

## Deployment Issues

### Error: "Deployment not found" or "Model not found"

**Symptoms**:
```
Error: The API deployment for this resource does not exist
Deployment 'gpt-4' not found
```

**Causes**:
- Deployment name mismatch
- Deployment not created
- Deployment in wrong region
- Deployment name is case-sensitive

**Solutions**:

1. **List available deployments**:
   ```bash
   # Using Azure CLI
   az cognitiveservices account deployment list \
     --name your-resource-name \
     --resource-group your-resource-group \
     --output table
   ```

2. **Check deployment names in Azure Portal**:
   - Go to Azure OpenAI Studio
   - Click "Deployments"
   - Note exact deployment names (case-sensitive)

3. **Update environment variables**:
   ```bash
   # Use exact deployment names
   export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"
   export AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-ada-002"
   ```

4. **Create missing deployments**:
   ```bash
   # Create GPT-4 deployment
   az cognitiveservices account deployment create \
     --name your-resource-name \
     --resource-group your-resource-group \
     --deployment-name gpt-4 \
     --model-name gpt-4 \
     --model-version "0613" \
     --model-format OpenAI \
     --sku-capacity 10 \
     --sku-name "Standard"
   ```

### Error: "Deployment is not ready"

**Symptoms**:
```
Error: Deployment is in 'Creating' state
Please wait for deployment to complete
```

**Causes**:
- Deployment still being created
- Deployment failed

**Solutions**:

1. **Wait for deployment to complete** (usually 1-2 minutes)

2. **Check deployment status**:
   ```bash
   az cognitiveservices account deployment show \
     --name your-resource-name \
     --resource-group your-resource-group \
     --deployment-name gpt-4 \
     --query "properties.provisioningState"
   ```

3. **If stuck, delete and recreate**:
   ```bash
   # Delete failed deployment
   az cognitiveservices account deployment delete \
     --name your-resource-name \
     --resource-group your-resource-group \
     --deployment-name gpt-4
   
   # Create new deployment
   # (see command above)
   ```

## Rate Limiting Issues

### Error: "Rate limit exceeded" or "429 Too Many Requests"

**Symptoms**:
```
Error: LLMRateLimitError: Azure OpenAI rate limit exceeded
Rate limit: 10,000 tokens per minute
Retry after: 30 seconds
```

**Causes**:
- Too many concurrent requests
- Token rate limit exceeded
- Request rate limit exceeded

**Solutions**:

1. **Wait and retry** (dev-agent does this automatically):
   - Automatic exponential backoff
   - Retries up to 3 times
   - No action needed

2. **Increase rate limits in Azure Portal**:
   - Go to Azure OpenAI Studio
   - Click "Deployments"
   - Edit deployment
   - Increase "Tokens per Minute Rate Limit"

3. **Reduce concurrent requests**:
   ```python
   # Configure batch size
   config = AzureOpenAIConfig(
       batch_size=8,  # Reduce from default 16
       # ... other config
   )
   ```

4. **Upgrade to higher tier**:
   - Consider Standard tier for higher limits
   - Check Azure OpenAI pricing tiers

### Error: "Quota exceeded"

**Symptoms**:
```
Error: Quota exceeded for this subscription
Monthly quota: 1,000,000 tokens
```

**Causes**:
- Monthly quota limit reached
- Subscription limits

**Solutions**:

1. **Check quota usage**:
   - View in Azure Portal under "Quotas"
   - Monitor usage patterns

2. **Request quota increase**:
   - Submit quota increase request in Azure Portal
   - Provide justification for increase

3. **Optimize token usage**:
   - See [Cost Management Guide](../usage/cost-management.md)
   - Enable embedding cache
   - Reduce context size

## Timeout Issues

### Error: "Request timeout" or "Connection timeout"

**Symptoms**:
```
Error: LLMTimeoutError: Request to Azure OpenAI timed out
Timeout: 60 seconds
```

**Causes**:
- Slow network connection
- Large request taking too long
- Azure OpenAI service issues

**Solutions**:

1. **Increase timeout**:
   ```bash
   export AZURE_OPENAI_TIMEOUT="120"  # Increase to 120 seconds
   ```

2. **Check network connection**:
   ```bash
   # Test connectivity
   curl -I https://your-resource.openai.azure.com/
   ```

3. **Reduce request size**:
   ```python
   # Reduce max tokens
   config = AzureOpenAIConfig(
       max_tokens=2000,  # Reduce from 4000
       # ... other config
   )
   ```

4. **Check Azure service status**:
   - Visit [Azure Status](https://status.azure.com/)
   - Check for service incidents

5. **Try different region**:
   - Create resource in different Azure region
   - Update endpoint URL

## Token Limit Issues

### Error: "Token limit exceeded" or "Context length exceeded"

**Symptoms**:
```
Error: LLMTokenLimitError: Token limit exceeded
Prompt tokens: 9,500
Model limit: 8,192
```

**Causes**:
- Prompt too long for model
- Too much context included
- Large code examples

**Solutions**:

1. **Reduce context size**:
   ```python
   # Configure context limits
   config = {
       "max_context_chunks": 3,  # Reduce from 5
       "max_context_tokens": 2000,  # Reduce from 4000
   }
   ```

2. **Use model with larger context**:
   ```bash
   # Use GPT-4 Turbo (128K context)
   export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4-turbo"
   ```

3. **Optimize prompts**:
   - Remove unnecessary context
   - Summarize large code blocks
   - Use more focused examples

4. **Split into smaller requests**:
   - Break large tasks into smaller pieces
   - Process incrementally

## Connection Issues

### Error: "Connection refused" or "Cannot connect"

**Symptoms**:
```
Error: Failed to connect to Azure OpenAI
Connection refused: https://your-resource.openai.azure.com/
```

**Causes**:
- Network connectivity issues
- Firewall blocking connection
- VPN/proxy issues
- Wrong endpoint URL

**Solutions**:

1. **Test basic connectivity**:
   ```bash
   # Test DNS resolution
   nslookup your-resource.openai.azure.com
   
   # Test HTTPS connection
   curl -I https://your-resource.openai.azure.com/
   ```

2. **Check firewall settings**:
   - Allow outbound HTTPS (port 443)
   - Whitelist Azure OpenAI endpoints

3. **Configure proxy** (if needed):
   ```bash
   export HTTPS_PROXY="http://proxy.example.com:8080"
   ```

4. **Verify endpoint URL**:
   ```bash
   # Should match your resource name
   echo $AZURE_OPENAI_ENDPOINT
   ```

### Error: "SSL certificate verification failed"

**Symptoms**:
```
Error: SSL: CERTIFICATE_VERIFY_FAILED
Unable to verify SSL certificate
```

**Causes**:
- Corporate proxy with SSL inspection
- Outdated CA certificates
- Network security tools

**Solutions**:

1. **Update CA certificates**:
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install ca-certificates
   
   # macOS
   brew install ca-certificates
   ```

2. **Configure SSL verification** (not recommended for production):
   ```python
   # Only for development/testing
   import ssl
   ssl._create_default_https_context = ssl._create_unverified_context
   ```

3. **Use corporate CA bundle**:
   ```bash
   export REQUESTS_CA_BUNDLE=/path/to/corporate-ca-bundle.crt
   ```

## Embedding Cache Issues

### Error: "Cache corrupted" or "Invalid cache entry"

**Symptoms**:
```
Error: Failed to load embedding from cache
Cache entry corrupted or invalid format
```

**Causes**:
- Corrupted cache files
- Disk full
- Permission issues

**Solutions**:

1. **Clear cache**:
   ```bash
   # Remove cache directory
   rm -rf .dev_agent/embedding_cache/
   
   # Rebuild cache
   uv run dev-agent init /path/to/project
   ```

2. **Check disk space**:
   ```bash
   df -h .dev_agent/
   ```

3. **Check permissions**:
   ```bash
   ls -la .dev_agent/embedding_cache/
   chmod -R u+rw .dev_agent/embedding_cache/
   ```

### Cache not being used

**Symptoms**:
- Embeddings regenerated every time
- High costs for repeated operations

**Diagnosis**:
```bash
# Check cache stats
uv run dev-agent cache-stats

# Should show cache hits
```

**Solutions**:

1. **Verify cache is enabled**:
   ```python
   # Check configuration
   config = load_config()
   print(config.use_embedding_cache)  # Should be True
   ```

2. **Check for code changes**:
   - Cache invalidates when code changes
   - This is expected behavior

3. **Verify model name consistency**:
   - Cache is model-specific
   - Changing models invalidates cache

## Configuration Issues

### Error: "Configuration not found" or "Invalid configuration"

**Symptoms**:
```
Error: Azure OpenAI configuration not found
Please run: dev-agent azure configure
```

**Causes**:
- Configuration not set up
- Environment variables not set
- Config file missing or corrupted

**Solutions**:

1. **Run configuration wizard**:
   ```bash
   uv run dev-agent azure configure
   ```

2. **Set environment variables**:
   ```bash
   export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
   export AZURE_OPENAI_API_KEY="your-api-key"
   export AZURE_OPENAI_API_VERSION="2024-02-15-preview"
   export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"
   export AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-ada-002"
   ```

3. **Check config file**:
   ```bash
   # View config
   cat ~/.dev_agent/dev_agent_config.json
   
   # Validate JSON format
   python -m json.tool ~/.dev_agent/dev_agent_config.json
   ```

4. **Reset configuration**:
   ```bash
   # Backup old config
   mv ~/.dev_agent/dev_agent_config.json ~/.dev_agent/dev_agent_config.json.bak
   
   # Reconfigure
   uv run dev-agent azure configure
   ```

## Performance Issues

### Slow embedding generation

**Symptoms**:
- Indexing takes very long
- Embedding generation is slow

**Solutions**:

1. **Check batch size**:
   ```bash
   # Increase batch size
   export AZURE_OPENAI_BATCH_SIZE="16"  # Default, optimal
   ```

2. **Enable concurrent processing**:
   ```python
   # Configure concurrent batches
   config = AzureOpenAIConfig(
       max_concurrent_batches=3,  # Process 3 batches in parallel
       # ... other config
   )
   ```

3. **Check network speed**:
   ```bash
   # Test download speed
   curl -o /dev/null https://your-resource.openai.azure.com/
   ```

4. **Use cache for repeated operations**:
   - Cache is automatic
   - Verify cache is working

### Slow completion generation

**Symptoms**:
- Code generation takes very long
- Specifications take minutes to generate

**Solutions**:

1. **Reduce max tokens**:
   ```bash
   export AZURE_OPENAI_MAX_TOKENS="2000"  # Reduce from 4000
   ```

2. **Reduce context size**:
   - Include fewer code examples
   - Summarize large contexts

3. **Use streaming**:
   ```python
   # Stream responses for faster perceived performance
   async for chunk in client.generate_streaming(prompt):
       print(chunk, end="", flush=True)
   ```

4. **Check Azure region**:
   - Use region closer to you
   - Check region performance

## Error Code Reference

| Error Code | Meaning | Solution |
|------------|---------|----------|
| 401 | Unauthorized | Check API key and permissions |
| 403 | Forbidden | Check firewall rules and access |
| 404 | Not Found | Verify deployment names |
| 429 | Rate Limit | Wait and retry, increase limits |
| 500 | Server Error | Check Azure service status |
| 503 | Service Unavailable | Retry later, check status |
| Timeout | Request timeout | Increase timeout, reduce size |

## Diagnostic Commands

### Check Configuration

```bash
# Test Azure OpenAI connection
uv run dev-agent azure test

# View current configuration
uv run dev-agent azure config show

# Validate configuration
uv run dev-agent azure config validate
```

### Check Cache

```bash
# View cache statistics
uv run dev-agent cache-stats

# Clear cache
uv run dev-agent cache-clear

# Rebuild cache
uv run dev-agent cache-rebuild
```

### Check Logs

```bash
# View recent logs
tail -f .dev_agent/logs/dev_agent.log

# Search for errors
grep ERROR .dev_agent/logs/dev_agent.log

# View API call logs
grep "Azure OpenAI API" .dev_agent/logs/dev_agent.log
```

## Getting Help

### Enable Debug Logging

```bash
# Set debug log level
export DEV_AGENT_LOG_LEVEL="DEBUG"

# Run with verbose output
uv run dev-agent --verbose init /path/to/project
```

### Collect Diagnostic Information

```bash
# Generate diagnostic report
uv run dev-agent diagnose > diagnostic_report.txt

# Include:
# - Configuration (API keys redacted)
# - Recent logs
# - System information
# - Azure OpenAI connectivity test
```

### Report Issues

When reporting issues, include:

1. **Error message** (full stack trace)
2. **Configuration** (redact API keys!)
3. **Steps to reproduce**
4. **Expected vs actual behavior**
5. **Environment information**:
   ```bash
   python --version
   uv --version
   uv run dev-agent --version
   ```

### Community Support

- **GitHub Issues**: [github.com/your-repo/issues](https://github.com/your-repo/issues)
- **Documentation**: [docs.dev-agent.dev](https://docs.dev-agent.dev)
- **Azure Support**: [Azure Support Portal](https://portal.azure.com/#blade/Microsoft_Azure_Support/HelpAndSupportBlade)

## Additional Resources

- [Azure OpenAI Setup Guide](azure-openai.md)
- [Cost Management Guide](../usage/cost-management.md)
- [Azure OpenAI Documentation](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/)
- [Azure Service Health](https://status.azure.com/)
- [Azure OpenAI Limits](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/quotas-limits)

## Preventive Measures

To avoid common issues:

1. **Set up monitoring**: Track API usage and errors
2. **Configure alerts**: Get notified of issues early
3. **Test regularly**: Run `dev-agent azure test` periodically
4. **Keep updated**: Update dev-agent and dependencies
5. **Review logs**: Check logs for warnings
6. **Backup config**: Keep configuration backed up
7. **Document setup**: Document your specific configuration
8. **Test changes**: Test configuration changes in dev first
9. **Monitor costs**: Track spending to avoid surprises
10. **Stay informed**: Subscribe to Azure service updates
