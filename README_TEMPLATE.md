# {Project Name}

> TL;DR: {one or two sentences — what this service does and for whom.}

## TOC

- [Documentation](#-documentation)
- [Reusable Dependencies](#reusable-dependencies)
- [Installation](#installation)
- [Usage](#usage)
- [Development](#development)
- [License](#license)
- [Contributing](#contributing)

## 📚 Documentation

See [openwiki/index.md](openwiki/index.md) for the full repository wiki
(architecture, design, operations, and per-package docs), kept up to date by
OpenWiki. See [CLAUDE.md](CLAUDE.md) for the engineering conventions this repo
follows.

## Reusable Dependencies

This repo pulls shared tooling from sibling repos instead of duplicating it
locally:

- **Logger** — [konrad-woj/logger](https://github.com/konrad-woj/logger):
  structured logging package. Each package depends on it via `[tool.uv.sources]`
  in its `pyproject.toml`; `packages/logger/` is a reference copy only, never
  fork/redefine it locally.
- **Skills** — [konrad-woj/skillset](https://github.com/konrad-woj/skillset):
  shared Claude Code skills. `sh sync_skills.sh` vendors them into the
  gitignored `.claude/skills/`.
- **Tach** — [gauge-sh/tach](https://github.com/gauge-sh/tach): enforces module
  boundaries within a package. Every package ships a `tach.toml` and a `tach`
  taskipy task.

## Packages

| Package | Purpose |
| ------- | ------- |
| `packages/data-models/` | Cross-package Pydantic models and API contracts |
| `packages/data-utils/` | Cross-package helpers for environment access and JSONL I/O |
| `packages/logger/` | Reference copy of the shared structured-logging package |
| `packages/{package_name}/` | {what this service does} |

## Installation

```bash
cp .env.example .env          # then populate the required keys
sh run_on_each.sh -b "uv sync --all-groups"
sh sync_skills.sh             # optional: vendor shared Claude Code skills
```

## Usage

### Getting Started

```bash
cd packages/{package_name}
uv run task app
```

### Examples

```python
# {minimal end-to-end example against the public API}
```

## Development

Run from inside a package directory (`packages/{package_name}`):

```bash
uv run task test          # unit tests
uv run task precommits    # format + lint + typecheck + boundaries + markdown
uv run task ci            # the same checks, non-mutating - what CI runs
```

Repo-wide: `sh run_on_each.sh -b "uv run task ci"`.

Build a service image from the repo root:

```bash
docker build -f Dockerfile.{package_name} -t {image_name} .
```

## License

{license}

## Contributing

{how to propose changes: design doc first (`docs/DESIGN_DOC_TEMPLATE.md`),
branch naming, review expectations.}
