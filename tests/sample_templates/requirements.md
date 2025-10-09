# Requirements Document

## Introduction

This feature enhances the dev-agent's Azure OpenAI integration to support Azure AD (Azure Active Directory) authentication with custom headers, replacing the current simple API key authentication. The enhancement will allow users to authenticate using bearer tokens and include custom headers (like user_sid) in all Azure OpenAI API calls, while maintaining compatibility with the existing codebase and removing the dependency on langchain.

The current implementation uses the standard OpenAI SDK with simple API key authentication. The new implementation needs to support Azure AD authentication patterns commonly used in enterprise environments, where authentication tokens and custom headers are required for compliance and auditing purposes.

## Requirements

### Requirement 1: Azure AD Authentication Support

**User Story:** As a developer working in an enterprise environment, I want to authenticate to Azure OpenAI using Azure AD bearer tokens instead of simple API keys, so that I can comply with my organization's security policies.

#### Acceptance Criteria

1. WHEN the system initializes the Azure OpenAI client THEN it SHALL support both API key authentication and Azure AD bearer token authentication
2. WHEN Azure AD authentication is configured THEN the system SHALL include the bearer token in the Authorization header for all API requests
3. WHEN the configuration includes AZURE_OPENAI_TOKEN environment variable THEN the system SHALL use bearer token authentication instead of API key authentication
4. IF both API key and bearer token are provided THEN the system SHALL prioritize bearer token authentication
5. WHEN using bearer token authentication THEN the system SHALL set openai_api_type to "azure_ad"

### Requirement 2: Custom Headers Support

**User Story:** As a system administrator, I want to include custom headers (like user_sid) in all Azure OpenAI API calls, so that I can track and audit API usage by user for compliance purposes.

#### Acceptance Criteria

1. WHEN the system makes API calls to Azure OpenAI THEN it SHALL support adding custom headers to all requests
2. WHEN custom headers are configured THEN the system SHALL include them in both completion and embedding API calls
3. WHEN the configuration includes custom header environment variables THEN the system SHALL automatically add them to the default_headers
4. IF a custom header named "user_sid" is provided THEN the system SHALL include it in all API requests
5. WHEN custom headers are configured THEN they SHALL be applied consistently across all LLM and embedding operations

### Requirement 3: Configuration Model Enhancement

**User Story:** As a developer, I want to configure Azure AD authentication and custom headers through environment variables, so that I can easily manage different configurations across environments without code changes.

#### Acceptance Criteria

1. WHEN the system loads configuration THEN it SHALL support the following new environment variables:
   - AZURE_OPENAI_TOKEN (bearer token for Azure AD auth)
   - AZURE_CHAT_DEPLOYMENT_NAME (alternative to AZURE_OPENAI_DEPLOYMENT_NAME)
   - AZURE_OPENAI_USER_SID (custom user identifier header)
   - AZURE_OPENAI_CUSTOM_HEADERS (JSON string for additional headers)
2. WHEN AZURE_CHAT_DEPLOYMENT_NAME is provided THEN it SHALL be used as an alias for deployment_name
3. WHEN custom headers are provided as JSON string THEN the system SHALL parse and validate them
4. IF custom header parsing fails THEN the system SHALL log a warning and continue with available headers
5. WHEN the configuration model is serialized THEN bearer tokens SHALL be redacted like API keys

### Requirement 4: Backward Compatibility

**User Story:** As an existing dev-agent user, I want the new authentication features to work alongside my current API key setup, so that I don't have to change my existing configuration immediately.

#### Acceptance Criteria

1. WHEN no bearer token is provided THEN the system SHALL fall back to API key authentication
2. WHEN existing environment variables are used THEN the system SHALL continue to work without changes
3. WHEN the configuration file uses old field names THEN the system SHALL map them to new field names automatically
4. IF Azure AD authentication fails THEN the system SHALL provide clear error messages indicating the authentication method used
5. WHEN using API key authentication THEN the system SHALL NOT include bearer token headers

### Requirement 5: Direct OpenAI SDK Integration

**User Story:** As a developer, I want the Azure OpenAI integration to use the official OpenAI SDK directly without langchain dependencies, so that I have better control over API calls and reduce dependency complexity.

#### Acceptance Criteria

1. WHEN the system makes Azure OpenAI API calls THEN it SHALL use AsyncAzureOpenAI from the openai package directly
2. WHEN custom headers are configured THEN they SHALL be passed to the AsyncAzureOpenAI client initialization
3. WHEN bearer token authentication is used THEN the api_key parameter SHALL be set to the bearer token value
4. IF the openai SDK version is >=1.50.0 THEN the system SHALL use the default_headers parameter for custom headers
5. WHEN initializing the client THEN the system SHALL NOT depend on any langchain packages

### Requirement 6: Error Handling and Validation

**User Story:** As a developer, I want clear error messages when authentication fails, so that I can quickly diagnose and fix configuration issues.

#### Acceptance Criteria

1. WHEN bearer token authentication fails THEN the system SHALL provide an error message indicating Azure AD authentication was attempted
2. WHEN custom headers are malformed THEN the system SHALL log a warning with details about the parsing error
3. WHEN required authentication credentials are missing THEN the system SHALL provide guidance on which environment variables to set
4. IF the bearer token is expired THEN the system SHALL provide a clear error message about token expiration
5. WHEN authentication succeeds THEN the system SHALL log the authentication method used (API key or Azure AD)

### Requirement 7: Testing and Documentation

**User Story:** As a developer integrating this feature, I want comprehensive tests and documentation, so that I can understand how to configure and use Azure AD authentication correctly.

#### Acceptance Criteria

1. WHEN the feature is implemented THEN unit tests SHALL cover both API key and bearer token authentication paths
2. WHEN the feature is implemented THEN integration tests SHALL verify custom headers are included in API calls
3. WHEN the feature is documented THEN examples SHALL show both authentication methods
4. IF a user needs to migrate from API key to Azure AD THEN documentation SHALL provide a migration guide
5. WHEN the configuration is documented THEN all new environment variables SHALL be listed with examples
