# example-library

Reference example of a plain importable library package: no FastAPI, no
entrypoint, just a `src/` module installed and consumed by other packages.
Copy this shape for a new cross-package or single-package library.

## `build_greeting`

`build_greeting` (`src/example_library/greetings.py`) is consumed by
`example-service` to show how one package depends on another locally.

```python
from example_library import build_greeting

build_greeting("World")
# "Hello, World!"
```

## Logging

`greetings.py` calls `get_logger(__name__)` and logs at `debug`, but never
configures logging itself — that's the entrypoint's job (see
`example-service`). A library that only calls `get_logger` behaves correctly
whether or not the process that imports it ever calls `configure_logging`.

## Development

```bash
uv sync --all-groups
uv run task test
uv run task precommits
```
