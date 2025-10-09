# Provider Selection Guide

dev-agent supports multiple AI providers, allowing you to choose the best option for your needs. This guide explains how to select, configure, and switch between providers.

## Supported Providers

### Azure OpenAI (Default)

- **Models**: GPT-4, GPT-4 Turbo, GPT-4o, GPT-3.5 Turbo
- **Embeddings**: text-embedding-ada-002 (1536 dimensions)
- **Best For**: Enterprise environments, Azure infrastructure, compliance requirements
- **Authentication**: API key or Azure AD bearer token

### Google Gemini

- **Models**: Gemini Pro, Gemini Pro Vision, Gemini Ultra
- **Embeddings**: embedding-001, text-embedding-004 (768 dimensions)
- **Best For**: Cost optimization, Google Cloud environments, multimodal capabilities
- **Authentication**: API key

## Provider Selection Methods

### 1. Environment Variable (Recommended)

Set the `PREFERRED_LLM_PROVIDER` environment variable:

```bash
# Use Azure OpenAI (default)
export PREFERRED_LLM_PROVIDER=azure

# Use Google Gemini
export PREFERRED_LLM_PROVIDER=gemini
```

### 2. Configuration File

Create a `.env` file in your project root:

```bash
# .env file
PREFERRED_LLM_PROVIDER=gemini
```

### 3. Runtime Selection

Some CLI commands support provider selection:

```bash
# Use specific provider for a command
dev-agent generate --provider gemini --prompt "Create a function"

# Check current provider
dev-agent status
```

## Configuration Requirements

### Azure OpenAI Configuration

```bash
# Required
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Optional
AZURE_OPENAI_MAX_TOKENS=4000
AZURE_OPENAI_TEMPERATURE=0.7
AZURE_OPENAI_MAX_RETRIES=3
AZURE_OPENAI_TIMEOUT=60
```

### Gemini Configuration

```bash
# Required
GEMINI_API_KEY=your-api-key-here

# Optional
GEMINI_MODEL_NAME=gemini-pro
GEMINI_EMBEDDING_MODEL=embedding-001
GEMINI_MAX_OUTPUT_TOKENS=2048
GEMINI_TEMPERATURE=0.7
GEMINI_TOP_P=0.95
GEMINI_TOP_K=40
GEMINI_MAX_RETRIES=3
GEMINI_TIMEOUT=60
```

## Provider Comparison

### Performance Comparison

| Feature | Azure OpenAI | Google Gemini |
|---------|--------------|---------------|
| **Code Generation** | Excellent (GPT-4) | Excellent (Gemini Pro) |
| **Code Understanding** | Excellent | Very Good |
| **Context Window** | 128K tokens (GPT-4 Turbo) | 32K tokens (Gemini Pro) |
| **Response Speed** | 1-3 seconds | 1-2 seconds |
| **Streaming Support** | Yes | Yes |
| **Multimodal** | GPT-4 Vision | Gemini Pro Vision |

### Cost Comparison (Approximate)

| Operation | Azure OpenAI | Google Gemini | Savings |
|-----------|--------------|---------------|---------|
| **Input Tokens** (1K) | $0.01 | $0.00025 | 97.5% |
| **Output Tokens** (1K) | $0.03 | $0.0005 | 98.3% |
| **Embeddings** (1K) | $0.0001 | $0.0001 | 0% |

*Note: Prices vary by model and region. Check current pricing.*

### Feature Comparison

| Feature | Azure OpenAI | Google Gemini |
|---------|--------------|---------------|
| **Enterprise Auth** | Azure AD | Google Cloud IAM |
| **Data Residency** | Azure regions | Google Cloud regions |
| **Compliance** | SOC 2, HIPAA, etc. | SOC 2, ISO 27001, etc. |
| **Rate Limits** | High (paid) | Moderate (free tier) |
| **Model Variety** | GPT family | Gemini family |

## Switching Providers

### From Azure OpenAI to Gemini

1. **Get Gemini API Key**:
   ```bash
   # Visit https://makersuite.google.com/app/apikey
   export GEMINI_API_KEY=your-gemini-key
   ```

2. **Set Provider Preference**:
   ```bash
   export PREFERRED_LLM_PROVIDER=gemini
   ```

3. **Verify Configuration**:
   ```bash
   dev-agent status
   ```

4. **Test Generation**:
   ```bash
   dev-agent generate --prompt "Hello world function"
   ```

### From Gemini to Azure OpenAI

1. **Configure Azure OpenAI**:
   ```bash
   export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   export AZURE_OPENAI_API_KEY=your-azure-key
   export AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
   export AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
   ```

2. **Set Provider Preference**:
   ```bash
   export PREFERRED_LLM_PROVIDER=azure
   ```

3. **Verify and Test**:
   ```bash
   dev-agent status
   dev-agent generate --prompt "Hello world function"
   ```

## Multi-Provider Setup

You can configure both providers and switch between them:

```bash
# Azure OpenAI Configuration
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
export AZURE_OPENAI_API_KEY=your-azure-key
export AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Gemini Configuration
export GEMINI_API_KEY=your-gemini-key
export GEMINI_MODEL_NAME=gemini-pro
export GEMINI_EMBEDDING_MODEL=embedding-001

# Switch providers as needed
export PREFERRED_LLM_PROVIDER=gemini  # or azure
```

## Provider-Specific Considerations

### Azure OpenAI

**Advantages:**
- Enterprise-grade security and compliance
- Integration with existing Azure infrastructure
- Azure AD authentication support
- Consistent performance and availability
- Larger context windows (GPT-4 Turbo)

**Considerations:**
- Higher cost per token
- Requires Azure subscription
- Regional availability limitations
- Deployment management overhead

**Best For:**
- Enterprise environments
- Compliance-sensitive applications
- Large context requirements
- Azure-native architectures

### Google Gemini

**Advantages:**
- Significantly lower cost per token
- Fast response times
- Multimodal capabilities (vision)
- Simple API key authentication
- Good performance for code tasks

**Considerations:**
- Smaller context window
- Rate limits on free tier
- Newer API (less mature ecosystem)
- Different data processing policies

**Best For:**
- Cost-sensitive applications
- High-volume usage
- Multimodal requirements
- Google Cloud environments

## Embedding Compatibility

### Vector Database Considerations

Both providers generate embeddings with different dimensions:

- **Azure OpenAI**: 1536 dimensions (text-embedding-ada-002)
- **Gemini**: 768 dimensions (embedding-001, text-embedding-004)

**Important**: You cannot mix embeddings from different providers in the same vector database. When switching providers, you'll need to:

1. **Clear existing embeddings**:
   ```bash
   rm -rf .dev_agent/embedding_cache/
   ```

2. **Re-index your codebase**:
   ```bash
   dev-agent init --force
   ```

### Migration Strategy

For large codebases, consider a gradual migration:

1. **Test with small projects** first
2. **Compare results** between providers
3. **Benchmark performance** and cost
4. **Plan re-indexing** during low-usage periods

## Troubleshooting

### Provider Detection Issues

```bash
# Check which provider is active
dev-agent status

# Force provider selection
export PREFERRED_LLM_PROVIDER=gemini
dev-agent status
```

### Configuration Conflicts

```bash
# Clear environment and restart
unset PREFERRED_LLM_PROVIDER
export PREFERRED_LLM_PROVIDER=azure
dev-agent status
```

### Embedding Dimension Mismatch

```
Error: Embedding dimension mismatch (expected 1536, got 768)
```

**Solution**: Clear embedding cache and re-index:
```bash
rm -rf .dev_agent/embedding_cache/
dev-agent init --force
```

## Best Practices

### Development Workflow

1. **Use Gemini for development** (lower cost)
2. **Use Azure OpenAI for production** (enterprise features)
3. **Test with both providers** to ensure compatibility
4. **Monitor costs** across providers

### Cost Optimization

1. **Choose appropriate models** for task complexity
2. **Use caching** to reduce API calls
3. **Batch operations** when possible
4. **Monitor token usage** regularly

### Security

1. **Never commit API keys** to version control
2. **Use environment variables** for configuration
3. **Rotate keys regularly**
4. **Monitor API usage** for anomalies

## Next Steps

- [Gemini Setup Guide](../configuration/gemini-setup.md) - Detailed Gemini configuration
- [Cost Management](cost-management.md) - Monitor and optimize costs
- [Gemini Examples](../examples/gemini-usage.md) - Practical usage examples
- [API Reference](../api/llm.md) - Technical documentation