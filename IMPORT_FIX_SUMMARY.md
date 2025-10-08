# Import Fix Summary

## Issue
When running `uv run dev-agent init`, the application failed with the error:
```
Could not initialize embedding client: cannot import name 'AzureEmbeddingClient' from 'dev_agent.llm.azure_client'
```

## Root Cause
Two files had incorrect imports attempting to import `AzureEmbeddingClient` from the wrong module:

1. **dev_agent/cli/main.py** (line 179)
2. **dev_agent/audit/audit_engine.py** (line 230)

Both files were trying to import:
```python
from dev_agent.llm.azure_client import AzureEmbeddingClient
```

However, `AzureEmbeddingClient` is actually defined in `dev_agent.llm.embeddings`, not in `dev_agent.llm.azure_client`.

## Solution
Fixed the incorrect imports in both files:

### 1. dev_agent/cli/main.py
**Before:**
```python
from dev_agent.llm.azure_client import AzureEmbeddingClient
```

**After:**
```python
from dev_agent.llm.embeddings import AzureEmbeddingClient
```

### 2. dev_agent/audit/audit_engine.py
**Before:**
```python
from dev_agent.llm.azure_client import AzureEmbeddingClient
```

**After:**
```python
from dev_agent.llm.embeddings import AzureEmbeddingClient
```

### 3. Enhanced dev_agent/llm/__init__.py
Also updated the LLM module's `__init__.py` to export both client classes for easier imports:

```python
from dev_agent.llm.azure_client import AzureOpenAIClient
from dev_agent.llm.base import IEmbeddingClient, ILLMClient
from dev_agent.llm.embeddings import AzureEmbeddingClient

__all__ = [
    "ILLMClient",
    "IEmbeddingClient",
    "AzureOpenAIClient",
    "AzureEmbeddingClient",
]
```

This allows for cleaner imports like:
```python
from dev_agent.llm import AzureEmbeddingClient, AzureOpenAIClient
```

## Module Structure
The correct module structure is:

```
dev_agent/llm/
├── __init__.py              # Exports both client classes
├── base.py                  # Abstract interfaces (ILLMClient, IEmbeddingClient)
├── azure_client.py          # AzureOpenAIClient (for completions)
├── embeddings.py            # AzureEmbeddingClient (for embeddings)
├── token_counter.py         # Token counting utilities
└── embedding_cache.py       # Embedding cache implementation
```

## Verification
The fix was verified by:
1. Running diagnostics on both modified files (no errors)
2. Testing the import directly: `uv run python -c "from dev_agent.llm.embeddings import AzureEmbeddingClient; print('✓ Import successful')"`

## Impact
This fix resolves the initialization error and allows `dev-agent init` to proceed correctly with Azure OpenAI embedding client initialization.

## Files Modified
- `dev_agent/cli/main.py`
- `dev_agent/audit/audit_engine.py`
- `dev_agent/llm/__init__.py`
