---
name: project-bootstrapper
description: >-
  Turn a clone of the project-template repo into a real, named project, or add a
  new package to one that already exists. Handles project identity, package
  scaffolding from the pyproject/tach examples, .env and sandbox setup, skill
  syncing, Dockerfiles, OpenWiki regeneration, and a full verification pass.
  Triggers on "bootstrap this template", "set up a new project", "start a new
  project from the template", "scaffold a new package", "add a package",
  "initialise the repo", "new service", "new microservice".
---

# Project Bootstrapper

Bootstraps a clone of the `project-template` monorepo into a working project,
and scaffolds new packages inside an already-bootstrapped one. Everything in the
template README's "Bootstrapping a new project" section, plus the identity,
hygiene, and verification work that section leaves to the reader.

## When to use this

| Situation | Mode |
| --------- | ---- |
| Fresh clone of `project-template`, no real packages yet | **Bootstrap** |
| Named project already, needs another service package | **Add package** |
| Neither — repo is unrelated to the template | Don't use this skill |

Detect the mode before doing anything: the repo is still un-bootstrapped if
`README_TEMPLATE.md` exists, `package.json` still has `"name":
"project-template"`, or `packages/` contains only `data-models`, `data-utils`
and `logger`.

## Phase 0 — Preflight and inputs

Never start editing before this phase completes.

1. **Check the toolchain.** `uv --version`, `node --version`, `git --version`,
   `npx --version`. Python must be 3.13 (`uv python list`). If anything is
   missing, stop and say exactly what to install — do not silently degrade.
2. **Check the working tree is clean.** `git status --short`. If it is dirty,
   ask whether to proceed or stash; bootstrapping rewrites many files and a
   dirty tree makes the result unreviewable.
3. **Read `CLAUDE.md`** in the repo. It is the source of truth for conventions
   and overrides anything in this skill that conflicts with it.
4. **Collect inputs by asking the user**, in one round, not one at a time:
   - Project name (kebab-case; becomes `package.json` `"name"` and the README
     title).
   - One-line project description.
   - Package(s) to create: for each, a kebab-case directory name, the
     importable module name (defaults to the directory name with underscores),
     and whether it is a FastAPI service, a worker, or a library.
   - New git remote URL, and whether to reset history to a single initial
     commit.
   - Which skills to sync from `skillset` (default: whatever `sh sync_skills.sh`
     pulls with no arguments).
   - Whether to regenerate OpenWiki now (needs `GEMINI_API_KEY`).
5. **Present a plan and get approval** before writing anything. List every file
   that will be created, renamed, or deleted. In "Add package" mode this is
   short; in "Bootstrap" mode it is not.

## Phase 1 — Project identity

1. `git mv README_TEMPLATE.md README.md` (overwriting the template README), then
   fill in the title, TL;DR, description, and the packages table from Phase 0's
   inputs. Leave `{placeholder}` markers only where the user has not decided
   yet, and list them in the final report.
2. Update `package.json` `"name"` to the project name.
3. Replace template descriptions in `packages/*/pyproject.toml` that still refer
   to the template rather than the project.
4. If the user asked for a history reset:
   `rm -rf .git && git init && git branch -M main`, then set the new remote.
   Otherwise just `git remote set-url origin <new-url>` and confirm the old
   template remote is gone (`git remote -v`).
5. Delete `openwiki/.last-update.json` — it pins the *template's* `gitHead` and
   would otherwise be carried into the new project as false provenance.

## Phase 2 — Package scaffolding

For each package from Phase 0, from `packages/`:

1. `mkdir -p {package_name}/src/{package_module} {package_name}/tests/unit
   {package_name}/tests/integration {package_name}/docs`. Add `notebooks/`,
   `evals/`, and `scripts/` only if the user asked for them — empty directories
   that nobody uses are noise. `evals/` and `scripts/` need `__init__.py`;
   `notebooks/` does not.
2. `cp pyproject.toml.example {package_name}/pyproject.toml` and populate
   `name`, `description`, and dependencies. Drop FastAPI/uvicorn from the
   dependency list for a library package. Uncomment and rename the `app` task to
   the real module for a service.
3. `cp tach.toml.example {package_name}/tach.toml`.
4. `cp logger/.python-version {package_name}/.python-version` (or write
   `3.13`).
5. Write `src/{package_module}/__init__.py` and, for a service, a `main.py`
   entrypoint that calls `configure_logger("INFO")` exactly once — per
   `CLAUDE.md`, configuration happens in the executable entrypoint and nowhere
   else.
6. Write a short `README.md` for the package: what it is, its public surface,
   and the three taskipy commands. Do not restate the code.
7. `cd {package_name} && uv sync --all-groups && uv run tach sync --add`.

Never fork the `logger` package into the new one. It comes from the shared git
repo via `[tool.uv.sources]`, already present in the example pyproject.

Check `packages/data-utils/` and `packages/data-models/` before writing any
helper or schema — anything reused across packages belongs there, not in a
service package.

## Phase 3 — Environment and secrets

1. `cp .env.example .env` at the repo root, and into each package that needs its
   own keys.
2. **Never read, print, or echo the contents of a populated `.env`.** List which
   keys are unset by name only, and tell the user to populate them.
3. Confirm `.env` is ignored: `git check-ignore .env` must succeed. If it does
   not, fix `.gitignore` before continuing.
4. If the user is on macOS and wants the sandbox profile:
   `sed "s|__HOME__|$HOME|g" claude-sandbox.sb > ~/claude-sandbox.sb` and print
   the alias line for their shell rc. Do not edit their rc file without asking.

## Phase 4 — Skills, Docker, and docs

1. `sh sync_skills.sh [skill ...]`. If it fails (no network, no repo access),
   report it and continue — it is not fatal to the bootstrap.
2. For each deployable service: `cp Dockerfile.example
   Dockerfile.{package_name}` and replace every `{package_name}` and
   `{package_module}` placeholder. Verify none remain:
   `grep -n "{package" Dockerfile.*` must return nothing outside
   `Dockerfile.example`.
3. If the user named a first feature, `cp docs/DESIGN_DOC_TEMPLATE.md
   {FEATURE_NAME}.md` at the repo root and pre-fill the title, Background, and
   Revision History rows. Do not invent Goals — hand it back for the user to
   fill, or hand off to `/designdoc-creator`.
4. If OpenWiki was requested and `GEMINI_API_KEY` is set: `npx openwiki --init`,
   then review the generated pages before staging them. If the key is missing,
   skip and say so.

## Phase 5 — Verification

This phase is the point of the skill. Do not skip it, and do not report success
without it.

```bash
sh run_on_each.sh -b "uv sync --all-groups --locked"
sh run_on_each.sh -b "uv run task ci"
npx --yes markdownlint-cli@0.49.1 '**/*.md' --ignore node_modules --ignore openwiki --ignore '**/.venv' --config .markdownlint.json
```

Then check the things a green gate does not catch:

- **Wheels are not empty.** For every package with a `[build-system]`, run
  `uv build` and list the wheel contents. A `[tool.hatch.build.targets.wheel]
  packages` entry that does not match the real `src/` path produces an empty
  wheel with no error. Delete `dist/` afterwards.
- **No leaked identity.** Grep the tree for the previous project's name, for
  absolute home paths (`/Users/`, `/home/`), and for `{package` placeholders.
- **No secrets staged.** `git status --short` must not list any `.env`. Run
  `git diff --cached` and scan for anything key-shaped before committing.
- **CI matrix covers the new package.** The workflow discovers packages from
  `packages/*/pyproject.toml`, so a package missing its `pyproject.toml` is
  silently untested. Confirm the discovery command lists every package.

Fix what you can, then re-run the gate. Report anything you could not fix rather
than lowering the bar — never delete a failing test or loosen a lint rule to get
green.

## Phase 6 — Commit and report

Commit with a `chore:` or `feat:` message describing the project or package, per
`CLAUDE.md`'s commit conventions: no assistant or employer names, no
`Co-Authored-By` or `Generated with` trailers, and branch names prefixed
`feature/`, `fix/`, or `chore/`.

Close with a short report:

- Packages created and their module names.
- Env keys still unpopulated (names only).
- Anything skipped and why (no network, no API key, user declined).
- Remaining `{placeholder}` markers in `README.md` and the design doc.
- The verification result, verbatim if anything failed.

## Guardrails

- **Ask before destroying.** `rm -rf .git`, overwriting a populated `.env`, and
  deleting an existing package all need explicit confirmation, every time.
- **Idempotent by default.** Re-running on a bootstrapped repo must detect that
  and switch to "Add package" mode rather than re-templating the README.
- **Don't invent structure.** Create only the directories the user asked for.
  The layout in `CLAUDE.md` is a permitted set, not a required one.
- **Don't add skills locally.** If a needed skill is missing, add it to the
  `skillset` repo. `.claude/skills/` is vendored and gitignored; anything
  written there is lost on the next sync.
