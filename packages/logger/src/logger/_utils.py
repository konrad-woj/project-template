"""Internal utilities shared across the logger package."""

from collections.abc import Callable

import structlog


def _get_log_method(logger: structlog.BoundLogger, level: str) -> Callable:
    """Get the appropriate log method based on level string."""
    level_lower = level.lower()
    if level_lower == "debug":
        return logger.debug
    elif level_lower == "info":
        return logger.info
    elif level_lower == "warning":
        return logger.warning
    elif level_lower == "error":
        return logger.error
    else:
        return logger.info  # Default fallback
