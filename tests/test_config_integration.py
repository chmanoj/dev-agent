"""Integration tests for configuration management."""

import json
import os
import shutil
import tempfile

import pytest

from dev_agent.config import ConfigManager, DevAgentConfig, get_logger, setup_logging


class TestConfigManagerIntegration:
    """Integration tests for ConfigManager."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_config.json")
        self.config_manager = ConfigManager(self.config_path)

    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_load_default_config(self):
        """Test loading default configuration when no file exists."""
        config = self.config_manager.load_config()

        assert isinstance(config, DevAgentConfig)
        assert config.version == "0.1.0"
        assert config.logging.level == "INFO"
        assert (
            config.indexing.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"
        )
        assert config.cli.auto_approve is False

    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        # Create custom config
        config = DevAgentConfig.default()
        config.logging.level = "DEBUG"
        config.cli.auto_approve = True
        config.indexing.max_file_size_mb = 20

        # Save config
        self.config_manager.save_config(config)

        # Verify file was created
        assert os.path.exists(self.config_path)

        # Create new manager and load config
        new_manager = ConfigManager(self.config_path)
        loaded_config = new_manager.load_config()

        assert loaded_config.logging.level == "DEBUG"
        assert loaded_config.cli.auto_approve is True
        assert loaded_config.indexing.max_file_size_mb == 20

    def test_update_config(self):
        """Test updating configuration values."""
        # Load initial config
        config = self.config_manager.load_config()
        assert config.logging.level == "INFO"

        # Update config
        self.config_manager.update_config(
            logging={"level": "WARNING", "file_enabled": False},
            cli={"auto_approve": True},
        )

        # Verify updates
        updated_config = self.config_manager.get_config()
        assert updated_config.logging.level == "WARNING"
        assert updated_config.logging.file_enabled is False
        assert updated_config.cli.auto_approve is True

    def test_reset_to_default(self):
        """Test resetting configuration to defaults."""
        # Modify config
        self.config_manager.update_config(
            logging={"level": "DEBUG"}, cli={"auto_approve": True}
        )

        # Reset to default
        self.config_manager.reset_to_default()

        # Verify reset
        config = self.config_manager.get_config()
        assert config.logging.level == "INFO"
        assert config.cli.auto_approve is False

    def test_project_config_loading(self):
        """Test loading project-specific configuration."""
        project_path = os.path.join(self.temp_dir, "test_project")
        os.makedirs(project_path)

        # Create project config directory
        project_config_dir = os.path.join(project_path, ".dev_agent")
        os.makedirs(project_config_dir)

        # Create project-specific config
        project_config = DevAgentConfig.default()
        project_config.cli.auto_approve = True
        project_config.logging.level = "WARNING"

        project_config_path = os.path.join(project_config_dir, "config.json")
        with open(project_config_path, "w") as f:
            json.dump(project_config.to_dict(), f)

        # Load project config
        loaded_config = self.config_manager.load_project_config(project_path)

        assert loaded_config.cli.auto_approve is True
        assert loaded_config.logging.level == "WARNING"

    def test_project_config_fallback(self):
        """Test fallback to global config when project config doesn't exist."""
        project_path = os.path.join(self.temp_dir, "test_project")
        os.makedirs(project_path)

        # Set global config
        self.config_manager.update_config(logging={"level": "ERROR"})

        # Load project config (should fall back to global)
        loaded_config = self.config_manager.load_project_config(project_path)

        assert loaded_config.logging.level == "ERROR"

    def test_save_project_config(self):
        """Test saving project-specific configuration."""
        project_path = os.path.join(self.temp_dir, "test_project")
        os.makedirs(project_path)

        # Create project config
        project_config = DevAgentConfig.default()
        project_config.indexing.chunk_size = 2000

        # Save project config
        self.config_manager.save_project_config(project_path, project_config)

        # Verify file was created
        expected_path = os.path.join(project_path, ".dev_agent", "config.json")
        assert os.path.exists(expected_path)

        # Verify content
        with open(expected_path) as f:
            data = json.load(f)

        assert data["indexing"]["chunk_size"] == 2000

    def test_corrupted_config_file(self):
        """Test handling of corrupted configuration file."""
        # Create corrupted config file
        with open(self.config_path, "w") as f:
            f.write("invalid json content")

        # Should fall back to default config
        config = self.config_manager.load_config()

        assert isinstance(config, DevAgentConfig)
        assert config.logging.level == "INFO"  # Default value


class TestLoggingIntegration:
    """Integration tests for logging configuration."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = os.path.join(self.temp_dir, "test_project")
        os.makedirs(self.project_path)

    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_setup_logging_with_config(self):
        """Test setting up logging with configuration."""
        from dev_agent.config.config_manager import LoggingConfig

        config = LoggingConfig(level="DEBUG", file_enabled=True, console_enabled=True)

        # Setup logging
        setup_logging(config, project_path=self.project_path, verbose=True)

        # Get logger and test
        logger = get_logger(__name__)
        assert logger.level <= 10  # DEBUG level

        # Test logging
        logger.debug("Test debug message")
        logger.info("Test info message")
        logger.warning("Test warning message")

        # Check that log file was created
        log_file = os.path.join(
            self.project_path, ".dev_agent", "logs", "dev_agent.log"
        )
        assert os.path.exists(log_file)

    def test_logging_file_rotation(self):
        """Test log file rotation."""
        from dev_agent.config.config_manager import LoggingConfig

        config = LoggingConfig(
            level="INFO",
            file_enabled=True,
            max_file_size_mb=1,  # Small size to trigger rotation
            backup_count=2,
        )

        setup_logging(config, project_path=self.project_path)
        logger = get_logger(__name__)

        # Generate enough log messages to trigger rotation
        for i in range(1000):
            logger.info(f"Test message {i} - " + "x" * 100)

        # Check that log files exist
        log_dir = os.path.join(self.project_path, ".dev_agent", "logs")
        log_files = [f for f in os.listdir(log_dir) if f.startswith("dev_agent.log")]

        # Should have main log file and potentially backup files
        assert len(log_files) >= 1

    def test_console_only_logging(self):
        """Test console-only logging configuration."""
        from dev_agent.config.config_manager import LoggingConfig

        config = LoggingConfig(level="INFO", file_enabled=False, console_enabled=True)

        setup_logging(config, project_path=self.project_path)
        logger = get_logger(__name__)

        # Test logging
        logger.info("Test console message")

        # Check that no log file was created
        log_file = os.path.join(
            self.project_path, ".dev_agent", "logs", "dev_agent.log"
        )
        assert not os.path.exists(log_file)

    def test_file_only_logging(self):
        """Test file-only logging configuration."""
        from dev_agent.config.config_manager import LoggingConfig

        config = LoggingConfig(level="INFO", file_enabled=True, console_enabled=False)

        setup_logging(config, project_path=self.project_path)
        logger = get_logger(__name__)

        # Test logging
        logger.info("Test file message")

        # Check that log file was created
        log_file = os.path.join(
            self.project_path, ".dev_agent", "logs", "dev_agent.log"
        )
        assert os.path.exists(log_file)

        # Verify content
        with open(log_file) as f:
            content = f.read()

        assert "Test file message" in content


class TestConfigSerialization:
    """Test configuration serialization and deserialization."""

    def test_config_to_dict(self):
        """Test converting configuration to dictionary."""
        config = DevAgentConfig.default()
        config.logging.level = "DEBUG"
        config.cli.auto_approve = True

        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["logging"]["level"] == "DEBUG"
        assert config_dict["cli"]["auto_approve"] is True
        assert config_dict["version"] == "0.1.0"

    def test_config_from_dict(self):
        """Test creating configuration from dictionary."""
        config_dict = {
            "version": "0.2.0",
            "logging": {"level": "WARNING", "file_enabled": False},
            "cli": {"auto_approve": True, "color_output": False},
            "indexing": {"max_file_size_mb": 25, "embedding_model": "custom-model"},
        }

        config = DevAgentConfig.from_dict(config_dict)

        assert config.version == "0.2.0"
        assert config.logging.level == "WARNING"
        assert config.logging.file_enabled is False
        assert config.cli.auto_approve is True
        assert config.cli.color_output is False
        assert config.indexing.max_file_size_mb == 25
        assert config.indexing.embedding_model == "custom-model"

    def test_partial_config_from_dict(self):
        """Test creating configuration from partial dictionary."""
        config_dict = {"logging": {"level": "ERROR"}}

        config = DevAgentConfig.from_dict(config_dict)

        # Should use provided values
        assert config.logging.level == "ERROR"

        # Should use defaults for missing values
        assert config.logging.file_enabled is True  # Default
        assert config.cli.auto_approve is False  # Default
        assert config.version == "0.1.0"  # Default


if __name__ == "__main__":
    pytest.main([__file__])
