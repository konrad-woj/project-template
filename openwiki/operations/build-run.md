---
type: Operations Guide
title: Build and Run Operations
description: Guide to building, running, and managing packages within the monorepo, including `run_on_each.sh` and Docker practices.
tags: [operations, build, run, docker, scripting]
---
# Build and Run Operations

This section outlines the primary methods for building, running, and managing the Python packages within this monorepo. Key tools include the `run_on_each.sh` helper script and package-specific Dockerfiles.

## `run_on_each.sh`

The `run_on_each.sh` script (`/run_on_each.sh`) is a utility designed to execute a specified shell command across all subdirectories within the `/packages/` directory. This is particularly useful for applying consistent operations, such as dependency synchronization or pre-commit checks, to all packages simultaneously.

### Usage

```bash
./run_on_each.sh [-b] <command>
```

*   `<command>`: The shell command to execute in each package directory (e.g., `uv sync`, `uv run task precommits`).
*   `-b`: (Optional) If present, the script will break (stop execution) immediately if any command fails in a package. Without this flag, it will continue to the next package, logging the failure.

**Examples**:

*   `./run_on_each.sh "uv sync"` - Synchronizes dependencies for all packages, continuing on error.
*   `./run_on_each.sh -b "uv run task precommits"` - Runs pre-commit tasks for all packages, stopping if any fail.

## Dockerization

Individual packages within the monorepo are intended to be containerized using package-specific Dockerfiles. As per `CLAUDE.md`, these Dockerfiles are typically located at the repository root, rather than within each package directory, because they often depend on multiple packages.

### `Dockerfile.{package_name}` Pattern

The pattern `Dockerfile.{package_name}` indicates a Dockerfile tailored for a specific package (e.g., `Dockerfile.my-app`). These Dockerfiles define the build process and runtime environment for each containerized service or application.

**Build Command Example** (conceptual, as concrete Dockerfiles are not present in this template):

```bash
docker build -f Dockerfile.{package_name} -t {image_name} .
```

This command builds a Docker image, tagging it with `{image_name}`, using the specified `Dockerfile.{package_name}`.

**Source**: `CLAUDE.md` for Dockerfile location and naming conventions.
