"""LLM integration layer for dev-agent.

This module provides abstract interfaces and implementations for LLM providers,
with Azure OpenAI as the primary implementation and Google Gemini as an alternative.
It includes factory functions for creating provider-specific clients with automatic
provider detection and credential validation.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from dev_agent.llm.azure_client import AzureOpenAIClient
from dev_agent.llm.base import IEmbeddingClient, ILLMClient
from dev_agent.llm.embeddings import AzureEmbeddingClient
from dev_agent.models.enums import LLMProvider

if TYPE_CHECKING:
    from pathlib import Path

    from dev_agent.models.llm_config import AzureOpenAIConfig, GeminiConfig

logger = logging.getLogger(__name__)

__all__ = [
    "ILLMClient",
    "IEmbeddingClient",
    "AzureOpenAIClient",
    "AzureEmbeddingClient",
    "create_llm_client",
    "create_embedding_client",
    "get_preferred_provider",
    "validate_provider_credentials",
]


def get_preferred_provider() -> LLMProvider:
    """Get the preferred LLM provider from environment variables.

    Checks the PREFERRED_LLM_PROVIDER environment variable to determine which
    provider to use. Defaults to Azure OpenAI for backward compatibility.

    Returns:
        LLMProvider enum value for the preferred provider

    Example:
        ```python
        provider = get_preferred_provider()
        print(f"Using provider: {provider.value}")
        ```
    """
    provider_env = os.getenv("PREFERRED_LLM_PROVIDER", "azure_openai").lower()
    
    # Map environment variable values to enum values
    provider_mapping = {
        "azure": LLMProvider.AZURE_OPENAI,
        "azure_openai": LLMProvider.AZURE_OPENAI,
        "gemini": LLMProvider.GEMINI,
        "google": LLMProvider.GEMINI,
        "google_gemini": LLMProvider.GEMINI,
    }
    
    provider = provider_mapping.get(provider_env, LLMProvider.AZURE_OPENAI)
    
    logger.debug(f"Preferred provider from environment: {provider.value}")
    return provider


def validate_provider_credentials(provider: LLMProvider) -> tuple[bool, str]:
    """Validate that required credentials are available for the specified provider.

    Args:
        provider: LLM provider to validate credentials for

    Returns:
        Tuple of (is_valid, error_message). If is_valid is True, error_message is empty.

    Example:
        ```python
        is_valid, error = validate_provider_credentials(LLMProvider.AZURE_OPENAI)
        if not is_valid:
            print(f"Credential validation failed: {error}")
        ```
    """
    if provider == LLMProvider.AZURE_OPENAI:
        # Check for Azure OpenAI credentials
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        bearer_token = os.getenv("AZURE_OPENAI_TOKEN")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or os.getenv("AZURE_CHAT_DEPLOYMENT_NAME")
        embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

        if not endpoint:
            return False, "AZURE_OPENAI_ENDPOINT environment variable is required"
        
        if not (api_key or bearer_token):
            return False, (
                "Either AZURE_OPENAI_API_KEY or AZURE_OPENAI_TOKEN environment variable is required. "
                "Set one of:\n"
                "  - AZURE_OPENAI_API_KEY (for API key authentication)\n"
                "  - AZURE_OPENAI_TOKEN (for Azure AD authentication)"
            )
        
        if not deployment:
            return False, (
                "AZURE_OPENAI_DEPLOYMENT_NAME or AZURE_CHAT_DEPLOYMENT_NAME environment variable is required"
            )
        
        if not embedding_deployment:
            return False, "AZURE_OPENAI_EMBEDDING_DEPLOYMENT environment variable is required"

        return True, ""

    elif provider == LLMProvider.GEMINI:
        # Check for Gemini credentials
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            return False, (
                "GEMINI_API_KEY environment variable is required. "
                "Get your API key at: https://makersuite.google.com/app/apikey"
            )
        
        # Basic validation of API key format
        if not api_key.startswith("AI"):
            return False, (
                "Invalid Gemini API key format. "
                "Gemini API keys should start with 'AI'. "
                "Get your API key at: https://makersuite.google.com/app/apikey"
            )

        return True, ""

    else:
        return False, f"Unsupported provider: {provider.value}"


def create_llm_client(
    provider: LLMProvider | str | None = None,
    config: AzureOpenAIConfig | GeminiConfig | None = None,
) -> ILLMClient:
    """Create an LLM client based on the specified provider.

    This factory function creates the appropriate LLM client implementation
    based on the provider. It supports automatic provider detection from
    environment variables and validates credentials before creating clients.

    Args:
        provider: LLM provider to use. Can be:
            - LLMProvider enum value (LLMProvider.AZURE_OPENAI, LLMProvider.GEMINI)
            - String value ("azure_openai", "azure", "gemini", "google")
            - None for automatic detection from PREFERRED_LLM_PROVIDER env var
        config: Provider-specific configuration. If None, configuration will be
               loaded from environment variables.

    Returns:
        ILLMClient implementation for the specified provider

    Raises:
        ValueError: If provider is unsupported, credentials are missing, or
                   configuration is invalid
        ImportError: If required dependencies for the provider are not installed

    Example:
        ```python
        # Automatic provider detection
        client = create_llm_client()

        # Explicit provider selection
        client = create_llm_client(provider="gemini")
        client = create_llm_client(provider=LLMProvider.AZURE_OPENAI)

        # With custom configuration
        config = GeminiConfig(api_key="AIza...", model_name="gemini-pro")
        client = create_llm_client(provider="gemini", config=config)
        ```
    """
    # Determine provider
    if provider is None:
        provider = get_preferred_provider()
    elif isinstance(provider, str):
        # Convert string to enum
        provider_mapping = {
            "azure": LLMProvider.AZURE_OPENAI,
            "azure_openai": LLMProvider.AZURE_OPENAI,
            "gemini": LLMProvider.GEMINI,
            "google": LLMProvider.GEMINI,
            "google_gemini": LLMProvider.GEMINI,
        }
        
        provider_lower = provider.lower()
        if provider_lower not in provider_mapping:
            supported_providers = ", ".join(sorted(provider_mapping.keys()))
            raise ValueError(
                f"Unsupported provider: '{provider}'. "
                f"Supported providers: {supported_providers}"
            )
        
        provider = provider_mapping[provider_lower]

    # Validate credentials
    is_valid, error_msg = validate_provider_credentials(provider)
    if not is_valid:
        raise ValueError(f"Provider credential validation failed: {error_msg}")

    # Create provider-specific client
    if provider == LLMProvider.AZURE_OPENAI:
        # Import Azure config class
        from dev_agent.models.llm_config import AzureOpenAIConfig
        
        if config is None:
            # Load configuration from environment
            from dev_agent.config.config_manager import ConfigManager
            config_manager = ConfigManager()
            config = config_manager.load_azure_config()
        
        if not isinstance(config, AzureOpenAIConfig):
            raise ValueError(
                f"Expected AzureOpenAIConfig for Azure OpenAI provider, got {type(config)}"
            )
        
        logger.info(f"Creating Azure OpenAI client for deployment: {config.deployment_name}")
        return AzureOpenAIClient(config)

    elif provider == LLMProvider.GEMINI:
        # Import Gemini config and client classes
        from dev_agent.models.llm_config import GeminiConfig
        
        if config is None:
            # Load configuration from environment
            from dev_agent.config.config_manager import ConfigManager
            config_manager = ConfigManager()
            config = config_manager.load_gemini_config()
        
        if not isinstance(config, GeminiConfig):
            raise ValueError(
                f"Expected GeminiConfig for Gemini provider, got {type(config)}"
            )
        
        # Import and create Gemini client (may raise ImportError if dependencies not installed)
        try:
            from dev_agent.llm.gemini_client import GeminiClient
            logger.info(f"Creating Gemini client for model: {config.model_name}")
            return GeminiClient(config)
        except ImportError as e:
            raise ImportError(
                "Gemini dependencies not installed. Install with: "
                "uv add google-generativeai google-api-core"
            ) from e

    else:
        raise ValueError(f"Unsupported provider: {provider.value}")


def create_embedding_client(
    provider: LLMProvider | str | None = None,
    config: AzureOpenAIConfig | GeminiConfig | None = None,
    cache_dir: Path | str | None = None,
) -> IEmbeddingClient:
    """Create an embedding client based on the specified provider.

    This factory function creates the appropriate embedding client implementation
    based on the provider. It supports automatic provider detection from
    environment variables and validates credentials before creating clients.

    Args:
        provider: LLM provider to use. Can be:
            - LLMProvider enum value (LLMProvider.AZURE_OPENAI, LLMProvider.GEMINI)
            - String value ("azure_openai", "azure", "gemini", "google")
            - None for automatic detection from PREFERRED_LLM_PROVIDER env var
        config: Provider-specific configuration. If None, configuration will be
               loaded from environment variables.
        cache_dir: Directory for embedding cache. Defaults to '.dev_agent/embedding_cache'

    Returns:
        IEmbeddingClient implementation for the specified provider

    Raises:
        ValueError: If provider is unsupported, credentials are missing, or
                   configuration is invalid
        ImportError: If required dependencies for the provider are not installed

    Example:
        ```python
        # Automatic provider detection
        client = create_embedding_client()

        # Explicit provider selection with custom cache directory
        client = create_embedding_client(
            provider="gemini",
            cache_dir="/custom/cache/path"
        )

        # With custom configuration
        config = GeminiConfig(api_key="AIza...", embedding_model="embedding-001")
        client = create_embedding_client(provider="gemini", config=config)
        ```
    """
    # Determine provider
    if provider is None:
        provider = get_preferred_provider()
    elif isinstance(provider, str):
        # Convert string to enum
        provider_mapping = {
            "azure": LLMProvider.AZURE_OPENAI,
            "azure_openai": LLMProvider.AZURE_OPENAI,
            "gemini": LLMProvider.GEMINI,
            "google": LLMProvider.GEMINI,
            "google_gemini": LLMProvider.GEMINI,
        }
        
        provider_lower = provider.lower()
        if provider_lower not in provider_mapping:
            supported_providers = ", ".join(sorted(provider_mapping.keys()))
            raise ValueError(
                f"Unsupported provider: '{provider}'. "
                f"Supported providers: {supported_providers}"
            )
        
        provider = provider_mapping[provider_lower]

    # Validate credentials
    is_valid, error_msg = validate_provider_credentials(provider)
    if not is_valid:
        raise ValueError(f"Provider credential validation failed: {error_msg}")

    # Create provider-specific client
    if provider == LLMProvider.AZURE_OPENAI:
        # Import Azure config class
        from dev_agent.models.llm_config import AzureOpenAIConfig
        
        if config is None:
            # Load configuration from environment
            from dev_agent.config.config_manager import ConfigManager
            config_manager = ConfigManager()
            config = config_manager.load_azure_config()
        
        if not isinstance(config, AzureOpenAIConfig):
            raise ValueError(
                f"Expected AzureOpenAIConfig for Azure OpenAI provider, got {type(config)}"
            )
        
        logger.info(f"Creating Azure embedding client for deployment: {config.embedding_deployment}")
        return AzureEmbeddingClient(config, cache_dir=cache_dir)

    elif provider == LLMProvider.GEMINI:
        # Import Gemini config and embedding client classes
        from dev_agent.models.llm_config import GeminiConfig
        
        if config is None:
            # Load configuration from environment
            from dev_agent.config.config_manager import ConfigManager
            config_manager = ConfigManager()
            config = config_manager.load_gemini_config()
        
        if not isinstance(config, GeminiConfig):
            raise ValueError(
                f"Expected GeminiConfig for Gemini provider, got {type(config)}"
            )
        
        # Import and create Gemini embedding client (may raise ImportError if dependencies not installed)
        try:
            from dev_agent.llm.gemini_embeddings import GeminiEmbeddingClient
            logger.info(f"Creating Gemini embedding client for model: {config.embedding_model}")
            return GeminiEmbeddingClient(config, cache_dir=cache_dir)
        except ImportError as e:
            raise ImportError(
                "Gemini dependencies not installed. Install with: "
                "uv add google-generativeai google-api-core"
            ) from e

    else:
        raise ValueError(f"Unsupported provider: {provider.value}")
