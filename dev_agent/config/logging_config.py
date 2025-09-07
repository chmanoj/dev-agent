"""Logging configuration for dev-agent."""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from .config_manager import LoggingConfig


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        """Format log record with colors."""
        if hasattr(record, 'levelname'):
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


def setup_logging(
    config: LoggingConfig,
    project_path: Optional[str] = None,
    verbose: bool = False
) -> None:
    """Set up logging configuration.
    
    Args:
        config: Logging configuration
        project_path: Optional project path for log files
        verbose: Enable verbose logging
    """
    # Determine log level
    if verbose:
        log_level = logging.DEBUG
    else:
        log_level = getattr(logging, config.level.upper(), logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    if config.console_enabled:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        if config.color_output and sys.stdout.isatty():
            console_formatter = ColoredFormatter(config.format)
        else:
            console_formatter = logging.Formatter(config.format)
        
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if config.file_enabled:
        log_dir = Path.home() / ".dev_agent" / "logs"
        if project_path:
            log_dir = Path(project_path) / ".dev_agent" / "logs"
        
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "dev_agent.log"
        
        # Use rotating file handler to manage log file size
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=config.max_file_size_mb * 1024 * 1024,
            backupCount=config.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        
        file_formatter = logging.Formatter(config.format)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger('dev_agent').setLevel(log_level)
    
    # Suppress noisy third-party loggers unless in debug mode
    if log_level > logging.DEBUG:
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('transformers').setLevel(logging.WARNING)
        logging.getLogger('sentence_transformers').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_system_info() -> None:
    """Log system information for debugging."""
    logger = get_logger(__name__)
    
    import platform
    import sys
    
    logger.info("=== System Information ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Architecture: {platform.architecture()}")
    logger.info(f"Processor: {platform.processor()}")
    logger.info("=== End System Information ===")


def log_config_info(config) -> None:
    """Log configuration information.
    
    Args:
        config: Configuration object to log
    """
    logger = get_logger(__name__)
    
    logger.debug("=== Configuration ===")
    logger.debug(f"Version: {config.version}")
    logger.debug(f"Logging level: {config.logging.level}")
    logger.debug(f"Indexing model: {config.indexing.embedding_model}")
    logger.debug(f"Vector DB type: {config.indexing.vector_db_type}")
    logger.debug(f"Auto approve: {config.cli.auto_approve}")
    logger.debug("=== End Configuration ===")