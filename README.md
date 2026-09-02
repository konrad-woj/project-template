# Project Template

Template repo for Python AI/ML microservices and POCs (FastAPI + `uv` monorepo).
Use it to bootstrap a new project, then delete this file's template sections and
replace it with `README_TEMPLATE.md` filled in for the project itself.

The fastest path is the `/project-bootstrapper` skill, which runs every step
below and verifies the result. The manual steps are documented here so the
template stands on its own.

## 📚 Documentation

See [openwiki/index.md](openwiki/index.md) for the full repository wiki
(architecture, design, operations, and per-package docs), kept up to date by
OpenWiki. See [CLAUDE.md](CLAUDE.md) for the full engineering conventions this
template enforces.

## Bootstrapping a new project from this template

1. Copy/clone this repo into the new project directory, then point `origin` at
   the new remote and reset history if this is a fresh project.
2. Replace the root README: `mv README_TEMPLATE.md README.md`, then fill in
   TL;DR, TOC, Installation, Usage, etc.
3. Rename the project in `package.json` (`"name"`), and update the `description`
   fields in `packages/*/pyproject.toml` that still say "template".
4. For each new service, copy `packages/pyproject.toml.example` to
   `packages/{package_name}/pyproject.toml` and populate `name`, `description`,
   and dependencies. Follow the `Code Structure` layout in `CLAUDE.md` for where
   `src/`, `tests/`, `docs/`, `evals/`, `notebooks/`, and `scripts/` go inside
   each package. Also copy `packages/tach.toml.example` to
   `packages/{package_name}/tach.toml`, and run `uv run tach sync --add` from
   the package once it has real modules to keep boundaries in sync.
5. Before starting a new feature or service, copy `docs/DESIGN_DOC_TEMPLATE.md`
   to `{FEATURE_NAME}.md` at the repo root and fill it in (see the
   `/designdoc-creator` skill).
6. Copy `.env.example` to `.env` at the repo root, and to a `.env` inside each
   package that needs its own keys. Populate required keys (e.g.
   `GEMINI_API_KEY`, `OPENAI_API_KEY`) and never commit populated `.env` files.
7. Cross-package utilities and Pydantic API models go in `packages/data-utils/`
   and `packages/data-models/` respectively — check there before adding
   something locally to a package.
8. Run `sh sync_skills.sh` to vendor the Claude Code skills you need from
   [konrad-woj/skillset](https://github.com/konrad-woj/skillset) into
   `.claude/skills/` (gitignored — never copy-paste skill content into this
   repo).
9. Copy `Dockerfile.example` to `Dockerfile.{package_name}` for each deployable
   service and replace the `{package_name}` / `{package_module}` placeholders.
10. Run `npx openwiki --init` to regenerate `openwiki/` for the new project, and
    review the output before committing it.
11. Verify the whole repo before the first commit:
    `sh run_on_each.sh -b "uv sync --all-groups"` then
    `sh run_on_each.sh -b "uv run task ci"`.

## Reusable Dependencies

This template pulls shared tooling from sibling repos instead of duplicating it
locally:

- **Logger** — [konrad-woj/logger](https://github.com/konrad-woj/logger):
  structured logging package. Each package depends on it via `[tool.uv.sources]`
  in its `pyproject.toml` (see `packages/pyproject.toml.example`);
  `packages/logger/` in this repo is a reference copy only, never fork/redefine
  it locally.
- **Skills** — [konrad-woj/skillset](https://github.com/konrad-woj/skillset):
  shared Claude Code skills used across projects. `sh sync_skills.sh` vendors
  them into the gitignored `.claude/skills/`. If a task needs a skill that
  doesn't exist yet, add it to the skillset repo instead of defining it locally
  here.
- **Tach** — [gauge-sh/tach](https://github.com/gauge-sh/tach): enforces module
  boundaries within a package. Every package ships a `tach.toml` (see
  `packages/tach.toml.example`) and a `tach` taskipy task; `uv run task
  precommits` runs `tach check` alongside ruff, pyright and markdownlint.

## Packages

| Package | Purpose |
| ------- | ------- |
| `packages/data-models/` | Cross-package Pydantic models and API contracts (`BaseSchema`) |
| `packages/data-utils/` | Cross-package helpers for environment access and JSONL I/O |
| `packages/logger/` | Reference copy of the shared structured-logging package |

## Quality gate

Every package exposes the same taskipy tasks, run from inside its directory:

```bash
uv run task test          # unit tests
uv run task precommits    # format + lint + typecheck + boundaries + markdown (mutates files)
uv run task ci            # the same checks, non-mutating - what CI runs
```

`.github/workflows/ci.yml` discovers every directory under `packages/` that has
a `pyproject.toml` and runs `uv run task ci` for it on each pull request and
push to `main`, so adding a package needs no workflow change.

## Repo-wide scripts

- `sh run_on_each.sh "uv sync"` runs a command inside every `packages/*/`
  directory, continuing past failures. Pass `-b` to stop at the first failure:
  `sh run_on_each.sh -b "uv run task ci"`. The script exits non-zero if the
  command failed in any package, so it works as a CI gate.
- `sh sync_skills.sh [skill ...]` vendors shared skills from the skillset repo
  into `.claude/skills/`. Override the source with `SKILLSET_REPO` /
  `SKILLSET_REF`.

## OpenWiki

Generates and maintains the repo wiki under `openwiki/` (see
`openwiki/quickstart.md` and `openwiki/INSTRUCTIONS.md` for scope):

```bash
npx openwiki --init                  # one-time setup
npx openwiki                         # interactive doc chat over the current repo
npx openwiki code --update --print   # manual local doc refresh
```

Defaults to Gemini (`GEMINI_API_KEY`, `OPENWIKI_PROVIDER`/`OPENWIKI_MODEL_ID` in
`.env`); CI (`.github/workflows/openwiki-update.yml`) runs the same way since
GitHub-hosted runners can't reach a local model server. For fully local/offline
use, uncomment the OpenAI-compatible block in `.env.example` instead. Don't
hand-edit the generated pages — update source code/docs and let OpenWiki
regenerate.

## Claude Code configuration

- `.claude/settings.json` holds the shared permission allowlist and is
  committed. `.claude/settings.local.json` (per-machine overrides) and
  `.claude/skills/` (vendored from skillset) are gitignored.
- `CLAUDE.md` is committed and is the source of truth for engineering
  conventions; `CLAUDE.local.md` is for personal overrides and is gitignored.

## Running Claude Code in a sandbox

This template ships a reference `sandbox-exec` profile, `claude-sandbox.sb`,
that restricts Claude Code's file access on macOS: it denies read/write on
credential and secret locations (SSH keys, cloud CLI configs, `.env` files,
keychains, shell history, etc.) while leaving the rest of the filesystem at its
default permissions.

`sandbox-exec` does not expand environment variables, so the profile uses a
`__HOME__` placeholder that must be substituted before use:

```bash
sed "s|__HOME__|$HOME|g" claude-sandbox.sb > ~/claude-sandbox.sb
echo 'alias claude="sandbox-exec -f ~/claude-sandbox.sb claude"' >> ~/.zshrc
source ~/.zshrc
```

Review and extend the deny lists in `claude-sandbox.sb` as you add new
credential locations (password managers, cloud CLIs, etc.) to your machine, then
re-run the `sed`.

`~/.gitconfig` is read-allowed (git reads it on every invocation) but
write-denied, so git works normally under the sandboxed alias while a run can't
tamper with it (e.g. planting a malicious `credential.helper` or
`url.insteadOf`). A profile change only takes effect in a new shell/`claude`
session — reload after editing `claude-sandbox.sb`.
