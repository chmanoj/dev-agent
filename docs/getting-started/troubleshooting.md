# Troubleshooting Guide

This guide helps you resolve common issues when using dev-agent.

## Quick Diagnostics

Run these commands to diagnose issues:

```bash
# Check configuration status
dev-agent setup --status

# Validate environment
dev-agent validate

# View detailed logs
cat .dev_agent/logs/dev_agent.log

# Test Azure OpenAI connection
dev-agent validate --test-connection
```

## Common Issues

### Installation Issues

#### Issue: `command not found: dev-agent`

**Symptoms:**
```bash
$ dev-agent
zsh: command not found: dev-agent
```

**Solutions:**

1. **Verify installation:**
   ```bash
   pip list | grep dev-agent
   # or
   uv pip list | grep dev-agent
   ```

2. **Reinstall:**
   ```bash
   uv pip install --force-reinstall dev-agent
   ```

3. **Check PATH:**
   ```bash
   echo $PATH
   # Ensure pip/uv bin directory is in PATH
   ```

4. **Use full path:**
   ```bash
   python -m dev_agent.cli.main --help
   ```

#### Issue: `ModuleNotFoundError: No module named 'dev_agent'`

**Symptoms:**
```
ModuleNotFoundError: No module named 'dev_agent'
```

**Solutions:**

1. **Activate virtual environment:**
   ```bash
   source .venv/bin/activate  # Linux/macOS
   .venv\Scripts\activate     # Windows
   ```

2. **Install in correct environment:**
   ```bash
   which python  # Verify correct Python
   pip install dev-agent
   ```

3. **Check Python version:**
   ```bash
   python --version  # Must be 3.10+
   ```

#### Issue: Dependency conflicts

**Symptoms:**
```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed.
```

**Solutions:**

1. **Use uv (recommended):**
   ```bash
   pip install uv
   uv pip install dev-agent
   ```

2. **Create fresh virtual environment:**
   ```bash
   python -m venv .venv-fresh
   source .venv-fresh/bin/activate
   pip install dev-agent
   ```

3. **Update pip:**
   ```bash
   pip install --upgrade pip setuptools wheel
   ```

### Azure OpenAI Configuration Issues

#### Issue: `AuthenticationError: Invalid API key`

**Symptoms:**
```
❌ Error: Azure OpenAI authentication failed

AuthenticationError: Invalid API key provided
```

**Solutions:**

1. **Verify API key:**
   ```bash
   # Check environment variable
   echo $AZURE_OPENAI_API_KEY
   
   # Should be 32 characters
   ```

2. **Check Azure Portal:**
   - Navigate to your Azure OpenAI resource
   - Go to "Keys and Endpoint"
   - Copy the correct key (Key 1 or Key 2)

3. **Re-run setup:**
   ```bash
   dev-agent setup
   # Enter correct API key when prompted
   ```

4. **Use environment variables:**
   ```bash
   export AZURE_OPENAI_API_KEY="your-correct-key"
   dev-agent validate --test-connection
   ```

#### Issue: `ResourceNotFoundError: Deployment not found`

**Symptoms:**
```
❌ Error: Deployment 'gpt-4' not found

ResourceNotFoundError: The API deployment for this resource does not exist
```

**Solutions:**

1. **Check deployment names:**
   ```bash
   # In Azure Portal:
   # Azure OpenAI → Model deployments
   # Note exact deployment names
   ```

2. **Update configuration:**
   ```bash
   dev-agent config set azure.deployment_name "your-actual-deployment-name"
   dev-agent config set azure.embedding_deployment "your-embedding-deployment"
   ```

3. **Common deployment names:**
   - `gpt-4` or `gpt-4-32k`
   - `gpt-35-turbo` (note: 35, not 3.5)
   - `text-embedding-ada-002`

4. **Verify in config:**
   ```bash
   dev-agent config show
   ```

#### Issue: `InvalidRequestError: Invalid endpoint`

**Symptoms:**
```
❌ Error: Invalid Azure OpenAI endpoint

InvalidRequestError: Invalid URL
```

**Solutions:**

1. **Check endpoint format:**
   ```bash
   # Correct format:
   https://your-resource-name.openai.azure.com/
   
   # NOT:
   https://your-resource-name.openai.azure.com/openai/deployments/...
   ```

2. **Get endpoint from Azure:**
   - Azure Portal → Your OpenAI resource
   - "Keys and Endpoint" section
   - Copy "Endpoint" value

3. **Update configuration:**
   ```bash
   export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
   dev-agent validate --test-connection
   ```

#### Issue: `RateLimitError: Rate limit exceeded`

**Symptoms:**
```
❌ Error: Rate limit exceeded

RateLimitError: Requests to the API are currently rate limited
```

**Solutions:**

1. **Wait and retry:**
   - Azure OpenAI has rate limits per minute
   - Wait 60 seconds and try again

2. **Check quota:**
   - Azure Portal → Your OpenAI resource
   - "Quotas" section
   - Verify you haven't exceeded limits

3. **Reduce batch size:**
   ```bash
   dev-agent config set azure.batch_size 8  # Default is 16
   ```

4. **Request quota increase:**
   - Azure Portal → Support → New support request
   - Request higher TPM (tokens per minute)

### Indexing Issues

#### Issue: Indexing fails on large codebase

**Symptoms:**
```
❌ Error: Indexing failed after 1000 files

MemoryError: Unable to allocate memory
```

**Solutions:**

1. **Index incrementally:**
   ```bash
   # Index specific directories
   dev-agent init --include "src/*"
   dev-agent reindex --include "tests/*"
   ```

2. **Exclude unnecessary files:**
   ```bash
   dev-agent init --exclude "tests/*,docs/*,build/*,node_modules/*"
   ```

3. **Increase memory:**
   ```bash
   # Set environment variable
   export PYTHONMALLOC=malloc
   
   # Or use system with more RAM
   ```

4. **Use file filters:**
   ```bash
   # Only Python files
   dev-agent init --pattern "*.py"
   
   # Exclude large files
   dev-agent init --max-file-size 1000000  # 1MB
   ```

#### Issue: Tree-sitter parsing errors

**Symptoms:**
```
⚠ Warning: Failed to parse src/legacy/old_code.py
SyntaxError: invalid syntax
```

**Solutions:**

1. **Skip problematic files:**
   ```bash
   dev-agent init --skip-errors
   ```

2. **Fix syntax errors:**
   ```bash
   # Run linter to find issues
   ruff check src/legacy/old_code.py
   
   # Fix syntax errors
   # Then re-index
   dev-agent reindex
   ```

3. **Exclude legacy code:**
   ```bash
   dev-agent init --exclude "src/legacy/*"
   ```

4. **Update tree-sitter:**
   ```bash
   pip install --upgrade tree-sitter tree-sitter-python
   ```

#### Issue: Embeddings generation slow

**Symptoms:**
```
📊 Indexing Progress: 10% (2 minutes elapsed, 18 minutes remaining)
```

**Solutions:**

1. **Increase batch size:**
   ```bash
   dev-agent config set azure.batch_size 32  # Default is 16
   ```

2. **Use caching:**
   ```bash
   dev-agent config set preferences.cache_embeddings true
   ```

3. **Parallel processing:**
   ```bash
   dev-agent init --parallel 4  # Use 4 workers
   ```

4. **Check network:**
   ```bash
   # Test connection speed
   curl -w "@-" -o /dev/null -s https://your-resource.openai.azure.com/
   ```

### Generation Issues

#### Issue: Generated code doesn't match existing style

**Symptoms:**
- Generated code uses different naming conventions
- Type hints missing or inconsistent
- Different error handling approach

**Solutions:**

1. **Re-index codebase:**
   ```bash
   dev-agent reindex --full
   ```

2. **Verify patterns detected:**
   ```bash
   dev-agent analyze patterns
   ```

3. **Provide more context:**
   ```bash
   # Include more example files
   dev-agent spec create "feature" --context "src/services/*.py"
   ```

4. **Adjust temperature:**
   ```bash
   # Lower temperature for more consistent output
   dev-agent config set azure.temperature 0.3
   ```

#### Issue: Specifications too generic

**Symptoms:**
- Specifications don't reference existing code
- Missing project-specific details
- Generic examples instead of codebase patterns

**Solutions:**

1. **Ensure indexing completed:**
   ```bash
   dev-agent status
   # Should show "Indexing: Complete"
   ```

2. **Provide detailed description:**
   ```bash
   dev-agent spec create "Add user authentication with JWT tokens, following existing FastAPI patterns in src/api/"
   ```

3. **Reference existing code:**
   ```bash
   dev-agent spec create "feature" --similar-to "src/services/user_service.py"
   ```

4. **Increase context window:**
   ```bash
   dev-agent config set azure.max_tokens 8000
   ```

#### Issue: Code generation timeout

**Symptoms:**
```
❌ Error: Request timeout

APITimeoutError: Request timed out after 60 seconds
```

**Solutions:**

1. **Increase timeout:**
   ```bash
   dev-agent config set azure.timeout 120  # 2 minutes
   ```

2. **Break into smaller tasks:**
   ```bash
   # Instead of "implement entire feature"
   # Use: "implement user model"
   #      "implement user repository"
   #      "implement user service"
   ```

3. **Check Azure status:**
   - Visit Azure Status page
   - Check for service incidents

4. **Retry with backoff:**
   ```bash
   dev-agent config set azure.max_retries 5
   ```

### State Management Issues

#### Issue: State file corrupted

**Symptoms:**
```
❌ Error: Failed to load project state

JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**Solutions:**

1. **Restore from backup:**
   ```bash
   cp .dev_agent/state.json.backup .dev_agent/state.json
   ```

2. **Reset state:**
   ```bash
   dev-agent reset --keep-documents
   ```

3. **Re-initialize:**
   ```bash
   # Backup documents first
   cp -r .dev_agent/documents /tmp/dev_agent_docs_backup
   
   # Re-initialize
   dev-agent init
   
   # Restore documents
   cp -r /tmp/dev_agent_docs_backup/* .dev_agent/documents/
   ```

#### Issue: Phase stuck or won't progress

**Symptoms:**
```
Current Phase: Specification
Status: In Progress (stuck for 2 days)
```

**Solutions:**

1. **Check phase status:**
   ```bash
   dev-agent status --detailed
   ```

2. **Force phase completion:**
   ```bash
   dev-agent phase complete specification
   ```

3. **Reset phase:**
   ```bash
   dev-agent phase reset specification
   dev-agent phase run specification
   ```

4. **Skip to next phase:**
   ```bash
   dev-agent phase skip specification
   ```

### Cost and Budget Issues

#### Issue: Unexpected high costs

**Symptoms:**
```
⚠ Warning: Cost exceeded budget threshold
Current: $15.50, Budget: $10.00
```

**Solutions:**

1. **Review cost report:**
   ```bash
   dev-agent cost report --detailed
   ```

2. **Identify expensive operations:**
   ```bash
   dev-agent cost report --by-operation
   ```

3. **Set budget limits:**
   ```bash
   dev-agent config set preferences.budget_threshold 20.0
   dev-agent config set preferences.cost_warnings_enabled true
   ```

4. **Optimize usage:**
   ```bash
   # Use caching
   dev-agent config set preferences.cache_embeddings true
   
   # Reduce batch size
   dev-agent config set azure.batch_size 8
   
   # Lower max tokens
   dev-agent config set azure.max_tokens 2000
   ```

5. **Estimate before operations:**
   ```bash
   dev-agent cost estimate --operation "index"
   dev-agent cost estimate --operation "spec"
   ```

### Performance Issues

#### Issue: CLI commands slow to respond

**Symptoms:**
- Commands take >5 seconds to start
- Frequent pauses during execution

**Solutions:**

1. **Check system resources:**
   ```bash
   # CPU and memory usage
   top
   
   # Disk space
   df -h
   ```

2. **Clear cache:**
   ```bash
   dev-agent cache clear
   ```

3. **Optimize vector database:**
   ```bash
   dev-agent optimize --vector-db
   ```

4. **Reduce index size:**
   ```bash
   # Re-index with filters
   dev-agent reindex --exclude "tests/*,docs/*"
   ```

#### Issue: Vector search returns irrelevant results

**Symptoms:**
- Search results don't match query
- Missing obvious matches

**Solutions:**

1. **Re-generate embeddings:**
   ```bash
   dev-agent reindex --regenerate-embeddings
   ```

2. **Adjust search parameters:**
   ```bash
   dev-agent config set search.top_k 10  # Return more results
   dev-agent config set search.threshold 0.7  # Adjust similarity threshold
   ```

3. **Use more specific queries:**
   ```bash
   # Instead of: "authentication"
   # Use: "JWT token authentication with FastAPI"
   ```

4. **Verify indexing:**
   ```bash
   dev-agent status
   # Check: "Files indexed" count
   ```

## Error Messages Reference

### Common Error Codes

| Error Code | Meaning | Solution |
|------------|---------|----------|
| `AUTH_001` | Invalid API key | Check Azure OpenAI API key |
| `AUTH_002` | Expired API key | Rotate API key in Azure Portal |
| `DEPLOY_001` | Deployment not found | Verify deployment names |
| `RATE_001` | Rate limit exceeded | Wait and retry, or request quota increase |
| `TIMEOUT_001` | Request timeout | Increase timeout or break into smaller tasks |
| `INDEX_001` | Indexing failed | Check file permissions and syntax |
| `STATE_001` | State file corrupted | Restore from backup or reset |
| `COST_001` | Budget exceeded | Review costs and adjust budget |

### Getting Detailed Error Information

```bash
# Enable verbose logging
dev-agent --verbose <command>

# View full error trace
dev-agent --debug <command>

# Save logs to file
dev-agent <command> 2>&1 | tee dev_agent_error.log
```

## Platform-Specific Issues

### macOS

#### Issue: SSL certificate errors

**Solution:**
```bash
# Install certificates
/Applications/Python\ 3.11/Install\ Certificates.command

# Or use certifi
pip install --upgrade certifi
```

#### Issue: Permission denied errors

**Solution:**
```bash
# Fix permissions
chmod +x $(which dev-agent)

# Or use sudo (not recommended)
sudo dev-agent <command>
```

### Linux

#### Issue: `libfaiss.so` not found

**Solution:**
```bash
# Install FAISS dependencies
sudo apt-get install libopenblas-dev

# Or reinstall FAISS
pip install --force-reinstall faiss-cpu
```

### Windows

#### Issue: Path too long errors

**Solution:**
```powershell
# Enable long paths
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force

# Or use shorter project paths
```

#### Issue: Encoding errors

**Solution:**
```powershell
# Set UTF-8 encoding
$env:PYTHONIOENCODING="utf-8"

# Or in PowerShell profile
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

## Getting Help

### Self-Service Resources

1. **Documentation:**
   - [Installation Guide](../installation.md)
   - [Configuration Guide](../configuration/azure-openai.md)
   - [API Reference](../api/)

2. **Examples:**
   - Check `examples/` directory
   - Review example projects

3. **Logs:**
   ```bash
   # View recent logs
   tail -f .dev_agent/logs/dev_agent.log
   
   # Search logs
   grep "ERROR" .dev_agent/logs/dev_agent.log
   ```

### Community Support

1. **GitHub Issues:**
   - Search existing issues
   - Open new issue with details
   - Include error logs and config (redact API keys!)

2. **Discussions:**
   - Ask questions in GitHub Discussions
   - Share solutions and tips

### Reporting Bugs

When reporting bugs, include:

```bash
# System information
dev-agent --version
python --version
uname -a  # or: systeminfo (Windows)

# Configuration (redact API keys!)
dev-agent config show

# Error logs
cat .dev_agent/logs/dev_agent.log

# Steps to reproduce
# 1. Run: dev-agent init
# 2. Error occurs: ...
```

### Feature Requests

Submit feature requests with:
- Clear description of desired functionality
- Use case and benefits
- Example usage

## Preventive Measures

### Regular Maintenance

```bash
# Weekly
dev-agent reindex --incremental
dev-agent cache clean --old

# Monthly
dev-agent optimize --all
dev-agent cost report --export monthly_report.json

# After major changes
dev-agent reindex --full
dev-agent validate --comprehensive
```

### Best Practices

1. **Keep dependencies updated:**
   ```bash
   pip install --upgrade dev-agent
   ```

2. **Monitor costs:**
   ```bash
   dev-agent cost report --weekly
   ```

3. **Backup state:**
   ```bash
   cp .dev_agent/state.json .dev_agent/state.json.backup
   ```

4. **Use version control:**
   ```bash
   git add .dev_agent/documents/
   git commit -m "docs: update specifications"
   ```

5. **Test in development:**
   ```bash
   # Test with small subset first
   dev-agent init --include "src/core/*"
   ```

## Still Having Issues?

If you're still experiencing problems:

1. **Run diagnostics:**
   ```bash
   dev-agent diagnose --full
   ```

2. **Check system requirements:**
   - Python 3.10+
   - 4GB+ RAM
   - Stable internet connection
   - Valid Azure OpenAI subscription

3. **Try minimal setup:**
   ```bash
   # Fresh virtual environment
   python -m venv .venv-test
   source .venv-test/bin/activate
   pip install dev-agent
   dev-agent setup
   ```

4. **Contact support:**
   - GitHub Issues: [github.com/your-org/dev-agent/issues](https://github.com/your-org/dev-agent/issues)
   - Email: support@your-org.com
   - Documentation: [docs.your-org.com](https://docs.your-org.com)
