"""Streaming read/write for JSON Lines datasets.

Example:
    >>> from pathlib import Path
    >>> path = Path("/tmp/rows.jsonl")
    >>> write_jsonl(path, [{"id": 1}, {"id": 2}])
    2
    >>> list(read_jsonl(path))
    [{'id': 1}, {'id': 2}]
"""

import json
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    """Yields one record per non-empty line, so large evaluation sets never load fully into memory."""
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                yield json.loads(stripped)


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            written += 1
    return written
