# Implementation: Insecure SSL Mode Feature

## Summary

Added `--insecure` flag to dev-agent to disable SSL certificate verification for development/testing purposes. This helps users quickly diagnose and work around SSL certificate issues while they implement proper fixes.

## Changes Made

### 1. Configuration Model (`dev_agent/models/llm_config.py`)

**Added:**
- `verify_ssl: bool` field to `AzureOpenAIConfig` (default: `True`)
- Documentation explaining the security implications

```python
verify_ssl: bool = Field(
    default=True,
    description="Verify SSL certificates (set to False to disable SSL verification - INSECURE!)",
)
```

### 2. Azure OpenAI Client (`dev_agent/llm/azure_client.py`)

**Modified:**
- Client initialization to create custom `httpx.AsyncClient` with `verify` parameter
- Added warning log when SSL verification is disabled

```python
# Create HTTP client with SSL verification setting
import httpx
http_client = httpx.AsyncClient(
    verify=config.verify_ssl,
    timeout=config.timeout,
)

# Log warning if SSL verification is disabled
if not config.verify_ssl:
    logger.warning(
        "⚠️  SSL certificate verification is DISABLED. "
        "This is insecure and should only be used for development/testing. "
        "Your connection is vulnerable to man-in-the-middle attacks."
    )
```

### 3. Embedding Client (`dev_agent/llm/embeddings.py`)

**Modified:**
- Same changes as Azure OpenAI client
- Custom HTTP client with SSL verification setting
- Warning log for embeddings

### 4. Configuration Manager (`dev_agent/config/config_manager.py`)

**Added:**
- Support for `AZURE_OPENAI_VERIFY_SSL` environment variable
- Parses boolean values: `true/false`, `1/0`, `yes/no`

```python
# SSL verification (default: True)
if verify_ssl := os.getenv("AZURE_OPENAI_VERIFY_SSL"):
    config_data["verify_ssl"] = verify_ssl.lower() in ("true", "1", "yes")
```

### 5. Main CLI (`dev_agent/cli/main.py`)

**Added:**
- Global `--insecure` flag to main app callback
- Security warning panel when flag is used
- Sets `AZURE_OPENAI_VERIFY_SSL=false` environment variable

```python
insecure: Annotated[
    bool, typer.Option("--insecure", help="Disable SSL certificate verification (INSECURE - for testing only)")
] = False,
```

### 6. Azure Config CLI (`dev_agent/cli/azure_config.py`)

**Added:**
- `--insecure` flag to `azure test` command
- Security warning panel specific to test command
- Overrides config to disable SSL verification

```python
insecure: bool = typer.Option(
    False,
    "--insecure",
    help="Disable SSL certificate verification (INSECURE - for testing only)"
),
```

### 7. Documentation

**Created:**
- `docs/configuration/insecure-ssl.md` - Comprehensive documentation
- `INSECURE_MODE_QUICK_START.md` - Quick reference guide
- `FIX_SSL_CERTIFICATE_ERROR.md` - SSL certificate troubleshooting (already existed)

## Usage Examples

### Command-Line Flags

```bash
# Global flag (affects all operations)
uv run dev-agent --insecure azure test
uv run dev-agent --insecure init
uv run dev-agent --insecure resume

# Command-specific flag
uv run dev-agent azure test --insecure
```

### Environment Variable

```bash
# Set for session
export AZURE_OPENAI_VERIFY_SSL=false
uv run dev-agent azure test

# Set for single command
AZURE_OPENAI_VERIFY_SSL=false uv run dev-agent azure test
```

### Configuration File

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

## Security Features

### Warnings

1. **Console Warning** - Yellow panel displayed when `--insecure` flag is used
2. **Log Warnings** - Warning logged for each client initialization
3. **Documentation** - Extensive warnings in all documentation

### Warning Message

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

## Testing

### Manual Testing

```bash
# 1. Test with SSL verification enabled (should fail with SSL error)
uv run dev-agent azure test

# 2. Test with SSL verification disabled (should work)
uv run dev-agent azure test --insecure

# 3. Test environment variable
export AZURE_OPENAI_VERIFY_SSL=false
uv run dev-agent azure test
unset AZURE_OPENAI_VERIFY_SSL

# 4. Test global flag
uv run dev-agent --insecure azure test

# 5. Verify warning is displayed
# Should see yellow warning panel
```

### Verification

```bash
# Check diagnostics (should show no errors)
uv run python -m mypy dev_agent/models/llm_config.py
uv run python -m mypy dev_agent/llm/azure_client.py
uv run python -m mypy dev_agent/llm/embeddings.py
uv run python -m mypy dev_agent/config/config_manager.py
```

## Configuration Precedence

The `verify_ssl` setting follows this precedence (highest to lowest):

1. **Command-line flag** (`--insecure`)
2. **Environment variable** (`AZURE_OPENAI_VERIFY_SSL`)
3. **Configuration file** (`verify_ssl` in config)
4. **Default value** (`True`)

## Backward Compatibility

- ✅ Existing configurations continue to work (default: `verify_ssl=True`)
- ✅ No breaking changes to API or configuration format
- ✅ New field is optional with safe default
- ✅ Environment variable is optional

## Security Considerations

### Risks When Disabled

- Man-in-the-middle (MITM) attacks
- API key theft
- Data interception and modification
- Connection to malicious servers

### Mitigations

- Default is secure (`verify_ssl=True`)
- Multiple warnings displayed
- Clear documentation of risks
- Guidance on proper SSL certificate fixes

### Recommended Use Cases

✅ **Acceptable:**
- Local development with certificate issues
- Debugging SSL problems
- Temporary workaround while fixing certificates
- Controlled test environments

❌ **Not Acceptable:**
- Production deployments
- Handling sensitive data
- Long-term solution
- Public-facing services

## Future Enhancements

Potential improvements:

1. **Certificate Pinning** - Pin specific certificates for extra security
2. **Custom CA Bundle** - Support custom CA certificate bundles
3. **Audit Logging** - Log when insecure mode is used
4. **Time Limit** - Auto-disable insecure mode after time period
5. **Approval Required** - Require explicit confirmation for insecure mode

## Related Issues

This feature addresses:
- SSL certificate verification failures on macOS
- Corporate proxy SSL inspection issues
- Development environment certificate problems
- Quick debugging of SSL vs other connection issues

## Documentation Links

- User Guide: `docs/configuration/insecure-ssl.md`
- Quick Start: `INSECURE_MODE_QUICK_START.md`
- SSL Fixes: `FIX_SSL_CERTIFICATE_ERROR.md`
- Debug Guide: `AZURE_CONNECTION_DEBUG_GUIDE.md`

## Rollout Plan

1. ✅ Implement feature with secure defaults
2. ✅ Add comprehensive warnings
3. ✅ Create documentation
4. ⏳ Test with users experiencing SSL issues
5. ⏳ Gather feedback
6. ⏳ Update documentation based on feedback
7. ⏳ Consider additional security features

## Support

For users experiencing SSL certificate issues:

1. **First**: Try proper SSL certificate fixes (see `FIX_SSL_CERTIFICATE_ERROR.md`)
2. **If blocked**: Use `--insecure` flag temporarily
3. **Then**: Implement proper fix as soon as possible
4. **Finally**: Remove insecure mode and verify secure connection works

## Conclusion

The `--insecure` flag provides a pragmatic solution for users experiencing SSL certificate issues while maintaining security by default and providing clear warnings about the risks.

**Key Principles:**
- Secure by default
- Clear warnings
- Temporary workaround, not permanent solution
- Comprehensive documentation
- Easy to use when needed
