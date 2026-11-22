"""Plain text / Markdown ingestion (G02).

The stored text is the exact UTF-8 decoding of the supplied bytes: no normalisation, no BOM stripping, no
line-ending changes. Passages carry zero-based, end-exclusive code-point offsets into that text, so every citation
can be checked with ``text[start:end] == quote``.

Passage rules:
* ``fixture_heading_passages_v1``: files with ``## <ID>`` headings (the G01 authored-fixture format) use the G01
  rule, so the bounded field parser keeps working on owner files written in that format.
* ``paragraph_blocks_v1``: otherwise each run of non-blank lines is one passage (``p0001``, ``p0002`` ...).

Structured PDF ingestion is not installed in this build: ``pdf_capability()`` reports it as unavailable and
a PDF upload is refused with that explanation rather than guessed at.
"""
from __future__ import annotations

import importlib.util
from pathlib import PurePath
import re

MAX_BYTES = 2_000_000
TEXT_SUFFIXES = {".md": "owner_markdown", ".markdown": "owner_markdown", ".txt": "owner_text"}
_BLOCK = re.compile(r"[^\r\n]*\S[^\r\n]*(?:\r?\n[^\r\n]*\S[^\r\n]*)*")
_SLUG = re.compile(r"[^A-Za-z0-9_-]+")
_HEADING = re.compile(r"^## [A-Za-z0-9][A-Za-z0-9_-]*[ \t]*\r?$", re.M)


class IngestError(Exception):
    def __init__(self, message: str, code: str) -> None:
        super().__init__(message)
        self.code = code


def pdf_capability() -> dict:
    for mod in ("docling", "pypdf"):
        if importlib.util.find_spec(mod):
            return {"state": "installed_not_enabled", "module": mod,
                    "description": f"{mod} is importable but the PDF adapter is not enabled in G02."}
    return {"state": "unavailable", "description": "No PDF parser is installed. Plain text and Markdown work; "
                                                    "add PDF support later as an optional extra."}


def slug_source_id(filename: str) -> str:
    stem = PurePath(filename).stem
    s = _SLUG.sub("-", stem).strip("-_")[:48]
    if not s or not s[0].isalnum():
        s = "doc-" + s
    return s


def paragraph_passages(text: str) -> list[dict]:
    out = []
    for n, m in enumerate(_BLOCK.finditer(text), start=1):
        out.append({"passage_id": f"p{n:04d}", "start_char": m.start(), "end_char": m.end(), "quote": m.group(0)})
    return out


def prepare(filename: str, raw: bytes, fixture_passages) -> dict:
    """Validate and decode one uploaded file and derive its passages. ``fixture_passages`` is the G01
    passage extractor (passed in to avoid a circular import)."""
    suffix = PurePath(filename).suffix.lower()
    if suffix == ".pdf":
        cap = pdf_capability()
        raise IngestError(f"PDF ingestion is not available in this build ({cap['state']}). "
                          "Convert the file to text or Markdown first.", "pdf_unavailable")
    if suffix not in TEXT_SUFFIXES:
        raise IngestError("only .md, .markdown and .txt files are accepted", "unsupported_type")
    if not raw:
        raise IngestError("the file is empty", "empty_file")
    if len(raw) > MAX_BYTES:
        raise IngestError(f"the file is larger than {MAX_BYTES // 1_000_000} MB", "too_large")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise IngestError(f"the file is not valid UTF-8 (byte {exc.start})", "not_utf8") from None
    if "\x00" in text:
        raise IngestError("the file contains NUL characters; it does not look like text", "binary_content")
    if _HEADING.search(text):
        passages, rule = fixture_passages(text), "fixture_heading_passages_v1"
    else:
        passages, rule = paragraph_passages(text), "paragraph_blocks_v1"
    if not passages:
        raise IngestError("no text passages were found", "no_passages")
    for p in passages:
        assert text[p["start_char"]:p["end_char"]] == p["quote"]
    title = None
    for line in text.splitlines():
        s = line.strip().lstrip("﻿")
        if s:
            title = s.lstrip("#").strip() or None
            break
    return {"text": text, "passages": passages, "passage_rule": rule, "source_kind": TEXT_SUFFIXES[suffix],
            "title": (title or PurePath(filename).name)[:200]}
