# Requirements Document: Azure OpenAI Integration

## Introduction

This specification defines the requirements for completing the Azure OpenAI integration in dev-agent. The system currently has basic Azure OpenAI service infrastructure but needs a comprehensive LLM abstraction layer, proper integration with all workflow phases, token management, cost tracking, and enhanced error handling. This integration will replace any local model dependencies and establish Azure OpenAI as the exclusive AI provider for all code generation, specification creation, design generation, and embedding operations.

## Requirements

### Requirement 1: LLM Abstraction Layer

**User Story:** As a developer, I want a clean abstraction layer for LLM operations so that the system can be extended to support multiple providers in the future while maintaining consistent interfaces.

#### Acceptance Criteria

1. WHEN the system needs to interact with an LLM THEN it SHALL use abstract interfaces defined in `dev_agent/llm/base.py`
2. WHEN creating an LLM client THEN it SHALL implement the `ILLMClient` interface with methods for completion, streaming, and token counting
3. WHEN creating an embedding client THEN it SHALL implement the `IEmbeddingClient` interface with methods for single and batch embedding generation
4. IF the system needs to add a new LLM provider THEN it SHALL only need to implement the abstract interfaces without modifying existing code
5. WHEN the LLM client is initialized THEN it SHALL validate all required configuration parameters using Pydantic models
6. WHEN an API key is stored THEN it SHALL use Pydantic `SecretStr` to prevent accidental logging or serialization

### Requirement 2: Azure OpenAI Client Implementation

**User Story:** As a developer, I want a robust Azure OpenAI client that handles all API interactions with proper retry logic, error handling, and async support so that the system is resilient to transient failures.

#### Acceptance Criteria

1. WHEN making any Azure OpenAI API call THEN it SHALL use async/await patterns for non-blocking operations
2. WHEN an API call fails with a transient error (rate limit, timeout) THEN it SHALL retry with exponential backoff using tenacity
3. WHEN an API call fails after all retries THEN it SHALL raise a specific LLM exception with context about the failure
4. WHEN generating completions THEN it SHALL support both standard and streaming responses
5. WHEN streaming responses THEN it SHALL yield tokens as they arrive for real-time CLI feedback
6. WHEN the client is initialized THEN it SHALL load configuration from environment variables with fallback to config files
7. WHEN authentication fails THEN it SHALL raise `LLMAuthenticationError` with guidance on fixing credentials
8. WHEN rate limits are hit THEN it SHALL log warnings and retry automatically with appropriate backoff

### Requirement 3: Token Management and Cost Tracking

**User Story:** As a user, I want to track token usage and estimated costs for all Azure OpenAI operations so that I can monitor and control my API spending.

#### Acceptance Criteria

1. WHEN making any completion request THEN it SHALL count tokens using tiktoken before the API call
2. WHEN a completion response is received THEN it SHALL record actual prompt tokens, completion tokens, and total tokens used
3. WHEN generating embeddings THEN it SHALL track embedding tokens separately from completion tokens
4. WHEN token usage exceeds a configurable threshold THEN it SHALL warn the user before proceeding
5. WHEN a workflow phase completes THEN it SHALL display a summary of tokens used and estimated cost
6. WHEN the user requests a cost report THEN it SHALL show breakdown by operation type (completion, embedding) with costs
7. WHEN calculating costs THEN it SHALL use current Azure OpenAI pricing for GPT-4 and text-embedding-ada-002
8. WHEN token counting fails THEN it SHALL log a warning but continue with the operation

### Requirement 4: Embedding Generation and Caching

**User Story:** As a developer, I want efficient embedding generation with caching so that the system doesn't waste API calls on duplicate content.

#### Acceptance Criteria

1. WHEN generating embeddings for code chunks THEN it SHALL batch requests in groups of 16 texts per API call
2. WHEN an embedding is generated THEN it SHALL cache the result to disk using a content hash as the key
3. WHEN the same text needs embedding again THEN it SHALL retrieve from cache instead of calling the API
4. WHEN the cache directory doesn't exist THEN it SHALL create it automatically in `.dev_agent/embedding_cache/`
5. WHEN embeddings are cached THEN it SHALL store metadata including model name, dimension, and timestamp
6. WHEN the embedding model changes THEN it SHALL invalidate old cache entries for that content
7. WHEN batch embedding fails for some texts THEN it SHALL continue with successful embeddings and log failures
8. WHEN the cache grows large THEN it SHALL provide a command to clear old cache entries

### Requirement 5: Prompt Engineering Templates

**User Story:** As a developer, I want structured prompt templates for each workflow phase so that the system generates consistent, high-quality outputs.

#### Acceptance Criteria

1. WHEN generating a specification THEN it SHALL use a template that includes codebase context, relevant examples, and detected patterns
2. WHEN generating a design document THEN it SHALL use a template that emphasizes architectural consistency with existing code
3. WHEN generating code THEN it SHALL use a template that includes similar implementations and style requirements
4. WHEN generating tasks THEN it SHALL use a template that breaks down work into incremental, testable steps
5. WHEN injecting context into prompts THEN it SHALL retrieve relevant code chunks using vector similarity search
6. WHEN formatting code examples in prompts THEN it SHALL include file paths, line numbers, and syntax highlighting markers
7. WHEN the prompt exceeds token limits THEN it SHALL truncate context intelligently while preserving critical information
8. WHEN templates are updated THEN it SHALL not require code changes, only template file modifications

### Requirement 6: Integration with Workflow Phases

**User Story:** As a user, I want all workflow phases (indexing, specification, design, implementation) to use Azure OpenAI so that the system provides consistent AI-powered assistance throughout.

#### Acceptance Criteria

1. WHEN the indexing phase runs THEN it SHALL use Azure OpenAI embeddings via text-embedding-ada-002
2. WHEN the specification phase runs THEN it SHALL use GPT-4 to generate specifications based on codebase analysis
3. WHEN the design phase runs THEN it SHALL use GPT-4 to create technical designs consistent with existing architecture
4. WHEN the implementation phase runs THEN it SHALL use GPT-4 to generate code matching existing patterns
5. WHEN any phase needs to search for relevant code THEN it SHALL use vector similarity with Azure OpenAI embeddings
6. WHEN a phase completes THEN it SHALL save token usage statistics to the project state
7. WHEN resuming a workflow THEN it SHALL load previous token usage and continue tracking
8. WHEN switching between phases THEN it SHALL maintain context about previous AI-generated content

### Requirement 7: Error Handling and Recovery

**User Story:** As a user, I want robust error handling so that transient API failures don't lose my work or require starting over.

#### Acceptance Criteria

1. WHEN an API call fails THEN it SHALL save the current state before raising an exception
2. WHEN authentication fails THEN it SHALL provide clear instructions on setting up Azure OpenAI credentials
3. WHEN rate limits are exceeded THEN it SHALL wait and retry automatically without user intervention
4. WHEN the API is unavailable THEN it SHALL allow the user to retry or save progress and exit
5. WHEN network errors occur THEN it SHALL distinguish between transient and permanent failures
6. WHEN an error occurs during streaming THEN it SHALL save any partial response received
7. WHEN multiple consecutive failures occur THEN it SHALL suggest checking Azure OpenAI service status
8. WHEN recovering from an error THEN it SHALL resume from the last successful operation

### Requirement 8: Configuration and Environment Management

**User Story:** As a user, I want flexible configuration options so that I can set up Azure OpenAI using environment variables, config files, or interactive CLI.

#### Acceptance Criteria

1. WHEN the system starts THEN it SHALL check for Azure OpenAI configuration in this order: environment variables, config file, interactive prompt
2. WHEN environment variables are set THEN they SHALL take precedence over config file values
3. WHEN running `dev-agent azure configure` THEN it SHALL provide an interactive wizard for setting up credentials
4. WHEN configuration is saved THEN it SHALL validate all required fields before writing to disk
5. WHEN API keys are stored in config files THEN they SHALL be encrypted or the user SHALL be warned to use environment variables
6. WHEN testing the configuration THEN it SHALL make actual API calls to verify credentials work
7. WHEN configuration is invalid THEN it SHALL provide specific error messages about what's missing or wrong
8. WHEN displaying configuration status THEN it SHALL mask API keys but show other settings

### Requirement 9: Testing Infrastructure

**User Story:** As a developer, I want comprehensive test coverage with mocked Azure OpenAI calls so that tests run fast and don't incur API costs.

#### Acceptance Criteria

1. WHEN running unit tests THEN they SHALL mock all Azure OpenAI API calls using pytest fixtures
2. WHEN testing LLM client methods THEN they SHALL use AsyncMock for async operations
3. WHEN testing error handling THEN they SHALL simulate various API error conditions
4. WHEN testing retry logic THEN they SHALL verify exponential backoff behavior
5. WHEN testing token counting THEN they SHALL verify accuracy against known examples
6. WHEN running integration tests THEN they SHALL be gated by an environment variable `AZURE_OPENAI_INTEGRATION_TESTS=true`
7. WHEN integration tests run THEN they SHALL use real Azure OpenAI API calls and verify end-to-end functionality
8. WHEN tests complete THEN they SHALL achieve >90% code coverage for all LLM-related modules

### Requirement 10: Documentation and Examples

**User Story:** As a user, I want comprehensive documentation so that I can understand how to set up and use Azure OpenAI integration.

#### Acceptance Criteria

1. WHEN reading the documentation THEN it SHALL include a step-by-step Azure OpenAI setup guide
2. WHEN setting up for the first time THEN the documentation SHALL explain how to create an Azure OpenAI resource
3. WHEN configuring deployments THEN the documentation SHALL explain the difference between model names and deployment names
4. WHEN managing costs THEN the documentation SHALL provide guidance on token usage and pricing
5. WHEN troubleshooting THEN the documentation SHALL include common error messages and solutions
6. WHEN viewing examples THEN they SHALL demonstrate all major LLM operations with realistic scenarios
7. WHEN API keys are shown in examples THEN they SHALL use placeholder values like `your-api-key-here`
8. WHEN security is discussed THEN the documentation SHALL emphasize never committing API keys to version control

### Requirement 11: Migration from Local Models

**User Story:** As a developer, I want to cleanly remove local model dependencies so that the codebase is simpler and Azure OpenAI is the only AI provider.

#### Acceptance Criteria

1. WHEN the migration is complete THEN sentence-transformers SHALL be removed from core dependencies
2. WHEN local embeddings are referenced THEN the code SHALL be removed or marked as deprecated
3. WHEN the indexing engine runs THEN it SHALL only use Azure OpenAI embeddings
4. WHEN old vector databases exist THEN the system SHALL detect and offer to rebuild with Azure embeddings
5. WHEN pyproject.toml is updated THEN sentence-transformers SHALL be in an optional dependency group for backward compatibility
6. WHEN tests reference local models THEN they SHALL be updated to mock Azure OpenAI instead
7. WHEN documentation mentions local models THEN it SHALL be updated to focus on Azure OpenAI
8. WHEN the migration is complete THEN all steering docs SHALL reflect Azure OpenAI as the primary provider

### Requirement 12: Performance Optimization

**User Story:** As a user, I want efficient API usage so that operations complete quickly without unnecessary API calls.

#### Acceptance Criteria

1. WHEN generating multiple embeddings THEN they SHALL be batched to minimize API calls
2. WHEN the same content is embedded multiple times THEN it SHALL use cached embeddings
3. WHEN making concurrent API calls THEN they SHALL use asyncio for parallel execution
4. WHEN streaming responses THEN they SHALL display tokens immediately without buffering
5. WHEN context windows are large THEN the system SHALL intelligently truncate while preserving key information
6. WHEN vector search is performed THEN it SHALL use FAISS for O(log n) similarity search
7. WHEN indexing large codebases THEN it SHALL show progress updates every 100 chunks
8. WHEN API calls are slow THEN it SHALL provide feedback to the user about what's happening

## Success Criteria

The Azure OpenAI integration will be considered complete when:

1. All workflow phases use Azure OpenAI exclusively for AI operations
2. Token usage and costs are tracked and reported to users
3. Embedding generation uses caching to minimize API calls
4. Error handling provides clear guidance and automatic recovery
5. Test coverage exceeds 90% with comprehensive mocking
6. Documentation includes setup guides, examples, and troubleshooting
7. Local model dependencies are removed from core requirements
8. The system passes all integration tests with real Azure OpenAI API calls
9. Configuration can be managed via environment variables, config files, or interactive CLI
10. All steering documentation reflects Azure OpenAI as the primary provider

## Non-Functional Requirements

### Performance
- Embedding generation SHALL complete within 5 seconds per 100 code chunks
- API calls SHALL timeout after 60 seconds with automatic retry
- Vector search SHALL return results within 100ms for databases with <100K chunks

### Security
- API keys SHALL never be logged or displayed in plain text
- Configuration files with API keys SHALL have restricted file permissions
- All API communication SHALL use HTTPS
- Credentials SHALL be validated before making API calls

### Reliability
- The system SHALL handle transient API failures gracefully with automatic retry
- State SHALL be preserved across API failures to prevent data loss
- The system SHALL continue operating if embedding cache is corrupted

### Maintainability
- LLM abstraction layer SHALL allow adding new providers without modifying existing code
- Prompt templates SHALL be externalized for easy updates
- Configuration SHALL use Pydantic models for validation and type safety
- All public APIs SHALL have comprehensive docstrings

### Usability
- Error messages SHALL provide actionable guidance for resolution
- Configuration wizard SHALL guide users through Azure OpenAI setup
- Token usage reports SHALL be clear and easy to understand
- Progress indicators SHALL show status during long-running operations
