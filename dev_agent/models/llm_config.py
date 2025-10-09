"""LLM configuration models using Pydantic for validation.

This module provides configuration models for LLM providers, including
Azure OpenAI and Google Gemini. The models use Pydantic v2 for validation,
type safety, and secure handling of sensitive data like API keys.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator


class AzureOpenAIConfig(BaseModel):
    """Enhanced Azure OpenAI configuration with Azure AD authentication support.

    This model provides comprehensive configuration for Azure OpenAI integration
    with support for both API key and Azure AD bearer token authentication,
    custom headers, and secure handling of sensitive data.

    Attributes:
        endpoint: Azure OpenAI endpoint URL (e.g., https://your-resource.openai.azure.com/)
        api_key: Azure OpenAI API key (stored securely as SecretStr, optional if bearer_token provided)
        bearer_token: Azure AD bearer token for authentication (optional if api_key provided)
        api_version: Azure OpenAI API version (default: 2024-02-15-preview)
        deployment_name: GPT-4 deployment name for completions
        embedding_deployment: Embedding model deployment name (text-embedding-ada-002)
        openai_api_type: OpenAI API type ("azure" for API key, "azure_ad" for bearer token)
        custom_headers: Custom headers to include in all API requests
        user_sid: User session ID for auditing and tracking
        max_tokens: Maximum tokens for completion generation (1-128000)
        temperature: Sampling temperature for generation (0.0-2.0)
        max_retries: Maximum retry attempts for failed API calls (0-10)
        timeout: Request timeout in seconds (1-300)
        batch_size: Batch size for embedding generation (1-100)
        verify_ssl: Verify SSL certificates (default: True, set to False to disable - INSECURE!)

    Example:
        ```python
        # API Key Authentication
        config = AzureOpenAIConfig(
            endpoint="https://my-resource.openai.azure.com/",
            api_key="sk-...",
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )

        # Azure AD Authentication
        config = AzureOpenAIConfig(
            endpoint="https://my-resource.openai.azure.com/",
            bearer_token="eyJ0eXAiOiJKV1QiLCJhbGc...",
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
            user_sid="A123456",
            custom_headers={"department": "engineering"},
        )
        ```

    Security:
        - API keys and bearer tokens are stored as SecretStr and never logged or serialized
        - JSON encoding automatically redacts sensitive credentials
        - Endpoint URL is validated for proper format
        - At least one authentication method (api_key or bearer_token) is required
    """

    endpoint: str = Field(
        ...,
        description="Azure OpenAI endpoint URL",
        examples=["https://your-resource.openai.azure.com/"],
    )
    api_key: SecretStr | None = Field(
        default=None,
        description="Azure OpenAI API key (stored securely, optional if bearer_token provided)",
    )
    bearer_token: SecretStr | None = Field(
        default=None,
        description="Azure AD bearer token for authentication (optional if api_key provided)",
    )
    api_version: str = Field(
        default="2024-02-15-preview",
        description="Azure OpenAI API version",
    )
    deployment_name: str = Field(
        ...,
        description="GPT-4 deployment name for completions",
        examples=["gpt-4", "gpt-4-turbo"],
    )
    embedding_deployment: str = Field(
        ...,
        description="Embedding model deployment name",
        examples=["text-embedding-ada-002"],
    )
    openai_api_type: str = Field(
        default="azure",
        description="OpenAI API type: 'azure' for API key, 'azure_ad' for bearer token",
    )
    custom_headers: dict[str, str] = Field(
        default_factory=dict,
        description="Custom headers to include in all API requests",
    )
    user_sid: str | None = Field(
        default=None,
        description="User session ID for auditing and tracking",
    )
    max_tokens: int = Field(
        default=4000,
        ge=1,
        le=128000,
        description="Maximum tokens for completion generation",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for generation",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts for failed API calls",
    )
    timeout: int = Field(
        default=60,
        ge=1,
        le=300,
        description="Request timeout in seconds",
    )
    batch_size: int = Field(
        default=16,
        ge=1,
        le=100,
        description="Batch size for embedding generation",
    )
    verify_ssl: bool = Field(
        default=True,
        description="Verify SSL certificates (set to False to disable SSL verification - INSECURE!)",
    )

    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(cls, v: str) -> str:
        """Validate endpoint URL format.

        Args:
            v: Endpoint URL to validate

        Returns:
            Validated endpoint URL

        Raises:
            ValueError: If endpoint doesn't start with http:// or https://
        """
        if not v.startswith(("http://", "https://")):
            raise ValueError("Endpoint must start with http:// or https://")

        # Ensure endpoint ends with trailing slash for consistency
        if not v.endswith("/"):
            v = f"{v}/"

        return v

    @model_validator(mode="after")
    def validate_authentication(self) -> AzureOpenAIConfig:
        """Validate authentication configuration.

        Ensures at least one authentication method is provided and sets
        the appropriate API type based on the authentication method.

        Returns:
            Validated configuration instance

        Raises:
            ValueError: If neither api_key nor bearer_token is provided
        """
        if not self.api_key and not self.bearer_token:
            raise ValueError(
                "Either api_key or bearer_token must be provided for authentication.\n"
                "Please set one of:\n"
                "  - AZURE_OPENAI_API_KEY (for API key authentication)\n"
                "  - AZURE_OPENAI_TOKEN (for Azure AD authentication)"
            )

        # Auto-set api_type based on authentication method
        # Bearer token takes precedence if both are provided
        if self.bearer_token:
            self.openai_api_type = "azure_ad"

        return self

    def get_auth_headers(self) -> dict[str, str]:
        """Build authentication and custom headers dictionary.

        Constructs a dictionary containing the Authorization header (if using
        bearer token), custom headers, and user_sid (if configured).

        Returns:
            Dictionary of headers to include in API requests

        Example:
            ```python
            config = AzureOpenAIConfig(
                endpoint="https://my-resource.openai.azure.com/",
                bearer_token="eyJ0eXAiOiJKV1QiLCJhbGc...",
                deployment_name="gpt-4",
                embedding_deployment="text-embedding-ada-002",
                user_sid="A123456",
                custom_headers={"department": "engineering"},
            )
            headers = config.get_auth_headers()
            # Returns: {
            #     "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGc...",
            #     "department": "engineering",
            #     "user_sid": "A123456"
            # }
            ```
        """
        headers: dict[str, str] = {}

        # Add Authorization header if using bearer token
        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token.get_secret_value()}"

        # Add custom headers
        headers.update(self.custom_headers)

        # Add user_sid if configured
        if self.user_sid:
            headers["user_sid"] = self.user_sid

        return headers

    def get_api_key_value(self) -> str:
        """Get the appropriate credential value for client initialization.

        Returns the bearer token if configured (for Azure AD authentication),
        otherwise returns the API key. This method is used when initializing
        the Azure OpenAI client, as the SDK expects the credential in the
        api_key parameter regardless of authentication method.

        Returns:
            Bearer token or API key value

        Raises:
            ValueError: If neither api_key nor bearer_token is configured

        Example:
            ```python
            config = AzureOpenAIConfig(
                endpoint="https://my-resource.openai.azure.com/",
                bearer_token="eyJ0eXAiOiJKV1QiLCJhbGc...",
                deployment_name="gpt-4",
                embedding_deployment="text-embedding-ada-002",
            )
            api_key_value = config.get_api_key_value()
            # Returns the bearer token value
            ```
        """
        if self.bearer_token:
            return self.bearer_token.get_secret_value()
        if self.api_key:
            return self.api_key.get_secret_value()

        raise ValueError(
            "No authentication credentials configured. "
            "Either api_key or bearer_token must be provided."
        )

    model_config = {
        "json_encoders": {SecretStr: lambda v: "***REDACTED***"},
        "json_schema_extra": {
            "examples": [
                {
                    "endpoint": "https://my-resource.openai.azure.com/",
                    "api_key": "your-api-key-here",
                    "api_version": "2024-02-15-preview",
                    "deployment_name": "gpt-4",
                    "embedding_deployment": "text-embedding-ada-002",
                    "max_tokens": 4000,
                    "temperature": 0.7,
                    "max_retries": 3,
                    "timeout": 60,
                    "batch_size": 16,
                },
                {
                    "endpoint": "https://my-resource.openai.azure.com/",
                    "bearer_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                    "api_version": "2024-02-15-preview",
                    "deployment_name": "gpt-4",
                    "embedding_deployment": "text-embedding-ada-002",
                    "openai_api_type": "azure_ad",
                    "user_sid": "A123456",
                    "custom_headers": {"department": "engineering"},
                    "max_tokens": 4000,
                    "temperature": 0.7,
                    "max_retries": 3,
                    "timeout": 60,
                    "batch_size": 16,
                },
            ]
        },
    }


class GeminiConfig(BaseModel):
    """Google Gemini API configuration with validation and secure credential handling.

    This model provides comprehensive configuration for Google Gemini integration
    with support for various Gemini models, secure API key handling, and
    configurable generation parameters.

    Attributes:
        api_key: Gemini API key (stored securely as SecretStr)
        model_name: Model for code generation (gemini-pro, gemini-pro-vision, gemini-ultra)
        embedding_model: Model for embeddings (embedding-001, text-embedding-004)
        api_endpoint: Gemini API endpoint (default: generativelanguage.googleapis.com)
        max_output_tokens: Maximum tokens for generation (1-8192)
        temperature: Sampling temperature for generation (0.0-2.0)
        top_p: Nucleus sampling parameter (0.0-1.0)
        top_k: Top-k sampling parameter (1-100)
        max_retries: Maximum retry attempts for failed API calls (0-10)
        timeout: Request timeout in seconds (1-300)
        batch_size: Batch size for embedding generation (1-100)
        safety_settings: Content filtering levels for safety

    Example:
        ```python
        config = GeminiConfig(
            api_key="your-gemini-api-key-here",
            model_name="gemini-pro",
            embedding_model="embedding-001",
            temperature=0.7,
            max_output_tokens=2048,
        )
        ```

    Security:
        - API keys are stored as SecretStr and never logged or serialized
        - JSON encoding automatically redacts sensitive credentials
        - API key format is validated before use
    """

    api_key: SecretStr = Field(
        ...,
        description="Gemini API key (stored securely, get from https://makersuite.google.com/app/apikey)",
    )
    model_name: str = Field(
        default="gemini-pro",
        description="Model for code generation",
        examples=["gemini-pro", "gemini-pro-vision", "gemini-ultra"],
    )
    embedding_model: str = Field(
        default="embedding-001",
        description="Model for embeddings",
        examples=["embedding-001", "text-embedding-004"],
    )
    api_endpoint: str = Field(
        default="generativelanguage.googleapis.com",
        description="Gemini API endpoint",
    )
    max_output_tokens: int = Field(
        default=2048,
        ge=1,
        le=8192,
        description="Maximum tokens for generation",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for generation",
    )
    top_p: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling parameter",
    )
    top_k: int = Field(
        default=40,
        ge=1,
        le=100,
        description="Top-k sampling parameter",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts for failed API calls",
    )
    timeout: int = Field(
        default=60,
        ge=1,
        le=300,
        description="Request timeout in seconds",
    )
    batch_size: int = Field(
        default=16,
        ge=1,
        le=100,
        description="Batch size for embedding generation",
    )
    safety_settings: dict[str, str] = Field(
        default_factory=dict,
        description="Content filtering levels for safety",
    )

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: SecretStr) -> SecretStr:
        """Validate Gemini API key format.

        Args:
            v: API key to validate

        Returns:
            Validated API key

        Raises:
            ValueError: If API key format is invalid
        """
        api_key_value = v.get_secret_value()

        # Gemini API keys typically start with "AI" and are 39 characters long
        if not api_key_value.startswith("AI"):
            raise ValueError(
                "Invalid Gemini API key format. "
                "Gemini API keys should start with 'AI'. "
                "Get your API key at: https://makersuite.google.com/app/apikey"
            )

        if len(api_key_value) < 20:
            raise ValueError(
                "Gemini API key appears to be too short. "
                "Please verify your API key is complete."
            )

        return v

    @field_validator("model_name")
    @classmethod
    def validate_model_name(cls, v: str) -> str:
        """Validate Gemini model name.

        Args:
            v: Model name to validate

        Returns:
            Validated model name

        Raises:
            ValueError: If model name is not supported
        """
        supported_models = {
            "gemini-2.5-flash-lite",
            "gemini-2.5-flash",
            "gemini-2.5-pro",
        }

        if v not in supported_models:
            raise ValueError(
                f"Unsupported Gemini model: {v}. "
                f"Supported models: {', '.join(sorted(supported_models))}"
            )

        return v

    @field_validator("embedding_model")
    @classmethod
    def validate_embedding_model(cls, v: str) -> str:
        """Validate Gemini embedding model name.

        Args:
            v: Embedding model name to validate

        Returns:
            Validated embedding model name

        Raises:
            ValueError: If embedding model name is not supported
        """
        supported_embedding_models = {
            "gemini-embedding-001",
        }

        if v not in supported_embedding_models:
            raise ValueError(
                f"Unsupported Gemini embedding model: {v}. "
                f"Supported models: {', '.join(sorted(supported_embedding_models))}"
            )

        return v

    @field_validator("api_endpoint")
    @classmethod
    def validate_api_endpoint(cls, v: str) -> str:
        """Validate API endpoint format.

        Args:
            v: API endpoint to validate

        Returns:
            Validated API endpoint

        Raises:
            ValueError: If endpoint format is invalid
        """
        # Remove protocol if present for validation
        endpoint = v.replace("https://", "").replace("http://", "")

        # Validate it's a reasonable hostname
        if not endpoint or "." not in endpoint:
            raise ValueError(
                "Invalid API endpoint format. "
                "Expected format: 'generativelanguage.googleapis.com' or similar"
            )

        # Return without protocol (will be added by the client)
        return endpoint

    def get_embedding_dimension(self) -> int:
        """Get the embedding dimension for the configured embedding model.

        Returns:
            Embedding dimension (768 for all current Gemini embedding models)
        """
        # All current Gemini embedding models use 768 dimensions
        return 768

    def get_api_key_value(self) -> str:
        """Get the API key value for client initialization.

        Returns:
            API key value

        Example:
            ```python
            config = GeminiConfig(api_key="AIza...")
            api_key = config.get_api_key_value()
            ```
        """
        return self.api_key.get_secret_value()

    model_config = {
        "json_encoders": {SecretStr: lambda v: "***REDACTED***"},
        "json_schema_extra": {
            "examples": [
                {
                    "api_key": "your-gemini-api-key-here",
                    "model_name": "gemini-pro",
                    "embedding_model": "embedding-001",
                    "api_endpoint": "generativelanguage.googleapis.com",
                    "max_output_tokens": 2048,
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_retries": 3,
                    "timeout": 60,
                    "batch_size": 16,
                    "safety_settings": {},
                },
                {
                    "api_key": "your-gemini-api-key-here",
                    "model_name": "gemini-2.5-flash",
                    "embedding_model": "gemini-embedding-001",
                    "api_endpoint": "generativelanguage.googleapis.com",
                    "max_output_tokens": 4096,
                    "temperature": 0.3,
                    "top_p": 0.8,
                    "top_k": 20,
                    "max_retries": 5,
                    "timeout": 120,
                    "batch_size": 32,
                    "safety_settings": {
                        "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE",
                        "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE",
                    },
                },
            ]
        },
    }
