# Implementation Plan: Azure OpenAI Integration

## Overview

This implementation plan breaks down the Azure OpenAI integration into discrete, manageable coding tasks. Each task builds incrementally on previous tasks and focuses on implementing specific components with tests.

## Task Breakdown

- [x] 1. Set up LLM abstraction layer and base interfaces
  - Create abstract interfaces for LLM and embedding clients
  - Define base exception classes for LLM operations
  - Add new enums for LLM providers and operation types
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

- [x] 1.1 Create base LLM interfaces in `dev_agent/llm/base.py`
  - Implement `ILLMClient` abstract class with completion, streaming, and token counting methods
  - Implement `IEmbeddingClient` abstract class with single and batch embedding methods
  - Add type hints using modern Python 3.10+ syntax
  - Include comprehensive docstrings in Google style
  - _Requirements: 1.1, 1.2_

- [x] 1.2 Create LLM exception hierarchy in `dev_agent/errors/llm_exceptions.py`
  - Implement base `LLMError` exception class
  - Implement specific exceptions: `LLMAuthenticationError`, `LLMRateLimitError`, `LLMTimeoutError`, `LLMBadRequestError`, `LLMAPIError`, `LLMTokenLimitError`, `LLMCostLimitError`
  - Add helpful error messages with resolution guidance
  - _Requirements: 7.1, 7.2, 7.3_

- [x] 1.3 Add LLM-related enums to `dev_agent/models/enums.py`
  - Add `LLMProvider` enum with `AZURE_OPENAI` value
  - Add `LLMOperationType` enum with completion, streaming, embedding values
  - _Requirements: 1.6_

- [x] 2. Implement Pydantic configuration models
  - Create enhanced Azure OpenAI configuration model
  - Create LLM response models
  - Create cost tracking models
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 2.1 Create enhanced `AzureOpenAIConfig` in `dev_agent/models/llm_config.py`
  - Use Pydantic BaseModel with field validation
  - Use `SecretStr` for API key field
  - Add validators for endpoint URL format
  - Add field constraints (min/max values)
  - Implement custom JSON encoder to redact API keys
  - _Requirements: 1.6, 8.5_

- [x] 2.2 Create LLM response models in `dev_agent/models/llm_responses.py`
  - Implement `CompletionResponse` dataclass with content, tokens, cost
  - Implement `EmbeddingResponse` dataclass with embeddings, tokens, cache stats
  - Add type hints for all fields
  - _Requirements: 3.2, 4.2_

- [x] 2.3 Create cost tracking models in `dev_agent/models/cost_tracking.py`
  - Implement `TokenUsage` dataclass for per-operation tracking
  - Implement `CostReport` dataclass for session/phase summaries
  - Add methods for aggregating usage across operations
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [x] 3. Implement token counter module
  - Create token counting functionality using tiktoken
  - Implement cost estimation logic
  - Add context window validation
  - _Requirements: 3.1, 3.2, 3.8_

- [x] 3.1 Create `TokenCounter` class in `dev_agent/llm/token_counter.py`
  - Implement `count_tokens()` method using tiktoken for GPT-4
  - Implement `estimate_cost()` method with Azure pricing
  - Implement `validate_context_window()` method for token limits
  - Add support for different models (GPT-4, GPT-4-32k, GPT-4-turbo)
  - Handle tiktoken errors gracefully with logging
  - _Requirements: 3.1, 3.2, 3.8_

- [x] 3.2 Write unit tests for token counter in `tests/test_token_counter.py`
  - Test token counting accuracy with known examples
  - Test cost estimation calculations
  - Test context window validation
  - Test error handling for invalid inputs
  - _Requirements: 9.1, 9.2, 9.5_

- [x] 4. Implement cost tracker module
  - Create cost tracking functionality
  - Implement usage aggregation
  - Add budget threshold warnings
  - _Requirements: 3.3, 3.4, 3.5, 3.6, 3.7_

- [x] 4.1 Create `CostTracker` class in `dev_agent/llm/cost_tracker.py`
  - Implement methods to record completion and embedding token usage
  - Implement `calculate_cost()` method with current Azure pricing
  - Implement `get_report()` method for usage summaries
  - Implement `check_budget_threshold()` method with warnings
  - Add per-phase cost tracking
  - Support session-level cost aggregation
  - _Requirements: 3.3, 3.4, 3.5, 3.6, 3.7_

- [x] 4.2 Write unit tests for cost tracker in `tests/test_cost_tracker.py`
  - Test token usage recording
  - Test cost calculation accuracy
  - Test budget threshold warnings
  - Test report generation
  - _Requirements: 9.1, 9.2_

- [x] 5. Implement embedding cache module
  - Create disk-based embedding cache
  - Implement SHA-256 content hashing
  - Add cache hit/miss tracking
  - _Requirements: 4.2, 4.3, 4.4, 4.5, 4.6, 4.8_

- [x] 5.1 Create `EmbeddingCache` class in `dev_agent/llm/embedding_cache.py`
  - Implement `get()` method to retrieve cached embeddings
  - Implement `set()` method to store embeddings with SHA-256 hash keys
  - Implement `_get_cache_key()` method for content hashing
  - Create cache directory structure in `.dev_agent/embedding_cache/`
  - Store cache metadata (model, dimension, timestamp)
  - Implement cache invalidation on model changes
  - _Requirements: 4.2, 4.3, 4.4, 4.5, 4.6_

- [x] 5.2 Write unit tests for embedding cache in `tests/test_embedding_cache.py`
  - Test cache hit scenarios
  - Test cache miss scenarios
  - Test cache key generation
  - Test cache invalidation
  - Test cache directory creation
  - _Requirements: 9.1, 9.2_


- [x] 6. Implement Azure OpenAI embedding client
  - Create embedding client with batch processing
  - Integrate with embedding cache
  - Add async batch processing
  - _Requirements: 4.1, 4.2, 4.7, 12.1, 12.2, 12.3_

- [x] 6.1 Create `AzureEmbeddingClient` class in `dev_agent/llm/embeddings.py`
  - Implement `IEmbeddingClient` interface
  - Implement `embed_text()` method for single text embedding
  - Implement `embed_batch()` method with batching (16 texts per API call)
  - Integrate with `EmbeddingCache` for cache lookups
  - Use `AsyncAzureOpenAI` for async API calls
  - Add progress tracking for large batches
  - Track cache hits and misses
  - Return 1536-dimensional vectors for text-embedding-ada-002
  - _Requirements: 4.1, 4.2, 4.7, 12.1, 12.2_

- [x] 6.2 Write unit tests for embedding client in `tests/test_azure_embedding_client.py`
  - Mock Azure OpenAI API calls
  - Test single text embedding
  - Test batch embedding with multiple texts
  - Test cache integration (hits and misses)
  - Test error handling for API failures
  - Test progress tracking
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [x] 7. Implement Azure OpenAI LLM client with retry logic
  - Create LLM client with async support
  - Implement retry logic with tenacity
  - Add streaming support
  - Integrate token counter
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_

- [x] 7.1 Create `AzureOpenAIClient` class in `dev_agent/llm/azure_client.py`
  - Implement `ILLMClient` interface
  - Initialize `AsyncAzureOpenAI` client with configuration
  - Implement `generate_completion()` method with async/await
  - Integrate `TokenCounter` for pre-flight token counting
  - Add retry decorator using tenacity for transient errors
  - Implement comprehensive error handling (auth, rate limit, timeout, bad request)
  - Map OpenAI exceptions to custom LLM exceptions
  - _Requirements: 2.1, 2.2, 2.3, 2.6, 2.7, 2.8_

- [x] 7.2 Implement streaming support in `AzureOpenAIClient`
  - Implement `generate_streaming()` method returning AsyncIterator
  - Use Azure OpenAI streaming API
  - Yield tokens as they arrive
  - Handle streaming errors gracefully
  - Save partial responses on errors
  - _Requirements: 2.4, 2.5, 7.6_

- [x] 7.3 Implement token counting and cost estimation in `AzureOpenAIClient`
  - Implement `count_tokens()` method using TokenCounter
  - Implement `estimate_cost()` method for prompt and completion tokens
  - Validate token limits before API calls
  - Record actual token usage from API responses
  - _Requirements: 3.1, 3.2, 3.8_

- [x] 7.4 Write unit tests for Azure LLM client in `tests/test_azure_llm_client.py`
  - Mock AsyncAzureOpenAI client
  - Test completion generation
  - Test streaming generation
  - Test token counting
  - Test cost estimation
  - Test retry logic with simulated failures
  - Test all error handling paths
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [-] 8. Implement prompt templates module
  - Create structured prompt templates
  - Implement context injection logic
  - Add template validation
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8_

- [x] 8.1 Create prompt template system in `dev_agent/llm/prompt_templates.py`
  - Define `PromptTemplate` dataclass with system prompt, user template, context requirements
  - Implement specification generation template
  - Implement design generation template
  - Implement code generation template
  - Implement task generation template
  - Add context injection methods
  - Add intelligent truncation for token limits
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8_

- [x] 8.2 Write unit tests for prompt templates in `tests/test_prompt_templates.py`
  - Test template rendering with context
  - Test context injection
  - Test intelligent truncation
  - Test all template types
  - _Requirements: 9.1, 9.2_

- [x] 9. Update configuration manager for enhanced Azure OpenAI config
  - Migrate from dataclass to Pydantic model
  - Add environment variable loading
  - Add configuration validation
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

- [x] 9.1 Update `ConfigManager` in `dev_agent/config/config_manager.py`
  - Replace `AzureOpenAIConfig` dataclass with Pydantic model
  - Add environment variable loading with precedence
  - Add configuration validation on load
  - Update `DevAgentConfig` to use new Pydantic model
  - Ensure backward compatibility with existing config files
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 9.2 Write unit tests for updated config manager in `tests/test_config_manager_azure.py`
  - Test environment variable loading
  - Test config file loading
  - Test validation errors
  - Test precedence (env vars > config file)
  - _Requirements: 9.1, 9.2_

- [x] 10. Update Azure OpenAI service to use new LLM client
  - Refactor existing service to use new abstraction
  - Maintain backward compatibility
  - Add deprecation warnings
  - _Requirements: 2.1, 2.2, 2.3, 11.1, 11.2_

- [x] 10.1 Refactor `AzureOpenAIService` in `dev_agent/services/azure_openai_service.py`
  - Update to use `AzureOpenAIClient` internally
  - Update to use `AzureEmbeddingClient` for embeddings
  - Maintain existing method signatures for backward compatibility
  - Add deprecation warnings for direct service usage
  - Update error handling to use new LLM exceptions
  - _Requirements: 2.1, 2.2, 11.1, 11.2_

- [x] 10.2 Update tests for Azure OpenAI service in `tests/test_azure_openai_service.py`
  - Update mocks to use new client structure
  - Test backward compatibility
  - Test deprecation warnings
  - _Requirements: 9.1, 9.2_

- [ ] 11. Update indexing engine to use new embedding client
  - Replace direct service calls with IEmbeddingClient
  - Add progress tracking
  - Integrate cost tracking
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 12.7_

- [ ] 11.1 Update `IndexingEngine` in `dev_agent/indexing/indexing_engine.py`
  - Accept `IEmbeddingClient` via dependency injection
  - Replace direct Azure service calls with embedding client
  - Add progress tracking for embedding generation (every 100 chunks)
  - Integrate with `CostTracker` for token usage
  - Add batch processing with configurable batch size
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 12.7_

- [ ] 11.2 Update tests for indexing engine in `tests/test_indexing_engine.py`
  - Mock IEmbeddingClient interface
  - Test progress tracking
  - Test cost tracking integration
  - Test batch processing
  - _Requirements: 9.1, 9.2_

- [x] 12. Update vector database to use new embedding client
  - Simplify to Azure OpenAI only
  - Remove local model fallback
  - Improve error handling
  - _Requirements: 6.1, 6.2, 11.3, 11.4, 11.5_

- [x] 12.1 Update `VectorDatabase` in `dev_agent/indexing/vector_database.py`
  - Accept `IEmbeddingClient` in constructor
  - Remove local model (sentence-transformers) fallback logic
  - Simplify to Azure OpenAI embeddings only
  - Update error handling to use LLM exceptions
  - Update cache integration
  - _Requirements: 6.1, 6.2, 11.3, 11.4, 11.5_

- [x] 12.2 Update tests for vector database in `tests/test_vector_database.py`
  - Mock IEmbeddingClient interface
  - Remove local model tests
  - Test Azure OpenAI integration
  - Test error handling
  - _Requirements: 9.1, 9.2_

- [ ] 13. Update specification generator to use new LLM client
  - Replace direct service calls with ILLMClient
  - Use prompt templates
  - Add context injection from vector search
  - Integrate cost tracking
  - _Requirements: 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8_

- [ ] 13.1 Update `SpecificationGenerator` in `dev_agent/generation/specification_generator.py`
  - Accept `ILLMClient` via dependency injection
  - Use specification prompt template from `prompt_templates.py`
  - Retrieve relevant code chunks via vector search
  - Inject context into prompt template
  - Validate token limits before generation
  - Integrate with `CostTracker`
  - Handle LLM exceptions appropriately
  - _Requirements: 6.2, 6.3, 6.4, 6.5, 6.6_

- [ ] 13.2 Update tests for specification generator in `tests/test_specification_generator.py`
  - Mock ILLMClient interface
  - Test prompt template usage
  - Test context injection
  - Test cost tracking
  - Test error handling
  - _Requirements: 9.1, 9.2_

- [ ] 14. Update design generator to use new LLM client
  - Replace direct service calls with ILLMClient
  - Use prompt templates
  - Add context injection
  - Integrate cost tracking
  - _Requirements: 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8_

- [ ] 14.1 Update `DesignGenerator` in `dev_agent/generation/design_generator.py`
  - Accept `ILLMClient` via dependency injection
  - Use design prompt template from `prompt_templates.py`
  - Retrieve relevant architecture patterns via vector search
  - Inject specification and context into prompt
  - Validate token limits before generation
  - Integrate with `CostTracker`
  - _Requirements: 6.2, 6.3, 6.4, 6.5, 6.6_

- [ ] 14.2 Update tests for design generator in `tests/test_design_generator.py`
  - Mock ILLMClient interface
  - Test prompt template usage
  - Test context injection
  - Test cost tracking
  - _Requirements: 9.1, 9.2_

- [ ] 15. Update task generator to use new LLM client
  - Replace direct service calls with ILLMClient
  - Use prompt templates
  - Add context injection
  - Integrate cost tracking
  - _Requirements: 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8_

- [ ] 15.1 Update `TaskGenerator` in `dev_agent/generation/task_generator.py`
  - Accept `ILLMClient` via dependency injection
  - Use task prompt template from `prompt_templates.py`
  - Inject design and requirements into prompt
  - Validate token limits before generation
  - Integrate with `CostTracker`
  - _Requirements: 6.2, 6.3, 6.4, 6.5, 6.6_

- [ ]* 15.2 Update tests for task generator in `tests/test_task_generator.py`
  - Mock ILLMClient interface
  - Test prompt template usage
  - Test cost tracking
  - _Requirements: 9.1, 9.2_

- [ ] 16. Update Python code generator to use new LLM client
  - Replace direct service calls with ILLMClient
  - Use prompt templates
  - Add context injection from similar code
  - Integrate cost tracking
  - _Requirements: 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8_

- [ ] 16.1 Update `PythonCodeGenerator` in `dev_agent/generation/python_code_generator.py`
  - Accept `ILLMClient` via dependency injection
  - Use code generation prompt template
  - Retrieve similar code implementations via vector search
  - Inject code patterns and style requirements into prompt
  - Validate token limits before generation
  - Integrate with `CostTracker`
  - _Requirements: 6.2, 6.3, 6.4, 6.5, 6.6_

- [ ] 16.2 Update tests for Python code generator in `tests/test_python_code_generator.py`
  - Mock ILLMClient interface
  - Test prompt template usage
  - Test context injection with similar code
  - Test cost tracking
  - _Requirements: 9.1, 9.2_

- [ ] 17. Update workflow manager to integrate cost tracking
  - Add cost tracking per phase
  - Display cost summaries
  - Save token usage to project state
  - Add budget warnings
  - _Requirements: 6.6, 6.7, 6.8, 3.4, 3.5, 3.6_

- [ ] 17.1 Update `WorkflowManager` in `dev_agent/workflow/workflow_manager.py`
  - Inject `CostTracker` instance
  - Track token usage per workflow phase
  - Display cost summary after each phase completion
  - Save token usage statistics to project state
  - Implement budget threshold warnings
  - Add cost report generation for entire workflow
  - _Requirements: 6.6, 6.7, 6.8, 3.4, 3.5, 3.6_

- [ ] 17.2 Update tests for workflow manager in `tests/test_workflow_manager.py`
  - Mock CostTracker
  - Test per-phase cost tracking
  - Test cost summary display
  - Test budget warnings
  - _Requirements: 9.1, 9.2_

- [ ] 18. Update CLI to display cost information
  - Add cost display to phase completions
  - Add cost report command
  - Add streaming progress for LLM operations
  - _Requirements: 3.5, 3.6, 12.4_

- [ ] 18.1 Update CLI commands in `dev_agent/cli/main.py` and `dev_agent/cli/interactive_cli.py`
  - Display token usage and cost after each phase
  - Add `cost-report` command to show session costs
  - Add streaming progress indicators for LLM operations
  - Display real-time token streaming in interactive mode
  - Add cost warnings when approaching budget limits
  - _Requirements: 3.5, 3.6, 12.4_

- [ ]* 18.2 Update CLI tests in `tests/test_cli_main.py` and `tests/test_interactive_cli.py`
  - Test cost display
  - Test cost report command
  - Test streaming progress
  - _Requirements: 9.1, 9.2_

- [ ] 19. Update Azure CLI configuration commands
  - Enhance interactive configuration wizard
  - Add connection testing
  - Add model validation
  - _Requirements: 8.3, 8.4, 8.6, 8.7_

- [ ] 19.1 Update `dev_agent/cli/azure_config.py`
  - Enhance `configure` command with better validation
  - Update `test` command to test both completion and embeddings
  - Add model deployment validation
  - Improve error messages with resolution guidance
  - Add configuration export/import commands
  - _Requirements: 8.3, 8.4, 8.6, 8.7_

- [ ]* 19.2 Update tests for Azure CLI config in `tests/test_azure_config.py`
  - Test configuration wizard
  - Test connection testing
  - Test validation
  - _Requirements: 9.1, 9.2_

- [ ] 20. Remove local model dependencies from core
  - Update pyproject.toml
  - Move sentence-transformers to optional dependencies
  - Update imports
  - _Requirements: 11.1, 11.2, 11.5, 11.6, 11.7_

- [ ] 20.1 Update `pyproject.toml`
  - Add `tiktoken>=0.6.0` and `tenacity>=8.2.0` to core dependencies
  - Move `sentence-transformers` to `[project.optional-dependencies]` under `local-embeddings`
  - Update dependency versions to latest
  - _Requirements: 11.1, 11.2, 11.5_

- [ ] 20.2 Remove local model imports and fallback logic
  - Remove sentence-transformers imports from core modules
  - Remove local model fallback logic from indexing engine
  - Remove local model fallback from vector database
  - Update error messages to guide users to Azure OpenAI setup
  - _Requirements: 11.2, 11.3, 11.4, 11.5_

- [ ] 20.3 Update documentation to reflect Azure OpenAI as primary provider
  - Update README.md to emphasize Azure OpenAI
  - Update installation guide with Azure OpenAI setup
  - Remove or deprecate local model documentation
  - _Requirements: 10.1, 10.2, 10.7, 11.7_

- [ ] 21. Create comprehensive documentation
  - Create Azure OpenAI setup guide
  - Create cost management guide
  - Create troubleshooting guide
  - Update API documentation
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8_

- [ ] 21.1 Create Azure OpenAI setup guide in `docs/configuration/azure-openai.md`
  - Step-by-step Azure OpenAI resource creation
  - Deployment configuration instructions
  - Environment variable setup
  - Configuration file setup
  - Connection testing
  - _Requirements: 10.1, 10.2, 10.3_

- [ ] 21.2 Create cost management guide in `docs/usage/cost-management.md`
  - Token usage explanation
  - Cost estimation methodology
  - Budget management strategies
  - Cost optimization tips
  - _Requirements: 10.4_

- [ ] 21.3 Create troubleshooting guide in `docs/configuration/troubleshooting.md`
  - Common error messages and solutions
  - Authentication issues
  - Rate limiting guidance
  - Timeout handling
  - Token limit errors
  - _Requirements: 10.5_

- [ ] 21.4 Create usage examples in `docs/examples/azure-setup.md`
  - Basic setup example
  - Configuration examples
  - Cost tracking examples
  - Never include real API keys (use placeholders)
  - _Requirements: 10.6, 10.7_

- [ ] 21.5 Update API documentation
  - Document all new LLM modules
  - Document configuration models
  - Document cost tracking APIs
  - Use mkdocstrings for auto-generation
  - _Requirements: 10.8_

- [ ] 22. Create integration tests with real Azure OpenAI API
  - Create gated integration tests
  - Test end-to-end workflows
  - Test cost tracking
  - Test error recovery
  - _Requirements: 9.6, 9.7, 9.8_

- [ ] 22.1 Create integration test suite in `tests/integration/test_azure_openai_integration.py`
  - Gate tests with `AZURE_OPENAI_INTEGRATION_TESTS=true` environment variable
  - Test end-to-end specification generation with real API
  - Test end-to-end code generation with real API
  - Test embedding generation and vector search with real API
  - Test cost tracking across workflow phases
  - Test error recovery and retry logic
  - Test streaming responses
  - _Requirements: 9.6, 9.7, 9.8_

- [ ] 23. Create example scripts demonstrating Azure OpenAI integration
  - Create specification generation example
  - Create code generation example
  - Create embedding example
  - Create cost tracking example
  - _Requirements: 10.6_

- [ ] 23.1 Create example scripts in `examples/`
  - Create `azure_specification_example.py` demonstrating spec generation
  - Create `azure_code_generation_example.py` demonstrating code generation
  - Create `azure_embedding_example.py` demonstrating embedding and search
  - Create `azure_cost_tracking_example.py` demonstrating cost tracking
  - Use placeholder API keys in examples
  - Add comprehensive comments
  - _Requirements: 10.6_

- [ ] 24. Update existing tests to use new mocking patterns
  - Update all tests to mock new LLM clients
  - Remove local model mocks
  - Ensure >90% coverage
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.8_

- [ ] 24.1 Update test fixtures in `tests/conftest.py`
  - Create `mock_llm_client` fixture
  - Create `mock_embedding_client` fixture
  - Create `mock_cost_tracker` fixture
  - Create `mock_token_counter` fixture
  - _Requirements: 9.1, 9.2_

- [ ] 24.2 Update existing test files to use new fixtures
  - Update all generation tests
  - Update all indexing tests
  - Update all workflow tests
  - Remove sentence-transformers mocks
  - _Requirements: 9.1, 9.2, 9.8_

- [ ] 25. Performance optimization and final testing
  - Optimize batch processing
  - Optimize cache performance
  - Run performance benchmarks
  - Verify all requirements met
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8_

- [ ] 25.1 Optimize batch processing and caching
  - Tune embedding batch size for optimal performance
  - Implement concurrent batch processing (up to 3 parallel)
  - Optimize cache lookup performance
  - Add cache warming for common queries
  - _Requirements: 12.1, 12.2, 12.3, 12.6_

- [ ] 25.2 Run performance benchmarks
  - Benchmark embedding generation (<5s per 100 chunks)
  - Benchmark completion generation (<10s for 1000 tokens)
  - Benchmark vector search (<100ms for 100K chunks)
  - Benchmark cache lookup (<10ms per embedding)
  - Document performance results
  - _Requirements: 12.1, 12.2, 12.3, 12.5, 12.6, 12.7, 12.8_

- [ ] 25.3 Final integration testing and validation
  - Run full test suite and verify >90% coverage
  - Run integration tests with real Azure OpenAI API
  - Test all workflow phases end-to-end
  - Verify all requirements are met
  - Test on Python 3.10, 3.11, 3.12, 3.13
  - Run code quality checks (ruff, mypy)
  - _Requirements: 9.8, all requirements_

## Testing Strategy

### Unit Tests (Marked with *)
- All unit tests MUST mock Azure OpenAI API calls
- Use pytest fixtures for consistent mocking
- Achieve >90% code coverage
- Tests MUST be fast (<1s each)

### Integration Tests
- Gated by `AZURE_OPENAI_INTEGRATION_TESTS=true`
- Use real Azure OpenAI API calls
- Test end-to-end workflows
- Verify cost tracking accuracy

### Performance Tests
- Benchmark critical operations
- Verify performance targets met
- Document results

## Success Criteria

The implementation will be considered complete when:

1. ✅ All 25 tasks are completed
2. ✅ All unit tests pass with >90% coverage
3. ✅ Integration tests pass with real Azure OpenAI API
4. ✅ Performance benchmarks meet targets
5. ✅ Documentation is complete and accurate
6. ✅ Code quality checks pass (ruff, mypy)
7. ✅ Local model dependencies removed from core
8. ✅ All workflow phases use Azure OpenAI
9. ✅ Cost tracking works across all operations
10. ✅ Steering docs reflect Azure OpenAI as primary provider

## Notes

- Tasks marked with `*` are optional unit test tasks that can be skipped if time is limited
- All core implementation tasks (non-test) are required
- Integration tests (task 22) should be run manually with real API credentials
- Performance optimization (task 25) should be done after all core functionality is working
