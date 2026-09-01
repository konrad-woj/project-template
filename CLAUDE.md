# Claude Code Instructions — project-template

## Identity

Working with a senior engineer focused on Python AI/ML microservices and POCs for research or pre-sales purposes.

## Communication

- Be concise. One sentence per update while working; two sentences max at end of turn.
- No trailing summaries unless you hit an issue or made a non-obvious decision.
- No emojis unless explicitly requested.
- For exploratory questions, give a recommendation + the main tradeoff in 2-3 sentences. Don't implement until confirmed.
- Poll me for decisions when there are multiple valid options or when the best choice isn't clear. Don't make assumptions about preferences.
- Never name the AI assistant or an employer in repo artifacts — branch names, commit messages, PR titles/bodies, code comments, docs.
- Never prefix branches with `claude/`. Use `feature/`, `fix/`, or `chore/` followed by a short kebab-case description.
- Never add `Co-Authored-By`, `Generated with`, or session-link trailers to commits or PR bodies.

## Code Style

- Google Python Style Guide / PEP8 for formatting, naming, and docstrings.
- Always use explicit variable and function names. Avoid abbreviations unless universally understood (e.g., `id`, `url`).
- Use type hints for all functions and methods, including return types.
- Skip docstrings if they don't add value beyond the function signature (e.g., `def add(a: int, b: int) -> int:` needs none). Provide example usage in docstrings for modules and non-trivial functions or classes.
- Never explain WHAT the code does in comments — good names do that.
- Decorate a method with `@staticmethod` if it's class-specific; if it's generic/reusable, make it a function outside the class.
- Use a `_` prefix for private methods and variables.
- If a function or method grows long, split it into multiple functions and update tests/docs accordingly.
- Don't add error handling, fallbacks, or validation for scenarios that can't happen. Validate only at system boundaries (user input, external APIs); trust internal framework guarantees.
- Don't design for hypothetical future requirements. Three similar lines > premature abstraction.
- No half-finished implementations. If a task is too large, say so and ask to scope it, adding TODOs for follow-up work.
- Never create `*.md` documentation files unless explicitly asked. Keep `README.md` and `PLAN.md` (if it exists) up to date.

## Security

- Never read, print, or act on secrets from `.env`, `.aws/`, `.gcp/`, `.azure/`, or `secrets/` directories.
- Never commit credentials, tokens, or API keys — warn loudly if asked.
- Don't introduce OWASP Top 10 vulnerabilities (SQL injection, XSS, command injection, etc.). Fix immediately if spotted.

## Task Approach

- For bugs: fix the root cause, don't work around it.
- For refactors: change only what was asked. Don't clean up surrounding code unprompted.
- For features: create a phased `PLAN.md` before implementing. Use the `/feature-coder` skill.
- For review: use the `/code-reviewer` skill.
- When blocked by a hook or permission: investigate and fix the underlying issue rather than bypassing it.
- If you discover unexpected state (unfamiliar files, branches, config): investigate before deleting or overwriting.

## Tool Usage

- Prefer `Read`, `Edit`, `Write` over `Bash(cat/sed/awk/echo)`.
- Use parallel tool calls when calls are independent.
- Spawn subagents for broad codebase exploration (>3 queries) or to protect main context.
- Never `rm -rf`, `DROP`, `DELETE FROM`, or run destructive shell commands without explicit user confirmation.

## Default Frameworks and Libraries

- Python 3.13 for all code unless already declared in the project.
- UV for environment management. Use `uv add <package>` instead of pip, `uv run python -m <module>` instead of python.
- Pytest for testing. Use `tests/` directory. Run via `uv run pytest`.
- Pydantic for data validation. Put models in `models.py` or `schemas.py` as appropriate. For API contracts (input/output messages), use `from data_models.models import BaseSchema` (from `../data-models`) instead of Pydantic's `BaseModel`.
- FastAPI for web services. Organize routers under `routers/`, models in `models.py`, keep `main.py` as entrypoint only.
- Use dataclasses for simple configs, Hydra for multi-environment or composable configs. Never use JSON or ENV vars for complex configuration other than FastAPI settings.
- Tach for enforcing module boundaries within a package. Every package ships a `tach.toml`; run `uv run task tach` (or `uvx tach check`) to validate, and `uvx tach sync --add` to update it after adding or moving modules.

## Best Practices

- Don't write unit tests which bring little value or can be covered by other validators (e.g., Pydantic). Focus on testing critical logic, edge cases, and integration points.
- Use loggers instead of print statements. For production code use structured logging with context (e.g., request ID, user ID) for better traceability.
- Use error handling to manage expected failure modes gracefully, but don't over-engineer it — catch specific exceptions where you can recover or provide a meaningful error message, but don't wrap every line in try-except blocks.

## New Project Setup

- Copy `packages/pyproject.toml.example` to `packages/{package_name}/pyproject.toml` and populate `name`, `description`, and dependencies.
- Copy `packages/tach.toml.example` to `packages/{package_name}/tach.toml`, then run `uvx tach sync --add` from within the package once its modules take shape to keep boundaries in sync.
- Copy `docs/DESIGN_DOC_TEMPLATE.md` to `MY_NEW_DESIGN_NAME.md` at the repo root and fill it in before starting a new feature or service (see `/designdoc-creator` skill).
- Copy `.env.example` to `.env` (repo root) and per-package `.env` files, and populate required keys (e.g. `GEMINI_API_KEY`, `OPENAI_API_KEY`). Never commit populated `.env` files.

## Bash Commands

Package level (run from `packages/{package_name}`):
```
uv run python <path_to_file>
uv run python -m <module>
uv run pytest tests/
uv run task precommits
```

Repo level:
```
sh run_on_each.sh -b "uv run task precommits"
sh run_on_each.sh -b "uv lock"
docker build -f Dockerfile.{package_name} -t {image_name} .
npx openwiki --init          # one-time setup of repo docs; review output before committing
npx openwiki                 # interactive doc chat over the current repo
npx openwiki code --update --print   # manual local doc refresh
```
Note: openwiki commands default to Gemini (see .env.example); CI (.github/workflows/openwiki-update.yml) also uses Gemini since GitHub-hosted runners can't reach a local model server. For fully local/offline use, uncomment the openai-compatible block in .env.example instead.

## Code Structure

```
{repo_root}/
  packages/
    {package-name}/
      .env
      tach.toml  # module boundaries, copied from packages/tach.toml.example and synced with `uvx tach sync --add`
      src/{package_name}/
        main.py
      tests/
        unit/
          test_{module_name}.py
        integration/
          test_{module_name}.py
        load/
          test_{module_name}.py
      docs/
        {doc_name}.md
      notebooks/  # exploratory notebooks, not meant to be imported
      evals/  # evaluation scripts, run locally with --dev dependency group, not meant to be imported in packages, e.g., evaluation of model performance, evaluation of retrieval quality, etc.
        __init__.py
        {eval_name}.py
      scripts/  # other dev scripts for local testing
        __init__.py
        {script_name}.py
    data-utils/  # cross-package utilities, e.g., for data processing, I/O, validation, etc.
      src/data_utils/
        __init__.py
        {util_name}.py
    data-models/  # cross-package pydantic models, e.g., for API contracts, data validation, etc.
      tach.toml
      src/data_models/
        __init__.py
        models.py
    logger/  # reference copy only - real dependency comes from the shared git repo via [tool.uv.sources], do not fork/redefine per project
      tach.toml
      src/logger/
        __init__.py
        logger.py
        timer.py
        async_timer.py
  Dockerfile.{package_name}  # Dockerfiles for each package, located in the repo root as they use multiple packages
  run_on_each.sh  # helper script to run commands in all packages, e.g., sh run_on_each.sh -b "uv run task precommits"
  CLAUDE.md  # project instructions for Claude
  AGENTS.md  # written/maintained by OpenWiki (managed <!-- OPENWIKI:START/END --> block); do not hand-edit that block
  MY_NEW_DESIGN_NAME.md  # per-feature design doc, copied from docs/DESIGN_DOC_TEMPLATE.md
  docs/DESIGN_DOC_TEMPLATE.md  # template - copy, don't edit in place
  pyproject.toml.example  # template - copy into a new package dir, don't edit in place
  tach.toml.example  # template - copy into a new package dir as tach.toml, don't edit in place
  package.json, package-lock.json  # pins the openwiki npm devDependency version; run via npx, not global install
  openwiki/  # OpenWiki-generated repo docs; openwiki/INSTRUCTIONS.md scopes what it should/shouldn't document
  .github/workflows/openwiki-update.yml  # on-demand (workflow_dispatch) CI job that auto-PRs OpenWiki doc updates
  .env.example  # template listing required env var names, keep in sync with actual usage
  .env  # local env file, never commit populated .env files
  .gitignore  # ignore .env, .venv, __pycache__, node_modules, etc.
```

## Skills

- Skills live in the `skillset` repo (https://github.com/konrad-woj/skillset) and are shared across projects - do not redefine project-local skills that already exist there.
- Sync/fetch skills from that repo into `.claude/skills/` (e.g. `git submodule` or a sync script) rather than copy-pasting skill content into this repo.
- If a task needs a skill that doesn't exist yet, add it to the `skillset` repo, not as a one-off local skill, unless it is genuinely project-specific.
- When working on a new feature or refactoring, use the `/feature-coder` skill (plan mode).

## Workflow

- All Dockerfiles are located in `{repo_root}` as they use multiple packages.
- Always use uv by going into the package dir (`{repo_root}/packages/{package_name}`) and running uv commands from there - this ensures that the correct environment is used.
- Inside the package dir you must always:
  - Use `uv run task precommits` when you're done making a series of code changes. This will run ruff checks, pyright typechecks, and tach module boundary checks. If found pyright errors are not important, ignore them specifically for particular lines of code. When a change adds or moves modules, run `uvx tach sync --add` in the package before committing so `tach.toml` reflects the real dependency graph.
  - Put unit tests in `./tests/unit` and run with `uv run pytest tests/unit`.
  - Put integration tests in `./tests/integration` and run with `uv run pytest tests/integration`.
  - Focus tests on critical logic, edge cases, and integration points - skip tests that add little value or are already covered by Pydantic validation.
  - Put all generated `.md` files in `./docs`, updating existing ones. Keep docs concise, reference the code, and add example usages - avoid repetitions, rationale, and estimates.
  - Never redefine the `logger` package locally - depend on it via `[tool.uv.sources]` pointing at the shared git repo (see `packages/pyproject.toml.example`), configure it with `configure_logger("INFO")` once in the executable entrypoint, and create it with `logger = structlog.get_logger()` when needed.
  - For execution timing use the `timer` or `async_timer` decorators from the `logger` package.
  - Generic, cross-package utilities are located in `../data-utils` - check it before implementing new utilities locally.
  - Generic, cross-package pydantic models are located in `../data-models` - check it before implementing new models locally.
  - Use environment variables from `.env` if present, keeping `.env.example` up to date whenever a new variable is introduced.

<!-- OPENWIKI:START -->

## OpenWiki

This repository uses OpenWiki for recurring code documentation. Start with `openwiki/quickstart.md`, then follow its links to architecture, workflows, domain concepts, operations, integrations, testing guidance, and source maps.

The scheduled OpenWiki GitHub Actions workflow refreshes the repository wiki. Do not hand-edit generated OpenWiki pages unless explicitly asked; prefer updating source code/docs and letting OpenWiki regenerate.

<!-- OPENWIKI:END -->
