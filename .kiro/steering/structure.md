# Project Structure

## Package Organization

The `dev_agent/` package follows a modular architecture with clear separation of concerns:

```
dev_agent/
├── __init__.py              # Package entry point with version
├── cli/                     # Command-line interface
│   ├── main.py             # Typer CLI application entry point
│   ├── interactive_cli.py  # Chat-based interactive interface
│   └── session_manager.py  # Session state management
├── llm/                     # LLM integration layer (NEW)
│   ├── __init__.py         # LLM client factory
│   ├── base.py             # Abstract LLM and embedding interfaces
│   ├── azure_client.py     # Azure OpenAI implementation
│   ├── embeddings.py       # Embedding client abstraction
│   ├── token_counter.py    # Token counting and management
│   ├── prompt_templates.py # Structured prompts for each phase
│   └── cost_tracker.py     # API usage and cost tracking
├── interfaces/             # Abstract base classes and protocols
│   ├── workflow_interface.py
│   ├── analysis_interface.py
│   ├── llm_interface.py    # LLM provider interface (NEW)
│   └── ...
├── models/                 # Pydantic data models
│   ├── enums.py           # Core enums (PhaseType, TaskStatus, LLMProvider)
│   ├── project_state.py   # Project state data structures
│   ├── documents.py       # Document models
│   ├── llm_config.py      # LLM configuration models (NEW)
│   └── ...
├── workflow/              # Workflow orchestration
│   ├── workflow_manager.py
│   ├── phase_manager.py
│   └── ...
├── indexing/              # Code analysis and indexing
│   ├── indexing_engine.py      # Uses Azure OpenAI embeddings
│   ├── tree_sitter_parser.py   # AST parsing
│   ├── vector_database.py      # FAISS storage
│   ├── code_chunker.py         # Semantic code chunking
│   └── embedding_cache.py      # Cache embeddings (NEW)
├── generation/            # Content generation (uses Azure OpenAI)
│   ├── specification_generator.py  # GPT-4 spec generation
│   ├── design_generator.py         # GPT-4 design generation
│   ├── task_generator.py           # GPT-4 task breakdown
│   └── python_code_generator.py    # GPT-4 code generation
├── analysis/              # Codebase analysis
│   └── codebase_analyzer.py
├── state/                 # State management
│   └── state_manager.py
├── config/                # Configuration management
│   ├── config_manager.py       # General config
│   ├── llm_config.py          # Azure OpenAI config (NEW)
│   └── logging_config.py
└── errors/                # Error handling
    ├── exceptions.py          # General exceptions
    ├── llm_exceptions.py      # LLM-specific exceptions (NEW)
    ├── error_handler.py
    └── recovery.py
```

## Project Root Structure

```
project-root/
├── dev_agent/              # Main package
├── tests/                  # Test suite
│   ├── sample_files/      # Test fixtures
│   └── test_*.py          # Test modules
├── examples/              # Usage examples and demos
├── scripts/               # Utility scripts
├── .dev_agent/           # Project state directory (created by tool)
│   ├── documents/        # Generated documents
│   └── state.json        # Project state
├── pyproject.toml        # Primary configuration
├── requirements.txt      # Legacy pip requirements
├── setup.py             # Legacy setup script
└── README.md            # Documentation
```

## Architecture Patterns

### Interface-Based Design
- All major components implement abstract interfaces from `interfaces/`
- Enables dependency injection and testing
- Clear contracts between components
- LLM clients implement `ILLMClient` and `IEmbeddingClient` interfaces

### Azure OpenAI Integration Layer
- **Abstraction**: `llm/base.py` defines provider-agnostic interfaces
- **Implementation**: `llm/azure_client.py` implements Azure OpenAI specifics
- **Retry Logic**: Exponential backoff with tenacity for resilient API calls
- **Token Management**: tiktoken for accurate token counting and cost estimation
- **Streaming Support**: Async streaming for real-time CLI feedback
- **Cost Tracking**: Monitor token usage and API costs per operation

### Enum-Driven State Management
- Core enums in `models/enums.py` define system states
- `PhaseType`: INDEXING, SPECIFICATION, DESIGN, IMPLEMENTATION
- `TaskStatus`: NOT_STARTED, IN_PROGRESS, COMPLETED, FAILED, BLOCKED
- `PhaseStatus`: NOT_STARTED, IN_PROGRESS, COMPLETED, FAILED, REQUIRES_APPROVAL
- `LLMProvider`: AZURE_OPENAI (BEDROCK planned for future)

### Pydantic Models
- All data structures use Pydantic v2 for validation
- Consistent serialization/deserialization
- Type safety and runtime validation
- `SecretStr` for API keys (never logged or serialized)
- LLM configuration models with validation

### Session-Based Workflow
- Persistent state across CLI sessions
- User approval required between phases
- State stored in `.dev_agent/` directory
- Embedding cache for performance optimization

### Async-First Architecture
- All Azure OpenAI calls use async/await
- Non-blocking API requests
- Concurrent embedding generation for batches
- Streaming responses for interactive CLI

## Naming Conventions

### Files and Modules
- Snake_case for all Python files
- Descriptive names indicating purpose
- Interface files end with `_interface.py`
- Test files prefixed with `test_`

### Classes
- PascalCase for class names
- Interface classes prefixed with `I` (e.g., `IWorkflowManager`)
- Exception classes suffixed with `Error` or `Exception`

### Functions and Variables
- Snake_case for functions and variables
- Private methods prefixed with `_`
- Constants in UPPER_CASE

### Project State Directory
- `.dev_agent/` created in project root
- Contains `state.json` and `documents/` subdirectory
- `embedding_cache/` for cached Azure OpenAI embeddings
- `logs/` for API call audit logs
- Managed automatically by the system

## LLM Integration Architecture

### Azure OpenAI Client Design
```python
# Abstract interface for any LLM provider
class ILLMClient(ABC):
    async def generate_completion(prompt: str, ...) -> str
    async def generate_streaming(prompt: str, ...) -> AsyncIterator[str]
    def count_tokens(text: str) -> int

class IEmbeddingClient(ABC):
    async def embed_text(text: str) -> list[float]
    async def embed_batch(texts: list[str]) -> list[list[float]]
    @property
    def dimension() -> int

# Azure OpenAI implementation
class AzureOpenAIClient(ILLMClient):
    # Uses openai.AsyncAzureOpenAI
    # Implements retry logic with tenacity
    # Tracks token usage and costs

class AzureEmbeddingClient(IEmbeddingClient):
    # Uses text-embedding-ada-002 (1536 dimensions)
    # Batches requests for efficiency
    # Caches embeddings to avoid re-computation
```

### Prompt Engineering Structure
- **Template-Based**: Structured prompts in `llm/prompt_templates.py`
- **Context Injection**: Relevant code chunks from vector search
- **Few-Shot Examples**: Include similar code from codebase
- **Consistency Enforcement**: Prompts emphasize matching existing patterns

### Error Handling & Resilience
- **Retry Logic**: Exponential backoff for transient failures
- **Rate Limiting**: Handle 429 errors gracefully
- **Timeout Management**: Configurable timeouts per operation
- **Fallback Strategies**: Graceful degradation on API failures
- **State Preservation**: Save state before API calls for recovery

### Security & Compliance
- **Environment Variables**: All credentials via env vars only
- **Secret Management**: Pydantic SecretStr for API keys
- **Audit Logging**: Log all API calls (without sensitive data)
- **No Data Leakage**: Code stays within your Azure tenant
- **Compliance**: Supports Azure compliance requirements