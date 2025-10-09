# Environment Variables

This guide covers all environment variables used by dev-agent for configuration.

## Provider Selection

### LLM Provider Selection

```bash
# Choose which AI provider to use
PREFERRED_LLM_PROVIDER=azure    # Default: Azure OpenAI
PREFERRED_LLM_PROVIDER=gemini   # Alternative: Google Gemini
```

## Azure OpenAI Configuration

### Required Variables

```bash
# Azure OpenAI endpoint (required)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# Authentication (choose one)
AZURE_OPENAI_API_KEY=your-api-key-here              # API key authentication
AZURE_OPENAI_TOKEN=eyJ0eXAiOiJKV1Qi...              # Azure AD bearer token

# API version (required)
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Model deployments (required)
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4                  # Chat/completion model
AZURE_CHAT_DEPLOYMENT_NAME=gpt-4                    # Alternative alias
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

### Optional Variables

```bash
# Generation parameters
AZURE_OPENAI_MAX_TOKENS=4000                        # Default: 4000
AZURE_OPENAI_TEMPERATURE=0.7                        # Default: 0.7
AZURE_OPENAI_MAX_RETRIES=3                          # Default: 3
AZURE_OPENAI_TIMEOUT=60                             # Default: 60 seconds
AZURE_OPENAI_BATCH_SIZE=16                          # Default: 16

# Azure AD authentication (enterprise)
AZURE_OPENAI_USER_SID=A123456                       # User session ID
AZURE_OPENAI_CUSTOM_HEADERS='{"department": "engineering"}'  # JSON format
```

## Google Gemini Configuration

### Required Variables

```bash
# Gemini API key (required)
GEMINI_API_KEY=your-gemini-api-key-here
```

### Optional Variables

```bash
# Model selection
GEMINI_MODEL_NAME=gemini-pro                         # Default: gemini-pro
GEMINI_EMBEDDING_MODEL=embedding-001                 # Default: embedding-001

# API configuration
GEMINI_API_ENDPOINT=generativelanguage.googleapis.com  # Default endpoint

# Generation parameters
GEMINI_MAX_OUTPUT_TOKENS=2048                        # Default: 2048
GEMINI_TEMPERATURE=0.7                               # Default: 0.7
GEMINI_TOP_P=0.95                                    # Default: 0.95
GEMINI_TOP_K=40                                      # Default: 40

# Request configuration
GEMINI_MAX_RETRIES=3                                 # Default: 3
GEMINI_TIMEOUT=60                                    # Default: 60 seconds
GEMINI_BATCH_SIZE=16                                 # Default: 16

# Safety settings (JSON format)
GEMINI_SAFETY_SETTINGS='{"HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE"}'

# Custom headers (JSON format)
GEMINI_CUSTOM_HEADERS='{"project": "dev-agent", "environment": "production"}'
```

## Application Configuration

### Logging

```bash
# Logging level
DEV_AGENT_LOG_LEVEL=INFO                             # DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO                                       # Alternative name

# Log file location
DEV_AGENT_LOG_FILE=~/.dev_agent/logs/dev-agent.log

# Disable colored output
NO_COLOR=1                                           # Any value disables colors
```

### Paths and Directories

```bash
# Custom configuration file
DEV_AGENT_CONFIG_PATH=/path/to/config.toml

# Custom cache directory
DEV_AGENT_CACHE_DIR=~/.dev_agent/cache

# Custom data directory
DEV_AGENT_DATA_DIR=~/.dev_agent/data
```

### Performance

```bash
# Indexing configuration
DEV_AGENT_MAX_FILE_SIZE_MB=10                        # Default: 10MB
DEV_AGENT_MAX_FILES=10000                            # Default: 10,000 files
DEV_AGENT_PARALLEL_WORKERS=4                         # Default: CPU count

# Memory limits
DEV_AGENT_MAX_MEMORY_MB=2048                         # Default: 2GB
DEV_AGENT_EMBEDDING_CACHE_SIZE=1000                  # Default: 1000 entries
```

### Feature Flags

```bash
# Enable/disable features
DEV_AGENT_ENABLE_STREAMING=true                      # Default: true
DEV_AGENT_ENABLE_CACHING=true                        # Default: true
DEV_AGENT_ENABLE_TELEMETRY=false                     # Default: false

# Integration test flags
AZURE_OPENAI_INTEGRATION_TESTS=true                  # Enable Azure OpenAI integration tests
GEMINI_INTEGRATION_TESTS=true                        # Enable Gemini integration tests
```

## Environment File Setup

### .env File (Recommended)

Create a `.env` file in your project root:

```bash
# .env file for local development

# Provider selection
PREFERRED_LLM_PROVIDER=gemini

# Gemini configuration
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL_NAME=gemini-pro
GEMINI_EMBEDDING_MODEL=embedding-001
GEMINI_TEMPERATURE=0.7

# Azure OpenAI configuration (backup)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-azure-api-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Application settings
DEV_AGENT_LOG_LEVEL=INFO
DEV_AGENT_ENABLE_STREAMING=true
```

**Important**: Add `.env` to your `.gitignore` file to prevent committing secrets.

### Shell Profile Setup

Add to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
# dev-agent configuration
export PREFERRED_LLM_PROVIDER=gemini
export GEMINI_API_KEY="your-gemini-api-key-here"
export DEV_AGENT_LOG_LEVEL=INFO

# Load from .env file if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi
```

### Docker Environment

For Docker deployments:

```dockerfile
# Dockerfile
ENV PREFERRED_LLM_PROVIDER=gemini
ENV GEMINI_API_KEY=${GEMINI_API_KEY}
ENV DEV_AGENT_LOG_LEVEL=INFO
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  dev-agent:
    image: dev-agent:latest
    environment:
      - PREFERRED_LLM_PROVIDER=gemini
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - DEV_AGENT_LOG_LEVEL=INFO
    env_file:
      - .env
```

## Security Best Practices

### API Key Management

```bash
# ✅ Good: Use environment variables
export GEMINI_API_KEY="your-key-here"

# ❌ Bad: Hardcode in scripts
GEMINI_API_KEY="sk-1234567890abcdef"  # Never do this!

# ✅ Good: Use secret management
export GEMINI_API_KEY=$(aws secretsmanager get-secret-value --secret-id gemini-key --query SecretString --output text)
```

### Environment Separation

```bash
# Development environment
export DEV_AGENT_ENV=development
export GEMINI_API_KEY="dev-key-here"
export DEV_AGENT_LOG_LEVEL=DEBUG

# Production environment
export DEV_AGENT_ENV=production
export GEMINI_API_KEY="prod-key-here"
export DEV_AGENT_LOG_LEVEL=WARNING
```

### Validation

```bash
# Check required variables are set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "Error: GEMINI_API_KEY is not set"
    exit 1
fi

# Validate provider selection
if [ "$PREFERRED_LLM_PROVIDER" != "azure" ] && [ "$PREFERRED_LLM_PROVIDER" != "gemini" ]; then
    echo "Error: PREFERRED_LLM_PROVIDER must be 'azure' or 'gemini'"
    exit 1
fi
```

## Configuration Precedence

Environment variables are loaded in this order (later values override earlier ones):

1. **System environment variables**
2. **Shell profile** (`~/.bashrc`, `~/.zshrc`)
3. **Global .env file** (`~/.dev_agent/.env`)
4. **Project .env file** (`./env`)
5. **Command-line arguments** (`--provider gemini`)

## Troubleshooting

### Check Current Configuration

```bash
# Show all dev-agent related environment variables
env | grep -E "(DEV_AGENT|AZURE_OPENAI|GEMINI|PREFERRED_LLM)" | sort

# Check specific provider configuration
dev-agent status

# Test configuration
dev-agent config validate
```

### Common Issues

#### Variable Not Set
```bash
# Check if variable is set
echo $GEMINI_API_KEY

# Set temporarily
export GEMINI_API_KEY="your-key-here"

# Set permanently (add to shell profile)
echo 'export GEMINI_API_KEY="your-key-here"' >> ~/.bashrc
source ~/.bashrc
```

#### Wrong Provider Selected
```bash
# Check current provider
echo $PREFERRED_LLM_PROVIDER

# Override for single command
PREFERRED_LLM_PROVIDER=gemini dev-agent status

# Change default
export PREFERRED_LLM_PROVIDER=gemini
```

#### Configuration Conflicts
```bash
# Clear all dev-agent variables
unset $(env | grep -o '^[^=]*DEV_AGENT[^=]*')
unset $(env | grep -o '^[^=]*AZURE_OPENAI[^=]*')
unset $(env | grep -o '^[^=]*GEMINI[^=]*')

# Reload configuration
source ~/.bashrc
```

## Examples

### Multi-Environment Setup

```bash
# ~/.bashrc or ~/.zshrc

# Function to switch between environments
switch_env() {
    case $1 in
        "dev")
            export PREFERRED_LLM_PROVIDER=gemini
            export GEMINI_API_KEY="$GEMINI_DEV_KEY"
            export DEV_AGENT_LOG_LEVEL=DEBUG
            echo "Switched to development environment (Gemini)"
            ;;
        "prod")
            export PREFERRED_LLM_PROVIDER=azure
            export AZURE_OPENAI_API_KEY="$AZURE_PROD_KEY"
            export DEV_AGENT_LOG_LEVEL=WARNING
            echo "Switched to production environment (Azure OpenAI)"
            ;;
        *)
            echo "Usage: switch_env [dev|prod]"
            ;;
    esac
}

# Usage:
# switch_env dev   # Use Gemini for development
# switch_env prod  # Use Azure OpenAI for production
```

### CI/CD Configuration

```yaml
# GitHub Actions
name: Test dev-agent
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    env:
      PREFERRED_LLM_PROVIDER: gemini
      GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
      DEV_AGENT_LOG_LEVEL: DEBUG
      GEMINI_INTEGRATION_TESTS: true
    
    steps:
      - uses: actions/checkout@v4
      - name: Test dev-agent
        run: |
          uv run pytest tests/
```

## Next Steps

- [Provider Selection Guide](../usage/provider-selection.md) - Choose the right provider
- [Azure OpenAI Setup](azure-openai.md) - Detailed Azure configuration
- [Gemini Setup Guide](gemini-setup.md) - Detailed Gemini configuration
- [Security Best Practices](security.md) - Secure your configuration