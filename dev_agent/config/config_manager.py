"""Configuration management for dev-agent."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from pydantic import SecretStr, ValidationError

from dev_agent.models.llm_config import AzureOpenAIConfig as PydanticAzureOpenAIConfig


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
    version: str = "0.1.0"

    @classmethod
    def default(cls) -> "DevAgentConfig":
        """Create default configuration with optional Azure OpenAI."""
        return cls(
            indexing=IndexingConfig(),
            logging=LoggingConfig(),
            cli=CLIConfig(),
            azure_openai=None,  # Azure OpenAI config loaded from env vars
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
        
        return config_dict

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DevAgentConfig":
        """Create configuration from dictionary.
        
        Args:
            data: Configuration dictionary
            
        Returns:
            DevAgentConfig instance with validated Azure OpenAI config
        """
        # Parse Azure OpenAI config if present
        azure_config = None
        if "azure_openai" in data and data["azure_openai"]:
            azure_data = data["azure_openai"]
            # Handle legacy field names for backward compatibility
            if "chat_model" in azure_data and "deployment_name" not in azure_data:
                azure_data["deployment_name"] = azure_data.pop("chat_model")
            if "embedding_model" in azure_data and "embedding_deployment" not in azure_data:
                azure_data["embedding_deployment"] = azure_data.pop("embedding_model")
            
            # Skip if API key is redacted (will be loaded from env vars)
            if azure_data.get("api_key") != "***REDACTED***":
                try:
                    azure_config = PydanticAzureOpenAIConfig(**azure_data)
                except ValidationError:
                    # If validation fails, skip and rely on env vars
                    pass
        
        return cls(
            indexing=IndexingConfig(**data.get("indexing", {})),
            logging=LoggingConfig(**data.get("logging", {})),
            cli=CLIConfig(**data.get("cli", {})),
            azure_openai=azure_config,
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
        
        Returns:
            AzureOpenAIConfig if all required env vars are present, None otherwise
            
        Environment Variables:
            AZURE_OPENAI_ENDPOINT: Azure OpenAI endpoint URL (required)
            AZURE_OPENAI_API_KEY: Azure OpenAI API key (required)
            AZURE_OPENAI_API_VERSION: API version (optional, default: 2024-02-15-preview)
            AZURE_OPENAI_DEPLOYMENT_NAME: GPT-4 deployment name (required)
            AZURE_OPENAI_EMBEDDING_DEPLOYMENT: Embedding deployment name (required)
            AZURE_OPENAI_MAX_TOKENS: Max tokens (optional, default: 4000)
            AZURE_OPENAI_TEMPERATURE: Temperature (optional, default: 0.7)
            AZURE_OPENAI_MAX_RETRIES: Max retries (optional, default: 3)
            AZURE_OPENAI_TIMEOUT: Timeout in seconds (optional, default: 60)
            AZURE_OPENAI_BATCH_SIZE: Batch size (optional, default: 16)
        """
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
        
        # Check if required env vars are present
        if not all([endpoint, api_key, deployment_name, embedding_deployment]):
            return None
        
        try:
            # Build config from env vars
            config_data = {
                "endpoint": endpoint,
                "api_key": api_key,
                "deployment_name": deployment_name,
                "embedding_deployment": embedding_deployment,
            }
            
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
            
            return PydanticAzureOpenAIConfig(**config_data)
        
        except (ValidationError, ValueError) as e:
            print(f"Warning: Failed to load Azure OpenAI config from environment: {e}")
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

        # Override Azure OpenAI config with environment variables (highest precedence)
        env_azure_config = self._load_azure_config_from_env()
        if env_azure_config is not None:
            self._config.azure_openai = env_azure_config

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

        # Override Azure OpenAI config with environment variables (highest precedence)
        env_azure_config = self._load_azure_config_from_env()
        if env_azure_config is not None:
            config.azure_openai = env_azure_config

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
