# Insecure SSL Mode - Feature Summary

## ✅ Implementation Complete

The `--insecure` flag has been successfully added to dev-agent to help users bypass SSL certificate verification issues during development and testing.

## 🎯 Problem Solved

You were experiencing:
```
httpcore.ConnectError: SSL: CERTIFICATE_VERIFY_FAILED
```

This feature allows you to temporarily bypass this error while you implement a proper fix.

## 🚀 How to Use

### Quick Test (Recommended First Step)

```bash
# Test if SSL is the only issue
uv run dev-agent azure test --insecure
```

If this succeeds, you know SSL certificates are the problem and everything else (API key, endpoint, deployment names) is configured correctly.

### Use in Development

```bash
# Global flag (affects all operations)
uv run dev-agent --insecure init
uv run dev-agent --insecure resume
uv run dev-agent --insecure azure test

# Command-specific flag
uv run dev-agent azure test --insecure

# Environment variable (persists for session)
export AZURE_OPENAI_VERIFY_SSL=false
uv run dev-agent azure test
uv run dev-agent init
```

## ⚠️ Security Warning

When you use `--insecure`, you'll see this warning:

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

## 📋 What Was Changed

### Code Changes

1. **`dev_agent/models/llm_config.py`**
   - Added `verify_ssl: bool` field (default: `True`)

2. **`dev_agent/llm/azure_client.py`**
   - Modified to use custom HTTP client with SSL verification setting
   - Added warning log when SSL is disabled

3. **`dev_agent/llm/embeddings.py`**
   - Same changes as azure_client.py for embeddings

4. **`dev_agent/config/config_manager.py`**
   - Added support for `AZURE_OPENAI_VERIFY_SSL` environment variable

5. **`dev_agent/cli/main.py`**
   - Added global `--insecure` flag
   - Shows security warning when used

6. **`dev_agent/cli/azure_config.py`**
   - Added `--insecure` flag to `azure test` command

### Documentation Created

1. **`docs/configuration/insecure-ssl.md`** - Comprehensive guide
2. **`INSECURE_MODE_QUICK_START.md`** - Quick reference
3. **`FIX_SSL_CERTIFICATE_ERROR.md`** - How to fix SSL properly
4. **`INSECURE_SSL_IMPLEMENTATION.md`** - Technical implementation details

### Test Scripts

1. **`test_insecure_mode.py`** - Unit tests (✅ All passing)
2. **`test_azure_debug.py`** - Debug script with full stack traces
3. **`test_azure_no_ssl.py`** - Manual SSL bypass test

## ✅ Verification

All tests pass:
```bash
$ uv run python test_insecure_mode.py

============================================================
Testing Insecure SSL Mode Implementation
============================================================

Testing AzureOpenAIConfig model...
  ✓ Default verify_ssl=True
  ✓ Explicit verify_ssl=False works
✅ Config model tests passed

Testing environment variable parsing...
  ✓ AZURE_OPENAI_VERIFY_SSL=false works
  ✓ AZURE_OPENAI_VERIFY_SSL=true works
  ✓ AZURE_OPENAI_VERIFY_SSL=1 works
  ✓ AZURE_OPENAI_VERIFY_SSL=0 works
✅ Environment variable tests passed

Testing client initialization...
  ✓ AzureOpenAIClient initialized with verify_ssl=False
  ✓ AzureEmbeddingClient initialized with verify_ssl=False
✅ Client initialization tests passed

Testing bearer token with insecure mode...
  ✓ Bearer token with verify_ssl=False works
✅ Bearer token tests passed

============================================================
✅ ALL TESTS PASSED
============================================================
```

## 🎬 Next Steps for You

### Step 1: Test with Insecure Mode

```bash
# This should now work
uv run dev-agent azure test --insecure
```

Expected result: ✅ Connection successful (with warnings)

### Step 2: Fix SSL Certificates Properly

Choose the best solution for your system:

#### macOS (Recommended):
```bash
/Applications/Python\ 3.11/Install\ Certificates.command
```

#### All Platforms:
```bash
uv pip install --upgrade certifi
export SSL_CERT_FILE=$(python3 -c "import certifi; print(certifi.where())")
echo 'export SSL_CERT_FILE=$(python3 -c "import certifi; print(certifi.where())")' >> ~/.zshrc
```

See `FIX_SSL_CERTIFICATE_ERROR.md` for detailed instructions.

### Step 3: Verify Secure Mode Works

```bash
# Remove insecure flag - should work now
uv run dev-agent azure test
```

### Step 4: Remove Insecure Settings

```bash
# Remove environment variable if set
unset AZURE_OPENAI_VERIFY_SSL

# Remove from config file if added
# (Don't commit verify_ssl: false to version control)
```

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| `INSECURE_MODE_QUICK_START.md` | Quick commands to get started |
| `docs/configuration/insecure-ssl.md` | Complete documentation |
| `FIX_SSL_CERTIFICATE_ERROR.md` | How to fix SSL properly |
| `AZURE_CONNECTION_DEBUG_GUIDE.md` | General debugging guide |
| `DEBUG_AZURE_TEST.md` | How to get detailed errors |

## 🔒 Security Features

- ✅ Secure by default (`verify_ssl=True`)
- ✅ Multiple warnings when disabled
- ✅ Clear documentation of risks
- ✅ Guidance on proper fixes
- ✅ No silent failures

## 🧪 Testing Commands

```bash
# Run unit tests
uv run python test_insecure_mode.py

# Test with real Azure OpenAI (insecure)
uv run dev-agent azure test --insecure

# Test with debug output
uv run python test_azure_debug.py

# Check for code issues
uv run mypy dev_agent/models/llm_config.py
uv run mypy dev_agent/llm/azure_client.py
uv run mypy dev_agent/llm/embeddings.py
```

## 💡 Key Features

1. **Multiple Ways to Use**
   - Command-line flag: `--insecure`
   - Environment variable: `AZURE_OPENAI_VERIFY_SSL=false`
   - Configuration file: `"verify_ssl": false`

2. **Clear Warnings**
   - Console warning panel
   - Log messages
   - Documentation

3. **Backward Compatible**
   - Existing configs work unchanged
   - Default is secure
   - No breaking changes

4. **Well Documented**
   - User guides
   - Technical docs
   - Security warnings

## 🎉 Success Criteria

- ✅ Feature implemented
- ✅ All tests passing
- ✅ No code diagnostics errors
- ✅ Documentation complete
- ✅ Security warnings in place
- ✅ Backward compatible

## 🤝 Support

If you have issues:

1. **SSL still failing?** Check `FIX_SSL_CERTIFICATE_ERROR.md`
2. **Different error?** Check `AZURE_CONNECTION_DEBUG_GUIDE.md`
3. **Need detailed errors?** Run `test_azure_debug.py`
4. **Still stuck?** Open a GitHub issue with diagnostic output

## 📝 Example Session

```bash
# 1. Initial error
$ uv run dev-agent azure test
❌ SSL: CERTIFICATE_VERIFY_FAILED

# 2. Test with insecure mode
$ uv run dev-agent azure test --insecure
⚠️  SSL CERTIFICATE VERIFICATION DISABLED
✅ All tests passed!

# 3. Fix SSL certificates
$ /Applications/Python\ 3.11/Install\ Certificates.command
✅ Certificates installed

# 4. Test secure mode
$ uv run dev-agent azure test
✅ All tests passed!

# 5. Success!
$ uv run dev-agent init
✅ Project initialized
```

## 🏁 Conclusion

The `--insecure` flag is now available to help you:

1. ✅ **Diagnose** - Confirm SSL is the only issue
2. ✅ **Unblock** - Continue development while fixing SSL
3. ✅ **Test** - Verify configuration in controlled environments

Remember: This is a **temporary workaround**, not a permanent solution. Always fix SSL certificates properly!

---

**Ready to test?**

```bash
uv run dev-agent azure test --insecure
```

Good luck! 🚀
