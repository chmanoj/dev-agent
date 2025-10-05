# Advanced Usage Patterns

## Overview

This guide covers advanced usage patterns and techniques for power users of dev-agent.

## Custom Workflow Patterns

### Iterative Refinement
Refine specifications and designs through multiple iterations:

```bash
# Initial specification
dev-agent phase specification

# Review and refine
dev-agent phase specification --refine

# Generate design
dev-agent phase design

# Refine design based on feedback
dev-agent phase design --refine
```

### Partial Workflow Execution
Execute specific phases without running the complete workflow:

```bash
# Index codebase only
dev-agent phase indexing

# Generate specification from existing index
dev-agent phase specification

# Skip to implementation
dev-agent phase implementation --skip-approval
```

### Multi-Project Management
Manage multiple projects with dev-agent:

```bash
# Initialize multiple projects
dev-agent init ~/projects/api
dev-agent init ~/projects/frontend
dev-agent init ~/projects/shared

# Switch between projects
dev-agent resume ~/projects/api
dev-agent resume ~/projects/frontend
```

## Advanced Configuration

### Custom Prompt Templates
Override default prompts for specialized use cases:

```python
from dev_agent.llm.prompt_templates import PromptTemplate

# Custom specification prompt
custom_spec_prompt = PromptTemplate(
    system_prompt="You are a domain expert in financial systems.",
    user_prompt_template="""
    Analyze this codebase and generate a specification for: {feature}
    
    Focus on:
    - Regulatory compliance
    - Audit trails
    - Data security
    
    Context: {context}
    """,
)

# Use custom prompt
generator.set_prompt_template("specification", custom_spec_prompt)
```

### Fine-Tuned Cost Control
Implement granular cost control:

```python
from dev_agent.llm.cost_tracker import CostTracker, BudgetLimit

# Set budget limits
tracker = CostTracker()
tracker.set_budget_limit(
    BudgetLimit(
        daily_limit=10.0,  # $10 per day
        phase_limit=5.0,   # $5 per phase
        operation_limit=1.0,  # $1 per operation
    )
)

# Enable warnings
tracker.enable_warnings(threshold=0.8)  # Warn at 80% of budget
```

### Custom Embedding Models
Use custom embedding configurations:

```python
from dev_agent.llm.embeddings import EmbeddingConfig

# Configure custom embeddings
config = EmbeddingConfig(
    model="text-embedding-ada-002",
    dimensions=1536,
    batch_size=32,  # Larger batches for faster processing
    cache_enabled=True,
    cache_ttl=86400,  # 24 hours
)
```

## Advanced Indexing Techniques

### Selective Indexing
Index specific parts of a large codebase:

```python
from dev_agent.indexing.indexing_engine import IndexingEngine
from pathlib import Path

engine = IndexingEngine()

# Index only specific directories
engine.index_paths([
    Path("src/core"),
    Path("src/api"),
    Path("src/models"),
])

# Exclude test files
engine.set_exclusions([
    "**/*_test.py",
    "**/test_*.py",
    "tests/**",
])
```

### Incremental Indexing
Update index for changed files only:

```bash
# Initial full index
dev-agent phase indexing

# Later, update only changed files
dev-agent phase indexing --incremental

# Force re-index specific files
dev-agent phase indexing --files src/core/main.py src/api/routes.py
```

### Custom Code Chunking
Implement custom chunking strategies:

```python
from dev_agent.indexing.code_chunker import CodeChunker, ChunkingStrategy

# Custom chunking strategy
chunker = CodeChunker(
    strategy=ChunkingStrategy.SEMANTIC,
    max_chunk_size=2000,  # Larger chunks
    overlap=200,  # More overlap for context
    preserve_structure=True,  # Keep class/function boundaries
)
```

## Advanced Generation Techniques

### Context-Aware Generation
Provide additional context for better generation:

```python
from dev_agent.generation.specification_generator import SpecificationGenerator

generator = SpecificationGenerator()

# Add domain-specific context
generator.add_context({
    "domain": "e-commerce",
    "patterns": ["microservices", "event-driven"],
    "constraints": ["PCI compliance", "GDPR"],
    "existing_services": ["payment", "inventory", "shipping"],
})

# Generate with enhanced context
spec = await generator.generate(
    feature="order processing service",
    include_examples=True,
    include_diagrams=True,
)
```

### Multi-Stage Generation
Break complex generation into stages:

```bash
# Stage 1: High-level design
dev-agent generate design --level high

# Stage 2: Detailed component design
dev-agent generate design --level detailed --component api

# Stage 3: Implementation tasks
dev-agent generate tasks --component api
```

### Template-Based Generation
Use templates for consistent output:

```python
from dev_agent.generation.template_system import TemplateSystem

# Load custom template
template_system = TemplateSystem()
template_system.load_template("microservice", "templates/microservice.json")

# Generate from template
result = await template_system.generate_from_template(
    template_name="microservice",
    parameters={
        "service_name": "payment-service",
        "database": "postgresql",
        "messaging": "rabbitmq",
    },
)
```

## Performance Optimization

### Parallel Processing
Process multiple operations in parallel:

```python
import asyncio
from dev_agent.indexing.indexing_engine import IndexingEngine

async def parallel_indexing():
    """Index multiple projects in parallel."""
    engine = IndexingEngine()
    
    projects = [
        Path("~/projects/api"),
        Path("~/projects/frontend"),
        Path("~/projects/shared"),
    ]
    
    # Index all projects concurrently
    tasks = [engine.index_project(p) for p in projects]
    results = await asyncio.gather(*tasks)
    
    return results
```

### Caching Strategies
Implement advanced caching:

```python
from dev_agent.llm.embedding_cache import EmbeddingCache, CacheStrategy

# Configure cache
cache = EmbeddingCache(
    strategy=CacheStrategy.LRU,  # Least Recently Used
    max_size_mb=1000,  # 1GB cache
    ttl=86400,  # 24 hour TTL
    compression=True,  # Compress cached data
)

# Warm cache with common queries
await cache.warm_cache([
    "authentication patterns",
    "database models",
    "API endpoints",
])
```

### Batch Operations
Optimize with batch processing:

```bash
# Batch embed multiple files
dev-agent embed --batch-size 32 src/**/*.py

# Batch generate specifications
dev-agent generate specs --batch features/*.md
```

## Integration Patterns

### CI/CD Integration
Integrate dev-agent into CI/CD pipelines:

```yaml
# .github/workflows/dev-agent.yml
name: Dev Agent Analysis

on:
  pull_request:
    branches: [main]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dev-agent
        run: pip install dev-agent
      
      - name: Index codebase
        env:
          AZURE_OPENAI_ENDPOINT: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
          AZURE_OPENAI_API_KEY: ${{ secrets.AZURE_OPENAI_API_KEY }}
        run: dev-agent phase indexing
      
      - name: Generate specification
        run: dev-agent phase specification --auto-approve
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: specifications
          path: .dev_agent/documents/
```

### IDE Integration
Integrate with VS Code:

```json
// .vscode/tasks.json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Dev Agent: Index",
      "type": "shell",
      "command": "dev-agent phase indexing",
      "problemMatcher": []
    },
    {
      "label": "Dev Agent: Generate Spec",
      "type": "shell",
      "command": "dev-agent phase specification",
      "problemMatcher": []
    }
  ]
}
```

### API Integration
Use dev-agent programmatically:

```python
from dev_agent.workflow.workflow_manager import WorkflowManager
from dev_agent.models.project_state import ProjectState
from pathlib import Path

async def automated_workflow():
    """Run automated workflow via API."""
    manager = WorkflowManager()
    
    # Initialize project
    project_path = Path("~/my-project")
    state = await manager.initialize_project(project_path)
    
    # Run indexing
    await manager.execute_phase("indexing", state)
    
    # Generate specification
    spec = await manager.execute_phase("specification", state)
    
    # Auto-approve if meets criteria
    if spec.quality_score > 0.8:
        await manager.approve_phase("specification", state)
    
    return state
```

## Troubleshooting Advanced Scenarios

### Large Codebase Handling
Optimize for very large codebases (100K+ files):

```python
from dev_agent.indexing.indexing_engine import IndexingEngine

engine = IndexingEngine()

# Configure for large codebases
engine.configure(
    batch_size=100,  # Process 100 files at a time
    max_workers=8,  # Use 8 parallel workers
    memory_limit_mb=4096,  # 4GB memory limit
    checkpoint_interval=1000,  # Save progress every 1000 files
)

# Enable progress tracking
engine.enable_progress_tracking(
    callback=lambda progress: print(f"Progress: {progress}%")
)
```

### Memory Management
Handle memory-intensive operations:

```python
from dev_agent.performance.memory_streamer import MemoryStreamer

# Stream large files
streamer = MemoryStreamer(chunk_size=1024*1024)  # 1MB chunks

async for chunk in streamer.stream_file("large_file.py"):
    # Process chunk without loading entire file
    await process_chunk(chunk)
```

### Error Recovery
Implement robust error recovery:

```python
from dev_agent.errors.recovery import RecoveryManager

recovery = RecoveryManager()

# Enable automatic recovery
recovery.enable_auto_recovery(
    max_retries=3,
    backoff_factor=2.0,
    checkpoint_enabled=True,
)

# Manual recovery
try:
    await workflow.execute()
except WorkflowError as e:
    # Recover from last checkpoint
    await recovery.recover_from_checkpoint(workflow)
```

## Best Practices

### Cost Optimization
- Use embedding cache aggressively
- Batch operations when possible
- Set appropriate budget limits
- Monitor token usage regularly

### Performance
- Index incrementally for large codebases
- Use parallel processing for multiple projects
- Configure appropriate batch sizes
- Enable compression for cache

### Quality
- Review generated content before approval
- Provide domain-specific context
- Use custom prompts for specialized domains
- Iterate on specifications and designs

### Security
- Rotate API keys regularly
- Use Azure Key Vault for production
- Enable audit logging
- Implement access controls

## Related Documentation

- [Basic Usage](basic-usage.md) - Getting started guide
- [Azure Setup](azure-setup.md) - Azure OpenAI configuration
- [CLI Reference](../cli-reference/commands.md) - Command reference
- [API Documentation](../api/workflow.md) - API reference
