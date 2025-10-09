# Gemini Provider Configuration Fix

## Issue
When using Gemini as the LLM provider, the CLI initialization failed with:
```
AttributeError: 'NoneType' object has no attribute 'api_key'
```

This occurred because the configuration check in `dev_agent/cli/main.py` was hardcoded to check for Azure OpenAI configuration without considering that the user might be using Gemini.

## Root Cause
The `_check_configuration_and_offer_setup()` function in `main.py` was directly accessing `config.azure_openai.api_key` without first checking:
1. Which LLM provider the user has configured
2. Whether `config.azure_openai` is `None` (which it is when using Gemini)

## Solution
Modified the configuration check to be provider-aware:

1. **Added provider detection**: Check which LLM provider is configured using `config_manager.get_llm_provider()`
2. **Provider-specific validation**: If Gemini is configured and valid, skip Azure OpenAI setup
3. **Graceful fallback**: If no provider is configured, offer the setup wizard
4. **Fixed typo**: Corrected missing comma in Gemini supported models list

## Changes Made

### 1. `dev_agent/cli/main.py`
- Added import for `LLMProvider` enum
- Modified `_check_configuration_and_offer_setup()` to:
  - Detect the configured LLM provider
  - Return `True` immediately if Gemini is configured
  - Only check Azure OpenAI configuration if it's the selected provider
  - Handle cases where `config.azure_openai` is `None`
- Modified `_check_configuration_and_warn()` to:
  - Detect the configured LLM provider
  - Return early if Gemini is configured (no warning needed)
  - Only warn about Azure OpenAI if it's the selected provider
  - Handle cases where `config.azure_openai` is `None`

### 2. `dev_agent/models/llm_config.py`
- Fixed typo in `GeminiConfig.validate_model_name()`: Added missing comma in supported models set

## Testing
To test with Gemini provider:

```bash
export GEMINI_API_KEY=AIza...  # Your actual Gemini API key
export GEMINI_MODEL_NAME=gemini-2.5-flash
export GEMINI_EMBEDDING_MODEL=gemini-embedding-001
export PREFERRED_LLM_PROVIDER=gemini

uv run dev-agent init ../your-project/
```

## Supported Gemini Models
- **Generation**: `gemini-2.5-flash-lite`, `gemini-2.5-flash`, `gemini-2.5-pro`
- **Embeddings**: `gemini-embedding-001`

## Environment Variables for Gemini
```bash
# Required
GEMINI_API_KEY=AIza...  # Get from https://makersuite.google.com/app/apikey
PREFERRED_LLM_PROVIDER=gemini

# Optional (with defaults)
GEMINI_MODEL_NAME=gemini-pro
GEMINI_EMBEDDING_MODEL=embedding-001
GEMINI_API_ENDPOINT=generativelanguage.googleapis.com
GEMINI_MAX_OUTPUT_TOKENS=2048
GEMINI_TEMPERATURE=0.7
GEMINI_TOP_P=0.95
GEMINI_TOP_K=40
GEMINI_MAX_RETRIES=3
GEMINI_TIMEOUT=60
GEMINI_BATCH_SIZE=16
```

## Notes
- Gemini API keys must start with "AI" and be at least 20 characters long
- The fix maintains backward compatibility with Azure OpenAI
- If both providers are configured, `PREFERRED_LLM_PROVIDER` determines which is used
- The system will attempt to fall back to the other provider if the preferred one is not configured

## Verification
The fix has been tested and verified to work correctly:
- ✅ Configuration loads successfully with Gemini provider
- ✅ Provider detection works correctly
- ✅ No errors when `config.azure_openai` is `None`
- ✅ Existing tests pass
- ✅ Backward compatibility with Azure OpenAI maintained

Run `python test_gemini_provider_fix.py` to verify the fix on your system.
