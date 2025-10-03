# Azure OpenAI Integration

Dev-agent **requires** Azure OpenAI for all AI-powered features. This integration provides enterprise-grade AI capabilities using your organization's Azure OpenAI deployments.

## Overview

Azure OpenAI is the exclusive AI provider for dev-agent, providing:

- **AI-powered specification generation** using GPT-4
- **Intelligent design document creation** with architectural insights
- **Smart task breakdown** for implementation planning
- **Semantic code embeddings** using text-embedding-ada-002
- **Enterprise security** with your Azure OpenAI endpoints
- **Cost control** through your Azure billing and quotas

**Note**: Local model support has been removed. Azure OpenAI configuration is mandatory for all AI operations.

## Prerequisites (Required)

Before using dev-agent, you must have:

1. **Azure OpenAI Resource**: An Azure OpenAI resource deployed in your Azure subscription
2. **Required Model Deployments**:
   - **GPT-4** (or GPT-4 Turbo) - for code generation, specifications, and designs
   - **text-embedding-ada-002** - for code embeddings and similarity search
3. **API Access**: Your API key and endpoint URL from the Azure portal

Without these prerequisites, dev-agent will not function.

## Configuration

### Environment Variables

The easiest way to configure Azure OpenAI is through environment variables:

```bash
export AZURE_OPENAI_API_KEY="your-api-key-here"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_VERSION="2024-02-01"  # optional
export AZURE_OPENAI_CHAT_MODEL="gpt-4"        # your deployment name
export AZURE_OPENAI_EMBEDDING_MODEL="text-embedding-ada-002"  # your deployment name
```

### Interactive Configuration

Use the built-in configuration command for guided setup:

```bash
dev-agent azure configure
```

This will prompt you for all necessary configuration values and test the connection.

### Manual Configuration

You can also configure Azure OpenAI programmatically:

```python
from dev_agent.config.config_manager import ConfigManager, AzureOpenAIConfig

config_manager = ConfigManager()
config = config_manager.get_config()

# Configure Azure OpenAI
config.azure_openai = AzureOpenAIConfig(
    api_key="your-api-key",
    endpoint="https://your-resource.openai.azure.com/",
    api_version="2024-02-01",
    chat_model="gpt-4",
    embedding_model="text-embedding-ada-002",
    max_tokens=4000,
    temperature=0.1,
    timeout=60,
    max_retries=3,
)

# Enable Azure embeddings
config.indexing.use_azure_embeddings = True

config_manager.save_config(config)
```

## Usage

### CLI Commands

#### Configure Azure OpenAI
```bash
# Interactive configuration
dev-agent azure configure

# Non-interactive configuration
dev-agent azure configure --api-key "your-key" --endpoint "your-endpoint"
```

#### Test Connection
```bash
dev-agent azure test
```

#### Check Status
```bash
dev-agent azure status
```

#### List Available Models
```bash
dev-agent azure models
```

#### Show Environment Variables
```bash
dev-agent azure env
```

### AI-Powered Generation

Once configured, dev-agent automatically uses Azure OpenAI for enhanced generation:

```bash
# Initialize project with AI-powered analysis
dev-agent init /path/to/your/project

# Resume with AI-enhanced workflows
dev-agent resume /path/to/your/project
```

### Programmatic Usage

```python
from dev_agent.services.azure_openai_service import AzureOpenAIService
from dev_agent.config.config_manager import DevAgentConfig

# Initialize service
config = DevAgentConfig.default()  # Load from config
service = AzureOpenAIService(config.azure_openai)

# Chat completion
response = service.chat_completion([
    {"role": "system", "content": "You are a helpful coding assistant."},
    {"role": "user", "content": "Explain Python decorators."}
])
print(response.content)

# Generate embeddings
embeddings = service.generate_embeddings([
    "def hello_world(): print('Hello, World!')",
    "class MyClass: pass"
])
print(f"Generated {len(embeddings.embeddings)} embeddings")
```

### Async Operations

```python
import asyncio
from dev_agent.services.azure_openai_service import AzureOpenAIService

async def main():
    service = AzureOpenAIService(config.azure_openai)
    
    # Async chat completion
    response = await service.async_chat_completion([
        {"role": "user", "content": "What is async programming?"}
    ])
    
    # Async embeddings
    embeddings = await service.async_generate_embeddings([
        "async def example(): pass"
    ])

asyncio.run(main())
```

## Features

### AI-Powered Specification Generation

Generate comprehensive specifications from:
- Existing codebase analysis
- User requirements
- Interactive refinement

```python
from dev_agent.generation.generator_factory import GeneratorFactory

factory = GeneratorFactory(config)
spec_generator = factory.create_specification_generator()

# Generate from user requirements
requirements = [
    "Create a REST API for user management",
    "Support authentication and authorization",
    "Provide CRUD operations"
]
spec_doc = spec_generator.generate_from_user_input(requirements)
```

### Intelligent Design Generation

Create detailed technical designs:

```python
design_generator = factory.create_design_generator()
design_doc = design_generator.generate_from_specification(spec_doc, analysis)
```

### Smart Task Breakdown

Generate implementation tasks:

```python
task_generator = factory.create_task_generator()
task_list = task_generator.generate_from_design(design_doc)
```

### Enhanced Code Embeddings

Use Azure OpenAI embeddings for better code similarity:

```python
from dev_agent.indexing.enhanced_indexing_engine import create_indexing_engine

# Create enhanced indexing engine
engine = create_indexing_engine(project_path, config)

# Build index with Azure embeddings
result = engine.build_index()

# Query similar code
matches = engine.query_similar_code("user authentication function")
```

## Model Support

### Chat Models

Supported Azure OpenAI chat models:
- `gpt-4` - Most capable model
- `gpt-4-32k` - Extended context window
- `gpt-4-turbo` - Latest GPT-4 Turbo
- `gpt-35-turbo` - Cost-effective option
- `gpt-35-turbo-16k` - Extended context

### Embedding Models

Supported embedding models:
- `text-embedding-ada-002` - Most capable (1536 dimensions)
- `text-embedding-3-small` - Faster, smaller model
- `text-embedding-3-large` - Larger, more capable model

**Note**: Use your Azure deployment names, not the base model names.

## Configuration Options

### Azure OpenAI Settings

```python
AzureOpenAIConfig(
    api_key="your-api-key",           # Required
    endpoint="your-endpoint",         # Required
    api_version="2024-02-01",        # API version
    chat_model="gpt-4",              # Chat model deployment name
    embedding_model="text-embedding-ada-002",  # Embedding model deployment
    max_tokens=4000,                 # Maximum tokens per request
    temperature=0.1,                 # Sampling temperature (0.0-2.0)
    timeout=60,                      # Request timeout in seconds
    max_retries=3,                   # Maximum retry attempts
)
```

### Indexing Settings

```python
IndexingConfig(
    use_azure_embeddings=True,       # Enable Azure embeddings
    max_file_size_mb=10,            # Maximum file size to process
    chunk_size=1000,                # Code chunk size
    overlap_size=200,               # Chunk overlap
    max_files_per_batch=100,        # Batch processing size
)
```

## Error Handling

The Azure OpenAI integration includes comprehensive error handling:

- **Connection failures**: Clear error messages with resolution guidance
- **Rate limiting**: Exponential backoff with automatic retries
- **Token limits**: Automatic chunking for large inputs
- **Model unavailability**: Informative error messages

```python
from dev_agent.errors.exceptions import ConfigurationError, ServiceError

try:
    service = AzureOpenAIService(config.azure_openai)
    response = service.chat_completion(messages)
except ConfigurationError as e:
    print(f"Configuration error: {e}")
except ServiceError as e:
    print(f"Service error: {e}")
```

## Security Best Practices

1. **Environment Variables**: Store API keys in environment variables, not code
2. **Key Rotation**: Regularly rotate your Azure OpenAI API keys
3. **Network Security**: Use Azure Private Endpoints if available
4. **Access Control**: Implement proper RBAC in Azure
5. **Monitoring**: Monitor API usage and costs in Azure portal

## Troubleshooting

### Common Issues

#### Connection Errors
```bash
# Test connection
dev-agent azure test

# Check configuration
dev-agent azure status
```

#### Authentication Errors
- Verify API key is correct
- Check endpoint URL format
- Ensure API version is supported

#### Model Not Found
- Verify deployment names in Azure portal
- Check model availability in your region
- Ensure models are deployed and running

#### Rate Limiting
- Monitor usage in Azure portal
- Implement request throttling
- Consider upgrading quota limits

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
dev-agent --debug azure test
```

### Log Analysis

Check logs for detailed error information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Cost Management

### Token Usage Monitoring

Monitor token usage through:
- Azure portal metrics
- Response usage information
- Built-in logging

```python
response = service.chat_completion(messages)
print(f"Tokens used: {response.usage}")
```

### Cost Optimization

- Use appropriate models for tasks (GPT-3.5 for simple tasks)
- Implement caching for repeated queries
- Set reasonable token limits
- Monitor and alert on usage

## Examples

### Complete Integration Example

```python
import os
from dev_agent.config.config_manager import DevAgentConfig, AzureOpenAIConfig
from dev_agent.generation.generator_factory import GeneratorFactory
from dev_agent.indexing.enhanced_indexing_engine import create_indexing_engine

# Configure Azure OpenAI
config = DevAgentConfig.default()
config.azure_openai = AzureOpenAIConfig(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    chat_model="gpt-4",
    embedding_model="text-embedding-ada-002",
)
config.indexing.use_azure_embeddings = True

# Create AI-powered generators
factory = GeneratorFactory(config)
spec_generator = factory.create_specification_generator()

# Generate specification
requirements = ["Build a web API", "Support user authentication"]
spec = spec_generator.generate_from_user_input(requirements)

# Create enhanced indexing
engine = create_indexing_engine("/path/to/project", config)
result = engine.build_index()

print(f"Generated specification: {spec.title}")
print(f"Indexed {result.metadata['total_files']} files")
```

### Demo Script

Run the included demo script:

```bash
python examples/azure_openai_demo.py
```

This demonstrates all Azure OpenAI features with your configuration.

## Support

For issues with Azure OpenAI integration:

1. Check the [troubleshooting section](#troubleshooting)
2. Review Azure OpenAI service status
3. Verify your Azure subscription and quotas
4. Check dev-agent logs for detailed error information

For Azure OpenAI service issues, consult the [Azure OpenAI documentation](https://docs.microsoft.com/en-us/azure/cognitive-services/openai/).