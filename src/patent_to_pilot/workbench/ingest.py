"""Plain text / Markdown ingestion (G02).

The stored text is the exact UTF-8 decoding of the supplied bytes: no normalisation, no BOM stripping, no
line-ending changes. Passages carry zero-based, end-exclusive code-point offsets into that text, so every citation
can be checked with ``text[start:end] == quote``.

Passage rules:
* ``fixture_heading_passages_v1``: files with ``## <ID>`` headings (the G01 authored-fixture format) use the G01
  rule, so the bounded field parser keeps working on owner files written in that format.
* ``paragraph_blocks_v1``: otherwise each run of non-blank lines is one passage (``p0001``, ``p0002`` ...).

PDF ingestion (D8, optional ``pypdf``): the text layer of each page is extracted with ``pypdf`` and stored as a
canonical UTF-8 text with one ``[page N]`` marker line per page (``pdf_text_layer_v1``). That canonical text *is* the
stored version (its bytes are the stored ``raw``), so every citation keeps ``text[start:end] == quote``; the original PDF's
sha256, page count and the pypdf version are kept in the version path as provenance. Passages are the non-blank blocks of
each page (``p<page>-<n>``); marker lines are never passages. Encrypted PDFs, PDFs without a text layer (scans) and
unreadable files are refused with an explanation; no OCR is attempted. Without ``pypdf`` a PDF upload is refused.
"""
from __future__ import annotations

import importlib.util
from pathlib import PurePath
import re

MAX_BYTES = 2_000_000
MAX_PDF_BYTES = 2_000_000          # the HTTP upload limit is sized for 2 MB; the extracted text obeys MAX_BYTES too
PDF_RULE = "pdf_text_layer_v1"
TEXT_SUFFIXES = {".md": "owner_markdown", ".markdown": "owner_markdown", ".txt": "owner_text"}
_BLOCK = re.compile(r"[^\r\n]*\S[^\r\n]*(?:\r?\n[^\r\n]*\S[^\r\n]*)*")
_SLUG = re.compile(r"[^A-Za-z0-9_-]+")
_HEADING = re.compile(r"^## [A-Za-z0-9][A-Za-z0-9_-]*[ \t]*\r?$", re.M)


class IngestError(Exception):
    def __init__(self, message: str, code: str) -> None:
        super().__init__(message)
        self.code = code


def pdf_capability() -> dict:
    if importlib.util.find_spec("pypdf"):
        import pypdf
        return {"state": "active", "module": "pypdf", "version": pypdf.__version__, "rule": PDF_RULE,
                "max_bytes": MAX_PDF_BYTES,
                "description": f"PDF text layer via pypdf {pypdf.__version__}; scanned PDFs (no text layer) are refused."}
    return {"state": "unavailable", "description": "No PDF parser is installed. Plain text and Markdown work; "
                                                    "install the optional 'pdf' extra (pypdf) for PDF files."}


def _pdf_text(raw: bytes) -> tuple[str, list[dict], dict]:
    """Canonical text, passages and provenance for a PDF. Raises IngestError on anything it cannot read safely."""
    import hashlib
    import io
    import pypdf
    from pypdf.errors import PdfReadError
    if len(raw) > MAX_PDF_BYTES:
        raise IngestError(f"the PDF is larger than {MAX_PDF_BYTES // 1_000_000} MB", "too_large")
    if not raw.startswith(b"%PDF-"):
        raise IngestError("the file does not start with a PDF header", "not_pdf")
    try:
        reader = pypdf.PdfReader(io.BytesIO(raw), strict=False)
        if reader.is_encrypted:
            raise IngestError("the PDF is encrypted; save an unencrypted copy first", "pdf_encrypted")
        pages = [(pg.extract_text() or "") for pg in reader.pages]
    except IngestError:
        raise
    except (PdfReadError, ValueError, KeyError, TypeError, AttributeError, OSError, RecursionError) as exc:
        raise IngestError(f"the PDF could not be read ({type(exc).__name__})", "pdf_unreadable") from None
    parts, passages, pos = [], [], 0
    for n, page in enumerate(pages, start=1):
        body = "\n".join(line.rstrip() for line in page.replace("\r\n", "\n").replace("\r", "\n").split("\n"))
        body = body.replace("\x00", "").strip()
        head = f"[page {n}]\n"
        chunk = head + body + "\n\n"
        base = pos + len(head)
        for k, m in enumerate(_BLOCK.finditer(body), start=1):
            passages.append({"passage_id": f"p{n:03d}-{k:03d}", "start_char": base + m.start(),
                             "end_char": base + m.end(), "quote": m.group(0), "page": n})
        parts.append(chunk)
        pos += len(chunk)
    text = "".join(parts)
    if not passages:
        raise IngestError("the PDF has no text layer (a scan?); OCR is not supported", "pdf_no_text")
    if len(text.encode("utf-8")) > MAX_BYTES:
        raise IngestError(f"the extracted text is larger than {MAX_BYTES // 1_000_000} MB", "too_large")
    meta = {"pdf_sha256": hashlib.sha256(raw).hexdigest(), "pages": len(pages), "pypdf": pypdf.__version__,
            "rule": PDF_RULE}
    return text, passages, meta


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
    if not raw:
        raise IngestError("the file is empty", "empty_file")
    if suffix == ".pdf":
        cap = pdf_capability()
        if cap["state"] != "active":
            raise IngestError(f"PDF ingestion is not available in this build ({cap['state']}). "
                              "Convert the file to text or Markdown first.", "pdf_unavailable")
        text, passages, meta = _pdf_text(raw)
        for p in passages:
            assert text[p["start_char"]:p["end_char"]] == p["quote"]
        first = next((p["quote"].splitlines()[0].strip() for p in passages if p["quote"].strip()), "")
        return {"text": text, "passages": passages, "passage_rule": PDF_RULE, "source_kind": "owner_pdf",
                "title": (first or PurePath(filename).name)[:200], "stored_raw": text.encode("utf-8"), "pdf": meta}
    if suffix not in TEXT_SUFFIXES:
        raise IngestError("only .md, .markdown, .txt and .pdf files are accepted", "unsupported_type")
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
