"""Utility to log function execution time using structlog.

Logs START and END messages with elapsed time. Catches and logs exceptions.
The log level can be set via decorator parameter (default="INFO") or TIMER_LOG_LEVEL environment variable.
Environment variable takes precedence if set.
"""

import functools
import os
import time
from collections.abc import Callable
from typing import TypeVar, cast

import structlog

from logger._utils import _get_log_method

# Preserve exact function/method signature through decorator
F = TypeVar("F", bound=Callable)


def timer(func=None, *, level: str = "INFO"):
    """Decorator that logs function execution time using structlog.

    START/END logs use the specified level (default: INFO). Environment variable
    TIMER_LOG_LEVEL overrides the decorator parameter if set.

    Usage:
        @timer
        def my_func(): ...

        @timer()
        def my_func(): ...

        @timer(level="DEBUG")
        def my_func(): ...

    Args:
        func: The function to decorate (when used without parentheses)
        level: Log level for START/END messages (default: "INFO")
    """

    def decorator(f: F) -> F:
        func_name = f.__qualname__

        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            log_ctx = {"func_name": func_name}
            logger = structlog.get_logger()

            # Environment variable takes precedence
            env_level = os.getenv("TIMER_LOG_LEVEL")
            effective_level = env_level or level
            log_method = _get_log_method(logger, effective_level)

            log_method("[START]", **log_ctx)
            start_time = time.time()
            try:
                result = f(*args, **kwargs)
                log_method("[END]", elapsed=f"{time.time() - start_time:.3f}s", **log_ctx)
                return result
            except Exception:
                logger.exception("[ERROR]", elapsed=f"{time.time() - start_time:.3f}s", **log_ctx)
                raise

        return cast(F, wrapper)

    # Support both @timer and @timer() and @timer(level="DEBUG")
    if func is None:
        return decorator
    return decorator(func)
