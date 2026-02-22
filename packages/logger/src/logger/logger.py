import logging
import string
from collections.abc import MutableMapping
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

import structlog
from pydantic import BaseModel
from structlog.contextvars import merge_contextvars

from logger.sorter import SemanticSorter

# List of external logger names whose outputs should be intercepted and formatted by structlog.
# This ensures consistent logging style (such as JSON or colored output) for logs
# from these common frameworks (gunicorn, uvicorn, etc.) and related modules.
LOGGERS_TO_INTERCEPT = {
    "gunicorn",
    "fastapi",
    "gunicorn.access",
    "gunicorn.error",
    "uvicorn",
    "uvicorn.access",
    "rapidocr.inference_engine",
    "rapidocr.inference_engine.onnxruntime",
    "rapidocr.inference_engine.onnxruntime.main",
}


def pydantic_models_to_json(logger: Any, name: str, event_dict: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    """Recursively serializes any pydantic BaseModel value in the event dictionary to its JSON representation.

    Traverses the event_dict structure (including nested dicts, lists, tuples, and sets) and replaces any
    instance of a pydantic BaseModel with a dictionary containing its type and `.model_dump()` output.

    Args:
        logger (Any): Logger instance (not used within the function, included for structlog compatibility).
        name (str): Name of the current logger or event.
        event_dict (MutableMapping[str, Any]): Structlog event dictionary to process.

    Returns:
        MutableMapping[str, Any]: Event dictionary where all pydantic BaseModel instances
        have been serialized to JSON-compatible dicts.
    """

    def _convert(obj):
        if isinstance(obj, BaseModel):
            return {"type": type(obj).__name__, "body": obj.model_dump()}
        if isinstance(obj, dict):
            return {k: _convert(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_convert(v) for v in obj]
        if isinstance(obj, tuple):
            return tuple(_convert(v) for v in obj)
        if isinstance(obj, set):
            return {_convert(v) for v in obj}
        return obj

    return {k: _convert(v) for k, v in event_dict.items()}


def is_probably_binary_string(s: str, threshold: float = 0.1, max_run: int = 5) -> bool:
    """Heuristically determine if a string is likely to contain binary data.

    Args:
        s: The string to check.
        threshold: Proportion of non-printable characters to consider as binary.
        max_run: Maximum allowed consecutive non-printable characters.

    Returns:
        True if the string is likely binary, False otherwise.
    """

    if not s:
        return False

    # Null byte is a strong binary indicator
    if "\x00" in s:
        return True

    # Count non-printable characters
    non_printable = sum(1 for c in s if c not in string.printable)
    if (non_printable / len(s)) > threshold:
        return True

    # Check for long runs of non-printable characters
    current_run = 0
    for c in s:
        if c not in string.printable:
            current_run += 1
            if current_run > max_run:
                return True
        else:
            current_run = 0

    return False


def truncate_str_in_traceback_obj(value: Any, max_length: int = 500, max_depth: int = 10, _depth: int = 0) -> Any:
    """Recursively traverse and truncate string values in a traceback object.

    Args:
        value: The object to process.
        max_length: Maximum allowed string length.
        max_depth: Maximum recursion depth.
        _depth: Current recursion depth (used internally).

    Returns:
        The processed object with truncated strings and binary data replaced.
    """

    if _depth > max_depth:
        return "...truncated (max depth reached)..."
    if isinstance(value, bytes):
        return f"<binary data, length={len(value)}>"
    if isinstance(value, str):
        if is_probably_binary_string(value):
            return f"<binary-like string, length={len(value)}>"
        if len(value) > max_length:
            return f"{value[:max_length]}...[truncated, total length={len(value)}]"
        return value
    if isinstance(value, dict):
        return {k: truncate_str_in_traceback_obj(v, max_length, max_depth, _depth + 1) for k, v in value.items()}
    if isinstance(value, list):
        return [truncate_str_in_traceback_obj(v, max_length, max_depth, _depth + 1) for v in value]
    if isinstance(value, tuple):
        return tuple(truncate_str_in_traceback_obj(v, max_length, max_depth, _depth + 1) for v in value)
    if isinstance(value, set):
        return {truncate_str_in_traceback_obj(v, max_length, max_depth, _depth + 1) for v in value}
    return value


def tracebacks_with_shorten_values(
    logger: Any, name: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    """Structlog processor to shorten long or binary values in exception tracebacks.

    Args:
        logger: The logger instance.
        name: The event name.
        event_dict: The event dictionary.

    Returns:
        The event dictionary with shortened exception values if present.
    """

    traceback_obj = structlog.processors.dict_tracebacks(logger, name, event_dict)
    if "exception" in traceback_obj:
        traceback_obj["exception"] = truncate_str_in_traceback_obj(traceback_obj["exception"])
    return traceback_obj


def replace_bytes_in_event_dict(
    logger: Any, name: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    """Recursively replaces all bytes objects in the event_dict with a placeholder string.
    The placeholder includes the first 8 bytes (header) in hex, and the total length.
    Returns a new dict, always a MutableMapping[str, Any].
    """

    def _replace(obj):
        if isinstance(obj, bytes):
            header = obj[:8].hex()
            return f"<binary data, header=0x{header}, length={len(obj)} bytes>"
        if isinstance(obj, dict):
            return {k: _replace(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_replace(v) for v in obj]
        if isinstance(obj, tuple):
            return tuple(_replace(v) for v in obj)
        if isinstance(obj, set):
            return {_replace(v) for v in obj}
        return obj

    return {k: _replace(v) for k, v in event_dict.items()}


def create_formatter(is_dev: bool = False) -> structlog.stdlib.ProcessorFormatter:
    """Creates a formatter for structured logging.

    Args:
        is_dev (bool): If True, use a human-readable console renderer; otherwise, use a JSON renderer.

    Returns:
        structlog.stdlib.ProcessorFormatter: Configured formatter for structlog integration.
    """

    timestamper = structlog.processors.TimeStamper(fmt="iso")
    shared_processors = [merge_contextvars, structlog.stdlib.add_log_level, timestamper, replace_bytes_in_event_dict]

    structlog.configure(
        processors=[*shared_processors, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    console_renderer = [structlog.dev.ConsoleRenderer()]
    json_renderer = [
        tracebacks_with_shorten_values,
        structlog.processors.EventRenamer("message"),
        SemanticSorter(order=["timestamp", "level", "message"]),
        pydantic_models_to_json,
        structlog.processors.JSONRenderer(),
    ]
    renderer = console_renderer if is_dev else json_renderer

    formatter = structlog.stdlib.ProcessorFormatter(
        # These run ONLY on `logging` entries that do NOT originate within structlog.
        foreign_pre_chain=shared_processors,
        # These run on ALL entries after the pre_chain is done.
        processors=[
            # Remove _record & _from_structlog.
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            *renderer,
        ],
    )

    return formatter


def create_handler(is_dev: bool = False) -> logging.Handler:
    """Creates a handler for structured logging.

    Args:
        is_dev (bool): If True, use a human-readable console renderer; otherwise, use a JSON renderer.

    Returns:
        logging.Handler: Configured logging handler for structlog integration.
    """

    formatter = create_formatter(is_dev)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    return handler


def intercept_loggers(log_level: int | str = logging.INFO):
    """Intercepts and configures loggers used by external modules.

    Ensures that selected foreign loggers and their sub-loggers use the same handler and log level,
    enabling consistent structured logging throughout the application.

    Args:
        log_level (int | str): Minimum logging level to apply.

    Returns:
        None
    """

    logger_names = set()
    logger_names.update(logging.root.manager.loggerDict.keys())
    logger_names.update(logging.Logger.manager.loggerDict.keys())
    logger_names.update(LOGGERS_TO_INTERCEPT)

    handler = create_handler()

    for logger_name in logger_names:
        foreign_logger = logging.getLogger(logger_name)

        # we want to remove handlers and add ours
        # only if there are some handlers already
        # OR logger is on a list of loggers to intercept
        if foreign_logger.handlers or (logger_name in LOGGERS_TO_INTERCEPT):
            foreign_logger.handlers = []
            foreign_logger.addHandler(handler)

        foreign_logger.setLevel(log_level)


def configure_logger(
    log_level: int | str = logging.INFO,
    is_dev: bool = False,
    log_file: str | Path | None = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB default
    backup_count: int = 5,
    use_rotation: bool = True,
) -> None:
    """Configures structured logger, logs JSON in production and in colors in development.
    Configuration should be done once per application

    Args:
        log_level: minimum logging level, ignores everything below
        is_dev: if True, logs will be colored
        log_file: optional path to log file. If provided, logs will be written to both console and file.
                  The file will always use JSON format regardless of is_dev setting.
        max_bytes: maximum size of a single log file before rotation (default: 10MB).
                   Only used when use_rotation=True.
        backup_count: number of backup files to keep during rotation (default: 5).
                      Only used when use_rotation=True.
        use_rotation: if True, use RotatingFileHandler; if False, use regular FileHandler with append mode.

    Returns:
        None
    """

    # Clear existing handlers to prevent duplicate logs.
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Use OUR `ProcessorFormatter` to format all `logging` entries.
    # Add console handler
    console_handler = create_handler(is_dev)
    root_logger.addHandler(console_handler)
    root_logger.setLevel(log_level)

    # Add file handler if log_file is specified
    if log_file:
        try:
            log_file = Path(log_file)
            # Ensure parent directory exists
            log_file.parent.mkdir(parents=True, exist_ok=True)

            # File logs always use JSON format for consistency
            file_formatter = create_formatter(is_dev=False)

            # Use rotation or simple append based on configuration
            if use_rotation:
                file_handler = RotatingFileHandler(
                    log_file,
                    mode="a",
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    encoding="utf-8",
                )
            else:
                file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")

            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(log_level)
            root_logger.addHandler(file_handler)

        except (OSError, PermissionError) as e:
            # Log the error to stderr but don't crash the application
            import sys

            print(f"Warning: Failed to configure file logging to {log_file}: {e}", file=sys.stderr)

    if not is_dev:
        intercept_loggers(log_level)
