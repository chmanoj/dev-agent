# SSL Certificate Error? Use --insecure Flag

## 🎯 Quick Solution

If you're getting `SSL: CERTIFICATE_VERIFY_FAILED` errors, you can now use the `--insecure` flag:

```bash
uv run dev-agent azure test --insecure
```

⚠️ **This is for testing only! Fix SSL certificates properly afterward.**

## 📖 Documentation

| Document | What It Does |
|----------|--------------|
| **[INSECURE_MODE_QUICK_START.md](INSECURE_MODE_QUICK_START.md)** | ⚡ Quick commands to get started |
| **[FIX_SSL_CERTIFICATE_ERROR.md](FIX_SSL_CERTIFICATE_ERROR.md)** | 🔧 How to fix SSL properly |
| **[docs/configuration/insecure-ssl.md](docs/configuration/insecure-ssl.md)** | 📚 Complete documentation |
| **[INSECURE_SSL_FEATURE_SUMMARY.md](INSECURE_SSL_FEATURE_SUMMARY.md)** | ✅ Feature overview |

## 🚀 Usage

### Test Azure Connection

```bash
# With insecure flag
uv run dev-agent azure test --insecure

# Or set environment variable
export AZURE_OPENAI_VERIFY_SSL=false
uv run dev-agent azure test
```

### Initialize Project

```bash
uv run dev-agent --insecure init
```

### Resume Project

```bash
uv run dev-agent --insecure resume
```

## ⚠️ Important

**This disables SSL certificate verification, which is INSECURE!**

Use this only to:
- ✅ Diagnose if SSL is the only issue
- ✅ Unblock development temporarily
- ✅ Test in controlled environments

Do NOT use this for:
- ❌ Production deployments
- ❌ Handling sensitive data
- ❌ Long-term solutions

## 🔧 Proper Fix

After confirming SSL is the issue, fix it properly:

### macOS
```bash
/Applications/Python\ 3.11/Install\ Certificates.command
```

### All Platforms
```bash
uv pip install --upgrade certifi
export SSL_CERT_FILE=$(python3 -c "import certifi; print(certifi.where())")
```

See [FIX_SSL_CERTIFICATE_ERROR.md](FIX_SSL_CERTIFICATE_ERROR.md) for details.

## 🧪 Test Scripts

```bash
# Unit tests
uv run python test_insecure_mode.py

# Debug with full stack traces
uv run python test_azure_debug.py

# Manual SSL bypass test
uv run python test_azure_no_ssl.py
```

## 📋 What Changed

- Added `--insecure` flag to CLI
- Added `AZURE_OPENAI_VERIFY_SSL` environment variable
- Added `verify_ssl` field to configuration
- Added security warnings
- Created comprehensive documentation

## ✅ Verification

All tests pass:
```bash
$ uv run python test_insecure_mode.py
✅ ALL TESTS PASSED
```

## 🎬 Your Next Steps

1. **Test with insecure mode**: `uv run dev-agent azure test --insecure`
2. **Fix SSL properly**: See `FIX_SSL_CERTIFICATE_ERROR.md`
3. **Test secure mode**: `uv run dev-agent azure test`
4. **Remove insecure settings**: `unset AZURE_OPENAI_VERIFY_SSL`

## 💬 Need Help?

- **SSL Issues**: [FIX_SSL_CERTIFICATE_ERROR.md](FIX_SSL_CERTIFICATE_ERROR.md)
- **Debugging**: [AZURE_CONNECTION_DEBUG_GUIDE.md](AZURE_CONNECTION_DEBUG_GUIDE.md)
- **Detailed Errors**: [DEBUG_AZURE_TEST.md](DEBUG_AZURE_TEST.md)

---

**Ready to test?**

```bash
uv run dev-agent azure test --insecure
```
