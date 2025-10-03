"""LLM configuration models using Pydantic for validation.

This module provides configuration models for LLM providers, specifically
Azure OpenAI. The models use Pydantic v2 for validation, type safety, and
secure handling of sensitive data like API keys.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, SecretStr, field_validator


class AzureOpenAIConfig(BaseModel):
    """Enhanced Azure OpenAI configuration with validation.
    
    This model provides comprehensive configuration for Azure OpenAI integration
    with field validation, secure API key handling, and sensible defaults.
    
    Attributes:
        endpoint: Azure OpenAI endpoint URL (e.g., https://your-resource.openai.azure.com/)
        api_key: Azure OpenAI API key (stored securely as SecretStr)
        api_version: Azure OpenAI API version (default: 2024-02-15-preview)
        deployment_name: GPT-4 deployment name for completions
        embedding_deployment: Embedding model deployment name (text-embedding-ada-002)
        max_tokens: Maximum tokens for completion generation (1-128000)
        temperature: Sampling temperature for generation (0.0-2.0)
        max_retries: Maximum retry attempts for failed API calls (0-10)
        timeout: Request timeout in seconds (1-300)
        batch_size: Batch size for embedding generation (1-100)
    
    Example:
        ```python
        config = AzureOpenAIConfig(
            endpoint="https://my-resource.openai.azure.com/",
            api_key="sk-...",
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )
        ```
    
    Security:
        - API keys are stored as SecretStr and never logged or serialized
        - JSON encoding automatically redacts API keys
        - Endpoint URL is validated for proper format
    """

    endpoint: str = Field(
        ...,
        description="Azure OpenAI endpoint URL",
        examples=["https://your-resource.openai.azure.com/"],
    )
    api_key: SecretStr = Field(
        ...,
        description="Azure OpenAI API key (stored securely)",
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
                }
            ]
        },
    }
