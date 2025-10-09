# Implementation Plan

This implementation plan outlines the tasks needed to add Azure AD authentication support with custom headers to dev-agent's Azure OpenAI integration. The tasks build incrementally, starting with configuration model enhancements, then client modifications, testing, and finally documentation.

## Tasks

- [x] 1. Enhance AzureOpenAIConfig model with Azure AD authentication fields
  - Add `bearer_token: SecretStr | None` field for Azure AD authentication
  - Add `custom_headers: dict[str, str]` field for custom request headers
  - Add `user_sid: str | None` field for user session tracking
  - Add `openai_api_type: str` field (default: "azure", can be "azure_ad")
  - Make `api_key` field optional (either api_key or bearer_token required)
  - Add `@model_validator` to ensure at least one authentication method is provided
  - Add `get_auth_headers()` method to build authentication and custom headers dict
  - Add `get_api_key_value()` method to return appropriate credential (token or key)
  - Update `model_config` to redact bearer_token like api_key in JSON serialization
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 3.1, 3.2, 3.5, 4.1, 4.2_

- [x] 2. Update ConfigManager to load Azure AD configuration from environment variables
  - Add support for `AZURE_OPENAI_TOKEN` environment variable (bearer token)
  - Add support for `AZURE_CHAT_DEPLOYMENT_NAME` as alias for `AZURE_OPENAI_DEPLOYMENT_NAME`
  - Add support for `AZURE_OPENAI_USER_SID` environment variable
  - Add support for `AZURE_OPENAI_CUSTOM_HEADERS` environment variable (JSON string)
  - Implement JSON parsing for custom headers with error handling
  - Update `_load_azure_config_from_env()` to prioritize bearer token over API key
  - Add logic to merge user_sid into custom_headers dict
  - Add warning logging for malformed custom headers JSON
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 6.2, 6.3_

- [x] 3. Modify AzureOpenAIClient to support Azure AD authentication and custom headers
  - Add `_build_default_headers()` helper method to construct headers dict
  - Add `_get_api_key_value()` helper method to return token or API key
  - Update `__init__()` to call helper methods and pass headers to AsyncAzureOpenAI
  - Pass `default_headers` parameter to AsyncAzureOpenAI client initialization
  - Update initialization logging to indicate authentication method used (API Key vs Azure AD)
  - Ensure Authorization header is added when using bearer token
  - Ensure custom headers and user_sid are included in default_headers
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4, 2.5, 5.1, 5.2, 5.3, 5.4, 6.5_

- [x] 4. Modify AzureEmbeddingClient to support Azure AD authentication and custom headers
  - Add `_build_default_headers()` helper method (same logic as AzureOpenAIClient)
  - Add `_get_api_key_value()` helper method (same logic as AzureOpenAIClient)
  - Update `__init__()` to call helper methods and pass headers to AsyncAzureOpenAI
  - Pass `default_headers` parameter to AsyncAzureOpenAI client initialization
  - Update initialization logging to indicate authentication method used
  - Ensure consistency with AzureOpenAIClient implementation
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3, 2.4, 2.5, 5.1, 5.2, 5.3, 5.4, 6.5_

- [x] 5. Enhance error handling for Azure AD authentication failures
  - Update authentication error messages to indicate which method was used (API key or bearer token)
  - Add specific error message for expired bearer tokens
  - Update `LLMAuthenticationError` messages in both clients to reference authentication method
  - Add guidance in error messages about checking token expiration
  - Ensure error messages reference correct environment variables based on auth method
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 6. Create comprehensive unit tests for Azure AD authentication
- [x] 6.1 Create test file `tests/test_azure_ad_authentication.py`
  - Create fixtures for API key config and bearer token config
  - Create fixture for config with custom headers
  - Create fixture for config with user_sid
  - _Requirements: 7.1, 7.2_

- [x] 6.2 Add configuration validation tests
  - Test API key authentication configuration validates correctly
  - Test bearer token authentication configuration validates correctly
  - Test missing both credentials raises ValueError
  - Test both credentials provided (bearer token takes precedence)
  - Test custom headers parsing from dict
  - Test user_sid configuration
  - Test openai_api_type is set to "azure_ad" when bearer token is provided
  - Test openai_api_type remains "azure" when only API key is provided
  - _Requirements: 1.4, 3.5, 7.1_

- [x] 6.3 Add client initialization tests
  - Test AzureOpenAIClient initializes with API key config
  - Test AzureOpenAIClient initializes with bearer token config
  - Test AzureEmbeddingClient initializes with API key config
  - Test AzureEmbeddingClient initializes with bearer token config
  - Test custom headers are passed to AsyncAzureOpenAI client
  - Test default_headers parameter is used correctly
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 7.1_

- [x] 6.4 Add header building tests
  - Test `_build_default_headers()` with API key (no Authorization header)
  - Test `_build_default_headers()` with bearer token (includes Authorization header)
  - Test custom headers are merged into default_headers
  - Test user_sid is added to headers when configured
  - Test empty custom headers when not configured
  - Test Authorization header format is "Bearer {token}"
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 7.1_

- [x] 6.5 Add authentication method detection tests
  - Test `_get_api_key_value()` returns API key when no bearer token
  - Test `_get_api_key_value()` returns bearer token when configured
  - Test `get_auth_headers()` method on config model
  - Test `get_api_key_value()` method on config model
  - _Requirements: 1.5, 7.1_

- [x] 6.6 Add backward compatibility tests
  - Test existing API key configuration still works unchanged
  - Test existing environment variables work without modification
  - Test config file with old format loads correctly
  - Test migration scenario from API key to bearer token
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 7.1_

- [x] 6.7 Add ConfigManager environment variable tests
  - Test `AZURE_OPENAI_TOKEN` environment variable is loaded
  - Test `AZURE_CHAT_DEPLOYMENT_NAME` alias works correctly
  - Test `AZURE_OPENAI_USER_SID` is loaded and added to headers
  - Test `AZURE_OPENAI_CUSTOM_HEADERS` JSON parsing
  - Test malformed JSON in custom headers logs warning and continues
  - Test bearer token takes precedence over API key when both are set
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 6.2, 7.1_

- [x] 6.8 Add integration tests with mocked Azure OpenAI API
  - Mock AsyncAzureOpenAI to verify headers are passed correctly
  - Verify Authorization header format in mocked calls
  - Verify custom headers are included in API requests
  - Verify user_sid appears in request headers
  - Test completion generation with Azure AD auth (mocked)
  - Test embedding generation with Azure AD auth (mocked)
  - _Requirements: 7.2, 7.3_

- [x] 7. Update documentation for Azure AD authentication
- [x] 7.1 Update `docs/configuration/azure-openai.md`
  - Add "Azure AD Authentication" section with overview
  - Document all new environment variables with descriptions
  - Provide configuration examples for API key and Azure AD auth
  - Add example for custom headers configuration
  - Add troubleshooting section for authentication issues
  - Add section on token expiration and refresh
  - _Requirements: 7.3, 7.4, 7.5_

- [x] 7.2 Create or update `docs/examples/azure-setup.md`
  - Add step-by-step Azure AD setup example
  - Show how to obtain bearer tokens
  - Demonstrate custom headers configuration
  - Show user_sid usage for auditing
  - Provide complete working examples
  - _Requirements: 7.3, 7.4_

- [x] 7.3 Update `README.md`
  - Add Azure AD authentication mention in features section
  - Update environment variables section with new variables
  - Add link to detailed Azure AD documentation
  - Update quick start guide if needed
  - _Requirements: 7.3, 7.5_

- [x] 7.4 Update `.kiro/steering/azure-openai.md` steering rules
  - Add Azure AD authentication configuration standards
  - Document custom headers usage patterns
  - Add security considerations for bearer tokens
  - Update configuration examples to include Azure AD
  - Add best practices for token management
  - _Requirements: 7.3, 7.5_

- [x] 8. Add migration guide and examples
  - Create migration guide document showing how to switch from API key to Azure AD
  - Provide side-by-side configuration examples
  - Document environment variable precedence rules
  - Add FAQ section for common migration questions
  - Include security best practices for token storage
  - _Requirements: 4.1, 4.2, 4.3, 7.3, 7.4_

## Notes

- All tasks build incrementally on previous tasks
- Testing tasks (6.x) should be completed after implementation tasks (1-5)
- Documentation tasks (7.x, 8) should be completed after testing
- Optional tasks marked with * can be skipped for MVP
- Each task references specific requirements from the requirements document
- Backward compatibility is maintained throughout all changes
- Security is prioritized with SecretStr usage and proper token handling
