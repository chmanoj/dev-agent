"""Configuration management for dev-agent."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from dev_agent.models.llm_config import AzureOpenAIConfig as PydanticAzureOpenAIConfig, GeminiConfig
from dev_agent.models.enums import LLMProvider

logger = logging.getLogger(__name__)


@dataclass
class IndexingConfig:
    """Configuration for indexing operations."""

    max_file_size_mb: int = 10
    chunk_size: int = 1000
    overlap_size: int = 200
    max_files_per_batch: int = 100
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"  # Deprecated: kept for backward compatibility
    vector_db_type: str = "faiss"
    use_azure_embeddings: bool = True  # Azure OpenAI is required


@dataclass
class LoggingConfig:
    """Configuration for logging."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_enabled: bool = True
    console_enabled: bool = True
    max_file_size_mb: int = 10
    backup_count: int = 5
    color_output: bool = True


@dataclass
class CLIConfig:
    """Configuration for CLI behavior."""

    auto_approve: bool = False
    progress_bar_enabled: bool = True
    color_output: bool = True
    session_timeout_minutes: int = 60


@dataclass
class DevAgentConfig:
    """Main configuration class for dev-agent."""

    indexing: IndexingConfig
    logging: LoggingConfig
    cli: CLIConfig
    azure_openai: PydanticAzureOpenAIConfig | None
    gemini: GeminiConfig | None = None
    version: str = "0.1.0"

    @classmethod
    def default(cls) -> DevAgentConfig:
        """Create default configuration with optional LLM providers."""
        return cls(
            indexing=IndexingConfig(),
            logging=LoggingConfig(),
            cli=CLIConfig(),
            azure_openai=None,  # Azure OpenAI config loaded from env vars
            gemini=None,  # Gemini config loaded from env vars
        )

    def to_dict(self, redact_secrets: bool = True) -> dict[str, Any]:
        """Convert configuration to dictionary.

        Args:
            redact_secrets: If True, redact API keys in output (default: True)

        Returns:
            Dictionary representation with Azure OpenAI config properly serialized
        """
        config_dict = {
            "indexing": asdict(self.indexing),
            "logging": asdict(self.logging),
            "cli": asdict(self.cli),
            "version": self.version,
        }

        # Serialize Azure OpenAI config if present
        if self.azure_openai is not None:
            # Use model_dump to get dict, excluding unset fields
            azure_dict = self.azure_openai.model_dump(
                mode="json",
                exclude_unset=True,
            )
            # Convert SecretStr to string for serialization
            if "api_key" in azure_dict:
                if redact_secrets:
                    azure_dict["api_key"] = "***REDACTED***"
                else:
                    # Get the actual secret value for saving
                    azure_dict["api_key"] = self.azure_openai.api_key.get_secret_value()
            config_dict["azure_openai"] = azure_dict

        # Serialize Gemini config if present
        if self.gemini is not None:
            # Use model_dump to get dict, excluding unset fields
            gemini_dict = self.gemini.model_dump(
                mode="json",
                exclude_unset=True,
            )
            # Convert SecretStr to string for serialization
            if "api_key" in gemini_dict:
                if redact_secrets:
                    gemini_dict["api_key"] = "***REDACTED***"
                else:
                    # Get the actual secret value for saving
                    gemini_dict["api_key"] = self.gemini.api_key.get_secret_value()
            config_dict["gemini"] = gemini_dict

        return config_dict

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DevAgentConfig:
        """Create configuration from dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            DevAgentConfig instance with validated Azure OpenAI config
        """
        # Parse Azure OpenAI config if present
        azure_config = None
        if data.get("azure_openai"):
            azure_data = data["azure_openai"]
            # Handle legacy field names for backward compatibility
            if "chat_model" in azure_data and "deployment_name" not in azure_data:
                azure_data["deployment_name"] = azure_data.pop("chat_model")
            if (
                "embedding_model" in azure_data
                and "embedding_deployment" not in azure_data
            ):
                azure_data["embedding_deployment"] = azure_data.pop("embedding_model")

            # Skip if API key is redacted (will be loaded from env vars)
            if azure_data.get("api_key") != "***REDACTED***":
                try:
                    azure_config = PydanticAzureOpenAIConfig(**azure_data)
                except ValidationError:
                    # If validation fails, skip and rely on env vars
                    pass

        # Parse Gemini config if present
        gemini_config = None
        if data.get("gemini"):
            gemini_data = data["gemini"]
            # Skip if API key is redacted (will be loaded from env vars)
            if gemini_data.get("api_key") != "***REDACTED***":
                try:
                    gemini_config = GeminiConfig(**gemini_data)
                except ValidationError:
                    # If validation fails, skip and rely on env vars
                    pass

        return cls(
            indexing=IndexingConfig(**data.get("indexing", {})),
            logging=LoggingConfig(**data.get("logging", {})),
            cli=CLIConfig(**data.get("cli", {})),
            azure_openai=azure_config,
            gemini=gemini_config,
            version=data.get("version", "0.1.0"),
        )


class ConfigManager:
    """Manages configuration loading, saving, and access.

    Configuration precedence (highest to lowest):
    1. Environment variables
    2. Project-specific config file
    3. Global config file
    4. Default values
    """

    DEFAULT_CONFIG_NAME = "dev_agent_config.json"

    def __init__(self, config_path: str | None = None):
        """Initialize configuration manager.

        Args:
            config_path: Optional path to configuration file
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Default to user's home directory
            self.config_path = Path.home() / ".dev_agent" / self.DEFAULT_CONFIG_NAME

        self._config: DevAgentConfig | None = None
        self._ensure_config_dir()

    @staticmethod
    def _load_azure_config_from_env() -> PydanticAzureOpenAIConfig | None:
        """Load Azure OpenAI configuration from environment variables.

        Environment variables take precedence over config file values.
        Supports both API key and Azure AD bearer token authentication.

        Returns:
            AzureOpenAIConfig if all required env vars are present, None otherwise

        Environment Variables:
            AZURE_OPENAI_ENDPOINT: Azure OpenAI endpoint URL (required)
            AZURE_OPENAI_API_KEY: Azure OpenAI API key (conditional - required if no bearer token)
            AZURE_OPENAI_TOKEN: Azure AD bearer token (conditional - required if no API key)
            AZURE_OPENAI_API_VERSION: API version (optional, default: 2024-02-15-preview)
            AZURE_OPENAI_DEPLOYMENT_NAME: GPT-4 deployment name (required)
            AZURE_CHAT_DEPLOYMENT_NAME: Alias for AZURE_OPENAI_DEPLOYMENT_NAME (optional)
            AZURE_OPENAI_EMBEDDING_DEPLOYMENT: Embedding deployment name (required)
            AZURE_OPENAI_USER_SID: User session ID for auditing (optional)
            AZURE_OPENAI_CUSTOM_HEADERS: Custom headers as JSON string (optional)
            AZURE_OPENAI_MAX_TOKENS: Max tokens (optional, default: 4000)
            AZURE_OPENAI_TEMPERATURE: Temperature (optional, default: 0.7)
            AZURE_OPENAI_MAX_RETRIES: Max retries (optional, default: 3)
            AZURE_OPENAI_TIMEOUT: Timeout in seconds (optional, default: 60)
            AZURE_OPENAI_BATCH_SIZE: Batch size (optional, default: 16)

        Note:
            - Bearer token (AZURE_OPENAI_TOKEN) takes precedence over API key if both are set
            - AZURE_CHAT_DEPLOYMENT_NAME is an alias for AZURE_OPENAI_DEPLOYMENT_NAME
            - Custom headers are parsed from JSON string format
            - user_sid is automatically merged into custom_headers dict
        """
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

        # Support both API key and bearer token authentication
        # Bearer token takes precedence if both are provided
        bearer_token = os.getenv("AZURE_OPENAI_TOKEN")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")

        # Support AZURE_CHAT_DEPLOYMENT_NAME as alias for AZURE_OPENAI_DEPLOYMENT_NAME
        deployment_name = os.getenv("AZURE_CHAT_DEPLOYMENT_NAME") or os.getenv(
            "AZURE_OPENAI_DEPLOYMENT_NAME"
        )
        embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

        # Check if required env vars are present
        # Either api_key or bearer_token must be provided (validated by Pydantic model)
        if not all([endpoint, deployment_name, embedding_deployment]):
            return None

        # At least one authentication method must be present
        if not api_key and not bearer_token:
            return None

        try:
            # Build config from env vars
            config_data: dict[str, Any] = {
                "endpoint": endpoint,
                "deployment_name": deployment_name,
                "embedding_deployment": embedding_deployment,
            }

            # Add authentication credentials
            # Bearer token takes precedence over API key
            if bearer_token:
                config_data["bearer_token"] = bearer_token
            if api_key:
                config_data["api_key"] = api_key

            # Parse custom headers from JSON string
            custom_headers: dict[str, str] = {}
            if custom_headers_json := os.getenv("AZURE_OPENAI_CUSTOM_HEADERS"):
                try:
                    parsed_headers = json.loads(custom_headers_json)
                    if isinstance(parsed_headers, dict):
                        # Ensure all values are strings
                        custom_headers = {
                            str(k): str(v) for k, v in parsed_headers.items()
                        }
                    else:
                        logger.warning(
                            "AZURE_OPENAI_CUSTOM_HEADERS must be a JSON object. "
                            f"Got {type(parsed_headers).__name__}. Using empty custom headers."
                        )
                except json.JSONDecodeError as e:
                    logger.warning(
                        f"Failed to parse AZURE_OPENAI_CUSTOM_HEADERS as JSON: {e}. "
                        "Using empty custom headers."
                    )

            # Add user_sid to custom headers if provided
            if user_sid := os.getenv("AZURE_OPENAI_USER_SID"):
                custom_headers["user_sid"] = user_sid
                config_data["user_sid"] = user_sid

            # Add custom headers to config if any were set
            if custom_headers:
                config_data["custom_headers"] = custom_headers

            # Add optional env vars if present
            if api_version := os.getenv("AZURE_OPENAI_API_VERSION"):
                config_data["api_version"] = api_version

            if max_tokens := os.getenv("AZURE_OPENAI_MAX_TOKENS"):
                config_data["max_tokens"] = int(max_tokens)

            if temperature := os.getenv("AZURE_OPENAI_TEMPERATURE"):
                config_data["temperature"] = float(temperature)

            if max_retries := os.getenv("AZURE_OPENAI_MAX_RETRIES"):
                config_data["max_retries"] = int(max_retries)

            if timeout := os.getenv("AZURE_OPENAI_TIMEOUT"):
                config_data["timeout"] = int(timeout)

            if batch_size := os.getenv("AZURE_OPENAI_BATCH_SIZE"):
                config_data["batch_size"] = int(batch_size)

            # SSL verification (default: True)
            if verify_ssl := os.getenv("AZURE_OPENAI_VERIFY_SSL"):
                config_data["verify_ssl"] = verify_ssl.lower() in ("true", "1", "yes")

            return PydanticAzureOpenAIConfig(**config_data)

        except (ValidationError, ValueError) as e:
            logger.warning("Failed to load Azure OpenAI config from environment: %s", e)
            return None

    def _ensure_config_dir(self) -> None:
        """Ensure configuration directory exists."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

    def load_config(self) -> DevAgentConfig:
        """Load configuration with precedence: env vars > config file > defaults.

        Configuration loading order:
        1. Load from config file (if exists) or use defaults
        2. Override Azure OpenAI config with environment variables (if present)

        Returns:
            Loaded configuration with environment variable overrides applied
        """
        if self._config is not None:
            return self._config

        # Load base config from file or defaults
        if self.config_path.exists():
            try:
                with open(self.config_path, encoding="utf-8") as f:
                    data = json.load(f)
                self._config = DevAgentConfig.from_dict(data)
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                print(f"Warning: Failed to load config from {self.config_path}: {e}")
                print("Using default configuration.")
                self._config = DevAgentConfig.default()
        else:
            self._config = DevAgentConfig.default()
            self.save_config()  # Save default config for future use

        # Override LLM provider configs with environment variables (highest precedence)
        env_azure_config = self._load_azure_config_from_env()
        if env_azure_config is not None:
            self._config.azure_openai = env_azure_config

        # Try to load Gemini config from environment variables
        try:
            env_gemini_config = self.load_gemini_config()
            self._config.gemini = env_gemini_config
        except ValueError:
            # Gemini config not available from env vars, that's okay
            pass

        return self._config

    def save_config(self, config: DevAgentConfig | None = None) -> None:
        """Save configuration to file.

        Args:
            config: Configuration to save (uses current if None)

        Note:
            API keys are saved in plain text to the config file.
            Users should use environment variables for production deployments.
        """
        if config is None:
            config = self._config or DevAgentConfig.default()

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                # Don't redact secrets when saving to file
                json.dump(config.to_dict(redact_secrets=False), f, indent=2)
            self._config = config
        except OSError as e:
            print(f"Warning: Failed to save config to {self.config_path}: {e}")

    def get_config(self) -> DevAgentConfig:
        """Get current configuration.

        Returns:
            Current configuration
        """
        if self._config is None:
            return self.load_config()
        return self._config

    def update_config(self, **kwargs) -> None:
        """Update configuration with new values.

        Args:
            **kwargs: Configuration values to update
        """
        config = self.get_config()

        # Update nested configuration objects
        for key, value in kwargs.items():
            if hasattr(config, key) and isinstance(value, dict):
                current_attr = getattr(config, key)
                for sub_key, sub_value in value.items():
                    if hasattr(current_attr, sub_key):
                        setattr(current_attr, sub_key, sub_value)
            elif hasattr(config, key):
                setattr(config, key, value)

        self.save_config(config)

    def reset_to_default(self) -> None:
        """Reset configuration to default values."""
        self._config = DevAgentConfig.default()
        self.save_config()

    def get_project_config_path(self, project_path: str) -> Path:
        """Get project-specific configuration path.

        Args:
            project_path: Path to the project

        Returns:
            Path to project configuration file
        """
        return Path(project_path) / ".dev_agent" / "config.json"

    def load_project_config(self, project_path: str) -> DevAgentConfig:
        """Load project-specific configuration with env var precedence.

        Configuration precedence:
        1. Environment variables (highest)
        2. Project-specific config file
        3. Global config file
        4. Default values (lowest)

        Args:
            project_path: Path to the project

        Returns:
            Project configuration with environment variable overrides applied
        """
        project_config_path = self.get_project_config_path(project_path)

        config: DevAgentConfig
        if project_config_path.exists():
            try:
                with open(project_config_path, encoding="utf-8") as f:
                    data = json.load(f)
                config = DevAgentConfig.from_dict(data)
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                print(f"Warning: Failed to load project config: {e}")
                # Fall back to global configuration
                config = self.load_config()
        else:
            # Fall back to global configuration
            config = self.load_config()

        # Override LLM provider configs with environment variables (highest precedence)
        env_azure_config = self._load_azure_config_from_env()
        if env_azure_config is not None:
            config.azure_openai = env_azure_config

        # Try to load Gemini config from environment variables
        try:
            env_gemini_config = self.load_gemini_config()
            config.gemini = env_gemini_config
        except ValueError:
            # Gemini config not available from env vars, that's okay
            pass

        return config

    def save_project_config(self, project_path: str, config: DevAgentConfig) -> None:
        """Save project-specific configuration.

        Args:
            project_path: Path to the project
            config: Configuration to save

        Note:
            API keys are saved in plain text to the config file.
            Users should use environment variables for production deployments.
        """
        project_config_path = self.get_project_config_path(project_path)
        project_config_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(project_config_path, "w", encoding="utf-8") as f:
                # Don't redact secrets when saving to file
                json.dump(config.to_dict(redact_secrets=False), f, indent=2)
        except OSError as e:
            print(f"Warning: Failed to save project config: {e}")

    def get_azure_openai_config(self) -> PydanticAzureOpenAIConfig:
        """Get Azure OpenAI configuration with validation.

        Returns:
            Validated Azure OpenAI configuration

        Raises:
            ValueError: If Azure OpenAI is not configured

        Note:
            This method checks environment variables first, then falls back
            to the config file. If neither is available, raises an error.
        """
        config = self.get_config()

        if config.azure_openai is None:
            raise ValueError(
                "Azure OpenAI is not configured. Please set environment variables:\n"
                "  AZURE_OPENAI_ENDPOINT\n"
                "  AZURE_OPENAI_API_KEY\n"
                "  AZURE_OPENAI_DEPLOYMENT_NAME\n"
                "  AZURE_OPENAI_EMBEDDING_DEPLOYMENT\n"
                "Or run: dev-agent azure configure"
            )

        return config.azure_openai

    def validate_azure_config(self) -> tuple[bool, str]:
        """Validate Azure OpenAI configuration.

        Returns:
            Tuple of (is_valid, error_message)
            If valid, error_message is empty string
        """
        try:
            config = self.get_azure_openai_config()

            # Check required fields
            if not config.endpoint:
                return False, "Azure OpenAI endpoint is not set"

            if not config.api_key:
                return False, "Azure OpenAI API key is not set"

            if not config.deployment_name:
                return False, "Azure OpenAI deployment name is not set"

            if not config.embedding_deployment:
                return False, "Azure OpenAI embedding deployment is not set"

            return True, ""

        except ValueError as e:
            return False, str(e)

    def load_gemini_config(self) -> GeminiConfig:
        """Load Gemini configuration from environment variables.

        Environment Variables:
            GEMINI_API_KEY: Gemini API key (required)
            GEMINI_MODEL_NAME: Model for code generation (optional, default: gemini-pro)
            GEMINI_EMBEDDING_MODEL: Model for embeddings (optional, default: embedding-001)
            GEMINI_API_ENDPOINT: API endpoint (optional, default: generativelanguage.googleapis.com)
            GEMINI_MAX_OUTPUT_TOKENS: Max output tokens (optional, default: 2048)
            GEMINI_TEMPERATURE: Temperature (optional, default: 0.7)
            GEMINI_TOP_P: Top-p parameter (optional, default: 0.95)
            GEMINI_TOP_K: Top-k parameter (optional, default: 40)
            GEMINI_MAX_RETRIES: Max retries (optional, default: 3)
            GEMINI_TIMEOUT: Timeout in seconds (optional, default: 60)
            GEMINI_BATCH_SIZE: Batch size (optional, default: 16)

        Returns:
            GeminiConfig instance loaded from environment variables

        Raises:
            ValueError: If required environment variables are missing or invalid
        """
        from dev_agent.models.llm_config import GeminiConfig
        from pydantic import SecretStr

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is required. "
                "Get your API key at: https://makersuite.google.com/app/apikey"
            )

        try:
            # Build config from env vars
            config_data: dict[str, Any] = {
                "api_key": SecretStr(api_key),
            }

            # Add optional env vars if present
            if model_name := os.getenv("GEMINI_MODEL_NAME"):
                config_data["model_name"] = model_name

            if embedding_model := os.getenv("GEMINI_EMBEDDING_MODEL"):
                config_data["embedding_model"] = embedding_model

            if api_endpoint := os.getenv("GEMINI_API_ENDPOINT"):
                config_data["api_endpoint"] = api_endpoint

            if max_output_tokens := os.getenv("GEMINI_MAX_OUTPUT_TOKENS"):
                config_data["max_output_tokens"] = int(max_output_tokens)

            if temperature := os.getenv("GEMINI_TEMPERATURE"):
                config_data["temperature"] = float(temperature)

            if top_p := os.getenv("GEMINI_TOP_P"):
                config_data["top_p"] = float(top_p)

            if top_k := os.getenv("GEMINI_TOP_K"):
                config_data["top_k"] = int(top_k)

            if max_retries := os.getenv("GEMINI_MAX_RETRIES"):
                config_data["max_retries"] = int(max_retries)

            if timeout := os.getenv("GEMINI_TIMEOUT"):
                config_data["timeout"] = int(timeout)

            if batch_size := os.getenv("GEMINI_BATCH_SIZE"):
                config_data["batch_size"] = int(batch_size)

            # Parse safety settings from JSON string
            if safety_settings_json := os.getenv("GEMINI_SAFETY_SETTINGS"):
                try:
                    safety_settings = json.loads(safety_settings_json)
                    if isinstance(safety_settings, dict):
                        config_data["safety_settings"] = safety_settings
                    else:
                        logger.warning(
                            "GEMINI_SAFETY_SETTINGS must be a JSON object. "
                            f"Got {type(safety_settings).__name__}. Using default safety settings."
                        )
                except json.JSONDecodeError as e:
                    logger.warning(
                        f"Failed to parse GEMINI_SAFETY_SETTINGS as JSON: {e}. "
                        "Using default safety settings."
                    )

            return GeminiConfig(**config_data)

        except (ValidationError, ValueError) as e:
            raise ValueError(f"Failed to load Gemini config from environment: {e}") from e

    def load_azure_config(self) -> PydanticAzureOpenAIConfig:
        """Load Azure OpenAI configuration from environment variables.

        This is a convenience method that wraps _load_azure_config_from_env
        and raises a clear error if configuration is not available.

        Returns:
            AzureOpenAIConfig instance loaded from environment variables

        Raises:
            ValueError: If required environment variables are missing or invalid
        """
        config = self._load_azure_config_from_env()
        if config is None:
            raise ValueError(
                "Azure OpenAI configuration is not available. Please set environment variables:\n"
                "  AZURE_OPENAI_ENDPOINT\n"
                "  AZURE_OPENAI_API_KEY (or AZURE_OPENAI_TOKEN for Azure AD)\n"
                "  AZURE_OPENAI_DEPLOYMENT_NAME\n"
                "  AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
            )
        return config

    def get_llm_provider(self) -> LLMProvider:
        """Determine which LLM provider to use based on configuration and environment.

        Provider selection logic:
        1. Check PREFERRED_LLM_PROVIDER environment variable
        2. If not set, default to Azure OpenAI for backward compatibility
        3. Validate that the selected provider has valid credentials

        Returns:
            LLMProvider enum value for the active provider

        Raises:
            ValueError: If no valid provider configuration is found

        Environment Variables:
            PREFERRED_LLM_PROVIDER: "azure_openai" or "gemini" (optional, defaults to "azure_openai")
        """
        # Check environment variable for preferred provider
        preferred_provider = os.getenv("PREFERRED_LLM_PROVIDER", "azure_openai").lower()
        
        # Map string values to enum
        provider_mapping = {
            "azure": LLMProvider.AZURE_OPENAI,
            "azure_openai": LLMProvider.AZURE_OPENAI,
            "gemini": LLMProvider.GEMINI,
        }
        
        if preferred_provider not in provider_mapping:
            raise ValueError(
                f"Unsupported LLM provider: {preferred_provider}. "
                f"Supported providers: {', '.join(provider_mapping.keys())}"
            )
        
        provider = provider_mapping[preferred_provider]
        
        # Validate that the selected provider has valid configuration
        is_valid, error_msg = self.validate_provider_config(provider)
        if not is_valid:
            # Try to fall back to the other provider if the preferred one is not configured
            fallback_provider = (
                LLMProvider.GEMINI if provider == LLMProvider.AZURE_OPENAI 
                else LLMProvider.AZURE_OPENAI
            )
            
            fallback_valid, _ = self.validate_provider_config(fallback_provider)
            if fallback_valid:
                logger.warning(
                    f"Preferred provider {provider.value} is not configured: {error_msg}. "
                    f"Falling back to {fallback_provider.value}"
                )
                return fallback_provider
            
            # Neither provider is configured
            raise ValueError(
                f"No valid LLM provider configuration found. "
                f"Preferred provider ({provider.value}) error: {error_msg}. "
                f"Please configure at least one provider."
            )
        
        return provider

    def validate_provider_config(self, provider: LLMProvider) -> tuple[bool, str]:
        """Validate configuration for a specific LLM provider.

        Args:
            provider: LLM provider to validate

        Returns:
            Tuple of (is_valid, error_message)
            If valid, error_message is empty string

        Example:
            ```python
            config_manager = ConfigManager()
            is_valid, error = config_manager.validate_provider_config(LLMProvider.GEMINI)
            if not is_valid:
                print(f"Gemini configuration error: {error}")
            ```
        """
        try:
            if provider == LLMProvider.AZURE_OPENAI:
                # Try to load Azure OpenAI configuration
                self.load_azure_config()
                return True, ""
            
            elif provider == LLMProvider.GEMINI:
                # Try to load Gemini configuration
                self.load_gemini_config()
                return True, ""
            
            else:
                return False, f"Unsupported provider: {provider.value}"
                
        except ValueError as e:
            return False, str(e)

    def get_llm_config(self, provider: LLMProvider | None = None) -> PydanticAzureOpenAIConfig | GeminiConfig:
        """Get LLM configuration for the specified or active provider.

        Args:
            provider: LLM provider to get config for (if None, uses active provider)

        Returns:
            Configuration object for the specified provider

        Raises:
            ValueError: If provider is not configured or unsupported

        Example:
            ```python
            config_manager = ConfigManager()
            
            # Get config for active provider
            llm_config = config_manager.get_llm_config()
            
            # Get config for specific provider
            azure_config = config_manager.get_llm_config(LLMProvider.AZURE_OPENAI)
            gemini_config = config_manager.get_llm_config(LLMProvider.GEMINI)
            ```
        """
        if provider is None:
            provider = self.get_llm_provider()

        if provider == LLMProvider.AZURE_OPENAI:
            return self.load_azure_config()
        elif provider == LLMProvider.GEMINI:
            return self.load_gemini_config()
        else:
            raise ValueError(f"Unsupported LLM provider: {provider.value}")

    def get_gemini_config(self) -> GeminiConfig:
        """Get Gemini configuration with validation.

        Returns:
            Validated Gemini configuration

        Raises:
            ValueError: If Gemini is not configured

        Note:
            This method checks environment variables first, then falls back
            to the config file. If neither is available, raises an error.
        """
        config = self.get_config()

        if config.gemini is None:
            # Try to load from environment variables
            try:
                return self.load_gemini_config()
            except ValueError:
                raise ValueError(
                    "Gemini is not configured. Please set environment variables:\n"
                    "  GEMINI_API_KEY\n"
                    "Or run: dev-agent gemini configure"
                ) from None

        return config.gemini
