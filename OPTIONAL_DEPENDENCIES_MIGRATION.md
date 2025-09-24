# Optional Dependencies Migration

This document describes the changes made to make sentence-transformers an optional dependency and streamline the default installation to only require Azure OpenAI.

## Changes Made

### 1. Updated pyproject.toml
- **Removed** `sentence-transformers>=3.3.0` from core dependencies
- **Added** new optional dependency group `local-embeddings` containing sentence-transformers
- **Kept** `openai>=1.50.0` as a core dependency for Azure OpenAI support

### 2. Updated requirements.txt
- **Removed** sentence-transformers from core requirements
- **Added** comment explaining how to install local embeddings support
- **Updated** to match pyproject.toml dependencies

### 3. Updated Configuration Defaults
- **Changed** `IndexingConfig.use_azure_embeddings` default from `False` to `True`
- This makes Azure OpenAI the default embedding provider

### 4. Enhanced Error Messages
- **Updated** `AzureVectorDatabase` to provide helpful installation instructions when sentence-transformers is missing
- **Added** CLI warnings in `main.py` to inform users about configuration status and optional dependencies

### 5. Updated Documentation
- **Updated** README.md with new installation options
- **Updated** tech steering file to reflect the new dependency structure
- **Added** clear distinction between default and optional installations

### 6. Fixed Import Issues
- **Fixed** incorrect import of `CodeMatch` in `azure_vector_database.py`

## Installation Options

### Default Installation (Azure OpenAI only)
```bash
pip install dev-agent
```
- Requires Azure OpenAI configuration
- Smaller installation size
- No PyTorch/ML dependencies

### With Local Embeddings Support
```bash
pip install 'dev-agent[local-embeddings]'
```
- Includes sentence-transformers for offline usage
- Larger installation due to PyTorch dependencies
- Works without Azure OpenAI as fallback

### Development Installation
```bash
pip install -e '.[dev]'
# or with local embeddings
pip install -e '.[dev,local-embeddings]'
```

## User Experience Changes

### Before
- All users got sentence-transformers by default (large PyTorch dependency)
- Local embeddings were the default fallback
- Heavier installation for all users

### After
- Default installation is lightweight (Azure OpenAI only)
- Users can opt-in to local embeddings if needed
- Clear error messages guide users to the right installation
- CLI provides helpful warnings about configuration status

## Migration Guide for Users

### If you have Azure OpenAI configured:
- No changes needed
- Default installation will work fine
- Existing configurations continue to work

### If you need offline/local embeddings:
- Install with: `pip install 'dev-agent[local-embeddings]'`
- Or upgrade existing installation: `pip install --upgrade 'dev-agent[local-embeddings]'`

### If you're unsure:
- Try default installation first
- CLI will warn you if additional dependencies are needed
- Follow the installation instructions provided in error messages

## Benefits

1. **Smaller Default Installation**: Removes ~500MB+ of PyTorch dependencies for users who don't need local embeddings
2. **Clearer Intent**: Makes it obvious that Azure OpenAI is the primary/recommended approach
3. **Better User Experience**: Clear error messages and installation guidance
4. **Flexible**: Users can still get local embeddings when needed
5. **Modern Python Practices**: Uses optional dependencies as intended

## Testing

The changes have been tested to ensure:
- ✅ Core functionality imports without sentence-transformers
- ✅ Azure OpenAI service works correctly
- ✅ Graceful fallback with helpful error messages
- ✅ Optional dependency installation works
- ✅ Existing configurations continue to work