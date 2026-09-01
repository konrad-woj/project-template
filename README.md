# Project Template

Template repo for Python AI/ML microservices and POCs (FastAPI + `uv` monorepo). Use it to bootstrap a new project, then delete this section and fill in `README_TEMPLATE.md` (renamed to `README.md`) with the project's own docs.

## 📚 Documentation

See [openwiki/index.md](openwiki/index.md) for the full repository wiki (architecture, design, operations, and per-package docs), kept up to date by OpenWiki. See `CLAUDE.md` for the full engineering conventions this template enforces.

## Bootstrapping a new project from this template

1. Copy/clone this repo into the new project directory.
2. Replace the root README: `mv README_TEMPLATE.md README.md`, then fill in TL;DR, TOC, Installation, Usage, etc.
3. For each new service, copy `packages/pyproject.toml.example` to `packages/{package_name}/pyproject.toml` and populate `name`, `description`, and dependencies. Follow the `Code Structure` layout in `CLAUDE.md` for where `src/`, `tests/`, `docs/`, `evals/`, `notebooks/`, and `scripts/` go inside each package. Also copy `packages/tach.toml.example` to `packages/{package_name}/tach.toml`, and run `uvx tach sync --add` from the package once it has real modules to keep boundaries in sync.
4. Before starting a new feature or service, copy `docs/DESIGN_DOC_TEMPLATE.md` to `{FEATURE_NAME}.md` at the repo root and fill it in (see the `/designdoc-creator` skill).
5. Copy `.env.example` to `.env` at the repo root, and to a `.env` inside each package that needs its own keys. Populate required keys (e.g. `GEMINI_API_KEY`, `OPENAI_API_KEY`) and never commit populated `.env` files.
6. Cross-package utilities and Pydantic API models go in `packages/data-utils/` and `packages/data-models/` respectively — check there before adding something locally to a package.
7. Sync the Claude Code skills you need from [konrad-woj/skillset](https://github.com/konrad-woj/skillset) into `.claude/skills/` — don't copy-paste skill content into this repo.
8. Run `npx openwiki --init` once to generate `openwiki/`, and review the output before committing it.

## Reusable Dependencies

This template pulls shared tooling from sibling repos instead of duplicating it locally:

- **Logger** — [konrad-woj/logger](https://github.com/konrad-woj/logger): structured logging package. Each package depends on it via `[tool.uv.sources]` in its `pyproject.toml` (see `packages/pyproject.toml.example`); `packages/logger/` in this repo is a reference copy only, never fork/redefine it locally.
- **Skills** — [konrad-woj/skillset](https://github.com/konrad-woj/skillset): shared Claude Code skills used across projects. Sync the skills you need into `.claude/skills/` manually rather than copy-pasting skill content into this repo; if a task needs a skill that doesn't exist yet, add it to the skillset repo instead of defining it locally here.
- **Tach** — [gauge-sh/tach](https://github.com/gauge-sh/tach): enforces module boundaries within a package. Every package ships a `tach.toml` (see `packages/tach.toml.example`) and a `tach` taskipy task; `uv run task precommits` runs `tach check` alongside ruff and pyright.

## Repo-wide scripts

- `sh run_on_each.sh "uv sync"` runs a command inside every `packages/*/` directory, continuing past failures. Pass `-b` to stop at the first failure instead: `sh run_on_each.sh -b "uv run task precommits"`.

## OpenWiki

Generates and maintains the repo wiki under `openwiki/` (see `openwiki/quickstart.md` and `openwiki/INSTRUCTIONS.md` for scope):

```
npx openwiki --init                  # one-time setup
npx openwiki                         # interactive doc chat over the current repo
npx openwiki code --update --print   # manual local doc refresh
```

Defaults to Gemini (`GEMINI_API_KEY`, `OPENWIKI_PROVIDER`/`OPENWIKI_MODEL_ID` in `.env`); CI (`.github/workflows/openwiki-update.yml`) runs the same way since GitHub-hosted runners can't reach a local model server. For fully local/offline use, uncomment the OpenAI-compatible block in `.env.example` instead. Don't hand-edit the generated pages — update source code/docs and let OpenWiki regenerate.

## Running Claude Code in a sandbox

This template ships a reference `sandbox-exec` profile, `claude-sandbox.sb`, that restricts Claude Code's file access on macOS: it denies read/write on credential and secret locations (SSH keys, cloud CLI configs, `.env` files, keychains, shell history, etc.) while leaving the rest of the filesystem at its default permissions.

To use it:

1. Copy the profile out of the repo to a stable path, e.g. `cp claude-sandbox.sb ~/claude-sandbox.sb`, and edit the hardcoded home-directory paths inside it to match your username.
2. Add an alias to your shell rc file (`~/.zshrc` or `~/.bashrc`):
   ```
   alias claude="sandbox-exec -f ~/claude-sandbox.sb claude"
   ```
3. Reload the shell: `source ~/.zshrc`.
4. Review and extend the deny lists in `claude-sandbox.sb` as you add new credential locations (password managers, cloud CLIs, etc.) to your machine.

`~/.gitconfig` is read-allowed (git reads it on every invocation) but write-denied, so git works normally under the sandboxed alias while a run can't tamper with it (e.g. planting a malicious `credential.helper` or `url.insteadOf`). A profile change only takes effect in a new shell/`claude` session — reload after editing `claude-sandbox.sb`.

