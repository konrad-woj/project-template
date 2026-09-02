# data-utils

Generic, cross-package helpers. Check here before writing a utility inside a
service package — anything reused by two packages belongs in this one.

## Environment access

`require_env` / `require_envs` (`src/data_utils/env.py`) read required keys at
startup and raise `MissingEnvironmentVariableError` naming every missing key at
once, so a misconfigured deployment fails immediately instead of at first use.
Empty strings count as missing, which is what an unpopulated `.env` produces.

```python
from data_utils import require_envs

config = require_envs(["GEMINI_API_KEY", "OPENAI_API_KEY"])
```

## JSONL I/O

`read_jsonl` / `write_jsonl` (`src/data_utils/jsonl.py`) stream JSON Lines
records so evaluation sets and datasets never load fully into memory.
`write_jsonl` creates missing parent directories and returns the record count.

```python
from pathlib import Path

from data_utils import read_jsonl, write_jsonl

write_jsonl(Path("evals/data/cases.jsonl"), cases)
for case in read_jsonl(Path("evals/data/cases.jsonl")):
    ...
```

## Development

```bash
uv sync --all-groups
uv run task test
uv run task precommits
```
