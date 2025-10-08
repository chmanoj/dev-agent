"""LLM configuration models using Pydantic for validation.

This module provides configuration models for LLM providers, specifically
Azure OpenAI. The models use Pydantic v2 for validation, type safety, and
secure handling of sensitive data like API keys.
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
    def validate_authentication(self) -> "AzureOpenAIConfig":
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
        "json_encoders": {
            SecretStr: lambda v: "***REDACTED***"
        },
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
