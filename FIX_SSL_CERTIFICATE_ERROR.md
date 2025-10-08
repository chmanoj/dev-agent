# Fix: SSL CERTIFICATE_VERIFY_FAILED Error

## The Problem

You're getting:
```
httpcore.ConnectError: SSL: CERTIFICATE_VERIFY_FAILED
```

This means Python can't verify the SSL certificate when connecting to Azure OpenAI. This is a **security feature**, not a bug.

## Quick Fixes (In Order of Preference)

### Solution 1: Update Python Certificates (Recommended for macOS)

If you're on **macOS** and installed Python via the official installer:

```bash
# Run the Install Certificates command that comes with Python
# For Python 3.11 (adjust version as needed)
/Applications/Python\ 3.11/Install\ Certificates.command

# Or manually:
pip install --upgrade certifi

# Then run this Python command to install certificates
python3 -c "import certifi; print(certifi.where())"
```

### Solution 2: Update System CA Certificates

#### macOS (using Homebrew):
```bash
# Install/update CA certificates
brew install ca-certificates

# Update certifi package
uv pip install --upgrade certifi

# Verify
python3 -c "import ssl; print(ssl.get_default_verify_paths())"
```

#### Linux (Ubuntu/Debian):
```bash
# Update CA certificates
sudo apt-get update
sudo apt-get install --reinstall ca-certificates

# Update Python certifi
uv pip install --upgrade certifi
```

#### Linux (RHEL/CentOS):
```bash
# Update CA certificates
sudo yum reinstall ca-certificates

# Update Python certifi
uv pip install --upgrade certifi
```

### Solution 3: Set SSL Certificate Path (If Behind Corporate Proxy)

If you're in a corporate environment with SSL inspection:

```bash
# Find where certifi stores certificates
python3 -c "import certifi; print(certifi.where())"

# Set the SSL_CERT_FILE environment variable
export SSL_CERT_FILE=$(python3 -c "import certifi; print(certifi.where())")

# Add to your shell profile for persistence
echo 'export SSL_CERT_FILE=$(python3 -c "import certifi; print(certifi.where())")' >> ~/.zshrc
source ~/.zshrc

# Test again
uv run python test_azure_debug.py
```

### Solution 4: Add Corporate Root CA (Corporate Networks Only)

If your company uses SSL inspection/MITM proxy:

```bash
# 1. Get your company's root CA certificate (ask IT department)
# Save it as: ~/company-root-ca.crt

# 2. Find Python's certificate bundle
CERT_PATH=$(python3 -c "import certifi; print(certifi.where())")
echo "Certificate bundle: $CERT_PATH"

# 3. Backup the original
cp "$CERT_PATH" "$CERT_PATH.backup"

# 4. Append your company's CA certificate
cat ~/company-root-ca.crt >> "$CERT_PATH"

# 5. Test
uv run python test_azure_debug.py
```

### Solution 5: Temporary Workaround - Disable SSL Verification (NOT RECOMMENDED)

⚠️ **WARNING: This is insecure and should only be used for testing!**

Create a temporary test script:

```python
# test_azure_no_ssl.py
import asyncio
import os
import ssl
import httpx
from dev_agent.models.llm_config import AzureOpenAIConfig
from dev_agent.llm.azure_client import AzureOpenAIClient
from openai import AsyncAzureOpenAI

async def test_without_ssl_verification():
    """Test connection without SSL verification - INSECURE!"""
    
    config = AzureOpenAIConfig(
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        embedding_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
    )
    
    # Create HTTP client that doesn't verify SSL
    http_client = httpx.AsyncClient(verify=False)
    
    # Create Azure OpenAI client with custom HTTP client
    client = AsyncAzureOpenAI(
        api_key=config.api_key.get_secret_value(),
        api_version=config.api_version,
        azure_endpoint=config.endpoint,
        http_client=http_client,
    )
    
    try:
        response = await client.chat.completions.create(
            model=config.deployment_name,
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=10,
        )
        print(f"✅ Connection works (without SSL verification): {response.choices[0].message.content}")
        print("\n⚠️  This proves the issue is SSL certificates, not network/auth.")
        print("Now fix the SSL certificates using one of the solutions above.")
    except Exception as e:
        print(f"❌ Still failed: {e}")
    finally:
        await http_client.aclose()

if __name__ == "__main__":
    asyncio.run(test_without_ssl_verification())
```

Run it:
```bash
uv run python test_azure_no_ssl.py
```

If this works, it confirms the issue is SSL certificates, not authentication or network.

## Detailed Diagnosis

### Check Current Certificate Setup

```bash
# Check Python's SSL configuration
python3 << 'EOF'
import ssl
import certifi

print("SSL Version:", ssl.OPENSSL_VERSION)
print("Default CA Bundle:", ssl.get_default_verify_paths())
print("Certifi CA Bundle:", certifi.where())

# Try to verify Azure OpenAI certificate
import socket
context = ssl.create_default_context()
try:
    with socket.create_connection(("your-resource.openai.azure.com", 443)) as sock:
        with context.wrap_socket(sock, server_hostname="your-resource.openai.azure.com") as ssock:
            print("✅ SSL verification successful!")
            print("Certificate:", ssock.getpeercert())
except ssl.SSLError as e:
    print(f"❌ SSL verification failed: {e}")
EOF
```

### Check if OpenSSL is Outdated

```bash
# Check OpenSSL version
openssl version

# Should be 1.1.1 or higher
# If older, update:

# macOS
brew upgrade openssl

# Linux
sudo apt-get update && sudo apt-get upgrade openssl
```

## Root Cause Analysis

This error typically happens because:

1. **Python can't find system CA certificates** (most common on macOS)
2. **Outdated CA certificate bundle** (certifi package needs update)
3. **Corporate SSL inspection** (MITM proxy replacing certificates)
4. **Python installed without certificates** (official Python installer on macOS)
5. **Virtual environment missing certificates** (uv/venv not inheriting system certs)

## Permanent Fix for macOS Users

If you're on macOS and installed Python from python.org:

```bash
# 1. Run the certificate installer that comes with Python
# This is the OFFICIAL fix from Python.org
cd /Applications/Python\ 3.*/
./Install\ Certificates.command

# 2. Verify it worked
python3 -c "import ssl; print(ssl.get_default_verify_paths())"

# 3. Test Azure connection
uv run python test_azure_debug.py
```

## Permanent Fix for Corporate Networks

If you're behind a corporate proxy with SSL inspection:

```bash
# 1. Export your company's root CA certificate from your browser
# Chrome: Settings → Privacy and security → Security → Manage certificates
# Export as: company-root-ca.crt

# 2. Set environment variable to use it
export REQUESTS_CA_BUNDLE=~/company-root-ca.crt
export SSL_CERT_FILE=~/company-root-ca.crt

# 3. Add to shell profile
cat >> ~/.zshrc << 'EOF'
export REQUESTS_CA_BUNDLE=~/company-root-ca.crt
export SSL_CERT_FILE=~/company-root-ca.crt
EOF

# 4. Reload shell
source ~/.zshrc

# 5. Test
uv run python test_azure_debug.py
```

## Verify the Fix

After applying any solution, verify it works:

```bash
# Test 1: Python SSL verification
python3 << 'EOF'
import ssl
import socket

context = ssl.create_default_context()
with socket.create_connection(("www.microsoft.com", 443)) as sock:
    with context.wrap_socket(sock, server_hostname="www.microsoft.com") as ssock:
        print("✅ SSL verification works!")
EOF

# Test 2: Azure OpenAI connection
uv run python test_azure_debug.py

# Test 3: Full dev-agent test
uv run dev-agent azure test
```

## Still Not Working?

### Advanced Debugging

```bash
# Enable SSL debug logging
export SSLKEYLOGFILE=~/ssl-keys.log
export OPENSSL_CONF=/dev/null

# Run with maximum verbosity
python3 -v -c "
import ssl
import urllib.request
try:
    urllib.request.urlopen('https://your-resource.openai.azure.com/')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
"
```

### Check Certificate Chain

```bash
# Download and inspect Azure OpenAI certificate
echo | openssl s_client -servername your-resource.openai.azure.com \
  -connect your-resource.openai.azure.com:443 2>/dev/null | \
  openssl x509 -text -noout

# Check certificate chain
openssl s_client -showcerts -servername your-resource.openai.azure.com \
  -connect your-resource.openai.azure.com:443 < /dev/null
```

## Summary of Solutions

| Solution | Best For | Security | Difficulty |
|----------|----------|----------|------------|
| Update Python Certs | macOS users | ✅ Secure | ⭐ Easy |
| Update CA Bundle | All platforms | ✅ Secure | ⭐ Easy |
| Set SSL_CERT_FILE | Corporate networks | ✅ Secure | ⭐⭐ Medium |
| Add Corporate CA | Corporate networks | ✅ Secure | ⭐⭐⭐ Hard |
| Disable SSL (temp) | Testing only | ❌ INSECURE | ⭐ Easy |

## Recommended Action Plan

1. **Try Solution 1** (Update Python Certificates) - 2 minutes
2. **Try Solution 2** (Update CA Certificates) - 2 minutes  
3. **Try Solution 3** (Set SSL_CERT_FILE) - 1 minute
4. If still failing, you're likely behind a corporate proxy → **Solution 4**
5. Use **Solution 5** only to confirm SSL is the issue, then fix properly

## After Fixing

Once SSL verification works, your Azure OpenAI connection should work perfectly. The error will change from:

❌ `SSL: CERTIFICATE_VERIFY_FAILED`

To either:
✅ `Success!` (if everything is configured correctly)

Or a different error like:
- `401 Unauthorized` → Wrong API key
- `404 Not Found` → Wrong deployment name
- `Connection refused` → Wrong endpoint

These are easier to fix once SSL is working!
