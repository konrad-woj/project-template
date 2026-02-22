import json
import logging
from pathlib import Path

import pytest
from structlog import BoundLogger, get_logger
from structlog.testing import capture_logs

from logger import configure_logger
from logger.logger import replace_bytes_in_event_dict


def test_configure_logger():
    configure_logger()
    log: BoundLogger = get_logger()
    with capture_logs() as cap_logs:
        log.info("Test - info", x=5, bar="foo")

        try:
            raise ValueError("Bad value")
        except ValueError:
            log.exception("Ooops")

        assert "x" in cap_logs[0]
        assert cap_logs[0]["x"] == 5
        assert "bar" in cap_logs[0]
        assert cap_logs[0]["bar"] == "foo"

        assert "log_level" in cap_logs[1]
        assert cap_logs[1]["log_level"] == "error"
        assert "exc_info" in cap_logs[1]


def test_bytes_are_replaced_in_logs():
    test_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    event_dict = {"data": test_bytes}
    expected_header = test_bytes[:8].hex()

    processed = replace_bytes_in_event_dict(logger=None, name="test", event_dict=event_dict)

    assert "data" in processed
    assert isinstance(processed["data"], str)
    assert processed["data"].startswith(f"<binary data, header=0x{expected_header}, length=")
    assert processed["data"].endswith(" bytes>")
    assert str(len(test_bytes)) in processed["data"]


def test_configure_logger_with_file_logging(tmp_path: Path):
    """Test that file logging is created when log_file parameter is provided."""
    log_file = tmp_path / "test_logs" / "test.log"

    # Configure logger with file logging (rotation disabled for simpler test)
    configure_logger(log_level=logging.INFO, is_dev=True, log_file=log_file, use_rotation=False)

    # Get logger and write some logs (outside capture_logs to let them reach file handler)
    log: BoundLogger = get_logger()
    log.info("Test message", test_key="test_value")

    # Flush handlers to ensure logs are written
    for handler in logging.getLogger().handlers:
        handler.flush()

    # Verify log file was created
    assert log_file.exists(), "Log file should be created"

    # Verify log file contains data
    log_content = log_file.read_text()
    assert len(log_content) > 0, "Log file should not be empty"

    # Verify log file uses JSON format
    log_lines = [line for line in log_content.strip().split("\n") if line]
    assert len(log_lines) > 0, "Log file should contain at least one line"

    # Parse first log line as JSON
    first_log = json.loads(log_lines[0])
    assert "test_key" in first_log, "Log should contain test_key"
    assert first_log["test_key"] == "test_value"
    assert "timestamp" in first_log, "Log should contain timestamp"
    assert "level" in first_log, "Log should contain level"
    assert "message" in first_log, "Log should contain message"


def test_configure_logger_creates_parent_directory(tmp_path: Path):
    """Test that parent directories are created automatically."""
    log_file = tmp_path / "nested" / "dir" / "structure" / "test.log"

    # Parent directory should not exist yet
    assert not log_file.parent.exists()

    # Configure logger with file in nested directory (rotation disabled for simpler test)
    configure_logger(log_level=logging.INFO, is_dev=False, log_file=log_file, use_rotation=False)

    # Get logger and write a log
    log: BoundLogger = get_logger()
    log.info("Test message")

    # Flush handlers
    for handler in logging.getLogger().handlers:
        handler.flush()

    # Verify parent directory was created
    assert log_file.parent.exists(), "Parent directories should be created"
    assert log_file.exists(), "Log file should be created"


def test_configure_logger_file_uses_json_format_in_dev_mode(tmp_path: Path):
    """Test that file logs always use JSON format, even in dev mode."""
    log_file = tmp_path / "dev_test.log"

    # Configure logger in dev mode with file logging (rotation disabled for simpler test)
    configure_logger(log_level=logging.INFO, is_dev=True, log_file=log_file, use_rotation=False)

    # Get logger and write logs
    log: BoundLogger = get_logger()
    log.info("Dev mode test", dev_key="dev_value")

    # Flush handlers
    for handler in logging.getLogger().handlers:
        handler.flush()

    # Verify log file uses JSON format (not colored console format)
    log_content = log_file.read_text()
    log_lines = [line for line in log_content.strip().split("\n") if line]

    # Parse as JSON - this will fail if it's colored console format
    first_log = json.loads(log_lines[0])
    assert "dev_key" in first_log
    assert first_log["dev_key"] == "dev_value"

    # Verify it doesn't contain ANSI color codes
    assert "\x1b[" not in log_content, "Log file should not contain ANSI color codes"


def test_configure_logger_without_file_logging():
    """Test backward compatibility - logger works without log_file parameter."""
    # Configure logger without file logging (original behavior)
    configure_logger(log_level=logging.INFO, is_dev=True)

    # Get logger and write logs
    log: BoundLogger = get_logger()
    with capture_logs() as cap_logs:
        log.info("No file test", no_file_key="no_file_value")

        # Verify logs were captured by structlog
        assert len(cap_logs) > 0
        assert cap_logs[0]["no_file_key"] == "no_file_value"

    # Verify no FileHandler was added (only StreamHandler)
    root_logger = logging.getLogger()
    file_handlers = [h for h in root_logger.handlers if isinstance(h, logging.FileHandler)]
    assert len(file_handlers) == 0, "No FileHandler should be added when log_file is None"


def test_configure_logger_both_handlers_receive_logs(tmp_path: Path):
    """Test that both console and file handlers receive the same logs."""
    log_file = tmp_path / "both_handlers.log"

    # Configure logger with file logging (rotation disabled for simpler test)
    configure_logger(log_level=logging.INFO, is_dev=True, log_file=log_file, use_rotation=False)

    # Get logger and write logs
    log: BoundLogger = get_logger()
    log.info("Test both handlers", handler_key="handler_value")
    log.warning("Warning message", warn_key="warn_value")

    # Flush handlers
    for handler in logging.getLogger().handlers:
        handler.flush()

    # Verify logs were written to file
    log_content = log_file.read_text()
    log_lines = [line for line in log_content.strip().split("\n") if line]
    assert len(log_lines) == 2, "File should contain both log entries"

    # Parse log lines
    first_log = json.loads(log_lines[0])
    second_log = json.loads(log_lines[1])

    assert first_log["handler_key"] == "handler_value"
    assert second_log["warn_key"] == "warn_value"


def test_configure_logger_file_respects_log_level(tmp_path: Path):
    """Test that file handler respects the configured log level."""
    log_file = tmp_path / "log_level_test.log"

    # Configure logger with WARNING level (rotation disabled for simpler test)
    configure_logger(log_level=logging.WARNING, is_dev=False, log_file=log_file, use_rotation=False)

    # Get logger and write logs at different levels
    log: BoundLogger = get_logger()
    log.debug("Debug message")
    log.info("Info message")
    log.warning("Warning message")
    log.error("Error message")

    # Flush handlers
    for handler in logging.getLogger().handlers:
        handler.flush()

    # Read file content
    log_content = log_file.read_text()
    log_lines = [line for line in log_content.strip().split("\n") if line]

    # Only WARNING and ERROR should be in the file
    assert len(log_lines) == 2, "File should only contain WARNING and ERROR logs"

    first_log = json.loads(log_lines[0])
    second_log = json.loads(log_lines[1])

    assert first_log["level"] == "warning"
    assert second_log["level"] == "error"


def test_configure_logger_appends_to_existing_file(tmp_path: Path):
    """Test that file logging appends to existing files instead of overwriting."""
    log_file = tmp_path / "append_test.log"

    # Configure logger and write first log
    configure_logger(log_level=logging.INFO, is_dev=False, log_file=log_file, use_rotation=False)
    log: BoundLogger = get_logger()
    log.info("First message")

    # Flush handlers
    for handler in logging.getLogger().handlers:
        handler.flush()

    # Verify first message is in file
    log_content = log_file.read_text()
    assert "First message" in log_content

    # Reconfigure logger (simulating application restart)
    configure_logger(log_level=logging.INFO, is_dev=False, log_file=log_file, use_rotation=False)
    log = get_logger()
    log.info("Second message")

    # Flush handlers
    for handler in logging.getLogger().handlers:
        handler.flush()

    # Verify both messages are in file (append mode)
    log_content = log_file.read_text()
    log_lines = [line for line in log_content.strip().split("\n") if line]
    assert len(log_lines) == 2, "File should contain both log entries"
    assert "First message" in log_content
    assert "Second message" in log_content


def test_configure_logger_uses_rotating_file_handler(tmp_path: Path):
    """Test that RotatingFileHandler is used when use_rotation=True."""
    log_file = tmp_path / "rotating_test.log"

    # Configure logger with rotation
    configure_logger(
        log_level=logging.INFO, is_dev=False, log_file=log_file, max_bytes=100, backup_count=2, use_rotation=True
    )

    # Find the RotatingFileHandler
    from logging.handlers import RotatingFileHandler

    root_logger = logging.getLogger()
    rotating_handlers = [h for h in root_logger.handlers if isinstance(h, RotatingFileHandler)]

    assert len(rotating_handlers) == 1, "Should have exactly one RotatingFileHandler"
    rotating_handler = rotating_handlers[0]

    # Verify configuration
    assert rotating_handler.maxBytes == 100
    assert rotating_handler.backupCount == 2


def test_configure_logger_handles_permission_error(tmp_path: Path):
    """Test that configuration gracefully handles permission errors."""
    import os
    import sys
    from io import StringIO

    # Skip if running as root (root can bypass permission checks)
    if os.geteuid() == 0:
        pytest.skip("Test cannot run as root - root bypasses permission checks")

    # Create a read-only directory (simulate permission denied)
    readonly_dir = tmp_path / "readonly"
    readonly_dir.mkdir()
    log_file = readonly_dir / "test.log"

    # Make directory read-only
    os.chmod(readonly_dir, 0o444)

    # Capture stderr
    old_stderr = sys.stderr
    sys.stderr = captured_stderr = StringIO()

    try:
        # Configure logger - should not crash (rotation disabled for simpler test)
        configure_logger(log_level=logging.INFO, is_dev=False, log_file=log_file, use_rotation=False)

        # Get logger and try to log (should work via console handler)
        log: BoundLogger = get_logger()
        log.info("Test message")

        # Verify warning was printed to stderr
        stderr_content = captured_stderr.getvalue()
        assert "Warning: Failed to configure file logging" in stderr_content or not log_file.exists()

    finally:
        # Restore stderr and permissions
        sys.stderr = old_stderr
        os.chmod(readonly_dir, 0o755)
