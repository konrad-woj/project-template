from pathlib import Path

from data_utils import read_jsonl, write_jsonl


def test_round_trip_creates_missing_parents(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "rows.jsonl"
    records = [{"id": 1, "text": "café"}, {"id": 2, "text": "naïve"}]

    assert write_jsonl(path, records) == 2
    assert list(read_jsonl(path)) == records


def test_read_skips_blank_lines(tmp_path: Path) -> None:
    path = tmp_path / "rows.jsonl"
    path.write_text('{"id": 1}\n\n   \n{"id": 2}\n', encoding="utf-8")

    assert list(read_jsonl(path)) == [{"id": 1}, {"id": 2}]
