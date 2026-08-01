---
type: Overview
title: Quickstart Guide
description: A quickstart guide to the monorepo, its structure, and key components.
---
# Quickstart Guide

This repository is a Python monorepo template managed with `uv` for dependency management and `taskipy` for task automation. It is structured to facilitate the development of multiple Python packages within a single repository, promoting code sharing and consistent tooling.

## Key Concepts

*   **Monorepo**: Houses multiple, distinct Python packages.
*   **`uv`**: Used for fast dependency resolution and package management. Each package manages its own dependencies and virtual environment.
*   **`taskipy`**: Automates common development tasks such as running tests and pre-commit hooks (e.g., `uv run task precommits`).

## Repository Structure

The repository follows a standard structure:

*   `/packages/`: Contains individual Python packages (e.g., `data-models`, `logger`).
*   `/docs/`: Root-level documentation and design templates.
*   `/openwiki/`: OpenWiki-generated documentation (this wiki).
*   `/run_on_each.sh`: A utility script to execute commands across all packages.

## Navigation

Explore the following sections to understand the repository in more detail:

*   [Packages](/openwiki/packages/index.md): Details about the individual Python packages in the monorepo.
*   [Architecture](/openwiki/architecture/overview.md): High-level architectural overview and inter-package relationships.
*   [Operations](/openwiki/operations/build-run.md): How to build, run, and manage packages.
*   [Design Documents](/openwiki/design/overview.md): Summaries of key design decisions.

## Backlog

*   Further detail on `taskipy` usage and custom tasks.
