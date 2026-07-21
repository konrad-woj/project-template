# New project setup
- Copy `packages/pyproject.toml.example` to `packages/{package_name}/pyproject.toml` and populate `name`, `description`, and dependencies.
- Copy `DESIGN_DOC_TEMPLATE.md` to `MY_NEW_DESIGN_NAME.md` at the repo root and fill it in before starting a new feature or service (see `/designdoc-creator` skill).
- Copy `.env.example` to `.env` (repo root) and per-package `.env` files, and populate required keys (e.g. `GEMINI_API_KEY`, `OPENAI_API_KEY`). Never commit populated `.env` files.

# Bash commands - package level
uv run python <path_to_file>
uv run python -m <module>
uv run pytest tests/
uv run task precommit

# Bash commands - repo level
sh run_on_each.sh -b "uv run task precommit"
sh run_on_each.sh -b "uv lock"
docker build -f Dockerfile.{package_name} -t {image_name} .

# Code style
- Google style docstrings
- PEP8 style
- if a method can be static and is class-specific, decorate it with `@staticmethod` but if is generic/reusable, make it a function outside the class
- use explicit naming for variables and functions
- use type hints for all functions and methods, including return types
- if a function or method is long, consider splitting it into multiple functions - if done so, make sure to update tests and docs accordingly
- use "_" prefix for private methods and variables
- don't add error handling, fallbacks, or validation for scenarios that can't happen - validate only at system boundaries (user input, external APIs)
- don't design for hypothetical future requirements - three similar lines beat a premature abstraction

# Code structure
{repo_root}/
  packages/
    {package-name}/
      .env
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
      src/data_models/
        __init__.py
        models.py
    logger/  # reference copy only - real dependency comes from the shared git repo via [tool.uv.sources], do not fork/redefine per project
      src/logger/
        __init__.py
        logger.py
        timer.py
        async_timer.py
  Dockerfile.{package_name}  # Dockerfiles for each package, located in the repo root as they use multiple packages
  run_on_each.sh  # helper script to run commands in all packages, e.g., sh run_on_each.sh -b "uv run task precommit"
  CLAUDE.md  # project instructions for Claude
  MY_NEW_DESIGN_NAME.md  # per-feature design doc, copied from DESIGN_DOC_TEMPLATE.md
  DESIGN_DOC_TEMPLATE.md  # template - copy, don't edit in place
  pyproject.toml.example  # template - copy into a new package dir, don't edit in place
  .env.example  # template listing required env var names, keep in sync with actual usage
  .env  # local env file, never commit populated .env files
  .gitignore  # ignore .env, .venv, __pycache__, etc.

# Skills
- Skills live in the `skillset` repo (https://github.com/konrad-woj/skillset) and are shared across projects - do not redefine project-local skills that already exist there.
- Sync/fetch skills from that repo into `.claude/skills/` (e.g. `git submodule` or a sync script) rather than copy-pasting skill content into this repo.
- If a task needs a skill that doesn't exist yet, add it to the `skillset` repo, not as a one-off local skill, unless it is genuinely project-specific.

# Plan mode
- When working on a new feature or refactoring, use /feature-coder skill

# Workflow
- All Dockerfiles are located in `{repo_root}` as they use multiple packages
- Always use uv by going into the package dir (`{repo_root}/packages/{package_name}`) and running uv commands from there - this ensures that the correct environment is used.
- Inside the package dir you must always:
  - Use `uv run task precommit` when you’re done making a series of code changes. This will run ruff checks and pyright typechecks. If found pyright errors are not important, ignore them specifically for particular lines of code
  - Put unit tests always in `./tests/unit` and run with `uv run pytest tests/unit`
  - Put integration tests always in `./tests/integration` and run with `uv run pytest tests/integration`
  - Focus tests on critical logic, edge cases, and integration points - skip tests that add little value or are already covered by Pydantic validation
  - Put all generated .md files in `./docs` dir update the existing ones
  - When writing docs, always keep it super concise and reference the code, add example usages. Avoid repetitions, rationale, estimates, etc.
  - Never redefine the `logger` package locally - depend on it via `[tool.uv.sources]` pointing at the shared git repo (see `packages/pyproject.toml.example`), configure it with `configure_logger("INFO")` once in the executable entrypoint, and create it with `logger = structlog.get_logger()` when needed
  - Never use print statements in packages - use structured logging instead
  - For execution timing use the `timer` or `async_timer` decorators from the `logger` package
  - Generic, cross-package utilities are located in `../data-utils` dir - check it before implementing new utilities locally
  - Generic, cross-package pydantic models are located in `../data-models` dir - check it before implementing new models locally
  - For API contracts (input/output messages) use our `from data_models.models import BaseSchema` class from `../data-models` package instead of Pydantic BaseModel
  - Use environment variables from `.env` file if present, keeping `.env.example` up to date whenever a new variable is introduced

