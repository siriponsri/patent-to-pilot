"""Path policy shared by schema inspection and runtime loaders (stdlib only).

A path is *protected* when its file name, or any directory component below ``root``, contains a TEST,
qrels, sealed, private or credential marker. Protected paths are refused before they are opened.
A path is *evaluator-side* when its name marks labels or gold evidence; inspection of such a path is
reduced to column names only.

Matching is deliberately broad (substring, case-insensitive): over-refusal is a safe failure.
"""
from __future__ import annotations

from pathlib import Path
import re

PROTECTED_MARKERS = ("test", "qrel", "sealed", "private", "secret", "credential", ".env")
EVALUATOR_MARKERS = ("gold", "relations", "label", "answer", "evidence", "judgment", "judgement")


class ProtectedPathError(PermissionError):
    """Raised when a caller asks to open a TEST, qrels, sealed, private or credential path."""


def _components(path: Path, root: Path | None) -> list[str]:
    path = Path(path)
    if root is not None:
        try:
            rel = path.resolve().relative_to(Path(root).resolve())
            return [p.lower() for p in rel.parts]
        except ValueError:
            pass
    # Without a usable root, check the file name and its immediate parent directory only, so an
    # unrelated ancestor (for example a pytest temporary directory) does not decide the policy.
    parts = [path.name.lower()]
    if path.parent.name:
        parts.append(path.parent.name.lower())
    return parts


def protected_reason(path: Path, root: Path | None = None) -> str | None:
    for comp in _components(path, root):
        for marker in PROTECTED_MARKERS:
            if marker in comp:
                return f"path component {comp!r} contains protected marker {marker!r}"
    return None


def evaluator_reason(path: Path, root: Path | None = None) -> str | None:
    for comp in _components(path, root):
        stem = re.sub(r"\.[a-z0-9]+$", "", comp)
        for marker in EVALUATOR_MARKERS:
            if marker in stem:
                return f"path component {comp!r} contains evaluator marker {marker!r}"
    return None


def assert_not_protected(path: Path, root: Path | None = None) -> None:
    reason = protected_reason(path, root)
    if reason:
        raise ProtectedPathError(f"refused to open {Path(path).name!r}: {reason}")
