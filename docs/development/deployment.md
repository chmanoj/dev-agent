# Deployment Guide

## Overview

This guide covers deploying dev-agent for production use, including package distribution, environment setup, and operational considerations.

## Package Distribution

### PyPI Release

#### Prerequisites
- PyPI account with 2FA enabled
- API token for automated uploads
- Clean working directory (no uncommitted changes)

#### Release Process
```bash
# 1. Update version in pyproject.toml
# Edit pyproject.toml: version = "1.0.0"

# 2. Update CHANGELOG.md
# Document all changes in the new version

# 3. Commit version bump
git add pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to 1.0.0"

# 4. Create git tag
git tag -a v1.0.0 -m "Release version 1.0.0"

# 5. Build package
uv build

# 6. Upload to PyPI
uv publish

# 7. Push changes and tags
git push origin main --tags
```

#### Automated Release (GitHub Actions)
Create a release on GitHub to trigger automated PyPI upload:

```bash
# Create release via GitHub CLI
gh release create v1.0.0 \
  --title "Release v1.0.0" \
  --notes "See CHANGELOG.md for details"
```

### Installation Methods

#### From PyPI (Recommended)
```bash
# Install latest version
pip install dev-agent

# Install specific version
pip install dev-agent==1.0.0

# Install with uv (faster)
uv pip install dev-agent
```

#### From Source
```bash
# Clone repository
git clone https://github.com/dev-agent/dev-agent.git
cd dev-agent

# Install in development mode
uv sync --dev

# Or with pip
pip install -e .
```

## Environment Setup

### Production Environment

#### Azure OpenAI Configuration
```bash
# Required environment variables
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_OPENAI_API_VERSION="2024-02-15-preview"
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-ada-002"

# Optional configuration
export AZURE_OPENAI_MAX_TOKENS="4000"
export AZURE_OPENAI_TEMPERATURE="0.7"
export AZURE_OPENAI_MAX_RETRIES="3"
export AZURE_OPENAI_TIMEOUT="60"
```

#### Using .env Files
```bash
# Create .env file (DO NOT commit to git)
cat > .env << EOF
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
EOF

# Load environment variables
source .env
```

### Docker Deployment

#### Dockerfile
```dockerfile
FROM python:3.11-slim

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./
COPY dev_agent ./dev_agent

# Install dependencies
RUN uv sync --no-dev

# Set environment variables (override at runtime)
ENV AZURE_OPENAI_ENDPOINT=""
ENV AZURE_OPENAI_API_KEY=""
ENV AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"
ENV AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-ada-002"

# Run CLI
ENTRYPOINT ["uv", "run", "dev-agent"]
```

#### Build and Run
```bash
# Build image
docker build -t dev-agent:latest .

# Run container
docker run -it \
  -e AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
  -e AZURE_OPENAI_API_KEY="$AZURE_OPENAI_API_KEY" \
  -v $(pwd):/workspace \
  dev-agent:latest init /workspace
```

### Azure Container Instances

#### Deploy to ACI
```bash
# Create resource group
az group create --name dev-agent-rg --location eastus

# Create container instance
az container create \
  --resource-group dev-agent-rg \
  --name dev-agent \
  --image dev-agent:latest \
  --environment-variables \
    AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
    AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4" \
  --secure-environment-variables \
    AZURE_OPENAI_API_KEY="$AZURE_OPENAI_API_KEY" \
  --cpu 2 \
  --memory 4
```

## Security Considerations

### API Key Management

#### Azure Key Vault
```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Get API key from Key Vault
credential = DefaultAzureCredential()
client = SecretClient(
    vault_url="https://your-keyvault.vault.azure.net/",
    credential=credential
)
api_key = client.get_secret("azure-openai-api-key").value
```

#### Environment-Specific Keys
```bash
# Development
export AZURE_OPENAI_API_KEY="dev-key"

# Staging
export AZURE_OPENAI_API_KEY="staging-key"

# Production
export AZURE_OPENAI_API_KEY="prod-key"
```

### Network Security
- Use private endpoints for Azure OpenAI
- Restrict API access by IP address
- Enable Azure OpenAI firewall rules
- Use VNet integration for container deployments

### Compliance
- Enable Azure OpenAI audit logging
- Implement data retention policies
- Follow organizational security policies
- Regular security audits

## Monitoring and Logging

### Application Logging
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/dev-agent/app.log'),
        logging.StreamHandler()
    ]
)
```

### Cost Tracking
```bash
# Generate cost report
dev-agent cost-report --export costs.json

# Monitor token usage
dev-agent status --detailed
```

### Azure Monitor Integration
```python
from azure.monitor.opentelemetry import configure_azure_monitor

# Enable Azure Monitor
configure_azure_monitor(
    connection_string="InstrumentationKey=your-key"
)
```

## Performance Optimization

### Caching Strategy
```bash
# Enable embedding cache
export DEV_AGENT_CACHE_DIR="/var/cache/dev-agent"

# Set cache size limit
export DEV_AGENT_CACHE_SIZE_MB="1000"
```

### Resource Limits
```bash
# Set memory limits
export DEV_AGENT_MAX_MEMORY_MB="2048"

# Set concurrent requests
export DEV_AGENT_MAX_CONCURRENT_REQUESTS="5"
```

## Backup and Recovery

### State Backup
```bash
# Backup project state
cp -r .dev_agent .dev_agent.backup

# Restore from backup
cp -r .dev_agent.backup .dev_agent
```

### Automated Backups
```bash
# Cron job for daily backups
0 2 * * * tar -czf /backups/dev-agent-$(date +\%Y\%m\%d).tar.gz .dev_agent
```

## Troubleshooting

### Common Issues

#### API Connection Failures
```bash
# Test Azure OpenAI connectivity
dev-agent validate

# Check environment variables
env | grep AZURE_OPENAI
```

#### Performance Issues
```bash
# Check cache status
ls -lh .dev_agent/embedding_cache/

# Clear cache if needed
rm -rf .dev_agent/embedding_cache/*
```

#### Memory Issues
```bash
# Monitor memory usage
dev-agent status --detailed

# Reduce batch size
export AZURE_OPENAI_BATCH_SIZE="8"
```

## Maintenance

### Regular Tasks
- Rotate Azure OpenAI API keys (every 90 days)
- Update dependencies monthly
- Review and clean embedding cache
- Monitor API usage and costs
- Update documentation

### Health Checks
```bash
# Validate configuration
dev-agent validate

# Test API connectivity
dev-agent audit

# Check system status
dev-agent status
```

## Scaling Considerations

### Horizontal Scaling
- Use shared state storage (Azure Blob Storage)
- Implement distributed caching (Redis)
- Load balance across multiple instances

### Vertical Scaling
- Increase memory for large codebases
- Use faster storage for embedding cache
- Optimize batch sizes for throughput

## Related Documentation

- [Configuration](../configuration/azure-openai.md) - Azure OpenAI setup
- [Security](../configuration/troubleshooting.md) - Security best practices
- [Architecture](architecture.md) - System design
