"""Streaming ingestion for the PLS CSV payloads acquired by G03."""

from __future__ import annotations

import csv
import hashlib
import os
import tempfile
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
import sys

from pydantic import BaseModel, ConfigDict, Field

csv.field_size_limit(min(sys.maxsize, 64 * 1024 * 1024))


class PatentDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document_id: str
    source_id: str
    source_version: str
    family_id: str | None = None
    publication_id: str | None = None
    kind_code: str | None = None
    title: str = ""
    abstract: str = ""
    claims: str = ""
    description: str = ""
    cpc: str = ""
    ipc: str = ""
    labels: str = ""
    publication_date: str | None = None
    publication_date_status: str = "unknown_not_in_source"
    missing_fields: list[str] = Field(default_factory=list)
    source_locator: str
    source_sha256: str


class IngestionReport(BaseModel):
    source_id: str
    source_version: str
    input_path: str
    output_path: str
    rows_read: int
    rows_written: int
    fields: list[str]
    missing_counts: dict[str, int]
    duplicate_key_count: int
    duplicate_family_count: int
    observed_family_count: int
    publication_dates_observed: int
    publication_dates_unknown: int
    max_rows: int | None = None


def _split_first(value: str) -> tuple[str | None, str | None]:
    values = [part.strip() for part in value.split(";") if part.strip()]
    return (values[0], values[1] if len(values) > 1 else None) if values else (None, None)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class PLSIngester:
    required_fields = ["Family Number", "Patent Number", "Kind Code", "Title", "Abstract", "Claims", "Description", "CPC", "IPC", "labels"]

    def iter_documents(self, path: str | Path, source_id: str, source_version: str, max_rows: int | None = None) -> Iterator[PatentDocument]:
        input_path = Path(path)
        source_sha256 = _sha256(input_path)
        with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None or reader.fieldnames != self.required_fields:
                raise ValueError(f"unexpected PLS fields: {reader.fieldnames}")
            for row_number, row in enumerate(reader, start=2):
                if None in row or any(value is None for value in row.values()) or len(row) != len(self.required_fields):
                    actual_width = sum(value is not None for key, value in row.items() if key is not None)
                    if None in row:
                        actual_width += len(row[None])
                    raise ValueError(
                        f"malformed CSV row at {input_path} row {row_number}: "
                        f"expected {len(self.required_fields)} fields, got {actual_width}"
                    )
                if max_rows is not None and row_number - 1 > max_rows:
                    break
                family_id, _ = _split_first(row.get("Family Number", ""))
                patent_id, secondary_patent_id = _split_first(row.get("Patent Number", ""))
                document_id = f"{source_id}:{family_id or 'unknown'}:{patent_id or secondary_patent_id or row_number}"
                missing = [field for field in ("Title", "Abstract", "Claims", "Description", "CPC", "IPC", "labels") if not (row.get(field) or "").strip()]
                yield PatentDocument(
                    document_id=document_id, source_id=source_id, source_version=source_version,
                    family_id=family_id, publication_id=patent_id,
                    kind_code=(row.get("Kind Code") or "").strip() or None,
                    title=(row.get("Title") or "").strip(), abstract=(row.get("Abstract") or "").strip(),
                    claims=(row.get("Claims") or "").strip(), description=(row.get("Description") or "").strip(),
                    cpc=(row.get("CPC") or "").strip(), ipc=(row.get("IPC") or "").strip(),
                    labels=(row.get("labels") or "").strip(), missing_fields=missing,
                    source_locator=f"{input_path.as_posix()}#row={row_number}", source_sha256=source_sha256,
                )

    def ingest_jsonl(self, path: str | Path, output: str | Path, source_id: str, source_version: str, max_rows: int | None = None) -> IngestionReport:
        input_path, output_path = Path(path), Path(output)
        resolved_input = input_path.resolve(strict=True)
        resolved_output = output_path.resolve(strict=False)
        same_file = resolved_input == resolved_output
        if output_path.exists():
            same_file = same_file or os.path.samefile(input_path, output_path)
        if same_file:
            raise ValueError("input and output must be different files")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        missing_counts: Counter[str] = Counter()
        key_counts: Counter[tuple[str | None, str | None]] = Counter()
        family_counts: Counter[str] = Counter()
        rows_read = rows_written = publication_dates_observed = 0
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", newline="\n", suffix=".jsonl",
                prefix=f".{output_path.name}.", dir=output_path.parent, delete=False
            ) as handle:
                temporary_path = Path(handle.name)
                for document in self.iter_documents(input_path, source_id, source_version, max_rows=max_rows):
                    rows_read += 1; rows_written += 1
                    for field in document.missing_fields: missing_counts[field] += 1
                    key_counts[(document.family_id, document.publication_id)] += 1
                    if document.family_id: family_counts[document.family_id] += 1
                    if document.publication_date: publication_dates_observed += 1
                    handle.write(document.model_dump_json() + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, output_path)
            temporary_path = None
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
        return IngestionReport(
            source_id=source_id, source_version=source_version, input_path=input_path.as_posix(), output_path=output_path.as_posix(),
            rows_read=rows_read, rows_written=rows_written, fields=self.required_fields,
            missing_counts=dict(sorted(missing_counts.items())),
            duplicate_key_count=sum(1 for count in key_counts.values() if count > 1),
            duplicate_family_count=sum(1 for count in family_counts.values() if count > 1),
            observed_family_count=len(family_counts), publication_dates_observed=publication_dates_observed,
            publication_dates_unknown=rows_written - publication_dates_observed, max_rows=max_rows,
        )

    def ingest_to_stream(self, path: str | Path, output, source_id: str, source_version: str, max_rows: int | None = None) -> int:
        count = 0
        for document in self.iter_documents(path, source_id, source_version, max_rows=max_rows):
            output.write(document.model_dump_json() + "\n"); count += 1
        return count
