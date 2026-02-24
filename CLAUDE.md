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
- if a function or method is long, consider splitting it into multiple functions - if done so, make sure to update tests and docs accordingly
- use "_" prefix for private methods and variables 

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
      docs/
        {doc_name}.md
      notebooks/  # exploratory notebooks, not meant to be imported
      evaluation/  # evaluation scripts, run locally with --dev dependency group, not meant to be imported in packages, e.g., evaluation of model performance, evaluation of retrieval quality, etc.
        __init__.py
        {evaluation_name}.py
      scripts/  # other dev scripts for local testing
        __init__.py
        {script_name}.py
    data-utils/
      src/data_utils/
        __init__.py
        {util_name}.py
    data-models/
      src/data_models/
        __init__.py
        models.py
    gemini-client/
      src/gemini_client/
        __init__.py
        gemini.py
        ...
    logger/
      src/logger/
        __init__.py
        logger.py
        timer.py
        async_timer.py
  Dockerfile.{package_name}  # Dockerfiles for each package, located in the repo root as they use multiple packages
  run_on_each.sh  # helper script to run commands in all packages, e.g., sh run_on_each.sh -b "uv run task precommit"
  CLAUDE.md  # project instructions for Claude
  DESIGN_DOC.md  # high-level design doc

# Plan mode
- When working on a new feature or refactoring, use /feature-coder skill

# Workflow
- All Dockerfiles are located in `{repo_root}` as they use multiple packages
- Always use uv by going into the package dir (`{repo_root}/packages/{package_name}`) and running uv commands from there - this ensures that the correct environment is used.
- Inside the package dir you must always:
  - Use `uv run task precommit` when you’re done making a series of code changes. This will run ruff checks and pyright typechecks. If found pyright errors are not important, ignore them specifically for particular lines of code
  - Put unit tests always in `./tests/unit` and run with `uv run pytest tests/unit`
  - Put integration tests always in `./tests/integration` and run with `uv run pytest tests/integration`
  - Put all generated .md files in `./docs` dir update the existing ones
  - When writing docs, always keep it super concise and reference the code, add example usages. Avoid repetitions, rationale, estimates, etc.
  - For logging, use our local `../logger` package, configure it with `configure_logger("INFO")` once in executable, and create it with `logger = stuctlog.get_logger()` when needed
  - Never use print statements in packages - use structured logging instead
  - For the execution timing use `timer` or `async_timer` modules from `../logger` package as decorators
  - Generic, cross-package utilities are located in `../data-utils` dir - check it before implementing new utilities locally
  - Generic, cross-package pydantic models are located in `../data-models` dir - check it before implementing new models locally
  - For API contracts (input/output messages) use our `from data_models.models import BaseSchema` class from `../data-models` package instead of Pydantic BaseModel
  - Use environment variables from `.env` file if present

