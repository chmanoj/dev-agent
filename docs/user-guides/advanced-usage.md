# Advanced Usage Guide

## Overview

This guide covers advanced features and techniques for power users of dev-agent. Learn how to customize behavior, optimize performance, integrate with other tools, and handle complex scenarios.

## Advanced Configuration

### Configuration Hierarchy

dev-agent uses a layered configuration system:

1. **System defaults** (built-in)
2. **User configuration** (`~/.dev_agent/config.json`)
3. **Project configuration** (`.dev_agent/config.json`)
4. **Environment variables** (highest priority)

### Complete Configuration Reference

```json
{
  "azure_openai": {
    "endpoint": "${AZURE_OPENAI_ENDPOINT}",
    "api_key": "${AZURE_OPENAI_API_KEY}",
    "api_version": "2024-02-15-preview",
    "deployment_name": "gpt-4",
    "embedding_deployment": "text-embedding-ada-002",
    "max_tokens": 4000,
    "temperature": 0.7,
    "max_retries": 3,
    "timeout": 60,
    "batch_size": 16
  },
  "indexing": {
    "exclude_patterns": [
      "node_modules/",
      "venv/",
      ".venv/",
      "dist/",
      "build/"
    ],
    "include_patterns": ["*.py", "*.md"],
    "max_file_size": 1048576,
    "parallel_processing": true,
    "max_workers": 4,
    "incremental_indexing": true,
    "embedding_cache": true,
    "cache_ttl": 2592000
  },
  "generation": {
    "max_context_chunks": 10,
    "max_chunk_size": 1000,
    "similarity_threshold": 0.7,
    "include_tests": true,
    "include_docs": true,
    "code_style": "pep8",
    "type_hints": "strict"
  },
  "cost_management": {
    "daily_budget": 10.0,
    "weekly_budget": 50.0,
    "monthly_budget": 200.0,
    "feature_budget": 2.0,
    "budget_warnings": true,
    "cost_tracking": true
  },
  "workflow": {
    "auto_approve": false,
    "require_tests": true,
    "require_docs": true,
    "max_iterations": 3
  },
  "logging": {
    "level": "INFO",
    "file": ".dev_agent/logs/dev-agent.log",
    "max_size": 10485760,
    "backup_count": 5
  }
}
```

### Environment Variable Overrides

```bash
# Override any configuration value
export DEV_AGENT_AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4-turbo
export DEV_AGENT_INDEXING_MAX_WORKERS=8
export DEV_AGENT_GENERATION_MAX_CONTEXT_CHUNKS=15
export DEV_AGENT_COST_MANAGEMENT_DAILY_BUDGET=20.0
```

## Advanced Indexing

### Custom Code Parsers

Add support for additional languages:

```python
# .dev_agent/custom_parsers.py
from dev_agent.indexing.language_parsers import BaseParser

class RustParser(BaseParser):
    """Custom parser for Rust code."""
    
    def parse_file(self, file_path: str) -> dict:
        """Parse Rust file and extract components."""
        # Implementation
        pass
    
    def extract_functions(self, ast) -> list:
        """Extract function definitions."""
        pass
    
    def extract_classes(self, ast) -> list:
        """Extract struct/trait definitions."""
        pass

# Register custom parser
from dev_agent.indexing import register_parser
register_parser('rust', RustParser())
```

### Selective Indexing

Index specific parts of your codebase:

```bash
# Index only specific directories
dev-agent index --include "src/core/" --include "src/api/"

# Index specific file types
dev-agent index --pattern "*.py" --pattern "*.pyx"

# Exclude specific patterns
dev-agent index --exclude "tests/" --exclude "*_test.py"
```

### Custom Embedding Models

Use custom embedding models:

```python
# .dev_agent/custom_embeddings.py
from dev_agent.llm.embeddings import BaseEmbeddingClient

class CustomEmbeddingClient(BaseEmbeddingClient):
    """Custom embedding client."""
    
    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for text."""
        # Use your custom model
        pass
    
    @property
    def dimension(self) -> int:
        """Embedding dimension."""
        return 768  # Your model's dimension

# Configure dev-agent to use custom embeddings
dev-agent config set embedding_client custom
```

### Embedding Cache Management

```bash
# View cache statistics
dev-agent cache stats

# Output:
Cache Statistics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total entries: 1,234
Cache size: 45.6 MB
Hit rate: 87.3%
Oldest entry: 2024-01-01
Newest entry: 2024-01-15

# Clear old cache entries
dev-agent cache clean --older-than 30d

# Clear entire cache
dev-agent cache clear

# Rebuild cache
dev-agent cache rebuild
```

## Advanced Generation

### Custom Prompt Templates

Create custom prompts for specific use cases:

```python
# .dev_agent/custom_prompts.py
from dev_agent.llm.prompt_templates import BasePromptTemplate

class APIEndpointPrompt(BasePromptTemplate):
    """Custom prompt for API endpoint generation."""
    
    template = """
You are generating a FastAPI endpoint for an existing API.

## Existing API Patterns
{api_patterns}

## Similar Endpoints
{similar_endpoints}

## Specification
{specification}

## Requirements
1. Follow RESTful conventions
2. Use Pydantic models for validation
3. Include OpenAPI documentation
4. Add authentication decorators
5. Implement error handling
6. Include rate limiting

## Output
Generate the complete endpoint code.
"""
    
    def format(self, **kwargs) -> str:
        """Format the prompt with context."""
        return self.template.format(**kwargs)

# Register custom prompt
from dev_agent.generation import register_prompt_template
register_prompt_template('api_endpoint', APIEndpointPrompt())
```

### Multi-Model Strategy

Use different models for different tasks:

```json
{
  "generation": {
    "models": {
      "specification": "gpt-4",
      "design": "gpt-4",
      "implementation": "gpt-4-turbo",
      "code_generation": "gpt-4-turbo",
      "documentation": "gpt-35-turbo",
      "tests": "gpt-35-turbo"
    }
  }
}
```

### Context Window Optimization

Optimize context for better results:

```python
# .dev_agent/context_optimizer.py
from dev_agent.generation.context_manager import ContextManager

class OptimizedContextManager(ContextManager):
    """Optimized context selection."""
    
    def select_context(
        self,
        query: str,
        max_chunks: int = 10
    ) -> list[str]:
        """Select most relevant context chunks."""
        # Get candidates
        candidates = self.vector_db.search(query, top_k=50)
        
        # Score by relevance and recency
        scored = self._score_chunks(candidates)
        
        # Diversify selection
        selected = self._diversify(scored, max_chunks)
        
        return selected
    
    def _score_chunks(self, chunks: list) -> list:
        """Score chunks by multiple factors."""
        # Implementation
        pass
    
    def _diversify(self, chunks: list, max_count: int) -> list:
        """Ensure diverse context selection."""
        # Implementation
        pass
```

### Streaming Response Handling

Custom streaming handlers:

```python
# .dev_agent/streaming_handlers.py
from dev_agent.cli.progress_display import StreamingHandler

class CustomStreamingHandler(StreamingHandler):
    """Custom streaming response handler."""
    
    async def handle_stream(
        self,
        stream: AsyncIterator[str]
    ) -> str:
        """Handle streaming response with custom logic."""
        full_response = []
        code_blocks = []
        
        async for chunk in stream:
            # Custom processing
            if self._is_code_block(chunk):
                code_blocks.append(chunk)
            
            # Display with syntax highlighting
            self._display_chunk(chunk)
            
            full_response.append(chunk)
        
        # Post-process
        return self._post_process(full_response, code_blocks)
```

## Advanced Workflow

### Custom Workflow Phases

Add custom phases to the workflow:

```python
# .dev_agent/custom_phases.py
from dev_agent.workflow.phase_manager import BasePhase

class SecurityAuditPhase(BasePhase):
    """Custom security audit phase."""
    
    async def execute(self, context: dict) -> dict:
        """Execute security audit."""
        # Analyze design for security issues
        design = context['design']
        
        # Run security checks
        vulnerabilities = await self._check_vulnerabilities(design)
        
        # Generate security recommendations
        recommendations = await self._generate_recommendations(
            vulnerabilities
        )
        
        return {
            'vulnerabilities': vulnerabilities,
            'recommendations': recommendations,
            'status': 'complete'
        }
    
    async def _check_vulnerabilities(self, design: str) -> list:
        """Check for security vulnerabilities."""
        # Implementation
        pass

# Register custom phase
from dev_agent.workflow import register_phase
register_phase('security_audit', SecurityAuditPhase())
```

### Workflow Hooks

Add hooks at different workflow stages:

```python
# .dev_agent/workflow_hooks.py
from dev_agent.workflow.hooks import WorkflowHook

class CodeQualityHook(WorkflowHook):
    """Hook to check code quality after generation."""
    
    async def on_code_generated(self, code: str, context: dict):
        """Run after code generation."""
        # Run linters
        lint_results = await self._run_linters(code)
        
        # Run type checker
        type_results = await self._run_type_checker(code)
        
        # Check complexity
        complexity = await self._check_complexity(code)
        
        if not self._passes_quality_checks(
            lint_results,
            type_results,
            complexity
        ):
            raise CodeQualityError("Generated code fails quality checks")
    
    async def _run_linters(self, code: str) -> dict:
        """Run code linters."""
        # Implementation
        pass

# Register hook
from dev_agent.workflow import register_hook
register_hook('post_generation', CodeQualityHook())
```

### Parallel Workflow Execution

Execute multiple features in parallel:

```python
# parallel_workflow.py
import asyncio
from dev_agent.workflow import WorkflowManager

async def process_features_parallel(features: list[str]):
    """Process multiple features in parallel."""
    workflow = WorkflowManager()
    
    # Create tasks for each feature
    tasks = [
        workflow.execute_feature(feature)
        for feature in features
    ]
    
    # Execute in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    for feature, result in zip(features, results):
        if isinstance(result, Exception):
            print(f"❌ {feature}: {result}")
        else:
            print(f"✅ {feature}: Complete")

# Usage
features = [
    "Add user authentication",
    "Add API rate limiting",
    "Add logging system"
]

asyncio.run(process_features_parallel(features))
```

## Integration with Other Tools

### CI/CD Integration

#### GitHub Actions

```yaml
# .github/workflows/dev-agent.yml
name: dev-agent Workflow

on:
  workflow_dispatch:
    inputs:
      feature:
        description: 'Feature to implement'
        required: true

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dev-agent
        run: pip install dev-agent
      
      - name: Configure Azure OpenAI
        env:
          AZURE_OPENAI_ENDPOINT: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
          AZURE_OPENAI_API_KEY: ${{ secrets.AZURE_OPENAI_API_KEY }}
        run: |
          dev-agent config set azure_openai.endpoint $AZURE_OPENAI_ENDPOINT
          dev-agent config set azure_openai.api_key $AZURE_OPENAI_API_KEY
      
      - name: Index codebase
        run: dev-agent index .
      
      - name: Generate feature
        run: |
          dev-agent generate \
            --feature "${{ github.event.inputs.feature }}" \
            --auto-approve
      
      - name: Run tests
        run: pytest
      
      - name: Create PR
        uses: peter-evans/create-pull-request@v5
        with:
          title: "feat: ${{ github.event.inputs.feature }}"
          body: "Generated by dev-agent"
          branch: "feature/dev-agent-${{ github.run_number }}"
```

#### GitLab CI

```yaml
# .gitlab-ci.yml
dev-agent:
  stage: generate
  image: python:3.11
  script:
    - pip install dev-agent
    - dev-agent config set azure_openai.endpoint $AZURE_OPENAI_ENDPOINT
    - dev-agent config set azure_openai.api_key $AZURE_OPENAI_API_KEY
    - dev-agent index .
    - dev-agent generate --feature "$FEATURE_DESCRIPTION" --auto-approve
    - pytest
  artifacts:
    paths:
      - generated_code/
  only:
    - web
```

### IDE Integration

#### VS Code Extension

```json
// .vscode/tasks.json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "dev-agent: Index Project",
      "type": "shell",
      "command": "dev-agent index .",
      "problemMatcher": []
    },
    {
      "label": "dev-agent: Generate Feature",
      "type": "shell",
      "command": "dev-agent generate --interactive",
      "problemMatcher": []
    },
    {
      "label": "dev-agent: Cost Report",
      "type": "shell",
      "command": "dev-agent cost --detailed",
      "problemMatcher": []
    }
  ]
}
```

#### PyCharm External Tools

```xml
<!-- Settings > Tools > External Tools -->
<tool name="dev-agent Index"
      program="dev-agent"
      parameters="index $ProjectFileDir$"
      workingDir="$ProjectFileDir$" />

<tool name="dev-agent Generate"
      program="dev-agent"
      parameters="generate --interactive"
      workingDir="$ProjectFileDir$" />
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: dev-agent-validate
        name: Validate with dev-agent
        entry: dev-agent validate
        language: system
        pass_filenames: false
      
      - id: dev-agent-cost-check
        name: Check dev-agent costs
        entry: bash -c 'dev-agent cost --today | grep -q "Budget: OK"'
        language: system
        pass_filenames: false
```

### Slack Integration

```python
# slack_integration.py
from slack_sdk import WebClient
from dev_agent.workflow import WorkflowManager

class SlackNotifier:
    """Send dev-agent notifications to Slack."""
    
    def __init__(self, token: str, channel: str):
        self.client = WebClient(token=token)
        self.channel = channel
    
    async def notify_phase_complete(
        self,
        phase: str,
        result: dict
    ):
        """Notify when phase completes."""
        message = f"""
✅ *{phase.title()} Phase Complete*

Duration: {result['duration']}
Cost: ${result['cost']:.2f}
Status: {result['status']}

<{result['document_url']}|View Document>
        """
        
        self.client.chat_postMessage(
            channel=self.channel,
            text=message
        )
    
    async def notify_error(self, error: Exception):
        """Notify on errors."""
        message = f"""
❌ *dev-agent Error*

{str(error)}

Please review and retry.
        """
        
        self.client.chat_postMessage(
            channel=self.channel,
            text=message
        )

# Usage
notifier = SlackNotifier(
    token=os.getenv('SLACK_TOKEN'),
    channel='#dev-agent-notifications'
)

workflow = WorkflowManager()
workflow.add_listener('phase_complete', notifier.notify_phase_complete)
workflow.add_listener('error', notifier.notify_error)
```

## Performance Optimization

### Caching Strategies

#### Multi-Level Cache

```python
# .dev_agent/cache_config.py
{
  "cache": {
    "levels": [
      {
        "type": "memory",
        "max_size": 100,
        "ttl": 3600
      },
      {
        "type": "disk",
        "path": ".dev_agent/cache",
        "max_size": 1073741824,
        "ttl": 2592000
      },
      {
        "type": "redis",
        "host": "localhost",
        "port": 6379,
        "ttl": 604800
      }
    ]
  }
}
```

#### Cache Warming

```bash
# Pre-populate cache with common queries
dev-agent cache warm --patterns "authentication" "api" "database"

# Warm cache from previous projects
dev-agent cache import --from /path/to/other/project
```

### Parallel Processing

```json
{
  "indexing": {
    "parallel_processing": true,
    "max_workers": 8,
    "chunk_size": 100
  },
  "generation": {
    "parallel_requests": true,
    "max_concurrent": 4
  }
}
```

### Database Optimization

```python
# .dev_agent/vector_db_config.py
{
  "vector_database": {
    "type": "faiss",
    "index_type": "IVF",
    "nlist": 100,
    "nprobe": 10,
    "metric": "cosine",
    "use_gpu": false
  }
}
```

## Monitoring and Observability

### Metrics Collection

```python
# metrics_collector.py
from prometheus_client import Counter, Histogram, Gauge
from dev_agent.workflow import WorkflowManager

# Define metrics
phase_duration = Histogram(
    'dev_agent_phase_duration_seconds',
    'Phase execution duration',
    ['phase']
)

api_calls = Counter(
    'dev_agent_api_calls_total',
    'Total API calls',
    ['operation']
)

token_usage = Counter(
    'dev_agent_tokens_total',
    'Total tokens used',
    ['type']
)

cost = Counter(
    'dev_agent_cost_dollars',
    'Total cost in dollars'
)

# Instrument workflow
class InstrumentedWorkflow(WorkflowManager):
    """Workflow with metrics collection."""
    
    async def execute_phase(self, phase: str):
        """Execute phase with metrics."""
        with phase_duration.labels(phase=phase).time():
            result = await super().execute_phase(phase)
        
        # Record metrics
        api_calls.labels(operation=phase).inc(result['api_calls'])
        token_usage.labels(type='prompt').inc(result['prompt_tokens'])
        token_usage.labels(type='completion').inc(result['completion_tokens'])
        cost.inc(result['cost'])
        
        return result
```

### Logging Configuration

```json
{
  "logging": {
    "version": 1,
    "formatters": {
      "detailed": {
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
      },
      "json": {
        "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
        "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
      }
    },
    "handlers": {
      "console": {
        "class": "logging.StreamHandler",
        "formatter": "detailed",
        "level": "INFO"
      },
      "file": {
        "class": "logging.handlers.RotatingFileHandler",
        "filename": ".dev_agent/logs/dev-agent.log",
        "maxBytes": 10485760,
        "backupCount": 5,
        "formatter": "json",
        "level": "DEBUG"
      },
      "syslog": {
        "class": "logging.handlers.SysLogHandler",
        "address": "/dev/log",
        "formatter": "json",
        "level": "WARNING"
      }
    },
    "loggers": {
      "dev_agent": {
        "handlers": ["console", "file", "syslog"],
        "level": "DEBUG"
      }
    }
  }
}
```

### Distributed Tracing

```python
# tracing.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configure tracing
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

tracer = trace.get_tracer(__name__)

# Instrument workflow
class TracedWorkflow(WorkflowManager):
    """Workflow with distributed tracing."""
    
    async def execute_phase(self, phase: str):
        """Execute phase with tracing."""
        with tracer.start_as_current_span(f"phase.{phase}") as span:
            span.set_attribute("phase.name", phase)
            
            result = await super().execute_phase(phase)
            
            span.set_attribute("phase.cost", result['cost'])
            span.set_attribute("phase.tokens", result['total_tokens'])
            
            return result
```

## Advanced Troubleshooting

### Debug Mode

```bash
# Enable debug mode
export DEV_AGENT_DEBUG=true
dev-agent --verbose generate --feature "Add authentication"

# Debug specific components
export DEV_AGENT_DEBUG_INDEXING=true
export DEV_AGENT_DEBUG_GENERATION=true
export DEV_AGENT_DEBUG_API=true
```

### Request/Response Logging

```python
# .dev_agent/debug_config.py
{
  "debug": {
    "log_requests": true,
    "log_responses": true,
    "log_embeddings": false,
    "log_context": true,
    "save_prompts": true,
    "prompt_dir": ".dev_agent/debug/prompts"
  }
}
```

### Performance Profiling

```bash
# Profile indexing
dev-agent index --profile

# Profile generation
dev-agent generate --profile --feature "Add authentication"

# View profile results
dev-agent profile show
```

## Next Steps

- Review [Four-Phase Workflow](four-phase-workflow.md)
- Learn about [Cost Management](cost-management.md)
- Check [Best Practices](best-practices.md)
- Explore [CLI Reference](../cli-reference/commands.md)
