# Project Template

> TL;DR:

## TOC


## 📚 Documentation

See [openwiki/index.md](openwiki/index.md) for the full repository wiki (architecture, design, operations, and per-package docs), kept up to date by OpenWiki.

## Reusable Dependencies

This template pulls shared tooling from sibling repos instead of duplicating it locally:

- **Logger** — [konrad-woj/logger](https://github.com/konrad-woj/logger): structured logging package. Each package depends on it via `[tool.uv.sources]` in its `pyproject.toml` (see `packages/pyproject.toml.example`); `packages/logger/` in this repo is a reference copy only, never fork/redefine it locally.
- **Skills** — [konrad-woj/skillset](https://github.com/konrad-woj/skillset): shared Claude Code skills used across projects. Sync the skills you need into `.claude/skills/` manually rather than copy-pasting skill content into this repo; if a task needs a skill that doesn't exist yet, add it to the skillset repo instead of defining it locally here.
- **Tach** — [gauge-sh/tach](https://github.com/gauge-sh/tach): enforces module boundaries within a package. Every package ships a `tach.toml` (see `packages/tach.toml.example`) and a `tach` taskipy task; `uv run task precommits` runs `tach check` alongside ruff and pyright.

## Installation


## Usage
### Getting Started


### Examples


## License


## Contributing

