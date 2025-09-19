"""Configuration management for dev-agent."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class AzureOpenAIConfig:
    """Configuration for Azure OpenAI integration."""

    api_key: str | None = None
    endpoint: str | None = None
    api_version: str = "2024-02-01"
    chat_model: str = "gpt-4"
    embedding_model: str = "text-embedding-ada-002"
    max_tokens: int = 4000
    temperature: float = 0.1
    timeout: int = 60
    max_retries: int = 3


@dataclass
class IndexingConfig:
    """Configuration for indexing operations."""

    max_file_size_mb: int = 10
    chunk_size: int = 1000
    overlap_size: int = 200
    max_files_per_batch: int = 100
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    vector_db_type: str = "faiss"
    use_azure_embeddings: bool = False


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
    azure_openai: AzureOpenAIConfig
    version: str = "0.1.0"

    @classmethod
    def default(cls) -> "DevAgentConfig":
        """Create default configuration."""
        return cls(
            indexing=IndexingConfig(),
            logging=LoggingConfig(),
            cli=CLIConfig(),
            azure_openai=AzureOpenAIConfig(),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DevAgentConfig":
        """Create configuration from dictionary."""
        return cls(
            indexing=IndexingConfig(**data.get("indexing", {})),
            logging=LoggingConfig(**data.get("logging", {})),
            cli=CLIConfig(**data.get("cli", {})),
            azure_openai=AzureOpenAIConfig(**data.get("azure_openai", {})),
            version=data.get("version", "0.1.0"),
        )


class ConfigManager:
    """Manages configuration loading, saving, and access."""

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

    def _ensure_config_dir(self) -> None:
        """Ensure configuration directory exists."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

    def load_config(self) -> DevAgentConfig:
        """Load configuration from file or create default.

        Returns:
            Loaded or default configuration
        """
        if self._config is not None:
            return self._config

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

        return self._config

    def save_config(self, config: DevAgentConfig | None = None) -> None:
        """Save configuration to file.

        Args:
            config: Configuration to save (uses current if None)
        """
        if config is None:
            config = self._config or DevAgentConfig.default()

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config.to_dict(), f, indent=2)
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
        """Load project-specific configuration.

        Args:
            project_path: Path to the project

        Returns:
            Project configuration (falls back to global if not found)
        """
        project_config_path = self.get_project_config_path(project_path)

        if project_config_path.exists():
            try:
                with open(project_config_path, encoding="utf-8") as f:
                    data = json.load(f)
                return DevAgentConfig.from_dict(data)
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                print(f"Warning: Failed to load project config: {e}")

        # Fall back to global configuration
        return self.load_config()

    def save_project_config(self, project_path: str, config: DevAgentConfig) -> None:
        """Save project-specific configuration.

        Args:
            project_path: Path to the project
            config: Configuration to save
        """
        project_config_path = self.get_project_config_path(project_path)
        project_config_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(project_config_path, "w", encoding="utf-8") as f:
                json.dump(config.to_dict(), f, indent=2)
        except OSError as e:
            print(f"Warning: Failed to save project config: {e}")
