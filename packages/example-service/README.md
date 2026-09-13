# example-service

Reference example of a runnable FastAPI service package: `main.py` entrypoint,
a router under `routers/`, response models in `models.py`, and a local path
dependency on `example-library`. Copy this shape for a new service.

Also demonstrates:

- `config.py` — a `pydantic-settings` `BaseSettings` (env vars / `.env`) picking which Hydra
  config variant to compose, and a Hydra-composed, Pydantic-validated `GreetingConfig` for it.
- `conf/` — Hydra config groups (`conf/greeting/default.yaml`, `conf/greeting/enthusiastic.yaml`).
- `exceptions.py` — a domain exception hierarchy mapped to HTTP responses via a FastAPI
  exception handler.
- `middleware.py` — a request-ID middleware that binds context for structured logging.

## Endpoints

`GET /greetings/{name}` — returns `{"message": "Hello, {name}!"}`. With the default greeting
style, the message is built with `example_library.build_greeting`, showing a package consuming
a sibling package via `[tool.uv.sources]`. Set `EXAMPLE_SERVICE_GREETING_STYLE=enthusiastic` to
use the Hydra-composed template instead. Names longer than `max_name_length` (from the same
config) return a `422` with a JSON `detail` message.

## Configuration

Set via env vars or a package-local `.env` (see `.env.example`), prefixed `EXAMPLE_SERVICE_`:

- `EXAMPLE_SERVICE_HOST` (default `0.0.0.0`)
- `EXAMPLE_SERVICE_PORT` (default `8000`)
- `EXAMPLE_SERVICE_GREETING_STYLE` — selects a Hydra config group under `conf/greeting/`
  (`default` or `enthusiastic`)

## Development

```bash
uv sync --all-groups
uv run task test
uv run task app          # serve on http://localhost:8000
uv run task precommits
```
