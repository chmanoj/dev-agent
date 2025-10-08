# Getting Detailed Error Messages from Azure Test Command

## Method 1: Add --verbose Flag (Recommended - Requires Code Change)

The current `dev-agent azure test` command doesn't have a verbose flag. Here's how to add it:

### Quick Fix: Modify the test command

Edit `dev_agent/cli/azure_config.py` and update the `test_azure_connection` function:

```python
@app.command("test")
def test_azure_connection(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed error messages and stack traces"
    ),
) -> None:
    """Test Azure OpenAI connection with comprehensive validation."""
    # ... existing code ...
    
    # In the exception handlers, add verbose output:
    except Exception as e:
        console.print(f"[red]✗ Chat completion test failed: {e}[/red]")
        if verbose:
            import traceback
            console.print("\n[yellow]Detailed error trace:[/yellow]")
            console.print(traceback.format_exc())
```

Then run:
```bash
uv run dev-agent azure test --verbose
```

## Method 2: Use Python Directly (Works Now - No Code Changes)

Create a test script to get full stack traces:

### Create `test_azure_debug.py`:

```python
#!/usr/bin/env python3
"""Debug script for Azure OpenAI connection testing with full error details."""

import asyncio
import logging
import os
import sys
import traceback
from pathlib import Path

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from dev_agent.config.config_manager import ConfigManager
from dev_agent.llm.azure_client import AzureOpenAIClient
from dev_agent.llm.embeddings import AzureEmbeddingClient


async def test_completion(config):
    """Test chat completion with detailed error reporting."""
    print("\n" + "="*60)
    print("Testing Chat Completion")
    print("="*60)
    
    try:
        print(f"Endpoint: {config.endpoint}")
        print(f"Deployment: {config.deployment_name}")
        print(f"API Version: {config.api_version}")
        print(f"Timeout: {config.timeout}s")
        print()
        
        client = AzureOpenAIClient(config)
        print("✓ Client initialized successfully")
        
        print("Sending test request...")
        response = await client.generate_completion(
            prompt="Say 'test successful' if you can read this.",
            system_prompt="You are a helpful assistant.",
            max_tokens=10,
        )
        
        print(f"✅ SUCCESS: {response}")
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {type(e).__name__}: {e}")
        print("\n" + "-"*60)
        print("FULL STACK TRACE:")
        print("-"*60)
        traceback.print_exc()
        print("-"*60)
        return False


async def test_embeddings(config):
    """Test embeddings with detailed error reporting."""
    print("\n" + "="*60)
    print("Testing Embeddings")
    print("="*60)
    
    try:
        print(f"Endpoint: {config.endpoint}")
        print(f"Embedding Deployment: {config.embedding_deployment}")
        print(f"API Version: {config.api_version}")
        print()
        
        client = AzureEmbeddingClient(config)
        print("✓ Client initialized successfully")
        
        print("Sending test embedding request...")
        embeddings = await client.embed_batch(texts=["test embedding"])
        
        if embeddings and len(embeddings) > 0:
            dimension = len(embeddings[0])
            print(f"✅ SUCCESS: Generated embedding with dimension {dimension}")
            return True
        else:
            print("❌ FAILED: No embeddings returned")
            return False
            
    except Exception as e:
        print(f"\n❌ FAILED: {type(e).__name__}: {e}")
        print("\n" + "-"*60)
        print("FULL STACK TRACE:")
        print("-"*60)
        traceback.print_exc()
        print("-"*60)
        return False


async def main():
    """Main test function."""
    print("="*60)
    print("Azure OpenAI Connection Debug Test")
    print("="*60)
    
    # Load configuration
    print("\nLoading configuration...")
    try:
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        if not config.azure_openai:
            print("❌ ERROR: Azure OpenAI is not configured")
            print("\nSet these environment variables:")
            print("  AZURE_OPENAI_ENDPOINT")
            print("  AZURE_OPENAI_API_KEY")
            print("  AZURE_OPENAI_DEPLOYMENT_NAME")
            print("  AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
            return
        
        azure_config = config.azure_openai
        print("✓ Configuration loaded successfully")
        
    except Exception as e:
        print(f"❌ ERROR loading configuration: {e}")
        traceback.print_exc()
        return
    
    # Test completion
    completion_success = await test_completion(azure_config)
    
    # Test embeddings
    embedding_success = await test_embeddings(azure_config)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Chat Completion: {'✅ PASSED' if completion_success else '❌ FAILED'}")
    print(f"Embeddings:      {'✅ PASSED' if embedding_success else '❌ FAILED'}")
    print("="*60)
    
    if completion_success and embedding_success:
        print("\n🎉 All tests passed! Your Azure OpenAI configuration is working.")
    else:
        print("\n⚠️  Some tests failed. Review the error details above.")


if __name__ == "__main__":
    asyncio.run(main())
```

### Run the debug script:

```bash
# Make it executable
chmod +x test_azure_debug.py

# Run with uv
uv run python test_azure_debug.py

# Or run directly with Python
python test_azure_debug.py
```

## Method 3: Enable Debug Logging (Works Now)

Set environment variables to enable detailed logging:

```bash
# Enable DEBUG level logging
export DEV_AGENT_LOG_LEVEL=DEBUG

# Enable Python's HTTP debug logging
export PYTHONVERBOSE=1

# Enable OpenAI SDK debug logging
export OPENAI_LOG=debug

# Run the test
uv run dev-agent azure test
```

## Method 4: Use Python's -v Flag

Run with Python's verbose flag to see import and execution details:

```bash
uv run python -v -m dev_agent.cli.main azure test
```

## Method 5: Interactive Python Session

Test interactively to see errors in real-time:

```python
# Start Python with uv
uv run python

# Then in the Python shell:
import asyncio
import os
from dev_agent.models.llm_config import AzureOpenAIConfig
from dev_agent.llm.azure_client import AzureOpenAIClient

# Create config
config = AzureOpenAIConfig(
    endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    embedding_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
)

# Test connection
client = AzureOpenAIClient(config)

# Run async test
async def test():
    try:
        response = await client.generate_completion("Say hello", max_tokens=10)
        print(f"Success: {response}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test())
```

## Method 6: Check Log Files

dev-agent writes logs to files. Check them for detailed error information:

```bash
# Check the main log file
cat .dev_agent/logs/dev_agent.log

# Or tail it in real-time
tail -f .dev_agent/logs/dev_agent.log

# Search for errors
grep -i error .dev_agent/logs/dev_agent.log
grep -i exception .dev_agent/logs/dev_agent.log
```

## Method 7: Use curl with Verbose Output

Test the raw API directly to see network-level errors:

```bash
# Test with maximum verbosity
curl -v -X POST \
  "$AZURE_OPENAI_ENDPOINT/openai/deployments/$AZURE_OPENAI_DEPLOYMENT_NAME/chat/completions?api-version=2024-02-15-preview" \
  -H "Content-Type: application/json" \
  -H "api-key: $AZURE_OPENAI_API_KEY" \
  -d '{
    "messages": [{"role": "user", "content": "test"}],
    "max_tokens": 10
  }' 2>&1 | tee curl_debug.log

# This will show:
# - DNS resolution
# - TCP connection
# - TLS handshake
# - HTTP headers
# - Response body
```

## Method 8: Network Packet Capture (Advanced)

For deep network debugging:

```bash
# Install tcpdump (if not already installed)
# macOS: brew install tcpdump
# Linux: sudo apt-get install tcpdump

# Capture traffic to Azure OpenAI (requires sudo)
sudo tcpdump -i any -w azure_openai.pcap host your-resource.openai.azure.com

# In another terminal, run the test
uv run dev-agent azure test

# Stop tcpdump (Ctrl+C), then analyze with Wireshark
wireshark azure_openai.pcap
```

## Quick Comparison

| Method | Ease of Use | Detail Level | Requires Code Change |
|--------|-------------|--------------|---------------------|
| Method 1: --verbose flag | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Yes |
| Method 2: Debug script | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | No |
| Method 3: Debug logging | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | No |
| Method 4: Python -v | ⭐⭐⭐ | ⭐⭐ | No |
| Method 5: Interactive | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | No |
| Method 6: Log files | ⭐⭐⭐⭐ | ⭐⭐⭐ | No |
| Method 7: curl verbose | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | No |
| Method 8: Packet capture | ⭐⭐ | ⭐⭐⭐⭐⭐ | No |

## Recommended Approach

**For immediate debugging (no code changes):**

1. Use Method 2 (debug script) - gives you full stack traces
2. Use Method 3 (debug logging) - enables detailed logging
3. Use Method 7 (curl) - tests raw API connectivity

**For long-term solution:**

Implement Method 1 (--verbose flag) in the codebase so all users can benefit.

## Example Output with Full Stack Trace

When you run the debug script, you'll see output like:

```
============================================================
Testing Chat Completion
============================================================
Endpoint: https://my-resource.openai.azure.com/
Deployment: gpt-4
API Version: 2024-02-15-preview
Timeout: 60s

✓ Client initialized successfully
Sending test request...

❌ FAILED: APIConnectionError: Connection error.

------------------------------------------------------------
FULL STACK TRACE:
------------------------------------------------------------
Traceback (most recent call last):
  File "/usr/lib/python3.11/http/client.py", line 1374, in _send_output
    self.send(msg)
  File "/usr/lib/python3.11/http/client.py", line 1318, in send
    self.connect()
  File "/usr/lib/python3.11/http/client.py", line 1289, in connect
    self.sock = self._create_connection(
  File "/usr/lib/python3.11/socket.py", line 827, in create_connection
    raise err
  File "/usr/lib/python3.11/socket.py", line 814, in create_connection
    sock.connect(sa)
ConnectionRefusedError: [Errno 61] Connection refused

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "test_azure_debug.py", line 45, in test_completion
    response = await client.generate_completion(
  File "dev_agent/llm/azure_client.py", line 123, in generate_completion
    response = await self._call_completion_with_retry(
  File "dev_agent/llm/azure_client.py", line 178, in _call_completion_with_retry
    response = await self.client.chat.completions.create(
openai.APIConnectionError: Connection error.
------------------------------------------------------------
```

This shows you exactly where the error occurred and what the underlying cause is!
