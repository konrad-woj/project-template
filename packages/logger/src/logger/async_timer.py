"""Async timer utility that logs task execution time using structlog.

Logs TASK START and TASK END messages with elapsed time. Catches and logs exceptions.
The log level can be set via decorator parameter (default="INFO") or TIMER_LOG_LEVEL environment variable.
Environment variable takes precedence if set.
"""

import asyncio
import functools
import os
import time
from collections.abc import Callable, Coroutine
from typing import Any, ParamSpec, TypeVar, cast, overload

import structlog

from logger._utils import _get_log_method

P = ParamSpec("P")
R = TypeVar("R")


@overload
def async_timer[**P, R](
    func: Callable[P, Coroutine[Any, Any, R]],
) -> Callable[P, Coroutine[Any, Any, R]]:  # pragma: no cover - typing overload
    ...


@overload
def async_timer(
    func: None = ..., *, enabled: bool | None = None, level: str = "INFO"
) -> Callable[
    [Callable[P, Coroutine[Any, Any, R]]], Callable[P, Coroutine[Any, Any, R]]
]:  # pragma: no cover - typing overload
    ...


def async_timer[**P, R](
    func: Callable[P, Coroutine[Any, Any, R]] | None = None,
    *,
    enabled: bool | None = None,
    level: str = "INFO",
) -> (
    Callable[P, Coroutine[Any, Any, R]]
    | Callable[[Callable[P, Coroutine[Any, Any, R]]], Callable[P, Coroutine[Any, Any, R]]]
):
    """Decorator that logs task start and completion using structlog.

    TASK START/END logs use the specified level (default: INFO). Environment variable
    TIMER_LOG_LEVEL overrides the decorator parameter if set.

    Usage:
        @async_timer
        async def my_func(): ...

        @async_timer()
        async def my_func(): ...

        @async_timer(level="DEBUG")
        async def my_func(): ...

        @async_timer(enabled=False)
        async def my_func(): ...

    Args:
        func: The async function to decorate (when used without parentheses)
        enabled: Whether timing is enabled (default: True, or based on ASYNC_TIMER_DISABLED env)
        level: Log level for TASK START/END messages (default: "INFO")
    """

    def decorator(f: Callable[P, Coroutine[Any, Any, R]]) -> Callable[P, Coroutine[Any, Any, R]]:
        # Check if timer should be enabled
        is_enabled = enabled
        if is_enabled is None:
            env_val = os.environ.get("ASYNC_TIMER_DISABLED", "0").lower()
            is_disabled = env_val in ("true", "1")
            is_enabled = not is_disabled

        if not is_enabled:
            return f

        task_name = f.__qualname__

        @functools.wraps(f)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            task = asyncio.current_task()
            task_id = id(task) if task else "unknown"
            log_ctx = {"task_name": task_name, "task_id": task_id}
            logger = structlog.get_logger()

            # Environment variable takes precedence
            env_level = os.getenv("TIMER_LOG_LEVEL")
            effective_level = env_level or level
            log_method = _get_log_method(logger, effective_level)

            log_method("[TASK START]", **log_ctx)
            start_time = time.time()
            try:
                result = await f(*args, **kwargs)
                log_method("[TASK END]", elapsed=f"{time.time() - start_time:.3f}s", **log_ctx)
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    "[TASK ERROR]", elapsed=f"{elapsed:.3f}s", error_type=type(e).__name__, error=str(e), **log_ctx
                )
                raise

        return cast(Callable[P, Coroutine[Any, Any, R]], wrapper)

    if func is None:
        return decorator

    return decorator(cast(Callable[P, Coroutine[Any, Any, R]], func))
