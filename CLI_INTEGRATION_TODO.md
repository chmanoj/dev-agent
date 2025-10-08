# CLI Integration TODO

## Overview
The core fixes are complete, but the CLI needs to be updated to pass `embedding_client` to `WorkflowManager`.

## Files to Update

### 1. dev_agent/cli/main.py (4 locations)

#### Location 1: Around line 489
```python
# BEFORE:
cli = EnhancedCLI()
workflow_manager = WorkflowManager(cli)
cli.workflow_manager = workflow_manager

# AFTER:
cli = EnhancedCLI()

# Initialize embedding client
from dev_agent.llm.embeddings import AzureEmbeddingClient
config = config_manager.get_config()
embedding_client = AzureEmbeddingClient(config.azure_openai) if config.azure_openai else None

workflow_manager = WorkflowManager(cli, embedding_client=embedding_client)
cli.workflow_manager = workflow_manager
```

#### Location 2: Around line 642
Same pattern as Location 1

#### Location 3: Around line 1522
Same pattern as Location 1

#### Location 4: Around line 1818
Same pattern as Location 1

### 2. dev_agent/cli/interactive_cli.py (1 location)

#### Around line 38
```python
# BEFORE:
self.workflow_manager = WorkflowManager(self)

# AFTER:
from dev_agent.llm.embeddings import AzureEmbeddingClient
from dev_agent.config import ConfigManager

config_manager = ConfigManager()
config = config_manager.get_config()
embedding_client = AzureEmbeddingClient(config.azure_openai) if config.azure_openai else None

self.workflow_manager = WorkflowManager(self, embedding_client=embedding_client)
```

### 3. dev_agent/cli/enhanced_cli.py (1 location)

#### Around line 1185
```python
# BEFORE:
self.workflow_manager = WorkflowManager(self)

# AFTER:
from dev_agent.llm.embeddings import AzureEmbeddingClient
from dev_agent.config import ConfigManager

config_manager = ConfigManager()
config = config_manager.get_config()
embedding_client = AzureEmbeddingClient(config.azure_openai) if config.azure_openai else None

self.workflow_manager = WorkflowManager(self, embedding_client=embedding_client)
```

## Error Handling

Add proper error handling when creating embedding client:

```python
try:
    from dev_agent.llm.embeddings import AzureEmbeddingClient
    config = config_manager.get_config()
    
    if config.azure_openai:
        embedding_client = AzureEmbeddingClient(config.azure_openai)
    else:
        embedding_client = None
        logger.warning("Azure OpenAI not configured - some features may be limited")
except Exception as e:
    logger.error(f"Failed to initialize embedding client: {e}")
    embedding_client = None
```

## Testing After Integration

```bash
# Test 1: Initialize new project
uv run dev-agent init /path/to/project

# Expected: No errors, cost displayed

# Test 2: Resume project
uv run dev-agent resume /path/to/project

# Expected: Can transition to specification phase

# Test 3: Interactive mode
uv run dev-agent

# Expected: All phases work correctly
```

## Verification Checklist

- [ ] All 6 locations updated
- [ ] Imports added correctly
- [ ] Error handling in place
- [ ] No type errors (run `uv run mypy dev_agent/cli`)
- [ ] Manual testing completed
- [ ] Cost tracking shows non-zero values
- [ ] Specification phase works without errors
- [ ] No token limit errors during indexing

## Alternative Approach

If you want to avoid updating all 6 locations, you could create a helper function:

```python
# In dev_agent/cli/main.py or a new utils file

def create_workflow_manager(cli_interface: ICLIInterface) -> WorkflowManager:
    """Create a WorkflowManager with proper initialization.
    
    Args:
        cli_interface: CLI interface instance
        
    Returns:
        Configured WorkflowManager instance
    """
    from dev_agent.llm.embeddings import AzureEmbeddingClient
    from dev_agent.config import ConfigManager
    
    config_manager = ConfigManager()
    config = config_manager.get_config()
    
    embedding_client = None
    if config.azure_openai:
        try:
            embedding_client = AzureEmbeddingClient(config.azure_openai)
        except Exception as e:
            logger.error(f"Failed to initialize embedding client: {e}")
    
    return WorkflowManager(cli_interface, embedding_client=embedding_client)

# Then use it everywhere:
workflow_manager = create_workflow_manager(cli)
```

This reduces code duplication and makes future updates easier.
