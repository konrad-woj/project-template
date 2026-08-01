---
type: Python Package
title: Logger Package
description: The `logger` package provides a standardized structured logging utility for all packages within the monorepo.
tags: [logging, structlog, utilities]
---
# Logger Package

The `logger` package (`/packages/logger`) offers a consistent and configurable structured logging solution for all services and applications in the monorepo. It leverages `structlog` to output logs in JSON format, which is ideal for machine readability and integration with log aggregation systems.

## Purpose

*   **Standardized Logging**: Ensures a uniform logging format across the entire monorepo.
*   **Structured Output**: Generates JSON-formatted logs for easier parsing, searching, and analysis.
*   **Developer Experience**: Supports a developer mode with enhanced readability using tools like `rich` or `better-exceptions`.

## Usage

### Initial Configuration

To configure the logger, call `configure_logger` once at the application's entry point, typically in `main.py`. The `is_dev` flag enables developer-friendly output.

**Source**: `/packages/logger/src/logger/logger.py` (via `__init__.py`)

```python
# main.py
from logger import configure_logger

if __file__ == "__main__":
    configure_logger(is_dev=True)
```

### Direct Logging

After initial configuration, obtain a logger instance using `structlog.get_logger()` and use it for structured logging.

```python
# some_part_of_app.py
import structlog

logger: structlog.stdlib.BoundLogger = structlog.get_logger()
logger.info("User event", user_id=123, action="login")
```

## Key Modules

*   `/packages/logger/src/logger/logger.py`: Contains the core logging configuration and utilities, including `configure_logger`.
*   `/packages/logger/src/logger/timer.py`: Provides synchronous timing utilities for performance measurement.
*   `/packages/logger/src/logger/async_timer.py`: Provides asynchronous timing utilities.

## Shared Dependency

It is important to note that the `logger` package is intended as a shared dependency. The real dependency comes from a shared Git repository via `[tool.uv.sources]`, and it should not be forked or redefined per project locally. This local copy serves as a reference.
