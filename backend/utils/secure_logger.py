"""
Secure Logger Utility
Automatically redacts sensitive information from log messages.
"""

import re
import os
from datetime import datetime


class SecureLogger:
    """Logger that automatically redacts sensitive information."""

    # Patterns to redact
    SENSITIVE_PATTERNS = [
        (r'jwt[_-]?secret["\']?\s*[:=]\s*["\']?([^"\'\s]+)', '[JWT_SECRET_REDACTED]'),
        (r'api[_-]?key["\']?\s*[:=]\s*["\']?([^"\'\s]+)', '[API_KEY_REDACTED]'),
        (r'password["\']?\s*[:=]\s*["\']?([^"\'\s]+)', '[PASSWORD_REDACTED]'),
        (r'bearer\s+([a-zA-Z0-9\-_\.]+)', 'Bearer [TOKEN_REDACTED]'),
        (r'mongodb(?:\+srv)?://([^@]+)@', 'mongodb://[CREDENTIALS_REDACTED]@'),
    ]

    @staticmethod
    def redact(message):
        """Redact sensitive information from message"""
        if not isinstance(message, str):
            message = str(message)

        for pattern, replacement in SecureLogger.SENSITIVE_PATTERNS:
            message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)

        return message

    @staticmethod
    def log(message, level='INFO'):
        """Log message with automatic redaction"""
        redacted_message = SecureLogger.redact(message)

        # Add timestamp
        timestamp = datetime.utcnow().isoformat()

        # Only log in development or if LOG_LEVEL allows
        log_level = os.getenv('LOG_LEVEL', 'INFO')

        if level == 'ERROR' or log_level == 'DEBUG':
            print(f"[{timestamp}] [{level}] {redacted_message}")

    @staticmethod
    def debug(message):
        SecureLogger.log(message, 'DEBUG')

    @staticmethod
    def info(message):
        SecureLogger.log(message, 'INFO')

    @staticmethod
    def warning(message):
        SecureLogger.log(message, 'WARNING')

    @staticmethod
    def error(message):
        SecureLogger.log(message, 'ERROR')


# Convenience instance
logger = SecureLogger()
