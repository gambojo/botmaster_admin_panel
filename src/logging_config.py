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
    Setup centralized logging configuration with separate audit logging.
    """
    global _logging_configured
    if _logging_configured:
        return

    # Основные логи
    logging_config = config.get('logging', {}).get('standard_log', {})
    audit_config = config.get('logging', {}).get('audit_log', {})

    # Основная конфигурация
    log_level = logging_config.get('level', 'INFO').upper()
    log_file = logging_config.get('file', 'logs/admin_panel.log')
    log_dir = Path(log_file).parent
    log_to_console = logging_config.get('console', True)
    log_format = logging_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    max_size = logging_config.get('max_size', 10 * 1024 * 1024)

    # Создаем директорию логов
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()

    # Форматтер для основных логов
    formatter = logging.Formatter(log_format)

    # Консольный хендлер
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Файловый хендлер для основных логов
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

    # Хендлер для ошибок
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

    # Аудит логгер
    if audit_config.get('enable', True):
        # Создаем отдельные логгеры для всех типов аудита
        audit_loggers = [
            'AuditLogger',  # общий аудит
            'AuditLoggerAPI',  # API вызовы
            'AuditLoggerAuth',  # аутентификация
            'AuditLoggerSecurity'  # безопасность
        ]

        # Форматтер для аудит-логов
        audit_format = audit_config.get('format', '%(asctime)s - %(name)s - AUDIT - %(message)s')
        audit_formatter = logging.Formatter(audit_format)

        for logger_name in audit_loggers:
            audit_logger = logging.getLogger(logger_name)
            audit_logger.propagate = False  # Важно: не передавать в корневой логгер
            audit_logger.setLevel(logging.INFO)
            audit_logger.handlers.clear()  # Очищаем существующие хендлеры

            # Файловый хендлер для аудита
            audit_file = audit_config.get('file', 'logs/audit.log')
            if audit_file:
                audit_file_handler = RotatingFileHandler(
                    audit_file,
                    maxBytes=audit_config.get('max_size', max_size),
                    backupCount=5,
                    encoding='utf-8'
                )
                audit_file_handler.setLevel(logging.INFO)
                audit_file_handler.setFormatter(audit_formatter)
                audit_logger.addHandler(audit_file_handler)

            # Консольный хендлер для аудита (если включен)
            if audit_config.get('console', False):
                audit_console_handler = logging.StreamHandler(sys.stdout)
                audit_console_handler.setLevel(logging.INFO)
                audit_console_handler.setFormatter(audit_formatter)
                audit_logger.addHandler(audit_console_handler)

    # Логируем инициализацию
    logger = logging.getLogger('LoggingConfig')
    logger.debug(f"Logging initialized: level={log_level}, dir={log_dir}, console={log_to_console}")

    if audit_config.get('enable', True):
        logger.debug(f"Audit logging enabled: file={audit_config.get('file')}, console={audit_config.get('console')}")

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
