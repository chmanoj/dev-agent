"""Comprehensive unit tests for Azure AD authentication support.

This test module validates the Azure AD authentication features including:
- Configuration validation with API key and bearer token
- Client initialization with different authentication methods
- Header building and authentication method detection
- Backward compatibility with existing API key authentication
- Environment variable loading and parsing
"""

from __future__ import annotations

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import SecretStr, ValidationError

from dev_agent.config.config_manager import ConfigManager
from dev_agent.llm.azure_client import AzureOpenAIClient
from dev_agent.llm.embeddings import AzureEmbeddingClient
from dev_agent.models.llm_config import AzureOpenAIConfig

# ============================================================================
# Fixtures (Task 6.1)
# ============================================================================


@pytest.fixture
def api_key_config():
    """Fixture for Azure OpenAI config with API key authentication.

    Returns:
        AzureOpenAIConfig configured with API key authentication
    """
    return AzureOpenAIConfig(
        endpoint="https://test-resource.openai.azure.com/",
        api_key=SecretStr("test-api-key-12345"),
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
        api_version="2024-02-15-preview",
        max_tokens=4000,
        temperature=0.7,
    )


@pytest.fixture
def bearer_token_config():
    """Fixture for Azure OpenAI config with bearer token authentication.

    Returns:
        AzureOpenAIConfig configured with Azure AD bearer token authentication
    """
    return AzureOpenAIConfig(
        endpoint="https://test-resource.openai.azure.com/",
        bearer_token=SecretStr("eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6InRlc3QifQ.test.token"),
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
        api_version="2024-02-15-preview",
        max_tokens=4000,
        temperature=0.7,
    )


@pytest.fixture
def config_with_custom_headers():
    """Fixture for config with custom headers.

    Returns:
        AzureOpenAIConfig with custom headers configured
    """
    return AzureOpenAIConfig(
        endpoint="https://test-resource.openai.azure.com/",
        bearer_token=SecretStr("eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6InRlc3QifQ.test.token"),
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
        custom_headers={
            "department": "engineering",
            "project": "dev-agent",
            "custom-header": "custom-value",
        },
    )


@pytest.fixture
def config_with_user_sid():
    """Fixture for config with user_sid.

    Returns:
        AzureOpenAIConfig with user_sid configured
    """
    return AzureOpenAIConfig(
        endpoint="https://test-resource.openai.azure.com/",
        bearer_token=SecretStr("eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6InRlc3QifQ.test.token"),
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
        user_sid="A123456",
    )


@pytest.fixture
def mock_azure_client():
    """Mock AsyncAzureOpenAI client for testing.

    Returns:
        AsyncMock configured to simulate Azure OpenAI API responses
    """
    client = AsyncMock()

    # Mock completion response
    client.chat.completions.create = AsyncMock(
        return_value=MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(content="Generated response"),
                    finish_reason="stop",
                )
            ],
            usage=MagicMock(
                prompt_tokens=100,
                completion_tokens=200,
                total_tokens=300,
            ),
        )
    )

    # Mock embeddings response
    client.embeddings.create = AsyncMock(
        return_value=MagicMock(
            data=[MagicMock(embedding=[0.1] * 1536)],
            usage=MagicMock(total_tokens=50),
        )
    )

    return client


# ============================================================================
# Configuration Validation Tests (Task 6.2)
# ============================================================================


class TestConfigurationValidation:
    """Test configuration validation for different authentication methods."""

    def test_api_key_authentication_validates_correctly(self, api_key_config):
        """Test that API key authentication configuration validates correctly."""
        assert api_key_config.api_key is not None
        assert api_key_config.bearer_token is None
        assert api_key_config.openai_api_type == "azure"
        assert api_key_config.endpoint == "https://test-resource.openai.azure.com/"
        assert api_key_config.deployment_name == "gpt-4"

    def test_bearer_token_authentication_validates_correctly(self, bearer_token_config):
        """Test that bearer token authentication configuration validates correctly."""
        assert bearer_token_config.bearer_token is not None
        assert bearer_token_config.api_key is None
        assert bearer_token_config.openai_api_type == "azure_ad"
        assert bearer_token_config.endpoint == "https://test-resource.openai.azure.com/"
        assert bearer_token_config.deployment_name == "gpt-4"

    def test_missing_both_credentials_raises_value_error(self):
        """Test that missing both credentials raises ValueError."""
        with pytest.raises(ValidationError) as exc_info:
            AzureOpenAIConfig(
                endpoint="https://test-resource.openai.azure.com/",
                deployment_name="gpt-4",
                embedding_deployment="text-embedding-ada-002",
            )

        # Check that the error message mentions authentication
        error_str = str(exc_info.value)
        assert "api_key or bearer_token" in error_str.lower()

    def test_both_credentials_provided_bearer_token_takes_precedence(self):
        """Test that when both credentials are provided, bearer token takes precedence."""
        config = AzureOpenAIConfig(
            endpoint="https://test-resource.openai.azure.com/",
            api_key=SecretStr("test-api-key"),
            bearer_token=SecretStr("test-bearer-token"),
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )

        # Bearer token should take precedence
        assert config.openai_api_type == "azure_ad"
        assert config.bearer_token is not None
        assert config.api_key is not None  # Both are present

    def test_custom_headers_parsing_from_dict(self, config_with_custom_headers):
        """Test that custom headers are parsed correctly from dict."""
        assert config_with_custom_headers.custom_headers == {
            "department": "engineering",
            "project": "dev-agent",
            "custom-header": "custom-value",
        }
        assert len(config_with_custom_headers.custom_headers) == 3

    def test_user_sid_configuration(self, config_with_user_sid):
        """Test that user_sid is configured correctly."""
        assert config_with_user_sid.user_sid == "A123456"

    def test_openai_api_type_set_to_azure_ad_with_bearer_token(self, bearer_token_config):
        """Test that openai_api_type is set to 'azure_ad' when bearer token is provided."""
        assert bearer_token_config.openai_api_type == "azure_ad"

    def test_openai_api_type_remains_azure_with_api_key(self, api_key_config):
        """Test that openai_api_type remains 'azure' when only API key is provided."""
        assert api_key_config.openai_api_type == "azure"


# ============================================================================
# Client Initialization Tests (Task 6.3)
# ============================================================================


class TestClientInitialization:
    """Test client initialization with different authentication methods."""

    def test_azure_openai_client_initializes_with_api_key(self, api_key_config, mock_azure_client):
        """Test that AzureOpenAIClient initializes correctly with API key config."""
        client = AzureOpenAIClient(api_key_config, client=mock_azure_client)

        assert client.config == api_key_config
        assert client.client == mock_azure_client
        assert client.token_counter is not None

    def test_azure_openai_client_initializes_with_bearer_token(self, bearer_token_config, mock_azure_client):
        """Test that AzureOpenAIClient initializes correctly with bearer token config."""
        client = AzureOpenAIClient(bearer_token_config, client=mock_azure_client)

        assert client.config == bearer_token_config
        assert client.client == mock_azure_client
        assert client.token_counter is not None

    def test_azure_embedding_client_initializes_with_api_key(self, api_key_config, mock_azure_client):
        """Test that AzureEmbeddingClient initializes correctly with API key config."""
        client = AzureEmbeddingClient(api_key_config, client=mock_azure_client)

        assert client.config == api_key_config
        assert client.client == mock_azure_client
        assert client.model == "text-embedding-ada-002"

    def test_azure_embedding_client_initializes_with_bearer_token(self, bearer_token_config, mock_azure_client):
        """Test that AzureEmbeddingClient initializes correctly with bearer token config."""
        client = AzureEmbeddingClient(bearer_token_config, client=mock_azure_client)

        assert client.config == bearer_token_config
        assert client.client == mock_azure_client
        assert client.model == "text-embedding-ada-002"

    @patch("dev_agent.llm.azure_client.AsyncAzureOpenAI")
    def test_custom_headers_passed_to_async_azure_openai_client(self, mock_async_azure, config_with_custom_headers):
        """Test that custom headers are passed to AsyncAzureOpenAI client."""
        AzureOpenAIClient(config_with_custom_headers)

        # Verify AsyncAzureOpenAI was called with default_headers
        mock_async_azure.assert_called_once()
        call_kwargs = mock_async_azure.call_args.kwargs

        assert "default_headers" in call_kwargs
        headers = call_kwargs["default_headers"]

        # Should include Authorization header and custom headers
        assert "Authorization" in headers
        assert "department" in headers
        assert "project" in headers
        assert "custom-header" in headers

    @patch("dev_agent.llm.azure_client.AsyncAzureOpenAI")
    def test_default_headers_parameter_used_correctly(self, mock_async_azure, bearer_token_config):
        """Test that default_headers parameter is used correctly."""
        AzureOpenAIClient(bearer_token_config)

        # Verify AsyncAzureOpenAI was called with default_headers
        mock_async_azure.assert_called_once()
        call_kwargs = mock_async_azure.call_args.kwargs

        assert "default_headers" in call_kwargs
        assert isinstance(call_kwargs["default_headers"], dict)


# ============================================================================
# Header Building Tests (Task 6.4)
# ============================================================================


class TestHeaderBuilding:
    """Test header building logic for different authentication methods."""

    def test_build_default_headers_with_api_key_no_authorization_header(self, api_key_config):
        """Test that _build_default_headers with API key does not include Authorization header."""
        client = AzureOpenAIClient(api_key_config, client=AsyncMock())
        headers = client._build_default_headers()

        # Should not include Authorization header for API key auth
        assert "Authorization" not in headers

    def test_build_default_headers_with_bearer_token_includes_authorization(self, bearer_token_config):
        """Test that _build_default_headers with bearer token includes Authorization header."""
        client = AzureOpenAIClient(bearer_token_config, client=AsyncMock())
        headers = client._build_default_headers()

        # Should include Authorization header for bearer token auth
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Bearer ")

    def test_custom_headers_merged_into_default_headers(self, config_with_custom_headers):
        """Test that custom headers are merged into default_headers."""
        client = AzureOpenAIClient(config_with_custom_headers, client=AsyncMock())
        headers = client._build_default_headers()

        # Should include all custom headers
        assert "department" in headers
        assert headers["department"] == "engineering"
        assert "project" in headers
        assert headers["project"] == "dev-agent"
        assert "custom-header" in headers
        assert headers["custom-header"] == "custom-value"

    def test_user_sid_added_to_headers_when_configured(self, config_with_user_sid):
        """Test that user_sid is added to headers when configured."""
        client = AzureOpenAIClient(config_with_user_sid, client=AsyncMock())
        headers = client._build_default_headers()

        # Should include user_sid header
        assert "user_sid" in headers
        assert headers["user_sid"] == "A123456"

    def test_empty_custom_headers_when_not_configured(self, api_key_config):
        """Test that custom headers are empty when not configured."""
        client = AzureOpenAIClient(api_key_config, client=AsyncMock())
        headers = client._build_default_headers()

        # Should not include any custom headers
        assert "department" not in headers
        assert "project" not in headers
        assert "user_sid" not in headers

    def test_authorization_header_format_is_bearer_token(self, bearer_token_config):
        """Test that Authorization header format is 'Bearer {token}'."""
        client = AzureOpenAIClient(bearer_token_config, client=AsyncMock())
        headers = client._build_default_headers()

        # Check Authorization header format
        assert "Authorization" in headers
        auth_header = headers["Authorization"]
        assert auth_header.startswith("Bearer ")

        # Extract token and verify it matches
        token = auth_header.replace("Bearer ", "")
        assert token == bearer_token_config.bearer_token.get_secret_value()


# ============================================================================
# Authentication Method Detection Tests (Task 6.5)
# ============================================================================


class TestAuthenticationMethodDetection:
    """Test authentication method detection logic."""

    def test_get_api_key_value_returns_api_key_when_no_bearer_token(self, api_key_config):
        """Test that _get_api_key_value returns API key when no bearer token."""
        client = AzureOpenAIClient(api_key_config, client=AsyncMock())
        api_key_value = client._get_api_key_value()

        assert api_key_value == "test-api-key-12345"

    def test_get_api_key_value_returns_bearer_token_when_configured(self, bearer_token_config):
        """Test that _get_api_key_value returns bearer token when configured."""
        client = AzureOpenAIClient(bearer_token_config, client=AsyncMock())
        api_key_value = client._get_api_key_value()

        # Should return bearer token value
        assert api_key_value.startswith("eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6InRlc3QifQ")

    def test_get_auth_headers_method_on_config_model(self, bearer_token_config):
        """Test get_auth_headers() method on config model."""
        headers = bearer_token_config.get_auth_headers()

        # Should include Authorization header
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Bearer ")

    def test_get_api_key_value_method_on_config_model_with_bearer_token(self, bearer_token_config):
        """Test get_api_key_value() method on config model with bearer token."""
        api_key_value = bearer_token_config.get_api_key_value()

        # Should return bearer token value
        assert api_key_value.startswith("eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6InRlc3QifQ")

    def test_get_api_key_value_method_on_config_model_with_api_key(self, api_key_config):
        """Test get_api_key_value() method on config model with API key."""
        api_key_value = api_key_config.get_api_key_value()

        # Should return API key value
        assert api_key_value == "test-api-key-12345"


# ============================================================================
# Backward Compatibility Tests (Task 6.6)
# ============================================================================


class TestBackwardCompatibility:
    """Test backward compatibility with existing API key authentication."""

    def test_existing_api_key_configuration_still_works(self, api_key_config, mock_azure_client):
        """Test that existing API key configuration still works unchanged."""
        # Should initialize without errors
        client = AzureOpenAIClient(api_key_config, client=mock_azure_client)

        assert client.config.api_key is not None
        assert client.config.bearer_token is None
        assert client.config.openai_api_type == "azure"

    def test_existing_environment_variables_work_without_modification(self):
        """Test that existing environment variables work without modification."""
        env_vars = {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "test-api-key",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = ConfigManager._load_azure_config_from_env()

            assert config is not None
            assert config.api_key is not None
            assert config.bearer_token is None
            assert config.openai_api_type == "azure"

    def test_config_file_with_old_format_loads_correctly(self):
        """Test that config file with old format loads correctly."""
        # Old format config (API key only)
        old_config = AzureOpenAIConfig(
            endpoint="https://test.openai.azure.com/",
            api_key=SecretStr("old-api-key"),
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )

        # Should load without errors
        assert old_config.api_key is not None
        assert old_config.bearer_token is None
        assert old_config.openai_api_type == "azure"

    def test_migration_scenario_from_api_key_to_bearer_token(self):
        """Test migration scenario from API key to bearer token."""
        # Start with API key config
        api_key_config = AzureOpenAIConfig(
            endpoint="https://test.openai.azure.com/",
            api_key=SecretStr("old-api-key"),
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )

        assert api_key_config.openai_api_type == "azure"

        # Migrate to bearer token config
        bearer_token_config = AzureOpenAIConfig(
            endpoint="https://test.openai.azure.com/",
            bearer_token=SecretStr("new-bearer-token"),
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )

        assert bearer_token_config.openai_api_type == "azure_ad"
        assert bearer_token_config.bearer_token is not None


# ============================================================================
# ConfigManager Environment Variable Tests (Task 6.7)
# ============================================================================


class TestConfigManagerEnvironmentVariables:
    """Test ConfigManager environment variable loading."""

    def test_azure_openai_token_environment_variable_loaded(self):
        """Test that AZURE_OPENAI_TOKEN environment variable is loaded."""
        env_vars = {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_TOKEN": "test-bearer-token",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = ConfigManager._load_azure_config_from_env()

            assert config is not None
            assert config.bearer_token is not None
            assert config.bearer_token.get_secret_value() == "test-bearer-token"

    def test_azure_chat_deployment_name_alias_works_correctly(self):
        """Test that AZURE_CHAT_DEPLOYMENT_NAME alias works correctly."""
        env_vars = {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "test-api-key",
            "AZURE_CHAT_DEPLOYMENT_NAME": "gpt-4-turbo",  # Using alias
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = ConfigManager._load_azure_config_from_env()

            assert config is not None
            assert config.deployment_name == "gpt-4-turbo"

    def test_azure_openai_user_sid_loaded_and_added_to_headers(self):
        """Test that AZURE_OPENAI_USER_SID is loaded and added to headers."""
        env_vars = {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_TOKEN": "test-bearer-token",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
            "AZURE_OPENAI_USER_SID": "A123456",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = ConfigManager._load_azure_config_from_env()

            assert config is not None
            assert config.user_sid == "A123456"

            # Check that user_sid is in custom_headers
            assert "user_sid" in config.custom_headers
            assert config.custom_headers["user_sid"] == "A123456"

    def test_azure_openai_custom_headers_json_parsing(self):
        """Test that AZURE_OPENAI_CUSTOM_HEADERS JSON parsing works."""
        custom_headers_json = json.dumps({
            "department": "engineering",
            "project": "dev-agent",
        })

        env_vars = {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_TOKEN": "test-bearer-token",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
            "AZURE_OPENAI_CUSTOM_HEADERS": custom_headers_json,
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = ConfigManager._load_azure_config_from_env()

            assert config is not None
            assert "department" in config.custom_headers
            assert config.custom_headers["department"] == "engineering"
            assert "project" in config.custom_headers
            assert config.custom_headers["project"] == "dev-agent"

    def test_malformed_json_in_custom_headers_logs_warning_and_continues(self):
        """Test that malformed JSON in custom headers logs warning and continues."""
        env_vars = {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_TOKEN": "test-bearer-token",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
            "AZURE_OPENAI_CUSTOM_HEADERS": "not-valid-json{",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            # Should not raise an error, just log a warning
            config = ConfigManager._load_azure_config_from_env()

            assert config is not None
            # Custom headers should be empty due to parsing error
            assert len(config.custom_headers) == 0

    def test_bearer_token_takes_precedence_over_api_key_when_both_set(self):
        """Test that bearer token takes precedence over API key when both are set."""
        env_vars = {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "test-api-key",
            "AZURE_OPENAI_TOKEN": "test-bearer-token",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = ConfigManager._load_azure_config_from_env()

            assert config is not None
            # Both should be present
            assert config.api_key is not None
            assert config.bearer_token is not None
            # But openai_api_type should be azure_ad (bearer token takes precedence)
            assert config.openai_api_type == "azure_ad"


# ============================================================================
# Integration Tests with Mocked Azure OpenAI API (Task 6.8)
# ============================================================================


class TestMockedAzureOpenAIIntegration:
    """Integration tests with mocked Azure OpenAI API to verify header passing."""

    @pytest.mark.asyncio
    async def test_mock_async_azure_openai_headers_passed_correctly(self, bearer_token_config):
        """Test that AsyncAzureOpenAI is initialized with correct headers."""
        with patch("dev_agent.llm.azure_client.AsyncAzureOpenAI") as mock_async_azure:
            # Create mock client instance
            mock_client_instance = AsyncMock()
            mock_async_azure.return_value = mock_client_instance

            # Initialize client
            client = AzureOpenAIClient(bearer_token_config)

            # Verify AsyncAzureOpenAI was called with correct parameters
            mock_async_azure.assert_called_once()
            call_kwargs = mock_async_azure.call_args.kwargs

            # Verify default_headers parameter exists
            assert "default_headers" in call_kwargs
            headers = call_kwargs["default_headers"]

            # Verify Authorization header is present and correctly formatted
            assert "Authorization" in headers
            assert headers["Authorization"].startswith("Bearer ")
            assert bearer_token_config.bearer_token.get_secret_value() in headers["Authorization"]

    @pytest.mark.asyncio
    async def test_authorization_header_format_in_mocked_calls(self, bearer_token_config):
        """Test that Authorization header format is correct in mocked API calls."""
        with patch("dev_agent.llm.azure_client.AsyncAzureOpenAI") as mock_async_azure:
            # Create mock client instance
            mock_client_instance = AsyncMock()
            mock_async_azure.return_value = mock_client_instance

            # Initialize client
            AzureOpenAIClient(bearer_token_config)

            # Get the headers that were passed
            call_kwargs = mock_async_azure.call_args.kwargs
            headers = call_kwargs["default_headers"]

            # Verify Authorization header format
            auth_header = headers["Authorization"]
            assert auth_header.startswith("Bearer ")

            # Extract token and verify it matches the config
            token_in_header = auth_header.replace("Bearer ", "")
            expected_token = bearer_token_config.bearer_token.get_secret_value()
            assert token_in_header == expected_token

    @pytest.mark.asyncio
    async def test_custom_headers_included_in_api_requests(self, config_with_custom_headers):
        """Test that custom headers are included in API requests."""
        with patch("dev_agent.llm.azure_client.AsyncAzureOpenAI") as mock_async_azure:
            # Create mock client instance
            mock_client_instance = AsyncMock()
            mock_async_azure.return_value = mock_client_instance

            # Initialize client
            AzureOpenAIClient(config_with_custom_headers)

            # Get the headers that were passed
            call_kwargs = mock_async_azure.call_args.kwargs
            headers = call_kwargs["default_headers"]

            # Verify all custom headers are present
            assert "department" in headers
            assert headers["department"] == "engineering"
            assert "project" in headers
            assert headers["project"] == "dev-agent"
            assert "custom-header" in headers
            assert headers["custom-header"] == "custom-value"

    @pytest.mark.asyncio
    async def test_user_sid_appears_in_request_headers(self, config_with_user_sid):
        """Test that user_sid appears in request headers."""
        with patch("dev_agent.llm.azure_client.AsyncAzureOpenAI") as mock_async_azure:
            # Create mock client instance
            mock_client_instance = AsyncMock()
            mock_async_azure.return_value = mock_client_instance

            # Initialize client
            AzureOpenAIClient(config_with_user_sid)

            # Get the headers that were passed
            call_kwargs = mock_async_azure.call_args.kwargs
            headers = call_kwargs["default_headers"]

            # Verify user_sid is present
            assert "user_sid" in headers
            assert headers["user_sid"] == "A123456"

    @pytest.mark.asyncio
    async def test_completion_generation_with_azure_ad_auth_mocked(self, bearer_token_config):
        """Test completion generation with Azure AD authentication (mocked)."""
        # Create mock client with completion response
        mock_client = AsyncMock()
        mock_response = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(content="Generated code here"),
                    finish_reason="stop",
                )
            ],
            usage=MagicMock(
                prompt_tokens=100,
                completion_tokens=200,
                total_tokens=300,
            ),
        )
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        # Initialize client with mocked Azure client
        client = AzureOpenAIClient(bearer_token_config, client=mock_client)

        # Generate completion
        result = await client.generate_completion(
            prompt="Write a Python function",
            system_prompt="You are a code generator",
        )

        # Verify the result
        assert result == "Generated code here"

        # Verify the API was called
        mock_client.chat.completions.create.assert_called_once()

        # Verify the call parameters
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4"
        assert len(call_kwargs["messages"]) == 2
        assert call_kwargs["messages"][0]["role"] == "system"
        assert call_kwargs["messages"][1]["role"] == "user"

    @pytest.mark.asyncio
    async def test_embedding_generation_with_azure_ad_auth_mocked(self, bearer_token_config, tmp_path):
        """Test embedding generation with Azure AD authentication (mocked)."""
        # Create mock client with embedding response
        mock_client = AsyncMock()
        mock_response = MagicMock(
            data=[MagicMock(embedding=[0.1] * 1536)],
            usage=MagicMock(total_tokens=50),
        )
        mock_client.embeddings.create = AsyncMock(return_value=mock_response)

        # Initialize embedding client with mocked Azure client and empty cache
        client = AzureEmbeddingClient(bearer_token_config, cache_dir=tmp_path / "cache", client=mock_client)

        # Generate embedding (unique text to avoid cache hits)
        import uuid
        unique_text = f"Sample text for embedding {uuid.uuid4()}"
        result = await client.embed_text(unique_text)

        # Verify the result
        assert len(result) == 1536
        assert all(x == 0.1 for x in result)

        # Verify the API was called
        mock_client.embeddings.create.assert_called_once()

        # Verify the call parameters
        call_kwargs = mock_client.embeddings.create.call_args.kwargs
        assert call_kwargs["model"] == "text-embedding-ada-002"
        assert call_kwargs["input"] == unique_text

    @pytest.mark.asyncio
    async def test_embedding_client_headers_passed_correctly(self, bearer_token_config):
        """Test that embedding client passes headers correctly to AsyncAzureOpenAI."""
        with patch("dev_agent.llm.embeddings.AsyncAzureOpenAI") as mock_async_azure:
            # Create mock client instance
            mock_client_instance = AsyncMock()
            mock_async_azure.return_value = mock_client_instance

            # Initialize embedding client
            AzureEmbeddingClient(bearer_token_config)

            # Verify AsyncAzureOpenAI was called with correct parameters
            mock_async_azure.assert_called_once()
            call_kwargs = mock_async_azure.call_args.kwargs

            # Verify default_headers parameter exists
            assert "default_headers" in call_kwargs
            headers = call_kwargs["default_headers"]

            # Verify Authorization header is present
            assert "Authorization" in headers
            assert headers["Authorization"].startswith("Bearer ")

    @pytest.mark.asyncio
    async def test_embedding_client_with_custom_headers(self, config_with_custom_headers):
        """Test that embedding client includes custom headers."""
        with patch("dev_agent.llm.embeddings.AsyncAzureOpenAI") as mock_async_azure:
            # Create mock client instance
            mock_client_instance = AsyncMock()
            mock_async_azure.return_value = mock_client_instance

            # Initialize embedding client
            AzureEmbeddingClient(config_with_custom_headers)

            # Get the headers that were passed
            call_kwargs = mock_async_azure.call_args.kwargs
            headers = call_kwargs["default_headers"]

            # Verify custom headers are present
            assert "department" in headers
            assert headers["department"] == "engineering"
            assert "project" in headers
            assert headers["project"] == "dev-agent"

    @pytest.mark.asyncio
    async def test_api_key_auth_does_not_include_authorization_header(self, api_key_config):
        """Test that API key authentication does not include Authorization header."""
        with patch("dev_agent.llm.azure_client.AsyncAzureOpenAI") as mock_async_azure:
            # Create mock client instance
            mock_client_instance = AsyncMock()
            mock_async_azure.return_value = mock_client_instance

            # Initialize client with API key config
            AzureOpenAIClient(api_key_config)

            # Get the headers that were passed
            call_kwargs = mock_async_azure.call_args.kwargs
            headers = call_kwargs["default_headers"]

            # Verify Authorization header is NOT present for API key auth
            assert "Authorization" not in headers

    @pytest.mark.asyncio
    async def test_streaming_completion_with_azure_ad_auth_mocked(self, bearer_token_config):
        """Test streaming completion with Azure AD authentication (mocked)."""
        # Create mock client with streaming response
        mock_client = AsyncMock()

        # Create async generator for streaming
        async def mock_stream():
            chunks = [
                MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello"))]),
                MagicMock(choices=[MagicMock(delta=MagicMock(content=" world"))]),
                MagicMock(choices=[MagicMock(delta=MagicMock(content="!"))]),
            ]
            for chunk in chunks:
                yield chunk

        mock_client.chat.completions.create = AsyncMock(return_value=mock_stream())

        # Initialize client with mocked Azure client
        client = AzureOpenAIClient(bearer_token_config, client=mock_client)

        # Generate streaming completion
        result_chunks = []
        async for chunk in client.generate_streaming(
            prompt="Say hello",
            system_prompt="You are a friendly assistant",
        ):
            result_chunks.append(chunk)

        # Verify the streaming result
        assert len(result_chunks) == 3
        assert "".join(result_chunks) == "Hello world!"

        # Verify the API was called with stream=True
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["stream"] is True

    @pytest.mark.asyncio
    async def test_batch_embedding_with_azure_ad_auth_mocked(self, bearer_token_config, tmp_path):
        """Test batch embedding generation with Azure AD authentication (mocked)."""
        # Create mock client with batch embedding response
        mock_client = AsyncMock()
        mock_response = MagicMock(
            data=[
                MagicMock(embedding=[0.1] * 1536),
                MagicMock(embedding=[0.2] * 1536),
                MagicMock(embedding=[0.3] * 1536),
            ],
            usage=MagicMock(total_tokens=150),
        )
        mock_client.embeddings.create = AsyncMock(return_value=mock_response)

        # Initialize embedding client with mocked Azure client and empty cache
        client = AzureEmbeddingClient(bearer_token_config, cache_dir=tmp_path / "cache", client=mock_client)

        # Generate batch embeddings (unique texts to avoid cache hits)
        import uuid
        unique_id = uuid.uuid4()
        texts = [f"Text 1 {unique_id}", f"Text 2 {unique_id}", f"Text 3 {unique_id}"]
        results = await client.embed_batch(texts)

        # Verify the results
        assert len(results) == 3
        assert all(len(embedding) == 1536 for embedding in results)
        assert all(x == 0.1 for x in results[0])
        assert all(x == 0.2 for x in results[1])
        assert all(x == 0.3 for x in results[2])

        # Verify the API was called
        mock_client.embeddings.create.assert_called_once()

        # Verify the call parameters
        call_kwargs = mock_client.embeddings.create.call_args.kwargs
        assert call_kwargs["model"] == "text-embedding-ada-002"
        assert call_kwargs["input"] == texts
