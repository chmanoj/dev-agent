# Quick Start: Using dev-agent with Google Gemini

This guide shows you how to use dev-agent with Google Gemini instead of Azure OpenAI.

## Prerequisites

1. Get a Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Your API key should start with "AI" (e.g., `AIzaSy...`)

## Setup

### 1. Set Environment Variables

```bash
# Required
export GEMINI_API_KEY="AIzaSy..."  # Your actual Gemini API key
export PREFERRED_LLM_PROVIDER="gemini"

# Optional (with defaults shown)
export GEMINI_MODEL_NAME="gemini-pro"
export GEMINI_EMBEDDING_MODEL="embedding-001"
export GEMINI_MAX_OUTPUT_TOKENS="2048"
export GEMINI_TEMPERATURE="0.7"
```

### 2. Initialize Your Project

```bash
# Navigate to your project directory
cd /path/to/your/project

# Initialize dev-agent
uv run dev-agent init .
```

That's it! dev-agent will now use Gemini for all AI operations.

## Supported Models

### Generation Models
- `gemini-2.5-flash-lite` - Fast, lightweight model
- `gemini-2.5-flash` - Balanced performance and speed
- `gemini-2.5-pro` - Most capable model

### Embedding Models
- `gemini-embedding-001` - Standard embedding model (768 dimensions)

## Configuration Options

All Gemini configuration is done via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Your Gemini API key (required) | - |
| `GEMINI_MODEL_NAME` | Model for code generation | `gemini-pro` |
| `GEMINI_EMBEDDING_MODEL` | Model for embeddings | `embedding-001` |
| `GEMINI_API_ENDPOINT` | API endpoint | `generativelanguage.googleapis.com` |
| `GEMINI_MAX_OUTPUT_TOKENS` | Max tokens for generation | `2048` |
| `GEMINI_TEMPERATURE` | Sampling temperature (0.0-2.0) | `0.7` |
| `GEMINI_TOP_P` | Nucleus sampling (0.0-1.0) | `0.95` |
| `GEMINI_TOP_K` | Top-k sampling (1-100) | `40` |
| `GEMINI_MAX_RETRIES` | Max retry attempts | `3` |
| `GEMINI_TIMEOUT` | Request timeout (seconds) | `60` |
| `GEMINI_BATCH_SIZE` | Batch size for embeddings | `16` |

## Troubleshooting

### "Invalid Gemini API key format"
- Ensure your API key starts with "AI"
- Verify you copied the complete key from Google AI Studio
- Check for extra spaces or quotes in the environment variable

### "Unsupported Gemini model"
- Use one of the supported models listed above
- Check for typos in the model name
- Ensure you're using the latest version of dev-agent

### "No valid LLM provider configuration found"
- Verify `GEMINI_API_KEY` is set correctly
- Check that `PREFERRED_LLM_PROVIDER` is set to "gemini"
- Try running: `echo $GEMINI_API_KEY` to verify the variable is set

## Switching Between Providers

You can switch between Gemini and Azure OpenAI by changing the `PREFERRED_LLM_PROVIDER` variable:

```bash
# Use Gemini
export PREFERRED_LLM_PROVIDER="gemini"

# Use Azure OpenAI
export PREFERRED_LLM_PROVIDER="azure_openai"
```

If both providers are configured, dev-agent will use the one specified in `PREFERRED_LLM_PROVIDER`.

## Example: Complete Setup

```bash
# 1. Set up Gemini
export GEMINI_API_KEY="AIzaSyYourActualKeyHere"
export PREFERRED_LLM_PROVIDER="gemini"
export GEMINI_MODEL_NAME="gemini-2.5-flash"

# 2. Initialize project
cd ~/my-python-project
uv run dev-agent init .

# 3. Start interactive mode
uv run dev-agent
```

## Getting Help

- Check the [main README](README.md) for general dev-agent usage
- See [GEMINI_PROVIDER_FIX.md](GEMINI_PROVIDER_FIX.md) for technical details
- Report issues on GitHub

## Cost Considerations

Gemini pricing is different from Azure OpenAI:
- Check current pricing at [Google AI Pricing](https://ai.google.dev/pricing)
- Gemini typically offers generous free tier
- Monitor your usage in Google AI Studio

Happy coding with Gemini! 🚀
