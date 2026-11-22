"""Guarded local row reader for JSONL files (stdlib only).

Refuses TEST/qrels/sealed/private/credential paths before opening them. Evaluator-marked paths are
refused unless ``allow_evaluator=True`` (evaluator-side code only). Lines are decoded as UTF-8 and
parsed with ``json``; string values are returned exactly as stored.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from .policy import ProtectedPathError, assert_not_protected, evaluator_reason


def iter_jsonl(path: Path | str, *, root: Path | str | None = None, allow_evaluator: bool = False) -> Iterator[dict]:
    p = Path(path)
    root_p = Path(root) if root is not None else None
    assert_not_protected(p, root_p)
    reason = evaluator_reason(p, root_p)
    if reason and not allow_evaluator:
        raise ProtectedPathError(f"refused runtime read of {p.name!r}: {reason}")
    with p.open("r", encoding="utf-8", newline="") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)
