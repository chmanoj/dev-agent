# Azure OpenAI Configuration Fix

## Problem

When running `uv run dev-agent init`, users encountered an error:
```
IndexingError: embedding_client is required
at cli/main.py line 167 _run_indexing_with_progress
```

## Root Cause

The code was attempting to initialize the Azure OpenAI embedding client, but when it failed (due to missing configuration), it only logged a warning and continued with `embedding_client=None`. This caused a downstream error in `VectorDatabase.__init__()` which requires a non-None embedding client.

## Solution

Modified `dev_agent/cli/main.py` in the `_run_indexing_with_progress` function to:

1. **Check if Azure OpenAI is configured** before attempting to create the embedding client
2. **Display a clear error message** with actionable steps if configuration is missing
3. **Exit gracefully** with proper error handling instead of continuing with None

## Changes Made

### File: `dev_agent/cli/main.py`

**Before:**
```python
embedding_client = None
try:
    from dev_agent.llm.azure_client import AzureEmbeddingClient
    config = config_manager.get_config()
    if config.azure_openai:
        embedding_client = AzureEmbeddingClient(config.azure_openai)
except Exception as e:
    if logger:
        logger.warning(f"Could not initialize embedding client: {e}")
```

**After:**
```python
embedding_client = None
try:
    from dev_agent.llm.azure_client import AzureEmbeddingClient
    from dev_agent.errors.exceptions import IndexingError
    
    config = config_manager.get_config()
    
    # Check if Azure OpenAI is configured
    if not config.azure_openai:
        console.print()
        console.print(Panel(
            "[red]Azure OpenAI is not configured.[/red]\n\n"
            "dev-agent requires Azure OpenAI for embeddings generation.\n\n"
            "Please configure Azure OpenAI first:\n"
            "  [cyan]dev-agent azure configure[/cyan]\n\n"
            "Or set environment variables:\n"
            "  [cyan]AZURE_OPENAI_ENDPOINT[/cyan]\n"
            "  [cyan]AZURE_OPENAI_API_KEY[/cyan]\n"
            "  [cyan]AZURE_OPENAI_DEPLOYMENT_NAME[/cyan]\n"
            "  [cyan]AZURE_OPENAI_EMBEDDING_DEPLOYMENT[/cyan]",
            title="❌ Configuration Required",
            border_style="red"
        ))
        raise typer.Exit(1)
    
    embedding_client = AzureEmbeddingClient(config.azure_openai)
    
except typer.Exit:
    raise
except Exception as e:
    console.print()
    console.print(Panel(
        f"[red]Failed to initialize Azure OpenAI embedding client:[/red]\n\n"
        f"{e}\n\n"
        "Please verify your Azure OpenAI configuration:\n"
        "  [cyan]dev-agent azure status[/cyan]\n\n"
        "Test your connection:\n"
        "  [cyan]dev-agent azure test[/cyan]\n\n"
        "Reconfigure if needed:\n"
        "  [cyan]dev-agent azure configure[/cyan]",
        title="❌ Initialization Failed",
        border_style="red"
    ))
    if logger:
        logger.error(f"Could not initialize embedding client: {e}", exc_info=True)
    raise typer.Exit(1)
```

## How to Configure Azure OpenAI

Users now have **two options** to configure Azure OpenAI:

### Option 1: Interactive Configuration (Recommended)
```bash
uv run dev-agent azure configure
```

This will:
- Guide you through entering your Azure OpenAI credentials
- Validate the configuration
- Optionally test the connection
- Save to `~/.dev_agent/dev_agent_config.json`

### Option 2: Environment Variables
Set these environment variables (highest precedence):

```bash
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_KEY="your-api-key-here"
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-ada-002"

# Optional
export AZURE_OPENAI_API_VERSION="2024-02-15-preview"
export AZURE_OPENAI_MAX_TOKENS="4000"
export AZURE_OPENAI_TEMPERATURE="0.7"
```

### Option 3: Manual Config File Edit
Edit `~/.dev_agent/dev_agent_config.json`:

```json
{
  "azure_openai": {
    "endpoint": "https://your-resource.openai.azure.com/",
    "api_key": "your-api-key-here",
    "api_version": "2024-02-15-preview",
    "deployment_name": "gpt-4",
    "embedding_deployment": "text-embedding-ada-002",
    "max_tokens": 4000,
    "temperature": 0.7,
    "max_retries": 3,
    "timeout": 60,
    "batch_size": 16
  },
  "indexing": {
    "use_azure_embeddings": true
  }
}
```

## Configuration Precedence

The system loads configuration in this order (highest to lowest):
1. **Environment variables** (highest priority)
2. Project-specific config file (`.dev_agent/config.json`)
3. Global config file (`~/.dev_agent/dev_agent_config.json`)
4. Default values (lowest priority)

## Verification Commands

After configuration, verify with:

```bash
# Check configuration status
uv run dev-agent azure status

# Test Azure OpenAI connection
uv run dev-agent azure test

# View environment variables
uv run dev-agent azure env
```

## User Experience Improvements

The fix provides:
- ✅ Clear error messages with actionable steps
- ✅ Helpful guidance on how to configure Azure OpenAI
- ✅ Multiple configuration options (interactive, env vars, manual)
- ✅ Proper error handling and graceful exit
- ✅ Better logging for debugging

## Testing

To test the fix:

1. **Without configuration:**
   ```bash
   # Should show clear error message
   uv run dev-agent init
   ```

2. **With configuration:**
   ```bash
   # Configure first
   uv run dev-agent azure configure
   
   # Then initialize
   uv run dev-agent init
   ```

3. **With environment variables:**
   ```bash
   export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
   export AZURE_OPENAI_API_KEY="your-key"
   export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"
   export AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-ada-002"
   
   uv run dev-agent init
   ```
