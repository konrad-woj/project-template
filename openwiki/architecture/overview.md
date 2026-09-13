---
type: Architecture
title: Architecture Overview
description: An overview of the monorepo's architecture, including inter-package relationships and shared dependencies.
tags: [architecture, monorepo, dependencies]
---
# Architecture Overview

This monorepo is designed to host multiple Python packages, enabling modular development, code reusability, and consistent tooling. The architecture emphasizes clear separation of concerns, with common functionalities encapsulated in shared packages.

## Monorepo Structure and Principles

*   **Modular Design**: Each package is an independent unit with its own `pyproject.toml` for dependency management.
*   **Shared Dependencies**: Core utilities and data models are centralized to avoid duplication and ensure consistency.
*   **Tooling**: `uv` manages Python dependencies efficiently, and `taskipy` standardizes command execution.

## Inter-Package Relationships

Packages within the monorepo often depend on each other or on external shared components:

*   **`logger`**: Not a package in this repo — every package that logs depends on [konrad-woj/logger](https://github.com/konrad-woj/logger) directly via a `[tool.uv.sources]` Git entry in its `pyproject.toml`. This ensures all projects use the same, centrally maintained logging solution.
    *   **Source of Truth**: `CLAUDE.md` outlines this approach for shared dependencies.
*   **`example-library` / `example-service`**: Reference pair showing both dependency styles: `example-service` (`/packages/example-service`) is a runnable FastAPI service that depends on `example-library` (`/packages/example-library`) via a local `[tool.uv.sources]` path entry, and on `logger` via the Git entry above. Both call `get_logger(__name__)`; only `example-service`, the entrypoint, calls `configure_logging()`.

### Diagram: Simplified Package Dependencies

```mermaid
graph TD
    A[Application/Service Package] --> C[logger]
    C --> E[structlog]
    subgraph Shared External Dependencies
        C -- from [tool.uv.sources] --> F[Canonical Logger Repo]
    end
    G[example-service] -- from [tool.uv.sources] path --> H[example-library]
```

## `pyproject.toml` and `uv` Configuration

Each package's `pyproject.toml` defines its specific dependencies. The monorepo setup, particularly the `[tool.uv.sources]` section (as mentioned in `CLAUDE.md`), allows for referencing shared external repositories, enabling controlled consumption of common internal libraries like the canonical `logger`.

**Source**: `CLAUDE.md` for general monorepo conventions and shared dependency strategy.
