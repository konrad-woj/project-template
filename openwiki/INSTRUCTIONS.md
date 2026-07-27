# OpenWiki scope for this repo

This is a Python monorepo template (`packages/{package_name}/`, managed with `uv`
and `taskipy`). Keep the wiki small and focused on what an AI coding agent or new
engineer needs to orient themselves — not a restatement of every file.

## Document

- `packages/*/src/**` — architecture, module responsibilities, how packages relate
  to each other (e.g. how a package depends on `data-models`, `data-utils`, or the
  shared `logger` package via `[tool.uv.sources]`).
- `packages/*/docs/*.md` and each package's `README.md` — treat these as the
  source of truth for that package's intent; summarize and link to them rather than
  duplicating their content.
- Public API surfaces: FastAPI routes/handlers, Pydantic/`data_models` schemas used
  as request/response contracts.
- Root-level design docs (files matching `*_DESIGN*.md` / copied from
  `DESIGN_DOC_TEMPLATE.md`) and the root `README.md`.
- `run_on_each.sh` and `Dockerfile.{package_name}` — how packages are built/run
  together.

## Do not document

- `.venv/`, `node_modules/`, `__pycache__/`, `.ruff_cache/`, `.pyright/` — generated
  environments/caches.
- `packages/*/notebooks/` — exploratory scratch, not meant to be imported.
- `packages/*/evals/` and `packages/*/scripts/` — dev-only tooling, not the
  documented product surface.
- Test fixtures and test bodies themselves (link to `tests/` as a directory, don't
  narrate individual test cases).
- `*.ipynb`, `docs/_build/`.

## Style

Keep pages concise and reference the code (file paths, function/class names) instead
of restating it. Prefer explaining *why* a module exists and how it fits into the
rest of the system over describing *what* each line does — this matches how docs
are written elsewhere in this repo (see CLAUDE.md's docs conventions).
