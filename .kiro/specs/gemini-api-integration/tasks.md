# Implementation Plan

- [x] 1. Set up Gemini configuration and models
  - Create `GeminiConfig` Pydantic model in `dev_agent/models/llm_config.py` with all required fields (api_key, model_name, embedding_model, etc.)
  - Add `LLMProvider` enum to `dev_agent/models/enums.py` with AZURE_OPENAI and GEMINI values
  - Implement field validators for GeminiConfig (api_key format, model names, parameter ranges)
  - Add SecretStr handling for api_key with JSON redaction
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 10.1, 10.2, 10.3_

- [x] 2. Implement Gemini LLM client
  - Create `dev_agent/llm/gemini_client.py` implementing ILLMClient interface
  - Implement `__init__` method with google-generativeai SDK initialization
  - Implement `generate_completion` method with Gemini API calls and error handling
  - Implement `generate_streaming` method for async token streaming
  - Implement `count_tokens` method using Gemini's token counting API
  - Implement `estimate_cost` method based on Gemini pricing
  - Add retry logic with tenacity for transient errors (rate limits, timeouts)
  - Map Gemini exceptions to dev-agent LLM exceptions (PermissionDenied → LLMAuthenticationError, etc.)
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 2.1 Write unit tests for GeminiClient
  - Create `tests/test_gemini_client.py` with mocked Gemini API calls
  - Test generate_completion with various parameters
  - Test generate_streaming with async iteration
  - Test error handling for all Gemini exception types
  - Test retry logic with simulated failures
  - Test token counting and cost estimation
  - _Requirements: 8.1, 8.2, 8.3_

- [x] 3. Implement Gemini embedding client
  - Create `dev_agent/llm/gemini_embeddings.py` implementing IEmbeddingClient interface
  - Implement `__init__` method with caching support (reuse EmbeddingCache)
  - Implement `embed_text` method with cache checking and Gemini API calls
  - Implement `embed_batch` method with batch processing and progress tracking
  - Implement `dimension` property returning correct dimension for Gemini models (768)
  - Add error handling mapping Gemini exceptions to LLM exceptions
  - Ensure FAISS compatibility with Gemini embeddings
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 3.1 Write unit tests for GeminiEmbeddingClient
  - Create `tests/test_gemini_embeddings.py` with mocked Gemini API calls
  - Test embed_text with cache hits and misses
  - Test embed_batch with various batch sizes
  - Test error handling for embedding API failures
  - Test dimension property returns correct value
  - Test FAISS compatibility with generated embeddings
  - _Requirements: 8.1, 8.2, 8.3, 8.7_

- [x] 4. Create LLM factory and provider selection
  - Update `dev_agent/llm/__init__.py` with factory functions
  - Implement `create_llm_client(provider, config)` function with provider detection
  - Implement `create_embedding_client(provider, config, cache_dir)` function
  - Add provider auto-detection logic (check PREFERRED_LLM_PROVIDER env var)
  - Validate provider credentials before creating clients
  - Raise clear errors for unsupported providers or missing credentials
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 4.1 Write unit tests for LLM factory
  - Create `tests/test_llm_factory.py` testing factory functions
  - Test create_llm_client with Azure and Gemini providers
  - Test create_embedding_client with both providers
  - Test provider auto-detection from environment variables
  - Test error handling for invalid providers
  - Test credential validation
  - _Requirements: 8.1, 8.4_

- [x] 5. Update configuration manager for Gemini
  - Update `dev_agent/config/config_manager.py` to load Gemini configuration
  - Implement `load_gemini_config()` method reading from environment variables
  - Implement `get_llm_provider()` method determining active provider
  - Implement `validate_provider_config()` method checking credentials
  - Add support for PREFERRED_LLM_PROVIDER environment variable
  - Update existing methods to support multi-provider configuration
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 5.1 Write unit tests for configuration manager updates
  - Update `tests/test_config_manager.py` with Gemini configuration tests
  - Test load_gemini_config with various environment variable combinations
  - Test get_llm_provider with different PREFERRED_LLM_PROVIDER values
  - Test validate_provider_config for both providers
  - Test backward compatibility with existing Azure-only configuration
  - _Requirements: 8.1_

- [x] 6. Enhance cost tracking for multi-provider support
  - Update `dev_agent/llm/cost_tracker.py` to track costs per provider
  - Add `provider` parameter to `record_completion` and `record_embedding` methods
  - Update `get_report()` to separate costs by provider
  - Add Gemini pricing constants (per 1K tokens for different models)
  - Implement `get_provider_cost(provider)` method for provider-specific costs
  - Update cost estimation to use provider-specific pricing
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 6.1 Write unit tests for multi-provider cost tracking
  - Update `tests/test_cost_tracker.py` with multi-provider tests
  - Test recording costs for both Azure and Gemini
  - Test get_report separates providers correctly
  - Test get_provider_cost returns correct values
  - Test cost estimation with different providers and models
  - _Requirements: 8.1_

- [x] 7. Update existing code to use factory pattern
  - Update `dev_agent/generation/specification_generator.py` to use factory
  - Update `dev_agent/generation/design_generator.py` to use factory
  - Update `dev_agent/generation/task_generator.py` to use factory
  - Update `dev_agent/generation/python_code_generator.py` to use factory
  - Update `dev_agent/indexing/indexing_engine.py` to use embedding factory
  - Update `dev_agent/workflow/specification_workflow.py` to use factory
  - Ensure backward compatibility with existing Azure OpenAI usage
  - _Requirements: 4.4, 4.5_

- [x] 8. Add CLI support for provider selection
  - Update `dev_agent/cli/main.py` to show active provider in status command
  - Add provider selection option to `init` command
  - Display provider information in interactive CLI welcome message
  - Add `--provider` flag to relevant CLI commands
  - Update help text to mention Gemini support
  - _Requirements: 1.1, 1.2_

- [x] 9. Create integration tests
  - Create `tests/integration/test_gemini_integration.py` for real API tests
  - Add integration test for Gemini completion generation
  - Add integration test for Gemini embedding generation
  - Add integration test for provider switching
  - Gate tests with GEMINI_INTEGRATION_TESTS environment variable
  - Add integration test for FAISS compatibility with Gemini embeddings
  - _Requirements: 8.2, 8.4, 8.7_

- [x] 10. Update documentation
  - Create `docs/configuration/gemini-setup.md` with Gemini setup instructions
  - Create `docs/usage/provider-selection.md` explaining how to choose providers
  - Create `docs/examples/gemini-usage.md` with Gemini-specific examples
  - Update `docs/installation.md` to include google-generativeai dependency
  - Update `docs/configuration/environment.md` with Gemini environment variables
  - Update `docs/usage/cost-management.md` with Gemini pricing information
  - Update `README.md` to mention Gemini support in features
  - Create API documentation for GeminiClient and GeminiEmbeddingClient
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 11. Add dependencies and update project configuration
  - Add `google-generativeai>=0.3.0` to pyproject.toml dependencies
  - Add `google-api-core>=2.15.0` to pyproject.toml dependencies
  - Update requirements.txt to include new dependencies
  - Run `uv sync --dev` to install new dependencies
  - Update .gitignore if needed for Gemini-specific files
  - _Requirements: 1.1_

- [x] 12. Verify end-to-end functionality
  - Test complete workflow with Gemini provider (indexing → specification → design → implementation)
  - Verify embeddings work correctly with FAISS vector database
  - Test provider switching during a session
  - Verify cost tracking works across both providers
  - Test error handling and recovery for Gemini API failures
  - Verify backward compatibility with existing Azure OpenAI workflows
  - _Requirements: 8.4, 8.5, 8.6_
