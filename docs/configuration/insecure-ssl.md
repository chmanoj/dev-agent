# Insecure SSL Mode (Development/Testing Only)

## ⚠️ Security Warning

**Disabling SSL certificate verification is INSECURE and should ONLY be used for development and testing purposes. NEVER use this in production environments.**

When SSL verification is disabled:
- Your connection is vulnerable to man-in-the-middle (MITM) attacks
- Attackers can intercept and modify your API requests and responses
- Your API keys and data can be stolen
- You have no guarantee you're connecting to the real Azure OpenAI service

## When to Use Insecure Mode

Use insecure mode ONLY in these scenarios:

1. **Local Development** - Testing on a development machine with certificate issues
2. **Corporate Networks** - Temporary workaround while waiting for proper CA certificates
3. **Debugging** - Isolating SSL certificate issues from other connection problems
4. **CI/CD Testing** - Automated tests in controlled environments (not recommended)

## Proper Solution

Instead of using insecure mode, you should fix SSL certificate issues properly:

1. **macOS**: Run `/Applications/Python 3.*/Install Certificates.command`
2. **All Platforms**: Update certifi: `uv pip install --upgrade certifi`
3. **Corporate Networks**: Add your company's root CA certificate
4. **See**: `FIX_SSL_CERTIFICATE_ERROR.md` for detailed solutions

## Usage

### Method 1: Global Flag (Affects All Commands)

```bash
# Disable SSL verification for all operations
uv run dev-agent --insecure azure test
uv run dev-agent --insecure init
uv run dev-agent --insecure resume
```

### Method 2: Command-Specific Flag

```bash
# Only disable SSL for the test command
uv run dev-agent azure test --insecure
```

### Method 3: Environment Variable

```bash
# Set environment variable (persists for session)
export AZURE_OPENAI_VERIFY_SSL=false

# Run commands normally
uv run dev-agent azure test
uv run dev-agent init
```

### Method 4: Configuration File

Add to your configuration file (`~/.dev_agent/dev_agent_config.json`):

```json
{
  "azure_openai": {
    "endpoint": "https://your-resource.openai.azure.com/",
    "api_key": "your-key",
    "deployment_name": "gpt-4",
    "embedding_deployment": "text-embedding-ada-002",
    "verify_ssl": false
  }
}
```

## Examples

### Test Azure Connection Without SSL Verification

```bash
# Quick test to see if SSL is the only issue
uv run dev-agent azure test --insecure
```

Expected output:
```
⚠️  SSL CERTIFICATE VERIFICATION DISABLED

Running in insecure mode. SSL certificates will NOT be verified.
This should ONLY be used for testing/development.

Testing Azure OpenAI Connection
================================

Testing configuration:
  Endpoint: https://your-resource.openai.azure.com/
  Deployment: gpt-4
  ...

✅ All tests passed!
```

### Initialize Project in Insecure Mode

```bash
# Initialize a project without SSL verification
uv run dev-agent --insecure init /path/to/project
```

### Resume Project in Insecure Mode

```bash
# Resume existing project without SSL verification
uv run dev-agent --insecure resume /path/to/project
```

## Warnings and Indicators

When running in insecure mode, you'll see:

1. **Console Warning** - Yellow warning panel at startup
2. **Log Messages** - Warning in logs for each Azure OpenAI client initialization
3. **Security Notice** - Reminder that SSL verification is disabled

Example warning:
```
╭─────────────────── ⚠️  Security Warning ───────────────────╮
│                                                             │
│  ⚠️  SSL CERTIFICATE VERIFICATION DISABLED                 │
│                                                             │
│  Running in insecure mode. SSL certificates will NOT be    │
│  verified. This should ONLY be used for testing/           │
│  development. NEVER use this in production environments.   │
│                                                             │
╰─────────────────────────────────────────────────────────────╯
```

## Environment Variables

All SSL-related environment variables:

```bash
# Disable SSL verification (insecure)
export AZURE_OPENAI_VERIFY_SSL=false

# Or enable explicitly (default)
export AZURE_OPENAI_VERIFY_SSL=true

# Alternative values that work:
# false, False, FALSE, 0, no, No, NO
# true, True, TRUE, 1, yes, Yes, YES
```

## Checking Current SSL Status

### Via Status Command

```bash
uv run dev-agent azure status
```

Look for the "Verify SSL" row in the configuration table.

### Via Python

```python
from dev_agent.config.config_manager import ConfigManager

config_manager = ConfigManager()
config = config_manager.get_config()

if config.azure_openai:
    print(f"SSL Verification: {config.azure_openai.verify_ssl}")
```

## Troubleshooting

### SSL Verification Still Failing

If you're still getting SSL errors even with `--insecure`:

1. **Check the flag is applied**:
   ```bash
   # Should show verify_ssl: false
   uv run dev-agent --insecure azure status
   ```

2. **Check environment variable**:
   ```bash
   echo $AZURE_OPENAI_VERIFY_SSL
   # Should output: false
   ```

3. **Try explicit environment variable**:
   ```bash
   AZURE_OPENAI_VERIFY_SSL=false uv run dev-agent azure test
   ```

### Different Error After Disabling SSL

If you get a different error after disabling SSL verification, it means SSL was the issue and now you're seeing the real problem:

- **401 Unauthorized** → Wrong API key or bearer token
- **404 Not Found** → Wrong deployment name or endpoint
- **Connection Refused** → Wrong endpoint URL or firewall blocking
- **Timeout** → Network connectivity issue

## Security Best Practices

### DO:
✅ Use insecure mode only for local development/testing
✅ Fix SSL certificates properly as soon as possible
✅ Document why insecure mode is needed in your team
✅ Use environment variables (not config files) for temporary insecure mode
✅ Remove insecure settings before committing code

### DON'T:
❌ Use insecure mode in production
❌ Commit `verify_ssl: false` to version control
❌ Leave insecure mode enabled permanently
❌ Use insecure mode with real/sensitive data
❌ Share API keys when using insecure mode

## Transition Plan: From Insecure to Secure

### Step 1: Confirm SSL is the Issue
```bash
# Test with insecure mode
uv run dev-agent azure test --insecure
```

### Step 2: Fix SSL Certificates
```bash
# macOS
/Applications/Python 3.11/Install Certificates.command

# Or update certifi
uv pip install --upgrade certifi
export SSL_CERT_FILE=$(python3 -c "import certifi; print(certifi.where())")
```

### Step 3: Test with SSL Verification Enabled
```bash
# Remove insecure flag
uv run dev-agent azure test
```

### Step 4: Remove Insecure Settings
```bash
# Remove environment variable
unset AZURE_OPENAI_VERIFY_SSL

# Remove from config file if added
# Edit ~/.dev_agent/dev_agent_config.json and remove "verify_ssl": false
```

### Step 5: Verify Secure Mode
```bash
# Should work without --insecure flag
uv run dev-agent azure test
uv run dev-agent init
```

## Logging

When SSL verification is disabled, you'll see log messages like:

```
2025-01-07 10:30:45 - dev_agent.llm.azure_client - WARNING - ⚠️  SSL certificate verification is DISABLED. This is insecure and should only be used for development/testing. Your connection is vulnerable to man-in-the-middle attacks.

2025-01-07 10:30:46 - dev_agent.llm.embeddings - WARNING - ⚠️  SSL certificate verification is DISABLED for embeddings. This is insecure and should only be used for development/testing.
```

These warnings are intentional and cannot be suppressed to ensure you're aware of the security risk.

## FAQ

### Q: Why not just disable SSL verification by default?
**A:** SSL verification is a critical security feature. Disabling it by default would make all users vulnerable to attacks.

### Q: Can I suppress the warnings?
**A:** No, the warnings are intentional. If you're using insecure mode, you should be constantly reminded of the security risk.

### Q: Is there a performance benefit to disabling SSL?
**A:** No, SSL verification has negligible performance impact. Never disable it for performance reasons.

### Q: Can I use this in production if I'm behind a firewall?
**A:** No. Firewalls don't protect against MITM attacks within your network. Always use proper SSL verification.

### Q: What if my company requires SSL inspection?
**A:** Add your company's root CA certificate to Python's certificate store. See `FIX_SSL_CERTIFICATE_ERROR.md` for instructions.

## Related Documentation

- [FIX_SSL_CERTIFICATE_ERROR.md](../../FIX_SSL_CERTIFICATE_ERROR.md) - How to fix SSL certificate issues properly
- [Azure OpenAI Configuration](azure-openai.md) - General Azure OpenAI setup
- [Security Best Practices](security.md) - Security guidelines for dev-agent

## Support

If you need to use insecure mode in production (you shouldn't), please:

1. Document the business justification
2. Get security team approval
3. Implement additional security controls
4. Plan to fix SSL certificates properly
5. Set a deadline to remove insecure mode

For help fixing SSL certificate issues properly, see `FIX_SSL_CERTIFICATE_ERROR.md` or open a GitHub issue.
