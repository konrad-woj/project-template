# Project Template

Template repo for Python AI/ML microservices and POCs (FastAPI + `uv` monorepo).
See [CLAUDE.md](CLAUDE.md) for the full engineering conventions, and
[openwiki/index.md](openwiki/index.md) for the generated repository wiki.

## Quick start — bootstrap your own repo

1. Copy/clone this repo into your new project directory, point `origin` at
   your new remote, and reset history if this is a fresh project.
2. `mv README_TEMPLATE.md README.md`, then fill in TL;DR, TOC, Installation,
   Usage, etc.
3. Rename the project in `package.json` (`"name"`), and update the
   `description` field in any `packages/*/pyproject.toml` that still says
   "template".
4. Decide what to do with the reference packages:
   - `packages/data-utils/` — keep; generic cross-package helpers.
   - `packages/example-library/` and `packages/example-service/` — copy their
     shape for your first real packages (a plain library and a runnable
     FastAPI service, wired to each other and to the shared `logger`
     dependency), then delete them once you no longer need the example.
5. For each new service: copy `packages/pyproject.toml.example` to
   `packages/{package_name}/pyproject.toml` (fill in `name`, `description`,
   dependencies) and `packages/tach.toml.example` to
   `packages/{package_name}/tach.toml`. Follow the `Code Structure` layout in
   `CLAUDE.md` for where `src/`, `tests/`, `docs/`, `evals/`, `notebooks/`, and
   `scripts/` go. Run `uv run tach sync --add` once the package has real
   modules.
6. Copy `Dockerfile.example` to `Dockerfile.{package_name}` for each
   deployable service and replace the `{package_name}` / `{package_module}`
   placeholders.
7. Copy `.env.example` to `.env` at the repo root (and to a `.env` inside any
   package that needs its own keys), and populate the required keys. Never
   commit a populated `.env`.
8. Run `sh sync_skills.sh` to vendor the Claude Code skills you need from
   [konrad-woj/skillset](https://github.com/konrad-woj/skillset) into the
   gitignored `.claude/skills/`.
9. Run `npx openwiki --init` to regenerate `openwiki/` for the new project,
   and review the output before committing it.
10. Before starting a new feature, copy `docs/DESIGN_DOC_TEMPLATE.md` to
    `{FEATURE_NAME}.md` at the repo root (see the `/designdoc-creator` skill).
11. Verify the whole repo before the first commit:

    ```bash
    sh run_on_each.sh -b "uv sync --all-groups"
    sh run_on_each.sh -b "uv run task ci"
    ```

## What's already set up

| Area | Details |
| --- | --- |
| Packages | `packages/data-utils/` (cross-package helpers), `packages/example-library/` + `packages/example-service/` (reference library/service pair) |
| Logger | Every package that logs depends on [konrad-woj/logger](https://github.com/konrad-woj/logger) via `[tool.uv.sources]` — see `packages/example-service` for a working `configure_logging()` / `get_logger(__name__)` example |
| Module boundaries | [gauge-sh/tach](https://github.com/gauge-sh/tach) — every package ships a `tach.toml`, checked by `uv run task tach` / `precommits` / `ci` |
| Quality gate | `uv run task test` / `precommits` / `ci` inside any package directory; `.github/workflows/ci.yml` auto-discovers every package |
| Repo-wide scripts | `sh run_on_each.sh [-b] "<cmd>"` runs `<cmd>` in every `packages/*/`; `sh sync_skills.sh [skill ...]` vendors shared skills |
| OpenWiki | `npx openwiki --init` / `npx openwiki` / `npx openwiki code --update --print` — see `openwiki/quickstart.md`; don't hand-edit generated pages |
| Claude Code config | `.claude/settings.json` (committed, shared permissions) vs. `.claude/settings.local.json` / `.claude/skills/` (gitignored) |
| Sandbox profile | `claude-sandbox.sb` — reference `sandbox-exec` profile denying access to credential/secret locations; setup instructions are in the file's own header comment |
| Over-engineering audits | [dietrichgebert/ponytail](https://github.com/dietrichgebert/ponytail) Claude Code plugin — `/ponytail-review` on a diff, `/ponytail-audit` on the whole repo |
