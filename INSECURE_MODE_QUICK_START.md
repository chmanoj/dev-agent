# Quick Start: Using Insecure Mode to Bypass SSL Certificate Errors

## ⚠️ IMPORTANT: This is for Testing Only!

If you're getting `SSL: CERTIFICATE_VERIFY_FAILED` errors and need to test quickly, you can temporarily disable SSL verification.

**This is INSECURE and should NEVER be used in production!**

## Quick Commands

### Test Azure Connection (Insecure)

```bash
uv run dev-agent azure test --insecure
```

### Initialize Project (Insecure)

```bash
uv run dev-agent --insecure init
```

### Resume Project (Insecure)

```bash
uv run dev-agent --insecure resume
```

### Use Environment Variable

```bash
# Set for current session
export AZURE_OPENAI_VERIFY_SSL=false

# Now run any command
uv run dev-agent azure test
uv run dev-agent init
```

## What You'll See

When using insecure mode, you'll see a warning:

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

This is intentional - you should always be aware when SSL verification is disabled.

## After Testing

Once you confirm that SSL certificates are the only issue, **fix them properly**:

### macOS (Recommended)

```bash
# Run Python's certificate installer
/Applications/Python\ 3.11/Install\ Certificates.command

# Or for Python 3.12
/Applications/Python\ 3.12/Install\ Certificates.command
```

### All Platforms

```bash
# Update certifi package
uv pip install --upgrade certifi

# Set SSL certificate file
export SSL_CERT_FILE=$(python3 -c "import certifi; print(certifi.where())")

# Add to shell profile for persistence
echo 'export SSL_CERT_FILE=$(python3 -c "import certifi; print(certifi.where())")' >> ~/.zshrc
source ~/.zshrc
```

### Test with SSL Verification Enabled

```bash
# Remove insecure flag - should work now
uv run dev-agent azure test
```

## Full Documentation

- **Insecure Mode Details**: `docs/configuration/insecure-ssl.md`
- **SSL Certificate Fixes**: `FIX_SSL_CERTIFICATE_ERROR.md`
- **General Debugging**: `AZURE_CONNECTION_DEBUG_GUIDE.md`

## Why This Exists

The `--insecure` flag is provided to:

1. **Quickly diagnose** if SSL certificates are the only issue
2. **Unblock development** while waiting for proper certificate fixes
3. **Test in controlled environments** where security is less critical

It is **NOT** intended for:

- ❌ Production use
- ❌ Handling sensitive data
- ❌ Long-term solutions
- ❌ Avoiding proper SSL configuration

## Security Implications

When SSL verification is disabled:

- 🔓 Your connection can be intercepted (MITM attacks)
- 🔓 Your API keys can be stolen
- 🔓 Your data can be modified in transit
- 🔓 You have no guarantee you're connecting to the real Azure OpenAI

**Always fix SSL certificates properly instead of using insecure mode!**
