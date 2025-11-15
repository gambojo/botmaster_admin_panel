"""
Audit logging system for admin panel.
Works with the new centralized logging system.
"""

import logging
from typing import Optional, Dict, Any


class AuditLogger:
    """
    Audit logger that works with the new centralized logging system.
    Provides specialized methods for different types of audit events.
    """

    def __init__(self, config_manager):
        """
        Initialize audit logger.

        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.audit_enabled = self.config_manager.get('logging.audit_log.enable', True)

        # Get specialized loggers - они будут использовать настройки из корневого логгера
        self.audit_logger = logging.getLogger('AuditLogger')
        self.api_logger = logging.getLogger('AuditLoggerAPI')
        self.auth_logger = logging.getLogger('AuditLoggerAuth')
        self.security_logger = logging.getLogger('AuditLoggerSecurity')

        self.audit_logger.info(f"AuditLogger initialized (enabled: {self.audit_enabled})")

    def _should_log_audit(self, log_type: str) -> bool:
        """Check if specific audit log type should be recorded."""
        return self.audit_enabled

    def log_api_call(self, endpoint: str, method: str, username: str = None,
                     response_status: int = None, ip_address: str = None,
                     user_agent: str = None, processing_time: float = None):
        """
        Log API calls with detailed user information.
        """
        if not self._should_log_audit('api_calls'):
            return

        status_info = f" [{response_status}]" if response_status is not None else ""
        user_info = f" by {username}" if username else ""
        time_info = f" ({processing_time:.3f}s)" if processing_time is not None else ""

        log_message = f"{method} {endpoint}{status_info}{user_info} from {ip_address}{time_info}"

        # Determine log level
        if response_status is None:
            level = logging.INFO
        elif response_status < 400:
            level = logging.INFO
        else:
            level = logging.WARNING

        self.api_logger.log(level, log_message)

    def log_user_action(self, username: str, action: str, target: str = None,
                        success: bool = True, ip_address: str = None):
        """
        Log user actions with simplified format.
        """
        if not self._should_log_audit('user_actions'):
            return

        target_info = f" on {target}" if target else ""
        status = "success" if success else "failed"

        log_message = f"USER {username} {action}{target_info} - {status}"
        if ip_address:
            log_message += f" from {ip_address}"

        level = logging.INFO if success else logging.WARNING
        self.audit_logger.log(level, log_message)

    def log_auth_event(self, event_type: str, username: str = None,
                       success: bool = True, ip_address: str = None):
        """
        Log authentication events with simplified format.
        """
        if not self._should_log_audit('auth_events'):
            return

        user_info = f" for {username}" if username else ""
        status = "success" if success else "failed"

        log_message = f"AUTH {event_type}{user_info} - {status}"
        if ip_address:
            log_message += f" from {ip_address}"

        level = logging.INFO if success else logging.WARNING
        self.auth_logger.log(level, log_message)

    def log_security_event(self, event_type: str, severity: str = 'MEDIUM',
                           username: str = None, ip_address: str = None,
                           details: str = None):
        """
        Log security-related events with simplified format.
        """
        if not self._should_log_audit('security_events'):
            return

        user_info = f" user:{username}" if username else ""
        ip_info = f" ip:{ip_address}" if ip_address else ""
        details_info = f" - {details}" if details else ""

        log_message = f"SECURITY {event_type}{user_info}{ip_info}{details_info}"

        # Map severity to log levels
        severity_levels = {
            'LOW': logging.INFO,
            'MEDIUM': logging.WARNING,
            'HIGH': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }

        level = severity_levels.get(severity, logging.WARNING)
        self.security_logger.log(level, log_message)

    def get_client_info(self, request) -> Dict[str, str]:
        """
        Extract client information from request.
        """
        return {
            'ip_address': request.remote,
            'user_agent': request.headers.get('User-Agent', 'Unknown')
        }
