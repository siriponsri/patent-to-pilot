"""Read-only schema inspection for local JSONL / CSV / JSON files (stdlib only).

The report holds column names, inferred types and a row count. It never holds a row value.
TEST, qrels, sealed, private and credential paths are refused before they are opened.
Evaluator-side paths (or ``role="evaluator"``) are reduced to column names only.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
import json
from pathlib import Path

from .policy import assert_not_protected, evaluator_reason

SUPPORTED = {".jsonl": "jsonl", ".ndjson": "jsonl", ".csv": "csv", ".json": "json"}


@dataclass(frozen=True)
class SchemaReport:
    path_name: str
    format: str
    columns: tuple[str, ...]
    types: dict = field(default_factory=dict)
    row_count: int | None = None
    reduced: bool = False
    note: str = ""

    def to_dict(self) -> dict:
        return {"path_name": self.path_name, "format": self.format, "columns": list(self.columns),
                "types": dict(self.types), "row_count": self.row_count, "reduced": self.reduced, "note": self.note}


def _type_name(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        inner = sorted({_type_name(v) for v in value})
        return f"list[{'|'.join(inner) if inner else 'empty'}]"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _csv_type(text: str) -> str:
    if text == "":
        return "empty"
    for caster, name in ((int, "int"), (float, "float")):
        try:
            caster(text)
            return name
        except ValueError:
            pass
    return "string"


def _merge(types: dict, key: str, name: str) -> None:
    types.setdefault(key, set()).add(name)


def _finish(types: dict) -> dict:
    return {k: "|".join(sorted(v)) for k, v in types.items()}


def _scan_records(records, reduced: bool):
    columns: list[str] = []
    types: dict = {}
    count = 0
    for rec in records:
        count += 1
        if not isinstance(rec, dict):
            _merge(types, "<row>", _type_name(rec))
            continue
        for key, value in rec.items():
            if key not in columns:
                columns.append(key)
            if not reduced:
                _merge(types, key, _type_name(value))
    return columns, types, count


def _jsonl_records(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def inspect_schema(path: Path | str, *, role: str = "runtime", root: Path | str | None = None) -> SchemaReport:
    """Inspect a local file's schema. ``role`` is ``runtime`` or ``evaluator``."""
    p = Path(path)
    root_p = Path(root) if root is not None else None
    assert_not_protected(p, root_p)  # refuse before opening
    fmt = SUPPORTED.get(p.suffix.lower())
    if fmt is None:
        raise ValueError(f"unsupported format {p.suffix!r}; supported: {sorted(SUPPORTED)}")
    if role not in ("runtime", "evaluator"):
        raise ValueError("role must be 'runtime' or 'evaluator'")
    ev = evaluator_reason(p, root_p)
    reduced = role == "evaluator" or ev is not None
    note = "reduced to column names only: " + (ev or "role=evaluator") if reduced else ""

    if fmt == "csv":
        with p.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.reader(fh)
            header = next(reader, [])
            if reduced:
                return SchemaReport(p.name, fmt, tuple(header), {}, None, True, note)
            types: dict = {}
            count = 0
            for row in reader:
                count += 1
                for key, cell in zip(header, row):
                    _merge(types, key, _csv_type(cell))
        return SchemaReport(p.name, fmt, tuple(header), _finish(types), count, False, note)

    if fmt == "jsonl":
        columns, types, count = _scan_records(_jsonl_records(p), reduced)
    else:
        doc = json.loads(p.read_text(encoding="utf-8"))
        records = doc if isinstance(doc, list) else [doc]
        columns, types, count = _scan_records(records, reduced)
    if reduced:
        return SchemaReport(p.name, fmt, tuple(columns), {}, None, True, note)
    return SchemaReport(p.name, fmt, tuple(columns), _finish(types), count, False, note)
