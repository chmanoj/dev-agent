# Google Gemini API Setup

This guide walks you through setting up Google Gemini API integration with dev-agent as an alternative to Azure OpenAI.

## Prerequisites

- Google Cloud Platform account
- Access to Google AI Studio or Vertex AI
- Python 3.10 or higher
- dev-agent installed

## Getting Your Gemini API Key

### Option 1: Google AI Studio (Recommended for Development)

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Choose your Google Cloud project or create a new one
5. Copy the generated API key

### Option 2: Vertex AI (Recommended for Production)

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Vertex AI API for your project
3. Create a service account with Vertex AI permissions
4. Generate and download a service account key
5. Set up authentication using the service account

## Environment Configuration

### Basic Setup (API Key Authentication)

Create a `.env` file in your project root or set environment variables:

```bash
# Gemini API Configuration
GEMINI_API_KEY=your-api-key-here
GEMINI_MODEL_NAME=gemini-pro
GEMINI_EMBEDDING_MODEL=embedding-001

# Optional: Advanced Configuration
GEMINI_API_ENDPOINT=generativelanguage.googleapis.com
GEMINI_MAX_OUTPUT_TOKENS=2048
GEMINI_TEMPERATURE=0.7
GEMINI_TOP_P=0.95
GEMINI_TOP_K=40
GEMINI_MAX_RETRIES=3
GEMINI_TIMEOUT=60
GEMINI_BATCH_SIZE=16

# Provider Selection
PREFERRED_LLM_PROVIDER=gemini
```

### Advanced Configuration

For production environments, you can configure additional settings:

```bash
# Safety Settings (JSON format)
GEMINI_SAFETY_SETTINGS='{"HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE"}'

# Custom Request Headers
GEMINI_CUSTOM_HEADERS='{"project": "dev-agent", "environment": "production"}'
```

## Available Models

### Generation Models

| Model | Description | Context Window | Best For |
|-------|-------------|----------------|----------|
| `gemini-pro` | Balanced performance and cost | 32K tokens | General code generation |
| `gemini-pro-vision` | Multimodal with image support | 16K tokens | Code with visual context |
| `gemini-ultra` | Highest capability | 32K tokens | Complex code generation |

### Embedding Models

| Model | Description | Dimensions | Best For |
|-------|-------------|------------|----------|
| `embedding-001` | General text embeddings | 768 | Code similarity search |
| `text-embedding-004` | Latest embedding model | 768 | Improved semantic search |

## Verification

Test your configuration by running:

```bash
# Check provider status
dev-agent status

# Test with a simple generation
dev-agent generate --prompt "Create a hello world function"
```

You should see output indicating Gemini is the active provider:

```
✓ LLM Provider: Google Gemini (gemini-pro)
✓ Embedding Provider: Google Gemini (embedding-001)
✓ API Key: Configured
✓ Connection: Success
```

## Pricing and Quotas

### Gemini Pro Pricing (as of 2024)

- **Input tokens**: $0.00025 per 1K tokens
- **Output tokens**: $0.0005 per 1K tokens
- **Embeddings**: $0.0001 per 1K tokens

### Rate Limits

- **Requests per minute**: 60 (free tier), 1000+ (paid)
- **Tokens per minute**: 32,000 (free tier), 128,000+ (paid)
- **Requests per day**: 1,500 (free tier), unlimited (paid)

## Troubleshooting

### Common Issues

#### Authentication Errors

```
Error: Failed to authenticate with Google Gemini API
```

**Solutions:**
- Verify your API key is correct
- Check that the API key hasn't expired
- Ensure you have sufficient quota
- Verify the Generative AI API is enabled in your Google Cloud project

#### Rate Limit Errors

```
Error: Gemini rate limit exceeded
```

**Solutions:**
- Wait for the rate limit to reset
- Upgrade to a paid plan for higher limits
- Implement request batching
- Use caching to reduce API calls

#### Model Not Found

```
Error: Model 'gemini-pro' not found
```

**Solutions:**
- Check that you're using a valid model name
- Verify the model is available in your region
- Try using `gemini-pro` instead of `gemini-1.0-pro`

#### Connection Timeouts

```
Error: Request to Gemini API timed out
```

**Solutions:**
- Increase the timeout value: `GEMINI_TIMEOUT=120`
- Check your internet connection
- Try a different API endpoint if available

### Debug Mode

Enable debug logging to troubleshoot issues:

```bash
export LOG_LEVEL=DEBUG
dev-agent status
```

This will show detailed information about API calls and responses.

## Security Best Practices

### API Key Security

- **Never commit API keys** to version control
- **Use environment variables** or secure secret management
- **Rotate keys regularly** (every 90 days)
- **Restrict API key permissions** to only required services
- **Monitor API usage** for unusual activity

### Data Privacy

- **Review Google's data policies** for Gemini API
- **Understand data retention** and processing policies
- **Consider data residency** requirements for your organization
- **Implement audit logging** for compliance

### Production Deployment

- **Use service accounts** instead of personal API keys
- **Implement proper error handling** and retry logic
- **Set up monitoring** and alerting for API usage
- **Configure rate limiting** to prevent quota exhaustion

## Migration from Azure OpenAI

If you're migrating from Azure OpenAI, see the [Provider Selection Guide](../usage/provider-selection.md) for detailed instructions on switching providers and maintaining compatibility.

## Next Steps

- [Provider Selection Guide](../usage/provider-selection.md) - Learn how to choose between providers
- [Gemini Usage Examples](../examples/gemini-usage.md) - See practical examples
- [Cost Management](../usage/cost-management.md) - Monitor and optimize costs
- [API Reference](../api/llm.md) - Detailed API documentation