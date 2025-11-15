"""
Centralized logging configuration for the bot framework.
Each component gets its own logger instance via logging.getLogger(__name__).
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Dict, Any


# Flag to prevent multiple setup calls
_logging_configured = False


def setup_logging(config: Dict[str, Any]) -> None:
    """
    Setup centralized logging configuration.
    Can only be called once - subsequent calls are ignored.

    Args:
        config: Configuration dictionary with logging settings
    """
    global _logging_configured

    # Prevent multiple setups
    if _logging_configured:
        return

    logging_config = config.get('logging', {}).get('standard_log', {})

    # Get configuration
    log_level = logging_config.get('level', 'INFO').upper()
    log_file = logging_config.get('file', 'logs/admin_panel.log')
    log_dir = Path(log_file).parent
    log_to_console = logging_config.get('console', True)
    log_format = logging_config.get('format',
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    max_size = logging_config.get('max_size', 10 * 1024 * 1024)  # 10 MB

    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Get root logger (without name = root)
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(log_format)

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handler - main log
    main_log_file = Path(log_file)
    file_handler = RotatingFileHandler(
        main_log_file,
        maxBytes=max_size,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Error log file
    error_log_file = log_path / 'errors.log'
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=max_size,
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)

    # Log startup message using proper module logger
    logger = logging.getLogger('LoggingConfig')
    logger.debug(f"Logging initialized: level={log_level}, dir={log_dir}, console={log_to_console}")

    # Mark as configured
    _logging_configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a component.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
